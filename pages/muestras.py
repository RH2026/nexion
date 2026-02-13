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

vars_css = {
    "bg": "#1B1E23", "card": "#282D34", "text": "#FFFAFA", 
    "sub": "#FFFFFF", "border": "#414852", "accent": "#00FFAA"
}

# ── TU BLOQUE DE CSS CON AJUSTES DE POSICIONAMIENTO ──────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
.stApp {{ background-color: {vars_css['bg']} !important; color: {vars_css['text']} !important; font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 1rem !important; padding-bottom: 5rem !important; }}

/* 1. NAVEGACIÓN PRINCIPAL (DERECHA) */
div[data-baseweb="tab-list"] {{
    display: flex;
    justify-content: flex-end !important;
    gap: 20px;
    border-bottom: 1px solid {vars_css['border']}33;
}}
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    border: none !important;
    color: {vars_css['sub']} !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
    padding: 10px 15px !important;
    opacity: 0.5;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    opacity: 1 !important;
    border-bottom: 2px solid {vars_css['accent']} !important;
}}
div[data-baseweb="tab-highlight"] {{ background-color: {vars_css['accent']} !important; }}

/* 2. LOGO IZQUIERDA (ABSOLUTO PARA ALINEAR CON TABS) */
.logo-container {{
    position: absolute;
    top: 0px;
    left: 0px;
    z-index: 1000;
}}

/* 3. TÍTULO SECCIÓN CENTRAL */
.section-title {{
    text-align: center;
    font-size: 10px;
    letter-spacing: 6px;
    color: {vars_css['text']};
    margin: -35px 0 25px 0;
    text-transform: uppercase;
    font-weight: 600;
}}

/* 4. SUBMENUS (TUS BOTONES) */
div.stButton > button {{
    background-color: transparent !important;
    color: {vars_css['sub']} !important;
    border: none !important;
    font-size: 9px !important;
    letter-spacing: 2px !important;
    padding: 5px 10px !important;
    opacity: 0.6;
    width: auto !important;
}}
div.stButton > button:hover {{ opacity: 1; color: {vars_css['accent']} !important; }}

/* FOOTER */
.footer {{ 
    position: fixed; bottom: 0; left: 0; width: 100%; 
    background-color: {vars_css['bg']}; color: {vars_css['sub']}; 
    text-align: center; padding: 12px 0; font-size: 8px; letter-spacing: 2px;
    border-top: 1px solid {vars_css['border']}; z-index: 999;
}}
</style>
""", unsafe_allow_html=True)

# ── LOGO (IZQUIERDA) ──────────────────────────
st.markdown('''
<div class="logo-container">
    <span style="font-weight:800; letter-spacing:3px; font-size:18px;">NEXION</span><br>
    <span style="font-size:7px; letter-spacing:2px; opacity:0.6;">SYSTEM SOLUTIONS</span>
</div>
''', unsafe_allow_html=True)

# ── MENÚ PRINCIPAL (A LA DERECHA) ──────────────────────────
tabs_n1 = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])

# ── CONTENIDO POR MÓDULO ──────────────────────────────

# --- 1. DASHBOARD ---
with tabs_n1[0]:
    st.markdown("<div class='section-title'>DASHBOARD</div>", unsafe_allow_html=True)
    
    # Filtro Período
    st.markdown("<p style='font-size:9px; letter-spacing:2px; margin-bottom:0;'>PERÍODO</p>", unsafe_allow_html=True)
    st.selectbox("FEBRERO", ["ENERO", "FEBRERO", "MARZO"], label_visibility="collapsed")
    
    # Submenú (Igual a la imagen)
    c_sub = st.columns([0.8, 0.8, 0.8, 0.8, 6])
    with c_sub[0]: 
        if st.button("KPI'S"): st.session_state.d_sub = "KPI"
    with c_sub[1]: 
        if st.button("RASTREO"): st.session_state.d_sub = "RASTREO"
    with c_sub[2]: 
        if st.button("VOLUMEN"): st.session_state.d_sub = "VOLUMEN"
    with c_sub[3]: 
        if st.button("RETRASOS"): st.session_state.d_sub = "RETRASOS"
    
    st.markdown("<hr style='border-top:1px solid #414852; opacity:0.2; margin-top:-10px;'>", unsafe_allow_html=True)
    
    # Aquí irían tus donuts de la imagen
    st.write(f"Renderizando: {st.session_state.get('d_sub', 'KPI')}")

# --- 2. SEGUIMIENTO ---
with tabs_n1[1]:
    st.markdown("<div class='section-title'>SEGUIMIENTO</div>", unsafe_allow_html=True)
    sub_s = st.columns([0.8, 0.8, 0.8, 7])
    if sub_s[0].button("TRK"): st.session_state.s_sub = "TRK"
    if sub_s[1].button("GANTT"): st.session_state.s_sub = "GANTT"
    if sub_s[2].button("QUEJAS"): st.session_state.s_sub = "QUEJAS"
    st.markdown("<hr style='border-top:1px solid #414852; opacity:0.2; margin-top:-10px;'>", unsafe_allow_html=True)

# --- 3. REPORTES ---
with tabs_n1[2]:
    st.markdown("<div class='section-title'>REPORTES</div>", unsafe_allow_html=True)
    sub_r = st.columns([0.8, 0.8, 0.8, 7])
    if sub_r[0].button("APQ"): st.session_state.r_sub = "APQ"
    if sub_r[1].button("OPS"): st.session_state.r_sub = "OPS"
    if sub_r[2].button("OTD"): st.session_state.r_sub = "OTD"
    st.markdown("<hr style='border-top:1px solid #414852; opacity:0.2; margin-top:-10px;'>", unsafe_allow_html=True)

# --- 4. FORMATOS ---
with tabs_n1[3]:
    st.markdown("<div class='section-title'>FORMATOS</div>", unsafe_allow_html=True)
    sub_f = st.columns([1.2, 1.2, 0.8, 6])
    if sub_f[0].button("SALIDA PT"): st.session_state.f_sub = "SALIDA"
    if sub_f[1].button("CONTRARRECIBOS"): st.session_state.f_sub = "RECIBOS"
    if sub_f[2].button("MUESTRAS"): st.session_state.f_sub = "MUESTRAS"
    st.markdown("<hr style='border-top:1px solid #414852; opacity:0.2; margin-top:-10px;'>", unsafe_allow_html=True)

# --- 5. HUB LOG ---
with tabs_n1[4]:
    st.markdown("<div class='section-title'>HUB LOG</div>", unsafe_allow_html=True)
    sub_h = st.columns([1.2, 1.2, 1.2, 5.5])
    if sub_h[0].button("SMART ROUTING"): st.session_state.h_sub = "ROUTING"
    if sub_h[1].button("DATA MGMT"): st.session_state.h_sub = "DATA"
    if sub_h[2].button("ORDER STAGING"): st.session_state.h_sub = "STAGING"
    st.markdown("<hr style='border-top:1px solid #414852; opacity:0.2; margin-top:-10px;'>", unsafe_allow_html=True)

# ── FOOTER ────────────────────────
st.markdown(f"""<div class="footer">NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 // ENGINEERED BY <b>HERNANPHY</b></div>""", unsafe_allow_html=True)

























