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

# ── ESTADOS DE NAVEGACIÓN (CONTROL MANUAL) ──
if "menu_principal" not in st.session_state:
    st.session_state.menu_principal = "DASHBOARD"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

vars_css = {
    "bg": "#1B1E23", "card": "#282D34", "text": "#FFFAFA", 
    "sub": "#FFFFFF", "border": "#414852", "logo": "n1.png"
}

# ── ESTILOS CSS PERSONALIZADOS (MODO DUAL) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
.stApp {{ background-color: {vars_css['bg']} !important; color: {vars_css['text']} !important; font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 0rem !important; padding-bottom: 5rem !important; }}

/* CONTENEDOR DE NAVEGACIÓN SUPERIOR */
.nav-wrapper {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 30px;
    background: {vars_css['bg']};
    border-bottom: 1px solid {vars_css['border']}33;
    position: sticky; top: 0; z-index: 999;
}}

/* BOTONES DE MENÚ (DERECHA) */
.main-nav-btns {{
    display: flex;
    gap: 20px;
}}

/* BOTONES DE SUBMENÚ (IZQUIERDA) */
.sub-nav-wrapper {{
    display: flex;
    justify-content: flex-start;
    padding: 10px 30px;
    gap: 25px;
    background: rgba(255,255,255,0.02);
    border-bottom: 1px solid {vars_css['border']}11;
}}

/* ESTILO DE BOTÓN COMO PESTAÑA (SIN SER TAB) */
.nav-btn {{
    background: none; border: none; color: white; opacity: 0.4;
    font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
    font-weight: 700; cursor: pointer; transition: 0.3s;
    padding: 8px 0;
}}
.nav-btn:hover {{ opacity: 1; }}
.nav-btn.active {{ opacity: 1; border-bottom: 2px solid #00FFAA; }}

/* FOOTER */
.footer {{ 
    position: fixed; bottom: 0; left: 0; width: 100%; 
    background-color: {vars_css['bg']}; color: {vars_css['sub']}; 
    text-align: center; padding: 12px 0; font-size: 8px; letter-spacing: 2px;
    border-top: 1px solid {vars_css['border']}; z-index: 999;
}}
</style>
""", unsafe_allow_html=True)

# ── LOGO Y MENÚ PRINCIPAL (CONTROL MANUAL) ──
# Creamos el Header
col_logo, col_space, col_menu = st.columns([1, 1, 3])

with col_logo:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists(vars_css["logo"]):
        st.image(vars_css["logo"], width=110)
    else:
        st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-5px; opacity:0.6;'>SYSTEM SOLUTIONS</p>", unsafe_allow_html=True)

with col_space:
    st.markdown(f"<p style='text-align:center; font-size:10px; letter-spacing:10px; opacity:0.3; margin-top:25px;'>DASHBOARD</p>", unsafe_allow_html=True)

with col_menu:
    # Simulamos el menú a la derecha usando columnas de botones
    m_cols = st.columns(5)
    opciones = ["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"]
    for i, op in enumerate(opciones):
        if m_cols[i].button(op, key=f"main_{op}", use_container_width=True):
            st.session_state.menu_principal = op
            # Resetear submenú al cambiar principal
            default_sub = {"DASHBOARD":"GENERAL", "SEGUIMIENTO":"TRK", "REPORTES":"APQ", "FORMATOS":"SALIDA DE PT", "HUB LOG":"SMART ROUTING"}
            st.session_state.menu_sub = default_sub[op]
            st.rerun()

# Línea divisoria decorativa
st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}33; margin:0;'>", unsafe_allow_html=True)

# ── SUBMENÚ (IZQUIERDA) ──
sub_options = {
    "DASHBOARD": ["GENERAL", "KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "CONTRARRECIBOS", "MUESTRAS"],
    "HUB LOG": ["SMART ROUTING", "DATA MANAGEMENT", "ORDER STAGING"]
}

current_subs = sub_options[st.session_state.menu_principal]
s_cols = st.columns(len(current_subs) + 1) # +1 para dejar espacio a la derecha

for i, s_op in enumerate(current_subs):
    # Estilo especial si está activo
    label = f"● {s_op}" if st.session_state.menu_sub == s_op else s_op
    if s_cols[i].button(label, key=f"sub_{s_op}"):
        st.session_state.menu_sub = s_op
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}11; margin:0;'>", unsafe_allow_html=True)

# ── ÁREA DE CONTENIDO ──
st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.menu_principal == "FORMATOS":
    if st.session_state.menu_sub == "MUESTRAS":
        st.subheader("CONTROL DE MUESTRAS")
        st.info("Espacio para gestión de muestras logísticas.")
    elif st.session_state.menu_sub == "SALIDA DE PT":
        st.subheader("SALIDA DE PRODUCTO TERMINADO")

elif st.session_state.menu_principal == "DASHBOARD":
    if st.session_state.menu_sub == "KPI'S":
        st.write("Visualización de Indicadores Clave")

# ── FOOTER ──
st.markdown(f"""
<div class="footer">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 // ENGINEERED BY <b>HERNANPHY</b>
</div>
""", unsafe_allow_html=True)







































