import streamlit as st
import pandas as pd
from datetime import datetime
import os
import streamlit.components.v1 as components
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


import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# URL de tu repositorio
GITHUB_URL = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/tareas.csv"

@st.cache_data(ttl=60) # Actualiza cada minuto
def load_nexion_tasks(url):
    try:
        df = pd.read_csv(url, encoding='utf-8')
        # Limpiar espacios en nombres de columnas
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Convertir fechas
        df['FECHA'] = pd.to_datetime(df['FECHA'])
        
        # Lógica para FECHA FIN: si no existe en el CSV, sumamos 1 día para visualizar la barra
        if 'FECHA_FIN' in df.columns:
            df['FECHA_FIN'] = pd.to_datetime(df['FECHA_FIN'])
        else:
            df['FECHA_FIN'] = df['FECHA'] + pd.to_timedelta(1, unit='d')
            
        return df
    except Exception as e:
        st.error(f"Error cargando base de datos: {e}")
        return pd.DataFrame()

# 1. CARGAR DATOS
df_tareas = load_nexion_tasks(GITHUB_URL)

# 2. RENDERIZAR GANTT
if not df_tareas.empty:
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <p style='color:{v['sub']}; font-size:10px; letter-spacing:3px; text-transform:uppercase;'>Timeline Operativo</p>
        </div>
    """, unsafe_allow_html=True)

    # Definir colores según importancia (estilo Ónix)
    color_map = {
        "Urgente": "#FF4B4B", # Rojo
        "Alta": "#FFBD45",    # Naranja
        "Media": "#3A86FF",   # Azul
        "Baja": "#8B949E"     # Gris
    }

    fig = px.timeline(
        df_tareas, 
        x_start="FECHA", 
        x_end="FECHA_FIN", 
        y="TAREA", 
        color="IMPORTANCIA",
        color_discrete_map=color_map,
        hover_data={"ULTIMO ACCION": True, "FECHA": "|%d %b", "FECHA_FIN": "|%d %b", "IMPORTANCIA": True}
    )

    # Invertir eje Y para ver lo más reciente arriba
    fig.update_yaxes(autorange="reversed")

    # Diseño Onix Dark
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color=v["text"],
        xaxis=dict(
            gridcolor=v["border"],
            tickfont=dict(size=10, color=v["sub"]),
            title=""
        ),
        yaxis=dict(
            gridcolor=v["border"],
            tickfont=dict(size=10),
            title=""
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Mostrar en Streamlit
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Mostrar la tabla detallada debajo
    with st.expander("VER DETALLE DE ACCIONES"):
        st.dataframe(
            df_tareas[['FECHA', 'IMPORTANCIA', 'TAREA', 'ULTIMO ACCION']], 
            use_container_width=True,
            hide_index=True
        )



