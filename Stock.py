#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""                       Stock.py
Created on Fri Nov 25 11:32:32 2016

@author: dmcauslan

Stock class that contains the information
- Number owned
- Total cost
- Stock Code
- Currency
And has a buy method that is used to buy that stock

Modified 29/11/2016:
    * implemented getOwned() method.
    * Stock class now takes as an input the database to save the data in.
    * created stockDownloader.py to help with downloading stock data.
    * stockDownloader stockScrape method works so far. The other methods 
    (in particular stockUpdate) need to be tested.
Modified 30/11/2016:
    * Class now downloads all past stock price data on initialization. Or
    alternatively, if the stock has been added to the database previously, it
    updates the database with the most recent data.
    * Implemented getPrice() and getValue() methods to get the price of the stock
    on a particular date, and the total value of the stock on a particular date.
    * Implemented getPriceRange() method which gets the price of the stock over a
    range of dates.
    * Implemented getValueRange() method which gets a data frame containing Date,
    Total_Owned and Total_Value for a range of dates.
Modified 01/12/2016:
    * Implemented sell() method for selling some of the stock.
    * Implemented remove() method for removing a transaction from the database
    (incase you made an error when adding it)
    * Fixed getValueRange() method so that it works with selling.
    * Removed TOTAL_OWNED column from database as it calculates incorrectly
    when purchases are not added in date order. TOTAL owned column can easily be
    generated in SQL using SUM(NUMBER_PURCHASED) AS TOTAL_OWNED.
    * Split getValueRange() method into getOwnedRange() and getValueRange() methods.
    * Implemented plot method which plots date vs total value, number owned, stock price and profit.
    * Implemented getSpentRange() method which calculates the amount spent over a
    range of dates.
    * Modified contstructor so that it gets the total number of shares owned and
    total amount spent from the data base on initializaiton.
Modified 02/12/2016:
    * Added addDividend(), removeDividend() and getDividend() methods, which add
    a dividend payment to the database, remove a dividend payment from the database, 
    and retrieve the total amount of dividends recieved up until a date respectively.
    * Updated str method to include dividend data.
Modified 05/12/2016:
    * Added getDividendRange() method.
    * Updated plot() method to include plotting dividends.

@author: fega

Modified 04/03/2020:
    * Added currency attribute
    * Added functions getBought and getSold that feed into getOwned
    * Modified getPrice 
    * Added getPricePaid and getCommissions that feed into getSpent. These functions replace the previous implementation of getSpent that did
      not take into account commission nor currency conversion. 
    
