import yfinance as yf
import time

tickers = "MSFT NVDA AAPL AMZN META"

inici = time.perf_counter()

data = yf.download(
    tickers,
    period="1y",
    auto_adjust=True,
    progress=False,
    group_by="ticker"
)

temps = time.perf_counter() - inici

print(data.head())
print()
print(f"Temps: {temps:.2f} segons")
print()
print(data.columns)
print()
print(data.columns.names)