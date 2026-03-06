import os
import io
import re
import json
import time
import zipfile
import unicodedata
import requests
from io import StringIO, BytesIO
from datetime import datetime, date, timedelta
import base64
import altair as alt

import pandas as pd
import numpy as np  # Opcional, pero suele ir de la mano con pandas
import streamlit as st
import streamlit.components.v1 as components
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
import math

import pytz
from github import Github
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

import google.generativeai as genai


# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="JYPESA | Logistics", layout="wide", initial_sidebar_state="collapsed")

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

@st.cache_data
def cargar_matriz_nexion():
    url = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except:
        return None

df_matriz = cargar_matriz_nexion()

# ── LOGIN ──────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 0

# ── TEMA FIJO (MODO OSCURO FORZADO - ONIX AZULADO) ──────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "DASHBOARD"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"


vars_css = {
    "bg": "#384A52",           # Fondo profundo (Base)
    "card": "#2B343B",         # Azul grisáceo oscuro para celdas
    "text": "#FFFFFF",         # Blanco Perla Ultra Chic (Texto principal)
    "sub": "#FFFFFF",          # Gris Azulado Claro (Subtítulos/Secundario)
    "border": "#4B5D67",       # Contorno sutil para elevación
    "table_header": "#ffffff",
    "table_bg": "#2B343B",# Tono profundo para encabezados de tabla
    "logo": "n1.png"           # Tu archivo de imagen
}

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
    background-color: #00A3A3 !important; 
    color: #ffffff !important; 
    border-color: #00A3A3 !important; 
}}



/* 5. INPUTS - SOLUCIÓN DEFINITIVA PARA BORDES CORTADOS */

/* Atacamos al contenedor que envuelve el input */
div[data-baseweb="input"] {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    height: 35px !important; /* <--- AGREGA ESTO (Ajusta el número a tu gusto) */
    border-radius: 4px !important;
    transition: all 0.3s ease-in-out !important;
}}

/* Cuando el usuario hace clic (Focus) en el contenedor */
div[data-baseweb="input"]:focus-within {{
    border: 1px solid #00A0A8 !important;
    box-shadow: 0 0 0 1px #00A0A8 !important;
}}

/* Estilo del campo de texto real */
.stTextInput input {{ 
    background-color: transparent !important; /* Para que se vea el fondo del contenedor */
    color: {vars_css['text']} !important; 
    border: none !important; /* Quitamos el borde de aquí para que no choque */
    box-shadow: none !important; 
    height: 35px !important;
    line-height: 35px !important; /* <--- PARA CENTRAR EL TEXTO VERTICALMENTE */
    text-align: center !important; 
    letter-spacing: 2px; 
    outline: none !important;
}}

/* Eliminamos cualquier borde extra que Streamlit ponga por defecto */
div[data-baseweb="base-input"] {{
    border: none !important;
    background-color: transparent !important;
}}

/* Bajar tamaño de los nombres de los filtros (Labels) */
[data-testid="stWidgetLabel"] p {{
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    color: {vars_css['sub']} !important;
    font-weight: 600 !important;
}}

/* Cambiar el texto de ADENTRO de los selectores (lo seleccionado) */
div[data-baseweb="select"] div {{
    font-size: 12px !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}

/* Cambiar el texto de ADENTRO del input de fecha */
input[data-testid="stDateInputView"] {{
    font-size: 12px !important;
    color: {vars_css['text']} !important;
}}

/* --- NUEVO: Control de Placeholder (Escapado para f-string) --- */
.stTextInput input::placeholder {{
    font-size: 12px !important; 
    color: {vars_css['sub']} !important; 
    opacity: 0.7 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
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


/* ───────── RECUPERACIÓN DEL AZUL EN FILTROS (SIN TOCAR NADA MÁS) ───────── */

/* Chips seleccionadas – Multiselect */
div[data-baseweb="tag"] {{
    background-color: #718096 !important;
    color: #ffffff !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
}}

div[data-baseweb="tag"] span {{
    color: #ffffff !important;
}}

div[data-baseweb="tag"] svg {{
    fill: #ffffff !important;
}}

/* Valor seleccionado – Selectbox */

/* ───────── SELECTBOX / MULTISELECT (ESTILO COMPLETO) ───────── */

/* 1. Contenedor Principal: Control de altura y centrado base */
div[data-baseweb="select"] > div:first-child {{
    height: 35px !important; 
    min-height: 35px !important;
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    display: flex !important;
    align-items: center !important;
    padding: 0 10px !important;
}}

/* 2. Ajuste del texto (Placeholder y Seleccionado) */
/* Eliminamos el line-height: 1 que lo empujaba hacia arriba */
div[data-baseweb="select"] div[role="button"],
div[data-baseweb="select"] [aria-selected="true"] {{
    font-size: 10px !important; /* Subimos a 10px para mejor equilibrio visual */
    color: {vars_css['text']} !important;
    text-transform: uppercase !important;
    line-height: normal !important; 
    display: flex !important;
    align-items: center !important;
}}

/* 3. El Menú Desplegable */
div[data-baseweb="popover"] ul {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    padding: 0 !important;
}}

/* 4. Cada opción individual */
div[data-baseweb="popover"] li {{
    background-color: transparent !important;
    color: {vars_css['text']} !important;
    font-size: 11px !important;
    padding: 8px 12px !important;
    text-transform: uppercase !important;
    transition: background 0.2s ease !important;
}}

/* 5. Hover en las opciones */
div[data-baseweb="popover"] li:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
}}

/* 6. Focus y limpieza de resplandores */
div[data-baseweb="select"]:focus-within {{
    border-color: #718096 !important;
    box-shadow: none !important;
    outline: none !important;
}}

/* Ajuste para el icono de la flecha (centrado vertical) */
div[data-baseweb="select"] svg {{
    fill: {vars_css['text']} !important;
    margin-top: auto !important;
    margin-bottom: auto !important;
}}

div[data-baseweb="select"] > div {{
    background-color: rgba(113, 128, 150, 0.15) !important;
    border: 1px solid #718096 !important;
}}

/* Focus - Sin color azul, mantiene el estilo neutro */
div[data-baseweb="select"]:focus-within {{
    border-color: #718096 !important; /* Mantiene el gris slate */
    box-shadow: none !important;      /* Elimina cualquier resplandor azul */
    outline: none !important;
}}

/* Eliminar el azul de fondo de la pestaña seleccionada */
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    border: none !important;
    color: {vars_css['sub']} !important; /* Texto grisáceo para los no seleccionados */
    font-weight: 400 !important;
    transition: all 0.3s ease !important;
}}

/* Estilo para la pestaña cuando está activa (seleccionada) */
div[data-baseweb="tab-list"] button[aria-selected="true"] {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
}}

div[data-baseweb="tab-list"] button:focus, 
div[data-baseweb="tab-list"] button:active {{
    outline: none !important;
    box-shadow: none !important;
}}

div[data-baseweb="tab-list"] button {{
    background-color: transparent !important;
    color: {vars_css['sub']} !important;
    border: none !important;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: #00FFAA !important; 
}}

/* ───────── POPOVER ESTILO PERSONALIZADO ───────── */

div[data-baseweb="layer"] div[data-baseweb="popover"] > div {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 6px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
}}

div[data-baseweb="popover"] {{
    color: {vars_css['text']} !important;
}}

button[kind="secondary"] {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
}}

button[kind="secondary"]:hover {{
    background-color: #617F8D !important;   /* un poco más claro que tu card */
    color: {vars_css['text']} !important;
    border-color: #617F8D !important;
}}

button[kind="secondary"] {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;

    height: 35px !important;
    min-height: 32px !important;
    padding: 0 12px !important;
    font-size: 11px !important;
    line-height: 30px !important;
}}

/* --- WIDGET DE RUTA PREMIUM (Optimizado para f-string) --- */
.kpi-ruta-container {{
    display: flex;
    justify-content: center;
    padding: 10px 0;
    font-family: 'Inter', sans-serif;
}}

.kpi-ruta-card {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 12px !important;
    padding: 30px !important;
    width: 100%;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2) !important;
}}

/* Línea de acento superior */
.kpi-ruta-card::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #00FFAA, #00A3A3);
}}

.kpi-tag {{
    font-size: 16px !important;
    letter-spacing: 3px;
    color: #00FFAA;
    font-weight: 500;
    text-transform: uppercase;
    opacity: 0.9;
}}

.kpi-route-flow {{
    margin: 20px 0;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
}}

.city {{
    font-size: 20px !important;
    font-weight: 600;
    color: {vars_css['text']};
    letter-spacing: 1px;
}}

.arrow {{
    color: #00FFAA;
    font-size: 34px;
    font-weight: bold;
}}

.kpi-value {{
    font-size: 28px !important;
    font-weight: 900;
    color: {vars_css['text']};
    margin: 5px 0;
    line-height: 1;
    text-shadow: 0 0 20px rgba(0,255,170,0.2);
}}

.kpi-value small {{
    font-size: 18px !important;
    color: {vars_css['sub']};
    letter-spacing: 2px;
    font-weight: 400;
}}

.kpi-subtext {{
    font-size: 16px !important;
    color: {vars_css['sub']};
    margin-top: 15px;
    line-height: 1.4;
}}

.kpi-subtext b {{
    color: #00FFAA;
}}

/* CLASE PARA TÍTULOS DE SECCIÓN DE DATOS */
.data-section-header {{
    font-size: 13px !important;
    letter-spacing: 3px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    color: {vars_css['sub']} !important;
    margin-bottom: 15px !important;
    margin-top: 25px !important;
    border-left: 3px solid #00FFAA; /* Una pequeña línea de acento como tus cards */
    padding-left: 10px !important;
}}

/* ───────── REFINAMIENTO GENERAL DEL POPOVER ───────── */

/* 1. Achicar el texto de los botones dentro del Popover */
div[data-baseweb="popover"] button {{
    font-size: 12px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}}

/* 2. Achicar el texto de los Expanders dentro del Popover (Navegación) */
div[data-baseweb="popover"] .st-expanderHeader p {{
    font-size: 12px !important;
    letter-spacing: 1.5px !important;
    font-weight: 600 !important;
}}

/* 3. Achicar cualquier texto simple (p, span) dentro del Popover */
div[data-baseweb="popover"] p, 
div[data-baseweb="popover"] span {{
    font-size: 12px !important;
    letter-spacing: 1px !important;
}}

/* 4. El botón de Logout (tipo Primary) lo hacemos aún más discreto */
div[data-baseweb="popover"] button[kind="primary"] {{
    font-size: 12px !important;
    height: 26px !important;
    min-height: 26px !important;
    line-height: 26px !important;
    background-color: transparent !important;
    border: 1px solid #ff4b4b !important; /* Un rojo sutil para identificar salida */
    color: #ff4b4b !important;
}}

div[data-baseweb="popover"] button[kind="primary"]:hover {{
    background-color: #ff4b4b !important;
    color: white !important;
}}

#CSS para multiselect----------------
/* 1. Altura forzada del contenedor del Multiselect */
div[data-baseweb="multiselect"] > div:first-child {{
    min-height: 35px !important;
    height: 35px !important;
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    align-items: center !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}}

/* 2. ELIMINAR EL PADDING DEL CONTENEDOR DE VALORES */
/* Aquí es donde Streamlit mete un padding de 8px que rompe todo */
div[data-baseweb="multiselect"] [data-testid="stMultiSelectFloatingValue"] {{
    padding-top: 0px !important;
    padding-bottom: 0px !important;
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    display: flex !important;
    align-items: center !important;
    height: 33px !important; /* Un pelín menos que el padre para el borde */
}}

/* 3. Ajuste de las "Pastillas" (Tags) si ya seleccionaste algo */
div[data-baseweb="multiselect"] [role="button"] {{
    height: 22px !important; /* Pastillas más pequeñas */
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    font-size: 10px !important;
    background-color: #00A3A3 !important; /* Color Aqua de Nexion */
    color: white !important;
}}

/* 4. El texto "Choose options" (Placeholder) */
div[data-baseweb="multiselect"] input::placeholder {{
    font-size: 10px !important;
    text-transform: uppercase !important;
    vertical-align: middle !important;
}}

/* 5. El Input invisible que empuja todo */
div[data-baseweb="multiselect"] input {{
    height: 33px !important;
    line-height: 33px !important;
    margin: 0 !important;
    padding: 0 !important;
}}

/* 6. Quitar el botón de "X" (Clear all) que a veces desalinea */
div[data-baseweb="multiselect"] [aria-label="Clear all"] {{
    height: 20px !important;
    align-self: center !important;
}}


