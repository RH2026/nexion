import streamlit as st


# ============================================================
# AUTENTICACIÓN Y REGRESO A LA PÁGINA ANTERIOR
# ============================================================

PAGINAS = {
    "accesscontrol": "pages/accesscontrol.py",
    "asignacionfletera": "pages/asignacionfletera.py",
    "entregas_agc": "pages/entregas_agc.py",
    "envios": "pages/envios.py",
    "etiquetas": "pages/etiquetas.py",
    "indicadores": "pages/indicadores.py",
    "log": "pages/log.py",
    "muestras": "pages/muestras.py",
    "grup": "pages/qrup.py",
}


def ir_a_login(pagina_actual):

    pagina_actual = str(
        pagina_actual
    ).strip().lower()

    if pagina_actual not in PAGINAS:
        pagina_actual = "indicadores"

    # Guardamos únicamente el destino.
    # NO usamos "page".
    st.query_params["return_to"] = pagina_actual

    st.switch_page("app_clean.py")


def exigir_autenticacion(pagina_actual):

    if not st.session_state.get(
        "autenticado",
        False
    ):

        ir_a_login(
            pagina_actual
        )

        st.stop()
