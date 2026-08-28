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
from sqlalchemy import text


def load_stg_prices(engine) :
    query = text("SELECT * FROM stg_prices")
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

engine = get_engine()
stg_df = load_stg_prices(engine)


class FeatureBuilder:
    def __init__(self, df):
        self.df = df.sort_values(['symbol', 'price_datetime']).copy()
    def add_lag_features(self):
        self.df['prev_close'] = self.df.groupby('symbol')['close_price'].shift(1)
        return self
    def add_returns(self):
        self.df['daily_return'] = (self.df['close_price'] - self.df['prev_close']) / self.df['prev_close']
        return self

    def add_moving_averages(self):
        self.df['ma_5'] = self.df.groupby('symbol')['close_price'].transform(lambda x: x.rolling(5).mean())
        self.df['ma_20'] = self.df.groupby('symbol')['close_price'].transform(lambda x: x.rolling(20).mean())
        return self

    def add_volatility(self, window=10):
        self.df[f"volatility_{window}"] = self.df.groupby("symbol")["daily_return"].transform(lambda x: x.rolling(window).std())
        return self

    def build(self):
        return self.df.dropna()



def main():
    engine = get_engine()
    stg_df = load_stg_prices(engine)

    builder = (
        FeatureBuilder(stg_df)
        .add_lag_features()
        .add_returns()
        .add_moving_averages()
        .add_volatility()
    )
    features_df = builder.build()

    print(f"Built features: {features_df.shape}")

    features_df["built_at"] = pd.Timestamp.utcnow()

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM curated_features"))  # clear before reload, same pattern as stg_prices

    final_cols = [
        "symbol", "price_datetime", "open_price", "high_price",
        "low_price", "close_price", "volume",
        "prev_close", "daily_return", "ma_5", "ma_20", "volatility_10",
        "built_at",
    ]
    features_df = features_df[final_cols]

    features_df.to_sql("curated_features", engine, if_exists="append", index=False)
    print(f"Inserted {len(features_df)} rows into curated_features.")


if __name__ == "__main__":
    main()