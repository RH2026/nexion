import streamlit as st


# ============================================================
# AUTENTICACIÓN Y REGRESO A LA PÁGINA SOLICITADA
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
# ENVIAR AL LOGIN
# ============================================================

def ir_a_login(pagina_actual):

    # --------------------------------------------------------
    # Normalizar nombre de página
    # --------------------------------------------------------

    pagina_actual = str(
        pagina_actual
    ).strip().lower()


    # --------------------------------------------------------
    # Validar que la página exista
    # --------------------------------------------------------

    if pagina_actual not in PAGINAS:

        pagina_actual = "indicadores"


    # --------------------------------------------------------
    # Guardar la página que el usuario quería abrir
    #
    # Ejemplo:
    #
    # indicadores
    # envios
    # etiquetas
    #
    # --------------------------------------------------------

    st.query_params["return_to"] = pagina_actual


    # --------------------------------------------------------
    # Ir al LOGIN
    #
    # El login está dentro de /pages
    # --------------------------------------------------------

    st.switch_page(
        "pages/log.py"
    )


# ============================================================
# EXIGIR AUTENTICACIÓN
# ============================================================

def exigir_autenticacion(pagina_actual):

    # --------------------------------------------------------
    # Revisar si existe una sesión autenticada
    # --------------------------------------------------------

    autenticado = st.session_state.get(
        "autenticado",
        False
    )


    # --------------------------------------------------------
    # Si NO está autenticado:
    #
    # 1. Guardamos la página solicitada
    # 2. Mandamos al login
    # 3. Detenemos la ejecución
    # --------------------------------------------------------

    if not autenticado:

        ir_a_login(
            pagina_actual
        )

        st.stop()
