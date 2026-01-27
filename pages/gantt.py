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


# --- DATOS DE PRUEBA (Estructura para Grupos, Progreso e Hitos) ---
df_gantt = [
    # INITIATION
    dict(Task="Requirements", Start='2026-03-01', Finish='2026-03-05', Resource='INITIATION', Complete=100),
    dict(Task="Stakeholder Workshop", Start='2026-03-04', Finish='2026-03-08', Resource='INITIATION', Complete=70),
    dict(Task="Initiation Complete", Start='2026-03-08', Finish='2026-03-08', Resource='INITIATION', Complete=100), # Hito
    
    # DESIGN
    dict(Task="E2E Solution Design", Start='2026-03-07', Finish='2026-03-18', Resource='DESIGN', Complete=45),
    dict(Task="Wireframes", Start='2026-03-12', Finish='2026-03-16', Resource='DESIGN', Complete=80),
    
    # IMPLEMENTATION
    dict(Task="ETL Development", Start='2026-03-15', Finish='2026-03-25', Resource='IMPLEMENTATION', Complete=20),
]

# Colores basados en tu tema Ónix + Acentos
colors = {
    'INITIATION': '#3A86FF',   # Azul corporativo
    'DESIGN': '#00F5D4',       # Verde neón/menta
    'IMPLEMENTATION': '#BE95FF' # Púrpura suave
}

# --- GENERACIÓN DEL GANTT ---
def generar_gantt_pro(df_list, color_map, text_color, bg_color, border_color):
    # Crear el objeto base
    fig = ff.create_gantt(
        df_list, 
        colors=color_map, 
        index_col='Resource', 
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True, 
        showgrid_y=True
    )

    # Inyectar Barras de Progreso (Overlay)
    for i in range(len(df_list)):
        task = df_list[i]
        # Si es un hito (Duración 0), dibujamos un diamante
        if task['Start'] == task['Finish']:
            fig.add_trace(go.Scatter(
                x=[task['Start']],
                y=[len(df_list) - 1 - i],
                mode='markers',
                marker=dict(symbol='diamond', size=12, color=color_map[task['Resource']]),
                name="Milestone",
                showlegend=False
            ))
        # Si tiene progreso, añadimos una sub-barra más oscura
        elif task['Complete'] > 0:
            progreso = task['Complete'] / 100
            # Cálculo simple de fecha de corte para el progreso
            # (En producción se usaría timedelta para precisión exacta)
            fig.add_trace(go.Scatter(
                x=[task['Start'], task['Start']], # Lógica simplificada para visual
                y=[len(df_list) - 1 - i, len(df_list) - 1 - i],
                mode='lines',
                line=dict(width=15, color='rgba(255,255,255,0.3)'),
                showlegend=False
            ))

    # Estilización estética NEXION
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=text_color, family="Inter", size=11),
        xaxis=dict(gridcolor=border_color, zeroline=False),
        yaxis=dict(gridcolor=border_color, zeroline=False),
        margin=dict(l=150, r=20, t=40, b=20), # Espacio para nombres de tareas
        height=450,
        hovermode='closest'
    )
    
    return fig

# --- RENDERIZADO EN STREAMLIT ---
# Usando las variables 'v' de tu script original
gantt_fig = generar_gantt_pro(df_gantt, colors, v["text"], v["bg"], v["border"])
st.plotly_chart(gantt_fig, use_container_width=True, config={'displayModeBar': False})



