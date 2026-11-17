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


def build_samples(aligned, features, output_folder):
    """Pair complete 20-session windows with the next open-to-open return."""
    values = features.drop(columns="Date").to_numpy()
    next_open = aligned["Open"].shift(-1)
    following_open = aligned["Open"].shift(-2)
    targets = following_open / next_open - 1
    windows = []
    records = []
    incomplete = 0

    # First 19 sessions cannot end a full window. last two lack targets.
    for t in range(19, len(features) - 2):
        window = values[t - 19:t + 1]
        if np.isnan(window).any():
            incomplete += 1
            continue
        windows.append(window)
        records.append({
            "Window_start": aligned["Date"].iloc[t - 19],
            "Decision_date": aligned["Date"].iloc[t],
            "Execution_date": aligned["Date"].iloc[t + 1],
            "Target_end_date": aligned["Date"].iloc[t + 2],
            "Target_return": targets.iloc[t],
        })

    if not windows:
        raise ValueError("No complete 20-day samples. Check the available data.")

    samples = pd.DataFrame(records)
    X = np.array(windows)
    y = samples["Target_return"].to_numpy(dtype=float)
    output_folder.mkdir(parents=True, exist_ok=True)
    samples.to_csv(output_folder / "sample_timeline.csv", index=False)
    print(f"Built {len(X)} samples of 20 days * {values.shape[1]} features; "
          f"{incomplete} windows excluded for missing features.")
    return X, y, samples


def prepare_folds(X, y, samples, output_folder):
    """Prepare expanding training sets and yearly validation sets, excluding 2025."""
    folds = []
    summary = []
    for year in [2022, 2023, 2024]:
        cutoff = pd.Timestamp(year=year - 1, month=12, day=31)
        year_end = pd.Timestamp(year=year, month=12, day=31)

        # Every training outcome must already be known at the cutoff.
        train = samples["Target_end_date"] <= cutoff
        validation = (
            (samples["Decision_date"].dt.year == year)
            & (samples["Target_end_date"] <= year_end)
        )
        if not train.any() or not validation.any():
            raise ValueError(f"Not enough samples for the {year} fold.")

        X_train = X[train]
        X_validation = X[validation]
        # One mean and standard deviation per feature, across training windows.
        mean = X_train.mean(axis=(0, 1))
        std = X_train.std(axis=(0, 1))
        std[std == 0] = 1  # Avoid division by zero for a constant feature.

        folds.append({
            "year": year,
            "X_train": (X_train - mean) / std,
            "y_train": y[train],
            "X_validation": (X_validation - mean) / std,
            "y_validation": y[validation],
            "train_dates": samples.loc[train].reset_index(drop=True),
            "validation_dates": samples.loc[validation].reset_index(drop=True),
            "mean": mean,
            "std": std,
        })
        summary.append({
            "Validation_year": year,
            "Training_cutoff": cutoff,
            "Training_samples": int(train.sum()),
            "Validation_samples": int(validation.sum()),
            "Last_training_target": samples.loc[train, "Target_end_date"].max(),
            "First_validation_decision": samples.loc[validation, "Decision_date"].min(),
            "Last_validation_target": samples.loc[validation, "Target_end_date"].max(),
        })
        print(f"{year}: {train.sum()} training samples, {validation.sum()} validation samples.")

    output_folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary).to_csv(output_folder / "split_summary.csv", index=False)
    return folds

