import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
from github import Github
import plotly.figure_factory as ff
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Automatizacion de Procesos", layout="wide", initial_sidebar_state="collapsed")

# ── 2. TEMA DINÁMICO ────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema

if tema == "oscuro":
    v = {
        "bg": "#05070A", 
        "card": "#0D1117", 
        "text": "#F0F6FC", 
        "sub": "#8B949E", 
        "border": "#1B1F24"
    }
else:
    v = {
        "bg": "#E9ECF1", 
        "card": "#FFFFFF", 
        "text": "#111111", 
        "sub": "#2D3136", 
        "border": "#C9D1D9"
    }

# ── 3. CSS MAESTRO (ALINEACIÓN DE LOGO Y UNIFICACIÓN TOTAL) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* 1. LIMPIEZA Y OCULTAR ELEMENTOS NATIVOS */
header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"] {{ 
    display:none !important; 
}}

.block-container {{ 
    padding-top: 1rem !important; 
    padding-bottom: 0rem !important;
}}

/* 2. FONDO Y TEXTO GLOBAL */
.stApp {{ 
    background: {v["bg"]} !important; 
    color: {v["text"]} !important; 
    font-family: 'Inter', sans-serif !important; 
}}

/* 3. ARREGLO DE ALINEACIÓN LOGO Y SUBTÍTULO */
div[data-testid="stImage"] {{
    text-align: left !important;
    width: fit-content !important;
}}

div[data-testid="stImage"] img {{ 
    image-rendering: -webkit-optimize-contrast !important; 
    transform: translateZ(0);
    margin-left: 0 !important;
}}

.stMarkdown p {{
    margin-left: 0 !important;
    text-align: left !important;
}}

/* 4. TÍTULOS DE CAMPOS */
[data-testid="stWidgetLabel"] p {{
    color: {v["text"]} !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    text-align: left !important;
}}

/* 5. UNIFICACIÓN DE CAJAS (ELIMINA BORDES DOBLES Y GROSORES) */
/* Aplicamos el borde base a los contenedores de los tres tipos de widget */
div[data-baseweb="input"], 
div[data-baseweb="select"] > div,
div[data-testid="stDateInput"] > div[data-baseweb="input"] {{
    background-color: {v["card"]} !important;
    border: 1px solid {v["border"]} !important; 
    border-radius: 4px !important;
    min-height: 42px !important;
    box-shadow: none !important; /* Quita el efecto de sombra/bisel */
}}

/* Eliminamos el borde de los elementos internos para que no se sumen */
.stTextInput input, .stDateInput input, div[data-baseweb="base-input"] {{
    border: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
    color: {v["text"]} !important;
    height: 40px !important;
}}

/* Aseguramos que el texto del Selectbox sea visible en ambos temas */
div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    color: {v["text"]} !important;
    padding-left: 10px !important;
}}

/* Quitamos el borde azul/rojo molesto al hacer clic (opcional, para estética limpia) */
div[data-baseweb="input"]:focus-within, 
div[data-baseweb="select"] > div:focus-within {{
    border-color: {v["text"]} !important; /* El borde se ilumina con el color del texto actual */
}}

/* 6. BOTONES CON HOVER INVERTIDO */
div.stButton>button {{
    background: {v["card"]} !important; 
    color: {v["text"]} !important;
    border: 1px solid {v["border"]} !important;
    border-radius: 4px !important;
    width: 100%;
    transition: all .3s ease;
    height: 42px !important;
}}

div.stButton>button:hover {{
    background: {v["text"]} !important;
    color: {v["bg"]} !important;
    border-color: {v["text"]} !important;
}}

</style>
""", unsafe_allow_html=True)

# ── 4. HEADER Y NAVEGACIÓN (Título Visual Actualizado) ───
c1, c2, c3 = st.columns([2, 3.5, .5], vertical_alignment="top")
with c1:
    logo = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo, width=140)
        # Actualización de subtítulo visual
        st.markdown(f"<div style='margin-top:-15px;'><p style='font-size:9px; color:{v['sub']}; letter-spacing:1px; text-transform:uppercase;'>Automatización de Procesos</p></div>", unsafe_allow_html=True)
    except: 
        st.markdown(f"<h2 style='color:{v['text']}; margin:0;'>NEXION</h2>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        if cols[i].button(b, key=f"nav_{b}", use_container_width=True):
            if b != "FORMATOS": st.switch_page("dashboard.py")
            else: st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="t_btn"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"; st.rerun()

st.markdown(f"<hr style='border-top:1px solid {v['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. TÍTULO MINIMALISTA (ZARA / DHL STYLE) ──────────
st.markdown(f"""
    <div style="text-align: center; margin-top: 10px; margin-bottom: 25px;">
        <h1 style="font-weight: 300; letter-spacing: 12px; text-transform: uppercase; font-size: 15px; color: {v['text']}; opacity: 0.9;">
            D I A G R A M A &nbsp; D E &nbsp; G A N T T&nbsp; 
        </h1>
    </div>
