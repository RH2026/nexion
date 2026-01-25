import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA PRO
st.set_page_config(
    page_title="NEXION | Portal Logístico", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. GESTIÓN DE TEMA Y PALETA PROFESIONAL
if "tema" not in st.session_state:
    st.session_state.tema = "claro" # DHL/FedEx suelen ser claros por defecto

if st.session_state.tema == "oscuro":
    # Paleta Dark Pro (Inspirada en dashboards de alta gama)
    bg_color = "#121212"
    nav_bg = "#1E1E1E"
    text_color = "#FFFFFF"
    accent_color = "#00FF00"  # Verde Neón para resaltar
    card_bg = "#1E1E1E"
    border = "1px solid #333333"
else:
    # Paleta Light Pro (Inspirada en DHL/FedEx)
    bg_color = "#F8F9FA"
    nav_bg = "#FFFFFF"
    text_color = "#1A1A1A"
    accent_color = "#D40511"  # Rojo DHL (o usa #FF6B00 para FedEx)
    card_bg = "#FFFFFF"
    border = "1px solid #E0E0E0"

# 3. CSS DE ALTO NIVEL (UI/UX)
st.markdown(f"""
    <style>
        /* Reset y Fondos */
        .stApp {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
            font-family: 'Inter', sans-serif;
        }}
        
        /* Ocultar elementos basura */
        header, footer, #MainMenu {{visibility: hidden;}}

        /* Navbar Superior Pro */
        .main-nav {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.8rem 3rem;
            background-color: {nav_bg};
            border-bottom: {border};
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 999;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        /* Tarjetas de Contenido */
        .portal-card {{
            background-color: {card_bg};
            padding: 2rem;
            border-radius: 12px;
            border: {border};
            box-shadow: 0 4px 20px rgba(0,0,0,0.03);
            margin-bottom: 1.5rem;
        }}

        /* Botones Estilo DHL */
        div.stButton > button {{
            border-radius: 4px !important;
            padding: 0.5rem 2rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            transition: all 0.3s ease !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 4. NAVBAR SUPERIOR (HTML Personalizado)
# Usamos columnas para que los botones de Streamlit vivan dentro del diseño
cols = st.columns([2, 1, 1, 1, 1, 1])

with cols[0]:
    st.markdown(f"<h2 style='margin:0; color:{accent_color}; font-weight:900;'>NEXION</h2>", unsafe_allow_html=True)

# Botones de Navegación
if "pagina" not in st.session_state: st.session_state.pagina = "INICIO"

with cols[1]:
    if st.button("RASTREO", use_container_width=True): st.session_state.pagina = "RASTREO"
with cols[2]:
    if st.button("KPIs", use_container_width=True): st.session_state.pagina = "KPIs"
with cols[3]:
    if st.button("REPORTES", use_container_width=True): st.session_state.pagina = "REPORTES"
with cols[4]:
    # Botón de Cambio de Tema (🌓)
    if st.button("🌓", use_container_width=True):
        st.session_state.tema = "oscuro" if st.session_state.tema == "claro" else "claro"
        st.rerun()

st.markdown("<br><br>", unsafe_allow_html=True)

# 5. SPLASH SCREEN (Animación DHL Style)
if "splash" not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
            <div style="height: 80vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div style="width: 100px; height: 5px; background: {accent_color}; animation: loading 1.5s infinite;"></div>
                <h1 style="color: {text_color}; font-weight: 200; letter-spacing: 5px; margin-top: 20px;">SINCRO NEXION</h1>
            </div>
            <style>
                @keyframes loading {{
                    0% {{ width: 0; }}
                    50% {{ width: 100%; }}
                    100% {{ width: 0; }}
                }}
            </style>
        """, unsafe_allow_html=True)
        time.sleep(1.8)
    st.session_state.splash = True
    st.rerun()

# 6. CONTENIDO DE LA PÁGINA
st.markdown(f"### {st.session_state.pagina}")
st.markdown("---")









































































































































































































































































































































