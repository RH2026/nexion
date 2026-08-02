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
    page_title="JYPESA | Logistics",
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

# --- MODIFICACIÓN FEDEX: Añadimos estilos para los menús desplegables ---
css_fedex = """
/* --- ESTILOS DE MENÚS TIPO FEDEX --- */
.fedex-menu {
    width: 100%;
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.fedex-menu ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
}

.fedex-menu li {
    position: relative;
}

.fedex-menu li a {
    display: block;
    color: #000000 !important;
    padding: 15px 20px;
    text-decoration: none;
    font-size: 14px;
    font-family: 'Inter', sans-serif !important;
    border-bottom: 1px solid #E0E0E0;
    font-weight: 500;
}

.fedex-menu li:last-child a {
    border-bottom: none;
}

/* Estilo del primer nivel de menú (el que se despliega) */
.fedex-menu > ul > li > a {
    background-color: #7D007D !important; /* Color púrpura como base del menú FedEx */
    color: #FFFFFF !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-left: 25px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-bottom: 0;
}

.fedex-menu > ul > li > a:after {
    content: '▼';
    font-size: 10px;
    color: #FFFFFF;
    margin-left: 10px;
}

.fedex-menu > ul > li:hover > a {
    background-color: #660066 !important; /* Color púrpura más oscuro al pasar el ratón */
}

/* Submenús (los elementos internos) */
.fedex-menu ul ul {
    display: none; /* Por defecto ocultos */
    position: static; /* Cambiado a static para que se expandan hacia abajo */
    background-color: #FFFFFF !important;
    box-shadow: none;
    padding-left: 0;
}

.fedex-menu li:hover > ul {
    display: block; /* Mostrar al pasar el ratón */
}

.fedex-menu ul ul li a {
    padding: 12px 25px 12px 35px;
    font-weight: 500;
    color: #424242 !important;
}

.fedex-menu ul ul li a:hover {
    background-color: #F5F5F5 !important;
}

/* Estilo para los enlaces destacados (ej. "TODOS LOS SERVICIOS") */
.fedex-menu .destacado a {
    color: #0072C6 !important; /* Azul FedEx para enlaces destacados */
    font-weight: 700;
    border-top: 1px solid #E0E0E0;
}
"""

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* --- ANIMACIONES DE ENTRADA --- */
@keyframes fadeInSlideDown {{
    0% {{
        opacity: 0;
        transform: translateY(-20px);
    }}
    100% {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.animate-fade-in {{
    animation: fadeInSlideDown 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
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

/* BOTONES DE LA BARRA DE MENÚ HORIZONTAL PRO */
.stHorizontalBlock div.stButton > button {{
    background: rgba(43, 52, 59, 0.75) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-top: 2px solid #00D4FF !important; /* Usamos tu azul cian */
    border-radius: 6px !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    height: 42px !important;
    width: 100% !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}}

.stHorizontalBlock div.stButton > button:hover {{
    background: rgba(0, 212, 255, 0.15) !important;
    color: #00D4FF !important;
    border-color: #00D4FF !important;
    transform: translateY(-200px) !important;
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
}}

/* BOTONES GENERALES RESTANTES */
div.stButton > button, div.stDownloadButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 34px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

/*FOOTER FIJO */
.footer {{ 
    position: fixed; 
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
}}

{css_fedex} /* --- AÑADIMOS EL CSS DE FEDEX AQUÍ --- */
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. SISTEMA DE SEGURIDAD PRO (VALIDACIÓN DE SESIÓN)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/entregas_agc.py"
    st.switch_page("pages/log.py")


# ==========================================
# 3. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================
@st.cache_data(ttl=60)
def obtener_matriz_github():
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv?nocache={int(time.time())}"
    try:
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except Exception as e:
        st.error(f"Error fatal al conectar con GitHub: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def cargar_datos_dashboard():
    t = int(time.time())
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
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
    st.session_state.menu_main = "ENTREGAS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "AGC"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1
if "tipo_resultado" not in st.session_state:
    st.session_state.tipo_resultado = "OPERACION"


# ==========================================
# 4. HEADER EXACTAMENTE DE 3 COLUMNAS + BARRA DE MENÚ INFERIOR
# ==========================================
header_zone = st.container()
with header_zone:
    # ── COLUMNA 1: LOGO | COLUMNA 2: TÍTULO DINÁMICO | COLUMNA 3: BUSCADOR ──
    c1, c2, c3 = st.columns([1.8, 5.2, 3.0], vertical_alignment="center")

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
                <p style='font-size: 13px; letter-spacing: 4px; color: {vars_css['sub']}; margin: 0; font-weight: 600; text-transform: uppercase; text-align: center;'>
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
