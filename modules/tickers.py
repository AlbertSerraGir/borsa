import pandas as pd


def carregar_tickers():

    df = pd.read_csv("data/tickers.csv")

    tickers = {}

    for _, fila in df.iterrows():

        tickers[fila["Empresa"]] = (
            fila["Ticker"],
            fila["Sector"]
        )

    return tickers