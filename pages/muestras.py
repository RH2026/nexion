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
import alt as alt
from datetime import date, datetime, timedelta
from io import BytesIO

# 1. CONFIGURACIÓN
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# --- MOTOR LOGÍSTICO (SIN CAMBIOS) ---
def d_local(dir_val):
    rangos = [(44100, 44990), (45010, 45245), (45400, 45429), (45500, 45595)]
    cps = re.findall(r'\b\d{5}\b', str(dir_val))
    for cp in cps:
        try:
            if any(inicio <= int(cp) <= fin for inicio, fin in rangos): return "LOCAL"
        except: continue
    return "FORÁNEO"

# --- CSS: EL BLOQUE CLARO Y LOS SUBBLOQUES DE TUS FOTOS ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .stApp {{ background-color: #0F1115 !important; font-family: 'Inter', sans-serif !important; }}
    .block-container {{ padding: 1.5rem 4rem !important; }}

    /* EL CONTENEDOR MÁS CLARO DE TU IMAGEN */
    .main-render-zone {{
        background-color: #1B1E23;
        border: 1px solid #2D323A;
        border-radius: 2px;
        padding: 25px;
        min-height: 75vh;
        margin-top: 15px;
    }}

    /* ESTILO DE BOTONES DE MENÚ (DERECHA Y SUBBLOQUES) */
    div.stButton > button {{
        background-color: transparent !important;
        color: #FFFFFF !important;
        border: 1px solid #414852 !important;
        border-radius: 0px !important;
        font-size: 10px !important;
        letter-spacing: 2px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        height: 35px !important;
        transition: 0.2s;
    }}
    
    div.stButton > button:hover {{
        background-color: #00FFAA !important;
        color: #000000 !important;
        border-color: #00FFAA !important;
    }}

    /* TITULOS DE SECCIÓN */
    .section-title {{
        text-align: center; font-size: 10px; letter-spacing: 12px; 
        color: white; opacity: 0.4; margin-bottom: 25px; font-weight: 800;
    }}
</style>
""", unsafe_allow_html=True)

# --- NAVEGACIÓN ---
if "main" not in st.session_state: st.session_state.main = "DASHBOARD"
if "sub" not in st.session_state: st.session_state.sub = "GENERAL"

# ── HEADER SUPERIOR ──
c_log, c_mid, c_nav = st.columns([1.5, 2, 4])
with c_log:
    st.markdown("NEXION <br> <span style='font-size:7px; letter-spacing:3px; color:#00FFAA;'>SYSTEM SOLUTIONS</span>", unsafe_allow_html=True)

with c_nav:
    m_btns = st.columns(5)
    labels = ["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"]
    for i, l in enumerate(labels):
        if m_btns[i].button(l, key=f"m_{l}", use_container_width=True):
            st.session_state.main = l
            st.rerun()

# ── RENDER PRINCIPAL (CANVAS) ──
st.markdown('<div class="main-render-zone">', unsafe_allow_html=True)
st.markdown(f'<div class="section-title">{st.session_state.main}</div>', unsafe_allow_html=True)

# Definición de Subsecciones
subs = {
    "DASHBOARD": ["GENERAL", "KPI'S", "RASTREO"],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "CONTRARRECIBOS", "MUESTRAS"],
    "HUB LOG": ["SMART ROUTING", "DATA MANAGEMENT"]
}

# Fila de Subbloques (Tal cual tus fotos: alineados a la izquierda dentro del bloque)
current_subs = subs[st.session_state.main]
s_cols = st.columns(len(current_subs) + 1)
for i, s_label in enumerate(current_subs):
    if s_cols[i].button(s_label, key=f"s_{s_label}", use_container_width=True):
        st.session_state.sub = s_label

st.markdown("<hr style='border: 0.1px solid #2D323A; margin: 20px 0;'>", unsafe_allow_html=True)

# ── CONTENIDO ESPECÍFICO ──
st.write(f"EJECUTANDO: {st.session_state.main} > {st.session_state.sub}")

if st.session_state.main == "FORMATOS" and st.session_state.sub == "MUESTRAS":
    st.markdown("### PANEL DE CONTROL DE MUESTRAS")
    # Tu código para muestras aquí

st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ──
st.markdown("<div style='text-align:center; margin-top:30px; font-size:8px; opacity:0.3; letter-spacing:4px;'>NEXION LOGISTICS // © 2026</div>", unsafe_allow_html=True)











































