import pandas as pd
import yfinance as yf


def obtenir_cartera_actual():

    try:

        moviments = pd.read_csv(
            "data/moviments.csv"
        )

    except:

        return pd.DataFrame()

    if len(moviments) == 0:

        return pd.DataFrame()

    posicions = {}

    for _, fila in moviments.iterrows():

        ticker = fila["Ticker"]

        if ticker not in posicions:

            posicions[ticker] = {
                "Actiu": fila["Actiu"],
                "Ticker": ticker,
                "Quantitat": 0,
                "Cost Total": 0
            }

        if fila["Operacio"] == "Compra":

            posicions[ticker]["Quantitat"] += (
                fila["Quantitat"]
            )

            posicions[ticker]["Cost Total"] += (
                fila["Quantitat"] * fila["Preu"]
            )

        elif fila["Operacio"] == "Venda":

            posicions[ticker]["Quantitat"] -= (
                fila["Quantitat"]
            )

    cartera = []

    for ticker, dades in posicions.items():

        if dades["Quantitat"] <= 0:
            continue

        preu_mitja = (
            dades["Cost Total"]
            / dades["Quantitat"]
        )
        try:

            dades_yf = yf.download(
                ticker,
                period="5d",
                auto_adjust=True,
                progress=False
            )

            if isinstance(dades_yf.columns, pd.MultiIndex):
                preu_actual = float(
                    dades_yf["Close"].iloc[-1, 0]
                )
            else:
                preu_actual = float(
                    dades_yf["Close"].iloc[-1]
                )

        except:

            preu_actual = 0

        valor_actual = (
            dades["Quantitat"]
            * preu_actual
        )

        cost_total = (
            dades["Quantitat"]
            * preu_mitja
        )

        guany_euros = (
            valor_actual
            - cost_total
        )

        if cost_total > 0:

            guany_percent = (
                guany_euros
                / cost_total
            ) * 100

        else:

            guany_percent = 0

        cartera.append({

            "Actiu": dades["Actiu"],

            "Ticker": ticker,

            "Quantitat": round(
                dades["Quantitat"],
                4
            ),

            "Preu Mitjà": round(
                preu_mitja,
                2
            ),

            "Preu Actual": round(
                preu_actual,
                2
            ),

            "Guany €": round(
                guany_euros,
                2
            ),

            "Guany %": round(
                guany_percent,
                2
            )
        })

    return pd.DataFrame(cartera)

def obtenir_tickers_cartera():

    cartera = obtenir_cartera_actual()

    if len(cartera) == 0:
        return []

    return cartera["Ticker"].tolist()