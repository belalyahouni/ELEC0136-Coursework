from pathlib import Path

import kagglehub
import numpy as np
import pandas as pd


def main():
    data_folder = Path(__file__).parent / "data"
    csv_path = data_folder / "sap500.csv"

    if not csv_path.exists():
        print("Downloading S&P 500 data...")
        data_folder.mkdir(parents=True, exist_ok=True)
        # Use a fixed version so dataset does not change between runs.
        kagglehub.dataset_download(
            "paveljurke/s-and-p-500-gspc-historical-data/versions/806",
            path="sap500.csv",
            output_dir=str(data_folder),
        )
    else:
        print("Using the saved S&P 500 CSV.")

    prices = pd.read_csv(csv_path)
    prices["Date"] = pd.to_datetime(prices["Date"])

    # Keep only the dates in our study period.
    prices = prices[prices["Date"].between("2020-01-01", "2025-12-31")].copy()

    print("Columns:", prices.columns.tolist())
    print("Date range:", prices["Date"].min().date(), "to", prices["Date"].max().date())
    print("Row count:", len(prices))

    # Check the selected data before using it.
    missing_values = prices.isna().sum().sum()
    duplicate_dates = prices["Date"].duplicated().sum()

    print("Missing values:", missing_values)
    print("Duplicate dates:", duplicate_dates)

    if missing_values > 0 or duplicate_dates > 0:
        raise ValueError("Missing values or duplicate dates found. Check the data before continuing.")

    price_columns = ["Open", "High", "Low", "Close"]
    prices[price_columns] = prices[price_columns].apply(pd.to_numeric)
    values = prices[price_columns]

    # A price must be finite and greater than zero.
    invalid_prices = (~np.isfinite(values) | (values <= 0)).any(axis=1)

    # Open and Close must lie within the day's price range.
    invalid_ranges = (
        (prices["Open"] < prices["Low"])
        | (prices["Open"] > prices["High"])
        | (prices["Close"] < prices["Low"])
        | (prices["Close"] > prices["High"])
    )

    print("Rows with invalid prices:", invalid_prices.sum())
    print("Rows with invalid price ranges:", invalid_ranges.sum())

    if invalid_prices.any() or invalid_ranges.any():
        raise ValueError("Invalid prices found. Check the data before continuing.")


if __name__ == "__main__":
    main()
