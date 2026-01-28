import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA Y VARIABLES ──────────────────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "pagina" not in st.session_state: 
    st.session_state.pagina = "RASTREO"

tema = st.session_state.tema
vars_css = {
    "oscuro": {"bg": "#05070A", "card": "#0D1117", "text": "#F0F6FC", "sub": "#8B949E", "border": "#1B1F24"},
    "claro": {"bg": "#E9ECF1", "card": "#FFFFFF", "text": "#111111", "sub": "#2D3136", "border": "#C9D1D9"}
}[tema]

# ── CSS MAESTRO ───────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .stApp {{ 
        background: {vars_css['bg']} !important; 
        color: {vars_css['text']} !important; 
        font-family: 'Inter', sans-serif !important; 
    }}
    
    /* Input Style */
    .stTextInput input {{
        background: {vars_css['card']} !important;
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-radius: 2px !important;
        height: 48px !important;
        text-align: center;
        letter-spacing: 2px;
    }}

    /* Buttons Hover Invertido */
    div.stButton>button {{
        background: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 2px !important;
        font-weight: 700 !important; 
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    div.stButton>button:hover {{
        background: {vars_css['text']} !important; 
        color: {vars_css['bg']} !important; 
    }}

    /* Footer Style */
    .footer {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: {vars_css['bg']};
        color: {vars_css['sub']};
        text-align: center;
        padding: 15px;
        font-size: 10px;
        letter-spacing: 3px;
        border-top: 1px solid {vars_css['border']};
        z-index: 100;
    }}
</style>
""", unsafe_allow_html=True)

# ── SPLASH SCREEN ────────────────────────────────────────
if "splash_completado" not in st.session_state:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS","SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="width:40px;height:40px;border:1px solid {vars_css['border']};border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
              <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.6)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER FIJO ──────────────────────────────────────────
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="center")

with c1:
    st.markdown(f"<h2 style='letter-spacing:4px; font-weight:800; margin:0; color:{vars_css['text']};'>NEXION</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:9px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-10px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    btn_labels = ["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]
    for i, b in enumerate(btn_labels):
        with cols[i]:
            if st.button(b, use_container_width=True, key=f"nav_{b}"):
                st.session_state.pagina = b
                st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:10px 0 30px;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE RENDERIZADO (ZONA DINÁMICA) ──────────────
main_container = st.container()

with main_container:
    if st.session_state.pagina == "RASTREO":
        _, col_search, _ = st.columns([1, 1.8, 1])
        with col_search:
            st.markdown(f"<p style='text-align:center; color:{vars_css['sub']}; font-size:12px; letter-spacing:8px; margin-bottom:20px;'>OPERATIONAL QUERY</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="NÚMERO DE GUÍA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")
    
    elif st.session_state.pagina == "INTELIGENCIA":
        st.subheader("Módulo de Inteligencia")
        st.info("Cargando modelos de predicción logística...")

    # Puedes agregar los demás elif aquí...

# ── PIE DE PÁGINA FIJO ───────────────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION SYSTEM v2.0.4 // TERMINAL ID: {vars_css['bg'].replace('#','')} // JALISCO, MX. © 2026
    </div>
""", unsafe_allow_html=True)


    









































































































































































































































































































































































































