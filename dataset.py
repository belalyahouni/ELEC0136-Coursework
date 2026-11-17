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

