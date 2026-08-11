import base64
from datetime import datetime
import io
import re
import time
import unicodedata
import zipfile
import calendar
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit.components.v1 as components
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Centro de Control",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── TEMA Y CSS MAESTROS ──────────────────────────────────────────
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
    "logo": "n1.png",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* --- ANIMACIONES DE ENTRADA --- */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(15px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

[data-testid="stVerticalBlock"] > div:not(:has(.footer)) {{
    animation: fadeInUp 0.6s ease-out;
}}

/* --- OCULTAR ELEMENTOS DE STREAMLIT Y SIDEBAR --- */
header, footer, [data-testid="stHeader"] {{
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}}

[data-testid="collapsedControl"], 
[data-testid="stSidebar"], 
[data-testid="stToolbar"], 
.viewerBadge_container__1QSob, 
#MainMenu, 
button[kind="header"] {{
    visibility: hidden !important;
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

/* APP BASE */
html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}

.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 5rem !important;
    background-color: {vars_css['bg']} !important;
}}

/* BOTONES SLIM Y BOTONES DE DESCARGA GENERALES */
div.stButton > button, div.stDownloadButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 28px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

/* --- ESTILO NEXION AMPLIADO PARA EL DATA EDITOR --- */
[data-testid="stDataFrame"] {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}}

/* --- SEPARACIÓN EQUILIBRADA EN EL POPOVER --- */
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {{
    gap: 0.35rem !important;
}}

div[data-testid="stPopoverBody"] .stButton {{
    margin-bottom: 4px !important;
}}

div[data-testid="stPopoverBody"] [data-testid="stExpander"] {{
    border: none !important;
    background: transparent !important;
    margin-bottom: 4px !important;
    > div {{
        padding: 0 !important;
    }}
}}

