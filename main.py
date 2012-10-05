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
import logging

from google.appengine.api import memcache
from google.appengine.ext import db
from datetime import date
from datetime import datetime
# from time import strftime


jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Developement')

class MainHandler(webapp2.RequestHandler):
    def get(self):
        key = 'alarm'

        alarms = memcache.get(key)

        if alarms is None:
            alarms = db.GqlQuery("SELECT * from Alarmtimestamp")

            alarms = list(alarms) 
            logging.info('DB Query!')
        else:
            logging.info('Cache Hit!: %s' % alarms[0].alarm_datetime)
        


        #still none?
        if  len(alarms)<1:
            displayalarm = Alarmtimestamp(alarm_datetime=datetime.today()) # first run without having set a last_alarm yet
        else:
            displayalarm = alarms[0]
            memcache.set('alarm', alarms) 
        today = datetime.today()
        timedelta = abs(today-displayalarm.alarm_datetime)

        template_values={'days':timedelta.days}
        template = jinja_environment.get_template('index.htm')       
        self.response.out.write(template.render(template_values))


class Resestpage(webapp2.RequestHandler):
    def get(self):
        message="Leave empty to set to (now)"
        template_values={"message":message}
        template = jinja_environment.get_template('reset.htm')       
        self.response.out.write(template.render(template_values))

    def post(self):
        user_date = self.request.get('date')
        user_time = self.request.get('time') 

        error_raised = None
        if user_date == '' and user_time=='':
            user_datetime = datetime.today()
        else:
            try:
                user_datetime = datetime.strptime(user_date+' '+user_time, '%d.%m.%Y %H:%M')#dd.mm.yyyy hh:mm
                

            except ValueError as e:
                error_raised = True


        if error_raised:
            message="Error with date/time format"
            template_values={'message':message}
        else:
            message="Last alarm set to %s" % datetime.strftime(user_datetime, "%a, %d %b %Y %H:%M:%S")
            template_values={'message':message}

            # all ok write to db, update cache
            q = db.GqlQuery("SELECT * from Alarmtimestamp")
            q = list(q)
            if len(q)<1:
                new_alarm = Alarmtimestamp(alarm_datetime = user_datetime)
                new_alarm.put()
                memcache.set('alarm', [new_alarm])
            else:
                existing_alarm = q[0]
                existing_alarm.alarm_datetime = user_datetime
                existing_alarm.put()
                memcache.set('alarm', [existing_alarm])
            # update cache


        template = jinja_environment.get_template('reset.htm')       
        self.response.out.write(template.render(template_values))


class Alarmtimestamp(db.Model):
    alarm_datetime = db.DateTimeProperty()



app = webapp2.WSGIApplication([('/', MainHandler),
                                ('/secretresetpage', Resestpage)],
                              debug=True)
