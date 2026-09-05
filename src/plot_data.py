import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from engine_init import get_engine, TableFetcher
from temporal_split import temporal_split_

engine = get_engine()
fetcher = TableFetcher(engine)
df = fetcher.fetch_curated_features()
df["price_datetime"] = pd.to_datetime(df["price_datetime"])

train_df, test_df = temporal_split_(df, test_split=0.2)

# Pick a few symbols to visualize
symbols_to_plot = df["symbol"].unique()[:5]

fig, axes = plt.subplots(len(symbols_to_plot), 1, figsize=(15, 4 * len(symbols_to_plot)))

for idx, symbol in enumerate(symbols_to_plot):
    sym_data = df[df["symbol"] == symbol]

    # Plot 1: close_price over time, with train/test split
    ax1 = axes[idx]
    train_sym = sym_data[sym_data["price_datetime"] < train_df["price_datetime"].max()]
    test_sym = sym_data[sym_data["price_datetime"] >= test_df["price_datetime"].min()]
    ax1.plot(train_sym["price_datetime"], train_sym["close_price"], label="train", alpha=0.7)
    ax1.plot(test_sym["price_datetime"], test_sym["close_price"], label="test", alpha=0.7)
    ax1.set_title(f"{symbol} close price")
    ax1.legend()
    ax1.grid()

# Add padding to x-axis labels
for ax_row in axes:
    if isinstance(ax_row, np.ndarray):
        for ax in ax_row:
            ax.tick_params(axis='x', pad=-25)  # increase pad value if needed
    else:
        ax_row.tick_params(axis='x', pad=-25)


plt.tight_layout()
plt.savefig("data/eda_plots.png", dpi=150)
plt.show()
print("Saved to data/eda_plots.png")