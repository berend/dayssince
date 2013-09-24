__author__ = 'berend'
from datetime import datetime
from datetime import timedelta
from models import Alarmtimestamp

def createAlarm(user_date, user_time, user_utc_offset):
    utc_offset = int(user_utc_offset[3:])

    if user_date == '' and user_time == '':
        return Alarmtimestamp(alarm_datetime=(datetime.utcnow()+ timedelta(minutes=60*utc_offset)))
    else:
        try:
            #dd.mm.yyyy hh:mm
            user_datetime = datetime.strptime(user_date + ' ' + user_time,'%d.%m.%Y %H:%M')

            #add timezone
            user_datetime = user_datetime + timedelta(minutes=60*utc_offset)
            return Alarmtimestamp(alarm_datetime=user_datetime)

        except ValueError:
            message = "Error with date/time format"
