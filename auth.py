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
# FUNCIONES DE NAVEGACIÓN
# ============================================================
def guardar_destino(pagina_actual):
    pagina_actual = str(pagina_actual).strip().lower()
    st.session_state["pagina_pendiente"] = pagina_actual if pagina_actual in PAGINAS else "dashboard"
    try:
        st.query_params["return_to"] = st.session_state["pagina_pendiente"]
    except Exception:
        pass
    return True

# ============================================================
# EXIGIR AUTENTICACIÓN
# ============================================================
def exigir_autenticacion(pagina_actual):
    if not st.session_state.get("autenticado", False):
        guardar_destino(pagina_actual)
        st.switch_page("pages/log.py")
        st.stop()
