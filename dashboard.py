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

* El contenedor de la burbuja */
div[data-baseweb="tag"] {{
    background-color: #718096 !important;
    border-radius: 4px !important;
    height: 22px !important;
    margin: 2px !important;
}}

/* El texto dentro de la burbuja (AQUÍ CAMBIA EL TAMAÑO) */
div[data-baseweb="tag"] span {{
    color: #ffffff !important;
    font-size: 14px !important; /* <--- Ajusta este número a tu gusto */
    font-weight: 600 !important;
    text-transform: uppercase !important;
}}

/* El icono de cerrar (X) */
div[data-baseweb="tag"] svg {{
    fill: #ffffff !important;
    height: 12px !important;
    width: 12px !important;
}}

/* AJUSTE EXTRA: El texto antes de ser seleccionado */
div[data-baseweb="select"] div {{
    font-size: 12px !important; /* Para que todo el multiselect sea uniforme */
    text-transform: uppercase !important;
}}

/* Valor seleccionado – Selectbox */

/* ───────── SELECTBOX / MULTISELECT (ESTILO COMPLETO) ───────── */

/* 1. Altura y alineación de la caja principal */
div[data-baseweb="select"] > div:first-child {{
    height: 35px !important; 
    min-height: 35px !important;
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    display: flex !important;
    align-items: center !important;
}}

/* 2. Ajuste del texto interno y el cursor */
div[data-baseweb="select"] div {{
    font-size: 11px !important;
    color: {vars_css['text']} !important;
    line-height: 1 !important;
    text-transform: uppercase !important;
}}

/* 3. El Menú Desplegable (La lista de opciones de tu foto) */
div[data-baseweb="popover"] ul {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    padding: 0 !important;
}}

/* 4. Cada opción individual de la lista */
div[data-baseweb="popover"] li {{
    background-color: transparent !important;
    color: {vars_css['text']} !important;
    font-size: 14px !important;
    padding: 8px 12px !important;
    text-transform: uppercase !important;
    transition: background 0.2s ease !important;
}}

/* 5. Hover en las opciones (Color Aqua para resaltar) */
div[data-baseweb="popover"] li:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
}}



