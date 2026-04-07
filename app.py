import streamlit as st

USUARIO_CORRECTO = "ptap"
CLAVE_CORRECTA = "c4ldas2026"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def login():
    st.title("Acceso restringido")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if usuario == USUARIO_CORRECTO and clave == CLAVE_CORRECTA:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

if not st.session_state.autenticado:
    login()
    st.stop()
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
    .stApp {
        background: linear-gradient(180deg, #dff4ff 0%, #eef9ff 35%, #f8fcff 100%);
    }

    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, rgba(8,74,117,0.96), rgba(33,134,181,0.92));
        color: white;
        padding: 2rem 2rem 1.8rem 2rem;
        border-radius: 24px;
        box-shadow: 0 10px 24px rgba(8,74,117,0.20);
        margin-bottom: 1.2rem;
    }

    .hero::before {
        content: "💧";
        position: absolute;
        right: 30px;
        top: 10px;
        font-size: 7rem;
        opacity: 0.10;
    }

    .hero h1 {
        color: white !important;
        margin: 0;
        font-size: 2.7rem;
        font-weight: 800;
    }

    .hero p {
        margin-top: 0.5rem;
        margin-bottom: 0;
        font-size: 1.05rem;
        color: #eaf7ff;
    }

    .bloque {
        background: rgba(255,255,255,0.94);
        padding: 1.2rem;
        border-radius: 18px;
        box-shadow: 0 4px 14px rgba(7,62,94,0.08);
        border: 1px solid rgba(7,62,94,0.08);
        margin-bottom: 1rem;
    }

    .etiqueta {
        display: inline-block;
        background: #cfefff;
        color: #0a4d6a;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }

    .caja-rango {
        background: linear-gradient(135deg, #e5f6ff, #f4fbff);
        border-left: 6px solid #0b4f6c;
        padding: 1rem;
        border-radius: 12px;
        font-size: 1.08rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }

    .stButton > button {
        background: linear-gradient(135deg, #0b6e4f, #15926d);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.75rem 1rem;
        font-weight: 700;
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #09543d, #0f7c5c);
        color: white;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #d6e8f2;
        padding: 14px;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f4fbff 0%, #eef8fc 100%);
    }

    h2, h3 {
        color: #0b4f6c !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>PTAP Caldas - Recomendación de PAC</h1>
    <p>Herramienta de apoyo operativo para definir el rango de dosis de PAC en prueba de jarras con base en datos históricos similares.</p>
</div>
""", unsafe_allow_html=True)


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

    scaler = StandardScaler()
    X_hist = scaler.fit_transform(df_base[variables])
    X_new = scaler.transform(nuevo[variables])

    pesos = np.array([3, 4, 3, 2], dtype=float)
    X_hist = X_hist * pesos
    X_new = X_new * pesos

    n_neighbors = min(vecinos_deseados, len(df_base))
    knn = NearestNeighbors(n_neighbors=n_neighbors)
    knn.fit(X_hist)
    distancias, indices = knn.kneighbors(X_new)

    similares = df_base.iloc[indices[0]].copy()
    similares["distancia"] = distancias[0]
    similares = similares.sort_values("distancia")

    col_pac = 'Caudal de dosificación del PAC (mL/min)'

    # Quitar extremos
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

    # Columna 1: jarras con base en mediana/rango final usado
    jarras_mediana = np.round(np.linspace(dosis_min, dosis_max, 6), 1)

    # Columna 2: jarras estrictas entre mínimo y máximo históricos
    jarras_minmax = np.round(np.linspace(pac_min, pac_max, 6), 1)

    tabla_jarras = pd.DataFrame({
        "Jarra": [1, 2, 3, 4, 5, 6],
        "Dosis PAC con mediana (mL/min)": jarras_mediana,
        "Dosis PAC entre mínimo y máximo (mL/min)": jarras_minmax
    })

    tabla_resumen = pd.DataFrame({
        "Indicador": ["Mínimo", "Mediana", "Máximo"],
        "PAC (mL/min)": [round(pac_min, 1), round(pac_mediana, 1), round(pac_max, 1)]
    })

    columnas_mostrar = variables + [col_pac, 'distancia']
    similares_filtrados = similares_filtrados[columnas_mostrar].copy()

    return {
        "ok": True,
        "similares_filtrados": similares_filtrados,
        "pac_min": pac_min,
        "pac_max": pac_max,
        "pac_mediana": pac_mediana,
        "pac_promedio": pac_promedio,
        "std": std,
        "n": n,
        "metodo": metodo,
        "motivo": motivo,
        "dosis_min": dosis_min,
        "dosis_max": dosis_max,
        "tabla_jarras": tabla_jarras,
        "tabla_resumen": tabla_resumen
    }


# =========================================
# CARGA DEL ARCHIVO
# =========================================
st.markdown("<div class='bloque'>", unsafe_allow_html=True)
st.markdown("<div class='etiqueta'>Archivo histórico</div>", unsafe_allow_html=True)

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
# BARRA LATERAL
# =========================================
st.sidebar.header("⚙️ Datos del caso actual")
st.sidebar.markdown("Ingresa las condiciones actuales del agua cruda.")

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
# RESULTADOS
# =========================================
if df is not None and calcular:
    resultado = calcular_rango_pac(df, caudal, turbiedad, ph, alcalinidad, vecinos_deseados)

    if not resultado["ok"]:
        st.error(resultado["mensaje"])
    else:
        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.markdown("<div class='etiqueta'>Resultado del análisis</div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Casos usados", resultado["n"])
        c2.metric("PAC mediana", round(resultado["pac_mediana"], 1))
        c3.metric("PAC promedio", round(resultado["pac_promedio"], 1))
        c4.metric("Desviación", round(resultado["std"], 1))

        st.markdown(
            f"<div class='caja-rango'><b>Rango recomendado para jarras:</b> "
            f"{round(resultado['dosis_min'],1)} a {round(resultado['dosis_max'],1)} mL/min</div>",
            unsafe_allow_html=True
        )

        info1, info2 = st.columns(2)
        with info1:
            st.write(f"*Método usado:* {resultado['metodo']}")
        with info2:
            st.write(f"*Motivo:* {resultado['motivo']}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.markdown("<div class='etiqueta'>Dosis sugeridas para 6 jarras</div>", unsafe_allow_html=True)

        col1, col2 = st.columns([2.4, 1])

        with col1:
            st.dataframe(resultado["tabla_jarras"], use_container_width=True)

        with col2:
            st.write("*Resumen PAC*")
            st.dataframe(resultado["tabla_resumen"], use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.markdown("<div class='etiqueta'>Casos históricos similares usados</div>", unsafe_allow_html=True)
        st.dataframe(resultado["similares_filtrados"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
