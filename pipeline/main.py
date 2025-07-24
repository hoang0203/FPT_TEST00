import os

import numpy as np
import pandas as pd
import pyodbc


from threading import Thread
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

def is_valid_email(email):
    '''Check if the email is valid according to specific rules:
    1. It should not be null or empty.
    2. It should not start with 'invalid'.
    3. It should contain an '@' symbol.
    4. The username part should not be empty.
    5. The domain part should contain at least one '.'.
    6. The domain should end with '.com', '.net', or '.org'.
    '''
    
    if pd.isnull(email):
        return False
    email = str(email)
    
    if email.lower().startswith('invalid'):
        return False
    if '@' not in email:
        return False
    username, _, domain = email.partition('@')
    
    if not username.strip():
        return False
    if '.' not in domain:
        return False
    if not domain.lower().endswith(('.com', '.net', '.org')):
        return False
    
    return True


def insert_customers_to_db(customers_df):
    '''Insert valid customers into the database.'''
    
    SERVER = os.getenv('SERVER')
    DATABASE = os.getenv('DATABASE')
    conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                      f'Server={SERVER};'
                      f'Database={DATABASE};'
                      'Trusted_Connection=yes;')
    cursor = conn.cursor()

    customers_df = customers_df.astype(str)
    
    for index, row in customers_df.iterrows():
        cursor.execute('''
            INSERT INTO [dim].[CUSTOMERS] (CUSTOMER_ID, NAME, EMAIL, ADDRESS, CREATED_AT)
            VALUES (?, ?, ?, ?, GETDATE())
        ''', row['customer_id'], row['name'], row['email'], row['address'])
    
    conn.commit()
    cursor.close()
    conn.close()
    
    
def etl_customers():
    '''Extract, Transform, Load customers data.'''
    customers_df = pd.read_csv(r'D:\Project\Test\FPT_TEST00\datasource\customers.csv')
    
    # filter out invalid or missing email addresses
    filtered_customers_df = customers_df[customers_df['email'].apply(is_valid_email)]
    
    flow = 5
    threads = []
     
    # Split the DataFrame into smaller chunks for parallel processing
    split_dfs = np.array_split(filtered_customers_df, flow)
    
    for i, split_df in enumerate(split_dfs):
        thread = Thread(target=insert_customers_to_db, args=(split_df,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    print("customers inserted successfully.")
    

def is_valid_date(date_str):
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            pd.to_datetime(date_str, format=fmt, errors='raise')
            return True
        except Exception:
            continue
    return False


def insert_transactions_to_db(transactions_df):
    '''Insert transactions into the database.'''
    
    SERVER = os.getenv('SERVER')
    DATABASE = os.getenv('DATABASE')
    conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                      f'Server={SERVER};'
                      f'Database={DATABASE};'
                      'Trusted_Connection=yes;')
    cursor = conn.cursor()

    # convert transaction_date to 'YYYY-MM-DD' format
    transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    transactions_df = transactions_df.astype(str)
    
    for index, row in transactions_df.iterrows():
        cursor.execute(f'''
            INSERT INTO [fact].[TRANSACTIONS] (TRANSACTION_ID, CUSTOMER_ID, TRANSACTION_DATE, AMOUNT, CREATED_AT)
            VALUES ('{row['transaction_id']}', '{row['customer_id']}', '{row['transaction_date']}', {row['amount']}, GETDATE())
        ''')

    conn.commit()
    cursor.close()
    conn.close()
    
    
def etl_transactions():
    '''Extract, Transform, Load transactions data.'''
    # Read transactions data from CSV file
    transactions_df = pd.read_csv(r'D:\Project\Test\FPT_TEST00\datasource\transactions.csv')
    
    # remove duplicate entries
    transactions_df = transactions_df.drop_duplicates()
    
    # filter out invalid dates
    transactions_df = transactions_df[transactions_df['transaction_date'].apply(is_valid_date)]
    
    flow = 5
    threads = []
     
    # Split the DataFrame into smaller chunks for parallel processing
    split_dfs = np.array_split(transactions_df, flow)
    
    for i, split_df in enumerate(split_dfs):
        thread = Thread(target=insert_transactions_to_db, args=(split_df,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    print("Transactions inserted successfully.")
    
    
def insert_products_to_db(products_df):
    '''Insert products into the database.'''
    
    SERVER = os.getenv('SERVER')
    DATABASE = os.getenv('DATABASE')
    conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                      f'Server={SERVER};'
                      f'Database={DATABASE};'
                      'Trusted_Connection=yes;')
    cursor = conn.cursor()

    products_df = products_df.astype(str)
    
    for index, row in products_df.iterrows():
        cursor.execute(f'''
            INSERT INTO [dim].[PRODUCTS] (PRODUCT_ID, PRODUCT_NAME, CATEGORY, PRICE, CREATED_AT)
            VALUES ('{row['product_id']}', '{row['product_name']}', '{row['category']}', {row['price']}, GETDATE())
        ''')

    conn.commit()
    cursor.close()
    conn.close()
    
    
def etl_products():
    '''Extract, Transform, Load products data.'''
    
    # Read products data from CSV file
    products_df = pd.read_csv(r'D:\Project\Test\FPT_TEST00\datasource\products.csv')

    # Standardize product names and categories
    products_df['product_name'] = products_df['product_name'].str.upper()
    products_df['category'] = products_df['category'].str.upper()
    
    flow = 5
    threads = []
    
    # Split the DataFrame into smaller chunks for parallel processing
    split_dfs = np.array_split(products_df, flow)
    
    for i, split_df in enumerate(split_dfs):
        thread = Thread(target=insert_products_to_db, args=(split_df,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    print("Products inserted successfully.")
    
    
def main():
    # ETL customers data
    etl_customers()
    # ETL transactions data
    etl_transactions()
    # ETL products data
    etl_products()


if __name__ == "__main__":
    main()
    