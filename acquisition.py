import pandas as pd
import yfinance as yf


def load_source(data_folder, ticker, name, columns):
    """Download one daily series, or reuse its saved CSV."""
    data_folder.mkdir(parents=True, exist_ok=True)
    csv_path = data_folder / f"{name}.csv"

    if csv_path.exists():
        print(f"Using saved {name} CSV.")
        data = pd.read_csv(csv_path, parse_dates=["Date"])
    else:
        print(f"Downloading {ticker}...")
        # The end date is exclusive. Keep missing rows for later alignment.
        data = yf.download(
            ticker, start="2020-01-01", end="2026-01-01",
            auto_adjust=False, keepna=True, multi_level_index=False,
            progress=False,
        )
        if data is None or data.empty:
            raise ValueError(f"No data returned for {ticker}.")
        data = data.reset_index()[["Date", *columns]].rename(columns=columns)

        data.to_csv(csv_path, index=False)
    return data


def load_prices(data_folder):
    return load_source(data_folder, "^GSPC", "prices", {
        column: column for column in ["Open", "High", "Low", "Close", "Volume"]
    })


def load_vix(data_folder):
    return load_source(data_folder, "^VIX", "vix", {"Close": "VIX"})


def load_treasury(data_folder):
    return load_source(data_folder, "^TNX", "treasury", {"Close": "Yield_10Y"})
