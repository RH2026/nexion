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

@st.cache_data
def motor_logistico_central():
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
    except: pass
    return {}, {}

# ── ESTADOS DE SESIÓN ──
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

vars_css = {
    "bg": "#1B1E23", "card": "#282D34", "text": "#FFFAFA", 
    "sub": "#FFFFFF", "border": "#414852", "logo": "n1.png"
}

# ── ESTILOS CSS (MANTENIENDO TU DISEÑO) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
.stApp {{ background-color: {vars_css['bg']} !important; color: {vars_css['text']} !important; font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 1rem !important; padding-bottom: 5rem !important; }}

/* POSICIONAMIENTO DE LOGO */
.logo-box {{
    position: absolute;
    top: -10px;
    left: 0px;
    z-index: 1000;
}}
.logo-sub-text {{
    font-size: 8px; letter-spacing: 2px; color: {vars_css['sub']}; 
    opacity: 0.6; margin-top: -20px; display: block;
}}

/* MENU PRINCIPAL (TABS SUPERIORES A LA DERECHA) */
div[data-testid="stTabNav"] > div[role="tablist"] {{
    justify-content: flex-end !important;
    gap: 20px;
    border-bottom: 1px solid {vars_css['border']}22 !important;
    padding-right: 20px;
}}

/* SUBMENUS (TABS NIVEL 2 A LA IZQUIERDA) */
div[data-testid="stVerticalBlock"] div[data-testid="stTabNav"] > div[role="tablist"] {{
    justify-content: flex-start !important;
    margin-top: 15px !important;
    border-bottom: none !important;
    padding-left: 0px;
}}

/* ESTILO GENERAL DE PESTAÑAS */
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    border: none !important;
    color: {vars_css['sub']} !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    opacity: 0.5;
    transition: all 0.3s ease;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    opacity: 1 !important;
    color: {vars_css['text']} !important;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: #00FFAA !important; 
}}

/* FOOTER */
.footer {{ 
    position: fixed; bottom: 0; left: 0; width: 100%; 
    background-color: {vars_css['bg']}; color: {vars_css['sub']}; 
    text-align: center; padding: 12px 0; font-size: 9px; letter-spacing: 2px;
    border-top: 1px solid {vars_css['border']}; z-index: 999;
}}
</style>
""", unsafe_allow_html=True)

# ── LOGO E IDENTIDAD ──
st.markdown(f'<div class="logo-box">', unsafe_allow_html=True)
if os.path.exists(vars_css["logo"]):
    st.image(vars_css["logo"], width=110)
else:
    st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>", unsafe_allow_html=True)
st.markdown(f'<span class="logo-sub-text">SYSTEM SOLUTIONS</span></div>', unsafe_allow_html=True)

# ── SPLASH SCREEN ──
if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        st.markdown(f"""
        <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
            <div style="width:40px;height:40px;border:1px solid {vars_css['border']}; border-top:1px solid #00FFAA;border-radius:50%;animation:spin 1s linear infinite;"></div>
            <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">ESTABLISHING SECURE ACCESS</p>
        </div>
        <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
        """, unsafe_allow_html=True)
        time.sleep(1)
    st.session_state.splash_completado = True
    st.rerun()

# ── NAVEGACIÓN POR PESTAÑAS (SIN RESTRICCIONES) ──
m_tabs = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])

# --- 1. DASHBOARD ---
with m_tabs[0]:
    s_dash = st.tabs(["GENERAL", "KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"])
    with s_dash[0]: st.write("Contenido General Dashboard")

# --- 2. SEGUIMIENTO ---
with m_tabs[1]:
    s_seg = st.tabs(["TRK", "GANTT", "QUEJAS"])
    with s_seg[0]: st.write("Módulo de Tracking")

# --- 3. REPORTES ---
with m_tabs[2]:
    s_rep = st.tabs(["APQ", "OPS", "OTD"])
    with s_rep[0]: st.write("Reportes APQ")

# --- 4. FORMATOS ---
with m_tabs[3]:
    # Agregada la subsección MUESTRAS como pediste
    s_for = st.tabs(["SALIDA DE PT", "CONTRARRECIBOS", "MUESTRAS"])
    with s_for[0]: st.write("Gestión de Salida PT")
    with s_for[2]: st.write("Gestión de Muestras")

# --- 5. HUB LOG ---
with m_tabs[4]:
    s_hub = st.tabs(["SMART ROUTING", "DATA MANAGEMENT", "ORDER STAGING"])
    with s_hub[0]: st.write("Configuración Smart Routing")

# ── FOOTER ──
st.markdown(f"""
<div class="footer">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
    <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
    <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
</div>
""", unsafe_allow_html=True)






































