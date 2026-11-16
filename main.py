from pathlib import Path

from acquisition import load_prices, load_vix, load_treasury
from exploration import explore_data
from storage import connect_database, create_tables, has_saved_data, read_data, save_data
from validation import check_price_dates, compare_signal_dates


def main():
    data_folder = Path(__file__).parent / "data"

    connection = connect_database(data_folder)
    try:
        create_tables(connection)
        saved_data = has_saved_data(connection)
        if saved_data:
            prices, vix, treasury = read_data(connection)
            print("Loaded saved data from SQLite.")
        else:
            prices = load_prices(data_folder)
            vix = load_vix(data_folder)
            treasury = load_treasury(data_folder)

        check_price_dates(prices)
        output_folder = Path(__file__).parent / "outputs"
        compare_signal_dates(prices, vix, treasury, output_folder)

        if not saved_data:
            save_data(connection, prices, vix, treasury)
            print("Saved validated data to SQLite.")

        print(f"Rows: {len(prices)} prices, {len(vix)} VIX, {len(treasury)} Treasury.")
        explore_data(prices, vix, treasury, output_folder)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
