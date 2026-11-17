from pathlib import Path

from acquisition import load_prices, load_vix, load_treasury
from dataset import align_data
from exploration import explore_data
from storage import connect_database, create_tables, has_saved_data, read_data, save_data
from validation import validate_source, check_price_dates, compare_signal_dates


def main():
    project_folder = Path(__file__).parent
    data_folder = project_folder / "data" / "yfinance"
    output_folder = project_folder / "outputs"

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

            validate_source(prices, "prices")
            validate_source(vix, "vix")
            validate_source(treasury, "treasury")
            check_price_dates(prices)

            save_data(connection, prices, vix, treasury)
            print("Saved validated data to SQLite.")

        compare_signal_dates(prices, vix, treasury, output_folder)
        align_data(prices, vix, treasury, output_folder)
        print(f"Rows: {len(prices)} prices, {len(vix)} VIX, {len(treasury)} Treasury.")
        explore_data(prices, vix, treasury, output_folder)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
