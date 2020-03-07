# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 16:40:36 2020

@author: fega
"""
from datetime import date, timedelta, datetime

# Converts a date in "yyyy-mm-dd" format to a dateTime object
def convertDate(dateString):
    [year, month, day] = map(int, dateString.split("-"))
    return date(year, month, day)

# Takes in a date in the format "yyyy-mm-dd hh:mm:ss" and increments it by one day. Or if the 
# day is a Friday, increment by 3 days, so the next day of data we get is the next
# Monday.
def incrementDate(dateString):
   
    dateTime = datetime.strptime(dateString, '%Y-%m-%d %H:%M:%S').date()
    # If the day of the week is a friday increment by 3 days.
    if dateTime.isoweekday() == 5:
        datePlus = dateTime + timedelta(3)
    else:
        datePlus = dateTime + timedelta(1)
    return str(datePlus)

# Takes in a date in the format "yyyy-mm-dd" and decrements it by one day. 
def decrementDate(dateString):
    [year, month, day] = dateString.split("-")
    dateTime = datetime.date(int(year), int(month), int(day))
    dateMinus = dateTime - datetime.timedelta(1)
    return str(dateMinus)
    