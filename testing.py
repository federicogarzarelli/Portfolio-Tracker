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


databasePath = "MyPortfolio.db"

database = Database(databasePath)

stockCode = "SGLD"

SGLD = ST.Stock(stockCode, database)
SGLD.plot()