/* 6. Quitar el resplandor azul de Streamlit al hacer click */
div[data-baseweb="select"]:focus-within {{
    border-color: #00A0A8 !important;
    box-shadow: 0 0 0 1px #00A0A8 !important;
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

/* 4. El botón de Logout con fondo rojo sólido y hover intenso */
div[data-baseweb="popover"] button[kind="primary"] {{
    font-size: 12px !important;
    height: 26px !important;
    min-height: 26px !important;
    line-height: 26px !important;
    
    /* Rojo sólido original (el que tenías en el hover) */
    background-color: #ff4b4b !important; 
    border: 1px solid #ff4b4b !important;
    color: white !important;
    
    border-radius: 4px !important; /* Para mantenerlo limpio */
    transition: background-color 0.3s ease !important;
}}

div[data-baseweb="popover"] button[kind="primary"]:hover {{
    /* Rojo más intenso y oscuro para el hover */
    background-color: #FF7C80 !important; 
    border-color: #FF7C80 !important;
    color: white !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
}}

/* ───────── SOLUCIÓN NUCLEAR: ICONO RESPONSIVE ───────── */

/* 1. Bloqueamos el texto vertical de tus fotos en cualquier tamaño */
button[data-testid="stBaseButton-secondary"] p {{
    white-space: nowrap !important;
    word-break: keep-all !important;
}}

/* 2. Media Query Agresiva (1200px para que cambie apenas muevas la ventana) */
@media (max-width: 1200px) {{
    
    /* Buscamos el botón del popover específicamente */
    div[data-testid="stPopover"] > button {{
        width: 45px !important;
        height: 45px !important;
        min-width: 45px !important;
        max-width: 45px !important;
        padding: 0 !important;
        border-radius: 50% !important; /* Lo hace circular y limpio */
        position: relative !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    /* OCULTAMOS TODO EL CONTENIDO ORIGINAL (Texto y Flecha) */
    div[data-testid="stPopover"] > button * {{
        display: none !important; /* Esto mata el texto vertical de raíz */
    }}

    /* INYECTAMOS EL ICONO SOLO */
    div[data-testid="stPopover"] > button::after {{
        content: "☰";
        display: block !important;
        font-size: 22px !important;
        color: {vars_css['text']} !important;
        position: absolute !important;
        left: 50% !important;
        top: 50% !important;
        transform: translate(-50%, -50%) !important;
    }}
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
                st.image(vars_css["logo"], width=160)
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
                
                # 2. BOTONES DE NAVEGACIÓN (Restricciones dinámicas
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
                        # Simplemente agregamos "CARTA RECLAMO" al final de esta lista
                        opciones_for = ["SALIDA DE PT", "CONTRARRECIBOS", "PROFORMA", "CARTA RECLAMO"]                        
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
                    # --- 3. RENDERIZADO DEL TIMELINE (REPARADO) ---
                    df_timeline = resultados
                    if not df_timeline.empty:
                        envio = df_timeline.iloc[0]
                        f_envio = envio.get("FECHA DE ENVÍO", "N/A")
                        f_promesa = envio.get("PROMESA DE ENTREGA", "N/A")
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
                    
                        # Colores base
                        color_envio, color_guia, color_promesa = "#38bdf8", ("#38bdf8" if tiene_guia else vars_css['border']), ("#a855f7" if tiene_guia else vars_css['border'])
                        linea_1_2, linea_2_3 = ("#38bdf8" if tiene_guia else vars_css['border']), ("#a855f7" if tiene_guia else vars_css['border'])
                        
                        # --- FIX ANTICRASH ---
                        # Convertimos primero a datetime
                        f_promesa_dt = pd.to_datetime(envio.get("PROMESA DE ENTREGA"), dayfirst=True, errors='coerce')
                        # Solo aplicamos normalize si NO es nulo para evitar el AttributeError
                        if pd.notnull(f_promesa_dt):
                            f_promesa_dt = f_promesa_dt.normalize()
                        
                        hoy = pd.Timestamp(datetime.now()).normalize()
                    
                        # --- LÓGICA DE ESTATUS Y COLORES FINALES ---
                        if not tiene_guia:
                            if trigger_val == "Enviada":
                                status_text, status_color = "GENERANDO GUÍA", "#38bdf8"
                            else:
                                status_text, status_color = "SURTIENDO", "#FFA500"
                            color_entrega, linea_3_4 = vars_css['border'], vars_css['border']
                            
                        elif not entregado_real:
                            status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if pd.isna(f_promesa_dt) or hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
                            color_entrega, linea_3_4 = vars_css['border'], vars_css['border']
                            
                        else:
                            # Aplicamos la misma seguridad para la fecha de entrega real por si acaso
                            f_entrega_dt = pd.to_datetime(envio.get("FECHA DE ENTREGA REAL"), dayfirst=True, errors='coerce')
                            if pd.notnull(f_entrega_dt): f_entrega_dt = f_entrega_dt.normalize()
                            
                            status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.isna(f_promesa_dt) or f_entrega_dt <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")
                            color_entrega, linea_3_4 = status_color, status_color
                    
                        # HTML en una sola línea
                        timeline_html = f'<div style="background:{vars_css["card"]}; padding:20px; border-radius:8px; border:1px solid {vars_css["border"]}; margin-bottom:25px; font-family:sans-serif;"><div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:30px;"><h2 style="margin:0; color:{vars_css["text"]}; font-size:14px; letter-spacing:1px; text-transform:uppercase; font-weight:800;">{envio["NOMBRE DEL CLIENTE"]}</h2><span style="background:{status_color}15; color:{status_color}; padding:4px 12px; border-radius:4px; font-weight:700; font-size:10px; border:1px solid {status_color}; letter-spacing:1px; white-space:nowrap;">{status_text}</span></div><div style="display:flex; align-items:center; justify-content:space-between; width:100%; position:relative; margin-bottom:30px; overflow-x:auto; padding-bottom:10px;"><div style="display:flex; flex-direction:column; align-items:center; flex:1; min-width:60px;"><div style="width:12px; height:12px; background:{color_envio}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">ENVÍO</div><div style="font-size:10px; color:white;">{f_envio}</div></div><div style="flex-grow:1; height:2px; background:{linea_1_2}; margin-top:-35px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1; min-width:60px;"><div style="width:12px; height:12px; background:{color_guia}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">GUÍA</div><div style="font-size:10px; color:white;">{"LISTA" if tiene_guia else "PENDIENTE"}</div></div><div style="flex-grow:1; height:2px; background:{linea_2_3}; margin-top:-35px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1; min-width:60px;"><div style="width:12px; height:12px; background:{color_promesa}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">PROMESA</div><div style="font-size:10px; color:white;">{f_promesa}</div></div><div style="flex-grow:1; height:2px; background:{linea_3_4}; margin-top:-35px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1; min-width:60px;"><div style="width:16px; height:16px; background:{color_entrega}; border-radius:50%; box-shadow:{"0 0 10px "+color_entrega+"44" if entregado_real else "none"}; z-index:2;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:8px; font-weight:700;">ENTREGA</div><div style="font-size:10px; color:white;">{f_entrega_val}</div></div></div><div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:15px; border-top:1px solid {vars_css["border"]}; padding-top:20px;"><div style="flex:1; min-width:80px;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">FLETERA</div><div style="color:white; font-size:14px; font-weight:800; margin-top:5px;">{envio["FLETERA"]}</div></div><div style="flex:1; min-width:80px; text-align:center;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">GUÍA</div><div style="color:white; font-size:14px; font-weight:800; margin-top:5px;">{n_guia}</div></div><div style="flex:1; min-width:80px; text-align:right;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">DESTINO</div><div style="color:white; font-size:14px; font-weight:800; margin-top:5px;">{envio["DESTINO"]}</div></div></div></div>'
                        st.markdown(timeline_html, unsafe_allow_html=True)
                    
                    # --- RENDERIZADO DE DETALLES (TU BLOQUE ORIGINAL) ---
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
            
            # --- 1. DEFINICIÓN DE FUNCIONES ---
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
            
            def render_listado_operativo_premium(df):
                # Llenamos vacíos y convertimos a diccionario
                data = df.fillna('').to_dict('records')
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <script src="https://cdn.tailwindcss.com"></script>
                    <style>
                        body {{ background-color: transparent; color: #e2e8f0; font-family: 'Inter', sans-serif; margin: 0; }}
                        .row-logistica {{
                            background-color: #263238;
                            border: 1px solid rgba(255, 255, 255, 0.05);
                            border-radius: 12px;
                            margin-bottom: 10px;
                            padding: 16px;
                            transition: all 0.3s ease;
                        }}
                        .row-logistica:hover {{
                            border-color: #00FFAA;
                            transform: translateX(5px);
                            background-color: #2d3b42;
                        }}
                        .label-mini {{
                            font-size: 8px;
                            text-transform: uppercase;
                            color: rgba(255,255,255,0.5);
                            font-weight: 800;
                            letter-spacing: 1px;
                        }}
                        .valor {{ font-size: 13px; font-weight: 700; color: #FFFFFF; }}
                        .highlight {{ color: #00FFAA; font-family: monospace; }}
                        
                        /* Scrollbar */
                        ::-webkit-scrollbar {{ width: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.2); }}
                        ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                    </style>
                </head>
                <body>
                    <div style="padding: 10px;">
                        {"".join([f'''
                        <div class="row-logistica">
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 items-center">
                                <div>
                                    <div class="label-mini">Pedido / Factura</div>
                                    <div class="valor highlight text-lg">{str(item.get('NÚMERO DE PEDIDO', ''))}</div>
                                    <div class="text-[10px] text-blue-300 opacity-80">Envío: {str(item.get('FECHA DE ENVÍO', ''))}</div>
                                </div>
                                
                                <div>
                                    <div class="label-mini">Cliente / Destino</div>
                                    <div class="valor truncate text-xs uppercase">{str(item.get('NOMBRE DEL CLIENTE', ''))[:40]}</div>
                                    <div class="text-[10px] text-white/50 italic">{str(item.get('DESTINO', ''))}</div>
                                </div>
            
                                <div class="border-x border-white/5 px-4">
                                    <div class="label-mini">Transporte y Guía</div>
                                    <div class="valor text-[11px]">{str(item.get('FLETERA', ''))}</div>
                                    <div class="text-[10px] {"text-emerald-400" if item.get('NÚMERO DE GUÍA') else "text-orange-400"}">
                                        {str(item.get('NÚMERO DE GUÍA', 'PENDIENTE'))}
                                    </div>
                                </div>
            
                                <div class="text-right">
                                    <div class="label-mini">Estatus Entrega</div>
                                    <div class="valor text-sm {"text-emerald-400" if item.get('FECHA DE ENTREGA REAL') else "text-orange-400"}">
                                        {str(item.get('FECHA DE ENTREGA REAL', 'EN TRÁNSITO'))}
                                    </div>
                                    <div class="text-[9px] text-white/40 uppercase">Promesa: {str(item.get('PROMESA DE ENTREGA', ''))}</div>
                                </div>
                            </div>
                        </div>
                        ''' for item in data])}
                    </div>
                </body>
                </html>
                """
                return components.html(html_content, height=600, scrolling=True)
            
            # --- EJECUCIÓN DEL MÓDULO ---
            df_raw = cargar_datos()
            
            if df_raw is not None:
                with st.expander("Listado de pedidos completo", expanded=False):
                                
                    # --- BÚSQUEDA MAESTRA ---
                    #1. Definimos la búsqueda
                    busqueda_manual = st.text_input("", key="bus_maestra_log", placeholder="🔍 Buscar...").strip()
                    
                    # 2. ¡AQUÍ ESTÁ EL TRUCO! 
                    # Creamos df_final por defecto con TODO el contenido
                    df_final = df_raw.copy() 
                    
                    if busqueda_manual:
                        # Si el usuario escribe algo, entonces SÍ filtramos
                        mask = (
                            df_raw["NÚMERO DE PEDIDO"].astype(str).str.contains(busqueda_manual, case=False, na=False) |
                            df_raw["NÚMERO DE GUÍA"].astype(str).str.contains(busqueda_manual, case=False, na=False) |
                            df_raw["NOMBRE DEL CLIENTE"].astype(str).str.contains(busqueda_manual, case=False, na=False)
                        )
                        df_final = df_raw[mask].copy()
                    
                        # 3. Ahora esta línea YA NO VA A TRONAR porque df_final siempre existe
                        st.markdown(f"<p style='color:#00FFAA; font-size:11px; font-style:italic;'>Mostrando {len(df_final)} registros</p>", unsafe_allow_html=True)
                    
                        if not df_final.empty:
                            # Preparación de datos para el Timeline
                            envio = df_final.iloc[0]
                            f_envio = str(envio.get("FECHA DE ENVÍO", "--"))
                            f_promesa = str(envio.get("PROMESA DE ENTREGA", "--"))
                            entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
                            f_entrega_val = str(envio["FECHA DE ENTREGA REAL"]) if entregado_real else "PENDIENTE"
                            tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]
                            n_guia = str(envio["NÚMERO DE GUÍA"]) if tiene_guia else "GENERANDO GUÍA..."
                            
                            # Colores dinámicos
                            status_color = "#00FFAA" if entregado_real else "#38bdf8"
                            status_text = "ENTREGADO" if entregado_real else "EN TRÁNSITO"
                            v_border = "rgba(255,255,255,0.1)"
                            v_sub = "rgba(255,255,255,0.6)"
                            
                            color_envio = "#38bdf8"
                            color_guia = "#38bdf8" if tiene_guia else v_border
                            color_promesa = "#a855f7" if tiene_guia else v_border
                            linea_1_2 = color_guia
                            linea_2_3 = color_promesa
                            linea_3_4 = status_color if entregado_real else v_border
                            color_entrega = status_color if entregado_real else v_border
                    
                            # 2. RENDER DEL TIMELINE EN UNA SOLA LÍNEA (Sin errores de f-string)
                            timeline_html = f'''<div style="background:#263238; padding:20px; border-radius:12px; border:1px solid {v_border}; margin-bottom:25px; font-family:sans-serif;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:25px;"><h2 style="margin:0; color:white; font-size:14px; letter-spacing:1px; text-transform:uppercase; font-weight:800;">{envio["NOMBRE DEL CLIENTE"]}</h2><span style="background:{status_color}15; color:{status_color}; padding:4px 12px; border-radius:4px; font-weight:700; font-size:10px; border:1px solid {status_color}; letter-spacing:1px;">{status_text}</span></div><div style="display:flex; align-items:center; justify-content:space-between; width:100%; position:relative; margin-bottom:10px;"><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_envio}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">ENVÍO</div><div style="font-size:10px; color:white; font-weight:600;">{f_envio}</div></div><div style="flex-grow:1; height:2px; background:{linea_1_2}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_guia}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">GUÍA</div><div style="font-size:10px; color:white; font-weight:600;">{"LISTA" if tiene_guia else "PENDIENTE"}</div></div><div style="flex-grow:1; height:2px; background:{linea_2_3}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_promesa}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">PROMESA</div><div style="font-size:10px; color:white; font-weight:600;">{f_promesa}</div></div><div style="flex-grow:1; height:2px; background:{linea_3_4}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:16px; height:16px; background:{color_entrega}; border-radius:50%; z-index:2; box-shadow:0 0 12px {color_entrega if entregado_real else '#00000000'}"></div><div style="font-size:9px; color:{v_sub}; margin-top:8px; font-weight:800; letter-spacing:1px;">ENTREGA</div><div style="font-size:10px; color:white; font-weight:600;">{f_entrega_val}</div></div></div><div style="display:flex; justify-content:space-between; border-top:1px solid rgba(255,255,255,0.05); padding-top:15px; margin-top:15px;"><div style="text-align:left;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">FLETERA</div><div style="color:white; font-size:12px; font-weight:700;">{envio["FLETERA"]}</div></div><div style="text-align:center;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">GUÍA</div><div style="color:white; font-size:12px; font-weight:700;">{n_guia}</div></div><div style="text-align:right;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">DESTINO</div><div style="color:white; font-size:12px; font-weight:700;">{envio["DESTINO"]}</div></div></div></div>'''
                            
                            st.markdown(timeline_html, unsafe_allow_html=True)
                        
                    # --- RENDER DEL LISTADO CHINGÓN ---
                    st.markdown(f"<p style='color:#00FFAA; font-size:11px; italic;'>Mostrando {len(df_final)} registros</p>", unsafe_allow_html=True)
                    render_listado_operativo_premium(df_final)
                
                   
            
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
                tab_kpis, tab_tiempos, tab_despachos, tab_participacion, tab_entregas_agc, tab_consignas = st.tabs([
                    "KPI´S", "TIEMPOS DE TRÁNSITO", "EFICIENCIA DESPACHOS", "DIST. CARGA", "ENTREGAS AGC", "CONSIGNAS"
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
                    st.write("") 
                    # =========================================================
                    # 1. PROCESAMIENTO DE DATOS
                    # =========================================================
                    df['FECHA DE ENVÍO'] = pd.to_datetime(df['FECHA DE ENVÍO'], errors='coerce')
                    df['FECHA DE ENTREGA REAL'] = pd.to_datetime(df['FECHA DE ENTREGA REAL'], errors='coerce')
                    df['DIAS_REALES'] = (df['FECHA DE ENTREGA REAL'] - df['FECHA DE ENVÍO']).dt.days
                    
                    # =========================================================
                    # 2. SECCIÓN DEL CALCULADOR INTELIGENTE
                    # =========================================================                
                    usuario_actual = st.session_state.get('usuario_activo', 'Cielo')
                    
                    c1, c2, c3 = st.columns([1, 1, 0.8])
                    
                    with c1:
                        st.text_input("ORIGEN", value="GUADALAJARA (GDL)", disabled=True, key="orig_fix")
                    
                    with c2:
                        busqueda_manual = st.text_input(
                            "BUSCAR POR DESTINO, CP O DOMICILIO", 
                            placeholder="Ej: 63734, Litibu, Cancún...",
                            key="busqueda_manual_v6"
                        )
                    
                    with c3:
                        num_cajas = st.number_input("CANTIDAD DE CAJAS", min_value=1, value=1, step=1)
                    
                    # --- LÓGICA DE VISUALIZACIÓN POR DEFECTO ---
                    if not busqueda_manual:
                        df_validos = df[df['DIAS_REALES'].notna()]
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
                    
                    # --- FILTRADO ORIGINAL (SIN ROMPER NADA) ---
                    busqueda_aux = busqueda_activa.lower()
                    mask = (
                        df['DESTINO'].astype(str).str.lower().str.contains(busqueda_aux, na=False) |
                        df['DOMICILIO'].astype(str).str.lower().str.contains(busqueda_aux, na=False)
                    )
                    
                    historial = df[mask & (df['DIAS_REALES'].notna())].copy()
                    
                    if not historial.empty:
                        # --- CÁLCULO DE TIEMPOS ---
                        fletera_recomendada = historial['FLETERA'].value_counts().idxmax()
                        promedio_dias = historial['DIAS_REALES'].mean()
                        total_viajes = len(historial)
                        dias_redondeados = math.ceil(promedio_dias)
                
                        # --- MOTOR LÓGICO DE PRECIOS NEXION ELITE ---

                        # 1. Preparación del texto de búsqueda
                        texto_domicilio = str(historial['DOMICILIO'].iloc[0]).upper()
                        
                        # 2. Lista Maestra de Región $65 (Convenio Especial + Bajío/Centro)
                        regiones_65 = [
                            # TUS DESTINOS DEL NORTE/PACÍFICO (FORMATO DOBLE)
                            "HERMOSILLO", "HERMOSILLO, SON", "GUAYMAS", "GUAYMAS, SON", 
                            "DURANGO", "DURANGO, DUR", "SALTILLO", "SALTILLO, COA", 
                            "TEPIC", "TEPIC, NAY", "MAZATLAN", "MAZATLAN, SIN", 
                            "CANANEA", "CANANEA, SON", "TORREON", "TORREON, COA", 
                            "CULIACAN", "CULIACAN, SIN", "CIUDAD OBREGON", "CIUDAD OBREGON, SON", 
                            "LOS MOCHIS", "LOS MOCHIS, SIN", "OBREGON", "OBREGON, SON", 
                            "CABORCA", "CABORCA, SON", "NOGALES", "NOGALES, SON", 
                            "NAVOJOA", "NAVOJOA, SON", "MONTERREY", "MONTERREY, NL",
                            "APODACA", "APODACA, NL", "PIEDRAS NEGRAS", "PIEDRAS NEGRAS, COA",
                            "NUEVO VALLARTA", "NUEVO VALLARTA, NAY", "RINCON DE GUAYABITOS", "RINCON DE GUAYABITOS, NAY",
                            "CAJEME, CIUDAD OBREGON, SON", "TORREON COAHUILA, COA",
                        
                            # ESTADOS Y ABREVIACIONES GENERALES (CENTRO/BAJÍO)
                            "QUERETARO", "QRO", "QUE", "GUANAJUATO", "GTO", "LEON", "CELAYA", 
                            "AGUASCALIENTES", "AGS", "SAN LUIS POTOSI", "SLP", "HIDALGO", "HID", 
                            "PUEBLA", "PUE", "JALISCO", "JAL", "ESTADO DE MEXICO", "EDOMEX",
                            "TLAXCALA", "TLA", "MORELOS", "MOR", "CDMX", "CMX", "DF", "DF2",
                            
                            # VARIANTES CDMX Y CIUDAD DE MÉXICO
                            "MEXICO, DF", "MEXICO, DF2", "CIUDAD DE MEXICO", "MÉXICO, DF2", ", CMX",
                            "CIUDAD DE MÉXICO, DF2", "DELEGACION CUAUHTEMOC, CMX", "ALCALDIA CUAUHTEMOC, CMX",
                            "ALCALDIA CUAJIMALPA DE MORELOS, CMX", "CUAJIMALPA DE MORELOS, DF2",
                            
                            # CIUDADES ESPECÍFICAS DE TU IMAGEN
                            "MATEHUALA, SLP", "IXTAPAN DE LA SAL, MEX", "QUERETARO, QUE", "ATITALAQUIA, HID",
                            "MORELIA, MCH", "SILAO, GTO", "TOLUCA, MEX", "SALAMANCA, GTO", "SANTIAGO DE QUERETARO, QUE",
                            "JURIQUILLA, QUE", "PACHUCA, HID", "CALVILLO, AGS", "PUEBLA, PUE", "AMEALCO DE BONFIL, QUE",
                            "TULA DE ALLENDE, HID", "ACAMBARO, GTO", "CUAUTLANCINGO, PUE", "NUEVA ITALIA, MCH", 
                            "JACONA, MCH", "CORONANGO, PUE", "IRAPUATO, GTO", "GUANAJUATO, GTO", 
                            "SAN MIGUEL DE ALLENDE, GTO", "ZAMORA, MCH", "CUERNAVACA, MOR", "TOLUCA, DF2", 
                            "IXTAPALUCA, MEX", "IZTACALCO, CMX", "TETLATLAHUACA, TLA", "NAUCALPAN DE JUAREZ, MEX", 
                            "NICOLAS ROMERO, MEX", "SAN ANDRES, PUE", "TLANEPANTLA, MEX", "TEPOTZOTLAN, MEX", 
                            "VALLE DE BRAVO, MEX", "PATZCUARO, MCH", "ALVARO OBREGON, CMX", "TLALPAN, DF2", 
                            "SAN ANDRES CHOLULA, PUE", "TOLUCA DE LERDO, MEX", "CEDRAL, SLP", "TEQUISQUIAPAN, QUE", 
                            "TLALNEPANTLA DE BAZ, CMX", "MÉXICO, DF2", "BERNAL, QUE", "SILAO DE LA VICTORIA, GTO", 
                            "SAN JUAN DEL RIO, QUE", "CUAHUTEMOC, CMX", "METEPEC, MEX", "PACHUCA de SOTO, HID", 
                            "MUNICIPIO ALVARO OBREGON, MCH", "TLANEPANTLA, CMX", "ATLIXCO, PUE", "MIGUEL HIDALGO, CMX", 
                            "SANTA CRUZ TECÁMAC, MEX", "EL MARQUES, QUE", "MARINA NACIONAL, CMX", "MEXICO, DF2", 
                            "CUAJIMALPA DE MORELOS, CMX", "URUAPAN, MCH", "CIUDAD DE MEXICO, DF2", "BENITO JUAREZ, CMX", 
                            "YAUHQUEMEHCAN, TLA", "NAUCALPAN DE JUAREZ, CMX", "GUADALAJARA, JAL", "ZAPOTLAN EL GRANDE, JAL",
                            "ARANDAS, JAL", "SAN JUAN DE LOS LAGOS, JAL", "JOCOTEPEC, JAL", "CD GUZMAN, JAL"
                        ]
                        
                        # 3. Aplicación del "SEGURO VERACRUZ" y Evaluación de Región
                        # Si detecta Veracruz en el domicilio, bloquea los $65 inmediatamente
                        if any(x in texto_domicilio for x in ["VERACRUZ", " VER ", " VER.", ", VER"]):
                            es_region_65 = False
                        else:
                            es_region_65 = any(region in texto_domicilio for region in regiones_65)
                        
                        # 4. Cálculo de Tarifas según cantidad de cajas
                        if 1 <= num_cajas <= 4:
                            precio_unitario = 450 / num_cajas
                            total_sin_iva = 450
                            leyenda_region = "Tarifa Plana Nacional (1-4 cajas)"
                        else:
                            if es_region_65:
                                precio_unitario = 65
                                leyenda_region = "Zona con Tarifa Preferencial"
                            else:
                                precio_unitario = 95
                                leyenda_region = "Zona Norte / Sur / Costa"
                            total_sin_iva = num_cajas * precio_unitario
                        
                        # 5. Impuesto y Total Final
                        total_con_iva = total_sin_iva * 1.16
                
                        # --- RENDERIZADO ESTILO ONYX REPOTENCIADO ---
                        st.markdown(f"""<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 25px;"><div class="kpi-ruta-card" style="flex: 1; min-width: 280px; border-left: 5px solid #A4B9C8; position: relative; overflow: hidden;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;"><span style="font-size: 0.7rem; color: #A4B9C8; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">Tiempo Estimado</span><span style="font-size: 1.1rem; color: #FFFFFF; font-weight: 900;">{fletera_recomendada}</span></div><div class="kpi-route-flow" style="margin: 15px 0;"><span class="city" style="font-size: 1.2rem;">GDL</span><div style="flex-grow: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;"><span style="font-size: 0.7rem; color: #A4B9C8; letter-spacing: 2px;">TRANSIT</span><div style="width: 80%; height: 2px; background: linear-gradient(90deg, transparent, #A4B9C8, transparent);"></div></div><span class="city" style="font-size: 1.2rem; color: #FFFFFF;">{texto_mostrar[:15]}</span></div><div style="display: flex; align-items: baseline; gap: 8px;"><span style="font-size: 2.2rem; font-weight: 900; color: #FFFFFF;">{dias_redondeados}</span><span style="font-size: 1rem; color: #A4B9C8; font-weight: bold;">DÍAS HÁBILES</span></div><div style="margin-top: 10px; font-size: 0.9rem; color: #A4B9C8; border-top: 1px solid rgba(164, 185, 200, 0.1); padding-top: 8px;">Basado en {total_viajes} entregas exitosas a esta zona.</div></div><div class="kpi-ruta-card" style="flex: 1; min-width: 280px; border-left: 5px solid #D4AF37; background: linear-gradient(145deg, #1c2a35, #111b22);"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;"><span style="color: #D4AF37; font-weight: 900; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1.5px;">Costo de Flete</span></div><div style="margin-top: 5px;"><div style="font-size: 0.75rem; color: #A4B9C8; text-transform: uppercase; letter-spacing: 1px;">Inversión Total</div><div style="display: flex; align-items: baseline; gap: 5px;"><span style="font-size: 2.2rem; font-weight: 400; color: #D4AF37;">${total_con_iva:,.2f}</span><span style="font-size: 0.8rem; color: #A4B9C8;">MXN</span></div></div><div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 10px; margin-top: 10px; border: 1px solid rgba(212, 175, 55, 0.1);"><div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #E0E6ED;"><span>Cajas: <b>{num_cajas}</b></span><span>Unit: <b>${precio_unitario:,.2f}</b></span></div><div style="font-size: 0.7rem; color: #D4AF37; margin-top: 5px; text-transform: uppercase; font-weight: bold;">✓ {leyenda_region}</div></div><div style="text-align: right; margin-top: 8px; font-size: 0.6rem; color: #A4B9C8; font-style: italic;">*Incluye 16% de IVA</div></div></div>""", unsafe_allow_html=True) # 3. Tabla de Detalles (Tu código original)
                        #------------
                        # --- HISTORIAL DE ENVÍOS ENCONTRADOS (DISEÑO PREMIUM) ---
                        if not historial.empty:
                            st.markdown('<p style="color:#FFFFFF; font-weight:800; letter-spacing:2px; font-size:14px; margin-bottom:15px; border-left: 4px solid #00FFAA; padding-left: 10px;">HISTORIAL DE ENVÍOS ENCONTRADOS</p>', unsafe_allow_html=True)
                            
                            # Preparación de datos
                            historial_sorted = historial[['NÚMERO DE PEDIDO','NOMBRE DEL CLIENTE','DOMICILIO','FECHA DE ENVÍO','FLETERA']].sort_values(by='FECHA DE ENVÍO', ascending=False).copy()
                            historial_sorted['FECHA_STR'] = historial_sorted['FECHA DE ENVÍO'].dt.strftime('%d/%m/%Y')
                            data_hist = historial_sorted.fillna('').to_dict('records')
                        
                            # Renderizado de Tarjetas
                            html_historial = f"""
                            <div style="padding: 5px; font-family: 'Inter', sans-serif;">
                                <style>
                                    .card-historial {{
                                        background-color: #263238;
                                        border: 1px solid rgba(255, 255, 255, 0.05);
                                        border-radius: 10px;
                                        padding: 14px 20px;
                                        margin-bottom: 10px;
                                        transition: all 0.3s ease;
                                        display: flex;
                                        justify-content: space-between;
                                        align-items: center;
                                        width: 100%;
                                        box-sizing: border-box;
                                    }}
                                    .card-historial:hover {{
                                        border-color: #38bdf8;
                                        background-color: #2d3b42;
                                        transform: translateX(4px);
                                    }}
                                    .label-mini {{ font-size: 8px; text-transform: uppercase; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px; }}
                                    .valor-id {{ font-size: 15px; font-weight: 800; color: #00FFAA; font-family: monospace; }}
                                    .valor-text {{ font-size: 12px; font-weight: 600; color: #FFFFFF; }}
                                    .sub-text {{ font-size: 10px; color: rgba(255,255,255,0.6); font-style: italic; }}
                                    
                                    /* Scrollbar */
                                    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                                    ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); }}
                                    ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                                    ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                                </style>
                                {"".join([f'''
                                <div class="card-historial">
                                    <div style="flex: 1;">
                                        <div class="label-mini">Pedido</div>
                                        <div class="valor-id">{str(item.get('NÚMERO DE PEDIDO', ''))}</div>
                                    </div>
                                    <div style="flex: 2; padding: 0 15px;">
                                        <div class="label-mini">Cliente / Domicilio</div>
                                        <div class="valor-text uppercase truncate">{str(item.get('NOMBRE DEL CLIENTE', ''))[:35]}</div>
                                        <div class="sub-text truncate">{str(item.get('DOMICILIO', ''))[:50]}</div>
                                    </div>
                                    <div style="flex: 1; text-align: right;">
                                        <div class="label-mini">Fletera / Fecha</div>
                                        <div style="color: #38bdf8; font-size: 12px; font-weight: 700;">{str(item.get('FLETERA', ''))}</div>
                                        <div class="valor-text" style="font-size: 11px; opacity: 0.8;">{item.get('FECHA_STR', '')}</div>
                                    </div>
                                </div>
                                ''' for item in data_hist])}
                            </div>
                            """
                            components.html(html_historial, height=450, scrolling=True)
                        
                        else:
                            st.info(f"Lo siento **{usuario_actual}**, no encontré historial para: **{busqueda_manual}**")   
                
               
                # PESTAÑA 3: DESPACHOS (Análisis de Despachos 24h)
                with tab_despachos:
                    # 1. Copia y limpieza inmediata
                    df_vol = df_mes.copy()
                    
                    # Forzamos la lectura de fechas ignorando errores de formato
                    df_vol['EMISION'] = pd.to_datetime(df_vol['EMISION'], errors='coerce')
                    df_vol['FECHA DE ENVÍO'] = pd.to_datetime(df_vol['FECHA DE ENVÍO'], errors='coerce')
                
                    # 2. Configuración de Feriados
                    lista_feriados = ['2026-01-01', '2026-02-02', '2026-03-16', '2026-05-01']
                    feriados_np = np.array(lista_feriados, dtype='datetime64[D]')
                
                    # 3. Función de Cálculo (Sin rodeos)
                    def calcular_kpi_24h(row):
                        ini = row['EMISION']
                        fin = row['FECHA DE ENVÍO']
                        
                        # Si en tu matriz ves el dato pero Python dice NaT, usamos 'fin' para rescatar la fila
                        if pd.isna(ini) and not pd.isna(fin):
                            ini = fin
                            
                        if pd.isna(ini) or pd.isna(fin):
                            return "Sin Datos"
                        
                        try:
                            # Comparación directa
                            if fin <= ini: return "A Tiempo"
                            
                            # Días hábiles (Lunes a Sábado '1111110')
                            d = np.busday_count(ini.date(), fin.date(), weekmask='1111100', holidays=feriados_np)
                            
                            if d == 0: return "A Tiempo"
                            if d == 1 and fin.time() <= ini.time(): return "A Tiempo"
                            return "Fuera de Tiempo"
                        except:
                            return "Sin Datos"
                
                    # 4. Ejecución del cálculo
                    df_vol['Estado_KPI'] = df_vol.apply(calcular_kpi_24h, axis=1)
                    
                    # 5. Métricas para las tarjetas
                    validos = df_vol[df_vol['Estado_KPI'] != "Sin Datos"]
                    tot_v = len(validos)
                    ok_v = len(validos[validos['Estado_KPI'] == "A Tiempo"])
                    no_v = tot_v - ok_v
                    
                    # 6. Interfaz Visual
                    st.markdown(f'<div style="text-align:center;margin-bottom:30px;"><p style="color:{vars_css["sub"]};font-size:11px;letter-spacing:3px;font-weight:700;text-transform:uppercase;">Desempeño Despachos 24h — {mes_sel}</p></div>', unsafe_allow_html=True)
                    
                    c_v1, c_v2, c_v3 = st.columns(3)
                    
                    def render_modern_bar(valor, total, label, color):
                        porcentaje = (valor / total * 100) if total > 0 else 0
                        st.markdown(f"""
                            <div style="background: rgba(26, 37, 47, 0.6); padding: 20px; border-radius: 15px; border: 1px solid #243441; text-align: center;">
                                <p style="color: #A4B9C8; font-size: 10px; margin-bottom: 5px; font-weight: bold;">{label.upper()}</p>
                                <h2 style="color: white; margin: 0; font-size: 24px;">{valor}</h2>
                                <p style="color: {color}; font-size: 16px; margin-top: 5px; font-weight: bold;">{porcentaje:.1f}%</p>
                                <div style="background-color: #0B1014; border-radius: 10px; height: 8px; width: 100%; margin-top: 10px;">
                                    <div style="background-color: {color}; height: 8px; width: {porcentaje}%; border-radius: 10px; box-shadow: 0 0 10px {color}88;"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with c_v1: render_modern_bar(tot_v, tot_v, "Total Facturas", "#5a8dee")
                    with c_v2: render_modern_bar(ok_v, tot_v, "A Tiempo", "#39da8a")
                    with c_v3: render_modern_bar(no_v, tot_v, "Fuera de Meta", "#ff5b5c")
                
                    # --- 7. DETALLE DE OPERACIÓN (SIEMPRE VISIBLE - COLOR SMART) ---
                    st.markdown("<p style='font-size:12px; font-weight:bold; color:#54AFE7; letter-spacing:2px; margin-top:20px; margin-bottom:15px;'>🔍 DETALLE DE OPERACIÓN EN TIEMPO REAL</p>", unsafe_allow_html=True)
                    
                    if not df_vol.empty:
                        # 1. Preparación de datos
                        df_display = df_vol[['NÚMERO DE PEDIDO','EMISION', 'FECHA DE ENVÍO', 'Estado_KPI']].copy()
                        
                        # Formateo para visualización
                        df_display['EMISION_STR'] = df_display['EMISION'].dt.strftime('%d/%m/%Y %H:%M').fillna("S/D")
                        df_display['ENVIO_STR'] = df_display['FECHA DE ENVÍO'].dt.strftime('%d/%m/%Y %H:%M').fillna("S/D")
                        
                        data_detalle = df_display.to_dict('records')
                        alto_detalle = min(len(data_detalle) * 90 + 20, 550)
                    
                        # 2. Renderizado de Tarjetas
                        html_detalle = f"""
                        <div style="font-family: 'Inter', sans-serif; padding-right: 10px;">
                            <style>
                                body {{ background: transparent; margin: 0; padding: 0; }}
                                ::-webkit-scrollbar {{ width: 8px; }}
                                ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.05); border-radius: 10px; }}
                                ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; min-height: 50px; }}
                                ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                    
                                .card-detalle {{
                                    background: #263238;
                                    border: 1px solid rgba(255, 255, 255, 0.05);
                                    border-left: 5px solid #94a3b8;
                                    border-radius: 10px;
                                    padding: 12px 20px;
                                    margin-bottom: 8px;
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    transition: 0.3s;
                                }}
                                .card-detalle:hover {{ border-color: #38bdf8; background: #2d3b42; transform: translateX(5px); }}
                                .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: normal; letter-spacing: 1px; text-transform: uppercase; }}
                                .val-pedido {{ color: #00FFAA; font-family: monospace; font-size: 15px; font-weight: 800; }}
                                .val-fecha {{ color: #FFFFFF; font-size: 11px; font-weight: 400; opacity: 0.9; }}
                                
                                .badge-kpi {{ padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; text-align: center; min-width: 100px; }}
                                
                                .st-entregado {{ background: rgba(0, 255, 170, 0.1); color: #00FFAA; border: 1px solid rgba(0, 255, 170, 0.2); }}
                                .st-transito {{ background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.2); }}
                                .st-fuera {{ background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid rgba(255, 75, 75, 0.2); }}
                                .st-otro {{ background: rgba(255, 255, 255, 0.05); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.1); }}
                            </style>
                            
                            {"".join([f'''
                            <div class="card-detalle" style="border-left-color: {
                                '#00FFAA' if 'ENTREGADO' in str(item['Estado_KPI']).upper() else 
                                '#38bdf8' if 'TRANS' in str(item['Estado_KPI']).upper() else 
                                '#FF4B4B' if 'FUERA DE TIEMPO' in str(item['Estado_KPI']).upper() else '#94a3b8'};">
                                
                                <div style="flex: 1;">
                                    <div class="label-mini">Pedido</div>
                                    <div class="val-pedido">{item['NÚMERO DE PEDIDO']}</div>
                                </div>
                                
                                <div style="flex: 1.5; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                                    <div class="label-mini">Emisión</div>
                                    <div class="val-fecha">{item['EMISION_STR']}</div>
                                </div>
                    
                                <div style="flex: 1.5; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                                    <div class="label-mini">Salida de Almacén</div>
                                    <div class="val-fecha">{item['ENVIO_STR']}</div>
                                </div>
                    
                                <div style="flex: 1; text-align: right;">
                                    <div class="badge-kpi {
                                        'st-entregado' if 'ENTREGADO' in str(item['Estado_KPI']).upper() else 
                                        'st-transito' if 'TRANS' in str(item['Estado_KPI']).upper() else 
                                        'st-fuera' if 'FUERA DE TIEMPO' in str(item['Estado_KPI']).upper() else 'st-otro'}">
                                        {str(item['Estado_KPI']).upper()}
                                    </div>
                                </div>
                            </div>
                            ''' for item in data_detalle])}
                        </div>
                        """
                        import streamlit.components.v1 as components
                        components.html(html_detalle, height=alto_detalle, scrolling=True)
                    
                        # 3. Botón de Descarga Excel
                        import io
                        df_excel = df_display.copy()
                        # Limpiamos fechas para el Excel (solo fecha sin hora o como prefieras)
                        df_excel['EMISION'] = df_excel['EMISION'].dt.strftime('%d/%m/%Y')
                        df_excel['FECHA DE ENVÍO'] = df_excel['FECHA DE ENVÍO'].dt.strftime('%d/%m/%Y')
                        
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df_excel.to_excel(writer, index=False, sheet_name='Detalle_Operacion')
                        buffer.seek(0)
                    
                        st.download_button(
                            label="DESCARGAR REPORTE DE OPERACIÓN (EXCEL)",
                            data=buffer,
                            file_name=f"Detalle_Operacion_{mes_sel}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    else:
                        st.info("No hay datos disponibles para el detalle.")
                    
                # PESTAÑA 4: % PARTICIPACIÓN-
                with tab_participacion:
                    # --- CSS BLINDADO: Clases específicas para resultados ---
                    st.markdown("""
                        <style>
                            .metric-card-agc {
                                background-color: #263238;
                                border: 1px solid rgba(255, 255, 255, 0.05);
                                border-radius: 12px;
                                padding: 12px;
                                text-align: center;
                                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                            }
                            /* Título de la tarjeta (Blanco, pequeño) */
                            .op-query-text {
                                color: #FFFFFF !important;
                                font-weight: 700 !important;
                                font-size: 10px !important;
                                letter-spacing: 1.5px !important;
                                text-transform: uppercase !important;
                                margin-bottom: 8px !important;
                                opacity: 0.8;
                            }
                            /* CLASE NUEVA: Para los números del Volumen */
                            .valor-volumen {
                                color: #FFFFFF !important;
                                font-weight: 800 !important;
                                font-family: monospace !important;
                                font-size: 26px !important; 
                                letter-spacing: 2px !important;
                                margin: 0 !important;
                            }
                            /* CLASE NUEVA: Para el nombre de la Paquetería */
                            .valor-carrier {
                                color: #00FFAA !important;
                                font-weight: 500 !important;
                                font-size: 26px !important;
                                font-style: italic !important;
                                letter-spacing: 1px !important;
                                margin: 0 !important;
                            }
                            /* Estilo para los Radio Buttons */
                            div[data-testid="stRadio"] > label {
                                color: #00FFAA !important;
                                font-family: 'Inter', sans-serif;
                                font-weight: 800 !important;
                                font-size: 11px !important;
                                text-transform: uppercase;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                
                    URL_LOGISTICA = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
                    
                    @st.cache_data
                    def load_data_logistica():
                        try:
                            df_l = pd.read_csv(URL_LOGISTICA, low_memory=False)
                            df_l.columns = [c.replace('_x000D_', '').strip() for c in df_l.columns]
                            if 'MES' in df_l.columns:
                                df_l['MES'] = df_l['MES'].astype(str).str.upper().str.strip()
                            if 'FORMA DE ENVIO' in df_l.columns:
                                df_l['FORMA DE ENVIO'] = df_l['FORMA DE ENVIO'].astype(str).str.strip()
                            df_l['CAJAS'] = pd.to_numeric(df_l['CAJAS'], errors='coerce').fillna(0)
                            return df_l
                        except Exception as e:
                            st.error(f"Error de conexión: {e}")
                            return None
                    
                    df_log = load_data_logistica()
                    
                    if df_log is not None:
                        st.markdown("<p class='op-query-text' style='text-align:center;'>DISTRIBUCION DE CARGA MENSUAL</p>", unsafe_allow_html=True)
                        
                        tipo_mov = st.radio(
                            "Selecciona el flujo:",
                            ["TODOS", "COBRO DESTINO", "COBRO REGRESO"],
                            index=0,
                            horizontal=True,
                            key=f"tipo_mov_{mes_sel}"
                        )
                
                        df_log_filtrado = df_log[df_log["MES"] == mes_sel].copy()
                
                        if tipo_mov == "COBRO DESTINO":
                            df_log_filtrado = df_log_filtrado[df_log_filtrado['FORMA DE ENVIO'].str.contains('DESTINO', case=False, na=False)]
                        elif tipo_mov == "COBRO REGRESO":
                            df_log_filtrado = df_log_filtrado[df_log_filtrado['FORMA DE ENVIO'].str.contains('REGRESO', case=False, na=False)]
                
                        if not df_log_filtrado.empty:
                            total_cajas_mes = df_log_filtrado['CAJAS'].sum()
                            df_part = df_log_filtrado.groupby('TRANSPORTE')['CAJAS'].sum().reset_index()
                            df_part['PORCENTAJE'] = (df_part['CAJAS'] / total_cajas_mes) * 100
                            df_part = df_part.sort_values(by='PORCENTAJE', ascending=True)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            c1, c2 = st.columns(2)
                            
                            with c1:
                                st.markdown(f"""
                                    <div class="metric-card-agc">
                                        <p class="op-query-text">VOLUMEN TOTAL (UNIT)</p>
                                        <p class="valor-volumen">{int(total_cajas_mes):,}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                            with c2:
                                lider_n = df_part.iloc[-1]['TRANSPORTE'] if not df_part.empty else "N/A"
                                st.markdown(f"""
                                    <div class="metric-card-agc">
                                        <p class="op-query-text">CARRIER DOMINANTE</p>
                                        <p class="valor-carrier">{lider_n}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # --- GRÁFICO DE BARRAS ---
                            altura_ajustada = max(400, len(df_part) * 40)

                            fig_bar = go.Figure(go.Bar(
                                x=df_part['PORCENTAJE'],
                                y=df_part['TRANSPORTE'],
                                orientation='h',
                                marker=dict(
                                    color=df_part['PORCENTAJE'],
                                    # Cambié el inicio de la escala para que combine mejor con el fondo oscuro
                                    colorscale=['#2c3e50', '#1cc88a'], 
                                    line=dict(color='rgba(255, 255, 255, 0.1)', width=1) # Un borde sutil
                                ),
                                text=df_part['PORCENTAJE'].apply(lambda x: f'{x:.1f}%'),
                                textposition='outside',
                                cliponaxis=False 
                            ))
                            
                            fig_bar.update_layout(
                                height=altura_ajustada,
                                # El color exacto de tus tarjetas AGC
                                paper_bgcolor='#263238', 
                                plot_bgcolor='#263238', 
                                font=dict(family="Inter", size=12, color="#FFFFFF"),
                                margin=dict(l=200, r=60, t=30, b=20),
                                # Añadimos bordes redondeados visuales (vía Streamlit container usualmente)
                                # pero aquí forzamos que el texto y ejes se vean impecables
                                xaxis=dict(
                                    showgrid=False, 
                                    zeroline=False, 
                                    showticklabels=True,
                                    tickfont=dict(color='rgba(255,255,255,0.5)')
                                ),
                                yaxis=dict(
                                    showgrid=False, 
                                    automargin=True,
                                    tickfont=dict(color='#FFFFFF', size=11)
                                ),
                                showlegend=False,
                                # Este paso es clave para que no se vea el recuadro blanco al hacer hover
                                hoverlabel=dict(
                                    bgcolor='#1a2432',
                                    font_size=12,
                                    font_family="Inter"
                                )
                            )
                            
                            # Renderizado con un toque extra de estilo AGC
                            st.plotly_chart(
                                fig_bar, 
                                use_container_width=True, 
                                config={'displayModeBar': False}, 
                                key=f"bar_part_{mes_sel}_{tipo_mov}"
                            )
                
                            # --- EXPANDER: DESGLOSE POR DESTINO ---
                            # --- EXPLORADOR DE RUTAS Y DESTINOS (DISEÑO PREMIUM CON SCROLL AGC) ---
                            st.markdown("<h3 style='color:white; font-size:16px; letter-spacing:2px; font-weight:800; border-left:4px solid #38bdf8; padding-left:10px; margin-bottom:20px;'>🌐 EXPLORADOR DE RUTAS Y DESTINOS</h3>", unsafe_allow_html=True)
                            
                            lista_carriers = ["TODOS"] + sorted(df_log_filtrado['TRANSPORTE'].unique())
                            
                            carrier_sel = st.selectbox(
                                "Selecciona un Carrier para detallar:", 
                                options=lista_carriers,
                                key=f"select_carrier_{mes_sel}_{tipo_mov}"
                            )
                            
                            # Lógica de filtrado
                            if carrier_sel != "TODOS":
                                df_dest_filtered = df_log_filtrado[df_log_filtrado['TRANSPORTE'] == carrier_sel].copy()
                            else:
                                df_dest_filtered = df_log_filtrado.copy()
                            
                            if not df_dest_filtered.empty:
                                df_dest_sum = df_dest_filtered.groupby(['TRANSPORTE', 'DESTINO', 'FORMA DE ENVIO'])['CAJAS'].sum().reset_index()
                                df_dest_sum = df_dest_sum.sort_values(by=['TRANSPORTE', 'CAJAS'], ascending=[True, False])
                                
                                total_sel = df_dest_sum['CAJAS'].sum()
                                st.markdown(f"<p style='color:#00FFAA; font-size:13px; font-weight:800; letter-spacing:1px; margin-bottom:15px;'>UNIDADES EN SELECCIÓN ACTUAL: {int(total_sel):,}</p>", unsafe_allow_html=True)
                                
                                data_rutas = df_dest_sum.to_dict('records')
                            
                                html_rutas = f"""
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
                            
                                        .carrier-group {{
                                            background: #263238;
                                            border: 1px solid rgba(255,255,255,0.05);
                                            border-radius: 12px;
                                            margin-bottom: 12px;
                                            overflow: hidden;
                                            width: 100%;
                                            transition: all 0.3s ease;
                                        }}
                                        .carrier-group:hover {{ border-color: rgba(0, 255, 170, 0.3); }}
                                        
                                        .carrier-header {{
                                            background: rgba(56, 189, 248, 0.1);
                                            padding: 10px 15px;
                                            border-bottom: 1px solid rgba(56, 189, 248, 0.2);
                                            display: flex;
                                            justify-content: space-between;
                                            align-items: center;
                                        }}
                                        .carrier-name {{ color: #38bdf8; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
                                        .route-row {{
                                            display: flex;
                                            justify-content: space-between;
                                            padding: 12px 15px;
                                            align-items: center;
                                        }}
                                        .dest-name {{ color: #FFFFFF; font-size: 12px; font-weight: 600; }}
                                        .method-tag {{ 
                                            background: rgba(168, 85, 247, 0.1); 
                                            color: #a855f7; 
                                            padding: 2px 6px; 
                                            border-radius: 4px; 
                                            font-size: 9px; 
                                            font-weight: 700;
                                            margin-left: 8px;
                                        }}
                                        .unit-badge {{ 
                                            background: rgba(0, 255, 170, 0.1); 
                                            color: #00FFAA; 
                                            padding: 5px 12px; 
                                            border-radius: 8px; 
                                            font-family: monospace; 
                                            font-weight: 800; 
                                            font-size: 13px;
                                            border: 1px solid rgba(0, 255, 170, 0.2);
                                        }}
                                    </style>
                                    {"".join([f'''
                                    <div class="carrier-group">
                                        <div class="carrier-header">
                                            <span class="carrier-name">{item['TRANSPORTE']}</span>
                                            <span style="color:rgba(255,255,255,0.3); font-size:8px; font-weight:800;">DETALLE DE RUTA</span>
                                        </div>
                                        <div class="route-row">
                                            <div>
                                                <span class="dest-name">{item['DESTINO']}</span>
                                                <span class="method-tag">{item['FORMA DE ENVIO']}</span>
                                            </div>
                                            <div class="unit-badge">{int(item['CAJAS']):,} u.</div>
                                        </div>
                                    </div>
                                    ''' for item in data_rutas])}
                                </div>
                                """
                                # Le dejamos scrolling=True para usar nuestro scroll personalizado amor
                                components.html(html_rutas, height=500, scrolling=True)
                                
                            else:
                                st.warning(f"No se encontraron registros para '{tipo_mov}' en el mes seleccionado.")
                
                # PESTAÑA 5: AGC
                with tab_entregas_agc:
                    st.markdown("<h3 style='text-align:center; color:white; font-size:18px; letter-spacing:4px; font-weight:900;'>PROGRAMA DE ENTREGAS AGC</h3>", unsafe_allow_html=True)
                    def render_logistica_flow_responsive(data):
                        html_content = f"""
                        <!DOCTYPE html>
                        <html lang="es">
                        <head>
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <script src="https://cdn.tailwindcss.com"></script>
                            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
                            <style>
                                body {{ 
                                    font-family: 'Inter', sans-serif; 
                                    background-color: #384A52; 
                                    color: #e2e8f0; 
                                    margin: 0;
                                    padding: 8px;
                                }}
                
                                /* ───────── SCROLLBAR PERSONALIZADO AGC ───────── */
                                ::-webkit-scrollbar {{
                                    width: 8px;
                                    height: 8px;
                                }}
                                ::-webkit-scrollbar-track {{
                                    background: rgba(0, 0, 0, 0.1);
                                    border-radius: 10px;
                                }}
                                ::-webkit-scrollbar-thumb {{
                                    /* Estado Natural: Azul sutil (como tu primera imagen) */
                                    background: #3498db; 
                                    border-radius: 10px;
                                    border: 2px solid #384A52; /* Efecto de separación */
                                }}
                                ::-webkit-scrollbar-thumb:hover {{
                                    /* Estado Activo: Verde brillante (como tu segunda imagen) */
                                    background: #2ecc71; 
                                    box-shadow: 0 0 10px rgba(46, 204, 113, 0.5);
                                }}
                
                                .list-row {{
                                    background-color: #263238;
                                    border: 1px solid rgba(255, 255, 255, 0.05);
                                    transition: all 0.2s ease;
                                    margin-bottom: 8px;
                                    border-radius: 12px;
                                    overflow: hidden;
                                    width: 100%;
                                }}
                                
                                .list-row:hover {{
                                    background-color: #2c3b42;
                                    border-color: rgba(56, 189, 248, 0.3);
                                }}
                
                                .status-indicator {{
                                    width: 4px;
                                    min-height: 100%;
                                }}
                                
                                .bg-pending {{ background-color: #f59e0b; box-shadow: 2px 0 10px rgba(245, 158, 11, 0.2); }}
                                .bg-delivered {{ background-color: #10b981; box-shadow: 2px 0 10px rgba(16, 185, 129, 0.2); }}
                                
                                .label-mini {{
                                    font-size: 8px;
                                    text-transform: uppercase;
                                    font-weight: 800;
                                    color: rgba(255,255,255,0.4);
                                    letter-spacing: 0.5px;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="w-full space-y-2">
                                {"".join([f'''
                                <div class="list-row flex items-stretch">
                                    <div class="status-indicator {"bg-delivered" if item['estatus'] == "ENTREGADA" else "bg-pending"}"></div>
                                    
                                    <div class="flex flex-col sm:flex-row flex-1 p-3 sm:items-center gap-3 sm:gap-6">
                                        
                                        <div class="flex-1 min-w-[120px]">
                                            <div class="label-mini">{item['semana']}</div>
                                            <div class="text-base sm:text-lg font-black text-white italic tracking-tighter leading-none">
                                                {item['oc']}
                                            </div>
                                        </div>
                
                                        <div class="hidden lg:block flex-[2]">
                                            <div class="label-mini">Referencia</div>
                                            <div class="text-[10px] text-white/60 italic truncate">
                                                {item['entrega_texto']}
                                            </div>
                                        </div>
                
                                        <div class="grid grid-cols-2 sm:flex sm:gap-12 gap-4 py-2 sm:py-0 border-t sm:border-t-0 sm:border-x border-white/5 sm:px-8">
                                            <div>
                                                <div class="label-mini">Volumen</div>
                                                <div class="text-sm font-bold text-white">{item['cantidad']}</div>
                                            </div>
                                            <div>
                                                <div class="label-mini">Cita</div>
                                                <div class="text-sm font-mono font-bold {"text-slate-400 opacity-50" if "PENDIENTE" in item['cita'].upper() else "text-blue-400"}">
                                                    {item['cita']}
                                                </div>
                                            </div>
                                        </div>
                
                                        <div class="flex justify-between sm:block sm:w-32 text-right border-t sm:border-t-0 pt-2 sm:pt-0">
                                            <div class="label-mini sm:hidden">Estatus</div>
                                            <div class="text-[10px] font-black uppercase {"text-emerald-400" if item['estatus'] == "ENTREGADA" else "text-orange-400"} tracking-tight">
                                                {item['estatus']}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                ''' for item in data])}
                            </div>
                        </body>
                        </html>
                        """
                        return components.html(html_content, height=800, scrolling=True)
                
                    # Dataset corregido
                    data_corregida = [
                        {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 8", "entrega_texto": "9 de marzo", "cita": "10/03/2026 - 11:00 AM", "estatus": "ENTREGADA"},
                        {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 13", "entrega_texto": "23 de marzo", "cita": "24/03/2026 - 08:00 AM", "estatus": "PENDIENTE"},
                        {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 15", "entrega_texto": "6 de abril", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 9197", "cantidad": "520", "semana": "SEM 17", "entrega_texto": "20 de abril", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo (L1)", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo (L2)", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo (L3)", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 21", "entrega_texto": "18 de mayo", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 23", "entrega_texto": "1 de junio", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 25", "entrega_texto": "15 de junio", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 26", "entrega_texto": "22 de junio", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                        {"oc": "OC 10663", "cantidad": "160", "semana": "SEM 27", "entrega_texto": "29 de junio", "cita": "PENDIENTE - 00:00 --", "estatus": "PENDIENTE"},
                    ]
                
                    render_logistica_flow_responsive(data_corregida)
                
                # PESTAÑA 6: CONSIGNAS
                with tab_consignas:
                    # --- CONFIGURACIÓN DE CONEXIÓN (GITHUB) ---
                    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
                    REPO_NAME = "RH2026/nexion"
                    FILE_PATH_CON = "consignas.csv"
                    URL_CONSIGNAS = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH_CON}"
                    
                    @st.cache_data(ttl=600)
                    def load_consignas():
                        try:
                            headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
                            df = pd.read_csv(URL_CONSIGNAS, storage_options=headers, low_memory=False)
                            df.columns = [c.strip() for c in df.columns]
                            
                            # --- LÓGICA DE ORDENAMIENTO POR FECHA ---
                            if 'F.DOC' in df.columns:
                                # Intentamos convertir a fecha (dayfirst=True por si viene en formato DD/MM/YYYY)
                                df['F_TEMP'] = pd.to_datetime(df['F.DOC'], errors='coerce', dayfirst=True)
                                # Ordenamos: las más recientes (NaT o vacías se van al final)
                                df = df.sort_values(by='F_TEMP', ascending=False).drop(columns=['F_TEMP'])
                                
                            return df
                        except Exception as e:
                            st.error(f"Error cargando consignas: {e}")
                            return None
                    
                    def render_expediente_chingon(df):
                        df_clean = df.fillna('')
                        data = df_clean.to_dict('records')
                        
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <script src="https://cdn.tailwindcss.com"></script>
                            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
                            <style>
                                body {{ 
                                    background-color: #384A52; 
                                    color: #e2e8f0; 
                                    font-family: 'Inter', sans-serif; 
                                    margin: 0; 
                                    padding: 10px 15px;
                                }}
                                
                                ::-webkit-scrollbar {{ 
                                    width: 08px; 
                                    height: 10px;
                                }}
                                ::-webkit-scrollbar-track {{ 
                                    background: rgba(0,0,0,0.2); 
                                    border-radius: 10px;
                                }}
                                ::-webkit-scrollbar-thumb {{ 
                                    background: rgba(56, 189, 248, 0.6); 
                                    border-radius: 10px;
                                    border: 2px solid #384A52;
                                }}
                                ::-webkit-scrollbar-thumb:hover {{ 
                                    background: rgba(0, 255, 170, 0.8); 
                                }}
                    
                                .row-expediente {{
                                    background-color: #263238;
                                    border: 1px solid rgba(255, 255, 255, 0.1);
                                    border-radius: 12px;
                                    margin-bottom: 12px;
                                    padding: 18px 24px;
                                    transition: all 0.3s ease;
                                    width: 100%;
                                    box-sizing: border-box;
                                }}
                                
                                .row-expediente:hover {{
                                    border-color: #00FFAA;
                                    background-color: #2d3b42;
                                    transform: scale(1.001);
                                }}
                                
                                .label-mini {{
                                    font-size: 8px;
                                    text-transform: uppercase;
                                    color: rgba(255,255,255,0.6); 
                                    font-weight: 800;
                                    letter-spacing: 1.5px;
                                }}
                                
                                .valor {{ font-size: 14px; font-weight: 700; color: #FFFFFF; }}
                                .highlight {{ color: #00FFAA; font-family: monospace; }}
                                
                                .text-muted-claro {{
                                    color: rgba(255,255,255,0.7); 
                                    font-style: italic;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="w-full">
                                {"".join([f'''
                                <div class="row-expediente">
                                    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
                                        
                                        <div>
                                            <div class="label-mini">Talon / Folio</div>
                                            <div class="valor highlight text-xl leading-none">{str(item.get('TALON', ''))}</div>
                                            <div class="text-[10px] text-blue-300 mt-1 opacity-90 italic">F. Doc: {str(item.get('F.DOC', ''))}</div>
                                        </div>
                                        
                                        <div class="md:border-l md:border-white/10 md:pl-6">
                                            <div class="label-mini">Destinatario / Origen-Dest</div>
                                            <div class="valor truncate text-sm uppercase">{str(item.get('DESTINATARIO', ''))[:45]}</div>
                                            <div class="text-[10px] text-muted-claro">{str(item.get('ORIGEN', ''))} → {str(item.get('DESTINO', ''))}</div>
                                        </div>
                    
                                        <div class="md:border-l md:border-white/10 md:pl-6">
                                            <div class="label-mini">Resumen Financiero</div>
                                            <div class="flex justify-between items-center">
                                                <span class="label-mini">Bultos:</span> <span class="valor text-xs">{str(item.get('BULTOS', '0'))}</span>
                                            </div>
                                            <div class="flex justify-between items-center">
                                                <span class="label-mini">Total Cargo:</span> <span class="valor text-emerald-400 text-sm">${str(item.get('TOTAL', '0'))}</span>
                                            </div>
                                        </div>
                    
                                        <div class="text-right md:border-l md:border-white/10 md:pl-6">
                                            <div class="label-mini">Estatus Entrega</div>
                                            <div class="valor text-sm {"text-orange-400" if not item.get('F.ENTREGA') else "text-white"}">
                                                {str(item.get('F.ENTREGA', 'PENDIENTE'))}
                                            </div>
                                            <div class="text-[10px] text-blue-300 font-bold uppercase tracking-tighter">
                                                {str(item.get('QUIEN RECIBIO', ''))[:25]}
                                            </div>
                                        </div>
                                    </div>
                    
                                    <div class="mt-4 pt-3 border-t border-white/10 flex flex-col md:flex-row justify-between gap-4">
                                        <div class="flex-1">
                                            <span class="label-mini text-blue-200">Domicilio Entrega:</span>
                                            <span class="text-[11px] text-white/80 ml-2"> {str(item.get('DOMICILIO DEL DESTINATARIO', ''))}</span>
                                        </div>
                                        <div class="text-right flex gap-4">
                                            <div>
                                                <span class="label-mini text-orange-200">Ref:</span>
                                                <span class="text-[11px] text-white/80 italic ml-1">{str(item.get('REFERENCIA', '--'))}</span>
                                            </div>
                                            <div>
                                                <span class="label-mini text-white/60">Notas:</span>
                                                <span class="text-[11px] text-white/70 italic ml-1">{str(item.get('OBSERVACION 1', '--'))}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                ''' for item in data])}
                            </div>
                        </body>
                        </html>
                        """
                        return components.html(html_content, height=1200, scrolling=True)
                    
                    # --- EJECUCIÓN PRINCIPAL ---
                    df_consignas = load_consignas()
                    
                    
                    if df_consignas is not None:
                        st.markdown("<h3 style='text-align:center; color:white; font-size:18px; letter-spacing:4px; font-weight:900;'>CONSIGNAS BARCELO</h3>", unsafe_allow_html=True)
                        
                        # Renderizado directo sin buscador amor
                        render_expediente_chingon(df_consignas)


        
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
                        # 1. Obtenemos las fleteras únicas
                        opciones_raw = sorted(df_seguimiento["FLETERA"].unique()) if "FLETERA" in df_seguimiento.columns else []
                        
                        # 2. Creamos la lista final agregando "TODOS" al inicio
                        opciones_f = ["TODOS"] + opciones_raw
                        
                        # 3. Cambiamos a selectbox para selección única
                        filtro_global_fletera = st.selectbox(
                            "FILTRAR PAQUETERÍA", 
                            options=opciones_f, 
                            index=0  # Esto hace que seleccione "TODOS" por defecto
                        )
                
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
                if filtro_global_fletera != "TODOS":
                    df_kpi = df_kpi[df_kpi["FLETERA"] == filtro_global_fletera]
                    
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
                m4.markdown(f"<div class='main-card-kpi' style='border-left-color:{color_ef};'><div class='kpi-label'>Porcentaje de Entrega</div><div class='kpi-value' style='color:{color_ef}; font-size:28px; font-weight:800;'>{eficiencia:.1f}%</div></div>", unsafe_allow_html=True)
                
                # ── 4. SEMÁFORO DE ALERTAS ──
                st.markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:bold; letter-spacing:2px; color:{vars_css['sub']}; text-align:center; margin-top:30px;'>S E M Á F O R O DE ALERTAS</p>", unsafe_allow_html=True)
                
                a1_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] == 1])
                a2_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"].between(2,4)])
                a5_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] >= 5])
                
                c_a1, c_a2, c_a3 = st.columns(3)
                c_a1.markdown(f"<div class='card-alerta' style='border-top: 4px solid #fde047;'><div style='color:#9CA3AF; font-size:10px;'>LEVE (1D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a1_v}</div></div>", unsafe_allow_html=True)
                c_a2.markdown(f"<div class='card-alerta' style='border-top: 4px solid #f97316;'><div style='color:#9CA3AF; font-size:10px;'>MODERADO (2-4D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a2_v}</div></div>", unsafe_allow_html=True)
                c_a3.markdown(f"<div class='card-alerta' style='border-top: 4px solid #ff4b4b;'><div style='color:#9CA3AF; font-size:10px;'>CRÍTICO (+5D)</div><div style='color:white; font-size:28px; font-weight:bold;'>{a5_v}</div></div>", unsafe_allow_html=True)                     
                
                # --- 5. PANEL DE EXCEPCIONES (DISEÑO WAR ROOM) ---
                # --- 5. PANEL DE EXCEPCIONES (DISEÑO WAR ROOM - VERSIÓN FINAL) ---
                st.divider()
                df_criticos = df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] > 0].copy() if not df_sin_entregar.empty else pd.DataFrame()
                
                if not df_criticos.empty:
                    st.markdown(f"""<p style='font-size:11px; font-weight:700; letter-spacing:8px; color:#FFFFFF; text-transform:uppercase; text-align:center; margin-bottom:20px;'>PANEL DE EXCEPCIONES CRÍTICAS</p>""", unsafe_allow_html=True)
                    
                    # Filtros directos sin expander
                    c1, c2 = st.columns(2)
                    with c1: 
                        lista_fleteras = ["TODOS"] + sorted(df_criticos["FLETERA"].unique())
                        sel_f = st.selectbox("TRANSPORTISTA:", options=lista_fleteras, key="f_critico_v2")
                    with c2: 
                        sel_g = st.selectbox("GRAVEDAD ATRASO:", ["TODOS", "CRÍTICO (+5 DÍAS)", "MODERADO (2-4 DÍAS)", "LEVE (1 DÍA)"], key="g_critico_v2")
                    
                    # Lógica de filtrado (Intacta, amor)
                    df_viz = df_criticos.copy()
                    if sel_f != "TODOS": df_viz = df_viz[df_viz["FLETERA"] == sel_f]
                    if sel_g == "CRÍTICO (+5 DÍAS)": df_viz = df_viz[df_viz["DIAS_ATRASO"] >= 5]
                    elif sel_g == "MODERADO (2-4 DÍAS)": df_viz = df_viz[df_viz["DIAS_ATRASO"].between(2, 4)]
                    elif sel_g == "LEVE (1 DÍA)": df_viz = df_viz[df_viz["DIAS_ATRASO"] == 1]
                
                    if not df_viz.empty:
                        df_viz = df_viz.sort_values("DIAS_ATRASO", ascending=False)
                        data_excepciones = df_viz.to_dict('records')
                        
                        # Alto dinámico
                        alto_panel = (len(data_excepciones) * 115) + 20
                
                        # --- 5. PANEL DE EXCEPCIONES (DISEÑO WAR ROOM CON PROMESA DE ENTREGA) ---
                        html_excepciones = f"""
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
                                    border: 1px solid rgba(255, 75, 75, 0.15);
                                    border-left: 6px solid #FF4B4B;
                                    border-radius: 12px;
                                    margin-bottom: 12px;
                                    padding: 18px 25px;
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    transition: all 0.3s ease;
                                    width: 100%;
                                    box-sizing: border-box;
                                }}
                                .card-excepcion:hover {{ 
                                    border-color: #FF4B4B; 
                                    background: #2d3b42;
                                    transform: translateX(5px);
                                }}
                                .badge-retraso {{
                                    background: rgba(255, 75, 75, 0.1);
                                    color: #FF4B4B;
                                    padding: 10px 18px;
                                    border-radius: 10px;
                                    font-weight: 800;
                                    font-family: monospace;
                                    font-size: 22px;
                                    text-align: center;
                                    min-width: 90px;
                                    border: 1px solid rgba(255, 75, 75, 0.3);
                                }}
                                .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }}
                                .factura-destacada {{ color: #FFFFFF; font-size: 19px; font-weight: 800; letter-spacing: 1px; font-family: monospace; }}
                                .info-main {{ color: #FFFFFF; font-size: 14px; font-weight: 700; }}
                                .info-sub {{ color: #FFFFFF; font-size: 11px; font-style: italic; }}
                                .moderado {{ border-left-color: #FFA500; border-color: rgba(255, 165, 0, 0.2); }}
                                .badge-moderado {{ color: #FFA500; background: rgba(255, 165, 0, 0.1); border-color: rgba(255, 165, 0, 0.3); }}
                            </style>
                            {"".join([f'''
                            <div class="card-excepcion {'moderado' if item['DIAS_ATRASO'] < 5 else ''}">
                                <div style="flex: 1.5;">
                                    <div class="label-mini">No. Factura / Pedido</div>
                                    <div class="factura-destacada">{item['NÚMERO DE PEDIDO']}</div>
                                    <div class="info-sub" style="margin-top:5px;">Cliente: {str(item['NOMBRE DEL CLIENTE'])[:35]}</div>
                                </div>
                        
                                <div style="flex: 1.5; padding: 0 15px; border-left: 1px solid rgba(255,255,255,0.05);">
                                    <div class="label-mini">Transporte / Estatus</div>
                                    <div class="info-main" style="color:#38bdf8;">{item['FLETERA']}</div>
                                    <div class="info-sub" style="color: #FFFFFF !important;">Guía: {item['NÚMERO DE GUÍA'] if item['NÚMERO DE GUÍA'] else 'SIN ASIGNAR'}</div>
                                </div>
                        
                                <div style="flex: 1.2; text-align: right; padding-right: 25px; border-left: 1px solid rgba(255,255,255,0.05);">
                                    <div class="label-mini">Días en Ruta</div>
                                    <div class="info-main" style="margin-bottom: 5px;">{item['DIAS_TRANS']} d.</div>
                                    <div class="label-mini" style="font-size: 7px; color: #FFA500;">P. Entrega</div>
                                    <div class="info-sub" style="font-size: 10px; font-style: normal;">{item['PROMESA DE ENTREGA'].strftime('%d/%m/%Y') if hasattr(item['PROMESA DE ENTREGA'], 'strftime') else item['PROMESA DE ENTREGA']}</div>
                                </div>
                        
                                <div>
                                    <div class="label-mini" style="text-align:center;">Retraso</div>
                                    <div class="badge-retraso {'badge-moderado' if item['DIAS_ATRASO'] < 5 else ''}">+{item['DIAS_ATRASO']}</div>
                                </div>
                            </div>
                            ''' for item in data_excepciones])}
                        </div>
                        """
                        # Altura fija para forzar el scroll interno y scrolling=True
                        components.html(html_excepciones, height=700, scrolling=True)
                    else:
                        st.info("No hay pedidos que coincidan con los filtros seleccionados.")
                else:
                    st.success("SISTEMA NEXION: SIN RETRASOS DETECTADOS")
                
               
                # --- 6. BOTÓN DE DESCARGA: EXCEPCIONES Y RETRASOS (SOLO FECHAS) ---
                st.divider()
                
                if not df_viz.empty:
                    import io
                
                    # 1. Preparamos una copia para el reporte sin afectar tu lógica principal
                    df_reporte = df_viz.copy()
                    
                    # Seleccionamos las columnas deseadas
                    columnas_excel = ["NÚMERO DE PEDIDO", "NOMBRE DEL CLIENTE", "FLETERA", "NÚMERO DE GUÍA", "DIAS_TRANS", "DIAS_ATRASO", "FECHA DE ENVÍO", "PROMESA DE ENTREGA"]
                    columnas_existentes = [c for c in columnas_excel if c in df_reporte.columns]
                    
                    # 2. LIMPIEZA DE FECHAS: Quitamos la hora dejando solo la fecha corta (DD/MM/YYYY)
                    for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA"]:
                        if col in df_reporte.columns:
                            # Convertimos a string con formato de fecha para que Excel no le vuelva a poner horas
                            df_reporte[col] = pd.to_datetime(df_reporte[col]).dt.strftime('%d/%m/%Y')
                
                    # 3. Preparamos el archivo Excel en memoria
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_reporte[columnas_existentes].to_excel(writer, index=False, sheet_name='Retrasos_Criticos')
                        
                    buffer.seek(0)
                
                    st.markdown(f"""<p style='font-size:11px; font-weight:700; letter-spacing:3px; color:#38bdf8; text-transform:uppercase; text-align:center; margin-bottom:10px;'>REPORTE DE EXCEPCIONES DETECTADAS</p>""", unsafe_allow_html=True)
                    
                    # 4. El botón de descarga
                    st.download_button(
                        label="DESCARGAR DETALLE DE RETRASOS (EXCEL)",
                        data=buffer,
                        file_name=f"Reporte_Retrasos_Nexion_{mes_sel}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="btn_descarga_excel_retrasos"
                    )
                    
                    st.markdown(f"<p style='color:#94a3b8; font-size:10px; text-align:center;'>Se exportarán {len(df_viz)} registros con anomalías en la entrega.</p>", unsafe_allow_html=True)
                else:
                    st.info("No hay datos de excepciones para exportar en este momento.")
                   
            
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
                
                    # 1. Definimos las columnas y preparamos datos
                    cols_export = ["FECHA", "IMPORTANCIA", "TAREA", "ULTIMO ACCION", "TIPO", "GRUPO"]
                    df_print = df_editado[cols_export].copy()
                    
                    # 2. HTML con fuente reducida y optimización de espacio
                    html_print = f"""
                    <style>
                        @media print {{
                            @page {{ size: letter; margin: 0.5cm; }}
                            body {{ margin: 0; padding: 0; }}
                            #printableArea {{ border: 1px solid black !important; }}
                        }}
                        #printableArea {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            width: 100%;
                            border: 2px solid black;
                            padding: 5px;
                            box-sizing: border-box;
                        }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin-top: 10px;
                            table-layout: auto;
                        }}
                        th {{
                            background-color: #000 !important;
                            color: #fff !important;
                            font-size: 10px;
                            border: 1px solid black;
                            padding: 4px;
                            text-transform: uppercase;
                        }}
                        td {{
                            border: 1px solid black;
                            padding: 4px;
                            font-size: 9px;
                            word-wrap: break-word;
                        }}
                    </style>
                    
                    <div id="printableArea">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid black; padding-bottom: 5px;">
                            <div>
                                <h2 style="margin: 0; font-size: 16px;">Jabones y Productos Especializados</h2>
                                <small style="font-size: 9px;">Distribución y Logística | 2026</small>
                            </div>
                            <div style="text-align: right;">
                                <h3 style="margin: 0; font-size: 14px; text-decoration: underline;">REPORTE DE TAREAS</h3>
                                <p style="margin: 0; font-size: 10px;">FECHA: {pd.Timestamp.now().strftime('%Y-%m-%d')}</p>
                            </div>
                        </div>
                        
                        <table>
                            <thead>
                                <tr>
                                    {"".join([f'<th>{col}</th>' for col in cols_export])}
                                </tr>
                            </thead>
                            <tbody>
                                {"".join([
                                    f'<tr>{"".join([f"<td>{row[col]}</td>" for col in cols_export])}</tr>'
                                    for _, row in df_print.iterrows()
                                ])}
                            </tbody>
                        </table>
                        
                        <div style="margin-top: 10px; border: 1px solid black; padding: 5px; min-height: 60px;">
                            <strong style="font-size: 10px;">COMENTARIOS / NOTAS:</strong>
                            <p style="font-size: 9px; margin: 5px 0;">Generado por: {st.session_state.get('alias', 'Rigoberto')}</p>
                        </div>
                    </div>
                    """
                    
                    # --- FILA DE BOTONES ---
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(":material/sync: SINCRONIZAR", use_container_width=True):
                            df_guardar = df_editado.drop(columns=["PROGRESO_VIEW"], errors="ignore")
                            if guardar_en_github(df_guardar):
                                st.session_state.df_tareas = df_guardar
                                st.rerun()
                    
                    with col2:
                        if st.button(":material/print: IMPRIMIR", use_container_width=True):
                            # Inyectamos el HTML y disparamos la impresión automáticamente
                            components.html(f"{html_print}<script>window.print();</script>", height=0, width=0)
                    
                    with col3:
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df_print.to_excel(writer, index=False, sheet_name='Tareas')
                        
                        st.download_button(
                            label=":material/table_view: BAJAR EXCEL",
                            data=buffer.getvalue(),
                            file_name="tareas_nexion.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                
                
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
                    min-height: 100px !important;
                    max-height: 100px !important;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                div[data-testid="stMetricValue"] { color: #E0E6ED; font-weight: 900; font-size: 1.1rem; }
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
                
                /* Esto cambia específicamente el tamaño del texto del Delta */
                div[data-testid="stMetricDelta"] {
                    font-size: 1.1rem !important; /* Aquí ajustas el tamaño (ejemplo: 0.9rem, 1.2rem, etc.) */
                    font-weight: bold;
                }                
                </style>
                """, unsafe_allow_html=True)
                
                if 'ver_grafico' not in st.session_state:
                    st.session_state.ver_grafico = False
                
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
                
                    for f_col in ['FECHA DE ENVIO', 'PROMESA DE ENTREGA', 'FECHA DE ENTREGA REAL']:
                        if f_col in df_actual.columns:
                            df_actual[f_col] = pd.to_datetime(df_actual[f_col], errors='coerce')
                
                    df_actual['MES'] = df_actual['MES'].astype(str).str.strip().str.upper()
                    df_2025['MES'] = df_2025['MES'].astype(str).str.strip().str.upper()
                
                    df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False)].copy()
                    df_gastos['COSTO DE FLETE'] = df_gastos['COSTO DE LA GUIA'] + df_gastos.get('COSTOS ADICIONALES', 0)
                
                    # 3. INTERFAZ
                    meses_nombres = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
                    mes_actual_txt = meses_nombres[datetime.now().month]
                    opciones_mes = ["TODOS"] + sorted(df_gastos['MES'].unique().tolist())
                    indice_def = opciones_mes.index(mes_actual_txt) if mes_actual_txt in opciones_mes else 0
                
                    c_f1, c_f2 = st.columns(2)
                    with c_f1: mes_sel = st.selectbox(":material/calendar_month: FILTRAR POR MES:", opciones_mes, index=indice_def)
                    with c_f2: flet_sel = st.selectbox(":material/local_shipping: FILTRAR POR FLETERA:", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))
                
                    df_filtered = df_gastos.copy()
                    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
                    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
                
                    # 4. CÁLCULOS
                    mask_evaluable = df_filtered['PROMESA DE ENTREGA'].notna() & df_filtered['FECHA DE ENTREGA REAL'].notna()
                    df_eval = df_filtered[mask_evaluable]
                    pct_eficiencia = ( (df_eval['FECHA DE ENTREGA REAL'] <= df_eval['PROMESA DE ENTREGA']).sum() / len(df_eval) * 100 ) if len(df_eval) > 0 else 0
                
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
                    num_inc = (df_filtered['VALUACION'] > 0).sum()
                    pct_inc = (num_inc/len(df_filtered)*100) if len(df_filtered)>0 else 0
                    inc_vi_monto = (total_flete_2026 + total_valuacion_2026) - total_flete_2025
                    # --- Faltantes para los deltas de abajo ---
                    total_valuacion_2025 = df_2025_filtrado['VALUACION'].sum() if 'VALUACION' in df_2025_filtrado.columns else 0
                    num_inc_2025 = (df_2025_filtrado['VALUACION'] > 0).sum() if 'VALUACION' in df_2025_filtrado.columns else 0
                    pct_inc_2025 = (num_inc_2025 / len(df_2025_filtrado) * 100) if len(df_2025_filtrado) > 0 else 0
                    
                    # La variación de la valuación (para el delta de k7)
                    var_val_monto = total_valuacion_2026 - total_valuacion_2025
                    # La variación de puntos porcentuales (para el delta de k8)
                    var_pct_inc = pct_inc - pct_inc_2025

                    var_inc_vi_pct = (inc_vi_monto / total_flete_2025 * 100) if total_flete_2025 > 0 else 0

                    # --- Lógica para Facturación Mes Anterior ---
                    # --- TRADUCTOR PARA OPERACIONES CON MESES ---
                    meses_map = {
                        "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, 
                        "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8, 
                        "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
                    }
                    meses_inv = {v: k for k, v in meses_map.items()}
                    
                    # --- LÓGICA DELTA FACTURACIÓN (MES ANTERIOR 2026) ---
                    # 1. Identificamos el mes que tienes seleccionado en el filtro
                    mes_actual_str = df_filtered['MES'].unique()[0] if not df_filtered.empty else None
                    
                    if mes_actual_str in meses_map:
                        mes_anterior_num = meses_map[mes_actual_str] - 1
                        mes_anterior_nombre = meses_inv.get(mes_anterior_num)
                        
                        # Aquí el cambio: usamos 'df_actual' que es tu DataFrame madre de 2026
                        df_mes_ant = df_actual[df_actual['MES'] == mes_anterior_nombre] 
                        total_fact_mes_anterior = df_mes_ant['FACTURACION'].sum()
                    else:
                        total_fact_mes_anterior = 0
                    
                    var_fact_mensual = ((total_fact_2026 - total_fact_mes_anterior) / total_fact_mes_anterior * 100) if total_fact_mes_anterior > 0 else 0

                    # --- LÓGICA DELTA EFICIENCIA (MES ANTERIOR 2026) ---
                    if mes_actual_str in meses_map:
                        # Filtramos el DataFrame original para el mes anterior (ya tenemos mes_anterior_nombre arriba)
                        df_eval_ant = df_actual[df_actual['MES'] == mes_anterior_nombre]
                        
                        # Aplicamos la misma máscara de evaluable para el mes pasado
                        mask_eval_ant = df_eval_ant['PROMESA DE ENTREGA'].notna() & df_eval_ant['FECHA DE ENTREGA REAL'].notna()
                        df_eval_ant = df_eval_ant[mask_eval_ant]
                        
                        # Calculamos el porcentaje de eficiencia del mes anterior
                        pct_eficiencia_ant = (
                            (df_eval_ant['FECHA DE ENTREGA REAL'] <= df_eval_ant['PROMESA DE ENTREGA']).sum() / len(df_eval_ant) * 100 
                        ) if len(df_eval_ant) > 0 else 0
                        
                        # La variación son puntos porcentuales (Ej: 95% - 90% = +5%)
                        var_eficiencia_mensual = pct_eficiencia - pct_eficiencia_ant
                    else:
                        var_eficiencia_mensual = 0
                                        
                
                    # --- BOTONES DE CAMBIO DE VISTA ---
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button("VER MÉTRICAS Y TARJETAS", use_container_width=True):
                            st.session_state.ver_grafico = False
                    with c_btn2:
                        if st.button("VER GRÁFICO COMPARATIVO", use_container_width=True):
                            st.session_state.ver_grafico = True
                
                    # --- 5, 6 y 7. VISTA DE TARJETAS ---
                    if not st.session_state.ver_grafico:
                        st.markdown("### RESUMEN DE RENDIMIENTO")
                        k1, k2, k3 = st.columns(3)
                        with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}", delta=f"{var_flete_total:.1f}% vs 2025", delta_color="inverse")
                        with k2: st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}", delta=f"{var_fact_mensual:.1f}% vs mes ant.")
                        with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}", delta=f"{var_volumen:.1f}% Vol.", delta_color="normal")
                        
                        k4, k5, k6 = st.columns(3)
                        with k4: st.metric("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%", delta=f"{diferencia_target:+.2f}% vs Target 7.5%", delta_color="inverse")
                        with k5: st.metric("COSTO POR CAJA", f"${costo_caja_2026:,.2f}", delta=f"{var_costo_caja:.1f}% vs 2025", delta_color="inverse")
                        with k6: st.metric("% EFICIENCIA ENTREGA", f"{pct_eficiencia:.1f}%", delta=f"{var_eficiencia_mensual:+.1f}% vs mes ant.")
                        
                        k7, k8, k9 = st.columns(3)
                        with k7: st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion_2026:,.2f}", delta=f"${var_val_monto:,.2f}", delta_color="inverse")
                        with k8: st.metric("% DE INCIDENCIAS", f"{pct_inc:.1f}%", delta=f"{var_pct_inc:.1f}%", delta_color="inverse")
                        with k9: st.metric("INCREMENTO + VI", f"${inc_vi_monto:,.2f}", delta=f"{var_inc_vi_pct:.1f}%", delta_color="normal")
                
                        # --- 6. ANÁLISIS DINÁMICO PROFUNDO ---
                        st.markdown("### DIAGNÓSTICO ESTRATÉGICO DE OPERACIÓN")
                        
                        # Lógica de interpretación
                        # 1. Análisis de Costo
                        if costo_log_real <= 7.5:
                            status_target = "🟢 DENTRO DEL TARGET"
                            desc_costo = "La gestión financiera es <span class='highlight'>óptima</span>, manteniendo la rentabilidad bajo los parámetros establecidos."
                        else:
                            status_target = "🔴 FUERA DE TARGET"
                            desc_costo = f"Se detecta una desviación del <span class='highlight'>{diferencia_target:.2f}%</span>. Es prioritario revisar la negociación con fleteras o la consolidación de carga."
                
                        # 2. Análisis de Eficiencia (On-Time)
                        if pct_eficiencia >= 95:
                            status_entrega = "Excelencia Logística"
                        elif pct_eficiencia >= 85:
                            status_entrega = "Operación Estable"
                        else:
                            status_entrega = "Alerta de Servicio"
                
                        # 3. Análisis de Incidencias
                        if pct_inc > 5:
                            alerta_incidencias = f"<br>⚠️ <b style='color:#FF4B4B;'>ALERTA:</b> El nivel de incidencias ({pct_inc:.1f}%) está impactando la valuación en <span class='highlight'>${total_valuacion_2026:,.2f}</span>."
                        else:
                            alerta_incidencias = ""
                
                        # 4. Análisis de Eficiencia Unitaria
                        tendencia_caja = "una <span class='highlight'>mejora</span>" if var_costo_caja <= 0 else "un <span class='highlight'>incremento</span>"
                
                        html_analisis = f'''
                        <div class="analysis-box">
                            <div style="display: flex; justify-content: space-between;">
                                <b>ESTADO FINANCIERO:</b> <span>{status_target}</span>
                            </div>
                            <hr style="border: 0.5px solid #243441; margin: 10px 0;">
                            <b>RESUMEN EJECUTIVO:</b><br>
                            • {desc_costo}<br>
                            • La logística de entregas se califica como <span class="highlight">{status_entrega}</span> con un cumplimiento del {pct_eficiencia:.1f}%.<br>
                            • El costo operativo por unidad presenta {tendencia_caja} del {abs(var_costo_caja):.1f}% vs el año anterior.{alerta_incidencias}
                            <br><br>
                            <i style="font-size: 0.85rem; color: #A4B9C8;">* Datos calculados dinámicamente basados en el cierre de fletes y promesas de entrega.</i>
                        </div>'''
                        
                        st.markdown(html_analisis, unsafe_allow_html=True)
                        st.write("")
                        # --- REPORTE DE IMPRESIÓN REPOTENCIADO (RESULTADOS GRÁFICOS) ---
                        def generar_reporte_grafico():
                            estatus_rep = "DENTRO DE PARÁMETROS" if costo_log_real <= 7.5 else "FUERA DE PARÁMETROS"
                            pct_cumplimiento_target = max(0, min(100, (7.5 / costo_log_real) * 100)) if costo_log_real > 0 else 0
                            c_flete_rep = "red" if var_flete_total > 0 else "green"
                            c_caja_rep = "red" if var_costo_caja > 0 else "green"
                            
                            # AJUSTE MANUAL A ZONA GDL (UTC-6)
                            ahora_gdl = datetime.utcnow() - timedelta(hours=6)
                            fecha_hoy = ahora_gdl.strftime('%d/%m/%Y')
                            hora_hoy = ahora_gdl.strftime('%H:%M')
                        
                            return f"""
                            <div id="printable-report" style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #000; background: #fff; max-width: 900px; margin: auto;">
                                <table style="width: 100%; border-bottom: 4px solid #000; margin-bottom: 20px;">
                                    <tr>
                                        <td style="width: 50%;">
                                            <h1 style="margin: 0; font-size: 14px; font-weight: 900; color: #000; border-bottom: none; text-transform: uppercase;">Jabones y Productos Especializados</h1>
                                            <p style="margin: 0; font-size: 11px; font-weight: bold; text-transform: uppercase; color: #666;">Distribución y Logística | 2026</p>
                                        </td>
                                        <td style="width: 50%; text-align: right; font-size: 11px; line-height: 1.6;">
                                            <b>REPORTE ID:</b> LOG-{mes_sel[:3].upper()}-2026<br>
                                            <b>FECHA:</b> {fecha_hoy} | <b>HORA:</b> {hora_hoy} (ZMG)<br>
                                            <span style="border: 2px solid #000; padding: 4px 10px; font-weight: bold; display: inline-block; margin-top: 8px;">
                                                {estatus_rep}
                                            </span>
                                        </td>
                                    </tr>
                                </table>
                        
                                <h2 style="text-align: center; text-transform: uppercase; font-size: 18px; text-decoration: underline;">Análisis Operativo Mensual: {mes_sel}</h2>
                                
                                <div style="margin-bottom: 30px;">
                                    <p style="font-size: 12px; font-weight: bold;">RENDIMIENTO VS META (TARGET 7.5%):</p>
                                    <div style="width: 100%; border: 2px solid #000; height: 35px; position: relative; background: #f0f0f0;">
                                        <div style="width: {pct_cumplimiento_target}%; background: #444; height: 100%;"></div>
                                        <div style="position: absolute; top: 8px; left: 10px; color: #fff; font-weight: bold;">ACTUAL: {costo_log_real:.2f}%</div>
                                        <div style="position: absolute; top: 8px; right: 10px; color: #000; font-weight: bold;">OBJETIVO: 7.50%</div>
                                    </div>
                                </div>
                        
                                <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                                    <div style="flex: 1; border: 1px solid #000; padding: 10px;">
                                        <p style="margin: 0 0 10px 0; font-size: 10px; font-weight: bold; text-align: center; background: #000; color: #fff;">ESTRUCTURA DE COSTOS</p>
                                        <table style="width: 100%; font-size: 11px; border-collapse: collapse;">
                                            <tr><td>Gasto Flete 2026:</td><td style="text-align: right; color:{c_flete_rep}"><b>${total_flete_2026:,.2f}</b></td></tr>
                                            <tr><td>Gasto Flete 2025:</td><td style="text-align: right;">${total_flete_2025:,.2f}</td></tr>
                                            <tr><td>Variación Gasto:</td><td style="text-align: right;"><b>{var_flete_total:+.1f}%</b></td></tr>
                                        </table>
                                    </div>
                                    <div style="flex: 1; border: 1px solid #000; padding: 10px;">
                                        <p style="margin: 0 0 10px 0; font-size: 10px; font-weight: bold; text-align: center; background: #000; color: #fff;">EFICIENCIA UNITARIA</p>
                                        <div style="text-align: center; padding-top: 5px;">
                                            <span style="font-size: 26px; font-weight: bold;">${costo_caja_2026:.2f}</span><br>
                                            <span style="font-size: 10px;">Costo por Caja Actual</span><br>
                                            <span style="font-size: 11px; color:{c_caja_rep}; font-weight:bold;">Var: {var_costo_caja:+.1f}% vs 2025</span>
                                        </div>
                                    </div>
                                </div>
                        
                                <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 30px;">
                                    <tr style="background: #000; color: #fff; border: 1px solid #000;">
                                        <th style="padding: 10px; text-align: left;">MÉTRICA DE OPERACIÓN DETALLADA</th>
                                        <th style="padding: 10px; text-align: center;">VALOR ACTUAL</th>
                                    </tr>
                                    <tr><td style="border: 1px solid #000; padding: 8px;">Facturación Bruta Totales</td><td style="border: 1px solid #000; padding: 8px; text-align: center; font-weight:bold;">${total_fact_2026:,.2f}</td></tr>
                                    <tr><td style="border: 1px solid #000; padding: 8px;">Cajas Enviadas (Volumen)</td><td style="border: 1px solid #000; padding: 8px; text-align: center;">{int(total_cajas_2026):,.0f} Uds.</td></tr>
                                    <tr><td style="border: 1px solid #000; padding: 8px;">Variación Volumen vs 2025</td><td style="border: 1px solid #000; padding: 8px; text-align: center;">{var_volumen:+.1f}%</td></tr>
                                    <tr><td style="border: 1px solid #000; padding: 8px;">Costo Logístico sobre Ventas</td><td style="border: 1px solid #000; padding: 8px; text-align: center; font-weight:bold;">{costo_log_real:.2f}%</td></tr>
                                    <tr style="background: #f9f9f9;"><td style="border: 1px solid #000; padding: 8px;"><b>Eficiencia On-Time (Entregas en Tiempo)</b></td><td style="border: 1px solid #000; padding: 8px; text-align: center; font-weight:bold;">{pct_eficiencia:.1f}%</td></tr>
                                    <tr><td style="border: 1px solid #000; padding: 8px;">Valuación de Incidencias</td><td style="border: 1px solid #000; padding: 8px; text-align: center;">${total_valuacion_2026:,.2f}</td></tr>
                                    <tr><td style="border: 1px solid #000; padding: 8px;">Porcentaje de Incidencias sobre Pedidos</td><td style="border: 1px solid #000; padding: 8px; text-align: center;">{pct_inc:.1f}%</td></tr>
                                    <tr><td style="border: 1px solid #000; padding: 8px;">Impacto Económico Neto (Incremento + VI)</td><td style="border: 1px solid #000; padding: 8px; text-align: center; font-weight:bold;">${inc_vi_monto:,.2f}</td></tr>
                                </table>
                        
                                <div style="margin-top: 60px; display: flex; justify-content: space-between; text-align: center; font-size: 11px;">
                                    <div style="width: 40%; border-top: 2px solid #000; padding-top: 10px;">
                                        <b>Rigoberto Hernández</b><br>Coordinador de Logística Nacional
                                    </div>
                                    <div style="width: 40%; border-top: 2px solid #000; padding-top: 10px;">
                                        <b>Carlos Fialko</b><br>Director General
                                    </div>
                                </div>
                            </div>
                            """
                        
                        # --- MEMORIA TÉCNICA DE CÁLCULO (LÓGICA Y DELTAS) ---
                        def generar_memoria_tecnica():
                            gasto_base_2025 = total_flete_2026 - inc_vi_monto
                            
                            # AJUSTE MANUAL A ZONA GDL (UTC-6)
                            ahora_gdl = datetime.utcnow() - timedelta(hours=6)
                            fecha_hoy = ahora_gdl.strftime('%d/%m/%Y')
                            hora_hoy = ahora_gdl.strftime('%H:%M')
                            
                            return f"""
                            <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 10px; color: #333; max-width: 800px; margin: auto; background-color: #fff;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #000; padding-bottom: 5px; margin-bottom: 15px;">
                                    <div style="text-align: left;">
                                        <h1 style="margin: 0; font-size: 18px; text-transform: uppercase;">Jabones y Productos Especializados</h1>
                                        <p style="margin: 2px 0; font-size: 10px; color: #666; font-weight: bold; text-transform: uppercase;">Memoria Técnica de Cálculo y Variaciones</p>
                                    </div>
                                    <div style="text-align: right; font-size: 10px; color: #444; line-height: 1.6;">
                                        <b>REPORTE ID:</b> TEC-{mes_sel[:3].upper()}-2026<br>
                                        <b>FECHA:</b> {fecha_hoy} | <b>HORA:</b> {hora_hoy} (ZMG)
                                    </div>
                                </div>
                        
                                <p style="font-size: 11px; line-height: 1.4; color: #555; margin-bottom: 15px;">
                                    Este documento detalla la trazabilidad algorítmica de los KPIs presentados en el periodo <b>{mes_sel} 2026</b>, incluyendo la procedencia de los indicadores comparativos (Deltas) contra el ejercicio 2025.
                                </p>
                        
                                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">1. COSTO LOGÍSTICO (KPI DE RENTABILIDAD)</h3>
                                    <div style="background: #f0f0f0; padding: 8px; text-align: center; font-family: 'Courier New'; font-weight: bold; font-size: 13px;">
                                        ( ∑ Flete Actual / ∑ Facturación Actual ) x 100
                                    </div>
                                    <p style="font-size: 10px; margin-top: 5px;"><b>Resultado:</b> (${total_flete_2026:,.2f} / ${total_fact_2026:,.2f}) x 100 = <b>{costo_log_real:.2f}%</b></p>
                                </div>
                        
                                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">2. EFICIENCIA DE ENTREGA (OTD)</h3>
                                    <div style="background: #f0f0f0; padding: 8px; text-align: center; font-family: 'Courier New'; font-weight: bold; font-size: 13px;">
                                        ( Envíos On-Time / Total Envíos Evaluables ) x 100
                                    </div>
                                    <p style="font-size: 10px; margin-top: 5px;"><b>Resultado:</b> Cumplimiento del <b>{pct_eficiencia:.1f}%</b> basado en registros evaluables.</p>
                                </div>
                        
                                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">3. COSTO POR CAJA (EFICIENCIA UNITARIA)</h3>
                                    <div style="background: #f0f0f0; padding: 8px; text-align: center; font-family: 'Courier New'; font-weight: bold; font-size: 13px;">
                                        Gasto de Flete Total / Cantidad de Cajas Enviadas
                                    </div>
                                    <p style="font-size: 10px; margin-top: 5px;"><b>Resultado:</b> ${total_flete_2026:,.2f} / {total_cajas_2026:,.0f} cajas = <b>${costo_caja_2026:,.2f} / caja</b></p>
                                </div>
                        
                                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">4. INCREMENTO LOGÍSTICO + VALUACIÓN INCIDENCIAS (VI)</h3>
                                    <div style="background: #f0f0f0; padding: 8px; text-align: center; font-family: 'Courier New'; font-weight: bold; font-size: 13px;">
                                        (Gasto_2026 - Gasto_2025) + Valuación_Incidencias
                                    </div>
                                    <p style="font-size: 10px; margin-top: 5px;"><b>Desglose:</b> (${total_flete_2026:,.2f} - ${gasto_base_2025:,.2f}) + ${total_valuacion_2026:,.2f} = <b>${inc_vi_monto:,.2f}</b></p>
                                </div>
                        
                                <div style="margin-top: 10px; padding: 10px; border: 2px solid #2276AA; background: #f0f7ff;">
                                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">5. ANÁLISIS DE DELTAS (COMPARATIVA ANUAL)</h3>
                                    <table style="width: 100%; font-size: 9px; border-collapse: collapse; text-align: left; margin-top: 5px;">
                                        <tr style="border-bottom: 1px solid #2276AA; background: #e3f2fd;">
                                            <th style="padding: 4px;">INDICADOR</th>
                                            <th>PREVIO (2025)</th>
                                            <th>ACTUAL (2026)</th>
                                            <th>VARIACIÓN (DELTA)</th>
                                        </tr>
                                        <tr>
                                            <td style="padding: 4px;"><b>Gasto de Flete</b></td>
                                            <td>${gasto_base_2025:,.2f}</td>
                                            <td>${total_flete_2026:,.2f}</td>
                                            <td style="color: #d32f2f; font-weight: bold;">{var_flete_total:+.1f}%</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 4px;"><b>Volumen Cajas</b></td>
                                            <td>{total_cajas_2025:,.0f}</td>
                                            <td>{total_cajas_2026:,.0f}</td>
                                            <td style="color: #2e7d32; font-weight: bold;">{var_volumen:+.1f}%</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 4px;"><b>Costo x Caja</b></td>
                                            <td>${costo_caja_2025:,.2f}</td>
                                            <td>${costo_caja_2026:,.2f}</td>
                                            <td style="color: #d32f2f; font-weight: bold;">{var_costo_caja:+.1f}%</td>
                                        </tr>
                                    </table>
                                </div>
                        
                                <div style="margin-top: 15px; padding: 10px; background: #fffde7; border-left: 5px solid #fbc02d; font-size: 9px; line-height: 1.3;">
                                    <b>INTERPRETACIÓN TÉCNICA:</b> La relación entre la baja de volumen ({var_volumen:+.1f}%) y el alza del gasto ({var_flete_total:+.1f}%) confirma un incremento en la tarifa unitaria por caja. Al no existir incidencias acumuladas (${total_valuacion_2026:,.2f}), el impacto financiero es estrictamente operativo.
                                </div>
                        
                                <div style="margin-top: 30px; display: flex; justify-content: space-around; text-align: center; font-size: 10px;">
                                    <div style="width: 200px; border-top: 1px solid #000; padding-top: 5px;">
                                        <b>Rigoberto Hernández</b><br>Coordinación de Logística
                                    </div>
                                </div>
                            </div>
                            """
                        
                        # --- BOTONES DE IMPRESIÓN (RESULTADOS Y MEMORIA TÉCNICA) ---
                        col_print1, col_print2 = st.columns(2)
                        
                        with col_print1:
                            if st.button(":material/print: GENERAR REPORTE GRÁFICO", type="primary", use_container_width=True):
                                reporte_html = generar_reporte_grafico()
                                components.html(f"""
                                    <script>
                                        var win = window.open('', '', 'height=1100,width=950');
                                        win.document.write(`<html><body>{reporte_html}</body></html>`);
                                        win.document.close();
                                        win.onload = function() {{ win.print(); win.close(); }};
                                    </script>
                                """, height=0)
                        
                        with col_print2:
                            if st.button(":material/calculate: IMPRIMIR CALCULO APLICADO", use_container_width=True):
                                memoria_html = generar_memoria_tecnica()
                                components.html(f"""
                                    <script>
                                        var win = window.open('', '', 'height=1100,width=950');
                                        win.document.write(`<html><body>{memoria_html}</body></html>`);
                                        win.document.close();
                                        win.onload = function() {{ win.print(); win.close(); }};
                                    </script>
                                """, height=0)
                
                    # --- 8. VISTA DE GRÁFICO (COMPARATIVO) ---
                    else:
                        st.markdown("###  COMPARATIVA ANUAL DE GASTOS (2025 vs 2026)")
                        
                        # 1. Preparación de datos
                        df_g_2026 = df_gastos.groupby('MES')['COSTO DE FLETE'].sum().reset_index()
                        df_g_2025 = df_2025.groupby('MES')['COSTO DE LA GUIA'].sum().reset_index()
                
                        # 2. Ordenar meses
                        meses_orden = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
                                       "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
                        df_g_2026['MES'] = pd.Categorical(df_g_2026['MES'], categories=meses_orden, ordered=True)
                        df_g_2025['MES'] = pd.Categorical(df_g_2025['MES'], categories=meses_orden, ordered=True)
                
                        # 3. Creación del Gráfico de Élite
                        fig = go.Figure()
                
                        # --- NUEVA BARRA 2025 (Azul Grisáceo Profundo) ---
                        fig.add_trace(go.Bar(
                            x=df_g_2025.sort_values('MES')['MES'], 
                            y=df_g_2025.sort_values('MES')['COSTO DE LA GUIA'], 
                            name='Gasto 2025', 
                            marker_color='#36b9cc', # <--- AQUÍ ESTÁ EL CAMBIO DE COLOR
                            text=[f'${x:,.0f}' for x in df_g_2025.sort_values('MES')['COSTO DE LA GUIA']],
                            textposition='outside',
                            textfont=dict(color='#A4B9C8') # Mantenemos el texto en gris claro para legibilidad
                        ))
                
                        # Barra 2026 (Oro / Dorado)
                        fig.add_trace(go.Bar(
                            x=df_g_2026.sort_values('MES')['MES'], 
                            y=df_g_2026.sort_values('MES')['COSTO DE FLETE'], 
                            name='Gasto 2026 (Actual)', 
                            marker_color='#D4AF37', # Oro
                            text=[f'${x:,.0f}' for x in df_g_2026.sort_values('MES')['COSTO DE FLETE']],
                            textposition='outside',
                            textfont=dict(color='#FFFFFF')
                        ))
                
                        # 4. Diseño Onyx
                        fig.update_layout(
                            template='plotly_dark',
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            barmode='group',
                            xaxis_title="MESES DE OPERACIÓN",
                            yaxis_title="MONTO TOTAL ($)",
                            font=dict(color="#A4B9C8"),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            margin=dict(t=80) # Espacio extra arriba para las etiquetas
                        )
                
                        st.plotly_chart(fig, use_container_width=True)
                        st.info("💡 Las etiquetas doradas muestran el gasto acumulado actual de JYPESA para comparación directa.")
                
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
                
                
                # --- FUNCIÓN PARA GENERAR EL HTML DE IMPRESIÓN (COSTOS ESPECIALES) ---
                def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, tel_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, cajas, unidad, comentarios, paq_nombre, tipo_pago):
                    filas_prod = f"""
                    <tr>
                        <td style='padding: 8px; border: 1px solid black;'>ENVIO DE MERCANCÍA ESPECIAL</td>
                        <td style='text-align:center; border: 1px solid black;'>-</td>
                        <td style='text-align:center; border: 1px solid black;'>{str(unidad).upper()}</td>
                        <td style='text-align:center; border: 1px solid black;'>{cajas}</td>
                    </tr>"""
                
                    html = f"""
                    <style>
                        @media print {{
                            @page {{ size: letter; margin: 1cm; }}
                            body {{ margin: 0; padding: 0; }}
                        }}
                    </style>
                    
                    <div id="printable-area" style="font-family:Arial; width:100%; box-sizing:border-box; background: white; color: black; display: flex; flex-direction: column; min-height: 95vh;">
                        
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                            <div style="text-align: left;">
                                <h1 style="margin: 0; font-size: 16px; font-weight: 900; letter-spacing: -0.5px; color: #000;">Jabones y Productos Especializados</h1>
                                <p style="margin: 0; font-size: 10px; font-weight: bold; text-transform: uppercase; color: #444;">Distribución y Logística | 2026</p>
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
                    
                        <div style="flex-grow: 1;">
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
                        </div>
                    
                        <div style="margin-top: 30px; padding-bottom: 20px;">
                            <div style="text-align:center; font-size:11px; font-weight:bold; margin-bottom:25px; border-bottom: 1px solid black; padding-bottom: 5px;">
                                RECIBO DE CONFORMIDAD DEL CLIENTE
                            </div>
                            <div style="display:flex; justify-content:space-between; text-align:center; font-size:10px;">
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
                            st.write("")
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
                            st.write("")
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
                if "reset_key" not in st.session_state:
                    st.session_state.reset_key = 0
                
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
                    "JHJY-0050 Llave magnetica para soporte JH": 180.00,
                    "68829526 Rack Dove Dove Mlac Bracket Metalized Bottle 1 Pieza": 193.90,
                    "JHJY-0033 Rack JH  Color Blanco de 2 pzas": 65.00,
                    "JHJY-0034 Rack JH  Color Blanco de 1 pzas": 50.00,
                    "JHJY-0045 Soporte de acero inoxidable Jypesa INOX Cap lock individual": 679.00,
                    "JHJY-0046 Soporte de acero inoxidable Jypesa INOX Cap lock doble": 679.00,
                    "JHJY-0047 Soporte de acero inoxidable Jypesa INOX Cap lock triple": 679.00,
                    "JHJY-0037 Llave para rack de acero Jypesa": 25.50,
                    "JHJY-0026 Rack JH Individual color Negro": 40.28,
                    "JHJY-0027 Rack JH Doble color Negro": 40.28,
        
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
                    <style>
                        @media print {{
                            @page {{ size: letter; margin: 1cm; }}
                            body {{ margin: 0; padding: 0; }}
                        }}
                    </style>
                    
                    <div id="printable-area" style="font-family:Arial; width:100%; box-sizing:border-box; background: white; color: black; display: flex; flex-direction: column; min-height: 95vh;">
                        
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
                                    {f"{str(calle).upper()}<br>" if calle and calle != "-" else ""}
                                    {f"Col: {str(col).upper()} " if col and col != "-" else ""}
                                    {f"C.P.: {cp}" if cp and cp != "-" else ""}
                                    {"<br>" if (col and col != "-") or (cp and cp != "-") else ""}
                                    {str(ciudad).upper()}{f", {str(estado).upper()}" if estado and estado != "-" else ""}<br>
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
                    
                        <div style="margin-top: 40px; padding-bottom: 20px;">
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
                
                nuevo_num = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1
                
                # --- INTERFAZ ---
                
                # --- CAPTURA NUEVA ---
                with st.container():
                    # Definimos valores por defecto (ya no se muestran a Ventas)
                    f_paq_nombre = ""
                    f_tipo_pago = ""
                    
                    # Ahora empezamos directamente con los datos que sí llena Ventas
                    c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])
                    
                    f_folio = c1.text_input(":material/confirmation_number: FOLIO", value=f"JYP-{nuevo_num}", disabled=True)
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
                        placeholder="NOMBRE DE QUIEN SOLICITA LAS MUESTRAS",
                        key=f"soli_{st.session_state.reset_key}" # <--- Agregamos esta línea
                    ).upper()
                
                with col_dest:
                    st.markdown(
                        '<div style="background:#f6c23e;color:black;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">DESTINATARIO / HOTEL</div>', 
                        unsafe_allow_html=True
                    )
                    st.write("")
                    # Agregamos la key dinámica a cada uno:
                    f_h = st.text_input(":material/hotel: Hotel / Nombre", key=f"h_{st.session_state.reset_key}").upper()
                    f_ca = st.text_input(":material/location_on: Calle y Número", key=f"ca_{st.session_state.reset_key}").upper()
                    
                    cd1, cd2 = st.columns(2)
                    f_co = cd1.text_input(":material/map: Colonia", key=f"co_{st.session_state.reset_key}").upper()
                    f_cp = cd2.text_input(":material/mailbox: C.P.", key=f"cp_{st.session_state.reset_key}")
                    
                    cd3, cd4 = st.columns(2)
                    f_ci = cd3.text_input(":material/location_city: Ciudad", key=f"ci_{st.session_state.reset_key}").upper()
                    f_es = cd4.text_input(":material/public: Estado", key=f"es_{st.session_state.reset_key}").upper()
                    
                    f_con = st.text_input(
                        ":material/contact_phone: Contacto Receptor", 
                        placeholder="NOMBRE Y TELÉFONO DE QUIEN RECIBE",
                        key=f"con_{st.session_state.reset_key}" # <--- La clave del éxito
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
                
                st.subheader(":material/shopping_cart: SELECCION DE PRODUCTOS")
                
                if "seleccionados_muestras" not in st.session_state:
                    st.session_state.seleccionados_muestras = []
                
                def eliminar_producto(prod_a_borrar):
                    st.session_state.seleccionados_muestras = [p for p in st.session_state.seleccionados_muestras if p != prod_a_borrar]
                    st.session_state.multi_prods_main = st.session_state.seleccionados_muestras
                
                seleccionados = st.multiselect(
                    ":material/search: Busca y selecciona productos:", 
                    list(precios.keys()),
                    key=f"prod_select_{st.session_state.reset_key}", # <--- Esto es lo que hace la magia
                    default=st.session_state.get('seleccionados_muestras', []),
                    placeholder="Selecciona los productos a enviar..."
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
                
                # 1. Inicializamos el estado del candado si no existe
                if "folio_guardado" not in st.session_state:
                    st.session_state.folio_guardado = False
                
                # BOTÓN GUARDAR
                # BOTÓN GUARDAR
                if col_b1.button(":material/save: GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
                    if not f_h: 
                        st.error("Falta el hotel")
                    # --- NUEVO CANDADO: SOLICITANTE OBLIGATORIO ---
                    elif not f_soli:
                        st.error("Falta el nombre de quien solicita (Solicitante / Agente)")
                    # ---------------------------------------------
                    elif not prods_actuales: 
                        st.error("Selecciona al menos un producto")
                    else:
                        # --- SOLUCIÓN NameError: Definimos nuevo_folio aquí adentro ---
                        nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1
                        
                        direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()
                        
                        reg = {
                            "FOLIO": nuevo_folio, 
                            "FECHA": f_fecha_sel.strftime("%Y-%m-%d"), 
                            "NOMBRE DEL HOTEL": f_h.upper(), 
                            "DESTINO": direccion_completa,
                            "CONTACTO": f_con.upper(), 
                            "SOLICITO": f_soli.upper(), # Aquí ya va validado
                            "PAQUETERIA": f_paq_sel.upper(),
                            "PAQUETERIA_NOMBRE": f_paq_nombre,
                            "NUMERO_GUIA": "", 
                            "COSTO_GUIA": 0.0,
                            "CANTIDAD_TOTAL": total_cantidad,
                            "COSTO_TOTAL": round(total_costo_prods, 2)
                        }
                        
                        # Llenamos las columnas de productos
                        for p in precios.keys():
                            reg[p] = 0
                            
                        for item in prods_actuales:
                            reg[item["desc"]] = item["cant"]
                
                        # Concatenamos y subimos a GitHub
                        df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
                        if subir_a_github(df_f, sha_actual, f"Folio {nuevo_folio}"):
                            # ACTIVAMOS EL CANDADO PARA PERMITIR IMPRESIÓN
                            st.session_state.folio_guardado = True
                            st.success(f"¡Guardado correctamente! Folio: JYP-{nuevo_folio}")
                            time.sleep(1)
                            st.rerun()
                
                # MENSAJE DE ADVERTENCIA PRO (TEXTO EN BLANCO)
                if not st.session_state.folio_guardado:
                    st.markdown("""
                        <div style="background-color: rgba(255, 165, 0, 0.1); border-left: 5px solid #FFA500; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                            <span style="color: white; font-size: 14px;">
                                <b style="color: #FFA500;">BLOQUEO DE SEGURIDAD:</b> 
                                Debes guardar el registro antes de poder imprimir.
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                
                # BOTÓN IMPRIMIR (CON CANDADO)
                # --- BOTÓN GUARDAR PDF ---
                if col_b2.button(":material/picture_as_pdf: GUARDAR PDF", use_container_width=True, disabled=not st.session_state.folio_guardado):
                    if not prods_actuales: 
                        st.warning("No hay productos")
                    else:
                        # AQUÍ ESTÁ EL TRUCO FÁCIL: Armamos el folio JYP aquí mismo
                        folio_simple = f"JYP-{nuevo_num}"
                        
                        h_print = generar_html_impresion(
                            folio_simple, # <--- Mandamos el texto JYP-XX
                            f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem, 
                            f_soli, f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, 
                            prods_actuales, f_coment, f_paq_nombre, f_tipo_pago
                        )
                        
                        # Este código abre la ventana para guardar como PDF con el nombre correcto
                        js_code = f"""
                            <html>
                                <head><title>{folio_simple}_{f_h}</title></head>
                                <body>
                                    {h_print}
                                    <script>setTimeout(function(){{ window.print(); }}, 500);</script>
                                </body>
                            </html>
                        """
                        components.html(js_code, height=0)
                
                # --- BOTÓN BORRAR (CORREGIDO) ---
                if col_b3.button(":material/delete_sweep: BORRAR", use_container_width=True):
                    # Reseteamos el candado de impresión
                    st.session_state.folio_guardado = False
                    
                    # Limpiamos la lista de memoria
                    st.session_state.seleccionados_muestras = []
                    
                    # Aumentamos la llave para que el multiselect se "auto-destruya" y nazca vacío
                    st.session_state.reset_key += 1
                    
                    # Reiniciamos la app para que se vea el cambio
                    st.rerun()
                
                # --- BÚSQUEDA RÁPIDA ---                
                # --- BÚSQUEDA RÁPIDA DE GUÍAS (DISEÑO MAXIMIZADO) ---
                st.write("")
                with st.expander("🔍 CONSULTA DE FOLIOS Y GUIAS)", expanded=False):
                    if not df_actual.empty:
                        busqueda = st.text_input("Escribe el nombre del Hotel o Folio para filtrar:").upper()
                        
                        df_vista = df_actual[["FOLIO", "FECHA", "NOMBRE DEL HOTEL", "PAQUETERIA_NOMBRE", "NUMERO_GUIA"]].copy()
                        df_vista.columns = ["FOLIO", "FECHA ENVÍO", "HOTEL", "PAQUETERÍA", "NÚMERO DE GUÍA"]
                        df_vista = df_vista.fillna('') 
                        
                        if busqueda:
                            df_vista = df_vista[df_vista.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
                        
                        df_render = df_vista.sort_values(by="FOLIO", ascending=False)
                        data_busqueda = df_render.to_dict('records')
                
                        alto_busqueda = min(len(data_busqueda) * 110 + 20, 500) # Subí un poco el alto por tarjeta
                
                        html_busqueda = f"""
                        <div style="font-family: 'Inter', sans-serif; padding-right: 10px;">
                            <style>
                                body {{ background: transparent; margin: 0; padding: 0; }}
                                ::-webkit-scrollbar {{ width: 8px; }}
                                ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                                ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; min-height: 50px; }}
                                ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                
                                .card-busqueda {{
                                    background: #263238;
                                    border: 1px solid rgba(255, 255, 255, 0.05);
                                    border-radius: 10px;
                                    padding: 15px;
                                    margin-bottom: 10px;
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    transition: all 0.3s ease;
                                }}
                                .card-busqueda:hover {{
                                    border-color: #38bdf8;
                                    background: #2d3b42;
                                    transform: translateX(5px);
                                }}
                                .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }}
                                .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }}
                                .val-hotel {{ color: #FFFFFF; font-size: 13px; font-weight: 700; margin-top: 2px; }}
                                
                                /* TEXTO DE LOGÍSTICA MÁS GRANDE */
                                .val-guia {{ color: #38bdf8; font-family: monospace; font-size: 15px; font-weight: 800; line-height: 1.2; }}
                                .val-sub-guia {{ color: #FFFFFF; font-family: monospace; font-size: 13px; font-weight: 700; margin-top: 4px; }}
                                
                                .pendiente {{ color: #f97316 !important; font-style: italic; opacity: 0.8; font-size: 11px; font-weight: 400; }}
                            </style>
                            {"".join([f'''
                            <div class="card-busqueda">
                                <div style="flex: 1.1;">
                                    <div class="label-mini">Folio / Fecha</div>
                                    <div class="val-folio">#{str(item['FOLIO'])}</div>
                                    <div style="color: rgba(255,255,255,0.5); font-size: 10px;">{str(item['FECHA ENVÍO'])[:10]}</div>
                                </div>
                                <div style="flex: 1.8; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                                    <div class="label-mini">Hotel</div>
                                    <div class="val-hotel">{str(item['HOTEL'])[:40]}</div>
                                </div>
                                <div style="flex: 1.6; text-align: right;">
                                    <div class="val-guia { 'pendiente' if item['PAQUETERÍA'] == '' or item['PAQUETERÍA'] == 'nan' else '' }">
                                        { item['PAQUETERÍA'] if item['PAQUETERÍA'] != '' and item['PAQUETERÍA'] != 'nan' else 'PAQUETERÍA PENDIENTE' }
                                    </div>
                                    
                                    <div class="val-sub-guia { 'pendiente' if item['NÚMERO DE GUÍA'] == '' or item['NÚMERO DE GUÍA'] == 'nan' else '' }">
                                        { item['NÚMERO DE GUÍA'] if item['NÚMERO DE GUÍA'] != '' and item['NÚMERO DE GUÍA'] != 'nan' else 'GUÍA PENDIENTE' }
                                    </div>
                                </div>
                            </div>
                            ''' for item in data_busqueda])}
                        </div>
                        """
                        import streamlit.components.v1 as components
                        components.html(html_busqueda, height=alto_busqueda, scrolling=True)
                        
                    else:
                        st.info("No hay registros todavía.")
                
                # --- PANEL DE ADMIN ---
                # --- PANEL DE ADMINISTRACIÓN (CORRECCIÓN DE NAMEERROR) ---
                st.divider()
                
                # 1. Definimos la lista de quiénes mandan aquí
                lista_admins = ["Rigoberto", "JMoreno"]
                
                # 2. DEFINIMOS LA VARIABLE (Esto es lo que te faltaba, amor)
                # Usamos .get() para que si no hay nadie, no truene y ponga 'Invitado'
                # Usamos .get() para que si no hay nadie, no truene y ponga 'Invitado'
                usuario_logeado = st.session_state.get('usuario_activo', 'Invitado')
                
                if usuario_logeado in lista_admins:
                    st.markdown("### 🛠 PANEL DE ADMINISTRACIÓN, PARA USO EXCLUSIVO DE LOGÍSTICA")
                    t1, t2 = st.tabs(["Gestionar Folios Existentes", "Historial y Reportes"])
                    
                    with t1:
                        if not df_actual.empty:
                            df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
                            opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]
                            
                            # 1. El selector siempre arriba
                            fol_sel_texto = st.selectbox(
                                "Seleccionar Folio para procesar (Logística):", 
                                opciones_folios, 
                                index=None, 
                                placeholder="Busca el folio que envió Ventas..."
                            )
                            
                            # --- SECCIONES SIEMPRE VISIBLES ---
                            st.divider() # Una línea para separar
                            c_adm1, c_adm2 = st.columns(2)
                            
                            # Inicializamos variables vacías por si no hay selección
                            datos_fol = None
                            fol_edit = None
                
                            if fol_sel_texto:
                                fol_edit = int(fol_sel_texto.split(" - ")[0])
                                datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]
                
                            with c_adm1:
                                st.subheader("1. ASIGNAR DATOS DE ENVIO")
                                n_paq_nombre = st.selectbox("Nombre de Paquetería", 
                                    ["TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES", "FEDEX", "PAQMEX", "TINY PACK"],
                                    index=None, placeholder="Selecciona paquetería...")
                                
                                n_tipo_pago = st.selectbox("Modalidad de Pago", 
                                    ["CREDITO", "COBRO DESTINO"],
                                    index=None, placeholder="¿Cómo se paga?")
                                
                                n_gui = st.text_input("Número de Guía").upper()
                                n_costo_guia = st.number_input("Costo de Flete ($)", min_value=0.0)
                
                                # El botón solo se activa si hay un folio seleccionado
                                btn_guardar = st.button(":material/update: GUARDAR Y ACTUALIZAR FOLIO", 
                                                        use_container_width=True, 
                                                        disabled=not fol_sel_texto)
                                
                                if btn_guardar and datos_fol is not None:
                                    idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                                    df_actual.at[idx, "PAQUETERIA_NOMBRE"] = n_paq_nombre
                                    df_actual.at[idx, "MODALIDAD_PAGO"] = n_tipo_pago
                                    df_actual.at[idx, "NUMERO_GUIA"] = n_gui
                                    df_actual.at[idx, "COSTO_GUIA"] = n_costo_guia
                                    
                                    if subir_a_github(df_actual, sha_actual, f"Logistica Folio {fol_edit}"):
                                        st.success(f"¡Folio {fol_edit} actualizado!")
                                        st.rerun()
                
                            with c_adm2:
                                st.subheader("2. IMPRESION FINAL")
                                st.info("Verifica los datos antes de imprimir. La base de datos no se afecta hasta que guardes.")
                                
                                # El botón de imprimir también se deshabilita si no hay selección
                                btn_imprimir = st.button(":material/print: IMPRIMIR FORMATO ACTUALIZADO", 
                                                          use_container_width=True, 
                                                          type="primary",
                                                          disabled=not fol_sel_texto)
                                
                                if btn_imprimir and datos_fol is not None:
                                    prods_re = []
                                    for p in precios.keys():
                                        if p in datos_fol and datos_fol[p] > 0: 
                                            prods_re.append({"desc": p, "cant": int(datos_fol[p])})
                                    
                                    paq_a_imprimir = n_paq_nombre if n_paq_nombre else datos_fol.get("PAQUETERIA_NOMBRE", "S/P")
                                    pago_a_imprimir = n_tipo_pago if n_tipo_pago else datos_fol.get("MODALIDAD_PAGO", "PENDIENTE")
                
                                    h_re = generar_html_impresion(
                                        f"JYP-{int(datos_fol['FOLIO'])}", 
                                        datos_fol.get("PAQUETERIA", "ENVIO"), 
                                        datos_fol.get("TIPO_ENTREGA", "DOMICILIO"), 
                                        datos_fol["FECHA"], 
                                        "RIGOBERTO HERNANDEZ", 
                                        "3319753122", 
                                        datos_fol["SOLICITO"], 
                                        datos_fol["NOMBRE DEL HOTEL"], 
                                        "", "", "", 
                                        datos_fol["DESTINO"], 
                                        "", 
                                        datos_fol["CONTACTO"], 
                                        prods_re, 
                                        "RE-IMPRESIÓN DE LOGÍSTICA", 
                                        paq_a_imprimir, 
                                        pago_a_imprimir 
                                    )
                                    components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)

                    with t2:
                        # --- REPORTE DE SALIDAS Y MUESTRAS (DISEÑO PREMIUM CON ORDEN DESCENDENTE) ---
                        if not df_actual.empty:
                            # 1. Cálculos de lógica (Intactos amor)
                            t_prod = df_actual["COSTO_TOTAL"].sum()
                            t_flete = df_actual["COSTO_GUIA"].sum()
                            filas_html = ""
                            tarjetas_html = ""
                            
                            # Usamos fillna para evitar los molestos NaN
                            df_render = df_actual.fillna(0)
                            
                            # --- EL CAMBIO CLAVE: Ordenamos para que el último folio aparezca primero ---
                            df_render = df_render.sort_values(by="FOLIO", ascending=False)
                        
                            for _, r in df_render.iterrows():
                                detalle_p = ""
                                for p in precios.keys():
                                    cant = r.get(p, 0)
                                    if cant > 0: 
                                        detalle_p += f"• {int(cant)} PZAS {str(p).upper()}<br>"
                                
                                # Guardamos para el PDF original (mantenemos tu lógica de impresión)
                                filas_html += f"<tr><td style='border:1px solid black;padding:10px;'>{r['FOLIO']}</td><td style='border:1px solid black;padding:10px;'><b>{str(r['SOLICITO']).upper()}</b><br><small>{r['FECHA']}</small></td><td style='border:1px solid black;padding:10px;'>{str(r['NOMBRE DEL HOTEL']).upper()}<br><small>{str(r['DESTINO']).upper()}</small></td><td style='border:1px solid black;padding:10px;font-size:10px;'>{detalle_p}</td><td style='border:1px solid black;padding:10px;text-align:right;'>${r['COSTO_TOTAL']:,.2f}</td><td style='border:1px solid black;padding:10px;text-align:right;'>${r['COSTO_GUIA']:,.2f}</td></tr>"
                                
                                # 2. Tarjetas visuales (Márgenes corregidos para que respiren amor)
                                tarjetas_html += f"""
                                <div class="card-reporte" style="padding: 20px 30px; margin-bottom: 15px;">
                                    <div class="col-folio" style="flex: 1;">
                                        <div class="label-mini">FOLIO</div>
                                        <div class="val-folio" style="margin-bottom: 5px;">#{r['FOLIO']}</div>
                                        <div class="val-sub">{r['FECHA']}</div>
                                    </div>
                                    
                                    <div class="col-info" style="flex: 2.5; padding: 0 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                                        <div class="label-mini">SOLICITANTE / DESTINO</div>
                                        <div class="val-main" style="margin-bottom: 4px;">{str(r['SOLICITO']).upper()}</div>
                                        <div class="val-sub">{str(r['NOMBRE DEL HOTEL']).upper()}</div>
                                        <div class="val-sub" style="opacity: 0.7;">{str(r['DESTINO']).upper()}</div>
                                    </div>
                                    
                                    <div class="col-detalle" style="flex: 2.5; padding: 0 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                                        <div class="label-mini">DESGLOSE PRODUCTOS</div>
                                        <div class="val-list" style="line-height: 1.6;">{detalle_p if detalle_p else 'SIN DETALLE'}</div>
                                    </div>
                                    
                                    <div class="col-costos" style="flex: 1.5; text-align: right; padding-left: 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                                        <div class="label-mini">INVERSIÓN</div>
                                        <div class="val-costo" style="font-size: 14px; margin-bottom: 5px;">Prod: ${r['COSTO_TOTAL']:,.2f}</div>
                                        <div class="val-flete" style="font-size: 14px;">Flete: ${r['COSTO_GUIA']:,.2f}</div>
                                    </div>
                                </div>
                                """
                        
                            # 3. TABLA DE ENVIOS --- Renderizado del visor con Scroll AGC
                            st.markdown(f"""
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                                    <p style='color:#00FFAA; font-weight:800; letter-spacing:2px; font-size:14px; margin:0;'>RESUMEN DE INVERSIÓN MUESTRAS JYPESA</p>
                                    <p style='color:#FFFFFF; font-size:12px; opacity:0.6;'>Total Registros: {len(df_actual)}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                            html_final = f"""
                            <div style="font-family: 'Inter', sans-serif;">
                                <style>
                                    body {{ background: transparent; margin: 0; padding: 0; }}
                                    .container-reporte {{ height: 500px; overflow-y: auto; padding-right: 10px; }}
                                    .card-reporte {{
                                        background: #263238; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px;
                                        padding: 15px 20px; margin-bottom: 12px; display: flex; min-width: 800px;
                                        justify-content: space-between; align-items: center; transition: 0.3s;
                                    }}
                                    .card-reporte:hover {{ border-color: #38bdf8; background: #2d3b42; }}
                                    .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px; }}
                                    .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }}
                                    .val-main {{ color: #FFFFFF; font-size: 12px; font-weight: 700; }}
                                    .val-sub {{ color: rgba(255,255,255,0.5); font-size: 10px; }}
                                    .val-list {{ color: #FFFFFF; font-size: 9px; line-height: 1.4; opacity: 0.8; }}
                                    .val-costo {{ color: #38bdf8; font-size: 13px; font-weight: 700; font-family: monospace; }}
                                    .val-flete {{ color: #a855f7; font-size: 13px; font-weight: 700; font-family: monospace; }}
                                    
                                    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                                    ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                                    ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; min-height: 60px; }}
                                    ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                                    
                                    .col-folio {{ flex: 0.8; }}
                                    .col-info {{ flex: 2; padding: 0 15px; border-left: 1px solid rgba(255,255,255,0.05); }}
                                    .col-detalle {{ flex: 2; padding: 0 15px; border-left: 1px solid rgba(255,255,255,0.05); }}
                                    .col-costos {{ flex: 1.2; text-align: right; padding-left: 15px; border-left: 1px solid rgba(255,255,255,0.05); }}
                                </style>
                                <div class="container-reporte">{tarjetas_html}</div>
                            </div>
                            """
                            import streamlit.components.v1 as components
                            components.html(html_final, height=520, scrolling=False)
                        
                            # Banner de Totales
                            st.markdown(f"""
                                <div style="background:#263238; border-top: 4px solid #00FFAA; border-radius: 0 0 12px 12px; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                                    <div style="color:rgba(255,255,255,0.6); font-size:12px;">PRODUCTOS: <span style="color:white; font-weight:bold;">${t_prod:,.2f}</span></div>
                                    <div style="color:rgba(255,255,255,0.6); font-size:12px;">FLETES: <span style="color:white; font-weight:bold;">${t_flete:,.2f}</span></div>
                                    <div style="color:#00FFAA; font-size:16px; font-weight:800; letter-spacing:1px;">INVERSIÓN TOTAL: ${(t_prod+t_flete):,.2f}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # 4. BOTONES DE ACCIÓN (Ahora sí fuera del else amor)
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                form_pt_html = f"<html><head><style>@media print{{body{{padding:15mm;}} .no-print{{display:none;}}}} body{{font-family:sans-serif;}} table{{width:100%;border-collapse:collapse;margin-top:15px;font-size:11px;}} th{{background:#eee;border:1px solid black;padding:8px;}}</style></head><body><div style='display:flex;justify-content:space-between;border-bottom:2px solid black;padding-bottom:10px;'><div><h2>JYPESA</h2><p style='margin:0;font-size:10px;'>AUTOMATIZACIÓN DE PROCESOS</p></div><div style='text-align:right;'><b>REPORTE DE SALIDA DE ENVIOS Y MUESTRAS</b><br>GENERADO: {date.today()}</div></div><table><thead><tr><th>FOLIO</th><th>SOLICITANTE</th><th>DESTINO</th><th>DETALLE</th><th>COSTO PROD.</th><th>FLETE</th></tr></thead><tbody>{filas_html}</tbody></table><div style='text-align:right;margin-top:20px;border-top:1px solid black;'><p>TOTAL PRODUCTOS: ${t_prod:,.2f}</p><p>TOTAL FLETES: ${t_flete:,.2f}</p><h3>INVERSIÓN TOTAL: ${(t_prod+t_flete):,.2f}</h3></div></body></html>"
                                if st.button(":material/print: IMPRIMIR REPORTE", type="primary", use_container_width=True):
                                    components.html(f"{form_pt_html}<script>window.print();</script>", height=0)
                            with c2:
                                from io import BytesIO
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_actual.to_excel(writer, index=False)
                                st.download_button(":material/download: DESCARGAR EXCEL", data=output.getvalue(), file_name=f"Matriz_{date.today()}.xlsx", use_container_width=True)
                            with c3:
                                if st.button(":material/update: ACTUALIZAR DATOS", use_container_width=True): st.rerun()
                        
                        else:
                            st.info("No hay registros todavía.")
                
                else:
                    # --- DISEÑO PRO: FRANJA ULTRA DELGADA EN UNA SOLA LÍNEA ---
                    html_restringido = f"""<div style="background-color:{vars_css['card']}; border:1px solid {vars_css['border']}; border-left:8px solid #F7C300; padding:18px 40px; border-radius:10px; margin:15px 0; box-shadow:0 6px 20px rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:space-between;"><div style="display:flex; align-items:center; gap:25px;"><span style="font-size:28px;">🔐</span><div style="text-align:left;"><span style="color:#F7C300; font-weight:900; font-size:14px; letter-spacing:3px; text-transform:uppercase; display:block; margin-bottom:4px;">ÁREA RESTRINGIDA</span><span style="color:{vars_css['text']}; font-size:14px; font-weight:500; opacity:0.9;">El perfil de operador <b>{usuario_logeado}</b> no cuenta con privilegios de nivel <b>Logística</b>.</span></div></div><div style="padding:6px 16px; border:1px solid rgba(247,195,0,0.5); background:rgba(247,195,0,0.1); border-radius:6px; font-size:11px; color:#F7C300; font-weight:900; letter-spacing:1px;">ID ACCESO: {st.session_state.get('usuario_activo', 'ERR')}</div></div>"""
                    st.markdown(html_restringido, unsafe_allow_html=True)
        
    
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
                st.markdown("<p style='font-size:12px; font-weight:normal; color:#FFFFFF; letter-spacing:2px; margin-bottom:10px;'>EDICIÓN SOLICITUD DE MATERIALES</p>", unsafe_allow_html=True)
                
                df_final_pt = st.data_editor(
                    st.session_state.rows, 
                    num_rows="dynamic", 
                    use_container_width=True, 
                    key="editor_pt", 
                    on_change=lookup_pt,
                    column_config={
                        "CODIGO": st.column_config.TextColumn(
                            "CÓDIGO", 
                            help="Escribe el código para buscar el producto",
                            validate=r"^[a-zA-Z0-9_-]+$" # Validación para que no metan caracteres raros
                        ),
                        "DESCRIPCION": st.column_config.TextColumn(
                            "DESCRIPCIÓN DEL PRODUCTO",
                            width="large",
                            disabled=True # Si tienes una función lookup, que no la editen a mano para no romper tu base
                        ),
                        "CANTIDAD": st.column_config.NumberColumn(
                            "CANT.", 
                            min_value=0,
                            max_value=1000,
                            step=1,
                            format="%d", # Sin decimales para que se vea limpio
                            width="small"
                        ),
                        # TRUCO PRO: Añade una columna de estatus visual aunque no esté en tu DF original
                        "DISPONIBILIDAD": st.column_config.CheckboxColumn(
                            "✅ LISTO",
                            help="Marca si ya tienes el material físicamente",
                            default=False
                        )
                    }
                )
                
                # --- EL TOQUE FINAL: INYECTANDO ESTILO AL EDITOR ---
                # Esto va a cambiar el color de las cabeceras del editor para que combinen con tu Dashboard
                st.markdown("""
                    <style>
                    /* Cambiamos el color de fondo de las cabeceras del editor */
                    [data-testid="stDataEditor"] div[role="columnheader"] {
                        background-color: #263238 !important;
                        color: #00FFAA !important;
                        font-weight: bold !important;
                    }
                    
                    /* Cambiamos el color de la fila seleccionada */
                    [data-testid="stDataEditor"] div[role="row"]:hover {
                        background-color: rgba(56, 189, 248, 0.05) !important;
                    }
                
                    /* El TextArea de comentarios con tu Onyx pero con un borde neón */
                    div[data-testid="stTextArea"] textarea {
                        background-color: #465B66 !important;
                        color: white !important;
                        border-radius: 15px !important;
                        border: 1px solid rgba(0, 255, 170, 0.3) !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                
                coment_val = st.text_area(
                    "NOTAS DE LOGÍSTICA", 
                    placeholder="¿Alguna instrucción especial para esta solicitud?", 
                    key="coment_in_pt"
                )
                
                # --- HTML PARA IMPRESIÓN PT ---
                filas_print = df_final_pt[df_final_pt["CODIGO"] != ""]
                tabla_html = "".join([
                    f"<tr><td style='border:1px solid black;padding:6px; font-size:10px;'>{r['CODIGO']}</td>"
                    f"<td style='border:1px solid black;padding:6px; font-size:10px;'>{r['DESCRIPCION']}</td>"
                    f"<td style='border:1px solid black;padding:6px;text-align:center; font-size:10px;'>{r['CANTIDAD']}</td></tr>" 
                    for _, r in filas_print.iterrows()
                ])
                
                form_pt_html = f"""
                <html>
                <head>
                    <style>
                        @page {{ 
                            size: letter; 
                            margin: 1cm; 
                        }}
                        @media print {{
                            body {{ margin: 0; padding: 0; }}
                            .print-container {{ min-height: 95vh; display: flex; flex-direction: column; }}
                        }}
                        body {{ 
                            font-family: sans-serif; 
                            color: black; 
                            background: white; 
                            margin: 0;
                        }}
                        .print-container {{
                            display: flex;
                            flex-direction: column;
                            min-height: 95vh; /* Esto empuja el contenido hacia abajo */
                            width: 100%;
                        }}
                        .main-content {{
                            flex-grow: 1; /* Esta sección crece para ocupar el espacio libre */
                        }}
                        table {{ 
                            width: 100%; 
                            border-collapse: collapse; 
                            margin-top: 10px; 
                        }}
                        th {{ 
                            background: #eee; 
                            border: 1px solid black; 
                            padding: 6px; 
                            text-align: left; 
                            font-size: 11px;
                        }}
                        .comments-section {{
                            margin-top: 15px;
                            font-size: 10px;
                            border: 1px solid black;
                            padding: 8px;
                            min-height: 30px;
                        }}
                        .signature-section {{
                            margin-top: 30px;
                            display: flex;
                            justify-content: space-between;
                            text-align: center;
                            font-size: 9px;
                            padding-bottom: 10px;
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
                        <div class="main-content">
                            <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:5px; margin-bottom:15px;">
                                <div>
                                    <h2 style="margin:0; font-size: 16px; letter-spacing:1px;">Jabones y Productos Especializados</h2>
                                    <p style="margin:0; font-size:9px; letter-spacing:1px;">Distribución y Logística | 2026</p>
                                </div>
                                <div style="text-align:right; font-size:11px;">
                                    <b>FOLIO:</b> {fol_val}<br>
                                    <b>FECHA:</b> {f_val}
                                </div>
                            </div>
                
                            <h3 style="text-align:center; font-size: 14px; letter-spacing:1px; margin: 10px 0;">ENTREGA DE MATERIALES PT</h3>
                            <p style="font-size:11px;"><b>TURNO:</b> {t_val}</p>
                            
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
                
                # Rellenar espacios vacíos sin bordes, solo para empujar las firmas al final
                num_filas = len(filas_c_data)
                # Ajustamos el espacio para que las firmas siempre queden abajo
                espacios = "".join(["<tr style='height:30px;'><td colspan='4'></td></tr>"] * max(0, 15 - num_filas))
                
                form_c_html = f"""
                <html>
                <head>
                    <style>
                        @media print {{
                            @page {{ size: letter; margin: 15mm; }}
                            body {{ -webkit-print-color-adjust: exact; }}
                            header, footer {{ display: none !important; }}
                        }}
                        
                        body {{ 
                            font-family: 'Helvetica', Arial, sans-serif; 
                            background: white; 
                            color: #222; 
                            margin: 0; 
                            padding: 0;
                        }}
                
                        .print-box {{ 
                            padding: 10px;
                            display: flex;
                            flex-direction: column;
                            min-height: 90vh; /* Esto ayuda a que el contenido estire hacia abajo */
                        }}
                
                        /* Cabezal con estilo limpio */
                        .header {{
                            display: flex; 
                            justify-content: space-between; 
                            border-bottom: 2px solid black; 
                            padding-bottom: 15px;
                            align-items: flex-end;
                        }}
                
                        /* Tabla sin bordes en las filas de datos */
                        table {{ 
                            width: 100%; 
                            border-collapse: collapse; 
                            margin-top: 30px; 
                        }}
                
                        thead th {{ 
                            border-bottom: 2px solid black; 
                            padding: 10px 5px; 
                            font-size: 12px; 
                            text-align: left;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }}
                
                        tbody td {{ 
                            padding: 12px 5px; 
                            font-size: 13px; 
                            border: none; /* Quitamos las filas para que se vea más 'chingón' */
                        }}
                
                        /* Contenedor de firmas al final */
                        .signature-container {{
                            margin-top: auto; /* Empuja las firmas al fondo */
                            padding-top: 50px;
                            display: flex;
                            justify-content: space-between;
                            text-align: center;
                            font-size: 12px;
                        }}
                
                        .sig-box {{
                            width: 40%;
                            border-top: 1px solid black;
                            padding-top: 8px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="print-box">
                        <div class="header">
                            <div>
                                <h2 style="margin:0; letter-spacing:1.5px; font-weight: 900; font-size: 14px; text-transform: uppercase;">
                                    Jabones y Productos Especializados
                                </h2>
                                <p style="margin:0; font-size:11px; color: #555; letter-spacing:1px;">Distribución y Logística | 2026</p>
                            </div>
                            <div style="text-align:right;">
                                <span style="font-weight:bold; border: 1.5px solid black; padding: 4px 12px; font-size: 14px;">{f_hora_c}</span>
                                <p style="margin:8px 0 0 0; font-size:10px; font-weight: bold;">FECHA IMPRESIÓN: {now_gdl.strftime('%d/%m/%Y')}</p>
                            </div>
                        </div>
                
                        <h4 style="text-align:center; margin-top:40px; letter-spacing:2px; text-transform: uppercase;">Reporte Entrega de Facturas de Contrarecibo</h4>
                
                        <table>
                            <thead>
                                <tr>
                                    <th>Fecha</th>
                                    <th>Código</th>
                                    <th>Paquetería</th>
                                    <th style="text-align:center;">Cantidad</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tabla_c_html}
                                {espacios}
                            </tbody>
                        </table>
                
                        <div class="signature-container">
                            <div class="sig-box">
                                <b>ELABORÓ</b><br>
                                Rigoberto Hernandez - Cord de Logística
                            </div>
                            <div class="sig-box">
                                <b>RECIBIÓ</b><br>
                                Nombre y Firma
                            </div>
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
         
            
            # --- SUBSECCIÓN D: CARTA RECLAMO ------
            elif st.session_state.menu_sub == "CARTA RECLAMO":
                def generar_carta_pro_html(datos_rem, datos_carta):
                    jypesa_azul = "#005691"
                    jypesa_amarillo = "#F7C300"

                    return f"""
                    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 10px 40px; color: #1a1a1a; max-width: 700px; margin: auto; background: white; line-height: 1.4; border: 1px solid #eee;">
                        <div style="height: 60px;"></div> 
                        <div style="border-bottom: 3px solid {jypesa_azul}; padding-bottom: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="display: flex; flex-direction: column;">
                                <span style="font-size: 1.15em; font-weight: 800; letter-spacing: 1px; color: #000000; text-transform: uppercase;">Jabones y Productos Especializados</span>
                                <span style="font-size: 0.9em; font-weight: 600; color: #666; letter-spacing: 0.5px;">Distribución y Logística | 2026</span>
                            </div>
                            <span style="font-size: 0.9em; color: #444; font-weight: 700;">{datos_carta['fecha_texto']}</span>
                        </div>
                        <div style="margin-bottom: 35px;">
                            <p style="margin: 0; font-size: 0.8em; color: #666; text-transform: uppercase;">Atención a:</p>
                            <p style="margin: 0; font-weight: bold; font-size: 1.15em; color: #000;">{datos_carta['paqueteria']}</p>
                            <p style="margin: 0; font-weight: bold; color: #444;">Departamento de Reclamos / Operaciones</p>
                        </div>
                        <div style="margin-bottom: 30px; background-color: #fefdf5; padding: 15px; border-radius: 4px; border-left: 5px solid {jypesa_amarillo};">
                            <h2 style="font-size: 1.1em; text-transform: uppercase; color: #000; margin:0; font-weight: 800; letter-spacing: 0.5px;">
                                ASUNTO: {datos_carta['asunto']}
                            </h2>
                        </div>
                        <div style="text-align: justify; font-size: 1.05em; color: #222; white-space: pre-wrap; min-height: 300px; padding: 0 10px;">{datos_carta['cuerpo_texto']}</div>
                        <div style="margin-top: 55px; margin-bottom: 40px; border-top: 2px solid #eee; padding-top: 20px;">
                            <p style="margin-bottom: 35px; color: #333;">Atentamente,</p>
                            <p style="margin: 0; font-weight: 800; font-size: 1.2em; color: {jypesa_azul};">{datos_rem['atencion']}</p>
                            <p style="margin: 0; font-size: 0.95em; font-weight: 700; color: #333;">Coordinador de Distribución y Logística</p>
                            <p style="margin: 0; font-size: 0.85em; color: #555;">JYPESA | S.A. de C.V.</p>
                            <div style="margin-top: 15px; font-size: 0.9em; color: #444; background-color: #f9f9f9; padding: 10px; border-radius: 4px; display: inline-block; border: 1px solid #eee;">
                                <span style="color: {jypesa_azul}; font-weight: bold;">📱 33 19 75 31 22</span> <span style="margin: 0 10px; color: #ccc;">|</span> 
                                <span>📞 {datos_rem['tel']}</span> <span style="margin: 0 10px; color: #ccc;">|</span> 
                                <span style="color: {jypesa_azul}; text-decoration: none;">✉ {datos_rem['email']}</span>
                            </div>
                        </div>
                    </div>
                    """
                
                # Fila 1: Datos principales
                st.write("")
                cr1, cr2, cr3, cr4 = st.columns([1.5, 1.2, 1, 1])
                with cr1:
                    paq_rec = st.selectbox(":material/local_shipping: FLETERA", ["ONE PAQUETERIA", "FEDEX", "ESTAFETA", "DHL", "TINY PACK", "PAQUETEXPRESS", "TRES GUERRAS"], key="sel_paq_rec")
                with cr2:
                    inc_rec = st.selectbox(":material/report_problem: INCIDENCIA", ["Faltante", "Extravío", "Siniestro / Daño Total", "Daño Parcial"], key="sel_inc_rec")
                with cr3:
                    fec_rec = st.date_input(":material/calendar_today: FECHA CARTA", date.today(), key="fec_rec")
                with cr4:
                    guia_rec = st.text_input(":material/tag: GUÍA", "JALGDL ", key="guia_rec")
                
                # Fila 2: Detalles (Agregado campo Factura)
                cr5, cr6, cr7, cr8 = st.columns([0.8, 1.2, 1, 1])
                with cr5:
                    caj_rec = st.number_input("CANT. CAJAS", min_value=1, value=1, key="caj_rec")
                with cr6:
                    cod_rec = st.text_input("CÓDIGOS", placeholder="Ej: 4052-L20", key="cod_rec")
                with cr7:
                    fac_rec = st.text_input("FACTURA", placeholder="Ej: F-12345", key="fac_rec")
                with cr8:
                    mon_rec = st.text_input("MONTO", placeholder="Ej: 30,441.87", key="mon_rec")
                
                st.divider()
                
                dict_asuntos_rec = {"Faltante": "Reclamo por Faltante de Mercancía", "Extravío": "Reporte de Extravío de Envío", "Siniestro / Daño Total": "Notificación de Siniestro (Daño Total)", "Daño Parcial": "Reclamo por Daño Parcial"}
                
                # Lógica dinámica mejorada con Factura
                if inc_rec == "Siniestro / Daño Total":
                    det_rec = (f"Por medio de la presente se notifica y formaliza el reclamo por siniestro correspondiente a la guía {guia_rec} con {caj_rec} cajas (Código: {cod_rec}), mismas que se reportan como pérdida total.\n\n"
                               f"Se anexan evidencias y la factura {fac_rec} para la validación y corroboración del valor de la mercancía.\n\n"
                               f"El importe de la mercancía a reclamar asciende a ${mon_rec} + IVA.")
                elif inc_rec == "Faltante":
                    det_rec = (f"Por medio de la presente se notifica el faltante de {caj_rec} cajas con el código {cod_rec} en la entrega correspondiente a la guía {guia_rec} y factura {fac_rec}.\n\n"
                               f"Solicitamos su apoyo para la localización de las mismas o, en su defecto, proceder con la indemnización por la cantidad de ${mon_rec} + IVA.")
                elif inc_rec == "Extravío":
                    det_rec = (f"Se reporta formalmente el extravío del envío amparado bajo la guía {guia_rec} y factura {fac_rec}, el cual contiene {caj_rec} cajas (Código {cod_rec}).\n\n"
                               f"Derivado de lo anterior, solicitamos el reembolso del valor declarado de ${mon_rec} + IVA.")
                else:
                    det_rec = (f"Se notifica que el envío amparado con la guía {guia_rec} y factura {fac_rec} llegó con daños parciales en {caj_rec} cajas (Código {cod_rec}).\n\n"
                               f"Se adjunta evidencia fotográfica de los daños y el costo de reposición asciende a ${mon_rec} + IVA.")
                
                txt_def_rec = f"{det_rec}\n\nAgradeceré su apoyo para dar seguimiento al proceso correspondiente y confirmar la recepción del presente reclamo.\n\nQuedo atento a sus comentarios.\n\nSaludos cordiales."
                
                st.write("### :material/edit: Edición de la Carta")
                cuerpo_final_rec = st.text_area("CUERPO DE LA CARTA", value=txt_def_rec, height=300, key=f"txt_area_rec_{caj_rec}_{mon_rec}_{cod_rec}_{inc_rec}_{guia_rec}_{fac_rec}")
                
                if st.button(":material/print: IMPRIMIR RECLAMO", use_container_width=True, type="primary"):
                    rem_rec = {"atencion": "Rigoberto Hernandez", "tel": "(52) 33 3540 2939 Ext. 157", "email": "rhernandez@jypesa.com"}
                    ms = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
                    fec_txt_rec = f"{fec_rec.day} de {ms[fec_rec.month - 1]} del {fec_rec.year}"
                    info_rec = {"paqueteria": paq_rec, "asunto": dict_asuntos_rec[inc_rec], "fecha_texto": fec_txt_rec, "cuerpo_texto": cuerpo_final_rec}
                    html_final_rec = generar_carta_pro_html(rem_rec, info_rec)
                    components.html(f"<html><body>{html_final_rec}<script>window.print();</script></body></html>", height=0)
                
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
                
                            if st.button(":material/cloud_sync: SINCRONIZAR", type="primary", use_container_width=True):
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
                st.markdown("<h1>ORDER STAGING</h1>", unsafe_allow_html=True)
                
                # Espacio reservado para futura lógica
                st.info("Sección en desarrollo. Próximamente visualización de pedidos en Staging.")
                pass
    
    
    # ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
    st.markdown(f"""
        <div class="footer">
            NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
            <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
            <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
        </div>
    """, unsafe_allow_html=True)
    
























































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































