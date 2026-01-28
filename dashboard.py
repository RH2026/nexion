Entiendo el problema, Rigoberto. Lo que sucede es que el "placeholder" (el texto de fondo) tiene un color predeterminado por el navegador que, en fondos blancos, se pierde por falta de contraste.

He añadido una regla específica en el CSS Maestro para forzar que el color del placeholder use siempre el color de contraste (--sub) definido en tu diccionario de variables. Así se verá nítido tanto en modo oscuro como en el modo claro que me mostraste.

Aquí tienes el código corregido:

Python
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

# ── CSS MAESTRO (TRANSICIÓN + CENTRADO + FIX PLACEHOLDER) ──
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

    /* CENTRADO Y ESTILO DE BUSCADOR */
    .stTextInput input {{
        background: {vars_css['card']} !important;
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-radius: 2px !important;
        height: 48px !important;
        text-align: center !important;
        letter-spacing: 2px;
        transition: all 0.4s ease;
    }}

    /* FIX: COLOR DEL TEXTO "INGRESE GUÍA O REFERENCIA..." */
    /* Se aplica a todos los motores de búsqueda para asegurar visibilidad */
    .stTextInput input::placeholder {{ color: {vars_css['sub']} !important; opacity: 1; }}
    .stTextInput input::-webkit-input-placeholder {{ color: {vars_css['sub']} !important; }}
    .stTextInput input::-moz-placeholder {{ color: {vars_css['sub']} !important; }}

    /* LOGO */
    div[data-testid='stImage'] img {{
        image-rendering: -webkit-optimize-contrast !important;
        image-rendering: crisp-edges !important;
    }}
    div[data-testid='stImage'] {{ margin-top: -20px !important; }}
    
    /* MENÚ */
    div.stButton>button {{
        background: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 2px !important;
        font-weight: 700 !important; 
        text-transform: uppercase;
        font-size: 10px !important;
        height: 35px !important;
        transition: all 0.3s ease !important;
    }}
    div.stButton>button:hover {{
        background: {vars_css['text']} !important; 
        color: {vars_css['bg']} !important; 
    }}

    /* FOOTER */
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

# ── HEADER ──────────────────────────────────────────────────
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

# ── CONTENEDOR CENTRAL ──────────────────────────────────────
main_container = st.container()

with main_container:
    if st.session_state.pagina == "RASTREO":
        st.markdown("<div style='margin-top: 8vh;'></div>", unsafe_allow_html=True)
        
        _, col_search, _ = st.columns([1, 1.8, 1])
        with col_search:
            st.markdown(f"<p style='text-align:center; color:{vars_css['sub']}; font-size:12px; letter-spacing:8px; margin-bottom:20px;'>OPERATIONAL QUERY</p>", unsafe_allow_html=True)
            
            # Buscador con placeholder ahora visible en blanco
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                with st.status("Accesando a Core...", expanded=False):
                    time.sleep(1)
                st.toast(f"Consultando: {busqueda}")

# ── FOOTER ──────────────────────────────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
    </div>
""", unsafe_allow_html=True)












































































































































































































































































































































































































