import yfinance as yf
import time
import pandas as pd


from modules.scoring import calcula_score


def obtenir_dades_mercat(tickers):
    inici = time.perf_counter()
    resultats = []

    # Crear diccionari per consultar dades
    info_tickers = {}

    # Llista de tickers
    llista_tickers = []

    for nom, info in tickers.items():

        ticker = info[0]

        sector = info[1]

        info_tickers[ticker] = {
        "Empresa": nom,
        "Sector": sector
    }

        llista_tickers.append(ticker)

    for ticker in llista_tickers:
        nom = info_tickers[ticker]["Empresa"]
        sector = info_tickers[ticker]["Sector"]
        temps_empresa = time.perf_counter()

        try:

            data = yf.download(
                ticker,
                period="1y",
                auto_adjust=True,
                progress=False
            )

            if len(data) < 200:
                continue

            if isinstance(data.columns, pd.MultiIndex):
                close = data["Close"].iloc[:, 0]
            else:
                close = data["Close"]

            preu = float(close.iloc[-1])

            ma50 = float(
                close.rolling(50).mean().iloc[-1]
            )

            ma200 = float(
                close.rolling(200).mean().iloc[-1]
            )

            momentum = float(
                (preu / close.iloc[-126] - 1) * 100
            )

            volatilitat = float(
                close.pct_change().std() * 100
            )

            maxim = float(close.max())

            distancia_maxim = float(
                ((preu / maxim) - 1) * 100
            )

            es_etf = sector == "ETF"

            score = calcula_score(
                preu,
                ma50,
                ma200,
                momentum,
                volatilitat,
                distancia_maxim,
                es_etf
            )

            confiança = round(score / 10, 1)

            if volatilitat < 2:
                risc = "Baix"
            elif volatilitat < 4:
                risc = "Mitjà"
            else:
                risc = "Alt"

            if score >= 80:
                accio = "Comprar fort"
            elif score >= 60:
                accio = "Comprar"
            else:
                accio = "Esperar"

            durada = time.perf_counter() - temps_empresa

            print(f"{nom:<25} {durada:.2f} s")      

            resultats.append({
                "Empresa": nom,
                "Sector": sector,
                "Ticker": ticker,
                "Preu": round(preu, 2),
                "Preu objectiu": round(maxim, 2),
                "Potencial %": round(
                    ((maxim / preu) - 1) * 100,
                    2
            ),
                "Momentum %": round(momentum, 2),
                "Volatilitat": round(volatilitat, 2),
                "Distància màxim %": round(distancia_maxim, 2),
                "Risc": risc,
                "Score": score,
                "Confiança": confiança,
                "Acció": accio
        })

        except Exception as e:

            print(f"Error amb {ticker}: {e}")

    df = pd.DataFrame(resultats)

    temps = time.perf_counter() - inici

    print("")
    print("=" * 50)
    print(f"Temps total: {temps:.2f} segons")
    print(f"Empreses analitzades: {len(df)}")
    print("=" * 50)
    print("")

    return df