import base64
from datetime import datetime
import io
import re
import time
import unicodedata
import zipfile
import calendar
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import streamlit as st
import pytz

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Logistics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── TEMA Y CSS MAESTROS ──────────────────────────────────────────
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
    "logo": "n1.png",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(15px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

header, footer, [data-testid="stHeader"] {{
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}}

[data-testid="collapsedControl"], 
[data-testid="stSidebar"], 
[data-testid="stToolbar"], 
.viewerBadge_container__1QSob, 
#MainMenu, 
button[kind="header"] {{
    visibility: hidden !important;
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}

.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 5rem !important;
    background-color: {vars_css['bg']} !important;
}}

div.stButton > button, div.stDownloadButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 32px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {{
    gap: 0.45rem !important;
}}

div[data-testid="stPopoverBody"] .stButton {{
    margin-bottom: 0rem !important;
}}

.footer {{ 
    position: fixed; 
    bottom: 0 !important; 
    left: 0 !important; 
    width: 100% !important; 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['sub']} !important; 
    text-align: center; 
    padding: 12px 0px !important; 
    font-size: 9px; 
    letter-spacing: 2px; 
    border-top: 1px solid {vars_css['border']} !important; 
    z-index: 999999 !important; 
}}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. SISTEMA DE SEGURIDAD PRO
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/entregas_agc.py"
    st.switch_page("pages/log.py")

