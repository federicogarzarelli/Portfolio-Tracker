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
import utils


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
    amountSpent = 0
    totalDividend = 0
    currency = ""
      
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
      currency = self.getCurrency([self.stockCode])
      currency  = currency.loc[0,self.database.YAHOO_CURRENCY]
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
        ownedRange = self.getOwnedRange(startDate = DEFAULT_STARTDATE, endDate = date)
        self.database.TOTAL_OWNED = ownedRange.loc[date, "Owned"]
        return self.database.TOTAL_OWNED
        
    # Get the number of the stock sold at date. Default date is today.
    def getSold(self, date = DEFAULT_DATE):
        data = self.soldRange(startDate = DEFAULT_STARTDATE, endDate = date)
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getSold.'.format(date))
            return 0
        return data.loc[date, "SoldCumSum"]

   # Get the number of the bought sold at date. Default date is today.
    def getBought(self, date = DEFAULT_DATE):
        data = self.soldRange(startDate = DEFAULT_STARTDATE, endDate = date)
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getBought.'.format(date))
            return 0
        return data.loc[date, "BoughtCumSum"]
               
    # Get the total spent as price paid + commissions
    def getSpent(self, date = DEFAULT_DATE):
        data = self.getSpentRange(self,  startDate = DEFAULT_STARTDATE, endDate = date)
        return data.loc[date, "SPENT_EUR_CUMSUM"]
    
     # Get the total price paid in Euros for a stock. Default date is today.
    def getPricePaid(self, date = DEFAULT_DATE):
        data = self.getPricePaidRange(startDate = DEFAULT_STARTDATE, endDate = date)
        return data.loc[date, "PRICEPAID_EUR_CUMSUM"]
              
    # Get the total commissions paid in Euros for a stock. Default date is today.
    def getCommissions(self, date = DEFAULT_DATE):
        data = self.getCommissionsRange(startDate = DEFAULT_STARTDATE, endDate = date)
        return data.loc[date, "COMMISSION_EUR_CUMSUM"]

    # Get the price of the stock at date. Default date is today.
    def getPrice(self, date = DEFAULT_DATE):
        data = self.getPriceRange(startDate = DEFAULT_STARTDATE, endDate = date)
        
        # If data is empty raise ValueError
        if data.empty:
            raise ValueError(('No price data for {}. Method: Stock.getPrice.'.format(date)))
        return data.at[date, self.database.PRICE]

    # get the total value of the stock at date. Default date is today.
    def getValue(self, date = DEFAULT_DATE):
        return self.getOwned(date) * self.getPrice(date)
        
    # Get the total amount of dividend payments at date.
    def getDividend(self, date = DEFAULT_DATE):
        data = self.getDividendRange(startDate = DEFAULT_STARTDATE, endDate = date)
               
        # If data is empty return 0
        if data.empty:
            print(('No dividend data for {}. Method: Stock.getDividend.'.format(date)))
            return 0
        return data.loc[date, "DividendCumSum"]

    # Get the currencies (YAHOO_CURRENCY) of a list of stocks
    def getCurrency(self, tickers):
        tickers_str = ""
        for ticker in tickers[:-1]:
            tickers_str = tickers_str + '"' + ticker + '", '
            
        tickers_str = tickers_str + '"' + tickers[-1] + '"'
        
        data = self.database.getStockInfo(tickers)
    
        # If data is empty return 0
        if data.empty:
            print(('No currency for {}. Method: Stock.getCurrency.'.format(tickers_str)))
            return 0
        return data[[self.database.YAHOO_CURRENCY]]
    
    
    ################ Range functions ###########################
    ## Similar to the ones up but for a range of dates
    
    # Get a data frame containing the price of the stock over a range of dates    
    def getPriceRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        tickers = [self.stockCode]
        data = self.database.getPrices(tickers, startDate, endDate)
        
        # If data is empty raise ValueError
        if data.empty:
            raise ValueError(('No price data in the range {} - {}. Method: Stock.getPriceRange'.format(startDate, endDate)))
        return data[[self.database.DATE, self.database.PRICE]]
    
    # Gets a dataframe containing the number of shares owned over a range of dates    
    def getOwnedRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        bought = self.getBoughtRange(startDate, endDate)
        sold = self.getSoldRange(startDate, endDate)
        
        data = pd.merge(bought, sold, how = 'inner', on = self.database.DATE)
        data['Owned'] = data['BoughtCumSum'] - data['SoldCumSum'] 
        
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getOwnedRange.'.format(endDate))
            return 0
        return data

   # Get the number of the stock sold at date over a range of dates. Default end date is today.
    def getSoldRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        data  = self.database.getTransactions([self.stockCode], startDate, endDate, direction = "SOLD")
        data[self.database.DATE] = utils.convertDate(data[self.database.DATE]) # Transform date into datetime
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DATE])
        
        data_Dates = pd.merge(Dates, data, how = "left", on = self.database.DATE)
        data_Dates['SoldCumSum'] = data_Dates[self.database.QUANTITY_SOLD].cumsum() 
        
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getSoldRange.'.format(endDate))
            return 0
        return data

   # Get the number of the bought sold at date over a range of dates. Default end date is today.
    def getBoughtRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        data  = self.database.getTransactions([self.stockCode], startDate, endDate, direction = "BOUGHT")
        data[self.database.DATE] = utils.convertDate(data[self.database.DATE]) # Transform date into datetime
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DATE])
        data_Dates = pd.merge(Dates, data, how = "left", on = self.database.DATE)
        data_Dates['SoldCumSum'] = data_Dates[self.database.QUANTITY_BOUGHT].cumsum() 
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getBoughtRange.'.format(endDate))
            return 0
        return data

    # Get the total price paid in Euros for a stock for a range of dates. Default enddate is today.
    def getPricePaidRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        # Get the number of sold assets used to buy this stock
        cost  = self.database.getTransactions([self.stockCode], startDate, endDate, direction = "BOUGHT")
        cost = cost.sort_values(by=['DATE', 'INSTRUMENT_SOLD'], ascending = True)
        cost['DATE'] = utils.convertDate(cost['DATE'])
        
        # Get the price of the sold assets on that date (this is CCYEUR exchange rate when a currency is used to pay)
        tickers_list = cost['INSTRUMENT_SOLD'].drop_duplicates().values.tolist() # list of instruments sold
        
        price = self.database.getPrices(tickers_list, startDate, endDate)
        price = price.sort_values(by=['DATE', 'IB_TICKER'], ascending = True)
        price.columns = ['DATE', 'INSTRUMENT_SOLD', 'PRICE_INSTRUMENT_SOLD']
        
        # Get the currencies of the sold assets
        currencies = self.getCurrency(tickers_list)
        currencies['INSTRUMENT_SOLD'] = tickers_list
        
        # Assign the currencies to the sold assets in the price table
        price_curr = pd.merge(price, currencies, how = 'left', on = 'INSTRUMENT_SOLD') 
        
        # Get the CCYEUR rates       
        tickers_list = price_curr['YAHOO_CURRENCY'].drop_duplicates().values.tolist() # list of currencies of the instruments sold
        priceYAHOOCURR = self.database.getPrices(tickers_list, startDate, endDate) 
        priceYAHOOCURR['DATE'] = utils.convertDate(priceYAHOOCURR['DATE'])
        priceYAHOOCURR = priceYAHOOCURR.sort_values(by=['DATE', 'IB_TICKER'], ascending = True)
        priceYAHOOCURR.columns = ['DATE', 'YAHOO_CURRENCY', 'PRICE_YAHOO_CURRENCY']
        
        # Assign the CCYEUR rates to the price table
        price_curr2 = pd.merge_asof(price_curr, priceYAHOOCURR, on='DATE', by='YAHOO_CURRENCY')
        
        # Assign the cost in EUR of the instruments sold to the transaction table
        cost_price_curr2 = pd.merge_asof(cost, price_curr2, on='DATE', by='INSTRUMENT_SOLD')
        
        # Calculate the price in EUR per transaction and add the cumulative sum
        cost_price_curr2['PRICEPAID_EUR'] =  cost_price_curr2['QUANTITY_SOLD'] *  cost_price_curr2['PRICE_INSTRUMENT_SOLD'] * cost_price_curr2['PRICE_YAHOO_CURRENCY']
        cost_price_curr2['PRICEPAID_EUR_CUMSUM'] = cost_price_curr2['PRICEPAID_EUR'].cumsum()
        # If data is empty return 0
        if cost_price_curr2.empty:
            print('No prices paid for dates up to {}. Method: Stock.getPricePaidRange.'.format(endDate))
            return 0
        return cost_price_curr2[[self.database.DATE,'PRICEPAID_EUR_CUMSUM']]
              
    # Get the total commissions paid in Euros for a stock for a range of dates. Default end date is today.
    def getCommissionsRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        # Get the commissions paid for a stock
        commissionsCHF  = self.database.getTransactions([self.stockCode], startDate, endDate, direction = "BOUGHT")
        commissionsCHF = commissionsCHF.sort_values(by=['DATE'], ascending = True)
        
        # Get the CHFEUR rates to convert the commissions to EUR              
        CHFEUR = self.database.getPrices("CHF", startDate, endDate)
        CHFEUR = CHFEUR.sort_values(by=['DATE'], ascending = True)

        # Transform DATE to datetime and merge the commission date to the previous available date 
        commissionsCHF['DATE'] = utils.convertDate(commissionsCHF['DATE'])
        CHFEUR['DATE'] = utils.convertDate(CHFEUR['DATE'])
               
        commissionsCHF_L_CHFEUR = pd.merge_asof(commissionsCHF, CHFEUR, on='DATE')
        
        # Convert the commission in EUR and add the cumulative sum
        commissionsCHF_L_CHFEUR['COMMISSION_EUR'] = commissionsCHF_L_CHFEUR['COMMISSION'] * commissionsCHF_L_CHFEUR['PRICE']
        commissionsCHF_L_CHFEUR['COMMISSION_EUR_CUMSUM'] = commissionsCHF_L_CHFEUR['COMMISSION_EUR'].cumsum()

        # If data is empty return 0
        if commissionsCHF_L_CHFEUR.empty:
            print('No commissions for dates up to {}. Method: Stock.getCommissionsRange.'.format(endDate))
            return 0
        return commissionsCHF_L_CHFEUR[[self.database.DATE,'COMMISSION_EUR_CUMSUM']]

    # Get the total spent as price paid + commissions for a range of dates. Default end date is today
    def getSpentRange(self,  startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        pricepaid = self.getPricePaidRange(startDate, endDate) 
        commissions = self.getCommissionsRange(startDate, endDate)
        
        data = pd.merge(pricepaid, commissions, how = 'inner', on = self.database.DATE)
        data['SPENT_EUR_CUMSUM'] = data['PRICEPAID_EUR_CUMSUM'] + data['COMMISSION_EUR_CUMSUM'] 
        
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getSpentRange.'.format(endDate))
            return 0
        return data
    
    # Get a dataframe containing the total value of the stock over a range of dates
    def getValueRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        # Get the price and the number of owned share by date
        price = self.getPriceRange(startDate, endDate)
        owned = self.getOwnedRange(startDate, endDate)
        owned[self.database.DATE] = utils.convertDate(owned[self.database.DATE])  # Transform date into datetime
        
        price_owned = pd.merge(price, owned, on=self.database.DATE)
        # Add a column for the total value of the stock
        price_owned['Total_Value'] = price_owned[self.database.PRICE] * price_owned['Owned']
        
        # Convert to EUR
        # 1. Get the currency of the stock and the corresponding CCYEUR rate
        currencies = self.getCurrency([self.stockCode])
        currency_list = currencies[self.database.YAHOO_CURRENCY].tolist()
        # 2. Get the exchange rate
        priceYAHOOCURR = self.database.getPrices(currency_list, startDate, endDate)
        priceYAHOOCURR['DATE'] = utils.convertDate(priceYAHOOCURR['DATE'])
        priceYAHOOCURR = priceYAHOOCURR.sort_values(by=['DATE', 'IB_TICKER'], ascending = True)
        priceYAHOOCURR.columns = ['DATE', 'YAHOO_CURRENCY', 'PRICE_YAHOO_CURRENCY']
        # 3. Merge the exchange rate to the price on the closest (earlier) date
        data = pd.merge_asof(price_owned, priceYAHOOCURR, on='DATE', by='YAHOO_CURRENCY')
        # 4. Calculate the value of the position in EUR
        data['VALUE_EUR'] =  data['Total_Value'] * data['PRICE_YAHOO_CURRENCY']
        
        # For any dates before the first purchase, set the total value to 0.
        data = data.fillna(0)
        # Remove the price and number owned columns
        data = data.drop([self.database.PRICE, self.database.TOTAL_OWNED], 1)
        
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getValueRange.'.format(endDate))
            return 0
        return data
        
    # Gets a dataframe containing the total amount of dividend income over a range of dates    
    def getDividendRange(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
        tickers = [self.stockCode]
        dividends = self.database.getDividends(tickers, startDate, endDate)
        dividends[self.database.DATE] = utils.convertDate(dividends[self.database.DATE]) # Transform date into datetime
        
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DATE])
        data = pd.merge(Dates, dividends, how = "left", on = self.database.DATE)
        data['DividendCumSum'] = data[self.database.DIVIDEND_AMOUNT].cumsum() 
           
        data = data[[self.database.DATE, 'DividendCumSum']]
        data = data.fillna(0)
        
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getDividendRange.'.format(endDate))
            return 0
        return data
        
        
#    # Plot stock data in a range of dates
#    def plot(self, startDate = DEFAULT_STARTDATE, endDate = DEFAULT_DATE):
#        # Format data to be plotted
#        date = self.getValueRange(startDate, endDate)[database.DATE].tolist()
#        date = list(map(utils.convertDate, date))
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
#        plt.xlabel(self.database.DATE, fontsize = 14)
#        
#        plt.show() 

        
        
