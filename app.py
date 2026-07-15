import streamlit as st
import base64
import hmac
import time
import re
import io
import unicodedata
from urllib.parse import quote
import requests
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
DOCUMENTOS_DIR = BASE_DIR / "Documentos"

LOGO_SERVAF_ARCHIVO = "servaf_color_vertical (1).png"


def obtener_logo_servaf_base64():
    """Retorna el logo SERVAF en base64 para usarlo dentro del encabezado HTML."""
    ruta_logo = BASE_DIR / LOGO_SERVAF_ARCHIVO
    if not ruta_logo.exists():
        return None

    try:
        with open(ruta_logo, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None



# =========================================
# SEGURIDAD PARA STREAMLIT CLOUD
# =========================================
def obtener_secreto(nombre, default=""):
    """Lee secretos de Streamlit Cloud sin romper la app si aún no están configurados."""
    try:
        valor = st.secrets.get(nombre, default)
        if valor is None:
            return default
        return str(valor)
    except Exception:
        return default


def entero_secreto(nombre, default):
    try:
        return int(obtener_secreto(nombre, str(default)))
    except Exception:
        return int(default)


def secreto_configurado(nombre):
    return obtener_secreto(nombre, "").strip() != ""


def comparar_secreto(valor_ingresado, valor_real):
    """Compara claves sin filtrar información por tiempo de comparación."""
    return hmac.compare_digest(str(valor_ingresado).strip(), str(valor_real).strip())


MAX_INTENTOS_PIN = entero_secreto("MAX_INTENTOS_PIN", 5)
BLOQUEO_SEGUNDOS_PIN = entero_secreto("BLOQUEO_SEGUNDOS_PIN", 600)
PIN_VER_DOCUMENTOS = obtener_secreto("PIN_VER_DOCUMENTOS", "")
PIN_ADMIN_DOCUMENTOS = obtener_secreto("PIN_ADMIN_DOCUMENTOS", "")

# Datos del repositorio para que el administrador pueda guardar/eliminar PDF de forma permanente en GitHub.
GITHUB_TOKEN = obtener_secreto("GITHUB_TOKEN", "")
GITHUB_REPO = obtener_secreto("GITHUB_REPO", "laboratoriosdeprocesos-hub/app-pac")
GITHUB_BRANCH = obtener_secreto("GITHUB_BRANCH", "main")
GITHUB_DOCS_DIR = obtener_secreto("GITHUB_DOCS_DIR", "Documentos").strip("/") or "Documentos"


def cargar_usuarios_desde_secretos():
    """Usuarios de acceso general. Las contraseñas deben estar en Streamlit Secrets."""
    usuarios = {}

    usuario_diviso = obtener_secreto("USUARIO_DIVISO", "diviso").strip().lower()
    clave_diviso = obtener_secreto("CLAVE_DIVISO", "")
    if usuario_diviso and clave_diviso:
        usuarios[usuario_diviso] = {"clave": clave_diviso, "planta": "Diviso"}

    usuario_caldas = obtener_secreto("USUARIO_CALDAS", "caldas").strip().lower()
    clave_caldas = obtener_secreto("CLAVE_CALDAS", "")
    if usuario_caldas and clave_caldas:
        usuarios[usuario_caldas] = {"clave": clave_caldas, "planta": "Caldas"}

    return usuarios


USUARIOS = cargar_usuarios_desde_secretos()


def segundos_restantes_bloqueo(nombre):
    hasta = float(st.session_state.get(f"bloqueado_hasta_{nombre}", 0) or 0)
    restante = int(max(0, hasta - time.time()))
    return restante


def registrar_intento_fallido(nombre):
    key_intentos = f"intentos_{nombre}"
    st.session_state[key_intentos] = int(st.session_state.get(key_intentos, 0)) + 1
    if st.session_state[key_intentos] >= MAX_INTENTOS_PIN:
        st.session_state[f"bloqueado_hasta_{nombre}"] = time.time() + BLOQUEO_SEGUNDOS_PIN
        st.session_state[key_intentos] = 0


def reiniciar_intentos(nombre):
    st.session_state[f"intentos_{nombre}"] = 0
    st.session_state[f"bloqueado_hasta_{nombre}"] = 0
 
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
 
if "vista" not in st.session_state:
    st.session_state.vista = "menu"
 
if "planta_usuario" not in st.session_state:
    st.session_state.planta_usuario = None

if "documentos_autorizado" not in st.session_state:
    st.session_state.documentos_autorizado = False

if "documentos_admin_autorizado" not in st.session_state:
    st.session_state.documentos_admin_autorizado = False
 
 
# =========================================
# ESTILOS GLOBALES
# =========================================
ESTILOS_GLOBALES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
 
:root {
    --azul-deep:   #003A70;
    --azul-mid:    #004A8F;
    --azul-accent: #008ACB;
    --azul-claro:  #48B9EA;
    --verde:       #6FAE4A;
    --verde-soft:  #EAF7E8;
    --teal:        #2DB9B0;
    --cyan:        #48B9EA;
    --agua:        #2DB9B0;
    --blanco:      #ffffff;
    --gris-1:      #EEF7FC;
    --gris-2:      #CFE5F4;
    --texto-dark:  #003A70;
    --texto-muted: #4E6F8A;
}
 
* { box-sizing: border-box; }
 
html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: #EEF7FC !important;
}
 
header { visibility: hidden !important; }
footer { visibility: hidden !important; }
 
.block-container {
    padding: 0.6rem 1.2rem 2rem 1.2rem !important;
    max-width: 100% !important;
}
 
.main > div { padding-top: 0 !important; }
 
