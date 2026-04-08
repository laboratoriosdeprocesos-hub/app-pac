import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


# =========================================
# CONFIGURACION GENERAL
# =========================================
st.set_page_config(
    page_title="PTAP - Recomendacion PAC",
    page_icon="💧",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
    }

    header {
        visibility: hidden;
    }

    .main > div {
        padding-top: 0rem;
    }
</style>
""", unsafe_allow_html=True)


# =========================================
# LOGIN
# =========================================
USUARIO_CORRECTO = "ptap"
CLAVE_CORRECTA = "c4ldas2026"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False


def mostrar_login():
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #dff4ff 0%, #eef9ff 35%, #f8fcff 100%);
        }

        .login-wrap {
            display: flex;
            align-items: flex-start;
            justify-content: center;
            margin-top: 2rem;
        }

        .login-box {
            width: 100%;
            max-width: 460px;
            background: rgba(255,255,255,0.96);
            padding: 2.2rem;
            border-radius: 24px;
            box-shadow: 0 12px 28px rgba(11,79,108,0.14);
            border: 1px solid rgba(11,79,108,0.08);
        }

        .login-logo {
            text-align: center;
            margin-bottom: 1rem;
        }

        .login-logo img {
            width: 95px;
            border-radius: 16px;
            background: white;
            padding: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        }

        .login-title {
            font-size: 2rem;
            font-weight: 800;
            color: #0b4f6c;
            text-align: center;
            margin-bottom: 0.3rem;
        }

        .login-sub {
            text-align: center;
            color: #4d6d7d;
            margin-bottom: 1.4rem;
            font-size: 1rem;
        }

        div[data-testid="stTextInput"] > div > div input {
            border-radius: 12px;
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
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='login-logo'><img src='https://raw.githubusercontent.com/laboratoriosdeprocesos-hub/app-pac/main/logo.jpeg'></div>",
        unsafe_allow_html=True
    )
    st.markdown("<div class='login-title'>Acceso PTAP</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='login-sub'>Ingresa tus credenciales para acceder a la herramienta de apoyo operativo</div>",
        unsafe_allow_html=True
    )

    usuario = st.text_input("Usuario")
    clave = st.text_input("Contrasena", type="password")

    if st.button("Ingresar"):
        if usuario == USUARIO_CORRECTO and clave == CLAVE_CORRECTA:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o contrasena incorrectos")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.autenticado:
    mostrar_login()
    st.stop()


# =========================================
# ESTILOS
# =========================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #dff4ff 0%, #eef9ff 35%, #f8fcff 100%);
    }

    .hero {
        background: linear-gradient(135deg, rgba(8,74,117,0.96), rgba(33,134,181,0.92));
        color: white;
        padding: 1.6rem 1.8rem;
        border-radius: 24px;
        box-shadow: 0 10px 24px rgba(8,74,117,0.20);
        margin-bottom: 1.2rem;
    }

    .hero-box {
        display: flex;
        align-items: center;
        gap: 22px;
    }

    .hero-logo {
        background: rgba(255,255,255,0.96);
        padding: 10px;
        border-radius: 18px;
        min-width: 120px;
        text-align: center;
    }

    .hero-logo img {
        width: 90px;
        display: block;
        margin: 0 auto;
    }

    .hero-texto h1 {
        color: white !important;
        margin: 0;
        font-size: 2.3rem;
        font-weight: 800;
    }

    .hero-texto p {
        margin-top: 0.45rem;
        margin-bottom: 0;
        font-size: 1rem;
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
        font-size: 1.05rem;
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

st.markdown("<div style='margin-top: -10px'></div>", unsafe_allow_html=True)
# =========================================
# =========================================
# ENCABEZADO CON IMAGEN
# =========================================
st.markdown("""
<div style="
    background: white;
    padding: 10px;
    border-radius: 15px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    margin-bottom: 15px;
