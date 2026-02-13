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

# 1. CONFIGURACIÓN MAESTRA
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

# --- ESTILOS DE ALTO IMPACTO (CERO PENDEJADAS) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    /* Reset de UI */
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    .stApp {{ background-color: #0F1115 !important; font-family: 'Inter', sans-serif !important; }}
    .block-container {{ padding: 0rem !important; }}

    /* HEADER INDUSTRIAL */
    .custom-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 60px;
        background: rgba(18, 20, 24, 0.95);
        border-bottom: 1px solid rgba(255,255,255,0.05);
        position: sticky; top: 0; z-index: 999;
    }}
    .brand-section {{ line-height: 1; }}
    .brand-logo {{ font-weight: 900; letter-spacing: 5px; font-size: 22px; color: white; }}
    .brand-tag {{ font-size: 7px; letter-spacing: 3px; color: #00FFAA; display: block; opacity: 0.8; }}

    /* BARRA DE SUBMENÚ (BARRA ÚNICA) */
    .sub-bar {{
        background: #16191E;
        padding: 10px 60px;
        display: flex;
        gap: 35px;
        border-bottom: 1px solid rgba(0, 255, 170, 0.1);
    }}

    /* SOBREESCRIBIR BOTONES PARA QUE PAREZCAN TEXTO DE MENÚ */
    div.stButton > button {{
        background: none !important;
        border: none !important;
        color: rgba(255,255,255,0.4) !important;
        font-size: 11px !important;
        letter-spacing: 2px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        padding: 0px !important;
        width: auto !important;
        transition: 0.3s !important;
    }}
    div.stButton > button:hover {{
        color: #00FFAA !important;
        transform: translateY(-1px);
    }}
    
    /* FOOTER */
    .footer-core {{
        position: fixed; bottom: 0; width: 100%;
        padding: 15px; background: #0F1115;
        border-top: 1px solid rgba(255,255,255,0.03);
        text-align: center; font-size: 8px; letter-spacing: 4px; color: rgba(255,255,255,0.3);
    }}
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE NAVEGACIÓN ---
if "main_nav" not in st.session_state: st.session_state.main_nav = "DASHBOARD"
if "sub_nav" not in st.session_state: st.session_state.sub_nav = "GENERAL"

# --- RENDERIZADO DE HEADER (LOGO IZQUIERDA | MENÚ DERECHA) ---
st.markdown(f"""
<div class="custom-header">
    <div class="brand-section">
        <span class="brand-logo">NEXION</span>
        <span class="brand-tag">SYSTEM SOLUTIONS</span>
    </div>
    <div style="font-size: 10px; letter-spacing: 10px; opacity: 0.2;">{st.session_state.main_nav}</div>
</div>
""", unsafe_allow_html=True)

# Inyectamos los botones del menú principal a la derecha usando columnas sobre el header
# (Usamos un truco de margen negativo para subirlos al nivel del header)
cols_main = st.columns([4, 1, 1, 1, 1, 1])
main_labels = ["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"]

for i, label in enumerate(main_labels):
    with cols_main[i+1]:
        st.markdown("<div style='margin-top: -55px;'>", unsafe_allow_html=True)
        # Resaltado si está activo
        estilo = "color: #00FFAA !important; opacity: 1;" if st.session_state.main_nav == label else ""
        if st.button(label, key=f"m_{label}"):
            st.session_state.main_nav = label
            # Reset subnav
            defaults = {"DASHBOARD":"GENERAL", "SEGUIMIENTO":"TRK", "REPORTES":"APQ", "FORMATOS":"SALIDA DE PT", "HUB LOG":"SMART ROUTING"}
            st.session_state.sub_nav = defaults[label]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- RENDERIZADO DE SUBMENÚ (BARRA ÚNICA IZQUIERDA) ---
sub_map = {
    "DASHBOARD": ["GENERAL", "KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "CONTRARRECIBOS", "MUESTRAS"],
    "HUB LOG": ["SMART ROUTING", "DATA MANAGEMENT", "ORDER STAGING"]
}

# Barra de submenú
st.markdown('<div style="background: #16191E; border-bottom: 1px solid rgba(0,255,170,0.1); padding: 5px 60px;">', unsafe_allow_html=True)
cols_sub = st.columns([1 for _ in sub_map[st.session_state.main_nav]] + [5]) # El final es para empujar a la izquierda
for i, sub_label in enumerate(sub_map[st.session_state.main_nav]):
    with cols_sub[i]:
        # El punto indica que está activo
        display_text = f"● {sub_label}" if st.session_state.sub_nav == sub_label else sub_label
        if st.button(display_text, key=f"s_{sub_label}"):
            st.session_state.sub_nav = sub_label
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- ÁREA DE TRABAJO ---
st.markdown("<div style='padding: 40px 60px;'>", unsafe_allow_html=True)

if st.session_state.main_nav == "FORMATOS":
    if st.session_state.sub_nav == "MUESTRAS":
        st.markdown("<h2 style='letter-spacing:-1px;'>Control de Muestras</h2>", unsafe_allow_html=True)
        st.write("Interfaz de gestión de muestras lista para código.")
    elif st.session_state.sub_nav == "SALIDA DE PT":
        st.markdown("<h2 style='letter-spacing:-1px;'>Salida de Producto Terminado</h2>", unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("""
<div class="footer-core">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 // ENGINEERED BY HERNANPHY
</div>
""", unsafe_allow_html=True)









































