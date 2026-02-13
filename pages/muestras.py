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
import altair as alt  # <--- CORREGIDO: ERA ALTAIR, NO ALT
from datetime import date, datetime, timedelta
from io import BytesIO

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# --- MOTOR LOGÍSTICO ---
def d_local(dir_val):
    rangos = [(44100, 44990), (45010, 45245), (45400, 45429), (45500, 45595)]
    cps = re.findall(r'\b\d{5}\b', str(dir_val))
    for cp in cps:
        try:
            if any(inicio <= int(cp) <= fin for inicio, fin in rangos): return "LOCAL"
        except: continue
    return "FORÁNEO"

# --- CSS: ARQUITECTURA DE BLOQUES FIEL A TUS FOTOS ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    /* ELIMINAR BASURA DE STREAMLIT */
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    .stApp {{ background-color: #0F1115 !important; font-family: 'Inter', sans-serif !important; }}
    .block-container {{ padding: 1.5rem 4rem !important; }}

    /* EL CANVAS (BLOQUE CLARO) DONDE SE RENDERIZA TODO */
    .main-render-zone {{
        background-color: #1B1E23;
        border: 1px solid #2D323A;
        border-radius: 2px;
        padding: 30px;
        min-height: 75vh;
        margin-top: 15px;
    }}

    /* BOTONES ESTILO BLOQUE (DERECHA Y SUBMENÚ) */
    div.stButton > button {{
        background-color: transparent !important;
        color: #FFFFFF !important;
        border: 1px solid #414852 !important;
        border-radius: 0px !important;
        font-size: 10px !important;
        letter-spacing: 2px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        height: 38px !important;
        width: 100% !important;
        transition: 0.2s ease-in-out;
    }}
    
    div.stButton > button:hover {{
        background-color: #00FFAA !important;
        color: #000000 !important;
        border-color: #00FFAA !important;
    }}

    .section-label {{
        text-align: center; font-size: 10px; letter-spacing: 12px; 
        color: white; opacity: 0.2; margin-bottom: 30px; font-weight: 800;
    }}
</style>
""", unsafe_allow_html=True)

# --- NAVEGACIÓN (SESSION STATE) ---
if "main_nav" not in st.session_state: st.session_state.main_nav = "DASHBOARD"
if "sub_nav" not in st.session_state: st.session_state.sub_nav = "GENERAL"

# ── HEADER (LOGO IZQUIERDA | NAVEGACIÓN DERECHA) ──
h_col1, h_col2, h_col3 = st.columns([2, 1, 4])

with h_col1:
    st.markdown("<div style='line-height:1;'><span style='font-weight:900; letter-spacing:5px; color:white; font-size:22px;'>NEXION</span><br><span style='font-size:7px; letter-spacing:3px; color:#00FFAA; opacity:0.8;'>SYSTEM SOLUTIONS</span></div>", unsafe_allow_html=True)

with h_col3:
    m_tabs = st.columns(5)
    labels = ["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"]
    for i, label in enumerate(labels):
        if m_tabs[i].button(label, key=f"btn_{label}"):
            st.session_state.main_nav = label
            # Reset sub-navegación al cambiar principal
            defaults = {"DASHBOARD":"GENERAL", "SEGUIMIENTO":"TRK", "REPORTES":"APQ", "FORMATOS":"SALIDA DE PT", "HUB LOG":"SMART ROUTING"}
            st.session_state.sub_nav = defaults[label]
            st.rerun()

# ── CANVAS DE RENDERIZADO (EL BLOQUE CLARO DE TUS FOTOS) ──
st.markdown('<div class="main-render-zone">', unsafe_allow_html=True)
st.markdown(f'<div class="section-label">{st.session_state.main_nav}</div>', unsafe_allow_html=True)

# Configuración de Sub-bloques
sub_options = {
    "DASHBOARD": ["GENERAL", "KPI'S", "RASTREO"],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "CONTRARRECIBOS", "MUESTRAS"],
    "HUB LOG": ["SMART ROUTING", "DATA MANAGEMENT"]
}

# Fila de Sub-bloques (Botones rectangulares alineados a la izquierda)
current_subs = sub_options[st.session_state.main_nav]
s_cols = st.columns([1, 1, 1, 1, 3]) # El último espacio es para empujar todo a la izquierda

for i, sub_label in enumerate(current_subs):
    # Resaltar botón activo
    if s_cols[i].button(sub_label, key=f"sub_{sub_label}"):
        st.session_state.sub_nav = sub_label
        st.rerun()

st.markdown("<hr style='border: 0.1px solid rgba(255,255,255,0.05); margin: 25px 0;'>", unsafe_allow_html=True)

# ── LÓGICA DE CONTENIDO ──
if st.session_state.main_nav == "FORMATOS":
    if st.session_state.sub_nav == "MUESTRAS":
        st.markdown("### 🧪 CONTROL DE MUESTRAS")
        st.write("Módulo listo para recibir los campos de entrada.")
    elif st.session_state.sub_nav == "SALIDA DE PT":
        st.write("Módulo Salida Producto Terminado")

elif st.session_state.main_nav == "DASHBOARD":
    st.write(f"Viendo métricas de: {st.session_state.sub_nav}")

st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER DISCRETO ──
st.markdown("<div style='text-align:center; margin-top:30px; font-size:8px; opacity:0.2; letter-spacing:4px;'>NEXION LOGISTICS CORE // 2026</div>", unsafe_allow_html=True)












