/*FOOTER FIJO BLINDADO */
.footer {{ 
    position: fixed !important; 
    bottom: 0 !important; 
    left: 0 !important; 
    width: 100% !important; 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['sub']} !important; 
    text-align: center; 
    padding: 12px 0px !important; 
    font-size: 9px; 
    letter-spacing: 2px; 
    border-top: 1px solid {vars_css['border']} !important; 
    z-index: 999999 !important; 
    animation: none !important;
    transform: none !important;
    opacity: 1 !important;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. SISTEMA DE SEGURIDAD PRO (VALIDACIÓN DE SESIÓN)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/accesscontrol.py"
    st.switch_page("pages/log.py")

# Validación exclusiva para Rigoberto (Admin supremo)
usuario_actual_val = st.session_state.get("usuario_activo", "").upper()
if usuario_actual_val != "RIGOBERTO":
    st.markdown(
        f"""
        <div style="
            background: {vars_css['card']}; 
            border: 1px solid {vars_css['border']}; 
            border-left: 5px solid #FFD700; 
            padding: 20px 25px; 
            border-radius: 8px; 
            width: 100%; 
            font-family: 'Inter', sans-serif; 
            color: white; 
            box-sizing: border-box; 
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        ">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <div style="width: 10px; height: 10px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 8px #FFD700;"></div>
                <span style="color: #FFD700; font-size: 13px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">
                    ACCESS RESTRICTED // NIVEL INSUFICIENTE
                </span>
            </div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 600; padding-left: 20px;">
                Módulo exclusivo para administración central. Credenciales de operador estándar detectadas.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col_regresar, col_vacia = st.columns([1.5, 4])
    with col_regresar:
        if st.button("REGRESAR AL PANEL PRINCIPAL", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.login_exitoso = False
            st.switch_page("pages/log.py")
            
    st.stop()


# ==========================================
# 3. CONFIGURACIÓN GITHUB PARA PERMISOS Y AUDITORÍA
# ==========================================
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

def asegurar_y_actualizar_matriz_en_github():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/permisos_usuarios.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    
    if r.status_code == 200:
        return 

    df_default = pd.DataFrame([
        {
            "USUARIO": "Rigoberto", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": True, "ENFOQUE": True, "ACCESS CONTROL": True,
            "ALERTAS": True, "GANTT": True, "QUEJAS": True, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": True, "ANALISIS MENSUAL": True, "DETALLE COSTOS": True, "ENVIOS ESPECIALES": True, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": True,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": True, "CAJA CHICA": True, "GASTOS": True, "MORENO": True, "VAZQUEZ": True, "MIGUEL": True
        },
        {
            "USUARIO": "AGomez", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": False, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "JMoreno", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": True, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": True, "QUEJAS": True, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": True,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": True, "VAZQUEZ": True, "MIGUEL": True
        },
        {
            "USUARIO": "Cynthia", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": True, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "Brenda", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": False, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "Fialko", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": False, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "Atencion3G", 
            "DASHBOARD": False, "SEGUIMIENTO": False, "ENTREGAS": False, "REPORTES": False, "FORMATOS": False, "CENTRO DE DATOS": False, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": False, "GANTT": False, "QUEJAS": False, "AGC": False, "AMAZON": False, "BARCELO": False, "NACIONAL": False,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": False, "PANEL MUESTRAS": False,
            "SALIDA DE PT": False, "CHECK LIST AGC": False, "QR AGC": False, "PREGUIA PAQMEX": False, "RECOLECCION 3G": False, "RECOLECCION ONE": False, "CARTA RECLAMO": False, "COTIZACIONES": False,
            "ASIGNAR FLETERA": False, "CARGAR DATOS": False, "ETIQUETAS": False, "ESCANEAR QR": False, "HERRAMIENTAS": False, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "Claudia", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": False, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "Ruth", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": False, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "Carlos", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": True, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": True, "QUEJAS": True, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": True, "ANALISIS MENSUAL": True, "DETALLE COSTOS": True, "ENVIOS ESPECIALES": True, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": True,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": True, "VAZQUEZ": True, "MIGUEL": True
        },
        {
            "USUARIO": "Sandra", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": False, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "ASanchez", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": False, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        },
        {
            "USUARIO": "MarthaC", 
            "DASHBOARD": True, "SEGUIMIENTO": True, "ENTREGAS": True, "REPORTES": True, "FORMATOS": True, "CENTRO DE DATOS": True, "FINANZAS": False, "ENFOQUE": False, "ACCESS CONTROL": False,
            "ALERTAS": True, "GANTT": False, "QUEJAS": False, "AGC": True, "AMAZON": True, "BARCELO": True, "NACIONAL": True,
            "COSTOS CEDIS": False, "ANALISIS MENSUAL": False, "DETALLE COSTOS": False, "ENVIOS ESPECIALES": False, "ENVIO DE MUESTRAS": True, "PANEL MUESTRAS": False,
            "SALIDA DE PT": True, "CHECK LIST AGC": True, "QR AGC": True, "PREGUIA PAQMEX": True, "RECOLECCION 3G": True, "RECOLECCION ONE": True, "CARTA RECLAMO": True, "COTIZACIONES": True,
            "ASIGNAR FLETERA": True, "CARGAR DATOS": True, "ETIQUETAS": True, "ESCANEAR QR": True, "HERRAMIENTAS": True, "WALLET": False, "CAJA CHICA": False, "GASTOS": False, "MORENO": False, "VAZQUEZ": False, "MIGUEL": False
        }
    ])

    csv_string = df_default.to_csv(index=False)
    payload = {
        "message": "Inicialización de matriz completa con submenús y ESCANEAR QR",
        "content": base64.b64encode(csv_string.encode()).decode()
    }
    requests.put(url, json=payload, headers=headers)

asegurar_y_actualizar_matriz_en_github()

# Función para registrar acceso automáticamente en auditoría y sincronizar con GitHub
def registrar_acceso_github(usuario, modulo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/auditoria_accesos.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
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

    # Agregar nuevo registro
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

# Registrar la visita actual a Access Control
usuario_actual = st.session_state.get("usuario_activo", "GUEST")
registrar_acceso_github(usuario_actual, "ACCESS CONTROL")

def cargar_matriz_permisos():
    if "df_permisos_local" in st.session_state:
        return st.session_state["df_permisos_local"]

    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/main/permisos_usuarios.csv?nocache={int(time.time())}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).upper().strip() for c in df.columns]
        st.session_state["df_permisos_local"] = df
        return df
    except Exception as e:
        return pd.DataFrame()

def guardar_matriz_en_github(df_actualizado):
    st.session_state["df_permisos_local"] = df_actualizado

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/permisos_usuarios.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    r_get = requests.get(url, headers=headers)
    sha = ""
    if r_get.status_code == 200:
        sha = r_get.json().get("sha", "")

    csv_string = df_actualizado.to_csv(index=False)
    payload = {
        "message": "Actualización de matriz de permisos desde Access Control",
        "content": base64.b64encode(csv_string.encode()).decode()
    }
    
    if sha:
        payload["sha"] = sha
        
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code in [200, 201]

@st.cache_data(ttl=15)
def cargar_datos_auditoria():
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/main/auditoria_accesos.csv?nocache={int(time.time())}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception:
        return pd.DataFrame(columns=["FECHA_HORA", "USUARIO", "MODULO"])


# ==========================================
# 4. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================
@st.cache_data(ttl=60)
def obtener_matriz_github():
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/main/matriz_historial.csv?nocache={int(time.time())}"
    try:
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def cargar_datos_dashboard():
    t = int(time.time())
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
    try:
        df = pd.read_csv(url, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return None

def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    ).upper()
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    return " ".join(texto.split())


# Inicialización segura de estados de menú
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "ACCESS CONTROL"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "SETTINGS"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1
if "tipo_resultado" not in st.session_state:
    st.session_state.tipo_resultado = "OPERACION"


# ==========================================
# 5. HEADER CON 4 COLUMNAS
# ==========================================
header_zone = st.container()
with header_zone:
    c1, c2, c3, c4 = st.columns([1.5, 3.5, 0.9, 0.9], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=160)
        except:
            st.write("**NEXION**")

    with c2:
        texto_principal = st.session_state.menu_main
        azul_nexion = "#82D4E6"
        oro_brillante = "#FFD700"

        if texto_principal == "DASHBOARD":
            texto_principal = f"NEXION <span style='color: {azul_nexion}; font-weight: 500; margin: 0 10px; font-size: 16px;'>|</span> SMART LOGISTICS"

        if st.session_state.menu_sub != "GENERAL":
            ruta = (
                f"{texto_principal} "
                f"<span style='color: {azul_nexion}; opacity: 0.8; margin: 0 15px;'>/</span> "
                f"<span style='color: {oro_brillante}; font-weight: 500; text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);'>"
                f"{st.session_state.menu_sub}</span>"
            )
        else:
            ruta = texto_principal

        st.markdown(
            f"""
            <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
                <p style='font-size: 13px; letter-spacing: 5px; color: {vars_css['sub']}; margin: 0; font-weight: 500; text-transform: uppercase; text-align: center;'>
                    {ruta}
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with c3:
        es_atencion3g = (
            st.session_state.get("usuario_activo", "").upper() == "ATENCION3G"
        )
        key_actual = f"main_search_v{st.session_state.search_key_version}"

        query = st.text_input(
            "Buscar",
            placeholder="🔍 BUSCADOR DESACTIVADO" if es_atencion3g else "🔍 Buscar...",
            label_visibility="collapsed",
            key=key_actual,
            disabled=es_atencion3g,
        )

        if query:
            url_raw = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
            try:
                df_matriz_fresco = pd.read_csv(url_raw)
                df_matriz_fresco.columns = df_matriz_fresco.columns.str.strip()
            except Exception:
                df_matriz_fresco = cargar_datos_dashboard()

            res_ops = pd.DataFrame()
            if df_matriz_fresco is not None:
                cols_op = [
                    "NÚMERO DE GUÍA",
                    "NÚMERO DE PEDIDO",
                    "NO CLIENTE",
                    "NOMBRE DEL CLIENTE",
                    "DESTINO",
                ]
                cols_op_disp = [c for c in cols_op if c in df_matriz_fresco.columns]
                if cols_op_disp:
                    mask_ops = df_matriz_fresco[cols_op_disp].astype(str).apply(
                        lambda x: x.str.contains(query, case=False, na=False)
                    ).any(axis=1)
                    res_ops = df_matriz_fresco[mask_ops].copy()

            res_t1 = pd.DataFrame()
            try:
                df_t1_temp = pd.read_excel("T1.xlsx") 
                df_t1_temp.columns = df_t1_temp.columns.str.strip().str.upper()
                cols_t1 = [c for c in ["OBSERVACION 1", "TALON", "DESTINATARIO", "DESTINO"] if c in df_t1_temp.columns]
                if cols_t1:
                    mask_t1 = df_t1_temp[cols_t1].astype(str).apply(
                        lambda x: x.str.contains(query, case=False, na=False)
                    ).any(axis=1)
                    match_t1 = df_t1_temp[mask_t1].copy()
                    if not match_t1.empty:
                        match_t1 = match_t1.rename(columns={
                            "TALON": "NÚMERO DE GUÍA",
                            "OBSERVACION 1": "NÚMERO DE PEDIDO",
                            "DESTINATARIO": "NOMBRE DEL CLIENTE",
                            "SUBTOTAL": "COSTO DE LA GUÍA",
                            "F.DOC": "FECHA DE ENVÍO",
                            "BULTOS": "CANTIDAD DE CAJAS"
                        })
                        match_t1["FLETERA"] = "TRES GUERRAS"
                        res_t1 = match_t1
            except Exception:
                pass

            if not res_ops.empty and not res_t1.empty:
                for idx, row in res_ops.iterrows():
                    guia_actual = str(row.get("NÚMERO DE GUÍA", "")).strip()
                    if guia_actual in ["", "nan", "0", "None"]:
                        pedido_global = str(row.get("NÚMERO DE PEDIDO", "")).strip()
                        match_en_t1 = res_t1[res_t1["NÚMERO DE PEDIDO"].astype(str).str.strip() == pedido_global]
                        if not match_en_t1.empty:
                            res_ops.loc[idx, "NÚMERO DE GUÍA"] = match_en_t1.iloc[0].get("NÚMERO DE GUÍA", guia_actual)
                            res_ops.loc[idx, "FLETERA"] = match_en_t1.iloc[0].get("FLETERA", "TRES GUERRAS")
                            if "COSTO DE LA GUÍA" in match_en_t1.columns and pd.notna(match_en_t1.iloc[0].get("COSTO DE LA GUÍA")):
                                res_ops.loc[idx, "COSTO DE LA GUÍA"] = match_en_t1.iloc[0].get("COSTO DE LA GUÍA")

            res_inv = pd.DataFrame()
            if res_ops.empty and res_t1.empty:
                try:
                    df_inv_temp = pd.read_csv("inventario.csv")
                    df_inv_temp.columns = df_inv_temp.columns.str.strip()
                    cols_inv = [c for c in ["CODIGO", "DESCRIPCION"] if c in df_inv_temp.columns]
                    if cols_inv:
                        mask_inv = df_inv_temp[cols_inv].astype(str).apply(
                            lambda x: x.str.contains(query, case=False, na=False)
                        ).any(axis=1)
                        res_inv = df_inv_temp[mask_inv]
                except Exception:
                    pass

            if not res_ops.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "OPERACION"
                st.session_state.resultado_busqueda = res_ops
            elif not res_t1.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "OPERACION" 
                st.session_state.resultado_busqueda = res_t1
            elif not res_inv.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "INVENTARIO"
                st.session_state.resultado_busqueda = res_inv
            else:
                st.session_state.busqueda_activa = False
                st.session_state.resultado_busqueda = None
                st.toast("Sin resultados: No se encontró en Matriz Global ni en T1", icon="⚠️")

    with c4:
        with st.popover("☰ Menú", use_container_width=True):
            usuario = st.session_state.get("usuario_activo", "GUEST")
            nombre_display = st.session_state.get("nombre_completo", "OPERADOR DESCONOCIDO")
        
            es_rigoberto = usuario.upper() == "RIGOBERTO"
            permisos = st.session_state.get("permisos", {})
            
            def tiene_permiso(clave):
                if es_rigoberto:
                    return True
                return permisos.get(clave, False)
        
            st.markdown(
                f"""
                <div style='background-color: rgba(255,255,255,0.05); padding: 8px 10px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #00D4FF;'>
                    <p style='color:#00D4FF; font-size:9px; font-weight:500; margin:0; letter-spacing:1px;'>USUARIO ACTIVO</p>
                    <p style='color:{vars_css['text']}; font-size:13px; font-weight:500; margin:0;'>{nombre_display.upper()}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )        
                    
            if tiene_permiso("DASHBOARD"):
                if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                    registrar_acceso_github(usuario, "DASHBOARD")
                    st.session_state.menu_main = "DASHBOARD"
                    st.session_state.menu_sub = "GENERAL"
                    st.session_state.busqueda_activa = False
                    st.switch_page("pages/indicadores.py")
                    st.rerun()
        
            if tiene_permiso("SEGUIMIENTO"):
                with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                    opciones_seg_posibles = ["ALERTAS", "GANTT", "QUEJAS"]
                    opciones_seg = [s for s in opciones_seg_posibles if tiene_permiso(s)]
                    for s in opciones_seg:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_sub_{s}"):
                            registrar_acceso_github(usuario, f"SEGUIMIENTO - {s}")
                            st.session_state.menu_main = "SEGUIMIENTO"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if tiene_permiso("ENTREGAS"):
                with st.expander("ENTREGAS", expanded=(st.session_state.menu_main == "ENTREGAS")):
                    opciones_ent_posibles = ["AGC", "AMAZON", "BARCELO", "NACIONAL"]
                    opciones_ent = [s for s in opciones_ent_posibles if tiene_permiso(s)]
                    for s in opciones_ent:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_ent_{s}"):
                            registrar_acceso_github(usuario, f"ENTREGAS - {s}")
                            st.session_state.menu_main = "ENTREGAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "AGC":
                                st.switch_page("pages/entregas_agc.py")
                            elif s == "NACIONAL":
                                st.switch_page("pages/envios.py")
                            else:
                                st.rerun()
        
            if tiene_permiso("REPORTES"):
                with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                    opciones_rep_posibles = ["COSTOS CEDIS", "ANALISIS MENSUAL", "DETALLE COSTOS", "ENVIOS ESPECIALES", "ENVIO DE MUESTRAS"]
                    opciones_rep = [s for s in opciones_rep_posibles if tiene_permiso(s)]
                    for s in opciones_rep:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_rep_{s}"):
                            registrar_acceso_github(usuario, f"REPORTES - {s}")
                            st.session_state.menu_main = "REPORTES"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "ENVIO DE MUESTRAS":
                                st.switch_page("pages/muestras.py")
                            else:
                                st.rerun()
        
            if tiene_permiso("FORMATOS"):
                with st.expander("FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")):
                    opciones_for_posibles = ["SALIDA DE PT", "CHECK LIST AGC", "QR AGC", "PREGUIA PAQMEX", "RECOLECCION 3G", "RECOLECCION ONE", "CARTA RECLAMO", "COTIZACIONES"]
                    opciones_for = [s for s in opciones_for_posibles if tiene_permiso(s)]
                    for s in opciones_for:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_for_{s}"):
                            registrar_acceso_github(usuario, f"FORMATOS - {s}")
                            st.session_state.menu_main = "FORMATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if tiene_permiso("CENTRO DE DATOS"):
                with st.expander("CENTRO DE DATOS", expanded=(st.session_state.menu_main == "CENTRO DE DATOS")):
                    opciones_hub_posibles = ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "ESCANEAR QR", "HERRAMIENTAS"]
                    opciones_hub = [s for s in opciones_hub_posibles if tiene_permiso(s)]
                    for s in opciones_hub:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_hub_{s}"):
                            registrar_acceso_github(usuario, f"CENTRO DE DATOS - {s}")
                            st.session_state.menu_main = "CENTRO DE DATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "ASIGNAR FLETERA":
                                st.switch_page("pages/asignacionfletera.py")
                            elif s == "ETIQUETAS":
                                st.switch_page("pages/etiquetas.py")
                            elif s == "ESCANEAR QR":
                                st.switch_page("pages/qrup.py")
                            else:
                                st.rerun()
        
            if tiene_permiso("FINANZAS"):
                with st.expander("FINANZAS", expanded=(st.session_state.menu_main == "FINANZAS")):
                    opciones_fin_posibles = ["WALLET", "CAJA CHICA", "GASTOS"]
                    opciones_fin = [s for s in opciones_fin_posibles if tiene_permiso(s)]
                    for s in opciones_fin:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_fin_{s}"):
                            registrar_acceso_github(usuario, f"FINANZAS - {s}")
                            st.session_state.menu_main = "FINANZAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()

            if tiene_permiso("ENFOQUE"):
                with st.expander("ENFOQUE", expanded=(st.session_state.get("menu_main") == "ENFOQUE")):
                    opciones_enf_posibles = ["MORENO", "VAZQUEZ", "MIGUEL"]
                    opciones_enf = [s for s in opciones_enf_posibles if tiene_permiso(s)]
                    for s in opciones_enf:
                        label = f"» {s}" if st.session_state.get("menu_sub") == s else s
                        if st.button(label, use_container_width=True, key=f"pop_enf_{s}"):
                            registrar_acceso_github(usuario, f"ENFOQUE - {s}")
                            st.session_state.menu_main = "ENFOQUE"
                            st.session_state.menu_sub = s
                            st.rerun()
        
            if tiene_permiso("ACCESS CONTROL") or es_rigoberto:
                if st.button("ACCESS CONTROL", use_container_width=True, key="pop_access_ctrl"):
                    registrar_acceso_github(usuario, "ACCESS CONTROL")
                    st.session_state.menu_main = "ACCESS CONTROL"
                    st.session_state.menu_sub = "SETTINGS"
                    st.switch_page("pages/accesscontrol.py")
        
            st.markdown("<hr style='margin: 4px 0; opacity: 0.1;'>", unsafe_allow_html=True)
            if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.autenticado = False
                st.session_state.splash_completado = False
                st.rerun()

    # ── RENDERIZADO DE RESULTADOS ──────────────────────────────────────────
    if st.session_state.busqueda_activa and st.session_state.resultado_busqueda is not None:
        resultados = st.session_state.resultado_busqueda
        total = len(resultados)
        tipo = st.session_state.get("tipo_resultado", "OPERACION")
        accent_color = "#00FFAA"
        inv_color = "#36b9cc"
        azul_premium = "#00D4FF"

        col_espacio, col_cerrar = st.columns([0.85, 0.15])
        with col_cerrar:
            if st.button("✕ CERRAR", key="btn_cerrar_top", use_container_width=True):
                st.session_state.busqueda_activa = False
                st.session_state.resultado_busqueda = None
                st.session_state.search_key_version += 1
                st.rerun()

        if tipo == "INVENTARIO":
            st.markdown(f"<style>.card-inv {{ transition: all 0.3s ease; cursor: pointer; }} .card-inv:hover {{ transform: translateX(8px); border-color: {inv_color} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(54, 185, 204, 0.1); }}</style>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:15px;'><div style='background:{inv_color};width:5px;height:20px;border-radius:2px;box-shadow:0 0 10px {inv_color};'></div><span style='color:white;font-size:14px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;'>EXISTENCIAS EN INVENTARIO <span style='color:{inv_color};'>({total})</span></span></div>", unsafe_allow_html=True)
            for _, i in resultados.iterrows():
                st.markdown(f"<div class='card-inv' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {inv_color};border-radius:10px;padding:10px 20px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CÓDIGO / SKU</span><br><b style='font-size:16px;color:{inv_color};letter-spacing:1px;'>{i.get('CODIGO','')}</b></div><div style='flex:3;padding-left:20px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>DESCRIPCIÓN</span><br><span style='font-size:13px;color:white;font-weight:600;line-height:1.2;'>{i.get('DESCRIPCION','')}</span></div><div style='flex:1;text-align:right;'><span style='background:{inv_color}15;color:{inv_color};padding:3px 8px;border-radius:4px;font-size:9px;font-weight:800;border:1px solid {inv_color}30;text-transform:uppercase;'>DISPONIBLE</span></div></div>", unsafe_allow_html=True)
        else:
            if total == 1:
                envio = resultados.iloc[0]
                entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
                f_entrega_val = envio["FECHA DE ENTREGA REAL"] if entregado_real else "PENDIENTE"

                trigger_val = str(envio.get("TRIGGER", "")).strip()
                tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]

                if tiene_guia:
                    n_guia = envio["NÚMERO DE GUÍA"]
                elif trigger_val == "Enviada":
                    n_guia = "GENERANDO GUÍA..."
                else:
                    n_guia = "EN ESPERA DE SURTIDO"

                f_promesa_dt = pd.to_datetime(envio.get("PROMESA DE ENTREGA"), dayfirst=True, errors="coerce")
                if pd.notnull(f_promesa_dt):
                    f_promesa_dt = f_promesa_dt.normalize()
                hoy = pd.Timestamp(datetime.now()).normalize()

                if not tiene_guia:
                    status_text, status_color = ("GENERANDO GUÍA", "#38bdf8") if trigger_val == "Enviada" else ("SURTIENDO", "#FFA500")
                elif not entregado_real:
                    status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if pd.isna(f_promesa_dt) or hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
                else:
                    f_entrega_dt = pd.to_datetime(envio.get("FECHA DE ENTREGA REAL"), dayfirst=True, errors="coerce")
                    if pd.notnull(f_entrega_dt):
                        f_entrega_dt = f_entrega_dt.normalize()
                    status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.isna(f_promesa_dt) or f_entrega_dt <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")

                tarjeta_unica_html = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 20px 25px; border-radius: 8px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;"><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #38bdf8; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #38bdf8;"></div><div style="font-size: 9px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;">ENVÍO</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('FECHA DE ENVÍO','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #38bdf8; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #a855f7; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #a855f7;"></div><div style="font-size: 9px; font-weight: 800; color: #a855f7; letter-spacing: 1px;">GUÍA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{n_guia if tiene_guia else 'EN PROCESO'}</div></div><div style="flex-grow: 1; height: 2px; background: #a855f7; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #eab308; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #eab308;"></div><div style="font-size: 9px; font-weight: 800; color: #eab308; letter-spacing: 1px;">PROMESA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('PROMESA DE ENTREGA','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #00FFAA; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: {status_color}; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px {status_color};"></div><div style="font-size: 9px; font-weight: 800; color: {status_color}; letter-spacing: 1px;">ENTREGA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{f_entrega_val}</div></div></div><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;"><div style="flex: 1.2; min-width: 200px;"><div style="color: {accent_color}; font-size: 16px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">{envio.get('FLETERA','N/A')}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">TALÓN / FOLIO</div><div style="color: {accent_color}; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{n_guia}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">REF / PEDIDO: <span style="color: white; font-size: 13px; font-weight: 700;">{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div></div><div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / CLIENTE</div><div style="color: white; font-weight: 800; font-size: 13px; text-transform: uppercase; line-height: 1.3; margin-top: 2px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div><div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 2px;">ID: {envio.get('NO CLIENTE','')} | {envio.get('DOMICILIO','')}</div><div style="font-size: 11px; color: {accent_color}; margin-top: 4px; font-weight: 600;">📍 GDL → {envio.get('DESTINO','N/A')}</div></div><div style="flex: 1.2; min-width: 150px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN CARGA</div><div style="color: white; font-weight: 700; font-size: 11px; margin-top: 2px;">BULTOS: <span style="color: {accent_color};">{envio.get('CANTIDAD DE CAJAS','0')}</span></div><div style="color: {accent_color}; font-weight: 800; font-size: 13px; margin-top: 2px;">$ {envio.get('COSTO DE LA GUÍA','0.00')}</div></div><div style="text-align: right; min-width: 130px;"><span style="background-color: {status_color}15; color: {status_color}; padding: 5px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; border: 1px solid {status_color}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">ESTATUS: {status_text}</span></div></div></div>"""
                st.markdown(tarjeta_unica_html, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'><div style='background: {azul_premium}; width: 5px; height: 22px; border-radius: 3px; box-shadow: 0 0 10px {azul_premium};'></div><span style='color: white; font-size: 15px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;'>MULTIPLE MATCHES DETECTED <span style='color: {azul_premium};'>({total})</span></span></div>", unsafe_allow_html=True)
                st.markdown(f"<style>.card-nexion {{ transition: all 0.3s ease !important; cursor: pointer; }} .card-nexion:hover {{ transform: translateX(10px); border-color: {azul_premium} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(0, 212, 255, 0.2); }}</style>", unsafe_allow_html=True)

                for _, d in resultados.iterrows():
                    status_text = d["COMENTARIOS"] if pd.notna(d.get("COMENTARIOS")) else "OK"
                    st.markdown(f"<div class='card-nexion' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {azul_premium};border-radius:12px;padding:18px 25px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>PEDIDO / FACTURA</span><br><b style='font-size:18px;color:{azul_premium};letter-spacing:0.5px;'># {d.get('NÚMERO DE PEDIDO','')}</b><br><span style='font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;'>Envío: {d.get('FECHA DE ENVÍO','')}</span></div><div style='flex:2.5;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CLIENTE / DESTINO</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('NOMBRE DEL CLIENTE','')}</b><br><i style='font-size:11px;color:rgba(255,255,255,0.5);font-style:normal;font-weight:600;'>{d.get('DESTINO','')}</i></div><div style='flex:1.8;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>TRANSPORTE Y GUÍA</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('FLETERA', d.get('TRANSPORTE', 'LOGÍSTICA'))}</b><br><span style='font-size:12px;color:{azul_premium};font-weight:700;font-family:monospace;'>{d.get('NÚMERO DE GUÍA','')}</span></div><div style='flex:1.2;text-align:right;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>ESTATUS ENTREGA</span><br><b style='font-size:14px;color:{azul_premium};'>{d.get('FECHA DE ENTREGA REAL','')}</b><br><span style='font-size:10px;color:white;font-weight:800;text-transform:uppercase;opacity:0.8;'>{status_text}</span></div></div>", unsafe_allow_html=True)

        st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)


# ==========================================
# 6. INTERFAZ PRINCIPAL (CENTRO DE CONTROL ULTRA COMPACTO + AUDITORÍA PRO)
# ==========================================
def main():
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    st.markdown("<p style='font-size: 15px; font-weight: 800; letter-spacing: 1.5px; color: white; margin-bottom: 2px;'>MATRIZ GLOBAL DE ACCESOS Y PERMISOS</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 11px; color: rgba(255,255,255,0.7); margin-bottom: 12px;'>Configura los permisos tanto de los módulos principales como de cada uno de sus submenús individuales por operador.</p>", unsafe_allow_html=True)

    # --- BLOQUE PARA AGREGAR NUEVO USUARIO ---
    st.markdown("---")
    with st.expander("➕ AGREGAR NUEVO OPERADOR AL SISTEMA"):
        col1, col2 = st.columns(2)
        nuevo_usuario = col1.text_input("NOMBRE DE USUARIO (ID)")
        if col2.button("REGISTRAR EN MATRIZ"):
            if nuevo_usuario and nuevo_usuario not in df_permisos["USUARIO"].values:
                # Creamos una fila nueva con todo en False
                nueva_fila = pd.DataFrame([{"USUARIO": nuevo_usuario}])
                for col in df_permisos.columns:
                    if col != "USUARIO":
                        nueva_fila[col] = False
                
                # Unimos y guardamos en sesión
                df_permisos = pd.concat([df_permisos, nueva_fila], ignore_index=True)
                st.session_state["df_permisos_local"] = df_permisos
                st.success(f"Operador {nuevo_usuario} agregado. ¡Recuerda dar click en GUARDAR Y SINCRONIZAR!")
            else:
                st.error("El usuario ya existe o el campo está vacío.")
    
    
    df_permisos = cargar_matriz_permisos()

    if not df_permisos.empty:
        for col in df_permisos.columns:
            if col != "USUARIO":
                df_permisos[col] = df_permisos[col].astype(bool)

        cols_dash = ["USUARIO", "DASHBOARD"]
        cols_seg = ["USUARIO", "SEGUIMIENTO", "ALERTAS", "GANTT", "QUEJAS"]
        cols_ent = ["USUARIO", "ENTREGAS", "AGC", "AMAZON", "BARCELO", "NACIONAL"]
        cols_rep = ["USUARIO", "REPORTES", "COSTOS CEDIS", "ANALISIS MENSUAL", "DETALLE COSTOS", "ENVIOS ESPECIALES", "ENVIO DE MUESTRAS", "PANEL MUESTRAS"]
        cols_for = ["USUARIO", "FORMATOS", "SALIDA DE PT", "CHECK LIST AGC", "QR AGC", "PREGUIA PAQMEX", "RECOLECCION 3G", "RECOLECCION ONE", "CARTA RECLAMO", "COTIZACIONES"]
        cols_dat = ["USUARIO", "CENTRO DE DATOS", "ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "ESCANEAR QR", "HERRAMIENTAS"]
        cols_fin = ["USUARIO", "FINANZAS", "WALLET", "CAJA CHICA", "GASTOS"]
        cols_enf = ["USUARIO", "ENFOQUE", "MORENO", "VAZQUEZ", "MIGUEL"]
        cols_acc = ["USUARIO", "ACCESS CONTROL"]

        tab_dash, tab_seg, tab_ent, tab_rep, tab_for, tab_dat, tab_fin, tab_enf, tab_acc, tab_aud = st.tabs([
            "DASHBOARD", "SEGUIMIENTO", "ENTREGAS", "REPORTES", 
            "FORMATOS", "DATOS", "FINANZAS", "ENFOQUE", "ACCESS CTRL", "AUDITORÍA"
        ])

        df_editado = df_permisos.copy()

        def renderizar_pestana_compacta(cols_tab, tab_key, df_fuente):
            c_m1, c_m2, c_esp = st.columns([1.5, 1.5, 4])
            with c_m1:
                if st.button("✅ Marcar Todo", key=f"btn_marcar_todo_{tab_key}", use_container_width=True):
                    for c in cols_tab:
                        if c != "USUARIO":
                            df_fuente[c] = True
                    st.session_state["df_permisos_local"] = df_fuente
                    st.rerun()

            with c_m2:
                if st.button("❌ Desmarcar Todo", key=f"btn_desmarcar_todo_{tab_key}", use_container_width=True):
                    for c in cols_tab:
                        if c != "USUARIO":
                            df_fuente[c] = False
                    st.session_state["df_permisos_local"] = df_fuente
                    st.rerun()

            st.markdown("<hr style='border-top:1px solid rgba(255,255,255,0.08); margin:8px 0;'>", unsafe_allow_html=True)

            with st.expander("⚡ Accesos rápidos por operador (Expandir/Contraer)", expanded=False):
                for idx, row in df_fuente.iterrows():
                    user_name = row["USUARIO"]
                    cols_u = st.columns([2, 1, 1, 4])
                    with cols_u[0]:
                        st.markdown(f"<span style='font-size:11px; font-weight:700; line-height:28px;'>👤 {user_name}</span>", unsafe_allow_html=True)
                    with cols_u[1]:
                        if st.button(f"Marcar", key=f"rc_m_{tab_key}_{user_name}", use_container_width=True):
                            for c in cols_tab:
                                if c != "USUARIO":
                                    df_fuente.loc[df_fuente["USUARIO"] == user_name, c] = True
                            st.session_state["df_permisos_local"] = df_fuente
                            st.rerun()
                    with cols_u[2]:
                        if st.button(f"Quitar", key=f"rc_d_{tab_key}_{user_name}", use_container_width=True):
                            for c in cols_tab:
                                if c != "USUARIO":
                                    df_fuente.loc[df_fuente["USUARIO"] == user_name, c] = False
                            st.session_state["df_permisos_local"] = df_fuente
                            st.rerun()
                st.markdown("<div style='margin: 4px 0;'></div>", unsafe_allow_html=True)

            df_t = df_fuente[[c for c in cols_tab if c in df_fuente.columns]].copy()
            sub_ed = st.data_editor(df_t, use_container_width=True, hide_index=True, key=f"ed_{tab_key}", height=360)
            
            for c in sub_ed.columns:
                if c != "USUARIO":
                    for idx, val in sub_ed[c].items():
                        user_val = sub_ed.loc[idx, "USUARIO"]
                        df_fuente.loc[df_fuente["USUARIO"] == user_val, c] = val
            return df_fuente

        with tab_dash:
            df_editado = renderizar_pestana_compacta(cols_dash, "dash", df_editado)

        with tab_seg:
            df_editado = renderizar_pestana_compacta(cols_seg, "seg", df_editado)

        with tab_ent:
            df_editado = renderizar_pestana_compacta(cols_ent, "ent", df_editado)

        with tab_rep:
            df_editado = renderizar_pestana_compacta(cols_rep, "rep", df_editado)

        with tab_for:
            df_editado = renderizar_pestana_compacta(cols_for, "for", df_editado)

        with tab_dat:
            df_editado = renderizar_pestana_compacta(cols_dat, "dat", df_editado)

        with tab_fin:
            df_editado = renderizar_pestana_compacta(cols_fin, "fin", df_editado)

        with tab_enf:
            df_editado = renderizar_pestana_compacta(cols_enf, "enf", df_editado)

        with tab_acc:
            df_editado = renderizar_pestana_compacta(cols_acc, "acc", df_editado)

        with tab_aud:
            st.markdown(f"""
                <div style='display:flex;align-items:center;gap:10px;margin:15px 0;'>
                    <div style='background:#FF4B4B;width:5px;height:25px;border-radius:2px;box-shadow:0 0 10px #FF4B4B;'></div>
                    <span style='color:white;font-size:16px;font-weight:800;letter-spacing:2px;text-transform:uppercase;'>MONITOR DE ACTIVIDAD // AUDITORÍA EN TIEMPO REAL</span>
                </div>
            """, unsafe_allow_html=True)
            
            try:
                df_logs = cargar_datos_auditoria()
                
                st.markdown(f"<style>.card-log {{ transition: all 0.3s ease; cursor: pointer; }} .card-log:hover {{ transform: translateX(5px); border-color: #FF4B4B !important; background: rgba(255, 75, 75, 0.05) !important; }}</style>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                if not df_logs.empty:
                    for index, row in df_logs.iloc[::-1].head(15).iterrows():
                        usr = str(row.get('USUARIO', 'GUEST'))
                        fch = str(row.get('FECHA_HORA', 'N/A'))
                        mod = str(row.get('MODULO', 'GENERAL'))
                        
                        st.markdown(f"""
                            <div class='card-log' style='background:rgba(30,39,46,0.5); border:1px solid rgba(255,255,255,0.05); border-left:4px solid #FF4B4B; border-radius:8px; padding:10px 20px; margin-bottom:8px; display:flex; align-items:center; justify-content:space-between;'>
                                <div style='flex:1;'>
                                    <span style='color:rgba(255,255,255,0.4); font-size:8px; font-weight:800; letter-spacing:1px; text-transform:uppercase;'>OPERADOR</span><br>
                                    <b style='font-size:14px; color:white; letter-spacing:0.5px;'>{usr.upper()}</b>
                                </div>
                                <div style='flex:2; padding-left:20px; border-left:1px solid rgba(255,255,255,0.08);'>
                                    <span style='color:rgba(255,255,255,0.4); font-size:8px; font-weight:800; letter-spacing:1px; text-transform:uppercase;'>MÓDULO ACCEDIDO</span><br>
                                    <b style='font-size:12px; color:#82D4E6;'>{mod.upper()}</b>
                                </div>
                                <div style='flex:2; padding-left:20px; border-left:1px solid rgba(255,255,255,0.08);'>
                                    <span style='color:rgba(255,255,255,0.4); font-size:8px; font-weight:800; letter-spacing:1px; text-transform:uppercase;'>FECHA Y HORA DE ACCESO</span><br>
                                    <span style='font-size:12px; color:#FF4B4B; font-family:monospace; font-weight:700;'>{fch}</span>
                                </div>
                                <div style='flex:0.5; text-align:right;'>
                                    <span style='background:rgba(0,255,170,0.1); color:#00FFAA; padding:3px 8px; border-radius:4px; font-size:8px; font-weight:800;'>ENTRY OK</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Esperando el primer registro de acceso para mostrar el historial...")
            except Exception as e:
                st.warning("No se pudo cargar el registro de auditoría en este momento.")

        st.markdown("<br>", unsafe_allow_html=True)
        col_b1, col_b2 = st.columns([1.5, 4])
        with col_b1:
            if st.button("GUARDAR Y SINCRONIZAR", use_container_width=True, type="primary"):
                with st.spinner("Actualizando permisos al instante..."):
                    exito = guardar_matriz_en_github(df_editado)
                    if exito:
                        st.success("¡Permisos actualizados al instante en la app y guardados en GitHub, mi amor! 🚀")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Error al sincronizar con GitHub. Revisa el token o los permisos.")
    else:
        st.warning("No se pudo cargar la matriz de permisos. Asegúrate de que el archivo exista en GitHub.")


if __name__ == "__main__":
    main()

# ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
st.markdown(
    f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