">
""", unsafe_allow_html=True)

st.image("ENCABEZADOS.png", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# CONFIGURACIONES POR PLANTA / MODULO
# =========================================
CONFIGS = {
    "Caldas": {
        "archivo": "2026 PTAP CALDAS.xlsx",
        "nombre_app": "PTAP Caldas",
        "variables_entrada": {
            "caudal": "Caudal A tratar (L/s)",
            "turbiedad": "Turbiedad de agua cruda (UNT)",
            "ph": "pH de agua cruda (Unid)",
            "alcalinidad_cruda": "Alcalinidad de agua cruda (mg/L)",
        },
        "col_pac": "Caudal de dosificación del PAC (mL/min)",
        "usa_alcalinidad_encalada": False
    },

    "Diviso - Modulo 500": {
        "archivo": "2026 PTAP DIVISO.xlsx",
        "nombre_app": "PTAP Diviso - Modulo 500",
        "variables_entrada": {
            "caudal": "Caudal A tratar módulo de 500 (L/s)",
            "turbiedad": "Turbiedad de agua cruda (UNT)",
            "ph": "pH de agua cruda (Unid)",
            "alcalinidad_cruda": "Alcalinidad de agua cruda (mg/L)",
            "alcalinidad_encalada": "Alcalinidad de agua encalada (mg/L)",
        },
        "col_pac": "Caudal de dosificación del PAC módulo de 500 (mL/min)",
        "usa_alcalinidad_encalada": True
    },

    "Diviso - Modulo 150": {
        "archivo": "2026 PTAP DIVISO.xlsx",
        "nombre_app": "PTAP Diviso - Modulo 150",
        "variables_entrada": {
            "caudal": "Caudal A tratar módulo de 150 (L/s)",
            "turbiedad": "Turbiedad de agua cruda (UNT)",
            "ph": "pH de agua cruda (Unid)",
            "alcalinidad_cruda": "Alcalinidad de agua cruda (mg/L)",
            "alcalinidad_encalada": "Alcalinidad de agua encalada (mg/L)",
        },
        "col_pac": "Caudal de dosificación del PAC módulo de 150 (mL/min)",
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


@st.cache_data
def cargar_y_limpiar_excel(archivo_excel, config_key):
    config = CONFIGS[config_key]
    df = pd.read_excel(archivo_excel)

    if config_key == "Caldas":
        col_caudal = obtener_nombre_columna(df, [
            "Caudal A tratar (L/s)"
        ])
        col_turbiedad = obtener_nombre_columna(df, [
            "Turbiedad de agua cruda (UNT)"
        ])
        col_ph = obtener_nombre_columna(df, [
            "pH de agua cruda (Unid)",
            "pH de agua cruda"
        ])
        col_alcalinidad_cruda = obtener_nombre_columna(df, [
            "Alcalinidad de agua cruda (mg/L)"
        ])
        col_pac = obtener_nombre_columna(df, [
            "Caudal de dosificación del PAC (mL/min)"
        ])

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
        col_ph = obtener_nombre_columna(df, [
            "pH de agua cruda (Unid)",
            "pH de agua cruda"
        ])
        col_alcalinidad_cruda = obtener_nombre_columna(df, [
            "Alcalinidad de agua cruda (mg/L)"
        ])
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
    else:
        return [
            {"caudal": 20, "turb": 10, "ph": 0.20, "alc": 6, "alc_enc": 6},
            {"caudal": 35, "turb": 20, "ph": 0.30, "alc": 10, "alc_enc": 10},
            {"caudal": 60, "turb": 35, "ph": 0.45, "alc": 15, "alc_enc": 15},
            {"caudal": 90, "turb": 50, "ph": 0.60, "alc": 20, "alc_enc": 20},
        ]


def calcular_rango_pac(
    df: pd.DataFrame,
    config_key: str,
    caudal: float,
    turbiedad: float,
    ph: float,
    alcalinidad_cruda: float,
    densidad_pac: float,
    vecinos_deseados: int,
    alcalinidad_encalada: float = None
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
    intentos = obtener_tolerancias(config_key)

    for tol in intentos:
        filtro = (
            df["caudal"].between(caudal - tol["caudal"], caudal + tol["caudal"]) &
            df["turbiedad"].between(turbiedad - tol["turb"], turbiedad + tol["turb"]) &
            df["ph"].between(ph - tol["ph"], ph + tol["ph"]) &
            df["alcalinidad_cruda"].between(alcalinidad_cruda - tol["alc"], alcalinidad_cruda + tol["alc"])
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
            "mensaje": "Muy pocos datos despues del prefiltro, incluso ampliando tolerancias."
        }

    scaler = StandardScaler()
    X_hist = scaler.fit_transform(df_base[variables])
    X_new = scaler.transform(nuevo[variables])

    if config["usa_alcalinidad_encalada"]:
        pesos = np.array([3, 4, 3, 2, 2], dtype=float)
    else:
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
    pac_mediana = float(similares_filtrados["pac_ml_min"].median())
    pac_promedio = float(similares_filtrados["pac_ml_min"].mean())
    std = float(similares_filtrados["pac_ml_min"].std()) if len(similares_filtrados) > 1 else 0.0
    n = int(len(similares_filtrados))
    ancho_rango = pac_max - pac_min

    if n < 5:
        usar_rango = False
        motivo = "Muy pocos casos"
    elif std > 40:
        usar_rango = False
        motivo = "Demasiada dispersion"
    elif pac_mediana > 0 and ancho_rango > 0.4 * pac_mediana:
        usar_rango = False
        motivo = "Rango demasiado amplio"
    else:
        usar_rango = True
        motivo = "Rango aceptable"

    if usar_rango:
        dosis_mediana_min = pac_min
        dosis_mediana_max = pac_max
        metodo = "Rango historico real"
    else:
        dosis_mediana_min = pac_mediana * 0.90
        dosis_mediana_max = pac_mediana * 1.10
        metodo = "Mediana +-10%"

    jarras = [1, 2, 3, 4, 5, 6]

    jarras_mediana = np.round(np.linspace(dosis_mediana_min, dosis_mediana_max, 6), 1)
    jarras_minmax = np.round(np.linspace(pac_min, pac_max, 6), 1)

    dosis_mgL_mediana = np.round((jarras_mediana * densidad_pac * 1000) / (60 * caudal), 2)
    dosis_mgL_minmax = np.round((jarras_minmax * densidad_pac * 1000) / (60 * caudal), 2)

    tabla_jarras = pd.DataFrame({
        "Jarra": jarras,
        "Caudal PAC con mediana (mL/min)": jarras_mediana,
        "Dosis PAC con mediana (mg/L)": dosis_mgL_mediana,
        "Caudal PAC entre minimo y maximo (mL/min)": jarras_minmax,
        "Dosis PAC entre minimo y maximo (mg/L)": dosis_mgL_minmax
    })

    tabla_resumen = pd.DataFrame({
        "Indicador": ["Minimo", "Mediana", "Media", "Maximo"],
        "PAC (mL/min)": [
            round(pac_min, 1),
            round(pac_mediana, 1),
            round(pac_promedio, 1),
            round(pac_max, 1)
        ]
    })

    columnas_mostrar = ["caudal", "turbiedad", "ph", "alcalinidad_cruda"]

    if config["usa_alcalinidad_encalada"]:
        columnas_mostrar.append("alcalinidad_encalada")

    columnas_mostrar += ["pac_ml_min", "distancia"]

    similares_filtrados = similares_filtrados[columnas_mostrar].copy()

    nombres_mostrar = {
        "caudal": "Caudal a tratar (L/s)",
        "turbiedad": "Turbiedad de agua cruda (UNT)",
        "ph": "pH de agua cruda",
        "alcalinidad_cruda": "Alcalinidad de agua cruda (mg/L)",
        "alcalinidad_encalada": "Alcalinidad de agua encalada (mg/L)",
        "pac_ml_min": "Caudal PAC (mL/min)",
        "distancia": "Distancia"
    }

    similares_filtrados = similares_filtrados.rename(columns=nombres_mostrar)

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
        "tabla_jarras": tabla_jarras,
        "tabla_resumen": tabla_resumen,
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
    elif config_key == "Diviso - Modulo 500":
        return {
            "caudal": 500.0,
            "turbiedad": 10.0,
            "ph": 7.20,
            "alcalinidad_cruda": 18.0,
            "alcalinidad_encalada": 25.0,
            "densidad_pac": 1.33
        }
    else:
        return {
            "caudal": 150.0,
            "turbiedad": 10.0,
            "ph": 7.20,
            "alcalinidad_cruda": 18.0,
            "alcalinidad_encalada": 25.0,
            "densidad_pac": 1.33
        }


# =========================================
# SELECCION DE PLANTA Y CARGA DE ARCHIVO
# =========================================
st.markdown("<div class='bloque'>", unsafe_allow_html=True)
st.markdown("<div class='etiqueta'>Seleccion de planta</div>", unsafe_allow_html=True)

planta_base = st.selectbox(
    "Selecciona la planta",
    ["Caldas", "Diviso"]
)

config_key = "Caldas"

if planta_base == "Diviso":
    modulo_diviso = st.selectbox(
        "Selecciona el modulo de Diviso",
        ["Modulo 500", "Modulo 150"]
    )

    if modulo_diviso == "Modulo 500":
        config_key = "Diviso - Modulo 500"
    else:
        config_key = "Diviso - Modulo 150"

df = None
archivo_excel = CONFIGS[config_key]["archivo"]

try:
    df = cargar_y_limpiar_excel(archivo_excel, config_key)
    st.success(f"Archivo cargado correctamente para: {CONFIGS[config_key]['nombre_app']}")
except Exception as e:
    st.error(f"No pude abrir o procesar el archivo: {e}")

if df is not None:
    st.write(f"Modo seleccionado: {CONFIGS[config_key]['nombre_app']}")
    st.write(f"Filas utiles: {len(df)}")

st.markdown("</div>", unsafe_allow_html=True)


# =========================================
# BARRA LATERAL
# =========================================
defaults = valores_por_defecto(config_key)

st.sidebar.header("⚙️ Datos del caso actual")
st.sidebar.markdown("Ingresa las condiciones actuales del agua cruda.")

caudal = st.sidebar.number_input("Caudal A tratar (L/s)", value=float(defaults["caudal"]), step=1.0)
turbiedad = st.sidebar.number_input("Turbiedad de agua cruda (UNT)", value=float(defaults["turbiedad"]), step=0.1)
ph = st.sidebar.number_input("pH de agua cruda", value=float(defaults["ph"]), step=0.01, format="%.2f")
alcalinidad_cruda = st.sidebar.number_input("Alcalinidad de agua cruda (mg/L)", value=float(defaults["alcalinidad_cruda"]), step=1.0)

alcalinidad_encalada = None
if CONFIGS[config_key]["usa_alcalinidad_encalada"]:
    alcalinidad_encalada = st.sidebar.number_input(
        "Alcalinidad de agua encalada (mg/L)",
        value=float(defaults["alcalinidad_encalada"]),
        step=1.0
    )

densidad_pac = st.sidebar.number_input(
    "Densidad del PAC (g/mL)",
    value=float(defaults["densidad_pac"]),
    step=0.01,
    format="%.2f"
)

vecinos_deseados = st.sidebar.slider(
    "Cantidad de datos historicos a evaluar",
    min_value=5,
    max_value=30,
    value=8,
    step=1
)

calcular = st.sidebar.button("Calcular rango PAC")

st.sidebar.markdown(
    """
    <style>
    div[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
        background: #f8d7da !important;
        color: #842029 !important;
        border: 1px solid #f5c2c7 !important;
    }
    div[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {
        background: #f1b0b7 !important;
        color: #6a1a21 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

cerrar_sesion = st.sidebar.button("Cerrar sesion", type="secondary")

if cerrar_sesion:
    st.session_state.autenticado = False
    st.rerun()


# =========================================
# RESULTADOS
# =========================================
if df is not None and calcular:
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
        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.markdown("<div class='etiqueta'>Resultado del analisis</div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Casos usados", resultado["n"])
        c2.metric("PAC mediana", round(resultado["pac_mediana"], 1))
        c3.metric("PAC media", round(resultado["pac_promedio"], 1))
        c4.metric("Desviacion", round(resultado["std"], 1))

        st.markdown(
            f"<div class='caja-rango'><b>Metodo usado:</b> {resultado['metodo']}<br>"
            f"<b>Motivo:</b> {resultado['motivo']}</div>",
            unsafe_allow_html=True
        )

        if resultado.get("tolerancia_usada") is not None:
            tol = resultado["tolerancia_usada"]
            texto_tol = (
                f"Caudal ±{tol['caudal']}, "
                f"Turbiedad ±{tol['turb']}, "
                f"pH ±{tol['ph']}, "
                f"Alcalinidad cruda ±{tol['alc']}"
            )
            if "alc_enc" in tol:
                texto_tol += f", Alcalinidad encalada ±{tol['alc_enc']}"

            st.info(f"Tolerancias usadas en el prefiltro: {texto_tol}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.markdown("<div class='etiqueta'>Dosis sugeridas para 6 jarras</div>", unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])

        with col1:
            st.dataframe(resultado["tabla_jarras"], use_container_width=True)

        with col2:
            st.write("Resumen PAC")
            st.dataframe(resultado["tabla_resumen"], use_container_width=True)
            st.write(f"Densidad PAC usada: {densidad_pac:.2f} g/mL")
            st.write(f"Caudal a tratar usado: {caudal:.2f} L/s")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.markdown("<div class='etiqueta'>Casos historicos similares usados</div>", unsafe_allow_html=True)
        st.dataframe(resultado["similares_filtrados"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
