# -*- coding: utf-8 -*-
"""
Child class of database to obtain filtered tables of the portfolio database.

Created on Sun Mar  8 11:50:49 2020

@author: feder
"""

import utils
import pandas as pd
from datetime import datetime, timedelta, date
import yfinance as yf # https://aroussi.com/post/python-yahoo-finance
# pip install yfinance --upgrade --no-cache-dir
from Database import Database

###############
## Constants ##
###############
# utils.DEFAULT_DATE = str(date.today())+ " 00:00:00"
# utils.DEFAULT_STARTDATE = "1975-01-01 00:00:00"

class PortfolioDB(Database):
    
    # Filter transactions table FACT_TRANSACTIONS for a range of dates and tickers
    def getTransactions(self, tickers, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE, direction = "BOUGHT"):
        
        tickers_str = ""
        for ticker in tickers[:-1]:
            tickers_str = tickers_str + '"' + ticker + '", '
            
        tickers_str = tickers_str + '"' + tickers[-1] + '"'
        
        if direction == "BOUGHT":
            sqlQuery = '''
               	SELECT *
            	FROM FACT_TRANSACTIONS 
            	WHERE INSTRUMENT_BOUGHT in ({}) and datetime(DATE) BETWEEN date("{}") AND date("{}")
            	ORDER BY TRANSACTION_ID;     
            ''' \
                .format(tickers_str, startDate, endDate)
        elif direction == "SOLD":
            sqlQuery = '''
               	SELECT *
            	FROM FACT_TRANSACTIONS 
            	WHERE INSTRUMENT_SOLD in ({}) and datetime(DATE) BETWEEN date("{}") AND date("{}")
            	ORDER BY TRANSACTION_ID;     
            ''' \
                .format(tickers_str, startDate, endDate)
        else:
            raise ValueError("Invalid option provided")
        data = self.readDatabase(sqlQuery) 
        return data
    
    # Filter stock information table DIM_STOCKS for a range of tickers
    def getStockInfo(self, tickers):
        
        tickers_str = ""
        for ticker in tickers[:-1]:
            tickers_str = tickers_str + '"' + ticker + '", '
            
        tickers_str = tickers_str + '"' + tickers[-1] + '"'
        
        sqlQuery = '''
           	SELECT *
        	FROM DIM_STOCKS 
        	WHERE IB_TICKER in ({});     
        ''' \
            .format(tickers_str)
        data = self.readDatabase(sqlQuery) 
        return data
    
    # Filter historical prices table FACT_HISTPRICES for a range of dates and tickers
    def getPrices(self, tickers, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        
        tickers_str = ""
        for ticker in tickers[:-1]:
            tickers_str = tickers_str + '"' + ticker + '", '
            
        tickers_str = tickers_str + '"' + tickers[-1] + '"'
        
        sqlQuery = '''
           	SELECT *
        	FROM FACT_HISTPRICES 
        	WHERE IB_TICKER in ({}) and datetime(DATE) BETWEEN date("{}") AND date("{}")
        	ORDER BY IB_TICKER, DATE;     
        ''' \
            .format(tickers_str, startDate, endDate)
        data = self.readDatabase(sqlQuery)
        data[self.DATE] = pd.to_datetime(data[self.DATE], format = '%Y-%m-%d %H:%M:%S')
        return data
    

    # Filter historical dividends table FACT_DIVIDENDS for a range of dates and tickers
    def getDividends(self, tickers, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        
        tickers_str = ""
        for ticker in tickers[:-1]:
            tickers_str = tickers_str + '"' + ticker + '", '
            
        tickers_str = tickers_str + '"' + tickers[-1] + '"'
        
        sqlQuery = '''
           	SELECT *
        	FROM FACT_DIVIDENDS 
        	WHERE IB_TICKER in ({}) and datetime(DIVIDEND_DATE) BETWEEN date("{}") AND date("{}")
        	ORDER BY IB_TICKER, DIVIDEND_DATE;     
        ''' \
            .format(tickers_str, startDate, endDate)
        data = self.readDatabase(sqlQuery) 
        return data
    
    # Checks whether stock is in database, if not it stockScrape to get all the data.
    # If it is in data base it checks whether the stock information is up to date and only fetches new data
    def updateStockData(self, stockCode):
        # Reads database
        sqlQuery = """SELECT {} FROM {} WHERE {} = '{}'; """ \
        .format(self.IB_TICKER, self.HISTORICAL_TABLE_NAME, self.IB_TICKER, stockCode)
        
    #    print(sqlQuery)
        stockData = self.readDatabase(sqlQuery)
               
        # Checks whether any previous data has been added for the particular stock code
        # if not then run initialStockScrape to get all past data
        if stockData.empty:
            print('Running stockScrape() on {}. --First run.'.format(stockCode))
            self.stockScrape(stockCode)
        else:
            #access database to get latestDate
            print('Running stockScrape() on {}. --Updating data.'.format(stockCode))
            # Performs SQL query to get the latest stock data date in database
            sqlQuery = """SELECT {}, max({}) AS Date FROM {} WHERE {} = '{}' GROUP BY {}""" \
            .format(self.IB_TICKER, self.DATE, self.HISTORICAL_TABLE_NAME, self.IB_TICKER, stockCode, self.IB_TICKER)
            
            y = self.readDatabase(sqlQuery)  
            minDate = y.Date[0]    # minDate is the earliest data of data that the program needs to download
            # Increment date by 1 day
            minDate = utils.incrementDate(minDate)
            
            if utils.convertDate(minDate) < datetime.today():
                # Updates stock data
                self.stockScrape(stockCode, minDate)
            else:
                # Data are already up to date
                print("Data for {} are already up to date. Module: updateStockData.".format(stockCode))            
        
    def getYahooCode(self, stockCode):
            sqlQuery = ''' SELECT {} FROM {} WHERE {} = '{}' ''' \
                .format(self.YAHOO_SYMBOL, self.STOCKS_TABLE_NAME,
                        self.IB_TICKER, stockCode)
            data = self.readDatabase(sqlQuery)
            # If data is empty return 0
            if data.empty:
                print(('No Yahoo Symbol for {}. Module: getYahooCode.'.format(stockCode)))
                return 0
            return data.at[0, self.YAHOO_SYMBOL]
        
    # function which does the first time initialization of the stock and 
    #downloads all past stock data, returns array of dates, and array of data
    def stockScrape(self, stockCode, minDate = utils.DEFAULT_STARTDATE):
        # Initialize pandas dataframe to hold stock data    
        stockDataFrame =  pd.DataFrame({self.DATE: [], self.IB_TICKER: [], self.PRICE: []});

        if stockCode == 'EUR':
            sdate = utils.convertDate(minDate)  # start date
            edate = datetime.now()
            edate = edate.replace(hour=0, minute=0, second=0, microsecond=0) # end date
            
            delta = edate - sdate       # as timedelta
            
            for i in range(delta.days + 1):
                day = sdate + timedelta(days=i)
                day = datetime.combine(day, datetime.min.time())
                stockDataFrame.loc[i] = [day] + ['EUR'] + [1] 
        else:
         
            YahooCode = self.getYahooCode(stockCode)
            stock = yf.Ticker(YahooCode)
            
            sdate = utils.convertDate(minDate)  # start date
            dowloaded_data = stock.history(interval="1d", start = sdate)
        
            # Manipulate the output
            Dates = dowloaded_data.index.to_frame()
            Dates = Dates.reset_index(drop=True)
            
            Price = dowloaded_data['Close'].reset_index(drop=True)
                
            Ticker = pd.DataFrame([stockCode] * len(dowloaded_data['Close']),columns=['Ticker'])
            
            stockDataFrame =  pd.concat([Dates, Ticker, Price], axis = 1)
        
        stockDataFrame.columns = self.HISTORICAL_COLUMNS
        stockDataFrame.ignore_index=True
               
        # Add to SQL database
        self.addToDatabase(stockDataFrame, self.HISTORICAL_TABLE_NAME)
    
    # DB Names
    
    ## Transactions table
    
    # Table Name
    TRANSACTIONS_TABLE_NAME = "FACT_TRANSACTIONS"
    
    # Table Columns
    TRANSACTION_ID = "TRANSACTION_ID"
    DATE = "DATE"
    INSTRUMENT_BOUGHT = "INSTRUMENT_BOUGHT"
    QUANTITY_BOUGHT = "QUANTITY_BOUGHT"
    INSTRUMENT_SOLD = "INSTRUMENT_SOLD"
    QUANTITY_SOLD = "QUANTITY_SOLD"
    COMMISSION = "COMMISSION"
    
    # Calculated fields
    TOTAL_SOLD = "TOTAL_SOLD"
    TOTAL_BOUGHT = "TOTAL_BOUGHT"
    TOTAL_OWNED = "TOTAL_OWNED"
    
    TRANSACTIONS_COLUMNS = [TRANSACTION_ID, DATE, INSTRUMENT_BOUGHT, QUANTITY_BOUGHT, INSTRUMENT_SOLD, QUANTITY_SOLD, COMMISSION]
    TRANSACTIONS_COLUMN_LIST = "{} DATE,{} TEXT,{} REAL,{} TEXT,{} REAL,{} REAL".format(TRANSACTION_ID, DATE, INSTRUMENT_BOUGHT, QUANTITY_BOUGHT, INSTRUMENT_SOLD, QUANTITY_SOLD, COMMISSION)
    
    ## Information about the stocks
    # Table Name
    STOCKS_TABLE_NAME = "DIM_STOCKS"
    
    # Table Columns
    NAME = "NAME"
    IB_TICKER = "IB_TICKER"
    IB_EXCHANGE = "IB_EXCHANGE"
    IB_CURRENCY = "IB_CURRENCY"
    ISIN = "ISIN"
    LINK_1 = "LINK_1"
    LINK_2 = "LINK_2"
    ICTAX_LINK = "ICTAX_LINK"
    FUND_DOMICILE = "FUND_DOMICILE"
    GOOGLE_FINANCE_SYMBOL = "GOOGLE_FINANCE_SYMBOL"
    YAHOO_SYMBOL = "YAHOO_SYMBOL"
    YAHOO_CURRENCY = "YAHOO_CURRENCY"
    
    STOCKS_COLUMNS = [NAME, IB_TICKER, IB_EXCHANGE, IB_CURRENCY, ISIN, LINK_1, LINK_2, ICTAX_LINK, FUND_DOMICILE, GOOGLE_FINANCE_SYMBOL, YAHOO_SYMBOL, YAHOO_CURRENCY]
    
    STOCKS_COLUMN_LIST = "{} TEXT, {} TEXT, {} TEXT, {} TEXT, {} TEXT, {} TEXT, {} TEXT, {} TEXT, {} TEXT, {} TEXT, {} TEXT, {} TEXT".format( NAME, IB_TICKER, IB_EXCHANGE, IB_CURRENCY, ISIN, LINK_1, LINK_2, ICTAX_LINK, FUND_DOMICILE, GOOGLE_FINANCE_SYMBOL, YAHOO_SYMBOL, YAHOO_CURRENCY)
    
    ## Historical prices table
    # Table Name
    HISTORICAL_TABLE_NAME = "FACT_HISTPRICES"
    
    DATE = "DATE"
    IB_TICKER = "IB_TICKER"
    PRICE = "PRICE"
    
    HISTORICAL_COLUMNS = [DATE, IB_TICKER, PRICE]
    
    HISTORICAL_COLUMN_LIST = "{} DATE, {} TEXT, {} REAL".format(DATE, IB_TICKER, PRICE)
    
    ## Dividends data table contract
    # Table Name
    DIVIDEND_TABLE_NAME = "FACT_DIVIDENDS"
    
    # Table Columns
    DIVIDEND_DATE = "DIVIDEND_DATE"    
    IB_TICKER = "IB_TICKER"    
    DIVIDEND_AMOUNT = "DIVIDEND_AMOUNT"    
           
    DIVIDEND_TOTAL = "DIVIDEND_TOTAL" 
    
    DIVIDEND_COLUMNS = [DIVIDEND_DATE, IB_TICKER, DIVIDEND_AMOUNT]  
       
    DIVIDEND_COLUMN_LIST =  "{} DATE, {} TEXT, {} REAL".format(DIVIDEND_DATE,  IB_TICKER,  DIVIDEND_AMOUNT)