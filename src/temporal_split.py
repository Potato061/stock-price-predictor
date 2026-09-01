from engine_init import get_engine
import pandas as pd
from sqlalchemy import text

engine = get_engine()


def load_curated_features(engine):
    query = text("SELECT * FROM curated_features ORDER BY symbol,price_datetime")
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

def temporal_split_(dataset, test_split=0.2):
    dataset = dataset.sort_values(["symbol", "price_datetime"]).copy()

    cutoff_date = dataset["price_datetime"].quantile(1 - test_split)
    print(f"Cutoff Date: {cutoff_date}")

    train_df = dataset[dataset["price_datetime"] < cutoff_date].copy()
    test_df = dataset[dataset["price_datetime"] >= cutoff_date].copy()

    print(f"Train: {len(train_df)} rows | Test: {len(test_df)} rows")
    print(f"Train date range: {train_df['price_datetime'].min()} -> {train_df['price_datetime'].max()}")
    print(f"Test date range:  {test_df['price_datetime'].min()} -> {test_df['price_datetime'].max()}")

    return train_df, test_df


if __name__ == "__main__":
    engine = get_engine()
    df = load_curated_features(engine)
    train_df, test_df = temporal_split_(df)

    """
        If a symbol's data happens to end before the cutoff
        it'll have zero test rows, and later evaluation for that symbol won't be meaningful.
    """

    train_symbols = set(train_df["symbol"].unique())
    test_symbols = set(test_df["symbol"].unique())
    print("Symbols missing from test:", train_symbols - test_symbols)