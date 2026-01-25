import streamlit as st
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core Logistics", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA (SESIÓN)
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

if st.session_state.tema == "oscuro":
    bg_color, card_bg, text_main, text_sub, border_color, btn_hover = "#0A0C10", "#161B22", "#F0F6FC", "#8B949E", "#30363D", "#21262D"
else:
    bg_color, card_bg, text_main, text_sub, border_color, btn_hover = "#F6F8FA", "#FFFFFF", "#1F2328", "#656D76", "#D0D7DE", "#F3F4F6"

# 3. CSS DINÁMICO
st.markdown(f"""
    <style>
        header, footer, #MainMenu, div[data-testid="stDecoration"] {{visibility: hidden;}}
        .stApp {{ background-color: {bg_color} !important; color: {text_main} !important; transition: all 0.4s ease; }}
        
        div.stButton > button {{
            background-color: {card_bg} !important; color: {text_main} !important;
            border: 1px solid {border_color} !important; border-radius: 6px !important;
            font-size: 13px !important; font-weight: 500; letter-spacing: 0.5px; height: 40px; transition: all 0.2s ease;
        }}
        div.stButton > button:hover {{ background-color: {btn_hover} !important; border-color: {text_sub} !important; }}
        
        .stTextInput input {{
            background-color: {bg_color} !important; color: {text_main} !important;
            border: 1px solid {border_color} !important; border-radius: 6px !important; height: 45px !important;
        }}
        div.stButton > button[kind="primary"] {{ background-color: {text_main} !important; color: {bg_color} !important; border: none !important; font-weight: 700 !important; }}
    </style>
""", unsafe_allow_html=True)

# 4. LÓGICA DE SPLASH SCREEN
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    placeholder = st.empty()
    with placeholder.container():
        # Animación minimalista tipo terminal
        mensajes = ["ESTABLISHING SECURE CONNECTION...", "SYNCING NEXION DATABASE...", "SYSTEM READY"]
        for m in mensajes:
            st.markdown(f"""
                <div style="height: 80vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: {bg_color};">
                    <div style="width: 40px; height: 40px; border: 2px solid {border_color}; border-top: 2px solid {text_main}; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
                    <p style="color: {text_main}; font-family: monospace; font-size: 12px; letter-spacing: 3px; margin-top: 30px; font-weight: 200;">{m}</p>
                </div>
                <style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
            """, unsafe_allow_html=True)
            time.sleep(1.0)
    st.session_state.splash_completado = True
    st.rerun()

# 5. HEADER Y NAVEGACIÓN
c_logo, c_nav, c_theme = st.columns([1.5, 4, 0.5])
with c_logo:
    st.markdown(f"<h2 style='color: {text_main}; font-weight: 200; letter-spacing: 3px; margin: 0;'>NEXION</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: {text_sub}; font-size: 10px; margin-top: -5px;'>CORE LOGISTICS UNIT</p>", unsafe_allow_html=True)

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

st.markdown("<div style='margin-bottom: 50px;'></div>", unsafe_allow_html=True)

# 6. BUSCADOR CENTRAL
_, col_search, _ = st.columns([1, 1.8, 1])
with col_search:
    st.markdown(f"<h3 style='font-weight: 300; color: {text_sub}; text-align: center; font-size: 14px; letter-spacing: 2px;'>OPERATIONAL QUERY</h3>", unsafe_allow_html=True)
    guia = st.text_input("", placeholder="Referencia de envío...", label_visibility="collapsed")
    if st.button("EXECUTE SEARCH", type="primary", use_container_width=True):
        st.toast("Searching...", icon="🔍")
        st.session_state.busqueda = guia

st.markdown(f"<hr style='border: 0; border-top: 1px solid {border_color}; margin: 40px 0;'>", unsafe_allow_html=True)











































































































































































































































































































































