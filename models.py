__author__ = 'berend'
from google.appengine.ext import db

class Alarmtimestamp(db.Model):
    def __str__(self):
        return str(self.alarm_datetime)

    alarm_datetime = db.DateTimeProperty()
    prev_alarm = db.DateTimeProperty()