</style>
""", unsafe_allow_html=True)


# ── DEFINICIÓN DE INTERFAZ DE LOGIN ────────────────────
def login_screen():
    # Ajustamos las proporciones para la columna central
    _, col, _ = st.columns([2, 2, 2]) 
    
    with col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>SYSTEM ACCESS REQUIRED</h3>", unsafe_allow_html=True)
        
        # Creamos el formulario. El 'clear_on_submit' puede ser False.
        with st.form("login_form", clear_on_submit=False):
            user_input = st.text_input("OPERATOR ID", placeholder="Introduce tu usuario")
            pass_input = st.text_input("ACCESS KEY", type="password", placeholder="••••••••")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            # Cambiamos st.button por st.form_submit_button
            submit_button = st.form_submit_button("VERIFY IDENTITY", use_container_width=True)
            
            if submit_button:
                lista_usuarios = st.secrets.get("usuarios", {})
                
                # VALIDACIÓN EXITOSA               
                # 1. Diccionario para convertir Operator ID en Nombre Real
                nombres_reales = {
                    "Rigoberto": "Rigoberto Hernández",
                    "AGomez": "Ale Gomez",
                    "JMoreno": "Jesus Moreno",
                    "Cynthia": "Cynthia Ornelas",
                    "Brenda": "Brenda Pizano",
                    "Fialko": "Fialko"
                }
                
                # 2. Diccionario de géneros (F = Femenino, M = Masculino)
                # Esto hará que el saludo sea dinámico
                generos = {
                    "Rigoberto": "M",
                    "AGomez": "F",
                    "JMoreno": "M",
                    "Cynthia": "F",
                    "Brenda": "F",
                    "Fialko": "M"
                }
                
                # --- VALIDACIÓN EXITOSA ---
                if user_input in lista_usuarios and str(lista_usuarios[user_input]) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = user_input
                    
                    # Buscamos el nombre completo
                    nombre_completo = nombres_reales.get(user_input, user_input)
                    st.session_state.nombre_completo = nombre_completo 
                    
                    # --- LÓGICA DE SALUDO DINÁMICO ---
                    gen = generos.get(user_input, "M")
                    saludo = "BIENVENIDA" if gen == "F" else "BIENVENIDO"
                    
                    # --- REDIRECCIÓN SEGÚN ROL ---
                    # Si es Ventas, lo mandamos directo a Muestras
                    if user_input.upper() == "VENTAS":
                        st.session_state.menu_main = "REPORTES"
                        st.session_state.menu_sub = "ENVIO DE MUESTRAS"
                    else:
                        # Para ti y los demás, el Dashboard de siempre
                        st.session_state.menu_main = "DASHBOARD"
                        st.session_state.menu_sub = "GENERAL"
                    
                    # Mostramos el mensaje personalizado
                    st.success(f"¡{saludo}!, {nombre_completo.upper()}") 
                    
                    # Pausa estética y recarga de la app
                    time.sleep(1) 
                    st.rerun()
                
                # MANEJO DEL ERROR
                else:
                    st.error("ERROR: ACCESS DENIED. INVALID CREDENTIALS.")
                    
# ── FLUJO DE CONTROL (SPLASH -> LOGIN -> APP) ──────────

# 1. ¿Falta mostrar el Splash?
if not st.session_state.splash_completado:
    # Creamos el contenedor vacío una sola vez
    p = st.empty()
    
    mensajes = ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]
    
    for m in mensajes:
        # IMPORTANTE: El 'with p.container()' debe estar DENTRO del for
        # Esto limpia el contenido anterior y pone el nuevo
        with p.container():
            st.markdown(f"""
            <div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:80px;height:80px;border:2px solid {vars_css['border']}; border-top:2px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
            </style>
            """, unsafe_allow_html=True)
            # Aumentamos un pelín el tiempo para que el ojo humano alcance a leer
            time.sleep(0.6) 
            
    # Al salir del bucle, limpiamos el espacio por completo
    p.empty()
    st.session_state.splash_completado = True
    st.rerun()

# 2. ¿Splash listo pero no se ha loggeado?
elif not st.session_state.autenticado:
    login_screen()

# 3. ¿Todo listo? Mostrar NEXION CORE
else:
    # ── HEADER CON 4 COLUMNAS (BÚSQUEDA OPTIMIZADA) ───────────────────────────
    header_zone = st.container()
    with header_zone:
        # c1: Logo | c2: Título | c3: Búsqueda (Reducida) | c4: Popover (Ampliada)
        c1, c2, c3, c4 = st.columns([1.5, 3.5, 0.9, 0.9], vertical_alignment="center")
        
        with c1:
            try:
                st.image(vars_css["logo"], width=180)
            except:
                st.write("**NEXION**")
    
        with c2:
            # RUTA DINÁMICA
            if st.session_state.menu_sub != "GENERAL":
                ruta = f"{st.session_state.menu_main} <span style='color:{vars_css['sub']}; opacity:0.4; margin: 0 15px;'>|</span> {st.session_state.menu_sub}"
            else:
                ruta = st.session_state.menu_main
            
            st.markdown(f"""
                <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
                    <p style='font-size: 13px; letter-spacing: 8px; color: {vars_css['sub']}; margin: 0; font-weight: 500; text-transform: uppercase; text-align: center;'>
                        {ruta}
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
        with c3:
            # Generamos una key única basada en la versión actual para el input
            key_actual = f"main_search_v{st.session_state.search_key_version}"
            
            query = st.text_input(
                "Buscar", 
                placeholder="🔍 Buscar...", 
                label_visibility="collapsed", 
                key=key_actual
            )
            
            if query:
                # ── FUERZA LECTURA DE DATOS MÁS RECIENTES (MATRIZ) ──
                url_raw = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
                try:
                    # Cargamos directamente de la URL para evitar datos viejos en caché
                    df_matriz_fresco = pd.read_csv(url_raw)
                except Exception:
                    df_matriz_fresco = df_matriz # Si falla, vuelve al anterior por seguridad

                # 1. BÚSQUEDA EN MATRIZ DE OPERACIONES (df_matriz_fresco)
                res_ops = pd.DataFrame()
                if df_matriz_fresco is not None:
                    res_ops = df_matriz_fresco[
                        (df_matriz_fresco['NÚMERO DE GUÍA'].astype(str).str.contains(query, case=False, na=False)) | 
                        (df_matriz_fresco['NÚMERO DE PEDIDO'].astype(str).str.contains(query, case=False, na=False)) |
                        (df_matriz_fresco['NO CLIENTE'].astype(str).str.contains(query, case=False, na=False)) |
                        (df_matriz_fresco['NOMBRE DEL CLIENTE'].astype(str).str.contains(query, case=False, na=False))
                    ]
                
                # 2. BÚSQUEDA EN INVENTARIO (inventario.csv)
                res_inv = pd.DataFrame()
                try:
                    df_inv_temp = pd.read_csv("inventario.csv")
                    res_inv = df_inv_temp[
                        (df_inv_temp['CODIGO'].astype(str).str.contains(query, case=False, na=False)) |
                        (df_inv_temp['DESCRIPCION'].astype(str).str.contains(query, case=False, na=False))
                    ]
                except Exception:
                    pass
        
                # Lógica de asignación de resultados
                if not res_ops.empty:
                    st.session_state.busqueda_activa = True
                    st.session_state.tipo_resultado = "OPERACION"
                    st.session_state.resultado_busqueda = res_ops
                elif not res_inv.empty:
                    st.session_state.busqueda_activa = True
                    st.session_state.tipo_resultado = "INVENTARIO"
                    st.session_state.resultado_busqueda = res_inv
                else:
                    st.session_state.busqueda_activa = False
                    st.toast("No se encontró ningún registro", icon="🔍")
        
        with c4:
            # --- BOTÓN POPOVER (NAVEGACIÓN + PERFIL) ---
            with st.popover("☰ NAVEGACIÓN", use_container_width=True):
            
                # 1. IDENTIFICACIÓN DE USUARIO
                usuario = st.session_state.get("usuario_activo", "GUEST")
                
                # Definimos los roles
                es_admin = (usuario.upper() == "RIGOBERTO")
                es_ventas = (usuario.upper() == "VENTAS") # <--- Nueva validación para Ventas
                
                nombre_display = st.session_state.get("nombre_completo", "OPERADOR DESCONOCIDO")
                
                st.markdown(f"""
                    <div style='background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin-bottom: 15px; border-left: 3px solid {vars_css['text']};'>
                        <p style='color:#f6c23e; font-size:9px; font-weight:500; margin:0; letter-spacing:1px;'>OPERATOR ACTIVE</p>
                        <p style='color:{vars_css['text']}; font-size:14px; font-weight:500; margin:0;'>{nombre_display.upper()}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<p style='color:#f0f0f0; font-size:6px; font-weight:400; margin-bottom:10px; letter-spacing:1px;'>MENÚ PRINCIPAL</p>", unsafe_allow_html=True)
                
                # 2. BOTONES DE NAVEGACIÓN (Restricciones dinámicas)
            
                # DASHBOARD: Solo lo ve el Admin o usuarios que NO sean Ventas
                if not es_ventas:
                    if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                        st.session_state.menu_main = "DASHBOARD"
                        st.session_state.menu_sub = "GENERAL"
                        st.session_state.busqueda_activa = False
                        st.rerun()
            
                # SEGUIMIENTO: Se oculta completamente para Ventas
                if not es_ventas:
                    with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                        opciones_seg = ["ALERTAS", "GANTT", "QUEJAS"] if es_admin else ["ALERTAS"]
                        for s in opciones_seg:
                            label = f"» {s}" if st.session_state.menu_sub == s else s
                            if st.button(label, use_container_width=True, key=f"pop_sub_{s}"):
                                st.session_state.menu_main = "SEGUIMIENTO"
                                st.session_state.menu_sub = s
                                st.session_state.busqueda_activa = False
                                st.rerun()
            
                # REPORTES: Ventas solo puede ver "ENVIO DE MUESTRAS"
                with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                    if es_admin:
                        opciones_rep = ["APQ", "% LOGISTICO", "ENVIOS ESPECIALES", "ENVIO DE MUESTRAS"]
                    elif es_ventas:
                        opciones_rep = ["ENVIO DE MUESTRAS"] # <--- Filtro estricto para Ventas
                    else:
                        opciones_rep = ["ENVIO DE MUESTRAS"] # Otros operadores
                        
                    for s in opciones_rep:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_rep_{s}"):
                            st.session_state.menu_main = "REPORTES"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
            
                # FORMATOS: Se oculta completamente para Ventas
                if not es_ventas:
                    with st.expander("FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")):
                        opciones_for = ["SALIDA DE PT", "CONTRARRECIBOS", "PROFORMA"]
                        for s in opciones_for:
                            label = f"» {s}" if st.session_state.menu_sub == s else s
                            if st.button(label, use_container_width=True, key=f"pop_for_{s}"):
                                st.session_state.menu_main = "FORMATOS"
                                st.session_state.menu_sub = s
                                st.session_state.busqueda_activa = False
                                st.rerun()
            
                # HUB LOG: Se oculta completamente para Ventas
                if not es_ventas:
                    with st.expander("HUB LOG", expanded=(st.session_state.menu_main == "HUB LOG")):
                        for s in ["SMART ROUTING", "DATA MANAGEMENT", "ORDER STAGING"]:
                            label = f"» {s}" if st.session_state.menu_sub == s else s
                            if st.button(label, use_container_width=True, key=f"pop_hub_{s}"):
                                st.session_state.menu_main = "HUB LOG"
                                st.session_state.menu_sub = s
                                st.session_state.busqueda_activa = False
                                st.rerun()
            
                # 3. SECCIÓN DE CIERRE DE SESIÓN
                st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)
                if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.session_state.autenticado = False
                    st.session_state.splash_completado = False
                    st.rerun()
                    
        # ── RENDERIZADO DE CONSULTA ──────────────────────────────────────────────────
        if st.session_state.busqueda_activa and st.session_state.resultado_busqueda is not None:
            resultados = st.session_state.resultado_busqueda
            total = len(resultados)
            tipo = st.session_state.get("tipo_resultado", "OPERACION")
            accent_color = "#1cc88a"
            inv_color = "#36b9cc" 
        
            # Botón Cerrar discreto
            col_espacio, col_cerrar = st.columns([0.85, 0.15])
            with col_cerrar:
                if st.button("✕ CERRAR", key="btn_cerrar_top", use_container_width=True):
                    st.session_state.busqueda_activa = False
                    st.session_state.resultado_busqueda = None
                    st.session_state.search_key_version += 1
                    st.rerun()
        
            if tipo == "INVENTARIO":
                st.markdown(f"<p style='color:{inv_color}; font-size:14px; font-weight:800; margin-bottom:10px; letter-spacing:1px;'>EXISTENCIAS EN INVENTARIO ({total})</p>", unsafe_allow_html=True)
                for index, i in resultados.iterrows():
                    st.markdown(f"""
                        <div style="background: rgba(54,185,204,0.07); border-left: 4px solid {inv_color}; padding: 12px 15px; margin-bottom: 8px; border-radius: 4px;">
                            <span style="color:{inv_color}; font-size:9px; font-weight:900; display:block; letter-spacing:1px;">CÓDIGO / SKU</span>
                            <span style="font-size:16px; font-weight:bold; color:white;">{i['CODIGO']}</span>
                            <div style="margin-top: 5px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 5px;">
                                <span style="font-size:13px; color:#E0E0E0;">{i['DESCRIPCION']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        
            else: 
                if total == 1:
                    d = resultados.iloc[0]
                    st.markdown(f"""
                        <div class="kpi-ruta-container">
                            <div class="kpi-ruta-card" style="background: rgba(255,255,255,0.05); border-top: 4px solid {accent_color}; position: relative; padding: 20px; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                    <span style="color: {accent_color}; font-weight: 800; font-size: 14px; letter-spacing: 1px;">DETALLES DE OPERACIÓN</span>
                                    <div style="display: flex; align-items: baseline; gap: 8px;">
                                        <span style="font-size:16px; font-weight:600; color: white; opacity: 0.9;">FACTURA:</span>
                                        <span style="color:{accent_color}; font-weight:800; font-size:22px;">{d['NÚMERO DE PEDIDO']}</span>
                                    </div>
                                </div>
                                <div class="kpi-route-flow" style="margin-bottom: 25px; display: flex; align-items: center;">
                                    <div class="city" style="color: white; font-weight:bold;">GDL</div>
                                    <div class="arrow" style="color: {accent_color}; margin: 0 15px;">→</div>
                                    <div class="city" style="color: white; font-weight:bold;">{d['DESTINO']}</div>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; text-align: left;">
                                    <div>
                                        <p style="color:{accent_color}; font-weight:800; font-size:10px; margin-bottom:5px; border-left: 2px solid {accent_color}; padding-left: 8px;">CLIENTE</p>
                                        <p style="font-size:14px; margin:0; color:white;"><b>{d['NOMBRE DEL CLIENTE']}</b></p>
                                        <p style="font-size:11px; color:#E0E0E0; margin-bottom:2px;">ID: {d['NO CLIENTE']}</p>
                                        <p style="font-size:11px; color:#E0E0E0; opacity:0.9;">{d['DOMICILIO']}</p>
                                    </div>
                                    <div>
                                        <p style="color:{accent_color}; font-weight:800; font-size:10px; margin-bottom:5px; border-left: 2px solid {accent_color}; padding-left: 8px;">LOGÍSTICA</p>
                                        <p style="font-size:12px; margin:0; color:white;">GUÍA: <b>{d['NÚMERO DE GUÍA']}</b></p>
                                        <p style="font-size:12px; margin:0; color:white;">FLETERA: <b>{d['FLETERA']}</b></p>
                                        <p style="font-size:12px; margin:0; color:white;">COSTO: <b>${d['COSTO DE LA GUÍA']}</b></p>
                                    </div>
                                    <div>
                                        <p style="color:{accent_color}; font-weight:800; font-size:10px; margin-bottom:5px; border-left: 2px solid {accent_color}; padding-left: 8px;">TIEMPOS</p>
                                        <p style="font-size:12px; margin:0; color:white;">ENVÍO: {d['FECHA DE ENVÍO']}</p>
                                        <p style="font-size:12px; margin:0; color:{accent_color}; font-weight:bold;">PROMESA: {d['PROMESA DE ENTREGA']}</p>
                                    </div>
                                    <div>
                                        <p style="color:{accent_color}; font-weight:800; font-size:10px; margin-bottom:5px; border-left: 2px solid {accent_color}; padding-left: 8px;">CARGA</p>
                                        <p style="font-size:12px; margin:0; color:white;">CAJAS: {d['CANTIDAD DE CAJAS']}</p>
                                        <p style="font-size:11px; color:#E0E0E0;">STATUS: {d['COMENTARIOS'] if pd.notna(d['COMENTARIOS']) else 'SIN OBSERVACIONES'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color:{accent_color}; font-size:14px; font-weight:800; margin-bottom:10px; letter-spacing:1px;'>MULTIPLE MATCHES DETECTED ({total})</p>", unsafe_allow_html=True)
                    for index, d in resultados.iterrows():
                        status_text = d['COMENTARIOS'] if pd.notna(d['COMENTARIOS']) else 'OK'
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.07); border-left: 4px solid {accent_color}; padding: 12px 15px; margin-bottom: 8px; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div style="flex: 1;">
                                        <span style="color:{accent_color}; font-size:9px; font-weight:900; display:block; letter-spacing:1px;">PEDIDO</span>
                                        <span style="font-size:15px; font-weight:bold; color:white;">{d['NÚMERO DE PEDIDO']}</span>
                                    </div>
                                    <div style="flex: 2;">
                                        <span style="color:{accent_color}; font-size:9px; font-weight:900; display:block; letter-spacing:1px;">CLIENTE ({d['NO CLIENTE']})</span>
                                        <span style="font-size:13px; color:white; font-weight:600;">{d['NOMBRE DEL CLIENTE']}</span>
                                    </div>
                                    <div style="flex: 1; text-align: right;">
                                        <span style="color:{accent_color}; font-size:9px; font-weight:900; display:block; letter-spacing:1px;">GUÍA</span>
                                        <span style="font-size:13px; color:#FFFFFF; font-weight:bold;">{d['NÚMERO DE GUÍA']}</span>
                                    </div>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 6px;">
                                    <span style="font-size:11px; color:#FFFFFF;">📍 <b>{d['DESTINO']}</b></span>
                                    <span style="font-size:11px; color:#FFFFFF;">📅 ENVÍO: <b>{d['FECHA DE ENVÍO']}</b></span>
                                    <div style="text-align: right;">
                                        <span style="font-size:11px; color:{accent_color}; font-weight:900;">📦 {d['CANTIDAD DE CAJAS']} CJ | </span>
                                        <span style="font-size:10px; color:#FFFFFF; opacity:0.8; font-style: italic;">{status_text}</span>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
        
        # Línea decorativa final
        st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)
    
    # ── CONTENEDOR DE CONTENIDO ──────────────────────────────────
    main_container = st.container()
    with main_container:
        # 1. DASHBOARD
        if st.session_state.menu_main == "DASHBOARD":
            
            # --- 1. DEFINICIÓN DE FUNCIONES (Primero definimos para evitar NameError) ---
            def cargar_datos():
                import time
                t = int(time.time())
                url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
                try:
                    df = pd.read_csv(url, encoding='utf-8-sig')
                    df.columns = df.columns.str.strip()
                    return df
                except Exception as e:
                    st.error(f"Error al cargar datos: {e}")
                    return None
            
            df_raw = cargar_datos()
            
            with st.expander("Detalle Operativo y Consulta de estatus de envios", expanded=False):
                # --- ESTILOS CSS ---
                st.markdown(f"""
                    <style>
                    .op-query-text {{ letter-spacing: 3px; color: {vars_css['sub']}; font-size: 10px; font-weight: 700; text-align: center; margin-bottom: 20px; }}
                    [data-testid="stDataFrame"] {{ border: 1px solid {vars_css['border']}; border-radius: 4px; }}
                    </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="op-query-text">CONSULTA DE ESTATUS LOGÍSTICO</div>', unsafe_allow_html=True)
                
                
                # --- 1. BLOQUE DE BÚSQUEDA GENERAL ---
                col_space1, col_search, col_space2 = st.columns([1, 2, 1])
                with col_search:
                    busqueda_manual = st.text_input("", key="busqueda_logistica_vfinal", placeholder="🔍 Ingrese factura o guía...").strip()
                    
                    # --- 2. LÓGICA DE FILTRADO (Subida aquí para validar el warning) ---
                    df_timeline = pd.DataFrame() # Inicializamos vacío
                    
                    if busqueda_manual:
                        # Buscamos en ambos campos usando el criterio flexible (contains)
                        mask_master = (df_raw["NÚMERO DE PEDIDO"].astype(str).str.contains(busqueda_manual, case=False)) | \
                                      (df_raw["NÚMERO DE GUÍA"].astype(str).str.contains(busqueda_manual, case=False))
                        
                        df_timeline = df_raw[mask_master].copy()
                        
                        # Ahora el mensaje solo saldrá si realmente no hay nada en ninguna columna
                        if df_timeline.empty:
                            st.warning("No se encontró detalle para la búsqueda principal.")
                
                # --- 3. RENDERIZADO DEL TIMELINE (ARRIBA) ---
                if not df_timeline.empty:
                    envio = df_timeline.iloc[0]
                    f_envio = envio.get("FECHA DE ENVÍO", "N/A")
                    f_promesa = envio.get("PROMESA DE ENTREGA", "N/A")
                    entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
                    f_entrega_val = envio["FECHA DE ENTREGA REAL"] if entregado_real else "PENDIENTE"
                    tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]
                    n_guia = envio["NÚMERO DE GUÍA"] if tiene_guia else "GENERANDO GUÍA..."
                    
                    color_envio, color_guia, color_promesa = "#38bdf8", ("#38bdf8" if tiene_guia else vars_css['border']), ("#a855f7" if tiene_guia else vars_css['border'])
                    linea_1_2, linea_2_3 = ("#38bdf8" if tiene_guia else vars_css['border']), ("#a855f7" if tiene_guia else vars_css['border'])
                    
                    f_promesa_dt = pd.to_datetime(envio["PROMESA DE ENTREGA"], dayfirst=True, errors='coerce')
                    hoy = pd.Timestamp(datetime.now())
                
                    if not tiene_guia:
                        status_text, status_color, color_entrega, linea_3_4 = "GENERANDO GUÍA", vars_css['sub'], vars_css['border'], vars_css['border']
                    elif not entregado_real:
                        status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if pd.isna(f_promesa_dt) or hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
                        color_entrega, linea_3_4 = status_color, status_color
                    else:
                        f_entrega_dt = pd.to_datetime(envio["FECHA DE ENTREGA REAL"], dayfirst=True, errors='coerce')
                        status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.isna(f_promesa_dt) or f_entrega_dt <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")
                        color_entrega, linea_3_4 = status_color, status_color
                
                    timeline_html = f'<div style="background:{vars_css["card"]}; padding:20px; border-radius:8px; border:1px solid {vars_css["border"]}; margin-bottom:25px; font-family:sans-serif;"><div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:30px;"><h2 style="margin:0; color:{vars_css["text"]}; font-size:14px; letter-spacing:1px; text-transform:uppercase; font-weight:800;">{envio["NOMBRE DEL CLIENTE"]}</h2><span style="background:{status_color}15; color:{status_color}; padding:4px 12px; border-radius:4px; font-weight:700; font-size:10px; border:1px solid {status_color}; letter-spacing:1px; white-space:nowrap;">{status_text}</span></div><div style="display:flex; align-items:center; justify-content:space-between; width:100%; position:relative; margin-bottom:30px; overflow-x:auto; padding-bottom:10px;"><div style="display:flex; flex-direction:column; align-items:center; flex:1; min-width:60px;"><div style="width:12px; height:12px; background:{color_envio}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">ENVÍO</div><div style="font-size:10px; color:white;">{f_envio}</div></div><div style="flex-grow:1; height:2px; background:{linea_1_2}; margin-top:-35px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1; min-width:60px;"><div style="width:12px; height:12px; background:{color_guia}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">GUÍA</div><div style="font-size:10px; color:white;">{"LISTA" if tiene_guia else "PENDIENTE"}</div></div><div style="flex-grow:1; height:2px; background:{linea_2_3}; margin-top:-35px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1; min-width:60px;"><div style="width:12px; height:12px; background:{color_promesa}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">PROMESA</div><div style="font-size:10px; color:white;">{f_promesa}</div></div><div style="flex-grow:1; height:2px; background:{linea_3_4}; margin-top:-35px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1; min-width:60px;"><div style="width:16px; height:16px; background:{color_entrega}; border-radius:50%; box-shadow:{"0 0 10px "+color_entrega+"44" if entregado_real else "none"}; z-index:2;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:8px; font-weight:700;">ENTREGA</div><div style="font-size:10px; color:white;">{f_entrega_val}</div></div></div><div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:15px; border-top:1px solid {vars_css["border"]}; padding-top:20px;"><div style="flex:1; min-width:80px;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">FLETERA</div><div style="color:white; font-size:14px; font-weight:800; margin-top:5px;">{envio["FLETERA"]}</div></div><div style="flex:1; min-width:80px; text-align:center;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">GUÍA</div><div style="color:white; font-size:14px; font-weight:800; margin-top:5px;">{n_guia}</div></div><div style="flex:1; min-width:80px; text-align:right;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">DESTINO</div><div style="color:white; font-size:14px; font-weight:800; margin-top:5px;">{envio["DESTINO"]}</div></div></div></div>'
                    st.markdown(timeline_html, unsafe_allow_html=True)
                
                # --- 3. INICIALIZACIÓN DE DATOS PARA FILTROS ---
                # Muy importante: Definimos df_filtrado desde el inicio
                df_filtrado = df_raw.copy()
                
                # --- 4. FILTROS MANUALES POR COLUMNA (ABAJO) ---
                st.markdown(f"<div style='color:{vars_css['sub']}; font-size:14px; font-weight:500; margin-bottom:10px; letter-spacing:1px;'>FILTROS DE TABLA</div>", unsafe_allow_html=True)
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                
                with col_f1:
                    f_no_cli = st.text_input("NO CLIENTE", key="f_no_cli", placeholder="Ej: C06778...")
                with col_f2:
                    f_nom_cli = st.text_input("NOMBRE DEL CLIENTE", key="f_nom_cli", placeholder="Nombre del cliente...")
                with col_f3:
                    f_destino = st.text_input("DESTINO", key="f_dest", placeholder="Ciudad o Estado...")
                with col_f4:
                    f_fletera = st.text_input("FLETERA", key="f_flet", placeholder="Nombre fletera...")
                
                # Aplicación de filtros manuales
                if f_no_cli:
                    df_filtrado = df_filtrado[df_filtrado["NO CLIENTE"].astype(str).str.contains(f_no_cli, case=False, na=False)]
                if f_nom_cli:
                    df_filtrado = df_filtrado[df_filtrado["NOMBRE DEL CLIENTE"].astype(str).str.contains(f_nom_cli, case=False, na=False)]
                if f_destino:
                    df_filtrado = df_filtrado[df_filtrado["DESTINO"].astype(str).str.contains(f_destino, case=False, na=False)]
                if f_fletera:
                    df_filtrado = df_filtrado[df_filtrado["FLETERA"].astype(str).str.contains(f_fletera, case=False, na=False)]
                
                # --- 5. RENDER TABLA GERENCIAL ---
                cols_orden = ["NO CLIENTE", "NÚMERO DE PEDIDO", "NOMBRE DEL CLIENTE", "DESTINO", "FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FLETERA", "NÚMERO DE GUÍA"]
                df_display = df_filtrado[[c for c in cols_orden if c in df_filtrado.columns]].copy()
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                   
            
            #INICIO DONITAS-------------------
            def render_kpi(valor, total, titulo, color):
                porc = (valor / total * 100) if total > 0 else 0
                # Circunferencia basada en radio 38
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
    
            # --- 2. CONFIGURACIÓN DE ESTILOS (CSS) ---
            st.markdown(f"""
            <style>
                .stApp {{ background-color: {vars_css['bg']} !important; }}
                
                /* ESPACIO EXTRA ENTRE EL MENÚ Y LAS DONAS */
                .spacer-menu {{
                    margin-top: 50px; /* Ajusta este valor si quieres más o menos espacio */
                }}
    
                /* ESTILOS DE LOS TABS (SUBMENÚ) */
                .stTabs [data-baseweb="tab-list"] {{
                    gap: 15px;
                    border-bottom: 1px solid #1e293b;
                }}
    
                .stTabs [data-baseweb="tab"] {{
                    background-color: #1a2432;
                    border-radius: 4px 4px 0px 0px;
                    color: #94a3b8;
                    padding: 10px 20px;
                    transition: all 0.3s ease;
                }}
    
                /* EFECTO HOVER */
                .stTabs [data-baseweb="tab"]:hover {{
                    background-color: #26354a;
                    color: #ffffff;
                }}
    
                /* ESTADO ACTIVO (DÓNDE ESTÁS) */
                .stTabs [aria-selected="true"] {{
                    background-color: #003399 !important; /* El azul de tu imagen */
                    color: white !important;
                    border-bottom: 2px solid #00FFAA !important;
                }}
    
                /* ESTILOS DE TUS DONAS (KPIs) */
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
    
            # --- 3. CARGA Y PROCESAMIENTO ---
            df_raw = cargar_datos()
            
            if df_raw is not None:
                import pytz
                from datetime import datetime
                tz_gdl = pytz.timezone('America/Mexico_City')
                hoy_gdl = datetime.now(tz_gdl).date()
                hoy_dt = pd.Timestamp(hoy_gdl)
                meses = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO","JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]
                
                col_f1, _ = st.columns([1, 4])
                with col_f1:
                    mes_sel = st.selectbox("PERÍODO", meses, index=hoy_gdl.month - 1)
            
                df = df_raw.copy()
                for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
            
                df_mes = df[df["FECHA DE ENVÍO"].dt.month == (meses.index(mes_sel) + 1)].copy()
            
                total_p = len(df_mes)
                entregados = len(df_mes[df_mes["FECHA DE ENTREGA REAL"].notna()])
                df_trans = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna()]
                en_tiempo = len(df_trans[df_trans["PROMESA DE ENTREGA"] >= hoy_dt])
                retrasados = len(df_trans[df_trans["PROMESA DE ENTREGA"] < hoy_dt])
                total_t = len(df_trans)  
    
                # --- 4. SUBMENÚ Y RENDERIZADO ---
                # Definimos los 4 nombres de las pestañas
                tab_kpis, tab_tiempos, tab_volumen, tab_participacion = st.tabs([
                    "KPI´S", "TIEMPOS DE TRÁNSITO", "VOLUMEN", "DIST. CARGA"
                ])
    
                # PESTAÑA 1: KPI'S (Tus donitas)
                with tab_kpis:
                    st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns(5)
                    with c1: render_kpi(total_p, total_p, "Pedidos", "#f6c23e")      # El Amarillo que te encantó
                    with c2: render_kpi(entregados, total_p, "Entregados", "#1cc88a") # Verde Esmeralda (Éxito)
                    with c3: render_kpi(total_t, total_p, "Tránsito", "#4e73df")    # Azul Real (Logística)
                    with c4: render_kpi(en_tiempo, total_p, "En Tiempo", "#36b9cc")  # Turquesa (Precisión)
                    with c5: render_kpi(retrasados, total_p, "Retraso", "#fb7185")   # Rojo Coral (Alerta)
                                    
                    # Espacio estético al final para que no se vea cortado el contenedor
                    st.markdown("<br>", unsafe_allow_html=True)
            
                    #--- SEPARADOR Y GRÁFICOS DE CARGA ACTIVA POR FLETERA ------
                    st.markdown(f"""
                        <hr style="border: 0; height: 1px; background: {vars_css['border']}; margin: 40px 0; opacity: 0.3;">
                        <div style="
                            color: {vars_css['sub']}; 
                            font-size: 14px; 
                            font-weight: 500; 
                            letter-spacing: 2px; 
                            margin-bottom: 20px; 
                            text-transform: uppercase;
                        ">
                            Distribución de Carga actual
                        </div>
                    """, unsafe_allow_html=True)
                    # Definimos los colores del estilo actual
                    color_transito = "#36b9cc" # Azul claro
                    color_retraso = "#fb7185"  # Rojo
                    
                    # Creamos las dos columnas directas en el contenedor
                    col_graf1, col_graf2 = st.columns(2)
                    
                    # --- COLUMNA 1: EN TRÁNSITO ---
                    with col_graf1:
                        df_t = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna() & (df_mes["PROMESA DE ENTREGA"] >= hoy_dt)].copy()
                        df_t_count = df_t.groupby("FLETERA").size().reset_index(name="CANTIDAD")
                        total_t_graf = df_t_count["CANTIDAD"].sum()
                    
                        st.markdown(f"""
                            <div style='background: linear-gradient(90deg, {color_transito}15 0%, transparent 100%); padding: 15px; border-radius: 4px; border-left: 4px solid {color_transito};'>
                                <p style='margin:0; color:{color_transito}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;'>🔵 En tránsito en tiempo</p>
                                <h2 style='margin:0; color:white; font-size:28px;'>{total_t_graf} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                            </div>
                        """, unsafe_allow_html=True)
                    
                        if not df_t_count.empty:
                            h_t = len(df_t_count) * 35 + 50
                            chart_t = alt.Chart(df_t_count).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=18, color=color_transito).encode(
                                x=alt.X("CANTIDAD:Q", title=None, axis=None),
                                y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='#94a3b8', labelFontSize=11))
                            )
                            text_t = chart_t.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700).encode(text="CANTIDAD:Q")
                            st.altair_chart((chart_t + text_t).properties(height=h_t).configure_view(strokeOpacity=0), use_container_width=True)
                        else:
                            st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin carga en tránsito</div>", unsafe_allow_html=True)
                    
                    # --- COLUMNA 2: RETRASADOS ---
                    with col_graf2:
                        df_r = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna() & (df_mes["PROMESA DE ENTREGA"] < hoy_dt)].copy()
                        df_r_count = df_r.groupby("FLETERA").size().reset_index(name="CANTIDAD")
                        total_r_graf = df_r_count["CANTIDAD"].sum()
                    
                        st.markdown(f"""
                            <div style='background: linear-gradient(90deg, {color_retraso}15 0%, transparent 100%); padding: 15px; border-radius: 4px; border-left: 4px solid {color_retraso};'>
                                <p style='margin:0; color:{color_retraso}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;'>🔴 En tránsito con Retraso</p>
                                <h2 style='margin:0; color:white; font-size:28px;'>{total_r_graf} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                            </div>
                        """, unsafe_allow_html=True)
                    
                        if not df_r_count.empty:
                            h_r = len(df_r_count) * 35 + 50
                            chart_r = alt.Chart(df_r_count).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=18, color=color_retraso).encode(
                                x=alt.X("CANTIDAD:Q", title=None, axis=None),
                                y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='#94a3b8', labelFontSize=11))
                            )
                            text_r = chart_r.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700).encode(text="CANTIDAD:Q")
                            st.altair_chart((chart_r + text_r).properties(height=h_r).configure_view(strokeOpacity=0), use_container_width=True)
                        else:
                            st.markdown("<div style='padding:20px; color:#00FFAA; font-size:12px; font-weight:bold;'>✓ Todo entregado a tiempo</div>", unsafe_allow_html=True)
            
            # PESTAÑA 2: RASTREO (Donde pondremos el buscador tipo DHL)
            with tab_tiempos: 
                st.write("")  # Esto agrega un pequeño espacio hacia abajo
                # =========================================================
                # 1. PROCESAMIENTO DE DATOS
                # =========================================================
                df['FECHA DE ENVÍO'] = pd.to_datetime(df['FECHA DE ENVÍO'], errors='coerce')
                df['FECHA DE ENTREGA REAL'] = pd.to_datetime(df['FECHA DE ENTREGA REAL'], errors='coerce')
                df['DIAS_REALES'] = (df['FECHA DE ENTREGA REAL'] - df['FECHA DE ENVÍO']).dt.days
                
                # =========================================================
                # 2. SECCIÓN DEL CALCULADOR INTELIGENTE CON ANÁLISIS REAL
                # =========================================================                
                usuario_actual = st.session_state.get('usuario_activo', 'Cielo')
                
                c1, c2 = st.columns([1, 1])
                
                with c1:
                    st.text_input("ORIGEN", value="GUADALAJARA (GDL)", disabled=True, key="orig_fix")
                
                with c2:
                    busqueda_manual = st.text_input(
                        "BUSCAR POR DESTINO, CP O DOMICILIO", 
                        placeholder="Ej: 63734, Litibu, Cancún...",
                        key="busqueda_manual_v6"
                    )
                
                # --- LÓGICA DE VISUALIZACIÓN POR DEFECTO ---
                if not busqueda_manual:
                    df_validos = df[df['DIAS_REALES'].notna()]
                    # Buscamos rutas rápidas de 2 días para el ejemplo inicial
                    rutas_dos_dias = df_validos[df_validos['DIAS_REALES'] == 2]
                    
                    if not rutas_dos_dias.empty:
                        busqueda_activa = rutas_dos_dias['DESTINO'].iloc[0]
                        texto_mostrar = f"{busqueda_activa}"
                    elif not df_validos.empty:
                        busqueda_activa = df_validos.groupby('DESTINO')['DIAS_REALES'].mean().idxmin()
                        texto_mostrar = f"{busqueda_activa} (Ruta sugerida)"
                    else:
                        busqueda_activa = ""
                        texto_mostrar = "CONSULTA DE RUTA"
                else:
                    busqueda_activa = busqueda_manual
                    texto_mostrar = busqueda_manual.upper()
                
                # --- FILTRADO Y ANÁLISIS DE FRECUENCIA ---
                busqueda_aux = busqueda_activa.lower()
                mask = (
                    df['DESTINO'].astype(str).str.lower().str.contains(busqueda_aux, na=False) |
                    df['DOMICILIO'].astype(str).str.lower().str.contains(busqueda_aux, na=False)
                )
                
                historial = df[mask & (df['DIAS_REALES'].notna())].copy()
                
                if not historial.empty:
                    # --- CÁLCULO DE LA FLETERA MÁS FRECUENTE ---
                    # Sacamos la fletera que más se repite para este destino específico
                    fletera_recomendada = historial['FLETERA'].value_counts().idxmax()
                    
                    promedio_dias = historial['DIAS_REALES'].mean()
                    total_viajes = len(historial)
                    dias_redondeados = math.ceil(promedio_dias)
                
                    # 1. Renderizado del Widget Dinámico
                    st.markdown(f"""
                        <div class="kpi-ruta-container">
                            <div class="kpi-ruta-card">
                                <span class="kpi-tag">Paquetería Recomendada: {fletera_recomendada}</span>
                                <div class="kpi-route-flow">
                                    <span class="city">GDL</span>
                                    <span class="arrow">→</span>
                                    <span class="city">{texto_mostrar}</span>
                                </div>
                                <div class="kpi-value">{dias_redondeados} <small>DÍAS</small></div>
                                <div class="kpi-subtext">
                                    La fletera más usada en <b>{total_viajes}</b> entregas exitosas a esta zona
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                    # 2. Tabla de Detalles
                    # 2. Tabla de Detalles Gobernada por tu CSS
                    st.markdown(f'<p class="data-section-header">Detalles de envíos encontrados</p>', unsafe_allow_html=True)
                    tabla_detalles = historial[[
                        'NÚMERO DE PEDIDO',
                        'NOMBRE DEL CLIENTE', 
                        'DOMICILIO', 
                        'FECHA DE ENVÍO', 
                        'FLETERA', 
                    ]].sort_values(by='FECHA DE ENVÍO', ascending=False)
                
                    tabla_detalles['FECHA DE ENVÍO'] = tabla_detalles['FECHA DE ENVÍO'].dt.strftime('%d/%m/%Y')
                
                    st.dataframe(tabla_detalles, use_container_width=True, hide_index=True)
                else:
                    st.info(f"Lo siento **{usuario_actual}**, no encontré historial para: **{busqueda_manual}**")
                    
                
                # PESTAÑA 3: VOLUMEN
                with tab_volumen:
                    st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)
                    st.write("Visualización de Volumen de Carga")
                    #AQUI
                
                    
                # PESTAÑA 4: % PARTICIPACIÓN
                with tab_participacion:
                    URL_LOGISTICA = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
                    
                    @st.cache_data
                    def load_data_logistica():
                        try:
                            df_l = pd.read_csv(URL_LOGISTICA, low_memory=False)
                            df_l.columns = [c.replace('_x000D_', '').strip() for c in df_l.columns]
                            if 'MES' in df_l.columns:
                                df_l['MES'] = df_l['MES'].astype(str).str.upper().str.strip()
                            df_l['CAJAS'] = pd.to_numeric(df_l['CAJAS'], errors='coerce').fillna(0)
                            return df_l
                        except Exception as e:
                            st.error(f"Error de conexión: {e}")
                            return None
                    
                    df_log = load_data_logistica()
                    
                    if df_log is not None:
                        # --- NUEVO FILTRO DE TIPO DE MOVIMIENTO ---
                        st.markdown("<p class='op-query-text' style='font-size:12px;'>DISTRIBUCION DE CARGA MENSUAL</p>", unsafe_allow_html=True)
                        tipo_mov = st.radio(
                            "Selecciona el flujo:",
                            ["TODOS", "COBRO DESTINO", "COBRO REGRESO"],
                            index=2,
                            horizontal=True,
                            key=f"tipo_mov_{mes_sel}"
                        )
                
                        # Aplicamos primer filtro: MES
                        df_log_filtrado = df_log[df_log["MES"] == mes_sel].copy()
                
                        # Aplicamos segundo filtro: Búsqueda de texto en TRANSPORTE
                        if tipo_mov == "COBRO DESTINO":
                            df_log_filtrado = df_log_filtrado[df_log_filtrado['TRANSPORTE'].str.contains('DESTINO', case=False, na=False)]
                        elif tipo_mov == "COBRO REGRESO":
                            df_log_filtrado = df_log_filtrado[df_log_filtrado['TRANSPORTE'].str.contains('REGRESO', case=False, na=False)]
                
                        if not df_log_filtrado.empty:
                            # --- CABECERA ---                                                            
                            total_cajas_mes = df_log_filtrado['CAJAS'].sum()
                            df_part = df_log_filtrado.groupby('TRANSPORTE')['CAJAS'].sum().reset_index()
                            df_part['PORCENTAJE'] = (df_part['CAJAS'] / total_cajas_mes) * 100
                            df_part = df_part.sort_values(by='PORCENTAJE', ascending=True)
                            
                            # METRICAS
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f"<p class='op-query-text' style='letter-spacing:3px;'>VOLUMEN TOTAL (UNIT)</p>", unsafe_allow_html=True)
                                st.markdown(f"<h4 style='text-align:center; color:#FFFFFF;'>{int(total_cajas_mes):,}</h4>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<p class='op-query-text' style='letter-spacing:3px;'>CARRIER DOMINANTE</p>", unsafe_allow_html=True)
                                lider_n = df_part.iloc[-1]['TRANSPORTE'] if not df_part.empty else "N/A"
                                st.markdown(f"<h4 style='text-align:center; color:#00FFAA;'>{lider_n}</h4>", unsafe_allow_html=True)
                            
                            # --- 4. GRÁFICO DE BARRAS (PLOTLY GO) ---
                            # Calculamos altura para que no se amontonen (40px por cada barra)
                            altura_ajustada = max(400, len(df_part) * 40)
                            
                            fig_bar = go.Figure(go.Bar(
                                x=df_part['PORCENTAJE'],
                                y=df_part['TRANSPORTE'],
                                orientation='h',
                                marker=dict(
                                    color=df_part['PORCENTAJE'],
                                    colorscale=['#1a2432', '#1cc88a']
                                ),
                                text=df_part['PORCENTAJE'].apply(lambda x: f'{x:.1f}%'),
                                textposition='outside',
                                cliponaxis=False # Evita que el texto se corte
                            ))
                            
                            fig_bar.update_layout(
                                height=altura_ajustada, # Altura dinámica
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(family="Inter", size=12, color="#FFFFFF"),
                                margin=dict(l=250, r=50, t=20, b=20), # Margen izquierdo grande para los nombres largos
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=True),
                                yaxis=dict(showgrid=False, automargin=True),
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False}, key=f"bar_part_{mes_sel}_{tipo_mov}")
                
                            # --- 6. EXPANDER: DESGLOSE POR DESTINO ---
                            st.markdown("<br>", unsafe_allow_html=True)
                            with st.expander("🌐 EXPLORADOR DE RUTAS Y DESTINOS"):
                                lista_carriers = sorted(df_log_filtrado['TRANSPORTE'].unique())
                                carriers_seleccionados = st.multiselect(
                                    "Filtrar por uno o varios Carriers:", 
                                    options=lista_carriers,
                                    default=None,
                                    key=f"multi_carrier_{mes_sel}_{tipo_mov}"
                                )
                                
                                if carriers_seleccionados:
                                    df_dest_filtered = df_log_filtrado[df_log_filtrado['TRANSPORTE'].isin(carriers_seleccionados)].copy()
                                else:
                                    df_dest_filtered = df_log_filtrado.copy()
                                
                                df_dest_sum = df_dest_filtered.groupby(['TRANSPORTE', 'DESTINO'])['CAJAS'].sum().reset_index()
                                df_dest_sum = df_dest_sum.sort_values(by=['TRANSPORTE', 'CAJAS'], ascending=[True, False])
                                
                                total_sel = df_dest_sum['CAJAS'].sum()
                                st.markdown(f"<p style='color:#00FFAA; font-size:12px;'>Unidades en selección actual: {int(total_sel):,}</p>", unsafe_allow_html=True)
                
                                st.dataframe(
                                    df_dest_sum,
                                    column_config={
                                        "TRANSPORTE": "CARRIER",
                                        "DESTINO": "CIUDAD / ESTADO",
                                        "CAJAS": st.column_config.NumberColumn("UNITS", format="%d")
                                    },
                                    use_container_width=True,
                                    hide_index=True,
                                    key=f"tabla_destinos_{mes_sel}_{tipo_mov}"
                                )
                        else:
                            st.warning(f"No se encontraron registros que coincidan con '{tipo_mov}' para el mes seleccionado.")

        
        elif st.session_state.menu_main == "SEGUIMIENTO":
            # ── A. CARGA DE DATOS (MATRIZ DESDE GITHUB) ──
            # ── A. CARGA DE DATOS (LECTURA DIRECTA Y DINÁMICA) ──
            def cargar_matriz_github():
                # El parámetro ?v= engaña a GitHub para que no use su propia memoria caché
                t = int(time.time())
                url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
                
                try:
                    # Leemos directo, sin @st.cache_data para que siempre sea información fresca
                    return pd.read_csv(url, encoding='utf-8-sig')
                except:
                    return None
            
            # Cargamos la matriz
            df_seguimiento = cargar_matriz_github()
    
            if df_seguimiento is None:
                st.error("⚠️ ERROR: No se detectó la base de datos en GitHub.")
                st.stop()
    
            # ── B. RELOJ MAESTRO (GUADALAJARA) ──
            tz_gdl = pytz.timezone('America/Mexico_City')
            hoy_gdl = datetime.now(tz_gdl).date()
    
            # ── C. NAVEGACIÓN DE SUB-MENÚ TRK ──
            if st.session_state.menu_sub == "ALERTAS":
                # 1. FILTROS DE CABECERA
                with st.container():
                    st.write("")
                    f_col1, f_col2, f_col3 = st.columns([1, 1.5, 1.5], vertical_alignment="bottom")
                    
                    with f_col2:
                        # Movemos el selector de mes arriba o lo calculamos primero para que el calendario lo use
                        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
                        mes_sel = st.selectbox("MES OPERATIVO", meses, index=hoy_gdl.month - 1)
                        mes_num = meses.index(mes_sel) + 1
                    
                    with f_col1:
                        # Lógica de fechas sincronizada con mes_sel
                        inicio_m = date(hoy_gdl.year, mes_num, 1)
                        
                        if mes_num == 12:
                            fin_m = date(hoy_gdl.year, 12, 31)
                        else:
                            fin_m = date(hoy_gdl.year, mes_num + 1, 1) - pd.Timedelta(days=1)
                        
                        # Aseguramos que fin_m sea objeto date puro
                        fin_m_final = fin_m.date() if hasattr(fin_m, 'date') else fin_m
                        
                        rango_fechas = st.date_input(
                            "RANGO DE ANÁLISIS",
                            value=(inicio_m, min(hoy_gdl.date() if hasattr(hoy_gdl, 'date') else hoy_gdl, fin_m_final)),
                            format="DD/MM/YYYY"
                        )
                    
                    with f_col3:
                        # Filtro de Fletera
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
                
                # ── 4. SEMÁFORO DE ALERTAS ──
                st.markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:2px; color:{vars_css['sub']}; text-align:center; margin-top:30px;'>S E M Á F O R O DE ALERTAS</p>", unsafe_allow_html=True)
                
                a1_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] == 1])
                a2_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"].between(2,4)])
                a5_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] >= 5])
                
                c_a1, c_a2, c_a3 = st.columns(3)
                c_a1.markdown(f"<div class='card-alerta' style='border-top: 4px solid #fde047;'><div style='color:#9CA3AF; font-size:10px;'>LEVE (1D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a1_v}</div></div>", unsafe_allow_html=True)
                c_a2.markdown(f"<div class='card-alerta' style='border-top: 4px solid #f97316;'><div style='color:#9CA3AF; font-size:10px;'>MODERADO (2-4D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a2_v}</div></div>", unsafe_allow_html=True)
                c_a3.markdown(f"<div class='card-alerta' style='border-top: 4px solid #ff4b4b;'><div style='color:#9CA3AF; font-size:10px;'>CRÍTICO (+5D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a5_v}</div></div>", unsafe_allow_html=True)                     
                
                # 5. PANEL DE EXCEPCIONES
                st.divider()
                df_criticos = df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] > 0].copy() if not df_sin_entregar.empty else pd.DataFrame()
                
                if not df_criticos.empty:
                    st.markdown(f"""<p style='font-size:11px; font-weight:700; letter-spacing:8px; color:{vars_css.get('sub', '#666')}; text-transform:uppercase; text-align:center; margin-bottom:20px;'>PANEL DE EXCEPCIONES</p>""", unsafe_allow_html=True)
                    with st.expander("Filtrar y analizar detalle de retrasos", expanded=True):
                        c1, c2 = st.columns(2)
                        with c1: 
                            sel_f = st.multiselect("TRANSPORTISTA:", sorted(df_criticos["FLETERA"].unique()), placeholder="TODOS")
                        with c2: 
                            sel_g = st.selectbox("GRAVEDAD ATRASO:", ["TODOS", "CRÍTICO (+5 DÍAS)", "MODERADO (2-4 DÍAS)", "LEVE (1 DÍA)"])
                        
                        st.markdown("---")
                        df_viz = df_criticos.copy()
                        if sel_f: df_viz = df_viz[df_viz["FLETERA"].isin(sel_f)]
                        if sel_g == "CRÍTICO (+5 DÍAS)": df_viz = df_viz[df_viz["DIAS_ATRASO"] >= 5]
                        elif sel_g == "MODERADO (2-4 DÍAS)": df_viz = df_viz[df_viz["DIAS_ATRASO"].between(2, 4)]
                        elif sel_g == "LEVE (1 DÍA)": df_viz = df_viz[df_viz["DIAS_ATRASO"] == 1]
                
                        columnas_deseadas = {
                            "NÚMERO DE PEDIDO": ["NÚMERO DE PEDIDO", "PEDIDO"],
                            "FLETERA": ["FLETERA"],
                            "NÚMERO DE GUÍA": ["NÚMERO DE GUÍA", "GUÍA"],
                            "DIAS_TRANS": ["DIAS_TRANS"],
                            "DIAS_ATRASO": ["DIAS_ATRASO"],                            
                            "NOMBRE DEL CLIENTE": ["NOMBRE DEL CLIENTE", "CLIENTE"],
                            "DESTINO": ["DESTINO", "CIUDAD"],
                            "FECHA DE ENVÍO": ["FECHA DE ENVÍO"],
                            "PROMESA DE ENTREGA": ["PROMESA DE ENTREGA"],
                            "FECHA DE ENTREGA REAL": ["FECHA DE ENTREGA REAL"],
                            
                        }
                        cols_finales = [next((c for c in p if c in df_viz.columns), None) for p in columnas_deseadas.values()]
                        cols_finales = [c for c in cols_finales if c is not None]
                
                        if not df_viz.empty:
                            st.dataframe(
                                df_viz[cols_finales].sort_values("DIAS_ATRASO", ascending=False),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    "FECHA DE ENVÍO": st.column_config.DateColumn("ENVÍO", format="DD/MM/YYYY"),
                                    "PROMESA DE ENTREGA": st.column_config.DateColumn("P. ENTREGA", format="DD/MM/YYYY"),
                                    "FECHA DE ENTREGA REAL": st.column_config.DateColumn("F. ENTREGA", format="DD/MM/YYYY"),
                                    "DIAS_TRANS": st.column_config.ProgressColumn("DÍAS VIAJE", format="%d", min_value=0, max_value=15, color="orange"),
                                    "DIAS_ATRASO": st.column_config.ProgressColumn("RETRASO", format="%d DÍAS", min_value=0, max_value=15, color="red")
                                }
                            )
                        else:
                            st.info("No hay pedidos que coincidan con los filtros seleccionados.")
                else:
                    st.success("SISTEMA NEXION: SIN RETRASOS DETECTADOS")
                
                # 6. DETALLE DE ENTREGAS DEL PRÓXIMO MES
                st.divider()
                df_detalle_prox = df_seguimiento.copy()
                df_detalle_prox.columns = [c.upper() for c in df_detalle_prox.columns]
                
                if "PROMESA DE ENTREGA" in df_detalle_prox.columns:
                    df_detalle_prox["PROMESA DE ENTREGA"] = pd.to_datetime(df_detalle_prox["PROMESA DE ENTREGA"], dayfirst=True, errors='coerce')
                    df_futuro = df_detalle_prox[(df_detalle_prox["PROMESA DE ENTREGA"].dt.month == proximo_mes_num) & (df_detalle_prox["PROMESA DE ENTREGA"].dt.year == anio_proximo)].copy()
                
                    if not df_futuro.empty:
                        st.markdown(f"""<p style='font-size:11px; font-weight:700; letter-spacing:5px; color:#a855f7; text-transform:uppercase; text-align:center;'>PLANIFICACIÓN DE ENTREGAS: {nombre_prox_mes}</p>""", unsafe_allow_html=True)
                        with st.expander(f"VER LISTADO DE {len(df_futuro)} PEDIDOS PARA {nombre_prox_mes}", expanded=False):
                            cols_prox = ["NÚMERO DE PEDIDO", "NOMBRE DEL CLIENTE", "DESTINO", "PROMESA DE ENTREGA", "FLETERA", "ESTATUS"]
                            cols_prox_existentes = [c for c in cols_prox if c in df_futuro.columns]
                            st.dataframe(
                                df_futuro[cols_prox_existentes].sort_values("PROMESA DE ENTREGA"),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    "PROMESA DE ENTREGA": st.column_config.DateColumn("FECHA PACTADA", format="DD/MM/YYYY"),
                                    "NÚMERO DE PEDIDO": st.column_config.TextColumn("PEDIDO"),
                                }
                            )
                   
            
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
                        import datetime as dt_module
                        return (dt_module.datetime.now(dt_module.timezone.utc) - dt_module.timedelta(hours=6)).date()
                
                def guardar_en_github(df):
                    """Sincroniza el DataFrame con el repositorio de GitHub."""
                    import base64
                    import requests
                    
                    if not TOKEN:
                        st.error("No se encontró el GITHUB_TOKEN en los secrets.")
                        return False
                        
                    csv_content = df.to_csv(index=False)
                    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
                    headers = {
                        "Authorization": f"token {TOKEN}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                    
                    try:
                        r = requests.get(api_url, headers=headers)
                        sha = r.json().get("sha") if r.status_code == 200 else None
                        
                        payload = {
                            "message": f"Actualización de tareas {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            "content": base64.b64encode(csv_content.encode()).decode(),
                            "branch": "main"
                        }
                        if sha:
                            payload["sha"] = sha
                            
                        response = requests.put(api_url, headers=headers, json=payload)
                        
                        if response.status_code in [200, 201]:
                            st.success("✅ ¡Sincronizado con éxito!")
                            return True
                        else:
                            st.error(f"Error de GitHub: {response.json().get('message')}")
                            return False
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
                        return False
                
                def cargar_datos_seguro():
                    columnas = [
                        "USUARIO","FECHA","FECHA_FIN","IMPORTANCIA","TAREA","ULTIMO ACCION",
                        "PROGRESO","DEPENDENCIAS","TIPO","GRUPO"
                    ]
                    hoy = obtener_fecha_mexico()
                    try:
                        import time
                        import requests
                        from io import StringIO
                        
                        r = requests.get(f"{CSV_URL}?t={int(time.time())}")
                        if r.status_code == 200:
                            df = pd.read_csv(StringIO(r.text))
                            df.columns = [c.strip().upper() for c in df.columns]
                            
                            for c in columnas:
                                if c not in df.columns:
                                    df[c] = ""
                            
                            df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce").dt.date
                            df["FECHA_FIN"] = pd.to_datetime(df["FECHA_FIN"], errors="coerce").dt.date
                            
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
                
                df_master = st.session_state.df_tareas.copy()
                
                # ── 3. DATA EDITOR (DENTRO DE EXPANDER) ───────────────────────────────────────────────
                with st.expander(":material/edit_note: Abrir editor de tareas", expanded=False):
                    st.subheader("EDITOR DE TAREAS")
                    df_editor = df_master.copy()
                    for col in ["USUARIO","IMPORTANCIA","TAREA","ULTIMO ACCION","DEPENDENCIAS","TIPO","GRUPO"]:
                        df_editor[col] = df_editor[col].astype(str).replace("nan", "").fillna("")
                    
                    df_editor["PROGRESO_VIEW"] = df_editor["PROGRESO"]
                    
                    df_editado = st.data_editor(
                        df_editor,
                        hide_index=True,
                        use_container_width=True,
                        num_rows="dynamic",
                        column_config={
                            "USUARIO": st.column_config.TextColumn("Responsable"),
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
                
                    if st.button("SINCRONIZAR CON GITHUB", use_container_width=True):
                        df_guardar = df_editado.drop(columns=["PROGRESO_VIEW"], errors="ignore")
                        if guardar_en_github(df_guardar):
                            st.session_state.df_tareas = df_guardar
                            st.rerun() 
                
                
                
                # ── 1. FILTROS Y CONTROLES ────────────────────────────────
                c1, c2 = st.columns([1, 2])
                with c1:
                    gantt_view = st.radio("Vista", ["Day", "Week", "Month", "Year"], horizontal=True, index=0, key="gantt_v")
                
                with c2:
                    grupos_disponibles = sorted(df_master["GRUPO"].astype(str).unique())
                    grupos_sel = st.multiselect("Filtrar por grupo", grupos_disponibles, default=grupos_disponibles, key="gantt_g")
                
                df_gantt = df_master[df_master["GRUPO"].isin(grupos_sel)].copy()
                
                mask_hito = df_gantt["TIPO"].str.lower() == "hito"
                df_gantt.loc[mask_hito, "FECHA_FIN"] = df_gantt.loc[mask_hito, "FECHA"]
                
                tasks_data = []
                for i, r in enumerate(df_gantt.itertuples(), start=1):
                    if not str(r.TAREA).strip(): 
                        continue
                
                    importancia = str(r.IMPORTANCIA).strip().lower()
                    task_id = f"T{i}"
                    
                    dependencias = str(r.DEPENDENCIAS).strip()
                    if dependencias:
                        dependencias_ids = []
                        for d in dependencias.split(','):
                            d = d.strip()
                            if d.isdigit():
                                dependencias_ids.append(f"T{int(d)+1}")
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
                
                # ── 2. RENDERIZADO GANTT ───────────────────────────────
                components.html(
                    f"""
                    <html>
                    <head>
                        <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.css'>
                        <script src='https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.js'></script>
                        <style>
                        html, body {{ background:#384A52; margin:0; padding:0; }}
                        #gantt {{ background:#384A52; }}
                        .gantt text {{ fill:#E5E7EB !important; font-size:12px; }}
                        .grid-background {{ fill:#384A52 !important; }}
                        .grid-header {{ fill:#1E262A !important; }}
                        .grid-row {{ fill:#384A52 !important; }}
                        .grid-row:nth-child(even) {{ fill:#3F525B !important; }}
                        .grid-line {{ stroke: #0F1517 !important; stroke-opacity: 0.1 !important; }}
                        .arrow {{ stroke: #9ca3af !important; stroke-width: 1.6 !important; opacity: 1 !important; fill: none !important; }}
                        .bar-wrapper.imp-urgente .bar {{ fill:#DC2626 !important; }}
                        .bar-wrapper.imp-alta    .bar {{ fill:#F97316 !important; }}
                        .bar-wrapper.imp-media   .bar {{ fill:#3B82F6 !important; }}
                        .bar-wrapper.imp-baja    .bar {{ fill:#22C55E !important; }}
                        .today-highlight {{ fill: #00FF00 !important; opacity: 0.2 !important; }}
                    
                        /* --- ESTILO PARA EL SCROLL DARK --- */
                        ::-webkit-scrollbar {{
                            width: 10px;
                            height: 10px;
                        }}
                        ::-webkit-scrollbar-track {{
                            background: #3F525B; /* Fondo del scroll igual al body */
                        }}
                        ::-webkit-scrollbar-thumb {{
                            background: #007076; /* Color de la barrita */
                            border-radius: 5px;
                        }}
                        ::-webkit-scrollbar-thumb:hover {{
                            background: #00A0A8; /* Color cuando pasas el mouse */
                        }}
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
                                setTimeout(function() {{
                                    document.querySelectorAll('#gantt svg line').forEach(function(line) {{
                                        var x1 = parseFloat(line.getAttribute('x1'));
                                        var x2 = parseFloat(line.getAttribute('x2'));
                                        var y1 = parseFloat(line.getAttribute('y1'));
                                        var y2 = parseFloat(line.getAttribute('y2'));
                                        if(x1 === x2) line.style.display = 'none';
                                        if(y1 === y2) {{
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
                    height=620,
                    scrolling=True
                )
                
                   
    
    
            
            elif st.session_state.menu_sub == "QUEJAS":
                st.markdown("<br><br>", unsafe_allow_html=True)
                # ── CONFIGURACIÓN GITHUB (QUEJAS) ──
                TOKEN = st.secrets.get("GITHUB_TOKEN", None)
                REPO_NAME = "RH2026/nexion"
                FILE_PATH = "gastos.csv"
                CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
                
                # ── FUNCIONES DE SOPORTE ──
                def cargar_datos_gastos():
                    columnas_base = ["FECHA", "ID", "QUEJA", "ESTATUS", "INCONFORMIDAD", "AGENTE", "ULTIMA ACCION", "GASTOS ADICIONALES"]
                    
                    mapeo_nombres = {
                        "PAQUETERIA": "ID",
                        "CLIENTE": "QUEJA",
                        "SOLICITO": "ESTATUS",
                        "DESTINO": "INCONFORMIDAD",
                        "CANTIDAD": "AGENTE",
                        "UM": "ULTIMA ACCION",
                        "COSTO": "GASTOS ADICIONALES"
                    }
                
                    try:
                        r = requests.get(f"{CSV_URL}?t={int(time.time())}")
                        if r.status_code == 200:
                            df = pd.read_csv(io.StringIO(r.text))
                
                            # Normalizar columnas
                            df.columns = [str(c).strip().upper() for c in df.columns]
                
                            # Renombrar si aplica
                            df = df.rename(columns=mapeo_nombres)
                
                            # Crear columnas faltantes
                            for col in columnas_base:
                                if col not in df.columns:
                                    df[col] = ""
                
                            # Orden exacto
                            df = df[columnas_base]
                
                            # 🔥 LIMPIEZA FUERTE DE NUMÉRICOS
                            df["GASTOS ADICIONALES"] = (
                                df["GASTOS ADICIONALES"]
                                .astype(str)
                                .str.replace("$", "", regex=False)
                                .str.replace(",", "", regex=False)
                                .str.strip()
                            )
                
                            df["GASTOS ADICIONALES"] = pd.to_numeric(
                                df["GASTOS ADICIONALES"], errors="coerce"
                            ).fillna(0.0)
                
                            return df
                
                    except Exception as e:
                        print("Error cargando gastos:", e)
                
                    return pd.DataFrame(columns=columnas_base)
                
                
                def guardar_en_github(df_to_save):
                    if not TOKEN:
                        return False
                    try:
                        from github import Github
                        g = Github(TOKEN)
                        repo = g.get_repo(REPO_NAME)
                
                        # 🔥 FORZAR NUMÉRICO ANTES DE GUARDAR
                        df_to_save["GASTOS ADICIONALES"] = pd.to_numeric(
                            df_to_save["GASTOS ADICIONALES"], errors="coerce"
                        ).fillna(0.0)
                
                        csv_data = df_to_save.to_csv(index=False)
                
                        try:
                            contents = repo.get_contents(FILE_PATH)
                            repo.update_file(
                                contents.path,
                                f"Update gastos {datetime.now()}",
                                csv_data,
                                contents.sha
                            )
                        except:
                            repo.create_file(
                                FILE_PATH,
                                "Initial gastos",
                                csv_data
                            )
                
                        return True
                    except Exception as e:
                        print("Error guardando en GitHub:", e)
                        return False
                
                
                # ── INTERFAZ ──                
                if "df_gastos" not in st.session_state:
                    st.session_state.df_gastos = cargar_datos_gastos()
                               
                
                # 👇 AQUÍ VA EL CSS
                st.markdown("""
                <style>
                
                /* Forzar wrap real dentro del DataEditor */
                [data-testid="stDataEditor"] [role="gridcell"] {
                    white-space: normal !important;
                    line-height: 1.4 !important;
                }
                
                /* El texto interno del cell */
                [data-testid="stDataEditor"] [role="gridcell"] div {
                    white-space: normal !important;
                    overflow: visible !important;
                    text-overflow: unset !important;
                    word-break: break-word !important;
                }
                
                /* Quitar ellipsis */
                [data-testid="stDataEditor"] span {
                    white-space: normal !important;
                    overflow: visible !important;
                    text-overflow: unset !important;
                }
                
                /* Permitir que la fila crezca */
                [data-testid="stDataEditor"] [role="row"] {
                    align-items: stretch !important;
                    height: auto !important;
                }
                
                </style>
                """, unsafe_allow_html=True)
                
                
                # ── COPIA SEGURA PARA EDITOR ──
                df_base = st.session_state.df_gastos.copy()
                
                # 🔥 Forzar tipos exactos
                columnas_texto = [
                    "FECHA", "ID", "QUEJA", "ESTATUS",
                    "INCONFORMIDAD", "AGENTE", "ULTIMA ACCION"
                ]
                
                for col in columnas_texto:
                    df_base[col] = df_base[col].astype("string")
                
                df_base["GASTOS ADICIONALES"] = pd.to_numeric(
                    df_base["GASTOS ADICIONALES"],
                    errors="coerce"
                ).fillna(0.0).astype("float64")  # 👈 esto es CLAVE
                
                # ── EDITOR DE DATOS ──
                df_editado = st.data_editor(
                    df_base,
                    use_container_width=True,
                    num_rows="dynamic",
                    row_height=90, 
                    key="editor_gastos_v_final_secure",
                    column_config={
                        "FECHA": st.column_config.TextColumn("FECHA"),
                        "ID": st.column_config.TextColumn("ID"),
                        "QUEJA": st.column_config.TextColumn("QUEJA"),
                        "ESTATUS": st.column_config.TextColumn("ESTATUS"),
                        "INCONFORMIDAD": st.column_config.TextColumn("INCONFORMIDAD"),
                        "AGENTE": st.column_config.TextColumn("AGENTE"),
                        "ULTIMA ACCION": st.column_config.TextColumn("ÚLTIMA ACCIÓN"),
                        "GASTOS ADICIONALES": st.column_config.NumberColumn(
                            "GASTOS ADICIONALES",
                            format="$%.2f"
                        )
                    }
                )
                
                # 🔥 BLINDAJE POST-EDICIÓN
                df_editado["GASTOS ADICIONALES"] = (
                    df_editado["GASTOS ADICIONALES"]
                    .astype(str)
                    .str.replace("$", "", regex=False)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                )
                
                df_editado["GASTOS ADICIONALES"] = pd.to_numeric(
                    df_editado["GASTOS ADICIONALES"], errors="coerce"
                ).fillna(0.0)
                
                
                # ── PREPARACIÓN DE IMPRESIÓN ──
                df_editado.columns = [str(c).upper().strip() for c in df_editado.columns]
                
                filas_v = df_editado[
                    df_editado["ID"].notna() &
                    (df_editado["ID"].astype(str).str.strip() != "")
                ].copy()
                
                tabla_html = ""
                
                if not filas_v.empty:
                    for _, r in filas_v.iterrows():
                        costo_fmt = f"${float(r.get('GASTOS ADICIONALES', 0)):,.2f}"
                        tabla_html += f"""
                        <tr>
                            <td style='border:1px solid #000;padding:5px;font-size:10px;'>{r.get('FECHA', '')}</td>
                            <td style='border:1px solid #000;padding:5px;font-size:10px;'>{r.get('ID', '')}</td>
                            <td style='border:1px solid #000;padding:5px;font-size:10px;'>{r.get('QUEJA', '')}</td>
                            <td style='border:1px solid #000;padding:5px;font-size:10px;'>{r.get('ESTATUS', '')}</td>
                            <td style='border:1px solid #000;padding:5px;font-size:10px;'>{r.get('INCONFORMIDAD', '')}</td>
                            <td style='border:1px solid #000;padding:5px;font-size:10px;'>{r.get('AGENTE', '')}</td>
                            <td style='border:1px solid #000;padding:5px;font-size:10px;'>{r.get('ULTIMA ACCION', '')}</td>
                            <td style='border:1px solid #000;padding:5px;font-size:10px;text-align:right;'>{costo_fmt}</td>
                        </tr>"""
                
                total_c = filas_v["GASTOS ADICIONALES"].sum() if not filas_v.empty else 0
                
                form_print = f"""
                <div style="font-family:Arial; padding:20px; color:black; background:white;">
                    <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:10px; margin-bottom:15px;">
                        <div><h2 style="margin:0; letter-spacing:2px;">JYPESA</h2><p style="margin:0; font-size:9px; letter-spacing:1px;">AUTOMATIZACIÓN DE PROCESOS</p></div>
                        <div style="text-align:right; font-size:10px;"><b>FECHA REPORTE:</b> {datetime.now().strftime('%d/%m/%Y')}<br><b>HORA:</b> {datetime.now().strftime('%I:%M %p').lower()}</div>
                    </div>
                    <h4 style="text-align:center; text-transform:uppercase; margin-bottom:20px;">Reporte Detallado de Seguimiento de Quejas</h4>
                    <table style="width:100%; border-collapse:collapse;">
                        <thead><tr style="background:#eee; font-size:10px;">
                            <th>FECHA</th><th>ID</th><th>QUEJA</th><th>ESTATUS</th><th>INCONFORMIDAD</th><th>AGENTE</th><th>ÚLTIMA ACCIÓN</th><th>GASTOS ADICIONALES</th>
                        </tr></thead>
                        <tbody>{tabla_html}</tbody>
                        <tfoot><tr style="font-weight:bold; background:#eee; font-size:11px;">
                            <td colspan="7" style="border:1px solid #000; text-align:right; padding:5px;">TOTAL GENERAL:</td>
                            <td style="border:1px solid #000; text-align:right; padding:5px;">${total_c:,.2f}</td>
                        </tr></tfoot>
                    </table>
                    <div style="margin-top:40px; display:flex; justify-content:space-around; text-align:center; font-size:10px;">
                        <div style="width:40%; border-top:1px solid black;">ELABORÓ<br>Rigoberto Hernandez / Cord. Logística</div>
                        <div style="width:40%; border-top:1px solid black;">AUTORIZÓ<br>Dirección de Operaciones</div>
                    </div>
                </div>"""
                
                
                # ── BOTONES ──
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    if st.button(":material/refresh: ACTUALIZAR", use_container_width=True):
                        st.session_state.df_gastos = cargar_datos_gastos()
                        st.rerun()
                
                with c2:
                    if st.button(":material/save: GUARDAR", type="primary", use_container_width=True):
                        if guardar_en_github(df_editado):
                            st.session_state.df_gastos = df_editado
                            st.toast("Sincronización exitosa", icon="✅")
                            time.sleep(1)
                            st.rerun()
                
                with c3:
                    if st.button(":material/print: IMPRIMIR", use_container_width=True):
                        components.html(
                            f"<html><body>{form_print}<script>window.print();</script></body></html>",
                            height=0
                        )
                        st.toast("Generando vista previa", icon="🖨️")
                
            else:
                st.subheader("MÓDULO DE SEGUIMIENTO")
                st.write("Seleccione una sub-categoría en la barra superior.")
    
        # 3. REPORTES
        elif st.session_state.menu_main == "REPORTES":
            
            # Aquí creamos el "espacio" para cada uno
            if st.session_state.menu_sub == "APQ":
                st.subheader("Análisis de Producto y Quejas (APQ)")
                # [Aquí va tu código o función para el reporte APQ]
                st.info("Cargando datos de calidad...")
                # Ejemplo: st.dataframe(df_apq)
    
            elif st.session_state.menu_sub == "% LOGISTICO":
                # --- 1. MOTOR DE DATOS NIVEL ELITE (ESTILO ONYX) ---
                st.markdown("""
                <style>
                .main { background-color: #0B1014; }
                
                [data-testid="stMetric"] { 
                    background-color: #1A252F; 
                    padding: 25px; 
                    border-radius: 12px; 
                    border-left: 5px solid #A4B9C8; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                    min-height: 160px !important;
                    max-height: 160px !important;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                
                div[data-testid="stMetricValue"] { color: #FFFFFF; font-weight: 900; font-size: 1.8rem; }
                div[data-testid="stMetricLabel"] { color: #A4B9C8; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.85rem; font-weight: bold; }
                
                h1 { color: #FFFFFF; font-family: 'Arial Black'; border-bottom: 2px solid #A4B9C8; padding-bottom: 10px; }
                h3 { color: #A4B9C8; margin-top: 30px; font-family: 'Arial'; text-transform: uppercase; letter-spacing: 2px; }
                
                .analysis-box {
                    background-color: #1A252F;
                    padding: 25px;
                    border-radius: 12px;
                    border: 1px solid #243441;
                    color: #A4B9C8;
                    line-height: 1.8;
                    font-size: 0.95rem;
                }
                .highlight { color: #FFFFFF; font-weight: bold; }
                </style>
                """, unsafe_allow_html=True)
                
                def limpiar_columnas(txt):
                    if not isinstance(txt, str): return txt
                    texto = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
                    return texto.strip().upper()
                
                def limpiar_dinero(col):
                    if col.dtype == object:
                        return pd.to_numeric(col.str.replace('$', '').str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                    return col.fillna(0)
                
                # 2. CARGA Y PROCESAMIENTO
                try:
                    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
                    df_2025 = pd.read_csv('Historial2025.csv')
                
                    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
                    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]
                
                    columnas_dinero = ['COSTO DE LA GUIA', 'FACTURACION', 'VALUACION', 'COSTOS ADICIONALES']
                    for col in columnas_dinero:
                        if col in df_actual.columns: df_actual[col] = limpiar_dinero(df_actual[col])
                    if 'COSTO DE LA GUIA' in df_2025.columns: df_2025['COSTO DE LA GUIA'] = limpiar_dinero(df_2025['COSTO DE LA GUIA'])
                
                    df_actual['MES'] = df_actual['MES'].astype(str).str.strip().str.upper()
                    df_2025['MES'] = df_2025['MES'].astype(str).str.strip().str.upper()
                
                    df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False)].copy()
                    df_gastos['COSTO DE FLETE'] = df_gastos['COSTO DE LA GUIA'] + df_gastos.get('COSTOS ADICIONALES', 0)
                
                    # 3. INTERFAZ
                    
                    c_f1, c_f2 = st.columns(2)
                    with c_f1: mes_sel = st.selectbox(":material/calendar_month: FILTRAR POR MES:", ["TODOS"] + sorted(df_gastos['MES'].unique().tolist()))
                    with c_f2: flet_sel = st.selectbox(":material/local_shipping: FILTRAR POR FLETERA:", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))
                
                    df_filtered = df_gastos.copy()
                    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
                    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
                
                    # 4. CÁLCULOS (LÓGICA FUNCIONAL INTEGRADA)
                    total_flete_2026 = df_filtered['COSTO DE FLETE'].sum()
                    total_fact_2026 = df_filtered['FACTURACION'].sum()
                    total_cajas_2026 = df_filtered['CAJAS'].sum()
                    total_valuacion_2026 = df_filtered['VALUACION'].sum()
                
                    meses_activos = df_filtered['MES'].unique()
                    df_2025_filtrado = df_2025[df_2025['MES'].isin(meses_activos)]
                    total_flete_2025 = df_2025_filtrado['COSTO DE LA GUIA'].sum()
                    total_cajas_2025 = df_2025_filtrado['CAJAS'].sum()
                
                    costo_caja_2026 = (total_flete_2026 / total_cajas_2026) if total_cajas_2026 > 0 else 0
                    costo_caja_2025 = (total_flete_2025 / total_cajas_2025) if total_cajas_2025 > 0 else 0
                    
                    var_costo_caja = ((costo_caja_2026 - costo_caja_2025) / costo_caja_2025 * 100) if costo_caja_2025 > 0 else 0
                    var_volumen = ((total_cajas_2026 - total_cajas_2025) / total_cajas_2025 * 100) if total_cajas_2025 > 0 else 0
                    var_flete_total = ((total_flete_2026 - total_flete_2025) / total_flete_2025 * 100) if total_flete_2025 > 0 else 0
                    
                    costo_log_real = (total_flete_2026/total_fact_2026*100) if total_fact_2026 > 0 else 0
                    diferencia_target = costo_log_real - 7.5
                    
                    # Lógica de incidencias del primer código
                    num_inc = (df_filtered['VALUACION'] > 0).sum()
                    pct_inc = (num_inc/len(df_filtered)*100) if len(df_filtered)>0 else 0
                    inc_vi_monto = (total_flete_2026 + total_valuacion_2026) - total_flete_2025
                
                    # 5. RENDERIZADO DE KPIs (PANTALLA)
                    st.markdown("### RESUMEN DE RENDIMIENTO")
                    k1, k2, k3, k4 = st.columns(4)
                    with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}", delta=f"{var_flete_total:.1f}% vs 2025", delta_color="inverse")
                    with k2: st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
                    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}", delta=f"{var_volumen:.1f}% Vol.", delta_color="off")
                    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%", delta=f"{diferencia_target:+.2f}% vs Target 7.5%", delta_color="inverse")
                
                    st.markdown("<br>", unsafe_allow_html=True)
                
                    k5, k6, k7, k8 = st.columns(4)
                    with k5: st.metric("COSTO POR CAJA", f"${costo_caja_2026:,.2f}", delta=f"{var_costo_caja:.1f}% vs 2025", delta_color="inverse")
                    with k6: st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion_2026:,.2f}")
                    with k7: st.metric("% DE INCIDENCIAS", f"{pct_inc:.1f}%")
                    with k8: st.metric("INCREMENTO + VI", f"${inc_vi_monto:,.2f}")
                
                    # 6. ANÁLISIS DINÁMICO
                    st.markdown("### ANÁLISIS DINÁMICO DE OPERACIÓN")
                    status_target = "🟢 DENTRO" if costo_log_real <= 7.5 else "🔴 FUERA"
                    status_eficiencia = "MÁS EFICIENTE" if var_costo_caja <= 0 else "MENOS EFICIENTE"
                    
                    html_analisis = f'''
                    <div class="analysis-box">
                        <b>Cumplimiento de Objetivos:</b> Actualmente la operación se encuentra <span class="highlight">{status_target}</span> del target logístico (7.5%), con un costo real del <span class="highlight">{costo_log_real:.2f}%</span> sobre la facturación bruta. <br><br>
                        <b>Análisis de Rendimiento Unitario:</b> El costo por caja ha variado un <span class="highlight">{var_costo_caja:+.1f}%</span> respecto al año pasado. Esto indica que operativamente hoy somos <span class="highlight">{status_eficiencia}</span> en la consolidación y despacho de mercancía de JYPESA.
                    </div>'''
                    st.markdown(html_analisis, unsafe_allow_html=True)
                
                    # 7. LÓGICA DE REPORTE PARA IMPRESIÓN
                    def generar_reporte_grafico():
                        estatus_rep = "DENTRO DE PARÁMETROS" if costo_log_real <= 7.5 else "FUERA DE PARÁMETROS"
                        pct_cumplimiento = max(0, min(100, (7.5 / costo_log_real) * 100)) if costo_log_real > 0 else 0
                        c_flete = "red" if var_flete_total > 0 else "green"
                        c_caja = "red" if var_costo_caja > 0 else "green"
                
                        html_content = f"""
                        <div id="printable-report" style="font-family: Arial, sans-serif; padding: 40px; color: #000; background: #fff; max-width: 900px; margin: auto; border: 1px solid #eee;">
                            <table style="width: 100%; border-bottom: 4px solid #000; margin-bottom: 20px;">
                                <tr>
                                    <td style="width: 50%;">
                                        <h1 style="margin: 0; font-size: 18px; font-weight: 900; letter-spacing: -1px; color: #000; border-bottom: none;">Jabones y Productos Especializados</h1>
                                        <p style="margin: 0; font-size: 11px; font-weight: bold; text-transform: uppercase;">Distribucion y Logística | 2026</p>
                                    </td>
                                    <td style="width: 50%; text-align: right; font-size: 11px;">
                                        <b>REPORTE ID:</b> LOG-{mes_sel[:3].upper()}-2026<br>
                                        <b>FECHA:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
                                        <span style="border: 2px solid #000; padding: 3px 8px; display: inline-block; margin-top: 5px; font-weight: bold;">{estatus_rep}</span>
                                    </td>
                                </tr>
                            </table>
                
                            <h2 style="text-align: center; text-transform: uppercase; margin-bottom: 30px; font-size: 18px; text-decoration: underline;">Análisis Operativo Mensual: {mes_sel}</h2>
                
                            <div style="margin-bottom: 40px;">
                                <p style="font-size: 12px; font-weight: bold; margin-bottom: 10px;">RENDIMIENTO VS META (TARGET 7.5%):</p>
                                <div style="width: 100%; border: 2px solid #000; height: 35px; position: relative; background: #f0f0f0;">
                                    <div style="width: {pct_cumplimiento}%; background: #444; height: 100%;"></div>
                                    <div style="position: absolute; top: 8px; left: 10px; color: #fff; font-weight: bold; font-size: 14px;">ACTUAL: {costo_log_real:.2f}%</div>
                                    <div style="position: absolute; top: 8px; right: 10px; color: #000; font-weight: bold; font-size: 14px;">OBJETIVO: 7.50%</div>
                                </div>
                            </div>
                
                            <div style="display: flex; gap: 20px; margin-bottom: 40px;">
                                <div style="flex: 1; border: 1px solid #000; padding: 10px;">
                                    <p style="margin: 0 0 10px 0; font-size: 10px; font-weight: bold; text-align: center; background: #000; color: #fff;">ESTRUCTURA DE COSTOS</p>
                                    <table style="width: 100%; font-size: 11px; border-collapse: collapse;">
                                        <tr><td>Gasto Flete:</td><td style="text-align: right; color:{c_flete}"><b>${total_flete_2026:,.2f}</b> ({var_flete_total:+.1f}%)</td></tr>
                                        <tr><td>Incidencias:</td><td style="text-align: right;"><b>${total_valuacion_2026:,.2f}</b></td></tr>
                                        <tr style="border-top: 1px solid #000;"><td><b>Total Op:</b></td><td style="text-align: right;"><b>${(total_flete_2026 + total_valuacion_2026):,.2f}</b></td></tr>
                                    </table>
                                </div>
                                <div style="flex: 1; border: 1px solid #000; padding: 10px;">
                                    <p style="margin: 0 0 10px 0; font-size: 10px; font-weight: bold; text-align: center; background: #000; color: #fff;">EFICIENCIA UNITARIA</p>
                                    <div style="text-align: center; padding-top: 5px;">
                                        <span style="font-size: 26px; font-weight: bold;">${costo_caja_2026:.2f}</span><br>
                                        <span style="font-size: 10px;">Costo por Caja</span><br>
                                        <span style="font-size: 11px; color:{c_caja}; font-weight:bold;">Var: {var_costo_caja:+.1f}% vs 2025</span>
                                    </div>
                                </div>
                            </div>
                
                            <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 50px;">
                                <thead>
                                    <tr style="background: #eee; border: 1px solid #000;">
                                        <th style="padding: 12px; text-align: left; border: 1px solid #000;">MÉTRICA DE OPERACIÓN</th>
                                        <th style="padding: 12px; text-align: center; border: 1px solid #000;">VALOR ACTUAL</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr><td style="padding: 10px; border: 1px solid #000;">Ventas Totales Brutas (Facturación)</td><td style="padding: 10px; border: 1px solid #000; text-align: center; font-weight:bold;">${total_fact_2026:,.2f}</td></tr>
                                    <tr><td style="padding: 10px; border: 1px solid #000;">Volumen de Despacho (Unidades)</td><td style="padding: 10px; border: 1px solid #000; text-align: center;">{int(total_cajas_2026):,.0f} Cajas</td></tr>
                                    <tr><td style="padding: 10px; border: 1px solid #000;">Variación Volumen vs 2025</td><td style="padding: 10px; border: 1px solid #000; text-align: center;">{var_volumen:+.1f}%</td></tr>
                                    <tr><td style="padding: 10px; border: 1px solid #000;">Impacto Económico Neto (INCR + VI)</td><td style="padding: 10px; border: 1px solid #000; text-align: center;">${inc_vi_monto:,.2f}</td></tr>
                                </tbody>
                            </table>
                
                            <div style="margin-top: 60px; display: flex; justify-content: space-between; text-align: center; font-size: 11px;">
                                <div style="width: 45%;">
                                    <div style="border-top: 2px solid #000; padding-top: 10px;">
                                        <b>HERNANPHY (RIGOBERTO)</b><br>Gerente de Logística JYPESA
                                    </div>
                                </div>
                                <div style="width: 45%;">
                                    <div style="border-top: 2px solid #000; padding-top: 10px;">
                                        <b>VALIDACIÓN NEXION</b><br>Ingeniería de Procesos
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                        return html_content
                
                    st.write("---")
                    if st.button(":material/print: GENERAR REPORTE GRÁFICO PARA IMPRESIÓN", type="primary", use_container_width=True):
                        reporte_html = generar_reporte_grafico()
                        
                        components.html(f"""
                            <script>
                                var win = window.open('', '', 'height=1100,width=950');
                                win.document.write('<html><head><title>Reporte_Tecnico_{mes_sel}</title></head><body>');
                                win.document.write(`{reporte_html}`);
                                win.document.write('</body></html>');
                                win.document.close();
                                win.onload = function() {{
                                    win.print();
                                    win.close();
                                }};
                            </script>
                        """, height=0)
                
                except Exception as e:
                    st.error(f"¡Atención, amor! Detalle en el código: {e}")
                            
            
            elif st.session_state.menu_sub == "ENVIOS ESPECIALES":
                # [Aquí va tu código o función para el reporte OTD]
                # --- VARIABLES DE GITHUB ---
                GITHUB_USER = "RH2026"
                GITHUB_REPO = "nexion"
                GITHUB_PATH = "CEE.csv"
                GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 
                
                # --- FUNCIONES GITHUB ---
                def obtener_datos_github():
                    try:
                        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
                        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
                        r = requests.get(url, headers=headers)
                        if r.status_code == 200:
                            content = r.json()
                            df = pd.read_csv(BytesIO(base64.b64decode(content['content'])))
                            return df, content['sha']
                    except:
                        pass
                    return pd.DataFrame(), None
                
                def subir_a_github(df, sha, msg):
                    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
                    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
                    csv_string = df.to_csv(index=False)
                    payload = {"message": msg, "content": base64.b64encode(csv_string.encode()).decode(), "sha": sha}
                    return requests.put(url, json=payload, headers=headers).status_code == 200
                
                # --- FUNCIÓN PARA GENERAR EL HTML DE IMPRESIÓN ---
                def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, tel_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, cajas, unidad, comentarios, paq_nombre, tipo_pago):
                    filas_prod = f"""
                    <tr>
                        <td style='padding: 8px; border: 1px solid black;'>ENVIO DE MERCANCÍA ESPECIAL</td>
                        <td style='text-align:center; border: 1px solid black;'>-</td>
                        <td style='text-align:center; border: 1px solid black;'>{str(unidad).upper()}</td>
                        <td style='text-align:center; border: 1px solid black;'>{cajas}</td>
                    </tr>"""
                
                    html = f"""
                    <div id="printable-area" style="font-family:Arial; border:2px solid black; padding:15px; width:700px; min-height:850px; margin:auto; position:relative; box-sizing:border-box; background: white; color: black;">
                        
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                            <div style="text-align: left;">
                                <h1 style="margin: 0; font-size: 16px; font-weight: 900; letter-spacing: -0.5px; color: #000;">Jabones y Productos Especializados</h1>
                                <p style="margin: 0; font-size: 10px; font-weight: bold; text-transform: uppercase;">Distribución y Logística | 2026</p>
                            </div>
                            <div style="text-align: right;">
                                <h2 style="margin: 0; font-size: 15px; text-decoration: underline; font-weight: 900;">ORDEN DE ENVÍO COSTOS ESPECIALES</h2>
                                <p style="margin: 2px 0 0 0; font-size: 12px;"><b>{paq_nombre} - {tipo_pago}</b></p>
                            </div>
                        </div>
                        
                        <table style="width:100%; border-collapse:collapse; margin-bottom:10px; font-size: 11px;">
                            <tr>
                                <td style="border:1px solid black; padding:4px;"><b>FOLIO:</b> {folio}</td>
                                <td style="border:1px solid black; padding:4px;"><b>ENVÍO:</b> {str(paq).upper()}</td>
                                <td style="border:1px solid black; padding:4px;"><b>ENTREGA:</b> {str(entrega).upper()}</td>
                                <td style="border:1px solid black; padding:4px;"><b>FECHA:</b> {fecha}</td>
                            </tr>
                        </table>
                    
                        <div style="display:flex; gap:5px; margin-bottom:10px;">
                            <div style="flex:1; border:1px solid black;">
                                <div style="background:black; color:white; text-align:center; font-weight:bold; font-size:11px; padding:2px;">REMITENTE</div>
                                <div style="padding:5px; font-size:10px; line-height:1.2;">
                                    <b>JABONES Y PRODUCTOS ESPECIALIZADOS</b><br>
                                    C. Cernícalo 155, La Aurora C.P.: 44460<br>
                                    ATN: {str(atn_rem).upper()}<br>
                                    TEL: {tel_rem}<br>
                                    SOLICITÓ: {str(solicitante).upper()}
                                </div>
                            </div>
                            <div style="flex:1; border:1px solid black;">
                                <div style="background:#b30000; color:white; text-align:center; font-weight:bold; font-size:11px; padding:2px;">DESTINATARIO</div>
                                <div style="padding:5px; font-size:10px; line-height:1.2;">
                                    <b>{str(hotel).upper()}</b><br>
                                    {str(calle).upper()}<br>
                                    Col: {str(col).upper()} C.P.: {cp}<br>
                                    {str(ciudad).upper()}, {str(estado).upper()}<br>
                                    ATN: {str(contacto).upper()}
                                </div>
                            </div>
                        </div>
                    
                        <table style="width:100%; border-collapse:collapse; margin-top:5px; font-size:11px;">
                            <tr style="background:#444; color:white;">
                                <th style="padding: 6px; border: 1px solid black;">DESCRIPCIÓN</th>
                                <th style="border: 1px solid black; width: 80px;">CÓDIGO</th>
                                <th style="border: 1px solid black; width: 60px;">U.M.</th>
                                <th style="border: 1px solid black; width: 60px;">CANT.</th>
                            </tr>
                            {filas_prod}
                        </table>
                    
                        <div style="border:1px solid black; padding:8px; margin-top:10px; font-size:11px; min-height: 60px;">
                            <b>COMENTARIOS:</b><br>{str(comentarios).upper()}
                        </div>
                    
                        <div style="position:absolute; bottom:30px; left:15px; right:15px;">
                            <div style="text-align:center; font-size:11px; font-weight:bold; margin-bottom:25px; border-bottom: 1px solid black; padding-bottom: 5px;">
                                RECIBO DE CONFORMIDAD DEL CLIENTE
                            </div>
                            <div style="display:flex; justify-content:space-between; text-align:center; font-size:10px;">
                                <div style="width:30%;">__________________________<br>FECHA RECIBO</div>
                                <div style="width:35%;">__________________________<br>NOMBRE Y FIRMA</div>
                                <div style="width:30%;">__________________________<br>SELLO DE RECIBIDO</div>
                            </div>
                        </div>
                    </div>
                    """
                    return html
                
                # --- CARGA DE DATOS ---
                df_actual, sha_actual = obtener_datos_github()
                nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1
                
                # --- INTERFAZ ---
                with st.container():
                    cp1, cp2 = st.columns(2)
                    f_paq_nombre = cp1.selectbox(":material/local_shipping: NOMBRE DE PAQUETERÍA", ["TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES", "FEDEX", "PAQMEX", "TINY PACK"])
                    f_tipo_pago = cp2.selectbox(":material/payments: MODALIDAD DE PAGO", ["CREDITO", "COBRO DESTINO"])
                    st.write("") 
                    c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])
                    f_folio = c1.text_input(":material/confirmation_number: FOLIO", value=str(nuevo_folio), disabled=True)
                    f_paq_sel = c2.selectbox(":material/local_shipping: FORMA DE ENVÍO", ["Envio Pagado", "Envio por cobrar", "Entrega Personal"])
                    f_ent_sel = c3.selectbox(":material/home_pin: TIPO DE ENTREGA", ["Domicilio", "Ocurre Oficina"])
                    f_fecha_sel = c4.date_input(":material/calendar_today: FECHA", date.today())
                
                st.divider()
                
                col_rem, col_dest = st.columns(2)
                with col_rem:
                    st.markdown('<div style="background:#CCDCE2;color:black;text-align:center;font-weight:bold;padding:10px;border-radius:4px;letter-spacing:1px;">REMITENTE</div>', unsafe_allow_html=True)
                    st.write("")
                    st.text_input(":material/corporate_fare: Nombre", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
                    c_rem1, c_rem2 = st.columns([2, 1])
                    f_atn_rem = c_rem1.text_input(":material/person: Atención", "RIGOBERTO HERNANDEZ")
                    f_tel_rem = c_rem2.text_input(":material/call: Teléfono", "3319753122")
                    f_soli = st.text_input(":material/badge: Solicitante / Agente", placeholder="NOMBRE DE QUIEN SOLICITA").upper()
                
                with col_dest:
                    st.markdown('<div style="background:#2276AA;color:white;text-align:center;font-weight:bold;padding:10px;border-radius:4px;letter-spacing:1px;">DESTINATARIO</div>', unsafe_allow_html=True)
                    st.write("")
                    f_h = st.text_input(":material/hotel: Hotel / Proveedor").upper()
                    f_ca = st.text_input(":material/location_on: Calle y Número").upper()
                    cd1, cd2 = st.columns(2)
                    f_co = cd1.text_input(":material/map: Colonia").upper()
                    f_cp = cd2.text_input(":material/mailbox: C.P.")
                    cd3, cd4 = st.columns(2)
                    f_ci = cd3.text_input(":material/location_city: Ciudad").upper()
                    f_es = cd4.text_input(":material/public: Estado").upper()
                    f_con = st.text_input(":material/contact_phone: Contacto Receptor", placeholder="QUIEN RECIBE").upper()
                
                st.divider()
                st.subheader(":material/inventory_2: Detalles del Envío")
                cd_1, cd_2 = st.columns(2)
                f_cajas = cd_1.number_input("CANTIDAD", min_value=1, step=1)
                f_unidad = cd_2.selectbox("UNIDAD DE MEDIDA", ["CAJA", "PALLET", "BULTO", "SACO", "BIDON", "ATADO", "OTRO"])
                
                f_costo_guia = st.number_input("COSTO DE GUÍA ($)", min_value=0.0, step=10.0)
                f_coment = st.text_area("💬 COMENTARIOS", height=70).upper()
                
                col_b1, col_b2, col_b3 = st.columns([1, 1, 0.5]) 
                if col_b1.button(":material/save: GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
                    if not f_h: st.error("Falta el hotel")
                    else:
                        direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()
                        reg = {
                            "FOLIO": nuevo_folio, "FECHA": f_fecha_sel.strftime("%Y-%m-%d"), 
                            "NOMBRE DEL HOTEL": f_h.upper(), "DESTINO": direccion_completa,
                            "CONTACTO": f_con.upper(), "SOLICITO": f_soli.upper() if f_soli else "JYPESA", 
                            "PAQUETERIA": f_paq_sel.upper(), "PAQUETERIA_NOMBRE": f_paq_nombre, 
                            "NUMERO_GUIA": "", "COSTO_GUIA": f_costo_guia, "CAJAS": f_cajas, "UNIDAD": f_unidad
                        }
                        df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
                        if subir_a_github(df_f, sha_actual, f"Folio CEE {nuevo_folio}"):
                            st.success(f"¡Guardado!"); time.sleep(1); st.rerun()
                
                if col_b2.button(":material/print: IMPRIMIR ESTE FOLIO", use_container_width=True):
                    h_print = generar_html_impresion(nuevo_folio, f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem, f_soli if f_soli else "JYPESA", f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, f_cajas, f_unidad, f_coment, f_paq_nombre, f_tipo_pago)
                    components.html(f"<html><body>{h_print}<script>window.print();</script></body></html>", height=0)
                
                if col_b3.button(":material/delete_sweep: BORRAR", use_container_width=True):
                    st.rerun()
                
                # --- PANEL DE ADMIN ---
                st.divider()
                st.markdown("### 🛠 PANEL DE ADMINISTRACIÓN")
                t1, t2 = st.tabs(["Gestionar Folios", "Historial y Reportes"])
                
                with t1:
                    if not df_actual.empty:
                        df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
                        opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]
                        fol_sel_texto = st.selectbox("Seleccionar Folio para Editar:", opciones_folios, index=None)
                        fol_edit = ""; datos_fol = None
                        if fol_sel_texto:
                            fol_edit = int(fol_sel_texto.split(" - ")[0]); datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]
                
                        c_adm1, c_adm2 = st.columns(2)
                        with c_adm1:
                            st.markdown(f'<div style="background:#5c7aff;color:white;padding:10px;border-radius:5px;">Actualizar Folio {fol_edit}</div>', unsafe_allow_html=True)
                            n_gui = st.text_input("Número de Guía", value=str(datos_fol["NUMERO_GUIA"]) if datos_fol is not None else "").upper()
                            c_gui = st.number_input("Costo Guía", value=float(datos_fol["COSTO_GUIA"]) if datos_fol is not None else 0.0)
                            if st.button(":material/update: ACTUALIZAR", use_container_width=True):
                                if datos_fol is not None:
                                    idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                                    df_actual.at[idx, "NUMERO_GUIA"] = n_gui; df_actual.at[idx, "COSTO_GUIA"] = c_gui
                                    if subir_a_github(df_actual, sha_actual, f"Edit {fol_edit}"):
                                        st.success("¡Listo!"); time.sleep(1); st.rerun()
                
                        with c_adm2:
                            st.markdown('<div style="background:#f6c23e;color:black;padding:10px;border-radius:5px;">Re-impresión</div>', unsafe_allow_html=True)
                            if st.button(":material/print: RE-IMPRIMIR", use_container_width=True):
                                if datos_fol is not None:
                                    u_med = datos_fol["UNIDAD"] if "UNIDAD" in datos_fol else "CAJAS"
                                    h_re = generar_html_impresion(fol_edit, datos_fol["PAQUETERIA"], "Domicilio", datos_fol["FECHA"], "RIGOBERTO HERNANDEZ", "3319753122", datos_fol["SOLICITO"], datos_fol["NOMBRE DEL HOTEL"], "-", "-", "-", datos_fol["DESTINO"], "", datos_fol["CONTACTO"], datos_fol["CAJAS"], u_med, "RE-IMPRESIÓN", datos_fol["PAQUETERIA_NOMBRE"], "S/P")
                                    components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)
                
                with t2:
                    if not df_actual.empty:
                        st.dataframe(df_actual, use_container_width=True)
                        t_flete = df_actual["COSTO_GUIA"].sum()
                        filas_html = ""
                        for _, r in df_actual.iterrows():
                            u_r = r['UNIDAD'] if 'UNIDAD' in r else 'CAJAS'
                            filas_html += f"<tr><td style='border:1px solid black;padding:8px;'>{r['FOLIO']}</td><td style='border:1px solid black;padding:8px;'><b>{str(r['SOLICITO']).upper()}</b><br><small>{r['FECHA']}</small></td><td style='border:1px solid black;padding:8px;'>{str(r['NOMBRE DEL HOTEL']).upper()}<br><small>{str(r['DESTINO']).upper()}</small></td><td style='border:1px solid black;padding:8px;'>ENVIO ESPECIAL: {int(r['CAJAS'])} {u_r}</td><td style='border:1px solid black;padding:8px;text-align:right;'>${r['COSTO_GUIA']:,.2f}</td></tr>"
                
                        form_pt_html = f"""
                        <html><head><style>body{{font-family:sans-serif;}} table{{width:100%;border-collapse:collapse;margin-top:15px;font-size:11px;}} th{{background:#eee;border:1px solid black;padding:8px;}}</style></head>
                        <body>
                            <div style="display:flex;justify-content:space-between;border-bottom:2px solid black;padding-bottom:10px;">
                                <div><h2>JYPESA</h2><p style="margin:0;font-size:10px;">REPORTE DE COSTOS ESPECIALES</p></div>
                                <div style="text-align:right;">GENERADO: {date.today()}</div>
                            </div>
                            <table><thead><tr><th>FOLIO</th><th>SOLICITANTE</th><th>DESTINO</th><th>DETALLE</th><th>FLETE</th></tr></thead>
                            <tbody>{filas_html}</tbody></table>
                            <div style="text-align:right;margin-top:20px;border-top:1px solid black;">
                                <h3>TOTAL INVERSIÓN FLETES: ${t_flete:,.2f}</h3>
                            </div>
                        </body></html>"""
                
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button(":material/print: IMPRIMIR REPORTE GENERAL", type="primary", use_container_width=True):
                                components.html(f"<html><body>{form_pt_html}<script>window.print();</script></body></html>", height=0)
                        with c2:
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_actual.to_excel(writer, index=False)
                            st.download_button(":material/download: DESCARGAR EXCEL", data=output.getvalue(), file_name=f"Matriz_CEE_{date.today()}.xlsx", use_container_width=True)
                        with c3:
                            if st.button(":material/update: REFRESCAR DATOS", use_container_width=True): st.rerun()  
                
                                
                                

            elif st.session_state.menu_sub == "ENVIO DE MUESTRAS":
                # --- VARIABLES DE GITHUB ---
                GITHUB_USER = "RH2026"
                GITHUB_REPO = "nexion"
                GITHUB_PATH = "muestras.csv"
                GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 
                
                # Diccionario de precios SINCRONIZADO
                precios = {
                    "Envio Muestras Especiales": 0.0,
                    "Accesorios Ecologicos": 47.85,
                    "Accesorios Lavarino": 47.85,
                    "Dispensador Almond": 218.33,
                    "Dispensador Biogena": 216.00,
                    "Dispensador Cava": 230.58,
                    "Dispensador Persea": 275.00,
                    "Dispensador Botánicos": 274.17,
                    "Dispensador Dove": 125.00,
                    "Kit Elements": 29.34,
                    "Kit Almond": 33.83,
                    "Kit Biogena": 48.95,
                    "Kit Cava": 34.59,
                    "Kit Persa": 58.02,
                    "Kit Lavarino": 36.30,
                    "Kit Botánicos": 29.34,
                    "Kit Rainforest": 30.34,
                    "Llave Magnetica": 180.00,
                    "Rack Dove": 0.00,
                    "Rack JH  Color Blanco de 2 pzas": 62.00,
                    "Rack JH  Color Blanco de 1 pzas": 50.00,
                    "Soporte dob INOX Cap lock": 679.00,
                    "Soporte Ind INOX Cap lock": 608.00
                }
                
                # --- FUNCIONES GITHUB ---
                def obtener_datos_github():
                    try:
                        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
                        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
                        r = requests.get(url, headers=headers)
                        if r.status_code == 200:
                            content = r.json()
                            df = pd.read_csv(BytesIO(base64.b64decode(content['content'])))
                            return df, content['sha']
                    except:
                        pass
                    return pd.DataFrame(), None
                
                def subir_a_github(df, sha, msg):
                    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
                    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
                    csv_string = df.to_csv(index=False)
                    payload = {"message": msg, "content": base64.b64encode(csv_string.encode()).decode(), "sha": sha}
                    return requests.put(url, json=payload, headers=headers).status_code == 200
                
                # --- FUNCIÓN PARA GENERAR EL HTML DE IMPRESIÓN ---
                def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, tel_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, productos, comentarios, paq_nombre, tipo_pago):
                    filas_prod = ""
                    for p in productos:
                        filas_prod += f"""
                        <tr>
                            <td style='padding: 8px; border: 1px solid black;'>{str(p['desc']).upper()}</td>
                            <td style='text-align:center; border: 1px solid black;'>-</td>
                            <td style='text-align:center; border: 1px solid black;'>PZAS</td>
                            <td style='text-align:center; border: 1px solid black;'>{p['cant']}</td>
                        </tr>"""
                
                    html = f"""
                    <div id="printable-area" style="font-family:Arial; border:2px solid black; padding:30px; width:780px; margin:20px auto; box-sizing:border-box; background: white; color: black; min-height: 1000px; display: flex; flex-direction: column;">
                        
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                            <div style="text-align: left;">
                                <h1 style="margin: 0; font-size: 18px; font-weight: 900; color: #000;">Jabones y Productos Especializados</h1>
                                <p style="margin: 0; font-size: 11px; font-weight: bold; text-transform: uppercase; color: #444;">Distribución y Logística | 2026</p>
                            </div>
                            <div style="text-align: right;">
                                <h2 style="margin: 0; font-size: 16px; text-decoration: underline; font-weight: 900;">ORDEN DE ENVÍO MUESTRAS</h2>
                                <p style="margin: 5px 0 0 0; font-size: 13px;"><b>{paq_nombre} - {tipo_pago}</b></p>
                            </div>
                        </div>
                        
                        <table style="width:100%; border-collapse:collapse; margin-bottom:15px; font-size: 12px;">
                            <tr>
                                <td style="border:1px solid black; padding:6px;"><b>FOLIO:</b> {folio}</td>
                                <td style="border:1px solid black; padding:6px;"><b>ENVÍO:</b> {str(paq).upper()}</td>
                                <td style="border:1px solid black; padding:6px;"><b>ENTREGA:</b> {str(entrega).upper()}</td>
                                <td style="border:1px solid black; padding:6px;"><b>FECHA:</b> {fecha}</td>
                            </tr>
                        </table>
                    
                        <div style="display:flex; gap:10px; margin-bottom:15px;">
                            <div style="flex:1; border:1px solid black;">
                                <div style="background:black; color:white; text-align:center; font-weight:bold; font-size:12px; padding:4px;">REMITENTE</div>
                                <div style="padding:8px; font-size:11px; line-height:1.4;">
                                    <b>JABONES Y PRODUCTOS ESPECIALIZADOS</b><br>
                                    C. Cernícalo 155, La Aurora C.P.: 44460<br>
                                    ATN: {str(atn_rem).upper()}<br>
                                    TEL: {tel_rem}<br>
                                    SOLICITÓ: {str(solicitante).upper()}
                                </div>
                            </div>
                            <div style="flex:1; border:1px solid black;">
                                <div style="background:#b30000; color:white; text-align:center; font-weight:bold; font-size:12px; padding:4px;">DESTINATARIO</div>
                                <div style="padding:8px; font-size:11px; line-height:1.4;">
                                    <b>{str(hotel).upper()}</b><br>
                                    {str(calle).upper()}<br>
                                    Col: {str(col).upper()} C.P.: {cp}<br>
                                    {str(ciudad).upper()}, {str(estado).upper()}<br>
                                    ATN: {str(contacto).upper()}
                                </div>
                            </div>
                        </div>
                    
                        <div style="flex-grow: 1;">
                            <table style="width:100%; border-collapse:collapse; margin-top:5px; font-size:12px;">
                                <tr style="background:#444; color:white;">
                                    <th style="padding: 8px; border: 1px solid black;">DESCRIPCIÓN DEL PRODUCTO</th>
                                    <th style="border: 1px solid black; width: 100px;">CÓDIGO</th>
                                    <th style="border: 1px solid black; width: 80px;">U.M.</th>
                                    <th style="border: 1px solid black; width: 80px;">CANT.</th>
                                </tr>
                                {filas_prod}
                            </table>
                            
                            <div style="border:1px solid black; padding:10px; margin-top:15px; font-size:12px; min-height: 80px;">
                                <b>COMENTARIOS:</b><br>{str(comentarios).upper()}
                            </div>
                        </div>
                    
                        <div style="margin-top: 40px; padding-top: 20px;">
                            <div style="text-align:center; font-size:12px; font-weight:bold; margin-bottom:40px; border-bottom: 2px solid black; padding-bottom: 8px;">
                                RECIBO DE CONFORMIDAD DEL CLIENTE
                            </div>
                            <div style="display:flex; justify-content:space-between; text-align:center; font-size:11px;">
                                <div style="width:30%;">__________________________<br><b>FECHA RECIBO</b></div>
                                <div style="width:35%;">__________________________<br><b>NOMBRE Y FIRMA</b></div>
                                <div style="width:30%;">__________________________<br><b>SELLO DE RECIBIDO</b></div>
                            </div>
                        </div>
                    </div>
                    """
                    return html
                
                # --- CARGA DE DATOS ---
                df_actual, sha_actual = obtener_datos_github()
                if not df_actual.empty:
                    for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL"]:
                        if col not in df_actual.columns: df_actual[col] = 0.0
                
                nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1
                
                # --- INTERFAZ ---
                
                # --- CAPTURA NUEVA ---
                with st.container():
                    # NUEVOS INPUTS SOLICITADOS CON ICONOS MATERIAL
                    cp1, cp2 = st.columns(2)
                    f_paq_nombre = cp1.selectbox(
                        ":material/local_shipping: NOMBRE DE PAQUETERÍA", 
                        ["TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES", "FEDEX", "PAQMEX", "TINY PACK",""]
                    )
                    f_tipo_pago = cp2.selectbox(
                        ":material/payments: MODALIDAD DE PAGO", 
                        ["CREDITO", "COBRO DESTINO"]
                    )
                    
                    st.write("") # Espaciador
                    
                    c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])
                    # Usamos str(nuevo_folio) como lo tienes en tu lógica
                    f_folio = c1.text_input(":material/confirmation_number: FOLIO", value=str(nuevo_folio), disabled=True)
                    f_paq_sel = c2.selectbox(
                        ":material/local_shipping: FORMA DE ENVÍO", 
                        ["Envio Pagado", "Envio por cobrar", "Entrega Personal"]
                    )
                    f_ent_sel = c3.selectbox(
                        ":material/home_pin: TIPO DE ENTREGA", 
                        ["Domicilio", "Ocurre Oficina"]
                    )
                    f_fecha_sel = c4.date_input(":material/calendar_today: FECHA", date.today())
                
                st.divider()
                
                col_rem, col_dest = st.columns(2)
                with col_rem:
                    st.markdown(
                        '<div style="background:#4e73df;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">REMITENTE</div>', 
                        unsafe_allow_html=True
                    )
                    st.write("")
                    st.text_input(":material/corporate_fare: Nombre", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
                    
                    c_rem1, c_rem2 = st.columns([2, 1])
                    f_atn_rem = c_rem1.text_input(":material/person: Atención", "RIGOBERTO HERNANDEZ")
                    f_tel_rem = c_rem2.text_input(":material/call: Teléfono", "3319753122")
                    f_soli = st.text_input(
                        ":material/badge: Solicitante / Agente", 
                        placeholder="NOMBRE DE QUIEN SOLICITA LAS MUESTRAS"
                    ).upper()
                
                with col_dest:
                    st.markdown(
                        '<div style="background:#f6c23e;color:black;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">DESTINATARIO / HOTEL</div>', 
                        unsafe_allow_html=True
                    )
                    st.write("")
                    f_h = st.text_input(":material/hotel: Hotel / Nombre").upper()
                    f_ca = st.text_input(":material/location_on: Calle y Número").upper()
                    
                    cd1, cd2 = st.columns(2)
                    f_co = cd1.text_input(":material/map: Colonia").upper()
                    f_cp = cd2.text_input(":material/mailbox: C.P.")
                    
                    cd3, cd4 = st.columns(2)
                    f_ci = cd3.text_input(":material/location_city: Ciudad").upper()
                    f_es = cd4.text_input(":material/public: Estado").upper()
                    f_con = st.text_input(
                        ":material/contact_phone: Contacto Receptor", 
                        placeholder="NOMBRE Y TELÉFONO DE QUIEN RECIBE"
                    ).upper()
                
                st.divider()
                
                # --- PRODUCTOS ---                
                # 1. CSS PARA QUE EL MULTISELECT CREZCA Y SE VEA PRO
                st.markdown("""
                    <style>
                    .stMultiSelect div[data-baseweb="select"] {
                        height: auto !important;
                        min-height: 45px !important;
                    }
                    .stMultiSelect div[data-baseweb="valueContainer"] {
                        flex-wrap: wrap !important;
                        display: flex !important;
                        gap: 5px !important;
                        padding: 5px 0 !important;
                    }
                    .stMultiSelect div[data-baseweb="tag"] {
                        background-color: #384A52 !important;
                        border-radius: 5px;
                        color: white !important;
                    }
                    div[data-testid="stNumberInput"] {
                        width: 100% !important;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                st.subheader(":material/shopping_cart: Selección de Productos")
                
                if "seleccionados_muestras" not in st.session_state:
                    st.session_state.seleccionados_muestras = []
                
                def eliminar_producto(prod_a_borrar):
                    st.session_state.seleccionados_muestras = [p for p in st.session_state.seleccionados_muestras if p != prod_a_borrar]
                    st.session_state.multi_prods_main = st.session_state.seleccionados_muestras
                
                seleccionados = st.multiselect(
                    ":material/search: Busca y selecciona productos:", 
                    list(precios.keys()),
                    key="multi_prods_main",
                    default=st.session_state.seleccionados_muestras,
                    placeholder="Selecciona los productos a enviar..." # <--- AQUÍ CAMBIAS EL TEXTO
                )
                
                st.session_state.seleccionados_muestras = seleccionados
                
                prods_actuales = []
                total_cantidad = 0
                total_costo_prods = 0
                
                if seleccionados:
                    st.info(f"Has seleccionado {len(seleccionados)} productos. Indica las cantidades abajo:")
                    
                    # --- CÁLCULO DINÁMICO DE LA ALTURA ---
                    # Calculamos cuántas filas hay (3 productos por fila)
                    num_filas = (len(seleccionados) + 2) // 3  
                    # Altura base por fila (aprox 90px) + un pequeño margen
                    # Ponemos un máximo de 500px para que no se coma toda la pantalla si son muchísimos
                    altura_dinamica = min(max(num_filas * 95, 120), 500) 
                    
                    with st.container(height=altura_dinamica, border=True):
                        col_bloque_1, col_bloque_2, col_bloque_3 = st.columns(3)
                        
                        for i, p in enumerate(seleccionados):
                            if i % 3 == 0:
                                target_col = col_bloque_1
                            elif i % 3 == 1:
                                target_col = col_bloque_2
                            else:
                                target_col = col_bloque_3
                            
                            with target_col:
                                c1, c2, c3 = st.columns([1.5, 1.8, 0.5])
                                
                                with c1:
                                    st.markdown(f"<div style='padding-top:10px; font-size:10px; line-height:1.1;'><b>{p.upper()}</b></div>", unsafe_allow_html=True)
                                
                                with c2:
                                    q = st.number_input("Cant", min_value=0, step=1, key=f"q_{p}", label_visibility="collapsed")
                                
                                with c3:
                                    st.button(":material/delete:", key=f"btn_del_{p}", type="tertiary", on_click=eliminar_producto, args=(p,))
                
                                if q > 0:
                                    prods_actuales.append({"desc": p, "cant": q})
                                    total_cantidad += q
                                    total_costo_prods += (q * (precios.get(p, 0)))
                                
                                st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)
                
                st.markdown("---")
                f_coment = st.text_area("💬 COMENTARIOS ADICIONALES", height=100).upper()
                
                # --- BOTONES PRINCIPALES ---
                col_b1, col_b2, col_b3 = st.columns([1, 1, 0.5]) 
                
                if col_b1.button(":material/save: GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
                    if not f_h: st.error("Falta el hotel")
                    elif not prods_actuales: st.error("Selecciona al menos un producto")
                    else:
                        direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()
                        reg = {
                            "FOLIO": nuevo_folio, "FECHA": f_fecha_sel.strftime("%Y-%m-%d"), 
                            "NOMBRE DEL HOTEL": f_h.upper(), "DESTINO": direccion_completa,
                            "CONTACTO": f_con.upper(), "SOLICITO": f_soli.upper() if f_soli else "JYPESA", "PAQUETERIA": f_paq_sel.upper(),
                            "PAQUETERIA_NOMBRE": "", "NUMERO_GUIA": "", "COSTO_GUIA": 0.0,
                            "CANTIDAD_TOTAL": total_cantidad,
                            "COSTO_TOTAL": round(total_costo_prods, 2)
                        }
                        for p, cant in cants_dict.items(): reg[p] = cant
                        df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
                        if subir_a_github(df_f, sha_actual, f"Folio {nuevo_folio}"):
                            st.success(f"¡Guardado! Costo: ${total_costo_prods}"); time.sleep(1); st.rerun()
                
                if col_b2.button(":material/print: IMPRIMIR ESTE FOLIO", use_container_width=True):
                    if not prods_actuales: st.warning("No hay productos")
                    else:
                        # Se pasan los nuevos campos a la función de impresión
                        h_print = generar_html_impresion(nuevo_folio, f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem, f_soli if f_soli else "JYPESA", f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, prods_actuales, f_coment, f_paq_nombre, f_tipo_pago)
                        components.html(f"<html><body>{h_print}<script>window.print();</script></body></html>", height=0)
                
                if col_b3.button(":material/delete_sweep: BORRAR", use_container_width=True):
                    st.rerun()
                
                # --- BÚSQUEDA RÁPIDA ---
                st.write("")
                with st.expander("🔍 BÚSQUEDA RÁPIDA DE GUÍAS (CONSULTA DE FOLIOS)", expanded=False):
                    if not df_actual.empty:
                        busqueda = st.text_input("Escribe el nombre del Hotel o Folio para filtrar:").upper()
                        df_vista = df_actual[["FOLIO", "FECHA", "NOMBRE DEL HOTEL", "PAQUETERIA_NOMBRE", "NUMERO_GUIA"]].copy()
                        df_vista.columns = ["FOLIO", "FECHA ENVÍO", "HOTEL", "PAQUETERÍA", "NÚMERO DE GUÍA"]
                        if busqueda:
                            df_vista = df_vista[df_vista.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
                        st.dataframe(df_vista.sort_values(by="FOLIO", ascending=False), use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay registros todavía.")
                
                # --- PANEL DE ADMIN ---
                # --- PANEL DE ADMIN ---
                st.divider()
                st.markdown("### 🛠 PANEL DE ADMINISTRACIÓN")
                t1, t2 = st.tabs(["Gestionar Folios Existentes", "Historial y Reportes"])
                
                with t1:
                    if not df_actual.empty:
                        df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
                        opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]
                        
                        fol_sel_texto = st.selectbox(
                            "Seleccionar Folio para Editar:", 
                            opciones_folios, 
                            index=None, 
                            placeholder="Busca un folio para cargar datos..."
                        )
                
                        # --- Lógica de carga de datos ---
                        # Inicializamos variables vacías por defecto
                        fol_edit = ""
                        datos_fol = None
                        
                        # Si hay algo seleccionado, llenamos las variables con la info real
                        if fol_sel_texto:
                            fol_edit = int(fol_sel_texto.split(" - ")[0])
                            datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]
                
                        # --- Interfaz siempre visible ---
                        c_adm1, c_adm2 = st.columns(2)
                        
                        with c_adm1:
                            st.markdown(f'<div style="background:#4e73df;color:white;padding:10px;border-radius:5px;">Actualizar envío - Folio {fol_edit}</div>', unsafe_allow_html=True)
                            st.write("")
                            
                            # El truco está en el "value": si datos_fol existe, pone el valor; si no, pone "" o 0.0
                            n_paq = st.text_input("Empresa de Paquetería", key="edit_paq", 
                                                 value=str(datos_fol["PAQUETERIA_NOMBRE"]) if datos_fol is not None else "").upper()
                            
                            n_gui = st.text_input("Número de Guía", key="edit_guia", 
                                                 value=str(datos_fol["NUMERO_GUIA"]) if datos_fol is not None else "").upper()
                            
                            c_gui = st.number_input("Costo de Guía ($)", key="edit_costo", 
                                                   value=float(datos_fol["COSTO_GUIA"]) if datos_fol is not None else 0.0)
                            
                            # El botón solo funciona si realmente se seleccionó un folio
                            if st.button(":material/update: ACTUALIZAR DATOS DE ENVÍO", use_container_width=True):
                                if datos_fol is not None:
                                    idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                                    df_actual.at[idx, "PAQUETERIA_NOMBRE"] = n_paq.upper()
                                    df_actual.at[idx, "NUMERO_GUIA"] = n_gui.upper()
                                    df_actual.at[idx, "COSTO_GUIA"] = c_gui
                                    if subir_a_github(df_actual, sha_actual, f"Guía {fol_edit}"):
                                        st.success("¡Datos actualizados!"); time.sleep(1); st.rerun()
                                else:
                                    st.warning("Primero debes seleccionar un folio de la lista superior.")
                        
                        with c_adm2:
                            st.markdown('<div style="background:#f6c23e;color:black;padding:10px;border-radius:5px;">Re-impresión de Documento</div>', unsafe_allow_html=True)
                            st.write("")
                            if st.button(":material/print: RE-GENERAR FORMATO E IMPRIMIR", use_container_width=True):
                                if datos_fol is not None:
                                    prods_re = []
                                    for p in precios.keys():
                                        if p in datos_fol and datos_fol[p] > 0: 
                                            prods_re.append({"desc": p, "cant": int(datos_fol[p])})
                                    
                                    h_re = generar_html_impresion(
                                        fol_edit, datos_fol["PAQUETERIA"], "Domicilio", datos_fol["FECHA"], 
                                        "RIGOBERTO HERNANDEZ", "3319753122", datos_fol["SOLICITO"], 
                                        datos_fol["NOMBRE DEL HOTEL"], "-", "-", "-", datos_fol["DESTINO"], 
                                        "", datos_fol["CONTACTO"], prods_re, "RE-IMPRESIÓN", "S/P", "S/D"
                                    )
                                    components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)
                                else:
                                    st.warning("Selecciona un folio para poder imprimir.")
                
                with t2:
                    if not df_actual.empty:
                        st.dataframe(df_actual, use_container_width=True)
                        t_prod = df_actual["COSTO_TOTAL"].sum()
                        t_flete = df_actual["COSTO_GUIA"].sum()
                        filas_html = ""
                        for _, r in df_actual.iterrows():
                            detalle_p = ""
                            for p in precios.keys():
                                cant = r.get(p, 0)
                                if cant > 0: detalle_p += f"• {int(cant)} PZAS {str(p).upper()}<br>"
                            filas_html += f"<tr><td style='border:1px solid black;padding:8px;'>{r['FOLIO']}</td><td style='border:1px solid black;padding:8px;'><b>{str(r['SOLICITO']).upper()}</b><br><small>{r['FECHA']}</small></td><td style='border:1px solid black;padding:8px;'>{str(r['NOMBRE DEL HOTEL']).upper()}<br><small>{str(r['DESTINO']).upper()}</small></td><td style='border:1px solid black;padding:8px;font-size:10px;'>{detalle_p}</td><td style='border:1px solid black;padding:8px;text-align:right;'>${r['COSTO_TOTAL']:,.2f}</td><td style='border:1px solid black;padding:8px;text-align:right;'>${r['COSTO_GUIA']:,.2f}</td></tr>"
                
                        form_pt_html = f"""
                        <html><head><style>@media print{{body{{padding:15mm;}} .no-print{{display:none;}}}} body{{font-family:sans-serif;}} table{{width:100%;border-collapse:collapse;margin-top:15px;font-size:11px;}} th{{background:#eee;border:1px solid black;padding:8px;}}</style></head>
                        <body>
                            <div style="display:flex;justify-content:space-between;border-bottom:2px solid black;padding-bottom:10px;">
                                <div><h2>JYPESA</h2><p style="margin:0;font-size:10px;">AUTOMATIZACIÓN DE PROCESOS</p></div>
                                <div style="text-align:right;"><b>REPORTE DE SALIDA DE ENVIOS Y MUESTRAS</b><br>GENERADO: {date.today()}</div>
                            </div>
                            <table><thead><tr><th>FOLIO</th><th>SOLICITANTE</th><th>DESTINO</th><th>DETALLE</th><th>COSTO PROD.</th><th>FLETE</th></tr></thead>
                            <tbody>{filas_html}</tbody></table>
                            <div style="text-align:right;margin-top:20px;border-top:1px solid black;">
                                <p>TOTAL PRODUCTOS: ${t_prod:,.2f}</p><p>TOTAL FLETES: ${t_flete:,.2f}</p><h3>INVERSIÓN TOTAL: ${(t_prod+t_flete):,.2f}</h3>
                            </div>
                        </body></html>"""
                
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button(":material/print: IMPRIMIR REPORTE", type="primary", use_container_width=True):
                                components.html(f"<html><body>{form_pt_html}<script>window.print();</script></body></html>", height=0)
                        with c2:
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_actual.to_excel(writer, index=False)
                            st.download_button(":material/download: DESCARGAR EXCEL", data=output.getvalue(), file_name=f"Matriz_{date.today()}.xlsx", use_container_width=True)
                        with c3:
                            if st.button(":material/update: ACTUALIZAR DATOS", use_container_width=True): st.rerun()
        
    
        # ── 4. MÓDULO DE FORMATOS (BLOQUE MAESTRO CONSOLIDADO) ────────────────────
        elif st.session_state.menu_main == "FORMATOS":
            import streamlit.components.v1 as components
            import os
    
            # --- SUBSECCIÓN A: SALIDA DE PT ---
            if st.session_state.menu_sub == "SALIDA DE PT":
                
                # ── A. GENERACIÓN DE FOLIO CON HORA DE GUADALAJARA ──
                if 'folio_nexion' not in st.session_state:
                    tz_gdl = pytz.timezone('America/Mexico_City') 
                    now_gdl = datetime.now(tz_gdl)
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
                    f_val = h1.date_input(":material/calendar_month: FECHA", value=datetime.now(), key="f_in_pt")
                    t_val = h2.selectbox(":material/schedule: TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_in_pt")
                    fol_val = h3.text_input(":material/fingerprint: FOLIO", value=st.session_state.folio_nexion, key="fol_in_pt")
                                        
                
                # ── NUEVA SECCIÓN: BÚSQUEDA AUXILIAR ──────────────────────────
                with st.expander(":material/search: Buscar Codigo", expanded=False):
                    busqueda = st.text_input("Escribe el nombre del producto o código (ej. Cepillo, Gorra, Elemnts, Cava):").strip().upper()
                    if busqueda:
                        resultados = df_inv[
                            df_inv['CODIGO'].astype(str).str.contains(busqueda, na=False) | 
                            df_inv['DESCRIPCION'].astype(str).str.upper().str.contains(busqueda, na=False)
                        ]
                        if not resultados.empty:
                            st.dataframe(resultados, use_container_width=True, hide_index=True)
                        else:
                            st.warning("No se encontraron coincidencias en el inventario.")
                
                
                # ── D. MOTOR DE BÚSQUEDA INTERNO (LOOKUP) ──────────────────────────
                def lookup_pt():
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
                df_final_pt = st.data_editor(
                    st.session_state.rows, 
                    num_rows="dynamic", 
                    use_container_width=True, 
                    key="editor_pt", 
                    on_change=lookup_pt,
                    column_config={
                        "CODIGO": st.column_config.TextColumn("CÓDIGO"),
                        "DESCRIPCION": st.column_config.TextColumn("DESCRIPCIÓN"),
                        "CANTIDAD": st.column_config.TextColumn("CANTIDAD", width="small")
                    }
                )
                # Definimos el color que quieres (puedes cambiarlo aquí)
                color_fondo = "#465B66"  # Un rosa claro, por ejemplo
                
                st.markdown(f"""
                    <style>
                    /* Buscamos el textarea que tenga tu 'key' específica */
                    div[data-testid="stTextArea"] textarea[id^="coment_in_pt"] {{
                        background-color: {color_fondo} !important;
                        color: #31333F !important; /* Color de la letra */
                    }}
                    
                    /* Esto cambia el contenedor del textarea por si acaso */
                    div[data-testid="stTextArea"] > div:nth-child(2) {{
                        background-color: {color_fondo} !important;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                
                # Tu código original
                coment_val = st.text_area(
                    ":material/chat: COMENTARIOS ADICIONALES", 
                    placeholder="Escribe aquí cualquier observación...", 
                    key="coment_in_pt"
                )
                
                # --- HTML PARA IMPRESIÓN PT ---
                filas_print = df_final_pt[df_final_pt["CODIGO"] != ""]
                tabla_html = "".join([
                    f"<tr><td style='border:1px solid black;padding:8px;'>{r['CODIGO']}</td>"
                    f"<td style='border:1px solid black;padding:8px;'>{r['DESCRIPCION']}</td>"
                    f"<td style='border:1px solid black;padding:8px;text-align:center;'>{r['CANTIDAD']}</td></tr>" 
                    for _, r in filas_print.iterrows()
                ])
                
                form_pt_html = f"""
                <html>
                <head>
                    <style>
                        @page {{ 
                            size: auto;
                            margin: 0mm; 
                        }}
                        @media print {{
                            body {{ 
                                margin: 0; 
                                padding: 15mm; 
                            }}
                            .no-print {{ display: none !important; }}
                        }}
                        body {{ font-family: sans-serif; color: black; background: white; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                        th {{ background: #eee; border: 1px solid black; padding: 8px; text-align: left; }}
                        .comments-section {{
                            margin-top: 20px;
                            font-size: 12px;
                            border: 1px solid black;
                            padding: 10px;
                            min-height: 40px;
                        }}
                        .signature-section {{
                            margin-top: 60px;
                            display: flex;
                            justify-content: space-between;
                            text-align: center;
                            font-size: 11px;
                        }}
                        .sig-box {{
                            width: 30%;
                            border-top: 1px solid black;
                            padding-top: 5px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="print-container">
                        <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:10px; margin-bottom:20px;">
                            <div>
                                <h2 style="margin:0; letter-spacing:2px;">JYPESA</h2>
                                <p style="margin:0; font-size:10px; letter-spacing:1px;">AUTOMATIZACIÓN DE PROCESOS</p>
                            </div>
                            <div style="text-align:right; font-size:12px;">
                                <b>FOLIO:</b> {fol_val}<br>
                                <b>FECHA:</b> {f_val}
                            </div>
                        </div>
                
                        <h3 style="text-align:center; letter-spacing:1px;">ENTREGA DE MATERIALES PT</h3>
                        <p style="font-size:12px;"><b>TURNO:</b> {t_val}</p>
                        
                        <table>
                            <thead>
                                <tr><th>CÓDIGO</th><th>DESCRIPCIÓN</th><th>CANTIDAD</th></tr>
                            </thead>
                            <tbody>
                                {tabla_html}
                            </tbody>
                        </table>
            
                        <div class="comments-section">
                            <b>COMENTARIOS:</b> {coment_val}
                        </div>
                
                        <div class="signature-section">
                            <div class="sig-box">
                                <b>ENTREGÓ</b><br>
                                Analista de Inventario
                            </div>
                            <div class="sig-box">
                                <b>AUTORIZACIÓN</b><br>
                                Carlos Fialko / Dir. Operaciones
                            </div>
                            <div class="sig-box">
                                <b>RECIBIÓ</b><br>
                                Rigoberto Hernandez / Cord. Logística
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(":material/picture_as_pdf: IMPRIMIR SALIDA PT", type="primary", use_container_width=True):
                        components.html(f"<html><body>{form_pt_html}<script>window.print();</script></body></html>", height=0)
                with c2:
                    if st.button(":material/refresh: BORRAR", use_container_width=True):
                        if 'folio_nexion' in st.session_state: del st.session_state.folio_nexion
                        st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": "0"}] * 10)
                        st.rerun()
    
            # --- SUBSECCIÓN B: CONTRARRECIBOS (CONSOLIDADO) ---
            elif st.session_state.menu_sub == "CONTRARRECIBOS":
                
                tz_gdl = pytz.timezone('America/Mexico_City')
                now_gdl = datetime.now(tz_gdl)
                
                # ── A. INICIALIZACIÓN DE ESTADO ──
                if 'reset_counter' not in st.session_state:
                    st.session_state.reset_counter = 0

                # Lista para almacenar los registros capturados en la sesión
                if 'lista_contrarecibos' not in st.session_state:
                    st.session_state.lista_contrarecibos = []

                # ── B. INTERFAZ DE CAPTURA ESTILO ELITE ──
                st.write("")
                
                with st.container(border=True):
                    c_h1, c_h2, c_h3 = st.columns([1, 1, 1])
                    f_fecha_c = c_h1.date_input(":material/calendar_today: FECHA", date.today())
                    f_hora_c = c_h2.text_input(":material/schedule: HORA", value=now_gdl.strftime('%I:%M %p').lower())
                    f_paq_c = c_h3.selectbox(":material/local_shipping: PAQUETERÍA", ["TP DISTRIBUIDORA","TP LOGISTICA","SANCHEZ BARCELATA","FEDEX", "PAQMEX", "TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES","FLETES DE REGRESO", "TINY PACK"])

                    c_d1, c_d2 = st.columns([2, 1])
                    f_cod_c = c_d1.text_input(":material/barcode: CÓDIGO / FACTURA", placeholder="Escribe el código y presiona Enter")
                    f_cant_c = c_d2.number_input(":material/format_list_numbered: CANTIDAD", min_value=1, value=1)
                    
                    if st.button(":material/add: AGREGAR A LA LISTA", use_container_width=True):
                        if f_cod_c:
                            nuevo_item = {
                                "FECHA": f_fecha_c.strftime('%d/%m/%Y'),
                                "CODIGO": f_cod_c.upper(),
                                "PAQUETERIA": f_paq_c,
                                "CANTIDAD": str(f_cant_c)
                            }
                            st.session_state.lista_contrarecibos.append(nuevo_item)
                            st.toast(f"Código {f_cod_c} agregado", icon="✅")
                        else:
                            st.error("Ingresa al menos un código.")

                # ── C. VISTA PREVIA DE LO CAPTURADO ──
                if st.session_state.lista_contrarecibos:
                    st.write("### :material/list_alt: Registros para Impresión")
                    df_preview = pd.DataFrame(st.session_state.lista_contrarecibos)
                    st.dataframe(df_preview, use_container_width=True)
                    
                    if st.button(":material/delete: LIMPIAR LISTA", type="secondary"):
                        st.session_state.lista_contrarecibos = []
                        st.rerun()

                # ── D. RENDERIZADO PARA IMPRESIÓN (MANTENIENDO TU FORMATO) ──
                filas_c_data = st.session_state.lista_contrarecibos
                tabla_c_html = "".join([
                    f"<tr>"
                    f"<td style='border-bottom:1px solid black;padding:8px;'>{r['FECHA']}</td>"
                    f"<td style='border-bottom:1px solid black;padding:8px;'>{r['CODIGO']}</td>"
                    f"<td style='border-bottom:1px solid black;padding:8px;'>{r['PAQUETERIA']}</td>"
                    f"<td style='border-bottom:1px solid black;padding:8px;text-align:center;'>{r['CANTIDAD']}</td>"
                    f"</tr>"
                    for r in filas_c_data
                ])
                
                # Rellenar espacios vacíos para que la hoja no se vea mocha
                num_filas = len(filas_c_data)
                espacios = "".join(["<tr><td style='border-bottom:1px solid black;height:25px;' colspan='4'></td></tr>"] * max(0, 12 - num_filas))
                
                form_c_html = f"""
                <html>
                <head>
                    <style>
                        @media print {{
                            @page {{ size: auto; margin: 0; }}
                            body {{ margin: 0; padding: 10mm; }}
                            header, footer {{ display: none !important; }}
                        }}
                        body {{ font-family: Arial, sans-serif; background: white; color: black; }}
                        .print-box {{ padding: 20px; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                        th, td {{ border-bottom: 1px solid black; padding: 8px; text-align: left; }}
                    </style>
                </head>
                <body>
                    <div class="print-box">
                        <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:10px;">
                            <div>
                                <h2 style="margin:0; letter-spacing:2px;">JYPESA</h2>
                                <p style="margin:0; font-size:10px; letter-spacing:1px;">AUTOMATIZACIÓN DE PROCESOS</p>
                            </div>
                            <div style="text-align:right;">
                                <span style="font-weight:bold; border:1px solid black; padding:2px 10px;">{f_hora_c}</span>
                                <p style="margin:5px 0 0 0; font-size:10px;">FECHA IMPRESIÓN: {now_gdl.strftime('%d/%m/%Y')}</p>
                            </div>
                        </div>
                        <h4 style="text-align:center; margin-top:30px; letter-spacing:1px;">REPORTE ENTREGA DE FACTURAS DE CONTRARECIBO</h4>
                        <table>
                            <thead>
                                <tr style="font-size:12px; border-bottom: 2px solid black;">
                                    <th>FECHA</th><th>CÓDIGO</th><th>PAQUETERÍA</th><th style="text-align:center;">CANTIDAD</th>
                                </tr>
                            </thead>
                            <tbody style="font-size:13px;">
                                {tabla_c_html}
                                {espacios}
                            </tbody>
                        </table>
                        <div style="margin-top:100px; display:flex; justify-content:space-between; text-align:center; font-size:12px;">
                            <div style="width:40%; border-top:1px solid black; padding-top:5px;"><b>ELABORÓ</b><br>Rigoberto Hernandez - Cord de Logística</div>
                            <div style="width:40%; border-top:1px solid black; padding-top:5px;"><b>RECIBIÓ</b><br>Nombre y Firma</div>
                        </div>
                    </div>
                </body>
                </html>
                """

                # ── E. ACCIONES DE IMPRESIÓN ──
                st.write("---")
                if st.button(":material/print: IMPRIMIR REPORTE DE CONTRARECIBOS", type="primary", use_container_width=True):
                    if not st.session_state.lista_contrarecibos:
                        st.warning("Agrega al menos un código antes de imprimir.")
                    else:
                        components.html(f"<html><body>{form_c_html}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)

            # --- SUBSECCIÓN C: PROFORMA ---
            elif st.session_state.menu_sub == "PROFORMA": # <-- Alineado con 'elif ... == "CONTRARRECIBOS"'
                # --- CONFIGURACIÓN DE PRODUCTOS ---
                productos_proforma = {
                    "Accesorios Ecologicos": ("Ecological Accessories", "3401.11", 2.50),
                    "Dispensador Almond": ("Almond Dispenser", "3924.90", 11.50),
                    "Kit Biogena": ("Biogena Amenities Kit", "3401.11", 3.20),
                    "Jabón de Tocador 40g": ("Toilet Soap 40g", "3401.11", 0.45),
                    "Shampoo Botánicos 30ml": ("Botanical Shampoo 30ml", "3305.10", 0.60),
                    "Soporte Inoxidable": ("Stainless Steel Holder", "7324.90", 35.00)
                }
                
                def generar_proforma_html(datos_rem, datos_dest, items, info_envio):
                    filas_html = ""
                    subtotal = 0
                    for item in items:
                        total_item = item['cant'] * item['precio']
                        subtotal += total_item
                        filas_html += f"""
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">{item['desc_es']}<br><i style="font-size:0.8em; color:#555;">{item['desc_en']}</i></td>
                            <td style="border: 1px solid #ddd; padding: 8px; text-align:center;">{item['hs']}</td>
                            <td style="border: 1px solid #ddd; padding: 8px; text-align:center;">{item['cant']}</td>
                            <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">${item['precio']:.2f}</td>
                            <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">${total_item:.2f}</td>
                        </tr>"""
                
                    return f"""
                    <div style="font-family: 'Helvetica', Arial, sans-serif; padding: 40px; color: #333; max-width: 800px; margin: auto; background: white;">
                        <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 10px;">
                            <div>
                                <h1 style="margin:0; color:#003399;">PROFORMA INVOICE</h1>
                                <p style="margin:0;">FACTURA PROFORMA</p>
                            </div>
                            <div style="text-align: right;">
                                <p style="margin:0;"><b>Date / Fecha:</b> {info_envio['fecha']}</p>
                                <p style="margin:0;"><b>Invoice #:</b> {info_envio['folio']}</p>
                                <p style="margin:0; font-size: 0.8em; color: #666;"><b>Tracking:</b> {info_envio['guia']}</p>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                            <div style="border: 1px solid #ccc; padding: 10px;">
                                <b style="font-size: 0.9em; color: #666;">SHIPPER / REMITENTE</b>
                                <p style="margin:5px 0; font-size: 0.85em;">
                                    <b>{datos_rem['empresa']}</b><br>
                                    {datos_rem['direccion']}<br>
                                    {datos_rem['ciudad']}, {datos_rem['pais']}<br>
                                    <b>ATN: {datos_rem['atencion']}</b><br>
                                    TEL: {datos_rem['tel']}
                                </p>
                            </div>
                            <div style="border: 1px solid #ccc; padding: 10px;">
                                <b style="font-size: 0.9em; color: #666;">CONSIGNEE / DESTINATARIO</b>
                                <p style="margin:5px 0; font-size: 0.85em;">
                                    <b>{datos_dest['nombre']}</b><br>
                                    {datos_dest['calle']}<br>
                                    {datos_dest['ciudad']}, {datos_dest['estado']} CP: {datos_dest['cp']}<br>
                                    {datos_dest['pais']}<br>
                                    <b>TAX ID / RFC:</b> {datos_dest['tax_id']}<br>
                                    TEL: {datos_dest['tel']}
                                </p>
                            </div>
                        </div>
                        <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.9em;">
                            <thead><tr style="background: #f2f2f2;"><th style="border: 1px solid #ddd; padding: 8px;">Description</th><th style="border: 1px solid #ddd; padding: 8px;">HS Code</th><th style="border: 1px solid #ddd; padding: 8px;">Qty</th><th style="border: 1px solid #ddd; padding: 8px;">Unit USD</th><th style="border: 1px solid #ddd; padding: 8px;">Total USD</th></tr></thead>
                            <tbody>{filas_html}</tbody>
                            <tfoot><tr><td colspan="4" style="text-align:right; padding: 10px;"><b>TOTAL VALUE USD:</b></td><td style="border: 1px solid #ddd; padding: 10px; text-align:right; background: #eee;"><b>${subtotal:.2f}</b></td></tr></tfoot>
                        </table>
                        <div style="margin-top: 30px; font-size: 0.7em; color: #666; border-top: 1px solid #eee; padding-top: 10px;">
                            <p>Declaration: The values declared are for customs purposes only. No commercial value.</p>
                        </div>
                    </div>
                    """
                
                # --- LÓGICA DE FOLIO AUTOMÁTICO ---
                if 'folio_num' not in st.session_state:
                    st.session_state.folio_num = int(datetime.now().strftime("%m%d%H%M"))
                
                                
                # SECCIÓN DE DATOS DE ENVÍO
                c_env1, c_env2, c_env3 = st.columns([1, 1, 1])
                f_folio = c_env1.text_input(":material/confirmation_number: FOLIO / INVOICE #", value=f"PRO-{st.session_state.folio_num}")
                f_fecha = c_env2.date_input(":material/calendar_today: FECHA DE ENVÍO", date.today())
                f_guia = c_env3.text_input(":material/local_shipping: NÚMERO DE GUÍA FEDEX", placeholder="0000 0000 0000")
                
                st.write("")
                col_izq, col_der = st.columns(2)
                
                with col_izq:
                    st.markdown('<div style="background:#4e73df;color:white;text-align:center;font-weight:bold;padding:8px;border-radius:4px 4px 0 0;">REMITENTE</div>', unsafe_allow_html=True)
                    st.text_input(":material/corporate_fare: NOMBRE", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
                    r1, r2 = st.columns([1.5, 1])
                    rem_atn = r1.text_input(":material/person: ATENCIÓN", "RIGOBERTO HERNANDEZ")
                    rem_tel = r2.text_input(":material/call: TELÉFONO", "3319753122")
                    rem_sol = st.text_input(":material/badge: SOLICITANTE / AGENTE").upper()
                
                with col_der:
                    st.markdown('<div style="background:#660099;color:withe;text-align:center;font-weight:bold;padding:8px;border-radius:4px 4px 0 0;">DESTINATARIO / HOTEL</div>', unsafe_allow_html=True)
                    dest_nom = st.text_input(":material/hotel: HOTEL / NOMBRE").upper()
                    dest_calle = st.text_input(":material/location_on: CALLE Y NÚMERO").upper()
                    dp1, dp2 = st.columns(2)
                    dest_pais = dp1.text_input(":material/public: PAÍS DESTINO").upper()
                    dest_estado = dp2.text_input(":material/map: ESTADO / PROVINCIA").upper()
                    dp3, dp4 = st.columns(2)
                    dest_ciudad = dp3.text_input(":material/location_city: CIUDAD").upper()
                    dest_tax = dp4.text_input(":material/receipt_long: TAX ID / RFC / RUC").upper()
                    dp5, dp6 = st.columns(2)
                    dest_contacto = dp5.text_input(":material/contact_phone: TEL. CONTACTO")
                    dest_cp = dp6.text_input(":material/mailbox: C.P. / ZIP CODE")
                
                st.divider()
                st.markdown("### :material/inventory_2: PRODUCTOS Y VALORES")
                seleccion = st.multiselect(":material/search: Busca productos:", list(productos_proforma.keys()))
                
                items_capturados = []
                if seleccion:
                    for prod in seleccion:
                        info = productos_proforma[prod]
                        cp1, cp2, cp3 = st.columns([2, 1, 1])
                        with cp1: st.write(f"**{prod}**")
                        with cp2: cant = st.number_input(f"Cant.", min_value=1, value=1, key=f"q_{prod}")
                        with cp3: precio = st.number_input(f"Precio (USD)", min_value=0.0, value=info[2], step=0.1, key=f"p_{prod}")
                        items_capturados.append({"desc_es": prod, "desc_en": info[0], "hs": info[1], "cant": cant, "precio": precio})
                
                st.write("")
                
                # Botón de impresión con icono de Material
                if st.button(":material/print: GENERAR E IMPRIMIR FACTURA", use_container_width=True, type="primary"):
                    if not dest_nom or not items_capturados:
                        st.error("Vida, faltan datos del hotel o productos.")
                    else:
                        rem_info = {
                            "empresa": "JABONES Y PRODUCTOS ESPECIALIZADOS", 
                            "direccion": "C. Cernícalo 155, La Aurora", 
                            "ciudad": "Guadalajara, Jalisco, 44460", 
                            "pais": "MEXICO", 
                            "tel": rem_tel,
                            "atencion": rem_atn
                        }
                        dest_info = {"nombre": dest_nom, "calle": dest_calle, "ciudad": dest_ciudad, "estado": dest_estado, "pais": dest_pais, "tel": dest_contacto, "tax_id": dest_tax, "cp": dest_cp}
                        
                        proforma_html = generar_proforma_html(rem_info, dest_info, items_capturados, {"folio": f_folio, "fecha": f_fecha, "guia": f_guia})
                        
                        st.session_state.folio_num += 1
                        st.success("¡Documento generado con éxito!")
                        components.html(f"<html><body>{proforma_html}<script>window.print();</script></body></html>", height=0)
                
                        

                
        # 5. HUB LOG
        elif st.session_state.menu_main == "HUB LOG":
            if st.session_state.menu_sub == "SMART ROUTING":               
                # --- 1. CARGA DE MATRIZ DESDE GITHUB (VERSION FORZADA) ---
                # --- 1. CARGA DE MATRIZ DESDE GITHUB (VERSION FORZADA) ---
                @st.cache_data(ttl=60) # Actualiza la caché cada minuto
                def obtener_matriz_github():
                    # Añadimos un timestamp para forzar a GitHub a no servir una versión cacheada
                    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv?nocache={int(time.time())}"
                    try:
                        m = pd.read_csv(url)
                        m.columns = [str(c).upper().strip() for c in m.columns]
                        return m
                    except Exception as e:
                        st.error(f"Error fatal al conectar con GitHub: {e}")
                        return pd.DataFrame()
                
                # --- NUEVA FUNCIÓN: GUARDADO AUTOMÁTICO DE FACTURACIÓN ---
                def guardar_facturacion_moreno(df):
                    try:
                        token = st.secrets["GITHUB_TOKEN"]
                        repo = "RH2026/nexion"
                        filename = "facturacion_moreno.csv"
                        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
                        
                        # Convertir a CSV para el repositorio
                        csv_content = df.to_csv(index=False).encode("utf-8-sig")
                        content_base64 = base64.b64encode(csv_content).decode("utf-8")
                        
                        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                        
                        # Obtener SHA si el archivo ya existe para sobreescribirlo
                        res = requests.get(url, headers=headers)
                        sha = res.json().get("sha") if res.status_code == 200 else None
                        
                        payload = {
                            "message": f"Auto-update Facturación: {time.strftime('%Y-%m-%d %H:%M')}",
                            "content": content_base64,
                            "branch": "main"
                        }
                        if sha: payload["sha"] = sha
                        
                        requests.put(url, headers=headers, json=payload)
                        return True
                    except Exception:
                        return False
                
                def limpiar_texto(texto):
                    if pd.isna(texto): return ""
                    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper()
                    texto = re.sub(r'[^A-Z0-9\s]', ' ', texto) 
                    return " ".join(texto.split())
                
                # --- 2. FUNCIONES MAESTRAS PDF ---
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
                
                # --- BLOQUE 1: PREPARACIÓN S&T ---
                st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>S&T PREPARATION MODULE</p>", unsafe_allow_html=True)
                uploaded_file = st.file_uploader("Subir archivo ERP", type=["xlsx", "csv"], label_visibility="collapsed")
                
                if uploaded_file is not None:
                    try:
                        # Carga inicial de datos
                        df = pd.read_csv(uploaded_file, sep=None, engine='python') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                        
                        # --- LÓGICA DE GUARDADO AUTOMÁTICO ---
                        # Se ejecuta inmediatamente al cargar, solo una vez por archivo
                        if f"uploaded_{uploaded_file.name}" not in st.session_state:
                            if guardar_facturacion_moreno(df):
                                st.toast("Archivo 'facturacion_moreno' guardado en GitHub", icon="🚀")
                                st.session_state[f"uploaded_{uploaded_file.name}"] = True
                            else:
                                st.error("Error al guardar en GitHub. Revisa el Token en Secrets.")
                
                        df.columns = [str(c).strip().replace('\n', '') for c in df.columns]
                        
                        col_folio = next((c for c in df.columns if 'factura' in c.lower() or 'docnum' in c.lower() or 'folio' in c.lower()), df.columns[0])
                        
                        col_left, col_right = st.columns([1, 2], gap="large")
                        with col_left:
                            st.markdown(f"<p class='op-query-text'>FILTROS</p>", unsafe_allow_html=True)
                            serie = pd.to_numeric(df[col_folio], errors='coerce').dropna()
                            inicio = st.number_input("Desde:", value=int(serie.min()) if not serie.empty else 0)
                            final = st.number_input("Hasta:", value=int(serie.max()) if not serie.empty else 0)
                            df[col_folio] = pd.to_numeric(df[col_folio], errors='coerce')
                            df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)].copy()
                
                        with col_right:
                            st.markdown(f"<p class='op-query-text'>SELECCIÓN</p>", unsafe_allow_html=True)
                            if not df_rango.empty:
                                info = df_rango.drop_duplicates(subset=[col_folio])[[col_folio]]
                                info.insert(0, "Incluir", True)
                                edited_df = st.data_editor(info, hide_index=True, use_container_width=True, key="ed_v4")
                            else: st.warning("Rango vacío")
                
                        if not df_rango.empty and not edited_df.empty:
                            folios_ok = edited_df[edited_df["Incluir"] == True][col_folio].tolist()
                            
                            # --- SECCIÓN DE BOTONES DE RENDER ---
                            st.markdown("---")
                            if st.button(":material/play_circle: RENDERIZAR TABLA", use_container_width=True):
                                st.session_state.df_final_st = df_rango[df_rango[col_folio].isin(folios_ok)]
                            
                            if "df_final_st" in st.session_state:
                                df_st = st.session_state.df_final_st
                                st.dataframe(df_st, use_container_width=True)
                                
                                sc1, sc2 = st.columns(2)
                                with sc1:
                                    towrite = io.BytesIO()
                                    df_st.to_excel(towrite, index=False, engine='openpyxl')
                                    st.download_button(label=":material/download: DESCARGAR S&T", data=towrite.getvalue(), file_name="ST_DATA.xlsx", use_container_width=True)
                                
                                with sc2:
                                    if st.button(":material/join_inner: SMART ROUTING (MOTOR DE ASIGNACIÓN)", type="primary", use_container_width=True):
                                        df_log = df_st.drop_duplicates(subset=[col_folio]).copy()
                                        matriz_db = obtener_matriz_github()
                                        
                                        col_dir_erp = next((c for c in df_log.columns if 'DIRECCION' in c.upper()), None)
                                        col_dest_matriz = 'DESTINO' if 'DESTINO' in matriz_db.columns else matriz_db.columns[0]
                                        col_flet_matriz = 'TRANSPORTE' if 'TRANSPORTE' in matriz_db.columns else 'FLETERA'
                                        col_tarifa_matriz = 'PRECIO POR CAJA' if 'PRECIO POR CAJA' in matriz_db.columns else 'COSTO'
                
                                        def motor_v4(row):
                                            if not col_dir_erp: return "ERROR: COL DIRECCION", 0.0
                                            dir_limpia = limpiar_texto(row[col_dir_erp])
                                            if any(loc in dir_limpia for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA", "TLAJOMULCO"]):
                                                return "LOCAL", 0.0
                                            for _, fila in matriz_db.iterrows():
                                                dest_key = limpiar_texto(fila[col_dest_matriz])
                                                if dest_key and (dest_key in dir_limpia):
                                                    flet = fila.get(col_flet_matriz, "ASIGNADO")
                                                    costo_val = pd.to_numeric(fila.get(col_tarifa_matriz, 0.0), errors='coerce')
                                                    return flet, costo_val
                                            return "REVISIÓN MANUAL", 0.0
                
                                        res = df_log.apply(motor_v4, axis=1)
                                        df_log['RECOMENDACION'] = [r[0] for r in res]
                                        df_log['COSTO'] = [r[1] for r in res]
                                        
                                        df_log = df_log.rename(columns={col_folio: "Factura"})
                                        cols_deseadas = ["Factura", "RECOMENDACION", "COSTO", "Transporte", "Nombre_Cliente", "Nombre_Extran", "Quantity", "DIRECCION", "DESTINO"]
                                        cols_finales = [c for c in cols_deseadas if c in df_log.columns]
                                        
                                        st.session_state.df_analisis = df_log[cols_finales]
                                        st.success("¡Motor sincronizado con datos recientes!")
                                        st.rerun()
                
                    except Exception as e: st.error(f"Error: {e}")
                
                # --- BLOQUE 2: SMART ROUTING & ANALISIS ---
                if "df_analisis" in st.session_state:
                    st.markdown("---")
                    st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>LOGISTICS INTELLIGENCE HUB</p>", unsafe_allow_html=True)
                    
                    p = st.session_state.df_analisis
                    modo_edicion = st.toggle("HABILITAR EDICIÓN MANUAL")
                    
                    p_editado = st.data_editor(
                        p, use_container_width=True, hide_index=True,
                        column_config={
                            "RECOMENDACION": st.column_config.TextColumn("FLETERA", disabled=not modo_edicion),
                            "COSTO": st.column_config.NumberColumn("TARIFA", format="$%.2f", disabled=not modo_edicion),
                        },
                        key="editor_final_github"
                    )
                
                    ba1, ba2 = st.columns(2)
                    with ba1:
                        if st.button(":material/save_as: FIJAR CAMBIOS", use_container_width=True):
                            st.session_state.df_analisis = p_editado
                            st.toast("Cambios guardados", icon="✅")
                    with ba2:
                        output_xlsx = io.BytesIO()
                        p_editado.to_excel(output_xlsx, index=False, engine='openpyxl')
                        st.download_button(label=":material/download: DESCARGAR ANÁLISIS", data=output_xlsx.getvalue(), file_name="Analisis_Final.xlsx", use_container_width=True)
                
                    with st.expander("SISTEMA DE SELLADO", expanded=False):
                        cx, cy = st.columns(2); ax = cx.slider("X", 0, 612, 510); ay = cy.slider("Y", 0, 792, 760)
                        
                        s1, s2 = st.columns(2)
                        with s1:
                            if st.button(":material/print: GENERAR SELLOS PAPEL", use_container_width=True):
                                st.download_button(":material/picture_as_pdf: DESCARGAR PDF", generar_sellos_fisicos(p_editado['RECOMENDACION'].tolist(), ax, ay), "Sellos.pdf", use_container_width=True)
                
                        st.markdown("---")
                        pdfs = st.file_uploader(":material/picture_as_pdf: Subir Facturas (PDF)", type="pdf", accept_multiple_files=True)
                        if pdfs:
                            if st.button("EJECUTAR SELLADO DIGITAL", use_container_width=True):
                                mapa = pd.Series(p_editado.RECOMENDACION.values, index=p_editado["Factura"].astype(str)).to_dict()
                                z_io = io.BytesIO()
                                with zipfile.ZipFile(z_io, "a") as zf:
                                    for pdf in pdfs:
                                        f_id = next((k for k in mapa.keys() if k in pdf.name.upper()), None)
                                        if f_id: zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ax, ay))
                                st.download_button(":material/folder_zip: DESCARGAR ZIP", z_io.getvalue(), "Sellado.zip", use_container_width=True)

    
            elif st.session_state.menu_sub == "DATA MANAGEMENT":
                #1. Definir la zona horaria de Guadalajara
                tz_gdl = pytz.timezone('America/Mexico_City')
                
                # ── ESTADO INICIAL ──
                st.info("Estado de Servidores : Online | Nexion Core: Active")
                
                # ── ESTILO VISUAL PRO (CSS) ──
                st.markdown("""
                    <style>
                    .main-header {
                        background: rgba(84, 175, 231, 0.1);
                        border-left: 5px solid #54AFE7;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }
                    .status-card {
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 15px;
                        text-align: center;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # ── CONFIGURACIÓN DE SEGURIDAD ──
                TOKEN = st.secrets.get("GITHUB_TOKEN", None)
                REPO_NAME = "RH2026/nexion"
                NOMBRE_EXCLUSIVO = "Matriz_Excel_Dashboard.csv"
                
                # ── DASHBOARD DE ESTADO RÁPIDO ──
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="status-card"><p style="margin:0; font-size:10px;">REPOSITORIO</p><p style="margin:0; color:#54AFE7; font-weight:bold;">{REPO_NAME.split("/")[1].upper()}</p></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="status-card"><p style="margin:0; font-size:10px;">ARCHIVO MAESTRO</p><p style="margin:0; font-weight:bold;">CSV</p></div>', unsafe_allow_html=True)
                with c3:
                    color_token = "#2ECC71" if TOKEN else "#E74C3C"
                    st.markdown(f'<div class="status-card"><p style="margin:0; font-size:10px;">TOKEN STATUS</p><p style="margin:0; color:{color_token}; font-weight:bold;">{"ACTIVO" if TOKEN else "ERROR"}</p></div>', unsafe_allow_html=True)
                
                st.write("---")
                
                # ── ÁREA DE CARGA EXCLUSIVA (GITHUB) ──
                with st.container(border=True):
                    st.markdown("#### :material/security: Zona de Carga Crítica")
                    st.caption(f"Solo se permite la actualización de: `{NOMBRE_EXCLUSIVO}`")
                    
                    uploaded_file_master = st.file_uploader("Actualizar Matriz Maestra", type=["csv"], help="Arrastra el archivo maestro aquí", key="master_uploader")
                
                    if uploaded_file_master is not None:
                        if uploaded_file_master.name != NOMBRE_EXCLUSIVO:
                            st.error(f":material/error: Nombre inválido: **{uploaded_file_master.name}**")
                            st.warning(f"El archivo debe renombrarse a: `{NOMBRE_EXCLUSIVO}` antes de subirlo.")
                        else:
                            st.success(f":material/check_circle: Archivo validado: {uploaded_file_master.name}")
                            
                            with st.expander(":material/visibility: Previsualizar datos locales"):
                                try:
                                    df_preview = pd.read_csv(uploaded_file_master)
                                    st.dataframe(df_preview.head(5), use_container_width=True)
                                    uploaded_file_master.seek(0)
                                except:
                                    st.error("No se pudo generar la vista previa del CSV.")
                
                            # --- CORRECCIÓN: HORA REAL GDL PARA MENSAJE ---
                            hora_actual_gdl = datetime.now(tz_gdl).strftime('%d/%m/%Y %H:%M')
                            commit_msg = st.text_input("Mensaje de Sincronización", 
                                                     value=f"Update Master {hora_actual_gdl}")
                
                            if st.button(":material/cloud_sync: SINCRONIZAR CON GITHUB", type="primary", use_container_width=True):
                                with st.status("Iniciando conexión con GitHub...", expanded=True) as status:
                                    try:
                                        from github import Github
                                        g = Github(TOKEN)
                                        repo = g.get_repo(REPO_NAME)
                                        file_content = uploaded_file_master.getvalue()
                
                                        st.write("Buscando archivo en el repositorio...")
                                        try:
                                            contents = repo.get_contents(NOMBRE_EXCLUSIVO)
                                            repo.update_file(contents.path, commit_msg, file_content, contents.sha)
                                            status.update(label="¡Matriz actualizada con éxito!", state="complete", expanded=False)
                                        except:
                                            repo.create_file(NOMBRE_EXCLUSIVO, commit_msg, file_content)
                                            status.update(label="¡Archivo creado exitosamente!", state="complete", expanded=False)
                                        
                                        st.toast("GitHub actualizado correctamente", icon="✅")
                                        st.cache_data.clear()
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as e:
                                        status.update(label=f"Fallo en la carga: {e}", state="error")
                
                # ── HISTORIAL DE ACTIVIDAD ──
                with st.expander(":material/history: Última actividad en el servidor"):
                    try:
                        from github import Github
                        g = Github(TOKEN)
                        repo = g.get_repo(REPO_NAME)
                        commits = repo.get_commits(path=NOMBRE_EXCLUSIVO)
                        last_commit = commits[0]
                        
                        # --- CORRECCIÓN: CONVERTIR UTC DE GITHUB A GDL ---
                        fecha_utc = last_commit.commit.author.date.replace(tzinfo=pytz.utc)
                        fecha_gdl = fecha_utc.astimezone(tz_gdl)
                        
                        st.write(f"**Última actualización:** {fecha_gdl.strftime('%d/%m/%Y %H:%M')}")
                        st.write(f"**Modificado por:** {last_commit.commit.author.name} :material/verified_user:")
                        st.write(f"**Nota:** {last_commit.commit.message}")
                        st.code(f"ID Registro: {last_commit.sha[:7]}", language="bash")
                    except:
                        st.info("Conectando con el servidor de seguridad de GitHub...")
            
            
            elif st.session_state.menu_sub == "ORDER STAGING":                
                # --- 1. CONFIGURACIÓN DE PODER ---
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                
                def leer_csv_github(nombre_archivo):
                    try:
                        url = f"https://api.github.com/repos/RH2026/nexion/contents/{nombre_archivo}"
                        headers = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"}
                        r = requests.get(url, headers=headers)
                        if r.status_code == 200:
                            content = r.json()
                            df = pd.read_csv(BytesIO(base64.b64decode(content['content'])))
                            # Limpieza Pro: Quitamos espacios en blanco en nombres de columnas
                            df.columns = df.columns.str.strip()
                            return df
                    except: return None
                    return None
                
                # --- 2. INTERFAZ TIPO DASHBOARD ---
                st.title("🚀 NEXION AI: INTELIGENCIA TOTAL")
                st.sidebar.header("Configuración de Análisis")
                
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                
                # --- 3. PROCESAMIENTO ANALÍTICO (EL TRABAJO DURO) ---
                def generar_auditoria_completa():
                    matrices = {
                        "Dashboard": "Matriz_Excel_Dashboard.csv",
                        "Facturación": "facturacion_moreno.csv",
                        "Inventario": "inventario.csv",
                        "Historial": "matriz_historial.csv",
                        "Muestras": "muestras.csv"
                    }
                    
                    reporte_master = "--- REPORTE ANALÍTICO ESTRUCTURADO PARA JYPESA ---\n"
                    
                    for nombre, archivo in matrices.items():
                        df = leer_csv_github(archivo)
                        if df is not None:
                            reporte_master += f"\n📊 MATRIZ: {nombre.upper()} ({len(df)} filas detectadas)\n"
                            
                            # Analizamos cada columna de forma inteligente
                            for col in df.columns:
                                # Si es numérica (Precios, Cantidades, Stock)
                                if pd.api.types.is_numeric_dtype(df[col]):
                                    suma = df[col].sum()
                                    promedio = df[col].mean()
                                    reporte_master += f"  > [Numérica] '{col}': Total Sumado={suma:,.2f} | Promedio={promedio:,.2f}\n"
                                
                                # Si es categoría (Clientes, Destinos, Productos, Vendedores)
                                else:
                                    # Sacamos los 10 valores que más se repiten (Frecuencia real)
                                    top_10 = df[col].value_counts().head(10).to_dict()
                                    reporte_master += f"  > [Categoría] '{col}': Top 10 Frecuencias={top_10}\n"
                            
                            # Agregamos una 'foto' de los últimos 5 movimientos para contexto narrativo
                            reporte_master += f"  > Últimos movimientos:\n{df.tail(5).to_string(index=False)}\n"
                        else:
                            reporte_master += f"\n❌ MATRIZ: {nombre.upper()} (No se pudo conectar)\n"
                            
                    return reporte_master
                
                # --- 4. LÓGICA DEL CHAT INTELIGENTE ---
                for m in st.session_state.messages:
                    with st.chat_message(m["role"]): st.markdown(m["content"])
                
                if pregunta := st.chat_input("Hazme una pregunta compleja sobre JYPESA o cualquier tema..."):
                    st.session_state.messages.append({"role": "user", "content": pregunta})
                    with st.chat_message("user"): st.markdown(pregunta)
                
                    with st.spinner("Analizando miles de registros y cruzando información..."):
                        try:
                            # Detectar el mejor modelo disponible
                            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                            model = genai.GenerativeModel(modelos[0])
                            
                            # Obtenemos la auditoría de Python
                            contexto_data = generar_auditoria_completa()
                            
                            # Prompt de "Super Asistente"
                            prompt_final = f"""
                            ESTE ES EL REPORTE DE DATOS REAL DE JYPESA:
                            {contexto_data}
                            
                            ERES UNA IA DE ELITE Y ANALISTA SENIOR.
                            Instrucciones:
                            1. Rigoberto te hará preguntas. Si la respuesta está en los datos de arriba, sé EXACTO.
                               Ejemplo: "Tienes 45 envíos a Mazatlán según la matriz de Muestras".
                            2. Si la pregunta es sobre estrategia, usa los datos para aconsejar.
                               Ejemplo: "Veo que el producto X tiene poco stock pero muchas muestras, ¡surte pronto!".
                            3. Si la pregunta es CUALQUIER OTRA COSA (cultura, ciencia, ocio), responde con excelencia.
                            4. Tu tono es profesional, inteligente y directo.
                            
                            Pregunta de Rigoberto: {pregunta}
                            """
                            
                            response = model.generate_content(prompt_final)
                            
                            with st.chat_message("assistant"):
                                st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                        except Exception as e:
                            st.error(f"Error en el Cerebro Central, amor: {str(e)}")
                                              
            
               
    
    
    # ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
    st.markdown(f"""
        <div class="footer">
            NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
            <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
            <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
        </div>
    """, unsafe_allow_html=True)
    



























































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































