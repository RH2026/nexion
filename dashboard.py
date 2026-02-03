import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
import plotly.graph_objects as go
import time
from github import Github
import json
import pytz
import zipfile
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re
import unicodedata
import io
import altair as alt
from datetime import date, datetime, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# --- MOTOR DE INTELIGENCIA LOGÍSTICA (XENOCODE CORE) ---
def d_local(dir_val):
    """Detecta si una dirección pertenece a la ZMG basada en CPs."""
    # Rangos de Zapopan, Guadalajara, Tonalá y Tlaquepaque
    rangos = [(44100, 44990), (45010, 45245), (45400, 45429), (45500, 45595)]
    cps = re.findall(r'\b\d{5}\b', str(dir_val))
    for cp in cps:
        try:
            if any(inicio <= int(cp) <= fin for inicio, fin in rangos): 
                return "LOCAL"
        except: 
            continue
    return "FORÁNEO"

@st.cache_data
def motor_logistico_central():
    """Carga la matriz historial para recomendaciones de fleteras."""
    try:
        if os.path.exists("matriz_historial.csv"):
            h = pd.read_csv("matriz_historial.csv", encoding='utf-8-sig')
            h.columns = [str(c).upper().strip() for c in h.columns]
            c_pre = [c for c in h.columns if 'PRECIO' in c][0]
            c_flet = [c for c in h.columns if 'FLETERA' in c or 'TRANSPORTE' in c][0]
            c_dir = [c for c in h.columns if 'DIRECCION' in c][0]
            h[c_pre] = pd.to_numeric(h[c_pre], errors='coerce').fillna(0)
            mejores = h.loc[h.groupby(c_dir)[c_pre].idxmin()]
            return mejores.set_index(c_dir)[c_flet].to_dict(), mejores.set_index(c_dir)[c_pre].to_dict()
    except: 
        pass
    return {}, {}

def load_lottieurl(url: str):
    """Carga la animación Lottie desde una URL"""
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ── TEMA FIJO (MODO OSCURO FORZADO - ONIX AZULADO) ──────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"

vars_css = {
    "bg": "#0E1117",      # Fondo Onix Azulado
    "card": "#1A1F2B",    # Fondos de tarjetas e inputs
    "text": "#E0E6ED",    # Texto principal
    "sub": "#8892B0",     # Texto secundario
    "border": "#2D333B",  # Bordes y líneas
    "logo": "n1.png"      # Logo
}

# ── CSS MAESTRO INTEGRAL (REPARACIÓN DEFINITIVA Y SIN ERRORES) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* 1. Limpieza de Interfaz */
header, footer, [data-testid="stHeader"] {{
    visibility: hidden;
    height: 0px;
}}

/* APP BASE */
html, body {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
}}

.stApp {{ 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['text']} !important; 
    font-family: 'Inter', sans-serif !important; 
}}

/* CONTENEDOR PRINCIPAL */
.block-container {{ 
    padding-top: 0.8rem !important; 
    padding-bottom: 5rem !important; 
    background-color: {vars_css['bg']} !important;
}}

/* 2. ANIMACIÓN DE ENTRADA (BLINDADA) */
@keyframes fadeInUp {{ 
    from {{ opacity: 0; transform: translateY(15px); }} 
    to {{ opacity: 1; transform: translateY(0); }} 
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

/* 3. TÍTULOS Y OPERATIONAL QUERY */
h3, .op-query-text {{ 
    font-size: 11px !important; 
    letter-spacing: 8px !important; 
    text-align: center !important; 
    margin-top: 8px !important; 
    margin-bottom: 18px !important; 
    color: {vars_css['sub']} !important; 
    display: block !important; 
    width: 100% !important; 
}}

/* 4. BOTONES SLIM */
div.stButton > button {{ 
    background-color: {vars_css['card']} !important; 
    color: {vars_css['text']} !important; 
    border: 1px solid {vars_css['border']} !important; 
    border-radius: 2px !important; 
    font-weight: 700 !important; 
    text-transform: uppercase; 
    font-size: 10px !important; 
    height: 28px !important; 
    min-height: 28px !important; 
    line-height: 28px !important; 
    transition: all 0.2s ease !important; 
    width: 100% !important; 
}}

div.stButton > button:hover {{ 
    background-color: #ffffff !important; 
    color: #000000 !important; 
    border-color: #ffffff !important; 
}}

/* 5. INPUTS */
.stTextInput input {{ 
    background-color: {vars_css['card']} !important; 
    color: {vars_css['text']} !important; 
    border: 1px solid {vars_css['border']} !important; 
    border-radius: 2px !important; 
    height: 45px !important; 
    text-align: center !important; 
    letter-spacing: 2px; 
}}

/* DATA EDITOR */
[data-testid="stDataEditor"] {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
}}

[data-testid="stDataEditor"] * {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
}}

/* 6. FOOTER FIJO */
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
    animation: none !important; 
    transform: none !important; 
}}

/* 7. GRÁFICOS / IFRAME (PLOTLY + FRAPPE) */
.stPlotlyChart {{
    visibility: visible !important;
    opacity: 1 !important;
    min-height: 300px !important;
}}

