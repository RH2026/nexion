import streamlit as st
import pandas as pd
from datetime import datetime
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


# --- 1. CONFIGURACIÓN DE CRÉDENCIALES Y REPO ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "tareas.csv"
CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/tareas.csv"

# --- 2. UTILIDADES ---
def obtener_fecha_mexico():
    utc_ahora = datetime.datetime.now(datetime.timezone.utc)
    return (utc_ahora - datetime.timedelta(hours=6)).date()

def cargar_datos_seguro():
    try:
        response = requests.get(CSV_URL)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            df.columns = [c.strip().upper() for c in df.columns]
            
            # Forzar conversión de fechas para evitar errores en st.data_editor
            for col in ['FECHA', 'FECHA_FIN']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
                else:
                    df[col] = obtener_fecha_mexico()
            
            # Limpiar nulos
            df['FECHA'] = df['FECHA'].fillna(obtener_fecha_mexico())
            df['FECHA_FIN'] = df['FECHA_FIN'].fillna(obtener_fecha_mexico())
            df['IMPORTANCIA'] = df['IMPORTANCIA'].fillna("Media")
            return df
        return pd.DataFrame(columns=['FECHA', 'FECHA_FIN', 'IMPORTANCIA', 'TAREA', 'ULTIMO ACCION'])
    except Exception:
        return pd.DataFrame(columns=['FECHA', 'FECHA_FIN', 'IMPORTANCIA', 'TAREA', 'ULTIMO ACCION'])

def guardar_en_github(df):
    if not TOKEN:
        st.error("No se encontró GITHUB_TOKEN en st.secrets")
        return
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(FILE_PATH, ref="main")
        # Convertir fechas a string para el CSV
        df_save = df.copy()
        df_save['FECHA'] = df_save['FECHA'].astype(str)
        df_save['FECHA_FIN'] = df_save['FECHA_FIN'].astype(str)
        
        repo.update_file(
            path=contents.path,
            message=f"Sincronización NEXION - {obtener_fecha_mexico()}",
            content=df_save.to_csv(index=False),
            sha=contents.sha,
            branch="main"
        )
        st.toast("✅ Sincronizado con GitHub", icon="🚀")
    except Exception as e:
        st.error(f"❌ Error al sincronizar: {e}")

# --- 3. INICIALIZACIÓN DE ESTADO ---
if 'df_tareas' not in st.session_state:
    st.session_state.df_tareas = cargar_datos_seguro()

# --- 4. VISUALIZACIÓN GANTT (ALTA CALIDAD) ---
st.markdown(f"<h1 style='text-align: center; font-weight: 300; letter-spacing: 12px; font-size: 20px; color: {v['text']};'>NEXION PROJECT FLOW</h1>", unsafe_allow_html=True)
st.markdown(f"<hr style='border-top:1px solid {v['border']}; margin:10px 0 30px;'>", unsafe_allow_html=True)

if not st.session_state.df_tareas.empty:
    # Preparar DF para Plotly
    df_plot = st.session_state.df_tareas.copy()
    df_plot = df_plot.rename(columns={'TAREA': 'Task', 'FECHA': 'Start', 'FECHA_FIN': 'Finish', 'IMPORTANCIA': 'Resource'})
    
    # Colores temáticos NEXION
    colors = {'Urgente': '#FF3131', 'Alta': '#FF914D', 'Media': '#00D2FF', 'Baja': '#444E5E'}

    try:
        # Generar Gantt Base
        fig = ff.create_gantt(
            df_plot, colors=colors, index_col='Resource', 
            show_colorbar=True, group_tasks=True, showgrid_x=True, showgrid_y=True
        )

        # Inyectar Estilo Premium con Graph Objects
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=v['text'], family="Inter", size=12),
            height=400,
            margin=dict(l=150, r=20, t=20, b=50),
            xaxis=dict(gridcolor=v['border'], linecolor=v['border'], tickformat="%d %b"),
            yaxis=dict(gridcolor=v['border'], linecolor=v['border'], autorange="reversed"),
        )
        
        # Añadir Hitos (diamantes blancos al final de cada barra)
        for i, row in df_plot.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['Finish']], y=[len(df_plot) - 1 - i],
                mode='markers', marker=dict(symbol='diamond', size=8, color='white'),
                showlegend=False, hoverinfo='skip'
            ))

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except Exception as e:
        st.warning("Agregue datos válidos en la tabla para generar el gráfico.")

# --- 5. EDITOR MAESTRO (INTEGRADO) ---
st.markdown(f"<div style='margin-top:20px; margin-bottom:10px;'><p style='font-size:11px; color:{v['sub']}; letter-spacing:2px; text-transform:uppercase;'>Consola de Edición en Tiempo Real</p></div>", unsafe_allow_html=True)

with st.container(border=True):
    # Asegurar que el dataframe que entra al editor tenga fechas reales de Python
    df_para_editar = st.session_state.df_tareas.copy()
    df_para_editar['FECHA'] = pd.to_datetime(df_para_editar['FECHA']).dt.date
    df_para_editar['FECHA_FIN'] = pd.to_datetime(df_para_editar['FECHA_FIN']).dt.date

    edited_df = st.data_editor(
        df_para_editar,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_maestro",
        column_config={
            "FECHA": st.column_config.DateColumn("📆 Inicio", format="DD/MM/YYYY", required=True),
            "FECHA_FIN": st.column_config.DateColumn("🏁 Fin", format="DD/MM/YYYY", required=True),
            "IMPORTANCIA": st.column_config.SelectboxColumn("🚦 Prioridad", options=["Baja", "Media", "Alta", "Urgente"], required=True),
            "TAREA": st.column_config.TextColumn("📝 Tarea", width="large"),
            "ULTIMO ACCION": st.column_config.TextColumn("🚚 Estatus", width="medium"),
        },
        hide_index=True,
    )

    # Botonera de Acciones
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("💾 GUARDAR Y SINCRONIZAR GITHUB", use_container_width=True, type="primary"):
            st.session_state.df_tareas = edited_df
            guardar_en_github(edited_df)
            st.rerun()
    with col_btn2:
        if st.button("🔄 RECARGAR DESDE NUBE", use_container_width=True):
            st.session_state.df_tareas = cargar_datos_seguro()
            st.rerun()





