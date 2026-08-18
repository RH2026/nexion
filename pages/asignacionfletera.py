import base64
from datetime import datetime, timedelta
import io
import re
import time
import unicodedata
import zipfile
import calendar
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit.components.v1 as components
import streamlit as st
import pytz
from auth import exigir_autenticacion

exigir_autenticacion("asignacionfletera")

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Almacén Historial",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── TEMA Y CSS MAESTROS ──────────────────────────────────────────
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
    "logo": "n1.png",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(15px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

[data-testid="stVerticalBlock"] > div {{ animation: fadeInUp 0.6s ease-out; }}

header, footer, [data-testid="stHeader"] {{ visibility: hidden !important; display: none !important; height: 0px !important; }}
[data-testid="collapsedControl"], [data-testid="stSidebar"], [data-testid="stToolbar"], .viewerBadge_container__1QSob, #MainMenu, button[kind="header"] {{ visibility: hidden !important; display: none !important; opacity: 0 !important; pointer-events: none !important; }}

html, body, .stApp {{ background-color: {vars_css['bg']} !important; color: {vars_css['text']} !important; font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 0.8rem !important; padding-bottom: 5rem !important; background-color: {vars_css['bg']} !important; }}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {vars_css['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {vars_css['border']}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: #00A3A3; }}

.scroll-container-almacen {{ max-height: 70vh; overflow-y: auto; padding-right: 5px; margin-bottom: 20px; }}
div[data-testid="stVerticalBlock"] {{ gap: 0.05rem !important; }}

/* AJUSTE FINO PARA EL SELECTBOX */
div[data-baseweb="select"] > div {{
    min-height: 42px !important;
    height: 42px !important;
    font-size: 10px !important;
    padding: 0px 8px !important;
    background-color: #2B343B !important;
    color: #ffffff !important;
    border: 1px solid #4B5D67 !important;
    border-radius: 6px !important;
    display: flex !important;
    align-items: center !important;
}}

.stSelectbox {{
    margin-top: -22px !important;
    margin-bottom: 0px !important;
}}

div.stButton > button, div.stDownloadButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 32px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

.footer {{ 
    position: fixed; bottom: 0 !important; left: 0 !important; width: 100% !important; 
    background-color: {vars_css['bg']} !important; color: {vars_css['sub']} !important; 
    text-align: center; padding: 12px 0px !important; font-size: 9px; 
    letter-spacing: 2px; border-top: 1px solid {vars_css['border']} !important; z-index: 999999 !important; 
}}
</style>
""",
    unsafe_allow_html=True,
)

# --- SISTEMA DE SEGURIDAD Y FUNCIONES ---
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/asignacionfletera.py"
    st.switch_page("pages/log.py")

def render_historial_almacen(data):
    if not data: return
    
    st.markdown('<p style="color:#FFFFFF; font-weight:800; letter-spacing:2px; font-size:12px; margin-bottom:12px;">HISTORIAL DE ALMACÉN // CONTROL DE FACTURAS</p>', unsafe_allow_html=True)
    st.markdown('<div class="scroll-container-almacen">', unsafe_allow_html=True)

    opciones_estatus_posibles = ["ENVIADA", "CANCELADA", "DETENIDA", "DUPLICADA", "CEDIS", "SOLO FACTURA", "NO ENTREGADA", "MOSTRADOR", "EXPORTACION"]

    for idx, item in enumerate(data):
        key_estatus = f"estatus_sel_{idx}_{item['factura']}"
        if key_estatus not in st.session_state: st.session_state[key_estatus] = "ENVIADA" if item.get('fecha_envio') else "PENDIENTE"
        estatus_val = st.session_state[key_estatus]
        color_borde = "#10b981" if estatus_val == "ENVIADA" else "#64748b"

        with st.container():
            col_tarjeta, col_select = st.columns([8.4, 1.6], vertical_alignment="center")
            with col_tarjeta:
                st.markdown(f"""
                <div style="background-color: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-left: 5px solid {color_borde}; border-radius: 6px; padding: 0px 12px; width: 100%; display: flex; align-items: center; height: 42px;">
                    <div style="display: flex; align-items: center; gap: 20px; font-size: 11px; width: 100%;">
                        <b style="color: white; font-style: italic; font-size: 12px;">#{item['factura']}</b>
                        <span style="color: #7dd3fc; flex-grow: 1;">{item.get('nombre_extran', 'N/A')}</span>
                        <span style="color: #fde047; font-weight: bold; margin-left: auto; padding-right: 15px;">{item.get('transporte', 'S/T')}</span>
                        <span style="color: #38bdf8; font-weight: 700; font-size: 10px;">📅 {item.get('fecha_envio', 'SIN F. ENVÍO')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_select:
                nuevo_estatus = st.selectbox("Estatus", opciones_estatus_posibles, index=opciones_estatus_posibles.index(estatus_val), key=f"sel_estatus_{idx}_{item['factura']}", label_visibility="collapsed")
                if nuevo_estatus != estatus_val:
                    st.session_state[key_estatus] = nuevo_estatus
                    st.rerun()
        st.markdown("<div style='margin-bottom: 2px;'></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN ---
def main():
    # Carga de datos simplificada para el ejemplo
    df_proc = pd.DataFrame({'factura': ['242420'], 'nombre_extran': ['HOLIDAY INN'], 'transporte': ['ONE'], 'fecha_envio': ['14/08/2026']})
    render_historial_almacen(df_proc.to_dict('records'))

if __name__ == "__main__":
    main()
