# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 12:09:03 2020

@author: fega
"""

import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# here enter the id of your google sheet
SAMPLE_SPREADSHEET_ID = '1AZUfiTU8WYlmJFB1FriZ37hzBc1v-vzLd-EzITFGs_g'
SAMPLE_RANGE_NAME = 'Data!A1:U8767'

def getGoogleSheetData(spreadsheet = SAMPLE_SPREADSHEET_ID, sheetdatarange = SAMPLE_RANGE_NAME):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])
   
    if not values:
        print('No data found.')
        return 0
    else:
        print('Data dumped. Returning data frame')
        column_names = values.pop(0)
        df = pd.DataFrame(values, columns=column_names)
        return df
    

#data = getGoogleSheetData(spreadsheet = SAMPLE_SPREADSHEET_ID, sheetdatarange = SAMPLE_RANGE_NAME)
    
