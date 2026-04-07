import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


# =========================================
# CONFIGURACIÓN GENERAL
# =========================================
st.set_page_config(
    page_title="PTAP Caldas - Recomendación PAC",
    page_icon="💧",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #f4f9fb;
    }

    h1, h2, h3 {
        color: #0b4f6c;
    }

    .subtitulo {
        color: #4f6d7a;
        font-size: 1.05rem;
        margin-top: -10px;
        margin-bottom: 20px;
    }

    .bloque {
        background-color: white;
        padding: 1.2rem;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }

    .stButton > button {
        background-color: #0b6e4f;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.7rem 1rem;
        font-weight: bold;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: #09543d;
        color: white;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #dbe7ec;
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.05);
    }

    .caja-rango {
        background-color: #e8f4f8;
        border-left: 6px solid #0b4f6c;
        padding: 1rem;
        border-radius: 10px;
        font-size: 1.1rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>💧 PTAP Caldas - Recomendación de PAC para prueba de jarras</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtitulo'>Sistema de apoyo operativo basado en históricos similares para definir rango de dosis en prueba de jarras</div>",
    unsafe_allow_html=True
)


# =========================================
# FUNCIÓN DE CARGA Y LIMPIEZA
# =========================================
@st.cache_data
def cargar_y_limpiar_excel(archivo_excel):
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


# =========================================
# FUNCIÓN PRINCIPAL
# =========================================
def calcular_rango_pac(
    df: pd.DataFrame,
    caudal: float,
    turbiedad: float,
    ph: float,
    alcalinidad: float,
    vecinos_deseados: int
):
    variables = [
        'Caudal A tratar (L/s)',
        'Turbiedad de agua cruda (UNT)',
        'pH de agua cruda (Unid)',
        'Alcalinidad de agua cruda (mg/L)'
    ]

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
            "mensaje": "Muy pocos datos después del prefiltro. Ajusta el caso o revisa el histórico."
        }

    # Escalado
    scaler = StandardScaler()
    X_hist = scaler.fit_transform(df_base[variables])
    X_new = scaler.transform(nuevo[variables])

    # Pesos
    pesos = np.array([3, 4, 3, 2], dtype=float)  # caudal, turbiedad, pH, alcalinidad
    X_hist = X_hist * pesos
    X_new = X_new * pesos

    # Vecinos
    n_neighbors = min(vecinos_deseados, len(df_base))
    knn = NearestNeighbors(n_neighbors=n_neighbors)
    knn.fit(X_hist)
    distancias, indices = knn.kneighbors(X_new)

    similares = df_base.iloc[indices[0]].copy()
    similares['distancia'] = distancias[0]
    similares = similares.sort_values('distancia')

    col_pac = 'Caudal de dosificación del PAC (mL/min)'

    # Quitar extremos por IQR
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
            "mensaje": "Después de quitar valores extremos quedaron muy pocos casos útiles."
        }

    pac_min = float(similares_filtrados[col_pac].min())
    pac_max = float(similares_filtrados[col_pac].max())
    pac_mediana = float(similares_filtrados[col_pac].median())
    pac_promedio = float(similares_filtrados[col_pac].mean())
    std = float(similares_filtrados[col_pac].std()) if len(similares_filtrados) > 1 else 0.0
    n = int(len(similares_filtrados))
    ancho_rango = pac_max - pac_min

    # Regla de decisión: rango real o mediana ±10%
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

    # Tabla de 6 jarras
    jarras = np.round(np.linspace(dosis_min, dosis_max, 6), 1)
    tabla_jarras = pd.DataFrame({
        "Jarra": [1, 2, 3, 4, 5, 6],
        "Dosis PAC (mL/min)": jarras
    })

    # Tabla resumen lateral de PAC
    tabla_resumen = pd.DataFrame({
        "Indicador": ["Mínimo", "Mediana", "Máximo"],
        "PAC (mL/min)": [round(pac_min, 1), round(pac_mediana, 1), round(pac_max, 1)]
    })

    columnas_mostrar = variables + [col_pac, 'distancia']
    similares_filtrados = similares_filtrados[columnas_mostrar].copy()

    return {
        "ok": True,
        "df_base_n": len(df_base),
        "similares_filtrados": similares_filtrados,
        "pac_min": pac_min,
        "pac_max": pac_max,
        "pac_mediana": pac_mediana,
        "pac_promedio": pac_promedio,
        "std": std,
        "n": n,
        "ancho_rango": ancho_rango,
        "usar_rango": usar_rango,
        "motivo": motivo,
        "metodo": metodo,
        "dosis_min": dosis_min,
        "dosis_max": dosis_max,
        "tabla_jarras": tabla_jarras,
        "tabla_resumen": tabla_resumen
    }


# =========================================
# CARGA DEL ARCHIVO
# =========================================
st.markdown("<div class='bloque'>", unsafe_allow_html=True)
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
            df = cargar_y_limpiar_excel(archivo_subido)
            st.success("Archivo subido y limpiado correctamente.")
        except Exception as e:
            st.error(f"No pude leer el archivo: {e}")

if df is not None:
    st.write(f"*Filas útiles:* {len(df)}")
st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# SIDEBAR
# =========================================
st.sidebar.header("⚙️ Datos del caso actual")

caudal = st.sidebar.number_input("Caudal A tratar (L/s)", value=170.0, step=1.0)
turbiedad = st.sidebar.number_input("Turbiedad de agua cruda (UNT)", value=50.0, step=1.0)
ph = st.sidebar.number_input("pH de agua cruda (Unid)", value=7.35, step=0.01, format="%.2f")
alcalinidad = st.sidebar.number_input("Alcalinidad de agua cruda (mg/L)", value=17.0, step=1.0)

vecinos_deseados = st.sidebar.slider(
    "Cantidad de datos históricos a evaluar",
    min_value=5,
    max_value=30,
    value=8,
    step=1
)

calcular = st.sidebar.button("Calcular rango PAC")


# =========================================
# RESULTADO
# =========================================
if df is not None and calcular:
    resultado = calcular_rango_pac(df, caudal, turbiedad, ph, alcalinidad, vecinos_deseados)

    if not resultado["ok"]:
        st.error(resultado["mensaje"])

    else:
        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.subheader("2) Resultado del análisis")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Casos similares usados", resultado["n"])
        c2.metric("PAC mediana", round(resultado["pac_mediana"], 1))
        c3.metric("PAC promedio", round(resultado["pac_promedio"], 1))
        c4.metric("Desviación", round(resultado["std"], 1))

        st.markdown(
            f"<div class='caja-rango'><b>Rango recomendado para jarras:</b> "
            f"{round(resultado['dosis_min'],1)} a {round(resultado['dosis_max'],1)} mL/min</div>",
            unsafe_allow_html=True
        )

        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.write(f"*Método usado:* {resultado['metodo']}")
        with col_info2:
            st.write(f"*Motivo:* {resultado['motivo']}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.subheader("3) Dosis sugeridas para 6 jarras")

        col_j1, col_j2 = st.columns([2, 1])

        with col_j1:
            st.dataframe(resultado["tabla_jarras"], use_container_width=True)

        with col_j2:
            st.write("*Resumen PAC*")
            st.dataframe(resultado["tabla_resumen"], use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.subheader("4) Casos históricos similares usados")
        st.dataframe(resultado["similares_filtrados"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
