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
    "dashboard": "dashboard.py",
    "locales": "pages/locales.py",
    "log": "log.py",
    "muestras": "pages/muestras.py",
    "picking": "pages/picking.py",
    "qrup": "pages/qrup.py",
    "facturacion": "pages/facturacion_af.py",
}


# ============================================================
# GUARDAR DESTINO
# ============================================================

def guardar_destino(pagina_actual):

    pagina_actual = str(
        pagina_actual
    ).strip().lower()

    if pagina_actual not in PAGINAS:
        pagina_actual = "dashboard"

    st.session_state["pagina_pendiente"] = pagina_actual

    try:
        st.query_params["return_to"] = pagina_actual
    except Exception:
        pass

    return True


# ============================================================
# OBTENER DESTINO
# ============================================================

def obtener_destino():

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

    return "dashboard"


# ============================================================
# EXIGIR AUTENTICACIÓN
# ============================================================

def exigir_autenticacion(pagina_actual):

    autenticado = st.session_state.get(
        "autenticado",
        False
    )

    if not autenticado:

        guardar_destino(
            pagina_actual
        )

        st.switch_page("pages/log.py")

        st.stop()
