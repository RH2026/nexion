import streamlit as st
import base64
from datetime import datetime
import requests
import io
import pandas as pd
import time

# ============================================================
# FUNCIÓN DE REGISTRO GLOBAL (OPTIMIZADA)
# ============================================================
def registrar_acceso_github(usuario, modulo):
    # Control: No registrar si ya se registró el mismo módulo en los últimos 30 segundos
    clave_sesion = f"ultimo_registro_{modulo}"
    ahora = time.time()
    if st.session_state.get(clave_sesion, 0) + 30 > ahora:
        return 

    st.session_state[clave_sesion] = ahora

    GITHUB_USER = "RH2026"
    GITHUB_REPO = "nexion"
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/auditoria_accesos.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    try:
        r = requests.get(url, headers=headers, timeout=3)
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if r.status_code == 200:
            file_data = r.json()
            sha = file_data.get("sha", "")
            content_decoded = base64.b64decode(file_data.get("content", "")).decode("utf-8")
            df_aud = pd.read_csv(io.StringIO(content_decoded))
        else:
            df_aud = pd.DataFrame(columns=["FECHA_HORA", "USUARIO", "MODULO"])
            sha = ""

        nuevo_registro = pd.DataFrame([{"FECHA_HORA": fecha_hora, "USUARIO": usuario, "MODULO": modulo}])
        df_aud = pd.concat([df_aud, nuevo_registro], ignore_index=True)
        
        # Mantener solo los últimos 200 para velocidad
        if len(df_aud) > 200:
            df_aud = df_aud.tail(200)
        
        csv_string = df_aud.to_csv(index=False)
        payload = {
            "message": f"Registro de acceso de {usuario} al módulo {modulo}",
            "content": base64.b64encode(csv_string.encode()).decode()
        }
        if sha:
            payload["sha"] = sha
        requests.put(url, json=payload, headers=headers, timeout=3)
    except Exception:
        pass 

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
# EXIGIR AUTENTICACIÓN Y REGISTRO (BLINDADO)
# ============================================================
def exigir_autenticacion(pagina_actual):
    if not st.session_state.get("autenticado", False):
        guardar_destino(pagina_actual)
        st.switch_page("pages/log.py")
        st.stop()
    
    # Registro automático (solo si el usuario está autenticado)
    usuario_activo = str(st.session_state.get("usuario_activo", "GUEST"))
    registrar_acceso_github(usuario_activo, pagina_actual.upper())
