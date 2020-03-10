# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 20:34:14 2020

@author: fega
"""

import pandas as pd
from Database import Database
from PortfolioDB import PortfolioDB
from stock import Stock
import utils 
from datetime import datetime, date
from GoogleSheetData import getGoogleSheetData
import GoogleSheetData 

databasePath = "MyPortfolio.db"

DEFAULT_DATE = str(date.today())+ " 00:00:00"
DEFAULT_STARTDATE = "2020-01-01 00:00:00" #"1975-01-01 00:00:00"

#googledatatable = getGoogleSheetData(GoogleSheetData.SAMPLE_SPREADSHEET_ID, GoogleSheetData.SAMPLE_RANGE_NAME)
googledatatable = pd.read_csv(r"C:\Users\fega\Desktop\googledatatable.csv")
MyPortfolioDB = PortfolioDB(databasePath, googledatatable)

CHF = Stock("CHF", MyPortfolioDB)
USD = Stock("USD", MyPortfolioDB)
EUR = Stock("EUR", MyPortfolioDB)
EIMI = Stock("EIMI", MyPortfolioDB)

print(EUR.stockCode)
print(EUR.numberOwned)
print(EUR.amountSpent)
print(EUR.totalDividend)
print(EUR.currency)

EUR.update()

print(EUR.stockCode)
print(EUR.numberOwned)
print(EUR.amountSpent)
print(EUR.totalDividend)
print(EUR.currency)

EUR.Profits_LossesRange(DEFAULT_STARTDATE, DEFAULT_DATE)
CHF.Profits_LossesRange(DEFAULT_STARTDATE, DEFAULT_DATE)  
USD.Profits_LossesRange(DEFAULT_STARTDATE, DEFAULT_DATE)  