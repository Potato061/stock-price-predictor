import sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import text
import pickle
import os
sys.path.insert(0, "../src")
from engine_init import get_engine, TableFetcher
from temporal_split import temporal_split_
"""
Build LSTM sequences from the flat curated_features table.

Takes train/test DataFrames and converts them into 3D arrays:
(samples, timesteps, features) ready for LSTM input.

Scaling is fit on train data only, then applied to both train & test (no leakage).
Sequences are built per-symbol to keep ticker boundaries clean.
"""


def load_and_split(test_split=0.2):
    """Load curated_features from database and split temporally."""
    engine = get_engine()
    fetcher = TableFetcher(engine)
    df = fetcher.fetch_curated_features()
    df["price_datetime"] = pd.to_datetime(df["price_datetime"])

    train_df,test_df = temporal_split_(df, test_split)

    print(f"Loaded {len(df)} total rows")
    print(f"Train: {len(train_df)} | Test: {len(test_df)}")
    return train_df, test_df


def get_feature_columns(df):
    """Identify which columns are actual features (not metadata/target)."""
    exclude = {"symbol", "price_datetime", "built_at", "ingested_at", "target_next_return"}
    return [col for col in df.columns if col not in exclude]


def scale_data(train_df, test_df, feature_cols):
    """
    Fit MinMaxScaler on train data, apply to both train and test.
    Returns scaled DataFrames and the fitted scaler (for later inverse transform).
    """
    scaler = MinMaxScaler()

    train_scaled = train_df.copy()
    train_scaled[feature_cols] = scaler.fit_transform(train_df[feature_cols])

    test_scaled = test_df.copy()
    test_scaled[feature_cols] = scaler.transform(test_df[feature_cols])

    return train_scaled, test_scaled, scaler


def build_sequences(df, feature_cols, seq_length=30):
    """
    Convert a DataFrame into sequences of shape (samples, timesteps, features).

    Each row becomes:
    X: [30 days of features] → y: [target for day 31]

    Sequences are built per symbol to avoid cross-ticker leakage.
    Rows without enough prior history (first seq_length-1 rows per symbol) are dropped.
    """
    X_list, y_list, symbols_list = [], [], []

    for symbol in df["symbol"].unique():
        symbol_df = df[df["symbol"] == symbol].reset_index(drop=True)

        # Need seq_length rows before we can form the first sequence
        if len(symbol_df) < seq_length + 1:
            print(f"  WARNING: {symbol} has only {len(symbol_df)} rows, need {seq_length + 1} for sequences. Skipping.")
            continue

        # Slide a window of seq_length rows, creating one sample per window
        for i in range(len(symbol_df) - seq_length):
            X_seq = symbol_df[feature_cols].iloc[i: i + seq_length].values
            X_seq = X_seq.astype(np.float32)# shape: (seq_length, num_features)
            y_val = symbol_df["target_next_return"].iloc[i + seq_length]  # scalar target at position seq_length

            X_list.append(X_seq)
            y_list.append(y_val)
            symbols_list.append(symbol)

    X = np.array(X_list)  # shape: (samples, seq_length, num_features)
    y = np.array(y_list)  # shape: (samples,)

    print(f"Built sequences: X shape {X.shape}, y shape {y.shape}")
    return X, y, np.array(symbols_list)


def main():
    seq_length = 30  # use 30 days of history to predict day 31's return

    # Load and split
    train_df, test_df = load_and_split()

    # Identify features
    feature_cols = get_feature_columns(train_df)
    print(f"Features: {feature_cols}")

    # Scale (fit on train only)
    print("\nScaling data...")
    train_scaled, test_scaled, scaler = scale_data(train_df, test_df, feature_cols)

    # Build sequences
    print(f"\nBuilding sequences (seq_length={seq_length})...")
    X_train, y_train, train_symbols = build_sequences(train_scaled, feature_cols, seq_length=seq_length)
    X_test, y_test, test_symbols = build_sequences(test_scaled, feature_cols, seq_length=seq_length)

    print(f"\nFinal shapes:")
    print(f"  X_train: {X_train.shape} | y_train: {y_train.shape}")
    print(f"  X_test:  {X_test.shape} | y_test:  {y_test.shape}")

    # Save for use in training
    os.makedirs("models/data", exist_ok=True)
    np.save("models/data/X_train.npy", X_train)
    np.save("models/data/y_train.npy", y_train)
    np.save("models/data/X_test.npy", X_test)
    np.save("models/data/y_test.npy", y_test)
    np.save("models/data/train_symbols.npy", train_symbols)
    np.save("models/data/test_symbols.npy", test_symbols)

    with open("models/data/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    print("\nSaved:")
    print("  - X_train.npy, y_train.npy")
    print("  - X_test.npy, y_test.npy")
    print("  - train_symbols.npy, test_symbols.npy")
    print("  - scaler.pkl (for inverse transform later)")


if __name__ == "__main__":
    main()