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

# ── VARIABLES DE TEMA ──
vars_css = {
    "bg": "#1B1E23", "card": "#282D34", "text": "#FFFAFA", 
    "sub": "#FFFFFF", "border": "#414852", "accent": "#00FFAA"
}

# ── CSS MAESTRO: NAVEGACIÓN DUAL ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
.stApp {{ background-color: {vars_css['bg']} !important; color: {vars_css['text']} !important; font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 1rem !important; }}

/* --- MENÚ PRINCIPAL (BOTONES DERECHA) --- */
div.stButton > button {{
    background-color: transparent !important;
    color: {vars_css['sub']} !important;
    border: none !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    font-weight: 700 !important;
    opacity: 0.5;
    transition: 0.3s;
}}
div.stButton > button:hover {{ opacity: 1; color: {vars_css['accent']} !important; }}

/* --- SUBMENÚ: BARRA CONTINUA (RADIO HORIZONTAL) --- */
div[data-testid="stHorizontalBlock"] div[data-testid="stWidgetLabel"] {{ display: none; }} /* Oculta labels de radio */

div[role="radiogroup"] {{
    flex-direction: row !important;
    background-color: rgba(255,255,255,0.03) !important;
    padding: 5px !important;
    border-radius: 5px !important;
    border: 1px solid {vars_css['border']}44 !important;
    width: fit-content !important;
}}

div[role="radiogroup"] label {{
    background-color: transparent !important;
    padding: 6px 15px !important;
    border-radius: 4px !important;
    margin-right: 5px !important;
    transition: 0.3s !important;
}}

div[role="radiogroup"] label[data-baseweb="radio"] {{
    background-color: transparent !important;
    color: {vars_css['sub']} !important;
    opacity: 0.6;
}}

div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {{
    background-color: {vars_css['accent']}11 !important;
    color: {vars_css['accent']} !important;
    opacity: 1;
    border: 1px solid {vars_css['accent']}33 !important;
}}

/* Ocultar el círculo del radio original */
div[role="radiogroup"] [data-testid="stMarkdownContainer"] p {{
    font-size: 10px !important;
    letter-spacing: 2px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
}}
div[role="radiogroup"] div[data-id="stRadio-option-label"] div:first-child {{ display: none !important; }}

/* FOOTER */
.footer {{ 
    position: fixed; bottom: 0; left: 0; width: 100%; 
    background-color: {vars_css['bg']}; color: {vars_css['sub']}; 
    text-align: center; padding: 12px 0; font-size: 8px; letter-spacing: 2px;
    border-top: 1px solid {vars_css['border']}; z-index: 999;
}}
</style>
""", unsafe_allow_html=True)

# ── ESTRUCTURA DE NAVEGACIÓN ──
if "main_choice" not in st.session_state: st.session_state.main_choice = "DASHBOARD"

# 1. HEADER: LOGO E IZQUIERDA | TÍTULO CENTRO | MENÚ DERECHA
h_col1, h_col2, h_col3 = st.columns([1.5, 2, 3])

with h_col1:
    st.markdown(f"**NEXION** \n<span style='font-size:7px; letter-spacing:3px; opacity:0.6;'>SYSTEM SOLUTIONS</span>", unsafe_allow_html=True)

with h_col2:
    st.markdown(f"<p style='text-align:center; font-size:10px; letter-spacing:8px; opacity:0.3; margin-top:10px;'>D A S H B O A R D</p>", unsafe_allow_html=True)

with h_col3:
    m_btns = st.columns(5)
    labels = ["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"]
    for i, l in enumerate(labels):
        if m_btns[i].button(l):
            st.session_state.main_choice = l
            st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}22; margin: 0 0 15px 0;'>", unsafe_allow_html=True)

# 2. BARRA DE SUBMENÚ (ALINEADA A LA IZQUIERDA)
sub_map = {
    "DASHBOARD": ["GENERAL", "KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "CONTRARRECIBOS", "MUESTRAS"],
    "HUB LOG": ["SMART ROUTING", "DATA MANAGEMENT", "ORDER STAGING"]
}

# La barra de submenú como un Radio Horizontal (estilo Apple/SaaS)
c_sub, _ = st.columns([4, 1])
with c_sub:
    sub_choice = st.radio("", sub_map[st.session_state.main_choice], horizontal=True, label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# ── CONTENIDO DINÁMICO ──
if st.session_state.main_choice == "FORMATOS":
    if sub_choice == "MUESTRAS":
        st.subheader("CONTROL DE MUESTRAS")
        # Aquí va tu lógica de Muestras
    elif sub_choice == "SALIDA DE PT":
        st.subheader("SALIDA DE PRODUCTO TERMINADO")

elif st.session_state.main_choice == "DASHBOARD":
    st.write(f"VISTA ACTIVA: {sub_choice}")

# ── FOOTER ──
st.markdown(f"""<div class="footer">NEXION // LOGISTICS OS // © 2026 // ENGINEERED BY <b>HERNANPHY</b></div>""", unsafe_allow_html=True)








































