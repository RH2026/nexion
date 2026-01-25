import streamlit as st
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION LOGISTICS", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA
if "tema" not in st.session_state:
    st.session_state.tema = "claro"

# Definición de paletas ( DHL: Amarillo/Rojo | Dark: Antracita/Verde )
if st.session_state.tema == "oscuro":
    bg_app = "#121212"
    bg_nav = "#1B1C1F"
    text_main = "#FFFFFF"
    accent = "#00FF00" 
    btn_bg = "#262730"
    border_color = "#333333"
else:
    bg_app = "#F8F9FA"  # Gris ultra claro tipo FedEx/DHL
    bg_nav = "#FFCC00"  # Amarillo DHL (puedes cambiarlo a blanco si prefieres)
    text_main = "#1A1A1A"
    accent = "#D40511"  # Rojo DHL
    btn_bg = "#FFFFFF"
    border_color = "#E0E0E0"

# 3. CSS MAESTRO PARA BOTONES Y NAVBAR
st.markdown(f"""
    <style>
        /* Fondo de la App */
        .stApp {{
            background-color: {bg_app} !important;
            color: {text_main} !important;
        }}

        /* Ocultar basura de Streamlit */
        header, footer, #MainMenu, div[data-testid="stDecoration"] {{visibility: hidden;}}

        /* --- ESTILO DE BOTONES DE NAVEGACIÓN --- */
        /* Forzamos que no sean negros */
        div.stButton > button {{
            background-color: {btn_bg} !important;
            color: {text_main} !important;
            border: 1px solid {border_color} !important;
            border-radius: 2px !important; /* DHL usa bordes muy rectos */
            padding: 0.6rem 1rem !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        div.stButton > button:hover {{
            border-color: {accent} !important;
            color: {accent} !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}

        /* Estilo para el buscador central tipo DHL */
        .stTextInput input {{
            border-radius: 0px !important;
            border: 2px solid {border_color} !important;
            height: 50px !important;
            font-size: 18px !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 4. NAVBAR SUPERIOR (Layout de Portal)
# Creamos una franja de color en la parte superior si es modo claro (estilo DHL)
if st.session_state.tema == "claro":
    st.markdown(f'<div style="background-color:{bg_nav}; height:5px; width:100%; position:fixed; top:0; left:0; z-index:1000;"></div>', unsafe_allow_html=True)

c_logo, c_nav1, c_nav2, c_nav3, c_nav4 = st.columns([2, 1, 1, 1, 1])

with c_logo:
    st.markdown(f"<h1 style='margin:0; color:{accent}; font-weight:900; font-size:35px;'>NEXION</h1>", unsafe_allow_html=True)

with c_nav1:
    if st.button("RASTREO", use_container_width=True):
        st.session_state.pagina = "principal"
with c_nav2:
    if st.button("KPIs", use_container_width=True):
        st.session_state.pagina = "KPIs"
with c_nav3:
    if st.button("REPORTES", use_container_width=True):
        st.session_state.pagina = "Reporte"
with c_nav4:
    # Botón de cambio de tema con icono adaptativo
    label_tema = "🌙 MODO OSCURO" if st.session_state.tema == "claro" else "☀️ MODO CLARO"
    if st.button(label_tema, use_container_width=True):
        st.session_state.tema = "oscuro" if st.session_state.tema == "claro" else "claro"
        st.rerun()

st.markdown("<hr style='margin-top:0; border-color:rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

# 5. BUSCADOR CENTRAL (DHL STYLE)
st.markdown("<br><br>", unsafe_allow_html=True)
_, col_mid, _ = st.columns([1, 2, 1])

with col_mid:
    st.markdown(f"<h2 style='text-align:center; font-weight:800;'>Rastrear su envío</h2>", unsafe_allow_html=True)
    num_guia = st.text_input("", placeholder="Ingrese número de rastreo (ej: NX-2026...)", label_visibility="collapsed")
    
    # Botón de acción principal (Rojo DHL)
    st.markdown(f"""
        <style>
        div[data-testid="stVerticalBlock"] > div:last-child button {{
            background-color: {accent} !important;
            color: white !important;
            border: none !important;
            width: 100% !important;
            height: 50px !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    if st.button("RASTREAR"):
        st.success(f"Buscando guía: {num_guia}")









































































































































































































































































































































