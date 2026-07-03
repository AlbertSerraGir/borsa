import math
import re
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "data" / "tickers.csv"
TARGET_TOTAL = 300
VALIDATION_CHUNK_SIZE = 80
REQUEST_PAUSE_SECONDS = 0


@dataclass(frozen=True)
class IndexConfig:
    name: str
    country: str
    url: str
    suffix: str = ""
    quota: int = 0


INDEX_CONFIGS = [
    IndexConfig(
        name="S&P 500",
        country="EUA",
        url="https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        quota=150,
    ),
    IndexConfig(
        name="Nasdaq-100",
        country="EUA",
        url="https://en.wikipedia.org/wiki/Nasdaq-100",
        quota=60,
    ),
    IndexConfig(
        name="IBEX 35",
        country="Espanya",
        url="https://en.wikipedia.org/wiki/IBEX_35",
        suffix=".MC",
        quota=25,
    ),
    IndexConfig(
        name="DAX",
        country="Alemanya",
        url="https://en.wikipedia.org/wiki/DAX",
        suffix=".DE",
        quota=25,
    ),
    IndexConfig(
        name="CAC 40",
        country="Franca",
        url="https://en.wikipedia.org/wiki/CAC_40",
        suffix=".PA",
        quota=25,
    ),
    IndexConfig(
        name="AEX",
        country="Paisos Baixos",
        url="https://en.wikipedia.org/wiki/AEX_index",
        suffix=".AS",
        quota=15,
    ),
    IndexConfig(
        name="SMI",
        country="Suissa",
        url="https://en.wikipedia.org/wiki/Swiss_Market_Index",
        suffix=".SW",
        quota=15,
    ),
    IndexConfig(
        name="FTSE MIB",
        country="Italia",
        url="https://en.wikipedia.org/wiki/FTSE_MIB",
        suffix=".MI",
        quota=15,
    ),
]


COLUMN_ALIASES = {
    "Empresa": [
        "company",
        "company name",
        "constituent",
        "name",
        "security",
        "component",
    ],
    "Ticker": [
        "symbol",
        "ticker",
        "ticker symbol",
        "epic",
        "code",
    ],
    "Sector": [
        "gics sector",
        "sector",
        "industry",
        "icb industry",
        "icb supersector",
        "supersector",
    ],
}


MANUAL_TICKER_FIXES = {
    "BRK.B": "BRK-B",
    "BF.B": "BF-B",
}


EUROPEAN_SUFFIXES = (".AS", ".DE", ".MC", ".MI", ".PA", ".SW")


def clean_text(value):
    if pd.isna(value):
        return ""

    text = str(value)
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_column_name(column):
    if isinstance(column, tuple):
        column = " ".join(clean_text(part) for part in column if clean_text(part))

    column = clean_text(column).lower()
    column = re.sub(r"[^a-z0-9]+", " ", column)
    return re.sub(r"\s+", " ", column).strip()


def find_column(columns, aliases):
    normalized = {normalize_column_name(column): column for column in columns}

    for alias in aliases:
        if alias in normalized:
            return normalized[alias]

    for normalized_name, original_name in normalized.items():
        if any(alias in normalized_name for alias in aliases):
            return original_name

    return None


def normalize_yahoo_ticker(raw_ticker, suffix):
    ticker = clean_text(raw_ticker).upper()
    ticker = ticker.split(" ")[0]
    ticker = ticker.replace("/", "-")

    if not ticker or ticker in {"NAN", "-"}:
        return ""

    ticker = MANUAL_TICKER_FIXES.get(ticker, ticker)

    if suffix and not ticker.endswith(EUROPEAN_SUFFIXES):
        ticker = f"{ticker}{suffix}"
    elif not suffix:
        ticker = ticker.replace(".", "-")

    return ticker


def pick_constituents_table(tables):
    best_table = None
    best_score = -1

    for table in tables:
        empresa_col = find_column(table.columns, COLUMN_ALIASES["Empresa"])
        ticker_col = find_column(table.columns, COLUMN_ALIASES["Ticker"])

        if empresa_col is None or ticker_col is None:
            continue

        score = len(table)
        sector_col = find_column(table.columns, COLUMN_ALIASES["Sector"])
        if sector_col is not None:
            score += 1000

        if score > best_score:
            best_table = table
            best_score = score

    return best_table