iframe {{
    background-color: {vars_css['bg']} !important;
    border: 1px solid {vars_css['border']} !important;
}}
</style>
""", unsafe_allow_html=True)

# ── SPLASH SCREEN ──────────────────────────────────────
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:40px;height:40px;border:1px solid {vars_css['border']}; border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.7)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER REESTRUCTURADO (CENTRADITO Y BALANCEADO) ──────────────────────────
header_zone = st.container()
with header_zone:
    # Usamos proporciones que den espacio suficiente a los lados para que el centro sea real
    c1, c2, c3 = st.columns([1.5, 4, 1.5], vertical_alignment="center")
    
    with c1:
        try:
            st.image(vars_css["logo"], width=110)
            st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0; color:{vars_css['text']};'>NEXION</h3>", unsafe_allow_html=True)

    with c2:
        # INDICADOR GENERAL (CENTRADO ABSOLUTO CON ESPACIADO NEXION)
        if st.session_state.menu_sub != "GENERAL":
            # Agregamos espacios manuales solo al separador "|" para que no se pegue a las letras
            ruta = f"{st.session_state.menu_main} <span style='color:{vars_css['sub']}; opacity:0.4; margin: 0 15px;'>|</span> {st.session_state.menu_sub}"
        else:
            ruta = st.session_state.menu_main
        
        st.markdown(f"""
            <div style='display: flex; justify-content: center; align-items: center; width: 100%; margin: 20px 0;'>
                <p style='font-size: 11px; 
                          letter-spacing: 8px;  /* ← Aumentado para efecto de doble espacio */
                          color: {vars_css['sub']}; 
                          margin: 0; 
                          font-weight: 700; 
                          text-transform: uppercase;
                          text-align: center;'>
                    {ruta}
                </p>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        # BOTÓN HAMBURGUESA - Alineado a la derecha del contenedor
        # Usamos una columna anidada o un div para empujar el popover a la derecha
        _, btn_col = st.columns([1, 2]) 
        with btn_col:
            with st.popover("☰", use_container_width=True):
                st.markdown("<p style='color:#64748b; font-size:10px; font-weight:700; margin-bottom:10px; letter-spacing:1px;'>NAVEGACIÓN</p>", unsafe_allow_html=True)
                
                # --- SECCIÓN DASHBOARD ---
                if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                    st.session_state.menu_main = "TRACKING"
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()
                
                # --- SECCIÓN SEGUIMIENTO ---
                with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                    for s in ["TRK", "GANTT", "QUEJAS"]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"pop_sub_{s}"):
                            st.session_state.menu_main = "SEGUIMIENTO"
                            st.session_state.menu_sub = s
                            st.rerun()

                # --- SECCIÓN REPORTES ---
                with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                    for s in ["APQ", "OPS", "OTD"]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"pop_rep_{s}"):
                            st.session_state.menu_main = "REPORTES"
                            st.session_state.menu_sub = s
                            st.rerun()

                # --- SECCIÓN FORMATOS ---
                with st.expander("FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")):
                    for s in ["SALIDA DE PT", "CONTRARRECIBOS"]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"pop_for_{s}"):
                            st.session_state.menu_main = "FORMATOS"
                            st.session_state.menu_sub = s
                            st.rerun()

                # --- SECCIÓN HUB LOG ---
                with st.expander("HUB LOG", expanded=(st.session_state.menu_main == "HUB LOG")):
                    # Definimos las sub-secciones de tu HUB
                    for s in ["SMART ROUTING", "SISTEMA", "ALERTAS"]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"pop_hub_{s}"):
                            st.session_state.menu_main = "HUB LOG"
                            st.session_state.menu_sub = s
                            st.rerun()
                

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px; opacity:0.2;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO ──────────────────────────────────
main_container = st.container()
with main_container:
    # 1. TRACKING
    if st.session_state.menu_main == "TRACKING":
        st.markdown("<div style='margin-top: 5vh;'></div>", unsafe_allow_html=True)
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"<p class='op-query-text'>O P E R A T I O N A L &nbsp; Q U E R Y</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")

    elif st.session_state.menu_main == "SEGUIMIENTO":
        # ── A. CARGA DE DATOS (MATRIZ DESDE GITHUB) ──
        @st.cache_data(ttl=600)
        def cargar_matriz_github():
            url = "https://raw.githubusercontent.com/RH2026/dashboard-logistica/refs/heads/main/Matriz_Excel_Dashboard.csv"
            try:
                return pd.read_csv(url, encoding='utf-8-sig')
            except:
                return None

        df_seguimiento = cargar_matriz_github()

        if df_seguimiento is None:
            st.error("⚠️ ERROR: No se detectó la base de datos en GitHub.")
            st.stop()

        # ── B. RELOJ MAESTRO (GUADALAJARA) ──
        tz_gdl = pytz.timezone('America/Mexico_City')
        hoy_gdl = datetime.now(tz_gdl).date()

        # ── C. NAVEGACIÓN DE SUB-MENÚ TRK ──
        if st.session_state.menu_sub == "TRK":
            # 1. FILTROS DE CABECERA
            with st.container():
                st.markdown(f"<p class='op-query-text' style='letter-spacing:8px; text-align:center;'>M Ó D U L O &nbsp; D E &nbsp; I N T E L I G E N C I A &nbsp; L O G Í S T I C A</p>", unsafe_allow_html=True)
                f_col1, f_col2, f_col3 = st.columns([1, 1.5, 1.5], vertical_alignment="bottom")
                
                with f_col1:
                    meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
                    mes_sel = st.selectbox("MES OPERATIVO", meses, index=hoy_gdl.month - 1)
                
                with f_col2:
                    mes_num = meses.index(mes_sel) + 1
                    inicio_m = date(hoy_gdl.year, mes_num, 1)
                    if mes_num == 12:
                        fin_m = date(hoy_gdl.year, 12, 31)
                    else:
                        fin_m = date(hoy_gdl.year, mes_num + 1, 1) - pd.Timedelta(days=1)
                    
                    fin_m_final = fin_m.date() if hasattr(fin_m, 'date') else fin_m
                    
                    rango_fechas = st.date_input(
                        "RANGO DE ANÁLISIS",
                        value=(inicio_m, min(hoy_gdl, fin_m_final) if mes_num == hoy_gdl.month else fin_m_final),
                        format="DD/MM/YYYY"
                    )

                with f_col3:
                    opciones_f = sorted(df_seguimiento["FLETERA"].unique()) if "FLETERA" in df_seguimiento.columns else []
                    filtro_global_fletera = st.multiselect("FILTRAR PAQUETERÍA", opciones_f, placeholder="TODOS")

            # ── 2. PROCESAMIENTO DE DATOS KPI ──
            df_kpi = df_seguimiento.copy()
            df_kpi.columns = [c.upper() for c in df_kpi.columns]
            
            for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
                if col in df_kpi.columns:
                    df_kpi[col] = pd.to_datetime(df_kpi[col], dayfirst=True, errors='coerce')
            
            # A. Filtrado por rango de fechas
            df_kpi = df_kpi.dropna(subset=["FECHA DE ENVÍO"])
            if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                df_kpi = df_kpi[(df_kpi["FECHA DE ENVÍO"].dt.date >= rango_fechas[0]) & 
                                (df_kpi["FECHA DE ENVÍO"].dt.date <= rango_fechas[1])]

            # B. Filtrado por fletera
            if filtro_global_fletera:
                df_kpi = df_kpi[df_kpi["FLETERA"].isin(filtro_global_fletera)]

            # C. Identificación de "En Tránsito" y Cálculo de Atrasos
            df_kpi['ESTATUS_CALCULADO'] = df_kpi['FECHA DE ENTREGA REAL'].apply(lambda x: 'ENTREGADO' if pd.notna(x) else 'EN TRANSITO')
            df_sin_entregar = df_kpi[df_kpi['ESTATUS_CALCULADO'] == 'EN TRANSITO'].copy()

            # --- AQUÍ CALCULAMOS LA COLUMNA QUE DABA ERROR ---
            if not df_sin_entregar.empty:
                df_sin_entregar["DIAS_ATRASO"] = (pd.Timestamp(hoy_gdl) - df_sin_entregar["PROMESA DE ENTREGA"]).dt.days
                df_sin_entregar["DIAS_ATRASO"] = df_sin_entregar["DIAS_ATRASO"].apply(lambda x: x if (pd.notna(x) and x > 0) else 0)
                df_sin_entregar["DIAS_TRANS"] = (pd.Timestamp(hoy_gdl) - df_sin_entregar["FECHA DE ENVÍO"]).dt.days
            else:
                # Si está vacío, creamos las columnas manualmente para evitar el KeyError
                df_sin_entregar["DIAS_ATRASO"] = 0
                df_sin_entregar["DIAS_TRANS"] = 0

            # D. Lógica para el PRÓXIMO MES
            proximo_mes_num = mes_num + 1 if mes_num < 12 else 1
            anio_proximo = hoy_gdl.year if mes_num < 12 else hoy_gdl.year + 1
            nombre_prox_mes = meses[proximo_mes_num - 1]

            # Buscamos en toda la base original los que se entregan el próximo mes
            df_full = df_seguimiento.copy()
            df_full.columns = [c.upper() for c in df_full.columns]
            if "PROMESA DE ENTREGA" in df_full.columns:
                fechas_promesa = pd.to_datetime(df_full["PROMESA DE ENTREGA"], dayfirst=True, errors='coerce')
                conteo_proximo = len(df_full[(fechas_promesa.dt.month == proximo_mes_num) & (fechas_promesa.dt.year == anio_proximo)])
            else:
                conteo_proximo = 0

            # E. Métricas Finales
            total_p = len(df_kpi)
            pend_p = len(df_sin_entregar)
            entregados_v = len(df_kpi[df_kpi['ESTATUS_CALCULADO'] == 'ENTREGADO'])
            eficiencia = (entregados_v / total_p * 100) if total_p > 0 else 0

            # ── 3. RENDERIZADO TARJETAS (4 COLUMNAS) ──
            st.markdown("<br>", unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)

            m1.markdown(f"<div class='main-card-kpi' style='border-left-color:#94a3b8;'><div class='kpi-label'>Carga Total {mes_sel}</div><div class='kpi-value' style='font-size:28px; font-weight:800;'>{total_p}</div></div>", unsafe_allow_html=True)
            m2.markdown(f"<div class='main-card-kpi' style='border-left-color:#38bdf8;'><div class='kpi-label'>En Tránsito</div><div class='kpi-value' style='color:#38bdf8; font-size:28px; font-weight:800;'>{pend_p}</div></div>", unsafe_allow_html=True)
            m3.markdown(f"<div class='main-card-kpi' style='border-left-color:#a855f7;'><div class='kpi-label'>Entregas {nombre_prox_mes}</div><div class='kpi-value' style='color:#a855f7; font-size:28px; font-weight:800;'>{conteo_proximo}</div></div>", unsafe_allow_html=True)
            
            color_ef = "#00FFAA" if eficiencia >= 95 else "#f97316"
            m4.markdown(f"<div class='main-card-kpi' style='border-left-color:{color_ef};'><div class='kpi-label'>Eficiencia</div><div class='kpi-value' style='color:{color_ef}; font-size:28px; font-weight:800;'>{eficiencia:.1f}%</div></div>", unsafe_allow_html=True)

            # ── 4. SEMÁFORO DE ALERTAS (YA NO DARÁ ERROR) ──
            st.markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:2px; color:{vars_css['sub']}; text-align:center; margin-top:30px;'>S E M Á F O R O DE ALERTAS</p>", unsafe_allow_html=True)
            
            a1_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] == 1])
            a2_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"].between(2,4)])
            a5_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] >= 5])
            
            c_a1, c_a2, c_a3 = st.columns(3)
            c_a1.markdown(f"<div class='card-alerta' style='border-top: 4px solid #fde047;'><div style='color:#9CA3AF; font-size:10px;'>LEVE (1D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a1_v}</div></div>", unsafe_allow_html=True)
            c_a2.markdown(f"<div class='card-alerta' style='border-top: 4px solid #f97316;'><div style='color:#9CA3AF; font-size:10px;'>MODERADO (2-4D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a2_v}</div></div>", unsafe_allow_html=True)
            c_a3.markdown(f"<div class='card-alerta' style='border-top: 4px solid #ff4b4b;'><div style='color:#9CA3AF; font-size:10px;'>CRÍTICO (+5D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a5_v}</div></div>", unsafe_allow_html=True)
                                 
            # 5. PANEL DE EXCEPCIONES (CON DISEÑO DE BARRAS DOBLES)
            st.divider()
            df_criticos = df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] > 0].copy() if not df_sin_entregar.empty else pd.DataFrame()
            
            if not df_criticos.empty:
                st.markdown(f"<p style='font-size:11px; font-weight:700; letter-spacing:8px; color:{vars_css['sub']}; text-transform:uppercase; text-align:center; margin-bottom:20px;'>PANEL DE EXCEPCIONES</p>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1: sel_f = st.multiselect("TRANSPORTISTA:", sorted(df_criticos["FLETERA"].unique()), placeholder="TODOS")
                with c2: sel_g = st.selectbox("GRAVEDAD ATRASO:", ["TODOS", "CRÍTICO (+5 DÍAS)", "MODERADO (2-4 DÍAS)", "LEVE (1 DÍA)"])
                
                df_viz = df_criticos.copy()
                if sel_f: df_viz = df_viz[df_viz["FLETERA"].isin(sel_f)]
                if sel_g == "CRÍTICO (+5 DÍAS)": df_viz = df_viz[df_viz["DIAS_ATRASO"] >= 5]
                elif sel_g == "MODERADO (2-4 DÍAS)": df_viz = df_viz[df_viz["DIAS_ATRASO"].between(2, 4)]
                elif sel_g == "LEVE (1 DÍA)": df_viz = df_viz[df_viz["DIAS_ATRASO"] == 1]

                # Mapeo de columnas para evitar KeyError
                columnas_deseadas = {
                    "NÚMERO DE PEDIDO": ["NÚMERO DE PEDIDO", "PEDIDO"],
                    "NOMBRE DEL CLIENTE": ["NOMBRE DEL CLIENTE", "CLIENTE"],
                    "DESTINO": ["DESTINO", "CIUDAD"],
                    "FECHA DE ENVÍO": ["FECHA DE ENVÍO"],
                    "PROMESA DE ENTREGA": ["PROMESA DE ENTREGA"],
                    "FLETERA": ["FLETERA"],
                    "GUIA": ["GUIA", "GUÍA"],
                    "DIAS_TRANS": ["DIAS_TRANS"],
                    "DIAS_ATRASO": ["DIAS_ATRASO"]
                }
                cols_finales = [next((c for c in p if c in df_viz.columns), None) for p in columnas_deseadas.values()]
                cols_finales = [c for c in cols_finales if c is not None]

                with st.expander("DETALLE TÉCNICO DE RETRASOS", expanded=True):
                    st.dataframe(
                        df_viz[cols_finales].sort_values("DIAS_ATRASO", ascending=False),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "FECHA DE ENVÍO": st.column_config.DateColumn("ENVÍO", format="DD/MM/YYYY"),
                            "PROMESA DE ENTREGA": st.column_config.DateColumn("P. ENTREGA", format="DD/MM/YYYY"),
                            "DIAS_TRANS": st.column_config.ProgressColumn("DÍAS VIAJE", format="%d", min_value=0, max_value=15, color="orange"),
                            "DIAS_ATRASO": st.column_config.ProgressColumn("RETRASO", format="%d DÍAS", min_value=0, max_value=15, color="red")
                        }
                    )
            else:
                st.success("SISTEMA NEXION: SIN RETRASOS DETECTADOS")

            # 6. DETALLE DE ENTREGAS DEL PRÓXIMO MES
            st.divider()
            
            # Filtramos el DataFrame original para obtener el detalle de esos pedidos
            # Usamos la lógica de proximo_mes_num y anio_proximo que ya definimos arriba
            df_detalle_prox = df_seguimiento.copy()
            df_detalle_prox.columns = [c.upper() for c in df_detalle_prox.columns]
            
            if "PROMESA DE ENTREGA" in df_detalle_prox.columns:
                df_detalle_prox["PROMESA DE ENTREGA"] = pd.to_datetime(df_detalle_prox["PROMESA DE ENTREGA"], dayfirst=True, errors='coerce')
                
                # Filtro exacto para el detalle
                df_futuro = df_detalle_prox[
                    (df_detalle_prox["PROMESA DE ENTREGA"].dt.month == proximo_mes_num) & 
                    (df_detalle_prox["PROMESA DE ENTREGA"].dt.year == anio_proximo)
                ].copy()

                if not df_futuro.empty:
                    st.markdown(f"<p style='font-size:11px; font-weight:700; letter-spacing:5px; color:#a855f7; text-transform:uppercase; text-align:center;'>PLANIFICACIÓN DE ENTREGAS: {nombre_prox_mes}</p>", unsafe_allow_html=True)
                    
                    with st.expander(f"VER LISTADO DE {len(df_futuro)} PEDIDOS PARA {nombre_prox_mes}", expanded=False):
                        # Seleccionamos columnas relevantes para no saturar la vista
                        cols_prox = ["NÚMERO DE PEDIDO", "NOMBRE DEL CLIENTE", "DESTINO", "PROMESA DE ENTREGA", "FLETERA", "ESTATUS"]
                        # Filtramos solo las que existan en el DF
                        cols_prox_existentes = [c for c in cols_prox if c in df_futuro.columns]
                        
                        st.dataframe(
                            df_futuro[cols_prox_existentes].sort_values("PROMESA DE ENTREGA"),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "PROMESA DE ENTREGA": st.column_config.DateColumn("FECHA PACTADA", format="DD/MM/YYYY"),
                                "NÚMERO DE PEDIDO": st.column_config.TextColumn("PEDIDO"),
                            }
                        )
                else:
                    st.info(f"No hay entregas programadas aún para {nombre_prox_mes}")

        
        elif st.session_state.menu_sub == "GANTT":
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "tareas.csv"
            CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
            
            # ── FUNCIONES DE FECHA Y CARGA REPARADAS ─────────────────────────────────────────────
            def obtener_fecha_mexico():
                """Retorna la fecha actual de Guadalajara sin errores de atributo."""
                try:
                    tz_gdl = pytz.timezone('America/Mexico_City')
                    return datetime.now(tz_gdl).date()
                except:
                    # Respaldo si falla pytz (tu lógica original corregida)
                    import datetime as dt_module
                    return (dt_module.datetime.now(dt_module.timezone.utc) - dt_module.timedelta(hours=6)).date()
            
            def cargar_datos_seguro():
                columnas = [
                    "FECHA","FECHA_FIN","IMPORTANCIA","TAREA","ULTIMO ACCION",
                    "PROGRESO","DEPENDENCIAS","TIPO","GRUPO"
                ]
                hoy = obtener_fecha_mexico()
                try:
                    # Carga con bust de caché para evitar datos viejos
                    import time
                    import requests
                    from io import StringIO
                    
                    r = requests.get(f"{CSV_URL}?t={int(time.time())}")
                    if r.status_code == 200:
                        df = pd.read_csv(StringIO(r.text))
                        df.columns = [c.strip().upper() for c in df.columns]
                        
                        # Asegurar que todas las columnas existan
                        for c in columnas:
                            if c not in df.columns:
                                df[c] = ""
                        
                        # Normalización de datos con la clase datetime correcta
                        df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce").dt.date
                        df["FECHA_FIN"] = pd.to_datetime(df["FECHA_FIN"], errors="coerce").dt.date
                        
                        # Reemplazar nulos por la fecha de hoy (GDL)
                        df["FECHA"] = df["FECHA"].apply(lambda x: x if isinstance(x, date) else hoy)
                        df["FECHA_FIN"] = df["FECHA_FIN"].apply(
                            lambda x: x if isinstance(x, date) else hoy + timedelta(days=1)
                        )
                        
                        df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors="coerce").fillna(0).astype(int)
                        df["IMPORTANCIA"] = df["IMPORTANCIA"].fillna("Media")
                        df["TIPO"] = df["TIPO"].fillna("Tarea")
                        df["GRUPO"] = df["GRUPO"].fillna("General")
                        df["DEPENDENCIAS"] = df["DEPENDENCIAS"].fillna("")
                        
                        return df[columnas]
                except Exception as e:
                    st.error(f"Error al cargar CSV: {e}")
                    
                return pd.DataFrame(columns=columnas)
            
            # ── GESTIÓN DE ESTADO ──────────────────────────────────────────────────────
            if "df_tareas" not in st.session_state:
                st.session_state.df_tareas = cargar_datos_seguro()
            
            # Copia de trabajo
            df_master = st.session_state.df_tareas.copy()
            
            # ── 1. FILTROS Y CONTROLES (PARTE SUPERIOR) ────────────────────────────────
                      
            c1, c2 = st.columns([1, 2])
            with c1:
                gantt_view = st.radio("Vista", ["Day", "Week", "Month", "Year"], horizontal=True, index=0, key="gantt_v")
            
            with c2:
                grupos_disponibles = sorted(df_master["GRUPO"].astype(str).unique())
                grupos_sel = st.multiselect("Filtrar por grupo", grupos_disponibles, default=grupos_disponibles, key="gantt_g")
            
            # Filtrado de datos para el Gantt
            df_gantt = df_master[df_master["GRUPO"].isin(grupos_sel)].copy()
            
            # 🔒 FORZAR HITOS A DURACIÓN CERO
            mask_hito = df_gantt["TIPO"].str.lower() == "hito"
            df_gantt.loc[mask_hito, "FECHA_FIN"] = df_gantt.loc[mask_hito, "FECHA"]
            
            # Preparar lista de tareas para el JS
            tasks_data = []
            for i, r in enumerate(df_gantt.itertuples(), start=1):
                if not str(r.TAREA).strip(): 
                    continue
            
                importancia = str(r.IMPORTANCIA).strip().lower()
                task_id = f"T{i}"  # id único T1, T2, T3...
                
                # Dependencias deben estar en formato T1,T2,... si vienen como índices
                dependencias = str(r.DEPENDENCIAS).strip()
                if dependencias:
                    # Convertimos índices a ids T#
                    dependencias_ids = []
                    for d in dependencias.split(','):
                        d = d.strip()
                        if d.isdigit():
                            dependencias_ids.append(f"T{int(d)+1}")  # sumamos 1 porque enumerate empieza en 1
                        else:
                            dependencias_ids.append(d)
                    dependencias = ','.join(dependencias_ids)
                
                tasks_data.append({
                    "id": task_id,
                    "name": f"[{r.GRUPO}] {r.TAREA}",
                    "start": str(r.FECHA),
                    "end": str(r.FECHA_FIN),
                    "progress": int(r.PROGRESO),
                    "dependencies": dependencias,
                    "custom_class": f"imp-{importancia}"
                })
            
            tasks_js_str = json.dumps(tasks_data)
            
            # ── 2. RENDERIZADO GANTT REPARADO ───────────────────────────────
            components.html(
                f"""
                <html>
                <head>
                    <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.css'>
                    <script src='https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.js'></script>
                    <style>
                        html, body {{ background:#111827; margin:0; padding:0; }}
                        #gantt {{ background:#0E1117; }}
                        .gantt text {{ fill:#E5E7EB !important; font-size:12px; }}
                        .grid-background {{ fill:#0b0e14 !important; }}
                        .grid-header {{ fill:#151a24 !important; }}
                        .grid-row {{ fill:#0b0e14 !important; }}
                        .grid-row:nth-child(even) {{ fill:#0f131a !important; }}
                        .grid-line {{ stroke: #1e2530 !important; stroke-opacity: 0.1 !important; }}
                        .arrow {{ stroke: #9ca3af !important; stroke-width: 1.6 !important; opacity: 1 !important; fill: none !important; }}
                        .bar-wrapper.imp-urgente .bar {{ fill:#DC2626 !important; }}
                        .bar-wrapper.imp-alta    .bar {{ fill:#F97316 !important; }}
                        .bar-wrapper.imp-media   .bar {{ fill:#3B82F6 !important; }}
                        .bar-wrapper.imp-baja    .bar {{ fill:#22C55E !important; }}
                        .today-highlight {{ fill: #00FF00 !important; opacity: 0.2 !important; }}
                    </style>
                </head>
                <body>
                    <div id='gantt'></div>
                    <script>
                        var tasks = {tasks_js_str};
                        if(tasks.length){{
                            var gantt = new Gantt('#gantt', tasks, {{
                                view_mode: '{gantt_view}',
                                bar_height: 20,
                                padding: 40,
                                date_format: 'YYYY-MM-DD'
                            }});
            
                            // Forzar suavizado de líneas horizontales y ocultar verticales
                            setTimeout(function() {{
                                document.querySelectorAll('#gantt svg line').forEach(function(line) {{
                                    var x1 = parseFloat(line.getAttribute('x1'));
                                    var x2 = parseFloat(line.getAttribute('x2'));
                                    var y1 = parseFloat(line.getAttribute('y1'));
                                    var y2 = parseFloat(line.getAttribute('y2'));
            
                                    if(x1 === x2) {{
                                        // ocultar verticales
                                        line.style.display = 'none';
                                    }}
                                    if(y1 === y2) {{
                                        // suavizar horizontales
                                        line.style.strokeOpacity = '0.1';
                                        line.style.stroke = '#1e2530';
                                    }}
                                }});
                            }}, 200);
                        }}
                    </script>
                </body>
                </html>
                """,
                height=420,
                scrolling=False
            )
            # ── 3. DATA EDITOR (ABAJO) ─────────────────────────────────────────────────
            st.subheader("EDITOR DE TAREAS")
            
            # Normalización para el Data Editor (Evitar strings "nan")
            df_editor = df_master.copy()
            for col in ["IMPORTANCIA","TAREA","ULTIMO ACCION","DEPENDENCIAS","TIPO","GRUPO"]:
                df_editor[col] = df_editor[col].astype(str).replace("nan", "").fillna("")
            
            df_editor["PROGRESO_VIEW"] = df_editor["PROGRESO"]
            
            df_editado = st.data_editor(
                df_editor,
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "FECHA": st.column_config.DateColumn("Inicio"),
                    "FECHA_FIN": st.column_config.DateColumn("Fin"),
                    "IMPORTANCIA": st.column_config.SelectboxColumn("Prioridad", options=["Urgente","Alta","Media","Baja"]),
                    "PROGRESO": st.column_config.NumberColumn("Progreso %", min_value=0, max_value=100, step=5),
                    "PROGRESO_VIEW": st.column_config.ProgressColumn("Avance", min_value=0, max_value=100),
                    "TAREA": st.column_config.TextColumn("Tarea"),
                    "ULTIMO ACCION": st.column_config.TextColumn("Última acción"),
                    "DEPENDENCIAS": st.column_config.TextColumn("Dependencias"),
                    "TIPO": st.column_config.SelectboxColumn("Tipo", options=["Tarea","Hito"]),
                    "GRUPO": st.column_config.TextColumn("Grupo"),
                }
            )
            
            # Sincronizar columna visual
            df_editado["PROGRESO_VIEW"] = df_editado["PROGRESO"]
            
            if st.button("SINCRONIZAR CON GITHUB", use_container_width=True):
                df_guardar = df_editado.drop(columns=["PROGRESO_VIEW"], errors="ignore")
                if guardar_en_github(df_guardar):
                    st.session_state.df_tareas = df_guardar
                    st.rerun()



        
        elif st.session_state.menu_sub == "QUEJAS":
            st.subheader("SEGUIMIENTO > QUEJAS")
            st.info("Gestión de incidencias")
        else:
            st.subheader("MÓDULO DE SEGUIMIENTO")
            st.write("Seleccione una sub-categoría en la barra superior.")

    # 3. REPORTES
    elif st.session_state.menu_main == "REPORTES":
        st.subheader(f"MÓDULO DE INTELIGENCIA > {st.session_state.menu_sub}")

    # 4. FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        import streamlit.components.v1 as components
        import os

        if st.session_state.menu_sub == "SALIDA DE PT":
            # ── A. GENERACIÓN DE FOLIO CON HORA DE GUADALAJARA ──
            if 'folio_nexion' not in st.session_state:
                # Definimos la zona horaria de Guadalajara/CDMX
                tz_gdl = pytz.timezone('America/Mexico_City') 
                # REPARACIÓN: Usamos datetime.now(tz) directamente
                now_gdl = datetime.now(tz_gdl)
                
                # Formato: F - AÑO MES DÍA - HORA MINUTO (Hora local de GDL)
                st.session_state.folio_nexion = f"F-{now_gdl.strftime('%Y%m%d-%H%M')}"                
            
            # ── B. CARGA DE INVENTARIO (RAÍZ) ──────────────────────
            @st.cache_data
            def load_inventory():
                ruta = os.path.join(os.getcwd(), "inventario.csv")
                if not os.path.exists(ruta): 
                    ruta = os.path.join(os.getcwd(), "..", "inventario.csv")
                try:
                    df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig')
                    df.columns = [str(c).strip().upper() for c in df.columns]
                    return df
                except: 
                    return pd.DataFrame(columns=['CODIGO', 'DESCRIPCION'])
            
            df_inv = load_inventory()
            
            # Inicialización única de las filas en el session_state
            if 'rows' not in st.session_state:
                st.session_state.rows = pd.DataFrame([
                    {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": "0"} 
                ] * 10)
                                    
            # ── C. CUERPO DE ENTRADA (ESTRUCTURA CON ICONOS MATERIAL) ────────────────
            with st.container(border=True):
                h1, h2, h3 = st.columns(3)
                
                # Fecha automática
                f_val = h1.date_input(":material/calendar_month: FECHA", value=datetime.now(), key="f_in")
                
                # Selección de turno
                t_val = h2.selectbox(":material/schedule: TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_in")
                
                # Folio Automático
                fol_val = h3.text_input(":material/fingerprint: FOLIO", value=st.session_state.folio_nexion, key="fol_in")
            
            # ── D. MOTOR DE BÚSQUEDA INTERNO (LOOKUP) ──────────────────────────
            def lookup():
                edits = st.session_state["editor_pt"].get("edited_rows", {})
                added = st.session_state["editor_pt"].get("added_rows", [])
                
                for row in added:
                    new_row = {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}
                    new_row.update(row)
                    st.session_state.rows = pd.concat([st.session_state.rows, pd.DataFrame([new_row])], ignore_index=True)
            
                for idx_str, info in edits.items():
                    idx = int(idx_str)
                    for col, val in info.items():
                        st.session_state.rows.at[idx, col] = val
                    
                    if "CODIGO" in info:
                        val_codigo = str(info["CODIGO"]).strip().upper()
                        if not df_inv.empty:
                            match = df_inv[df_inv['CODIGO'].astype(str).str.strip().str.upper() == val_codigo]
                            if not match.empty:
                                st.session_state.rows.at[idx, "DESCRIPCION"] = match.iloc[0]['DESCRIPCION']
                                st.session_state.rows.at[idx, "CODIGO"] = val_codigo
            
            # ── E. EDITOR DE DATOS DINÁMICO ────────────────────────────────────
            st.markdown("<p style='font-size:12px; font-weight:bold; color:#54AFE7; letter-spacing:2px;'>DETALLE DE MATERIALES</p>", unsafe_allow_html=True)
            df_final = st.data_editor(
                st.session_state.rows, 
                num_rows="dynamic", 
                use_container_width=True, 
                key="editor_pt", 
                on_change=lookup,
                column_config={
                    "CODIGO": st.column_config.TextColumn(":material/qr_code: CÓDIGO"),
                    "DESCRIPCION": st.column_config.TextColumn(":material/description: DESCRIPCIÓN"),
                    "CANTIDAD": st.column_config.TextColumn(":material/pin: CANTIDAD", width="small")
                }
            )
            
            # ── F. RENDERIZADO PRO (HTML PARA IMPRESIÓN) ───────────────────────────
            filas_print = df_final[df_final["CODIGO"] != ""]
            tabla_html = "".join([
                f"<tr>"
                f"<td style='border:1px solid black;padding:8px;'>{r['CODIGO']}</td>"
                f"<td style='border:1px solid black;padding:8px;'>{r['DESCRIPCION']}</td>"
                f"<td style='border:1px solid black;padding:8px;text-align:center;'>{r['CANTIDAD']}</td>"
                f"</tr>" 
                for _, r in filas_print.iterrows()
            ])
            
            form_html = f"""
            <div style="font-family:sans-serif; padding:20px; color:black; background:white;">
                <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:10px;">
                    <div>
                        <h2 style="margin:0; letter-spacing:2px;">JYPESA</h2>
                        <p style="margin:0; font-size:10px; letter-spacing:1px;">AUTOMATIZACIÓN DE PROCESOS</p>
                    </div>
                    <div style="text-align:right; font-size:12px;">
                        <p style="margin:0;"><b>FOLIO:</b> {fol_val}</p>
                        <p style="margin:0;"><b>FECHA:</b> {f_val}</p>
                        <p style="margin:0;"><b>TURNO:</b> {t_val}</p>
                    </div>
                </div>
                <h3 style="text-align:center; letter-spacing:5px; margin-top:30px; text-decoration:underline;">ENTREGA DE MATERIALES PT</h3>
                <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                    <thead><tr style="background:#f2f2f2;">
                        <th style="border:1px solid black;padding:10px;">CÓDIGO</th>
                        <th style="border:1px solid black;padding:10px;">DESCRIPCIÓN</th>
                        <th style="border:1px solid black;padding:10px;text-align:center;">CANTIDAD</th>
                    </tr></thead>
                    <tbody>{tabla_html}</tbody>
                </table>
                <div style="margin-top:80px; display:flex; justify-content:space-around; text-align:center; font-size:10px;">
                    <div style="width:30%; border-top:1px solid black;">ENTREGÓ<br><b>Analista de Inventario</b></div>
                    <div style="width:30%; border-top:1px solid black;">AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></div>
                    <div style="width:30%; border-top:1px solid black;">RECIBIÓ<br><b>Rigoberto Hernandez / Cord.Logística</b></div>
                </div>
            </div>
            """
          
            # ── G. BOTONES DE ACCIÓN FINAL (MATERIAL DESIGN) ─────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            col_pdf, col_reset = st.columns(2) 
            
            with col_pdf:
                if st.button(":material/picture_as_pdf: GENERAR FORMATO PDF", 
                             type="primary", 
                             use_container_width=True, 
                             key="btn_pdf_nexion"):
                    components.html(f"<html><body>{form_html}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)
                    st.toast("Generando vista previa...", icon="⚙️")
            
            with col_reset:
                if st.button(":material/refresh: ACTUALIZAR SISTEMA", 
                             type="primary", 
                             use_container_width=True, 
                             key="btn_reset_nexion"):
                    if 'folio_nexion' in st.session_state:
                        del st.session_state.folio_nexion
                    st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": "0"}] * 10)
                    st.rerun()
                        
                    
    # --- SUBSECCIÓN B: CONTRARRECIBOS (CORREGIDO) ---
    elif st.session_state.menu_sub == "CONTRARRECIBOS": # <--- CAMBIO CLAVE
        # Configuración de zona horaria Guadalajara
        tz_gdl = pytz.timezone('America/Mexico_City')
        now_gdl = datetime.now(tz_gdl)
        
        # ── A. INICIALIZACIÓN DE ESTADO ──
        if 'rows_contrarecibo' not in st.session_state:
            # Creamos un formato vacío con las columnas de tu imagen
            st.session_state.rows_contrarecibo = pd.DataFrame([
                {"FECHA": now_gdl.strftime('%d/%m/%Y'), "CODIGO": "", "PAQUETERIA": "", "CANTIDAD": ""} 
            ] * 10)
        
        # ── B. ENCABEZADO Y CONTROLES ──
        st.markdown("### REPORTE ENTREGA DE FACTURAS DE CONTRARECIBO")
        
        with st.container(border=True):
            col_h1, col_h2 = st.columns([2, 1])
            with col_h2:
                # Hora que aparece en la esquina superior derecha de tu imagen
                hora_reporte = st.text_input("HORA", value=now_gdl.strftime('%I:%M %p').lower())
        
        # ── C. EDITOR DE DATOS (MANUAL) ──
        # Adaptado a: FECHA | CODIGO | PAQUETERIA | CANTIDAD
        df_editado = st.data_editor(
            st.session_state.rows_contrarecibo,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_contrarecibo",
            column_config={
                "FECHA": st.column_config.TextColumn("FECHA"),
                "CODIGO": st.column_config.TextColumn("CODIGO"),
                "PAQUETERIA": st.column_config.TextColumn("PAQUETERIA"),
                "CANTIDAD": st.column_config.TextColumn("CANTIDAD")
            }
        )
        
        # ── D. RENDERIZADO PARA IMPRESIÓN (HTML) ──
        filas_validas = df_editado[df_editado["CODIGO"] != ""]
        tabla_html = "".join([
            f"<tr>"
            f"<td style='border-bottom:1px solid black; padding:8px;'>{r['FECHA']}</td>"
            f"<td style='border-bottom:1px solid black; padding:8px;'>{r['CODIGO']}</td>"
            f"<td style='border-bottom:1px solid black; padding:8px;'>{r['PAQUETERIA']}</td>"
            f"<td style='border-bottom:1px solid black; padding:8px; text-align:center;'>{r['CANTIDAD']}</td>"
            f"</tr>"
            for _, r in filas_validas.iterrows()
        ])
        
        # Espacios en blanco para mantener el formato de la imagen si hay pocos datos
        espacios_blancos = "".join(["<tr><td style='border-bottom:1px solid black; height:25px;' colspan='4'></td></tr>"] * (12 - len(filas_validas)))
        
        form_html = f"""
        <div style="font-family: Arial, sans-serif; color: black; background: white; padding: 40px;">
            <div style="text-align: right; border-bottom: 2px solid black; margin-bottom: 10px;">
                <span style="font-weight: bold; border: 1px solid black; padding: 2px 10px;">{hora_reporte}</span>
            </div>
            
            <h4 style="text-align: center; margin-bottom: 30px; letter-spacing: 1px;">REPORTE ENTREGA DE FACTURAS DE CONTRARECIBO</h4>
            
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="text-align: left; font-size: 12px; border-bottom: 1px solid black;">
                        <th style="padding: 8px; width: 20%;">FECHA</th>
                        <th style="padding: 8px; width: 20%;">CODIGO</th>
                        <th style="padding: 8px; width: 40%;">PAQUETERIA</th>
                        <th style="padding: 8px; width: 20%; text-align: center;">CANTIDAD</th>
                    </tr>
                </thead>
                <tbody style="font-size: 13px;">
                    {tabla_html}
                    {espacios_blancos}
                </tbody>
            </table>
        
            <div style="margin-top: 100px; display: flex; justify-content: space-between; text-align: center; font-size: 12px;">
                <div style="width: 40%;">
                    <div style="border-top: 1px solid black; padding-top: 5px;">
                        <b>ELABORÓ</b><br>
                        Rigoberto - Cord de Logística
                    </div>
                </div>
                <div style="width: 40%;">
                    <div style="border-top: 1px solid black; padding-top: 5px;">
                        <b>RECIBIÓ</b><br>
                        Nombre y Firma
                    </div>
                </div>
            </div>
        </div>
        """
        
        # ── E. ACCIONES ──
        st.write("---")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("📄 GENERAR PDF / IMPRIMIR", type="primary", use_container_width=True):
                components.html(f"<html><body>{form_html}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)
        
        with col_btn2:
            if st.button("🔄 LIMPIAR FORMATO", use_container_width=True):
                st.session_state.rows_contrarecibo = pd.DataFrame([
                    {"FECHA": now_gdl.strftime('%d/%m/%Y'), "CODIGO": "", "PAQUETERIA": "", "CANTIDAD": ""} 
                ] * 10)
                st.rerun()
            
    # 5. HUB LOG
    elif st.session_state.menu_main == "HUB LOG":
        # Librerías necesarias para el funcionamiento del HUB
        import os
        import io
        import zipfile
        import pandas as pd
        from datetime import datetime as dt_class
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from pypdf import PdfReader, PdfWriter

        if st.session_state.menu_sub == "SMART ROUTING":
            st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>LOGISTICS INTELLIGENCE HUB | XENOCODE CORE</p>", unsafe_allow_html=True)
            
            # --- RUTAS Y MOTOR ---
            archivo_log = "log_maestro_acumulado.csv"
            
            # Intentar obtener el motor logístico (asegura que la función esté definida)
            try:
                d_flet, d_price = motor_logistico_central()
            except:
                d_flet, d_price = {}, {}
                st.warning("Motor logístico central no detectado. Cargando en modo manual.")

            if 'db_acumulada' not in st.session_state:
                st.session_state.db_acumulada = pd.read_csv(archivo_log) if os.path.exists(archivo_log) else pd.DataFrame()

            # --- FUNCIONES DE SELLADO INTERNAS ---
            def generar_sellos_fisicos(lista_textos, x, y):
                output = PdfWriter()
                for texto in lista_textos:
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=letter)
                    can.setFont("Helvetica-Bold", 11)
                    can.drawString(x, y, f"{str(texto).upper()}")
                    can.save()
                    packet.seek(0)
                    output.add_page(PdfReader(packet).pages[0])
                out_io = io.BytesIO()
                output.write(out_io)
                return out_io.getvalue()

            def marcar_pdf_digital(pdf_file, texto_sello, x, y):
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.setFont("Helvetica-Bold", 11)
                can.drawString(x, y, f"{str(texto_sello).upper()}")
                can.save()
                packet.seek(0)
                new_pdf = PdfReader(packet)
                existing_pdf = PdfReader(pdf_file)
                output = PdfWriter()
                page = existing_pdf.pages[0]
                page.merge_page(new_pdf.pages[0])
                output.add_page(page)
                for i in range(1, len(existing_pdf.pages)):
                    output.add_page(existing_pdf.pages[i])
                out_io = io.BytesIO()
                output.write(out_io)
                return out_io.getvalue()

            # --- CARGA Y PROCESAMIENTO ERP ----
            file_p = st.file_uploader(":material/upload_file: SUBIR ARCHIVO ERP (CSV)", type="csv") 
            
            # --- 1. ESTADO DE ESPERA: CALIBRACIÓN DE ESPACIOS ---
            if not file_p:
                st.markdown(f"""
                    <div class="nexion-fixed-wrapper">
                        <div class="nexion-center-node">
                            <div class="nexion-core-point"></div>
                            <div class="nexion-halo-ring"></div>
                        </div>
                        <p class="nexion-tech-label">LOGISTICS INTELLIGENCE HUB | SYSTEM READY</p>
                    </div>
                    <style>
                        .nexion-fixed-wrapper {{ height: 250px !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; background: transparent !important; position: relative !important; }}
                        .nexion-center-node {{ position: relative !important; display: flex !important; align-items: center !important; justify-content: center !important; width: 20px !important; height: 20px !important; }}
                        .nexion-core-point {{ width: 14px !important; height: 14px !important; background-color: #54AFE7 !important; border-radius: 50% !important; box-shadow: 0 0 20px #54AFE7, 0 0 40px rgba(84,175,231,0.4) !important; animation: nexion-vibrance 2s ease-in-out infinite !important; z-index: 10 !important; position: absolute !important; }}
                        .nexion-halo-ring {{ position: absolute !important; width: 14px !important; height: 14px !important; border: 1px solid #54AFE7 !important; border-radius: 50% !important; opacity: 0 !important; animation: nexion-perfect-spread 4s linear infinite !important; z-index: 5 !important; }}
                        .nexion-tech-label {{ color: #54AFE7 !important; font-family: 'Monospace', monospace !important; letter-spacing: 5px !important; font-size: 10px !important; margin-top: 35px !important; opacity: 0.8 !important; text-align: center !important; }}
                        @keyframes nexion-vibrance {{ 0%, 100% {{ transform: scale(1); filter: brightness(1); }} 50% {{ transform: scale(1.2); filter: brightness(1.4); }} }}
                        @keyframes nexion-perfect-spread {{ 0% {{ transform: scale(1); opacity: 0; }} 20% {{ opacity: 0.4; }} 100% {{ transform: scale(6); opacity: 0; }} }}
                    </style>
                """, unsafe_allow_html=True)
            
            # --- 2. ESTADO ACTIVO: MOTOR SMART ---
            else:
                if "archivo_actual" not in st.session_state or st.session_state.archivo_actual != file_p.name:
                    if "df_analisis" in st.session_state: del st.session_state["df_analisis"]
                    st.session_state.archivo_actual = file_p.name
                    st.rerun()

                try:
                    if "df_analisis" not in st.session_state:
                        p = pd.read_csv(file_p, encoding='utf-8-sig')
                        p.columns = [str(c).upper().strip() for c in p.columns]
                        col_id = 'FACTURA' if 'FACTURA' in p.columns else ('DOCNUM' if 'DOCNUM' in p.columns else p.columns[0])
                        
                        if 'DIRECCION' in p.columns:
                            def motor_prioridad(row):
                                addr = str(row['DIRECCION']).upper()
                                # Lógica local GDL
                                if any(loc in addr for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA"]):
                                    return "LOCAL"
                                return d_flet.get(row['DIRECCION'], "SIN HISTORIAL")

                            p['RECOMENDACION'] = p.apply(motor_prioridad, axis=1)
                            p['COSTO'] = p.apply(lambda r: 0.0 if r['RECOMENDACION'] == "LOCAL" else d_price.get(r['DIRECCION'], 0.0), axis=1)
                            p['FECHA_HORA'] = dt_class.now().strftime("%Y-%m-%d %H:%M")
                            
                            cols_sistema = [col_id, 'RECOMENDACION', 'COSTO', 'FECHA_HORA']
                            otras = [c for c in p.columns if c not in cols_sistema]
                            st.session_state.df_analisis = p[cols_sistema + otras]

                    st.markdown("### :material/analytics: RECOMENDACIONES GENERADAS")
                    modo_edicion = st.toggle(":material/edit_note: EDITAR VALORES")
                    
                    p_editado = st.data_editor(
                        st.session_state.df_analisis,
                        use_container_width=True,
                        num_rows="fixed",
                        column_config={
                            "RECOMENDACION": st.column_config.TextColumn(":material/local_shipping: FLETERA", disabled=not modo_edicion),
                            "COSTO": st.column_config.NumberColumn(":material/payments: TARIFA", format="$%.2f", disabled=not modo_edicion),
                        },
                        key="editor_pro_v11"
                    )

                    with st.container():
                        st.download_button(
                            label=":material/download: DESCARGAR RESULTADOS (CSV ANALIZADO)",
                            data=p_editado.to_csv(index=False).encode('utf-8-sig'),
                            file_name="Analisis_Nexion.csv",
                            use_container_width=True,
                            key="btn_descarga_top"
                        )
                        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
                        c_izq, c_der = st.columns(2)
                        with c_izq:
                            if st.button(":material/push_pin: FIJAR CAMBIOS", use_container_width=True):
                                st.session_state.df_analisis = p_editado
                                st.toast("Cambios aplicados", icon="📌")
                        with c_der:
                            id_guardado = f"guardado_{st.session_state.archivo_actual}"
                            if not st.session_state.get(id_guardado, False):
                                if st.button(":material/save: GUARDAR REGISTROS", use_container_width=True):
                                    st.session_state[id_guardado] = True
                                    st.snow()
                                    st.rerun()
                            else:
                                st.button(":material/verified_user: REGISTROS ASEGURADOS", use_container_width=True, disabled=True)
                    
                    # --- SISTEMA DE SELLADO ---
                    st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:30px 0; opacity:0.3;'>", unsafe_allow_html=True)
                    st.markdown("<h3 style='font-size: 16px; color: white;'>:material/print: SISTEMA DE SELLADO Y SOBREIMPRESIÓN</h3>", unsafe_allow_html=True)
                    
                    with st.expander(":material/settings: PANEL DE CALIBRACIÓN", expanded=True):
                        col_x, col_y = st.columns(2)
                        ajuste_x = col_x.slider("Eje X (Horizontal)", 0, 612, 510)
                        ajuste_y = col_y.slider("Eje Y (Vertical)", 0, 792, 760)

                    st.markdown("<p style='font-weight: 800; font-size: 12px; letter-spacing: 1px; margin-bottom:5px;'>IMPRESIÓN FÍSICA</p>", unsafe_allow_html=True)
                    if st.button(":material/article: GENERAR SELLOS PARA FACTURAS (PAPEL)", use_container_width=True):
                        sellos = st.session_state.df_analisis['RECOMENDACION'].tolist()
                        if sellos:
                            pdf_out = generar_sellos_fisicos(sellos, ajuste_x, ajuste_y)
                            st.download_button(":material/download: DESCARGAR PDF DE SELLOS", pdf_out, "Sellos_Fisicos.pdf", use_container_width=True)
                    
                    st.markdown("<div style='margin-top:25px;'></div>", unsafe_allow_html=True)
                    st.markdown("<p style='font-weight: 800; font-size: 12px; letter-spacing: 1px; margin-bottom:5px;'>SELLADO DIGITAL (SOBRE PDF)</p>", unsafe_allow_html=True)
                    with st.container(border=True):
                        pdfs = st.file_uploader("Subir Facturas PDF", type="pdf", accept_multiple_files=True)
                        if pdfs:
                            if st.button("EJECUTAR ESTAMPADO DIGITAL"):
                                df_ref = st.session_state.get('df_analisis', pd.DataFrame())
                                if not df_ref.empty:
                                    mapa = pd.Series(df_ref.RECOMENDACION.values, index=df_ref[df_ref.columns[0]].astype(str)).to_dict()
                                    z_buf = io.BytesIO()
                                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                                        for pdf in pdfs:
                                            f_id = next((f for f in mapa.keys() if f in pdf.name.upper()), None)
                                            if f_id:
                                                zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ajuste_x, ajuste_y))
                                    st.download_button(":material/folder_zip: DESCARGAR ZIP SELLADO", z_buf.getvalue(), "Facturas_Digitales.zip", use_container_width=True)

                except Exception as e:
                    st.error(f"Error en procesamiento Smart: {e}")

        elif st.session_state.menu_sub == "SISTEMA":
            st.info("ESTADO DE SERVIDORES: ONLINE | XENOCODE CORE: ACTIVE")
            
        elif st.session_state.menu_sub == "ALERTAS":
            st.warning("NO HAY ALERTAS CRÍTICAS EN EL HUB LOG.")

# ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
st.markdown(f"""
<div class="footer">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
    <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
    <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
</div>
""", unsafe_allow_html=True)


































































































































































































































































































































































































































































































































































































































































































































