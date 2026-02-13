import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
import plotly.graph_objects as go
import plotly.express as px
import time
from github import Github
import json
import pytz
import zipfile
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re
import unicodedata
import io
import altair as alt
from datetime import date, datetime, timedelta
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# --- MOTOR DE INTELIGENCIA LOGÍSTICA (XENOCODE CORE) ---
def d_local(dir_val):
    """Detecta si una dirección pertenece a la ZMG basada en CPs."""
    rangos = [(44100, 44990), (45010, 45245), (45400, 45429), (45500, 45595)]
    cps = re.findall(r'\b\d{5}\b', str(dir_val))
    for cp in cps:
        try:
            if any(inicio <= int(cp) <= fin for inicio, fin in rangos): 
                return "LOCAL"
        except: 
            continue
    return "FORÁNEO"

@st.cache_data
def motor_logistico_central():
    """Carga la matriz historial para recomendaciones de fleteras."""
    try:
        if os.path.exists("matriz_historial.csv"):
            h = pd.read_csv("matriz_historial.csv", encoding='utf-8-sig')
            h.columns = [str(c).upper().strip() for c in h.columns]
            c_pre = [c for c in h.columns if 'PRECIO' in c][0]
            c_flet = [c for c in h.columns if 'FLETERA' in c or 'TRANSPORTE' in c][0]
            c_dir = [c for c in h.columns if 'DIRECCION' in c][0]
            h[c_pre] = pd.to_numeric(h[c_pre], errors='coerce').fillna(0)
            mejores = h.loc[h.groupby(c_dir)[c_pre].idxmin()]
            return mejores.set_index(c_dir)[c_flet].to_dict(), mejores.set_index(c_dir)[c_pre].to_dict()
    except: 
        pass
    return {}, {}

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ── LOGIN Y ESTADOS ──────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

# ── TEMA FIJO (TUS VARIABLES ORIGINALES) ──────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

vars_css = {
    "bg": "#1B1E23",      
    "card": "#282D34",    
    "text": "#FFFAFA",    
    "sub": "#FFFFFF",     
    "border": "#414852",  
    "table_header": "#2D3748", 
    "logo": "n1.png"
}

# ── TU BLOQUE DE CSS ORIGINAL (SIN CAMBIOS) ──────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* 1. Limpieza de Interfaz */
header, footer, [data-testid="stHeader"] {{
    visibility: hidden;
    height: 0px;
}}

/* APP BASE */
html, body {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
}}

.stApp {{ 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['text']} !important; 
    font-family: 'Inter', sans-serif !important; 
}}

/* CONTENEDOR PRINCIPAL */
.block-container {{ 
    padding-top: 0.8rem !important; 
    padding-bottom: 5rem !important; 
    background-color: {vars_css['bg']} !important;
}}

