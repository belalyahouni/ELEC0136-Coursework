import numpy as np
import pandas as pd


def align_data(prices, vix, treasury, output_folder):
    """Match same-day data, assumed available that evening, to S&P sessions."""
    aligned = prices.sort_values("Date").reset_index(drop=True)
    aligned = aligned.merge(vix[["Date", "VIX"]], on="Date", how="left",
                            validate="one_to_one")
    aligned = aligned.merge(treasury[["Date", "Yield_10Y"]], on="Date", how="left",
                            validate="one_to_one")

    # Keep missing rows so later windows do not skip trading sessions.
    aligned["Signals_available"] = aligned["VIX"].notna() & aligned["Yield_10Y"].notna()
    output_folder.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(output_folder / "aligned_data.csv", index=False)
    print(f"Aligned {len(aligned)} S&P sessions; "
          f"{(~aligned['Signals_available']).sum()} have unavailable signals.")
    return aligned


def calculate_features(aligned, output_folder):
    """Calculate seven daily features using current and earlier sessions only."""
    features = pd.DataFrame({"Date": aligned["Date"]})
    features["SP_log_return"] = np.log(aligned["Close"] / aligned["Close"].shift(1))
    features["Intraday_range"] = (aligned["High"] - aligned["Low"]) / aligned["Close"]
    features["Price_to_SMA20"] = aligned["Close"] / aligned["Close"].rolling(20).mean()
    features["VIX"] = aligned["VIX"]
    features["VIX_change"] = aligned["VIX"].diff()
    features["Yield_10Y"] = aligned["Yield_10Y"]
    features["Yield_change"] = aligned["Yield_10Y"].diff()

    # Keep warm-up and missing rows; sample construction will exclude affected windows.
    output_folder.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_folder / "daily_features.csv", index=False)
    print(f"Calculated features: {len(features.dropna())} complete daily rows.")
    return features

