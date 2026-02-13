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

# ── ESTADOS DE SESIÓN ──────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

vars_css = {
    "bg": "#1B1E23", "card": "#282D34", "text": "#FFFAFA", 
    "sub": "#FFFFFF", "border": "#414852", "accent": "#00FFAA"
}

# ── CSS DEFINITIVO: SEPARACIÓN DE NIVELES ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
.stApp {{ background-color: {vars_css['bg']} !important; color: {vars_css['text']} !important; font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 1rem !important; padding-bottom: 5rem !important; }}

/* LOGO POSICIÓN */
.logo-container {{
    position: absolute;
    top: -15px;
    left: 0px;
    z-index: 1000;
}}

/* NIVEL 1: PESTAÑAS PRINCIPALES A LA DERECHA */
/* Seleccionamos el primer bloque de tabs que aparece en el body */
.stApp > div:nth-child(1) div[data-baseweb="tab-list"] {{
    justify-content: flex-end !important;
    gap: 20px;
    border-bottom: 1px solid {vars_css['border']}33;
}}

/* NIVEL 2: PESTAÑAS DENTRO DE CONTENIDO A LA IZQUIERDA */
/* Usamos descendencia para forzar que los tabs anidados se alineen a la izquierda */
div[data-testid="stVerticalBlock"] div[data-baseweb="tab-list"] {{
    justify-content: flex-start !important;
    margin-top: 20px !important;
    border-bottom: none !important;
}}

/* ESTILO COMÚN DE TABS */
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    border: none !important;
    color: {vars_css['sub']} !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    opacity: 0.5;
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

# ── LOGO n1.png ──
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
if os.path.exists("n1.png"):
    st.image("n1.png", width=180)
else:
    st.markdown('<h2 style="letter-spacing:4px; font-weight:800; margin:0;">NEXION</h2>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── LÓGICA DE LOGIN ──
if not st.session_state.splash_completado:
    st.session_state.splash_completado = True
    st.rerun()

if not st.session_state.autenticado:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<br><br><h3 style='text-align:center; letter-spacing:5px;'>SYSTEM ACCESS</h3>", unsafe_allow_html=True)
        st.text_input("OPERATOR_ID")
        st.text_input("ACCESS_KEY", type="password")
        if st.button("VERIFY IDENTITY", use_container_width=True):
            st.session_state.autenticado = True
            st.rerun()
else:
    # ── MENÚ PRINCIPAL (NIVEL 1 - DERECHA) ──
    tabs_n1 = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])

    # --- 1. DASHBOARD ---
    with tabs_n1[0]:
        st.markdown("<p style='font-size:9px; letter-spacing:2px; margin: 25px 0 0 0;'>PERÍODO</p>", unsafe_allow_html=True)
        st.selectbox("FEBRERO", ["ENERO", "FEBRERO", "MARZO"], label_visibility="collapsed")
        
        # SUBSECCIONES (NIVEL 2 - IZQUIERDA)
        sub_dashboard = st.tabs(["KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"])
        with sub_dashboard[0]:
            st.write("Renderizando KPI'S...")
        with sub_dashboard[1]:
            st.write("Renderizando RASTREO...")

    # --- 2. SEGUIMIENTO ---
    with tabs_n1[1]:
        sub_seguimiento = st.tabs(["TRK", "GANTT", "QUEJAS"])
        with sub_seguimiento[0]: st.write("Contenido TRK")

    # --- 3. REPORTES ---
    with tabs_n1[2]:
        sub_reportes = st.tabs(["APQ", "OPS", "OTD"])
        with sub_reportes[0]: st.write("Contenido Reportes")

    # --- 4. FORMATOS ---
    with tabs_n1[3]:
        sub_formatos = st.tabs(["SALIDA PT", "CONTRARRECIBOS", "MUESTRAS"])
        with sub_formatos[0]: st.write("Contenido Formatos")

    # --- 5. HUB LOG ---
    with tabs_n1[4]:
        sub_hub = st.tabs(["SMART ROUTING", "DATA MGMT", "ORDER STAGING"])
        with sub_hub[0]: st.write("Contenido Hub")

    # ── FOOTER ──
    st.markdown(f"""<div class="footer">NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 // ENGINEERED BY <b>HERNANPHY</b></div>""", unsafe_allow_html=True)





























