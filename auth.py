import streamlit as st
import base64
from datetime import datetime
import requests
import io
import pandas as pd

# ============================================================
# FUNCIÓN DE REGISTRO GLOBAL (Mantenla aquí o en un utils.py)
# ============================================================
def registrar_acceso_github(usuario, modulo):
    GITHUB_USER = "RH2026"
    GITHUB_REPO = "nexion"
    # Asegúrate de tener el token accesible desde st.secrets
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/auditoria_accesos.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    try:
        r = requests.get(url, headers=headers)
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
        
        csv_string = df_aud.to_csv(index=False)
        payload = {
            "message": f"Registro de acceso de {usuario} al módulo {modulo}",
            "content": base64.b64encode(csv_string.encode()).decode()
        }
        if sha:
            payload["sha"] = sha
        requests.put(url, json=payload, headers=headers)
    except Exception as e:
        # Fallo silencioso para no romper la navegación si falla el log
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
# GUARDAR/OBTENER DESTINO (Igual que antes)
# ============================================================
def guardar_destino(pagina_actual):
    pagina_actual = str(pagina_actual).strip().lower()
    if pagina_actual not in PAGINAS:
        pagina_actual = "dashboard"
    st.session_state["pagina_pendiente"] = pagina_actual
    try:
        st.query_params["return_to"] = pagina_actual
    except Exception:
        pass
    return True

def obtener_destino():
    destino = st.session_state.get("pagina_pendiente", None)
    if destino:
        destino = str(destino).strip().lower()
        if destino in PAGINAS: return destino
    try:
        destino = st.query_params.get("return_to", None)
        if destino:
            destino = str(destino).strip().lower()
            if destino in PAGINAS: return destino
    except Exception:
        pass
    return "dashboard"

# ============================================================
# EXIGIR AUTENTICACIÓN Y REGISTRO
# ============================================================
def exigir_autenticacion(pagina_actual):
    autenticado = st.session_state.get("autenticado", False)

    if not autenticado:
        guardar_destino(pagina_actual)
        st.switch_page("pages/log.py")
        st.stop()
    
    # --- REGISTRO AUTOMÁTICO DE USUARIO ---
    # Esto ocurre cada vez que una página verifica autenticación
    usuario_activo = st.session_state.get("usuario_activo", "GUEST")
    registrar_acceso_github(usuario_activo, pagina_actual.upper())
