# ELEC0136 coursework

Daily S&P 500, VIX and 10-year Treasury yield data from Yahoo Finance through
`yfinance`, covering 2020–2025. The pipeline acquires, validates, stores and
explores data, then aligns external signals to S&P sessions. Features and modelling come later.

```sh
conda env create -f environment.yml
conda activate mlsd-coursework
python main.py
```

For an existing environment, use
`conda env update -n mlsd-coursework -f environment.yml`.

- Symbols: `^GSPC` (OHLC/volume), `^VIX` (Close), `^TNX` (Close).
- TNX is a yield in percent. There is no 2-year yield.
- CSVs and SQLite live in `data/yfinance/`.
- Reruns use SQLite. Without a database, saved CSVs rebuild it; missing CSVs are downloaded.
- Missing VIX/yield values are retained as SQL NULL for later date alignment.
- `main.py` validates CSV/downloaded data before saving it to SQLite.
- Database reruns trust the previously validated tables.
- CSVs preserve acquisition results; they are not proof that validation passed.
- Plots, calendar differences and large-change reports are saved in `outputs/`.
- Large changes compare available values without altering stored observations.
- `outputs/aligned_data.csv` keeps every S&P session with same-date VIX and yield values and one combined availability flag; missing values are never filled.
- Existing `calendar_differences.csv` records absent dates, null values and extra dates. Source SQLite tables remain unchanged.
- Daily observations are assumed available that evening; historical publication times have not been verified. Unavailable rows remain in the calendar so later sample construction can exclude affected windows without skipping sessions.

The user's real downloads passed local rebuild and database-reuse checks.
Yahoo may revise historical data or fail to respond; saved CSVs allow local reuse.
