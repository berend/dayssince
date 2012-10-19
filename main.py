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
import json

from google.appengine.api import memcache
from google.appengine.ext import db
from datetime import datetime
# from time import strftime


jinja_environment = jinja2.Environment(autoescape=True,
                                       loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Developement')


class BaseHandler(webapp2.RequestHandler):
    def render(self, template_name, template_values):
        template = jinja_environment.get_template(template_name)
        self.response.out.write(template.render(template_values))

    def render_json(self, template_values):
        self.response.headers['Content-Type'] = "application/json; charset=UTF-8"
        self.response.out.write(json.dumps(template_values))


class MainHandler(BaseHandler):
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
        if  len(alarms) < 1:
            displayalarm = Alarmtimestamp(alarm_datetime=datetime.today())
        else:
            displayalarm = alarms[0]
            memcache.set('alarm', alarms)
        today = datetime.today()
        timedelta = today - displayalarm.alarm_datetime

        template_values = {'days': timedelta.days,
                           'hours': timedelta.seconds / 3600}
        self.render('index.htm', template_values)


class AdminPage(BaseHandler):
    def get(self, path):
        message = "Leave empty to set to (now)"
        template_values = {"message": message}
        self.render('reset.htm', template_values)

    def post(self, path):
        user_date = self.request.get('date')
        user_time = self.request.get('time')

        error_raised = None
        if user_date == '' and user_time == '':
            user_datetime = datetime.today()
        else:
            try:
                #dd.mm.yyyy hh:mm
                user_datetime = datetime.strptime(user_date + ' ' + user_time, '%d.%m.%Y %H:%M')

            except ValueError:
                error_raised = True

        if error_raised:
            message = "Error with date/time format"
            template_values = {'message': message}
        else:
            message = "Last alarm set to %s" % datetime.strftime(user_datetime, "%a, %d %b %Y %H:%M:%S")
            template_values = {'message': message}

            # all ok write to db, update cache
            q = db.GqlQuery("SELECT * from Alarmtimestamp")
            q = list(q)
            if len(q) < 1:
                new_alarm = Alarmtimestamp(alarm_datetime=user_datetime)
                new_alarm.put()
                memcache.set('alarm', [new_alarm])
            else:
                existing_alarm = q[0]
                existing_alarm.alarm_datetime = user_datetime
                existing_alarm.put()
                memcache.set('alarm', [existing_alarm])
            # update cache

        self.render('reset.htm', template_values)


class NewPage(BaseHandler):
    def get(self):
        template_values = {"message": "New Page - GET handler"}
        self.render('generic.htm', template_values)

    def Post(self):
        template_values = {"message": "New Page - POST handler"}
        self.render('generic.htm', template_values)


class CustomMainPage(BaseHandler):
    def get(self, path):
        template_values = {"message": "CustomMainPage - GET handler for [%s]" % path}
        self.render('generic.htm', template_values)

    def Post(self, path):
        template_values = {"message": "CustomMainPage - POST handler for [%s]" % path}
        self.render('generic.htm', template_values)


class Alarmtimestamp(db.Model):
    alarm_datetime = db.DateTimeProperty(required=True)
    alarm_path = db.StringProperty(required=True)


class CustomAlarm(db.Model):
    alarm_path = db.StringProperty(required=True)
    user_login = db.StringProperty(required=True)
    user_pass = db.StringProperty(required=True)
    user_id = db.StringProperty(required=True)
    user_email = db.StringProperty(required=True)


app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/new', NewPage),
                               ('/(.+)/admin', AdminPage),
                               ('/(.+)/login', LoginPage),
                               ('/(.+)', CustomMainPage)
                               ],
                              debug=True)
