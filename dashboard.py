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

# ── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────
st.set_page_config(
    page_title="NEXION | Core",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── ESTADO GLOBAL ────────────────────────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

tema = st.session_state.tema

vars_css = {
    "oscuro": {
        "bg": "#0E1117",
        "card": "#111827",
        "text": "#F0F6FC",
        "sub": "#8B949E",
        "border": "#1B1F24",
        "logo": "n1.png"
    },
    "claro": {
        "bg": "#E3E7ED",
        "card": "#FFFFFF",
        "text": "#111111",
        "sub": "#2D3136",
        "border": "#C9D1D9",
        "logo": "n2.png"
    }
}[tema]

# ── CSS MAESTRO ESTABILIZADO ──────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{
    visibility: hidden;
    height: 0px;
}}

.block-container {{
    padding-top: 0.5rem !important;
    padding-bottom: 0rem !important;
}}

.stApp {{
    background: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
    transition: background-color .6s ease, color .6s ease;
}}

/* ── CONTENIDO ANIMADO SOLAMENTE ── */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.main-content > div {{
    animation: fadeInUp .45s ease-out;
}}

/* INPUT */
.stTextInput input {{
    background: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    height: 42px !important;
    font-size: 11px !important;
    text-align: center !important;
    letter-spacing: 2px;
}}

/* BOTONES */
div.stButton > button {{
    background: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    font-size: 10px !important;
    height: 32px !important;
    font-weight: 700 !important;
    width: 100%;
    min-width: 40px;
}}

div.stButton > button:hover {{
    background: {vars_css['text']} !important;
    color: {vars_css['bg']} !important;
}}

/* LOGO ESTABLE */
div[data-testid="stImage"] img {{
    height: 48px !important;
    object-fit: contain !important;
}}

.footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: {vars_css['bg']};
    color: {vars_css['sub']};
    font-size: 9px;
    letter-spacing: 2px;
    text-align: center;
    padding: 10px;
    border-top: 1px solid {vars_css['border']};
    z-index: 100;
}}
</style>
""", unsafe_allow_html=True)

# ── SPLASH ───────────────────────────────────────────────────
if not st.session_state.splash_completado:
    splash = st.empty()
    with splash.container():
        for txt in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;
                        justify-content:center;align-items:center;">
                <div style="width:40px;height:40px;border:1px solid {vars_css['border']};
                            border-top:1px solid {vars_css['text']};
                            border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-size:10px;letter-spacing:5px;
                          color:{vars_css['text']};">{txt}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.6)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER ───────────────────────────────────────────────────
c1, c2, c3 = st.columns([1.5, 5, .4], vertical_alignment="center")

with c1:
    st.image(vars_css["logo"], width=120)
    st.markdown(
        f"<p style='font-size:8px;letter-spacing:2px;color:{vars_css['sub']};margin-top:-20px;'>CORE INTELLIGENCE</p>",
        unsafe_allow_html=True
    )

with c2:
    menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]
    cols = st.columns(len(menus))
    for i, m in enumerate(menus):
        with cols[i]:
            label = f"● {m}" if st.session_state.menu_main == m else m
            if st.button(label, key=f"main_{m}"):
                st.session_state.menu_main = m
                st.session_state.menu_sub = "GENERAL"
                st.rerun()

with c3:
    icon = "☾" if tema == "oscuro" else "☀"
    if st.button(icon, key="theme_btn"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']};'>", unsafe_allow_html=True)

# ── CONTENIDO ────────────────────────────────────────────────
st.markdown("<div class='main-content'>", unsafe_allow_html=True)

if st.session_state.menu_main == "TRACKING":
    st.markdown("<div style='margin-top:8vh'></div>", unsafe_allow_html=True)
    _, c, _ = st.columns([1, 1.6, 1])
    with c:
        st.markdown(
            f"<p style='text-align:center;color:{vars_css['sub']};letter-spacing:8px;font-size:11px;'>OPERATIONAL QUERY</p>",
            unsafe_allow_html=True
        )
        ref = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA", label_visibility="collapsed")
        if st.button("EXECUTE SYSTEM SEARCH"):
            st.toast(f"Buscando: {ref}")

st.markdown("</div>", unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────
st.markdown("""
<div class="footer">
NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
</div>
""", unsafe_allow_html=True)







































































































































































































































































































































































































































