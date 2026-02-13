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
    rangos = [(44100, 44990), (45010, 45245), (45400, 45429), (45500, 45595)]
    cps = re.findall(r'\b\d{5}\b', str(dir_val))
    for cp in cps:
        try:
            if any(inicio <= int(cp) <= fin for inicio, fin in rangos): return "LOCAL"
        except: continue
    return "FORÁNEO"

# --- ESTILOS DE ARQUITECTURA (SHELl & CANVAS) ---
vars_css = {
    "shell_bg": "#0F1115",    # Fondo más oscuro exterior
    "canvas_bg": "#1B1E23",   # El bloque claro de tus fotos
    "accent": "#00FFAA",      # Neón Nexion
    "border": "#2D323A",
    "text": "#FFFAFA"
}

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .stApp {{ 
        background-color: {vars_css['shell_bg']} !important; 
        font-family: 'Inter', sans-serif !important; 
    }}

    /* CONTENEDOR PRINCIPAL (CANVAS) */
    .main-canvas {{
        background-color: {vars_css['canvas_bg']};
        border: 1px solid {vars_css['border']};
        border-radius: 4px;
        padding: 20px;
        min-height: 80vh;
        margin-top: 10px;
    }}

    /* BOTONES DEL MENÚ PRINCIPAL (DERECHA) */
    div.stButton > button {{
        background: transparent !important;
        border: 1px solid transparent !important;
        color: rgba(255,255,255,0.4) !important;
        font-size: 11px !important;
        letter-spacing: 2px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        color: {vars_css['accent']} !important;
        border-bottom: 1px solid {vars_css['accent']} !important;
    }}

    /* SUBMENU TABS (DENTRO DEL CANVAS) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        background-color: rgba(255,255,255,0.03) !important;
        border: 1px solid {vars_css['border']} !important;
        color: rgba(255,255,255,0.5) !important;
        font-size: 10px !important;
        letter-spacing: 1px !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {vars_css['accent']}11 !important;
        color: {vars_css['accent']} !important;
        border: 1px solid {vars_css['accent']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER (FUERA DEL CANVAS) ---
col_logo, col_empty, col_nav = st.columns([1.5, 2, 4])

with col_logo:
    st.markdown(f"<div style='margin-top:10px;'><span style='font-weight:900; letter-spacing:5px; color:white; font-size:20px;'>NEXION</span><br><span style='font-size:7px; letter-spacing:3px; color:{vars_css['accent']}; opacity:0.8;'>SYSTEM SOLUTIONS</span></div>", unsafe_allow_html=True)

with col_nav:
    # Menú Principal a la derecha como en tu imagen
    m_cols = st.columns(5)
    labels = ["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"]
    if "main_choice" not in st.session_state: st.session_state.main_choice = "DASHBOARD"
    
    for i, l in enumerate(labels):
        if m_cols[i].button(l, key=f"main_{l}"):
            st.session_state.main_choice = l
            st.rerun()

# --- RENDERIZADO DEL CANVAS (EL BLOQUE CLARO) ---
# Todo lo que ocurra aquí adentro estará contenido en el bloque visual
with st.container():
    st.markdown('<div class="main-canvas">', unsafe_allow_html=True)
    
    # Título de Sección (el que aparece en el centro en tu foto)
    st.markdown(f"<p style='text-align:center; font-size:10px; letter-spacing:10px; opacity:0.3; margin-bottom:30px;'>{st.session_state.main_choice}</p>", unsafe_allow_html=True)

    # Definición de Subbloques según la sección
    sub_map = {
        "DASHBOARD": ["KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"],
        "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
        "REPORTES": ["APQ", "OPS", "OTD"],
        "FORMATOS": ["SALIDA DE PT", "CONTRARRECIBOS", "MUESTRAS"],
        "HUB LOG": ["SMART ROUTING", "DATA MANAGEMENT", "ORDER STAGING"]
    }

    # Renderizamos los subbloques como pestañas integradas al canvas
    subs = st.tabs(sub_map[st.session_state.main_choice])
    
    # ── LOGICA DE CONTENIDO POR SECCIÓN ──
    current_main = st.session_state.main_choice
    
    # Ejemplo para FORMATOS -> MUESTRAS
    if current_main == "FORMATOS":
        with subs[0]: st.write("Contenido Salida PT")
        with subs[1]: st.write("Contenido Contrarrecibos")
        with subs[2]: 
            st.markdown("### GESTIÓN DE MUESTRAS")
            st.info("Renderizando subbloque de muestras...")

    # Ejemplo para DASHBOARD
    elif current_main == "DASHBOARD":
        with subs[0]: # KPI'S
            st.markdown("#### PERFORMANCE OPERATIVO")
            # Aquí pondrías tus gráficos circulares como los de la imagen
            c1, c2, c3, c4, c5 = st.columns(5)
            # Simulación de métricas
            c1.metric("PEDIDOS", "341", "100%")
            c2.metric("ENTREGADOS", "219", "64.2%")

    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ──
st.markdown(f"""
<div style="position: fixed; bottom: 0; width: 100%; text-align: center; padding: 10px; font-size: 8px; color: rgba(255,255,255,0.2); letter-spacing: 3px;">
    NEXION // LOGISTICS OS // © 2026 // ENGINEERED BY HERNANPHY
</div>
""", unsafe_allow_html=True)










































