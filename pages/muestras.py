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
vars_css = {
    "bg": "#1B1E23",      
    "card": "#282D34",    
    "text": "#FFFAFA",    
    "sub": "#FFFFFF",     
    "border": "#414852",  
    "table_header": "#2D3748", 
    "logo": "n1.png"
}

# ── TU BLOQUE DE CSS ORIGINAL (ÍNTEGRO) ──────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{
    visibility: hidden;
    height: 0px;
}}

html, body {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
}}

.stApp {{ 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['text']} !important; 
    font-family: 'Inter', sans-serif !important; 
}}

.block-container {{ 
    padding-top: 0.8rem !important; 
    padding-bottom: 5rem !important; 
    background-color: {vars_css['bg']} !important;
}}

@keyframes fadeInUp {{ 
    from {{ opacity: 0; transform: translateY(15px); }} 
    to {{ opacity: 1; transform: translateY(0); }} 
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

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

/* Estilos de Pestañas Superiores */
button[data-baseweb="tab"] {{
    font-size: 10px !important;
    letter-spacing: 2px !important;
    border: none !important;
    text-transform: uppercase !important;
    color: {vars_css['sub']} !important;
    opacity: 0.6;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    opacity: 1 !important;
    font-weight: 800 !important;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: #00FFAA !important; 
}}
</style>
""", unsafe_allow_html=True)

# ── FLUJO INICIAL ──────────────────────────
if not st.session_state.splash_completado:
    st.session_state.splash_completado = True
    st.rerun()

if not st.session_state.autenticado:
    # Login simplificado sin restricciones
    _, col, _ = st.columns([2, 2, 2])
    with col:
        st.markdown("<br><br><br><h3 style='text-align: center;'>SYSTEM ACCESS REQUIRED</h3>", unsafe_allow_html=True)
        st.text_input("OPERATOR ID", key="user_id")
        st.text_input("ACCESS KEY", type="password", key="access_key")
        if st.button("VERIFY IDENTITY"):
            st.session_state.autenticado = True
            st.rerun()
else:
    # ── HEADER Y MENÚ PRINCIPAL (NIVEL 1) ──────────────────────────
    c1, c2 = st.columns([1, 5], vertical_alignment="center")
    with c1:
        st.markdown(f"<h2 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:7px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-5px;'>SYSTEM SOLUTIONS</p>", unsafe_allow_html=True)
    
    with c2:
        tabs_n1 = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])

    st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:-15px 0 20px; opacity:0.2;'>", unsafe_allow_html=True)

    # ── RENDERIZADO DE CONTENIDO POR MÓDULO ──────────────────────────────

    # --- 1. DASHBOARD ---
    with tabs_n1[0]:
        st.markdown("<h3 class='op-query-text'>DASHBOARD</h3>", unsafe_allow_html=True)
        
        # Filtro de Período (Imagen)
        st.markdown("<p style='font-size:9px; letter-spacing:2px;'>PERÍODO</p>", unsafe_allow_html=True)
        st.selectbox("FEBRERO", ["ENERO", "FEBRERO", "MARZO", "ABRIL"], label_visibility="collapsed")
        
        # Submenú Nivel 2
        sub_d = st.columns([1, 1, 1, 1, 6])
        if sub_d[0].button("KPI'S"): st.session_state.d_sub = "KPI"
        if sub_d[1].button("RASTREO"): st.session_state.d_sub = "RASTREO"
        if sub_d[2].button("VOLUMEN"): st.session_state.d_sub = "VOLUMEN"
        if sub_d[3].button("RETRASOS"): st.session_state.d_sub = "RETRASOS"
        
        st.markdown("<hr style='border-top:1px solid #414852; opacity:0.1; margin-top:0;'>", unsafe_allow_html=True)
        
        # Lógica de renderizado Dashboard
        d_view = st.session_state.get("d_sub", "KPI")
        if d_view == "KPI":
            st.write("Cargando indicadores clave (Donut Charts)...")
        elif d_view == "RASTREO":
            st.write("Vista de Rastreo de Unidades")

    # --- 2. SEGUIMIENTO ---
    with tabs_n1[1]:
        st.markdown("<h3 class='op-query-text'>SEGUIMIENTO</h3>", unsafe_allow_html=True)
        
        sub_s = st.columns([1, 1, 1, 7])
        if sub_s[0].button("TRK"): st.session_state.s_sub = "TRK"
        if sub_s[1].button("GANTT"): st.session_state.s_sub = "GANTT"
        if sub_s[2].button("QUEJAS"): st.session_state.s_sub = "QUEJAS"
        
        st.markdown("<hr style='border-top:1px solid #414852; opacity:0.1; margin-top:0;'>", unsafe_allow_html=True)
        
        s_view = st.session_state.get("s_sub", "TRK")
        if s_view == "TRK":
            st.write("Módulo de Tracking en tiempo real")
        elif s_view == "GANTT":
            st.write("Diagrama de Gantt Logístico")
        elif s_view == "QUEJAS":
            st.write("Gestión de Incidencias y Quejas")

    # --- 3. REPORTES ---
    with tabs_n1[2]:
        st.markdown("<h3 class='op-query-text'>REPORTES</h3>", unsafe_allow_html=True)
        
        sub_r = st.columns([1, 1, 1, 7])
        if sub_r[0].button("APQ"): st.session_state.r_sub = "APQ"
        if sub_r[1].button("OPS"): st.session_state.r_sub = "OPS"
        if sub_r[2].button("OTD"): st.session_state.r_sub = "OTD"
        
        st.markdown("<hr style='border-top:1px solid #414852; opacity:0.1; margin-top:0;'>", unsafe_allow_html=True)
        
        r_view = st.session_state.get("r_sub", "APQ")
        if r_view == "APQ":
            st.subheader("Análisis de Producto y Quejas (APQ)")
        elif r_view == "OPS":
            st.subheader("Eficiencia Operativa (OPS)")
        elif r_view == "OTD":
            st.subheader("On-Time Delivery (OTD)")

    # --- 4. FORMATOS ---
    with tabs_n1[3]:
        st.markdown("<h3 class='op-query-text'>FORMATOS</h3>", unsafe_allow_html=True)
        
        sub_f = st.columns([1.5, 1.5, 1, 6])
        if sub_f[0].button("SALIDA PT"): st.session_state.f_sub = "SALIDA"
        if sub_f[1].button("CONTRARRECIBOS"): st.session_state.f_sub = "RECIBOS"
        if sub_f[2].button("MUESTRAS"): st.session_state.f_sub = "MUESTRAS"
        
        st.markdown("<hr style='border-top:1px solid #414852; opacity:0.1; margin-top:0;'>", unsafe_allow_html=True)
        
        f_view = st.session_state.get("f_sub", "SALIDA")
        if f_view == "SALIDA":
            st.write("Generador de Formatos: Salida de Producto Terminado")
        elif f_view == "RECIBOS":
            st.write("Generador de Contrarrecibos")
        elif f_view == "MUESTRAS":
            st.write("Módulo de Gestión y Formatos para Muestras")

    # --- 5. HUB LOG ---
    with tabs_n1[4]:
        st.markdown("<h3 class='op-query-text'>HUB LOG</h3>", unsafe_allow_html=True)
        
        sub_h = st.columns([1.5, 1.5, 1.5, 5.5])
        if sub_h[0].button("SMART ROUTING"): st.session_state.h_sub = "ROUTING"
        if sub_h[1].button("DATA MANAGEMENT"): st.session_state.h_sub = "DATA"
        if sub_h[2].button("ORDER STAGING"): st.session_state.h_sub = "STAGING"
        
        st.markdown("<hr style='border-top:1px solid #414852; opacity:0.1; margin-top:0;'>", unsafe_allow_html=True)
        
        h_view = st.session_state.get("h_sub", "ROUTING")
        if h_view == "ROUTING":
            st.write("Optimización de Rutas Inteligentes")
        elif h_view == "DATA":
            st.write("Administración de Base de Datos Logística")
        elif h_view == "STAGING":
            st.write("Preparación y Etiquetado de Órdenes")

    # ── FOOTER FIJO (BRANDING) ────────────────────────
    st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
        <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
    </div>
    """, unsafe_allow_html=True)

























