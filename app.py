import streamlit as st
import yfinance as yf
import pandas as pd
from modules.tickers import (
    afegir_ticker_usuari,
    carregar_tickers,
    carregar_tickers_df,
    carregar_tickers_usuari_df,
    cercar_tickers_yahoo,
    eliminar_ticker_usuari
)

from datetime import datetime
from modules.market_fast import obtenir_dades_mercat
from modules.portfolio import genera_cartera
from modules.cartera import (
    obtenir_cartera_actual,
    obtenir_tickers_cartera
)



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

st.subheader("⭐ Els meus actius")

@st.cache_data(ttl=300)
def cercar_actius_yahoo(consulta):
    return cercar_tickers_yahoo(consulta)


cerca_actiu = st.text_input(
    "Cerca una empresa"
)

suggeriments_actius = cercar_actius_yahoo(
    cerca_actiu
)

ticker_usuari = ""

if suggeriments_actius:

    opcions_actius = {
        f"{actiu['Empresa']} ({actiu['Ticker']})": actiu['Ticker']
        for actiu in suggeriments_actius
    }

    actiu_seleccionat = st.selectbox(
        "Resultats",
        list(opcions_actius.keys())
    )

    ticker_usuari = opcions_actius[actiu_seleccionat]

elif cerca_actiu.strip():

    st.info(
        "No s'han trobat resultats a Yahoo Finance."
    )

if st.button("Afegir actiu"):

    try:

        nou_actiu = afegir_ticker_usuari(
            ticker_usuari
        )

        st.success(
            f"Actiu afegit correctament: "
            f"{nou_actiu['Empresa']} ({nou_actiu['Ticker']})"
        )

        st.cache_data.clear()
        st.rerun()

    except Exception as e:

        st.error(str(e))

actius_usuari = carregar_tickers_usuari_df()

if len(actius_usuari) > 0:

    st.dataframe(
        actius_usuari,
        width="stretch"
    )

    for _, actiu_usuari in actius_usuari.iterrows():

        col_actiu, col_eliminar = st.columns([4, 1])

        with col_actiu:
            st.write(
                f"{actiu_usuari['Empresa']} "
                f"({actiu_usuari['Ticker']})"
            )

        with col_eliminar:
            if st.button(
                "Eliminar",
                key=f"eliminar_{actiu_usuari['Ticker']}"
            ):

                eliminar_ticker_usuari(
                    actiu_usuari["Ticker"]
                )

                st.success(
                    "Actiu eliminat correctament."
                )

                st.cache_data.clear()
                st.rerun()

else:

    st.info(
        "Encara no has afegit cap actiu personal."
    )

tickers_df = carregar_tickers_df()
tickers = carregar_tickers()

@st.cache_data(ttl=300)
def carregar_mercat(tickers):
    return obtenir_dades_mercat(tickers)

with st.spinner("Analitzant mercat..."):

    df = carregar_mercat(tickers)

if len(df) == 0:

    st.error(
        "No s'han pogut obtenir dades."
    )

    st.stop()

df = df.sort_values(
    by="Score",
    ascending=False
)
tickers_cartera = obtenir_tickers_cartera()

df["A la cartera?"] = df["Ticker"].apply(
    lambda x: "✅ Sí" if x in tickers_cartera else "❌ No"
)

def recomanacio(fila):

    score = fila["Score"]
    te = fila["A la cartera?"] == "✅ Sí"

    if not te and score >= 80:
        return "🟢 Comprar"

    elif te and score >= 80:
        return "🟡 Mantenir"

    elif te and score < 60:
        return "🔴 Revisar"

    else:
        return "⚪ Esperar"


df["Recomanació"] = df.apply(
    recomanacio,
    axis=1
)

comprar = len(
    df[df["Recomanació"] == "🟢 Comprar"]
)

mantenir = len(
    df[df["Recomanació"] == "🟡 Mantenir"]
)

revisar = len(
    df[df["Recomanació"] == "🔴 Revisar"]
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

millor_compra = df[
    df["Recomanació"] == "🟢 Comprar"
]

if len(millor_compra) > 0:

    millor = millor_compra.iloc[0]

    st.success(
        f"""
⭐ Millor oportunitat d'avui

Empresa: {millor['Empresa']}

Score: {millor['Score']}

Potencial: {millor['Potencial %']} %

Risc: {millor['Risc']}
"""
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

st.subheader("📜 Històric de Moviments")

try:

    moviments = pd.read_csv(
        "data/moviments.csv"
    )

    st.dataframe(
        moviments,
        width="stretch"
    )

    st.subheader("🗑️ Eliminar Moviment")

    index_eliminar = st.selectbox(
        "Selecciona el moviment a eliminar",
        moviments.index,
        format_func=lambda x:
        f"{moviments.loc[x, 'Data']} | "
        f"{moviments.loc[x, 'Actiu']} | "
        f"{moviments.loc[x, 'Operacio']} | "
        f"{moviments.loc[x, 'Quantitat']}"
)

    if st.button("Eliminar moviment"):

        moviments = moviments.drop(
            index=index_eliminar
        )

        moviments.to_csv(
            "data/moviments.csv",
            index=False
        )

        st.success(
            "Moviment eliminat correctament."
         )

        st.rerun()

except:

    st.warning(
        "No hi ha moviments registrats."
    )

st.subheader("📂 La Meva Cartera")

cartera_actual = obtenir_cartera_actual()

if len(cartera_actual) > 0:

    cartera_actual["Capital Invertit"] = (
        cartera_actual["Quantitat"]
        * cartera_actual["Preu Mitjà"]
    )

    cartera_actual["Valor Actual"] = (
        cartera_actual["Quantitat"]
        * cartera_actual["Preu Actual"]
    )

    capital_invertit = (
        cartera_actual["Capital Invertit"]
        .sum()
    )

    valor_actual_total = (
        cartera_actual["Valor Actual"]
        .sum()
    )

    benefici_total = (
        valor_actual_total
        - capital_invertit
    )

    if capital_invertit > 0:

        rendibilitat_total = (
            benefici_total
            / capital_invertit
        ) * 100

    else:

        rendibilitat_total = 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "💰 Capital invertit",
            f"{capital_invertit:,.2f} €"
        )

    with col2:
        st.metric(
            "📈 Valor actual",
            f"{valor_actual_total:,.2f} €"
        )

    with col3:
        st.metric(
            "🚀 Benefici total",
            f"{benefici_total:,.2f} €"
        )

    with col4:
        st.metric(
            "📊 Rendibilitat",
            f"{rendibilitat_total:.2f}%"
        )

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