""", unsafe_allow_html=True)

# --- 1. CONFIGURACIÓN ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "tareas.csv"
CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/tareas.csv"

# --- 2. FUNCIONES DE APOYO ---
def obtener_fecha_mexico():
    utc_ahora = datetime.datetime.now(datetime.timezone.utc)
    return (utc_ahora - datetime.timedelta(hours=6)).date()

def cargar_datos_seguro():
    columnas_base = ['FECHA', 'FECHA_FIN', 'IMPORTANCIA', 'TAREA', 'ULTIMO ACCION']
    hoy_local = obtener_fecha_mexico()
    try:
        response = requests.get(CSV_URL)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            df.columns = [c.strip().upper() for c in df.columns]
            
            for col in columnas_base:
                if col not in df.columns:
                    df[col] = ""
            
            for col in ['FECHA', 'FECHA_FIN']:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
                # Usamos hoy_local definido arriba
                df[col] = df[col].apply(lambda x: x if isinstance(x, datetime.date) else hoy_local)
            
            df['IMPORTANCIA'] = df['IMPORTANCIA'].astype(str).replace('nan', 'Media')
            df['TAREA'] = df['TAREA'].astype(str).replace('nan', '')
            df['ULTIMO ACCION'] = df['ULTIMO ACCION'].astype(str).replace('nan', '')
            
            return df[columnas_base]
        return pd.DataFrame(columns=columnas_base)
    except Exception:
        return pd.DataFrame(columns=columnas_base)

def guardar_en_github(df):
    if not TOKEN:
        st.error("No se encontró el GITHUB_TOKEN"); return False
    try:
        # Definimos hoy aquí para evitar el error 'name hoy is not defined'
        hoy_sync = obtener_fecha_mexico()
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        df_save = df.copy()
        df_save['FECHA'] = df_save['FECHA'].astype(str)
        df_save['FECHA_FIN'] = df_save['FECHA_FIN'].astype(str)
        
        csv_data = df_save.to_csv(index=False)
        contents = repo.get_contents(FILE_PATH, ref="main")
        repo.update_file(
            contents.path, 
            f"Actualización NEXION {hoy_sync}", 
            csv_data, 
            contents.sha, 
            branch="main"
        )
        st.toast("✅ Sincronizado con GitHub", icon="🚀")
        return True
    except Exception as e:
        st.error(f"Error GitHub: {e}"); return False

# --- 3. GESTIÓN DE ESTADO ---
if 'df_tareas' not in st.session_state:
    st.session_state.df_tareas = cargar_datos_seguro()

# --- 4. INTERFAZ VISUAL ---
if not st.session_state.df_tareas.empty:
    try:
        df_p = st.session_state.df_tareas.copy()
        df_p = df_p.rename(columns={'TAREA':'Task', 'FECHA':'Start', 'FECHA_FIN':'Finish', 'IMPORTANCIA':'Resource'})
        colors = {'Urgente': '#FF3131', 'Alta': '#FF914D', 'Media': '#00D2FF', 'Baja': '#444E5E'}
        
        fig = ff.create_gantt(df_p, colors=colors, index_col='Resource', group_tasks=True, showgrid_x=True, showgrid_y=True)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color=v['text']), height=350)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except:
        st.info("Ingresa fechas válidas para ver el gráfico.")

# --- 5. EDITOR MAESTRO ---
with st.container(border=True):
    df_input = st.session_state.df_tareas.copy()
    
    df_editado = st.data_editor(
        df_input,
        num_rows="dynamic",
        use_container_width=True,
        key="nexion_editor_v4", # Nueva key para refrescar cache
        column_config={
            "FECHA": st.column_config.DateColumn("📆 Inicio", required=True),
            "FECHA_FIN": st.column_config.DateColumn("🏁 Fin", required=True),
            "IMPORTANCIA": st.column_config.SelectboxColumn("🚦 Prioridad", options=["Baja", "Media", "Alta", "Urgente"]),
            "TAREA": st.column_config.TextColumn("📝 Tarea"),
            "ULTIMO ACCION": st.column_config.TextColumn("🚚 Estatus"),
        },
        hide_index=True
    )

    col1, col2 = st.columns(2)
    if col1.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
        st.session_state.df_tareas = df_editado
        if guardar_en_github(df_editado):
            st.rerun()

    if col2.button("🔄 RECARGAR", use_container_width=True):
        st.session_state.df_tareas = cargar_datos_seguro()
        st.rerun()












