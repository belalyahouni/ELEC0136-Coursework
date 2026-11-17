import matplotlib

matplotlib.use("Agg")  # Save figures without opening a window.
import matplotlib.pyplot as plt
import pandas as pd


def explore_data(prices, vix, treasury, output_folder):
    """Plot the study data and list large changes for manual inspection."""
    output_folder.mkdir(parents=True, exist_ok=True)
    prices = prices.sort_values("Date")
    vix = vix.sort_values("Date")
    treasury = treasury.sort_values("Date")

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    axes[0].plot(prices["Date"], prices["Close"])
    axes[0].set_title("S&P 500 closing level")
    axes[0].set_ylabel("Index points")

    axes[1].plot(vix["Date"], vix["VIX"], color="darkorange")
    axes[1].set_title("VIX closing level")
    axes[1].set_ylabel("VIX points")

    axes[2].plot(treasury["Date"], treasury["Yield_10Y"], color="seagreen")
    axes[2].set_title("10-year Treasury yield (Yahoo ^TNX)")
    axes[2].set_ylabel("Annualised yield (%)")
    axes[2].set_xlabel("Date")

    for ax in axes:
        ax.grid(alpha=0.25)
    fig.suptitle("Source data overview: 2020–2025")
    fig.tight_layout()
    fig.savefig(output_folder / "data_overview.png", dpi=150)
    plt.close(fig)

    series = [
        ("S&P 500", prices, "Close", "%"),
        ("VIX", vix, "VIX", "index points"),
        ("Treasury 10Y", treasury, "Yield_10Y", "percentage points"),
    ]
    largest_changes = []
    for name, data, column, unit in series:
        # Compare consecutive available values for this report only.
        # The source frames and database keep all missing observations.
        changes = data[["Date", column]].dropna(subset=[column]).rename(columns={column: "Value"}).copy()
        changes["Previous_date"] = changes["Date"].shift(1)
        changes["Previous_value"] = changes["Value"].shift(1)
        if name == "S&P 500":
            changes["Change"] = changes["Value"].pct_change(fill_method=None) * 100
        else:
            changes["Change"] = changes["Value"].diff()

        # Rank changes between consecutive observations, including holiday gaps.
        changes["Absolute_change"] = changes["Change"].abs()
        changes["Series"] = name
        changes["Unit"] = unit
        largest_changes.append(changes.nlargest(5, "Absolute_change"))

    report = pd.concat(largest_changes, ignore_index=True)
    report = report[["Series", "Previous_date", "Date", "Previous_value", "Value", "Change", "Unit"]]
    report.to_csv(output_folder / "largest_changes.csv", index=False)
    print("Saved data_overview.png and largest_changes.csv. No observations changed.")
