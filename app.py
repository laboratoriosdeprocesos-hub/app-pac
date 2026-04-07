import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


# =========================================
# CONFIGURACION GENERAL
# =========================================
st.set_page_config(
    page_title="PTAP Caldas - Recomendacion PAC",
    page_icon="💧",
    layout="wide"
)

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
        .login-box {
            max-width: 420px;
            margin: 60px auto;
            background: rgba(255,255,255,0.96);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.10);
            border: 1px solid rgba(11,79,108,0.08);
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
            margin-bottom: 1.2rem;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<div class='login-title'>💧 Acceso PTAP Caldas</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-sub'>Ingresa tus credenciales para entrar a la app</div>", unsafe_allow_html=True)

    usuario = st.text_input("Usuario")
    clave = st.text_input("Contrasena", type="password")

    if st.button("Ingresar"):
        if usuario == USUARIO_CORRECTO and clave == CLAVE_CORRECTA:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o contrasena incorrectos")

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

# =========================================
# ESTILOS
# =========================================
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

    .hero h1 {
        color: white !important;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 800;
    }

    .hero p {
        margin-top: 0.5rem;
        margin-bottom: 0;
        font-size: 1.05rem;
        color: #eaf7ff;
    }

    .hero-box {
        display: flex;
        align-items: center;
        gap: 24px;
    }

    .hero-logo {
        background: rgba(255,255,255,0.95);
        padding: 10px;
        border-radius: 16px;
        min-width: 120px;
        text-align: center;
    }

    .hero-logo img {
        width: 95px;
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

st.markdown("""
<div class="hero">
    <div class="hero-box">
        <div class="hero-logo">
            <img src="https://raw.githubusercontent.com/laboratoriosdeprocesos-hub/app-pac/main/logo.jpeg">
        </div>
        <div>
            <h1>PTAP Caldas - Recomendacion de PAC</h1>
            <p>Herramienta de apoyo operativo para definir dosis de PAC en prueba de jarras con base en datos historicos similares.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
# =========================================
# FUNCION DE CARGA Y LIMPIEZA
# =========================================
@st.cache_data
def cargar_y_limpiar_excel(archivo_excel):
    df = pd.read_excel(archivo_excel)

    columnas = [
        "Caudal A tratar (L/s)",
        "Turbiedad de agua cruda (UNT)",
        "pH de agua cruda (Unid)",
        "Alcalinidad de agua cruda (mg/L)",
        "Caudal de dosificación del PAC (mL/min)"
    ]

    for col in columnas:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(" ", "", regex=False)
            .str.replace(",,", ",", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=columnas).copy()
    return df


# =========================================
# FUNCION PRINCIPAL
# =========================================
def calcular_rango_pac(
    df: pd.DataFrame,
    caudal: float,
    turbiedad: float,
    ph: float,
    alcalinidad: float,
    densidad_pac: float,
    vecinos_deseados: int
):
    variables = [
        "Caudal A tratar (L/s)",
        "Turbiedad de agua cruda (UNT)",
        "pH de agua cruda (Unid)",
        "Alcalinidad de agua cruda (mg/L)"
    ]

    nuevo = pd.DataFrame([{
        "Caudal A tratar (L/s)": caudal,
        "Turbiedad de agua cruda (UNT)": turbiedad,
        "pH de agua cruda (Unid)": ph,
        "Alcalinidad de agua cruda (mg/L)": alcalinidad
    }])

    # Prefiltro
    df_base = df[
        (df["Caudal A tratar (L/s)"].between(caudal - 15, caudal + 15)) &
        (df["Turbiedad de agua cruda (UNT)"].between(turbiedad - 8, turbiedad + 8)) &
        (df["pH de agua cruda (Unid)"].between(ph - 0.15, ph + 0.15)) &
        (df["Alcalinidad de agua cruda (mg/L)"].between(alcalinidad - 5, alcalinidad + 5))
    ].copy()

    if len(df_base) < 5:
        return {
            "ok": False,
            "mensaje": "Muy pocos datos despues del prefiltro. Ajusta el caso o revisa el historico."
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

    col_pac = "Caudal de dosificación del PAC (mL/min)"

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
            "mensaje": "Despues de quitar valores extremos quedaron muy pocos casos utiles."
        }

    pac_min = float(similares_filtrados[col_pac].min())
    pac_max = float(similares_filtrados[col_pac].max())
    pac_mediana = float(similares_filtrados[col_pac].median())
    pac_promedio = float(similares_filtrados[col_pac].mean())
    std = float(similares_filtrados[col_pac].std()) if len(similares_filtrados) > 1 else 0.0
    n = int(len(similares_filtrados))
    ancho_rango = pac_max - pac_min

    # Regla para decidir si usar rango real o mediana +-10%
    if n < 5:
        usar_rango = False
        motivo = "Muy pocos casos"
    elif std > 40:
        usar_rango = False
        motivo = "Demasiada dispersion"
    elif ancho_rango > 0.4 * pac_mediana:
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

    # Series de jarras
    jarras = [1, 2, 3, 4, 5, 6]

    # 1) Caudal PAC con mediana / rango final usado
    jarras_mediana = np.round(np.linspace(dosis_mediana_min, dosis_mediana_max, 6), 1)

    # 2) Caudal PAC entre minimo y maximo estrictos
    jarras_minmax = np.round(np.linspace(pac_min, pac_max, 6), 1)

    # Conversion a mg/L
    # Dosis(mg/L) = (Qpac(mL/min) * densidad(g/mL) * 1000) / (60 * Qagua(L/s))
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

    columnas_mostrar = variables + [col_pac, "distancia"]
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
        "tabla_jarras": tabla_jarras,
        "tabla_resumen": tabla_resumen
    }


# =========================================
# CARGA DEL ARCHIVO
# =========================================
st.markdown("<div class='bloque'>", unsafe_allow_html=True)
st.markdown("<div class='etiqueta'>Archivo historico</div>", unsafe_allow_html=True)

opcion_archivo = st.radio(
    "Como quieres cargar el archivo?",
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
    st.write(f"*Filas utiles:* {len(df)}")

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
densidad_pac = st.sidebar.number_input("Densidad del PAC (g/mL)", value=1.33, step=0.01, format="%.2f")

vecinos_deseados = st.sidebar.slider(
    "Cantidad de datos historicos a evaluar",
    min_value=5,
    max_value=30,
    value=8,
    step=1
)

if st.sidebar.button("Cerrar sesion"):
    st.session_state.autenticado = False
    st.rerun()

calcular = st.sidebar.button("Calcular rango PAC")


# =========================================
# RESULTADOS
# =========================================
if df is not None and calcular:
    resultado = calcular_rango_pac(
        df,
        caudal,
        turbiedad,
        ph,
        alcalinidad,
        densidad_pac,
        vecinos_deseados
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

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.markdown("<div class='etiqueta'>Dosis sugeridas para 6 jarras</div>", unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])

        with col1:
            st.dataframe(resultado["tabla_jarras"], use_container_width=True)

        with col2:
            st.write("*Resumen PAC*")
            st.dataframe(resultado["tabla_resumen"], use_container_width=True)
            st.write(f"*Densidad PAC usada:* {densidad_pac:.2f} g/mL")
            st.write(f"*Caudal a tratar usado:* {caudal:.2f} L/s")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bloque'>", unsafe_allow_html=True)
        st.markdown("<div class='etiqueta'>Casos historicos similares usados</div>", unsafe_allow_html=True)
        st.dataframe(resultado["similares_filtrados"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