def load_index_constituents(config):
    tables = pd.read_html(config.url)
    table = pick_constituents_table(tables)

    if table is None:
        raise ValueError(f"No s'ha trobat cap taula valida per a {config.name}")

    empresa_col = find_column(table.columns, COLUMN_ALIASES["Empresa"])
    ticker_col = find_column(table.columns, COLUMN_ALIASES["Ticker"])
    sector_col = find_column(table.columns, COLUMN_ALIASES["Sector"])

    rows = []
    for _, row in table.iterrows():
        empresa = clean_text(row.get(empresa_col, ""))
        ticker = normalize_yahoo_ticker(row.get(ticker_col, ""), config.suffix)
        sector = clean_text(row.get(sector_col, "")) if sector_col is not None else "N/D"

        if not empresa or not ticker:
            continue

        rows.append({
            "Empresa": empresa,
            "Ticker": ticker,
            "Sector": sector or "N/D",
            "Pais": config.country,
            "Index": config.name,
            "_quota": config.quota,
            "_order": len(rows),
        })

    return rows


def remove_duplicates(rows):
    seen = set()
    unique_rows = []

    for row in rows:
        ticker = row["Ticker"]
        if ticker in seen:
            continue

        seen.add(ticker)
        unique_rows.append(row)

    return unique_rows


def has_price_data(downloaded, ticker):
    if downloaded.empty:
        return False

    if isinstance(downloaded.columns, pd.MultiIndex):
        if ticker not in downloaded.columns.get_level_values(0):
            return False

        ticker_data = downloaded[ticker]
    else:
        ticker_data = downloaded

    price_column = "Close" if "Close" in ticker_data.columns else "Adj Close"
    if price_column not in ticker_data.columns:
        return False

    return ticker_data[price_column].dropna().shape[0] > 0


def validate_yahoo_tickers(rows):
    valid_tickers = set()
    tickers = [row["Ticker"] for row in rows]
    total_chunks = math.ceil(len(tickers) / VALIDATION_CHUNK_SIZE)

    for chunk_number, start in enumerate(range(0, len(tickers), VALIDATION_CHUNK_SIZE), start=1):
        chunk = tickers[start:start + VALIDATION_CHUNK_SIZE]
        print(f"Validant Yahoo Finance {chunk_number}/{total_chunks}: {len(chunk)} tickers")

        try:
            downloaded = yf.download(
                chunk,
                period="5d",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as exc:
            print(f"Error validant bloc {chunk_number}: {exc}")
            downloaded = pd.DataFrame()

        for ticker in chunk:
            if has_price_data(downloaded, ticker):
                valid_tickers.add(ticker)

        time.sleep(REQUEST_PAUSE_SECONDS)

    return [row for row in rows if row["Ticker"] in valid_tickers]


def select_balanced_rows(rows):
    selected = []
    selected_tickers = set()

    for config in INDEX_CONFIGS:
        index_rows = [row for row in rows if row["Index"] == config.name]
        for row in index_rows[:config.quota]:
            selected.append(row)
            selected_tickers.add(row["Ticker"])

    if len(selected) >= TARGET_TOTAL:
        return selected[:TARGET_TOTAL]

    remaining = [row for row in rows if row["Ticker"] not in selected_tickers]

    while len(selected) < TARGET_TOTAL and remaining:
        added_in_round = False

        for config in INDEX_CONFIGS:
            row = next((item for item in remaining if item["Index"] == config.name), None)
            if row is None:
                continue

            selected.append(row)
            selected_tickers.add(row["Ticker"])
            remaining = [item for item in remaining if item["Ticker"] != row["Ticker"]]
            added_in_round = True

            if len(selected) >= TARGET_TOTAL:
                break

        if not added_in_round:
            break

    return selected


def build_ticker_csv():
    all_rows = []

    for config in INDEX_CONFIGS:
        print(f"Carregant {config.name}...")
        rows = load_index_constituents(config)
        print(f"  {len(rows)} constituents trobats")
        all_rows.extend(rows)

    unique_rows = remove_duplicates(all_rows)
    print(f"Tickers unics abans de validar: {len(unique_rows)}")

    valid_rows = validate_yahoo_tickers(unique_rows)
    print(f"Tickers valids a Yahoo Finance: {len(valid_rows)}")

    selected_rows = select_balanced_rows(valid_rows)
    output_rows = [
        {column: row[column] for column in ["Empresa", "Ticker", "Sector", "Pais", "Index"]}
        for row in selected_rows
    ]

    df = pd.DataFrame(output_rows, columns=["Empresa", "Ticker", "Sector", "Pais", "Index"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"CSV generat: {OUTPUT_PATH}")
    print(f"Actius guardats: {len(df)}")


if __name__ == "__main__":
    build_ticker_csv()
