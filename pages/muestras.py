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
            return mejores.set_index(c_dir)[c_flet].to_dict(), mejores.set_index(c_dir)[c_flet].to_dict()
    except: 
        pass
    return {}, {}

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ── ESTADO DE SESIÓN ──────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

# ── TEMA FIJO ──────────────────────────
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
}}

div.stButton > button:hover {{ 
    background-color: #ffffff !important; 
    color: #000000 !important; 
}}

div[data-baseweb="input"] {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
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

/* Estilo pestañas */
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    border: none !important;
    color: {vars_css['sub']} !important;
    font-size: 12px !important;
    letter-spacing: 2px !important;
}}

div[data-baseweb="tab-list"] button[aria-selected="true"] {{
    background-color: {vars_css['card']} !important;
    color: #00FFAA !important;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: #00FFAA !important; 
}}
</style>
""", unsafe_allow_html=True)

def login_screen():
    _, col, _ = st.columns([2, 2, 2]) 
    with col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>SYSTEM ACCESS REQUIRED</h3>", unsafe_allow_html=True)
        user_input = st.text_input("OPERATOR ID")
        pass_input = st.text_input("ACCESS KEY", type="password")
        if st.button("VERIFY IDENTITY"):
            # Sin restricciones: entra directo
            st.session_state.autenticado = True
            st.session_state.usuario_activo = user_input
            st.rerun()

# --- FLUJO DE CONTROL ---
if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:40px;height:40px;border:1px solid {vars_css['border']}; border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.10)
    st.session_state.splash_completado = True
    st.rerun()

elif not st.session_state.autenticado:
    login_screen()

else:
    # ── HEADER ──────────────────────────
    c1, c2, c3 = st.columns([1.5, 4, 1.5], vertical_alignment="center")
    with c1:
        try:
            st.image(vars_css["logo"], width=110)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>", unsafe_allow_html=True)
    
    with c2:
        # MENU DE PESTAÑAS (TABS) PRINCIPAL
        tabs_main = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])
    
    with c3:
        st.markdown(f"<p style='font-size:9px; text-align:right; color:#00FFAA;'>● ONLINE</p>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px; opacity:0.2;'>", unsafe_allow_html=True)

    # ── CONTENIDO POR TABS ──────────────────────────────────
    
    # --- TAB 1: DASHBOARD ---
    with tabs_main[0]:
        st.session_state.menu_main = "DASHBOARD"
        st.session_state.menu_sub = "GENERAL"
        # Contenido DASHBOARD
        st.markdown("### OPERATIONAL OVERVIEW")

    # --- TAB 2: SEGUIMIENTO ---
    with tabs_main[1]:
        st.session_state.menu_main = "SEGUIMIENTO"
        sub = st.selectbox("SUBSECCIÓN", ["TRK", "GANTT", "QUEJAS"], label_visibility="collapsed")
        st.session_state.menu_sub = sub
        
        if sub == "TRK":
            st.write("Módulo TRK")
        elif sub == "GANTT":
            st.write("Módulo GANTT")
        elif sub == "QUEJAS":
            st.write("Módulo QUEJAS")

    # --- TAB 3: REPORTES ---
    with tabs_main[2]:
        st.session_state.menu_main = "REPORTES"
        sub = st.selectbox("SUBSECCIÓN", ["APQ", "OPS", "OTD"], label_visibility="collapsed")
        st.session_state.menu_sub = sub
        
        if sub == "APQ":
            st.subheader("Análisis de Producto y Quejas (APQ)")
        elif sub == "OPS":
            st.subheader("Eficiencia Operativa (OPS)")
        elif sub == "OTD":
            st.subheader("On-Time Delivery (OTD)")

    # --- TAB 4: FORMATOS ---
    with tabs_main[3]:
        st.session_state.menu_main = "FORMATOS"
        # Agregada la subsección MUESTRAS
        sub = st.selectbox("SUBSECCIÓN", ["SALIDA DE PT", "CONTRARRECIBOS", "MUESTRAS"], label_visibility="collapsed")
        st.session_state.menu_sub = sub
        
        if sub == "SALIDA DE PT":
            st.write("Módulo SALIDA DE PT")
        elif sub == "CONTRARRECIBOS":
            st.write("Módulo CONTRARRECIBOS")
        elif sub == "MUESTRAS":
            st.write("Módulo MUESTRAS / SAMPLES")

    # --- TAB 5: HUB LOG ---
    with tabs_main[4]:
        st.session_state.menu_main = "HUB LOG"
        sub = st.selectbox("SUBSECCIÓN", ["SMART ROUTING", "DATA MANAGEMENT", "ORDER STAGING"], label_visibility="collapsed")
        st.session_state.menu_sub = sub
        
        if sub == "SMART ROUTING":
            st.write("Módulo SMART ROUTING")
        elif sub == "DATA MANAGEMENT":
            st.write("Módulo DATA MANAGEMENT")
        elif sub == "ORDER STAGING":
            st.write("Módulo ORDER STAGING")

    # ── FOOTER FIJO ────────────────────────
    st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
        <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
    </div>
    """, unsafe_allow_html=True)























