import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


# =========================================
# CONFIGURACION GENERAL
# =========================================
st.set_page_config(
    page_title="PTAP - DIVISO & CALDAS",
    page_icon="💧",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent

USUARIO_CORRECTO = "ptap"
CLAVE_CORRECTA = "plantas2026"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "vista" not in st.session_state:
    st.session_state.vista = "menu"


# =========================================
# ESTILOS GLOBALES
# =========================================

ESTILOS_GLOBALES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --azul-deep:   #0a1628;
    --azul-mid:    #0d2347;
    --azul-accent: #1a6fff;
    --cyan:        #00c8ff;
    --agua:        #00e5c0;
    --blanco:      #ffffff;
    --gris-1:      #f0f6ff;
    --gris-2:      #dce9f7;
    --texto-dark:  #0a1628;
    --texto-muted: #5a7899;
}

* {
    box-sizing: border-box;
}

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: #f0f6ff !important;
}

header {
    visibility: hidden !important;
}

footer {
    visibility: hidden !important;
}

.block-container {
    padding: 0.6rem 1.2rem 2rem 1.2rem !important;
    max-width: 100% !important;
}

.main > div {
    padding-top: 0 !important;
}

/* Encabezado */
.app-header {
    background: linear-gradient(135deg, #0a1628 0%, #0d2347 55%, #0f3060 100%);
    border-radius: 20px;
    padding: 1.4rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.2rem;
    box-shadow: 0 12px 40px rgba(10,22,40,0.22);
    position: relative;
    overflow: hidden;
}

.app-header::before {
    content: "";
    position: absolute;
    right: -60px;
    top: -60px;
    width: 260px;
    height: 260px;
    background: radial-gradient(circle, rgba(0,200,255,0.12) 0%, transparent 70%);
    border-radius: 50%;
}

.app-header::after {
    content: "";
    position: absolute;
    right: 80px;
    bottom: -80px;
    width: 180px;
    height: 180px;
    background: radial-gradient(circle, rgba(0,229,192,0.08) 0%, transparent 70%);
    border-radius: 50%;
}

.header-logo {
    font-family: 'Inter', sans-serif;
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--cyan);
    letter-spacing: 3px;
    text-transform: uppercase;
    position: relative;
    z-index: 2;
}

.header-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: 0.2px;
    color: white;
    position: relative;
    z-index: 2;
    text-align: center;
}

.header-badge {
    background: rgba(0,200,255,0.12);
    border: 1px solid rgba(0,200,255,0.3);
    color: var(--cyan);
    padding: 0.3rem 1rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 1px;
    position: relative;
    z-index: 2;
}

/* Bloques */
.bloque {
    background: white;
    padding: 1.4rem 1.6rem;
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(10,22,40,0.07);
    border: 1px solid rgba(220,233,247,0.8);
    margin-bottom: 1.1rem;
}

.bloque-mini {
    background: #f8fcff;
    border: 1px solid #e1edf5;
    border-radius: 16px;
    padding: 0.95rem;
    margin-bottom: 0.85rem;
}

.titulo-mini {
    font-size: 0.95rem;
    font-weight: 800;
    color: #0b4f6c;
    margin-bottom: 0.4rem;
}

/* Etiquetas */
.etiqueta {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: linear-gradient(135deg, #e8f4ff, #d6ecff);
    color: #0d2347;
    padding: 0.28rem 0.9rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-bottom: 0.9rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border: 1px solid rgba(26,111,255,0.15);
}

/* Menu cards */
.menu-card {
    background: white;
    border: 1px solid rgba(220,233,247,0.9);
    border-radius: 20px;
    padding: 1.5rem 1.4rem 1.1rem 1.4rem;
    height: 100%;
    box-shadow: 0 4px 20px rgba(10,22,40,0.06);
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.menu-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #1a6fff, #00c8ff);
    border-radius: 20px 20px 0 0;
}

.menu-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(10,22,40,0.12);
}

.menu-icon {
    font-size: 2rem;
    margin-bottom: 0.7rem;
    display: block;
}

.menu-titulo {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.08rem;
    color: #0a1628;
    margin-bottom: 0.45rem;
    letter-spacing: 0.1px;
}

.menu-texto {
    font-size: 0.9rem;
    color: var(--texto-muted);
    line-height: 1.55;
    margin-bottom: 1rem;
}

/* Paneles */
.panel-izquierdo {
    background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
    border: 1px solid #dceaf4;
    border-radius: 22px;
    padding: 1.1rem 1.1rem 0.9rem 1.1rem;
    box-shadow: 0 10px 28px rgba(7,62,94,0.08);
    position: sticky;
    top: 0.8rem;
}

.panel-derecho {
    background: rgba(255,255,255,0.98);
    border: 1px solid #dceaf4;
    border-radius: 22px;
    padding: 1.1rem;
    box-shadow: 0 10px 28px rgba(7,62,94,0.08);
}

.subtitulo-panel {
    color: #0b4f6c;
    font-size: 1.12rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}

.texto-panel {
    color: #5b7482;
    font-size: 0.93rem;
    line-height: 1.5;
    margin-bottom: 0.9rem;
}

.titulo-seccion-resultado {
    font-size: 1.08rem;
    font-weight: 800;
    color: #0b4f6c;
    margin-bottom: 0.45rem;
    margin-top: 0.25rem;
}

.hr-suave {
    border: none;
    border-top: 1px solid #e5eef5;
    margin: 0.8rem 0 1rem 0;
}

