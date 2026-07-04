import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import yfinance as yf


COLUMNES_TICKERS = [
    "Empresa",
    "Ticker",
    "Sector",
    "Pais",
    "Index"
]

FITXER_TICKERS_BASE = "data/tickers.csv"
FITXER_TICKERS_USUARI = "data/tickers_usuari.csv"
INDEX_USUARI = "Usuari"


def assegurar_fitxer_tickers_usuari():
    try:
        pd.read_csv(FITXER_TICKERS_USUARI)
    except FileNotFoundError:
        pd.DataFrame(columns=COLUMNES_TICKERS).to_csv(
            FITXER_TICKERS_USUARI,
            index=False
        )


def normalitzar_tickers_df(df):
    for columna in COLUMNES_TICKERS:
        if columna not in df.columns:
            df[columna] = ""

    df = df[COLUMNES_TICKERS].copy()
    df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
    df["Empresa"] = df["Empresa"].astype(str).str.strip()
    df["Sector"] = df["Sector"].astype(str).str.strip()
    df["Pais"] = df["Pais"].astype(str).str.strip()
    df["Index"] = df["Index"].astype(str).str.strip()

    df = df[df["Ticker"] != ""]
    df = df.drop_duplicates(subset="Ticker", keep="first")

    return df.reset_index(drop=True)


def carregar_tickers_usuari_df():
    assegurar_fitxer_tickers_usuari()
    df = pd.read_csv(FITXER_TICKERS_USUARI)
    return normalitzar_tickers_df(df)


def carregar_tickers_df():
    assegurar_fitxer_tickers_usuari()

    tickers_base = pd.read_csv(FITXER_TICKERS_BASE)
    tickers_usuari = pd.read_csv(FITXER_TICKERS_USUARI)

    df = pd.concat(
        [tickers_base, tickers_usuari],
        ignore_index=True
    )

    return normalitzar_tickers_df(df)


def carregar_tickers():
    df = carregar_tickers_df()

    tickers = {}

    for _, fila in df.iterrows():
        tickers[fila["Empresa"]] = (
            fila["Ticker"],
            fila["Sector"]
        )

    return tickers


def cercar_tickers_yahoo(consulta, limit=10):
    consulta = consulta.strip()

    if len(consulta) < 2:
        return []

    params = urlencode({
        "q": consulta,
        "quotesCount": limit,
        "newsCount": 0,
        "enableFuzzyQuery": False,
        "quotesQueryId": "tss_match_phrase_query"
    })

    request = Request(
        f"https://query2.finance.yahoo.com/v1/finance/search?{params}",
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []

    resultats = []
    tickers_vistos = set()

    for resultat in payload.get("quotes", []):
        ticker = str(resultat.get("symbol", "")).strip().upper()
        empresa = (
            resultat.get("longname")
            or resultat.get("shortname")
            or resultat.get("name")
            or ""
        )
        tipus = resultat.get("quoteType", "")

        if not ticker or not empresa or ticker in tickers_vistos:
            continue

        if tipus not in {"EQUITY", "ETF", "MUTUALFUND", "INDEX"}:
            continue

        tickers_vistos.add(ticker)
        resultats.append({
            "Empresa": empresa,
            "Ticker": ticker
        })

        if len(resultats) >= limit:
            break

    return resultats


def obtenir_info_yahoo(ticker):
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Introdueix un ticker.")

    actiu = yf.Ticker(ticker)
    historial = actiu.history(period="5d")

    if historial.empty:
        raise ValueError("Aquest ticker no existeix a Yahoo Finance.")

    info = actiu.get_info()

    empresa = (
        info.get("longName")
        or info.get("shortName")
        or ticker
    )

    sector = info.get("sector") or "Usuari"
    pais = info.get("country") or "Usuari"

    return {
        "Empresa": empresa,
        "Ticker": ticker,
        "Sector": sector,
        "Pais": pais,
        "Index": INDEX_USUARI
    }


def afegir_ticker_usuari(ticker):
    assegurar_fitxer_tickers_usuari()
    ticker = ticker.strip().upper()

    tickers_actuals = carregar_tickers_df()

    if ticker in tickers_actuals["Ticker"].tolist():
        raise ValueError("Aquest ticker ja existeix a la llista.")

    nou_actiu = obtenir_info_yahoo(ticker)
    tickers_usuari = carregar_tickers_usuari_df()

    tickers_usuari = pd.concat(
        [tickers_usuari, pd.DataFrame([nou_actiu])],
        ignore_index=True
    )

    tickers_usuari = normalitzar_tickers_df(tickers_usuari)
    tickers_usuari.to_csv(
        FITXER_TICKERS_USUARI,
        index=False
    )

    return nou_actiu


def eliminar_ticker_usuari(ticker):
    assegurar_fitxer_tickers_usuari()
    ticker = ticker.strip().upper()

    tickers_usuari = carregar_tickers_usuari_df()
    tickers_usuari = tickers_usuari[
        tickers_usuari["Ticker"] != ticker
    ]

    tickers_usuari.to_csv(
        FITXER_TICKERS_USUARI,
        index=False
    )
