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
