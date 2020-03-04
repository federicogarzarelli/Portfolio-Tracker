# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 20:34:14 2020

@author: fega
"""

import pandas as pd
from Database import Database

databasePath = "MyPortfolio.db"

db = Database(databasePath)

sqlQuery = "SELECT * FROM DIM_STOCKS LIMIT 10"

DIM_STOCKS = db.readDatabase(sqlQuery)

import stockDownloader as downloader
stockCode = "USD"
downloader.updateStockData(stockCode, db)