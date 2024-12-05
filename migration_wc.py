import pandas as pd
import sqlite3

# Read Excel file with multiple sheets
excel_file = pd.ExcelFile('Calculations/work_centers.xlsx')

# Create SQLite database connection
conn = sqlite3.connect('Calculations/work_centers.db')

# For each sheet in Excel file create a table
for sheet_name in excel_file.sheet_names:
    # Read sheet data
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    # Create table in database using sheet name
    df.to_sql(sheet_name, conn, if_exists='replace', index=False)

conn.close()