import xml.etree.ElementTree as ET

import kagglehub
import numpy as np
import pandas as pd
import requests


def load_prices(data_folder):
    """Download or reuse S&P 500 data, check it, and return the study rows."""
    data_folder.mkdir(parents=True, exist_ok=True)
    csv_path = data_folder / "sap500.csv"

    if not csv_path.exists():
        print("Downloading S&P 500 data...")
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

    return prices


def load_vix(data_folder):
    """Download or reuse VIX data, check it, and return the study rows."""
    data_folder.mkdir(parents=True, exist_ok=True)
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

    return vix


def load_treasury(data_folder):
    """Download or reuse Treasury data, check it, and return the study rows."""
    data_folder.mkdir(parents=True, exist_ok=True)
    treasury_rows = []
    url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"

    for year in range(2020, 2026):
        treasury_path = data_folder / f"treasury_{year}.xml"
        if not treasury_path.exists():
            print(f"Downloading Treasury data for {year}...")
            response = requests.get(
                url,
                params={"data": "daily_treasury_yield_curve", "field_tdr_date_value": year},
                timeout=30,
            )
            response.raise_for_status()
            treasury_path.write_bytes(response.content)
        else:
            print(f"Using the saved Treasury XML for {year}.")

        # Each XML properties element contains one day's rates.
        root = ET.parse(treasury_path).getroot()
        rows = root.findall(".//{*}properties")
        if not rows:
            raise ValueError(f"No Treasury observations found for {year}.")

        for row in rows:
            date = pd.to_datetime(row.findtext("{*}NEW_DATE"))
            if pd.isna(date) or date.year != year:
                raise ValueError(f"Missing or incorrect date in Treasury file for {year}.")
            treasury_rows.append({
                "Date": date,
                "Yield_2Y": row.findtext("{*}BC_2YEAR"),
                "Yield_10Y": row.findtext("{*}BC_10YEAR"),
            })

    if not treasury_rows:
        raise ValueError("No Treasury observations found in the downloaded files.")

    treasury = pd.DataFrame(treasury_rows)
    treasury["Date"] = pd.to_datetime(treasury["Date"])
    treasury[["Yield_2Y", "Yield_10Y"]] = treasury[["Yield_2Y", "Yield_10Y"]].apply(pd.to_numeric)
    treasury = treasury[treasury["Date"].between("2020-01-01", "2025-12-31")].copy()

    print("Treasury date range:", treasury["Date"].min().date(), "to", treasury["Date"].max().date())
    print("Treasury row count:", len(treasury))

    missing_yields = treasury.isna().sum().sum()
    duplicate_treasury_dates = treasury["Date"].duplicated().sum()
    invalid_yields = ~np.isfinite(treasury[["Yield_2Y", "Yield_10Y"]]).all(axis=1)

    print("Treasury missing values:", missing_yields)
    print("Treasury duplicate dates:", duplicate_treasury_dates)
    print("Treasury rows with nonfinite yields:", invalid_yields.sum())

    if missing_yields > 0 or duplicate_treasury_dates > 0 or invalid_yields.any():
        raise ValueError("Treasury validation failed. Check the data before continuing.")
    return treasury
