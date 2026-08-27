"""
Phase 3a — Fetch metadata into the ITEMS table.

Run this BEFORE fetch_prices.py — raw_prices has a FK to items.symbol,
so items must be populated first or every price insert will fail.

Source: Wikipedia's S&P 500 constituent list.
- Free, no API key, no rate limit, no paywall risk
- Already includes GICS Sector / Sub-Industry, so no need to call
  Twelve Data's /profile endpoint at all
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def get_engine():
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_NAME", "StockPrices")
    conn_str = f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    return create_engine(conn_str)


def get_sp500_table():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url, headers=headers)
    sp500 = pd.read_html(response.text)[0]
    return sp500


def build_items_df(sp500):
    # Pick ~100 symbols spread across sectors (same sampling logic as fetch_prices)
    picked = (
        sp500.groupby("GICS Sector", group_keys=False)
        .apply(lambda x: x.sample(min(len(x), 10), random_state=42))
        .head(100)
    )

    items_df = pd.DataFrame({
        "symbol": picked["Symbol"],
        "exchange": None,          # not in this table; leave NULL or fill later
        "mic_code": None,
        "currency": "USD",         # safe default, all S&P 500 trade in USD
        "asset_type": "Common Stock",
        "company_name": picked["Security"]
    })
    return items_df.reset_index(drop=True)



def main():
    sp500 = get_sp500_table()
    items_df = build_items_df(sp500)

    os.makedirs("data/raw_backups", exist_ok=True)
    items_df.to_csv("data/raw_backups/items_backup.csv", index=False)

    print(f"Built {len(items_df)} item rows.")
    print(items_df.head())

    engine = get_engine()
    items_df.to_sql("items", engine, if_exists="append", index=False)
    print("Inserted into items table.")


if __name__ == "__main__":
    main()