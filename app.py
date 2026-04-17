# =========================================
# VISTA RECOMENDACION
# =========================================
if st.session_state.vista != "recomendacion":
    st.stop()

# ---------- ESTILO EXTRA SOLO PARA VISTA RECOMENDACION ----------
st.markdown("""
<style>
.panel-izquierdo {
    background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
    border: 1px solid #dceaf4;
    border-radius: 20px;
    padding: 1rem 1rem 0.6rem 1rem;
    box-shadow: 0 8px 24px rgba(7,62,94,0.08);
    position: sticky;
    top: 0.8rem;
}

.panel-derecho {
    background: rgba(255,255,255,0.96);
    border: 1px solid #dceaf4;
    border-radius: 20px;
    padding: 1rem;
    box-shadow: 0 8px 24px rgba(7,62,94,0.08);
}

.subtitulo-panel {
    color: #0b4f6c;
    font-size: 1.1rem;
    font-weight: 800;
    margin-bottom: 0.4rem;
}

.texto-panel {
    color: #5b7482;
    font-size: 0.93rem;
    line-height: 1.45;
    margin-bottom: 0.9rem;
}

.hr-suave {
    border: none;
    border-top: 1px solid #e5eef5;
    margin: 0.8rem 0 1rem 0;
}

.bloque-mini {
    background: #f8fcff;
    border: 1px solid #e1edf5;
    border-radius: 16px;
    padding: 0.9rem;
    margin-bottom: 0.8rem;
}

.titulo-mini {
    font-size: 0.92rem;
    font-weight: 800;
    color: #0b4f6c;
    margin-bottom: 0.35rem;
}

.texto-mini {
    font-size: 0.88rem;
    color: #5b7482;
    line-height: 1.4;
}

.titulo-seccion-resultado {
    font-size: 1.1rem;
    font-weight: 800;
    color: #0b4f6c;
    margin-bottom: 0.4rem;
    margin-top: 0.2rem;
}

@media (max-width: 1100px) {
    .panel-izquierdo {
        position: relative;
        top: 0;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================================
# VARIABLES DE RECOMENDACION
# =========================================
col_form, col_result = st.columns([1, 1.85], gap="large")

with col_form:
    st.markdown("<div class='panel-izquierdo'>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo-panel'>Configuración del análisis</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='texto-panel'>Selecciona la planta, define las condiciones actuales del agua y ejecuta la recomendación.</div>",
        unsafe_allow_html=True
    )

    # ---------------------------
    # SELECCION DE PLANTA
    # ---------------------------
    planta_base = st.selectbox(
        "Selecciona la planta",
        ["Caldas", "Diviso"]
    )

    config_key = "Caldas"

    if planta_base == "Diviso":
        modulo_diviso = st.selectbox(
            "Selecciona el módulo de Diviso",
            ["Módulo 500", "Módulo 150"]
        )

        if modulo_diviso == "Módulo 500":
            config_key = "Diviso - Modulo 500"
        else:
            config_key = "Diviso - Modulo 150"

    st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)

    # ---------------------------
    # FUENTE DE DATOS
    # ---------------------------
    st.markdown("<div class='bloque-mini'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-mini'>Fuente de datos</div>", unsafe_allow_html=True)

    fuente_datos = st.radio(
        "Selecciona el origen",
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
            st.error(f"No pude abrir o procesar el archivo: {e}")
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
                st.error(f"No pude leer el archivo subido: {e}")
        else:
            st.info("Sube un archivo Excel para continuar.")

    if df is not None:
        st.caption(f"{CONFIGS[config_key]['nombre_app']} · Filas útiles: {len(df)}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------
    # DATOS DEL CASO ACTUAL
    # ---------------------------
    defaults = valores_por_defecto(config_key)

    st.markdown("<div class='bloque-mini'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-mini'>Datos del caso actual</div>", unsafe_allow_html=True)

    caudal = st.number_input(
        "Caudal a tratar (L/s)",
        value=float(defaults["caudal"]),
        step=1.0
    )

    turbiedad = st.number_input(
        "Turbiedad de agua cruda (UNT)",
        value=float(defaults["turbiedad"]),
        step=0.1
    )

    ph = st.number_input(
        "pH de agua cruda",
        value=float(defaults["ph"]),
        step=0.01,
        format="%.2f"
    )

    alcalinidad_cruda = st.number_input(
        "Alcalinidad de agua cruda (mg/L)",
        value=float(defaults["alcalinidad_cruda"]),
        step=1.0
    )

    alcalinidad_encalada = None
    if CONFIGS[config_key]["usa_alcalinidad_encalada"]:
        alcalinidad_encalada = st.number_input(
            "Alcalinidad de agua encalada (mg/L)",
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
        "Cantidad de datos históricos a evaluar",
        min_value=5,
        max_value=30,
        value=8,
        step=1
    )

    calcular = st.button("Calcular recomendación", use_container_width=True, key="btn_calcular_panel")

    if st.button("Volver al menú", type="secondary", use_container_width=True, key="volver_menu_lateral"):
        st.session_state.vista = "menu"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================
# PANEL DERECHO - RESULTADOS
# =========================================
with col_result:
    st.markdown("<div class='panel-derecho'>", unsafe_allow_html=True)

    st.markdown("<div class='subtitulo-panel'>Resultado de la recomendación</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='texto-panel'>Aquí verás el resumen, dosis sugeridas, casos históricos similares y la relación entre PAC y turbiedad.</div>",
        unsafe_allow_html=True
    )

    if df is None:
        st.info("Primero carga una fuente de datos válida en el panel izquierdo.")
    elif not calcular:
        st.info("Completa los datos del panel izquierdo y presiona «Calcular recomendación».")
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
            r1.metric("Casos usados", resultado["n"])
            r2.metric("PAC promedio", round(resultado["pac_promedio"], 1))
            r3.metric("PAC mínimo", round(resultado["pac_min"], 1))
            r4.metric("PAC máximo", round(resultado["pac_max"], 1))

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

            st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)

            st.markdown("<div class='titulo-seccion-resultado'>Dosis sugeridas para prueba de jarras</div>", unsafe_allow_html=True)
            st.caption(f"Densidad PAC usada: {densidad_pac:.2f} g/mL · Caudal a tratar: {caudal:.2f} L/s")
            st.dataframe(resultado["tabla_jarras"], use_container_width=True)

            st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)

            st.markdown("<div class='titulo-seccion-resultado'>Casos históricos similares</div>", unsafe_allow_html=True)

            st.dataframe(
                resultado["similares_filtrados"].style.format({
                    "Caudal a tratar (L/s)": "{:.1f}",
                    "Turbiedad de agua cruda (UNT)": "{:.1f}",
                    "pH de agua cruda": "{:.2f}",
                    "Alcalinidad de agua cruda (mg/L)": "{:.1f}",
                    "Alcalinidad de agua encalada (mg/L)": "{:.1f}",
                    "Caudal PAC (mL/min)": "{:.1f}",
                    "Distancia": "{:.3f}"
                }),
                use_container_width=True
            )

            st.markdown("<hr class='hr-suave'>", unsafe_allow_html=True)

            st.markdown("<div class='titulo-seccion-resultado'>Visualización</div>", unsafe_allow_html=True)

            df_grafica = resultado["similares_filtrados"].copy()
            df_grafica = df_grafica.sort_values(by="Caudal PAC (mL/min)")

            fig = px.line(
                df_grafica,
                x="Caudal PAC (mL/min)",
                y="Turbiedad de agua cruda (UNT)",
                title="Relación Caudal PAC vs Turbiedad",
                markers=True
            )

            fig.update_traces(
                line=dict(
                    color="#1f77ff",
                    width=2,
                    shape="spline"
                ),
                marker=dict(
                    size=7,
                    color="#1f77ff",
                    line=dict(color="white", width=1)
                )
            )

            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="#0b4f6c"),
                xaxis=dict(
                    title="Caudal PAC (mL/min)",
                    gridcolor="#dbeafe"
                ),
                yaxis=dict(
                    title="Turbiedad de agua cruda (UNT)",
                    gridcolor="#dbeafe"
                ),
                height=460
            )

            st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
