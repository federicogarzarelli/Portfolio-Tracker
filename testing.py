# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 20:34:14 2020

@author: fega
"""

import pandas as pd
from Database import Database
import Stock as ST
import utils 
import datetime
import PortfolioDB

databasePath = "MyPortfolio.db"

stockCode = "EUR"

DEFAULT_DATE = str(datetime.date.today())
DEFAULT_STARTDATE = "1975-01-01"


MyPortfolioDB = PortfolioDB(databasePath)
EUR = ST.Stock(stockCode, MyPortfolioDB)
##SGLD.plot()
#
#
#EUR.getCHFEURRange(startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE)




# Test PortfolioDB

#tickers = ["CHF", "EIMI", "IDJV"]
#startDate = DEFAULT_STARTDATE
#endDate = DEFAULT_DATE
#
#
#
#trans = MyPortfolioDB.getTransactions(tickers, startDate, endDate)
#StockInfo = MyPortfolioDB.getStockInfo(tickers)
#Prices = MyPortfolioDB.getPrices(tickers, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE)
#Dividends = MyPortfolioDB.getDividends(tickers, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE)

minDate = "1975-01-01"

    
     
