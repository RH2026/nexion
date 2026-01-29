import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA Y VARIABLES ──────────────────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state: 
    st.session_state.menu_main = "TRACKING"

tema = st.session_state.tema
vars_css = {
    "oscuro": {"bg": "#05070A", "card": "#0D1117", "text": "#F0F6FC", "sub": "#8B949E", "border": "#1B1F24", "logo": "n1.png"},
    "claro": {"bg": "#E9ECF1", "card": "#FFFFFF", "text": "#111111", "sub": "#2D3136", "border": "#C9D1D9", "logo": "n2.png"}
}[tema]

# ── CSS MAESTRO (ELITE UI DESIGN) ─────────────────────────
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
        transition: background-color 0.8s ease;
    }}

    /* --- INPUT BUSCADOR --- */
    .stTextInput input {{
        background: {vars_css['card']} !important;
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-radius: 2px !important;
        height: 42px !important;
        font-size: 11px !important;
        text-align: center !important;
        letter-spacing: 2px;
    }}

    /* --- BOTONES MENÚ PRINCIPAL --- */
    div.stButton>button {{
        background: transparent !important; 
        color: {vars_css['sub']} !important;
        border: none !important;
        font-weight: 700 !important; 
        text-transform: uppercase;
        font-size: 11px !important;
        letter-spacing: 2px;
        transition: all 0.4s ease;
    }}
    div.stButton>button:hover {{
        color: {vars_css['text']} !important;
        background: transparent !important;
    }}

    /* --- DISEÑO ELITE PARA TABS (SUBMENÚS) --- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 40px;
        background-color: transparent;
        border-bottom: 1px solid {vars_css['border']};
        margin-bottom: 25px;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        background-color: transparent !important;
        border: none !important;
        color: {vars_css['sub']} !important;
        font-size: 10px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 3px;
        padding: 0px 10px !important;
        transition: all 0.3s ease;
    }}

    .stTabs [aria-selected="true"] {{
        color: {vars_css['text']} !important;
        border-bottom: 2px solid {vars_css['text']} !important;
    }}

    /* NITIDEZ LOGO */
    div[data-testid='stImage'] img {{
        image-rendering: -webkit-optimize-contrast !important;
        transform: translateZ(0);
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
    p = st.empty()
    with p.container():
        for m in ["CORE SYSTEM ACCESS", "SYNCHRONIZING DATA", "READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="width:30px;height:30px;border:1px solid {vars_css['border']};border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
              <p style="margin-top:30px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
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
            st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>", unsafe_allow_html=True)

    with c2:
        cols_main = st.columns(4)
        main_menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]
        for i, m in enumerate(main_menus):
            with cols_main[i]:
                # Estilo dinámico para el botón activo
                label = f"● {m}" if st.session_state.menu_main == m else m
                if st.button(label, use_container_width=True, key=f"main_{m}"):
                    st.session_state.menu_main = m
                    st.rerun()

    with c3:
        if st.button("☾" if tema == "oscuro" else "☀", key="theme_btn"):
            st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
            st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:-5px 0 20px;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO DINÁMICO (DISEÑO ELITE) ────────
main_container = st.container()

with main_container:
    # 1. TRACKING
    if st.session_state.menu_main == "TRACKING":
        st.markdown("<div style='margin-top: 8vh;'></div>", unsafe_allow_html=True)
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"<p style='text-align:center; color:{vars_css['sub']}; font-size:11px; letter-spacing:8px; margin-bottom:20px;'>O P E R A T I O N A L &nbsp; Q U E R Y</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")

    # 2. SEGUIMIENTO (USANDO TABS ELITE)
    elif st.session_state.menu_main == "SEGUIMIENTO":
        tab1, tab2 = st.tabs(["TRK", "GANTT"])
        with tab1:
            st.write("### Panel de Seguimiento TRK")
            # TU CÓDIGO AQUÍ
        with tab2:
            st.write("### Visualización GANTT")
            # TU CÓDIGO AQUÍ

    # 3. REPORTES (USANDO TABS ELITE)
    elif st.session_state.menu_main == "REPORTES":
        tab1, tab2, tab3 = st.tabs(["APQ", "OPS", "OTD"])
        with tab1:
            st.write("### Reporte APQ")
        with tab2:
            st.write("### Reporte Operativo OPS")
        with tab3:
            st.write("### Indicador OTD")

    # 4. FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        tab1, = st.tabs(["SALIDA DE PT"])
        with tab1:
            st.write("### Gestión: Salida de PT")

# ── FOOTER ──────────────────────────────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
    </div>
""", unsafe_allow_html=True)



















































































































































































































































































































































































































