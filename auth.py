import streamlit as st


# ============================================================
# PÁGINAS DISPONIBLES
# ============================================================

PAGINAS = {
    "accesscontrol": "pages/accesscontrol.py",
    "asignacionfletera": "pages/asignacionfletera.py",
    "entregas_agc": "pages/entregas_agc.py",
    "envios": "pages/envios.py",
    "etiquetas": "pages/etiquetas.py",
    "indicadores": "pages/indicadores.py",
    "locales": "pages/locales.py",
    "log": "pages/log.py",
    "muestras": "pages/muestras.py",
    "picking": "pages/picking.py",
    "qrup": "pages/qrup.py",
}


# ============================================================
# GUARDAR PÁGINA DESTINO
# ============================================================

def guardar_destino(pagina_actual):

    # --------------------------------------------------------
    # Normalizar nombre
    # --------------------------------------------------------

    pagina_actual = str(
        pagina_actual
    ).strip().lower()


    # --------------------------------------------------------
    # Validar página
    # --------------------------------------------------------

    if pagina_actual not in PAGINAS:
        return False


    # --------------------------------------------------------
    # GUARDAR EN SESSION STATE
    #
    # Esto permite conservar el destino mientras navegamos
    # entre las páginas de Streamlit.
    # --------------------------------------------------------

    st.session_state["pagina_pendiente"] = (
        pagina_actual
    )


    # --------------------------------------------------------
    # GUARDAR TAMBIÉN EN LA URL
    #
    # Esto funciona como respaldo.
    # --------------------------------------------------------

    st.query_params["return_to"] = (
        pagina_actual
    )


    return True


# ============================================================
# OBTENER DESTINO
# ============================================================

def obtener_destino():

    # --------------------------------------------------------
    # PRIMERA OPCIÓN:
    # SESSION STATE
    # --------------------------------------------------------

    destino = st.session_state.get(
        "pagina_pendiente",
        None
    )

    if destino:

        destino = str(
            destino
        ).strip().lower()

        if destino in PAGINAS:

            return destino


    # --------------------------------------------------------
    # SEGUNDA OPCIÓN:
    # QUERY PARAMS
    # --------------------------------------------------------

    try:

        destino = st.query_params.get(
            "return_to",
            None
        )

        if destino:

            destino = str(
                destino
            ).strip().lower()

            if destino in PAGINAS:

                return destino

    except Exception:

        pass


    # --------------------------------------------------------
    # NO SE ENCONTRÓ DESTINO
    # --------------------------------------------------------

    return None


# ============================================================
# ENVIAR AL LOGIN
# ============================================================

def ir_a_login(pagina_actual):

    # --------------------------------------------------------
    # Guardar exactamente la página actual
    # --------------------------------------------------------

    destino_guardado = guardar_destino(
        pagina_actual
    )


    # --------------------------------------------------------
    # Si la página no existe en nuestro mapa,
    # usamos indicadores como último recurso.
    # --------------------------------------------------------

    if not destino_guardado:

        guardar_destino(
            "indicadores"
        )


    # --------------------------------------------------------
    # IR AL LOGIN
    #
    # IMPORTANTE:
    # log.py está dentro de /pages
    # --------------------------------------------------------

    st.switch_page(
        "pages/log.py"
    )


# ============================================================
# EXIGIR AUTENTICACIÓN
# ============================================================

def exigir_autenticacion(pagina_actual):

    autenticado = st.session_state.get(
        "autenticado",
        False
    )


    # --------------------------------------------------------
    # SI NO ESTÁ AUTENTICADO
    # --------------------------------------------------------

    if not autenticado:

        ir_a_login(
            pagina_actual
        )

        st.stop()
