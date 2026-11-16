import pandas as pd
import pandas_market_calendars as mcal


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

    for source, data in [("VIX", vix), ("Treasury", treasury)]:
        signal_dates = pd.DatetimeIndex(data["Date"])
        missing = price_dates.difference(signal_dates)
        extra = signal_dates.difference(price_dates)

        print(f"{source}: {len(missing)} S&P dates without an observation; {len(extra)} extra dates.")
        for label, dates in [("Missing on S&P date", missing), ("Outside S&P dates", extra)]:
            for date in dates:
                differences.append({
                    "Source": source,
                    "Date": date.strftime("%Y-%m-%d"),
                    "Difference": label,
                })

    output_folder.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(differences, columns=["Source", "Date", "Difference"])
    report.to_csv(output_folder / "calendar_differences.csv", index=False)
