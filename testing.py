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

databasePath = "MyPortfolio.db"

DEFAULT_DATE = str(date.today())+ " 00:00:00"
DEFAULT_STARTDATE = "2020-01-01 00:00:00" #"1975-01-01 00:00:00"


MyPortfolioDB = PortfolioDB(databasePath)

EUR = Stock("EUR", MyPortfolioDB)
CHF = Stock("CHF", MyPortfolioDB)
USD = Stock("USD", MyPortfolioDB)
EIMI = Stock("EIMI", MyPortfolioDB)

print(EIMI.stockCode)
print(EIMI.numberOwned)
print(EIMI.amountSpent)
print(EIMI.totalDividend)
print(EIMI.currency)

EIMI.update()

print(EIMI.stockCode)
print(EIMI.numberOwned)
print(EIMI.amountSpent)
print(EIMI.totalDividend)
print(EIMI.currency)

EIMI.Profits_LossesRange(DEFAULT_STARTDATE, DEFAULT_DATE)
     
