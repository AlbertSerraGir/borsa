import streamlit as st
import yfinance as yf
import pandas as pd

from datetime import datetime
from modules.market import obtenir_dades_mercat
from modules.portfolio import genera_cartera
from modules.cartera import obtenir_cartera_actual



st.set_page_config(
    page_title="Assessor d'Inversió",
    layout="wide"
)

st.title("📈 Assessor d'Inversió Personal")

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

tickers = {

    # ETFs
    "SP500 ETF": ("SPY", "ETF"),
    "Nasdaq ETF": ("QQQ", "ETF"),
    "MSCI World ETF": ("URTH", "ETF"),

    # Tecnologia
    "Microsoft": ("MSFT", "Tecnologia"),
    "Nvidia": ("NVDA", "Tecnologia"),
    "Apple": ("AAPL", "Tecnologia"),
    "Amazon": ("AMZN", "Tecnologia"),
    "Alphabet": ("GOOGL", "Tecnologia"),
    "Meta": ("META", "Tecnologia"),
    "ASML": ("ASML", "Tecnologia"),

    # Bancs
    "Santander": ("SAN.MC", "Bancari"),
    "BBVA": ("BBVA.MC", "Bancari"),
    "JPMorgan": ("JPM", "Bancari"),

    # Salut
    "Johnson & Johnson": ("JNJ", "Salut"),
    "UnitedHealth": ("UNH", "Salut"),

    # Utilities
    "Iberdrola": ("IBE.MC", "Utilities"),

    # Consum
    "Coca-Cola": ("KO", "Consum"),
    "Costco": ("COST", "Consum"),
    "Inditex": ("ITX.MC", "Consum"),
    "Visa": ("V", "Financer")
}

with st.spinner("Analitzant mercat..."):

    df = obtenir_dades_mercat(tickers)


if len(df) == 0:

    st.error(
        "No s'han pogut obtenir dades."
    )

    st.stop()

df = df.sort_values(
    by="Score",
    ascending=False
)


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Actius analitzats",
        len(df)
    )

with col2:
    st.metric(
        "Millor Score",
        int(df.iloc[0]["Score"])
    )

with col3:
    st.metric(
        "Millor oportunitat",
        df.iloc[0]["Empresa"]
    )

st.subheader("🏆 Ranking d'Oportunitats")

st.dataframe(
    df,
    width="stretch"
)

st.subheader("📈 Anàlisi Gràfica")

empresa_seleccionada = st.selectbox(
    "Selecciona un actiu",
    df["Empresa"].tolist()
)

st.write(
    f"Actiu seleccionat: {empresa_seleccionada}"
)

ticker_seleccionat = tickers[
    empresa_seleccionada
][0]

dades = yf.download(
    ticker_seleccionat,
    period="1y",
    auto_adjust=True,
    progress=False
)

if isinstance(dades.columns, pd.MultiIndex):
    close = dades["Close"].iloc[:, 0]
else:
    close = dades["Close"]

graf_df = pd.DataFrame()

graf_df["Preu"] = close
graf_df["MA50"] = close.rolling(50).mean()
graf_df["MA200"] = close.rolling(200).mean()

st.line_chart(
    graf_df,
    height=450
)

st.subheader("🤖 Anàlisi Automàtica")

preu_actual = close.iloc[-1]
ma50_actual = graf_df["MA50"].iloc[-1]
ma200_actual = graf_df["MA200"].iloc[-1]

if preu_actual > ma50_actual and ma50_actual > ma200_actual:

    tendencia = "🟢 Alcista"

    comentari = """
El preu es troba per sobre de la MA50 i la MA200.

La MA50 també està per sobre de la MA200.

La tendència continua sent positiva.
"""

elif preu_actual > ma50_actual:

    tendencia = "🟡 Moderadament alcista"

    comentari = """
El preu està per sobre de la MA50 però la tendència de llarg termini encara no és totalment favorable.
"""

else:

    tendencia = "🔴 Baixista"

    comentari = """
El preu es troba per sota de la MA50.

La tendència actual mostra debilitat i es recomana prudència.
"""

st.success(
    f"Tendència detectada: {tendencia}"
)

st.info(comentari)

cartera = genera_cartera(
    df,
    capital,
    perfil
)

st.subheader("💼 Cartera Recomanada")

st.dataframe(
    cartera,
    width="stretch"
)

st.subheader("📂 La Meva Cartera")

cartera_actual = obtenir_cartera_actual()

st.dataframe(
    cartera_actual,
    width="stretch"
)

st.subheader("➕ Registrar Operació")

with st.form("nova_operacio"):

    data_operacio = st.date_input(
        "Data"
    )

    operacio = st.selectbox(
        "Operació",
        ["Compra", "Venda"]
    )

    tipus = st.selectbox(
        "Tipus",
        ["Accio", "ETF", "Cripto"]
    )

    actiu = st.text_input(
        "Nom de l'actiu"
    )

    ticker = st.text_input(
        "Ticker"
    )

    quantitat = st.number_input(
        "Quantitat",
        min_value=0.0001,
        value=1.0
    )

    preu = st.number_input(
        "Preu",
        min_value=0.0,
        value=0.0
    )

    boto_guardar = st.form_submit_button(
        "Guardar operació"
    )

    if boto_guardar:

        nova_operacio = pd.DataFrame([{
            "Data": data_operacio.strftime("%Y-%m-%d"),
            "Operacio": operacio,
            "Tipus": tipus,
            "Actiu": actiu,
            "Ticker": ticker.upper(),
            "Quantitat": quantitat,
            "Preu": preu
        }])

        try:

            moviments = pd.read_csv(
                "data/moviments.csv"
            )

            moviments = pd.concat(
                [moviments, nova_operacio],
                ignore_index=True
            )

        except:

            moviments = nova_operacio

        moviments.to_csv(
            "data/moviments.csv",
            index=False
        )

        st.success(
            "Operació guardada correctament."
        )

        st.rerun()

millor = df.iloc[0]

st.subheader("🤖 Resum del Sistema")

st.info(
    f"""
Millor oportunitat detectada: {millor['Empresa']}

Score: {millor['Score']}/100

Confiança: {millor['Confiança']}/10

Nivell de risc: {millor.get('Risc', 'No disponible')}

Perfil seleccionat: {perfil}

Capital disponible: {capital} €
"""
)