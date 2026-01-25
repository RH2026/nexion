import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

if st.session_state.tema == "oscuro":
    bg_color, card_bg, text_main, text_sub, border_color, btn_hover = "#05070A", "#0D1117", "#F0F6FC", "#8B949E", "#1B1F24", "#161B22"
else:
    bg_color, card_bg, text_main, text_sub, border_color, btn_hover = "#F5F7FA", "#FFFFFF", "#1A1C1E", "#656D76", "#D8DEE4", "#EBEEF2"

# 3. CSS DINÁMICO REFINADO
st.markdown(f"""
    <style>
        header, footer, #MainMenu, div[data-testid="stDecoration"] {{visibility: hidden;}}
        .stApp {{ background-color: {bg_color} !important; color: {text_main} !important; transition: all 0.5s ease; }}
        
        div.stButton > button {{
            background-color: {card_bg} !important; color: {text_main} !important;
            border: 1px solid {border_color} !important; border-radius: 2px !important;
            font-size: 11px !important; font-weight: 600 !important; letter-spacing: 2px !important;
            text-transform: uppercase; height: 42px; transition: all 0.3s ease;
        }}
        div.stButton > button:hover {{ background-color: {btn_hover} !important; border-color: {text_main} !important; }}
        
        .stTextInput input {{
            background-color: {card_bg} !important; color: {text_main} !important;
            border: 1px solid {border_color} !important; border-radius: 2px !important; height: 48px !important;
        }}
        div.stButton > button[kind="primary"] {{ 
            background-color: {text_main} !important; color: {bg_color} !important; 
            border: none !important; font-weight: 700 !important; 
        }}
    </style>
""", unsafe_allow_html=True)

# 4. HEADER PERSISTENTE
c_logo, c_nav, c_theme = st.columns([1.5, 4, 0.5])
with c_logo:
    st.markdown(f"<h2 style='color: {text_main}; font-weight: 200; letter-spacing: 4px; margin: 0;'>NEXION</h2><p style='color: {text_sub}; font-size: 9px; margin-top: -5px; letter-spacing: 1px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)

with c_nav:
    m = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "ESTATUS"]):
        with m[i]:
            if st.button(b, use_container_width=True):
                st.session_state.pagina = b
                st.rerun()

with c_theme:
    if st.button("☀️" if st.session_state.tema == "oscuro" else "🌙"):
        st.session_state.tema = "claro" if st.session_state.tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border:0; border-top:1px solid {border_color}; margin:10px 0 30px 0;'>", unsafe_allow_html=True)

# 5. LÓGICA DE SPLASH (Cubre solo el área de contenido)
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    splash_zone = st.empty()
    with splash_zone.container():
        for msg in ["ESTABLISHING SECURE CONNECTION", "SYNCING MANIFESTS", "SYSTEM ONLINE"]:
            st.markdown(f'<div style="height:50vh; display:flex; flex-direction:column; justify-content:center; align-items:center;"><div style="width:30px; height:30px; border:1px solid {border_color}; border-top:1px solid {text_main}; border-radius:50%; animation:spin 0.8s linear infinite;"></div><p style="color:{text_main}; font-family:monospace; font-size:10px; letter-spacing:5px; margin-top:40px;">{msg}</p></div><style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>', unsafe_allow_html=True)
            time.sleep(0.8)
    st.session_state.splash_completado = True
    st.rerun()

# 6. MOTOR DE DATOS
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("Matriz_Excel_Dashboard.csv", encoding="utf-8")
        df.columns = df.columns.str.strip().str.upper()
        df["NO CLIENTE"] = df["NO CLIENTE"].astype(str).str.strip()
        columnas_fecha = ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
        hoy = pd.Timestamp.today().normalize()
        df["ESTATUS_CALCULADO"] = df.apply(lambda r: "ENTREGADO" if pd.notna(r["FECHA DE ENTREGA REAL"]) else ("RETRASADO" if pd.notna(r["PROMESA DE ENTREGA"]) and r["PROMESA DE ENTREGA"] < hoy else "EN TRANSITO"), axis=1)
        return df
    except:
        return pd.DataFrame(columns=["NO CLIENTE", "FLETERA", "DESTINO", "ESTATUS_CALCULADO"])

df = cargar_datos()

# 7. RENDERIZADO DE CONTENIDO (RASTREO)
if st.session_state.get("pagina", "RASTREO") == "RASTREO":
    _, col_search, _ = st.columns([1, 1.6, 1])
    with col_search:
        st.markdown(f"<p style='text-align: center; color: {text_sub}; font-size: 11px; letter-spacing: 3px; text-transform: uppercase;'>Operational Query</p>", unsafe_allow_html=True)
        busqueda = st.text_input("", placeholder="Referencia o Guía...", label_visibility="collapsed")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        btn_search = st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True)

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

    # Filtrado y Tabla
    df_visual = df.copy()
    if busqueda and btn_search:
        mask = df_visual.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_visual = df_visual[mask]

    # Selectores Premium
    f1, f2, f3, f4 = st.columns(4)
    with f1: f_cli = st.selectbox("Client ID", options=["ALL"] + sorted(df_visual["NO CLIENTE"].unique().tolist()))
    with f2: f_car = st.selectbox("Carrier", options=["ALL"] + sorted(df_visual["FLETERA"].unique().tolist()))
    with f3: f_des = st.selectbox("Destination", options=["ALL"] + sorted(df_visual["DESTINO"].unique().tolist()))
    with f4: f_est = st.selectbox("Status", options=["ALL"] + sorted(df_visual["ESTATUS_CALCULADO"].unique().tolist()))

    if f_cli != "ALL": df_visual = df_visual[df_visual["NO CLIENTE"] == f_cli]
    if f_car != "ALL": df_visual = df_visual[df_visual["FLETERA"] == f_car]
    if f_des != "ALL": df_visual = df_visual[df_visual["DESTINO"] == f_des]
    if f_est != "ALL": df_visual = df_visual[df_visual["ESTATUS_CALCULADO"] == f_est]

    st.dataframe(df_visual, use_container_width=True, hide_index=True, height=450)

















































































































































































































































































































































