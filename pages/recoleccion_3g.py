import base64
import calendar
from datetime import date, datetime, timedelta
import io
from io import BytesIO, StringIO
import json
import math
import os
import random
import re
import time
import unicodedata
import zipfile

import altair as alt
from fpdf import FPDF
from github import Github
import google.generativeai as genai
import numpy as np
import pandas as pd

# CAMBIO 1: Pillow con alias para no chocar con ReportLab
from PIL import Image as PILImage, ImageDraw, ImageFont

import plotly.express as px
import plotly.graph_objects as go
from pypdf import PdfReader, PdfWriter
import pytz
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

# CAMBIO 2: Importamos platypus completo para usar platypus.Image sin perder ningún elemento
import reportlab.platypus as platypus
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image


import requests
import streamlit as st
import streamlit.components.v1 as components
from auth import exigir_autenticacion


# ============================================================
# AUTENTICACIÓN
# ============================================================

exigir_autenticacion("recoleccion_3g")


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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap');

/* --- ANIMACIONES DE ENTRADA --- */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(15px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

/* --- OCULTAR ELEMENTOS DE STREAMLIT Y SIDEBAR --- */
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

/* APP BASE */
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

/* BOTONES SLIM Y BOTONES DE DESCARGA */
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

/* --- SEPARACIÓN EQUILIBRADA EN EL POPOVER --- */
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {{
    gap: 0.45rem !important;
}}

div[data-testid="stPopoverBody"] .stButton {{
    margin-bottom: 0rem !important;
}}

div[data-testid="stPopoverBody"] [data-testid="stExpander"] {{
    border: none !important;
    background: transparent !important;
    margin-bottom: 0rem !important;
    > div {{
        padding: 0 !important;
    }}
}}

/* ===================== TABS - ESTILO NEXION (IGUAL A TÍTULOS DINÁMICOS) ===================== */

/* CONTENEDOR DE LAS PESTAÑAS */
div[data-testid="stTabs"] [role="tablist"] {{
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    gap: 36px !important;
    margin: 0 !important;
    padding: 0 !important;
    background-color: transparent !important;
    border-bottom: 1px solid {vars_css['border']} !important;
}}

/* CADA PESTAÑA (INACTIVA / BASE) */
div[data-testid="stTabs"] button,
div[data-testid="stTabs"] div[data-baseweb="tab"],
div[data-testid="stTabs"] [role="tab"] {{
    min-height: 30px !important;
    height: 30px !important;
    padding: 0px 4px !important;
    margin: 0 !important;
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    transition: all .25s ease !important;
    flex: 0 0 auto !important;
}}

/* TEXTO INTERNO DE LAS PESTAÑAS (IGUALADO A TÍTULOS DINÁMICOS: 13px y 5px de espacio) */
div[data-testid="stTabs"] [role="tab"] p,
div[data-testid="stTabs"] [role="tab"] span {{
    color: rgba(255, 255, 255, 0.6) !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    letter-spacing: 0px !important;
    text-transform: uppercase !important;
    margin: 0 !important;
}}

/* HOVER EN PESTAÑAS */
div[data-testid="stTabs"] [role="tab"]:hover p,
div[data-testid="stTabs"] [role="tab"]:hover span {{
    color: #FFD700 !important;
}}

/* TAB ACTIVA (TEXTO BLANCO PURO IDÉNTICO AL HEADER) */
div[data-testid="stTabs"] button[aria-selected="true"],
div[data-testid="stTabs"] div[aria-selected="true"],
div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: transparent !important;
    background-color: transparent !important;
}}

div[data-testid="stTabs"] [role="tab"][aria-selected="true"] p,
div[data-testid="stTabs"] [role="tab"][aria-selected="true"] span {{
    color: #FFFFFF !important;
    font-weight: 400 !important;
    letter-spacing: 0px !important;
}}

/* ELIMINAR FOCUS / SOMBRAS DE STREAMLIT */
div[data-testid="stTabs"] button:focus,
div[data-testid="stTabs"] button:active,
div[data-testid="stTabs"] [role="tab"]:focus {{
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
}}

/* LÍNEA INFERIOR DE SELECCIÓN (INDICADOR DE COLOR) */
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {{
    background-color: #38bdf8 !important;
    height: 2px !important;
}}

/*FOOTER FIJO */
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

/* --- TARJETAS DE KPI ESTILO WAR ROOM --- */
.base-card-alerta {{
    background-color: #2B343B;
    border: 1px solid #4B5D67;
    border-left: 5px solid #38bdf8;
    padding: 16px 20px;
    border-radius: 6px;
    width: 100%;
    font-family: 'Inter', sans-serif;
    color: white;
    box-sizing: border-box;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    margin-bottom: 10px;
}}