/* Caja resaltada */
.caja-rango {
    background: linear-gradient(135deg, #eef6ff, #f5faff);
    border-left: 5px solid #1a6fff;
    padding: 1.1rem 1.3rem;
    border-radius: 14px;
    font-size: 0.93rem;
    margin: 0.8rem 0;
    color: #0a1628;
    line-height: 1.65;
    box-shadow: inset 0 0 0 1px rgba(26,111,255,0.08);
}

/* Métricas */
div[data-testid="stMetric"] {
    background: linear-gradient(160deg, #f8fbff 0%, #eef5ff 100%) !important;
    border: 1px solid rgba(26,111,255,0.12) !important;
    padding: 1rem 1.2rem !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 16px rgba(10,22,40,0.06) !important;
}

div[data-testid="stMetricLabel"] > div {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: var(--texto-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

div[data-testid="stMetricValue"] > div {
    font-family: 'Inter', sans-serif !important;
    color: #0d2347 !important;
    font-weight: 800 !important;
    font-size: 1.65rem !important;
    letter-spacing: 0 !important;
}

/* Botones */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    background: linear-gradient(135deg, #1a6fff 0%, #0052cc 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    min-height: 48px !important;
    width: 100% !important;
    box-shadow: 0 6px 20px rgba(26,111,255,0.28) !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
}

.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, #f0f6ff 0%, #e4eeff 100%) !important;
    color: #0d2347 !important;
    border: 1px solid rgba(26,111,255,0.2) !important;
    box-shadow: 0 4px 12px rgba(10,22,40,0.07) !important;
}

/* Inputs */
div[data-testid="stTextInput"] > label,
div[data-testid="stNumberInput"] > label,
div[data-testid="stSelectbox"] > label,
div[data-testid="stSlider"] > label,
div[data-testid="stRadio"] > label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    color: #3a5270 !important;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

div[data-baseweb="input"] input,
div[data-baseweb="select"] > div {
    border-radius: 12px !important;
    border: 1.5px solid #dce9f7 !important;
    background: #f8fbff !important;
    font-size: 0.96rem !important;
    color: #0a1628 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid #dce9f7 !important;
    box-shadow: 0 4px 16px rgba(10,22,40,0.06) !important;
}

thead tr th {
    background: #0d2347 !important;
    color: white !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    text-align: center !important;
}

tbody tr:nth-child(even) {
    background: #f8fbff !important;
}

tbody tr td {
    text-align: center !important;
    color: #0a1628 !important;
}

/* Expander */
div[data-testid="stExpander"] {
    border: 1.5px solid #dce9f7 !important;
    border-radius: 16px !important;
    background: white !important;
    overflow: hidden;
}

.streamlit-expanderHeader {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: #0d2347 !important;
    font-size: 0.95rem !important;
}

/* Alerts */
div[data-testid="stInfo"],
div[data-testid="stSuccess"],
div[data-testid="stError"] {
    border-radius: 14px !important;
}

/* Titulos */
h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
    color: #0a1628 !important;
}

h1 {
    font-size: 1.5rem !important;
    font-weight: 800 !important;
}

h2 {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
}

h3 {
    font-size: 1rem !important;
    font-weight: 700 !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: #f0f6ff;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: #b8d0e8;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #1a6fff;
}

@media (max-width: 1100px) {
    .panel-izquierdo {
        position: relative;
        top: 0;
    }
}

@media (max-width: 768px) {
    .block-container {
        padding: 0.4rem 0.6rem 1.5rem !important;
    }

    .bloque {
        padding: 1rem 1.1rem;
        border-radius: 16px;
    }

    .app-header {
        padding: 1rem 1.2rem;
        flex-direction: column;
        gap: 0.6rem;
        text-align: center;
    }

    .header-title {
        font-size: 1.1rem;
    }

    div[data-testid="stMetricValue"] > div {
        font-size: 1.35rem !important;
    }
}
</style>
"""



# =========================================
# LOGIN
# =========================================
ESTILOS_LOGIN = """
<style>
.login-card {
    background: white;
    border-radius: 28px;
    box-shadow: 0 24px 80px rgba(10,22,40,0.16);
    display: flex;
    overflow: hidden;
    max-width: 960px;
    width: 100%;
    min-height: 540px;
    border: 1px solid rgba(220,233,247,0.6);
}
.login-left {
    background: linear-gradient(145deg, #0a1628 0%, #0d2347 50%, #0f3a6e 100%);
    padding: 3rem 2.5rem;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 520px;
    border-radius: 24px;
}
.login-left::before {
    content: "";
    position: absolute;
    top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,200,255,0.14) 0%, transparent 70%);
    border-radius: 50%;
}
.login-left::after {
    content: "";
    position: absolute;
    bottom: -60px; left: -60px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, rgba(0,229,192,0.10) 0%, transparent 70%);
    border-radius: 50%;
}
.login-brand {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 800;
    color: #00c8ff;
    letter-spacing: 4px;
    text-transform: uppercase;
    position: relative;
    z-index: 2;
}
.login-center { position: relative; z-index: 2; }
.login-headline {
    font-family: 'Inter', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    color: white;
    line-height: 1.05;
    margin-bottom: 1rem;
}
.login-headline span { color: #00c8ff; }
.login-desc {
    color: rgba(255,255,255,0.65);
    font-size: 0.97rem;
    line-height: 1.65;
    max-width: 340px;
}
.login-footer-left {
    position: relative;
    z-index: 2;
    color: rgba(255,255,255,0.45);
    font-size: 0.78rem;
    letter-spacing: 0.5px;
    font-weight: 500;
    text-transform: uppercase;
}
.login-title-r {
    font-family: 'Inter', sans-serif;
    font-size: 1.9rem;
    font-weight: 800;
    color: #0a1628;
    margin-bottom: 0.35rem;
}
.login-sub-r {
    color: #5a7899;
    font-size: 0.92rem;
    margin-bottom: 2rem;
    line-height: 1.55;
}
.login-bottom-note {
    margin-top: 1.5rem;
    display: flex;
    justify-content: space-between;
    color: #8a9db0;
    font-size: 0.82rem;
}
.login-bottom-note span { color: #1a6fff; font-weight: 600; }
</style>
"""


def mostrar_login():
    st.markdown(ESTILOS_GLOBALES, unsafe_allow_html=True)
    st.markdown(ESTILOS_LOGIN, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([0.4, 2.6, 0.4])

    with col_c:
        left, right = st.columns([1.1, 1], gap="medium")

        with left:
            st.markdown("""
            <div class="login-left">
                <div class="login-brand">SERVAF</div>
                <div class="login-center">
                    <div class="login-headline">Planta<br><span>de Agua</span><br>Potable</div>
                    <div class="login-desc">
                        Sistema inteligente de apoyo operativo basado en datos históricos y
                        condiciones actuales para dosificación de PAC.
                    </div>
                </div>
                <div class="login-footer-left">Dirección de Producción y Tratamiento</div>
            </div>
            """, unsafe_allow_html=True)

        with right:
            st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
            st.markdown("<div class='login-title-r'>Iniciar sesión</div>", unsafe_allow_html=True)
            st.markdown(
                "<div class='login-sub-r'>Accede con tus credenciales institucionales para continuar.</div>",
                unsafe_allow_html=True
            )

            usuario = st.text_input("Usuario", placeholder="Ingresa tu usuario", key="login_usuario")
            clave = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_clave")

            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

            if st.button("INGRESAR AL SISTEMA", key="btn_login"):
                if usuario == USUARIO_CORRECTO and clave == CLAVE_CORRECTA:
                    st.session_state.autenticado = True
                    st.session_state.vista = "menu"
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

            st.markdown("""
            <div class="login-bottom-note">
                <span style="color:#8a9db0">Acceso institucional</span>
                <span>PTAP DIVISO · CALDAS</span>
            </div>
            """, unsafe_allow_html=True)


# =========================================
# CONFIGURACIONES POR PLANTA
# =========================================
CONFIGS = {
    "Caldas": {
        "archivo": "2026 PTAP CALDAS.xlsx",
        "nombre_app": "PTAP Caldas",
        "usa_alcalinidad_encalada": False
    },
    "Diviso - Modulo 500": {
        "archivo": "2026 PTAP DIVISO.xlsx",
        "nombre_app": "PTAP Diviso - Módulo 500",
        "usa_alcalinidad_encalada": True
    },
    "Diviso - Modulo 150": {
        "archivo": "2026 PTAP DIVISO.xlsx",
        "nombre_app": "PTAP Diviso - Módulo 150",
        "usa_alcalinidad_encalada": True
    }
}


# =========================================
# FUNCIONES AUXILIARES
# =========================================
def limpiar_columna_numerica(serie):
    return pd.to_numeric(
        serie.astype(str)
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.replace(",,", ",", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )


def obtener_nombre_columna(df, candidatos):
    for col in candidatos:
        if col in df.columns:
            return col
    raise ValueError(f"No encontré ninguna de estas columnas: {candidatos}")


@st.cache_data(ttl=60)
def cargar_y_limpiar_excel(archivo_excel, config_key):
    config = CONFIGS[config_key]

    if isinstance(archivo_excel, str):
        ruta = BASE_DIR / archivo_excel
        df = pd.read_excel(ruta)
    else:
        df = pd.read_excel(archivo_excel)

    if config_key == "Caldas":
        col_caudal = obtener_nombre_columna(df, ["Caudal A tratar (L/s)"])
        col_turbiedad = obtener_nombre_columna(df, ["Turbiedad de agua cruda (UNT)"])
        col_ph = obtener_nombre_columna(df, ["pH de agua cruda (Unid)", "pH de agua cruda"])
        col_alcalinidad_cruda = obtener_nombre_columna(df, ["Alcalinidad de agua cruda (mg/L)"])
        col_pac = obtener_nombre_columna(df, ["Caudal de dosificación del PAC (mL/min)"])

        rename_map = {
            col_caudal: "caudal",
            col_turbiedad: "turbiedad",
            col_ph: "ph",
            col_alcalinidad_cruda: "alcalinidad_cruda",
            col_pac: "pac_ml_min",
        }

    else:
        if config_key == "Diviso - Modulo 500":
            col_caudal = obtener_nombre_columna(df, [
                "Caudal A tratar módulo de 500 (L/s)",
                "Caudal A tratar modulo de 500 (L/s)",
                "Caudal A tratar módulo 500 (L/s)",
                "Caudal A tratar modulo 500 (L/s)"
            ])
            col_pac = obtener_nombre_columna(df, [
                "Caudal de dosificación del PAC módulo de 500 (mL/min)",
                "Caudal de dosificacion del PAC modulo de 500 (mL/min)",
                "Caudal de dosificación del PAC módulo 500 (mL/min)",
                "Caudal de dosificacion del PAC modulo 500 (mL/min)"
            ])
        else:
            col_caudal = obtener_nombre_columna(df, [
                "Caudal A tratar módulo de 150 (L/s)",
                "Caudal A tratar modulo de 150 (L/s)",
                "Caudal A tratar módulo 150 (L/s)",
                "Caudal A tratar modulo 150 (L/s)"
            ])
            col_pac = obtener_nombre_columna(df, [
                "Caudal de dosificación del PAC módulo de 150 (mL/min)",
                "Caudal de dosificacion del PAC modulo de 150 (mL/min)",
                "Caudal de dosificación del PAC módulo 150 (mL/min)",
                "Caudal de dosificacion del PAC modulo 150 (mL/min)"
            ])

        col_turbiedad = obtener_nombre_columna(df, [
            "Turbiedad de agua cruda (UNT)",
            "Turbiedad de agua cruda (UNT).1"
        ])
        col_ph = obtener_nombre_columna(df, ["pH de agua cruda (Unid)", "pH de agua cruda"])
        col_alcalinidad_cruda = obtener_nombre_columna(df, ["Alcalinidad de agua cruda (mg/L)"])
        col_alcalinidad_encalada = obtener_nombre_columna(df, [
            "Alcalinidad de agua encalada (mg/L)",
            "Alcalinidad de agua encalda (mg/L)"
        ])

        rename_map = {
            col_caudal: "caudal",
            col_turbiedad: "turbiedad",
            col_ph: "ph",
            col_alcalinidad_cruda: "alcalinidad_cruda",
            col_alcalinidad_encalada: "alcalinidad_encalada",
            col_pac: "pac_ml_min",
        }

    df = df.rename(columns=rename_map)

    columnas_numericas = ["caudal", "turbiedad", "ph", "alcalinidad_cruda", "pac_ml_min"]

    if config["usa_alcalinidad_encalada"]:
        columnas_numericas.append("alcalinidad_encalada")

    for col in columnas_numericas:
        df[col] = limpiar_columna_numerica(df[col])

    df = df.dropna(subset=columnas_numericas).copy()
    return df


def obtener_tolerancias(config_key):
    if config_key == "Caldas":
        return [
            {"caudal": 15, "turb": 8, "ph": 0.15, "alc": 5},
            {"caudal": 25, "turb": 15, "ph": 0.25, "alc": 8},
            {"caudal": 40, "turb": 25, "ph": 0.35, "alc": 12},
        ]

    return [
        {"caudal": 20, "turb": 5, "ph": 0.20, "alc": 6, "alc_enc": 6},
        {"caudal": 35, "turb": 10, "ph": 0.30, "alc": 10, "alc_enc": 10},
        {"caudal": 60, "turb": 20, "ph": 0.45, "alc": 15, "alc_enc": 15},
        {"caudal": 90, "turb": 30, "ph": 0.60, "alc": 20, "alc_enc": 20},
    ]


def calcular_rango_pac(
    df,
    config_key,
    caudal,
    turbiedad,
    ph,
    alcalinidad_cruda,
    densidad_pac,
    vecinos_deseados,
    alcalinidad_encalada=None
):
    config = CONFIGS[config_key]

    variables = ["caudal", "turbiedad", "ph", "alcalinidad_cruda"]
    nuevo_dict = {
        "caudal": caudal,
        "turbiedad": turbiedad,
        "ph": ph,
        "alcalinidad_cruda": alcalinidad_cruda
    }

    if config["usa_alcalinidad_encalada"]:
        variables.append("alcalinidad_encalada")
        nuevo_dict["alcalinidad_encalada"] = alcalinidad_encalada

    nuevo = pd.DataFrame([nuevo_dict])
    df_base = pd.DataFrame()
    tolerancia_usada = None

    for tol in obtener_tolerancias(config_key):
        filtro = (
            df["caudal"].between(caudal - tol["caudal"], caudal + tol["caudal"]) &
            df["turbiedad"].between(turbiedad - tol["turb"], turbiedad + tol["turb"]) &
            df["ph"].between(ph - tol["ph"], ph + tol["ph"]) &
            df["alcalinidad_cruda"].between(
                alcalinidad_cruda - tol["alc"],
                alcalinidad_cruda + tol["alc"]
            )
        )

        if config["usa_alcalinidad_encalada"]:
            filtro = filtro & df["alcalinidad_encalada"].between(
                alcalinidad_encalada - tol["alc_enc"],
                alcalinidad_encalada + tol["alc_enc"]
            )

        df_base = df[filtro].copy()

        if len(df_base) >= 5:
            tolerancia_usada = tol
            break

    if len(df_base) < 5:
        return {
            "ok": False,
            "mensaje": "Muy pocos datos después del prefiltro, incluso ampliando tolerancias."
        }

    scaler = StandardScaler()
    X_hist = scaler.fit_transform(df_base[variables])
    X_new = scaler.transform(nuevo[variables])

    pesos = np.array(
        [3, 4, 3, 2, 2] if config["usa_alcalinidad_encalada"] else [3, 4, 3, 2],
        dtype=float
    )

    X_hist = X_hist * pesos
    X_new = X_new * pesos

    n_neighbors = min(vecinos_deseados, len(df_base))
    knn = NearestNeighbors(n_neighbors=n_neighbors)
    knn.fit(X_hist)
    distancias, indices = knn.kneighbors(X_new)

    similares = df_base.iloc[indices[0]].copy()
    similares["distancia"] = distancias[0]
    similares = similares.sort_values("distancia")

    q1 = similares["pac_ml_min"].quantile(0.25)
    q3 = similares["pac_ml_min"].quantile(0.75)
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr

    similares_filtrados = similares[
        (similares["pac_ml_min"] >= lim_inf) &
        (similares["pac_ml_min"] <= lim_sup)
    ].copy()

    if len(similares_filtrados) < 3:
        similares_filtrados = similares.copy()

    pac_min = float(similares_filtrados["pac_ml_min"].min())
    pac_max = float(similares_filtrados["pac_ml_min"].max())
    pac_promedio = float(similares_filtrados["pac_ml_min"].mean())
    std = float(similares_filtrados["pac_ml_min"].std()) if len(similares_filtrados) > 1 else 0.0
    n = int(len(similares_filtrados))

    jarras = [1, 2, 3, 4, 5, 6]
    jarras_recomendadas = np.round(np.linspace(pac_min, pac_max, 6), 1)
    dosis_mgL = np.round((jarras_recomendadas * densidad_pac * 1000) / (60 * caudal), 2)

    tabla_jarras = pd.DataFrame({
        "Jarra": jarras,
        "Caudal PAC recomendado (mL/min)": jarras_recomendadas,
        "Dosis PAC recomendada (mg/L)": dosis_mgL
    })

    columnas_mostrar = ["caudal", "turbiedad", "ph", "alcalinidad_cruda"]

    if config["usa_alcalinidad_encalada"]:
        columnas_mostrar.append("alcalinidad_encalada")

    columnas_mostrar += ["pac_ml_min", "distancia"]

    similares_filtrados = similares_filtrados[columnas_mostrar].rename(columns={
        "caudal": "Caudal a tratar (L/s)",
        "turbiedad": "Turbiedad de agua cruda (UNT)",
        "ph": "pH de agua cruda",
        "alcalinidad_cruda": "Alcalinidad de agua cruda (mg/L)",
        "alcalinidad_encalada": "Alcalinidad de agua encalada (mg/L)",
        "pac_ml_min": "Caudal PAC (mL/min)",
        "distancia": "Distancia"
    })

    return {
        "ok": True,
        "similares_filtrados": similares_filtrados,
        "pac_min": pac_min,
        "pac_max": pac_max,
        "pac_promedio": pac_promedio,
        "std": std,
        "n": n,
        "tabla_jarras": tabla_jarras,
        "tolerancia_usada": tolerancia_usada
    }


def valores_por_defecto(config_key):
    if config_key == "Caldas":
        return {
            "caudal": 170.0,
            "turbiedad": 50.0,
            "ph": 7.35,
            "alcalinidad_cruda": 17.0,
            "alcalinidad_encalada": None,
            "densidad_pac": 1.33
        }

    if config_key == "Diviso - Modulo 500":
        return {
            "caudal": 340.0,
            "turbiedad": 10.0,
            "ph": 7.20,
            "alcalinidad_cruda": 11.0,
            "alcalinidad_encalada": 16.0,
            "densidad_pac": 1.33
        }

    return {
        "caudal": 160.0,
        "turbiedad": 10.0,
        "ph": 7.20,
        "alcalinidad_cruda": 11.0,
        "alcalinidad_encalada": 16.0,
        "densidad_pac": 1.33
    }


# =========================================
# CALCULADORA DE CONSUMO Y TANQUE
# =========================================
def mostrar_calculadora_pac():
    st.markdown("<div class='bloque'>", unsafe_allow_html=True)
    st.markdown("<div class='etiqueta'>💧 Calculadora de PAC</div>", unsafe_allow_html=True)
 
    st.markdown("""
    <p style="color:#5a7899;font-size:0.93rem;margin-bottom:1.2rem;line-height:1.6">
    Registra uno o varios periodos de consumo para calcular automáticamente el consumo total de PAC,
    el descenso en el nivel del tanque y la altura estimada restante.
    Usa horas como <code>07:00</code>, <code>13:30</code>, <code>22:00</code> o solo <code>7</code>, <code>13</code>.
    Si la hora final es menor que la inicial, se asume cruce a la madrugada del día siguiente.
    </p>
    """, unsafe_allow_html=True)
 
    tanques = {
        "TQ1 - 10000 L": {"area": 2.6267, "radio": 0.9144},
        "TQ2 - 10000 L": {"area": 2.6746, "radio": 0.9227},
        "TQ3 - 15000 L": {"area": 3.8484, "radio": 1.1068}
    }
 
    tanque = st.selectbox(
        "Selecciona el tanque de PAC",
        list(tanques.keys()),
        key="calc_tanque"
    )
 
    area_tanque = tanques[tanque]["area"]
    radio_tanque = tanques[tanque]["radio"]
 
    st.markdown(f"""
    <div style="display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap">
        <div style="background:#f0f6ff;border:1px solid #dce9f7;border-radius:12px;padding:0.7rem 1.2rem;font-size:0.87rem;color:#0d2347">
            <span style="font-weight:700;display:block;font-size:0.72rem;color:#5a7899;text-transform:uppercase;margin-bottom:2px">Radio</span>
            {radio_tanque:.4f} m
        </div>
        <div style="background:#f0f6ff;border:1px solid #dce9f7;border-radius:12px;padding:0.7rem 1.2rem;font-size:0.87rem;color:#0d2347">
            <span style="font-weight:700;display:block;font-size:0.72rem;color:#5a7899;text-transform:uppercase;margin-bottom:2px">Área</span>
            {area_tanque:.4f} m²
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    def normalizar_hora(valor):
        if pd.isna(valor):
            return None
 
        texto = str(valor).strip()
 
        if texto == "":
            return None
 
        if ":" not in texto:
            if texto.isdigit():
                h = int(texto)
                if 0 <= h <= 24:
                    return f"{h:02d}:00"
            return None
 
        partes = texto.split(":")
        if len(partes) != 2:
            return None
 
        h_txt, m_txt = partes[0].strip(), partes[1].strip()
 
        if not h_txt.isdigit() or not m_txt.isdigit():
            return None
 
        h = int(h_txt)
        m = int(m_txt)
 
        if 0 <= h <= 24 and 0 <= m <= 59:
            if h == 24 and m != 0:
                return None
            return f"{h:02d}:{m:02d}"
 
        return None
 
    def hora_a_minutos(hora_str):
        hora_normal = normalizar_hora(hora_str)
        if hora_normal is None:
            return np.nan
        h, m = hora_normal.split(":")
        return int(h) * 60 + int(m)
 
    tabla_inicial = pd.DataFrame({
        "Hora inicio": ["07:00"],
        "Hora final": ["08:00"],
        "Caudal PAC (mL/min)": [100.0],
        "Densidad PAC (g/mL)": [1.33]
    })
 
    if "tabla_consumos_pac" not in st.session_state:
        st.session_state.tabla_consumos_pac = tabla_inicial.copy()
 
    c_btn1, c_btn2 = st.columns(2)
 
    with c_btn1:
        if st.button("+ Agregar fila", use_container_width=True, key="btn_fila_base"):
            nueva_fila = pd.DataFrame({
                "Hora inicio": [""],
                "Hora final": [""],
                "Caudal PAC (mL/min)": [0.0],
                "Densidad PAC (g/mL)": [1.33]
            })
            st.session_state.tabla_consumos_pac = pd.concat(
                [st.session_state.tabla_consumos_pac, nueva_fila],
                ignore_index=True
            )
            st.rerun()
 
    with c_btn2:
        if st.button("🗑 Limpiar tabla", use_container_width=True, key="btn_limpiar_tabla"):
            st.session_state.tabla_consumos_pac = tabla_inicial.copy()
            st.rerun()
 
    altura_pasada = st.number_input(
        "Altura actual del tanque (m)",
        min_value=0.0,
        value=2.00,
        step=0.01,
        format="%.2f",
        key="calc_altura_pasada"
    )
 
    st.markdown("#### Registros de consumo")
 
    # ─── FIX: se elimina la reasignación de session_state después del data_editor ───
    # Streamlit sincroniza automáticamente el widget con session_state usando la key.
    # Reasignarlo manualmente fuerza un re-render que borra lo que el usuario escribió.
    tabla_editada = st.data_editor(
        st.session_state.tabla_consumos_pac,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_consumos_pac",
        column_config={
            "Hora inicio": st.column_config.TextColumn(
                "Hora inicio",
                help="Ejemplo: 07:00 o 7",
                width="medium"
            ),
            "Hora final": st.column_config.TextColumn(
                "Hora final",
                help="Ejemplo: 08:30 o 8",
                width="medium"
            ),
            "Caudal PAC (mL/min)": st.column_config.NumberColumn(
                "Caudal PAC (mL/min)",
                min_value=0.0,
                step=0.1,
                format="%.2f",
                width="medium"
            ),
            "Densidad PAC (g/mL)": st.column_config.NumberColumn(
                "Densidad PAC (g/mL)",
                min_value=0.01,
                step=0.01,
                format="%.2f",
                width="medium"
            ),
        }
    )
    # ─── FIN FIX: la línea eliminada era:
    #     st.session_state.tabla_consumos_pac = tabla_editada.copy(deep=True)
    # ────────────────────────────────────────────────────────────────────────────
 
    df_calc = tabla_editada.copy(deep=True)
 
    columnas_requeridas = [
        "Hora inicio",
        "Hora final",
        "Caudal PAC (mL/min)",
        "Densidad PAC (g/mL)"
    ]
 
    if df_calc.empty:
        st.info("Ingresa al menos una fila para ver el cálculo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    # Limpiar filas completamente vacías
    df_calc = df_calc.dropna(how="all").copy()
 
    if df_calc.empty:
        st.info("Ingresa al menos una fila para ver el cálculo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    # Normalizar horas
    df_calc["Hora inicio"] = df_calc["Hora inicio"].apply(normalizar_hora)
    df_calc["Hora final"] = df_calc["Hora final"].apply(normalizar_hora)
 
    # Convertir numéricos
    df_calc["Caudal PAC (mL/min)"] = pd.to_numeric(df_calc["Caudal PAC (mL/min)"], errors="coerce")
    df_calc["Densidad PAC (g/mL)"] = pd.to_numeric(df_calc["Densidad PAC (g/mL)"], errors="coerce")
 
    # Convertir horas a minutos
    df_calc["Min inicio"] = df_calc["Hora inicio"].apply(hora_a_minutos)
    df_calc["Min final"] = df_calc["Hora final"].apply(hora_a_minutos)
 
    # Solo calcular con filas completas
    df_validas = df_calc.dropna(subset=[
        "Hora inicio",
        "Hora final",
        "Caudal PAC (mL/min)",
        "Densidad PAC (g/mL)",
        "Min inicio",
        "Min final"
    ]).copy()
 
    if df_validas.empty:
        st.info("Completa una fila válida y el cálculo aparecerá automáticamente.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    # Validaciones
    df_validas = df_validas[
        (df_validas["Min inicio"] >= 0) &
        (df_validas["Min inicio"] <= 1440) &
        (df_validas["Min final"] >= 0) &
        (df_validas["Min final"] <= 1440) &
        (df_validas["Caudal PAC (mL/min)"] >= 0) &
        (df_validas["Densidad PAC (g/mL)"] > 0)
    ].copy()
 
    if df_validas.empty:
        st.error("Revisa los datos. La densidad debe ser mayor que cero y las horas deben ser válidas.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    df_validas["Tiempo (min)"] = np.where(
        df_validas["Min final"] >= df_validas["Min inicio"],
        df_validas["Min final"] - df_validas["Min inicio"],
        (24 * 60 - df_validas["Min inicio"]) + df_validas["Min final"]
    )
 
    df_validas["Consumo (g)"] = (
        df_validas["Tiempo (min)"] *
        df_validas["Caudal PAC (mL/min)"] *
        df_validas["Densidad PAC (g/mL)"]
    )
 
    df_validas["Consumo (kg)"] = df_validas["Consumo (g)"] / 1000
 
    df_validas["Volumen consumido (m³)"] = (
        df_validas["Consumo (kg)"] /
        (df_validas["Densidad PAC (g/mL)"] * 1000)
    )
 
    df_validas["Descenso altura (m)"] = df_validas["Volumen consumido (m³)"] / area_tanque
 
    df_validas["Altura estimada (m)"] = (
        altura_pasada - df_validas["Descenso altura (m)"].cumsum()
    ).clip(lower=0)
 
    consumo_total_g = df_validas["Consumo (g)"].sum()
    consumo_total_kg = df_validas["Consumo (kg)"].sum()
    descenso_total_m = df_validas["Descenso altura (m)"].sum()
    altura_actual = max(altura_pasada - descenso_total_m, 0)
 
    df_mostrar = df_validas.copy()
    df_mostrar.insert(0, "No.", range(1, len(df_mostrar) + 1))
 
    df_mostrar = df_mostrar[[
        "No.",
        "Hora inicio",
        "Hora final",
        "Tiempo (min)",
        "Caudal PAC (mL/min)",
        "Densidad PAC (g/mL)",
        "Consumo (g)",
        "Consumo (kg)",
        "Descenso altura (m)",
        "Altura estimada (m)"
    ]]
 
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='etiqueta'>📊 Resultados</div>", unsafe_allow_html=True)
 
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Consumo total (g)", f"{consumo_total_g:,.2f}")
    r2.metric("Consumo total (kg)", f"{consumo_total_kg:.4f}")
    r3.metric("Descenso de nivel (m)", f"{descenso_total_m:.4f}")
    r4.metric("Altura estimada actual (m)", f"{altura_actual:.4f}")
 
    st.subheader("Detalle por registro")
 
    st.dataframe(
        df_mostrar.style.format({
            "Tiempo (min)": "{:.1f}",
            "Caudal PAC (mL/min)": "{:.1f}",
            "Densidad PAC (g/mL)": "{:.2f}",
            "Consumo (g)": "{:.2f}",
            "Consumo (kg)": "{:.4f}",
            "Descenso altura (m)": "{:.4f}",
            "Altura estimada (m)": "{:.4f}"
        }),
        use_container_width=True
    )
 
    if len(df_mostrar) > 1:
        alturas = [altura_pasada] + list(df_mostrar["Altura estimada (m)"])
        labels = ["Inicio"] + [f"Reg. {i}" for i in range(1, len(df_mostrar) + 1)]
 
        fig_altura = go.Figure()
        fig_altura.add_trace(go.Scatter(
            x=labels,
            y=alturas,
            mode="lines+markers",
            line=dict(color="#1a6fff", width=2.5, shape="spline"),
            marker=dict(size=9, color="#1a6fff", line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor="rgba(26,111,255,0.07)"
        ))
        fig_altura.update_layout(
            title="Evolución de altura estimada del tanque",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter", color="#0a1628", size=12),
            xaxis=dict(title="Registro", gridcolor="#e8f0fe"),
            yaxis=dict(title="Altura (m)", gridcolor="#e8f0fe"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=300
        )
        st.plotly_chart(fig_altura, use_container_width=True)
 
    st.markdown(f"""
    <div class="caja-rango">
        <b>Resumen final</b><br>
        Tanque: {tanque} · Área: {area_tanque:.4f} m² ·
        Altura inicial: {altura_pasada:.2f} m ·
        Descenso total: {descenso_total_m:.4f} m ·
        <b>Altura estimada actual: {altura_actual:.4f} m</b>
    </div>
    """, unsafe_allow_html=True)
 
    st.markdown("""
    <div class="caja-rango" style="border-left-color:#00c8ff">
        <b>Fórmulas aplicadas</b><br>
        <span style="color:#3a5270">
        Tiempo (min) = Hora final - Hora inicio &nbsp;|&nbsp; Si final &lt; inicio -> (1440 - inicio) + final<br>
        Consumo (g) = Tiempo × Caudal (mL/min) × Densidad (g/mL)<br>
        Descenso (m) = [Consumo (kg) / (Densidad × 1000)] / Área (m²)<br>
        Altura estimada = Altura inicial - Σ descensos acumulados
        </span>
    </div>
    """, unsafe_allow_html=True)
 
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# FLUJO DE ACCESO
# =========================================
if not st.session_state.autenticado:
    mostrar_login()
    st.stop()

st.markdown(ESTILOS_GLOBALES, unsafe_allow_html=True)


# =========================================
# ENCABEZADO DE LA APP
# =========================================
st.markdown("""
<div class="app-header">
    <div class="header-logo">💧 SERVAF</div>
    <div class="header-title">
        Sistema de Recomendación de PAC<br>
        <span style="font-size:0.85rem;font-weight:400;color:rgba(255,255,255,0.55)">
            Planta de Agua Potable · Diviso & Caldas
        </span>
    </div>
    <div class="header-badge">PTAP 2026</div>
</div>
""", unsafe_allow_html=True)


# =========================================
# MENU DINAMICO
# =========================================
st.markdown("<div class='bloque'>", unsafe_allow_html=True)

with st.expander("🧭 Menú principal", expanded=False):
    m1, m2, m3 = st.columns([1.15, 1.15, 0.85])

    with m1:
        st.markdown("""
        <div class="menu-card">
            <span class="menu-icon">🔬</span>
            <div class="menu-titulo">Recomendación PAC</div>
            <div class="menu-texto">
                Consulta casos históricos similares y genera dosis sugeridas para prueba de jarras.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("Entrar a recomendación PAC", use_container_width=True, key="btn_ir_recomendacion"):
            st.session_state.vista = "recomendacion"
            st.rerun()

    with m2:
        st.markdown("""
        <div class="menu-card">
            <span class="menu-icon">🧮</span>
            <div class="menu-titulo">Calculadora PAC</div>
            <div class="menu-texto">
                Calcula consumos de PAC, descenso de nivel y altura estimada del tanque.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("Entrar a calculadora PAC", use_container_width=True, key="btn_ir_calculadora"):
            st.session_state.vista = "calculadora"
            st.rerun()

    with m3:
        st.markdown("""
        <div class="menu-card">
            <span class="menu-icon">🔒</span>
            <div class="menu-titulo">Sesión activa</div>
            <div class="menu-texto">
                Cierra la sesión y vuelve al acceso principal.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("Cerrar sesión", type="secondary", use_container_width=True, key="btn_cerrar_superior"):
            st.session_state.autenticado = False
            st.session_state.vista = "menu"
            st.rerun()

if st.session_state.vista == "menu":
    st.info("Selecciona una herramienta desde el menú desplegable.")

st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# VISTA CALCULADORA
# =========================================
if st.session_state.vista == "calculadora":
    mostrar_calculadora_pac()
    st.stop()

if st.session_state.vista != "recomendacion":
    st.stop()


# =========================================
# VISTA RECOMENDACION - PC EN DOS PANELES
# =========================================
col_form, col_result = st.columns([1, 1.85], gap="large")

with col_form:
    st.markdown("<div class='panel-izquierdo'>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-panel'>Configuración del análisis</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='texto-panel'>Selecciona la planta, define las condiciones actuales del agua y ejecuta la recomendación.</div>",
        unsafe_allow_html=True
    )

    planta_base = st.selectbox(
        "Selecciona la planta de tratamiento",
        ["Caldas", "Diviso"]
    )

    config_key = "Caldas"

    if planta_base == "Diviso":
        modulo_diviso = st.selectbox(
            "Selecciona el módulo de Diviso",
            ["Módulo 500", "Módulo 150"]
        )
        config_key = "Diviso - Modulo 500" if modulo_diviso == "Módulo 500" else "Diviso - Modulo 150"

    st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)

    st.markdown("<div class='bloque-mini'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-mini'>Fuente de datos</div>", unsafe_allow_html=True)

    fuente_datos = st.radio(
        "Fuente de datos históricos",
        ["Usar archivo del sistema", "Subir archivo Excel"],
        horizontal=False,
        label_visibility="collapsed"
    )

    if st.button("Actualizar datos", key="actualizar_datos_lateral", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    df = None
    archivo_excel = CONFIGS[config_key]["archivo"]

    if fuente_datos == "Usar archivo del sistema":
        try:
            df = cargar_y_limpiar_excel(archivo_excel, config_key)
            st.success(f"Datos cargados: {CONFIGS[config_key]['nombre_app']}")
        except Exception as e:
            st.error(f"No se pudo abrir el archivo: {e}")
    else:
        archivo_subido = st.file_uploader(
            "Sube el archivo Excel de la planta seleccionada",
            type=["xlsx"],
            key=f"uploader_{config_key}"
        )

        if archivo_subido is not None:
            try:
                df = cargar_y_limpiar_excel(archivo_subido, config_key)
                st.success(f"Archivo subido correctamente para: {CONFIGS[config_key]['nombre_app']}")
            except Exception as e:
                st.error(f"No se pudo leer el archivo: {e}")
        else:
            st.info("Sube un archivo Excel para continuar.")

    if df is not None:
        st.caption(f"{CONFIGS[config_key]['nombre_app']} · Filas útiles: {len(df)}")

    st.markdown("</div>", unsafe_allow_html=True)

    defaults = valores_por_defecto(config_key)

    st.markdown("<div class='bloque-mini'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-mini'>Datos del caso actual</div>", unsafe_allow_html=True)

    caudal = st.number_input("Caudal a tratar (L/s)", value=float(defaults["caudal"]), step=1.0)
    turbiedad = st.number_input("Turbiedad del agua cruda (UNT)", value=float(defaults["turbiedad"]), step=0.1)
    ph = st.number_input("pH del agua cruda", value=float(defaults["ph"]), step=0.01, format="%.2f")
    alcalinidad_cruda = st.number_input("Alcalinidad agua cruda (mg/L)", value=float(defaults["alcalinidad_cruda"]), step=1.0)

    alcalinidad_encalada = None
    if CONFIGS[config_key]["usa_alcalinidad_encalada"]:
        alcalinidad_encalada = st.number_input(
            "Alcalinidad agua encalada (mg/L)",
            value=float(defaults["alcalinidad_encalada"]),
            step=1.0
        )

    densidad_pac = st.number_input(
        "Densidad del PAC (g/mL)",
        value=float(defaults["densidad_pac"]),
        step=0.01,
        format="%.2f"
    )

    vecinos_deseados = st.slider(
        "Cantidad de registros históricos a evaluar",
        min_value=5,
        max_value=30,
        value=8,
        step=1
    )

    calcular = st.button("⚡ Calcular rango PAC", use_container_width=True, key="btn_calcular_panel")

    if st.button("← Volver al menú", type="secondary", use_container_width=True, key="volver_menu_lateral"):
        st.session_state.vista = "menu"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_result:
    st.markdown("<div class='panel-derecho'>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-panel'>Resultado de la recomendación</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='texto-panel'>Aquí verás el resumen, dosis sugeridas, casos históricos similares y la gráfica principal.</div>",
        unsafe_allow_html=True
    )

    if df is None:
        st.info("Primero carga una fuente de datos válida en el panel izquierdo.")
    elif not calcular:
        st.info("Completa los datos del panel izquierdo y presiona «Calcular rango PAC».")
    else:
        resultado = calcular_rango_pac(
            df=df,
            config_key=config_key,
            caudal=caudal,
            turbiedad=turbiedad,
            ph=ph,
            alcalinidad_cruda=alcalinidad_cruda,
            densidad_pac=densidad_pac,
            vecinos_deseados=vecinos_deseados,
            alcalinidad_encalada=alcalinidad_encalada
        )

        if not resultado["ok"]:
            st.error(resultado["mensaje"])
        else:
            st.markdown("<div class='titulo-seccion-resultado'>Resumen general</div>", unsafe_allow_html=True)

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Registros usados", resultado["n"])
            r2.metric("PAC promedio", round(resultado["pac_promedio"], 1))
            r3.metric("PAC mínimo", round(resultado["pac_min"], 1))
            r4.metric("PAC máximo", round(resultado["pac_max"], 1))

            if resultado.get("tolerancia_usada") is not None:
                tol = resultado["tolerancia_usada"]
                texto_tol = (
                    f"Caudal ±{tol['caudal']} · Turbiedad ±{tol['turb']} · "
                    f"pH ±{tol['ph']} · Alc. cruda ±{tol['alc']}"
                )
                if "alc_enc" in tol:
                    texto_tol += f" · Alc. encalada ±{tol['alc_enc']}"
                st.info(f"Tolerancias del prefiltro: {texto_tol}")

            st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)

            st.markdown("<div class='titulo-seccion-resultado'>Dosis sugeridas para prueba de jarras</div>", unsafe_allow_html=True)
            st.caption(f"Densidad PAC usada: {densidad_pac:.2f} g/mL · Caudal a tratar: {caudal:.2f} L/s")
            st.dataframe(resultado["tabla_jarras"], use_container_width=True)

            st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)

            st.markdown("<div class='titulo-seccion-resultado'>Registros históricos similares</div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='color:#5a7899;font-size:0.88rem;margin-bottom:0.8rem'>Registros más cercanos al caso actual ordenados por similitud.</p>",
                unsafe_allow_html=True
            )

            fmt = {
                "Caudal a tratar (L/s)": "{:.1f}",
                "Turbiedad de agua cruda (UNT)": "{:.1f}",
                "pH de agua cruda": "{:.2f}",
                "Alcalinidad de agua cruda (mg/L)": "{:.1f}",
                "Caudal PAC (mL/min)": "{:.1f}",
                "Distancia": "{:.3f}"
            }
            if "Alcalinidad de agua encalada (mg/L)" in resultado["similares_filtrados"].columns:
                fmt["Alcalinidad de agua encalada (mg/L)"] = "{:.1f}"

            st.dataframe(
                resultado["similares_filtrados"].style.format(fmt),
                use_container_width=True
            )

            st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)

            st.markdown("<div class='titulo-seccion-resultado'>Visualización</div>", unsafe_allow_html=True)

            df_grafica = resultado["similares_filtrados"].sort_values("Caudal PAC (mL/min)")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_grafica["Caudal PAC (mL/min)"],
                y=df_grafica["Turbiedad de agua cruda (UNT)"],
                mode="lines+markers",
                name="Históricos",
                line=dict(color="#1a6fff", width=2.2, shape="spline"),
                marker=dict(size=8, color="#1a6fff", line=dict(color="white", width=2), symbol="circle"),
                fill="tozeroy",
                fillcolor="rgba(26,111,255,0.05)"
            ))
            fig.add_trace(go.Scatter(
                x=[resultado["pac_promedio"]],
                y=[turbiedad],
                mode="markers",
                name="Caso actual",
                marker=dict(size=14, color="#00e5c0", line=dict(color="#0a1628", width=2), symbol="star")
            ))
            fig.update_layout(
                title=dict(
                    text="Caudal PAC vs Turbiedad - Registros similares",
                    font=dict(family="Syne", size=14, color="#0a1628")
                ),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="DM Sans", color="#0a1628", size=12),
                xaxis=dict(title="Caudal PAC (mL/min)", gridcolor="#e8f0fe", linecolor="#dce9f7"),
                yaxis=dict(title="Turbiedad (UNT)", gridcolor="#e8f0fe", linecolor="#dce9f7"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=50, b=20),
                height=360
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
