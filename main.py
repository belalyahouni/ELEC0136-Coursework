from pathlib import Path

from acquisition import load_prices, load_vix, load_treasury
from storage import connect_database, create_tables, has_saved_data, read_data, save_data


def main():
    data_folder = Path(__file__).parent / "data"

    connection = connect_database(data_folder)
    try:
        create_tables(connection)
        if has_saved_data(connection):
            prices, vix, treasury = read_data(connection)
            print("Loaded saved data from SQLite.")
        else:
            prices = load_prices(data_folder)
            vix = load_vix(data_folder)
            treasury = load_treasury(data_folder)
            save_data(connection, prices, vix, treasury)
            print("Saved validated data to SQLite.")

        print(f"Rows: {len(prices)} prices, {len(vix)} VIX, {len(treasury)} Treasury.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
