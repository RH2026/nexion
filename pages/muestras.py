import streamlit as st
import pandas as pd
from datetime import datetime
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

# --- MOTOR DE INTELIGENCIA LOGÍSTICA ---
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

# ── ESTADOS DE SESIÓN ──────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

vars_css = {
    "bg": "#1B1E23", "card": "#282D34", "text": "#FFFAFA", 
    "sub": "#FFFFFF", "border": "#414852", "accent": "#00FFAA"
}

# ── CSS RECONSTRUIDO AL 100% PARA ALINEACIÓN DUAL ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
.stApp {{ background-color: {vars_css['bg']} !important; color: {vars_css['text']} !important; font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 1rem !important; padding-bottom: 5rem !important; }}

/* 1. LOGO IZQUIERDA */
.logo-container {{
    position: absolute;
    top: 0px;
    left: 0px;
    z-index: 1000;
}}
.logo-main {{ font-weight: 800; letter-spacing: 3px; font-size: 20px; color: {vars_css['text']}; }}
.logo-sub {{ font-size: 7px; letter-spacing: 2px; opacity: 0.6; display: block; margin-top: -5px; }}

/* 2. TÍTULO CENTRAL IZQUIERDA (D A S H B O A R D) */
.center-title {{
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: 20px;
    font-size: 10px;
    letter-spacing: 8px;
    font-weight: 600;
    text-transform: uppercase;
    color: {vars_css['text']};
    opacity: 0.8;
}}

/* 3. MENU PRINCIPAL (DERECHA) */
div[data-testid="stTabNav"] > div[role="tablist"] {{
    justify-content: flex-end !important;
    gap: 15px;
    border-bottom: 1px solid {vars_css['border']}33 !important;
}}

/* 4. SUBMENUS (IZQUIERDA) - Forzamos el bloque vertical */
div[data-testid="stVerticalBlock"] div[data-testid="stTabNav"] > div[role="tablist"] {{
    justify-content: flex-start !important;
    margin-top: 25px !important;
    border-bottom: none !important;
}}

/* ESTILOS DE TABS COMUNES */
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    border: none !important;
    color: {vars_css['sub']} !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    opacity: 0.5;
    padding: 10px 15px !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    opacity: 1 !important;
    border-bottom: 2px solid {vars_css['accent']} !important;
}}
div[data-baseweb="tab-highlight"] {{ background-color: {vars_css['accent']} !important; }}

/* FOOTER */
.footer {{ 
    position: fixed; bottom: 0; left: 0; width: 100%; 
    background-color: {vars_css['bg']}; color: {vars_css['sub']}; 
    text-align: center; padding: 12px 0; font-size: 8px; letter-spacing: 2px;
    border-top: 1px solid {vars_css['border']}; z-index: 999;
}}
</style>
""", unsafe_allow_html=True)

# ── LOGO Y IDENTIDAD ──
st.markdown(f'''
<div class="logo-container">
    <div class="logo-main">NEXION</div>
    <div class="logo-sub">SYSTEM SOLUTIONS</div>
</div>
<div class="center-title">D A S H B O A R D</div>
''', unsafe_allow_html=True)

# ── LÓGICA DE FLUJO ORIGINAL ──
if not st.session_state.splash_completado:
    st.session_state.splash_completado = True
    st.rerun()

if not st.session_state.autenticado:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<br><br><h3 style='text-align:center;'>ACCESS REQUIRED</h3>", unsafe_allow_html=True)
        user = st.text_input("OPERATOR_ID")
        key = st.text_input("ACCESS_KEY", type="password")
        if st.button("VERIFY IDENTITY", use_container_width=True):
            st.session_state.autenticado = True
            st.rerun()
else:
    # ── MENU PRINCIPAL (DERECHA) ──
    tabs_n1 = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])

    with tabs_n1[0]: # DASHBOARD
        # SUBSECCIONES (IZQUIERDA)
        sub_dashboard = st.tabs(["KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"])
        
        with sub_dashboard[0]: # KPI'S
            st.markdown("<br><br>", unsafe_allow_html=True)
            # Aquí van tus Donuts (Pedidos, Entregados, etc.)
            st.write("Visualización de Indicadores Activa")

    with tabs_n1[1]: # SEGUIMIENTO
        sub_seguimiento = st.tabs(["TRK", "GANTT", "QUEJAS"])
        with sub_seguimiento[0]: st.write("Contenido de Tracking")

    # ── FOOTER ──
    st.markdown(f"""<div class="footer">NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 // ENGINEERED BY <b>HERNANPHY</b></div>""", unsafe_allow_html=True)

































