import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


# =========================
# CONFIGURACIÓN DE LA APP
# =========================
st.set_page_config(page_title="PAC - Rango para Jarras", layout="wide")
st.title("Recomendación de rango PAC para prueba de jarras")


# =========================
# FUNCIÓN PARA LIMPIAR DATOS
# =========================
@st.cache_data
def cargar_y_limpiar_excel(archivo_excel: str) -> pd.DataFrame:
    df = pd.read_excel(archivo_excel)

    columnas = [
        'Caudal A tratar (L/s)',
        'Turbiedad de agua cruda (UNT)',
        'pH de agua cruda (Unid)',
        'Alcalinidad de agua cruda (mg/L)',
        'Caudal de dosificación del PAC (mL/min)'
    ]

    for col in columnas:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(' ', '', regex=False)
            .str.replace(',,', ',', regex=False)
            .str.replace(',', '.', regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=columnas).copy()
    return df


# =========================
# FUNCIÓN PRINCIPAL
# =========================
def calcular_rango_pac(
    df: pd.DataFrame,
    caudal: float,
    turbiedad: float,
    ph: float,
    alcalinidad: float
):
    variables = [
        'Caudal A tratar (L/s)',
        'Turbiedad de agua cruda (UNT)',
        'pH de agua cruda (Unid)',
        'Alcalinidad de agua cruda (mg/L)'
    ]

    # Caso nuevo
    nuevo = pd.DataFrame([{
        'Caudal A tratar (L/s)': caudal,
        'Turbiedad de agua cruda (UNT)': turbiedad,
        'pH de agua cruda (Unid)': ph,
        'Alcalinidad de agua cruda (mg/L)': alcalinidad
    }])

    # Prefiltro
    df_base = df[
        (df['Caudal A tratar (L/s)'].between(caudal - 15, caudal + 15)) &
        (df['Turbiedad de agua cruda (UNT)'].between(turbiedad - 8, turbiedad + 8)) &
        (df['pH de agua cruda (Unid)'].between(ph - 0.15, ph + 0.15)) &
        (df['Alcalinidad de agua cruda (mg/L)'].between(alcalinidad - 5, alcalinidad + 5))
    ].copy()

    if len(df_base) < 5:
        return {
            "ok": False,
            "mensaje": "Muy pocos datos después del prefiltro. Amplía un poco los rangos o revisa el histórico."
        }

    # Escalado
    scaler = StandardScaler()
    X_hist = scaler.fit_transform(df_base[variables])
    X_new = scaler.transform(nuevo[variables])

    # Pesos
    pesos = np.array([3, 4, 3, 2], dtype=float)
    X_hist = X_hist * pesos
    X_new = X_new * pesos

    # Vecinos similares
    n_neighbors = min(8, len(df_base))
    knn = NearestNeighbors(n_neighbors=n_neighbors)
    knn.fit(X_hist)
    distancias, indices = knn.kneighbors(X_new)

    similares = df_base.iloc[indices[0]].copy()
    similares['distancia'] = distancias[0]
    similares = similares.sort_values('distancia')

    # Quitar extremos por IQR
    col_pac = 'Caudal de dosificación del PAC (mL/min)'
    q1 = similares[col_pac].quantile(0.25)
    q3 = similares[col_pac].quantile(0.75)
    iqr = q3 - q1

    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr

    similares_filtrados = similares[
        (similares[col_pac] >= lim_inf) &
        (similares[col_pac] <= lim_sup)
    ].copy()

    if len(similares_filtrados) < 3:
        return {
            "ok": False,
            "mensaje": "Después de quitar extremos quedaron muy pocos casos. Revisa el histórico o amplía rangos."
        }

    pac_min = float(similares_filtrados[col_pac].min())
    pac_max = float(similares_filtrados[col_pac].max())
    pac_mediana = float(similares_filtrados[col_pac].median())
    std = float(similares_filtrados[col_pac].std()) if len(similares_filtrados) > 1 else 0.0
    n = int(len(similares_filtrados))
    ancho_rango = pac_max - pac_min

    # Regla: usar rango real si es aceptable; si no, usar mediana ±10%
    if n < 5:
        usar_rango = False
        motivo = "Muy pocos casos"
    elif std > 40:
        usar_rango = False
        motivo = "Demasiada dispersión"
    elif ancho_rango > 0.4 * pac_mediana:
        usar_rango = False
        motivo = "Rango demasiado amplio"
    else:
        usar_rango = True
        motivo = "Rango aceptable"

    if usar_rango:
        dosis_min = pac_min
        dosis_max = pac_max
        metodo = "Rango histórico real"
    else:
        dosis_min = pac_mediana * 0.90
        dosis_max = pac_mediana * 1.10
        metodo = "Mediana ±10%"

    jarras = np.round(np.linspace(dosis_min, dosis_max, 6), 1)
    tabla_jarras = pd.DataFrame({
        "Jarra": [1, 2, 3, 4, 5, 6],
        "Dosis PAC (mL/min)": jarras
    })

    columnas_mostrar = variables + [col_pac, 'distancia']
    similares_filtrados = similares_filtrados[columnas_mostrar]

    return {
        "ok": True,
        "df_base_n": len(df_base),
        "similares_filtrados": similares_filtrados,
        "pac_min": pac_min,
        "pac_max": pac_max,
        "pac_mediana": pac_mediana,
        "std": std,
        "n": n,
        "ancho_rango": ancho_rango,
        "usar_rango": usar_rango,
        "motivo": motivo,
        "metodo": metodo,
        "dosis_min": dosis_min,
        "dosis_max": dosis_max,
        "tabla_jarras": tabla_jarras
    }


