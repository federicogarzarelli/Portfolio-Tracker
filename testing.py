# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 20:34:14 2020

@author: fega
"""

import pandas as pd
from Database import Database
from PortfolioDB import PortfolioDB
import Stock as ST
import utils 
from datetime import datetime, date

databasePath = "MyPortfolio.db"

DEFAULT_DATE = str(date.today())
DEFAULT_STARTDATE = "1975-01-01"


MyPortfolioDB = PortfolioDB(databasePath)

EUR = ST.Stock("EUR", MyPortfolioDB)
EIMI = ST.Stock("EIMI", MyPortfolioDB)


print(EIMI.stockCode)
print(EIMI.numberOwned)
print(EIMI.amountSpent)
print(EIMI.totalDividend)
print(EIMI.currency)

     
