from pathlib import Path

from acquisition import load_prices, load_vix, load_treasury
from storage import connect_database, create_tables


def main():
    data_folder = Path(__file__).parent / "data"

    prices = load_prices(data_folder)
    vix = load_vix(data_folder)
    treasury = load_treasury(data_folder)

    connection = connect_database(data_folder)
    try:
        create_tables(connection)
        print("SQLite tables are ready: prices, vix, treasury.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
