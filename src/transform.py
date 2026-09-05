import os
import json
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from engine_init import get_engine
load_dotenv()


def load_raw_prices(engine):
    """Pull every row from raw_prices into a DataFrame."""
    query = text("SELECT symbol, raw_json FROM raw_prices")
    with engine.connect() as conn:
        raw_df = pd.read_sql(query, conn)
    return raw_df


def unpack_row(symbol, raw_json_str):
    """Parse one raw_json blob into a flat DataFrame of daily rows."""
    data = json.loads(raw_json_str)

    if "values" not in data:
        print(f"  WARNING: no 'values' key for {symbol} — response may be an error/status message")
        return pd.DataFrame()

    values_df = pd.json_normalize(data["values"])
    values_df["symbol"] = symbol
    return values_df


def build_stg_prices(raw_df):
    """Loop over every raw_prices row, unpack, concat, clean, validate."""
    all_frames = []

    for _, row in raw_df.iterrows():
        symbol = row["symbol"]
        frame = unpack_row(symbol, row["raw_json"])
        if not frame.empty:
            all_frames.append(frame)

    if not all_frames:
        raise ValueError("No usable data unpacked from raw_prices — check raw_json contents.")

    stg_df = pd.concat(all_frames, ignore_index=True)

    # ---- Type conversion ----
    stg_df["price_datetime"] = pd.to_datetime(stg_df["datetime"])
    for col in ["open", "high", "low", "close"]:
        stg_df[col] = pd.to_numeric(stg_df[col], errors="coerce")
    stg_df["volume"] = pd.to_numeric(stg_df["volume"], errors="coerce").astype("Int64")

    # Rename to match stg_prices schema
    stg_df = stg_df.rename(columns={
        "open": "open_price",
        "high": "high_price",
        "low": "low_price",
        "close": "close_price",
    })

    # ---- Validation ----
    before = len(stg_df)

    # Drop rows missing required fields
    stg_df = stg_df.dropna(subset=["symbol", "price_datetime", "close_price"])

    # Drop exact duplicate (symbol, price_datetime) pairs, keep first
    stg_df = stg_df.drop_duplicates(subset=["symbol", "price_datetime"], keep="first")

    after = len(stg_df)
    print(f"Validation: {before} rows -> {after} rows after cleaning ({before - after} dropped)")

    stg_df["ingested_at"] = pd.Timestamp.utcnow()

    # Keep only the columns stg_prices actually has
    final_cols = [
        "symbol", "price_datetime", "open_price", "high_price",
        "low_price", "close_price", "volume", "ingested_at",
    ]
    stg_df = stg_df[final_cols]

    return stg_df


def main():
    engine = get_engine()

    print("Loading raw_prices...")
    raw_df = load_raw_prices(engine)
    print(f"Loaded {len(raw_df)} raw rows (one per symbol fetch).")

    print("Unpacking JSON into flat rows...")
    stg_df = build_stg_prices(raw_df)
    print(f"Built {len(stg_df)} clean daily price rows for {stg_df['symbol'].nunique()} symbols.")

    os.makedirs("../data/raw_backups", exist_ok=True)
    stg_df.to_csv("data/raw_backups/stg_prices_backup.csv", index=False)

    print("Writing to stg_prices (replacing existing contents)...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM stg_prices"))  # clear before reload, keeps table consistent on re-runs
    stg_df.to_sql("stg_prices", engine, if_exists="append", index=False)

    print("Done. stg_prices is up to date.")


if __name__ == "__main__":
    main()