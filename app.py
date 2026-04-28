import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime, timedelta
from textwrap import dedent
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
 
USUARIOS = {
    "diviso": {"clave": "diviso123", "planta": "Diviso"},
    "caldas": {"clave": "caldas123", "planta": "Caldas"},
}
 
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
 
if "vista" not in st.session_state:
    st.session_state.vista = "menu"
 
if "planta_usuario" not in st.session_state:
    st.session_state.planta_usuario = None
 
 
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
 
* { box-sizing: border-box; }
 
html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: #f0f6ff !important;
}
 
header { visibility: hidden !important; }
footer { visibility: hidden !important; }
 
.block-container {
    padding: 0.6rem 1.2rem 2rem 1.2rem !important;
    max-width: 100% !important;
}
 
.main > div { padding-top: 0 !important; }
 
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
    right: -60px; top: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(0,200,255,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
 
.app-header::after {
    content: "";
    position: absolute;
    right: 80px; bottom: -80px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(0,229,192,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
 
.header-logo {
    font-size: 1.05rem; font-weight: 800; color: var(--cyan);
    letter-spacing: 3px; text-transform: uppercase; position: relative; z-index: 2;
}
 
.header-title {
    font-size: 1.35rem; font-weight: 700; color: white;
    position: relative; z-index: 2; text-align: center;
}
 
.header-badge {
    background: rgba(0,200,255,0.12);
    border: 1px solid rgba(0,200,255,0.3);
    color: var(--cyan);
    padding: 0.3rem 1rem; border-radius: 999px;
    font-size: 0.78rem; font-weight: 600; letter-spacing: 1px;
    position: relative; z-index: 2;
}
 
.bloque {
    background: white; padding: 1.4rem 1.6rem; border-radius: 20px;
    box-shadow: 0 4px 24px rgba(10,22,40,0.07);
    border: 1px solid rgba(220,233,247,0.8); margin-bottom: 1.1rem;
}
 
.bloque-mini {
    background: #f8fcff; border: 1px solid #e1edf5;
    border-radius: 16px; padding: 0.95rem; margin-bottom: 0.85rem;
}
 
.titulo-mini { font-size: 0.95rem; font-weight: 800; color: #0b4f6c; margin-bottom: 0.4rem; }
 
.etiqueta {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: linear-gradient(135deg, #e8f4ff, #d6ecff); color: #0d2347;
    padding: 0.28rem 0.9rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700;
    margin-bottom: 0.9rem; letter-spacing: 0.5px; text-transform: uppercase;
    border: 1px solid rgba(26,111,255,0.15);
}
 
.menu-card {
    background: white; border: 1px solid rgba(220,233,247,0.9); border-radius: 20px;
    padding: 1.5rem 1.4rem 1.1rem 1.4rem; height: 100%;
    box-shadow: 0 4px 20px rgba(10,22,40,0.06); position: relative; overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
 
.menu-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #1a6fff, #00c8ff); border-radius: 20px 20px 0 0;
}
 
.menu-card:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(10,22,40,0.12); }
 
.menu-icon { font-size: 2rem; margin-bottom: 0.7rem; display: block; }
.menu-titulo { font-weight: 700; font-size: 1.08rem; color: #0a1628; margin-bottom: 0.45rem; }
.menu-texto { font-size: 0.9rem; color: var(--texto-muted); line-height: 1.55; margin-bottom: 1rem; }
 
.panel-izquierdo {
    background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
    border: 1px solid #dceaf4; border-radius: 22px; padding: 1.1rem 1.1rem 0.9rem 1.1rem;
    box-shadow: 0 10px 28px rgba(7,62,94,0.08); position: sticky; top: 0.8rem;
}
 
.panel-derecho {
    background: rgba(255,255,255,0.98); border: 1px solid #dceaf4; border-radius: 22px;
    padding: 1.1rem; box-shadow: 0 10px 28px rgba(7,62,94,0.08);
}
 
.subtitulo-panel { color: #0b4f6c; font-size: 1.12rem; font-weight: 800; margin-bottom: 0.35rem; }
.texto-panel { color: #5b7482; font-size: 0.93rem; line-height: 1.5; margin-bottom: 0.9rem; }
 
.titulo-seccion-resultado {
    font-size: 1.08rem; font-weight: 800; color: #0b4f6c;
    margin-bottom: 0.45rem; margin-top: 0.25rem;
}
 
.hr-suave { border: none; border-top: 1px solid #e5eef5; margin: 0.8rem 0 1rem 0; }
 
.caja-rango {
    background: linear-gradient(135deg, #eef6ff, #f5faff); border-left: 5px solid #1a6fff;
    padding: 1.1rem 1.3rem; border-radius: 14px; font-size: 0.93rem; margin: 0.8rem 0;
    color: #0a1628; line-height: 1.65; box-shadow: inset 0 0 0 1px rgba(26,111,255,0.08);
}
 
div[data-testid="stMetric"] {
    background: linear-gradient(160deg, #f8fbff 0%, #eef5ff 100%) !important;
    border: 1px solid rgba(26,111,255,0.12) !important; padding: 1rem 1.2rem !important;
    border-radius: 16px !important; box-shadow: 0 4px 16px rgba(10,22,40,0.06) !important;
}
 
div[data-testid="stMetricLabel"] > div {
    font-size: 0.78rem !important; font-weight: 600 !important;
    color: var(--texto-muted) !important; text-transform: uppercase; letter-spacing: 0.5px;
}
 
div[data-testid="stMetricValue"] > div {
    color: #0d2347 !important; font-weight: 800 !important;
    font-size: 1.65rem !important; letter-spacing: 0 !important;
}
 
.stButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 700 !important;
    font-size: 0.9rem !important;
    background: linear-gradient(135deg, #1a6fff 0%, #0052cc 100%) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    min-height: 48px !important; width: 100% !important;
    box-shadow: 0 6px 20px rgba(26,111,255,0.28) !important;
}
 
.stButton > button:hover { transform: translateY(-1px); }
 
.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, #f0f6ff 0%, #e4eeff 100%) !important;
    color: #0d2347 !important; border: 1px solid rgba(26,111,255,0.2) !important;
    box-shadow: 0 4px 12px rgba(10,22,40,0.07) !important;
}
 
div[data-testid="stTextInput"] > label,
div[data-testid="stNumberInput"] > label,
div[data-testid="stSelectbox"] > label,
div[data-testid="stSlider"] > label,
div[data-testid="stRadio"] > label {
    font-size: 1rem !important; font-weight: 700 !important;
    color: #3a5270 !important; text-transform: uppercase; letter-spacing: 0.4px;
}
 
div[data-baseweb="input"] input,
div[data-baseweb="select"] > div {
    border-radius: 12px !important; border: 1.5px solid #dce9f7 !important;
    background: #f8fbff !important; font-size: 0.96rem !important; color: #0a1628 !important;
}
 
[data-testid="stDataFrame"] {
    border-radius: 16px !important; overflow: hidden !important;
    border: 1px solid #dce9f7 !important; box-shadow: 0 4px 16px rgba(10,22,40,0.06) !important;
}
 
thead tr th {
    background: #0d2347 !important; color: white !important;
    font-weight: 700 !important; font-size: 0.8rem !important; text-align: center !important;
}
 
tbody tr:nth-child(even) { background: #f8fbff !important; }
tbody tr td { text-align: center !important; color: #0a1628 !important; }
 
div[data-testid="stExpander"] {
    border: 1.5px solid #dce9f7 !important; border-radius: 16px !important;
    background: white !important; overflow: hidden;
}
 
.streamlit-expanderHeader {
    font-weight: 700 !important; color: #0d2347 !important; font-size: 0.95rem !important;
}
 
div[data-testid="stInfo"],
div[data-testid="stSuccess"],
div[data-testid="stError"] { border-radius: 14px !important; }
 
h1, h2, h3 { font-family: 'Inter', sans-serif !important; color: #0a1628 !important; }
h1 { font-size: 1.5rem !important; font-weight: 800 !important; }
h2 { font-size: 1.15rem !important; font-weight: 700 !important; }
h3 { font-size: 1rem !important; font-weight: 700 !important; }
 
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f0f6ff; border-radius: 10px; }
::-webkit-scrollbar-thumb { background: #b8d0e8; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #1a6fff; }
 
@media (max-width: 1100px) { .panel-izquierdo { position: relative; top: 0; } }
 
@media (max-width: 768px) {
    .block-container { padding: 0.4rem 0.6rem 1.5rem !important; }
    .bloque { padding: 1rem 1.1rem; border-radius: 16px; }
    .app-header { padding: 1rem 1.2rem; flex-direction: column; gap: 0.6rem; text-align: center; }
    .header-title { font-size: 1.1rem; }
    div[data-testid="stMetricValue"] > div { font-size: 1.35rem !important; }
}
 
.tanque-card { overflow: visible !important; width: 100% !important; }
.tanque-layout { overflow: visible !important; width: 100% !important; }
.tanque-svg-wrap { overflow: visible !important; }
[data-testid="stMarkdownContainer"] { overflow: visible !important; }
</style>
"""
 
# =========================================
# LOGIN
# =========================================
ESTILOS_LOGIN = """
<style>
.login-left {
    background: linear-gradient(145deg, #0a1628 0%, #0d2347 50%, #0f3a6e 100%);
    padding: 3rem 2.5rem; position: relative; overflow: hidden;
    display: flex; flex-direction: column; justify-content: space-between;
    min-height: 520px; border-radius: 24px;
}
.login-left::before {
    content: ""; position: absolute; top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,200,255,0.14) 0%, transparent 70%);
    border-radius: 50%;
}
.login-left::after {
    content: ""; position: absolute; bottom: -60px; left: -60px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, rgba(0,229,192,0.10) 0%, transparent 70%);
    border-radius: 50%;
}
.login-brand {
    font-size: 0.85rem; font-weight: 800; color: #00c8ff;
    letter-spacing: 4px; text-transform: uppercase; position: relative; z-index: 2;
}
.login-center { position: relative; z-index: 2; }
.login-headline { font-size: 3rem; font-weight: 800; color: white; line-height: 1.05; margin-bottom: 1rem; }
.login-headline span { color: #00c8ff; }
.login-desc { color: rgba(255,255,255,0.65); font-size: 0.97rem; line-height: 1.65; max-width: 340px; }
.login-footer-left {
    position: relative; z-index: 2; color: rgba(255,255,255,0.45);
    font-size: 0.78rem; letter-spacing: 0.5px; font-weight: 500; text-transform: uppercase;
}
.login-title-r { font-size: 1.9rem; font-weight: 800; color: #0a1628; margin-bottom: 0.35rem; }
.login-sub-r { color: #5a7899; font-size: 0.92rem; margin-bottom: 2rem; line-height: 1.55; }
.login-bottom-note {
    margin-top: 1.5rem; display: flex; justify-content: space-between;
    color: #8a9db0; font-size: 0.82rem;
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
                    <div class="login-headline">Planta de tratamiento<br><span>de Agua</span><br>Potable</div>
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
            clave   = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_clave")
 
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
 
            if st.button("INGRESAR AL SISTEMA", key="btn_login"):
                u = usuario.strip().lower()
                if u in USUARIOS and clave == USUARIOS[u]["clave"]:
                    st.session_state.autenticado    = True
                    st.session_state.vista          = "menu"
                    st.session_state.planta_usuario = USUARIOS[u]["planta"]
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
        serie.astype(str).str.strip()
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
        col_caudal            = obtener_nombre_columna(df, ["Caudal A tratar (L/s)"])
        col_turbiedad         = obtener_nombre_columna(df, ["Turbiedad de agua cruda (UNT)"])
        col_ph                = obtener_nombre_columna(df, ["pH de agua cruda (Unid)", "pH de agua cruda"])
        col_alcalinidad_cruda = obtener_nombre_columna(df, ["Alcalinidad de agua cruda (mg/L)"])
        col_pac               = obtener_nombre_columna(df, ["Caudal de dosificación del PAC (mL/min)"])
        rename_map = {
            col_caudal: "caudal", col_turbiedad: "turbiedad", col_ph: "ph",
            col_alcalinidad_cruda: "alcalinidad_cruda", col_pac: "pac_ml_min",
        }
    else:
        if config_key == "Diviso - Modulo 500":
            col_caudal = obtener_nombre_columna(df, [
                "Caudal A tratar módulo de 500 (L/s)", "Caudal A tratar modulo de 500 (L/s)",
                "Caudal A tratar módulo 500 (L/s)",    "Caudal A tratar modulo 500 (L/s)"
            ])
            col_pac = obtener_nombre_columna(df, [
                "Caudal de dosificación del PAC módulo de 500 (mL/min)",
                "Caudal de dosificacion del PAC modulo de 500 (mL/min)",
                "Caudal de dosificación del PAC módulo 500 (mL/min)",
                "Caudal de dosificacion del PAC modulo 500 (mL/min)"
            ])
        else:
            col_caudal = obtener_nombre_columna(df, [
                "Caudal A tratar módulo de 150 (L/s)", "Caudal A tratar modulo de 150 (L/s)",
                "Caudal A tratar módulo 150 (L/s)",    "Caudal A tratar modulo 150 (L/s)"
            ])
            col_pac = obtener_nombre_columna(df, [
                "Caudal de dosificación del PAC módulo de 150 (mL/min)",
                "Caudal de dosificacion del PAC modulo de 150 (mL/min)",
                "Caudal de dosificación del PAC módulo 150 (mL/min)",
                "Caudal de dosificacion del PAC modulo 150 (mL/min)"
            ])
 
        col_turbiedad         = obtener_nombre_columna(df, ["Turbiedad de agua cruda (UNT)", "Turbiedad de agua cruda (UNT).1"])
        col_ph                = obtener_nombre_columna(df, ["pH de agua cruda (Unid)", "pH de agua cruda"])
        col_alcalinidad_cruda = obtener_nombre_columna(df, ["Alcalinidad de agua cruda (mg/L)"])
        col_alcalinidad_enc   = obtener_nombre_columna(df, ["Alcalinidad de agua encalada (mg/L)", "Alcalinidad de agua encalda (mg/L)"])
 
        rename_map = {
            col_caudal: "caudal", col_turbiedad: "turbiedad", col_ph: "ph",
            col_alcalinidad_cruda: "alcalinidad_cruda",
            col_alcalinidad_enc: "alcalinidad_encalada", col_pac: "pac_ml_min",
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
            {"caudal": 15, "turb": 8,  "ph": 0.15, "alc": 5},
            {"caudal": 25, "turb": 15, "ph": 0.25, "alc": 8},
            {"caudal": 40, "turb": 25, "ph": 0.35, "alc": 12},
        ]
    return [
        {"caudal": 20, "turb": 5,  "ph": 0.20, "alc": 6,  "alc_enc": 6},
        {"caudal": 35, "turb": 10, "ph": 0.30, "alc": 10, "alc_enc": 10},
        {"caudal": 60, "turb": 20, "ph": 0.45, "alc": 15, "alc_enc": 15},
        {"caudal": 90, "turb": 30, "ph": 0.60, "alc": 20, "alc_enc": 20},
    ]
 
 
def calcular_rango_pac(df, config_key, caudal, turbiedad, ph,
                       alcalinidad_cruda, densidad_pac, vecinos_deseados,
                       alcalinidad_encalada=None):
    config = CONFIGS[config_key]
    variables  = ["caudal", "turbiedad", "ph", "alcalinidad_cruda"]
    nuevo_dict = {"caudal": caudal, "turbiedad": turbiedad, "ph": ph, "alcalinidad_cruda": alcalinidad_cruda}
 
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
            df["alcalinidad_cruda"].between(alcalinidad_cruda - tol["alc"], alcalinidad_cruda + tol["alc"])
        )
        if config["usa_alcalinidad_encalada"]:
            filtro = filtro & df["alcalinidad_encalada"].between(
                alcalinidad_encalada - tol["alc_enc"], alcalinidad_encalada + tol["alc_enc"]
            )
        df_base = df[filtro].copy()
        if len(df_base) >= 5:
            tolerancia_usada = tol
            break
 
    if len(df_base) < 5:
        return {"ok": False, "mensaje": "Muy pocos datos después del prefiltro, incluso ampliando tolerancias."}
 
    scaler = StandardScaler()
    X_hist = scaler.fit_transform(df_base[variables])
    X_new  = scaler.transform(nuevo[variables])
    pesos  = np.array([3, 4, 3, 2, 2] if config["usa_alcalinidad_encalada"] else [3, 4, 3, 2], dtype=float)
    X_hist *= pesos
    X_new  *= pesos
 
    n_neighbors = min(vecinos_deseados, len(df_base))
    knn = NearestNeighbors(n_neighbors=n_neighbors)
    knn.fit(X_hist)
    distancias, indices = knn.kneighbors(X_new)
 
    similares = df_base.iloc[indices[0]].copy()
    similares["distancia"] = distancias[0]
    similares = similares.sort_values("distancia")
 
    q1  = similares["pac_ml_min"].quantile(0.25)
    q3  = similares["pac_ml_min"].quantile(0.75)
    iqr = q3 - q1
    similares_filtrados = similares[
        (similares["pac_ml_min"] >= q1 - 1.5*iqr) & (similares["pac_ml_min"] <= q3 + 1.5*iqr)
    ].copy()
    if len(similares_filtrados) < 3:
        similares_filtrados = similares.copy()
 
    pac_min      = float(similares_filtrados["pac_ml_min"].min())
    pac_max      = float(similares_filtrados["pac_ml_min"].max())
    pac_promedio = float(similares_filtrados["pac_ml_min"].mean())
    std          = float(similares_filtrados["pac_ml_min"].std()) if len(similares_filtrados) > 1 else 0.0
    n            = int(len(similares_filtrados))
 
    jarras_recomendadas = np.round(np.linspace(pac_min, pac_max, 6), 1)
    dosis_mgL = np.round((jarras_recomendadas * densidad_pac * 1000) / (60 * caudal), 2)
 
    tabla_jarras = pd.DataFrame({
        "Jarra": [1,2,3,4,5,6],
        "Caudal PAC recomendado (mL/min)": jarras_recomendadas,
        "Dosis PAC recomendada (mg/L)": dosis_mgL
    })
 
    columnas_mostrar = ["caudal", "turbiedad", "ph", "alcalinidad_cruda"]
    if config["usa_alcalinidad_encalada"]:
        columnas_mostrar.append("alcalinidad_encalada")
    columnas_mostrar += ["pac_ml_min", "distancia"]
 
    similares_filtrados = similares_filtrados[columnas_mostrar].rename(columns={
        "caudal": "Caudal a tratar (L/s)", "turbiedad": "Turbiedad de agua cruda (UNT)",
        "ph": "pH de agua cruda", "alcalinidad_cruda": "Alcalinidad de agua cruda (mg/L)",
        "alcalinidad_encalada": "Alcalinidad de agua encalada (mg/L)",
        "pac_ml_min": "Caudal PAC (mL/min)", "distancia": "Distancia"
    })
 
    return {
        "ok": True, "similares_filtrados": similares_filtrados,
        "pac_min": pac_min, "pac_max": pac_max, "pac_promedio": pac_promedio,
        "std": std, "n": n, "tabla_jarras": tabla_jarras, "tolerancia_usada": tolerancia_usada
    }
 
 
def valores_por_defecto(config_key):
    if config_key == "Caldas":
        return {"caudal": 170.0, "turbiedad": 50.0, "ph": 7.35,
                "alcalinidad_cruda": 17.0, "alcalinidad_encalada": None, "densidad_pac": 1.33}
    if config_key == "Diviso - Modulo 500":
        return {"caudal": 340.0, "turbiedad": 10.0, "ph": 7.20,
                "alcalinidad_cruda": 11.0, "alcalinidad_encalada": 16.0, "densidad_pac": 1.33}
    return {"caudal": 160.0, "turbiedad": 10.0, "ph": 7.20,
            "alcalinidad_cruda": 11.0, "alcalinidad_encalada": 16.0, "densidad_pac": 1.33}
 
 
# =========================================
# HELPERS HORA
# =========================================
def parse_hora(texto):
    if not texto or str(texto).strip() == "":
        return None
    texto = str(texto).strip()
    if ":" in texto:
        partes = texto.split(":")
        if len(partes) != 2:
            return None
        h_txt, m_txt = partes[0].strip(), partes[1].strip()
        if not h_txt.isdigit() or not m_txt.isdigit():
            return None
        h, m = int(h_txt), int(m_txt)
    else:
        if not texto.isdigit():
            return None
        h, m = int(texto), 0
    if 0 <= h <= 23 and 0 <= m <= 59:
        return h * 60 + m
    return None
 
 
def minutos_a_hora_str(minutos):
    minutos = int(minutos) % 1440
    h = minutos // 60
    m = minutos % 60
    return f"{h:02d}:{m:02d}"
 
 
def minutos_a_hora_futura(min_base, delta_min):
    total = (min_base + int(round(delta_min))) % 1440
    return minutos_a_hora_str(total)
 
 
# =========================================
# TANQUE SVG ANIMADO
# =========================================
def generar_tanque_svg(
    h_actual, h_rebose, h_minima, h_lleno,
    hora_actual_str, hora_rebose_str, hora_minimo_str,
    tendencia, Q_neto_Ls,
):
    pct_actual = max(0.0, min(1.0, h_actual / h_lleno)) * 100
    pct_rebose = max(0.0, min(1.0, h_rebose / h_lleno)) * 100
    pct_minima = max(0.0, min(1.0, h_minima / h_lleno)) * 100
 
    TK_X, TK_Y, TK_W, TK_H = 55, 40, 160, 280
    TK_BOTTOM = TK_Y + TK_H
    VB_W, VB_H = 340, 420
 
    y_agua   = TK_BOTTOM - (pct_actual / 100) * TK_H
    y_rebose = TK_BOTTOM - (pct_rebose / 100) * TK_H
    y_minima = TK_BOTTOM - (pct_minima / 100) * TK_H
 
    if pct_actual > 85:
        c1, c2 = "#e63946", "#ff6b7a"
        estado_color, estado_txt = "#e63946", "&#9888;&#65039; NIVEL ALTO"
    elif pct_actual < 20:
        c1, c2 = "#f4a261", "#ffd166"
        estado_color, estado_txt = "#f4a261", "&#9888;&#65039; NIVEL BAJO"
    else:
        c1, c2 = "#1a6fff", "#00c8ff"
        estado_color, estado_txt = "#2a9d8f", "&#9989; NIVEL NORMAL"
 
    flecha = "&#9650; Subiendo" if tendencia == "subiendo" else (
        "&#9660; Bajando" if tendencia == "bajando" else "&#8594; Estable"
    )
    signo      = "+" if Q_neto_Ls >= 0 else ""
    txt_rebose = hora_rebose_str if hora_rebose_str else "&#8212;"
    txt_minimo = hora_minimo_str if hora_minimo_str else "&#8212;"
 
    escala_lines = ""
    for i in range(5):
        yy  = TK_Y + i * TK_H // 4
        val = h_lleno * (1 - i / 4)
        escala_lines += (
            f'<line x1="{TK_X-18}" y1="{yy}" x2="{TK_X-8}" y2="{yy}" '
            f'stroke="#8ab0c8" stroke-width="1.2"/>'
            f'<text x="{TK_X-20}" y="{yy+4}" text-anchor="end" font-size="8" '
            f'font-family="Inter,sans-serif" fill="#5a7899">{val:.1f}</text>'
        )
 
    burbujas = ""
    if tendencia != "bajando":
        for cx_b, cy_b, r_b, dur, begin in [
            (TK_X + int(TK_W * 0.3), TK_BOTTOM - 20, 3,   "3.5s", "0s"),
            (TK_X + int(TK_W * 0.6), TK_BOTTOM - 10, 2,   "4.2s", "1s"),
            (TK_X + int(TK_W * 0.45),TK_BOTTOM - 30, 2.5, "5s",   "2s"),
        ]:
            burbujas += (
                f'<circle cx="{cx_b}" cy="{cy_b}" r="{r_b}" fill="rgba(255,255,255,0.6)">'
                f'<animate attributeName="cy" values="{TK_BOTTOM};{TK_Y}" '
                f'dur="{dur}" repeatCount="indefinite" begin="{begin}"/>'
                f'<animate attributeName="opacity" values="0.7;0" '
                f'dur="{dur}" repeatCount="indefinite" begin="{begin}"/>'
                f'</circle>'
            )
 
    cx_w = TK_X + 3
    cw_w = TK_W - 6
    wave_d = (
        f"M {cx_w},{y_agua:.1f} "
        + "".join([
            f"Q {cx_w + cw_w*(k+0.5)/8:.1f},{y_agua + (-7 if k%2==0 else 7):.1f} "
            f"{cx_w + cw_w*(k+1)/8:.1f},{y_agua:.1f} "
            for k in range(8)
        ])
        + "".join([
            f"Q {cx_w + cw_w*(k+8.5)/8:.1f},{y_agua + (-7 if k%2==0 else 7):.1f} "
            f"{cx_w + cw_w*(k+9)/8:.1f},{y_agua:.1f} "
            for k in range(8)
        ])
        + f"L {cx_w + cw_w*2},{TK_BOTTOM} L {cx_w},{TK_BOTTOM} Z"
    )
 
    sub_tendencia = (
        "Nivel subiendo" if tendencia == "subiendo"
        else ("Nivel bajando" if tendencia == "bajando" else "Nivel estable")
    )
 
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: transparent; font-family: 'Inter', sans-serif; padding: 4px; }}
.tk-wrap {{
  background: linear-gradient(160deg, #f0f8ff 0%, #e4f1fc 100%);
  border: 1.5px solid #c5ddf0; border-radius: 20px;
  padding: 1.1rem 1.1rem 1.3rem 1.1rem;
  box-shadow: 0 8px 32px rgba(10,30,60,0.10); width: 100%;
}}
.tk-titulo {{
  font-size: 0.82rem; font-weight: 800; color: #0b4f6c;
  letter-spacing: 1px; text-transform: uppercase; text-align: center; margin-bottom: 0.35rem;
}}
.tk-estado {{
  background: {estado_color}22; border: 1.5px solid {estado_color}; color: {estado_color};
  font-weight: 800; font-size: 0.76rem; padding: 0.22rem 0.85rem; border-radius: 999px;
  text-align: center; letter-spacing: 0.5px; margin: 0 auto 0.85rem auto; display: table;
}}
.tk-svg-wrap {{ width: 100%; max-width: 380px; margin: 0 auto; overflow: visible; }}
.tk-svg-wrap svg {{ width: 100%; height: auto; display: block; overflow: visible; }}
.tk-info-grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));
  gap: 0.6rem; margin-top: 0.9rem; width: 100%;
}}
.tk-badge {{
  background: white; border: 1px solid #dce9f7; border-radius: 13px;
  padding: 0.6rem 0.85rem; font-size: 0.81rem; color: #0a1628;
  box-shadow: 0 2px 8px rgba(10,22,40,0.06);
}}
.lbl {{ font-size: 0.66rem; font-weight: 700; color: #5a7899; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 2px; }}
.val {{ font-size: 0.98rem; font-weight: 800; color: #0d2347; word-break: break-word; display: block; }}
.sub {{ font-size: 0.70rem; color: #8aabca; margin-top: 1px; display: block; }}
</style>
</head>
<body>
<div class="tk-wrap">
  <div class="tk-titulo">&#127959;&#65039; Estado del Tanque &mdash; {hora_actual_str}</div>
  <div class="tk-estado">{estado_txt}</div>
  <div class="tk-svg-wrap">
    <svg viewBox="0 0 {VB_W} {VB_H}" xmlns="http://www.w3.org/2000/svg" overflow="visible">
      <defs>
        <linearGradient id="gAgua" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{c2}" stop-opacity="0.95"/>
          <stop offset="100%" stop-color="{c1}" stop-opacity="1"/>
        </linearGradient>
        <linearGradient id="gTanque" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#d0e8f5"/>
          <stop offset="35%" stop-color="#eaf4fc"/>
          <stop offset="65%" stop-color="#eaf4fc"/>
          <stop offset="100%" stop-color="#b8d4e8"/>
        </linearGradient>
        <linearGradient id="gReflejo" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="rgba(255,255,255,0)"/>
          <stop offset="25%" stop-color="rgba(255,255,255,0.35)"/>
          <stop offset="50%" stop-color="rgba(255,255,255,0)"/>
        </linearGradient>
        <clipPath id="clipTk">
          <rect x="{TK_X+3}" y="{TK_Y}" width="{TK_W-6}" height="{TK_H}"/>
        </clipPath>
      </defs>
      <rect x="{TK_X+6}" y="{TK_Y+6}" width="{TK_W}" height="{TK_H+20}" rx="10" fill="rgba(10,30,60,0.12)"/>
      <rect x="{TK_X}" y="{TK_Y}" width="{TK_W}" height="{TK_H+20}" rx="10" fill="url(#gTanque)" stroke="#8ab4cc" stroke-width="2.5"/>
      <g clip-path="url(#clipTk)">
        <rect x="{TK_X+3}" y="{y_agua:.1f}" width="{TK_W-6}" height="{TK_BOTTOM - y_agua:.1f}" fill="url(#gAgua)" opacity="0.92"/>
        <g>
          <path d="{wave_d}" fill="{c2}" opacity="0.5">
          </path>
          <animateTransform attributeName="transform" type="translate" from="0,0" to="{-(cw_w)},0" dur="2.8s" repeatCount="indefinite"/>
        </g>
        <rect x="{TK_X+3}" y="{y_agua:.1f}" width="{TK_W-6}" height="{TK_BOTTOM - y_agua:.1f}" fill="url(#gReflejo)" opacity="0.55"/>
        {burbujas}
      </g>
      <line x1="{TK_X-8}" y1="{y_rebose:.1f}" x2="{TK_X+TK_W+8}" y2="{y_rebose:.1f}" stroke="#e63946" stroke-width="1.8" stroke-dasharray="5,3" opacity="0.9"/>
      <text x="{TK_X+TK_W+12}" y="{y_rebose+4:.1f}" font-size="8.5" font-family="Inter,sans-serif" fill="#e63946" font-weight="700">REBOSE {h_rebose:.2f}m</text>
      <line x1="{TK_X-8}" y1="{y_minima:.1f}" x2="{TK_X+TK_W+8}" y2="{y_minima:.1f}" stroke="#f4a261" stroke-width="1.8" stroke-dasharray="5,3" opacity="0.9"/>
      <text x="{TK_X+TK_W+12}" y="{y_minima+4:.1f}" font-size="8.5" font-family="Inter,sans-serif" fill="#f4a261" font-weight="700">MIN {h_minima:.2f}m</text>
      <rect x="{TK_X + TK_W//2 - 32:.0f}" y="{y_agua-26:.1f}" width="64" height="20" rx="10" fill="{c1}" opacity="0.9"/>
      <text x="{TK_X + TK_W//2:.0f}" y="{y_agua-13:.1f}" text-anchor="middle" font-size="9.5" font-family="Inter,sans-serif" fill="white" font-weight="800">{h_actual:.3f} m</text>
      <rect x="{TK_X-8}" y="{TK_Y-10}" width="{TK_W+16}" height="13" rx="6" fill="#8ab4cc" stroke="#6a9ab8" stroke-width="1.5"/>
      <circle cx="{TK_X-1}" cy="{TK_Y-4}" r="2.5" fill="#5a8aa8"/>
      <circle cx="{TK_X+TK_W+1}" cy="{TK_Y-4}" r="2.5" fill="#5a8aa8"/>
      <circle cx="{TK_X+TK_W//2}" cy="{TK_Y-4}" r="2.5" fill="#5a8aa8"/>
      <rect x="{TK_X-10}" y="{TK_BOTTOM+20}" width="{TK_W+20}" height="13" rx="6" fill="#8ab4cc" stroke="#6a9ab8" stroke-width="1.5"/>
      <rect x="{TK_X+8}" y="{TK_BOTTOM+33}" width="12" height="26" rx="4" fill="#7aa4bc" stroke="#6090a8" stroke-width="1"/>
      <rect x="{TK_X+TK_W-20}" y="{TK_BOTTOM+33}" width="12" height="26" rx="4" fill="#7aa4bc" stroke="#6090a8" stroke-width="1"/>
      <line x1="{TK_X-22}" y1="{TK_Y}" x2="{TK_X-22}" y2="{TK_BOTTOM}" stroke="#b8d0e4" stroke-width="1.5"/>
      {escala_lines}
      <text x="{TK_X + TK_W//2:.0f}" y="{TK_BOTTOM+17}" text-anchor="middle" font-size="11" font-family="Inter,sans-serif" fill="{estado_color}" font-weight="700">{flecha}</text>
    </svg>
  </div>
  <div class="tk-info-grid">
    <div class="tk-badge">
      <span class="lbl">Hora actual</span>
      <span class="val">{hora_actual_str}</span>
      <span class="sub">Lectura m&#225;s reciente</span>
    </div>
    <div class="tk-badge">
      <span class="lbl">Nivel actual</span>
      <span class="val" style="color:{estado_color}">{h_actual:.3f} m</span>
      <span class="sub">{pct_actual:.1f}% del volumen</span>
    </div>
    <div class="tk-badge">
      <span class="lbl">Caudal neto</span>
      <span class="val">{signo}{Q_neto_Ls:.2f} L/s</span>
      <span class="sub">{sub_tendencia}</span>
    </div>
    <div class="tk-badge" style="border-left:4px solid #e63946;">
      <span class="lbl">&#9201; Hora rebose</span>
      <span class="val" style="color:#e63946">{txt_rebose}</span>
      <span class="sub">L&#237;mite: {h_rebose:.2f} m</span>
    </div>
    <div class="tk-badge" style="border-left:4px solid #f4a261;">
      <span class="lbl">&#9201; Hora m&#237;nimo</span>
      <span class="val" style="color:#f4a261">{txt_minimo}</span>
      <span class="sub">L&#237;mite: {h_minima:.2f} m</span>
    </div>
  </div>
</div>
</body>
</html>"""
    return html
 
 
# =========================================
# CALCULADORA DE CONSUMO PAC
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
 
    tanque       = st.selectbox("Selecciona el tanque de PAC", list(tanques.keys()), key="calc_tanque")
    area_tanque  = tanques[tanque]["area"]
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
        h, m = int(h_txt), int(m_txt)
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
        "Hora inicio": ["07:00"], "Hora final": ["08:00"],
        "Caudal PAC (mL/min)": [100.0], "Densidad PAC (g/mL)": [1.33]
    })
 
    if "tabla_consumos_pac" not in st.session_state:
        st.session_state.tabla_consumos_pac = tabla_inicial.copy()
 
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("+ Agregar fila", use_container_width=True, key="btn_fila_base"):
            st.session_state.tabla_consumos_pac = pd.concat([
                st.session_state.tabla_consumos_pac,
                pd.DataFrame({"Hora inicio": [""], "Hora final": [""],
                              "Caudal PAC (mL/min)": [0.0], "Densidad PAC (g/mL)": [1.33]})
            ], ignore_index=True)
            st.rerun()
    with c_btn2:
        if st.button("🗑 Limpiar tabla", use_container_width=True, key="btn_limpiar_tabla"):
            st.session_state.tabla_consumos_pac = tabla_inicial.copy()
            st.rerun()
 
    altura_pasada = st.number_input(
        "Altura actual del tanque (m)", min_value=0.0, value=2.00,
        step=0.01, format="%.2f", key="calc_altura_pasada"
    )
 
    st.markdown("#### Registros de consumo")
 
    tabla_editada = st.data_editor(
        st.session_state.tabla_consumos_pac,
        num_rows="dynamic", use_container_width=True, hide_index=True,
        key="editor_consumos_pac",
        column_config={
            "Hora inicio":         st.column_config.TextColumn("Hora inicio",          help="Ejemplo: 07:00 o 7", width="medium"),
            "Hora final":          st.column_config.TextColumn("Hora final",           help="Ejemplo: 08:30 o 8", width="medium"),
            "Caudal PAC (mL/min)": st.column_config.NumberColumn("Caudal PAC (mL/min)", min_value=0.0,  step=0.1,  format="%.2f", width="medium"),
            "Densidad PAC (g/mL)": st.column_config.NumberColumn("Densidad PAC (g/mL)", min_value=0.01, step=0.01, format="%.2f", width="medium"),
        }
    )
 
    df_calc = tabla_editada.copy(deep=True)
 
    if df_calc.empty:
        st.info("Ingresa al menos una fila para ver el cálculo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    df_calc = df_calc.dropna(how="all").copy()
    if df_calc.empty:
        st.info("Ingresa al menos una fila para ver el cálculo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    df_calc["Hora inicio"]         = df_calc["Hora inicio"].apply(normalizar_hora)
    df_calc["Hora final"]          = df_calc["Hora final"].apply(normalizar_hora)
    df_calc["Caudal PAC (mL/min)"] = pd.to_numeric(df_calc["Caudal PAC (mL/min)"], errors="coerce")
    df_calc["Densidad PAC (g/mL)"] = pd.to_numeric(df_calc["Densidad PAC (g/mL)"], errors="coerce")
    df_calc["Min inicio"]          = df_calc["Hora inicio"].apply(hora_a_minutos)
    df_calc["Min final"]           = df_calc["Hora final"].apply(hora_a_minutos)
 
    df_validas = df_calc.dropna(subset=[
        "Hora inicio", "Hora final", "Caudal PAC (mL/min)", "Densidad PAC (g/mL)", "Min inicio", "Min final"
    ]).copy()
 
    if df_validas.empty:
        st.info("Completa una fila válida y el cálculo aparecerá automáticamente.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    df_validas = df_validas[
        (df_validas["Min inicio"] >= 0) & (df_validas["Min inicio"] <= 1440) &
        (df_validas["Min final"]  >= 0) & (df_validas["Min final"]  <= 1440) &
        (df_validas["Caudal PAC (mL/min)"] >= 0) & (df_validas["Densidad PAC (g/mL)"] > 0)
    ].copy()
 
    if df_validas.empty:
        st.error("Revisa los datos. La densidad debe ser mayor que cero y las horas deben ser válidas.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    df_validas["Tiempo (min)"] = np.where(
        df_validas["Min final"] >= df_validas["Min inicio"],
        df_validas["Min final"] - df_validas["Min inicio"],
        (24*60 - df_validas["Min inicio"]) + df_validas["Min final"]
    )
    df_validas["Consumo (g)"]            = df_validas["Tiempo (min)"] * df_validas["Caudal PAC (mL/min)"] * df_validas["Densidad PAC (g/mL)"]
    df_validas["Consumo (kg)"]           = df_validas["Consumo (g)"] / 1000
    df_validas["Volumen consumido (m³)"] = df_validas["Consumo (kg)"] / (df_validas["Densidad PAC (g/mL)"] * 1000)
    df_validas["Descenso altura (m)"]    = df_validas["Volumen consumido (m³)"] / area_tanque
    df_validas["Altura estimada (m)"]    = (altura_pasada - df_validas["Descenso altura (m)"].cumsum()).clip(lower=0)
 
    consumo_total_g  = df_validas["Consumo (g)"].sum()
    consumo_total_kg = df_validas["Consumo (kg)"].sum()
    descenso_total_m = df_validas["Descenso altura (m)"].sum()
    altura_actual    = max(altura_pasada - descenso_total_m, 0)
 
    df_mostrar = df_validas.copy()
    df_mostrar.insert(0, "No.", range(1, len(df_mostrar) + 1))
    df_mostrar = df_mostrar[[
        "No.", "Hora inicio", "Hora final", "Tiempo (min)",
        "Caudal PAC (mL/min)", "Densidad PAC (g/mL)",
        "Consumo (g)", "Consumo (kg)", "Descenso altura (m)", "Altura estimada (m)"
    ]]
 
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='etiqueta'>📊 Resultados</div>", unsafe_allow_html=True)
 
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Consumo total (g)",         f"{consumo_total_g:,.2f}")
    r2.metric("Consumo total (kg)",        f"{consumo_total_kg:.4f}")
    r3.metric("Descenso de nivel (m)",     f"{descenso_total_m:.4f}")
    r4.metric("Altura estimada actual (m)", f"{altura_actual:.4f}")
 
    st.subheader("Detalle por registro")
    st.dataframe(
        df_mostrar.style.format({
            "Tiempo (min)": "{:.1f}", "Caudal PAC (mL/min)": "{:.1f}", "Densidad PAC (g/mL)": "{:.2f}",
            "Consumo (g)": "{:.2f}", "Consumo (kg)": "{:.4f}",
            "Descenso altura (m)": "{:.4f}", "Altura estimada (m)": "{:.4f}"
        }),
        use_container_width=True
    )
 
    if len(df_mostrar) > 1:
        alturas = [altura_pasada] + list(df_mostrar["Altura estimada (m)"])
        labels  = ["Inicio"] + [f"Reg. {i}" for i in range(1, len(df_mostrar) + 1)]
        fig_altura = go.Figure()
        fig_altura.add_trace(go.Scatter(
            x=labels, y=alturas, mode="lines+markers",
            line=dict(color="#1a6fff", width=2.5, shape="spline"),
            marker=dict(size=9, color="#1a6fff", line=dict(color="white", width=2)),
            fill="tozeroy", fillcolor="rgba(26,111,255,0.07)"
        ))
        fig_altura.update_layout(
            title="Evolución de altura estimada del tanque",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter", color="#0a1628", size=12),
            xaxis=dict(title="Registro", gridcolor="#e8f0fe"),
            yaxis=dict(title="Altura (m)", gridcolor="#e8f0fe"),
            margin=dict(l=20, r=20, t=40, b=20), height=300
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
        Tiempo (min) = Hora final - Hora inicio &nbsp;|&nbsp; Si final &lt; inicio → (1440 - inicio) + final<br>
        Consumo (g) = Tiempo × Caudal (mL/min) × Densidad (g/mL)<br>
        Descenso (m) = [Consumo (kg) / (Densidad × 1000)] / Área (m²)<br>
        Altura estimada = Altura inicial - Σ descensos acumulados
        </span>
    </div>
    """, unsafe_allow_html=True)
 
    st.markdown("</div>", unsafe_allow_html=True)
 
 
# =========================================
# PANEL DE RESULTADOS HTML — PTAP STYLE
# =========================================
def generar_panel_resultados_html(
    altura_actual, altura_antes, altura_lleno,
    altura_rebose, altura_minima, nivel_objetivo, banda_control,
    area_equiv, volumen_total,
    Q_entrada_tanque_Ls, caudal_salida_ls, Q_neto_Ls,
    Q_neto_proyeccion_Ls, caudal_salida_esperada_ls,
    Q_planta_recomendado_Ls, caudal_entrada_planta_actual,
    delta_entrada_planta, relacion_operativa,
    Q_tanque_post_ajuste_Ls, Q_neto_post_ajuste_Ls,
    hora_antes_str, hora_actual_str, hora_efecto_str,
    delta_t_min, tiempo_recorrido_min, tiempo_correccion_min,
    nivel_cuando_llega_ajuste, nivel_final_estimado,
    hora_rebose_str, hora_minimo_str, t_rebose_min, t_minimo_min,
    estado_operativo, accion_operativa, color_estado,
    tendencia_actual, tendencia_proy,
    incertidumbre_alta, ajuste_limitado, caudal_no_contabilizado_Ls,
    porcentaje_no_contabilizado, posible_fuga,
    hay_lavado, lavado_afecta_resultado, tipo_lavado,
    texto_entrada, texto_salida,
    mostrar_recomendacion_valvulero,
    Q_salida_valvulero_Ls, caudal_salida_ls_actual,
    max_ajuste_seguro_ls, caudal_max_planta, Q_planta_requerido_Ls,
    fuente_relacion, relacion_observada,
):
    # ── Porcentajes ──────────────────────────────────────────────────────────
    def pct(h):
        return max(0.0, min(100.0, h / altura_lleno * 100)) if altura_lleno > 0 else 0.0

    pct_actual   = pct(altura_actual)
    pct_objetivo = pct(nivel_objetivo)
    pct_rebose   = pct(altura_rebose)
    pct_minima   = pct(altura_minima)

    # ── Color segun nivel ────────────────────────────────────────────────────
    if pct_actual > 90:
        nivel_color = "#c0392b"; nivel_label = "NIVEL CRITICO ALTO"
        agua_c1, agua_c2 = "#e63946", "#ff6b7a"
    elif pct_actual > 75:
        nivel_color = "#d35400"; nivel_label = "NIVEL ALTO"
        agua_c1, agua_c2 = "#f4a261", "#ffd166"
    elif pct_actual < 15:
        nivel_color = "#c0392b"; nivel_label = "NIVEL CRITICO BAJO"
        agua_c1, agua_c2 = "#e63946", "#ff6b7a"
    elif pct_actual < 30:
        nivel_color = "#d35400"; nivel_label = "NIVEL BAJO"
        agua_c1, agua_c2 = "#f4a261", "#ffd166"
    else:
        nivel_color = "#1a7a5a"; nivel_label = "NIVEL NORMAL"
        agua_c1, agua_c2 = "#1a6fff", "#00c8ff"

    # ── Color de tendencia ───────────────────────────────────────────────────
    if tendencia_proy == "subiendo":
        tend_color = "#1a7a5a"; tend_icon = "▲"; tend_txt = "SUBIENDO"
    elif tendencia_proy == "bajando":
        tend_color = "#c0392b"; tend_icon = "▼"; tend_txt = "BAJANDO"
    else:
        tend_color = "#4a7899"; tend_icon = "●"; tend_txt = "ESTABLE"

    # ── Accion recomendada ───────────────────────────────────────────────────
    if delta_entrada_planta > 0.5:
        accion_color = "#1a7a5a"; accion_icon = "⬆"; accion_dir = "SUBIR"
    elif delta_entrada_planta < -0.5:
        accion_color = "#c0392b"; accion_icon = "⬇"; accion_dir = "BAJAR"
    else:
        accion_color = "#4a7899"; accion_icon = "●"; accion_dir = "MANTENER"

    # ── Helpers ──────────────────────────────────────────────────────────────
    def fmt_tiempo(v):
        if v is None:
            return "No aplica"
        h, m = int(v) // 60, int(v) % 60
        return f"{h}h {m}min" if h > 0 else f"{m} min"

    delta_h = altura_actual - altura_antes
    signo_dh = "+" if delta_h >= 0 else ""
    signo_qn = "+" if Q_neto_Ls >= 0 else ""
    signo_da = "+" if delta_entrada_planta >= 0 else ""
    signo_naj = "+" if Q_neto_post_ajuste_Ls >= 0 else ""

    rebose_txt = hora_rebose_str if hora_rebose_str else "No aplica"
    minimo_txt = hora_minimo_str if hora_minimo_str else "No aplica"
    rebose_dur = fmt_tiempo(t_rebose_min)
    minimo_dur = fmt_tiempo(t_minimo_min)

    rebose_color = ("#c0392b" if (t_rebose_min is not None and t_rebose_min < 60)
                    else "#d35400" if (t_rebose_min is not None and t_rebose_min < 180)
                    else "#4a7899")
    minimo_color = ("#c0392b" if (t_minimo_min is not None and t_minimo_min < 60)
                    else "#d35400" if (t_minimo_min is not None and t_minimo_min < 180)
                    else "#4a7899")

    rel_obs_txt = (f"{relacion_observada:.3f}"
                   if (relacion_observada is not None
                       and isinstance(relacion_observada, float)
                       and relacion_observada == relacion_observada)
                   else "N/D")

    urgente = ((t_rebose_min is not None and t_rebose_min < tiempo_recorrido_min) or
               (t_minimo_min is not None and t_minimo_min < tiempo_recorrido_min))

    # ── Alerta urgente ───────────────────────────────────────────────────────
    alerta_html = ""
    if urgente:
        alerta_html = (
            '<div style="background:#fef2f2;border:2px solid #c0392b;border-radius:12px;'
            'padding:10px 16px;margin:8px 12px 0 12px;display:flex;align-items:center;gap:8px;'
            'font-family:Inter,sans-serif;font-size:0.82rem;font-weight:700;color:#c0392b;'
            'letter-spacing:0.5px">'
            '⚡ LIMITE ALCANZABLE ANTES DEL RECORRIDO PTAP — ACCION INMEDIATA'
            '</div>'
        )

    # ── Incertidumbre ────────────────────────────────────────────────────────
    inc_html = ""
    if incertidumbre_alta:
        motivos = []
        if hay_lavado and lavado_afecta_resultado:
            motivos.append(f"lavado ({tipo_lavado})")
        if posible_fuga:
            motivos.append("fuga posible")
        if caudal_no_contabilizado_Ls > 80 or porcentaje_no_contabilizado > 35:
            motivos.append(f"Q no contabilizado {caudal_no_contabilizado_Ls:.1f} L/s")
        motivos_txt = " · ".join(motivos) if motivos else "multiples factores"
        inc_html = (
            f'<div style="background:#fffbeb;border:1px solid #d97706;border-radius:10px;'
            f'padding:8px 12px;margin-bottom:8px;font-family:Inter,sans-serif;'
            f'font-size:0.78rem;color:#92400e;line-height:1.5">'
            f'&#9888; ALTA INCERTIDUMBRE: {motivos_txt} — confirme con nueva lectura'
            f'</div>'
        )

    # ── Limite ajuste ────────────────────────────────────────────────────────
    limite_html = ""
    if ajuste_limitado:
        limite_html += (
            f'<div style="background:#fffbeb;border:1px dashed #d97706;border-radius:8px;'
            f'padding:6px 10px;margin-bottom:6px;font-family:Inter,sans-serif;'
            f'font-size:0.72rem;color:#92400e">'
            f'Ajuste limitado a +/-{max_ajuste_seguro_ls:.0f} L/s por incertidumbre'
            f'</div>'
        )
    if Q_planta_requerido_Ls > caudal_max_planta:
        limite_html += (
            f'<div style="background:#fffbeb;border:1px dashed #d97706;border-radius:8px;'
            f'padding:6px 10px;margin-bottom:6px;font-family:Inter,sans-serif;'
            f'font-size:0.72rem;color:#92400e">'
            f'Calculo ideal requiere {Q_planta_requerido_Ls:.1f} L/s, maximo: {caudal_max_planta:.1f} L/s'
            f'</div>'
        )

    # ── Valvulero ────────────────────────────────────────────────────────────
    valv_html = ""
    if mostrar_recomendacion_valvulero:
        if delta_entrada_planta > 0.5:
            vc = "#1a7a5a"; vd = "ABRIR SALIDA"
        elif delta_entrada_planta < -0.5:
            vc = "#c0392b"; vd = "CERRAR SALIDA"
        else:
            vc = "#4a7899"; vd = "MANTENER SALIDA"
        valv_html = (
            f'<div style="background:#f0f6ff;border:1.5px solid #2563eb;border-radius:12px;'
            f'padding:10px 14px;margin-top:8px;font-family:Inter,sans-serif">'
            f'<div style="font-size:0.68rem;font-weight:700;color:#1e3a5f;text-transform:uppercase;'
            f'letter-spacing:1px;margin-bottom:4px">Referencia valvulero</div>'
            f'<div style="font-size:1.1rem;font-weight:800;color:{vc}">{vd}</div>'
            f'<div style="font-size:0.8rem;color:#374151;margin-top:3px;line-height:1.5">'
            f'De <b>{caudal_salida_ls_actual:.2f}</b> L/s a <b>{Q_salida_valvulero_Ls:.2f}</b> L/s'
            f' — temporal mientras llega ajuste de planta</div>'
            f'</div>'
        )

    # ── SVG del tanque ────────────────────────────────────────────────────────
    TW, TH, TX, TY = 105, 255, 60, 30
    TB = TY + TH

    def nivel_y(p):
        return TB - (p / 100.0) * TH

    y_agua   = nivel_y(pct_actual)
    y_obj    = nivel_y(pct_objetivo)
    y_rebose = nivel_y(pct_rebose)
    y_minima = nivel_y(pct_minima)

    cx_w, cw_w = TX + 3, TW - 6

    def wave(y):
        p = f"M {cx_w},{y:.1f} "
        for k in range(8):
            p += (f"Q {cx_w + cw_w*(k+0.5)/8:.1f},{y + (-5 if k%2==0 else 5):.1f} "
                  f"{cx_w + cw_w*(k+1)/8:.1f},{y:.1f} ")
        for k in range(8):
            p += (f"Q {cx_w + cw_w*(k+8.5)/8:.1f},{y + (-5 if k%2==0 else 5):.1f} "
                  f"{cx_w + cw_w*(k+9)/8:.1f},{y:.1f} ")
        p += f"L {cx_w + cw_w*2},{TB} L {cx_w},{TB} Z"
        return p

    wave_d = wave(y_agua)

    burbujas = ""
    if tendencia_proy != "bajando":
        for bx, by, br, bd, bb in [
            (TX + int(TW*0.3), TB-12, 2.2, "3.2s", "0s"),
            (TX + int(TW*0.6), TB-7,  1.8, "4.1s", "1.1s"),
            (TX + int(TW*0.5), TB-22, 1.5, "5.0s", "2.2s"),
        ]:
            burbujas += (
                f'<circle cx="{bx}" cy="{by}" r="{br}" fill="rgba(255,255,255,0.65)">'
                f'<animate attributeName="cy" values="{TB};{TY}" dur="{bd}" repeatCount="indefinite" begin="{bb}"/>'
                f'<animate attributeName="opacity" values="0.6;0" dur="{bd}" repeatCount="indefinite" begin="{bb}"/>'
                f'</circle>'
            )

    escala = ""
    for i in range(5):
        sy = TY + i * TH // 4
        sv = altura_lleno * (1 - i / 4)
        escala += (
            f'<line x1="{TX-12}" y1="{sy}" x2="{TX-5}" y2="{sy}" stroke="#94a3b8" stroke-width="1.2"/>'
            f'<text x="{TX-14}" y="{sy+4}" text-anchor="end" font-size="7.5" '
            f'font-family="Inter,sans-serif" fill="#475569">{sv:.1f}</text>'
        )

    # ── HTML completo ─────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
      rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: #f0f6ff;
  font-family: Inter, sans-serif;
  color: #0f172a;
  padding: 10px;
  font-size: 13px;
}}

/* ── HEADER ── */
.hdr {{
  background: linear-gradient(90deg, #0d2347 0%, #1a4a8a 100%);
  border-radius: 14px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}}
.hdr-title {{
  font-size: 0.95rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}}
.hdr-sub {{
  font-size: 0.65rem;
  color: rgba(255,255,255,0.70);
  letter-spacing: 0.8px;
  margin-top: 2px;
}}
.hdr-time {{
  font-size: 1rem;
  font-weight: 700;
  color: #0d2347;
  background: rgba(255,255,255,0.92);
  border-radius: 8px;
  padding: 4px 14px;
  white-space: nowrap;
}}

/* ── LAYOUT PRINCIPAL ── */
.main-grid {{
  display: grid;
  grid-template-columns: 190px 1fr;
  gap: 10px;
  align-items: start;
}}

/* ── TARJETA GENÉRICA ── */
.card {{
  background: #ffffff;
  border: 1px solid #dce9f7;
  border-radius: 14px;
  padding: 11px 13px;
  box-shadow: 0 2px 8px rgba(10,22,40,0.06);
}}
.card-titulo {{
  font-size: 0.62rem;
  font-weight: 700;
  color: #1e3a5f;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 7px;
  border-bottom: 1px solid #e8f0fb;
  padding-bottom: 5px;
}}

/* ── PANEL TANQUE ── */
.tank-panel {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}}
.nivel-badge {{
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.8px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 2px solid {nivel_color};
  color: {nivel_color};
  background: {nivel_color}18;
  text-transform: uppercase;
}}

/* ── MÉTRICAS ── */
.metrics-row {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 8px;
}}
.mc {{
  background: #ffffff;
  border: 1px solid #dce9f7;
  border-radius: 12px;
  padding: 9px 11px;
  box-shadow: 0 2px 6px rgba(10,22,40,0.05);
  position: relative;
  overflow: hidden;
}}
.mc::before {{
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: 12px 12px 0 0;
  background: #1a6fff;
}}
.mc.verde::before {{ background: #16a34a; }}
.mc.rojo::before  {{ background: #dc2626; }}
.mc.naranja::before {{ background: #ea580c; }}
.mc.azul::before {{ background: #2563eb; }}
.m-lbl {{
  font-size: 0.60rem;
  font-weight: 600;
  color: #4a7899;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  display: block;
  margin-bottom: 3px;
}}
.m-val {{
  font-size: 1.3rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.1;
  display: block;
}}
.m-unit {{
  font-size: 0.60rem;
  color: #64748b;
  margin-top: 2px;
  display: block;
}}

/* ── ACCIÓN PRINCIPAL ── */
.accion-panel {{
  background: #ffffff;
  border: 2px solid {accion_color}55;
  border-radius: 14px;
  padding: 12px 14px;
  margin-bottom: 8px;
  box-shadow: 0 2px 8px rgba(10,22,40,0.06);
}}
.accion-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 9px;
}}
.accion-icono {{
  font-size: 2rem;
  color: {accion_color};
  font-weight: 900;
  line-height: 1;
}}
.accion-titulo {{
  font-size: 0.9rem;
  font-weight: 800;
  color: {accion_color};
  text-transform: uppercase;
  letter-spacing: 0.8px;
}}
.accion-sub {{
  font-size: 0.78rem;
  color: #374151;
  line-height: 1.4;
  margin-top: 2px;
}}
.accion-numeros {{
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}}
.an-item {{
  background: #f0f6ff;
  border: 1px solid #dce9f7;
  border-radius: 10px;
  padding: 7px 12px;
  text-align: center;
}}
.an-lbl {{
  font-size: 0.58rem;
  font-weight: 600;
  color: #4a7899;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  display: block;
  margin-bottom: 2px;
}}
.an-val {{
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  display: block;
}}
.an-unit {{
  font-size: 0.58rem;
  color: #64748b;
}}
.an-flecha {{
  font-size: 1.4rem;
  color: #94a3b8;
  font-weight: 700;
}}

/* ── LÍNEA DE TIEMPO ── */
.tl-chips {{
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
  margin-bottom: 7px;
}}
.chip {{
  border-radius: 8px;
  padding: 3px 10px;
  font-weight: 700;
  font-size: 0.78rem;
  white-space: nowrap;
}}
.chip-azul  {{ background: #1a6fff; color: #fff; }}
.chip-morado {{ background: #6c63ff; color: #fff; }}
.chip-verde  {{ background: #16a34a; color: #fff; }}
.tl-sep {{
  font-size: 0.72rem;
  color: #64748b;
}}
.tl-det {{
  font-size: 0.75rem;
  color: #374151;
  line-height: 1.6;
  margin-top: 4px;
}}
.tl-det b {{ color: #0f172a; }}
.tl-det .vc {{ color: #6c63ff; font-weight: 700; }}
.tl-det .vg {{ color: #16a34a; font-weight: 700; }}
.tl-det .va {{ color: {accion_color}; font-weight: 700; }}

/* ── FILA INFERIOR ── */
.bottom-row {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}}

/* ── BARRA DE NIVEL ── */
.nivel-bar-wrap {{
  position: relative;
  height: 26px;
  background: #e8f0fb;
  border-radius: 13px;
  overflow: visible;
  margin-bottom: 7px;
  border: 1px solid #dce9f7;
}}
.nivel-bar-fill {{
  position: absolute;
  left: 0; top: 0; bottom: 0;
  border-radius: 13px;
  background: linear-gradient(90deg, {agua_c1}, {agua_c2});
  width: {pct_actual:.1f}%;
  transition: width 0.8s ease;
}}
.nivel-bar-fill::after {{
  content: "";
  position: absolute;
  right: 0; top: 0; bottom: 0;
  width: 30px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35));
  border-radius: 0 13px 13px 0;
}}
.nivel-bar-obj {{
  position: absolute;
  top: -4px; bottom: -4px;
  width: 3px;
  background: #16a34a;
  border-radius: 2px;
  left: {pct_objetivo:.1f}%;
  box-shadow: 0 0 6px #16a34a88;
}}
.nivel-bar-reb {{
  position: absolute;
  top: -4px; bottom: -4px;
  width: 2px;
  background: #dc2626;
  border-radius: 2px;
  left: {pct_rebose:.1f}%;
}}
.nivel-bar-min {{
  position: absolute;
  top: -4px; bottom: -4px;
  width: 2px;
  background: #ea580c;
  border-radius: 2px;
  left: {pct_minima:.1f}%;
}}
.nivel-bar-txt {{
  position: absolute;
  left: 8px; top: 50%;
  transform: translateY(-50%);
  font-size: 0.70rem;
  font-weight: 700;
  color: #ffffff;
  z-index: 2;
  text-shadow: 0 1px 3px rgba(0,0,0,0.55);
}}
.leyenda-bar {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 0.60rem;
  color: #374151;
  margin-bottom: 7px;
}}
.ld {{ display: flex; align-items: center; gap: 3px; font-weight: 600; }}
.ld-dot {{ width: 9px; height: 9px; border-radius: 2px; flex-shrink: 0; }}

/* ── STATS RESULTADO ── */
.res-stats {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
}}
.rs {{
  text-align: center;
  background: #f8fbff;
  border: 1px solid #dce9f7;
  border-radius: 10px;
  padding: 7px 5px;
}}
.rs-lbl {{
  font-size: 0.58rem;
  font-weight: 600;
  color: #4a7899;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  display: block;
  margin-bottom: 2px;
}}
.rs-val {{
  font-size: 1.0rem;
  font-weight: 800;
  color: #0f172a;
  display: block;
}}

/* ── LIMITES ── */
.lim-row {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 7px;
}}
.lim-item {{
  background: #f8fbff;
  border-radius: 10px;
  padding: 8px 10px;
  border-left: 3px solid;
}}
.lim-lbl {{
  font-size: 0.60rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  display: block;
  margin-bottom: 3px;
}}
.lim-hora {{
  font-size: 1.15rem;
  font-weight: 800;
  display: block;
  line-height: 1.1;
}}
.lim-dur {{
  font-size: 0.65rem;
  color: #64748b;
  display: block;
  margin-top: 2px;
}}

/* ── BALANCE TÉCNICO ── */
.bal-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
}}
.bi {{
  text-align: center;
  background: #f8fbff;
  border: 1px solid #dce9f7;
  border-radius: 9px;
  padding: 7px 5px;
}}
.bi-lbl {{
  font-size: 0.58rem;
  font-weight: 600;
  color: #4a7899;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: block;
  margin-bottom: 2px;
}}
.bi-val {{
  font-size: 0.85rem;
  font-weight: 700;
  color: #0f172a;
  display: block;
}}

/* ── LECTURA COMPACTA BAJO TANQUE ── */
.lecturas-box {{
  width: 100%;
  background: #f0f6ff;
  border: 1px solid #dce9f7;
  border-radius: 10px;
  padding: 7px 10px;
  font-size: 0.72rem;
  color: #374151;
  line-height: 1.75;
  text-align: center;
}}
.lecturas-box b {{ color: #0f172a; }}
.lecturas-box .val-tend {{ color: {tend_color}; font-weight: 700; }}
.lecturas-box .val-nivel {{ color: {nivel_color}; font-weight: 700; }}
</style>
</head>
<body>

<!-- ═══ HEADER ═══ -->
<div class="hdr">
  <div>
    <div class="hdr-title">&#128167; Monitor de Tanque &mdash; PTAP</div>
    <div class="hdr-sub">Balance Hidráulico en Tiempo Real</div>
  </div>
  <div class="hdr-time">&#128336; {hora_actual_str}</div>
</div>

{alerta_html}
{'<div style="height:8px"></div>' if alerta_html else ''}

<!-- ═══ GRID PRINCIPAL ═══ -->
<div class="main-grid">

  <!-- ── COLUMNA TANQUE ── -->
  <div class="tank-panel">
    <div class="card" style="width:100%;display:flex;flex-direction:column;align-items:center;gap:7px;padding:11px 8px">
      <div style="font-size:0.62rem;font-weight:700;color:#1e3a5f;text-transform:uppercase;letter-spacing:1px">
        Estado del Tanque
      </div>
      <div class="nivel-badge">{nivel_label}</div>

      <svg viewBox="0 0 210 330" xmlns="http://www.w3.org/2000/svg"
           style="width:100%;max-width:200px;overflow:visible">
        <defs>
          <linearGradient id="gAg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="{agua_c2}" stop-opacity="0.95"/>
            <stop offset="100%" stop-color="{agua_c1}"/>
          </linearGradient>
          <linearGradient id="gTk" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%"   stop-color="#d0e8f5"/>
            <stop offset="35%"  stop-color="#eaf4fc"/>
            <stop offset="65%"  stop-color="#eaf4fc"/>
            <stop offset="100%" stop-color="#b8d4e8"/>
          </linearGradient>
          <linearGradient id="gRef" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%"  stop-color="rgba(255,255,255,0)"/>
            <stop offset="30%" stop-color="rgba(255,255,255,0.30)"/>
            <stop offset="60%" stop-color="rgba(255,255,255,0)"/>
          </linearGradient>
          <clipPath id="clipT">
            <rect x="{TX+3}" y="{TY}" width="{TW-6}" height="{TH}"/>
          </clipPath>
        </defs>

        <!-- Sombra -->
        <rect x="{TX+5}" y="{TY+5}" width="{TW}" height="{TH+22}"
              rx="9" fill="rgba(10,30,60,0.10)"/>
        <!-- Cuerpo -->
        <rect x="{TX}" y="{TY}" width="{TW}" height="{TH+22}"
              rx="9" fill="url(#gTk)" stroke="#8ab4cc" stroke-width="2"/>

        <!-- Agua -->
        <g clip-path="url(#clipT)">
          <rect x="{TX+3}" y="{y_agua:.1f}" width="{TW-6}"
                height="{TB - y_agua:.1f}" fill="url(#gAg)" opacity="0.92"/>
          <path d="{wave_d}" fill="{agua_c2}" opacity="0.45">
            <animateTransform attributeName="transform" type="translate"
              from="0,0" to="{-(cw_w):.0f},0" dur="2.6s" repeatCount="indefinite"/>
          </path>
          <rect x="{TX+3}" y="{y_agua:.1f}" width="{TW-6}"
                height="{TB - y_agua:.1f}" fill="url(#gRef)" opacity="0.5"/>
          {burbujas}
        </g>

        <!-- Línea rebose -->
        <line x1="{TX-5}" y1="{y_rebose:.1f}" x2="{TX+TW+5}" y2="{y_rebose:.1f}"
              stroke="#dc2626" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.9"/>
        <text x="{TX+TW+18}" y="{y_rebose+4:.1f}" font-size="7.5"
              font-family="Inter,sans-serif" fill="#dc2626" font-weight="700">
          REB {altura_rebose:.2f}m
        </text>

        <!-- Línea mínima -->
        <line x1="{TX-5}" y1="{y_minima:.1f}" x2="{TX+TW+5}" y2="{y_minima:.1f}"
              stroke="#ea580c" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.9"/>
        <text x="{TX+TW+18}" y="{y_minima+4:.1f}" font-size="7.5"
              font-family="Inter,sans-serif" fill="#ea580c" font-weight="700">
          MIN {altura_minima:.2f}m
        </text>

        <!-- Línea objetivo -->
        <line x1="{TX-5}" y1="{y_obj:.1f}" x2="{TX+TW+5}" y2="{y_obj:.1f}"
              stroke="#16a34a" stroke-width="1.5" stroke-dasharray="3,2" opacity="0.8"/>
        <text x="{TX+TW+18}" y="{y_obj+4:.1f}" font-size="7.5"
              font-family="Inter,sans-serif" fill="#16a34a" font-weight="700">
          OBJ {nivel_objetivo:.2f}m
        </text>

        <!-- Etiqueta nivel -->
        <rect x="{TX + TW//2 - 28:.0f}" y="{y_agua - 21:.1f}"
              width="56" height="17" rx="8" fill="{agua_c1}" opacity="0.92"/>
        <text x="{TX + TW//2:.0f}" y="{y_agua - 9:.1f}"
              text-anchor="middle" font-size="9"
              font-family="Inter,sans-serif" fill="white" font-weight="800">
          {altura_actual:.3f} m
        </text>

        <!-- Tapa -->
        <rect x="{TX-6}" y="{TY-9}" width="{TW+12}" height="12"
              rx="5" fill="#8ab4cc" stroke="#6a9ab8" stroke-width="1.5"/>
        <!-- Base -->
        <rect x="{TX-8}" y="{TB+22}" width="{TW+16}" height="11"
              rx="5" fill="#8ab4cc" stroke="#6a9ab8" stroke-width="1.5"/>
        <rect x="{TX+6}" y="{TB+33}" width="10" height="20"
              rx="3" fill="#7aa4bc" stroke="#6090a8" stroke-width="1"/>
        <rect x="{TX+TW-16}" y="{TB+33}" width="10" height="20"
              rx="3" fill="#7aa4bc" stroke="#6090a8" stroke-width="1"/>

        <!-- Escala -->
        <line x1="{TX-17}" y1="{TY}" x2="{TX-17}" y2="{TB}"
              stroke="#94a3b8" stroke-width="1.5"/>
        {escala}

        <!-- Tendencia -->
        <text x="{TX + TW//2:.0f}" y="{TB+16}"
              text-anchor="middle" font-size="10"
              font-family="Inter,sans-serif"
              fill="{tend_color}" font-weight="700">
          {tend_icon} {tend_txt}
        </text>
      </svg>

      <!-- Lecturas compactas -->
      <div class="lecturas-box">
        <b>{hora_antes_str}</b> &#8594; <span class="val-nivel">{altura_actual:.3f} m</span><br>
        Q neto: <span class="val-tend">{signo_qn}{Q_neto_Ls:.2f} L/s</span><br>
        &#916;h: <span class="val-tend">{signo_dh}{delta_h:.4f} m</span>
        &nbsp;&middot;&nbsp; &#916;t: <b>{delta_t_min:.0f} min</b>
      </div>
    </div>
  </div>

  <!-- ── COLUMNA DERECHA ── -->
  <div style="display:flex;flex-direction:column;gap:8px">

    {inc_html}

    <!-- Métricas -->
    <div class="metrics-row">
      <div class="mc azul">
        <span class="m-lbl">Nivel actual</span>
        <span class="m-val" style="color:{nivel_color}">{altura_actual:.3f}</span>
        <span class="m-unit">m &nbsp;·&nbsp; {pct_actual:.1f}% cap.</span>
      </div>
      <div class="mc verde">
        <span class="m-lbl">Entrada al tanque</span>
        <span class="m-val" style="color:#15803d">{Q_entrada_tanque_Ls:.2f}</span>
        <span class="m-unit">L/s estimada</span>
      </div>
      <div class="mc naranja">
        <span class="m-lbl">Salida del tanque</span>
        <span class="m-val" style="color:#c2410c">{caudal_salida_ls:.2f}</span>
        <span class="m-unit">L/s actual</span>
      </div>
      <div class="mc {'verde' if Q_neto_Ls >= 0 else 'rojo'}">
        <span class="m-lbl">Q neto tanque</span>
        <span class="m-val" style="color:{tend_color}">{signo_qn}{Q_neto_Ls:.2f}</span>
        <span class="m-unit">L/s &nbsp;·&nbsp; {tend_txt}</span>
      </div>
    </div>

    <!-- Acción principal -->
    <div class="accion-panel">
      {limite_html}
      <div class="accion-header">
        <div class="accion-icono">{accion_icon}</div>
        <div>
          <div class="accion-titulo">{accion_dir} ENTRADA A PLANTA</div>
          <div class="accion-sub">{texto_entrada} &nbsp;·&nbsp; Efecto en tanque: <b>{hora_efecto_str}</b> &nbsp;(recorrido {tiempo_recorrido_min} min)</div>
        </div>
      </div>
      <div class="accion-numeros">
        <div class="an-item">
          <span class="an-lbl">Planta actual</span>
          <span class="an-val">{caudal_entrada_planta_actual:.2f}</span>
          <span class="an-unit">L/s</span>
        </div>
        <div class="an-flecha">&#8594;</div>
        <div class="an-item">
          <span class="an-lbl">Recomendado</span>
          <span class="an-val" style="color:{accion_color}">{Q_planta_recomendado_Ls:.2f}</span>
          <span class="an-unit">L/s</span>
        </div>
        <div class="an-flecha">&#8594;</div>
        <div class="an-item">
          <span class="an-lbl">Ajuste</span>
          <span class="an-val" style="color:{accion_color}">{signo_da}{delta_entrada_planta:.2f}</span>
          <span class="an-unit">L/s</span>
        </div>
        <div class="an-item">
          <span class="an-lbl">Rel. P&#8594;T</span>
          <span class="an-val">{relacion_operativa:.3f}</span>
          <span class="an-unit">{fuente_relacion[:22]}</span>
        </div>
      </div>
    </div>

    <!-- Línea de tiempo -->
    <div class="card">
      <div class="card-titulo">&#9203; Línea de tiempo del ajuste</div>
      <div class="tl-chips">
        <span class="chip chip-azul">Ajustar ahora &middot; {hora_actual_str}</span>
        <span class="tl-sep">&#8594; {tiempo_recorrido_min} min &#8594;</span>
        <span class="chip chip-morado">Efecto en tanque &middot; {hora_efecto_str}</span>
        <span class="tl-sep">&#8594; {tiempo_correccion_min} min &#8594;</span>
        <span class="chip chip-verde">Objetivo {nivel_objetivo:.2f} m</span>
      </div>
      <div class="tl-det">
        Nivel cuando llega ajuste: <span class="vc">{nivel_cuando_llega_ajuste:.3f} m</span>
        &nbsp;&middot;&nbsp; Objetivo: <span class="vg">{nivel_objetivo:.2f} m</span>
        &nbsp;&middot;&nbsp; Estimado post-corrección: <span class="va">{nivel_final_estimado:.3f} m</span>
        &nbsp;&middot;&nbsp; Q neto esperado: <span style="color:{tend_color};font-weight:700">{signo_naj}{Q_neto_post_ajuste_Ls:.2f} L/s</span>
      </div>
    </div>

    <!-- Fila inferior: límites + proyección -->
    <div class="bottom-row">

      <!-- Límites -->
      <div class="card">
        <div class="card-titulo">&#9888; Llegada estimada a límites</div>
        <div class="lim-row">
          <div class="lim-item" style="border-color:{rebose_color}">
            <span class="lim-lbl" style="color:{rebose_color}">&#128308; Rebose ({altura_rebose:.2f} m)</span>
            <span class="lim-hora" style="color:{rebose_color}">{rebose_txt}</span>
            <span class="lim-dur">{rebose_dur}</span>
          </div>
          <div class="lim-item" style="border-color:{minimo_color}">
            <span class="lim-lbl" style="color:{minimo_color}">&#128992; Mínimo ({altura_minima:.2f} m)</span>
            <span class="lim-hora" style="color:{minimo_color}">{minimo_txt}</span>
            <span class="lim-dur">{minimo_dur}</span>
          </div>
        </div>
      </div>

      <!-- Proyección -->
      <div class="card">
        <div class="card-titulo">&#128202; Nivel proyectado</div>

        <div class="nivel-bar-wrap">
          <div class="nivel-bar-fill"></div>
          <div class="nivel-bar-obj"></div>
          <div class="nivel-bar-reb"></div>
          <div class="nivel-bar-min"></div>
          <div class="nivel-bar-txt">{altura_actual:.3f} m ({pct_actual:.0f}%)</div>
        </div>

        <div class="leyenda-bar">
          <div class="ld"><div class="ld-dot" style="background:{agua_c1}"></div>Actual</div>
          <div class="ld"><div class="ld-dot" style="background:#16a34a"></div>Objetivo</div>
          <div class="ld"><div class="ld-dot" style="background:#dc2626"></div>Rebose</div>
          <div class="ld"><div class="ld-dot" style="background:#ea580c"></div>Mínimo</div>
        </div>

        <div class="res-stats">
          <div class="rs">
            <span class="rs-lbl">Cuando llega ajuste</span>
            <span class="rs-val" style="color:#6c63ff">{nivel_cuando_llega_ajuste:.3f} m</span>
          </div>
          <div class="rs">
            <span class="rs-lbl">Post corrección</span>
            <span class="rs-val" style="color:{accion_color}">{nivel_final_estimado:.3f} m</span>
          </div>
          <div class="rs">
            <span class="rs-lbl">Q neto esperado</span>
            <span class="rs-val" style="color:{tend_color}">{signo_qn}{Q_neto_proyeccion_Ls:.2f} L/s</span>
          </div>
        </div>
      </div>
    </div>

    {valv_html}

    <!-- Balance técnico -->
    <div class="card">
      <div class="card-titulo">&#9881; Balance técnico</div>
      <div class="bal-grid">
        <div class="bi">
          <span class="bi-lbl">Q no contabilizado</span>
          <span class="bi-val" style="color:{'#c0392b' if caudal_no_contabilizado_Ls > 80 else '#0f172a'}">{caudal_no_contabilizado_Ls:.2f} L/s ({porcentaje_no_contabilizado:.1f}%)</span>
        </div>
        <div class="bi">
          <span class="bi-lbl">Q entrada planta ref.</span>
          <span class="bi-val">{caudal_entrada_planta_actual:.2f} L/s</span>
        </div>
        <div class="bi">
          <span class="bi-lbl">Área equiv.</span>
          <span class="bi-val">{area_equiv:.2f} m²</span>
        </div>
        <div class="bi">
          <span class="bi-lbl">&#916;h observado</span>
          <span class="bi-val">{signo_dh}{delta_h:.4f} m</span>
        </div>
        <div class="bi">
          <span class="bi-lbl">Rel. observada</span>
          <span class="bi-val">{rel_obs_txt}</span>
        </div>
        <div class="bi">
          <span class="bi-lbl">Rel. operativa</span>
          <span class="bi-val">{relacion_operativa:.3f}</span>
        </div>
      </div>
    </div>

  </div><!-- fin columna derecha -->
</div><!-- fin main-grid -->

</body>
</html>"""
    return html
# =========================================
# CALCULADORA DE TANQUE DE AGUA
# =========================================
def mostrar_calculadora_tanque():

    st.markdown("<div class='bloque'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='etiqueta'>🏗️ Calculadora de tanque de agua</div>",
        unsafe_allow_html=True
    )

    col_iz, col_der = st.columns([1.0, 1.8], gap="large")

    # ─────────────────────────────────────────────────────────────────────────
    # FUNCIONES INTERNAS
    # ─────────────────────────────────────────────────────────────────────────
    def rangos_dia(inicio, fin):
        if inicio is None or fin is None:
            return []
        inicio = int(inicio) % 1440
        fin    = int(fin) % 1440
        if fin >= inicio:
            return [(inicio, fin)]
        return [(inicio, 1440), (0, fin)]

    def solape_minutos(inicio_a, fin_a, inicio_b, fin_b):
        total = 0
        for a1, a2 in rangos_dia(inicio_a, fin_a):
            for b1, b2 in rangos_dia(inicio_b, fin_b):
                total += max(0, min(a2, b2) - max(a1, b1))
        return total

    def obtener_relacion_por_franja(minuto_actual):
        hora = int(minuto_actual // 60)
        if   0 <= hora < 6:   return 0.49, "00:00–05:59"
        elif 6 <= hora < 12:  return 0.76, "06:00–11:59"
        elif 12 <= hora < 16: return 0.82, "12:00–15:59"
        elif 16 <= hora < 20: return 0.70, "16:00–19:59"
        else:                 return 0.64, "20:00–23:59"

    def limitar_valor(valor, minimo, maximo):
        return max(minimo, min(valor, maximo))

    def texto_delta_entrada(delta):
        if delta > 0.1:  return f"Subir entrada a planta en {delta:.2f} L/s"
        elif delta < -0.1: return f"Bajar entrada a planta en {abs(delta):.2f} L/s"
        return "Mantener entrada actual a planta"

    def texto_delta_salida(delta):
        if delta > 0.1:  return f"Abrir salida del tanque en {delta:.2f} L/s"
        elif delta < -0.1: return f"Reducir salida del tanque en {abs(delta):.2f} L/s"
        return "Mantener salida actual del tanque"

    def formato_horas(v):
        if v is None: return "No aplica"
        h, m = int(v) // 60, int(v) % 60
        return f"{h} h {m} min" if h > 0 else f"{m} min"

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL IZQUIERDO — ENTRADAS
    # ─────────────────────────────────────────────────────────────────────────
    with col_iz:

        with st.expander("📐 Geometría del tanque", expanded=True):
            volumen_total = st.number_input(
                "Volumen total del tanque (m³)",
                min_value=1.0, value=1350.0, step=10.0, format="%.2f", key="tanq_vol_total"
            )
            altura_lleno = st.number_input(
                "Altura cuando el tanque está lleno (m)",
                min_value=0.01, value=2.85, step=0.01, format="%.2f", key="tanq_altura_lleno"
            )
            area_equiv = volumen_total / altura_lleno if altura_lleno > 0 else 0.0
            st.info(f"Área equivalente: **{area_equiv:.4f} m²** = {volumen_total:.1f} / {altura_lleno:.2f}")

        with st.expander("⚙️ Límites operativos", expanded=True):
            altura_rebose = st.number_input(
                "Altura límite de rebose (m)",
                min_value=0.01, value=2.82, step=0.01, format="%.2f", key="tanq_altura_rebose"
            )
            altura_minima = st.number_input(
                "Altura mínima operativa (m)",
                min_value=0.0, value=1.40, step=0.01, format="%.2f", key="tanq_altura_minima"
            )

        with st.expander("🕐 Lecturas de nivel", expanded=True):
            hora_antes_txt = st.text_input(
                "Hora lectura anterior (HH:MM)", value="04:40", key="tanq_hora_antes"
            )
            altura_antes = st.number_input(
                "Altura lectura anterior (m)",
                min_value=0.0, value=2.85, step=0.01, format="%.2f", key="tanq_altura_antes"
            )
            hora_actual_txt = st.text_input(
                "Hora lectura actual (HH:MM)", value="05:40", key="tanq_hora_actual"
            )
            altura_actual = st.number_input(
                "Altura lectura actual (m)",
                min_value=0.0, value=2.82, step=0.01, format="%.2f", key="tanq_altura_actual"
            )

        with st.expander("🚰 Caudales", expanded=True):
            st.info(
                "Entrada a **planta** ≠ entrada al **tanque**. "
                "Pérdidas, lavados y tiempo hidráulico reducen lo que llega al tanque."
            )
            caudal_max_planta = st.number_input(
                "Caudal máximo de la planta (L/s)",
                min_value=1.0, value=220.0, step=1.0, format="%.2f", key="tanq_caudal_max_planta"
            )
            caudal_entrada_planta_actual = st.number_input(
                "Caudal actual de entrada a planta (L/s)",
                min_value=0.0, value=213.5, step=0.5, format="%.2f", key="tanq_caudal_entrada_planta_actual"
            )
            caudal_planta_referencia = st.number_input(
                "Caudal promedio de planta para esta lectura (L/s)",
                min_value=0.0, value=float(caudal_entrada_planta_actual),
                step=0.5, format="%.2f", key="tanq_caudal_planta_referencia",
                help="Caudal que probablemente originó el cambio observado en el tanque."
            )
            usar_entrada_manual = st.checkbox(
                "Ingresar caudal de entrada al tanque manualmente",
                value=False, key="tanq_usar_entrada_manual"
            )
            caudal_entrada_manual_ls = None
            if usar_entrada_manual:
                caudal_entrada_manual_ls = st.number_input(
                    "Caudal de entrada al tanque (L/s)",
                    min_value=0.0, value=0.0, step=0.5, format="%.2f", key="tanq_caudal_entrada_manual"
                )
            caudal_salida_ls = st.number_input(
                "Caudal de salida del tanque (L/s)",
                min_value=0.0, value=150.0, step=0.5, format="%.2f", key="tanq_caudal_salida"
            )
            caudal_min_salida = st.number_input(
                "Caudal mínimo de salida (L/s)",
                min_value=0.0, value=0.0, step=1.0, format="%.2f", key="tanq_caudal_min_salida"
            )
            caudal_max_salida = st.number_input(
                "Caudal máximo de salida (L/s)",
                min_value=0.0, value=200.0, step=1.0, format="%.2f", key="tanq_caudal_max_salida"
            )

        with st.expander("⏱️ Tiempo de recorrido PTAP", expanded=True):
            tiempo_recorrido_min = st.number_input(
                "Tiempo de recorrido PTAP (minutos)",
                min_value=0, value=45, step=1, key="tanq_tiempo_recorrido",
                help="Desde que ajustas en planta hasta que el cambio llega al tanque."
            )

        with st.expander("🎯 Nivel objetivo y corrección", expanded=True):
            nivel_objetivo_default = min(max(2.80, altura_minima), altura_rebose)
            if "tanq_nivel_objetivo" in st.session_state:
                st.session_state.tanq_nivel_objetivo = min(
                    max(float(st.session_state.tanq_nivel_objetivo), float(altura_minima)),
                    float(altura_rebose)
                )
            nivel_objetivo = st.number_input(
                "Nivel objetivo del tanque (m)",
                min_value=float(altura_minima), max_value=float(altura_rebose),
                value=float(nivel_objetivo_default), step=0.01, format="%.2f",
                key="tanq_nivel_objetivo"
            )
            banda_control = st.number_input(
                "Banda aceptable (m)",
                min_value=0.01, value=0.05, step=0.01, format="%.2f", key="tanq_banda_control"
            )
            tiempo_correccion_min = st.number_input(
                "Tiempo para corregir el nivel (min)",
                min_value=5, value=45, step=5, key="tanq_tiempo_correccion"
            )
            usar_demanda_esperada = st.checkbox(
                "Usar caudal de salida esperado diferente al actual",
                value=False, key="tanq_usar_demanda_esperada"
            )
            if usar_demanda_esperada:
                caudal_salida_esperada_ls = st.number_input(
                    "Caudal de salida esperado (L/s)",
                    min_value=0.0, value=float(caudal_salida_ls),
                    step=0.5, format="%.2f", key="tanq_caudal_salida_esperada"
                )
            else:
                caudal_salida_esperada_ls = caudal_salida_ls

        with st.expander("🌙 Lavados, fugas o pérdidas", expanded=False):
            hay_lavado = st.checkbox("Hay lavado de filtro o estructura", value=False, key="tanq_hay_lavado")
            tipo_lavado = "No aplica"
            hora_ini_lavado_txt = ""
            hora_fin_lavado_txt = ""
            conoce_caudal_lavado = False
            caudal_lavado_estimado = 0.0
            if hay_lavado:
                tipo_lavado = st.selectbox(
                    "Tipo de evento",
                    ["Lavado de filtro", "Lavado de sedimentador", "Lavado de floculador",
                     "Lavado de estructura", "Purga", "Otro"],
                    key="tanq_tipo_lavado"
                )
                col_lav1, col_lav2 = st.columns(2)
                with col_lav1:
                    hora_ini_lavado_txt = st.text_input("Hora inicio (HH:MM)", value="", key="tanq_hora_ini_lavado")
                with col_lav2:
                    hora_fin_lavado_txt = st.text_input("Hora fin (HH:MM)", value="", key="tanq_hora_fin_lavado")
                conoce_caudal_lavado = st.checkbox("Conozco caudal del lavado", value=False, key="tanq_conoce_caudal_lavado")
                if conoce_caudal_lavado:
                    caudal_lavado_estimado = st.number_input(
                        "Caudal del lavado (L/s)", min_value=0.0, value=0.0,
                        step=1.0, format="%.2f", key="tanq_caudal_lavado_estimado"
                    )
            posible_fuga = st.checkbox("Hay posible fuga o pérdida no medida", value=False, key="tanq_posible_fuga")
            mostrar_recomendacion_valvulero = st.checkbox(
                "Mostrar referencia para valvulero", value=True, key="tanq_mostrar_recomendacion_valvulero"
            )
            limitar_ajuste_por_incertidumbre = st.checkbox(
                "Limitar ajuste con alta incertidumbre", value=True, key="tanq_limitar_ajuste_incertidumbre"
            )
            max_ajuste_seguro_ls = st.number_input(
                "Ajuste máximo seguro por ciclo (L/s)",
                min_value=1.0, value=15.0, step=1.0, format="%.2f", key="tanq_max_ajuste_seguro"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL DERECHO — CÁLCULOS Y PANEL HTML
    # ─────────────────────────────────────────────────────────────────────────
    with col_der:

        # ── Validaciones ────────────────────────────────────────────────────
        errores = []
        if altura_lleno <= 0:
            errores.append("La altura del tanque lleno debe ser mayor que cero.")
        if altura_rebose > altura_lleno:
            errores.append("La altura de rebose no puede superar la altura cuando el tanque está lleno.")
        if altura_minima >= altura_rebose:
            errores.append("La altura mínima debe ser menor que la altura de rebose.")
        if caudal_min_salida > caudal_max_salida:
            errores.append("El caudal mínimo de salida no puede ser mayor que el máximo.")
        min_antes  = parse_hora(hora_antes_txt)
        min_actual = parse_hora(hora_actual_txt)
        if min_antes is None:
            errores.append(f"Hora anterior inválida: '{hora_antes_txt}'.")
        if min_actual is None:
            errores.append(f"Hora actual inválida: '{hora_actual_txt}'.")
        if errores:
            for e in errores:
                st.error(e)
            st.markdown("</div>", unsafe_allow_html=True)
            return

        delta_t_min = (min_actual - min_antes if min_actual >= min_antes
                       else 1440 - min_antes + min_actual)
        if delta_t_min == 0:
            st.error("Las dos horas son iguales. Ingresa horas distintas.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        hora_antes_str  = minutos_a_hora_str(min_antes)
        hora_actual_str = minutos_a_hora_str(min_actual)
        delta_t_s = delta_t_min * 60
        delta_h   = altura_actual - altura_antes

        # ── Balance actual ───────────────────────────────────────────────────
        if usar_entrada_manual and caudal_entrada_manual_ls is not None:
            Q_entrada_tanque_Ls = caudal_entrada_manual_ls
            Q_neto_Ls   = Q_entrada_tanque_Ls - caudal_salida_ls
            Q_neto_m3s  = Q_neto_Ls / 1000
        else:
            Q_neto_m3s  = area_equiv * delta_h / delta_t_s
            Q_neto_Ls   = Q_neto_m3s * 1000
            Q_entrada_tanque_Ls = caudal_salida_ls + Q_neto_Ls

        tendencia_actual = ("subiendo" if Q_neto_Ls > 0.01 else
                            "bajando"  if Q_neto_Ls < -0.01 else "estable")

        # ── Proyección recorrido ─────────────────────────────────────────────
        t_recorrido_s = tiempo_recorrido_min * 60
        hora_efecto_str = minutos_a_hora_futura(min_actual, tiempo_recorrido_min)
        Q_neto_proyeccion_Ls  = Q_entrada_tanque_Ls - caudal_salida_esperada_ls
        Q_neto_proyeccion_m3s = Q_neto_proyeccion_Ls / 1000
        tendencia_proy = ("subiendo" if Q_neto_proyeccion_Ls > 0.01 else
                          "bajando"  if Q_neto_proyeccion_Ls < -0.01 else "estable")
        delta_h_recorrido = (Q_neto_proyeccion_m3s * t_recorrido_s / area_equiv
                             if area_equiv > 0 else 0.0)
        nivel_cuando_llega_ajuste = altura_actual + delta_h_recorrido

        nivel_objetivo_min = nivel_objetivo - banda_control
        nivel_objetivo_max = nivel_objetivo + banda_control

        # ── Lavados / fugas ──────────────────────────────────────────────────
        min_ini_lavado = None
        min_fin_lavado = None
        lavado_horas_validas   = False
        dur_lavado_min         = 0
        solape_lavado_lectura_min = 0
        solape_lavado_futuro_min  = 0
        lavado_afecta_resultado   = False
        lavado_afecta_futuro      = False
        volumen_lavado_m3 = None

        min_planta_inicio = (min_antes  - tiempo_recorrido_min) % 1440
        min_planta_fin    = (min_actual - tiempo_recorrido_min) % 1440
        min_futuro_fin    = (min_actual + tiempo_recorrido_min + tiempo_correccion_min) % 1440

        if hay_lavado:
            min_ini_lavado = parse_hora(hora_ini_lavado_txt)
            min_fin_lavado = parse_hora(hora_fin_lavado_txt)
            if min_ini_lavado is not None and min_fin_lavado is not None:
                lavado_horas_validas = True
                dur_lavado_min = (min_fin_lavado - min_ini_lavado
                                  if min_fin_lavado >= min_ini_lavado
                                  else 1440 - min_ini_lavado + min_fin_lavado)
                solape_lavado_lectura_min = solape_minutos(
                    min_antes, min_actual, min_ini_lavado, min_fin_lavado)
                solape_lp = solape_minutos(
                    min_planta_inicio, min_planta_fin, min_ini_lavado, min_fin_lavado)
                solape_lavado_futuro_min = solape_minutos(
                    min_actual, min_futuro_fin, min_ini_lavado, min_fin_lavado)
                lavado_afecta_resultado = (solape_lavado_lectura_min > 0 or solape_lp > 0)
                lavado_afecta_futuro    = solape_lavado_futuro_min > 0
                if conoce_caudal_lavado and caudal_lavado_estimado > 0:
                    volumen_lavado_m3 = caudal_lavado_estimado * dur_lavado_min * 60 / 1000

        caudal_no_contabilizado_Ls  = max(0.0, caudal_planta_referencia - Q_entrada_tanque_Ls)
        porcentaje_no_contabilizado = (caudal_no_contabilizado_Ls / caudal_planta_referencia * 100
                                       if caudal_planta_referencia > 0 else 0.0)
        caudal_no_contabilizado_alto = (caudal_no_contabilizado_Ls > 80 or
                                        porcentaje_no_contabilizado > 35)
        incertidumbre_alta = (caudal_no_contabilizado_alto or lavado_afecta_resultado or
                              lavado_afecta_futuro or posible_fuga)

        # ── Relación planta → tanque ─────────────────────────────────────────
        relacion_franja, nombre_franja = obtener_relacion_por_franja(min_actual)
        relacion_observada = (Q_entrada_tanque_Ls / caudal_planta_referencia
                              if caudal_planta_referencia > 0 and Q_entrada_tanque_Ls > 0 else float('nan'))
        relacion_observada_valida = (not (relacion_observada != relacion_observada) and
                                     relacion_observada > 0)
        if relacion_observada_valida:
            relacion_operativa = relacion_observada
            fuente_relacion    = "Relación observada en esta lectura"
        else:
            relacion_operativa = relacion_franja
            fuente_relacion    = f"Referencia por franja {nombre_franja}"

        # ── Llegada a límites ────────────────────────────────────────────────
        hora_rebose_str = None; hora_minimo_str = None
        t_rebose_min = None;    t_minimo_min    = None
        if Q_neto_proyeccion_m3s > 0 and (altura_rebose - altura_actual) > 0:
            t_rebose_min    = area_equiv * (altura_rebose - altura_actual) / Q_neto_proyeccion_m3s / 60
            hora_rebose_str = minutos_a_hora_futura(min_actual, t_rebose_min)
        if Q_neto_proyeccion_m3s < 0 and (altura_actual - altura_minima) > 0:
            t_minimo_min    = area_equiv * (altura_actual - altura_minima) / abs(Q_neto_proyeccion_m3s) / 60
            hora_minimo_str = minutos_a_hora_futura(min_actual, t_minimo_min)

        # ── Caudal requerido ─────────────────────────────────────────────────
        t_correccion_s = max(tiempo_correccion_min * 60, 60)
        if nivel_cuando_llega_ajuste < nivel_objetivo_min:
            estado_operativo = "Nivel por debajo del objetivo"
            accion_operativa = "corregir subiendo"
            color_estado     = "orange"
            Q_neto_correccion_Ls   = (area_equiv * (nivel_objetivo - nivel_cuando_llega_ajuste)
                                      / t_correccion_s * 1000)
            Q_requerido_tanque_Ls  = caudal_salida_esperada_ls + Q_neto_correccion_Ls
        elif nivel_cuando_llega_ajuste > nivel_objetivo_max:
            estado_operativo = "Nivel por encima del objetivo"
            accion_operativa = "corregir bajando"
            color_estado     = "red"
            Q_neto_correccion_Ls   = (area_equiv * (nivel_objetivo - nivel_cuando_llega_ajuste)
                                      / t_correccion_s * 1000)
            Q_requerido_tanque_Ls  = caudal_salida_esperada_ls + Q_neto_correccion_Ls
        else:
            estado_operativo = "Nivel dentro de la banda aceptable"
            accion_operativa = "sostener nivel"
            color_estado     = "green"
            Q_requerido_tanque_Ls  = (Q_entrada_tanque_Ls if abs(Q_neto_proyeccion_Ls) <= 2
                                      else caudal_salida_esperada_ls)

        Q_requerido_tanque_Ls = max(0.0, Q_requerido_tanque_Ls)
        Q_planta_requerido_Ls = (Q_requerido_tanque_Ls / relacion_operativa
                                 if relacion_operativa > 0 else caudal_entrada_planta_actual)
        Q_planta_requerido_Ls = max(0.0, Q_planta_requerido_Ls)
        Q_planta_sin_limite   = min(Q_planta_requerido_Ls, caudal_max_planta)
        delta_entrada_sin_lim = Q_planta_sin_limite - caudal_entrada_planta_actual

        if incertidumbre_alta and limitar_ajuste_por_incertidumbre:
            delta_lim = limitar_valor(delta_entrada_sin_lim, -max_ajuste_seguro_ls, max_ajuste_seguro_ls)
            Q_planta_recomendado_Ls = limitar_valor(
                caudal_entrada_planta_actual + delta_lim, 0.0, caudal_max_planta)
            ajuste_limitado = abs(delta_lim - delta_entrada_sin_lim) > 0.1
        else:
            Q_planta_recomendado_Ls = Q_planta_sin_limite
            ajuste_limitado = False

        delta_entrada_planta = Q_planta_recomendado_Ls - caudal_entrada_planta_actual
        texto_entrada = texto_delta_entrada(delta_entrada_planta)

        # ── Resultado después de que el ajuste de planta llega al tanque ───────
        Q_tanque_post_ajuste_Ls = Q_planta_recomendado_Ls * relacion_operativa

        Q_neto_post_ajuste_Ls = Q_tanque_post_ajuste_Ls - caudal_salida_esperada_ls

        nivel_final_estimado = nivel_cuando_llega_ajuste + (
            (Q_neto_post_ajuste_Ls / 1000) * t_correccion_s / area_equiv
        )
     
        Q_salida_valvulero_Ls = limitar_valor(Q_entrada_tanque_Ls, caudal_min_salida, caudal_max_salida)
        delta_salida_valvulero = Q_salida_valvulero_Ls - caudal_salida_ls
        texto_salida = texto_delta_salida(delta_salida_valvulero)

        # ── Relación observada para HTML ─────────────────────────────────────
        rel_obs_display = relacion_observada if relacion_observada_valida else float('nan')

        # ── Renderizar panel HTML ────────────────────────────────────────────
        panel_html = generar_panel_resultados_html(
            altura_actual=altura_actual,
            altura_antes=altura_antes,
            altura_lleno=altura_lleno,
            altura_rebose=altura_rebose,
            altura_minima=altura_minima,
            nivel_objetivo=nivel_objetivo,
            banda_control=banda_control,
            area_equiv=area_equiv,
            volumen_total=volumen_total,
            Q_entrada_tanque_Ls=Q_entrada_tanque_Ls,
            caudal_salida_ls=caudal_salida_ls,
            Q_neto_Ls=Q_neto_Ls,
            Q_neto_proyeccion_Ls=Q_neto_proyeccion_Ls,
            caudal_salida_esperada_ls=caudal_salida_esperada_ls,
            Q_planta_recomendado_Ls=Q_planta_recomendado_Ls,
            caudal_entrada_planta_actual=caudal_entrada_planta_actual,
            delta_entrada_planta=delta_entrada_planta,
            relacion_operativa=relacion_operativa,
            Q_tanque_post_ajuste_Ls=Q_tanque_post_ajuste_Ls,
            Q_neto_post_ajuste_Ls=Q_neto_post_ajuste_Ls,
            hora_antes_str=hora_antes_str,
            hora_actual_str=hora_actual_str,
            hora_efecto_str=hora_efecto_str,
            delta_t_min=delta_t_min,
            tiempo_recorrido_min=tiempo_recorrido_min,
            tiempo_correccion_min=tiempo_correccion_min,
            nivel_cuando_llega_ajuste=nivel_cuando_llega_ajuste,
            nivel_final_estimado=nivel_final_estimado,
            hora_rebose_str=hora_rebose_str,
            hora_minimo_str=hora_minimo_str,
            t_rebose_min=t_rebose_min,
            t_minimo_min=t_minimo_min,
            estado_operativo=estado_operativo,
            accion_operativa=accion_operativa,
            color_estado=color_estado,
            tendencia_actual=tendencia_actual,
            tendencia_proy=tendencia_proy,
            incertidumbre_alta=incertidumbre_alta,
            ajuste_limitado=ajuste_limitado,
            caudal_no_contabilizado_Ls=caudal_no_contabilizado_Ls,
            porcentaje_no_contabilizado=porcentaje_no_contabilizado,
            posible_fuga=posible_fuga,
            hay_lavado=hay_lavado,
            lavado_afecta_resultado=lavado_afecta_resultado,
            tipo_lavado=tipo_lavado,
            texto_entrada=texto_entrada,
            texto_salida=texto_salida,
            mostrar_recomendacion_valvulero=mostrar_recomendacion_valvulero,
            Q_salida_valvulero_Ls=Q_salida_valvulero_Ls,
            caudal_salida_ls_actual=caudal_salida_ls,
            max_ajuste_seguro_ls=max_ajuste_seguro_ls,
            caudal_max_planta=caudal_max_planta,
            Q_planta_requerido_Ls=Q_planta_requerido_Ls,
            fuente_relacion=fuente_relacion,
            relacion_observada=rel_obs_display,
        )

        components.html(panel_html, height=1060, scrolling=False)

        # ── Gráfica Plotly (expandible) ──────────────────────────────────────
        with st.expander("📈 Proyección del nivel — próximas 6 horas", expanded=False):
            pasos_min  = list(range(0, 361, 10))
            horas_proj = [minutos_a_hora_futura(min_actual, p) for p in pasos_min]
            y_max = max(altura_rebose * 1.13, altura_actual * 1.2)

            niv_proj = [round(max(0.0, min(altura_rebose*1.05,
                          altura_actual + Q_neto_proyeccion_m3s*(p*60)/area_equiv)), 4)
                        for p in pasos_min]

            niv_aj = []
            for p in pasos_min:
                if p < tiempo_recorrido_min:
                    h_aj = altura_actual + Q_neto_proyeccion_m3s * (p*60) / area_equiv
                else:
                    h_aj = nivel_cuando_llega_ajuste + (
                        (Q_neto_post_ajuste_Ls/1000) * ((p-tiempo_recorrido_min)*60) / area_equiv)
                niv_aj.append(round(max(0.0, min(altura_rebose*1.05, h_aj)), 4))

            fig = go.Figure()
            fig.add_hrect(y0=altura_rebose, y1=y_max,
                          fillcolor="rgba(230,57,70,0.07)", line_width=0)
            fig.add_hrect(y0=0, y1=altura_minima,
                          fillcolor="rgba(244,162,97,0.07)", line_width=0)
            for y_val, color, label in [
                (altura_rebose, "#e63946", f"Rebose {altura_rebose:.2f}m"),
                (altura_minima, "#f4a261", f"Mínimo {altura_minima:.2f}m"),
                (nivel_objetivo, "#00c8a0", f"Objetivo {nivel_objetivo:.2f}m"),
            ]:
                fig.add_shape(type="line", x0=0, x1=1, xref="paper",
                              y0=y_val, y1=y_val,
                              line=dict(color=color, width=1.8, dash="dash"))
                fig.add_annotation(x=1, y=y_val, xref="paper",
                                   text=label, showarrow=False,
                                   font=dict(color=color, size=10),
                                   xanchor="left")
            fig.add_trace(go.Scatter(
                x=horas_proj, y=niv_proj, mode="lines",
                name="Sin ajuste", line=dict(color="#1a6fff", width=2.5, shape="spline"),
                fill="tozeroy", fillcolor="rgba(26,111,255,0.06)"
            ))
            fig.add_trace(go.Scatter(
                x=horas_proj, y=niv_aj, mode="lines",
                name="Con ajuste recomendado",
                line=dict(color="#00c8a0", width=2.5, dash="dash", shape="spline"),
                fill="tozeroy", fillcolor="rgba(0,200,160,0.04)"
            ))
            fig.add_trace(go.Scatter(
                x=[hora_actual_str], y=[altura_actual], mode="markers",
                name="Nivel actual",
                marker=dict(size=14, color="#00c8ff", line=dict(color="#0a1628", width=2))
            ))
            fig.add_shape(type="line", x0=hora_efecto_str, x1=hora_efecto_str,
                          y0=0, y1=y_max,
                          line=dict(color="#a89dff", width=1.5, dash="dot"))
            fig.add_annotation(x=hora_efecto_str, y=y_max*0.92,
                               text=f"Efecto ajuste<br>{hora_efecto_str}",
                               showarrow=False,
                               font=dict(color="#a89dff", size=10),
                               bgcolor="rgba(20,30,60,0.85)",
                               bordercolor="#a89dff", borderwidth=1, borderpad=4)
            if hora_rebose_str:
                fig.add_trace(go.Scatter(x=[hora_rebose_str], y=[altura_rebose],
                    mode="markers", name=f"Rebose {hora_rebose_str}",
                    marker=dict(size=13, color="#e63946", line=dict(color="white", width=2), symbol="x-open-dot")))
            if hora_minimo_str:
                fig.add_trace(go.Scatter(x=[hora_minimo_str], y=[altura_minima],
                    mode="markers", name=f"Mínimo {hora_minimo_str}",
                    marker=dict(size=13, color="#f4a261", line=dict(color="white", width=2), symbol="x-open-dot")))

            tick_vals = [horas_proj[i] for i, p in enumerate(pasos_min) if p % 30 == 0]
            fig.update_layout(
                plot_bgcolor="#0a1e3d", paper_bgcolor="#0d2347",
                font=dict(family="Barlow Condensed", color="#d0e8f5", size=12),
                xaxis=dict(title="Hora del día", gridcolor="#1a3a6a", linecolor="#1a3a6a",
                           tickangle=-30, tickvals=tick_vals, tickfont=dict(size=11)),
                yaxis=dict(title="Altura (m)", gridcolor="#1a3a6a", linecolor="#1a3a6a",
                           range=[0, y_max], tickfont=dict(size=11)),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                            bgcolor="rgba(10,30,64,0.9)", bordercolor="#1a3a6a",
                            borderwidth=1, font=dict(size=11, color="#d0e8f5")),
                margin=dict(l=20, r=120, t=20, b=60), height=420
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
# =========================================
# FLUJO DE ACCESO
# =========================================
if not st.session_state.autenticado:
    mostrar_login()
    st.stop()
 
st.markdown(ESTILOS_GLOBALES, unsafe_allow_html=True)
 
 
# =========================================
# ENCABEZADO
# =========================================
planta_badge = st.session_state.get("planta_usuario", "")
st.markdown(f"""
<div class="app-header">
    <div class="header-logo">💧 SERVAF</div>
    <div class="header-title">
        HERRAMIENTA WEB DE APOYO PARA OPERACIÓN<br>
        <span style="font-size:0.85rem;font-weight:400;color:rgba(255,255,255,0.55)">
            Planta de Tratamiento Agua Potable · Diviso & Caldas
        </span>
    </div>
    <div class="header-badge">PTAP · {planta_badge}</div>
</div>
""", unsafe_allow_html=True)
 
 
# =========================================
# MENU DINAMICO
# =========================================
st.markdown("<div class='bloque'>", unsafe_allow_html=True)
 
with st.expander("🧭 Menú principal", expanded=False):
    m1, m2, m3, m4 = st.columns([1, 1, 1, 0.75])
 
    with m1:
        st.markdown("""
        <div class="menu-card">
            <span class="menu-icon">🔬</span>
            <div class="menu-titulo">Recomendación PAC</div>
            <div class="menu-texto">Consulta casos históricos similares y genera dosis sugeridas para prueba de jarras.</div>
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
            <div class="menu-texto">Calcula consumos de PAC, descenso de nivel y altura estimada del tanque de PAC.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("Entrar a calculadora PAC", use_container_width=True, key="btn_ir_calculadora"):
            st.session_state.vista = "calculadora"
            st.rerun()
 
    with m3:
        st.markdown("""
        <div class="menu-card">
            <span class="menu-icon">🏗️</span>
            <div class="menu-titulo">Calculadora de Tanque</div>
            <div class="menu-texto">Estima caudal de entrada, balance hídrico y hora exacta de rebose o mínimo operativo.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("Entrar a calculadora de tanque", use_container_width=True, key="btn_ir_tanque"):
            st.session_state.vista = "tanque"
            st.rerun()
 
    with m4:
        st.markdown("""
        <div class="menu-card">
            <span class="menu-icon">🔒</span>
            <div class="menu-titulo">Sesión activa</div>
            <div class="menu-texto">Cierra la sesión y vuelve al acceso principal.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("Cerrar sesión", type="secondary", use_container_width=True, key="btn_cerrar_superior"):
            st.session_state.autenticado    = False
            st.session_state.vista          = "menu"
            st.session_state.planta_usuario = None
            st.rerun()
 
if st.session_state.vista == "menu":
    st.info("Selecciona una herramienta desde el menú desplegable.")
 
st.markdown("</div>", unsafe_allow_html=True)
 
 
# =========================================
# VISTAS
# =========================================
if st.session_state.vista == "calculadora":
    mostrar_calculadora_pac()
    st.stop()
 
if st.session_state.vista == "tanque":
    mostrar_calculadora_tanque()
    st.stop()
 
if st.session_state.vista != "recomendacion":
    st.stop()
 
 
# =========================================
# VISTA RECOMENDACION — panel doble
# =========================================
def _init_rec_state(config_key):
    d = valores_por_defecto(config_key)
    if "rec_config_key" not in st.session_state or st.session_state.rec_config_key != config_key:
        st.session_state.rec_config_key = config_key
        st.session_state.rec_caudal     = d["caudal"]
        st.session_state.rec_turbiedad  = d["turbiedad"]
        st.session_state.rec_ph         = d["ph"]
        st.session_state.rec_alc_cruda  = d["alcalinidad_cruda"]
        st.session_state.rec_alc_enc    = d["alcalinidad_encalada"] if d["alcalinidad_encalada"] else 16.0
        st.session_state.rec_densidad   = d["densidad_pac"]
        st.session_state.rec_vecinos    = 8
        st.session_state.rec_resultado  = None
 
 
col_form, col_result = st.columns([1, 1.85], gap="large")
 
with col_form:
    st.markdown("<div class='panel-izquierdo'>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-panel'>Configuración del análisis</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='texto-panel'>Define las condiciones actuales del agua y ejecuta la recomendación.</div>",
        unsafe_allow_html=True
    )
 
    planta_usuario = st.session_state.get("planta_usuario", "Caldas")
 
    if planta_usuario == "Diviso":
        st.markdown(
            "<div style='background:#eef6ff;border:1px solid #c5dcf5;border-radius:12px;"
            "padding:0.55rem 1rem;font-size:0.87rem;color:#0d2347;margin-bottom:0.8rem'>"
            "🏭 <b>Planta:</b> Diviso</div>",
            unsafe_allow_html=True
        )
        modulo_diviso = st.selectbox("Selecciona el módulo", ["Módulo 500", "Módulo 150"], key="rec_modulo_diviso")
        config_key = "Diviso - Modulo 500" if modulo_diviso == "Módulo 500" else "Diviso - Modulo 150"
    else:
        st.markdown(
            "<div style='background:#eef6ff;border:1px solid #c5dcf5;border-radius:12px;"
            "padding:0.55rem 1rem;font-size:0.87rem;color:#0d2347;margin-bottom:0.8rem'>"
            "🏭 <b>Planta:</b> Caldas</div>",
            unsafe_allow_html=True
        )
        config_key = "Caldas"
 
    _init_rec_state(config_key)
 
    st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)
 
    st.markdown("<div class='bloque-mini'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-mini'>Fuente de datos</div>", unsafe_allow_html=True)
 
    fuente_datos = st.radio(
        "Fuente", ["Usar archivo del sistema", "Subir archivo Excel"],
        horizontal=False, label_visibility="collapsed", key="rec_fuente_datos"
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
            "Sube el archivo Excel", type=["xlsx"], key=f"uploader_{config_key}"
        )
        if archivo_subido is not None:
            try:
                df = cargar_y_limpiar_excel(archivo_subido, config_key)
                st.success(f"Archivo subido: {CONFIGS[config_key]['nombre_app']}")
            except Exception as e:
                st.error(f"No se pudo leer el archivo: {e}")
        else:
            st.info("Sube un archivo Excel para continuar.")
 
    if df is not None:
        st.caption(f"{CONFIGS[config_key]['nombre_app']} · Filas útiles: {len(df)}")
 
    st.markdown("</div>", unsafe_allow_html=True)
 
    st.markdown("<div class='bloque-mini'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-mini'>Datos del caso actual</div>", unsafe_allow_html=True)
 
    st.number_input("Caudal a tratar (L/s)",           value=st.session_state.rec_caudal,    step=1.0,  key="rec_caudal")
    st.number_input("Turbiedad del agua cruda (UNT)",  value=st.session_state.rec_turbiedad, step=0.1,  key="rec_turbiedad")
    st.number_input("pH del agua cruda",               value=st.session_state.rec_ph,        step=0.01, format="%.2f", key="rec_ph")
    st.number_input("Alcalinidad agua cruda (mg/L)",   value=st.session_state.rec_alc_cruda, step=1.0,  key="rec_alc_cruda")
 
    if CONFIGS[config_key]["usa_alcalinidad_encalada"]:
        st.number_input("Alcalinidad agua encalada (mg/L)", value=st.session_state.rec_alc_enc, step=1.0, key="rec_alc_enc")
 
    st.number_input("Densidad del PAC (g/mL)", value=st.session_state.rec_densidad, step=0.01, format="%.2f", key="rec_densidad")
    st.slider("Registros históricos a evaluar", min_value=5, max_value=30,
              value=st.session_state.rec_vecinos, step=1, key="rec_vecinos")
 
    caudal               = st.session_state.rec_caudal
    turbiedad            = st.session_state.rec_turbiedad
    ph                   = st.session_state.rec_ph
    alcalinidad_cruda    = st.session_state.rec_alc_cruda
    alcalinidad_encalada = st.session_state.rec_alc_enc if CONFIGS[config_key]["usa_alcalinidad_encalada"] else None
    densidad_pac         = st.session_state.rec_densidad
    vecinos_deseados     = st.session_state.rec_vecinos
 
    if st.button("⚡ Calcular rango PAC", use_container_width=True, key="btn_calcular_panel"):
        if df is not None:
            st.session_state.rec_resultado = calcular_rango_pac(
                df=df, config_key=config_key, caudal=caudal, turbiedad=turbiedad,
                ph=ph, alcalinidad_cruda=alcalinidad_cruda, densidad_pac=densidad_pac,
                vecinos_deseados=vecinos_deseados, alcalinidad_encalada=alcalinidad_encalada
            )
        else:
            st.session_state.rec_resultado = None
 
    if st.button("← Volver al menú", type="secondary", use_container_width=True, key="volver_menu_lateral"):
        st.session_state.vista = "menu"
        st.rerun()
 
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
 
 
# =========================================
# PANEL DERECHO — RESULTADOS PAC
# =========================================
with col_result:
    st.markdown("<div class='panel-derecho'>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-panel'>Resultado de la recomendación</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='texto-panel'>Aquí verás el resumen, dosis sugeridas, casos históricos similares y la gráfica principal.</div>",
        unsafe_allow_html=True
    )
 
    resultado = st.session_state.get("rec_resultado", None)
 
    if df is None:
        st.info("Primero carga una fuente de datos válida en el panel izquierdo.")
    elif resultado is None:
        st.info("Completa los datos del panel izquierdo y presiona «Calcular rango PAC».")
    elif not resultado["ok"]:
        st.error(resultado["mensaje"])
    else:
        st.markdown("<div class='titulo-seccion-resultado'>Resumen general</div>", unsafe_allow_html=True)
 
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Registros usados", resultado["n"])
        r2.metric("PAC promedio",     round(resultado["pac_promedio"], 1))
        r3.metric("PAC mínimo",       round(resultado["pac_min"], 1))
        r4.metric("PAC máximo",       round(resultado["pac_max"], 1))
 
        if resultado.get("tolerancia_usada") is not None:
            tol = resultado["tolerancia_usada"]
            texto_tol = (f"Caudal ±{tol['caudal']} · Turbiedad ±{tol['turb']} · "
                         f"pH ±{tol['ph']} · Alc. cruda ±{tol['alc']}")
            if "alc_enc" in tol:
                texto_tol += f" · Alc. encalada ±{tol['alc_enc']}"
            st.info(f"Tolerancias del prefiltro: {texto_tol}")
 
        st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-seccion-resultado'>Dosis sugeridas para prueba de jarras</div>", unsafe_allow_html=True)
        st.caption(f"Densidad PAC usada: {densidad_pac:.2f} g/mL · Caudal a tratar: {caudal:.2f} L/s")
        st.dataframe(resultado["tabla_jarras"], use_container_width=True)
 
        st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-seccion-resultado'>Registros históricos similares</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#5a7899;font-size:0.88rem;margin-bottom:0.8rem'>Registros más cercanos al caso actual ordenados por similitud.</p>", unsafe_allow_html=True)
 
        fmt = {
            "Caudal a tratar (L/s)": "{:.1f}", "Turbiedad de agua cruda (UNT)": "{:.1f}",
            "pH de agua cruda": "{:.2f}", "Alcalinidad de agua cruda (mg/L)": "{:.1f}",
            "Caudal PAC (mL/min)": "{:.1f}", "Distancia": "{:.3f}"
        }
        if "Alcalinidad de agua encalada (mg/L)" in resultado["similares_filtrados"].columns:
            fmt["Alcalinidad de agua encalada (mg/L)"] = "{:.1f}"
 
        st.dataframe(resultado["similares_filtrados"].style.format(fmt), use_container_width=True)
 
        st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-seccion-resultado'>Visualización</div>", unsafe_allow_html=True)
 
        df_grafica = resultado["similares_filtrados"].sort_values("Caudal PAC (mL/min)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_grafica["Caudal PAC (mL/min)"], y=df_grafica["Turbiedad de agua cruda (UNT)"],
            mode="lines+markers", name="Históricos",
            line=dict(color="#1a6fff", width=2.2, shape="spline"),
            marker=dict(size=8, color="#1a6fff", line=dict(color="white", width=2), symbol="circle"),
            fill="tozeroy", fillcolor="rgba(26,111,255,0.05)"
        ))
        fig.add_trace(go.Scatter(
            x=[resultado["pac_promedio"]], y=[turbiedad],
            mode="markers", name="Caso actual",
            marker=dict(size=14, color="#00e5c0", line=dict(color="#0a1628", width=2), symbol="star")
        ))
        fig.update_layout(
            title=dict(text="Caudal PAC vs Turbiedad - Registros similares",
                       font=dict(family="Syne", size=14, color="#0a1628")),
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="DM Sans", color="#0a1628", size=12),
            xaxis=dict(title="Caudal PAC (mL/min)", gridcolor="#e8f0fe", linecolor="#dce9f7"),
            yaxis=dict(title="Turbiedad (UNT)",      gridcolor="#e8f0fe", linecolor="#dce9f7"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20), height=360
        )
        st.plotly_chart(fig, use_container_width=True)
 
    st.markdown("</div>", unsafe_allow_html=True)
 
