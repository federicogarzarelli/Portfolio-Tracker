# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 16:40:36 2020

@author: fega
"""


from datetime import date, timedelta, datetime

DEFAULT_DATE = str(date.today())+ " 00:00:00"
DEFAULT_STARTDATE = "2020-01-01 00:00:00" #"1975-01-01 00:00:00"

# Converts a date in "yyyy-mm-dd" format to a dateTime object
def convertDate(dateString):
   return datetime.strptime(dateString, '%Y-%m-%d %H:%M:%S')

# Takes in a date in the format "yyyy-mm-dd hh:mm:ss" and increments it by one day. Or if the 
# day is a Friday, increment by 3 days, so the next day of data we get is the next
# Monday.
def incrementDate(dateString):
    dateTime = datetime.strptime(dateString, '%Y-%m-%d %H:%M:%S')
    # If the day of the week is a friday increment by 3 days.
    if dateTime.isoweekday() == 5:
        datePlus = dateTime + timedelta(3)
    else:
        datePlus = dateTime + timedelta(1)
    return str(datePlus)