# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 20:34:14 2020

@author: fega
"""

import pandas as pd
from Database import Database
import stockContract as SC
import Stock as ST
import stockDownloader as downloader
import utils 
import datetime

databasePath = "MyPortfolio.db"

database = Database(databasePath)

stockCode = "EUR"

EUR = ST.Stock(stockCode, database)
#SGLD.plot()


DEFAULT_DATE = str(datetime.date.today())
DEFAULT_STARTDATE = "1975-01-01"
SGLD.getCHFEUR(startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE)

