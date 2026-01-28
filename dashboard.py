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
    "oscuro": {"bg": "#05070A", "card": "#0D1117", "text": "#F0F6FC", "sub": "#8B949E", "border": "#1B1F24", "logo": "n1.png"},
    "claro": {"bg": "#E9ECF1", "card": "#FFFFFF", "text": "#111111", "sub": "#2D3136", "border": "#C9D1D9", "logo": "n2.png"}
}[tema]

# ── CSS MAESTRO (INTERFACE & INTERACTIVITY) ──────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* ELIMINAR ELEMENTOS NATIVOS */
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .block-container {{ 
        padding-top: 0.5rem !important; 
        padding-bottom: 0rem !important; 
    }}

    /* TRANSICIÓN DE TEMA */
    .stApp {{ 
        background: {vars_css['bg']} !important; 
        color: {vars_css['text']} !important; 
        font-family: 'Inter', sans-serif !important;
        transition: background-color 0.8s ease, color 0.8s ease !important;
    }}

    /* ── INPUT DE BÚSQUEDA (CENTRADO + PEQUEÑO) ── */
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

    /* VISIBILIDAD DE PLACEHOLDER */
    .stTextInput input::placeholder {{ color: {vars_css['sub']} !important; opacity: 1; font-size: 11px; }}
    .stTextInput input::-webkit-input-placeholder {{ color: {vars_css['sub']} !important; }}

    /* ── BOTONES: ESTILO BASE ── */
    div.stButton>button {{
        background: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 2px !important;
        font-weight: 700 !important; 
        text-transform: uppercase;
        font-size: 10px !important;
        height: 35px !important;
        transition: all 0.3s ease-in-out !important;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    /* ── HOVER INVERTIDO (PARA TODOS LOS BOTONES) ── */
    div.stButton>button:hover {{
        background: {vars_css['text']} !important; 
        color: {vars_css['bg']} !important; 
        border-color: {vars_css['text']} !important;
    }}

    /* ── AJUSTE ESPECÍFICO PARA EL BOTÓN DE BÚSQUEDA (PRIMARY) ── */
    div.stButton>button[kind="primary"] {{
        background: {vars_css['card']} !important; /* Empezar igual que los otros */
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        height: 45px !important;
        font-size: 11px !important;
    }}

    /* Forzar el hover invertido en el botón primario también */
    div.stButton>button[kind="primary"]:hover {{
        background: {vars_css['text']} !important;
        color: {vars_css['bg']} !important;
        border-color: {vars_css['text']} !important;
    }}

    /* LOGO Y NITIDEZ */
    div[data-testid='stImage'] img {{
        image-rendering: -webkit-optimize-contrast !important;
        image-rendering: crisp-edges !important;
    }}
    div[data-testid='stImage'] {{ margin-top: -20px !important; }}

    /* FOOTER FIJO */
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
        transition: background-color 0.8s ease;
    }}
</style>
""", unsafe_allow_html=True)

# ── HEADER Y NAVEGACIÓN ─────────────────────────────────────
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
        cols = st.columns(4)
        btn_labels = ["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]
        for i, b in enumerate(btn_labels):
            with cols[i]:
                if st.button(b, use_container_width=True, key=f"nav_{b}"):
                    st.session_state.pagina = b
                    st.rerun()

    with c3:
        if st.button("☾" if tema == "oscuro" else "☀", key="theme_btn"):
            st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
            st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:-5px 0 20px;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO DINÁMICO ────────────────────────
main_container = st.container()

with main_container:
    if st.session_state.pagina == "RASTREO":
        st.markdown("<div style='margin-top: 10vh;'></div>", unsafe_allow_html=True)
        
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"""
                <p style='text-align:center; color:{vars_css['sub']}; font-size:11px; letter-spacing:8px; margin-bottom:20px; text-transform:uppercase;'>
                    O P E R A T I O N A L &nbsp; Q U E R Y
                </p>
            """, unsafe_allow_html=True)
            
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            # Botón de búsqueda (Primary)
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                with st.status("Accesando a Core Intelligence...", expanded=False):
                    time.sleep(1)
                st.toast(f"Buscando guía: {busqueda}")

    elif st.session_state.pagina == "INTELIGENCIA":
        st.markdown("<div style='margin-top: 5vh;'></div>", unsafe_allow_html=True)
        st.subheader("Módulo de Inteligencia Logística")
        st.write("Contenido en desarrollo para Xenocode...")

    elif st.session_state.pagina == "REPORTES":
        st.subheader("Reportes Operativos")
        st.write("Sección de análisis de datos SAP.")

    elif st.session_state.pagina == "FORMATOS":
        st.subheader("Formatos y Documentación")
        st.write("Descarga de formatos logísticos.")

# ── FOOTER FIJO ──────────────────────────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
    </div>
""", unsafe_allow_html=True)
















































































































































































































































































































































































































