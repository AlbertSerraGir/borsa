import pandas as pd

def genera_cartera(df, capital, perfil):

    # Filtre de risc segons perfil
    if perfil == "Conservador":

        df_filtrat = df[
            df["Risc"].isin(["Baix", "Mitjà"])
        ]

        pesos = [70, 20, 10]

    elif perfil == "Moderat":

        df_filtrat = df.copy()

        pesos = [50, 30, 20]

    else:

        df_filtrat = df.copy()

        pesos = [40, 35, 25]

    sectors_utilitzats = []
    seleccionades = []

    for _, fila in df_filtrat.iterrows():

        if fila["Sector"] not in sectors_utilitzats:

            seleccionades.append(fila)

            sectors_utilitzats.append(
                fila["Sector"]
            )

        if len(seleccionades) == 3:
            break

    top = pd.DataFrame(seleccionades)

    cartera = []

    for i in range(min(3, len(top))):

        cartera.append({
            "Actiu": top.iloc[i]["Empresa"],
            "Sector": top.iloc[i]["Sector"],
            "Score": top.iloc[i]["Score"],
            "Risc": top.iloc[i]["Risc"],
            "%": pesos[i],
            "Import (€)": round(
                capital * pesos[i] / 100,
                2
            )
        })

    return pd.DataFrame(cartera)