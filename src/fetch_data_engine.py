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
import time
from engine_init import get_engine





def get_symbols_df():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
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






def fetch_prices():
    os.makedirs("data/raw_backups", exist_ok=True)
    engine = get_engine()
    symbols = get_symbols_df()
    all_rows = []

    for symbol in symbols:
        url = f"https://api.twelvedata.com/time_series?apikey={key}&symbol={symbol}&interval=1day&outputsize=5000&format=json"
        try:
            res = requests.get(url=url)
            if res.status_code == 200:
                data = res.json()
                all_rows.append({
                    "symbol": symbol,
                    "fetched_at": datetime.now(timezone.utc),
                    "source_api": "twelvedata",
                    "interval": "1day",
                    "raw_json": json.dumps(data),
                })
                print(f"Fetched {symbol}")
            else:
                print(f"Failed {symbol}: {res.status_code}")
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

        time.sleep(8)

    raw_df = pd.DataFrame(all_rows)
    raw_df.to_json("data/raw_backups/raw_prices_backup.json", orient="records")  # local safety net

    raw_df.to_sql("raw_prices", engine, if_exists="append", index=False)
    print(f"Inserted {len(raw_df)} rows into raw_prices")

if __name__ == "__main__":
    fetch_prices()