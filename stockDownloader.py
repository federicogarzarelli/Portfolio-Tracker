#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""                  stockDownloader.py       
Created on Tue Nov 29 11:28:12 2016

@author: hplustech

@author: fega

Modified 04/03/2020:
    * Now use yfinance to download the data
"""

import stockContract as SC
import pandas as pd
from datetime import datetime, timedelta

import yfinance as yf # https://aroussi.com/post/python-yahoo-finance
# pip install yfinance --upgrade --no-cache-dir
    
#takes a date input as a list of strings in the format 'mmm d, yyyy' and converts it to
#yyyy-mm-dd
def convertDate(dateString):
    # a dictionary to convert months to a number
    monthDict = {'Jan': '01', 'Feb':'02', 'Mar':'03','Apr':'04','May':'05','Jun':'06',
    'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    
    for n in range(len(dateString)):
        #splits the string
        splitDate = re.split('\W+',dateString[n])
        # cconverts the date into date object
        dateString[n] = datetime.date(int(splitDate[2]),int(monthDict[splitDate[1]]),int(splitDate[0])).isoformat() #y,m,d
    return dateString


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
    
    
# Checks whether stock is in database, if not it stockScrape to get all the data.
# If it is in data base it checks whether the stock information is up to date and only fetches new data
def updateStockData(stockCode, database):
    # Reads database
    sqlQuery = """SELECT {} FROM {} WHERE {} = '{}'; """ \
    .format(SC.IB_TICKER, SC.HISTORICAL_TABLE_NAME, SC.IB_TICKER, stockCode)
    
#    print(sqlQuery)
    stockData = database.readDatabase(sqlQuery)
           
    # Checks whether any previous data has been added for the particular stock code
    # if not then run initialStockScrape to get all past data
    if stockData.empty:
        print('Running stockScrape() on {}. --First run.'.format(stockCode))
        stockScrape(stockCode, database)
    else:
        #access database to get latestDate
        print('Running stockScrape() on {}. --Updating data.'.format(stockCode))
        # Performs SQL query to get the latest stock data date in database
        sqlQuery = """SELECT {}, max({}) AS Date FROM {} WHERE {} = '{}' GROUP BY {}""" \
        .format(SC.IB_TICKER, SC.DATE, SC.HISTORICAL_TABLE_NAME, SC.IB_TICKER, stockCode, SC.IB_TICKER)
        
        y = database.readDatabase(sqlQuery)  
        minDate = y.Date[0]    # minDate is the earliest data of data that the program needs to download
        # Increment date by 1 day
        minDate = incrementDate(minDate)
        
        # Updates stock data
        stockScrape(stockCode, database, minDate)                     
    
def getYahooCode(stockCode, database):
        sqlQuery = ''' SELECT {} FROM {} WHERE {} = '{}' ''' \
            .format(SC.YAHOO_SYMBOL, SC.STOCKS_TABLE_NAME,
                    SC.IB_TICKER, stockCode)
        data = database.readDatabase(sqlQuery)
        # If data is empty return 0
        if data.empty:
            print(('No Yahoo Symbol for {}.'.format(stockCode)))
            return 0
        return data.get_value(0, SC.YAHOO_SYMBOL)   
    
# function which does the first time initialization of the stock and 
#downloads all past stock data, returns array of dates, and array of data
def stockScrape(stockCode, database, minDate = '1975-01-01'):
    # Initialize pandas dataframe to hold stock data    
    stockDataFrame =  pd.DataFrame({SC.DATE: [], SC.IB_TICKER: [], SC.PRICE: []});
 
    YahooCode = getYahooCode(stockCode, database)
    stock = yf.Ticker(YahooCode)

    dowloaded_data = stock.history(interval="1d", start = minDate)

    # Manipulate the output
    Dates = dowloaded_data.index.to_frame()
    Dates = Dates.reset_index(drop=True)
    
    Price = dowloaded_data['Close'].reset_index(drop=True)
        
    Ticker = pd.DataFrame([stockCode] * len(dowloaded_data['Close']),columns=['Ticker'])
    
    stockDataFrame =  pd.concat([Dates, Ticker, Price], axis = 1)
    stockDataFrame.columns = SC.HISTORICAL_COLUMNS
    stockDataFrame.ignore_index=True
           
    # Add to SQL database
    database.addToDatabase(stockDataFrame, SC.HISTORICAL_TABLE_NAME)
    
    
## Testing code
#testPath = 'C:/Users/feder/Google Drive/Work/Portfolio Tracker/Code Repo/MyPortfolio.db'
#testDB = Database(testPath) 
#testDB.createTable(SC.HISTORICAL_TABLE_NAME, SC.HISTORICAL_COLUMN_LIST)
#updateStockData("CHF", testDB)
##stockScrape("IJR.AX", testDB, "1990-11-10")
#print(testDB.readDatabase('''SELECT * FROM {}'''.format(SC.HISTORICAL_TABLE_NAME)))