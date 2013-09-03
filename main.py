#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
# import logging
import pprint

from google.appengine.api import memcache
from google.appengine.ext import db
from datetime import datetime
from datetime import timedelta

filep = os.path.join(os.path.dirname(__file__), 'templates')
jinja_environment = jinja2.Environment(autoescape=True,
                                       loader=jinja2.FileSystemLoader(filep))

pp = pprint.PrettyPrinter(indent=4)

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Developement')


def rebuild_memcache():
    record_high = timedelta.min
    record_low = timedelta.max
    prev_alarm_temp = None

    q = db.GqlQuery("SELECT * FROM Alarmtimestamp ORDER BY alarm_datetime ASC")
    alarms = q.fetch(500)

    if alarms:

        # calc records
        for element in alarms:
            if prev_alarm_temp:
                element.prev_alarm = prev_alarm_temp
                # logging.info('record_high')
                if (element.alarm_datetime - element.prev_alarm) > record_high:
                    record_high = (element.alarm_datetime - element.prev_alarm)
                if (element.alarm_datetime - element.prev_alarm) < record_low:
                    record_low = (element.alarm_datetime - element.prev_alarm)

            prev_alarm_temp = element.alarm_datetime
        memcache.set('record_high', record_high)
        memcache.set('record_low', record_low)
        memcache.set('alarms', alarms)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        #check memcache and rebuild if empty
        alarms = memcache.get('alarms')
        if alarms is None:
            rebuild_memcache()
            alarms = memcache.get('alarms')

        #fetch records
        if len(alarms) > 1:
            record_high = memcache.get('record_high')
            record_low = memcache.get('record_low')
            record_high_days = record_high.days
            record_high_hours = record_high.seconds / 3600
            record_low_days = record_low.days
            record_low_hours = record_low.seconds / 3600
        else:
            record_high_days = 0
            record_high_hours = 0
            record_low_days = 0
            record_low_hours = 0

        displayalarm = alarms[len(alarms) - 1]
        today = datetime.today()
        timedelta = today - displayalarm.alarm_datetime
        # logging.info('len(alarms): %s' % len(alarms))
        template_values = {'days': timedelta.days,
                           'hours': timedelta.seconds / 3600,
                           'record_high_days': record_high_days,
                           'record_high_hours': record_high_hours,
                           'record_low_days': record_low_days,
                           'record_low_hours': record_low_hours,
                           'show_records': len(alarms) > 1}
        template = jinja_environment.get_template('index.htm')
        self.response.out.write(template.render(template_values))


class Resestpage(webapp2.RequestHandler):
    def get(self):
        message = "Leave empty to set to (now)"
        alarms = memcache.get('alarms')
        template_values = {'message': message,
                           'alarms': alarms}
        template = jinja_environment.get_template('reset.htm')
        self.response.out.write(template.render(template_values))

    def post(self):
        user_date = self.request.get('date')
        user_time = self.request.get('time')
        user_utc_offset = self.request.get('utc_offset')

        # usre_utc_offset format is like this UTC-04
        utc_offset = int(user_utc_offset])

        error_raised = None
        if user_date == '' and user_time == '':
            user_datetime = datetime.today()
        else:
            try:
                #dd.mm.yyyy hh:mm
                user_datetime = datetime.strptime(user_date +
                                                  ' ' +
                                                  user_time,
                                                  '%d.%m.%Y %H:%M')

            except ValueError:
                error_raised = True

        if error_raised:
            message = "Error with date/time format"

        else:
            message = "Last alarm set to %s" % datetime.strftime(user_datetime,
                      "%a, %d %b %Y %H:%M:%S")

            #write new alarm into db
            new_alarm = Alarmtimestamp(alarm_datetime=user_datetime)
            new_alarm.put()

            #update cache
            alarms = memcache.get('alarms')

            if len(alarms) < 1:
                memcache.set('alarms', [new_alarm])
            else:
                alarms.append(new_alarm)
                memcache.set('alarms', alarms)

        # logging.info('alarms: %s' % pp.pformat(alarms))
        template_values = {'message': message,
                           'alarms': alarms}
        template = jinja_environment.get_template('reset.htm')
        self.response.out.write(template.render(template_values))


class Alarmtimestamp(db.Model):
    alarm_datetime = db.DateTimeProperty()
    prev_alarm = db.DateTimeProperty()

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/secretresetpage', Resestpage)],
                              debug=True)
