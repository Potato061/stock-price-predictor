import sqlalchemy as sql
import pandas as pd
import pyodbc
import os
import json
import requests
from datetime import datetime, timezone
from fetch_data import key
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

load_dotenv()

def get_symbols_df():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url,headers=headers)
    sp500 = pd.read_html(response.text)[0]

    symbols_df = (
        sp500.groupby("GICS Sector", group_keys=False)
        .apply(lambda x: x.sample(min(len(x), 10), random_state=42))  # ~10 per sector
        .head(100)
    )
    SYMBOLS = symbols_df["Symbol"].tolist()
    assert len(SYMBOLS) > 0
    return SYMBOLS


def get_engine():
    server = os.getenv("DB_SERVER","localhost")
    database = os.getenv("DB_NAME","StockPrices")
    conn_str = f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    return create_engine(conn_str)



def fetch_items():
    all_responses = []
    engine = get_engine()
    symbols = get_symbols_df()
    for symbol in symbols:
        url=f"https://api.twelvedata.com/time_series?apikey={key}&symbol={symbol}&interval=1day&type=stock&format=json"
        try:
            res = requests.get(url=url,headers=headers)
            if res.status_code == 200:
                all_responses.append(res.json())
                print(f"Fetched {symbol}")
            else:

                print(f"Failed {symbol}: {res.status_code}")

            time.sleep(1)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

    print(f"Fetched {len(all_responses)} symbols")