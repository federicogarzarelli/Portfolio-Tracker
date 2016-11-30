'''                   databaseFunctions.py
Created: 28/11/2016
    Python script that holds the functions for creating, reading and loading from 
    sqlite databases.
'''

import sqlite3
import pandas as pd

# Database class to create a new database at the file location given in databasePath.
# Includes methods for creating tables, clearing and removing tables. Adding to and
# querying the database.
class Database():
    # Class initializer
    def __init__(self, databasePath):
      self.databasePath = databasePath
      conn = sqlite3.connect(self.databasePath)
      conn.close()
         
    # function which creates the table (tableName) with the columns in columnList
    def createTable(self, tableName, columnList):
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()        
        #Created database
        sql_command = """ CREATE TABLE {} ({}) """.format(tableName, columnList)
        cursor.execute(sql_command)
        conn.commit()
        conn.close()
        print("Table created") 
    
    # Deletes all rows from the table
    def clearTable(self, tableName):
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()    
        sql_command = """ DELETE FROM {} """.format(tableName) 
        cursor.execute(sql_command)
        conn.commit()
        conn.close()
        print("Table cleared")

        
    # function which removes the table (tableName) from the database db
    def removeTable(self, tableName):
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()        
        #Remove database
        sql_command = """ DROP TABLE IF EXISTS {} """.format(tableName) 
        cursor.execute(sql_command)
        conn.commit()
        conn.close()
        print("Table removed")
        
            
    # function which adds data in dataframe to table
    def addToDatabase(self, dataFrame, tableName):
        conn = sqlite3.connect(self.databasePath)
        dataFrame.to_sql(name = tableName, con = conn, if_exists = 'append', index = False)       
        conn.commit()
        conn.close()
    
            
    # Uses the query sqlQuery to read the database
    def readDatabase(self, sqlQuery):
        conn = sqlite3.connect(self.databasePath)               
        dataFrame = pd.read_sql(sqlQuery, conn)
        conn.close()
        return dataFrame
    