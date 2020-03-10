# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 18:25:36 2020

@author: fega
"""

# from pandas_datareader import data, wb
# import pandas_datareader as pdr
# from datetime import datetime

# data = pdr.get_data_fred('GS10')

# goog = pdr.get_data_yahoo("EIMI.SW", datetime(2000,1,1), datetime(2020,3,9))

# goog = pdr.get


ALPHAVANTAGE_API_KEY = 'P9EQZ6ESCW8YMFCA'
import pandas_datareader.data as web
from datetime import datetime

f = web.DataReader("EIMI.SWI", "av-daily", start=datetime(2014, 1, 1),
                    end=datetime(2020, 3, 9),
                    api_key=ALPHAVANTAGE_API_KEY)

