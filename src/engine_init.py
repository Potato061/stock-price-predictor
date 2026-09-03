from sqlalchemy import create_engine, text
import os
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

def get_engine():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME","StockPrices")
    conn_str = f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    return create_engine(conn_str)



class TableFetcher:
    def __init__(self,engine):
        self.engine = engine


    def fetch_table(self,table_name : str, order_by=None):
        query = f"SELECT * FROM  {table_name} "
        if order_by:
            query += f"ORDER BY {order_by}"
        with self.engine.connect() as conn:
            return pd.read_sql(text(query), conn)

    def fetch_curated_features(self):
        return self.fetch_table("curated_features", "symbol, price_datetime")

    def fetch_stg_prices(self):
        return self.fetch_table("stg_prices", "symbol, price_datetime")

    def fetch_items(self):
        return self.fetch_table("items")