/* 2. ANIMACIÓN DE ENTRADA (BLINDADA) */
@keyframes fadeInUp {{ 
    from {{ opacity: 0; transform: translateY(15px); }} 
    to {{ opacity: 1; transform: translateY(0); }} 
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

/* 3. TÍTULOS Y OPERATIONAL QUERY */
h3, .op-query-text {{ 
    font-size: 11px !important; 
    letter-spacing: 8px !important; 
    text-align: center !important; 
    margin-top: 8px !important; 
    margin-bottom: 18px !important; 
    color: {vars_css['sub']} !important; 
    display: block !important; 
    width: 100% !important; 
}}

/* 4. BOTONES SLIM */
div.stButton > button {{ 
    background-color: {vars_css['card']} !important; 
    color: {vars_css['text']} !important; 
    border: 1px solid {vars_css['border']} !important; 
    border-radius: 2px !important; 
    font-weight: 700 !important; 
    text-transform: uppercase; 
    font-size: 10px !important; 
    height: 28px !important; 
    min-height: 28px !important; 
    line-height: 28px !important; 
    transition: all 0.2s ease !important; 
    width: 100% !important; 
}}

div.stButton > button:hover {{ 
    background-color: #ffffff !important; 
    color: #000000 !important; 
    border-color: #ffffff !important; 
}}

/* 5. INPUTS */
div[data-baseweb="input"] {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    transition: all 0.3s ease-in-out !important;
}}

div[data-baseweb="input"]:focus-within {{
    border: 1px solid #2563eb !important;
    box-shadow: 0 0 0 1px #2563eb !important;
}}

.stTextInput input {{ 
    background-color: transparent !important;
    color: {vars_css['text']} !important; 
    border: none !important; 
    box-shadow: none !important; 
    height: 45px !important; 
    text-align: center !important; 
    letter-spacing: 2px; 
    outline: none !important;
}}

/* 6. FOOTER FIJO */
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

/* TABS Y FILTROS */
div[data-baseweb="tag"] {{
    background-color: #2563eb !important;
    color: #ffffff !important;
}}

div[data-baseweb="tab-list"] button[aria-selected="true"] {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: #00FFAA !important; 
}}
</style>
""", unsafe_allow_html=True)

# ── LÓGICA DE NAVEGACIÓN ──────────────────────────
if not st.session_state.splash_completado:
    st.session_state.splash_completado = True
    st.rerun()

if not st.session_state.autenticado:
    # Pantalla de login simplificada para tu reparación
    _, col, _ = st.columns([2, 2, 2])
    with col:
        st.markdown("<br><br><h3 style='text-align: center;'>SYSTEM ACCESS</h3>", unsafe_allow_html=True)
        st.text_input("OPERATOR ID", key="user")
        st.text_input("ACCESS KEY", type="password", key="pass")
        if st.button("VERIFY IDENTITY"):
            st.session_state.autenticado = True
            st.rerun()
else:
    # --- HEADER CON TABS PRINCIPALES ---
    c1, c2 = st.columns([1, 4], vertical_alignment="center")
    with c1:
        st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0; text-align:left !important;'>NEXION</h3>", unsafe_allow_html=True)
    
    with c2:
        tab_principal = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])

    st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:0px 0 20px; opacity:0.2;'>", unsafe_allow_html=True)

    # --- CONTENEDOR DE CONTENIDO (CON SUBMENUS INTERNOS) ---
    
    # 1. DASHBOARD
    with tab_principal[0]:
        st.write("### DASHBOARD CENTRAL")

    # 2. SEGUIMIENTO
    with tab_principal[1]:
        # Submenú interno tipo botones (como tu imagen)
        sub_c = st.columns([1, 1, 1, 6])
        if sub_c[0].button("TRK"): st.session_state.sub_seg = "TRK"
        if sub_c[1].button("GANTT"): st.session_state.sub_seg = "GANTT"
        if sub_c[2].button("QUEJAS"): st.session_state.sub_seg = "QUEJAS"
        
        st.markdown("---")
        actual = st.session_state.get("sub_seg", "TRK")
        st.write(f"Modulo: {actual}")

    # 3. REPORTES
    with tab_principal[2]:
        sub_c = st.columns([1, 1, 1, 6])
        if sub_c[0].button("APQ"): st.session_state.sub_rep = "APQ"
        if sub_c[1].button("OPS"): st.session_state.sub_rep = "OPS"
        if sub_c[2].button("OTD"): st.session_state.sub_rep = "OTD"
        
        st.markdown("---")
        st.write(f"Reporte: {st.session_state.get('sub_rep', 'APQ')}")

    # 4. FORMATOS
    with tab_principal[3]:
        sub_c = st.columns([1.5, 1.5, 1, 5])
        if sub_c[0].button("SALIDA PT"): st.session_state.sub_for = "SALIDA PT"
        if sub_c[1].button("CONTRARRECIBOS"): st.session_state.sub_for = "CONTRARRECIBOS"
        if sub_c[2].button("MUESTRAS"): st.session_state.sub_for = "MUESTRAS"
        
        st.markdown("---")
        st.write(f"Formato: {st.session_state.get('sub_for', 'SALIDA PT')}")

    # 5. HUB LOG
    with tab_principal[4]:
        sub_c = st.columns([1.5, 1.5, 1.5, 4.5])
        if sub_c[0].button("SMART ROUTING"): st.session_state.sub_hub = "SMART ROUTING"
        if sub_c[1].button("DATA MGMT"): st.session_state.sub_hub = "DATA MGMT"
        if sub_c[2].button("ORDER STAGING"): st.session_state.sub_hub = "ORDER STAGING"
        
        st.markdown("---")
        st.write(f"Hub: {st.session_state.get('sub_hub', 'SMART ROUTING')}")

    # ── FOOTER ORIGINAL ────────────────────────
    st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
        <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
    </div>
    """, unsafe_allow_html=True)
























