import os
import io
import re
import json
import time
import zipfile
import unicodedata
import requests
import base64
import math
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
import pytz
import google.generativeai as genai
from io import StringIO, BytesIO
from datetime import datetime, date, timedelta
from github import Github
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="JYPESA | Logistics", layout="wide", initial_sidebar_state="collapsed")


def registrar_acceso(usuario):
    # Usamos tus imports globales: os, pandas (pd), datetime y pytz
    archivo_log = "log_accesos.csv"
    
    # 1. Configuramos la zona horaria de Guadalajara
    zona_horaria = pytz.timezone('America/Mexico_City')
    
    # 2. Obtenemos la hora exacta (6:54 PM ahorita)
    ahora = datetime.now(zona_horaria).strftime("%Y-%m-%d %I:%M %p")
    
    # 3. Creamos el DataFrame para el registro
    nuevo_registro = pd.DataFrame([[usuario, ahora]], columns=["Usuario", "Fecha/Hora"])
    
    # 4. Guardado Forzoso: Si falla aquí, la app se detiene (SIN TRY/EXCEPT)
    if not os.path.isfile(archivo_log):
        # Crea el archivo por primera vez
        nuevo_registro.to_csv(archivo_log, index=False)
    else:
        # Añade al archivo existente
        nuevo_registro.to_csv(archivo_log, mode='a', header=False, index=False)




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

/* Diccionario de colores de acento por prioridad */
:root {{
    --color-urgente: #ff4b4b; /* Rojo Intenso */
    --color-alta: #f97316;    /* Naranja Eléctrico */
    --color-media: #38bdf8;   /* Azul Neón */
    --color-baja: #00FFAA;    /* Verde Esmeralda */
}}

.nexion-task-card {{
    background: rgba(30, 39, 46, 0.6); /* Fondo Glass traslúcido */
    border: 1px solid rgba(255, 255, 255, 0.05); /* Borde de luz sutil */
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 15px;
    transition: all 0.3s ease;
    text-align: left;
    display: flex;
    flex-direction: column;
    border-left: 5px solid #94a3b8; /* Borde de acento por defecto */
    height: auto;
}}

/* EFECTO HOVER DISCRETO Y PRO */
.nexion-task-card:hover {{
    transform: translateX(8px); /* Desplazamiento sutil a la derecha */
    background: rgba(45, 52, 54, 0.8); /* Se aclara un poco */
    box-shadow: 0 10px 25px rgba(0,0,0,0.3); /* Sombra de profundidad */
}}

/* Variaciones de color por prioridad */
.task-urgente {{ border-left-color: var(--color-urgente) !important; }}
.task-alta {{ border-left-color: var(--color-alta) !important; }}
.task-media {{ border-left-color: var(--color-media) !important; }}
.task-baja {{ border-left-color: var(--color-baja) !important; }}

/* Tipografía Elite */
.task-header-folio {{
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: white;
    text-transform: uppercase;
    margin-bottom: 2px;
}}
.task-client-title {{
    font-size: 14px;
    font-weight: 800;
    color: white;
    line-height: 1.2;
}}
.task-sub-info {{
    font-size: 9px;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-top: 4px;
}}
.task-status-label {{
    background: rgba(255,255,255,0.05);
    color: white;
    font-size: 9px;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    margin-top: 10px;
    align-self: flex-start;
}}


