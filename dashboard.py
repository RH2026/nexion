import streamlit as st
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

if st.session_state.tema == "oscuro":
    # --- FONDO NEGRO MÁS AZULADO (Chic/Nice) ---
    bg_color = "#05070A"      
    card_bg = "#0D1117"       # Un tono arriba para las tarjetas
    text_main = "#F0F6FC"
    text_sub = "#8B949E"
    border_color = "#21262D"  # Borde casi invisible pero presente
    btn_hover = "#161B22"
else:
    # --- FONDO BLANCO MÁS PERLA ---
    bg_color = "#F5F7FA"      
    card_bg = "#FFFFFF"       
    text_main = "#1A1C1E"
    text_sub = "#656D76"
    border_color = "#C9D1D9"
    btn_hover = "#EBEEF2"

# 3. CSS DINÁMICO REFINADO (Estilo Minimalista Zara)
st.markdown(f"""
    <style>
        header, footer, #MainMenu, div[data-testid="stDecoration"] {{visibility: hidden;}}
        
        .stApp {{
            background-color: {bg_color} !important;
            color: {text_main} !important;
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        /* Botones de Navegación Estilo "Editorial" */
        div.stButton > button {{
            background-color: {card_bg} !important;
            color: {text_main} !important;
            border: 1px solid {border_color} !important;
            border-radius: 2px !important; /* Bordes más rectos para look Zara */
            font-size: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 2px !important;
            text-transform: uppercase;
            height: 42px;
            transition: all 0.3s ease;
        }}

        div.stButton > button:hover {{
            background-color: {btn_hover} !important;
            border-color: {text_main} !important;
        }}

        /* Inputs de Búsqueda */
        .stTextInput input {{
            background-color: {card_bg} !important;
            color: {text_main} !important;
            border: 1px solid {border_color} !important;
            border-radius: 2px !important;
            height: 48px !important;
            font-size: 15px !important;
        }}

        /* Botón Primario (Alto Contraste) */
        div.stButton > button[kind="primary"] {{
            background-color: {text_main} !important;
            color: {bg_color} !important;
            border: none !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 4. SPLASH SCREEN ADAPTATIVO
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    placeholder = st.empty()
    with placeholder.container():
        mensajes = ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]
        for m in mensajes:
            st.markdown(f"""
                <div style="height: 80vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: {bg_color};">
                    <div style="width: 30px; height: 30px; border: 1px solid {border_color}; border-top: 1px solid {text_main}; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    <p style="color: {text_main}; font-family: monospace; font-size: 10px; letter-spacing: 5px; margin-top: 40px; font-weight: 200;">{m}</p>
                </div>
                <style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
            """, unsafe_allow_html=True)
            time.sleep(0.9)
    st.session_state.splash_completado = True
    st.rerun()

# 5. HEADER (Logo y Navegación)
c_logo, c_nav, c_theme = st.columns([1.5, 4, 0.5])
with c_logo:
    st.markdown(f"<h2 style='color: {text_main}; font-weight: 200; letter-spacing: 4px; margin: 0;'>NEXION</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: {text_sub}; font-size: 9px; margin-top: -5px; letter-spacing: 1px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)

with c_nav:
    m = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "ESTATUS"]):
        with m[i]:
            if st.button(b, use_container_width=True):
                st.session_state.pagina = b
                st.rerun()

with c_theme:
    icon = "☀️" if st.session_state.tema == "oscuro" else "🌙"
    if st.button(icon):
        st.session_state.tema = "claro" if st.session_state.tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown("<div style='margin-bottom: 60px;'></div>", unsafe_allow_html=True)

# 6. SECCIÓN DE BÚSQUEDA CENTRAL
_, col_search, _ = st.columns([1, 1.6, 1])
with col_search:
    st.markdown(f"<p style='text-align: center; color: {text_sub}; font-size: 12px; letter-spacing: 3px; font-weight: 300;'>OPERATIONAL QUERY</p>", unsafe_allow_html=True)
    guia = st.text_input("", placeholder="Referencia de envío...", label_visibility="collapsed")
    if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
        st.toast("Accessing manifests...", icon="🔍")
        st.session_state.busqueda = guia

st.markdown(f"<hr style='border: 0; border-top: 1px solid {border_color}; margin: 50px 0;'>", unsafe_allow_html=True)















































































































































































































































































































































