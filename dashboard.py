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

# ── CSS MAESTRO (INCLUYE NITIDEZ DE LOGO) ──────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .stApp {{ 
        background: {vars_css['bg']} !important; 
        color: {vars_css['text']} !important; 
        font-family: 'Inter', sans-serif !important; 
    }}

    /* NITIDEZ EXTREMA PARA LOGOS */
    div[data-testid='stImage'] img {{
        image-rendering: -webkit-optimize-contrast !important;
        image-rendering: crisp-edges !important;
        transform: translateZ(0);
    }}

    /* Ajuste de margen para el logo */
    div[data-testid='stImage'] {{
        margin-top: -10px !important;
    }}
    
    .stTextInput input {{
        background: {vars_css['card']} !important;
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-radius: 2px !important;
        height: 48px !important;
        text-align: center;
    }}

    div.stButton>button {{
        background: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 2px !important;
        font-weight: 700 !important; 
        text-transform: uppercase;
    }}
    div.stButton>button:hover {{
        background: {vars_css['text']} !important; 
        color: {vars_css['bg']} !important; 
    }}

    .footer {{
        position: fixed;
        bottom: 0; left: 0; width: 100%;
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

# ── HEADER CON LOGOS DINÁMICOS ──────────────────────────────
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="center")

with c1:
    try:
        st.image(vars_css["logo"], width=130)
        st.markdown(f"""
            <div style='margin-top: -15px;'>
                <p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; text-transform:uppercase;'>
                    Core Intelligence
                </p>
            </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback si las imágenes no están en el directorio
        st.markdown(f"<h2 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h2>", unsafe_allow_html=True)

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

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 30px;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO (BLOQUE CENTRAL) ────────────────
main_container = st.container()

with main_container:
    if st.session_state.pagina == "RASTREO":
        _, col_search, _ = st.columns([1, 1.8, 1])
        with col_search:
            st.markdown(f"<p style='text-align:center; color:{vars_css['sub']}; font-size:12px; letter-spacing:8px; margin-bottom:20px;'>OPERATIONAL QUERY</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="REFERENCIA O GUÍA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast("Accediendo a la base de datos...")

# ── FOOTER ──────────────────────────────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION SYSTEM v2.0.4 // JALISCO, MX. © 2026
    </div>
""", unsafe_allow_html=True)











































































































































































































































































































































































