# =========================
# CARGA DEL ARCHIVO
# =========================
st.subheader("1) Archivo histórico")

opcion_archivo = st.radio(
    "¿Cómo quieres cargar el archivo?",
    ["Usar archivo local 2026 PTAP CALDAS.xlsx", "Subir archivo manualmente"]
)

df = None

if opcion_archivo == "Usar archivo local 2026 PTAP CALDAS.xlsx":
    try:
        df = cargar_y_limpiar_excel("2026 PTAP CALDAS.xlsx")
        st.success("Archivo local cargado correctamente.")
    except Exception as e:
        st.error(f"No pude abrir el archivo local: {e}")
else:
    archivo_subido = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])
    if archivo_subido is not None:
        try:
            df = pd.read_excel(archivo_subido)

            columnas = [
                'Caudal A tratar (L/s)',
                'Turbiedad de agua cruda (UNT)',
                'pH de agua cruda (Unid)',
                'Alcalinidad de agua cruda (mg/L)',
                'Caudal de dosificación del PAC (mL/min)'
            ]

            for col in columnas:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.strip()
                    .str.replace(' ', '', regex=False)
                    .str.replace(',,', ',', regex=False)
                    .str.replace(',', '.', regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df = df.dropna(subset=columnas).copy()
            st.success("Archivo subido y limpiado correctamente.")
        except Exception as e:
            st.error(f"No pude leer el archivo: {e}")

if df is not None:
    st.write(f"Filas útiles: {len(df)}")

    st.subheader("2) Datos del caso actual")

    col1, col2 = st.columns(2)

    with col1:
        caudal = st.number_input("Caudal A tratar (L/s)", value=170.0, step=1.0)
        turbiedad = st.number_input("Turbiedad de agua cruda (UNT)", value=50.0, step=1.0)

    with col2:
        ph = st.number_input("pH de agua cruda (Unid)", value=7.35, step=0.01, format="%.2f")
        alcalinidad = st.number_input("Alcalinidad de agua cruda (mg/L)", value=17.0, step=1.0)

    if st.button("Calcular rango PAC"):
        resultado = calcular_rango_pac(df, caudal, turbiedad, ph, alcalinidad)

        if not resultado["ok"]:
            st.error(resultado["mensaje"])
        else:
            st.subheader("3) Resultado")

            c1, c2, c3 = st.columns(3)
            c1.metric("Casos similares usados", resultado["n"])
            c2.metric("Mediana PAC", round(resultado["pac_mediana"], 1))
            c3.metric("Desviación", round(resultado["std"], 1))

            st.write(f"**Método usado:** {resultado['metodo']}")
            st.write(f"**Motivo:** {resultado['motivo']}")
            st.write(
                f"**Rango recomendado para jarras:** "
                f"{round(resultado['dosis_min'],1)} a {round(resultado['dosis_max'],1)} mL/min"
            )

            st.subheader("4) Seis jarras sugeridas")
            st.dataframe(resultado["tabla_jarras"], use_container_width=True)

            st.subheader("5) Casos históricos similares usados")
            st.dataframe(resultado["similares_filtrados"], use_container_width=True)