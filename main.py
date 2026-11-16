from pathlib import Path

import kagglehub
import numpy as np
import pandas as pd
import requests


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

    vix_path = data_folder / "VIX_History.csv"
    if not vix_path.exists():
        print("Downloading VIX data...")
        url = "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        vix_path.write_bytes(response.content)
    else:
        print("Using the saved VIX CSV.")

    # We only need the date and closing VIX level.
    vix = pd.read_csv(vix_path, usecols=["DATE", "CLOSE"])
    vix = vix.rename(columns={"DATE": "Date", "CLOSE": "VIX"})
    vix["Date"] = pd.to_datetime(vix["Date"], format="%m/%d/%Y")
    if vix["Date"].isna().any():
        raise ValueError("VIX data contains missing dates.")
    vix = vix[vix["Date"].between("2020-01-01", "2025-12-31")].copy()

    if vix.empty:
        raise ValueError("No VIX data found for 2020–2025.")

    print("VIX date range:", vix["Date"].min().date(), "to", vix["Date"].max().date())
    print("VIX row count:", len(vix))

    vix["VIX"] = pd.to_numeric(vix["VIX"])
    missing_vix = vix.isna().sum().sum()
    duplicate_vix_dates = vix["Date"].duplicated().sum()
    invalid_vix = ~np.isfinite(vix["VIX"]) | (vix["VIX"] <= 0)

    print("VIX missing values:", missing_vix)
    print("VIX duplicate dates:", duplicate_vix_dates)
    print("VIX invalid values:", invalid_vix.sum())

    if missing_vix > 0 or duplicate_vix_dates > 0 or invalid_vix.any():
        raise ValueError("VIX validation failed. Check the data before continuing.")


if __name__ == "__main__":
    main()
