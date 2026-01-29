import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
from github import Github
import plotly.figure_factory as ff
import plotly.graph_objects as go
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA Y VARIABLES ──────────────────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state: 
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"

tema = st.session_state.tema
vars_css = {
    "oscuro": {"bg": "#0E1117", "card": "#111827", "text": "#F0F6FC", "sub": "#8B949E", "border": "#1B1F24", "logo": "n1.png"},
    "claro": {"bg": "#E3E7ED", "card": "#FFFFFF", "text": "#111111", "sub": "#2D3136", "border": "#C9D1D9", "logo": "n2.png"}
}[tema]

# ── CSS MAESTRO (CON ANIMACIONES ELITE) ─────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .block-container {{ 
        padding-top: 0.5rem !important; 
        padding-bottom: 0rem !important; 
    }}

    .stApp {{ 
        background: {vars_css['bg']} !important; 
        color: {vars_css['text']} !important; 
        font-family: 'Inter', sans-serif !important;
        transition: background-color 0.8s ease, color 0.8s ease !important;
    }}

    /* ── ANIMACIÓN DE ENTRADA (FADE & SLIDE) ── */
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Aplicar a los contenedores principales */
    [data-testid="stVerticalBlock"] > div {{
        animation: fadeInUp 0.6s ease-out;
    }}

    /* INPUT DE BÚSQUEDA */
    .stTextInput input {{
        background: {vars_css['card']} !important;
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-radius: 2px !important;
        height: 42px !important;
        font-size: 11px !important;
        text-align: center !important;
        line-height: 42px !important;
        padding: 0px !important;
        letter-spacing: 2px;
        transition: all 0.3s ease;
    }}
    .stTextInput input:focus {{
        border-color: {vars_css['text']} !important;
        box-shadow: 0 0 10px rgba(240, 246, 252, 0.1);
    }}

    /* BOTONES Y HOVER */
    div.stButton>button {{
        background: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 2px !important;
        font-weight: 700 !important; 
        text-transform: uppercase;
        font-size: 10px !important;
        height: 32px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
    }}
    div.stButton>button:hover {{
        background: {vars_css['text']} !important; 
        color: {vars_css['bg']} !important; 
        transform: translateY(-1px);
    }}

    /* LOGO Y NITIDEZ */
    div[data-testid='stImage'] img {{
        image-rendering: -webkit-optimize-contrast !important;
        image-rendering: crisp-edges !important;
    }}
    div[data-testid='stImage'] {{ margin-top: -20px !important; }}

    .footer {{
        position: fixed;
        bottom: 0; left: 0; width: 100%;
        background-color: {vars_css['bg']};
        color: {vars_css['sub']};
        text-align: center;
        padding: 10px;
        font-size: 9px;
        letter-spacing: 2px;
        border-top: 1px solid {vars_css['border']};
        z-index: 100;
    }}
</style>
""", unsafe_allow_html=True)

# ── 4. SPLASH SCREEN ──────────────────────────────────────
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="width:40px;height:40px;border:1px solid {vars_css['border']};
              border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
              <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.7)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER Y NAVEGACIÓN PRINCIPAL ──────────────────────────
header_zone = st.container()
with header_zone:
    c1, c2, c3 = st.columns([1.5, 5, 0.4], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=120)
            st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>", unsafe_allow_html=True)

    with c2:
        cols_main = st.columns(4)
        main_menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]
        for i, m in enumerate(main_menus):
            with cols_main[i]:
                # Indicador de selección sutil
                btn_label = f"● {m}" if st.session_state.menu_main == m else m
                if st.button(btn_label, use_container_width=True, key=f"main_{m}"):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()

    with c3:
        if st.button("☾" if tema == "oscuro" else "☀", key="theme_btn"):
            st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
            st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:-5px 0 10px;'>", unsafe_allow_html=True)

# ── NAVEGACIÓN DE SUB MENÚS (DINÁMICO) ──────────────────────
sub_zone = st.container()
with sub_zone:
    sub_map = {
        "TRACKING": [],
        "SEGUIMIENTO": ["TRK", "GANTT"],
        "REPORTES": ["APQ", "OPS", "OTD"],
        "FORMATOS": ["SALIDA DE PT"]
    }
    
    current_subs = sub_map[st.session_state.menu_main]
    
    if current_subs:
        cols_sub = st.columns(len(current_subs) + 4)
        for i, s in enumerate(current_subs):
            with cols_sub[i]:
                # Efecto visual si está seleccionado
                sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                if st.button(sub_label, use_container_width=True, key=f"sub_{s}"):
                    st.session_state.menu_sub = s
                    st.rerun()
        st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; opacity:0.3; margin:0px 0 20px;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO (CON ANIMACIÓN CSS) ─────────────
main_container = st.container()
with main_container:
    
    # 1. TRACKING
    if st.session_state.menu_main == "TRACKING":
        st.markdown("<div style='margin-top: 8vh;'></div>", unsafe_allow_html=True)
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"<p style='text-align:center; color:{vars_css['sub']}; font-size:11px; letter-spacing:8px; margin-bottom:20px;'>O P E R A T I O N A L &nbsp; Q U E R Y</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")

    # 2. SEGUIMIENTO
    elif st.session_state.menu_main == "SEGUIMIENTO":
        if st.session_state.menu_sub == "TRK":
            st.subheader("SEGUIMIENTO > TRK")
            # ESPACIO PARA TU CONTENIDO
        elif st.session_state.menu_sub == "GANTT":
            st.subheader("SEGUIMIENTO > GANTT")
            
            # ESPACO PARA TU GANTT
            
    
    # 3. REPORTES
    elif st.session_state.menu_main == "REPORTES":
        if st.session_state.menu_sub == "APQ":
            st.subheader("REPORTES > APQ")
        elif st.session_state.menu_sub == "OPS":
            st.subheader("REPORTES > OPS")
        elif st.session_state.menu_sub == "OTD":
            st.subheader("REPORTES > OTD")

    # 4. FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        if st.session_state.menu_sub == "SALIDA DE PT":
            st.subheader("FORMATOS > SALIDA DE PT")

# ── FOOTER FIJO ──────────────────────────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
    </div>
""", unsafe_allow_html=True)































































































































































































































































































































































































