# ==========================================
# 3. FUNCIONES MAESTRAS DE DATOS
# ==========================================
@st.cache_data(ttl=60)
def cargar_datos_dashboard():
    t = int(time.time())
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
    try:
        df = pd.read_csv(url, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return None

if "menu_main" not in st.session_state:
    st.session_state.menu_main = "ENTREGAS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "AGC"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1

# ==========================================
# 4. HEADER LIMPIO
# ==========================================
header_zone = st.container()
with header_zone:
    c1, c2, c3, c4 = st.columns([1.5, 3.5, 0.9, 0.9], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=160)
        except:
            st.write("**NEXION**")

    with c2:
        st.markdown(
            f"""
            <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
                <p style='font-size: 13px; letter-spacing: 5px; color: {vars_css['sub']}; margin: 0; font-weight: 500; text-transform: uppercase; text-align: center;'>
                    NEXION <span style='color: #82D4E6; font-weight: 500; margin: 0 10px; font-size: 16px;'>|</span> SMART LOGISTICS
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with c3:
        pass

    with c4:
        with st.popover("☰ Menú", use_container_width=True):
            if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.autenticado = False
                st.session_state.splash_completado = False
                st.rerun()

# ==========================================
# 5. INTERFAZ PRINCIPAL (DONITAS + GRÁFICOS)
# ==========================================
def main():
    main_container = st.container()
    with main_container:
        def cargar_datos():
            t = int(time.time())
            url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
            try:
                df = pd.read_csv(url, encoding='utf-8-sig')
                df.columns = df.columns.str.strip()
                return df
            except Exception as e:
                st.error(f"Error al cargar datos: {e}")
                return None

        def render_kpi(valor, total, titulo, color):
            porc = (valor / total * 100) if total > 0 else 0
            circunferencia = 238.76
            offset = circunferencia - (porc / 100 * circunferencia)
            
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-title">{titulo}</div>
                    <div style="position: relative; width: 160px; height: 160px; display: flex; align-items: center; justify-content: center;">
                        <svg class="stat-circle" viewBox="0 0 100 100">
                            <circle class="stat-bg" cx="50" cy="50" r="38"></circle>
                            <circle class="stat-progress" cx="50" cy="50" r="38" 
                                    style="stroke: {color}; 
                                           stroke-dasharray: {circunferencia}; 
                                           stroke-dashoffset: {offset};">
                            </circle>
                        </svg>
                        <div class="stat-value">{valor}</div>
                    </div>
                    <div class="stat-percent" style="color: {color};">{porc:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <style>
            .stApp {{ background-color: {vars_css['bg']} !important; }}
            .metric-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                width: 100%;
            }}
            .metric-title {{ color: #94a3b8; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; font-weight: 600; }}
            .stat-circle {{ transform: rotate(-90deg); width: 160px; height: 160px; overflow: visible; }}
            .stat-circle circle {{ fill: none; stroke-width: 15; }}
            .stat-bg {{ stroke: #2F3E45; }}
            .stat-progress {{ transition: stroke-dashoffset 0.8s ease-in-out; stroke-linecap: butt; }}
            .stat-value {{ position: absolute; color: white; font-size: 22px; font-weight: 800; top: 50%; left: 50%; transform: translate(-50%, -50%); }}
            .stat-percent {{ font-size: 16px; margin-top: 5px; font-weight: 700; }}
        </style>
        """, unsafe_allow_html=True)

        df_raw = cargar_datos()
        
        if df_raw is not None:
            tz_gdl = pytz.timezone('America/Mexico_City')
            hoy_gdl = datetime.now(tz_gdl).date()
            hoy_dt = pd.Timestamp(hoy_gdl)
            meses = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO","JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]
            
            col_f1, _ = st.columns([1, 2])  
            with col_f1:
                mes_sel = st.selectbox("PERÍODO", meses, index=hoy_gdl.month - 1)
            
            df = df_raw.copy()
            for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        
            df_mes = df[df["FECHA DE ENVÍO"].dt.month == (meses.index(mes_sel) + 1)].copy()
        
            total_p = len(df_mes)
            entregados = len(df_mes[df_mes["FECHA DE ENTREGA REAL"].notna()])
            df_trans = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna()]
            en_tiempo = len(df_trans[df_trans["PROMESA DE ENTREGA"] >= hoy_dt])
            retrasados = len(df_trans[df_trans["PROMESA DE ENTREGA"] < hoy_dt])
            total_t = len(df_trans)

            # --- RENDERIZADO DE LAS DONITAS EN 4 COLUMNAS ---
            st.markdown("<br>", unsafe_allow_html=True)
            col_k1, col_k2, col_k3, col_k4 = st.columns(4)
            with col_k1:
                render_kpi(total_p, total_p, "TOTAL PEDIDOS", "#38bdf8")
            with col_k2:
                render_kpi(entregados, total_p, "ENTREGADOS", "#00FFAA")
            with col_k3:
                render_kpi(en_tiempo, total_t if total_t > 0 else 1, "EN TIEMPO", "#a855f7")
            with col_k4:
                render_kpi(retrasados, total_t if total_t > 0 else 1, "RETRASADOS", "#ff4b4b")

            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # --- GRÁFICOS INFERIORES (ENTREGA Y EN TRÁNSITO) ---
            g_col1, g_col2 = st.columns(2)
            
            with g_col1:
                st.markdown("<p style='color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; text-align: center;'>Distribución de Entregas</p>", unsafe_allow_html=True)
                if not df_mes.empty:
                    df_entregas_status = pd.DataFrame({
                        'Estatus': ['Entregados', 'Pendientes/En Tránsito'],
                        'Cantidad': [entregados, total_t]
                    })
                    fig_pie = px.pie(
                        df_entregas_status, 
                        names='Estatus', 
                        values='Cantidad', 
                        hole=0.5,
                        color='Estatus',
                        color_discrete_map={'Entregados': '#00FFAA', 'Pendientes/En Tránsito': '#38bdf8'}
                    )
                    fig_pie.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=280
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No hay datos para graficar en este período.")

            with g_col2:
                st.markdown("<p style='color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; text-align: center;'>Comportamiento de Envíos por Fletera</p>", unsafe_allow_html=True)
                if not df_mes.empty and "FLETERA" in df_mes.columns:
                    df_fletera = df_mes["FLETERA"].value_counts().reset_index()
                    df_fletera.columns = ['Fletera', 'Total']
                    fig_bar = px.bar(
                        df_fletera, 
                        x='Fletera', 
                        y='Total',
                        text='Total',
                        color='Fletera',
                        color_discrete_sequence=['#38bdf8', '#00FFAA', '#a855f7', '#ff4b4b']
                    )
                    fig_bar.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=280,
                        showlegend=False
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("No hay datos de fleteras disponibles.")

if __name__ == "__main__":
    main()

st.markdown(
    f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
