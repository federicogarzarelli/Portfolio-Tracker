#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""                       Stock.py
Created on Fri Nov 25 11:32:32 2016

@author: dmcauslan

Stock class that contains the information
- Number OWNED
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
    Total_OWNED and Total_Value for a range of dates.
Modified 01/12/2016:
    * Implemented sell() method for selling some of the stock.
    * Implemented remove() method for removing a transaction from the database
    (incase you made an error when adding it)
    * Fixed getValueRange() method so that it works with selling.
    * Removed TOTAL_OWNED column from database as it calculates incorrectly
    when purchases are not added in date order. TOTAL OWNED column can easily be
    generated in SQL using SUM(NUMBER_PURCHASED) AS TOTAL_OWNED.
    * Split getValueRange() method into getOwnedRange() and getValueRange() methods.
    * Implemented plot method which plots date vs total value, number OWNED, stock price and profit.
    * Implemented getSpentRange() method which calculates the amount spent over a
    range of dates.
    * Modified contstructor so that it gets the total number of shares OWNED and
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
# utils.DEFAULT_DATE = str(datetime.date.today())+ " 00:00:00"
# utils.DEFAULT_STARTDATE = "1975-01-01 00:00:00"

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
    def __init__(self, stockCode, database, datasource = "GOOGLEFINANCE"): # "YAHOOFINANCE"
      self.stockCode = stockCode
      self.database = database
      
      if datasource == "YAHOOFINANCE":
          self.currencyfield = self.database.YAHOO_CURRENCY
      elif datasource == "GOOGLEFINANCE":
          self.currencyfield = self.database.GOOGLE_FINANCE_CURRENCY
      
      # Updates the database with any price data that it does not have.
      try:
          self.database.updateStockData(self.stockCode, utils.datasource)
      except urllib.request.URLError:
          print("{} data not updated. URL Error.".format(self.stockCode))
     
    # Class string method
    def __str__(self):
         return "{} - number OWNED: {}, total cost: ${:.2f}, total dividend: ${:.2f}." \
                .format(self.stockCode, self.numberOwned, self.totalCost, self.totalDividend)

    def update(self): # to run after all the stocks have been updated
      # Updates the numberOwned, totalCost and totalDividend values
      numOwned = self.getOwned()
      if numOwned != None:
          self.numberOwned = numOwned
      amountSpent = self.getSpent()
      if amountSpent != None:
          self.amountSpent = amountSpent
      dividend = self.getDividend()
      if dividend != None:
          self.totalDividend = dividend
      currency = self.getCurrency([self.stockCode])
      currency  = currency.loc[0,self.currencyfield]
      if currency != None:
          self.currency = currency


    # Buy a number of stocks at a price and save in the database
    def buy(self, quantity_bought, instrument_sold, quantity_sold, commission, date = utils.DEFAULT_DATE):
        purchaseData = pd.DataFrame({self.database.DATE: [date],
                                     self.database.INSTRUMENT_BOUGHT: [self.stockCode],
                                     self.database.QUANTITY_BOUGHT: [quantity_bought],
                                     self.database.INSTRUMENT_SOLD: [instrument_sold],
                                     self.database.QUANTITY_SOLD: quantity_sold,
                                     self.database.COMMISSION: [commission]})
        self.database.addToDatabase(purchaseData, self.database.TRANSACTIONS_TABLE_NAME)
    
    # Sell a number of stocks at a price and save in the database     
    def sell(self, quantity_bought, instrument_bought, quantity_sold, commission, date = utils.DEFAULT_DATE):
        purchaseData = pd.DataFrame({self.database.DATE: [date],
                                     self.database.INSTRUMENT_BOUGHT: [instrument_bought],
                                     self.database.QUANTITY_BOUGHT: [quantity_bought],
                                     self.database.INSTRUMENT_SOLD: [self.stockCode],
                                     self.database.QUANTITY_SOLD: quantity_sold,
                                     self.database.COMMISSION: [commission]})
        self.database.addToDatabase(purchaseData, self.database.TRANSACTIONS_TABLE_NAME)
    
    # Adds a dividend payment to the dividend database table
    def addDividend(self, payment, date = utils.DEFAULT_DATE):
        dividendData = pd.DataFrame({self.database.DIVIDEND_DATE: [date],
                                     self.database.IB_TICKER: [self.stockCode],
                                     self.database.DIVIDEND_AMOUNT: [payment]})
        self.database.addToDatabase(dividendData, self.database.DIVIDEND_TABLE_NAME)        
    
    # Removes a divident payment from the dividend database table
    def removeDividend(self, payment, date):
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
    
    # Get the number of the stock OWNED at date. Default date is today.
    def getOwned(self, date = utils.DEFAULT_DATE):
        OwnedRange = self.getOwnedRange(startDate = utils.DEFAULT_STARTDATE, endDate = date)
        Owned_at_date = OwnedRange.loc[OwnedRange[self.database.DATE]==date,"OWNED"]
        return Owned_at_date.values[0]
        
    # Get the number of the stock sold at date. Default date is today.
    def getSold(self, date = utils.DEFAULT_DATE):
        data = self.soldRange(startDate = utils.DEFAULT_STARTDATE, endDate = date)
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getSold.'.format(date))
            return 0
        return data.loc[data[self.database.DATE]==date,"SOLD_CUMSUM"].values[0]

   # Get the number of the bought sold at date. Default date is today.
    def getBought(self, date = utils.DEFAULT_DATE):
        data = self.soldRange(startDate = utils.DEFAULT_STARTDATE, endDate = date)
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getBought.'.format(date))
            return 0
        return data.loc[data[self.database.DATE]==date,"BOUGHT_CUMSUM"].values[0]
               
    # Get the total spent as price paid + commissions
    def getSpent(self, date = utils.DEFAULT_DATE):
        data = self.getSpentRange(startDate = utils.DEFAULT_STARTDATE, endDate = date)
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getSpent.'.format(date))
            return 0
        return data.loc[data[self.database.DATE]==date,"SPENT_EUR_CUMSUM"].values[0]
    
     # Get the total price paid in Euros for a stock. Default date is today.
    def getPricePaid(self, date = utils.DEFAULT_DATE):
        data = self.getPricePaidRange(startDate = utils.DEFAULT_STARTDATE, endDate = date)
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getPricePaid.'.format(date))
            return 0
        return data.loc[data[self.database.DATE]==date,"PRICEPAID_EUR_CUMSUM"].values[0]
              
    # Get the total commissions paid in Euros for a stock. Default date is today.
    def getCommissions(self, date = utils.DEFAULT_DATE):
        data = self.getCommissionsRange(startDate = utils.DEFAULT_STARTDATE, endDate = date)
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getCommissions.'.format(date))
            return 0
        return data.loc[data[self.database.DATE]==date,"COMMISSION_EUR_CUMSUM"].values[0]

    # Get the profit & losses in EUR for a stock. Default date is today.
    def Profits_Losses(self, date = utils.DEFAULT_DATE):
        data = self.Profits_LossesRange(startDate  = utils.DEFAULT_STARTDATE, endDate = date)
        if data.empty:
            print('No profits and losses for dates up to {}. Method: Stock.Profits_Losses.'.format(date))
            return 0
        return data.loc[data[self.database.DATE]==date,"P_L"].values[0]

    # Get the price of the stock at date. Default date is today.
    def getPrice(self, date = utils.DEFAULT_DATE):
        data = self.getPriceRange(startDate = utils.DEFAULT_STARTDATE, endDate = date)
        
        # If data is empty raise ValueError
        if data.empty:
            raise ValueError(('No price data for {}. Method: Stock.getPrice.'.format(date)))
        return data.loc[data[self.database.DATE]==date,self.database.PRICE].values[0]

    # get the total value of the stock at date. Default date is today.
    def getValue(self, date = utils.DEFAULT_DATE):
        return self.getOwned(date) * self.getPrice(date)
        
    # Get the total amount of dividend payments at date.
    def getDividend(self, date = utils.DEFAULT_DATE):
        data = self.getDividendRange(startDate = utils.DEFAULT_STARTDATE, endDate = date)          
        # If data is empty return 0
        if data.empty:
            print(('No dividend data for {}. Method: Stock.getDividend.'.format(date)))
            return 0
        return data.loc[data[self.database.DIVIDEND_DATE]==date,"DIVIDEND_CUMSUM"].values[0]

    # Get the currencies (YAHOO_CURRENCY or GOOGLE_FINANCE_CURRENCY) of a list of stocks
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
        return data[[self.currencyfield]]
    
    
    ################ Range functions ###########################
    ## Similar to the ones up but for a range of dates
    
    def Profits_LossesRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        spent = self.getSpentRange(startDate, endDate)
        value = self.getValueRange(startDate, endDate)
        
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DATE])
        dates_spent = pd.merge(Dates, spent, how = "left", on = self.database.DATE)
        dates_spent_value = pd.merge(dates_spent, value, how = "left", on = self.database.DATE)
        dates_spent_value["P_L"] = dates_spent_value["VALUE_EUR"] - dates_spent_value["SPENT_EUR_CUMSUM"]
        data = dates_spent_value[[self.database.DATE,"P_L"]]
                
        # If data is empty raise ValueError
        if data.empty:
            raise ValueError(('No profit & loss data in the range {} - {}. Method: Stock.Profits_LossesRange'.format(startDate, endDate)))
        return data
        
    # Get a data frame containing the price of the stock over a range of dates    
    def getPriceRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        tickers = [self.stockCode]
        data = self.database.getPrices(tickers, startDate, endDate)
        
        # If data is empty raise ValueError
        if data.empty:
            raise ValueError(('No price data in the range {} - {}. Method: Stock.getPriceRange'.format(startDate, endDate)))
        return data[[self.database.DATE, self.database.PRICE]]
    
    # Gets a dataframe containing the number of shares OWNED over a range of dates    
    def getOwnedRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        bought = self.getBoughtRange(startDate, endDate)
        sold = self.getSoldRange(startDate, endDate)
        
        data = pd.merge(bought, sold, how = 'outer', on = self.database.DATE)
        data['OWNED'] = data['BOUGHT_CUMSUM'] - data['SOLD_CUMSUM'] 
        
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getOwnedRange.'.format(endDate))
            return 0
        return data

   # Get the number of the stock sold at date over a range of dates. Default end date is today.
    def getSoldRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        sold  = self.database.getTransactions([self.stockCode], startDate, endDate, direction = "SOLD")
        sold = sold[[self.database.DATE, self.database.QUANTITY_SOLD]]
        sold[self.database.DATE] = pd.to_datetime(sold[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')# Transform date into datetime
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DATE])
        
        data = pd.merge(Dates, sold, how = "left", on = self.database.DATE)
        data = data.fillna(0)
        data['SOLD_CUMSUM'] = data[self.database.QUANTITY_SOLD].cumsum() 
        
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getSoldRange.'.format(endDate))
            return 0
        return data

   # Get the number of the bought sold at date over a range of dates. Default end date is today.
    def getBoughtRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        bought  = self.database.getTransactions([self.stockCode], startDate, endDate, direction = "BOUGHT")
        bought = bought[[self.database.DATE, self.database.QUANTITY_BOUGHT]]
        bought[self.database.DATE] = pd.to_datetime(bought[self.database.DATE], format = '%Y-%m-%d %H:%M:%S') # Transform date into datetime
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DATE])
        
        data = pd.merge(Dates, bought, how = "left", on = self.database.DATE)
        data = data.fillna(0)
        data['BOUGHT_CUMSUM'] = data[self.database.QUANTITY_BOUGHT].cumsum() 
        # If data is empty return 0
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getBoughtRange.'.format(endDate))
            return 0
        return data

    # Get the total price paid in Euros for a stock for a range of dates. Default enddate is today.
    def getPricePaidRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        # Get the number of sold assets used to buy this stock
        cost  = self.database.getTransactions([self.stockCode], startDate, endDate, direction = "BOUGHT")
        cost = cost.sort_values(by=['DATE', 'INSTRUMENT_SOLD'], ascending = True)
        cost[self.database.DATE] = pd.to_datetime(cost[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')
        
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
        tickers_list = price_curr[self.currencyfield].drop_duplicates().values.tolist() # list of currencies of the instruments sold
        priceDATACURR = self.database.getPrices(tickers_list, startDate, endDate) 
        priceDATACURR[self.database.DATE] = pd.to_datetime(priceDATACURR[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')
        priceDATACURR = priceDATACURR.sort_values(by=['DATE', 'IB_TICKER'], ascending = True)
        priceDATACURR.columns = ['DATE', self.currencyfield, 'PRICE_DATA_CURRENCY']
        
        # Assign the CCYEUR rates to the price table
        price_curr2 = pd.merge_asof(price_curr, priceDATACURR, on='DATE', by=self.currencyfield)
        
        # Assign the cost in EUR of the instruments sold to the transaction table
        cost_price_curr2 = pd.merge_asof(cost, price_curr2, on='DATE', by='INSTRUMENT_SOLD')
        
        # Calculate the price in EUR per transaction and add the cumulative sum
        cost_price_curr2['PRICEPAID_EUR'] =  cost_price_curr2['QUANTITY_SOLD'] *  cost_price_curr2['PRICE_INSTRUMENT_SOLD'] * cost_price_curr2['PRICE_DATA_CURRENCY']

        
        # Now create a series of dates and join to it
        cost_price_curr2[self.database.DATE] = pd.to_datetime(cost_price_curr2[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')# Transform date into datetime
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DATE])
        
        data = pd.merge(Dates, cost_price_curr2, how = "left", on = self.database.DATE)
        data = data.fillna(0)
        data['PRICEPAID_EUR_CUMSUM'] = data['PRICEPAID_EUR'].cumsum()
        
        # If data is empty return 0
        if data.empty:
            print('No prices paid for dates up to {}. Method: Stock.getPricePaidRange.'.format(endDate))
            return 0
        return data[[self.database.DATE,'PRICEPAID_EUR_CUMSUM']]
              
    # Get the total commissions paid in Euros for a stock for a range of dates. Default end date is today.
    def getCommissionsRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        # Get the commissions paid for a stock
        commissionsCHF  = self.database.getTransactions([self.stockCode], startDate, endDate, direction = "BOUGHT")
        commissionsCHF = commissionsCHF.sort_values(by=['DATE'], ascending = True)
        
        # Get the CHFEUR rates to convert the commissions to EUR              
        CHFEUR = self.database.getPrices(["CHF"], startDate, endDate)
        CHFEUR = CHFEUR.sort_values(by=['DATE'], ascending = True)

        # Transform DATE to datetime and merge the commission date to the previous available date 
        commissionsCHF[self.database.DATE] = pd.to_datetime(commissionsCHF[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')
        CHFEUR[self.database.DATE] =  pd.to_datetime(CHFEUR[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')
               
        commissionsCHF_L_CHFEUR = pd.merge_asof(commissionsCHF, CHFEUR, on='DATE')
        
        # Convert the commission in EUR and add the cumulative sum
        commissionsCHF_L_CHFEUR['COMMISSION_EUR'] = commissionsCHF_L_CHFEUR['COMMISSION'] * commissionsCHF_L_CHFEUR['PRICE']

        # Now create a series of dates and join to it
        commissionsCHF_L_CHFEUR[self.database.DATE] = pd.to_datetime(commissionsCHF_L_CHFEUR[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')# Transform date into datetime
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DATE])
        
        data = pd.merge(Dates, commissionsCHF_L_CHFEUR, how = "left", on = self.database.DATE)
        data = data.fillna(0)
        data['COMMISSION_EUR_CUMSUM'] = data['COMMISSION_EUR'].cumsum()

        # If data is empty return 0
        if data.empty:
            print('No commissions for dates up to {}. Method: Stock.getCommissionsRange.'.format(endDate))
            return 0
        return data[[self.database.DATE,'COMMISSION_EUR_CUMSUM']]

    # Get the total spent as price paid + commissions for a range of dates. Default end date is today
    def getSpentRange(self,  startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        pricepaid = self.getPricePaidRange(startDate, endDate) 
        commissions = self.getCommissionsRange(startDate, endDate)
        
        data = pd.merge(pricepaid, commissions, how = 'inner', on = self.database.DATE)
        data['SPENT_EUR_CUMSUM'] = data['PRICEPAID_EUR_CUMSUM'] + data['COMMISSION_EUR_CUMSUM'] 
        
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getSpentRange.'.format(endDate))
            return 0
        return data
    
    # Get a dataframe containing the total value of the stock over a range of dates
    def getValueRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        # Get the price and the number of OWNED share by date
        price = self.getPriceRange(startDate, endDate)
        OWNED = self.getOwnedRange(startDate, endDate)
        OWNED[self.database.DATE] = pd.to_datetime(OWNED[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')  # Transform date into datetime
        
        price_OWNED = pd.merge(price, OWNED, how = "left", on=self.database.DATE)
        # Add a column for the total value of the stock
        price_OWNED['Total_Value'] = price_OWNED[self.database.PRICE] * price_OWNED['OWNED']
        
        # Convert to EUR
        # 1. Get the currency of the stock and the corresponding CCYEUR rate
        currencies = self.getCurrency([self.stockCode])
        currency_list = currencies[self.currencyfield].tolist()
        # 2. Get the exchange rate
        priceDATACURR = self.database.getPrices(currency_list, startDate, endDate)
        priceDATACURR[self.database.DATE] = pd.to_datetime(priceDATACURR[self.database.DATE], format = '%Y-%m-%d %H:%M:%S')
        priceDATACURR = priceDATACURR.sort_values(by=['DATE', 'IB_TICKER'], ascending = True)
        priceDATACURR.columns = ['DATE', self.currencyfield, 'PRICE_DATA_CURRENCY']
        # 3. Merge the exchange rate to the price on the closest (earlier) date
        data = pd.merge_asof(price_OWNED, priceDATACURR, on='DATE')
        # 4. Calculate the value of the position in EUR
        data['VALUE_EUR'] =  data['Total_Value'] * data['PRICE_DATA_CURRENCY']
        
        # For any dates before the first purchase, set the total value to 0.
        data = data.fillna(0)
        # Remove the price and number OWNED columns
        data = data[[self.database.DATE,'VALUE_EUR']]
        
        if data.empty:
            print('No data for dates up to {}. Method: Stock.getValueRange.'.format(endDate))
            return 0
        return data
        
    # Gets a dataframe containing the total amount of dividend income over a range of dates    
    def getDividendRange(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
        tickers = [self.stockCode]
        dividends = self.database.getDividends(tickers, startDate, endDate)
        dividends[self.database.DIVIDEND_DATE] = pd.to_datetime(dividends[self.database.DIVIDEND_DATE], format = '%Y-%m-%d %H:%M:%S') # Transform date into datetime
        
        Dates = pd.DataFrame(pd.date_range(startDate, endDate), columns = [self.database.DIVIDEND_DATE])
        data = pd.merge(Dates, dividends, how = "left", on = self.database.DIVIDEND_DATE)
        data = data.fillna(0)
        data['DIVIDEND_CUMSUM'] = data[self.database.DIVIDEND_AMOUNT].cumsum() 
           
        data = data[[self.database.DIVIDEND_DATE, 'DIVIDEND_CUMSUM']]

        if data.empty:
            print('No data for dates up to {}. Method: Stock.getDividendRange.'.format(endDate))
            return 0
        return data
        
        
#    # Plot stock data in a range of dates
#    def plot(self, startDate = utils.DEFAULT_STARTDATE, endDate = utils.DEFAULT_DATE):
#        # Format data to be plotted
#        date = self.getValueRange(startDate, endDate)[database.DATE].tolist()
#        date = list(map(utils.convertDate, date))
#        value = self.getValueRange(startDate, endDate)["Total_Value"]
#        OWNED = self.getOwnedRange(startDate, endDate)[database.TOTAL_OWNED]
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
#        ax.plot(date, OWNED)
#        ax.set_ylabel("Number of shares OWNED", fontsize = 14, color = sns.color_palette()[0])
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

        
        
