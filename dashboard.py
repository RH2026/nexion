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

/* PLACEHOLDER FIX (CLARO + OSCURO) */
.stTextInput input::placeholder {
    color: {vars_css['sub']} !important;
    opacity: 1 !important;
}

.stTextInput input::-webkit-input-placeholder {
    color: {vars_css['sub']} !important;
}

.stTextInput input:-ms-input-placeholder {
    color: {vars_css['sub']} !important;
}

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

# ── HEADER Y NAVEGACIÓN PRINCIPAL ──────────────────────────
header_zone = st.container()
with header_zone:
    c1, c2, c3 = st.columns([1.5, 5, 0.4], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=120)
            st.markdown(
                f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; "
                f"margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>",
                unsafe_allow_html=True
            )
        except:
            st.markdown(
                "<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>",
                unsafe_allow_html=True
            )

    with c2:
        cols_main = st.columns(4)
        main_menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]

        for i, m in enumerate(main_menus):
            with cols_main[i]:
                label = f"● {m}" if st.session_state.menu_main == m else m
                if st.button(label, key=f"main_{m}", use_container_width=True):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()

    with c3:
        icon = "☾" if tema == "oscuro" else "☀"
        if st.button(icon, key="theme_btn"):
            st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
            st.rerun()

st.markdown(
    f"<hr style='border-top:1px solid {vars_css['border']}; margin:-5px 0 10px;'>",
    unsafe_allow_html=True
)

# ── SUB MENÚS (RESTAURADOS, ESTABLES, SIN ANIMACIÓN) ─────────
sub_zone = st.container()
with sub_zone:
    sub_map = {
        "TRACKING": [],
        "SEGUIMIENTO": ["TRK", "GANTT"],
        "REPORTES": ["APQ", "OPS", "OTD"],
        "FORMATOS": ["SALIDA DE PT"]
    }

    current_subs = sub_map.get(st.session_state.menu_main, [])

    if current_subs:
        cols_sub = st.columns(len(current_subs) + 4)

        for i, s in enumerate(current_subs):
            with cols_sub[i]:
                label = f"» {s}" if st.session_state.menu_sub == s else s
                if st.button(label, key=f"sub_{s}", use_container_width=True):
                    st.session_state.menu_sub = s
                    st.rerun()

        st.markdown(
            f"<hr style='border-top:1px solid {vars_css['border']}; "
            f"opacity:0.3; margin:0px 0 20px;'>",
            unsafe_allow_html=True
        )

# ── CONTENIDO (ÚNICO BLOQUE ANIMADO) ────────────────────────
st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# 1. TRACKING
if st.session_state.menu_main == "TRACKING":
    st.markdown("<div style='margin-top: 8vh;'></div>", unsafe_allow_html=True)
    _, col_search, _ = st.columns([1, 1.6, 1])

    with col_search:
        st.markdown(
            f"<p style='text-align:center; color:{vars_css['sub']}; "
            f"font-size:11px; letter-spacing:8px; margin-bottom:20px;'>"
            f"O P E R A T I O N A L &nbsp; Q U E R Y</p>",
            unsafe_allow_html=True
        )

        busqueda = st.text_input(
            "REF",
            placeholder="INGRESE GUÍA O REFERENCIA...",
            label_visibility="collapsed"
        )

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
            st.toast(f"Buscando: {busqueda}")

# 2. SEGUIMIENTO
elif st.session_state.menu_main == "SEGUIMIENTO":

    if st.session_state.menu_sub == "TRK":
        st.subheader("SEGUIMIENTO > TRK")

    elif st.session_state.menu_sub == "GANTT":
        st.subheader("SEGUIMIENTO > GANTT")
        # ⬅️ AQUÍ VA TODO TU CÓDIGO GANTT ORIGINAL SIN CAMBIOS

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

st.markdown("</div>", unsafe_allow_html=True)








































































































































































































































































































































































































































