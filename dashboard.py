import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
import plotly.graph_objects as go
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA FIJO (MODO CLARO FORZADO) ──────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "claro"
if "menu_main" not in st.session_state: 
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"

# Variables de diseño
vars_css = {
    "bg": "#E3E7ED",      # Fondo principal solicitado
    "card": "#FFFFFF",    # Fondos de tarjetas e inputs
    "text": "#111111",    # Texto principal
    "sub": "#2D3136",     # Texto secundario
    "border": "#C9D1D9",  # Bordes y líneas
    "logo": "n2.png"      # Logo
}

# ── CSS MAESTRO (REPARADO: ESPACIO, ANIMACIÓN Y FOOTER FIJO) ──
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* 1. Limpieza de Interfaz */
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .block-container {{ 
        padding-top: 2rem !important; 
        padding-bottom: 5rem !important; 
    }}

    .stApp {{ 
        background-color: {vars_css['bg']} !important; 
        color: {vars_css['text']} !important; 
        font-family: 'Inter', sans-serif !important;
    }}

    /* 2. ESPACIADO DE BLOQUES */
    [data-testid="stVerticalBlock"] {{
        gap: 0.8rem !important; 
    }}

    /* 3. ANIMACIÓN DE ENTRADA (Fade In Up) */
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Aplicar animación SOLO al contenido (excluyendo el footer) */
    [data-testid="stVerticalBlock"] > div:not(.element-container:has(.footer)) {{
        animation: fadeInUp 0.6s ease-out;
    }}

    /* ── TÍTULOS ESTILO "OPERATIONAL QUERY" (H3) ── */
    h3 {{
        font-size: 13px !important; /* Tamaño similar al de la captura */
        font-weight: 400 !important;
        text-transform: uppercase;
        letter-spacing: 8px !important; /* El secreto del estilo */
        text-align: center !important;
        margin-top: 30px !important;
        margin-bottom: 25px !important;
        color: {vars_css['sub']} !important;
        display: block;
        width: 100%;
    }}

    /* 5. ESTILO DE BOTONES */
    div.stButton > button {{
        background-color: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 2px !important;
        font-weight: 700 !important; 
        text-transform: uppercase;
        font-size: 11px !important;
        height: 38px !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }}

    div.stButton > button:hover {{
        background-color: {vars_css['text']} !important; 
        color: {vars_css['bg']} !important; 
        border-color: {vars_css['text']} !important;
    }}

    /* Botones de Submenú */
    div.stButton > button[key^="sub_"] {{
        height: 32px !important;
        font-size: 10px !important;
        margin-top: 2px !important;
    }}

    /* 6. INPUT DE BÚSQUEDA Y TEXTO OPERATIONAL */
    .stTextInput input {{
        background-color: {vars_css['card']} !important;
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-radius: 2px !important;
        height: 45px !important;
        text-align: center !important;
        letter-spacing: 2px;
    }}

    .op-query-text {{
        text-align: center;
        color: {vars_css['sub']};
        font-size: 11px;
        letter-spacing: 8px;
        margin-bottom: 25px;
        text-transform: uppercase;
    }}

    /* 7. FOOTER DEFINITIVO (INMUNE A ANIMACIONES) */
    .footer {{
        position: fixed;
        bottom: 0 !important; 
        left: 0 !important; 
        width: 100vw !important;
        background-color: {vars_css['bg']} !important;
        color: {vars_css['sub']} !important;
        text-align: center;
        padding: 12px 0px !important;
        font-size: 9px;
        letter-spacing: 2px;
        border-top: 1px solid {vars_css['border']} !important;
        z-index: 999999 !important;
        animation: none !important;
        transform: none !important;
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

# ── HEADER Y NAVEGACIÓN (LÍNEA 1) ──────────────────────────
header_zone = st.container()
with header_zone:
    c1, c2 = st.columns([1.5, 5.4], vertical_alignment="center")
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
                seleccionado = st.session_state.menu_main == m
                btn_label = f"● {m}" if seleccionado else m
                if st.button(btn_label, use_container_width=True, key=f"main_{m}"):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()

# ── SUBMENÚS (LÍNEA 2 COMPLETA) ────────────────────────────
sub_map = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "PAGOS"]
}

current_subs = sub_map.get(st.session_state.menu_main, [])
if current_subs:
    sub_zone = st.container()
    with sub_zone:
        cols_sub = st.columns(len(current_subs) + 4)
        for i, s in enumerate(current_subs):
            with cols_sub[i]:
                sub_activo = st.session_state.menu_sub == s
                sub_label = f"» {s}" if sub_activo else s
                if st.button(sub_label, use_container_width=True, key=f"sub_{s}"):
                    st.session_state.menu_sub = s
                    st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px; opacity:0.3;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO ──────────────────────────────────
main_container = st.container()
with main_container:
    # 1. TRACKING
    if st.session_state.menu_main == "TRACKING":
        st.markdown("<div style='margin-top: 5vh;'></div>", unsafe_allow_html=True)
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"<p class='op-query-text'>O P E R A T I O N A L &nbsp; Q U E R Y</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")

    # 2. SEGUIMIENTO
    elif st.session_state.menu_main == "SEGUIMIENTO":
        if st.session_state.menu_sub == "TRK":
            st.subheader("SEGUIMIENTO > TRK")
            st.info("Espacio para contenido de Tracking Operativo")
        elif st.session_state.menu_sub == "GANTT":
            st.subheader("SEGUIMIENTO > GANTT")
            st.info("Espacio para visualización de Cronograma")
        elif st.session_state.menu_sub == "QUEJAS":
            st.subheader("SEGUIMIENTO > PORTAL DE QUEJAS")
            st.info("Contenedor para registro y seguimiento de quejas")

    # 3. REPORTES
    elif st.session_state.menu_main == "REPORTES":
        st.subheader(f"MÓDULO DE INTELIGENCIA > {st.session_state.menu_sub}")

    # 4. FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        if st.session_state.menu_sub == "SALIDA DE PT":
            st.subheader("FORMATOS > SALIDA DE PRODUCTO TERMINADO")
        elif st.session_state.menu_sub == "PAGOS":
            st.subheader("FORMATOS > CONTROL DE PAGOS")
        else:
            st.subheader("CENTRO DE DOCUMENTACIÓN")
            st.write("Seleccione un formato del submenú superior.")

# ── FOOTER FIJO (SOLUCIÓN DEFINITIVA) ────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
    </div>
""", unsafe_allow_html=True)


















































































































































































































































































































































































































