.app-header {
    background: linear-gradient(135deg, #003A70 0%, #004A8F 55%, #006AA8 100%);
    border-radius: 20px;
    padding: 1.05rem 1.35rem;
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
    letter-spacing: 3px; text-transform: none; position: relative; z-index: 2;
}

.header-logo-card {
    position: relative;
    z-index: 2;
    min-width: 150px;
    max-width: 170px;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: none !important;
}

.header-logo-card img {
    width: 100%;
    max-height: 82px;
    object-fit: contain;
    display: block;
    filter: drop-shadow(0 2px 4px rgba(0, 30, 70, 0.18));
}

.header-left-brand {
    position: relative;
    z-index: 2;
    min-width: 170px;
    color: #D9F3FF;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 1.8px;
    text-transform: uppercase;
}

.header-left-brand span {
    display: block;
    color: #79D0F2;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.7px;
    margin-top: 0.2rem;
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
    background: #F7FCFF; border: 1px solid #D8EAF4;
    border-radius: 16px; padding: 0.95rem; margin-bottom: 0.85rem;
}
 
.titulo-mini { font-size: 0.95rem; font-weight: 800; color: #005B8E; margin-bottom: 0.4rem; }
 
.etiqueta {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: linear-gradient(135deg, #E6F5FB, #D5ECF8); color: #004A8F;
    padding: 0.28rem 0.9rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700;
    margin-bottom: 0.9rem; letter-spacing: 0.5px; text-transform: none;
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
    background: linear-gradient(90deg, #008ACB, #48B9EA); border-radius: 20px 20px 0 0;
}
 
.menu-card:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(10,22,40,0.12); }
 
.menu-icon { font-size: 2rem; margin-bottom: 0.7rem; display: block; }
.menu-titulo { font-weight: 700; font-size: 1.08rem; color: #003A70; margin-bottom: 0.45rem; }
.menu-texto { font-size: 0.9rem; color: var(--texto-muted); line-height: 1.55; margin-bottom: 1rem; }
 
.panel-izquierdo {
    background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
    border: 1px solid #CFE5F4; border-radius: 22px; padding: 1.1rem 1.1rem 0.9rem 1.1rem;
    box-shadow: 0 10px 28px rgba(7,62,94,0.08); position: sticky; top: 0.8rem;
}
 
.panel-derecho {
    background: rgba(255,255,255,0.98); border: 1px solid #CFE5F4; border-radius: 22px;
    padding: 1.1rem; box-shadow: 0 10px 28px rgba(7,62,94,0.08);
}
 
.subtitulo-panel { color: #005B8E; font-size: 1.12rem; font-weight: 800; margin-bottom: 0.35rem; }
.texto-panel { color: #54748A; font-size: 0.93rem; line-height: 1.5; margin-bottom: 0.9rem; }
 
.titulo-seccion-resultado {
    font-size: 1.08rem; font-weight: 800; color: #005B8E;
    margin-bottom: 0.45rem; margin-top: 0.25rem;
}
 
.hr-suave { border: none; border-top: 1px solid #D8EAF4; margin: 0.8rem 0 1rem 0; }
 
.caja-rango {
    background: linear-gradient(135deg, #EAF6FC, #f5faff); border-left: 5px solid #008ACB;
    padding: 1.1rem 1.3rem; border-radius: 14px; font-size: 0.93rem; margin: 0.8rem 0;
    color: #003A70; line-height: 1.65; box-shadow: inset 0 0 0 1px rgba(26,111,255,0.08);
}
 
div[data-testid="stMetric"] {
    background: linear-gradient(160deg, #F7FCFF 0%, #eef5ff 100%) !important;
    border: 1px solid rgba(26,111,255,0.12) !important; padding: 1rem 1.2rem !important;
    border-radius: 16px !important; box-shadow: 0 4px 16px rgba(10,22,40,0.06) !important;
}
 
div[data-testid="stMetricLabel"] > div {
    font-size: 0.78rem !important; font-weight: 600 !important;
    color: var(--texto-muted) !important; text-transform: none; letter-spacing: 0.5px;
}
 
div[data-testid="stMetricValue"] > div {
    color: #004A8F !important; font-weight: 800 !important;
    font-size: 1.65rem !important; letter-spacing: 0 !important;
}
 
.stButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 700 !important;
    font-size: 0.9rem !important;
    background: linear-gradient(135deg, #008ACB 0%, #005B96 100%) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    min-height: 48px !important; width: 100% !important;
    box-shadow: 0 6px 20px rgba(26,111,255,0.28) !important;
}
 
.stButton > button:hover { transform: translateY(-1px); }
 
.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, #EEF7FC 0%, #DDEFFA 100%) !important;
    color: #004A8F !important; border: 1px solid rgba(26,111,255,0.2) !important;
    box-shadow: 0 4px 12px rgba(10,22,40,0.07) !important;
}
 
div[data-testid="stTextInput"] > label,
div[data-testid="stNumberInput"] > label,
div[data-testid="stSelectbox"] > label,
div[data-testid="stSlider"] > label,
div[data-testid="stRadio"] > label {
    font-size: 1rem !important; font-weight: 700 !important;
    color: #315C7E !important; text-transform: none; letter-spacing: 0.4px;
}
 
div[data-baseweb="input"] input,
div[data-baseweb="select"] > div {
    border-radius: 12px !important; border: 1.5px solid #CFE5F4 !important;
    background: #F7FCFF !important; font-size: 0.96rem !important; color: #003A70 !important;
}
 
[data-testid="stDataFrame"] {
    border-radius: 16px !important; overflow: hidden !important;
    border: 1px solid #CFE5F4 !important; box-shadow: 0 4px 16px rgba(10,22,40,0.06) !important;
}
 
thead tr th {
    background: #004A8F !important; color: white !important;
    font-weight: 700 !important; font-size: 0.8rem !important; text-align: center !important;
}
 
tbody tr:nth-child(even) { background: #F7FCFF !important; }
tbody tr td { text-align: center !important; color: #003A70 !important; }
 
div[data-testid="stExpander"] {
    border: 1.5px solid #CFE5F4 !important; border-radius: 16px !important;
    background: white !important; overflow: hidden;
}
 
.streamlit-expanderHeader {
    font-weight: 700 !important; color: #004A8F !important; font-size: 0.95rem !important;
}
 
div[data-testid="stInfo"],
div[data-testid="stSuccess"],
div[data-testid="stError"] { border-radius: 14px !important; }
 
h1, h2, h3 { font-family: 'Inter', sans-serif !important; color: #003A70 !important; }
h1 { font-size: 1.5rem !important; font-weight: 800 !important; }
h2 { font-size: 1.15rem !important; font-weight: 700 !important; }
h3 { font-size: 1rem !important; font-weight: 700 !important; }
 

/* ===============================
   TABLAS PROFESIONALES
   =============================== */
[data-testid="stDataFrame"] {
    border-radius: 18px !important;
    overflow: hidden !important;
    border: 1px solid #CFE5F4 !important;
    box-shadow: 0 8px 26px rgba(10,22,40,0.08) !important;
    background: #ffffff !important;
}
[data-testid="stDataFrame"] div[role="grid"] {
    border-radius: 18px !important;
}
[data-testid="stDataFrame"] [role="columnheader"] {
    background: #004A8F !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.35px !important;
    text-transform: none !important;
    border-right: 1px solid rgba(255,255,255,0.14) !important;
}
[data-testid="stDataFrame"] [role="gridcell"] {
    font-size: 0.88rem !important;
    color: #003A70 !important;
    border-color: #e8f0f8 !important;
}
[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] {
    background: #F7FCFF !important;
}
[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
    background: #EAF6FC !important;
}
.tabla-nota {
    color:#4E6F8A;
    font-size:0.84rem;
    margin-top:0.35rem;
    margin-bottom:0.55rem;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #EEF7FC; border-radius: 10px; }
::-webkit-scrollbar-thumb { background: #A7D2E4; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #008ACB; }
 
@media (max-width: 1100px) { .panel-izquierdo { position: relative; top: 0; } }
 
@media (max-width: 768px) {
    .block-container { padding: 0.4rem 0.6rem 1.5rem !important; }
    .bloque { padding: 1rem 1.1rem; border-radius: 16px; }
    .app-header { padding: 1rem 1.2rem; flex-direction: column; gap: 0.6rem; text-align: center; }
    .header-title { font-size: 1.1rem; }
    .header-left-brand { min-width: 0; }
    .header-logo-card { min-width: 150px; max-width: 175px; }
    div[data-testid="stMetricValue"] > div { font-size: 1.35rem !important; }
}
 
.tanque-card { overflow: visible !important; width: 100% !important; }
.tanque-layout { overflow: visible !important; width: 100% !important; }
.tanque-svg-wrap { overflow: visible !important; }
[data-testid="stMarkdownContainer"] { overflow: visible !important; }


/* ===============================
   PALETA SERVAF GESTIÓN 2025
   Aplicada a toda la app, excepto el diseño propio del login.
   =============================== */
html, body, .stApp {
    background:
        radial-gradient(circle at 88% 6%, rgba(72,185,234,0.22) 0%, rgba(72,185,234,0.06) 34%, transparent 58%),
        linear-gradient(135deg, #F7FCFF 0%, #EEF7FC 52%, #E5F3FA 100%) !important;
}
.app-header {
    background:
        radial-gradient(circle at 88% -20%, rgba(255,255,255,0.24) 0%, transparent 42%),
        linear-gradient(135deg, #003A70 0%, #004A8F 52%, #008ACB 100%) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    box-shadow: 0 14px 36px rgba(0, 58, 112, 0.22) !important;
}
.header-logo, .header-badge { color: #DDF5FF !important; }
.header-badge {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.30) !important;
}
.bloque, .panel-derecho, .panel-izquierdo, .menu-card {
    border-color: #CFE5F4 !important;
    box-shadow: 0 10px 28px rgba(0, 58, 112, 0.075) !important;
}
.menu-card::before {
    background: linear-gradient(90deg, #003A70, #008ACB 58%, #6FAE4A) !important;
}
.etiqueta {
    background: linear-gradient(135deg, #E6F5FB 0%, #F1FAEF 100%) !important;
    color: #003A70 !important;
    border-color: rgba(0, 138, 203, 0.20) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #005B96 0%, #008ACB 100%) !important;
    box-shadow: 0 8px 20px rgba(0, 91, 150, 0.22) !important;
}
.stButton > button:hover {
    filter: brightness(1.02) !important;
    box-shadow: 0 10px 24px rgba(0, 91, 150, 0.26) !important;
}
.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, #F7FCFF 0%, #E6F5FB 100%) !important;
    color: #003A70 !important;
    border: 1px solid rgba(0, 138, 203, 0.25) !important;
    box-shadow: 0 5px 14px rgba(0, 58, 112, 0.075) !important;
}
div[data-testid="stMetric"] {
    background: linear-gradient(160deg, #FFFFFF 0%, #F1FAEF 100%) !important;
    border-color: rgba(111, 174, 74, 0.20) !important;
}
div[data-testid="stMetricValue"] > div { color: #003A70 !important; }
[data-testid="stDataFrame"] [role="columnheader"], thead tr th {
    background: linear-gradient(135deg, #003A70 0%, #004A8F 100%) !important;
}
[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
    background: #E6F5FB !important;
}
::-webkit-scrollbar-track { background: #EEF7FC !important; }
::-webkit-scrollbar-thumb { background: #A7D2E4 !important; }
::-webkit-scrollbar-thumb:hover { background: #008ACB !important; }

/* Logo SERVAF sin fondo blanco en encabezado */
.app-header .header-logo-card {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
.app-header .header-logo-card img {
    max-height: 82px !important;
    max-width: 170px !important;
    object-fit: contain !important;
    filter: drop-shadow(0 2px 4px rgba(0, 30, 70, 0.18));
}


/* ===============================
   CORRECCIÓN VISUAL DE INPUTS STREAMLIT
   Quita el aviso "Press Enter to apply", elimina bordes rojos feos
   y deja campos más limpios/profesionales.
   =============================== */
[data-testid="InputInstructions"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    opacity: 0 !important;
}

.stTextInput,
.stNumberInput,
.stTextArea,
.stDateInput,
.stTimeInput,
.stSelectbox {
    margin-bottom: 0.65rem !important;
}

.stTextInput div[data-baseweb="input"],
.stNumberInput div[data-baseweb="input"],
.stDateInput div[data-baseweb="input"],
.stTimeInput div[data-baseweb="input"] {
    background: #FFFFFF !important;
    border: 1.5px solid #CFE5F4 !important;
    border-radius: 14px !important;
    box-shadow: 0 3px 10px rgba(0, 58, 112, 0.045) !important;
    min-height: 46px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease !important;
    overflow: hidden !important;
}

.stTextInput div[data-baseweb="input"]:focus-within,
.stNumberInput div[data-baseweb="input"]:focus-within,
.stDateInput div[data-baseweb="input"]:focus-within,
.stTimeInput div[data-baseweb="input"]:focus-within {
    background: #FFFFFF !important;
    border-color: #008ACB !important;
    box-shadow: 0 0 0 3px rgba(0, 138, 203, 0.13), 0 5px 14px rgba(0, 58, 112, 0.075) !important;
    outline: none !important;
}

.stTextInput div[data-baseweb="input"] input,
.stNumberInput div[data-baseweb="input"] input,
.stDateInput div[data-baseweb="input"] input,
.stTimeInput div[data-baseweb="input"] input {
    background: transparent !important;
    color: #003A70 !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    min-height: 44px !important;
    font-size: 0.96rem !important;
    font-weight: 500 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

.stTextInput div[data-baseweb="input"] input:focus,
.stNumberInput div[data-baseweb="input"] input:focus,
.stDateInput div[data-baseweb="input"] input:focus,
.stTimeInput div[data-baseweb="input"] input:focus {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

.stTextInput input::placeholder,
.stNumberInput input::placeholder,
.stDateInput input::placeholder,
.stTimeInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #8FA8BC !important;
    opacity: 1 !important;
}

.stTextArea textarea {
    background: #FFFFFF !important;
    color: #003A70 !important;
    border: 1.5px solid #CFE5F4 !important;
    border-radius: 14px !important;
    box-shadow: 0 3px 10px rgba(0, 58, 112, 0.045) !important;
    font-size: 0.96rem !important;
    font-weight: 500 !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

.stTextArea textarea:focus {
    border-color: #008ACB !important;
    box-shadow: 0 0 0 3px rgba(0, 138, 203, 0.13), 0 5px 14px rgba(0, 58, 112, 0.075) !important;
    outline: none !important;
}

.stTextInput svg,
.stNumberInput svg,
.stDateInput svg,
.stTimeInput svg,
.stSelectbox svg {
    color: #315C7E !important;
    opacity: 0.78 !important;
}

.stTextInput button,
.stNumberInput button,
.stDateInput button,
.stTimeInput button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #315C7E !important;
}

/* Evita que el borde rojo del navegador o de BaseWeb quede marcado visualmente */
input:invalid,
input:required,
input:focus:invalid,
input:focus-visible,
textarea:focus-visible {
    box-shadow: none !important;
    outline: none !important;
}

div[data-baseweb="input"][aria-invalid="true"],
div[data-baseweb="input"]:has(input[aria-invalid="true"]) {
    border-color: #CFE5F4 !important;
    box-shadow: 0 3px 10px rgba(0, 58, 112, 0.045) !important;
}

div[data-baseweb="input"][aria-invalid="true"]:focus-within,
div[data-baseweb="input"]:has(input[aria-invalid="true"]):focus-within {
    border-color: #008ACB !important;
    box-shadow: 0 0 0 3px rgba(0, 138, 203, 0.13), 0 5px 14px rgba(0, 58, 112, 0.075) !important;
}

/* Selectbox limpio */
.stSelectbox div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1.5px solid #CFE5F4 !important;
    border-radius: 14px !important;
    box-shadow: 0 3px 10px rgba(0, 58, 112, 0.045) !important;
    min-height: 46px !important;
    color: #003A70 !important;
}

.stSelectbox div[data-baseweb="select"] > div:focus-within,
.stSelectbox div[data-baseweb="select"] > div:hover {
    border-color: #008ACB !important;
    box-shadow: 0 0 0 3px rgba(0, 138, 203, 0.13), 0 5px 14px rgba(0, 58, 112, 0.075) !important;
}

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
    letter-spacing: 4px; text-transform: none; position: relative; z-index: 2;
}
.login-center { position: relative; z-index: 2; }
.login-headline { font-size: 3rem; font-weight: 800; color: white; line-height: 1.05; margin-bottom: 1rem; }
.login-headline span { color: #00c8ff; }
.login-desc { color: rgba(255,255,255,0.65); font-size: 0.97rem; line-height: 1.65; max-width: 340px; }
.login-footer-left {
    position: relative; z-index: 2; color: rgba(255,255,255,0.45);
    font-size: 0.78rem; letter-spacing: 0.5px; font-weight: 500; text-transform: none;
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
                restante = segundos_restantes_bloqueo("login")
                if restante > 0:
                    st.error(f"Acceso bloqueado temporalmente. Intenta nuevamente en {restante} segundos.")
                elif not USUARIOS:
                    st.error("Faltan configurar los usuarios y claves en Streamlit Cloud Secrets.")
                    st.info("Configura USUARIO_DIVISO, CLAVE_DIVISO, USUARIO_CALDAS y CLAVE_CALDAS en los Secrets de la app.")
                else:
                    u = usuario.strip().lower()
                    clave_real = USUARIOS.get(u, {}).get("clave", "")
                    if u in USUARIOS and comparar_secreto(clave, clave_real):
                        reiniciar_intentos("login")
                        st.session_state.autenticado    = True
                        st.session_state.vista          = "menu"
                        st.session_state.planta_usuario = USUARIOS[u]["planta"]
                        st.rerun()
                    else:
                        registrar_intento_fallido("login")
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
# CONFIGURACIÓN DE TANQUES SEGÚN INSTRUCTIVO SGI-PYT-INS-070
# =========================================
TANQUES_OPERATIVOS = {
    "Diviso": {
        "Tanque principal (4400 m³)": {
            "capacidad_m3": 4400.0,
            "altura_lleno_default": 2.85,
            "altura_rebose_default": 2.82,
            "altura_minima_default": 1.40,
            "caudal_max_planta_default": 520.0,
            "tiene_macromedidor_entrada": True,
            "nota_entrada": "El agua producida por los módulos 150 y 500 se une en una sola conducción hacia los tanques. Revisar producción total y macromedición de Diviso.",
            "registro_macro": "SGI-PYT-FOR-123 Registro macromedidores Diviso",
            "registro_diario": "SGI-PYT-FOR-125 Registro diario de operaciones Diviso",
            "salidas": [
                "Cunduy-Malvinas",
                "Comuna Oriental",
                "La Paz",
                "Álamos",
                "Altos de Colinas",
                "Sebastopol",
                "Línea de Occidente",
            ],
        },
        "Tanque complementario (1100 m³)": {
            "capacidad_m3": 1100.0,
            "altura_lleno_default": 2.85,
            "altura_rebose_default": 2.82,
            "altura_minima_default": 1.40,
            "caudal_max_planta_default": 520.0,
            "tiene_macromedidor_entrada": True,
            "nota_entrada": "El agua producida por los módulos 150 y 500 se une en una sola conducción hacia los tanques. Revisar producción total y macromedición de Diviso.",
            "registro_macro": "SGI-PYT-FOR-123 Registro macromedidores Diviso",
            "registro_diario": "SGI-PYT-FOR-125 Registro diario de operaciones Diviso",
            "salidas": [
                "Cunduy-Malvinas",
                "Comuna Oriental",
                "La Paz",
                "Álamos",
                "Altos de Colinas",
                "Sebastopol",
                "Línea de Occidente",
            ],
        },
        "Sistema Diviso total (5500 m³)": {
            "capacidad_m3": 5500.0,
            "altura_lleno_default": 2.85,
            "altura_rebose_default": 2.82,
            "altura_minima_default": 1.40,
            "caudal_max_planta_default": 520.0,
            "tiene_macromedidor_entrada": True,
            "nota_entrada": "Uso para balance conjunto cuando se interpreten los dos tanques como sistema total: 4400 m³ + 1100 m³.",
            "registro_macro": "SGI-PYT-FOR-123 Registro macromedidores Diviso",
            "registro_diario": "SGI-PYT-FOR-125 Registro diario de operaciones Diviso",
            "salidas": [
                "Cunduy-Malvinas",
                "Comuna Oriental",
                "La Paz",
                "Álamos",
                "Altos de Colinas",
                "Sebastopol",
                "Línea de Occidente",
            ],
        },
    },
    "Caldas": {
        "Tanque PTAP Caldas (1365 m³)": {
            "capacidad_m3": 1365.0,
            "altura_lleno_default": 2.85,
            "altura_rebose_default": 2.82,
            "altura_minima_default": 1.40,
            "caudal_max_planta_default": 220.0,
            "tiene_macromedidor_entrada": False,
            "nota_entrada": "La entrada al tanque de Caldas no cuenta con macromedidor. El seguimiento se interpreta con nivel del tanque, salidas macromedidas y comportamiento de producción.",
            "registro_macro": "SGI-PYT-FOR-133 Registro macromedidores Caldas",
            "registro_diario": "SGI-PYT-FOR-136 Registro diario de operaciones Caldas",
            "salidas": [
                "Centro",
                "Ciudadela I",
                "Ciudadela II",
                "Heliconias",
                "Acolsure",
            ],
        }
    },
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


# =========================================
# TABLAS PROFESIONALES
# =========================================
def _estilo_accion_tabla(valor):
    texto = str(valor).lower()
    if any(pal in texto for pal in ["abrir", "aumentar", "alto", "puede"]):
        return "background-color:#e8f6f2;color:#0b6b58;font-weight:800;border-radius:8px;"
    if any(pal in texto for pal in ["cerrar", "reducir", "bajo", "crítico", "critico"]):
        return "background-color:#fff1f0;color:#a61d24;font-weight:800;border-radius:8px;"
    if any(pal in texto for pal in ["mantener", "normal", "estable"]):
        return "background-color:#eef4ff;color:#174ea6;font-weight:800;border-radius:8px;"
    return ""


def _estilo_numero_balance(valor):
    try:
        v = float(valor)
    except Exception:
        return ""
    if v > 0:
        return "color:#0b6b58;font-weight:800;"
    if v < 0:
        return "color:#a61d24;font-weight:800;"
    return "color:#42526e;font-weight:700;"


def estilo_tabla_profesional(df, formatos=None, na_rep="Sin dato"):
    """Aplica un estilo corporativo limpio a tablas operativas sin dibujos ni adornos excesivos."""
    if df.__class__.__name__ == "Styler":
        styler = df
        data = df.data
    else:
        data = df.copy()
        if formatos:
            styler = data.style.format(formatos, na_rep=na_rep)
        else:
            styler = data.style.format(na_rep=na_rep)

    styler = styler.set_table_styles([
        {"selector": "thead th", "props": [
            ("background-color", "#004A8F"),
            ("color", "#ffffff"),
            ("font-weight", "800"),
            ("text-transform", "uppercase"),
            ("letter-spacing", "0.35px"),
            ("font-size", "12px"),
            ("border", "1px solid #1f3a63"),
            ("text-align", "center"),
            ("padding", "9px 10px"),
        ]},
        {"selector": "tbody td", "props": [
            ("border", "1px solid #e6eef7"),
            ("padding", "8px 10px"),
            ("font-size", "13px"),
            ("color", "#003A70"),
        ]},
        {"selector": "tbody tr:nth-child(even)", "props": [("background-color", "#F7FCFF")]},
        {"selector": "tbody tr:hover", "props": [("background-color", "#EAF6FC")]},
        {"selector": "caption", "props": [("caption-side", "top"), ("font-weight", "800"), ("color", "#005B8E")]},
    ])
    styler = styler.set_properties(**{
        "text-align": "center",
        "vertical-align": "middle",
        "font-family": "Inter, Arial, sans-serif",
    })

    for col in getattr(data, "columns", []):
        col_txt = str(col).lower()
        try:
            if any(k in col_txt for k in ["acción", "accion", "estado", "decisión", "decision"]):
                styler = styler.map(_estilo_accion_tabla, subset=[col])
            if any(k in col_txt for k in ["balance", "ajuste", "cambio"]):
                styler = styler.map(_estilo_numero_balance, subset=[col])
        except Exception:
            try:
                if any(k in col_txt for k in ["acción", "accion", "estado", "decisión", "decision"]):
                    styler = styler.applymap(_estilo_accion_tabla, subset=[col])
                if any(k in col_txt for k in ["balance", "ajuste", "cambio"]):
                    styler = styler.applymap(_estilo_numero_balance, subset=[col])
            except Exception:
                pass
    return styler


def mostrar_tabla_profesional(df, formatos=None, na_rep="Sin dato", height=None):
    styler = estilo_tabla_profesional(df, formatos=formatos, na_rep=na_rep)
    kwargs = {"use_container_width": True, "hide_index": True}
    if height is not None:
        kwargs["height"] = height
    try:
        st.dataframe(styler, **kwargs)
    except TypeError:
        kwargs.pop("hide_index", None)
        st.dataframe(styler, **kwargs)


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
        "Caudal de PAC recomendado (mL/min)": jarras_recomendadas,
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
        "pac_ml_min": "Caudal de PAC (mL/min)", "distancia": "Distancia"
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

    TK_X, TK_Y, TK_W, TK_H = 86, 56, 108, 248
    TK_BOTTOM = TK_Y + TK_H
    VB_W, VB_H = 300, 452

    y_agua   = TK_BOTTOM - (pct_actual / 100) * TK_H
    y_rebose = TK_BOTTOM - (pct_rebose / 100) * TK_H
    y_minima = TK_BOTTOM - (pct_minima / 100) * TK_H

    if pct_actual >= 92:
        accent = "#C2410C"
        accent_soft = "#FFF7ED"
        agua_top = "#FB7185"
        agua_bottom = "#E11D48"
        estado_txt = "NIVEL MUY ALTO"
    elif pct_actual >= 82:
        accent = "#DC2626"
        accent_soft = "#FEF2F2"
        agua_top = "#FB7185"
        agua_bottom = "#F43F5E"
        estado_txt = "NIVEL CRÍTICO ALTO"
    elif pct_actual <= 20:
        accent = "#B45309"
        accent_soft = "#FFFBEB"
        agua_top = "#FBBF24"
        agua_bottom = "#F59E0B"
        estado_txt = "NIVEL BAJO"
    else:
        accent = "#0A8F83"
        accent_soft = "#F0FDFA"
        agua_top = "#38BDF8"
        agua_bottom = "#2563EB"
        estado_txt = "NIVEL OPERATIVO"

    tendencia_label = "SUBIENDO" if tendencia == "subiendo" else ("BAJANDO" if tendencia == "bajando" else "ESTABLE")
    flecha = "▲" if tendencia == "subiendo" else ("▼" if tendencia == "bajando" else "●")
    signo = "+" if Q_neto_Ls >= 0 else ""
    txt_rebose = hora_rebose_str if hora_rebose_str else "No aplica"
    txt_minimo = hora_minimo_str if hora_minimo_str else "No aplica"

    escala_lines = ""
    for i in range(5):
        yy = TK_Y + i * TK_H / 4
        val = h_lleno * (1 - i / 4)
        escala_lines += (
            f'<line x1="{TK_X-16}" y1="{yy:.1f}" x2="{TK_X-6}" y2="{yy:.1f}" stroke="#94A3B8" stroke-width="1.1"/>'
            f'<text x="{TK_X-20}" y="{yy+4:.1f}" text-anchor="end" font-size="8.8" font-family="Inter,sans-serif" fill="#64748B">{val:.1f}</text>'
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
  background: #ffffff;
  border: 1px solid #D7E3F1;
  border-radius: 18px;
  padding: 14px 14px 12px 14px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}}
.tk-header {{ text-align:center; margin-bottom: 8px; }}
.tk-kicker {{ font-size: 11px; font-weight: 800; color: #334155; letter-spacing: 1.1px; text-transform: none; }}
.tk-status {{
  margin: 8px auto 0 auto; display:inline-flex; align-items:center; gap:6px;
  background: {accent_soft}; color: {accent}; border: 1.3px solid {accent};
  border-radius: 999px; padding: 4px 12px; font-size: 12px; font-weight: 800;
}}
.tk-svg-wrap {{ width:100%; display:flex; justify-content:center; margin: 6px 0 10px 0; }}
.tk-svg-wrap svg {{ width:100%; max-width:250px; height:auto; }}
.tk-footer {{
  background:#F8FAFC; border:1px solid #E2E8F0; border-radius:14px; padding:12px;
}}
.tk-footer-row {{ display:flex; align-items:baseline; justify-content:center; gap:6px; flex-wrap:wrap; margin-bottom:6px; }}
.tk-time {{ font-size: 14px; font-weight: 800; color:#0F172A; }}
.tk-level {{ font-size: 16px; font-weight: 800; color:{accent}; }}
.tk-metrics {{ display:grid; grid-template-columns: 1fr; gap:4px; text-align:center; }}
.tk-metric {{ font-size: 12.5px; color:#334155; }}
.tk-metric b {{ color:#0F172A; }}
.tk-metric .accent {{ color:{accent}; font-weight:800; }}
</style>
</head>
<body>
<div class="tk-wrap">
  <div class="tk-header">
    <div class="tk-kicker">Estado del tanque</div>
    <div class="tk-status">{estado_txt}</div>
  </div>
  <div class="tk-svg-wrap">
    <svg viewBox="0 0 {VB_W} {VB_H}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="gAgua" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{agua_top}" stop-opacity="0.92"/>
          <stop offset="100%" stop-color="{agua_bottom}" stop-opacity="0.98"/>
        </linearGradient>
        <linearGradient id="gTanque" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#E2E8F0"/>
          <stop offset="50%" stop-color="#F8FAFC"/>
          <stop offset="100%" stop-color="#CBD5E1"/>
        </linearGradient>
        <clipPath id="clipTank">
          <rect x="{TK_X+3}" y="{TK_Y+2}" width="{TK_W-6}" height="{TK_H-4}" rx="12"/>
        </clipPath>
      </defs>

      <text x="{VB_W/2:.0f}" y="24" text-anchor="middle" font-size="18" font-family="Inter,sans-serif" font-weight="800" fill="#0F172A">{h_actual:.3f} m</text>
      <text x="{VB_W/2:.0f}" y="41" text-anchor="middle" font-size="11" font-family="Inter,sans-serif" font-weight="600" fill="#64748B">Nivel actual • {pct_actual:.1f}% del volumen</text>

      <line x1="{TK_X-20}" y1="{TK_Y}" x2="{TK_X-20}" y2="{TK_BOTTOM}" stroke="#CBD5E1" stroke-width="1.2"/>
      {escala_lines}

      <rect x="{TK_X-8}" y="{TK_Y-12}" width="{TK_W+16}" height="14" rx="7" fill="#8FB7CF" stroke="#789EB5" stroke-width="1"/>
      <rect x="{TK_X}" y="{TK_Y}" width="{TK_W}" height="{TK_H}" rx="16" fill="url(#gTanque)" stroke="#94A3B8" stroke-width="2"/>
      <g clip-path="url(#clipTank)">
        <rect x="{TK_X+3}" y="{y_agua:.1f}" width="{TK_W-6}" height="{TK_BOTTOM-y_agua:.1f}" fill="url(#gAgua)"/>
        <rect x="{TK_X+3}" y="{y_agua:.1f}" width="{TK_W-6}" height="{TK_BOTTOM-y_agua:.1f}" fill="rgba(255,255,255,0.08)"/>
      </g>
      <rect x="{TK_X+4}" y="{TK_Y+4}" width="14" height="{TK_H-8}" rx="7" fill="rgba(255,255,255,0.18)"/>
      <rect x="{TK_X-10}" y="{TK_BOTTOM+4}" width="{TK_W+20}" height="12" rx="6" fill="#8FB7CF" stroke="#789EB5" stroke-width="1"/>
      <rect x="{TK_X+16}" y="{TK_BOTTOM+16}" width="10" height="28" rx="3" fill="#7B9CB2"/>
      <rect x="{TK_X+TK_W-26}" y="{TK_BOTTOM+16}" width="10" height="28" rx="3" fill="#7B9CB2"/>

      <line x1="{TK_X-8}" y1="{y_rebose:.1f}" x2="{TK_X+TK_W+44}" y2="{y_rebose:.1f}" stroke="#DC2626" stroke-width="1.5" stroke-dasharray="5,4"/>
      <text x="{TK_X+TK_W+48}" y="{y_rebose+4:.1f}" font-size="9" font-family="Inter,sans-serif" font-weight="700" fill="#DC2626">REB {h_rebose:.2f} m</text>

      <line x1="{TK_X-8}" y1="{y_minima:.1f}" x2="{TK_X+TK_W+44}" y2="{y_minima:.1f}" stroke="#D97706" stroke-width="1.5" stroke-dasharray="5,4"/>
      <text x="{TK_X+TK_W+48}" y="{y_minima+4:.1f}" font-size="9" font-family="Inter,sans-serif" font-weight="700" fill="#D97706">MIN {h_minima:.2f} m</text>

      <rect x="{TK_X+16}" y="{max(TK_Y+10, y_agua-26):.1f}" width="{TK_W-32}" height="20" rx="10" fill="#FFFFFF" stroke="#D7E3F1"/>
      <text x="{VB_W/2:.0f}" y="{max(TK_Y+24, y_agua-12):.1f}" text-anchor="middle" font-size="10" font-family="Inter,sans-serif" font-weight="800" fill="#0F172A">{flecha} {tendencia_label}</text>
    </svg>
  </div>
  <div class="tk-footer">
    <div class="tk-footer-row">
      <span class="tk-time">{hora_actual_str}</span>
      <span style="color:#94A3B8; font-weight:700;">—</span>
      <span class="tk-level">{h_actual:.3f} m</span>
    </div>
    <div class="tk-metrics">
      <div class="tk-metric">Q neto: <span class="accent">{signo}{Q_neto_Ls:.2f} L/s</span></div>
      <div class="tk-metric">Hora rebose: <b>{txt_rebose}</b> · Hora mínimo: <b>{txt_minimo}</b></div>
    </div>
  </div>
</div>
</body>
</html>"""
    return html


# =========================================
# BLOQUE VISUAL DE FÓRMULAS — ESTILO PROFESIONAL
# =========================================
def mostrar_formulas_pac_profesionales():
    """Muestra las fórmulas de la calculadora PAC en formato matemático limpio.
    Se usa MathJax dentro de components.html para evitar que las fórmulas se vean
    como texto plano y mantener una presentación tipo documento técnico.
    """
    html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script>
window.MathJax = {
  tex: { inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']] },
  svg: { fontCache: 'global' }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #003A70;
}
.formula-wrap {
    background: linear-gradient(135deg, #F7FCFF 0%, #eef7ff 100%);
    border: 1px solid #d6e8f7;
    border-left: 6px solid #48B9EA;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 6px 22px rgba(10, 22, 40, 0.06);
}
.formula-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
    color: #005B8E;
    font-size: 16px;
    font-weight: 850;
    letter-spacing: .2px;
}
.formula-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(260px, 1fr));
    gap: 14px;
}
.formula-card {
    background: #ffffff;
    border: 1px solid #CFE5F4;
    border-radius: 16px;
    padding: 14px 14px 12px 14px;
    min-height: 132px;
    box-shadow: 0 4px 16px rgba(10, 22, 40, 0.055);
}
.formula-name {
    font-size: 12px;
    text-transform: none;
    letter-spacing: .55px;
    font-weight: 800;
    color: #4E6F8A;
    margin-bottom: 6px;
}
.formula-eq {
    min-height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #004A8F;
    overflow-x: auto;
}
.formula-note {
    margin-top: 7px;
    color: #4E6F8A;
    line-height: 1.45;
    font-size: 12px;
}
.formula-footer {
    margin-top: 12px;
    background: #ffffff;
    border: 1px dashed #bdd6ee;
    border-radius: 13px;
    padding: 10px 12px;
    color: #315C7E;
    font-size: 12.5px;
    line-height: 1.55;
}
@media (max-width: 760px) {
    .formula-grid { grid-template-columns: 1fr; }
    .formula-card { min-height: auto; }
}
</style>
</head>
<body>
<div class="formula-wrap">
    <div class="formula-title">🧮 Fórmulas aplicadas</div>
    <div class="formula-grid">
        <div class="formula-card">
            <div class="formula-name">1. Tiempo del periodo</div>
            <div class="formula-eq">\[t = H_f - H_i\]</div>
            <div class="formula-note">Si el periodo cruza medianoche: \(t = (1440 - H_i) + H_f\).</div>
        </div>
        <div class="formula-card">
            <div class="formula-name">2. Consumo de PAC</div>
            <div class="formula-eq">\[C_g = t \times Q_{PAC} \times \rho\]</div>
            <div class="formula-note">Donde \(Q_{PAC}\) está en mL/min y \(\rho\) en g/mL.</div>
        </div>
        <div class="formula-card">
            <div class="formula-name">3. Descenso del nivel</div>
            <div class="formula-eq">\[\Delta h = \frac{C_{kg}}{\rho \times 1000 \times A}\]</div>
            <div class="formula-note">Convierte el consumo a volumen y lo divide entre el área del tanque.</div>
        </div>
        <div class="formula-card">
            <div class="formula-name">4. Altura estimada</div>
            <div class="formula-eq">\[h_{actual} = h_i - \sum \Delta h\]</div>
            <div class="formula-note">Resta los descensos acumulados a la altura inicial del tanque.</div>
        </div>
    </div>
    <div class="formula-footer">
        <b>Variables:</b> \(t\): tiempo en minutos · \(H_i\): hora inicial · \(H_f\): hora final ·
        \(C_g\): consumo en gramos · \(C_{kg}\): consumo en kilogramos · \(A\): área del tanque en m² ·
        \(\rho\): densidad del PAC.
    </div>
</div>
</body>
</html>
"""
    components.html(html, height=540, scrolling=False)



# =========================================
# BLOQUE VISUAL DE FÓRMULAS HIDRÁULICAS — ESTILO PROFESIONAL
# =========================================
def mostrar_formulas_hidraulicas_profesionales():
    """Muestra todas las fórmulas del Sistema hidráulico en tarjetas limpias.
    Usa MathJax en components.html para que las expresiones se vean como documento técnico.
    """
    html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script>
window.MathJax = {
  tex: { inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']] },
  svg: { fontCache: 'global' }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #003A70;
}
.formula-wrap {
    background: linear-gradient(135deg, #F7FCFF 0%, #EEF8FF 100%);
    border: 1px solid #D6E8F7;
    border-left: 6px solid #48B9EA;
    border-radius: 18px;
    padding: 18px 20px 16px 20px;
    box-shadow: 0 6px 22px rgba(10, 22, 40, 0.06);
}
.formula-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
    color: #005B8E;
    font-size: 16px;
    font-weight: 850;
    letter-spacing: .2px;
}
.formula-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(280px, 1fr));
    gap: 14px;
}
.formula-card {
    background: #FFFFFF;
    border: 1px solid #CFE5F4;
    border-radius: 16px;
    padding: 16px 16px 14px 16px;
    min-height: 150px;
    box-shadow: 0 4px 16px rgba(10, 22, 40, 0.055);
}
.formula-card-wide {
    grid-column: 1 / -1;
    min-height: 165px;
}
.formula-name {
    font-size: 12px;
    text-transform: none;
    letter-spacing: .55px;
    font-weight: 800;
    color: #4E6F8A;
    margin-bottom: 6px;
}
.formula-eq {
    min-height: 68px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #004A8F;
    overflow-x: auto;
    padding: 7px 3px;
    font-size: 1.18rem;
}
.formula-note {
    margin-top: 7px;
    color: #4E6F8A;
    line-height: 1.45;
    font-size: 12px;
}
.formula-footer {
    margin-top: 12px;
    background: #FFFFFF;
    border: 1px dashed #BDD6EE;
    border-radius: 13px;
    padding: 10px 12px;
    color: #315C7E;
    font-size: 12.5px;
    line-height: 1.55;
}
.formula-warning {
    margin-top: 10px;
    background: #FFFDF7;
    border: 1px solid #F3D98B;
    border-left: 5px solid #F4B942;
    border-radius: 13px;
    padding: 10px 12px;
    color: #5F4B1B;
    font-size: 12.5px;
    line-height: 1.5;
}
@media (max-width: 760px) {
    .formula-grid { grid-template-columns: 1fr; }
    .formula-card { min-height: auto; }
}
</style>
</head>
<body>
<div class="formula-wrap">
    <div class="formula-title">📐 Fórmulas hidráulicas aplicadas</div>

    <div class="formula-grid">
        <div class="formula-card">
            <div class="formula-name">1. Área equivalente del tanque</div>
            <div class="formula-eq">\[A = \frac{C}{h_{max}}\]</div>
            <div class="formula-note">Convierte capacidad y nivel máximo operativo en un área hidráulica aproximada.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">2. Volumen calculado desde el nivel</div>
            <div class="formula-eq">\[V = h \times A\]</div>
            <div class="formula-note">El operador ingresa nivel \(h\); la app calcula volumen. Se limita entre 0 y la capacidad.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">3. Porcentaje de llenado</div>
            <div class="formula-eq">\[\%L = \frac{V}{C}\times 100\]</div>
            <div class="formula-note">Sirve para clasificar el tanque como bajo, normal, alto o crítico.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">4. Volúmenes de referencia</div>
            <div class="formula-eq">\[V_{min}=C\frac{p_{min}}{100}\quad V_{obj}=C\frac{p_{obj}}{100}\quad V_{alto}=C\frac{p_{alto}}{100}\]</div>
            <div class="formula-note">Define mínimo, objetivo y nivel alto de operación según porcentajes configurados.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">5. Salida total por ramales</div>
            <div class="formula-eq">\[Q_{salida}=\sum_{i=1}^{n} Q_i\]</div>
            <div class="formula-note">Cuando se elige salida por ramales, la salida total se calcula sumando cada conducción.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">6. Salida total directa</div>
            <div class="formula-eq">\[Q_{salida}=Q_{total}\]</div>
            <div class="formula-note">Cuando ya existe un macromedidor total, se usa ese dato como salida del tanque.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">7. Balance hidráulico instantáneo</div>
            <div class="formula-eq">\[Q_{neto}=Q_{entrada}-Q_{salida}\]</div>
            <div class="formula-note">Si es positivo el tanque sube; si es negativo el tanque baja.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">8. Conversión de caudal a cambio horario</div>
            <div class="formula-eq">\[\Delta V_h = 3.6\times Q_{neto}\]</div>
            <div class="formula-note">Porque \(1\,L/s = 3.6\,m^3/h\). El resultado queda en \(m^3/h\).</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">9. Proyección de volumen</div>
            <div class="formula-eq">\[V(t)=V_0+3.6\times Q_{neto}\times t\]</div>
            <div class="formula-note">Estima el volumen futuro manteniendo constante el balance actual durante \(t\) horas.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">10. Cambio de nivel entre dos lecturas</div>
            <div class="formula-eq">\[\Delta h=h_f-h_i\]</div>
            <div class="formula-note">Se usa cuando no hay macromedidor de entrada y se tienen dos niveles con tiempo conocido.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">11. Cambio de volumen por diferencia de nivel</div>
            <div class="formula-eq">\[\Delta V=A\times\Delta h\]</div>
            <div class="formula-note">Convierte el cambio de altura del tanque en cambio de volumen.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">12. Caudal neto estimado por nivel</div>
            <div class="formula-eq">\[Q_{neto,nivel}=\frac{\Delta V}{3.6\times\Delta t_h}\]</div>
            <div class="formula-note">Calcula el balance real observado en \(L/s\) a partir de nivel inicial y final.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">13. Entrada estimada sin macromedidor</div>
            <div class="formula-eq">\[Q_{entrada,est}=Q_{salida}+Q_{neto,nivel}\]</div>
            <div class="formula-note">Si el tanque subió, la entrada estimada aumenta; si bajó, disminuye.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">14. Entrada requerida para llegar al objetivo</div>
            <div class="formula-eq">\[Q_{req}=Q_{salida}+\frac{V_{obj}-V}{3.6\times T}\]</div>
            <div class="formula-note">Calcula qué entrada se necesitaría para llegar al volumen objetivo en \(T\) horas.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">15. Tiempo a nivel alto</div>
            <div class="formula-eq">\[t_{alto}=\frac{V_{alto}-V}{3.6\times Q_{neto}}\quad ;\quad Q_{neto}>0\]</div>
            <div class="formula-note">Se aplica cuando el tanque está subiendo. Ayuda a prevenir rebose.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">16. Tiempo a nivel mínimo</div>
            <div class="formula-eq">\[t_{min}=\frac{V-V_{min}}{3.6\times |Q_{neto}|}\quad ;\quad Q_{neto}<0\]</div>
            <div class="formula-note">Se aplica cuando el tanque está bajando. Ayuda a prevenir desabastecimiento.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">17. Producción que entra al tanque 4400 m³</div>
            <div class="formula-eq">\[Q_{prod}=Q_{módulo\,500}+Q_{módulo\,150}\]</div>
            <div class="formula-note">El agua producida por los módulos 500 y 150 se une antes de ingresar al tanque Diviso 4400 m³.</div>
        </div>

        <div class="formula-card formula-card-wide">
            <div class="formula-name">18. Balance tanque Diviso 4400 m³</div>
            <div class="formula-eq">\[\begin{aligned}Q_{salida,4400}&=Q_{4400\rightarrow1100}+Q_{linea\,CunMal}+Q_{Occidente}+Q_{otras}\\[4pt]Q_{neto,4400}&=Q_{prod}-Q_{salida,4400}\end{aligned}\]</div>
            <div class="formula-note">Las salidas propias del 4400 m³ son: línea Cunduy-Malvinas, Línea de Occidente, transferencia al 1100 m³ y otras si existen.</div>
        </div>

        <div class="formula-card formula-card-wide">
            <div class="formula-name">19. Salida total del tanque 1100 m³</div>
            <div class="formula-eq">\[Q_{salida,1100}=Q_{Comuna}+Q_{La\,Paz}+Q_{Álamos}+Q_{Altos}+Q_{Sebastopol}+Q_{otro}\]</div>
            <div class="formula-note">Las salidas sectorizadas del 1100 m³ se suman para obtener la salida total del tanque.</div>
        </div>

        <div class="formula-card formula-card-wide">
            <div class="formula-name">20. Entrada al tanque 1100 m³</div>
            <div class="formula-eq">\[\begin{aligned}Q_{entrada,1100}&=Q_{macro,4400\rightarrow1100}\\[4pt]Q_{entrada,1100}&=Q_{salida,1100}+\frac{V_f-V_i}{3.6\times\Delta t_h}\end{aligned}\]</div>
            <div class="formula-note">Si hay macromedidor se usa el dato medido. Si no hay macro, se estima con diferencia de nivel y balance de masa.</div>
        </div>

        <div class="formula-card formula-card-wide">
            <div class="formula-name">21. Línea única en T hacia Cunduy y Malvinas</div>
            <div class="formula-eq">\[\begin{aligned}Q_{linea\,CunMal}&=Q_{entrada,Cun}+Q_{continua,Mal}\\[4pt]Q_{continua,Mal}&=\max\left(0,\,Q_{linea\,CunMal}-Q_{entrada,Cun}\right)\end{aligned}\]</div>
            <div class="formula-note">Representa una sola conducción: primero deriva a Cunduy y el caudal restante continúa hacia Malvinas.</div>
        </div>

        <div class="formula-card">
            <div class="formula-name">22. Límite máximo de conducción</div>
            <div class="formula-eq">\[Q_{despacho}=\min(Q_{calculado},\,Q_{max})\]</div>
            <div class="formula-note">Evita recomendar un caudal mayor al límite operativo configurado.</div>
        </div>

        <div class="formula-card formula-card-wide">
            <div class="formula-name">23. Error de cierre de cada tanque</div>
            <div class="formula-eq">\[\varepsilon=Q_{entrada}-Q_{salida}-\frac{V_f-V_i}{3.6\,\Delta t_h}\]</div>
            <div class="formula-note">Si el error es cercano a cero, los caudales y el cambio de nivel son compatibles. Un error alto indica lecturas de horas distintas, una salida faltante, doble conteo o una medición incorrecta.</div>
        </div>

        <div class="formula-card formula-card-wide">
            <div class="formula-name">24. Balance conjunto de los tanques 4400 y 1100</div>
            <div class="formula-eq">\[\begin{aligned}Q_{entrada,4400}-\left(Q_{ext,4400}+Q_{salida,1100}\right)&=Q_{alm,4400}+Q_{alm,1100}\\[4pt]Q_{alm,j}&=\frac{V_{f,j}-V_{i,j}}{3.6\,\Delta t_h}\end{aligned}\]</div>
            <div class="formula-note">La transferencia 4400 → 1100 es interna: sale del 4400 y entra al 1100, por eso se cancela en el balance conjunto y no debe contarse dos veces.</div>
        </div>

        <div class="formula-card formula-card-wide">
            <div class="formula-name">25. Transferencia sostenible hacia el tanque 1100</div>
            <div class="formula-eq">\[Q_{4400\rightarrow1100,sost}=Q_{entrada,4400}-Q_{ext,4400}-Q_{alm,4400,obj}\]</div>
            <div class="formula-note">Para mantener estable el tanque 4400 se usa \(Q_{alm,4400,obj}=0\). Si la transferencia real es mayor, el 4400 debe bajar de nivel.</div>
        </div>
    </div>

    <div class="formula-footer">
        <b>Variables:</b>
        \(A\): área equivalente en m² · \(C\): capacidad del tanque en m³ · \(h\): nivel actual en m ·
        \(h_i\): nivel inicial · \(h_f\): nivel final · \(h_{max}\): nivel máximo operativo ·
        \(V\): volumen actual en m³ · \(V_0\): volumen inicial · \(Q\): caudal en L/s ·
        \(Q_{entrada}\): entrada · \(Q_{salida}\): salida · \(Q_{neto}\): balance ·
        \(\Delta t_h\): tiempo en horas · \(T\): horizonte de corrección en horas.
    </div>

    <div class="formula-warning">
        <b>Nota técnica:</b> estas fórmulas usan una aproximación lineal nivel-volumen. Si más adelante tienes la tabla real de calibración de cada tanque, el sistema puede reemplazar \(V=h\times A\) por una curva o tabla nivel-volumen más precisa.
    </div>
</div>
</body>
</html>
"""
    components.html(html, height=1960, scrolling=False)


# =========================================
# CALCULADORA DE CONSUMO PAC
# =========================================
def mostrar_calculadora_pac():
    st.markdown("<div class='bloque'>", unsafe_allow_html=True)
    st.markdown("<div class='etiqueta'>💧 Calculadora de PAC</div>", unsafe_allow_html=True)
 
    st.markdown("""
    <p style="color:#4E6F8A;font-size:0.93rem;margin-bottom:1.2rem;line-height:1.6">
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
        <div style="background:#EEF7FC;border:1px solid #CFE5F4;border-radius:12px;padding:0.7rem 1.2rem;font-size:0.87rem;color:#004A8F">
            <span style="font-weight:700;display:block;font-size:0.72rem;color:#4E6F8A;text-transform:uppercase;margin-bottom:2px">Radio</span>
            {radio_tanque:.4f} m
        </div>
        <div style="background:#EEF7FC;border:1px solid #CFE5F4;border-radius:12px;padding:0.7rem 1.2rem;font-size:0.87rem;color:#004A8F">
            <span style="font-weight:700;display:block;font-size:0.72rem;color:#4E6F8A;text-transform:uppercase;margin-bottom:2px">Área</span>
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
        "Caudal de PAC (mL/min)": [100.0], "Densidad del PAC (g/mL)": [1.33]
    })
 
    if "tabla_consumos_pac" not in st.session_state:
        st.session_state.tabla_consumos_pac = tabla_inicial.copy()
 
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("+ Agregar fila", use_container_width=True, key="btn_fila_base"):
            st.session_state.tabla_consumos_pac = pd.concat([
                st.session_state.tabla_consumos_pac,
                pd.DataFrame({"Hora inicio": [""], "Hora final": [""],
                              "Caudal de PAC (mL/min)": [0.0], "Densidad del PAC (g/mL)": [1.33]})
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
            "Caudal de PAC (mL/min)": st.column_config.NumberColumn("Caudal de PAC (mL/min)", min_value=0.0,  step=0.1,  format="%.2f", width="medium"),
            "Densidad del PAC (g/mL)": st.column_config.NumberColumn("Densidad del PAC (g/mL)", min_value=0.01, step=0.01, format="%.2f", width="medium"),
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
    df_calc["Caudal de PAC (mL/min)"] = pd.to_numeric(df_calc["Caudal de PAC (mL/min)"], errors="coerce")
    df_calc["Densidad del PAC (g/mL)"] = pd.to_numeric(df_calc["Densidad del PAC (g/mL)"], errors="coerce")
    df_calc["Min inicio"]          = df_calc["Hora inicio"].apply(hora_a_minutos)
    df_calc["Min final"]           = df_calc["Hora final"].apply(hora_a_minutos)
 
    df_validas = df_calc.dropna(subset=[
        "Hora inicio", "Hora final", "Caudal de PAC (mL/min)", "Densidad del PAC (g/mL)", "Min inicio", "Min final"
    ]).copy()
 
    if df_validas.empty:
        st.info("Completa una fila válida y el cálculo aparecerá automáticamente.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
 
    df_validas = df_validas[
        (df_validas["Min inicio"] >= 0) & (df_validas["Min inicio"] <= 1440) &
        (df_validas["Min final"]  >= 0) & (df_validas["Min final"]  <= 1440) &
        (df_validas["Caudal de PAC (mL/min)"] >= 0) & (df_validas["Densidad del PAC (g/mL)"] > 0)
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
    df_validas["Consumo (g)"]            = df_validas["Tiempo (min)"] * df_validas["Caudal de PAC (mL/min)"] * df_validas["Densidad del PAC (g/mL)"]
    df_validas["Consumo (kg)"]           = df_validas["Consumo (g)"] / 1000
    df_validas["Volumen consumido (m³)"] = df_validas["Consumo (kg)"] / (df_validas["Densidad del PAC (g/mL)"] * 1000)
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
        "Caudal de PAC (mL/min)", "Densidad del PAC (g/mL)",
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
    mostrar_tabla_profesional(
        df_mostrar,
        formatos={
            "Tiempo (min)": "{:.1f}", "Caudal de PAC (mL/min)": "{:.1f}", "Densidad del PAC (g/mL)": "{:.2f}",
            "Consumo (g)": "{:.2f}", "Consumo (kg)": "{:.4f}",
            "Descenso altura (m)": "{:.4f}", "Altura estimada (m)": "{:.4f}"
        }
    )
 
    if len(df_mostrar) > 1:
        alturas = [altura_pasada] + list(df_mostrar["Altura estimada (m)"])
        labels  = ["Inicio"] + [f"Reg. {i}" for i in range(1, len(df_mostrar) + 1)]
        fig_altura = go.Figure()
        fig_altura.add_trace(go.Scatter(
            x=labels, y=alturas, mode="lines+markers",
            line=dict(color="#008ACB", width=2.5, shape="spline"),
            marker=dict(size=9, color="#008ACB", line=dict(color="white", width=2)),
            fill="tozeroy", fillcolor="rgba(26,111,255,0.07)"
        ))
        fig_altura.update_layout(
            title="Evolución de altura estimada del tanque",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter", color="#003A70", size=12),
            xaxis=dict(title="Registro", gridcolor="#E3F2F8"),
            yaxis=dict(title="Altura (m)", gridcolor="#E3F2F8"),
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
 
    mostrar_formulas_pac_profesionales()
 
    st.markdown("</div>", unsafe_allow_html=True)
 
 
# =========================================
# PANEL DE RESULTADOS HTML — PTAP STYLE
# =========================================

# =============================================================================
# REEMPLAZA COMPLETAMENTE ESTAS DOS SECCIONES EN TU app.py:
#   1. La función generar_panel_resultados_html(...)
#   2. La línea: components.html(panel_html, height=1020, scrolling=True)
#      por:      components.html(panel_html, height=1060, scrolling=False)
#
# CAMBIOS PRINCIPALES:
#   - Fondo claro (#EEF7FC / blanco) en lugar de azul oscuro -> mejor lectura
#   - Todos los textos en colores oscuros con contraste WCAG AA correcto
#   - Grid responsive que cabe sin scroll en pantallas normales
#   - Corregido bug: "color:#3a4a7a)" tenia parentesis de mas
#   - Tamano de fuente ligeramente mayor en etiquetas
#   - Tarjetas con sombra suave en lugar de fondo translucido oscuro
# =============================================================================

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
        nivel_color = "#258B6A"; nivel_label = "NIVEL NORMAL"
        agua_c1, agua_c2 = "#008ACB", "#48B9EA"

    # ── Color de tendencia ───────────────────────────────────────────────────
    if tendencia_proy == "subiendo":
        tend_color = "#258B6A"; tend_icon = "▲"; tend_txt = "SUBIENDO"
    elif tendencia_proy == "bajando":
        tend_color = "#c0392b"; tend_icon = "▼"; tend_txt = "BAJANDO"
    else:
        tend_color = "#4E7F9F"; tend_icon = "●"; tend_txt = "ESTABLE"

    # ── Accion recomendada ───────────────────────────────────────────────────
    if delta_entrada_planta > 0.5:
        accion_color = "#258B6A"; accion_icon = "⬆"; accion_dir = "SUBIR"
    elif delta_entrada_planta < -0.5:
        accion_color = "#c0392b"; accion_icon = "⬇"; accion_dir = "BAJAR"
    else:
        accion_color = "#4E7F9F"; accion_icon = "●"; accion_dir = "MANTENER"

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
    signo_q_post = "+" if Q_neto_post_ajuste_Ls >= 0 else ""
    
    if Q_neto_post_ajuste_Ls > 0.05:
        color_q_post = "#258B6A"
        txt_q_post = "SUBIENDO"
    elif Q_neto_post_ajuste_Ls < -0.05:
        color_q_post = "#c0392b"
        txt_q_post = "BAJANDO"
    else:
        color_q_post = "#4E7F9F"
        txt_q_post = "ESTABLE"

    rebose_txt = hora_rebose_str if hora_rebose_str else "No aplica"
    minimo_txt = hora_minimo_str if hora_minimo_str else "No aplica"
    rebose_dur = fmt_tiempo(t_rebose_min)
    minimo_dur = fmt_tiempo(t_minimo_min)

    rebose_color = ("#c0392b" if (t_rebose_min is not None and t_rebose_min < 60)
                    else "#d35400" if (t_rebose_min is not None and t_rebose_min < 180)
                    else "#4E7F9F")
    minimo_color = ("#c0392b" if (t_minimo_min is not None and t_minimo_min < 60)
                    else "#d35400" if (t_minimo_min is not None and t_minimo_min < 180)
                    else "#4E7F9F")

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
            vc = "#258B6A"; vd = "ABRIR SALIDA"
        elif delta_entrada_planta < -0.5:
            vc = "#c0392b"; vd = "CERRAR SALIDA"
        else:
            vc = "#4E7F9F"; vd = "MANTENER SALIDA"
        valv_html = (
            f'<div style="background:#EEF7FC;border:1.5px solid #2563eb;border-radius:12px;'
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
    TW, TH, TX, TY = 100, 250, 45, 20
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
  background: #EEF7FC;
  font-family: Inter, sans-serif;
  color: #0f172a;
  padding: 10px;
  font-size: 13px;
}}

/* ── HEADER ── */
.hdr {{
  background: linear-gradient(90deg, #004A8F 0%, #1a4a8a 100%);
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
  text-transform: none;
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
  color: #004A8F;
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
  border: 1px solid #CFE5F4;
  border-radius: 14px;
  padding: 11px 13px;
  box-shadow: 0 2px 8px rgba(10,22,40,0.06);
}}
.card-titulo {{
  font-size: 0.62rem;
  font-weight: 700;
  color: #1e3a5f;
  text-transform: none;
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
  text-transform: none;
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
  border: 1px solid #CFE5F4;
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
  background: #008ACB;
}}
.mc.verde::before {{ background: #67A84A; }}
.mc.rojo::before  {{ background: #dc2626; }}
.mc.naranja::before {{ background: #ea580c; }}
.mc.azul::before {{ background: #2563eb; }}
.m-lbl {{
  font-size: 0.60rem;
  font-weight: 600;
  color: #4E7F9F;
  text-transform: none;
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
  text-transform: none;
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
  background: #EEF7FC;
  border: 1px solid #CFE5F4;
  border-radius: 10px;
  padding: 7px 12px;
  text-align: center;
}}
.an-lbl {{
  font-size: 0.58rem;
  font-weight: 600;
  color: #4E7F9F;
  text-transform: none;
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
.chip-azul  {{ background: #008ACB; color: #fff; }}
.chip-morado {{ background: #008ACB; color: #fff; }}
.chip-verde  {{ background: #67A84A; color: #fff; }}
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
.tl-det .vc {{ color: #008ACB; font-weight: 700; }}
.tl-det .vg {{ color: #67A84A; font-weight: 700; }}
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
  border: 1px solid #CFE5F4;
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
  background: #67A84A;
  border-radius: 2px;
  left: {pct_objetivo:.1f}%;
  box-shadow: 0 0 6px #67A84A88;
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
  background: #F7FCFF;
  border: 1px solid #CFE5F4;
  border-radius: 10px;
  padding: 7px 5px;
}}
.rs-lbl {{
  font-size: 0.58rem;
  font-weight: 600;
  color: #4E7F9F;
  text-transform: none;
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
  background: #F7FCFF;
  border-radius: 10px;
  padding: 8px 10px;
  border-left: 3px solid;
}}
.lim-lbl {{
  font-size: 0.60rem;
  font-weight: 700;
  text-transform: none;
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
  background: #F7FCFF;
  border: 1px solid #CFE5F4;
  border-radius: 9px;
  padding: 7px 5px;
}}
.bi-lbl {{
  font-size: 0.58rem;
  font-weight: 600;
  color: #4E7F9F;
  text-transform: none;
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
  background: #EEF7FC;
  border: 1px solid #CFE5F4;
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
              rx="9" fill="url(#gTk)" stroke="#A8D6E9" stroke-width="2"/>

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
        <text x="{TX+TW+8}" y="{y_rebose+4:.1f}" font-size="7.5"
              font-family="Inter,sans-serif" fill="#dc2626" font-weight="700">
          REB {altura_rebose:.2f}m
        </text>

        <!-- Línea mínima -->
        <line x1="{TX-5}" y1="{y_minima:.1f}" x2="{TX+TW+5}" y2="{y_minima:.1f}"
              stroke="#ea580c" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.9"/>
        <text x="{TX+TW+8}" y="{y_minima+4:.1f}" font-size="7.5"
              font-family="Inter,sans-serif" fill="#ea580c" font-weight="700">
          MIN {altura_minima:.2f}m
        </text>

        <!-- Línea objetivo -->
        <line x1="{TX-5}" y1="{y_obj:.1f}" x2="{TX+TW+5}" y2="{y_obj:.1f}"
              stroke="#67A84A" stroke-width="1.5" stroke-dasharray="3,2" opacity="0.8"/>
        <text x="{TX+TW+8}" y="{y_obj+4:.1f}" font-size="7.5"
              font-family="Inter,sans-serif" fill="#67A84A" font-weight="700">
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
              rx="5" fill="#A8D6E9" stroke="#6a9ab8" stroke-width="1.5"/>
        <!-- Base -->
        <rect x="{TX-8}" y="{TB+22}" width="{TW+16}" height="11"
              rx="5" fill="#A8D6E9" stroke="#6a9ab8" stroke-width="1.5"/>
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
          <div class="ld"><div class="ld-dot" style="background:#67A84A"></div>Objetivo</div>
          <div class="ld"><div class="ld-dot" style="background:#dc2626"></div>Rebose</div>
          <div class="ld"><div class="ld-dot" style="background:#ea580c"></div>Mínimo</div>
        </div>

        <div class="res-stats">
          <div class="rs">
            <span class="rs-lbl">Cuando llega ajuste</span>
            <span class="rs-val" style="color:#008ACB">{nivel_cuando_llega_ajuste:.3f} m</span>
          </div>
          <div class="rs">
            <span class="rs-lbl">Post corrección</span>
            <span class="rs-val" style="color:{accion_color}">{nivel_final_estimado:.3f} m</span>
          </div>
          <div class="rs">
            <span class="rs-lbl">Q neto esperado</span>
            <span class="rs-val" style="color:{color_q_post}">{signo_q_post}{Q_neto_post_ajuste_Ls:.2f} L/s</span>
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

    # La calculadora queda amarrada a la planta con la que inició sesión el usuario.
    # Las capacidades y salidas se precargan según el instructivo SGI-PYT-INS-070.
    planta_usuario_tanque = st.session_state.get("planta_usuario", "Caldas")
    if planta_usuario_tanque not in TANQUES_OPERATIVOS:
        planta_usuario_tanque = "Caldas"

    tanques_disponibles = TANQUES_OPERATIVOS[planta_usuario_tanque]
    nombres_tanques = list(tanques_disponibles.keys())

    col_sel_tq, col_info_tq = st.columns([0.85, 1.75], gap="medium")
    with col_sel_tq:
        tanque_seleccionado = st.selectbox(
            "Tanque a evaluar",
            nombres_tanques,
            key="tanq_tanque_seleccionado",
        )

    cfg_tanque = tanques_disponibles[tanque_seleccionado]

    # Cuando cambia el tanque, se actualizan los valores base sin perder la libertad de editarlos.
    if st.session_state.get("tanq_tanque_activo") != tanque_seleccionado:
        st.session_state.tanq_tanque_activo = tanque_seleccionado
        st.session_state.tanq_vol_total = float(cfg_tanque["capacidad_m3"])
        st.session_state.tanq_altura_lleno = float(cfg_tanque.get("altura_lleno_default", 2.85))
        st.session_state.tanq_altura_rebose = float(cfg_tanque.get("altura_rebose_default", 2.82))
        st.session_state.tanq_altura_minima = float(cfg_tanque.get("altura_minima_default", 1.40))
        st.session_state.tanq_caudal_max_planta = float(cfg_tanque.get("caudal_max_planta_default", 220.0))
        if "tanq_salidas_activas" in st.session_state:
            del st.session_state["tanq_salidas_activas"]

    with col_info_tq:
        salidas_txt = ", ".join(cfg_tanque["salidas"])
        macro_entrada_txt = "Sí tiene referencia de macromedición de entrada/producción" if cfg_tanque["tiene_macromedidor_entrada"] else "No tiene macromedidor de entrada al tanque"
        st.info(
            f"**Planta:** {planta_usuario_tanque} · **Capacidad:** {cfg_tanque['capacidad_m3']:.0f} m³ · "
            f"**Entrada:** {macro_entrada_txt}.  \n"
            f"**Salidas principales:** {salidas_txt}.  \n"
            f"**Registros:** {cfg_tanque['registro_macro']} · {cfg_tanque['registro_diario']}."
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
                min_value=1.0,
                value=float(st.session_state.get("tanq_vol_total", cfg_tanque["capacidad_m3"])),
                step=10.0, format="%.2f", key="tanq_vol_total"
            )
            altura_lleno = st.number_input(
                "Altura cuando el tanque está lleno (m)",
                min_value=0.01,
                value=float(st.session_state.get("tanq_altura_lleno", cfg_tanque.get("altura_lleno_default", 2.85))),
                step=0.01, format="%.2f", key="tanq_altura_lleno"
            )
            area_equiv = volumen_total / altura_lleno if altura_lleno > 0 else 0.0
            st.info(f"Área equivalente: **{area_equiv:.4f} m²** = {volumen_total:.1f} / {altura_lleno:.2f}")

        with st.expander("⚙️ Límites operativos", expanded=True):
            altura_rebose = st.number_input(
                "Altura límite de rebose (m)",
                min_value=0.01,
                value=float(st.session_state.get("tanq_altura_rebose", cfg_tanque.get("altura_rebose_default", 2.82))),
                step=0.01, format="%.2f", key="tanq_altura_rebose"
            )
            altura_minima = st.number_input(
                "Altura mínima operativa (m)",
                min_value=0.0,
                value=float(st.session_state.get("tanq_altura_minima", cfg_tanque.get("altura_minima_default", 1.40))),
                step=0.01, format="%.2f", key="tanq_altura_minima"
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

        with st.expander("🚰 Caudales y salidas", expanded=True):
            st.info(
                "Entrada a **planta** ≠ entrada al **tanque**. "
                "Pérdidas, lavados, demanda y tiempo hidráulico reducen lo que llega al tanque. "
                + cfg_tanque["nota_entrada"]
            )

            salidas_activas = st.multiselect(
                "Salidas activas observadas",
                options=cfg_tanque["salidas"],
                default=st.session_state.get("tanq_salidas_activas", []),
                key="tanq_salidas_activas",
                help="Selecciona las salidas que están aportando al caudal total de salida registrado."
            )
            if salidas_activas:
                st.caption("Salidas seleccionadas: " + ", ".join(salidas_activas))
            else:
                st.caption("Puedes dejarlo vacío si solo vas a trabajar con el caudal total de salida.")

            caudal_max_planta = st.number_input(
                "Caudal máximo de la planta (L/s)",
                min_value=1.0,
                value=float(st.session_state.get("tanq_caudal_max_planta", cfg_tanque.get("caudal_max_planta_default", 220.0))),
                step=1.0, format="%.2f", key="tanq_caudal_max_planta"
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
            Q_requerido_tanque_Ls  = caudal_salida_esperada_ls

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
            y_max = max(altura_rebose * 1.10, altura_actual * 1.12, nivel_objetivo * 1.08)

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

            fig.add_hrect(y0=0, y1=altura_minima,
                          fillcolor="rgba(245, 158, 11, 0.06)", line_width=0)
            fig.add_hrect(y0=altura_rebose, y1=y_max,
                          fillcolor="rgba(220, 38, 38, 0.05)", line_width=0)

            line_specs = [
                (altura_rebose, "#B91C1C", f"Rebose {altura_rebose:.2f} m", "dash"),
                (altura_minima, "#B45309", f"Mínimo {altura_minima:.2f} m", "dash"),
                (nivel_objetivo, "#0A8F83", f"Objetivo {nivel_objetivo:.2f} m", "dot"),
            ]
            for y_val, color, label, dash in line_specs:
                fig.add_hline(y=y_val, line=dict(color=color, width=1.5, dash=dash))
                fig.add_annotation(
                    x=1.005, y=y_val, xref="paper", yref="y",
                    text=label, showarrow=False, xanchor="left",
                    font=dict(color=color, size=10)
                )

            fig.add_trace(go.Scatter(
                x=horas_proj, y=niv_proj, mode="lines",
                name="Sin ajuste",
                line=dict(color="#005B96", width=2.6, shape="spline")
            ))
            fig.add_trace(go.Scatter(
                x=horas_proj, y=niv_aj, mode="lines",
                name="Con ajuste recomendado",
                line=dict(color="#6FAE4A", width=2.6, dash="dash", shape="spline")
            ))
            fig.add_trace(go.Scatter(
                x=[hora_actual_str], y=[altura_actual], mode="markers",
                name="Nivel actual",
                marker=dict(size=10, color="#0F172A", line=dict(color="#FFFFFF", width=1.5))
            ))

            fig.add_vline(x=hora_efecto_str, line_width=1.2, line_dash="dot", line_color="#64748B")
            fig.add_annotation(
                x=hora_efecto_str, y=y_max*0.95,
                text=f"Efecto del ajuste\n{hora_efecto_str}",
                showarrow=False,
                font=dict(color="#315C7E", size=10),
                bgcolor="#F8FAFC",
                bordercolor="#CBD5E1",
                borderwidth=1,
                borderpad=4
            )

            if hora_rebose_str:
                fig.add_trace(go.Scatter(
                    x=[hora_rebose_str], y=[altura_rebose],
                    mode="markers", name=f"Rebose {hora_rebose_str}",
                    marker=dict(size=11, color="#B91C1C", symbol="diamond")
                ))
            if hora_minimo_str:
                fig.add_trace(go.Scatter(
                    x=[hora_minimo_str], y=[altura_minima],
                    mode="markers", name=f"Mínimo {hora_minimo_str}",
                    marker=dict(size=11, color="#B45309", symbol="diamond")
                ))

            tick_vals = [horas_proj[i] for i, p in enumerate(pasos_min) if p % 30 == 0]
            fig.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font=dict(family="Inter", color="#0F172A", size=12),
                xaxis=dict(
                    title="Hora del día",
                    gridcolor="#D8EAF4",
                    linecolor="#CFE5F4",
                    tickangle=-30,
                    tickvals=tick_vals,
                    tickfont=dict(size=11, color="#334155"),
                    title_font=dict(size=12, color="#334155")
                ),
                yaxis=dict(
                    title="Altura (m)",
                    gridcolor="#D8EAF4",
                    linecolor="#CFE5F4",
                    range=[0, y_max],
                    tickfont=dict(size=11, color="#334155"),
                    title_font=dict(size=12, color="#334155")
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=1.02,
                    xanchor="left", x=0,
                    bgcolor="rgba(255,255,255,0.92)",
                    bordercolor="#CFE5F4",
                    borderwidth=1,
                    font=dict(size=11, color="#334155")
                ),
                margin=dict(l=24, r=110, t=18, b=54),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# SISTEMA HIDRÁULICO DE TANQUES
# =========================================
def mostrar_sistema_hidraulico():
    """
    Sistema hidráulico organizado por planta y por tanque.
    Permite trabajar con nivel, convertir nivel a volumen, estimar entradas por
    cambio de nivel cuando no hay macromedidor y evaluar salidas por total o por ramales.
    """

    st.markdown("<div class='bloque'>", unsafe_allow_html=True)
    st.markdown("<div class='etiqueta'>💧 Sistema hidráulico · tanques independientes</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='texto-panel'>Este módulo separa la operación por planta y por tanque. "
        "Solo necesitas ingresar el <b>nivel</b> y los caudales disponibles. Cuando no hay macromedidor de entrada, "
        "la app puede estimar la entrada usando la diferencia de niveles en un periodo de tiempo. "
        "No controla válvulas reales; solo entrega cálculos de apoyo para revisar con el personal autorizado.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("""
    <style>
    .sish-card{
        background:rgba(255,255,255,0.90);
        border:1px solid rgba(0,90,140,0.14);
        border-radius:18px;
        padding:1.05rem 1.15rem;
        box-shadow:0 8px 24px rgba(0,49,83,0.06);
        margin:0.55rem 0 1rem 0;
    }
    .sish-title{
        color:#003A70;
        font-weight:900;
        font-size:1.05rem;
        letter-spacing:.2px;
        margin-bottom:.18rem;
    }
    .sish-sub{
        color:#4E6F8A;
        font-size:.86rem;
        line-height:1.45;
        margin-bottom:.7rem;
    }
    .formula-box{
        background:#F5FBFF;
        border:1px solid rgba(0,138,203,.16);
        border-left:6px solid #008ACB;
        border-radius:14px;
        padding:.85rem 1rem;
        color:#003A70;
        font-size:.90rem;
        line-height:1.65;
        margin:.65rem 0 1rem 0;
    }
    .decision-box{
        background:white;
        border-radius:18px;
        padding:1rem 1.2rem;
        box-shadow:0 8px 26px rgba(10,22,40,.08);
        margin:1rem 0;
    }
    .mini-note{
        background:#F7FBFD;
        border:1px dashed rgba(0,90,140,.22);
        border-radius:14px;
        padding:.75rem .9rem;
        color:#255E82;
        font-size:.87rem;
        line-height:1.48;
        margin-top:.5rem;
    }
    .calc-wrap{
        background:#F7FCFF;
        border:1px solid rgba(0,138,203,.18);
        border-left:6px solid #00A3E0;
        border-radius:16px;
        padding:1rem 1rem .8rem 1rem;
        margin:.75rem 0 1rem 0;
        box-shadow:0 6px 18px rgba(0,49,83,.05);
    }
    .calc-title{
        color:#003A70;
        font-weight:900;
        font-size:1rem;
        margin-bottom:.6rem;
    }
    .calc-grid{
        display:grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap:.8rem;
    }
    .calc-card{
        background:#FFFFFF;
        border:1px solid rgba(0,90,140,.14);
        border-radius:14px;
        padding:.8rem .9rem;
        min-height:150px;
    }
    .calc-name{
        color:#234E70;
        font-weight:800;
        font-size:.9rem;
        margin-bottom:.28rem;
    }
    .calc-eq{
        color:#0B5AA8;
        font-size:1.15rem;
        text-align:center;
        line-height:1.8;
        margin:.35rem 0 .45rem 0;
        overflow-x:auto;
        font-weight:700;
    }
    .calc-note{
        color:#5A7890;
        font-size:.82rem;
        line-height:1.45;
        margin-top:.25rem;
    }
    @media (max-width: 900px){
        .calc-grid{grid-template-columns:1fr;}
        .calc-card{min-height:auto;}
    }
    </style>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────
    # Utilidades hidráulicas
    # ─────────────────────────────────────────────────────────────────────
    def clamp(v, lo, hi):
        return max(float(lo), min(float(v), float(hi)))

    def safe_div(a, b, default=0.0):
        try:
            if abs(float(b)) < 1e-12:
                return default
            return float(a) / float(b)
        except Exception:
            return default

    def q_to_m3h(q_ls):
        return float(q_ls) * 3.6

    def fmt_num(v, dec=2):
        try:
            return f"{float(v):,.{dec}f}"
        except Exception:
            return "0.00"

    def fmt_tiempo(horas):
        if horas is None or not np.isfinite(horas) or horas < 0:
            return "No aplica"
        if horas < 1/60:
            return "< 1 min"
        h = int(horas)
        m = int(round((horas - h) * 60))
        if m == 60:
            h += 1
            m = 0
        if h <= 0:
            return f"{m} min"
        return f"{h} h {m:02d} min"

    def area_equivalente(capacidad_m3, nivel_max_m):
        return safe_div(capacidad_m3, max(nivel_max_m, 0.0001), 0.0)

    def volumen_por_nivel(nivel_m, nivel_max_m, capacidad_m3):
        area = area_equivalente(capacidad_m3, nivel_max_m)
        volumen = max(float(nivel_m), 0.0) * area
        return clamp(volumen, 0.0, capacidad_m3)

    def pct_tanque(volumen, capacidad):
        return safe_div(volumen, capacidad, 0.0) * 100.0

    def cambio_por_nivel(nivel_actual, nivel_anterior, capacidad_m3, nivel_max_m, periodo_min):
        """Calcula cambio de volumen y Q neto a partir de diferencia de nivel."""
        area = area_equivalente(capacidad_m3, nivel_max_m)
        delta_h = float(nivel_actual) - float(nivel_anterior)
        delta_v = area * delta_h
        horas = max(float(periodo_min) / 60.0, 1/60)
        q_neto_ls = delta_v / horas / 3.6
        return delta_h, delta_v, q_neto_ls

    def estimar_entrada_desde_nivel(nivel_actual, nivel_anterior, capacidad_m3, nivel_max_m, periodo_min, salida_ls):
        delta_h, delta_v, q_neto_ls = cambio_por_nivel(nivel_actual, nivel_anterior, capacidad_m3, nivel_max_m, periodo_min)
        q_entrada = max(0.0, float(salida_ls) + q_neto_ls)
        return q_entrada, delta_h, delta_v, q_neto_ls

    def error_cierre_balance(q_entrada, q_salida, nivel_actual, nivel_anterior, capacidad_m3, nivel_max_m, periodo_min):
        """Calcula el error de cierre en L/s usando caudales y cambio observado de nivel."""
        delta_h, delta_v, q_almacenamiento = cambio_por_nivel(
            nivel_actual,
            nivel_anterior,
            capacidad_m3,
            nivel_max_m,
            periodo_min,
        )
        error_ls = float(q_entrada) - float(q_salida) - float(q_almacenamiento)
        return {
            "delta_h_m": delta_h,
            "delta_v_m3": delta_v,
            "q_almacenamiento_ls": q_almacenamiento,
            "error_ls": error_ls,
        }

    def tiempo_a_limite(volumen, capacidad, q_neto_ls, min_pct, alto_pct):
        q_m3h = q_to_m3h(q_neto_ls)
        v_min = capacidad * min_pct / 100.0
        v_alto = capacidad * alto_pct / 100.0
        if abs(q_m3h) < 0.0001:
            return "Estable", "No aplica", None
        if q_m3h > 0:
            horas = max(0.0, (v_alto - volumen) / q_m3h)
            return "Subiendo", fmt_tiempo(horas), horas
        horas = max(0.0, (volumen - v_min) / abs(q_m3h))
        return "Bajando", fmt_tiempo(horas), horas

    def estado_tanque(volumen, capacidad, min_pct, objetivo_pct, alto_pct):
        pct = pct_tanque(volumen, capacidad)
        if pct <= min_pct:
            return pct, "Crítico bajo", "🔴", "#e63946"
        if pct < objetivo_pct - 10:
            return pct, "Bajo", "🟠", "#f4a261"
        if pct >= alto_pct:
            return pct, "Alto / riesgo rebose", "🔴", "#e63946"
        if pct > objetivo_pct + 10:
            return pct, "Alto controlado", "🟡", "#e9c46a"
        return pct, "Normal", "🟢", "#2DB9A3"

    def requerimiento_entrada(volumen, capacidad, salida_ls, horizonte_h, objetivo_pct, alto_pct):
        """Entrada requerida para llegar al objetivo en el horizonte sin ignorar la salida."""
        objetivo_vol = capacidad * objetivo_pct / 100.0
        horizonte_h = max(float(horizonte_h), 0.25)
        q_req = float(salida_ls) + (objetivo_vol - float(volumen)) / (3.6 * horizonte_h)
        pct = pct_tanque(volumen, capacidad)
        if pct >= alto_pct:
            q_req = min(q_req, float(salida_ls) * 0.70)
        return max(0.0, q_req)

    def evaluar_tanque(nombre, nivel, capacidad, nivel_max, q_in, q_out, min_pct, objetivo_pct, alto_pct):
        volumen = volumen_por_nivel(nivel, nivel_max, capacidad)
        q_neto = float(q_in) - float(q_out)
        pct, estado, icono, color = estado_tanque(volumen, capacidad, min_pct, objetivo_pct, alto_pct)
        tendencia, tiempo_limite, horas_limite = tiempo_a_limite(volumen, capacidad, q_neto, min_pct, alto_pct)
        return {
            "Tanque": nombre,
            "Nivel (m)": float(nivel),
            "Volumen calculado (m³)": volumen,
            "Capacidad (m³)": float(capacidad),
            "% llenado": pct,
            "Entrada (L/s)": float(q_in),
            "Salida (L/s)": float(q_out),
            "Balance (L/s)": q_neto,
            "Cambio (m³/h)": q_to_m3h(q_neto),
            "Estado": f"{icono} {estado}",
            "Tendencia": tendencia,
            "Tiempo a límite": tiempo_limite,
            "_horas_limite": horas_limite,
            "_color": color,
        }

    def card_inicio(titulo, subtitulo=""):
        st.markdown(f"<div class='sish-card'><div class='sish-title'>{titulo}</div><div class='sish-sub'>{subtitulo}</div>", unsafe_allow_html=True)

    def card_fin():
        st.markdown("</div>", unsafe_allow_html=True)

    def mostrar_resumen_tanque(nombre, nivel, volumen, capacidad, q_in, q_out, min_pct, objetivo_pct, alto_pct):
        pct, estado, icono, color = estado_tanque(volumen, capacidad, min_pct, objetivo_pct, alto_pct)
        q_neto = q_in - q_out
        tendencia, tiempo_limite, _ = tiempo_a_limite(volumen, capacidad, q_neto, min_pct, alto_pct)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"{nombre} · nivel", f"{nivel:.2f} m", f"{pct:.1f}%")
        c2.metric("Volumen calculado", f"{volumen:,.2f} m³")
        c3.metric("Balance", f"{q_neto:+.2f} L/s", f"{q_to_m3h(q_neto):+.2f} m³/h")
        c4.metric("Tendencia", tendencia, tiempo_limite)
        st.markdown(f"<div class='mini-note'><b>Estado:</b> <span style='color:{color};font-weight:900'>{icono} {estado}</span>. Entrada {q_in:.2f} L/s · salida {q_out:.2f} L/s.</div>", unsafe_allow_html=True)

    def input_salidas(nombre_base, opciones, total_default, key_base, titulo="Modo de salida"):
        """Permite usar salida total o desglosada por ramales."""
        modo = st.radio(
            titulo,
            ["Usar salida total", "Desglosar por salidas"],
            horizontal=True,
            key=f"{key_base}_modo_salida",
        )
        valores = {}
        if modo == "Usar salida total":
            total = st.number_input(
                f"Salida total {nombre_base} (L/s)",
                min_value=0.0,
                value=float(total_default),
                step=1.0,
                format="%.2f",
                key=f"{key_base}_salida_total",
            )
            valores["Salida total"] = total
            return total, valores, modo
        cols = st.columns(min(4, max(1, len(opciones))))
        total = 0.0
        for i, (label, default) in enumerate(opciones):
            with cols[i % len(cols)]:
                val = st.number_input(
                    f"{label} (L/s)",
                    min_value=0.0,
                    value=float(default),
                    step=1.0,
                    format="%.2f",
                    key=f"{key_base}_salida_{i}",
                )
            valores[label] = val
            total += val
        st.caption(f"Salida total calculada por ramales: {total:.2f} L/s")
        return total, valores, modo


    def mostrar_tarjetas_formula_entrada(nombre_tanque, capacidad, nivel_max, nivel_actual, nivel_anterior, periodo_min, salida_ls, delta_h, delta_v, q_neto_ls, q_in):
        area = area_equivalente(capacidad, nivel_max)
        periodo_h = max(float(periodo_min) / 60.0, 1/60)
        html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']] }},
  svg: {{ fontCache: 'global' }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<style>
* {{ box-sizing: border-box; }}
body {{
    margin:0;
    padding:0;
    background:transparent;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color:#003A70;
}}
.calc-wrap {{
    background: linear-gradient(135deg, #F7FCFF 0%, #eef7ff 100%);
    border:1px solid #d6e8f7;
    border-left:6px solid #48B9EA;
    border-radius:18px;
    padding:16px 18px;
    box-shadow:0 6px 22px rgba(10,22,40,.06);
}}
.calc-title {{
    color:#005B8E;
    font-size:15px;
    font-weight:850;
    margin-bottom:12px;
}}
.calc-grid {{
    display:grid;
    grid-template-columns:repeat(2, minmax(260px, 1fr));
    gap:12px;
}}
.calc-card {{
    background:#FFFFFF;
    border:1px solid #CFE5F4;
    border-radius:16px;
    padding:13px 14px 11px 14px;
    min-height:132px;
    box-shadow:0 4px 16px rgba(10,22,40,.055);
}}
.calc-card-wide {{ grid-column:1 / -1; min-height:125px; }}
.calc-name {{
    font-size:12px;
    letter-spacing:.35px;
    font-weight:800;
    color:#4E6F8A;
    margin-bottom:6px;
}}
.calc-eq {{
    min-height:50px;
    display:flex;
    align-items:center;
    justify-content:center;
    color:#004A8F;
    overflow-x:auto;
}}
.calc-note {{
    margin-top:7px;
    color:#4E6F8A;
    line-height:1.45;
    font-size:12px;
}}
@media (max-width:760px) {{
    .calc-grid {{ grid-template-columns:1fr; }}
    .calc-card {{ min-height:auto; }}
}}
</style>
</head>
<body>
<div class="calc-wrap">
    <div class="calc-title">📘 Entrada estimada a {nombre_tanque}</div>
    <div class="calc-grid">
        <div class="calc-card">
            <div class="calc-name">1. Área equivalente</div>
            <div class="calc-eq">\\[A=\\frac{{C}}{{h_{{max}}}}=\\frac{{{capacidad:.2f}}}{{{nivel_max:.2f}}}={area:.2f}\\;m^2\\]</div>
            <div class="calc-note">Convierte la capacidad operativa y el nivel máximo en un área hidráulica equivalente.</div>
        </div>
        <div class="calc-card">
            <div class="calc-name">2. Cambio de nivel</div>
            <div class="calc-eq">\\[\\Delta h=h_f-h_i={nivel_actual:.2f}-{nivel_anterior:.2f}={delta_h:+.3f}\\;m\\]</div>
            <div class="calc-note">Si el resultado es positivo, el tanque subió; si es negativo, bajó.</div>
        </div>
        <div class="calc-card">
            <div class="calc-name">3. Cambio de volumen</div>
            <div class="calc-eq">\\[\\Delta V=A\\times\\Delta h={area:.2f}\\times({delta_h:+.3f})={delta_v:+.2f}\\;m^3\\]</div>
            <div class="calc-note">Muestra cuánto cambió el volumen real del tanque entre dos lecturas.</div>
        </div>
        <div class="calc-card">
            <div class="calc-name">4. Caudal neto por nivel</div>
            <div class="calc-eq">\\[Q_{{neto,nivel}}=\\frac{{\\Delta V}}{{3.6\\times\\Delta t_h}}=\\frac{{{delta_v:+.2f}}}{{3.6\\times{periodo_h:.2f}}}={q_neto_ls:+.2f}\\;L/s\\]</div>
            <div class="calc-note">Tiempo usado: {periodo_min:.0f} min = {periodo_h:.2f} h.</div>
        </div>
        <div class="calc-card calc-card-wide">
            <div class="calc-name">5. Entrada estimada</div>
            <div class="calc-eq">\\[Q_{{entrada,est}}=Q_{{salida}}+Q_{{neto,nivel}}={salida_ls:.2f}+({q_neto_ls:+.2f})={q_in:.2f}\\;L/s\\]</div>
            <div class="calc-note">Suma la salida actual más el balance observado para estimar la entrada al tanque.</div>
        </div>
    </div>
</div>
</body>
</html>
"""
        components.html(html, height=500, scrolling=False)

    def mostrar_tarjetas_formula_modulos_4400(q_mod_500, q_mod_150, q_total):
        html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']] }},
  svg: {{ fontCache: 'global' }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<style>
* {{ box-sizing: border-box; }}
body {{
    margin:0;
    padding:0;
    background:transparent;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color:#003A70;
}}
.calc-wrap {{
    background: linear-gradient(135deg, #F7FCFF 0%, #eef7ff 100%);
    border:1px solid #d6e8f7;
    border-left:6px solid #48B9EA;
    border-radius:18px;
    padding:16px 18px;
    box-shadow:0 6px 22px rgba(10,22,40,.06);
}}
.calc-title {{
    color:#005B8E;
    font-size:15px;
    font-weight:850;
    margin-bottom:12px;
}}
.calc-grid {{
    display:grid;
    grid-template-columns:repeat(2, minmax(260px, 1fr));
    gap:12px;
}}
.calc-card {{
    background:#FFFFFF;
    border:1px solid #CFE5F4;
    border-radius:16px;
    padding:13px 14px 11px 14px;
    min-height:132px;
    box-shadow:0 4px 16px rgba(10,22,40,.055);
}}
.calc-card-wide {{ grid-column:1 / -1; min-height:125px; }}
.calc-name {{
    font-size:12px;
    letter-spacing:.35px;
    font-weight:800;
    color:#4E6F8A;
    margin-bottom:6px;
}}
.calc-eq {{
    min-height:54px;
    display:flex;
    align-items:center;
    justify-content:center;
    color:#004A8F;
    overflow-x:auto;
}}
.calc-note {{
    margin-top:7px;
    color:#4E6F8A;
    line-height:1.45;
    font-size:12px;
}}
@media (max-width:760px) {{
    .calc-grid {{ grid-template-columns:1fr; }}
    .calc-card {{ min-height:auto; }}
}}
</style>
</head>
<body>
<div class="calc-wrap">
    <div class="calc-title">📘 Entrada al tanque 4400 por módulos</div>
    <div class="calc-grid">
        <div class="calc-card">
            <div class="calc-name">1. Módulo 500</div>
            <div class="calc-eq">\[Q_{{M500}}={q_mod_500:.2f}\;L/s\]</div>
            <div class="calc-note">Caudal producido por el módulo de 500 antes de unirse con el módulo 150.</div>
        </div>
        <div class="calc-card">
            <div class="calc-name">2. Módulo 150</div>
            <div class="calc-eq">\[Q_{{M150}}={q_mod_150:.2f}\;L/s\]</div>
            <div class="calc-note">Caudal producido por el módulo de 150 antes de unirse con el módulo 500.</div>
        </div>
        <div class="calc-card calc-card-wide">
            <div class="calc-name">3. Entrada total al tanque 4400</div>
            <div class="calc-eq">\[Q_{{entrada,4400}}=Q_{{M500}}+Q_{{M150}}={q_mod_500:.2f}+{q_mod_150:.2f}={q_total:.2f}\;L/s\]</div>
            <div class="calc-note">El agua producida por ambos módulos se une en una sola conducción antes de alimentar el tanque 4400 m³.</div>
        </div>
    </div>
</div>
</body>
</html>
"""
        components.html(html, height=360, scrolling=False)

    def input_entrada(nombre_tanque, key_base, q_macro_default, nivel_actual, capacidad, nivel_max, salida_ls, forzar_estimacion=False, permitir_modulos=False):
        """Entrada por macromedidor, estimada con diferencia de nivel o, para Diviso 4400, desglosada por módulos."""
        opciones = ["Tengo macromedidor / dato de entrada", "Estimar por diferencia de nivel"]
        if permitir_modulos:
            opciones.append("Desglosar módulos 500 + 150")
        idx = 1 if forzar_estimacion else 0
        modo = st.radio(
            f"Entrada a {nombre_tanque}",
            opciones,
            index=idx,
            horizontal=True,
            key=f"{key_base}_modo_entrada",
        )
        if modo == "Tengo macromedidor / dato de entrada":
            q_in = st.number_input(
                f"Entrada medida a {nombre_tanque} (L/s)",
                min_value=0.0,
                value=float(q_macro_default),
                step=1.0,
                format="%.2f",
                key=f"{key_base}_q_entrada_macro",
            )
            return q_in, {"Modo entrada": "Macromedidor", "Q entrada (L/s)": q_in}

        if modo == "Desglosar módulos 500 + 150":
            c1, c2 = st.columns(2)
            with c1:
                q_mod_500 = st.number_input(
                    "Producción módulo 500 (L/s)",
                    min_value=0.0,
                    value=350.0,
                    step=1.0,
                    format="%.2f",
                    key=f"{key_base}_q_mod_500_entrada",
                )
            with c2:
                q_mod_150 = st.number_input(
                    "Producción módulo 150 (L/s)",
                    min_value=0.0,
                    value=120.0,
                    step=1.0,
                    format="%.2f",
                    key=f"{key_base}_q_mod_150_entrada",
                )
            q_in = q_mod_500 + q_mod_150
            mostrar_tarjetas_formula_modulos_4400(q_mod_500, q_mod_150, q_in)
            return q_in, {
                "Modo entrada": "Módulos 500 + 150",
                "Módulo 500 (L/s)": q_mod_500,
                "Módulo 150 (L/s)": q_mod_150,
                "Q entrada (L/s)": q_in,
            }

        c1, c2 = st.columns(2)
        with c1:
            nivel_anterior = st.number_input(
                f"Nivel anterior {nombre_tanque} (m)",
                min_value=0.0,
                max_value=max(float(nivel_max) * 1.3, 1.0),
                value=max(0.0, float(nivel_actual) - 0.05),
                step=0.01,
                format="%.2f",
                key=f"{key_base}_nivel_anterior",
            )
        with c2:
            periodo_min = st.number_input(
                "Tiempo entre lecturas (min)",
                min_value=1.0,
                value=60.0,
                step=5.0,
                format="%.0f",
                key=f"{key_base}_periodo_min",
            )
        q_in, delta_h, delta_v, q_neto_ls = estimar_entrada_desde_nivel(
            nivel_actual, nivel_anterior, capacidad, nivel_max, periodo_min, salida_ls
        )
        mostrar_tarjetas_formula_entrada(
            nombre_tanque=nombre_tanque,
            capacidad=capacidad,
            nivel_max=nivel_max,
            nivel_actual=nivel_actual,
            nivel_anterior=nivel_anterior,
            periodo_min=periodo_min,
            salida_ls=salida_ls,
            delta_h=delta_h,
            delta_v=delta_v,
            q_neto_ls=q_neto_ls,
            q_in=q_in,
        )
        return q_in, {
            "Modo entrada": "Estimación por nivel",
            "Nivel anterior (m)": nivel_anterior,
            "Tiempo entre lecturas (min)": periodo_min,
            "Δh (m)": delta_h,
            "ΔV (m³)": delta_v,
            "Q neto por nivel (L/s)": q_neto_ls,
            "Q entrada (L/s)": q_in,
        }

    def accion_por_ajuste(delta, margen):
        if delta > margen:
            return "Abrir / aumentar"
        if delta < -margen:
            return "Cerrar / reducir"
        return "Mantener"

    def tabla_salida_detallada(diccionario):
        if not diccionario:
            return pd.DataFrame()
        return pd.DataFrame([{"Salida": k, "Caudal (L/s)": v} for k, v in diccionario.items()])

    def plot_volumenes(df_eval, titulo):
        if df_eval.empty:
            return
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Volumen calculado",
            x=df_eval["Tanque"],
            y=df_eval["Volumen calculado (m³)"],
            text=[f"{v:,.0f}" for v in df_eval["Volumen calculado (m³)"]],
            textposition="auto",
        ))
        fig.add_trace(go.Bar(
            name="Capacidad",
            x=df_eval["Tanque"],
            y=df_eval["Capacidad (m³)"],
            opacity=0.35,
        ))
        fig.update_layout(
            title=titulo,
            barmode="overlay",
            height=360,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=55, b=40),
            yaxis_title="m³",
            legend=dict(orientation="h", y=1.10, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────
    # Criterios generales
    # ─────────────────────────────────────────────────────────────────────
    planta_login = st.session_state.get("planta_usuario", "Diviso")
    tab_diviso, tab_caldas, tab_formulas = st.tabs(["Diviso", "Caldas", "Fórmulas usadas"])

    with st.expander("⚙️ Criterios generales de decisión", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            horizonte_h = st.number_input("Horizonte de análisis (horas)", min_value=0.25, value=6.0, step=0.5, format="%.2f", key="sish2_horizonte")
        with c2:
            min_pct = st.number_input("Mínimo operativo (%)", min_value=1.0, max_value=80.0, value=30.0, step=1.0, key="sish2_min_pct")
        with c3:
            objetivo_pct = st.number_input("Nivel objetivo (%)", min_value=10.0, max_value=95.0, value=70.0, step=1.0, key="sish2_obj_pct")
        with c4:
            alto_pct = st.number_input("Alto / rebose operativo (%)", min_value=50.0, max_value=100.0, value=90.0, step=1.0, key="sish2_alto_pct")
        margen_ls = st.number_input("Margen para decidir abrir/cerrar (L/s)", min_value=0.0, value=5.0, step=1.0, key="sish2_margen")
        st.caption("El margen evita recomendar maniobras por diferencias pequeñas o ruido de lectura.")

    # ─────────────────────────────────────────────────────────────────────
    # DIVISO
    # ─────────────────────────────────────────────────────────────────────
    with tab_diviso:
        st.markdown("<div class='titulo-seccion-resultado'>PTAP Diviso · tanques independientes y línea única Cunduy-Malvinas</div>", unsafe_allow_html=True)

        with st.expander("⚙️ Geometría Diviso, Cunduy y Malvinas", expanded=False):
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                cap_4400 = st.number_input("Capacidad tanque Diviso 4400 (m³)", min_value=1.0, value=4400.0, step=10.0, format="%.2f", key="sish2_cap_4400")
                nmax_4400 = st.number_input("Nivel máximo 4400 (m)", min_value=0.10, value=5.67, step=0.01, format="%.2f", key="sish2_nmax_4400")
            with g2:
                cap_1100 = st.number_input("Capacidad tanque Diviso 1100 (m³)", min_value=1.0, value=1100.0, step=10.0, format="%.2f", key="sish2_cap_1100")
                nmax_1100 = st.number_input("Nivel máximo 1100 (m)", min_value=0.10, value=4.02, step=0.01, format="%.2f", key="sish2_nmax_1100")
            with g3:
                cap_cunduy = st.number_input("Capacidad operativa Cunduy (m³)", min_value=1.0, value=3000.0, step=10.0, format="%.2f", key="sish2_cap_cunduy")
                nmax_cunduy = st.number_input("Nivel máximo Cunduy (m)", min_value=0.10, value=3.93, step=0.01, format="%.2f", key="sish2_nmax_cunduy")
            with g4:
                cap_malvinas = st.number_input("Capacidad operativa Malvinas (m³)", min_value=1.0, value=4000.0, step=10.0, format="%.2f", key="sish2_cap_malvinas")
                nmax_malvinas = st.number_input("Nivel máximo Malvinas (m)", min_value=0.10, value=3.73, step=0.01, format="%.2f", key="sish2_nmax_malvinas")
            st.caption("Si después tienes la tabla real nivel-volumen de cada tanque, se puede reemplazar esta aproximación lineal por una curva de calibración más precisa.")

        selector = st.multiselect(
            "Tanques/destinos a incluir en el cálculo de Diviso",
            ["Tanque 1100", "Tanque Cunduy", "Tanque Malvinas"],
            default=["Tanque 1100", "Tanque Cunduy", "Tanque Malvinas"],
            key="sish2_destinos_diviso",
            help="Puedes desmarcar un tanque si en ese momento no lo quieres incluir en la recomendación.",
        )
        incluir_1100 = "Tanque 1100" in selector
        incluir_cunduy = "Tanque Cunduy" in selector
        incluir_malvinas = "Tanque Malvinas" in selector

        # ── Tanque 4400 ─────────────────────────────────────────────────
        card_inicio(
            "Tanque Diviso 4400 m³",
            "Recibe una sola entrada de agua producida por los módulos 500 y 150 ya unidos antes del tanque. "
            "La entrada puede registrarse con macromedidor total, estimarse por diferencia de nivel o desglosarse como suma de los módulos 500 y 150. "
            "Sus salidas principales son: línea Cunduy-Malvinas, Línea de Occidente, transferencia al tanque 1100 m³ y otras si existen."
        )
        t1, t2 = st.columns([1, 1.15], gap="large")
        with t1:
            nivel_4400 = st.number_input(
                "Nivel actual 4400 (m)",
                min_value=0.0,
                max_value=max(nmax_4400 * 1.3, 1.0),
                value=3.52,
                step=0.01,
                format="%.2f",
                key="sish2_nivel_4400",
            )
            vol_4400 = volumen_por_nivel(nivel_4400, nmax_4400, cap_4400)
            st.caption(f"Volumen calculado: {vol_4400:,.2f} m³ · {pct_tanque(vol_4400, cap_4400):.1f}%")
            st.markdown(
                "<div class='mini-note'><b>Entrada del 4400:</b> usa el macromedidor de entrada total al tanque. "
                "Si ese macro no está disponible, selecciona estimación por diferencia de nivel. En ese caso la app usa: "
                "salidas del 4400 + cambio de volumen observado.</div>",
                unsafe_allow_html=True,
            )
        with t2:
            salidas_4400_default = [
                ("Línea Cunduy-Malvinas", 295.14 if (incluir_cunduy or incluir_malvinas) else 0.00),
                ("Línea de Occidente", 21.29),
                ("Otras salidas 4400", 0.00),
            ]
            q_salida_4400_base, det_salidas_4400, modo_salida_4400 = input_salidas(
                "tanque 4400",
                salidas_4400_default,
                312.43,
                "sish2_4400",
                "Salidas del tanque 4400",
            )
            linea_cm_definida = False
            if incluir_cunduy or incluir_malvinas:
                if modo_salida_4400 == "Desglosar por salidas":
                    q_linea_cunduy_malvinas = det_salidas_4400.get("Línea Cunduy-Malvinas", 0.0)
                    linea_cm_definida = True
                    st.caption(
                        f"Línea Cunduy-Malvinas considerada como una sola conducción: {q_linea_cunduy_malvinas:.2f} L/s. "
                        "Luego se reparte en la T: entrada a Cunduy + caudal que continúa hacia Malvinas."
                    )
                    st.markdown(
                        "<div class='mini-note'><b>Salida 4400 → 1100:</b> no se digita aquí. "
                        "Se toma automáticamente de la entrada calculada o medida del tanque 1100. "
                        "Así evitas escribir un dato que no conoces y el balance queda consistente.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    q_linea_cunduy_malvinas = 0.0
                    st.caption(
                        "En modo salida total, el valor del tanque 4400 representa toda la salida del tanque, "
                        "incluida la transferencia al 1100, la línea Cunduy-Malvinas y las demás salidas. "
                        "Por eso no se suma aparte la entrada del 1100 para el balance del 4400."
                    )
            else:
                q_linea_cunduy_malvinas = 0.0
        card_fin()

        # Variables base antes de evaluar los destinos
        q_hacia_1100 = 0.0
        q_entrada_cunduy = 0.0
        q_derivacion_cunduy_no_eval = 0.0
        q_continua_malvinas = q_linea_cunduy_malvinas if incluir_malvinas else 0.0
        reqs_destinos = []
        filas_destinos = []

        # ── Tanque 1100 ─────────────────────────────────────────────────
        if incluir_1100:
            card_inicio(
                "Tanque Diviso 1100 m³",
                "Este tanque es alimentado por el tanque 4400. Sus salidas principales son Comuna Oriental, La Paz, Álamos, Altos de Colinas, Sebastopol y otro. "
                "La entrada puede tomarse por macromedidor, si algún día existe, o estimarse matemáticamente con diferencia de nivel."
            )
            c1, c2 = st.columns([1, 1.15], gap="large")
            with c1:
                nivel_1100 = st.number_input(
                    "Nivel actual 1100 (m)",
                    min_value=0.0,
                    max_value=max(nmax_1100 * 1.3, 1.0),
                    value=3.81,
                    step=0.01,
                    format="%.2f",
                    key="sish2_nivel_1100",
                )
                vol_1100 = volumen_por_nivel(nivel_1100, nmax_1100, cap_1100)
                st.caption(f"Volumen calculado: {vol_1100:,.2f} m³ · {pct_tanque(vol_1100, cap_1100):.1f}%")
                st.markdown(
                    "<div class='mini-note'><b>Entrada 4400 → 1100:</b> si no tienes macromedidor, usa la opción "
                    "<b>Estimar por diferencia de nivel</b>. La app calcula la entrada con el cambio de nivel, el tiempo entre lecturas y las salidas del 1100.</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                q_salida_1100, det_salidas_1100, modo_salida_1100 = input_salidas(
                    "tanque 1100",
                    [
                        ("Comuna Oriental", 0.0),
                        ("La Paz", 0.0),
                        ("Álamos", 0.0),
                        ("Altos de Colinas", 0.0),
                        ("Sebastopol", 0.0),
                        ("Otro", 0.0),
                    ],
                    0.0,
                    "sish2_1100",
                    "Salidas del tanque 1100",
                )

            q_in_1100, est_1100 = input_entrada(
                "tanque 1100 desde tanque 4400",
                "sish3_1100_entrada",
                35.0,
                nivel_1100,
                cap_1100,
                nmax_1100,
                q_salida_1100,
                forzar_estimacion=False,
            )
            q_hacia_1100 = q_in_1100
            st.markdown(
                f"<div class='mini-note'><b>Identidad hidráulica obligatoria:</b> "
                f"Q<sub>4400→1100</sub> = Q<sub>entrada,1100</sub> = {q_hacia_1100:.2f} L/s. "
                "El tanque 1100 no tiene otra entrada en este modelo.</div>",
                unsafe_allow_html=True,
            )

            if modo_salida_4400 == "Desglosar por salidas":
                st.markdown(
                    f"<div class='mini-note'><b>Transferencia automática 4400 → 1100:</b> la app usará {q_hacia_1100:.2f} L/s "
                    "como salida del tanque 4400 hacia el tanque 1100. Ese valor viene de la entrada medida o estimada del 1100.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='mini-note'><b>Entrada usada para el 1100:</b> {q_hacia_1100:.2f} L/s. "
                    "Como el tanque 4400 está en modo salida total, este valor se usa para el balance del 1100, "
                    "pero no se suma de nuevo a la salida total del 4400 para evitar doble conteo.</div>",
                    unsafe_allow_html=True,
                )

            mostrar_resumen_tanque("1100", nivel_1100, vol_1100, cap_1100, q_in_1100, q_salida_1100, min_pct, objetivo_pct, alto_pct)
            req_1100 = requerimiento_entrada(vol_1100, cap_1100, q_salida_1100, horizonte_h, objetivo_pct, alto_pct)
            reqs_destinos.append({
                "Destino": "Tanque 1100",
                "Entrada actual (L/s)": q_in_1100,
                "Entrada requerida (L/s)": req_1100,
                "Máximo sugerido (L/s)": max(req_1100, q_in_1100, 80.0),
            })
            filas_destinos.append(evaluar_tanque("Diviso 1100", nivel_1100, cap_1100, nmax_1100, q_in_1100, q_salida_1100, min_pct, objetivo_pct, alto_pct))
            card_fin()
        else:
            nivel_1100 = 0.0
            vol_1100 = 0.0
            q_salida_1100 = 0.0
            q_in_1100 = 0.0

        # ── Balance final del tanque 4400 ────────────────────────────────
        if modo_salida_4400 == "Desglosar por salidas":
            q_salida_4400 = q_salida_4400_base + (q_hacia_1100 if incluir_1100 else 0.0)
            det_salidas_4400["Transferencia automática 4400 → 1100"] = q_hacia_1100 if incluir_1100 else 0.0
            st.markdown("<div class='titulo-seccion-resultado'>Balance final del tanque 4400 m³</div>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            b1.metric("Salidas directas 4400", f"{q_salida_4400_base:.2f} L/s")
            b2.metric("Salida 4400 → 1100", f"{q_hacia_1100:.2f} L/s")
            b3.metric("Salida total 4400", f"{q_salida_4400:.2f} L/s")
            st.markdown(
                "<div class='mini-note'><b>Cálculo:</b> salida total 4400 = línea Cunduy-Malvinas + Línea de Occidente + otras salidas directas "
                "+ transferencia 4400 → 1100. La transferencia al 1100 es exactamente la entrada medida o estimada del tanque 1100.</div>",
                unsafe_allow_html=True,
            )
        else:
            q_salida_4400 = q_salida_4400_base
            st.markdown("<div class='titulo-seccion-resultado'>Balance final del tanque 4400 m³</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='mini-note'><b>Modo salida total:</b> se usa {q_salida_4400:.2f} L/s como salida total del 4400. "
                "Este valor ya debe incluir la transferencia al 1100, Cunduy-Malvinas, Línea de Occidente y otras salidas.</div>",
                unsafe_allow_html=True,
            )

        q_in_4400, est_4400 = input_entrada(
            "tanque 4400",
            "sish3_4400_entrada",
            470.20,
            nivel_4400,
            cap_4400,
            nmax_4400,
            q_salida_4400,
            permitir_modulos=True,
        )
        mostrar_resumen_tanque("4400", nivel_4400, vol_4400, cap_4400, q_in_4400, q_salida_4400, min_pct, objetivo_pct, alto_pct)

        # ── Coherencia hidráulica exacta 4400 → 1100 ─────────────────
        # La transferencia al 1100 se cuenta una sola vez: es salida del 4400 y entrada del 1100.
        # Que la salida total supere la entrada es posible únicamente si el tanque aporta almacenamiento.
        q_almacenamiento_calculado_4400 = q_in_4400 - q_salida_4400
        q_transferencia_estable = max(0.0, q_in_4400 - q_salida_4400_base)
        area_4400 = area_equivalente(cap_4400, nmax_4400)
        cambio_altura_teorico_m_h = safe_div(q_almacenamiento_calculado_4400 * 3.6, area_4400, 0.0)

        st.markdown("<div class='titulo-seccion-resultado'>Coherencia matemática del sistema 4400 → 1100</div>", unsafe_allow_html=True)
        cco1, cco2, cco3, cco4 = st.columns(4)
        cco1.metric("Entrada al 4400", f"{q_in_4400:.2f} L/s")
        cco2.metric("Salida total del 4400", f"{q_salida_4400:.2f} L/s", f"{q_salida_4400-q_in_4400:+.2f} L/s")
        cco3.metric("Transferencia 4400 → 1100", f"{q_hacia_1100:.2f} L/s")
        cco4.metric("Transferencia estable al 1100", f"{q_transferencia_estable:.2f} L/s")

        if q_almacenamiento_calculado_4400 < -max(margen_ls, 0.5):
            st.warning(
                f"Las salidas superan la entrada en {abs(q_almacenamiento_calculado_4400):.2f} L/s. "
                f"Eso exige que el tanque 4400 entregue {abs(q_almacenamiento_calculado_4400)*3.6:.2f} m³/h de su volumen almacenado. "
                f"Con la geometría lineal configurada, el nivel debería bajar aproximadamente {abs(cambio_altura_teorico_m_h):.3f} m/h. "
                "El resultado solo es coherente si el nivel realmente disminuye a una velocidad semejante."
            )
        elif q_almacenamiento_calculado_4400 > max(margen_ls, 0.5):
            st.success(
                f"El tanque 4400 está almacenando aproximadamente {q_almacenamiento_calculado_4400:.2f} L/s "
                f"({q_almacenamiento_calculado_4400*3.6:.2f} m³/h)."
            )
        else:
            st.info("La entrada y la salida total del tanque 4400 están casi equilibradas.")

        with st.expander("Validar el balance con niveles del mismo periodo", expanded=True):
            st.markdown(
                "Ingresa los niveles iniciales medidos antes del intervalo. Los niveles actuales mostrados arriba se toman como niveles finales. "
                "Todos los caudales deben corresponder al mismo periodo.",
                unsafe_allow_html=True,
            )
            vb1, vb2, vb3 = st.columns(3)
            with vb1:
                periodo_validacion_min = st.number_input(
                    "Tiempo entre nivel inicial y final (min)",
                    min_value=1.0,
                    value=60.0,
                    step=5.0,
                    format="%.0f",
                    key="sish_validacion_periodo",
                )
            with vb2:
                nivel_inicial_4400 = st.number_input(
                    "Nivel inicial 4400 (m)",
                    min_value=0.0,
                    max_value=max(nmax_4400 * 1.3, 1.0),
                    value=max(0.0, nivel_4400 + 0.05),
                    step=0.01,
                    format="%.2f",
                    key="sish_validacion_nivel_4400",
                )
            with vb3:
                if incluir_1100:
                    nivel_inicial_1100 = st.number_input(
                        "Nivel inicial 1100 (m)",
                        min_value=0.0,
                        max_value=max(nmax_1100 * 1.3, 1.0),
                        value=float(nivel_1100),
                        step=0.01,
                        format="%.2f",
                        key="sish_validacion_nivel_1100",
                    )
                else:
                    nivel_inicial_1100 = 0.0

            cierre_4400 = error_cierre_balance(
                q_in_4400,
                q_salida_4400,
                nivel_4400,
                nivel_inicial_4400,
                cap_4400,
                nmax_4400,
                periodo_validacion_min,
            )

            if incluir_1100:
                cierre_1100 = error_cierre_balance(
                    q_hacia_1100,
                    q_salida_1100,
                    nivel_1100,
                    nivel_inicial_1100,
                    cap_1100,
                    nmax_1100,
                    periodo_validacion_min,
                )
            else:
                cierre_1100 = {
                    "delta_h_m": 0.0,
                    "delta_v_m3": 0.0,
                    "q_almacenamiento_ls": 0.0,
                    "error_ls": 0.0,
                }

            # Salidas externas del 4400: no incluyen la transferencia interna al 1100.
            if modo_salida_4400 == "Desglosar por salidas":
                q_externas_4400 = q_salida_4400_base
            else:
                q_externas_4400 = max(
                    0.0,
                    q_salida_4400 - (q_hacia_1100 if incluir_1100 else 0.0),
                )

            q_salidas_externas_sistema = q_externas_4400 + (q_salida_1100 if incluir_1100 else 0.0)
            q_almacenamiento_sistema = (
                cierre_4400["q_almacenamiento_ls"]
                + cierre_1100["q_almacenamiento_ls"]
            )
            error_sistema = (
                q_in_4400
                - q_salidas_externas_sistema
                - q_almacenamiento_sistema
            )

            rv1, rv2, rv3, rv4 = st.columns(4)
            rv1.metric("Almacenamiento observado 4400", f"{cierre_4400['q_almacenamiento_ls']:+.2f} L/s")
            rv2.metric("Error de cierre 4400", f"{cierre_4400['error_ls']:+.2f} L/s")
            rv3.metric(
                "Error de cierre 1100",
                f"{cierre_1100['error_ls']:+.2f} L/s" if incluir_1100 else "No incluido",
            )
            rv4.metric("Error conjunto 4400 + 1100", f"{error_sistema:+.2f} L/s")

            st.latex(
                r"\varepsilon_{4400}=Q_{entrada,4400}-Q_{salida,4400}-\frac{V_{f,4400}-V_{i,4400}}{3.6\,\Delta t_h}"
            )
            if incluir_1100:
                st.latex(
                    r"\varepsilon_{1100}=Q_{4400\rightarrow1100}-Q_{salida,1100}-\frac{V_{f,1100}-V_{i,1100}}{3.6\,\Delta t_h}"
                )
                st.latex(
                    r"Q_{entrada,4400}-\left(Q_{ext,4400}+Q_{salida,1100}\right)=Q_{alm,4400}+Q_{alm,1100}"
                )

            tolerancia_cierre = max(float(margen_ls), 5.0)
            errores_individuales = [abs(cierre_4400["error_ls"])]
            if incluir_1100:
                errores_individuales.append(abs(cierre_1100["error_ls"]))

            if abs(error_sistema) <= tolerancia_cierre and max(errores_individuales) <= tolerancia_cierre:
                st.success(
                    f"Balance consistente dentro de ±{tolerancia_cierre:.2f} L/s. "
                    "La transferencia 4400 → 1100 fue contada una sola vez y se cancela en el balance conjunto."
                )
            elif abs(error_sistema) <= tolerancia_cierre * 2:
                st.warning(
                    "El balance presenta una diferencia moderada. Revisa que todos los niveles y caudales sean del mismo intervalo, "
                    "que no falte una salida y que los macromedidores tengan la misma hora de lectura."
                )
            else:
                st.error(
                    "Los datos no cierran matemáticamente. Revisa doble conteo, salidas faltantes, horarios diferentes, "
                    "lecturas de nivel, macromedidores o la geometría nivel-volumen utilizada."
                )

            tabla_cierre = pd.DataFrame([
                {
                    "Elemento": "Tanque 4400",
                    "Entrada (L/s)": q_in_4400,
                    "Salida (L/s)": q_salida_4400,
                    "Almacenamiento observado (L/s)": cierre_4400["q_almacenamiento_ls"],
                    "Error de cierre (L/s)": cierre_4400["error_ls"],
                },
                *([{
                    "Elemento": "Tanque 1100",
                    "Entrada (L/s)": q_hacia_1100,
                    "Salida (L/s)": q_salida_1100,
                    "Almacenamiento observado (L/s)": cierre_1100["q_almacenamiento_ls"],
                    "Error de cierre (L/s)": cierre_1100["error_ls"],
                }] if incluir_1100 else []),
                {
                    "Elemento": "Sistema conjunto",
                    "Entrada (L/s)": q_in_4400,
                    "Salida externa (L/s)": q_salidas_externas_sistema,
                    "Almacenamiento observado (L/s)": q_almacenamiento_sistema,
                    "Error de cierre (L/s)": error_sistema,
                },
            ])
            st.dataframe(tabla_cierre.round(2), use_container_width=True, hide_index=True)

        filas_eval = [
            evaluar_tanque(
                "Diviso 4400",
                nivel_4400,
                cap_4400,
                nmax_4400,
                q_in_4400,
                q_salida_4400,
                min_pct,
                objetivo_pct,
                alto_pct,
            )
        ] + filas_destinos

        # ── Cunduy ───────────────────────────────────────────────────────
        if incluir_cunduy:
            card_inicio("Tanque Cunduy", "Destino alimentado desde la conducción de Diviso. Si no hay macro de entrada, se estima con cambio de nivel.")
            c1, c2 = st.columns([1, 1.15], gap="large")
            with c1:
                nivel_cunduy = st.number_input("Nivel actual Cunduy (m)", min_value=0.0, max_value=max(nmax_cunduy * 1.3, 1.0), value=2.81, step=0.01, format="%.2f", key="sish2_nivel_cunduy")
                vol_cunduy = volumen_por_nivel(nivel_cunduy, nmax_cunduy, cap_cunduy)
                st.caption(f"Volumen calculado: {vol_cunduy:,.2f} m³ · {pct_tanque(vol_cunduy, cap_cunduy):.1f}%")
            with c2:
                q_salida_cunduy, det_salidas_cunduy, modo_salida_cunduy = input_salidas(
                    "Cunduy",
                    [("Salida principal Cunduy", 130.22), ("Torasso / sector asociado", 0.0), ("Otras salidas", 0.0)],
                    130.22,
                    "sish2_cunduy",
                    "Salidas de Cunduy",
                )
            q_default_cunduy = min(q_linea_cunduy_malvinas, 111.36) if linea_cm_definida and q_linea_cunduy_malvinas > 0 else 111.36
            q_in_cunduy, est_cunduy = input_entrada("Cunduy", "sish2_cunduy", q_default_cunduy, nivel_cunduy, cap_cunduy, nmax_cunduy, q_salida_cunduy)
            q_entrada_cunduy = q_in_cunduy
            if incluir_malvinas and linea_cm_definida:
                q_continua_malvinas = max(0.0, q_linea_cunduy_malvinas - q_entrada_cunduy)
            elif incluir_malvinas:
                # En modo salida total no se conoce el caudal específico de la línea desde el 4400.
                # Este valor solo queda como referencia inicial para la entrada medida/estimada de Malvinas.
                q_continua_malvinas = 183.78
            else:
                q_continua_malvinas = 0.0
            mostrar_resumen_tanque("Cunduy", nivel_cunduy, vol_cunduy, cap_cunduy, q_in_cunduy, q_salida_cunduy, min_pct, objetivo_pct, alto_pct)
            if linea_cm_definida:
                st.markdown(
                    f"<div class='mini-note'><b>T de Cunduy:</b> línea Cunduy-Malvinas = {q_linea_cunduy_malvinas:.2f} L/s · "
                    f"entrada a Cunduy = {q_entrada_cunduy:.2f} L/s · "
                    f"caudal que continúa hacia Malvinas = {q_continua_malvinas:.2f} L/s.</div>",
                    unsafe_allow_html=True,
                )
                if q_entrada_cunduy > q_linea_cunduy_malvinas + 0.5 and q_linea_cunduy_malvinas > 0:
                    st.warning("La entrada calculada/registrada a Cunduy es mayor que el caudal total de la línea Cunduy-Malvinas. Revisa si las lecturas corresponden al mismo periodo o si falta otro aporte.")
            else:
                st.markdown(
                    "<div class='mini-note'><b>Modo salida total del 4400:</b> la salida total ya incluye la línea Cunduy-Malvinas. "
                    "Por eso Cunduy se analiza con su propia entrada medida o estimada por diferencia de nivel, sin pedir un caudal adicional de la línea.</div>",
                    unsafe_allow_html=True,
                )
            req_cunduy = requerimiento_entrada(vol_cunduy, cap_cunduy, q_salida_cunduy, horizonte_h, objetivo_pct, alto_pct)
            max_cunduy = st.number_input("Máximo recomendado de entrada a Cunduy (L/s)", min_value=0.0, value=220.0, step=5.0, format="%.2f", key="sish2_qmax_cunduy")
            reqs_destinos.append({"Destino": "Cunduy", "Entrada actual (L/s)": q_in_cunduy, "Entrada requerida (L/s)": req_cunduy, "Máximo sugerido (L/s)": max_cunduy})
            filas_eval.append(evaluar_tanque("Cunduy", nivel_cunduy, cap_cunduy, nmax_cunduy, q_in_cunduy, q_salida_cunduy, min_pct, objetivo_pct, alto_pct))
            card_fin()

        # Si Malvinas se evalúa pero Cunduy no, solo se descuenta la T cuando la línea fue desglosada.
        if incluir_malvinas and not incluir_cunduy:
            if linea_cm_definida:
                st.markdown("<div class='titulo-seccion-resultado'>T de Cunduy en la línea hacia Malvinas</div>", unsafe_allow_html=True)
                q_derivacion_cunduy_no_eval = st.number_input(
                    "Entrada o derivación a Cunduy, sin evaluar el tanque Cunduy (L/s)",
                    min_value=0.0,
                    max_value=max(float(q_linea_cunduy_malvinas), 1.0),
                    value=min(float(q_linea_cunduy_malvinas), 111.36),
                    step=1.0,
                    format="%.2f",
                    key="sish2_derivacion_cunduy_no_eval",
                    help="Aunque no evalúes el tanque Cunduy, si la línea pasa por la T debes descontar lo que entra a Cunduy para estimar lo que continúa a Malvinas.",
                )
                q_continua_malvinas = max(0.0, q_linea_cunduy_malvinas - q_derivacion_cunduy_no_eval)
                st.caption(f"Caudal que continúa hacia Malvinas = {q_linea_cunduy_malvinas:.2f} - {q_derivacion_cunduy_no_eval:.2f} = {q_continua_malvinas:.2f} L/s")
            else:
                q_derivacion_cunduy_no_eval = 0.0
                q_continua_malvinas = 183.78
                st.info("Como estás usando salida total del tanque 4400, no se separa la línea Cunduy-Malvinas. Malvinas se analizará con su propia entrada medida o estimada por diferencia de nivel.")

        # ── Malvinas ─────────────────────────────────────────────────────
        if incluir_malvinas:
            card_inicio("Tanque Malvinas", "Destino alimentado por el caudal que continúa después de la T de Cunduy. Puedes usar salida total o ramales.")
            c1, c2 = st.columns([1, 1.15], gap="large")
            with c1:
                nivel_malvinas = st.number_input("Nivel actual Malvinas (m)", min_value=0.0, max_value=max(nmax_malvinas * 1.3, 1.0), value=1.61, step=0.01, format="%.2f", key="sish2_nivel_malvinas")
                vol_malvinas = volumen_por_nivel(nivel_malvinas, nmax_malvinas, cap_malvinas)
                st.caption(f"Volumen calculado: {vol_malvinas:,.2f} m³ · {pct_tanque(vol_malvinas, cap_malvinas):.1f}%")
            with c2:
                q_salida_malvinas, det_salidas_malvinas, modo_salida_malvinas = input_salidas(
                    "Malvinas",
                    [
                        ("Salida principal Malvinas", 154.19),
                        ("Ángeles", 11.55),
                        ("Comfaca / Villa Susana", 3.22),
                        ("Andes Altos 6''", 8.72),
                        ("Otras salidas", 0.0),
                    ],
                    177.68,
                    "sish2_malvinas",
                    "Salidas de Malvinas",
                )
            q_in_malvinas, est_malvinas = input_entrada("Malvinas", "sish2_malvinas", q_continua_malvinas, nivel_malvinas, cap_malvinas, nmax_malvinas, q_salida_malvinas)
            mostrar_resumen_tanque("Malvinas", nivel_malvinas, vol_malvinas, cap_malvinas, q_in_malvinas, q_salida_malvinas, min_pct, objetivo_pct, alto_pct)
            if linea_cm_definida:
                st.markdown(
                    f"<div class='mini-note'><b>Entrada a Malvinas:</b> se toma como el caudal que continúa después de Cunduy. "
                    f"Línea total = {q_linea_cunduy_malvinas:.2f} L/s · descontado en Cunduy = {(q_entrada_cunduy if incluir_cunduy else q_derivacion_cunduy_no_eval):.2f} L/s · "
                    f"continúa hacia Malvinas = {q_continua_malvinas:.2f} L/s.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='mini-note'><b>Entrada a Malvinas:</b> en modo salida total del 4400 no se separa la línea Cunduy-Malvinas. "
                    f"La entrada de Malvinas se toma del dato que registres o de la estimación por diferencia de nivel. Entrada usada: {q_in_malvinas:.2f} L/s.</div>",
                    unsafe_allow_html=True,
                )
            req_malvinas = requerimiento_entrada(vol_malvinas, cap_malvinas, q_salida_malvinas, horizonte_h, objetivo_pct, alto_pct)
            max_malvinas = st.number_input("Máximo recomendado de entrada a Malvinas (L/s)", min_value=0.0, value=260.0, step=5.0, format="%.2f", key="sish2_qmax_malvinas")
            reqs_destinos.append({"Destino": "Malvinas", "Entrada actual (L/s)": q_in_malvinas, "Entrada requerida (L/s)": req_malvinas, "Máximo sugerido (L/s)": max_malvinas})
            filas_eval.append(evaluar_tanque("Malvinas", nivel_malvinas, cap_malvinas, nmax_malvinas, q_in_malvinas, q_salida_malvinas, min_pct, objetivo_pct, alto_pct))
            card_fin()

        # ── Recomendación Diviso ─────────────────────────────────────────
        st.markdown("<div class='titulo-seccion-resultado'>Resultado integral Diviso</div>", unsafe_allow_html=True)
        df_eval = pd.DataFrame(filas_eval)
        df_public = df_eval.drop(columns=[c for c in ["_horas_limite", "_color"] if c in df_eval.columns])
        mostrar_tabla_profesional(
            df_public,
            formatos={
                "Nivel (m)": "{:.2f}",
                "Volumen calculado (m³)": "{:,.2f}",
                "Capacidad (m³)": "{:,.2f}",
                "% llenado": "{:.1f}%",
                "Entrada (L/s)": "{:.2f}",
                "Salida (L/s)": "{:.2f}",
                "Balance (L/s)": "{:+.2f}",
                "Cambio (m³/h)": "{:+.2f}",
            },
        )

        vol_total_diviso = vol_4400 + (vol_1100 if incluir_1100 else 0.0)
        cap_total_diviso = cap_4400 + (cap_1100 if incluir_1100 else 0.0)
        pct_total_diviso = pct_tanque(vol_total_diviso, cap_total_diviso)
        reserva_diviso_ls = max(0.0, (vol_total_diviso - cap_total_diviso * min_pct / 100.0) / (3.6 * horizonte_h))
        q_limite_conduccion = st.number_input("Límite máximo general de despacho desde Diviso (L/s)", min_value=1.0, value=450.0, step=5.0, format="%.2f", key="sish2_limite_despacho_diviso")
        q_salida_segura_diviso = clamp(q_in_4400 + reserva_diviso_ls, 0.0, q_limite_conduccion)

        rec_df = pd.DataFrame(reqs_destinos)
        if not rec_df.empty:
            rec_df["Entrada recomendada (L/s)"] = rec_df.apply(lambda r: min(r["Entrada requerida (L/s)"], r["Máximo sugerido (L/s)"]), axis=1)
            suma_rec = rec_df["Entrada recomendada (L/s)"].sum()
            if suma_rec > q_salida_segura_diviso and suma_rec > 0:
                factor = q_salida_segura_diviso / suma_rec
                rec_df["Entrada recomendada (L/s)"] = rec_df["Entrada recomendada (L/s)"] * factor
            rec_df["Ajuste recomendado (L/s)"] = rec_df["Entrada recomendada (L/s)"] - rec_df["Entrada actual (L/s)"]
            rec_df["Acción"] = rec_df["Ajuste recomendado (L/s)"].apply(lambda x: accion_por_ajuste(x, margen_ls))
            st.markdown("<div class='titulo-seccion-resultado'>Recomendación por destino seleccionado</div>", unsafe_allow_html=True)
            mostrar_tabla_profesional(
                rec_df,
                formatos={
                    "Entrada actual (L/s)": "{:.2f}",
                    "Entrada requerida (L/s)": "{:.2f}",
                    "Máximo sugerido (L/s)": "{:.2f}",
                    "Entrada recomendada (L/s)": "{:.2f}",
                    "Ajuste recomendado (L/s)": "{:+.2f}",
                },
            )
            ajuste_total = rec_df["Entrada recomendada (L/s)"].sum() - rec_df["Entrada actual (L/s)"].sum()

            rec_cunduy = float(rec_df.loc[rec_df["Destino"] == "Cunduy", "Entrada recomendada (L/s)"].sum()) if "Cunduy" in rec_df["Destino"].values else (q_derivacion_cunduy_no_eval if incluir_malvinas else 0.0)
            rec_malvinas = float(rec_df.loc[rec_df["Destino"] == "Malvinas", "Entrada recomendada (L/s)"].sum()) if "Malvinas" in rec_df["Destino"].values else 0.0
            if incluir_cunduy or incluir_malvinas:
                if linea_cm_definida:
                    q_linea_recomendada = rec_cunduy + rec_malvinas
                    ajuste_linea = q_linea_recomendada - q_linea_cunduy_malvinas
                    st.markdown("<div class='titulo-seccion-resultado'>Resumen de la línea única Cunduy-Malvinas</div>", unsafe_allow_html=True)
                    l1, l2, l3, l4 = st.columns(4)
                    l1.metric("Línea actual", f"{q_linea_cunduy_malvinas:.2f} L/s")
                    l2.metric("Entrada/derivación Cunduy", f"{(q_entrada_cunduy if incluir_cunduy else q_derivacion_cunduy_no_eval):.2f} L/s")
                    l3.metric("Continúa a Malvinas", f"{q_continua_malvinas:.2f} L/s")
                    l4.metric("Ajuste línea", f"{ajuste_linea:+.2f} L/s")
                    st.markdown(
                        "<div class='mini-note'><b>Interpretación:</b> no se suman dos conducciones independientes desde Diviso. "
                        "Desde el 4400 sale una sola línea Cunduy-Malvinas; en la T se descuenta lo que entra a Cunduy y el remanente continúa a Malvinas.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown("<div class='titulo-seccion-resultado'>Lectura en modo salida total 4400</div>", unsafe_allow_html=True)
                    st.markdown(
                        "<div class='mini-note'><b>Salida total:</b> el caudal total del tanque 4400 ya incluye todas las salidas, incluida la línea Cunduy-Malvinas. "
                        "Por eso la app no calcula un ajuste de línea separado en este modo. Para ver el reparto Cunduy/Malvinas desde la conducción, cambia a Desglosar por salidas.</div>",
                        unsafe_allow_html=True,
                    )
        else:
            ajuste_total = 0.0

        if pct_total_diviso <= min_pct:
            decision = "REDUCIR DESPACHO DESDE DIVISO"
            color = "#e63946"
            detalle = f"La reserva total Diviso está en {pct_total_diviso:.1f}%. Evita aumentar salidas hasta recuperar nivel."
        elif ajuste_total > margen_ls:
            decision = "AUMENTAR DESPACHO HACIA DESTINOS SELECCIONADOS"
            color = "#2DB9A3"
            detalle = f"Los destinos seleccionados requieren aproximadamente +{ajuste_total:.2f} L/s, limitado por la salida segura de Diviso ({q_salida_segura_diviso:.2f} L/s)."
        elif ajuste_total < -margen_ls:
            decision = "REDUCIR DESPACHO HACIA ALGÚN DESTINO"
            color = "#e76f51"
            detalle = f"La recomendación total baja {ajuste_total:.2f} L/s frente a lo registrado. Revisa los destinos altos o con riesgo de rebose."
        else:
            decision = "MANTENER Y SEGUIR TENDENCIA"
            color = "#008ACB"
            detalle = "Las diferencias están dentro del margen definido. Mantén seguimiento de niveles, entradas y salidas."

        st.markdown(
            f"<div class='decision-box' style='border-left:7px solid {color}'>"
            f"<div style='font-size:.78rem;color:#4E6F8A;font-weight:900;text-transform:uppercase;letter-spacing:.7px'>Decisión sugerida Diviso</div>"
            f"<div style='font-size:1.35rem;font-weight:900;color:{color};margin:.2rem 0'>{decision}</div>"
            f"<div style='font-size:.95rem;color:#003A70;line-height:1.55'>{detalle}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Reserva total Diviso", f"{vol_total_diviso:,.2f} m³", f"{pct_total_diviso:.1f}%")
        m2.metric("Salida segura Diviso", f"{q_salida_segura_diviso:.2f} L/s")
        m3.metric("Salida actual 4400", f"{q_salida_4400:.2f} L/s")
        m4.metric("Ajuste total destinos", f"{ajuste_total:+.2f} L/s")

        plot_volumenes(df_eval, "Diviso · volumen calculado desde nivel")

        st.markdown("""
        <div class="caja-rango" style="border-left-color:#48B9EA">
        <b>Lógica hidráulica Diviso</b><br>
        Al tanque <b>4400 m³</b> le entra la producción unida de los módulos <b>500</b> y <b>150</b>. Sus salidas principales son la <b>línea hacia el 1100</b>, la <b>línea Cunduy-Malvinas</b>, la <b>Línea de Occidente</b> y otras si existen. El tanque <b>1100 m³</b> es alimentado por el 4400 y sus salidas sectorizadas son Comuna Oriental, La Paz, Álamos, Altos de Colinas, Sebastopol y Otro. La conducción Cunduy-Malvinas sigue siendo una sola línea: en la T una parte entra a Cunduy y el remanente continúa a Malvinas.
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────
    # CALDAS
    # ─────────────────────────────────────────────────────────────────────
    with tab_caldas:
        st.markdown("<div class='titulo-seccion-resultado'>PTAP Caldas · tanque independiente 1365 m³</div>", unsafe_allow_html=True)

        with st.expander("⚙️ Geometría Caldas", expanded=False):
            g1, g2 = st.columns(2)
            with g1:
                cap_caldas = st.number_input("Capacidad tanque Caldas (m³)", min_value=1.0, value=1365.0, step=10.0, format="%.2f", key="sish2_cap_caldas")
            with g2:
                nmax_caldas = st.number_input("Nivel máximo Caldas (m)", min_value=0.10, value=3.59, step=0.01, format="%.2f", key="sish2_nmax_caldas")

        card_inicio("Tanque Caldas", "Caldas no siempre cuenta con macromedidor de entrada al tanque. Por eso se puede estimar la entrada con diferencia de alturas y salidas macromedidas.")
        c1, c2 = st.columns([1, 1.15], gap="large")
        with c1:
            nivel_caldas = st.number_input("Nivel actual Caldas (m)", min_value=0.0, max_value=max(nmax_caldas * 1.3, 1.0), value=2.50, step=0.01, format="%.2f", key="sish2_nivel_caldas")
            vol_caldas = volumen_por_nivel(nivel_caldas, nmax_caldas, cap_caldas)
            st.caption(f"Volumen calculado: {vol_caldas:,.2f} m³ · {pct_tanque(vol_caldas, cap_caldas):.1f}%")
        with c2:
            q_salida_caldas, det_salidas_caldas, modo_salida_caldas = input_salidas(
                "Caldas",
                [
                    ("Centro", 40.0),
                    ("Ciudadela I", 35.0),
                    ("Ciudadela II", 35.0),
                    ("Heliconias", 25.0),
                    ("Acolsure", 25.0),
                    ("Otras salidas", 0.0),
                ],
                160.0,
                "sish2_caldas",
                "Salidas de Caldas",
            )
        q_in_caldas, est_caldas = input_entrada("Caldas", "sish2_caldas", 170.0, nivel_caldas, cap_caldas, nmax_caldas, q_salida_caldas, forzar_estimacion=True)
        mostrar_resumen_tanque("Caldas", nivel_caldas, vol_caldas, cap_caldas, q_in_caldas, q_salida_caldas, min_pct, objetivo_pct, alto_pct)
        card_fin()

        q_limite_salida_caldas = st.number_input("Límite máximo de salida Caldas (L/s)", min_value=1.0, value=230.0, step=5.0, format="%.2f", key="sish2_lim_caldas")
        reserva_caldas_ls = max(0.0, (vol_caldas - cap_caldas * min_pct / 100.0) / (3.6 * horizonte_h))
        q_salida_segura = clamp(q_in_caldas + reserva_caldas_ls, 0.0, q_limite_salida_caldas)
        req_entrada_caldas = requerimiento_entrada(vol_caldas, cap_caldas, q_salida_caldas, horizonte_h, objetivo_pct, alto_pct)
        q_salida_recomendada = q_salida_caldas
        pct_caldas, estado_caldas, icono_caldas, color_caldas = estado_tanque(vol_caldas, cap_caldas, min_pct, objetivo_pct, alto_pct)

        if pct_caldas <= min_pct:
            decision = "REDUCIR SALIDAS DE CALDAS"
            color = "#e63946"
            q_salida_recomendada = min(q_salida_caldas, q_salida_segura)
            detalle = f"Caldas está bajo ({pct_caldas:.1f}%). La salida segura estimada es {q_salida_segura:.2f} L/s."
        elif q_salida_caldas > q_salida_segura + margen_ls:
            decision = "REDUCIR SALIDA TOTAL"
            color = "#e76f51"
            q_salida_recomendada = q_salida_segura
            detalle = f"La salida actual supera la salida segura por {q_salida_caldas - q_salida_segura:.2f} L/s."
        elif pct_caldas >= alto_pct:
            decision = "PUEDE AUMENTAR SALIDAS SI OPERATIVAMENTE APLICA"
            color = "#2DB9A3"
            q_salida_recomendada = q_salida_segura
            detalle = f"Caldas está alto ({pct_caldas:.1f}%). Puede despachar más si hay demanda y autorización."
        else:
            decision = "MANTENER Y SEGUIR TENDENCIA"
            color = "#008ACB"
            detalle = "El balance no exige una maniobra fuerte. Continúa verificando nivel y demanda."

        eval_actual = evaluar_tanque("Caldas actual", nivel_caldas, cap_caldas, nmax_caldas, q_in_caldas, q_salida_caldas, min_pct, objetivo_pct, alto_pct)
        eval_recom = evaluar_tanque("Caldas recomendado", nivel_caldas, cap_caldas, nmax_caldas, q_in_caldas, q_salida_recomendada, min_pct, objetivo_pct, alto_pct)
        tabla_caldas = pd.DataFrame([eval_actual, eval_recom]).drop(columns=["_horas_limite", "_color"])

        st.markdown(
            f"<div class='decision-box' style='border-left:7px solid {color}'>"
            f"<div style='font-size:.78rem;color:#4E6F8A;font-weight:900;text-transform:uppercase;letter-spacing:.7px'>Decisión sugerida Caldas</div>"
            f"<div style='font-size:1.35rem;font-weight:900;color:{color};margin:.2rem 0'>{decision}</div>"
            f"<div style='font-size:.95rem;color:#003A70;line-height:1.55'>{detalle}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Volumen Caldas", f"{vol_caldas:,.2f} m³", f"{pct_caldas:.1f}%")
        m2.metric("Entrada estimada/medida", f"{q_in_caldas:.2f} L/s")
        m3.metric("Salida segura", f"{q_salida_segura:.2f} L/s")
        m4.metric("Ajuste salida", f"{q_salida_recomendada - q_salida_caldas:+.2f} L/s")

        mostrar_tabla_profesional(
            tabla_caldas,
            formatos={
                "Nivel (m)": "{:.2f}",
                "Volumen calculado (m³)": "{:,.2f}",
                "Capacidad (m³)": "{:,.2f}",
                "% llenado": "{:.1f}%",
                "Entrada (L/s)": "{:.2f}",
                "Salida (L/s)": "{:.2f}",
                "Balance (L/s)": "{:+.2f}",
                "Cambio (m³/h)": "{:+.2f}",
            },
        )

        if modo_salida_caldas == "Desglosar por salidas" and q_salida_caldas > 0:
            factor = safe_div(q_salida_recomendada, q_salida_caldas, 1.0)
            sectores_df = pd.DataFrame([
                {"Sector": k, "Salida actual (L/s)": v, "Salida recomendada proporcional (L/s)": v * factor}
                for k, v in det_salidas_caldas.items()
            ])
            st.markdown("<div class='titulo-seccion-resultado'>Distribución proporcional por sectores</div>", unsafe_allow_html=True)
            mostrar_tabla_profesional(
                sectores_df,
                formatos={"Salida actual (L/s)": "{:.2f}", "Salida recomendada proporcional (L/s)": "{:.2f}"},
            )

        plot_volumenes(pd.DataFrame([eval_actual]), "Caldas · volumen calculado desde nivel")

        st.markdown("""
        <div class="caja-rango" style="border-left-color:#48B9EA">
        <b>Nota para Caldas</b><br>
        Si no hay macromedidor de entrada, usa dos lecturas de nivel con hora conocida. La app calcula el cambio de volumen y estima la entrada sumando ese balance a la salida medida.
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────
    # Fórmulas usadas
    # ─────────────────────────────────────────────────────────────────────
    with tab_formulas:
        mostrar_formulas_hidraulicas_profesionales()

    st.markdown("""
    <div class="caja-rango" style="border-left-color:#e63946">
    <b>Advertencia operativa</b><br>
    Esta pantalla es de apoyo al análisis. Las maniobras de válvulas deben hacerse lentamente, con autorización y registrando la novedad cuando aplique. Si hay lectura incoherente, fuga, caída rápida de nivel o posible afectación de continuidad, se debe reportar y verificar en campo.
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Volver al menú", type="secondary", use_container_width=True, key="volver_menu_sistema_hidraulico"):
        st.session_state.vista = "menu"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# DOCUMENTOS DEL SISTEMA - VISOR PDF CON PIN
# =========================================
def asegurar_carpeta_documentos():
    """Crea la carpeta Documentos si no existe y devuelve la ruta."""
    DOCUMENTOS_DIR.mkdir(parents=True, exist_ok=True)
    return DOCUMENTOS_DIR


def listar_pdfs_documentos():
    """Lista automáticamente todos los PDF guardados en la carpeta Documentos."""
    carpeta = asegurar_carpeta_documentos()
    return sorted(
        [ruta for ruta in carpeta.glob("*.pdf") if ruta.is_file()],
        key=lambda ruta: ruta.name.lower()
    )


def nombre_archivo_pdf_seguro(nombre_archivo):
    """Evita rutas extrañas y conserva únicamente el nombre del archivo PDF."""
    nombre = Path(str(nombre_archivo)).name.strip()
    nombre = nombre.replace("/", "_").replace("\\", "_")
    if not nombre.lower().endswith(".pdf"):
        nombre = f"{nombre}.pdf"
    return nombre


def obtener_ruta_sin_sobrescribir(carpeta, nombre_archivo):
    """Si ya existe un PDF con el mismo nombre, crea nombre_1.pdf, nombre_2.pdf, etc."""
    ruta = carpeta / nombre_archivo
    if not ruta.exists():
        return ruta

    base = ruta.stem
    sufijo = ruta.suffix
    contador = 1
    while True:
        nueva_ruta = carpeta / f"{base}_{contador}{sufijo}"
        if not nueva_ruta.exists():
            return nueva_ruta
        contador += 1


def pdf_es_valido(uploaded_file, max_mb=25):
    """Valida tamaño y firma básica de PDF."""
    try:
        data = uploaded_file.getbuffer()
        if len(data) > max_mb * 1024 * 1024:
            return False, f"supera el tamaño máximo de {max_mb} MB"
        if not bytes(data[:5]).startswith(b"%PDF-"):
            return False, "el archivo no parece ser un PDF válido"
        return True, ""
    except Exception as exc:
        return False, str(exc)


def github_habilitado():
    return bool(GITHUB_TOKEN.strip() and GITHUB_REPO.strip() and GITHUB_BRANCH.strip())


def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_url_contenido(nombre_archivo):
    ruta_repo = f"{GITHUB_DOCS_DIR}/{nombre_archivo}"
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{quote(ruta_repo)}"


def github_obtener_info(nombre_archivo):
    if not github_habilitado():
        return None, "GitHub no configurado"
    try:
        resp = requests.get(
            github_url_contenido(nombre_archivo),
            headers=github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json(), None
        if resp.status_code == 404:
            return None, None
        return None, f"GitHub respondió {resp.status_code}: {resp.text[:250]}"
    except Exception as exc:
        return None, str(exc)


def github_nombre_disponible(nombre_archivo):
    info, error = github_obtener_info(nombre_archivo)
    if error:
        return nombre_archivo
    if info is None:
        return nombre_archivo

    ruta = Path(nombre_archivo)
    base = ruta.stem
    sufijo = ruta.suffix or ".pdf"
    contador = 1
    while True:
        candidato = f"{base}_{contador}{sufijo}"
        info, error = github_obtener_info(candidato)
        if error or info is None:
            return candidato
        contador += 1


def github_guardar_pdf(nombre_archivo, contenido_bytes, reemplazar=False):
    if not github_habilitado():
        return False, "GitHub no está configurado. El PDF solo se guardó temporalmente en la app."

    nombre_final = nombre_archivo
    info_existente, error_info = github_obtener_info(nombre_final)
    if error_info:
        return False, error_info

    if info_existente is not None and not reemplazar:
        nombre_final = github_nombre_disponible(nombre_final)
        info_existente = None

    payload = {
        "message": f"Agregar/actualizar documento {nombre_final}",
        "content": base64.b64encode(contenido_bytes).decode("utf-8"),
        "branch": GITHUB_BRANCH,
    }
    if info_existente is not None and info_existente.get("sha"):
        payload["sha"] = info_existente["sha"]

    try:
        resp = requests.put(
            github_url_contenido(nombre_final),
            headers=github_headers(),
            json=payload,
            timeout=30,
        )
        if resp.status_code in (200, 201):
            return True, nombre_final
        return False, f"GitHub respondió {resp.status_code}: {resp.text[:300]}"
    except Exception as exc:
        return False, str(exc)


def github_eliminar_pdf(nombre_archivo):
    if not github_habilitado():
        return False, "GitHub no está configurado. Se eliminará solo de forma temporal si existe en la app."

    info, error_info = github_obtener_info(nombre_archivo)
    if error_info:
        return False, error_info
    if info is None:
        return False, "No existe en GitHub"

    payload = {
        "message": f"Eliminar documento {nombre_archivo}",
        "sha": info.get("sha"),
        "branch": GITHUB_BRANCH,
    }

    try:
        resp = requests.delete(
            github_url_contenido(nombre_archivo),
            headers=github_headers(),
            json=payload,
            timeout=30,
        )
        if resp.status_code == 200:
            return True, nombre_archivo
        return False, f"GitHub respondió {resp.status_code}: {resp.text[:300]}"
    except Exception as exc:
        return False, str(exc)


def guardar_pdfs_subidos(archivos_subidos, reemplazar=False):
    """Guarda PDF cargados. En Streamlit Cloud, si GITHUB_TOKEN está configurado, también los sube al repositorio para permanencia."""
    carpeta = asegurar_carpeta_documentos()
    guardados = []
    errores = []

    for archivo in archivos_subidos:
        try:
            valido, motivo = pdf_es_valido(archivo, max_mb=25)
            if not valido:
                errores.append(f"{getattr(archivo, 'name', 'archivo')}: {motivo}")
                continue

            nombre = nombre_archivo_pdf_seguro(archivo.name)
            contenido = bytes(archivo.getbuffer())

            # 1) Guardado permanente en GitHub si está configurado.
            nombre_final = nombre
            if github_habilitado():
                ok_git, resultado_git = github_guardar_pdf(nombre, contenido, reemplazar=reemplazar)
                if ok_git:
                    nombre_final = resultado_git
                else:
                    errores.append(f"{nombre}: no se pudo guardar en GitHub ({resultado_git})")
                    # No se detiene: también se intenta guardar temporalmente para esta sesión.

            # 2) Guardado local para que se vea inmediatamente en la sesión actual.
            ruta_destino = carpeta / nombre_final if reemplazar else obtener_ruta_sin_sobrescribir(carpeta, nombre_final)
            ruta_destino.write_bytes(contenido)
            guardados.append(ruta_destino.name)
        except Exception as exc:
            errores.append(f"{getattr(archivo, 'name', 'archivo')}: {exc}")

    return guardados, errores


@st.cache_data(show_spinner=False)
def obtener_info_pdf_bytes(pdf_bytes):
    """Devuelve número de páginas del PDF. Usa PyMuPDF para evitar visor bloqueado por Chrome."""
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    n_paginas = doc.page_count
    doc.close()
    return n_paginas


@st.cache_data(show_spinner=False)
def renderizar_pdf_a_imagenes(pdf_bytes, pagina_inicio, pagina_fin, zoom=1.55):
    """Renderiza páginas del PDF a PNG para mostrarlas con st.image.

    Esta forma evita el problema de Chrome bloqueando iframes con PDF en base64.
    Requiere PyMuPDF en requirements.txt.
    """
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    paginas = []
    matriz = fitz.Matrix(float(zoom), float(zoom))

    for i in range(pagina_inicio - 1, pagina_fin):
        if i < 0 or i >= doc.page_count:
            continue
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=matriz, alpha=False)
        paginas.append((i + 1, pix.tobytes("png")))

    doc.close()
    return paginas


def mostrar_pdf_en_pagina(ruta_pdf, alto=850):
    """Muestra un PDF dentro de Streamlit como imágenes de páginas.

    No usa iframe porque Chrome puede bloquear PDF embebidos en base64 dentro de Streamlit.
    """
    ruta_pdf = Path(ruta_pdf)

    if not ruta_pdf.exists():
        st.error(f"No se encontró el archivo PDF: {ruta_pdf.name}")
        st.info("Verifica que el PDF esté dentro de la carpeta Documentos del repositorio.")
        return

    pdf_bytes = ruta_pdf.read_bytes()

    try:
        total_paginas = obtener_info_pdf_bytes(pdf_bytes)
    except ModuleNotFoundError:
        st.error("Falta instalar PyMuPDF para visualizar PDF dentro de la app.")
        st.code("PyMuPDF", language="text")
        st.info("Agrega esa línea en requirements.txt, guarda los cambios y vuelve a desplegar la app. Mientras tanto puedes usar el botón de descarga del PDF.")
        return
    except Exception as exc:
        st.error(f"No se pudo leer el PDF: {exc}")
        st.info("Puedes usar el botón de descarga para abrirlo directamente en el navegador.")
        return

    if total_paginas <= 0:
        st.warning("El PDF no tiene páginas para mostrar.")
        return

    # Vista fija en alta calidad. Se elimina el selector de tamaño para evitar baja resolución.
    zoom = 2.1  # Equivale a "Extra grande".

    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        pagina_inicio = st.number_input(
            "Desde página",
            min_value=1,
            max_value=int(total_paginas),
            value=1,
            step=1,
            key=f"pdf_inicio_{ruta_pdf.name}"
        )
    with col_p2:
        pagina_fin_default = min(int(total_paginas), int(pagina_inicio) + 4)
        pagina_fin = st.number_input(
            "Hasta página",
            min_value=int(pagina_inicio),
            max_value=int(total_paginas),
            value=pagina_fin_default,
            step=1,
            key=f"pdf_fin_{ruta_pdf.name}"
        )

    if int(pagina_fin) - int(pagina_inicio) > 9:
        st.warning("Para que la app no se ponga lenta, se recomienda visualizar máximo 10 páginas a la vez.")

    pagina_fin = min(int(pagina_fin), int(pagina_inicio) + 9)

    with st.spinner("Cargando vista del PDF..."):
        paginas = renderizar_pdf_a_imagenes(pdf_bytes, int(pagina_inicio), int(pagina_fin), float(zoom))

    st.caption(f"Mostrando páginas {pagina_inicio} a {pagina_fin} de {total_paginas}.")

    for numero_pagina, imagen_png in paginas:
        st.markdown(f"<div class='titulo-seccion-resultado'>Página {numero_pagina}</div>", unsafe_allow_html=True)
        st.image(imagen_png, use_container_width=True)


def eliminar_pdfs_documentos(nombres_pdf):
    """Elimina PDF seleccionados. Si GitHub está configurado, también los elimina del repositorio para que el cambio sea permanente."""
    carpeta = asegurar_carpeta_documentos()
    eliminados = []
    errores = []

    for nombre in nombres_pdf:
        try:
            nombre_seguro = nombre_archivo_pdf_seguro(nombre)
            ruta = carpeta / nombre_seguro

            # Seguridad: solo se permite borrar archivos PDF dentro de la carpeta Documentos.
            if ruta.parent.resolve() != carpeta.resolve():
                errores.append(f"{nombre}: ruta no permitida")
                continue
            if Path(nombre_seguro).suffix.lower() != ".pdf":
                errores.append(f"{nombre}: no es PDF")
                continue

            # Eliminación permanente en GitHub, si está configurado.
            if github_habilitado():
                ok_git, resultado_git = github_eliminar_pdf(nombre_seguro)
                if not ok_git and resultado_git != "No existe en GitHub":
                    errores.append(f"{nombre}: no se pudo eliminar en GitHub ({resultado_git})")

            # Eliminación local para que se refleje en la sesión actual.
            if ruta.exists():
                ruta.unlink()

            eliminados.append(nombre_seguro)
        except Exception as exc:
            errores.append(f"{nombre}: {exc}")

    return eliminados, errores


def mostrar_documentos_sistema():
    st.markdown("<div class='bloque'>", unsafe_allow_html=True)
    st.markdown("<div class='etiqueta'>📄 Documentos del sistema</div>", unsafe_allow_html=True)

    st.markdown("""
    <p style="color:#4E6F8A;font-size:0.93rem;line-height:1.6;margin-bottom:1rem">
    Consulta los instructivos PDF directamente desde la aplicación. El acceso de consulta permite ver y descargar.
    El acceso de administrador permite agregar y eliminar PDF. Las claves se leen desde Streamlit Cloud Secrets.
    </p>
    """, unsafe_allow_html=True)

    # Crear carpeta si no existe.
    asegurar_carpeta_documentos()

    # ---------------------------------------------------------
    # ACCESO POR PIN
    # ---------------------------------------------------------
    col_estado_1, col_estado_2 = st.columns([2, 2])
    with col_estado_1:
        if st.session_state.get("documentos_autorizado", False):
            st.success("Acceso de consulta activo: puedes ver y descargar PDF.")
        else:
            st.warning("Acceso de consulta bloqueado.")
    with col_estado_2:
        if st.session_state.get("documentos_admin_autorizado", False):
            st.success("Acceso administrador activo: puedes agregar y eliminar PDF.")
        else:
            st.info("Acceso administrador bloqueado.")

    if not st.session_state.get("documentos_autorizado", False):
        st.markdown("<div class='titulo-seccion-resultado'>Ingresar como consulta</div>", unsafe_allow_html=True)
        cpin1, cpin2 = st.columns([3, 1])
        with cpin1:
            pin_ver = st.text_input(
                "PIN para ver y descargar documentos",
                type="password",
                placeholder="Ingresa el PIN de consulta",
                key="pin_ver_documentos"
            )
        with cpin2:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            if st.button("Entrar", use_container_width=True, key="btn_ingresar_ver_documentos"):
                restante = segundos_restantes_bloqueo("documentos_consulta")
                if restante > 0:
                    st.error(f"Consulta bloqueada temporalmente. Intenta nuevamente en {restante} segundos.")
                elif not PIN_VER_DOCUMENTOS:
                    st.error("Falta configurar PIN_VER_DOCUMENTOS en Streamlit Cloud Secrets.")
                elif comparar_secreto(pin_ver, PIN_VER_DOCUMENTOS):
                    reiniciar_intentos("documentos_consulta")
                    st.session_state.documentos_autorizado = True
                    st.success("Acceso autorizado.")
                    st.rerun()
                else:
                    registrar_intento_fallido("documentos_consulta")
                    st.error("PIN de consulta incorrecto.")

    with st.expander("🔐 Ingresar como administrador", expanded=False):
        st.caption("El administrador puede agregar y eliminar PDF. El PIN debe configurarse en Streamlit Cloud Secrets, no en el código.")
        admin_pin = st.text_input(
            "PIN de administrador",
            type="password",
            placeholder="Ingresa el PIN de administrador",
            key="pin_admin_documentos"
        )
        if st.button("Activar modo administrador", use_container_width=True, key="btn_ingresar_admin_documentos"):
            restante = segundos_restantes_bloqueo("documentos_admin")
            if restante > 0:
                st.error(f"Administrador bloqueado temporalmente. Intenta nuevamente en {restante} segundos.")
            elif not PIN_ADMIN_DOCUMENTOS:
                st.error("Falta configurar PIN_ADMIN_DOCUMENTOS en Streamlit Cloud Secrets.")
            elif comparar_secreto(admin_pin, PIN_ADMIN_DOCUMENTOS):
                reiniciar_intentos("documentos_admin")
                st.session_state.documentos_admin_autorizado = True
                st.session_state.documentos_autorizado = True
                st.success("Modo administrador activado.")
                st.rerun()
            else:
                registrar_intento_fallido("documentos_admin")
                st.error("PIN de administrador incorrecto.")

    if not st.session_state.get("documentos_autorizado", False):
        st.info("Ingresa el PIN de consulta para ver los PDF o el PIN de administrador para gestionar documentos.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    col_bloq1, col_bloq2, col_bloq3 = st.columns([1, 1, 1])
    with col_bloq1:
        if st.button("🔒 Bloquear consulta", type="secondary", use_container_width=True, key="btn_bloquear_ver_documentos"):
            st.session_state.documentos_autorizado = False
            st.session_state.documentos_admin_autorizado = False
            st.rerun()
    with col_bloq2:
        if st.session_state.get("documentos_admin_autorizado", False):
            if st.button("🔒 Salir de admin", type="secondary", use_container_width=True, key="btn_bloquear_admin_documentos"):
                st.session_state.documentos_admin_autorizado = False
                st.rerun()
    with col_bloq3:
        if st.button("🔄 Actualizar lista", use_container_width=True, key="btn_actualizar_documentos_top"):
            st.rerun()

    # ---------------------------------------------------------
    # PANEL ADMINISTRADOR: AGREGAR Y ELIMINAR
    # ---------------------------------------------------------
    if st.session_state.get("documentos_admin_autorizado", False):
        st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-seccion-resultado'>Panel de administrador</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="caja-rango" style="border-left-color:#f4a261">
            <b>Importante sobre permanencia</b><br>
            En Streamlit Cloud, los archivos guardados solo en la carpeta local pueden perderse al reiniciar o redeplegar la app.
            Para guardar y eliminar PDF de forma permanente desde la app, configura <b>GITHUB_TOKEN</b>, <b>GITHUB_REPO</b>, <b>GITHUB_BRANCH</b> y <b>GITHUB_DOCS_DIR</b> en Streamlit Secrets.
            Si no configuras GitHub, los cambios pueden ser temporales.
        </div>
        """, unsafe_allow_html=True)

        if github_habilitado():
            st.success("Sincronización permanente con GitHub activa.")
        else:
            st.warning("GitHub no está configurado en Secrets: los PDF agregados o eliminados desde la app pueden ser temporales.")

        tab_subir, tab_eliminar = st.tabs(["➕ Agregar PDF", "🗑️ Eliminar PDF"])

        with tab_subir:
            archivos = st.file_uploader(
                "Selecciona uno o varios PDF para agregar",
                type=["pdf"],
                accept_multiple_files=True,
                key="uploader_documentos_pdf_admin"
            )
            reemplazar = st.checkbox(
                "Reemplazar si ya existe un PDF con el mismo nombre",
                value=False,
                key="chk_reemplazar_pdf_admin"
            )

            if st.button("Guardar PDF(s)", use_container_width=True, key="btn_guardar_pdfs_admin"):
                if not archivos:
                    st.info("Primero selecciona al menos un PDF.")
                else:
                    guardados, errores = guardar_pdfs_subidos(archivos, reemplazar=reemplazar)
                    if guardados:
                        st.success("PDF guardado(s): " + ", ".join(guardados))
                    if errores:
                        st.error("Algunos archivos no se pudieron guardar: " + " | ".join(errores))
                    st.rerun()

        with tab_eliminar:
            pdfs_para_borrar = listar_pdfs_documentos()
            if not pdfs_para_borrar:
                st.info("No hay PDF para eliminar.")
            else:
                nombres_borrar = [pdf.name for pdf in pdfs_para_borrar]
                seleccion_borrar = st.multiselect(
                    "Selecciona los PDF que deseas eliminar",
                    nombres_borrar,
                    key="multiselect_borrar_pdfs"
                )
                confirmar_borrado = st.checkbox(
                    "Confirmo que deseo eliminar los PDF seleccionados",
                    value=False,
                    key="chk_confirmar_borrado_pdfs"
                )

                if st.button("Eliminar PDF seleccionado(s)", use_container_width=True, key="btn_eliminar_pdfs_admin"):
                    if not seleccion_borrar:
                        st.info("Selecciona al menos un PDF para eliminar.")
                    elif not confirmar_borrado:
                        st.warning("Marca la confirmación antes de eliminar.")
                    else:
                        eliminados, errores = eliminar_pdfs_documentos(seleccion_borrar)
                        if eliminados:
                            st.success("PDF eliminado(s): " + ", ".join(eliminados))
                        if errores:
                            st.error("Algunos PDF no se pudieron eliminar: " + " | ".join(errores))
                        st.rerun()

    # ---------------------------------------------------------
    # LISTA, DESCARGA Y VISUALIZACIÓN
    # ---------------------------------------------------------
    pdfs = listar_pdfs_documentos()

    st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-seccion-resultado'>Consulta de documentos</div>", unsafe_allow_html=True)

    if not pdfs:
        st.info("Todavía no hay PDF en la carpeta Documentos.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    nombres = [pdf.name for pdf in pdfs]
    documento = st.selectbox("Selecciona el PDF que deseas consultar", nombres, key="select_documento_pdf")
    ruta_seleccionada = next(pdf for pdf in pdfs if pdf.name == documento)

    try:
        pdf_bytes = ruta_seleccionada.read_bytes()
    except Exception as exc:
        st.error(f"No se pudo abrir el archivo seleccionado: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    col_descarga_pdf_a, col_descarga_pdf_b = st.columns([3, 1])
    with col_descarga_pdf_a:
        st.caption(f"Documento seleccionado: {ruta_seleccionada.name}")
    with col_descarga_pdf_b:
        st.download_button(
            label="⬇️ Descargar PDF",
            data=pdf_bytes,
            file_name=ruta_seleccionada.name,
            mime="application/pdf",
            use_container_width=True,
            key="btn_descargar_pdf"
        )

    st.markdown("<div class='titulo-seccion-resultado'>Vista del PDF</div>", unsafe_allow_html=True)
    mostrar_pdf_en_pagina(ruta_seleccionada, alto=850)

    with st.expander("📁 PDF disponibles en la carpeta Documentos", expanded=False):
        tabla_docs = pd.DataFrame({
            "Documento": [pdf.name for pdf in pdfs],
            "Tamaño (MB)": [round(pdf.stat().st_size / (1024 * 1024), 2) for pdf in pdfs],
        })
        mostrar_tabla_profesional(tabla_docs)

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
logo_servaf_b64 = obtener_logo_servaf_base64()

if logo_servaf_b64:
    # IMPORTANTE: se construye en una sola línea, sin sangría inicial.
    # Si el HTML queda indentado, Markdown puede mostrarlo como texto/código.
    logo_header_html = (
        f'<div class="header-logo-card">'
        f'<img src="data:image/png;base64,{logo_servaf_b64}" alt="SERVAF">'
        f'</div>'
    )
else:
    logo_header_html = '<div class="header-logo">💧 SERVAF</div>'

st.markdown(f"""
<div class="app-header">
    <div class="header-left-brand">
        Dirección Producción
        <span>y Tratamiento</span>
    </div>
    <div class="header-title">
        HERRAMIENTA WEB DE APOYO PARA OPERACIÓN<br>
        <span style="font-size:0.85rem;font-weight:400;color:rgba(255,255,255,0.72)">
            Planta de Tratamiento Agua Potable · Diviso & Caldas
        </span>
    </div>
    {logo_header_html}
</div>
""", unsafe_allow_html=True)
 
 
# =========================================
# MENÚ PROFESIONAL OPTIMIZADO
# =========================================
MENU_PROFESIONAL_CSS = """
<style>
.menu-pro-shell {
    padding: 0.95rem 1.15rem 1.05rem 1.15rem !important;
    margin-bottom: 1rem !important;
}
.menu-pro-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.15rem 0.2rem 0.8rem 0.2rem;
    border-bottom: 1px solid #e4edf8;
    margin-bottom: 0.85rem;
}
.menu-pro-title {
    font-size: 1.08rem;
    font-weight: 850;
    color: #003A70;
    letter-spacing: -0.01em;
}
.menu-pro-subtitle {
    color: #4E6F8A;
    font-size: 0.84rem;
    margin-top: 0.15rem;
    line-height: 1.35;
}
.menu-pro-active {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #E6F5FB, #f3f9ff);
    border: 1px solid #cde3ff;
    color: #004A8F;
    border-radius: 999px;
    padding: 0.42rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 800;
    white-space: nowrap;
}
.menu-pro-group {
    background: linear-gradient(180deg, #ffffff 0%, #F7FCFF 100%);
    border: 1px solid #CFE5F4;
    border-radius: 18px;
    padding: 0.85rem 0.95rem 0.95rem 0.95rem;
    box-shadow: 0 5px 18px rgba(10,22,40,0.055);
    min-height: 118px;
    margin-bottom: 0.2rem;
}
.menu-pro-group-title {
    font-size: 0.91rem;
    font-weight: 850;
    color: #005B8E;
    text-transform: none;
    letter-spacing: 0.045em;
    margin-bottom: 0.2rem;
}
.menu-pro-group-text {
    color: #4E6F8A;
    font-size: 0.80rem;
    line-height: 1.42;
    min-height: 2.1rem;
    margin-bottom: 0.55rem;
}
.menu-pro-mini-note {
    background: #f3f8ff;
    color: #486681;
    border: 1px dashed #c8def5;
    border-radius: 12px;
    padding: 0.55rem 0.7rem;
    font-size: 0.78rem;
    line-height: 1.45;
    margin-top: 0.55rem;
}
.menu-pro-shell .stButton > button {
    min-height: 40px !important;
    font-size: 0.82rem !important;
    border-radius: 10px !important;
    padding: 0.35rem 0.55rem !important;
    box-shadow: 0 4px 14px rgba(26,111,255,0.15) !important;
}
.menu-pro-shell .stButton > button[kind="secondary"] {
    box-shadow: 0 3px 10px rgba(10,22,40,0.055) !important;
}
@media (max-width: 900px) {
    .menu-pro-header {
        flex-direction: column;
        align-items: flex-start;
    }
    .menu-pro-active {
        white-space: normal;
    }
}
</style>
"""
st.markdown(MENU_PROFESIONAL_CSS, unsafe_allow_html=True)


if st.session_state.vista in ("scada", "historico_scada", "tanque"):
    st.session_state.vista = "despacho"

def nombre_vista_actual(vista):
    nombres = {
        "menu": "Inicio",
        "recomendacion": "Recomendación PAC",
        "calculadora": "Calculadora PAC",
        "despacho": "Sistema hidráulico",
        "documentos": "Documentos del sistema",
    }
    return nombres.get(vista, "Inicio")


st.markdown("<div class='bloque menu-pro-shell'>", unsafe_allow_html=True)
st.markdown(f"""
<div class="menu-pro-header">
    <div>
        <div class="menu-pro-title">Centro de control operativo</div>
        <div class="menu-pro-subtitle">Accesos organizados por proceso. El menú queda compacto para no ocupar espacio en las pantallas de resultados.</div>
    </div>
    <div class="menu-pro-active">Vista actual: {nombre_vista_actual(st.session_state.vista)}</div>
</div>
""", unsafe_allow_html=True)

col_pac, col_hid, col_doc, col_sesion = st.columns([1.05, 1.45, 1.05, 0.85], gap="medium")

with col_pac:
    st.markdown("""
    <div class="menu-pro-group">
        <div class="menu-pro-group-title">💧 PAC y laboratorio</div>
        <div class="menu-pro-group-text">Consulta datos históricos, calcula consumos y apoya la prueba de jarras.</div>
    </div>
    """, unsafe_allow_html=True)
    b1, b2 = st.columns(2, gap="small")
    with b1:
        if st.button("Recomendación", use_container_width=True, key="btn_ir_recomendacion", type="primary" if st.session_state.vista == "recomendacion" else "secondary"):
            st.session_state.vista = "recomendacion"
            st.rerun()
    with b2:
        if st.button("Calculadora PAC", use_container_width=True, key="btn_ir_calculadora", type="primary" if st.session_state.vista == "calculadora" else "secondary"):
            st.session_state.vista = "calculadora"
            st.rerun()

with col_hid:
    st.markdown("""
    <div class="menu-pro-group">
        <div class="menu-pro-group-title">🏗️ Sistema hidráulico</div>
        <div class="menu-pro-group-text">Evalúa niveles, volúmenes calculados, entradas, salidas, válvulas y tiempos de llenado o vaciado.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Sistema hidráulico", use_container_width=True, key="btn_ir_sistema_hidraulico", type="primary" if st.session_state.vista == "despacho" else "secondary"):
        st.session_state.vista = "despacho"
        st.rerun()

with col_doc:
    st.markdown("""
    <div class="menu-pro-group">
        <div class="menu-pro-group-title">📄 Documentos</div>
        <div class="menu-pro-group-text">Consulta instructivos PDF con PIN, visualiza páginas y descarga archivos.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Abrir documentos", use_container_width=True, key="btn_ir_documentos", type="primary" if st.session_state.vista == "documentos" else "secondary"):
        st.session_state.vista = "documentos"
        st.rerun()
    st.markdown("<div class='menu-pro-mini-note'>Documentos protegidos por Secrets · Admin con carga/eliminación segura.</div>", unsafe_allow_html=True)

with col_sesion:
    st.markdown("""
    <div class="menu-pro-group">
        <div class="menu-pro-group-title">👤 Sesión</div>
        <div class="menu-pro-group-text">Control de acceso de la aplicación.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Inicio", type="secondary", use_container_width=True, key="btn_ir_inicio"):
        st.session_state.vista = "menu"
        st.rerun()
    if st.button("Cerrar sesión", type="secondary", use_container_width=True, key="btn_cerrar_superior"):
        st.session_state.autenticado    = False
        st.session_state.vista          = "menu"
        st.session_state.planta_usuario = None
        st.session_state.documentos_autorizado = False
        st.session_state.documentos_admin = False
        st.rerun()

if st.session_state.vista == "menu":
    st.info("Selecciona una herramienta desde el centro de control operativo.")

st.markdown("</div>", unsafe_allow_html=True)




# =========================================
# VISTAS
# =========================================
if st.session_state.vista == "calculadora":
    mostrar_calculadora_pac()
    st.stop()
 
if st.session_state.vista == "despacho":
    mostrar_sistema_hidraulico()
    st.stop()

if st.session_state.vista == "documentos":
    mostrar_documentos_sistema()
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
            "<div style='background:#EAF6FC;border:1px solid #c5dcf5;border-radius:12px;"
            "padding:0.55rem 1rem;font-size:0.87rem;color:#004A8F;margin-bottom:0.8rem'>"
            "🏭 <b>Planta:</b> Diviso</div>",
            unsafe_allow_html=True
        )
        modulo_diviso = st.selectbox("Selecciona el módulo", ["Módulo 500", "Módulo 150"], key="rec_modulo_diviso")
        config_key = "Diviso - Modulo 500" if modulo_diviso == "Módulo 500" else "Diviso - Modulo 150"
    else:
        st.markdown(
            "<div style='background:#EAF6FC;border:1px solid #c5dcf5;border-radius:12px;"
            "padding:0.55rem 1rem;font-size:0.87rem;color:#004A8F;margin-bottom:0.8rem'>"
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
    st.number_input("Alcalinidad del agua cruda (mg/L)",   value=st.session_state.rec_alc_cruda, step=1.0,  key="rec_alc_cruda")
 
    if CONFIGS[config_key]["usa_alcalinidad_encalada"]:
        st.number_input("Alcalinidad del agua encalada (mg/L)", value=st.session_state.rec_alc_enc, step=1.0, key="rec_alc_enc")
 
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
        mostrar_tabla_profesional(
            resultado["tabla_jarras"],
            formatos={
                "Caudal de PAC recomendado (mL/min)": "{:.1f}",
                "Dosis PAC recomendada (mg/L)": "{:.2f}",
            }
        )
 
        st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-seccion-resultado'>Registros históricos similares</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#4E6F8A;font-size:0.88rem;margin-bottom:0.8rem'>Registros más cercanos al caso actual ordenados por similitud.</p>", unsafe_allow_html=True)
 
        fmt = {
            "Caudal a tratar (L/s)": "{:.1f}", "Turbiedad de agua cruda (UNT)": "{:.1f}",
            "pH de agua cruda": "{:.2f}", "Alcalinidad de agua cruda (mg/L)": "{:.1f}",
            "Caudal de PAC (mL/min)": "{:.1f}", "Distancia": "{:.3f}"
        }
        if "Alcalinidad de agua encalada (mg/L)" in resultado["similares_filtrados"].columns:
            fmt["Alcalinidad de agua encalada (mg/L)"] = "{:.1f}"
 
        mostrar_tabla_profesional(resultado["similares_filtrados"], formatos=fmt)
 
        st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-seccion-resultado'>Visualización</div>", unsafe_allow_html=True)
 
        df_grafica = resultado["similares_filtrados"].sort_values("Caudal de PAC (mL/min)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_grafica["Caudal de PAC (mL/min)"], y=df_grafica["Turbiedad de agua cruda (UNT)"],
            mode="lines+markers", name="Históricos",
            line=dict(color="#008ACB", width=2.2, shape="spline"),
            marker=dict(size=8, color="#008ACB", line=dict(color="white", width=2), symbol="circle"),
            fill="tozeroy", fillcolor="rgba(26,111,255,0.05)"
        ))
        fig.add_trace(go.Scatter(
            x=[resultado["pac_promedio"]], y=[turbiedad],
            mode="markers", name="Caso actual",
            marker=dict(size=14, color="#2DB9B0", line=dict(color="#003A70", width=2), symbol="star")
        ))
        fig.update_layout(
            title=dict(text="Caudal de PAC vs. turbiedad - registros similares",
                       font=dict(family="Syne", size=14, color="#003A70")),
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="DM Sans", color="#003A70", size=12),
            xaxis=dict(title="Caudal de PAC (mL/min)", gridcolor="#E3F2F8", linecolor="#CFE5F4"),
            yaxis=dict(title="Turbiedad (UNT)",      gridcolor="#E3F2F8", linecolor="#CFE5F4"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20), height=360
        )
        st.plotly_chart(fig, use_container_width=True)
 
    st.markdown("</div>", unsafe_allow_html=True)
