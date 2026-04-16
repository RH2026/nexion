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

/* 1. ELIMINAR BARRA SUPERIOR (GITHUB, FORK, MENU) Y AJUSTAR ESPACIO */
header[data-testid="stHeader"] {{
    visibility: hidden;
    height: 0% !important;
}}

.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
}}

/* 2. CONFIGURACIÓN DE FONDO Y TEXTO */
.main {{ 
    background-color: {vars_css['bg']}; 
    color: {vars_css['text']}; 
    font-family: 'Inter', sans-serif; 
}}

/* 4. FUERZA BRUTA: BOTONES AL 100% ESTILO NEXION */
[data-testid="stVerticalBlock"] > div {{
    width: 100% !important;
}}

.stButton {{
    width: 100% !important;
}}

.stButton > button {{
    width: 100% !important;
    background-color: #00FFAA !important;
    color: #0B1114 !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    height: 50px !important;
    border: none !important;
    display: block !important;
    margin: 10px 0 !important;
}}

/* 5. INPUTS Y SELECTORES (Look minimalista) */
.stTextInput>div>div>input, div[data-baseweb="select"] {{
    background-color: {vars_css['card']} !important;
    color: white !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 2px !important;
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
}}

</style>
""", unsafe_allow_html=True)


# ── DEFINICIÓN DE INTERFAZ DE LOGIN ────────────────────
def login_screen():
    # Ajustamos las proporciones para la columna central
    _, col, _ = st.columns([2, 2, 2]) 
    
    with col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; margin-bottom: 30px; color: #60A5FA !important; letter-spacing: 5px; font-weight: 500;'></h3>", unsafe_allow_html=True)
        
        # Creamos el formulario. El 'clear_on_submit' puede ser False.
        with st.form("login_form", clear_on_submit=False):
            user_input = st.text_input("USUARIO", placeholder="Introduce tu usuario")
            pass_input = st.text_input("PASSWORD", type="password", placeholder="••••••••")
            
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

   

else:
    # ── HEADER CON 4 COLUMNAS (BÚSQUEDA OPTIMIZADA) ───────────────────────────
    # --- CONFIGURACIÓN GITHUB ---
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "locales.csv"
    
    st.set_page_config(page_title="NEXION SMART LOGISTICS", layout="wide")
    
    # --- ESTILO NEXION (FUERZA BRUTA TOTAL) ---
    st.markdown("""
        <style>
        /* 1. Fondo y Base */
        .main { background-color: #0B1114; color: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
        
        /* 2. Header */
        .header-container { display: flex; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #1A2226; padding-bottom: 10px; }
        .header-logo { width: 180px; margin-right: 20px; }
        h1 { color: #FFFFFF; font-size: 1.4rem; letter-spacing: 1px; margin: 0; }
        h3 { color: #FFFFFF; text-transform: uppercase; letter-spacing: 1px; font-size: 0.95rem; padding-bottom: 5px; margin-top: 20px; border-bottom: 1px solid #1A2226; }
        
        /* 3. EL HACK DEFINITIVO PARA BOTONES ANCHOS */
        /* Forzamos al contenedor del botón a ocupar todo el espacio */
        div.stButton {
            width: 100%;
            display: block;
        }
        
        /* Forzamos al botón mismo */
        div.stButton > button {
            width: 100% !important;
            background-color: #00FFAA !important;
            color: #0B1114 !important;
            font-weight: bold !important;
            border-radius: 4px !important;
            border: none !important;
            height: 2.5em !important;
            text-transform: uppercase !important;
            font-size: 1.1rem !important;
            letter-spacing: 2px !important;
            margin-top: 15px !important;
            margin-bottom: 15px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
    
        div.stButton > button:hover {
            background-color: #00D18B !important;
            color: #FFFFFF !important;
            box-shadow: 0px 0px 15px rgba(0, 255, 170, 0.4);
        }
    
        /* 4. Estilos de Inputs y Selectores */
        .stSelectbox label, .stMultiSelect label, .stTextInput label { color: #FFFFFF !important; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
        div[data-baseweb="select"] { background-color: #1A2226; border: 1px solid #333; border-radius: 4px; }
        .stAlert { background-color: #1A2226; color: #00FFAA; border: 1px solid #00FFAA; border-radius: 4px; }
        hr { border: 0.5px solid #1A2226; }
        
        /* Quitar padding extra de Streamlit */
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
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
            df.columns = df.columns.str.upper().str.strip()
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
        st.markdown(f'<div class="header-container"><img src="data:image/png;base64,{logo_b64}" class="header-logo"><h1>NEXION SMART LOGISTICS</h1></div>', unsafe_allow_html=True)
    else:
        st.title("NEXION SMART LOGISTICS")
    
    # --- DATA ---
    df, sha = descargar_matriz()
    
    if df is not None:
        def obtener_valor(fila, posibles_nombres):
            for nombre in posibles_nombres:
                if nombre in fila.index:
                    return fila[nombre]
            return "N/D"
    
        # --- CARGA ---
        st.markdown("<h3>1. SALIDA DE ALMACEN (CARGA)</h3>", unsafe_allow_html=True)
        col_trigger = next((c for c in ['TRIGGER', 'ESTADO'] if c in df.columns), 'TRIGGER')
        col_pedido = next((c for c in ['NÚMERO DE PEDIDO', 'FOLIO', 'PEDIDO'] if c in df.columns), 'NÚMERO DE PEDIDO')
        
        disponibles = df[~df[col_trigger].isin(['EN RUTA', 'ENTREGADO'])]
        if not disponibles.empty:
            pedidos_sel = st.multiselect("SELECCIONAR FOLIOS:", options=disponibles[col_pedido].unique(), key="ms_carga")
            if pedidos_sel:
                ref_k = str(pedidos_sel[0])
                f1 = st.camera_input("FOTO 1: PRODUCTO", key=f"c1_{ref_k}")
                if f1:
                    f2 = st.camera_input("FOTO 2: UNIDAD", key=f"c2_{ref_k}")
                    if f2:
                        f3 = st.camera_input("FOTO 3: ESTIBA", key=f"c3_{ref_k}")
                        if f3:
                            # BOTÓN ANCHO
                            if st.button("CONFIRMAR SALIDA DE UNIDAD", use_container_width=True):
                                with st.spinner("PROCESANDO..."):
                                    ahora_c = datetime.now().strftime('%Y-%m-%d %H:%M')
                                    for p in pedidos_sel:
                                        idx = df[df[col_pedido] == str(p)].index
                                        df.loc[idx, col_trigger] = 'EN RUTA'
                                        df.loc[idx, 'FECHA DE ENVÍO'] = ahora_c
                                    if actualizar_github(df, sha, f"Carga: {pedidos_sel}"):
                                        st.rerun()
        else:
            st.info("NO HAY PENDIENTES EN ALMACEN")
    
        st.markdown("<br><hr>", unsafe_allow_html=True)
    
        # --- ENTREGA ---
        st.markdown("<h3>2. ENTREGA EN DESTINO</h3>", unsafe_allow_html=True)
        en_ruta = df[df[col_trigger] == 'EN RUTA']
        
        if not en_ruta.empty:
            opciones = en_ruta.apply(lambda x: f"{x[col_pedido]} | {obtener_valor(x, ['NOMBRE DEL CLIENTE', 'CLIENTE'])}", axis=1)
            sel = st.selectbox("PEDIDO A ENTREGAR:", opciones)
            id_p = sel.split(" | ")[0].strip()
            dat = en_ruta[en_ruta[col_pedido] == id_p].iloc[0]
            
            st.markdown(f"""
                <div style="background-color: #1A2226; padding: 15px; border-radius: 4px; border-left: 4px solid #00FFAA; margin-bottom: 20px;">
                    <p style="margin:0; font-size: 0.7rem; color: #00FFAA; font-weight: bold;">DESTINO:</p>
                    <p style="margin:0; font-size: 1rem; font-weight: bold;">{obtener_valor(dat, ['DESTINO', 'HOTEL'])}</p>
                    <p style="margin:10px 0 0 0; font-size: 0.7rem; color: #00FFAA; font-weight: bold;">DOMICILIO:</p>
                    <p style="margin:0; font-size: 0.85rem;">{obtener_valor(dat, ['DOMICILIO', 'DIRECCION'])}</p>
                </div>
            """, unsafe_allow_html=True)
            
            f_ent = st.camera_input("EVIDENCIA FINAL", key=f"ce_{id_p}")
            obs = st.text_input("OBSERVACIONES:", key=f"obs_{id_p}")
    
            # BOTÓN ANCHO
            if st.button("FINALIZAR ENTREGA", use_container_width=True):
                if f_ent:
                    with st.spinner("GUARDANDO..."):
                        ahora_e = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        idx_f = df[(df[col_pedido] == id_p) & (df[col_trigger] == 'EN RUTA')].index
                        if not idx_f.empty:
                            df.loc[idx_f[0], 'FECHA DE ENTREGA REAL'] = ahora_e
                            df.loc[idx_f[0], col_trigger] = 'ENTREGADO'
                            df.loc[idx_f[0], 'INCIDENCIAS'] = obs
                            if actualizar_github(df, sha, f"Entrega: {id_p}"):
                                st.rerun()
                else:
                    st.error("EVIDENCIA FOTOGRAFICA REQUERIDA")
        else:
            st.info("NO HAY PEDIDOS EN RUTA ACTUALMENTE")
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
