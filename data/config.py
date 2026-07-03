import streamlit as st
import yfinance as yf
import pandas as pd

from modules.scoring import calcula_score
from modules.portfolio import genera_cartera

st.set_page_config(
    page_title="Assessor d'Inversió",
    layout="wide"
)

st.title("📈 Assessor d'Inversió Personal")

# -------------------------
# CONFIGURACIÓ
# -------------------------

capital = st.number_input(
    "Capital disponible (€)",
    min_value=100,
    value=1000,
    step=100
)

perfil = st.selectbox(
    "Perfil d'inversor",
    [
        "Conservador",
        "Moderat",
        "Agressiu"
    ]
)

# -------------------------
# ACTIUS
# -------------------------

tickers = {

    # ETFs
    "SP500 ETF": "SPY",
    "Nasdaq ETF": "QQQ",
    "MSCI World ETF": "URTH",

    # Tecnologia
    "Microsoft": "MSFT",
    "Nvidia": "NVDA",
    "Apple": "AAPL",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",

    # Financers
    "Visa": "V",
    "JPMorgan": "JPM",
    "Santander": "SAN.MC",
    "BBVA": "BBVA.MC",

    # Salut
    "Johnson & Johnson": "JNJ",
    "UnitedHealth": "UNH",

    # Europa
    "ASML": "ASML",
    "Inditex": "ITX.MC",
    "Iberdrola": "IBE.MC",

    # Consum
    "Coca-Cola": "KO",
    "Costco": "COST"
}

# -------------------------
# ANÀLISI
# -------------------------

resultats = []

with st.spinner("Analitzant mercat..."):

    for nom, ticker in tickers.items():

        try:

            data = yf.download(
                ticker,
                period="1y",
                auto_adjust=True,
                progress=False
            )

            if len(data) < 200:
                continue

            close = data.iloc[:, 0]

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

            score = calcula_score(
                preu,
                ma50,
                ma200,
                momentum
            )

            confiança = round(
                score / 10,
                1
            )

            if score >= 90:
                accio = "Comprar fort"

            elif score >= 70:
                accio = "Comprar"

            else:
                accio = "Esperar"

            resultats.append({
                "Empresa": nom,
                "Ticker": ticker,
                "Preu": round(preu, 2),
                "Momentum %": round(momentum, 2),
                "Volatilitat": round(volatilitat, 2),
                "Score": score,
                "Confiança": confiança,
                "Acció": accio
            })

        except Exception as e:

            st.warning(
                f"Error amb {ticker}: {e}"
            )

# -------------------------
# RESULTATS
# -------------------------

df = pd.DataFrame(resultats)

if len(df) == 0:

    st.error(
        "No s'han trobat dades."
    )

    st.stop()

df = df.sort_values(
    by="Score",
    ascending=False
)

st.subheader(
    "🏆 Ranking d'Oportunitats"
)

st.dataframe(
    df,
    use_container_width=True
)

# -------------------------
# CARTERA
# -------------------------

st.subheader(
    "💼 Cartera Recomanada"
)

cartera = genera_cartera(
    df,
    capital,
    perfil
)

st.dataframe(
    cartera,
    use_container_width=True
)

# -------------------------
# RESUM
# -------------------------

millor = df.iloc[0]

st.subheader(
    "🤖 Resum"
)

st.info(
    f"""
Millor oportunitat actual:
{millor['Empresa']}

Score:
{millor['Score']}/100

Confiança:
{millor['Confiança']}/10

Perfil:
{perfil}

Capital:
{capital} €
"""
)