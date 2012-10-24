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


import os
# import logging
import utils
import webapp2

from utils import BaseHandler
from google.appengine.api import memcache
from google.appengine.ext import db
from datetime import datetime
# from time import strftime


DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Developement')


class FrontPage(BaseHandler):
    def get(self):
        self.render('frontpage.htm', {})


class AdminPage(BaseHandler):
    def get(self, path):
        if self.user_id:
            message = "Leave empty to set to (now)"
            template_values = {"message": message}
            self.render('reset.htm', template_values)
        else:
            self.redirect("/%s/login" % path)

    def post(self, path):
        if self.user_id:
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
        else:
            self.redirect("/%s/login" % path)


class NewPage(BaseHandler):
    def get(self):
        template_values = {"isAvailable": False}
        self.render('new.htm', template_values)

    def post(self):
        user_availhash = self.request.get('availhash')
        user_custompath = self.request.get('custompath')
        q = db.GqlQuery("SELECT * from Alarmtimestamp")
        q = list(q)
        template_values = {"message": "New Page - POST handler"}
        self.render('new.htm', template_values)


class NewUser(BaseHandler):
    def get(self):
        template_values = {"submit_error": False}
        self.render('newuser.htm', template_values)

    def post(self):
        user_login = self.request.get('login')
        user_yourname = self.request.get('yourname')
        user_password = self.request.get('password')
        user_password_repeat = self.request.get('password_repeat')
        user_email = self.request.get('email')

        if user_password != user_password_repeat:
            template_values = {"error_message": "Passwords don't match!", "submit_error": True}
            self.render('newuser.htm', template_values)
        elif user_password == "":
            template_values = {"error_message": "Passwords are empty!", "submit_error": True}
            self.render('newuser.htm', template_values)
        elif User.get_by_key_name(user_login):
            template_values = {"error_message": "Username is already taken!", "submit_error": True}
            self.render('newuser.htm', template_values)
        else:
            #no error, create new user!
            pw_hash = utils.hash_pw_for_db(user_password)
            user_cookie = utils.make_cookie(user_login)

            new_user = User(key_name=user_login, yourname=user_yourname, password=pw_hash, email=user_email)
            new_user.put()

            #login new user by creating cookie and display sucess web page
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(user_cookie))
            self.render('new_user_created.htm', {})


class CustomMainPage(BaseHandler):
    def get(self, path):
        template_values = {"message": "CustomMainPage - GET handler for [%s]" % path}
        self.render('generic.htm', template_values)

    def post(self, path):
        user_custompath = self.request.get('custompath')
        user_hidden_hash = self.request.get('availhash')

        utils.check_custom_path_hash(user_custompath, user_hidden_hash)
        template_values = {"message": "CustomMainPage - POST handler for [%s]" % path}
        self.render('generic.htm', template_values)


class LoginPage(BaseHandler):
    def get(self, path):
        template_values = {"message": "LoginPage - GET handler for [%s]" % path}
        self.render('generic.htm', template_values)

    def post(self, path):
        template_values = {"message": "LoginPage - GET handler for [%s]" % path}
        self.render('generic.htm', template_values)


class Alarmtimestamp(db.Model):
    alarm_datetime = db.DateTimeProperty(required=True)
    alarm_path = db.StringProperty(required=True)


class CustomAlarm(db.Model):
    alarm_path = db.StringProperty(required=True)


class User(db.Model):
    #user_login is going into the key, when creating and referencing users
    yourname = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()

app = webapp2.WSGIApplication([('/', FrontPage),
                               ('/new', NewPage),
                               ('/newuser', NewUser),
                               ('/(.+)/admin', AdminPage),
                               ('/(.+)/login', LoginPage),
                               ('/(.+)', CustomMainPage)
                               ],
                              debug=True)