"""
import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import urllib.request

###############
## Constants ##
###############
DEFAULT_DATE = str(datetime.date.today())
DEFAULT_STARTDATE = "1975-01-01"

# Class for holding the information of an individual stock.
# Parameters:   numberOwned
#               totalCost
#               stockCode
#               dataBase
#               totalDividend
class Stock:
    numberOwned = 0
    totalCost = 0
    totalDividend = 0
      
    # Class initializer
    def __init__(self, stockCode, database):
      self.stockCode = stockCode
      self.database = database
      # Updates the database with any price data that it does not have.
      try:
          self.database.updateStockData(self.stockCode)
      except urllib.request.URLError:
          print("{} data not updated. URL Error.".format(self.stockCode))
      
      # Updates the numberOwned, totalCost and totalDividend values
      numOwned = self.getOwned()
      if numOwned != None:
          self.numberOwned = numOwned
      amountSpent = self.getSpent()
      if amountSpent != None:
          self.totalCost = amountSpent
      dividend = self.getDividend()
      if dividend != None:
          self.totalDividend = dividend
      currency = self.getCurrency()
      if currency != None:
          self.currency = currency
    
    # Class string method
    def __str__(self):
         return "{} - number owned: {}, total cost: ${:.2f}, total dividend: ${:.2f}." \
                .format(self.stockCode, self.numberOwned, self.totalCost, self.totalDividend)


    # Buy a number of stocks at a price and save in the database
    def buy(self, quantity_bought, instrument_sold, quantity_sold, commission, date = DEFAULT_DATE):
        self.numberOwned += quantity_bought
        #self.totalCost += quantity_bought*price  # to update
        purchaseData = pd.DataFrame({self.database.DATE: [date],
                                     self.database.INSTRUMENT_BOUGHT: [self.stockCode],
                                     self.database.QUANTITY_BOUGHT: [quantity_bought],
                                     self.database.INSTRUMENT_SOLD: [instrument_sold],
                                     self.database.QUANTITY_SOLD: quantity_sold,
                                     self.database.COMMISSION: [commission]})
        self.database.addToDatabase(purchaseData, self.database.TRANSACTIONS_TABLE_NAME)
    
    # Sell a number of stocks at a price and save in the database     
    def sell(self, quantity_bought, instrument_bought, quantity_sold, commission, date = DEFAULT_DATE):
        self.numberOwned -= quantity_sold
        #self.totalCost += quantity_bought*price  # to update
        purchaseData = pd.DataFrame({self.database.DATE: [date],
                                     self.database.INSTRUMENT_BOUGHT: [instrument_bought],
                                     self.database.QUANTITY_BOUGHT: [quantity_bought],
                                     self.database.INSTRUMENT_SOLD: [self.stockCode],
                                     self.database.QUANTITY_SOLD: quantity_sold,
                                     self.database.COMMISSION: [commission]})
        self.database.addToDatabase(purchaseData, self.database.TRANSACTIONS_TABLE_NAME)
    
    # Adds a dividend payment to the dividend database table
    def addDividend(self, payment, date = DEFAULT_DATE):
        self.totalDividend += payment
        dividendData = pd.DataFrame({self.database.DIVIDEND_DATE: [date],
                                     self.database.IB_TICKER: [self.stockCode],
                                     self.database.DIVIDEND_AMOUNT: [payment]})
        self.database.addToDatabase(dividendData, self.database.DIVIDEND_TABLE_NAME)        
    
    # Removes a divident payment from the dividend database table
    def removeDividend(self, payment, date):
        self.totalDividend -= payment
        sqlCommand = '''DELETE FROM {} 
            WHERE {} LIKE '{}'
            AND {} == {}
            AND {} == date("{}")''' \
            .format(self.database.DIVIDEND_TABLE_NAME, 
                    self.database.IB_TICKER, self.stockCode,
                    self.database.DIVIDEND_AMOUNT, payment,
                    self.database.DIVIDEND_DATE, date)
        rowsRemoved = self.database.executeCommand(sqlCommand)
        
        # Check whether the data removal was succesful. If not, user most likely
        # made an input error, so throw a ValueError so they know about it.
        if rowsRemoved == 0:
            self.totalDividend += payment
            raise ValueError("Dividend payment of ${} was not in database. Module: removeDividend.".format(payment, date))
    
    # Get the number of the stock owned at date. Default date is today.
    def getOwned(self, date = DEFAULT_DATE):
        self.database.TOTAL_OWNED = self.getBought(date) - self.getSold(date)
        return self.database.TOTAL_OWNED
        
    # Get the number of the stock sold at date. Default date is today.
    def getSold(self, date = DEFAULT_DATE):
        data  = self.database.getTransactions([self.stockCode], startDate = DEFAULT_STARTDATE, endDate = date)
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getSold.'.format(date))
            return 0
        return sum(data[self.database.QUANTITY_SOLD])

   # Get the number of the bought sold at date. Default date is today.
    def getBought(self, date = DEFAULT_DATE):
        data  = self.database.getTransactions([self.stockCode], startDate = DEFAULT_STARTDATE, endDate = date)
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getBought.'.format(date))
            return 0
        return data.at[0, self.database.QUANTITY_BOUGHT]
               
    # Get the total spent as price paid + commissions
    def getSpent(self, date = DEFAULT_DATE):
        return self.getPricePaid(date) * self.getCommissions(date)
    
     # Get the total price paid in Euros for a stock. Default date is today.
    def getPricePaid(self, date = DEFAULT_DATE):
        cost  = self.database.getTransactions([self.stockCode], startDate = DEFAULT_STARTDATE, endDate = date)
        cost = cost.sort_values(by=['DATE', 'INSTRUMENT_SOLD'], ascending = True)
        cost['DATE'] = pd.to_datetime(cost['DATE'], infer_datetime_format=True)
        
        tickers_list = cost['INSTRUMENT_SOLD'].drop_duplicates().values.tolist()
        
        price = self.database.getPrices(tickers_list, startDate = DEFAULT_STARTDATE, endDate = date)
        price = price.sort_values(by=['DATE', 'IB_TICKER'], ascending = True)
        price.columns = ['DATE', 'INSTRUMENT_SOLD', 'PRICE_INSTRUMENT_SOLD']
        
        currencies = self.getCurrency(tickers_list)
        currencies['INSTRUMENT_SOLD'] = tickers_list
        
        price_curr = pd.merge(price, currencies, how = 'left', on = 'INSTRUMENT_SOLD') 
        
        # Transform DATE to datetime and merge the commission date to the previous available date 
        price_curr['DATE'] = pd.to_datetime(price_curr['DATE'], infer_datetime_format=True)
        
        tickers_list = price_curr['YAHOO_CURRENCY'].drop_duplicates().values.tolist()
        priceYAHOOCURR = self.database.getPrices(tickers_list, startDate = DEFAULT_STARTDATE, endDate = date)
        priceYAHOOCURR['DATE'] = pd.to_datetime(priceYAHOOCURR['DATE'], infer_datetime_format=True)
        priceYAHOOCURR = priceYAHOOCURR.sort_values(by=['DATE', 'IB_TICKER'], ascending = True)
        priceYAHOOCURR.columns = ['DATE', 'YAHOO_CURRENCY', 'PRICE_YAHOO_CURRENCY']
        price_curr2 = pd.merge_asof(price_curr, priceYAHOOCURR, on='DATE', by='YAHOO_CURRENCY')
        
        cost_price_curr2 = pd.merge_asof(cost, price_curr2, on='DATE', by='INSTRUMENT_SOLD')
        cost_price_curr2['PRICEPAID_EUR'] =  cost_price_curr2['QUANTITY_SOLD'] *  cost_price_curr2['PRICE_INSTRUMENT_SOLD'] * cost_price_curr2['PRICE_YAHOO_CURRENCY']
        return sum(cost_price_curr2['PRICEPAID_EUR'])
              
    # Get the total commissions paid in Euros for a stock. Default date is today.
    def getCommissions(self, date = DEFAULT_DATE):
        commissionsCHF  = self.database.getTransactions([self.stockCode], startDate = DEFAULT_STARTDATE, endDate = date)
        commissionsCHF = commissionsCHF.sort_values(by=['DATE'], ascending = True)
        
        # Get the CHFEUR rates to convert the commissions to EUR              
        CHFEUR = self.database.getPrices("CHF", startDate = DEFAULT_STARTDATE, endDate = date)
        CHFEUR = CHFEUR.sort_values(by=['DATE'], ascending = True)

        # Transform DATE to datetime and merge the commission date to the previous available date 
        commissionsCHF['DATE'] = pd.to_datetime(commissionsCHF['DATE'], infer_datetime_format=True)
        CHFEUR['DATE'] = pd.to_datetime(CHFEUR['DATE'], infer_datetime_format=True)
               
        commissionsCHF_L_CHFEUR = pd.merge_asof(commissionsCHF, CHFEUR, on='DATE')
        commissionsCHF_L_CHFEUR['COMMISSION_EUR'] = commissionsCHF_L_CHFEUR['COMMISSION'] * commissionsCHF_L_CHFEUR['PRICE']
        
        # If data is empty return 0
        if commissionsCHF_L_CHFEUR.empty:
            print('No commissions for dates up to {}. Method: Stock.getCommissions2.'.format(date))
            return 0
        return sum(commissionsCHF_L_CHFEUR['COMMISSION_EUR'])

    # Get the price of the stock at date. Default date is today.
    def getPrice(self, date = DEFAULT_DATE):
        sqlQuery = ''' SELECT {} FROM {}
            WHERE {} LIKE '{}'
            AND {} LIKE '{}' ''' \
            .format(self.database.PRICE, self.database.HISTORICAL_TABLE_NAME, 
                    self.database.IB_TICKER, self.stockCode, 
                    self.database.DATE, date)
        data = self.database.readDatabase(sqlQuery)
        # If data is empty raise ValueError
        if data.empty:
            raise ValueError(('No price data for {}. Method: Stock.getPrice.'.format(date)))
        return data.at[0, self.database.PRICE]

    # get the total value of the stock at date. Default date is today.
    def getValue(self, date = DEFAULT_DATE):
        return self.getOwned(date) * self.getPrice(date)
        
    # Get the total amount of dividend payments at date.
    def getDividend(self, date = DEFAULT_DATE):
        sqlQuery = ''' SELECT SUM({}) AS {} FROM {}
            WHERE {} LIKE '{}'
            AND {} <= date("{}") ''' \
            .format(self.database.DIVIDEND_AMOUNT, self.database.DIVIDEND_TOTAL, self.database.DIVIDEND_TABLE_NAME,
                    self.database.IB_TICKER, self.stockCode,
                    self.database.DIVIDEND_DATE, date)
        data = self.database.readDatabase(sqlQuery)
        # If data is empty return 0
        if data.empty:
            print(('No dividend data for {}. Method: Stock.getDividend.'.format(date)))
            return 0
        return data.at[0, self.database.DIVIDEND_TOTAL]

    # Get the currency (YAHOO_CURRENCY) of the stock.
    def getCurrency(self, tickers):
        tickers_str = ""
        for ticker in tickers[:-1]:
            tickers_str = tickers_str + '"' + ticker + '", '
            
        tickers_str = tickers_str + '"' + tickers[-1] + '"'
        
        sqlQuery = ''' SELECT {} FROM {} WHERE {} in ({})''' \
            .format(self.database.YAHOO_CURRENCY, self.database.STOCKS_TABLE_NAME,
                    self.database.IB_TICKER, tickers_str)
        data = self.database.readDatabase(sqlQuery)
        # If data is empty return 0
        if data.empty:
            print(('No currency for {}. Method: Stock.getCurrency.'.format(tickers_str)))
            return 0
        return data
       
#################### to update ##############################
    # Get a data frame containing the price of the stock over a range of dates    
    def getPriceRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        sqlQuery = ''' SELECT {}, {} FROM {}
            WHERE {} LIKE '{}'
            AND {} BETWEEN date("{}") AND date("{}") 
            ORDER BY {} ASC''' \
            .format(self.database.DATE, self.database.PRICE, self.database.HISTORICAL_TABLE_NAME, 
                    self.database.IB_TICKER, self.stockCode, 
                    self.database.DATE, startDate, endDate,
                    self.database.DATE)
        data = self.database.readDatabase(sqlQuery)
        # If data is empty raise ValueError
        if data.empty:
            raise ValueError(('No price data in the range {} - {}. Method: Stock.getPriceRange'.format(startDate, endDate)))
        return data
    
#        
#    
#    # Gets a dataframe containing the number of shares owned over a range of dates    
#    def getOwnedRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
#        # Perform a left outer join to get the total number of stocks owned at each
#        # date in the historical data table.
#        sqlQuery = ''' SELECT {}.{}, SUM({}.{}) AS {}, MAX({}.{}) AS {} FROM {}   
#            LEFT OUTER JOIN {} ON {}.{} >= {}.{}
#            AND {}.{} == {}.{}
#            WHERE {}.{} LIKE '{}' 
#            AND {} BETWEEN date("{}") AND date("{}")
#            GROUP BY {} ORDER BY {} ASC''' \
#            .format(database.HISTORICAL_TABLE_NAME, database.DATE, 
#                    database.TABLE_NAME, database.NUMBER_PURCHASED, database.TOTAL_OWNED, 
#                    database.TABLE_NAME, database.DATE, database.DATE,
#                    database.HISTORICAL_TABLE_NAME, 
#                    database.TABLE_NAME, database.HISTORICAL_TABLE_NAME, database.DATE, database.TABLE_NAME, database.DATE,
#                    database.HISTORICAL_TABLE_NAME, database.IB_TICKER, database.TABLE_NAME, database.CODE,
#                    database.HISTORICAL_TABLE_NAME, database.IB_TICKER, self.stockCode,
#                    database.DATE, startDate, endDate,
#                    database.DATE, database.DATE)
#
#        data = self.database.readDatabase(sqlQuery)
#        # Remove the unwanted Purchase_Date column
#        data = data.drop(database.DATE, 1)
#        # For any dates before the first purchase, set the number owned to 0.
#        data = data.fillna(0)
#        return data
#        
#        
#   # Gets a dataframe containing the total spend on the shares owned over a range of dates    
#    def getSpentRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
#        # Perform a left outer join to get the total number of stocks owned at each
#        # date in the historical data table.
#        sqlQuery = ''' SELECT {}.{}, SUM({}.{}) AS {}, MAX({}.{}) AS {} FROM {}   
#            LEFT OUTER JOIN {} ON {}.{} >= {}.{}
#            AND {}.{} == {}.{}
#            WHERE {}.{} LIKE '{}' 
#            AND {} BETWEEN date("{}") AND date("{}")
#            GROUP BY {} ORDER BY {} ASC''' \
#            .format(database.HISTORICAL_TABLE_NAME, database.DATE, 
#                    database.TABLE_NAME, database.COST, database.TOTAL_SPENT, 
#                    database.TABLE_NAME, database.DATE, database.DATE,
#                    database.HISTORICAL_TABLE_NAME, 
#                    database.TABLE_NAME, database.HISTORICAL_TABLE_NAME, database.DATE, database.TABLE_NAME, database.DATE,
#                    database.HISTORICAL_TABLE_NAME, database.IB_TICKER, database.TABLE_NAME, database.CODE,
#                    database.HISTORICAL_TABLE_NAME, database.IB_TICKER, self.stockCode,
#                    database.DATE, startDate, endDate,
#                    database.DATE, database.DATE)
#
#        data = self.database.readDatabase(sqlQuery)
#        # Remove the unwanted Purchase_Date column
#        data = data.drop(database.DATE, 1)
#        # For any dates before the first purchase, set the number owned to 0.
#        data = data.fillna(0)
#        return data
#        
#        
#    # Get a dataframe containing the total value of the stock over a range of dates
#    def getValueRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
#        data = pd.merge(self.getPriceRange(startDate, endDate), self.getOwnedRange(startDate, endDate), on=database.DATE)
#        # Add a column for the total value of the stock
#        data['Total_Value'] = data[database.PRICE] * data[database.TOTAL_OWNED]
#        # For any dates before the first purchase, set the total value to 0.
#        data = data.fillna(0)
#        # Remove the price and number owned columns
#        data = data.drop([database.PRICE, database.TOTAL_OWNED], 1)
#        return data
#        
#
    # Gets a dataframe containing the total amount of dividen income over a range of dates    
    def getDividendRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        # Perform a left outer join to get the total number of stocks owned at each
        # date in the historical data table.
        sqlQuery = ''' SELECT {}.{}, SUM({}.{}) AS {}, MAX({}.{}) AS {} FROM {}   
            LEFT OUTER JOIN {} ON {}.{} >= {}.{}
            AND {}.{} == {}.{}
            WHERE {}.{} LIKE '{}' 
            AND {} BETWEEN date("{}") AND date("{}")
            GROUP BY {} ORDER BY {} ASC''' \
            .format(database.HISTORICAL_TABLE_NAME, database.DATE, 
                    database.DIVIDEND_TABLE_NAME, database.DIVIDEND_AMOUNT, database.DIVIDEND_TOTAL, 
                    database.DIVIDEND_TABLE_NAME, database.DIVIDEND_DATE, database.DIVIDEND_DATE,
                    database.HISTORICAL_TABLE_NAME, 
                    database.DIVIDEND_TABLE_NAME, database.HISTORICAL_TABLE_NAME, database.DATE, database.DIVIDEND_TABLE_NAME, database.DIVIDEND_DATE,
                    database.HISTORICAL_TABLE_NAME, database.IB_TICKER, database.DIVIDEND_TABLE_NAME, database.IB_TICKER,
                    database.HISTORICAL_TABLE_NAME, database.IB_TICKER, self.stockCode,
                    database.DATE, startDate, endDate,
                    database.DATE, database.DATE)

        data = self.database.readDatabase(sqlQuery)
        # Remove the unwanted Purchase_Date column
        data = data.drop(database.DIVIDEND_DATE, 1)
        # For any dates before the first purchase, set the number owned to 0.
        data = data.fillna(0)
        return data
        
        
#    # Plot stock data in a range of dates
#    def plot(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
#        # Format data to be plotted
#        date = self.getValueRange(startDate, endDate)[database.DATE].tolist()
#        date = list(map(convertDate, date))
#        value = self.getValueRange(startDate, endDate)["Total_Value"]
#        owned = self.getOwnedRange(startDate, endDate)[database.TOTAL_OWNED]
#        price = self.getPriceRange(startDate, endDate)[database.PRICE]
#        spent = self.getSpentRange(startDate, endDate)[database.TOTAL_SPENT]
#        dividend = self.getDividendRange(startDate, endDate)[database.DIVIDEND_TOTAL]
#
#        # Do plotting
#        fig = plt.figure()
#        plt.clf()  
#        
#        ax = fig.add_subplot(411)
#        plt.title(self.stockCode, fontsize = 16)
#        ax.plot(date, value)
#        ax.plot(date, spent, color = sns.color_palette()[1])
#        plt.ylabel("Amount ($)", fontsize = 14)
#        plt.legend(["Value", "Amount Spent"], loc = "upper left")
#        
#        sns.set_style("dark")
#        ax = fig.add_subplot(412)  
#        ax.plot(date, owned)
#        ax.set_ylabel("Number of shares owned", fontsize = 14, color = sns.color_palette()[0])
#        ax2 = ax.twinx()
#        ax2.plot(date, dividend, color = sns.color_palette()[1])
#        ax2.set_ylabel("Total Dividend ($)", fontsize = 14, color = sns.color_palette()[1])
#        ax2.xaxis.grid(True)
#        ax.xaxis.grid(True)
#        
#        sns.set_style("darkgrid")
#        ax = fig.add_subplot(413)
#        plt.plot(date, price)
#        plt.ylabel("Stock price ($)", fontsize = 14)
#        
#        ax = fig.add_subplot(414)
#        plt.plot(date, value - spent)
#        plt.plot(date, value - spent + dividend)
#        plt.legend(["Share Profit", "Share Profit + Dividend"], loc = "upper left")
#        plt.ylabel("Profit ($)", fontsize = 14)
#        plt.xlabel("Date", fontsize = 14)
#        
#        plt.show() 

        
        
