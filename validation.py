import numpy as np
import pandas as pd
import pandas_market_calendars as mcal


def validate_source(data, name):
    """Check newly loaded data before it is stored in SQLite."""
    columns = {
        "prices": ["Open", "High", "Low", "Close", "Volume"],
        "vix": ["VIX"],
        "treasury": ["Yield_10Y"],
    }[name]
    if data.empty or not {"Date", *columns}.issubset(data.columns):
        raise ValueError(f"{name}: empty data or missing required columns.")
    dates = data["Date"]
    if dates.isna().any() or dates.duplicated().any():
        raise ValueError(f"{name}: missing or duplicate dates.")
    if not dates.between("2020-01-01", "2025-12-31").all():
        raise ValueError(f"{name}: dates outside the study period.")
    values = data[columns].apply(pd.to_numeric, errors="raise")
    print(f"{name}: {values.isna().sum().sum()} missing values.")
    if np.isinf(values).any().any():
        raise ValueError(f"{name}: infinite values.")
    if name == "prices":
        if values.isna().any().any():
            raise ValueError("prices: missing values.")
        ohlc = values[["Open", "High", "Low", "Close"]]
        if (ohlc <= 0).any().any():
            raise ValueError("prices: OHLC values must be positive.")
        if not (
            values["Open"].between(values["Low"], values["High"])
            & values["Close"].between(values["Low"], values["High"])
        ).all():
            raise ValueError("prices: invalid OHLC ranges.")
        if ((values["Volume"] < 0) | (values["Volume"] % 1 != 0)).any():
            raise ValueError("prices: volume must be a nonnegative integer.")
    elif name == "vix" and (values["VIX"] <= 0).any():
        raise ValueError("vix: levels must be positive.")
    print(f"Validated {name}: {len(data)} rows, {dates.min().date()} to {dates.max().date()}.")


def check_price_dates(prices):
    """Compare S&P dates with the NYSE trading calendar for our study period."""
    calendar = mcal.get_calendar("NYSE")
    expected_dates = calendar.valid_days("2020-01-01", "2025-12-31").tz_localize(None)
    actual_dates = pd.DatetimeIndex(prices["Date"])

    missing_dates = expected_dates.difference(actual_dates)
    unexpected_dates = actual_dates.difference(expected_dates)

    print("Missing S&P trading dates:", len(missing_dates))
    print("Unexpected S&P dates:", len(unexpected_dates))

    if len(missing_dates) > 0 or len(unexpected_dates) > 0:
        print("Missing:", missing_dates.strftime("%Y-%m-%d").tolist())
        print("Unexpected:", unexpected_dates.strftime("%Y-%m-%d").tolist())
        raise ValueError("S&P dates do not match the trading calendar. Check the data.")


def compare_signal_dates(prices, vix, treasury, output_folder):
    """Record calendar differences without filling or removing observations."""
    price_dates = pd.DatetimeIndex(prices["Date"])
    differences = []

    for source, data, column in [("VIX", vix, "VIX"), ("Treasury", treasury, "Yield_10Y")]:
        signal_dates = pd.DatetimeIndex(data["Date"])
        missing = price_dates.difference(signal_dates)
        extra = signal_dates.difference(price_dates)

        print(f"{source}: {len(missing)} S&P dates without an observation; {len(extra)} extra dates.")
        empty = pd.DatetimeIndex(data.loc[data[column].isna(), "Date"]).intersection(price_dates)
        print(f"{source}: {len(empty)} S&P dates with a missing value.")
        for label, dates in [("Missing on S&P date", missing), ("Outside S&P dates", extra),
                             ("Missing value on S&P date", empty)]:
            for date in dates:
                differences.append({
                    "Source": source,
                    "Date": date.strftime("%Y-%m-%d"),
                    "Difference": label,
                })

    output_folder.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(differences, columns=["Source", "Date", "Difference"])
    report.to_csv(output_folder / "calendar_differences.csv", index=False)
