import sqlite3


def connect_database(data_folder):
    """Open our local database file, creating it if needed."""
    data_folder.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(data_folder / "coursework.db")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_tables(connection):
    """Create the data tables in the connected coursework database."""
    cursor = connection.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                date TEXT PRIMARY KEY NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vix (
                date TEXT PRIMARY KEY NOT NULL,
                vix REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasury (
                date TEXT PRIMARY KEY NOT NULL,
                yield_2y REAL NOT NULL,
                yield_10y REAL NOT NULL
            )
        """)
        connection.commit()
    finally:
        cursor.close()
