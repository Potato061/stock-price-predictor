from sqlalchemy import create_engine
import os

def get_engine():
    server = os.getenv("DB_SERVER","localhost")
    database = os.getenv("DB_NAME","StockPrices")
    conn_str = f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    return create_engine(conn_str)