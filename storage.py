import sqlite3

import pandas as pd


def connect_database(data_folder):
    """Open our local database file, creating it if needed."""
    data_folder.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(data_folder / "coursework.db")


def create_tables(connection):
    """Create the data tables in the connected coursework database."""
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS prices (
            date TEXT PRIMARY KEY NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS vix (
            date TEXT PRIMARY KEY NOT NULL,
            vix REAL
        );
        CREATE TABLE IF NOT EXISTS treasury (
            date TEXT PRIMARY KEY NOT NULL,
            yield_10y REAL
        );
    """)


def save_data(connection, prices, vix, treasury):
    """Save the validated study data, replacing the previous contents."""
    tables = [
        ("prices", prices, ["Date", "Open", "High", "Low", "Close", "Volume"]),
        ("vix", vix, ["Date", "VIX"]),
        ("treasury", treasury, ["Date", "Yield_10Y"]),
    ]

    # Commit all three tables together, or undo the changes if an insert fails.
    with connection:
        for table, data, columns in tables:
            if data.empty:
                raise ValueError(f"Cannot save an empty {table} dataset.")
            rows = data[columns].copy()
            rows["Date"] = rows["Date"].dt.strftime("%Y-%m-%d")
            placeholders = ", ".join(["?"] * len(columns))

            # Table names come from the fixed list above; values use placeholders.
            connection.execute(f"DELETE FROM {table}")
            connection.executemany(
                f"INSERT INTO {table} VALUES ({placeholders})",
                rows.itertuples(index=False, name=None),
            )


def has_saved_data(connection):
    """Check all three tables have data from a previous import."""
    for table in ("prices", "vix", "treasury"):
        if connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone() is None:
            return False
    return True


def read_data(connection):
    """Load the saved tables with the same column names as the source data."""
    prices = pd.read_sql_query("""
        SELECT date AS Date, open AS Open, high AS High, low AS Low,
               close AS Close, volume AS Volume
        FROM prices ORDER BY date
    """, connection, parse_dates=["Date"])

    vix = pd.read_sql_query("""
        SELECT date AS Date, vix AS VIX
        FROM vix ORDER BY date
    """, connection, parse_dates=["Date"])

    treasury = pd.read_sql_query("""
        SELECT date AS Date, yield_10y AS Yield_10Y
        FROM treasury ORDER BY date
    """, connection, parse_dates=["Date"])

    return prices, vix, treasury