#-----RENDER DE MODULO ALERTAS------
.kpi-slim-card {{
    background: rgba(30, 39, 46, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 12px 18px; /* Más delgada verticalmente */
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border-left: 4px solid #94a3b8; /* El acento de color lateral */
}}
.kpi-slim-card:hover {{
    transform: translateX(5px); /* Movimiento lateral discreto */
    background: rgba(30, 39, 46, 0.9);
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}}
.slim-label {{
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 1.2px;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
    margin-bottom: 2px;
}}
.slim-value {{
    font-size: 22px; /* Tamaño reducido para elegancia */
    font-weight: 800;
    line-height: 1;
}}

/* --- ESTILOS MAESTROS DE NEXION (SECCIÓN SEMÁFORO ALERTAS) --- */   
/* Estilo base oscuro para alertas (Negro profundo con glass effect) */
.base-card-alerta {{
    background: rgba(30, 39, 46, 0.8); /* Negro Obsidiana ultra oscuro y glass */
    border: 1px solid rgba(255, 255, 255, 0.05); /* Borde de luz súper fino */
    border-radius: 12px;
    padding: 15px 20px;
    border-left: 5px solid; /* Mantenemos el borde lateral de color */
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 70px; /* Misma altura que tus KPIs de arriba para simetría */
    transition: all 0.3s ease !important;
    cursor: pointer;
}}

/* El hover elegante (Solo flota y brilla un poco) */
.base-card-alerta:hover {{
    transform: translateY(-5px);
    background: rgba(10, 15, 20, 0.9) !important;
    filter: brightness(1.15);
    box-shadow: 0 10px 25px rgba(0,0,0,0.5); /* Sombra de profundidad */
}}

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

/* ───────── SELECTBOX / MULTISELECT (ESTILO COMPLETO) ───────── */


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
    font-size: 08px !important;
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
        st.markdown("<h3 style='text-align: center; margin-bottom: 30px; color: #60A5FA !important; letter-spacing: 5px; font-weight: 500;'>SYSTEM ACCESS REQUIRED</h3>", unsafe_allow_html=True)
        
        # Creamos el formulario. El 'clear_on_submit' puede ser False.
        with st.form("login_form", clear_on_submit=False):
            user_input = st.text_input("OPERATOR ID", placeholder="Introduce tu usuario")
            pass_input = st.text_input("ACCESS KEY", type="password", placeholder="••••••••")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            # Cambiamos st.button por st.form_submit_button
            submit_button = st.form_submit_button("VERIFY IDENTITY", use_container_width=True)
            
            if submit_button:
                lista_usuarios = st.secrets.get("usuarios", {})
                
                             
                # 1. Diccionario para convertir Operator ID en Nombre Real
                nombres_reales = {
                    "Rigoberto": "Rigoberto Hernández",
                    "AGomez": "Ale Gomez",
                    "JMoreno": "Jesus Moreno",
                    "Cynthia": "Cynthia",
                    "Brenda": "Brenda",
                    "Fialko": "Fialko",
                    "Atencion3G": "Sandra Yaneli",
                    "Claudia": "Claudia"
                }
                
                # 2. Diccionario de géneros (F = Femenino, M = Masculino)
                # Esto hará que el saludo sea dinámico
                generos = {
                    "Rigoberto": "M",
                    "AGomez": "F",
                    "JMoreno": "M",
                    "Cynthia": "F",
                    "Brenda": "F",
                    "Fialko": "M",
                    "Yaneli": "F",
                    "Claudia": "F"
                }
                
                # --- VALIDACIÓN EXITOSA ---
                if user_input in lista_usuarios and str(lista_usuarios[user_input]) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = user_input
                    registrar_acceso(user_input)
                    
                    nombre_completo = nombres_reales.get(user_input, user_input)
                    st.session_state.nombre_completo = nombre_completo 
                    
                    gen = generos.get(user_input, "M")
                    saludo = "BIENVENIDA" if gen == "F" else "BIENVENIDO"
                    
                    # --- REDIRECCIÓN INTELIGENTE ---
                    if user_input.upper() == "RIGOBERTO":
                        # Para ti, amor, reseteamos el módulo para que veas la pantalla de cuadros
                        st.session_state.ejecutivo_modulo = None 
                    elif user_input.upper() == "VENTAS":
                        st.session_state.menu_main = "REPORTES"
                        st.session_state.menu_sub = "ENVIO DE MUESTRAS"
                        st.session_state.ejecutivo_modulo = "CORE" # Ellos van directo
                    elif user_input.upper() == "ATENCION3G":
                        st.session_state.menu_main = "SEGUIMIENTO"
                        st.session_state.menu_sub = "ALERTAS"
                        st.session_state.ejecutivo_modulo = "CORE" # Ellos van directo
                    else:
                        st.session_state.menu_main = "DASHBOARD"
                        st.session_state.menu_sub = "GENERAL"
                        st.session_state.ejecutivo_modulo = "CORE"

                    st.success(f"¡{saludo}!, {nombre_completo.upper()}") 
                    time.sleep(1) 
                    st.rerun()
                
                # MANEJO DEL ERROR
                else:
                    st.error("ERROR: ACCESS DENIED. INVALID CREDENTIALS.")
                    
# ── FLUJO DE CONTROL (SPLASH -> LOGIN -> APP) ──────────

# ==============================================================================
# ── FLUJO DE CONTROL MAESTRO (SPLASH -> LOGIN -> CEO GATE -> CORE) ──
# ==============================================================================

# 1. ¿FALTA MOSTRAR EL SPLASH?
if not st.session_state.get('splash_completado', False):
    # Creamos el contenedor vacío una sola vez
    p = st.empty()
    
    # Mensajes ejecutivos y técnicos para JYPESA
    mensajes = [
        "ESTABLISHING SECURE ACCESS...",
        "LOADING LOGISTICS DATA...",
        "SYNCHRONIZING WITH GITHUB REPO...",
        "SYSTEM READY..."
    ]
    
    for m in mensajes:
        with p.container():
            st.markdown(f"""
            <div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:80px;height:80px;border:2px solid rgba(255,255,255,0.05); border-top:2px solid #00D4FF; border-radius:50%;animation:spin 1s linear infinite; box-shadow: 0 0 15px rgba(0,212,255,0.3);"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:white;text-transform:uppercase;">{m}</p>
            </div>
            <style>
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
            </style>
            """, unsafe_allow_html=True)
            # Tiempo estético para lectura
            time.sleep(0.7)
            
    # Limpiamos y marcamos como completado
    p.empty()
    st.session_state.splash_completado = True
    st.rerun()

# 2. ¿SPLASH LISTO PERO NO SE HA LOGGEADO?
elif not st.session_state.get('autenticado', False):
    # Llamamos a tu función de login existente
    login_screen()


# ── 3. ¿YA SE LOGUEÓ PERO ES RIGOBERTO Y NO HA ELEGIDO MÓDULO? (PUERTA ÉLITE LOGO CENTRADO) ──
elif st.session_state.usuario_activo.upper() == "RIGOBERTO" and st.session_state.get('ejecutivo_modulo') is None:
    
    # 💎 CSS DE ALTA GAMA: Centrado absoluto con Flexbox
    st.markdown("""
        <style>
        /* Título NEXION Protagonista (Arriba, Grande, Fuerte) */
        .brand-title {
            text-align: center;
            font-size: 55px; /* Gigante y potente */
            font-weight: 900;
            letter-spacing: 25px; /* Ultra espaciado ejecutivo */
            color: #ffffff;
            margin-top: 40px;
            margin-bottom: 5px;
            text-transform: uppercase;
            text-shadow: 0 0 15px rgba(255, 255, 255, 0.15); /* Brillo sutil blanco */
        }
    
        /* Subtítulo Versión Discreto */
        .brand-version {
            text-align: center;
            font-size: 10px;
            color: #FFFFFF; /* Muy tenue */
            letter-spacing: 5px;
            margin-bottom: 25px;
            text-transform: uppercase;
        }
    
        /* Saludo CEO Discreto (Abajo, Pequeño, Elegante) */
        .ceo-protocol-greet {
            text-align: center;
            font-size: 12px; /* Pequeño y sutil */
            font-weight: 400;
            letter-spacing: 4px;
            color: #8fa3b0; /* Color sub de NEXION */
            margin-bottom: 45px; /* Espacio antes de los módulos */
            text-transform: uppercase;
        }
    
        /* --- RESTO DEL CSS DE LAS TARJETAS (Mantenemos el look compacto) --- */
        .ceo-card {
            background: rgba(30, 39, 46, 0.85) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 18px;
            padding: 20px 10px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            height: 190px; /* Un pelín más compactas */
            margin-bottom: 15px;
        }
    
        .ceo-card:hover {
            transform: translateY(-8px);
            background: rgba(45, 52, 54, 0.98) !important;
            border-color: #00D4FF !important;
            box-shadow: 0 10px 25px rgba(0, 212, 255, 0.2);
        }
    
        .ceo-icon { 
            font-size: 48px; 
            margin-bottom: 12px; 
            filter: drop-shadow(0 0 8px rgba(255,255,255,0.1)); 
        }
    
        .ceo-title { 
            font-size: 11px; 
            font-weight: 800; 
            color: #ffffff; 
            letter-spacing: 2px; 
            text-transform: uppercase; 
            text-align: center; 
        }
    
        .stButton>button { 
            border-radius: 8px !important; 
            font-size: 10px !important; 
            padding: 2px 10px !important; 
            background: rgba(255,255,255,0.03) !important; 
            transition: all 0.3s ease !important; 
        }
    
        [data-testid="stHorizontalBlock"] { 
            max-width: 900px; 
            margin: 0 auto; 
        }
        </style>
    """, unsafe_allow_html=True)
    
    # --- LOGO Y SALUDOS ---
    st.markdown('<div class="brand-logo-full-center">', unsafe_allow_html=True)
    try:
        st.image("n2.png", width=180) 
    except:
        st.markdown("<h1 style='text-align:center; color:white; letter-spacing:10px;'>NEXION</h1>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div class='brand-version'>CORPORATE OPERATIVE SYSTEM v3.0</div>", unsafe_allow_html=True)
    st.markdown("<div class='ceo-protocol-greet'>BIENVENIDO // SECURE ACCESS GRANTED</div>", unsafe_allow_html=True)

    # ⚡ REPARACIÓN: Definimos las columnas antes de usarlas
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    with m_col1:
        st.markdown("<div class='ceo-card'><div class='ceo-icon'><svg xmlns='http://www.w3.org/2000/svg' height='40px' viewBox='0 -960 960 960' width='40px' fill='#60A5FA'><path d='M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm-40-82v-78q-33 0-56.5-23.5T360-320v-40L168-552q-8 35-8 72 0 140 89.5 246T440-162Zm282-192q30-42 44-90t14-96q0-128-78.5-224T520-800v40q0 33-23.5 56.5T440-680h-80v80q0 33-23.5 56.5T280-520h-40v80h200q33 0 56.5 23.5T520-360v80h40q33 0 56.5 23.5T640-233v23q48-26 82-72Z'/></svg></div><div class='ceo-title'>Dashboard<br>Global</div></div>", unsafe_allow_html=True)
        if st.button("ACCEDER", key="btn_dash", use_container_width=True):
            st.session_state.ejecutivo_modulo = "CORE"; st.session_state.menu_main = "DASHBOARD"; st.rerun()

    with m_col2:
        st.markdown("<div class='ceo-card'><div class='ceo-icon'><svg xmlns='http://www.w3.org/2000/svg' height='40px' viewBox='0 -960 960 960' width='40px' fill='#60A5FA'><path d='M240-160q-33 0-56.5-23.5T160-240v-440q0-33 23.5-56.5T240-760h440l120 160v360q0 33-23.5 56.5T720-160H240Zm0-80h480v-330L655-680H240v440Zm240-100q42 0 71-29t29-71q0-42-29-71t-71-29q-42 0-71 29t-29 71q0 42 29 71t71 29Z'/></svg></div><div class='ceo-title'>Seguimiento<br>Entregas</div></div>", unsafe_allow_html=True)
        if st.button("GESTIONAR", key="btn_seg", use_container_width=True):
            st.session_state.ejecutivo_modulo = "CORE"; st.session_state.menu_main = "SEGUIMIENTO"; st.session_state.menu_sub = "ALERTAS"; st.rerun()
    
    with m_col3:
        st.markdown("<div class='ceo-card'><div class='ceo-icon'><svg xmlns='http://www.w3.org/2000/svg' height='40px' viewBox='0 -960 960 960' width='40px' fill='#60A5FA'><path d='M320-240h320v-80H320v80Zm0-160h320v-80H320v80ZM240-80q-33 0-56.5-23.5T160-160v-640q0-33 23.5-56.5T240-880h320l240 240v480q0 33-23.5 56.5T720-80H240Zm280-520v-200H240v640h480v-440H520Z'/></svg></div><div class='ceo-title'>Reportes<br>Ejecutivos</div></div>", unsafe_allow_html=True)
        if st.button("VISUALIZAR", key="btn_rep", use_container_width=True):
            st.session_state.ejecutivo_modulo = "CORE"; st.session_state.menu_main = "REPORTES"; st.session_state.menu_sub = "% LOGISTICO"; st.rerun()
    
    with m_col4:
        st.markdown("<div class='ceo-card'><div class='ceo-icon'><svg xmlns='http://www.w3.org/2000/svg' height='40px' viewBox='0 -960 960 960' width='40px' fill='#60A5FA'><path d='M240-80q-33 0-56.5-23.5T160-160v-400q0-33 23.5-56.5T240-640h40v-80q0-83 58.5-141.5T480-920q83 0 141.5 58.5T680-720v80h40q33 0 56.5 23.5T800-560v400q0 33-23.5 56.5T720-80H240Zm0-80h480v-400H240v400Zm240-120q33 0 56.5-23.5T560-360q0-33-23.5-56.5T480-440q-33 0-56.5 23.5T400-360q0 33 23.5 56.5T480-280ZM360-640h240v-80q0-50-35-85t-85-35q-50 0-85 35t-35 85v80Z'/></svg></div><div class='ceo-title'>Admin<br>Hub Log</div></div>", unsafe_allow_html=True)
        if st.button("CONFIGURAR", key="btn_hub", use_container_width=True):
            st.session_state.ejecutivo_modulo = "CORE"; st.session_state.menu_main = "HUB LOG"; st.session_state.menu_sub = "SMART ROUTING"; st.rerun()


   

else:
    # ── HEADER CON 4 COLUMNAS (BÚSQUEDA OPTIMIZADA) ───────────────────────────
    # --- CONFIGURACIÓN GITHUB ---
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "locales.csv"
    
    # --- CONFIGURACIÓN DE PÁGINA ---
    st.set_page_config(page_title="NEXION SMART LOGISTICS", layout="wide")
    
    # --- ESTILO CORPORATIVO JYPESA ---
    st.markdown("""
        <style>
        .main { background-color: #0B1114; color: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
        .header-container { display: flex; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #1A2226; padding-bottom: 10px; }
        .header-logo { width: 180px; margin-right: 20px; }
        h1 { color: #FFFFFF; font-size: 1.4rem; letter-spacing: 1px; margin: 0; }
        h3 { color: #FFFFFF; text-transform: uppercase; letter-spacing: 1px; font-size: 0.95rem; padding-bottom: 5px; margin-top: 20px; border-bottom: 1px solid #1A2226; }
        
        /* BOTÓN TOTALMENTE CENTRADO Y ANCHO */
        .stButton>button { 
            background-color: #00FFAA; 
            color: #0B1114; 
            font-weight: bold; 
            border-radius: 4px; 
            border: none; 
            height: 4em; 
            width: 100%; 
            text-transform: uppercase;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            font-size: 1rem;
            letter-spacing: 2px;
        }
        .stButton>button:hover { background-color: #00D18B; color: #FFFFFF; }
        
        .stSelectbox label, .stMultiSelect label, .stTextInput label { color: #FFFFFF !important; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
        div[data-baseweb="select"] { background-color: #1A2226; border: 1px solid #333; border-radius: 4px; }
        .stAlert { background-color: #1A2226; color: #00FFAA; border: 1px solid #00FFAA; border-radius: 4px; }
        hr { border: 0.5px solid #1A2226; }
        </style>
        """, unsafe_allow_html=True)
    
    # --- FUNCIONES ---
    def descargar_matriz():
        timestamp = int(time.time())
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?t={timestamp}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json", "Cache-Control": "no-cache"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            datos = response.json()
            content = base64.b64decode(datos['content']).decode('utf-8')
            df = pd.read_csv(StringIO(content))
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip().replace(['nan', 'None', 'NaN', 'null'], '')
            return df, datos['sha']
        return None, None
    
    def actualizar_github(df, sha, mensaje):
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        csv_content = df.to_csv(index=False)
        encoded = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        payload = {"message": mensaje, "content": encoded, "sha": sha}
        response = requests.put(url, headers=headers, json=payload)
        return response.status_code == 200
    
    def get_base64_logo(file):
        try:
            with open(file, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        except:
            return None
    
    # --- HEADER ---
    logo_b64 = get_base64_logo('n2.png')
    if logo_b64:
        st.markdown(f'<div class="header-container"><img src="data:image/png;base64,{logo_b64}" class="header-logo"><h1></h1></div>', unsafe_allow_html=True)
    else:
        st.title("NEXION SMART LOGISTICS")
    
    # --- LÓGICA DE DATOS ---
    df, sha = descargar_matriz()
    
    if df is not None:
        # --- SECCIÓN 1: CARGA ---
        st.markdown("<h3>1. SALIDA DE ALMACEN (CARGA)</h3>", unsafe_allow_html=True)
        disponibles = df[~df['TRIGGER'].isin(['EN RUTA', 'ENTREGADO'])]
        
        if not disponibles.empty:
            pedidos_sel = st.multiselect("SELECCIONAR FOLIOS:", options=disponibles['NÚMERO DE PEDIDO'].unique(), key="ms_carga")
            if pedidos_sel:
                ref_k = str(pedidos_sel[0])
                f1 = st.camera_input("FOTO 1: PRODUCTO", key=f"c1_{ref_k}")
                if f1:
                    f2 = st.camera_input("FOTO 2: UNIDAD", key=f"c2_{ref_k}")
                    if f2:
                        f3 = st.camera_input("FOTO 3: ESTIBA", key=f"c3_{ref_k}")
                        if f3:
                            if st.button("CONFIRMAR SALIDA DE UNIDAD"):
                                with st.spinner("PROCESANDO..."):
                                    ahora_c = datetime.now().strftime('%Y-%m-%d %H:%M')
                                    for p in pedidos_sel:
                                        idx = df[df['NÚMERO DE PEDIDO'] == str(p)].index
                                        df.loc[idx, 'TRIGGER'] = 'EN RUTA'
                                        df.loc[idx, 'FECHA DE ENVÍO'] = ahora_c
                                    if actualizar_github(df, sha, f"Carga: {pedidos_sel}"):
                                        st.rerun()
        else:
            st.info("NO HAY PENDIENTES EN ALMACEN")
    
        st.markdown("<br><hr>", unsafe_allow_html=True)
    
        # --- SECCIÓN 2: ENTREGA ---
        st.markdown("<h3>2. ENTREGA EN DESTINO</h3>", unsafe_allow_html=True)
        en_ruta = df[df['TRIGGER'] == 'EN RUTA']
        
        if not en_ruta.empty:
            opciones = en_ruta.apply(lambda x: f"{x['NÚMERO DE PEDIDO']} | {x['NOMBRE DEL CLIENTE']}", axis=1)
            sel = st.selectbox("PEDIDO A ENTREGAR:", opciones)
            id_p = sel.split(" | ")[0].strip()
            dat = en_ruta[en_ruta['NÚMERO DE PEDIDO'] == id_p].iloc[0]
            
            st.markdown(f"""
                <div style="background-color: #1A2226; padding: 15px; border-radius: 4px; border-left: 4px solid #00FFAA; margin-bottom: 20px;">
                    <p style="margin:0; font-size: 0.7rem; color: #00FFAA; font-weight: bold;">DESTINO:</p>
                    <p style="margin:0; font-size: 1rem; font-weight: bold;">{dat['DESTINO']}</p>
                    <p style="margin:10px 0 0 0; font-size: 0.7rem; color: #00FFAA; font-weight: bold;">DOMICILIO:</p>
                    <p style="margin:0; font-size: 0.85rem;">{dat['DOMICILIO']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            f_ent = st.camera_input("EVIDENCIA FINAL", key=f"ce_{id_p}")
            obs = st.text_input("OBSERVACIONES:", key=f"obs_{id_p}")
    
            # BOTÓN DE PANTALLA COMPLETA
            if st.button("FINALIZAR ENTREGA"):
                if f_ent:
                    with st.spinner("GUARDANDO..."):
                        ahora_e = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        idx_f = df[(df['NÚMERO DE PEDIDO'] == id_p) & (df['TRIGGER'] == 'EN RUTA')].index
                        if not idx_f.empty:
                            df.loc[idx_f[0], 'FECHA DE ENTREGA REAL'] = ahora_e
                            df.loc[idx_f[0], 'TRIGGER'] = 'ENTREGADO'
                            df.loc[idx_f[0], 'INCIDENCIAS'] = obs
                            if actualizar_github(df, sha, f"Entrega: {id_p}"):
                                st.rerun()
                else:
                    st.error("EVIDENCIA FOTOGRAFICA REQUERIDA")
        else:
            st.info("NO HAY PEDIDOS EN RUTA")
    else:
        st.error("ERROR DE CONEXIÓN CON LOCALES.CSV")


    # ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
    st.markdown(f"""
        <div class="footer">
            NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
            <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
            <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
        </div>
    """, unsafe_allow_html=True)
