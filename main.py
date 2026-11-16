from pathlib import Path

from acquisition import load_prices, load_vix, load_treasury


def main():
    data_folder = Path(__file__).parent / "data"

    prices = load_prices(data_folder)
    vix = load_vix(data_folder)
    treasury = load_treasury(data_folder)


if __name__ == "__main__":
    main()
