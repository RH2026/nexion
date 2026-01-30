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

Entiendo perfectamente. El diseño anterior era demasiado apretado y no dejaba respirar los elementos de NEXION. He ajustado el CSS Maestro para devolverle el "aire" al diseño, separando los bloques y dándole un aspecto mucho más limpio y profesional sin perder la elegancia.

Aquí tienes el código reparado:

Python
# ── CSS MAESTRO (REPARADO: MÁS ESPACIO Y RESPIRO) ────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* 1. Ocultar elementos nativos */
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .block-container {{ 
        padding-top: 1.5rem !important; /* Más respiro superior */
        padding-bottom: 2rem !important; 
    }}

    /* 2. Fondo principal */
    .stApp {{ 
        background-color: {vars_css['bg']} !important; 
        color: {vars_css['text']} !important; 
        font-family: 'Inter', sans-serif !important;
    }}

    /* REPARACIÓN: SEPARACIÓN ENTRE BLOQUES */
    [data-testid="stVerticalBlock"] {{
        gap: 1.2rem !important; /* Aumentamos el espacio global entre secciones */
    }}

    /* 3. Animación de entrada */
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    [data-testid="stVerticalBlock"] > div {{
        animation: fadeInUp 0.6s ease-out;
    }}

    /* 4. Estilo de Botones Generales */
    div.stButton > button {{
        background-color: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 4px !important; /* Bordes ligeramente más suaves */
        font-weight: 600 !important; 
        text-transform: uppercase;
        font-size: 11px !important; /* Un poco más legible */
        height: 38px !important; /* Más altura para no asfixiar el texto */
        transition: all 0.3s ease !important;
        width: 100%;
        margin-bottom: 8px !important; /* Separación individual */
    }}

    div.stButton > button:hover {{
        background-color: {vars_css['text']} !important; 
        color: {vars_css['bg']} !important; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }}

    /* 5. ESTILO PARA SUBMENÚS (Con su propio aire) */
    div.stButton > button[key^="sub_"] {{
        height: 32px !important;
        font-size: 10px !important;
        background-color: rgba(255, 255, 255, 0.5) !important;
        border-radius: 4px !important;
        margin-top: 4px !important; /* Separación del botón padre */
        border: 1px solid {vars_css['border']} !important;
    }}

    /* 6. Inputs de Búsqueda */
    .stTextInput input {{
        background-color: {vars_css['card']} !important;
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-radius: 4px !important;
        height: 48px !important; /* Buscador más imponente */
        font-size: 12px !important;
        text-align: center !important;
        letter-spacing: 1px;
    }}

    /* 7. Footer Fijo */
    .footer {{
        position: fixed;
        bottom: 0; left: 0; width: 100%;
        background-color: {vars_css['bg']};
        color: {vars_css['sub']};
        text-align: center;
        padding: 15px;
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

# ── HEADER Y NAVEGACIÓN REPARADA (CON SUBMENÚS Y MÁS AIRE) ──
header_zone = st.container()
with header_zone:
    # Restauramos c3 solo para dar margen al final si es necesario, o usamos 2 columnas
    c1, c2 = st.columns([1.5, 5.4], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=120)
            st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>", unsafe_allow_html=True)

    with c2:
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
                # 1. MENÚ PRINCIPAL
                seleccionado = st.session_state.menu_main == m
                btn_label = f"● {m}" if seleccionado else m
                
                if st.button(btn_label, use_container_width=True, key=f"main_{m}"):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()
                
                # 2. SUBMENÚ RESTAURADO (Solo aparece si está seleccionado)
                if seleccionado and sub_map[m]:
                    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                    for s in sub_map[m]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"sub_{s}"):
                            st.session_state.menu_sub = s
                            # Opcional: Si quieres que se oculte al dar clic, 
                            # podrías resetear menu_main aquí, pero por ahora lo dejo fijo.
                            st.rerun()

# Línea divisoria
st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:15px 0 25px; opacity:0.4;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO (DINÁMICO POR SUBMENÚ) ──────────
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

    # 2. SEGUIMIENTO
    elif st.session_state.menu_main == "SEGUIMIENTO":
        if st.session_state.menu_sub == "TRK":
            st.subheader("SEGUIMIENTO > CONTROL DE TRK")
            # Tu lógica de tabla aquí
        elif st.session_state.menu_sub == "GANTT":
            st.subheader("SEGUIMIENTO > CRONOGRAMA GANTT")
            # Tu lógica de Gantt aquí
        else:
            st.info("Seleccione una opción del menú SEGUIMIENTO")

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




































































































































































































































































































































































































































