import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
from github import Github
import plotly.graph_objects as go
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA FIJO (MODO CLARO) ──────────────────────────────────
# Forzamos el estado a claro
st.session_state.tema = "claro"

if "menu_main" not in st.session_state: 
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"

# Diccionario simplificado: eliminamos la estructura de "oscuro" para evitar errores
vars_css = {
    "bg": "#E3E7ED",      # Fondo principal solicitado
    "card": "#FFFFFF",    # Fondo de tarjetas e inputs
    "text": "#111111",    # Texto principal
    "sub": "#2D3136",     # Texto secundario/subtítulos
    "border": "#C9D1D9",  # Líneas y bordes
    "logo": "n2.png"      # Logo para versión clara
}

# ── CSS MAESTRO (CON ANIMACIONES ELITE) ─────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* Ocultar elementos nativos de Streamlit */
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .block-container {{ 
        padding-top: 0.5rem !important; 
        padding-bottom: 0rem !important; 
    }}

    /* Fondo principal de la App */
    .stApp {{ 
        background-color: {vars_css['bg']} !important; 
        color: {vars_css['text']} !important; 
        font-family: 'Inter', sans-serif !important;
    }}

    /* ── ANIMACIÓN DE ENTRADA ── */
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    [data-testid="stVerticalBlock"] > div {{
        animation: fadeInUp 0.6s ease-out;
    }}

    /* INPUTS DE BÚSQUEDA */
    .stTextInput input {{
        background-color: {vars_css['card']} !important;
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-radius: 2px !important;
        height: 42px !important;
        font-size: 11px !important;
        text-align: center !important;
        letter-spacing: 2px;
        transition: all 0.3s ease;
    }}
    
    .stTextInput input:focus {{
        border-color: {vars_css['text']} !important;
        box-shadow: 0 0 8px rgba(0, 0, 0, 0.05);
    }}

    /* BOTONES */
    div.stButton>button {{
        background-color: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 2px !important;
        font-weight: 700 !important; 
        text-transform: uppercase;
        font-size: 10px !important;
        height: 32px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    
    div.stButton>button:hover {{
        background-color: {vars_css['text']} !important; 
        color: {vars_css['bg']} !important; 
        transform: translateY(-1px);
    }}

    /* LOGO Y FOOTER */
    div[data-testid='stImage'] img {{
        image-rendering: -webkit-optimize-contrast !important;
    }}

    .footer {{
        position: fixed;
        bottom: 0; left: 0; width: 100%;
        background-color: {vars_css['bg']};
        color: {vars_css['sub']};
        text-align: center;
        padding: 10px;
        font-size: 9px;
        letter-spacing: 2px;
        border-top: 1px solid {vars_css['border']};
        z-index: 100;
    }}
</style>
""", unsafe_allow_html=True)

# ── 4. SPLASH SCREEN ──────────────────────────────────────
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="width:40px;height:40px;border:1px solid {vars_css['border']};
              border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
              <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.7)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER Y NAVEGACIÓN UNIFICADA (ACORDEÓN VERTICAL) ──────
header_zone = st.container()
with header_zone:
    c1, c2, c3 = st.columns([1.5, 5, 0.4], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=120)
            st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>", unsafe_allow_html=True)

    with c2:
        # Definición de estructura de navegación
        sub_map = {
            "TRACKING": [],
            "SEGUIMIENTO": ["TRK", "GANTT"],
            "REPORTES": ["APQ", "OPS", "OTD"],
            "FORMATOS": ["SALIDA DE PT"]
        }
        
        cols_main = st.columns(4)
        main_menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]
        
        for i, m in enumerate(main_menus):
            with cols_main[i]:
                # 1. BOTÓN DE MENÚ PRINCIPAL
                seleccionado = st.session_state.menu_main == m
                btn_label = f"● {m}" if seleccionado else m
                
                if st.button(btn_label, use_container_width=True, key=f"main_{m}"):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()
                
                # 2. DESPLIEGUE DE SUBMENÚ (Solo si el padre está seleccionado)
                if seleccionado and sub_map[m]:
                    st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
                    for s in sub_map[m]:
                        sub_activo = st.session_state.menu_sub == s
                        sub_label = f"» {s}" if sub_activo else s
                        
                        # Usamos una clave única y un estilo que el CSS pueda identificar
                        if st.button(sub_label, use_container_width=True, key=f"sub_{s}"):
                            st.session_state.menu_sub = s
                            st.rerun()

    with c3:
        st.button("☀", key="theme_btn_fixed")

# Línea divisoria más limpia
st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:10px 0 20px; opacity:0.5;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO (MANTENIENDO TU LÓGICA DE MÓDULOS) ──
main_container = st.container()
with main_container:
    # 1. TRACKING
    if st.session_state.menu_main == "TRACKING":
        st.markdown("<div style='margin-top: 5vh;'></div>", unsafe_allow_html=True)
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"<p style='text-align:center; color:{vars_css['sub']}; font-size:11px; letter-spacing:8px; margin-bottom:20px;'>O P E R A T I O N A L &nbsp; Q U E R Y</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")

    # 2. SEGUIMIENTO (Incluye el Editor de GitHub que tenías)
    elif st.session_state.menu_main == "SEGUIMIENTO":
        if st.session_state.menu_sub == "TRK":
            st.subheader("SEGUIMIENTO > TRK")
        elif st.session_state.menu_sub == "GANTT":
            st.subheader("SEGUIMIENTO > GANTT")
            
            # --- Aquí va tu lógica de GitHub y Editor que ya tienes configurada ---
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "tareas.csv"
            CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/tareas.csv"
            
            # (Mantener funciones obtener_fecha_mexico, cargar_datos_seguro y guardar_en_github)
            # [Lógica del Editor st.data_editor...]
            if 'df_tareas' not in st.session_state:
                # Nota: Asegúrate de tener las funciones definidas arriba o importadas
                try: st.session_state.df_tareas = cargar_datos_seguro()
                except: st.write("Error cargando base de datos.")

            with st.container(border=True):
                if 'df_tareas' in st.session_state:
                    df_editado = st.data_editor(
                        st.session_state.df_tareas,
                        num_rows="dynamic",
                        use_container_width=True,
                        key="nexion_editor_v2",
                        hide_index=True
                    )
                    if st.button("💾 SINCRONIZAR CAMBIOS", use_container_width=True, type="primary"):
                        # guardar_en_github(df_editado)
                        st.toast("Datos procesados")

    # 3. REPORTES
    elif st.session_state.menu_main == "REPORTES":
        st.subheader(f"MÓDULO DE INTELIGENCIA > {st.session_state.menu_sub}")

    # 4. FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        st.subheader("CENTRO DE DOCUMENTACIÓN")

# ── FOOTER FIJO ──────────────────────────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
    </div>
""", unsafe_allow_html=True)

































































































































































































































































































































































































































