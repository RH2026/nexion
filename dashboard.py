import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core Intelligence", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

if st.session_state.tema == "oscuro":
    bg_color, card_bg, text_main, text_sub, border_color, btn_hover = "#05070A", "#0D1117", "#F0F6FC", "#8B949E", "#1B1F24", "#161B22"
else:
    bg_color, card_bg, text_main, text_sub, border_color, btn_hover = "#F5F7FA", "#FFFFFF", "#1A1C1E", "#656D76", "#D8DEE4", "#EBEEF2"

# 3. CSS DINÁMICO (Zara & DHL Logic)
st.markdown(f"""
    <style>
        header, footer, #MainMenu, div[data-testid="stDecoration"] {{visibility: hidden;}}
        .stApp {{ background-color: {bg_color} !important; color: {text_main} !important; transition: all 0.5s ease; }}
        
        /* Botones de Navegación */
        div.stButton > button {{
            background-color: {card_bg} !important; color: {text_main} !important;
            border: 1px solid {border_color} !important; border-radius: 2px !important;
            font-size: 11px !important; font-weight: 600 !important; letter-spacing: 2px !important;
            text-transform: uppercase; height: 42px; transition: all 0.3s ease;
        }}
        div.stButton > button:hover {{ background-color: {btn_hover} !important; border-color: {text_main} !important; }}
        
        /* Inputs y Selectores */
        .stTextInput input, div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            background-color: {card_bg} !important; color: {text_main} !important;
            border: 1px solid {border_color} !important; border-radius: 2px !important;
        }}
        div.stButton > button[kind="primary"] {{ background-color: {text_main} !important; color: {bg_color} !important; border: none !important; }}
    </style>
""", unsafe_allow_html=True)

# 4. HEADER SIEMPRE VISIBLE (Logo, Menú y Tema)
c_logo, c_nav, c_theme = st.columns([1.5, 4, 0.5])
with c_logo:
    st.markdown(f"<h2 style='color: {text_main}; font-weight: 200; letter-spacing: 4px; margin: 0;'>NEXION</h2><p style='color: {text_sub}; font-size: 9px; margin-top: -5px; letter-spacing: 1px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)

with c_nav:
    m = st.columns(4)
    paginas = ["RASTREO", "INTELIGENCIA", "REPORTES", "ESTATUS"]
    for i, b in enumerate(paginas):
        with m[i]:
            if st.button(b, use_container_width=True):
                st.session_state.pagina = b
                st.rerun()

with c_theme:
    if st.button("☀️" if st.session_state.tema == "oscuro" else "🌙"):
        st.session_state.tema = "claro" if st.session_state.tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border:0; border-top:1px solid {border_color}; margin:10px 0 30px 0;'>", unsafe_allow_html=True)

# --- ESPACIO PARA EL CONTENIDO DINÁMICO ---
contenido_principal = st.empty()

# 5. LÓGICA DE SPLASH (Solo dentro del contenedor central)
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    with contenido_principal.container():
        mensajes = ["ESTABLISHING CONNECTION", "SYNCING MANIFESTS", "SYSTEM ONLINE"]
        for m in mensajes:
            st.markdown(f'<div style="height:50vh; display:flex; flex-direction:column; justify-content:center; align-items:center;"><div style="width:30px; height:30px; border:1px solid {border_color}; border-top:1px solid {text_main}; border-radius:50%; animation:spin 1s linear infinite;"></div><p style="color:{text_main}; font-family:monospace; font-size:10px; letter-spacing:5px; margin-top:40px;">{m}</p></div><style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>', unsafe_allow_html=True)
            time.sleep(0.8)
    st.session_state.splash_completado = True
    st.rerun()

# 6. MOTOR DE DATOS (Se carga en silencio después del Splash)
@st.cache_data
def cargar_datos():
    df = pd.read_csv("Matriz_Excel_Dashboard.csv", encoding="utf-8")
    df.columns = df.columns.str.strip().str.upper()
    df["NO CLIENTE"] = df["NO CLIENTE"].astype(str).str.strip()
    df["FECHA DE ENVÍO"] = pd.to_datetime(df["FECHA DE ENVÍO"], errors="coerce", dayfirst=True)
    df["PROMESA DE ENTREGA"] = pd.to_datetime(df["PROMESA DE ENTREGA"], errors="coerce", dayfirst=True)
    df["FECHA DE ENTREGA REAL"] = pd.to_datetime(df["FECHA DE ENTREGA REAL"], errors="coerce", dayfirst=True)
    hoy = pd.Timestamp.today().normalize()
    def calcular_estatus(row):
        if pd.notna(row["FECHA DE ENTREGA REAL"]): return "ENTREGADO"
        if pd.notna(row["PROMESA DE ENTREGA"]) and row["PROMESA DE ENTREGA"] < hoy: return "RETRASADO"
        return "EN TRANSITO"
    df["ESTATUS_CALCULADO"] = df.apply(calcular_estatus, axis=1)
    return df

df = cargar_datos()

# 7. RENDERIZADO DEL DASHBOARD
with contenido_principal.container():
    # Buscador Central
    _, col_search, _ = st.columns([1, 1.6, 1])
    with col_search:
        st.markdown(f"<p style='text-align: center; color: {text_sub}; font-size: 11px; letter-spacing: 3px; text-transform: uppercase;'>Operational Query</p>", unsafe_allow_html=True)
        busqueda = st.text_input("", placeholder="Referencia o Guía...", label_visibility="collapsed")

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
















































































































































































































































































































