/* --- FORZAR ESTILO EN BOTONES DE FORMULARIO (ST.FORM_SUBMIT_BUTTON) --- */
div.stFormSubmitButton > button {{
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

div.stFormSubmitButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

</style>
""",
    unsafe_allow_html=True,
)


#----registra usuario------
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

def registrar_acceso_github(usuario, modulo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/auditoria_accesos.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if r.status_code == 200:
        file_data = r.json()
        sha = file_data.get("sha", "")
        content_decoded = base64.b64decode(file_data.get("content", "")).decode("utf-8")
        df_aud = pd.read_csv(io.StringIO(content_decoded))
    else:
        df_aud = pd.DataFrame(columns=["FECHA_HORA", "USUARIO", "MODULO"])
        sha = ""

    nuevo_registro = pd.DataFrame([{"FECHA_HORA": fecha_hora, "USUARIO": usuario, "MODULO": modulo}])
    df_aud = pd.concat([df_aud, nuevo_registro], ignore_index=True)
    
    csv_string = df_aud.to_csv(index=False)
    payload = {
        "message": f"Registro de acceso de {usuario} al módulo {modulo}",
        "content": base64.b64encode(csv_string.encode()).decode()
    }
    if sha:
        payload["sha"] = sha
        
    requests.put(url, json=payload, headers=headers)


# ==========================================
# 2. SISTEMA DE SEGURIDAD PRO (VALIDACIÓN DE SESIÓN Y BLINDAJE)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "dashboard.py"
    st.switch_page("log.py")

def verificar_permiso_pagina(modulo, submodulo=None):
    permisos = st.session_state.get("permisos", {})
    if st.session_state.get("usuario_activo", "").upper() == "RIGOBERTO":
        return True
        
    if not permisos.get(modulo.upper(), False):
        st.markdown(
            f"""
            <div style="
                background: {vars_css['card']}; 
                border: 1px solid {vars_css['border']}; 
                border-left: 5px solid #FFD700; 
                padding: 20px 25px; 
                border-radius: 8px; 
                width: 100%; 
                font-family: 'Inter', sans-serif; 
                color: white; 
                box-sizing: border-box; 
                margin-bottom: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <div style="width: 10px; height: 10px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 8px #FFD700;"></div>
                    <span style="color: #FFD700; font-size: 13px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">
                        ACCESS RESTRICTED // MÓDULO NO AUTORIZADO
                    </span>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 600; padding-left: 20px;">
                    No tienes permisos para acceder al módulo: <b style="color: white; text-transform: uppercase;">{modulo}</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col_regresar_m, col_vacia_m = st.columns([1.5, 4])
        with col_regresar_m:
            if st.button("REGRESAR AL INICIO", key="btn_regresar_modulo", use_container_width=True):
                st.switch_page("dashboard.py")
        st.stop()
            
    if submodulo and not permisos.get(submodulo.upper(), False):
        st.markdown(
            f"""
            <div style="
                background: {vars_css['card']}; 
                border: 1px solid {vars_css['border']}; 
                border-left: 5px solid #FFD700; 
                padding: 20px 25px; 
                border-radius: 8px; 
                width: 100%; 
                font-family: 'Inter', sans-serif; 
                color: white; 
                box-sizing: border-box; 
                margin-bottom: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <div style="width: 10px; height: 10px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 8px #FFD700;"></div>
                    <span style="color: #FFD700; font-size: 13px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">
                        ACCESS RESTRICTED // SECCIÓN BLOQUEADA
                    </span>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 600; padding-left: 20px;">
                    No tienes permisos para acceder a la sección: <b style="color: white; text-transform: uppercase;">{submodulo}</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col_regresar_s, col_vacia_s = st.columns([1.5, 4])
        with col_regresar_s:
            if st.button("REGRESAR AL INICIO", key="btn_regresar_submodulo", use_container_width=True):
                st.switch_page("dashboard.py")
        st.stop()

# Blindaje de Módulo DASHBOARD
verificar_permiso_pagina("FORMATOS" "RECOLECCION 3G")


# ==========================================
# 3. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================
@st.cache_data(ttl=60)
def obtener_matriz_github():
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv?nocache={int(time.time())}"
    try:
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except Exception as e:
        st.error(f"Error fatal al conectar con GitHub: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def cargar_datos_dashboard():
    t = int(time.time())
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
    try:
        df = pd.read_csv(url, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return None


def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    ).upper()
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    return " ".join(texto.split())


# Inicialización segura de estados de menú
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "FORMATOS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "RECOLECCIONES 3G"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1
if "tipo_resultado" not in st.session_state:
    st.session_state.tipo_resultado = "OPERACION"


# ==========================================
# 4. HEADER CON 4 COLUMNAS Y MENÚ BLINDADO
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
        texto_principal = st.session_state.menu_main
        azul_nexion = "#82D4E6"
        oro_brillante = "#FFD700"

        if texto_principal == "DASHBOARD":
            texto_principal = f"NEXION <span style='color: {azul_nexion}; font-weight: 500; margin: 0 10px; font-size: 16px;'>|</span> SMART LOGISTICS"

        if st.session_state.menu_sub != "GENERAL":
            ruta = (
                f"{texto_principal} "
                f"<span style='color: {azul_nexion}; opacity: 0.8; margin: 0 15px;'>/</span> "
                f"<span style='color: {oro_brillante}; font-weight: 500; text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);'>"
                f"{st.session_state.menu_sub}</span>"
            )
        else:
            ruta = texto_principal

        st.markdown(
            f"""
            <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
                <p style='font-size: 13px; letter-spacing: 5px; color: {vars_css['sub']}; margin: 0; font-weight: 500; text-transform: uppercase; text-align: center;'>
                    {ruta}
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with c3:
        es_atencion3g = (
            st.session_state.get("usuario_activo", "").upper() == "ATENCION3G"
        )
        key_actual = f"main_search_v{st.session_state.search_key_version}"

        query = st.text_input(
            "Buscar",
            placeholder="🔍 BUSCADOR DESACTIVADO" if es_atencion3g else "🔍 Buscar...",
            label_visibility="collapsed",
            key=key_actual,
            disabled=es_atencion3g,
        )

        if query:
            url_raw = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
            try:
                df_matriz_fresco = pd.read_csv(url_raw)
                df_matriz_fresco.columns = df_matriz_fresco.columns.str.strip()
            except Exception:
                df_matriz_fresco = cargar_datos_dashboard()

            # 1. Búsqueda en Matriz Principal (Global)
            res_ops = pd.DataFrame()
            if df_matriz_fresco is not None:
                cols_op = [
                    "NÚMERO DE GUÍA",
                    "NÚMERO DE PEDIDO",
                    "NO CLIENTE",
                    "NOMBRE DEL CLIENTE",
                    "DESTINO",
                ]
                cols_op_disp = [c for c in cols_op if c in df_matriz_fresco.columns]
                if cols_op_disp:
                    mask_ops = df_matriz_fresco[cols_op_disp].astype(str).apply(
                        lambda x: x.str.contains(query, case=False, na=False)
                    ).any(axis=1)
                    res_ops = df_matriz_fresco[mask_ops].copy()

            # 2. Búsqueda en Archivo T1.xlsx
            res_t1 = pd.DataFrame()
            try:
                df_t1_temp = pd.read_excel("T1.xlsx") 
                df_t1_temp.columns = df_t1_temp.columns.str.strip().str.upper()
                
                cols_t1 = [c for c in ["OBSERVACION 1", "TALON", "DESTINATARIO", "DESTINO"] if c in df_t1_temp.columns]
                
                if cols_t1:
                    mask_t1 = df_t1_temp[cols_t1].astype(str).apply(
                        lambda x: x.str.contains(query, case=False, na=False)
                    ).any(axis=1)
                    match_t1 = df_t1_temp[mask_t1].copy()
                    
                    if not match_t1.empty:
                        match_t1 = match_t1.rename(columns={
                            "TALON": "NÚMERO DE GUÍA",
                            "OBSERVACION 1": "NÚMERO DE PEDIDO",
                            "DESTINATARIO": "NOMBRE DEL CLIENTE",
                            "SUBTOTAL": "COSTO DE LA GUÍA",
                            "F.DOC": "FECHA DE ENVÍO",
                            "BULTOS": "CANTIDAD DE CAJAS"
                        })
                        match_t1["FLETERA"] = "TRES GUERRAS"
                        res_t1 = match_t1
            except Exception:
                pass

            # 3. CRUCE DE INFORMACIÓN
            if not res_ops.empty and not res_t1.empty:
                for idx, row in res_ops.iterrows():
                    guia_actual = str(row.get("NÚMERO DE GUÍA", "")).strip()
                    if guia_actual in ["", "nan", "0", "None"]:
                        pedido_global = str(row.get("NÚMERO DE PEDIDO", "")).strip()
                        match_en_t1 = res_t1[res_t1["NÚMERO DE PEDIDO"].astype(str).str.strip() == pedido_global]
                        if not match_en_t1.empty:
                            res_ops.loc[idx, "NÚMERO DE GUÍA"] = match_en_t1.iloc[0].get("NÚMERO DE GUÍA", guia_actual)
                            res_ops.loc[idx, "FLETERA"] = match_en_t1.iloc[0].get("FLETERA", "TRES GUERRAS")
                            if "COSTO DE LA GUÍA" in match_en_t1.columns and pd.notna(match_en_t1.iloc[0].get("COSTO DE LA GUÍA")):
                                res_ops.loc[idx, "COSTO DE LA GUÍA"] = match_en_t1.iloc[0].get("COSTO DE LA GUÍA")

            # 4. Búsqueda en Inventario
            res_inv = pd.DataFrame()
            if res_ops.empty and res_t1.empty:
                try:
                    df_inv_temp = pd.read_csv("inventario.csv")
                    df_inv_temp.columns = df_inv_temp.columns.str.strip()
                    cols_inv = [c for c in ["CODIGO", "DESCRIPCION"] if c in df_inv_temp.columns]
                    if cols_inv:
                        mask_inv = df_inv_temp[cols_inv].astype(str).apply(
                            lambda x: x.str.contains(query, case=False, na=False)
                        ).any(axis=1)
                        res_inv = df_inv_temp[mask_inv]
                except Exception:
                    pass

            if not res_ops.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "OPERACION"
                st.session_state.resultado_busqueda = res_ops
            elif not res_t1.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "OPERACION" 
                st.session_state.resultado_busqueda = res_t1
            elif not res_inv.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "INVENTARIO"
                st.session_state.resultado_busqueda = res_inv
            else:
                st.session_state.busqueda_activa = False
                st.session_state.resultado_busqueda = None
                st.toast("Sin resultados: No se encontró en Matriz Global ni en T1", icon="⚠️")

    with c4:
        with st.popover("☰ Menú", use_container_width=True):
            usuario = st.session_state.get("usuario_activo", "GUEST")
            permisos = st.session_state.get("permisos", {})
            nombre_display = st.session_state.get("nombre_completo", "OPERADOR DESCONOCIDO")
        
            st.markdown(
                f"""
                <div style='background-color: rgba(255,255,255,0.05); padding: 8px 10px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #00D4FF;'>
                    <p style='color:#00D4FF; font-size:9px; font-weight:500; margin:0; letter-spacing:1px;'>USUARIO ACTIVO</p>
                    <p style='color:{vars_css['text']}; font-size:13px; font-weight:500; margin:0;'>{nombre_display.upper()}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
        
            if permisos.get("DASHBOARD", False):
                if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                    registrar_acceso_github(usuario, "DASHBOARD")
                    st.session_state.menu_main = "DASHBOARD"
                    st.session_state.menu_sub = "GENERAL"
                    st.session_state.busqueda_activa = False
                    st.switch_page("dashboard.py")
        
            if permisos.get("SEGUIMIENTO", False):
                with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                    opciones_seg_posibles = ["ALERTAS", "GANTT", "INCIDENCIAS"]
                    opciones_seg = [s for s in opciones_seg_posibles if permisos.get(s, False)]
                    for s in opciones_seg:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_sub_{s}2"):
                            registrar_acceso_github(usuario, f"SEGUIMIENTO - {s}")
                            st.session_state.menu_main = "SEGUIMIENTO"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            
                            # Redirección específica para incidencias
                            if s == "INCIDENCIAS":
                                st.switch_page("pages/incidencias_tr.py")
                            else:
                                st.rerun()
        
            if permisos.get("ENTREGAS", False):
                with st.expander("ENTREGAS", expanded=(st.session_state.menu_main == "ENTREGAS")):
                    opciones_ent_posibles = ["AGC", "AMAZON", "BARCELO", "NACIONAL"]
                    opciones_ent = [s for s in opciones_ent_posibles if permisos.get(s, False)]
                    for s in opciones_ent:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_ent_{s}2"):
                            registrar_acceso_github(usuario, f"ENTREGAS - {s}")
                            st.session_state.menu_main = "ENTREGAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "AGC":
                                st.switch_page("pages/entregas_agc.py")
                            elif s == "NACIONAL":
                                st.switch_page("pages/envios.py")
                            else:
                                st.rerun()
        
            if permisos.get("REPORTES", False):
                with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                    opciones_rep_posibles = ["COSTOS CEDIS", "ANALISIS MENSUAL", "DETALLE COSTOS", "ENVIOS ESPECIALES", "ENVIO DE MUESTRAS"]
                    opciones_rep = [s for s in opciones_rep_posibles if permisos.get(s, False)]
                    for s in opciones_rep:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_rep_{s}2"):
                            registrar_acceso_github(usuario, f"REPORTES - {s}")
                            st.session_state.menu_main = "REPORTES"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "ENVIO DE MUESTRAS":
                                st.switch_page("pages/muestras.py")
                            else:
                                st.rerun()
        
            if permisos.get("FORMATOS", False):
                with st.expander("FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")):
                    opciones_for_posibles = ["SALIDA DE PT", "CHECK LIST AGC", "QR AGC", "PREGUIA PAQMEX", "RECOLECCION 3G", "RECOLECCION ONE", "CARTA RECLAMO", "COTIZACIONES"]
                    opciones_for = [s for s in opciones_for_posibles if permisos.get(s, False)]
                    for s in opciones_for:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_for_{s}2"):
                            registrar_acceso_github(usuario, f"FORMATOS - {s}")
                            st.session_state.menu_main = "FORMATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if permisos.get("CENTRO DE DATOS", False):
                with st.expander("CENTRO DE DATOS", expanded=(st.session_state.menu_main == "CENTRO DE DATOS")):
                    opciones_hub_posibles = ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "ESCANEAR QR", "HERRAMIENTAS"]
                    opciones_hub = [s for s in opciones_hub_posibles if permisos.get(s, False)]
                    for s in opciones_hub:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_hub_{s}2"):
                            registrar_acceso_github(usuario, f"CENTRO DE DATOS - {s}")
                            st.session_state.menu_main = "CENTRO DE DATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "ASIGNAR FLETERA":
                                st.switch_page("pages/facturacion_af.py")
                            elif s == "CARGAR DATOS":
                                st.switch_page("pages/cargardt.py")
                            elif s == "ETIQUETAS":
                                st.switch_page("pages/etiquetas.py")
                            elif s == "ESCANEAR QR":
                                st.switch_page("pages/qrup.py")
                            else:
                                st.rerun()
        
            if permisos.get("FINANZAS", False):
                with st.expander("FINANZAS", expanded=(st.session_state.menu_main == "FINANZAS")):
                    opciones_fin_posibles = ["WALLET", "CAJA CHICA", "GASTOS"]
                    opciones_fin = [s for s in opciones_fin_posibles if permisos.get(s, False)]
                    for s in opciones_fin:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_fin_{s}2"):
                            registrar_acceso_github(usuario, f"FINANZAS - {s}")
                            st.session_state.menu_main = "FINANZAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()

            if permisos.get("ENFOQUE", False):
                with st.expander("ENFOQUE", expanded=(st.session_state.get("menu_main") == "ENFOQUE")):
                    opciones_enf_posibles = ["MORENO", "VAZQUEZ", "MIGUEL"]
                    opciones_enf = [s for s in opciones_enf_posibles if permisos.get(s, False)]
                    for s in opciones_enf:
                        label = f"» {s}" if st.session_state.get("menu_sub") == s else s
                        if st.button(label, use_container_width=True, key=f"pop_enf_{s}2"):
                            registrar_acceso_github(usuario, f"ENFOQUE - {s}")
                            st.session_state.menu_main = "ENFOQUE"
                            st.session_state.menu_sub = s
                            st.rerun()
        
            if permisos.get("ACCESS CONTROL", False) or usuario.upper() == "RIGOBERTO":
                if st.button("ACCESS CONTROL", use_container_width=True, key="pop_access_ctrl2"):
                    registrar_acceso_github(usuario, "ACCESS CONTROL")
                    st.session_state.menu_main = "ACCESS CONTROL"
                    st.session_state.menu_sub = "SETTINGS"
                    st.switch_page("pages/accesscontrol.py")
        
            st.markdown("<hr style='margin: 4px 0; opacity: 0.1;'>", unsafe_allow_html=True)
            if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.autenticado = False
                st.session_state.splash_completado = False
                st.rerun()

    # ── RENDERIZADO DE RESULTADOS DE BÚSQUEDA ──────────────────────────────
    if st.session_state.busqueda_activa and st.session_state.resultado_busqueda is not None:
        resultados = st.session_state.resultado_busqueda
        total = len(resultados)
        tipo = st.session_state.get("tipo_resultado", "OPERACION")
        accent_color = "#00FFAA"
        inv_color = "#36b9cc"
        azul_premium = "#00D4FF"

        col_espacio, col_cerrar = st.columns([0.85, 0.15])
        with col_cerrar:
            if st.button("✕ CERRAR", key="btn_cerrar_top", use_container_width=True):
                st.session_state.busqueda_activa = False
                st.session_state.resultado_busqueda = None
                st.session_state.search_key_version += 1
                st.rerun()

        if tipo == "INVENTARIO":
            st.markdown(f"<style>.card-inv {{ transition: all 0.3s ease; cursor: pointer; }} .card-inv:hover {{ transform: translateX(8px); border-color: {inv_color} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(54, 185, 204, 0.1); }}</style>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:15px;'><div style='background:{inv_color};width:5px;height:20px;border-radius:2px;box-shadow:0 0 10px {inv_color};'></div><span style='color:white;font-size:14px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;'>EXISTENCIAS EN INVENTARIO <span style='color:{inv_color};'>({total})</span></span></div>", unsafe_allow_html=True)
            for _, i in resultados.iterrows():
                st.markdown(f"<div class='card-inv' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {inv_color};border-radius:10px;padding:10px 20px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CÓDIGO / SKU</span><br><b style='font-size:16px;color:{inv_color};letter-spacing:1px;'>{i.get('CODIGO','')}</b></div><div style='flex:3;padding-left:20px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>DESCRIPCIÓN</span><br><span style='font-size:13px;color:white;font-weight:600;line-height:1.2;'>{i.get('DESCRIPCION','')}</span></div><div style='flex:1;text-align:right;'><span style='background:{inv_color}15;color:{inv_color};padding:3px 8px;border-radius:4px;font-size:9px;font-weight:800;border:1px solid {inv_color}30;text-transform:uppercase;'>DISPONIBLE</span></div></div>", unsafe_allow_html=True)
        else:
            if total == 1:
                envio = resultados.iloc[0]
                entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
                f_entrega_val = envio["FECHA DE ENTREGA REAL"] if entregado_real else "PENDIENTE"
                trigger_val = str(envio.get("TRIGGER", "")).strip()
                tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]

                if tiene_guia:
                    n_guia = envio["NÚMERO DE GUÍA"]
                elif trigger_val == "Enviada":
                    n_guia = "GENERANDO GUÍA..."
                else:
                    n_guia = "EN ESPERA DE SURTIDO"

                f_promesa_dt = pd.to_datetime(envio.get("PROMESA DE ENTREGA"), dayfirst=True, errors="coerce")
                if pd.notnull(f_promesa_dt):
                    f_promesa_dt = f_promesa_dt.normalize()
                hoy = pd.Timestamp(datetime.now()).normalize()

                if not tiene_guia:
                    status_text, status_color = ("GENERANDO GUÍA", "#38bdf8") if trigger_val == "Enviada" else ("SURTIENDO", "#FFA500")
                elif not entregado_real:
                    status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if pd.isna(f_promesa_dt) or hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
                else:
                    f_entrega_dt = pd.to_datetime(envio.get("FECHA DE ENTREGA REAL"), dayfirst=True, errors="coerce")
                    if pd.notnull(f_entrega_dt):
                        f_entrega_dt = f_entrega_dt.normalize()
                    status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.isna(f_promesa_dt) or f_entrega_dt <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")

                tarjeta_unica_html = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 20px 25px; border-radius: 8px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;"><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #38bdf8; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #38bdf8;"></div><div style="font-size: 9px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;">ENVÍO</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('FECHA DE ENVÍO','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #38bdf8; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #a855f7; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #a855f7;"></div><div style="font-size: 9px; font-weight: 800; color: #a855f7; letter-spacing: 1px;">GUÍA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{n_guia if tiene_guia else 'EN PROCESO'}</div></div><div style="flex-grow: 1; height: 2px; background: #a855f7; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #eab308; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #eab308;"></div><div style="font-size: 9px; font-weight: 800; color: #eab308; letter-spacing: 1px;">PROMESA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('PROMESA DE ENTREGA','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #00FFAA; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: {status_color}; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px {status_color};"></div><div style="font-size: 9px; font-weight: 800; color: {status_color}; letter-spacing: 1px;">ENTREGA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{f_entrega_val}</div></div></div><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;"><div style="flex: 1.2; min-width: 200px;"><div style="color: {accent_color}; font-size: 16px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">{envio.get('FLETERA','N/A')}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">TALÓN / FOLIO</div><div style="color: {accent_color}; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{n_guia}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">REF / PEDIDO: <span style="color: white; font-size: 13px; font-weight: 700;">{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div></div><div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / CLIENTE</div><div style="color: white; font-weight: 800; font-size: 13px; text-transform: uppercase; line-height: 1.3; margin-top: 2px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div><div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 2px;">ID: {envio.get('NO CLIENTE','')} | {envio.get('DOMICILIO','')}</div><div style="font-size: 11px; color: {accent_color}; margin-top: 4px; font-weight: 600;">📍 GDL → {envio.get('DESTINO','N/A')}</div></div><div style="flex: 1.2; min-width: 150px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN CARGA</div><div style="color: white; font-weight: 700; font-size: 11px; margin-top: 2px;">BULTOS: <span style="color: {accent_color};">{envio.get('CANTIDAD DE CAJAS','0')}</span></div><div style="color: {accent_color}; font-weight: 800; font-size: 13px; margin-top: 2px;">$ {envio.get('COSTO DE LA GUÍA','0.00')}</div></div><div style="text-align: right; min-width: 130px;"><span style="background-color: {status_color}15; color: {status_color}; padding: 5px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; border: 1px solid {status_color}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">ESTATUS: {status_text}</span></div></div></div>"""
                st.markdown(tarjeta_unica_html, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'><div style='background: {azul_premium}; width: 5px; height: 22px; border-radius: 3px; box-shadow: 0 0 10px {azul_premium};'></div><span style='color: white; font-size: 15px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;'>MULTIPLE MATCHES DETECTED <span style='color: {azul_premium};'>({total})</span></span></div>", unsafe_allow_html=True)
                st.markdown(f"<style>.card-nexion {{ transition: all 0.3s ease !important; cursor: pointer; }} .card-nexion:hover {{ transform: translateX(10px); border-color: {azul_premium} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(0, 212, 255, 0.2); }}</style>", unsafe_allow_html=True)

                for _, d in resultados.iterrows():
                    status_text = d["COMENTARIOS"] if "COMENTARIOS" in d and pd.notna(d.get("COMENTARIOS")) else "OK"
                    st.markdown(f"<div class='card-nexion' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {azul_premium};border-radius:12px;padding:18px 25px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>PEDIDO / FACTURA</span><br><b style='font-size:18px;color:{azul_premium};letter-spacing:0.5px;'># {d.get('NÚMERO DE PEDIDO','')}</b><br><span style='font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;'>Envío: {d.get('FECHA DE ENVÍO','')}</span></div><div style='flex:2.5;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CLIENTE / DESTINO</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('NOMBRE DEL CLIENTE','')}</b><br><i style='font-size:11px;color:rgba(255,255,255,0.5);font-style:normal;font-weight:600;'>{d.get('DESTINO','')}</i></div><div style='flex:1.8;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>TRANSPORTE Y GUÍA</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('FLETERA', d.get('TRANSPORTE', 'LOGÍSTICA'))}</b><br><span style='font-size:12px;color:{azul_premium};font-weight:700;font-family:monospace;'>{d.get('NÚMERO DE GUÍA','')}</span></div><div style='flex:1.2;text-align:right;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>ESTATUS ENTREGA</span><br><b style='font-size:14px;color:{azul_premium};'>{d.get('FECHA DE ENTREGA REAL','')}</b><br><span style='font-size:10px;color:white;font-weight:800;text-transform:uppercase;opacity:0.8;'>{status_text}</span></div></div>", unsafe_allow_html=True)

        st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)

# ==========================================
# 5. INTERFAZ PRINCIPAL CON SISTEMA DE TABS
# ==========================================
def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True
    
    st.markdown("""
    <style>
        /* 2. Estilo corporativo para los botones personalizados */
        div.stButton > button,
        div.stButton > button:link,
        div.stButton > button:visited {
            background-color: #2B343B !important; 
            color: #FFFFFF !important;            
            border: 1px solid #2B343B !important; 
            border-radius: 5px !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            box-shadow: none !important;
        }
        
        div.stButton > button:hover,
        div.stButton > button:focus {
            background-color: #00A3A3 !important; 
            color: #FFFFFF !important;            
            border-color: #00A3A3 !important;
            box-shadow: none !important;
        }
        
        div.stButton > button:active {
            background-color: #00A3A3 !important;
            border-color: #00A3A3 !important;
            color: #FFFFFF !important;
        }
    </style>
""", unsafe_allow_html=True)
    
    # --- FUNCIONES DE GITHUB PARA EL CONTROL DE ESTATUS Y EDICIÓN ---
    GITHUB_REPO = "RH2026/nexion"
    GITHUB_FILE = "recolecciones_estatus.csv"
    BRANCH = "main"

    def cargar_estatus_github():
        try:
            url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{GITHUB_FILE}"
            token = st.secrets["GITHUB_TOKEN"]
            headers = {"Authorization": f"token {token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
                df.columns = df.columns.astype(str).str.strip()
                return df
            else:
                return pd.DataFrame(columns=["Folio", "Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total", "Estatus", "Observaciones"])
        except Exception:
            return pd.DataFrame(columns=["Folio", "Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total", "Estatus", "Observaciones"])

    def guardar_estatus_github(df_nuevo, mensaje="Actualizar estatus de recolecciones"):
        try:
            token = st.secrets["GITHUB_TOKEN"]
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            
            response_get = requests.get(url, headers=headers)
            sha = response_get.json().get("sha") if response_get.status_code == 200 else None

            csv_buffer = df_nuevo.to_csv(index=False, encoding="utf-8-sig")
            content_encoded = base64.b64encode(csv_buffer.encode("utf-8")).decode("utf-8")

            payload = {
                "message": mensaje,
                "content": content_encoded,
                "branch": BRANCH
            }
            if sha:
                payload["sha"] = sha

            response_put = requests.put(url, headers=headers, json=payload)
            if response_put.status_code in [200, 201]:
                return True
            else:
                st.error(f"Error al guardar en GitHub: {response_put.status_code} - {response_put.text}")
                return False
        except Exception as e:
            st.error(f"No se pudo guardar en GitHub: {e}")
            return False

    # --- DEFINICIÓN DE TABS ---
    tab1, tab2, tab3 = st.tabs(["Formato Solicitud", "Render de Estatus", "Edición y Actualización"])
    # --- TAB 1: EL FORMATO ORIGINAL DE TRESGUERRAS ---
    with tab1:
        
        @st.cache_data(ttl=60)
        def cargar_matriz_facturacion_completa():
            try:
                repo = "RH2026/nexion"
                filename = "clientes.csv"  # <-- Apunta directo a clientes.csv
                branch = "main"
                url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filename}"
                token = st.secrets["GITHUB_TOKEN"]
                headers = {"Authorization": f"token {token}"}
                
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
                    df.columns = [str(c).upper().strip() for c in df.columns]
                    return df
                else:
                    st.error(f"Error al descargar {filename} de GitHub (Código {response.status_code}).")
                    return pd.DataFrame()
            except Exception as e:
                st.error(f"No se pudo cargar la matriz de clientes: {e}")
                return pd.DataFrame()

        df_facturacion = cargar_matriz_facturacion_completa()
        registro = pd.Series(dtype=object)    

        if not df_facturacion.empty:
            df_facturacion.columns = [str(c).upper().strip() for c in df_facturacion.columns]
            
            # Búsqueda dinámica y segura de columnas clave
            col_factura = next((c for c in ["FACTURA", "FOLIO"] if c in df_facturacion.columns), df_facturacion.columns[0])
            col_cliente_num = next((c for c in ["NO CLIENTE", "CLIENTE", "NUMERO_CLIENTE"] if c in df_facturacion.columns), None)
            col_nombre_hotel = next((c for c in ["NOMBRE_EXTRAN", "NOMBRE", "CLIENTE_NOMBRE"] if c in df_facturacion.columns), None)
    
            # Forzar conversión limpia a string evitando .0 en números de cliente o facturas
            df_facturacion[col_factura] = df_facturacion[col_factura].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            if col_cliente_num:
                df_facturacion[col_cliente_num] = df_facturacion[col_cliente_num].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
            top_col1, top_col2, top_col3, top_col4 = st.columns(4)
            
            with top_col1:
                fecha_recoleccion_deseada = st.date_input("📅 Fecha Recolección", value=datetime.now(), key="tg_fecha_rec")
            fecha_rec_str = fecha_recoleccion_deseada.strftime("%d/%m/%Y")
    
            with top_col2:
                criterio_busqueda = st.selectbox("🔍 Buscar por:", ["Folio de Factura", "Número de Cliente"], key="tg_criterio_busq")
    
            with top_col3:
                if criterio_busqueda == "Folio de Factura":
                    facturas_disponibles = sorted(df_facturacion[col_factura].dropna().unique().tolist())
                    num_factura = st.selectbox("Selecciona Factura", facturas_disponibles, key="tg_sel_fact")
                    if num_factura:
                        match_df = df_facturacion[df_facturacion[col_factura] == str(num_factura)]
                        if not match_df.empty:
                            registro = match_df.iloc[0]
                else:
                    if col_cliente_num:
                        clientes_disponibles = sorted(df_facturacion[col_cliente_num].dropna().unique().tolist())
                        cliente_elegido = st.selectbox("Selecciona No. Cliente", clientes_disponibles, key="tg_sel_cte")
                        num_factura = st.text_input("✍️ Folio Nuevo (Asignar)", value="S/F", key="tg_txt_fact_nuevo")
                        
                        if cliente_elegido:
                            match_cte = df_facturacion[df_facturacion[col_cliente_num] == str(cliente_elegido)]
                            if not match_cte.empty:
                                registro = match_cte.iloc[0]
                    else:
                        st.warning("No se encontró la columna de Número de Cliente en la matriz.")
                        num_factura = st.text_input("✍️ Ingresa Folio Manual", key="tg_txt_fact")
    
            with top_col4:
                tipo_pago_tg = st.selectbox("💳 Condición de Pago", ["POR COBRAR (DESTINO)", "PAGADO (ORIGEN)", "CRÉDITO"], key="tg_tipo_pago")

            # Extracción segura de valores para evitar errores de tipo
            def_extran = str(registro.get(col_nombre_hotel, "")) if not registro.empty and col_nombre_hotel and pd.notna(registro.get(col_nombre_hotel)) else ""
            def_dom = str(registro.get("DOMICILIO", registro.get("CALLE", ""))) if not registro.empty and pd.notna(registro.get("DOMICILIO", registro.get("CALLE", ""))) else ""
            def_col = str(registro.get("COLONIA", "")) if not registro.empty and pd.notna(registro.get("COLONIA", "")) else ""
            def_cui = str(registro.get("CUIDAD", registro.get("CIUDAD", ""))) if not registro.empty and pd.notna(registro.get("CUIDAD", registro.get("CIUDAD", ""))) else ""
            def_cp = str(registro.get("CP", "")) if not registro.empty and pd.notna(registro.get("CP", "")) else ""
            def_cp = def_cp.replace('.0', '') if def_cp else ""
            def_est = str(registro.get("ESTADO", "")) if not registro.empty and pd.notna(registro.get("ESTADO", "")) else ""

            tel_val = ""
            if not registro.empty:
                for col_p in ["TELEFONO", "TEL", "TELÉFONO"]:
                    if col_p in registro and pd.notna(registro[col_p]):
                        tel_val = str(registro[col_p]).replace('.0', '').strip()
                        break

            st.markdown("---")

            def titulo_seccion(texto, color_fondo="#b71c1c"):
                st.markdown(f"""
                    <div style="background-color: {color_fondo}; padding: 8px; border-radius: 4px; text-align: center; color: white; font-weight: bold; font-size: 15px; margin-bottom: 10px;">
                        {texto}
                    </div>
                """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                titulo_seccion("REMITENTE - RECOLECCIÓN (PROVEEDOR)", color_fondo="#e65100")
                rem_cliente = st.text_input("Comercializadora / Proveedor", value=def_extran, key=f"rem_cli_{num_factura}")
                rem_calle = st.text_input("Calle y Número (Remitente)", value=def_dom, key=f"rem_call_{num_factura}")
                rc1, rc2 = st.columns(2)
                with rc1:
                    rem_colonia = st.text_input("Colonia (Remitente)", value=def_col, key=f"rem_col_{num_factura}")
                with rc2:
                    rem_cp = st.text_input("CP (Remitente)", value=def_cp, key=f"rem_cp_{num_factura}")
                rc3, rc4 = st.columns(2)
                with rc3:
                    rem_cui = st.text_input("Ciudad / Municipio", value=def_cui, key=f"rem_cui_{num_factura}")
                with rc4:
                    rem_estado = st.text_input("Estado", value=def_est, key=f"rem_est_{num_factura}")
                rc5, rc6 = st.columns(2)
                with rc5:
                    rem_contacto = st.text_input("Persona que entrega", value="", key=f"rem_cont_{num_factura}")
                with rc6:
                    rem_tel = st.text_input("Teléfono Remitente", value=tel_val, key=f"rem_tel_{num_factura}")

            with col2:
                titulo_seccion("DESTINATARIO - ENTREGA (JYPESA)", color_fondo="#4B6B94")
                dest_cliente = st.text_input("Cliente Destino", value="Jabones y productos Especializados", key=f"dest_cli_{num_factura}")
                dest_calle = st.text_input("Calle Destino", value="C. Cernícalo 155", key=f"dest_call_{num_factura}")
                dc1, dc2 = st.columns(2)
                with dc1:
                    dest_colonia = st.text_input("Colonia Destino", value="La Aurora", key=f"dest_col_{num_factura}")
                with dc2:
                    dest_cp = st.text_input("CP Destino", value="44460", key=f"dest_cp_{num_factura}")
                dc3, dc4 = st.columns(2)
                with dc3:
                    dest_cui = st.text_input("Ciudad Destino", value="Guadalajara", key=f"dest_cui_{num_factura}")
                with dc4:
                    dest_estado = st.text_input("Estado Destino", value="Jalisco", key=f"dest_est_{num_factura}")
                dc5, dc6 = st.columns(2)
                with dc5:
                    dest_contacto = st.text_input("Persona que recibe", value="Jazmin Castillo", key=f"dest_cont_{num_factura}")
                with dc6:
                    dest_tel = st.text_input("Teléfono Destino", value="33 3540 2939 Ext.123", key=f"dest_tel_{num_factura}")

            titulo_seccion("FACTURAR A (DATOS FISCALES JYPESA)", color_fondo="#37474f")
            fac_cliente = st.text_input("Facturar a Nombre de", value="JABONES Y PRODUCTOS ESPECIALIZADOS SA DE CV", key=f"fac_cli_{num_factura}")
            fac_domicilio = st.text_input("Domicilio Fiscal", value="Privada del Gallo No. 1525, Col. La Aurora C.P. 44460 Guadalajara, JAL México", key=f"fac_dom_{num_factura}")
            fac_rfc = st.text_input("RFC Facturación", value="JPE830408B35", key=f"fac_rfc_{num_factura}")

            # --- SECCIÓN DINÁMICA DE EMBARQUE ---
            st.markdown("---")
            titulo_seccion("📦 DETALLE DE EMBARQUE Y LÍNEAS DE CARGA", color_fondo="#e65100")

            if "lineas_embarque" not in st.session_state:
                st.session_state.lineas_embarque = [
                    {"cantidad": 1, "tipo": "TARIMA", "descripcion": "AMENIDADES", "largo": 1.20, "ancho": 1.20, "alto": 2.00, "peso": 800.0}
                ]

            for idx, linea in enumerate(st.session_state.lineas_embarque):
                st.markdown(f"**Renglón {idx + 1}**")
                lc1, lc2, lc3, lc4, lc5, lc6, lc7 = st.columns([1, 2, 2, 1, 1, 1, 1])
                with lc1:
                    linea["cantidad"] = st.number_input("Cant.", min_value=1, value=linea["cantidad"], key=f"cant_{idx}")
                with lc2:
                    linea["tipo"] = st.selectbox("Tipo Bulto", ["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"], index=["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"].index(linea["tipo"]) if linea["tipo"] in ["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"] else 0, key=f"tipo_{idx}")
                with lc3:
                    linea["descripcion"] = st.text_input("Descripción", value=linea["descripcion"], key=f"desc_{idx}")
                with lc4:
                    linea["largo"] = st.number_input("Largo (m)", value=float(linea["largo"]), key=f"larg_{idx}")
                with lc5:
                    linea["ancho"] = st.number_input("Ancho (m)", value=float(linea.get("ancho", 1.20)), key=f"anch_{idx}")
                with lc6:
                    linea["alto"] = st.number_input("Alto (m)", value=float(linea["alto"]), key=f"alt_{idx}")
                with lc7:
                    linea["peso"] = st.number_input("Peso (KG)", value=float(linea["peso"]), key=f"pes_{idx}")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("➕ Agregar otra línea de carga", key="btn_add_line"):
                    st.session_state.lineas_embarque.append({"cantidad": 1, "tipo": "CAJA", "descripcion": "MERCANCIA", "largo": 0.50, "ancho": 0.50, "alto": 0.50, "peso": 50.0})
                    st.rerun()
            with col_btn2:
                if len(st.session_state.lineas_embarque) > 1 and st.button("🗑️ Eliminar última línea", key="btn_del_line"):
                    st.session_state.lineas_embarque.pop()
                    st.rerun()

            total_peso_calc = sum(l["peso"] * l["cantidad"] for l in st.session_state.lineas_embarque)
            st.info(f"⚖️ **Peso Total Calculado:** {total_peso_calc:,.2f} KG")

            def generar_pdf_tresguerras_oficial():
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
                story = []
                
                fecha_actual = datetime.now().strftime("%d/%m/%Y")
                
                th_style = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=colors.white, alignment=1)
                cell_bold = ParagraphStyle("CB", fontName="Helvetica-Bold", fontSize=6, leading=7.5)
                cell_normal = ParagraphStyle("CN", fontName="Helvetica", fontSize=6, leading=7.5)
                cell_center = ParagraphStyle("CC", fontName="Helvetica", fontSize=6, leading=7.5, alignment=1)

                logo_io = obtener_logo_tresguerras()
                logo_elem = Image(logo_io, width=85, height=22) if logo_io else Paragraph("<b>TRESGUERRAS</b>", cell_center)
                
                header_table = Table([
                    [
                        logo_elem, 
                        Paragraph("<b>AUTOTRANSPORTES DE CARGA TRESGUERRAS<br/>SOLICITUD DE SERVICIO</b>", ParagraphStyle("HT", alignment=1, fontSize=8.5, fontName="Helvetica-Bold")), 
                        Paragraph(f"<b>FECHA SOLICITUD:</b> {fecha_actual}<br/><b>FOLIO:</b> {num_factura}", ParagraphStyle("H2", fontSize=6, alignment=1))
                    ],
                    ["", Paragraph("PAQUETERIA", ParagraphStyle("PAQ", alignment=1, fontSize=5.5, fontName="Helvetica-Bold")), ""]
                ], colWidths=[105, 382, 115])
                header_table.setStyle(TableStyle([
                    ("SPAN", (0,0), (0,1)),
                    ("SPAN", (2,0), (2,1)),
                    ("GRID", (0,0), (-1,-1), 1, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("ALIGN", (0,0), (0,0), "CENTER"),
                    ("BACKGROUND", (1,0), (1,0), colors.HexColor("#e0e0e0")),
                    ("BACKGROUND", (2,0), (2,0), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (1,1), (1,1), colors.HexColor("#f5f5f5")),
                ]))
                story.append(header_table)
                story.append(Spacer(1, 2))

                fechas_table = Table([
                    [Paragraph("<b>FECHA DE RECOLECCION:</b>", cell_bold), Paragraph(fecha_rec_str, cell_center), Paragraph("<b>FECHA SOLICITUD</b>", cell_bold), Paragraph(fecha_actual, cell_center)],
                    [Paragraph("<b>FECHA DE RECEPCION:</b>", cell_bold), "", Paragraph("<b>FOLIO</b>", cell_bold), ""]
                ], colWidths=[110, 150, 105, 237])
                fechas_table.setStyle(TableStyle([
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("BACKGROUND", (1,0), (1,0), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (3,0), (3,0), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (1,1), (1,1), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (3,1), (3,1), colors.HexColor("#fff59d")),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))
                story.append(fechas_table)
                story.append(Spacer(1, 2))

                rem_data = [
                    [Paragraph("REMITENTE - RECOLECCION", th_style), ""],
                    [Paragraph("CLIENTE:", cell_bold), Paragraph(rem_cliente, cell_bold)],
                    [Paragraph("CALLE Y NUMERO:", cell_bold), Paragraph(rem_calle, cell_normal)],
                    [Paragraph("COLONIA / CP:", cell_bold), Paragraph(f"{rem_colonia} - C.P. {rem_cp}", cell_normal)],
                    [Paragraph("CIUDAD / ESTADO:", cell_bold), Paragraph(f"{rem_cui}, {rem_estado}", cell_normal)],
                    [Paragraph("CONTACTO / TEL:", cell_bold), Paragraph(f"{rem_contacto} - {rem_tel}", cell_normal)],
                ]
                t_rem = Table(rem_data, colWidths=[90, 211])
                t_rem.setStyle(TableStyle([
                    ("SPAN", (0,0), (1,0)),
                    ("BACKGROUND", (0,0), (1,0), colors.HexColor("#e65100")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))

                dest_data = [
                    [Paragraph("DESTINATARIO - ENTREGA", th_style), ""],
                    [Paragraph("CLIENTE:", cell_bold), Paragraph(dest_cliente, cell_bold)],
                    [Paragraph("CALLE Y NUMERO:", cell_bold), Paragraph(dest_calle, cell_normal)],
                    [Paragraph("COLONIA / CP:", cell_bold), Paragraph(f"{dest_colonia} - C.P. {dest_cp}", cell_normal)],
                    [Paragraph("CIUDAD / ESTADO:", cell_bold), Paragraph(f"{dest_cui}, {dest_estado}", cell_normal)],
                    [Paragraph("CONTACTO / TEL:", cell_bold), Paragraph(f"{dest_contacto} - {dest_tel}", cell_normal)],
                ]
                t_dest = Table(dest_data, colWidths=[90, 211])
                t_dest.setStyle(TableStyle([
                    ("SPAN", (0,0), (1,0)),
                    ("BACKGROUND", (0,0), (1,0), colors.black),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))

                t_top = Table([[t_rem, t_dest]], colWidths=[301, 301])
                story.append(t_top)
                story.append(Spacer(1, 2))

                fac_data = [
                    [Paragraph("<b>FACTURAR A:</b>", th_style), "", ""],
                    [Paragraph(fac_cliente, cell_center), "", ""],
                    [Paragraph("<b>DOMICILIO:</b>", cell_bold), Paragraph("Cel. 33 19 75 31 22", cell_center), ""],
                    [Paragraph(f"Privada del Gallo No. 1525, Col. La Aurora C.P. 44460 Guadalajara, JAL México<br/>Tel.. 0152 (33) 35402939<br/>E-mail: rhernandez@jypesa.com", ParagraphStyle("FD", alignment=1, fontSize=6, fontName="Helvetica", leading=7.5)), "", ""],
                    [Paragraph("<b>RFC:</b>", cell_bold), Paragraph(f"RFC {fac_rfc}", cell_center), ""]
                ]
                t_fac = Table(fac_data, colWidths=[75, 427, 100])
                t_fac.setStyle(TableStyle([
                    ("SPAN", (0,0), (2,0)),
                    ("SPAN", (0,1), (2,1)),
                    ("SPAN", (1,2), (2,2)),
                    ("SPAN", (0,3), (2,3)),
                    ("SPAN", (1,4), (2,4)),
                    ("BACKGROUND", (0,0), (2,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (0,1), (2,1), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (0,2), (0,2), colors.HexColor("#b71c1c")),
                    ("TEXTCOLOR", (0,2), (0,2), colors.white),
                    ("BACKGROUND", (1,2), (2,2), colors.HexColor("#ffffff")),
                    ("BACKGROUND", (0,3), (2,3), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (0,4), (2,4), colors.HexColor("#b71c1c")),
                    ("TEXTCOLOR", (0,4), (2,4), colors.white),
                    ("BACKGROUND", (1,4), (2,4), colors.HexColor("#fff59d")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))
                story.append(t_fac)
                story.append(Spacer(1, 2))

                emb_headers = ["Cantidad", "TIPO DE BULTOS", "DESCRIPCION", "DIAMETRO", "ALTO", "CUBICAJE (m3)", "PESO (KG)"]
                emb_data = [
                    [Paragraph("<b>INFORMACION DE EMBARQUE</b>", th_style), "", "", Paragraph("<b>DIMENSIONES (mts)</b>", th_style), "", Paragraph("<b>VOLUMEN</b>", th_style), Paragraph("<b>PESO POR BULTO</b>", th_style)],
                    [Paragraph(h, th_style) for h in emb_headers]
                ]

                for l in st.session_state.lineas_embarque:
                    ancho_val = l.get('ancho', 1.20)
                    dim_str = f"{l['largo']} x {ancho_val} x {l['alto']}"
                    emb_data.append([
                        str(l["cantidad"]), 
                        str(l["tipo"]), 
                        str(l["descripcion"]), 
                        str(dim_str), 
                        "", 
                        "0", 
                        str(l["peso"])
                    ])

                filas_actuales = len(st.session_state.lineas_embarque)
                for _ in range(max(0, 6 - filas_actuales)):
                    emb_data.append(["", "", "", "", "", "0", ""])
                    
                emb_data.append(["", "", "", "", "", "0", f"{total_peso_calc:,.1f}"])

                t_emb = Table(emb_data, colWidths=[45, 65, 182, 95, 65, 80, 70])
                t_emb.setStyle(TableStyle([
                    ("SPAN", (0,0), (2,0)),
                    ("SPAN", (3,0), (4,0)),
                    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#b71c1c")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("ALIGN", (0,0), (-1,-1), "CENTER"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))
                story.append(t_emb)
                story.append(Spacer(1, 2))

                th_red = ParagraphStyle("THR", fontName="Helvetica-Bold", fontSize=6, leading=7, textColor=colors.white, alignment=1)
                th_green = ParagraphStyle("THG", fontName="Helvetica-Bold", fontSize=6, leading=7, textColor=colors.white, alignment=1)

                mid_table_data = [
                    [
                        Paragraph("<b>MERCANCIA ASEGURADA</b>", th_red), 
                        Paragraph("<b>REQUIERE ACUSE DE RECIBO</b>", th_red), 
                        Paragraph("<b>DESCRIPCION DEL ACUSE:</b>", th_red)
                    ],
                    [
                        Table([
                            [Paragraph("SI", cell_center), "", Paragraph("VALOR DECLARADO", cell_bold)],
                            [Paragraph("NO", cell_center), Paragraph("X", cell_center), Paragraph("POR CUENTA Y RIESGO", cell_bold)]
                        ], colWidths=[30, 30, 85], style=[
                            ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#fff59d")),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                        ]),
                        Table([
                            [Paragraph("SI", cell_center), Paragraph("X", cell_center), Paragraph("N<br/>O", cell_center)],
                            ["", "", ""]
                        ], colWidths=[30, 30, 25], style=[
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                        ]),
                        ""
                    ],
                    [
                        Paragraph("<b>TIPO DE PAGO MARCAR CON UNA X</b>", th_green), 
                        Paragraph("<b>MARCAR CON UNA X (EAD / OCURRE)</b>", th_green), 
                        Paragraph("<b>DOCUMENTOS QUE ANEXA</b>", th_red)
                    ],
                    [
                        Table([
                            [Paragraph("pagado (origen)", cell_center), Paragraph("por cobrar (destino)", cell_center), Paragraph("Credito", cell_center)],
                            ["", "", Paragraph("X", cell_center)]
                        ], colWidths=[48, 52, 45], style=[
                            ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                        ]),
                        Table([
                            [Paragraph("Recolección", cell_center), Paragraph("Recepción", cell_center), Paragraph("Entrega Domicilio", cell_center)],
                            [Paragraph("X", cell_center), "", Paragraph("X", cell_center)]
                        ], colWidths=[48, 45, 62], style=[
                            ("BACKGROUND", (0,1), (0,1), colors.HexColor("#fff59d")),
                            ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                        ]),
                        Table([
                            [Paragraph("factura", cell_center), Paragraph("orden de compra", cell_center), Paragraph("pedimento", cell_center), Paragraph("otro", cell_center)]
                        ], colWidths=[70, 70, 70, 62], style=[
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 4),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                        ])
                    ]
                ]

                t_mid = Table(mid_table_data, colWidths=[145, 155, 302])
                t_mid.setStyle(TableStyle([
                    ("SPAN", (2,1), (2,1)),
                    ("BACKGROUND", (0,0), (0,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (1,0), (1,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (2,0), (2,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (0,2), (0,2), colors.HexColor("#2e7d32")),
                    ("BACKGROUND", (1,2), (1,2), colors.HexColor("#2e7d32")),
                    ("BACKGROUND", (2,2), (2,2), colors.HexColor("#b71c1c")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("TOPPADDING", (0,0), (-1,-1), 1),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                ]))
                story.append(t_mid)
                story.append(Spacer(1, 2))

                t_final_block = Table([
                    [Paragraph("<b>DATOS DE QUIEN SOLICITA EL SERVICIO</b>", th_style), Paragraph("<b>OBSERVACIONES</b>", th_style)],
                    [
                        Table([
                            [Paragraph("<b>NOMBRE:</b>", cell_bold), Paragraph("RIGOBERTO HERNANDEZ", cell_center)],
                            [Paragraph("<b>EMPRESA:</b>", cell_bold), Paragraph("JYPESA", cell_center)],
                            [Paragraph("<b>E-MAIL:</b>", cell_bold), Paragraph("rhernandez@jypesa.com", cell_center)],
                            [Paragraph("<b>TELEFONO:</b>", cell_bold), Paragraph("Cel. 33 19 75 31 22", cell_center)]
                        ], colWidths=[70, 230], style=[
                            ("BACKGROUND", (1,0), (1,-1), colors.HexColor("#fff59d")),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1.5),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                        ]),
                        Paragraph("<b>LLAMAR AL REMITENTE UNA HORA ANTES DE LA RECOLECCIÓN,</b> SI NO QUIEREN ENTREGAR LLAMAR AL TELÉFONO<br/>Cel. 33 19 75 31 22 Rigoberto Hernandez", cell_normal)
                    ]
                ], colWidths=[300, 302])
                t_final_block.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (0,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (1,0), (1,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (1,1), (1,1), colors.HexColor("#fff59d")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("TOPPADDING", (0,0), (-1,-1), 2),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ]))
                story.append(t_final_block)

                doc.build(story)
                buffer.seek(0)
                return buffer

            st.markdown("---")
            col_gen1, col_gen2 = st.columns(2)
            with col_gen1:
                if st.button("Generar Orden de Recolección (Tresguerras Oficial)", use_container_width=True, key="btn_gen_pdf_tg"):
                    pdf_buf = generar_pdf_tresguerras_oficial()
                    st.success("¡Formato de Tresguerras generado correctamente!")
                    st.download_button(
                        label="📥 Descargar PDF Tresguerras Oficial",
                        data=pdf_buf,
                        file_name=f"Tresguerras_Oficial_{num_factura}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_pdf_tg_btn"
                    )
            with col_gen2:
                if st.button("Registrar Folio en Estatus GitHub", use_container_width=True, key="btn_guardar_gh_tab1"):
                    df_estatus_actual = cargar_estatus_github()
                    nuevo_registro = pd.DataFrame([{
                        "Folio": str(num_factura),
                        "Fecha_Recoleccion": fecha_rec_str,
                        "Cliente": str(dest_cliente),
                        "Proveedor": str(rem_cliente),
                        "Peso_Total": float(total_peso_calc),
                        "Estatus": "PENDIENTE DE RECOLECCION",
                        "Observaciones": "Creado desde solicitud Tresguerras"
                    }])
                    if not df_estatus_actual.empty and str(num_factura) in df_estatus_actual["Folio"].values:
                        df_estatus_actual.loc[df_estatus_actual["Folio"] == str(num_factura), ["Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total"]] = [fecha_rec_str, str(dest_cliente), str(rem_cliente), float(total_peso_calc)]
                        df_final = df_estatus_actual
                    else:
                        df_final = pd.concat([df_estatus_actual, nuevo_registro], ignore_index=True)
                    
                    if guardar_estatus_github(df_final, f"Registro de folio {num_factura}"):
                        st.success(f"¡Folio {num_factura} guardado/actualizado exitosamente en GitHub!")
        else:
            st.warning("No se encontraron datos en la matriz de facturación.")

    # --- TAB 2: RENDER DE ESTATUS ---
    # --- TAB 2: RENDER DE ESTATUS (NIVEL WAR ROOM) ---
    with tab2:
        
        df_estatus = cargar_estatus_github()

        if not df_estatus.empty:
            # Normalizar columnas a mayúsculas para evitar errores de Matriz
            df_estatus.columns = [str(c).upper().strip() for c in df_estatus.columns]

            # 1. FILTROS DE CABECERA PARA EL TABLERO
            with st.container():
                f_col1, f_col2 = st.columns([2, 2], vertical_alignment="bottom")
                
                with f_col1:
                    # Filtro por Estatus
                    opciones_estatus = ["TODOS"] + sorted(df_estatus["ESTATUS"].dropna().unique().tolist()) if "ESTATUS" in df_estatus.columns else ["TODOS"]
                    filtro_estatus_tab2 = st.selectbox("FILTRAR POR ESTATUS", options=opciones_estatus, key="sel_estatus_tab2")
                
                with f_col2:
                    # Filtro por Proveedor / Fletera
                    col_prov_key = "PROVEEDOR" if "PROVEEDOR" in df_estatus.columns else ("FLETERA" if "FLETERA" in df_estatus.columns else None)
                    if col_prov_key:
                        opciones_prov = ["TODOS"] + sorted(df_estatus[col_prov_key].dropna().unique().tolist())
                        filtro_prov_tab2 = st.selectbox("FILTRAR POR PROVEEDOR", options=opciones_prov, key="sel_prov_tab2")
                    else:
                        filtro_prov_tab2 = "TODOS"

            # 2. PROCESAMIENTO Y APLICACIÓN DE FILTROS
            df_render = df_estatus.copy()
            
            if filtro_estatus_tab2 != "TODOS":
                df_render = df_render[df_render["ESTATUS"] == filtro_estatus_tab2]
                
            if filtro_prov_tab2 != "TODOS" and col_prov_key:
                df_render = df_render[df_render[col_prov_key] == filtro_prov_tab2]

            # 3. TARJETAS DE MÉTRICAS SUPERIORES (KPIs)
            total_envios = len(df_estatus)
            filtrados_n = len(df_render)
            
            pendientes_n = len(df_estatus[df_estatus["ESTATUS"].str.upper().str.contains("PENDIENTE|PROCESO", na=False)]) if "ESTATUS" in df_estatus.columns else 0
            entregados_n = len(df_estatus[df_estatus["ESTATUS"].str.upper().str.contains("ENTREGADO", na=False)]) if "ESTATUS" in df_estatus.columns else 0
            peso_total_val = df_estatus["PESO_TOTAL"].sum() if "PESO_TOTAL" in df_estatus.columns else 0.0

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)

            with kpi1:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #38bdf8;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>TOTAL REGISTROS</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{total_envios} <span style='font-size: 10px; color: #38bdf8; font-weight: 700; text-transform: uppercase;'>FOLIOS</span></div>
                    </div>
                """, unsafe_allow_html=True)

            with kpi2:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #FDE047;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>PENDIENTES</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{pendientes_n} <span style='font-size: 10px; color: #FDE047; font-weight: 700; text-transform: uppercase;'>ACTIVOS</span></div>
                    </div>
                """, unsafe_allow_html=True)

            with kpi3:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #00FFAA;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>ENTREGADOS</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{entregados_n} <span style='font-size: 10px; color: #00FFAA; font-weight: 700; text-transform: uppercase;'>COMPLETOS</span></div>
                    </div>
                """, unsafe_allow_html=True)

            with kpi4:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #F97316;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>PESO ACUMULADO</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{peso_total_val:,.1f} <span style='font-size: 10px; color: #F97316; font-weight: 700; text-transform: uppercase;'>KG</span></div>
                    </div>
                """, unsafe_allow_html=True)

            # 4. PANEL DE VISUALIZACIÓN ESTILO WAR ROOM PARA EL RENDER
            st.markdown(f"<p style='font-size:11px; font-weight:700; letter-spacing:8px; color:#FFFFFF; text-transform:uppercase; text-align:center; margin-bottom:20px;'>DETALLE OPERATIVO DE GITHUB</p>", unsafe_allow_html=True)

            if not df_render.empty:
                data_render = df_render.to_dict('records')
                
                # HTML con tarjetas custom estilo War Room idénticas al bloque de alertas
                html_render_cards = f"""
                <div style="font-family: 'Inter', sans-serif; padding-right: 10px;">
                    <style>
                        body {{ background: transparent; margin: 0; padding: 0; }}
                        
                        /* ───────── SCROLLBAR AGC STYLE ───────── */
                        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ 
                            background: #3498db; 
                            border-radius: 10px; 
                            border: 2px solid #384A52; 
                        }}
                        ::-webkit-scrollbar-thumb:hover {{ 
                            background: #2ecc71; 
                            box-shadow: 0 0 10px rgba(46, 204, 113, 0.5); 
                        }}

                        .card-excepcion {{
                            background: #263238;
                            border: 1px solid rgba(56, 189, 248, 0.15);
                            border-left: 6px solid #38bdf8;
                            border-radius: 12px;
                            margin-bottom: 12px;
                            padding: 18px 25px;
                            display: flex;
                            flex-wrap: wrap;
                            gap: 15px;
                            justify-content: space-between;
                            align-items: center;
                            transition: all 0.3s ease;
                            width: 100%;
                            box-sizing: border-box;
                        }}
                        .card-excepcion:hover {{ 
                            border-color: #38bdf8; 
                            background: #2d3b42;
                            transform: translateX(5px);
                        }}
                        .badge-estatus {{
                            background: rgba(56, 189, 248, 0.1);
                            color: #38bdf8;
                            padding: 8px 14px;
                            border-radius: 8px;
                            font-weight: 800;
                            font-family: monospace;
                            font-size: 13px;
                            text-align: center;
                            border: 1px solid rgba(56, 189, 248, 0.3);
                        }}
                        .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }}
                        .factura-destacada {{ color: #FFFFFF; font-size: 18px; font-weight: 800; letter-spacing: 1px; font-family: monospace; }}
                        .info-main {{ color: #FFFFFF; font-size: 13px; font-weight: 700; }}
                        .info-sub {{ color: #94a3b8; font-size: 11px; }}
                    </style>
                    {"".join([f'''
                    <div class="card-excepcion">
                        <div style="flex: 1.5; min-width: 180px;">
                            <div class="label-mini">Folio / Factura</div>
                            <div class="factura-destacada">{item.get('FOLIO', 'N/A')}</div>
                            <div class="info-sub" style="margin-top:4px;">Fecha: {item.get('FECHA_RECOLECCION', 'N/A')}</div>
                        </div>

                        <div style="flex: 2; min-width: 220px; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                            <div class="label-mini">Cliente / Destino</div>
                            <div class="info-main">{str(item.get('CLIENTE', 'N/A'))[:40]}</div>
                            <div class="info-sub" style="color: #FFFFFF !important;">Proveedor: {str(item.get('PROVEEDOR', 'N/A'))[:35]}</div>
                        </div>

                        <div style="flex: 1; min-width: 120px; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                            <div class="label-mini">Peso Total</div>
                            <div class="info-main" style="color: #00FFAA;">{float(item.get('PESO_TOTAL', 0.0)):,.2f} KG</div>
                            <div class="info-sub">Observación registrada</div>
                        </div>

                        <div style="flex: 1.2; min-width: 160px; text-align: right;">
                            <div class="label-mini" style="text-align:center;">Estatus Actual</div>
                            <div class="badge-estatus">{item.get('ESTATUS', 'PENDIENTE')}</div>
                        </div>
                    </div>
                    ''' for item in data_render])}
                </div>
                """
                
                # Renderizamos con componentes de altura controlada y scroll pro
                components.html(html_render_cards, height=600, scrolling=True)
            else:
                st.markdown(f"""
                    <div style="background: rgba(56, 189, 248, 0.05); border: 1px dashed #38bdf8; border-radius: 10px; padding: 25px; text-align: center; margin-top: 20px;">
                        <p style="color: #38bdf8; font-size: 16px; margin: 0;"><b>SIN REGISTROS BAJO ESTE FILTRO</b></p>
                        <p style="color: #94a3b8; font-size: 12px; margin-top: 5px;">No se encontraron elementos que coincidan con los criterios seleccionados en el render.</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aún no hay registros de estatus guardados en GitHub para renderizar en este apartado.")

    # --- TAB 3: EDICIÓN Y ACTUALIZACIÓN ---
    with tab3:
        st.markdown("")
        df_estatus_edit = cargar_estatus_github()

        if not df_estatus_edit.empty:
            folios_list = df_estatus_edit["Folio"].astype(str).unique().tolist()
            folio_a_editar = st.selectbox("Selecciona el Folio a Modificar / Actualizar", folios_list, key="edit_folio_sel")

            if folio_a_editar:
                fila_actual = df_estatus_edit[df_estatus_edit["Folio"].astype(str) == str(folio_a_editar)].iloc[0]
                
                with st.form("form_edicion_estatus"):
                    st.markdown(f"**Editando Folio:** `{folio_a_editar}`")
                    
                    nuevo_estatus = st.selectbox(
                        "Estatus de la Recolección", 
                        ["PENDIENTE DE RECOLECCION", "EN RUTA", "ENTREGADO", "CANCELADO", "INCIDENCIA"],
                        index=["PENDIENTE DE RECOLECCION", "EN RUTA", "ENTREGADO", "CANCELADO", "INCIDENCIA"].index(fila_actual["Estatus"]) if fila_actual["Estatus"] in ["PENDIENTE DE RECOLECCION", "EN RUTA", "ENTREGADO", "CANCELADO", "INCIDENCIA"] else 0
                    )
                    nueva_obs = st.text_area("Observaciones / Notas de Entrega", value=str(fila_actual.get("Observaciones", "")))
                    nuevo_cliente = st.text_input("Cliente Destino", value=str(fila_actual.get("Cliente", "")))
                    nuevo_proveedor = st.text_input("Proveedor Remitente", value=str(fila_actual.get("Proveedor", "")))
                    nuevo_peso = st.number_input("Peso Total (KG)", value=float(fila_actual.get("Peso_Total", 0.0)))

                    btn_guardar_cambios = st.form_submit_button("💾 GUARDAR CAMBIOS")

                    if btn_guardar_cambios:
                        idx_match = df_estatus_edit[df_estatus_edit["Folio"].astype(str) == str(folio_a_editar)].index
                        df_estatus_edit.loc[idx_match, "Estatus"] = nuevo_estatus
                        df_estatus_edit.loc[idx_match, "Observaciones"] = nueva_obs
                        df_estatus_edit.loc[idx_match, "Cliente"] = nuevo_cliente
                        df_estatus_edit.loc[idx_match, "Proveedor"] = nuevo_proveedor
                        df_estatus_edit.loc[idx_match, "Peso_Total"] = nuevo_peso

                        if guardar_estatus_github(df_estatus_edit, f"Actualización de estatus para folio {folio_a_editar}"):
                            st.success(f"¡Cambios guardados correctamente en GitHub para el folio {folio_a_editar}!")
                            st.rerun()
        else:
            st.warning("No hay registros disponibles para editar en GitHub.")

if __name__ == "__main__":
    main()

# ── FOOTER FIJO ────────────────────────
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
