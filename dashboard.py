import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
import plotly.graph_objects as go
import plotly.express as px
import time
from github import Github
import json
import pytz
import zipfile
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re
import unicodedata
import io
import altair as alt
from datetime import date, datetime, timedelta
from io import BytesIO

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

# ── LOGIN ──────────────────────────
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

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
    background-color: #57737F !important; 
    color: #ffffff !important; 
    border-color: #57737F !important; 
}}



/* 5. INPUTS - SOLUCIÓN DEFINITIVA PARA BORDES CORTADOS */

/* Atacamos al contenedor que envuelve el input */
div[data-baseweb="input"] {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
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
    height: 45px !important; 
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

    height: 32px !important;
    min-height: 32px !important;
    padding: 0 12px !important;
    font-size: 11px !important;
    line-height: 30px !important;
}}


</style>
""", unsafe_allow_html=True)


# ── DEFINICIÓN DE INTERFAZ DE LOGIN ────────────────────
def login_screen():
    # Ajustamos las proporciones a [3, 2, 3] para que la columna central sea más angosta
    _, col, _ = st.columns([2, 2, 2]) 
    
    with col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Usamos una clase personalizada para asegurar que el texto se vea bien en el centro
        st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>SYSTEM ACCESS REQUIRED</h3>", unsafe_allow_html=True)
        
        with st.container():
            user_input = st.text_input("OPERATOR ID", placeholder="Introduce tu usuario")
            pass_input = st.text_input("ACCESS KEY", type="password", placeholder="••••••••")
            
            # Espacio extra antes del botón
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            if st.button("VERIFY IDENTITY"):
                lista_usuarios = st.secrets.get("usuarios", {})
                
                if user_input in lista_usuarios and str(lista_usuarios[user_input]) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = user_input
                    
                    # REDIRECCIÓN ESPECÍFICA
                    if user_input == "JMoreno":
                        st.session_state.menu_main = "FORMATOS"
                        st.session_state.menu_sub = "SALIDA DE PT"
                    else:
                        # Forzamos que cualquier otro usuario entre a DASHBOARD
                        st.session_state.menu_main = "DASHBOARD"
                        st.session_state.menu_sub = "GENERAL"
                    
                    st.success(f"BIENVENIDO!, {user_input.upper()}")
                    time.sleep(1) 
                    st.rerun()
# ── FLUJO DE CONTROL (SPLASH -> LOGIN -> APP) ──────────

# 1. ¿Falta mostrar el Splash?
if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:60px;height:60px;border:2px solid {vars_css['border']}; border-top:2px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.13)
    st.session_state.splash_completado = True
    st.rerun()

# 2. ¿Splash listo pero no se ha loggeado?
elif not st.session_state.autenticado:
    login_screen()

# 3. ¿Todo listo? Mostrar NEXION CORE
else:
    # ── HEADER REESTRUCTURADO (CENTRADITO Y BALANCEADO) ──────────────────────────
    header_zone = st.container()
    with header_zone:
        # Usamos proporciones que den espacio suficiente a los lados para que el centro sea real
        c1, c2, c3 = st.columns([1.5, 4, 1.5], vertical_alignment="center")
        
        with c1:
            try:
                # Solo mostramos el logo con el ancho que definiste
                st.image(vars_css["logo"], width=180)
            except:
                # Si falla la carga de la imagen, no mostramos nada (o podrías dejar un pass)
                pass
    
        with c2:
            # INDICADOR GENERAL (CENTRADO ABSOLUTO CON ESPACIADO NEXION)
            if st.session_state.menu_sub != "GENERAL":
                # Agregamos espacios manuales solo al separador "|" para que no se pegue a las letras
                ruta = f"{st.session_state.menu_main} <span style='color:{vars_css['sub']}; opacity:0.4; margin: 0 15px;'>|</span> {st.session_state.menu_sub}"
            else:
                ruta = st.session_state.menu_main
            
            st.markdown(f"""
                <div style='display: flex; justify-content: center; align-items: center; width: 100%; margin: 20px 0;'>
                    <p style='font-size: 13px; 
                              letter-spacing: 8px;  /* ← Aumentado para efecto de doble espacio */
                              color: {vars_css['sub']}; 
                              margin: 0; 
                              font-weight: 500; 
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
                    
                    # Identificamos quién está operando
                    usuario = st.session_state.get("usuario_activo", "")

                    # --- SECCIONES RESTRINGIDAS (J Moreno NO las ve) ---
                    if usuario != "JMoreno":
                        # DASHBOARD
                        if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                            st.session_state.menu_main = "DASHBOARD"
                            st.session_state.menu_sub = "GENERAL"
                            st.rerun()
                        
                        # SEGUIMIENTO
                        with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                            for s in ["TRK", "GANTT", "QUEJAS"]:
                                sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                                if st.button(sub_label, use_container_width=True, key=f"pop_sub_{s}"):
                                    st.session_state.menu_main = "SEGUIMIENTO"
                                    st.session_state.menu_sub = s
                                    st.rerun()

                        # REPORTES
                        with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                            for s in ["APQ", "OPS", "OTD"]:
                                sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                                if st.button(sub_label, use_container_width=True, key=f"pop_rep_{s}"):
                                    st.session_state.menu_main = "REPORTES"
                                    st.session_state.menu_sub = s
                                    st.rerun()

                    # --- SECCIÓN FORMATOS (Visible para todos, pero con opciones filtradas) ---
                    with st.expander("FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")):
                        # Definimos qué formatos ve cada uno
                        if usuario == "JMoreno":
                            formatos_visibles = ["SALIDA DE PT"]
                        else:
                            formatos_visibles = ["SALIDA DE PT", "CONTRARRECIBOS"]

                        for s in formatos_visibles:
                            sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                            if st.button(sub_label, use_container_width=True, key=f"pop_for_{s}"):
                                st.session_state.menu_main = "FORMATOS"
                                st.session_state.menu_sub = s
                                st.rerun()

                    # --- SECCIÓN HUB LOG (J Moreno NO la ve) ---
                    if usuario != "JMoreno":
                        with st.expander("HUB LOG", expanded=(st.session_state.menu_main == "HUB LOG")):
                            for s in ["SMART ROUTING", "DATA MANAGEMENT", "ORDER STAGING"]:
                                sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                                if st.button(sub_label, use_container_width=True, key=f"pop_hub_{s}"):
                                    st.session_state.menu_main = "HUB LOG"
                                    st.session_state.menu_sub = s
                                    st.rerun()
                    
    
    st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px; opacity:0.2;'>", unsafe_allow_html=True)
    
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
                .stat-bg {{ stroke: #22282E; }}
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
                tab_kpis, tab_rastreo, tab_volumen, tab_participacion = st.tabs([
                    "KPI´S", "RASTREO", "VOLUMEN", "DIST. CARGA"
                ])
    
                # PESTAÑA 1: KPI'S (Tus donitas)
                with tab_kpis:
                    st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns(5)
                    with c1: render_kpi(total_p, total_p, "Pedidos", "#ffffff")
                    with c2: render_kpi(entregados, total_p, "Entregados", "#00FFAA")
                    with c3: render_kpi(total_t, total_p, "Tránsito", "#38bdf8")
                    with c4: render_kpi(en_tiempo, total_p, "En Tiempo", "#a855f7")
                    with c5: render_kpi(retrasados, total_p, "Retraso", "#ff4b4b")
                
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    with st.expander("DETALLE OPERATIVO"):
                        st.dataframe(
                            df_mes.sort_values("FECHA DE ENVÍO", ascending=False),
                            use_container_width=True,
                            hide_index=True
                        )
    
                # PESTAÑA 2: RASTREO (Donde pondremos el buscador tipo DHL)
                with tab_rastreo:
                    st.markdown('<div class="spacer-m3"></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="op-query-text">CONSULTA DE ESTATUS LOGÍSTICO</div>', unsafe_allow_html=True)
                
                    # COLUMNAS PARA CENTRAR LA BÚSQUEDA
                    col_space1, col_search, col_space2 = st.columns([1, 2, 1])
                    
                    with col_search:
                        busqueda_manual = st.text_input("", key="busqueda_clean", placeholder="Ingrese numero de guia o factura...").strip()
                
                    # LÓGICA DE AUTO-RELLENO: Si no hay búsqueda, usamos el primer registro del mes actual
                    if not busqueda_manual:
                        hoy_ref = pd.Timestamp(datetime.now())
                        # Filtramos por el mes actual (Febrero) para mostrar algo de inicio
                        df_mes = df_raw[pd.to_datetime(df_raw["FECHA DE ENVÍO"], dayfirst=True).dt.month == hoy_ref.month]
                        busqueda = str(df_mes.iloc[0]["NÚMERO DE PEDIDO"]) if not df_mes.empty else None
                    else:
                        busqueda = busqueda_manual

                    if busqueda:
                        resultado = df_raw[(df_raw["NÚMERO DE PEDIDO"].astype(str).str.contains(busqueda, case=False)) | (df_raw["NÚMERO DE GUÍA"].astype(str).str.contains(busqueda, case=False))]
                
                        if not resultado.empty:
                            envio = resultado.iloc[0]
                            f_envio = envio["FECHA DE ENVÍO"]
                            f_promesa = envio["PROMESA DE ENTREGA"]
                            entregado_real = pd.notna(envio["FECHA DE ENTREGA REAL"])
                            f_entrega_val = envio["FECHA DE ENTREGA REAL"] if entregado_real else "PENDIENTE"
                            tiene_guia = pd.notna(envio["NÚMERO DE GUÍA"]) and str(envio["NÚMERO DE GUÍA"]).strip() not in ["", "0", "nan"]
                            n_guia = envio["NÚMERO DE GUÍA"] if tiene_guia else "GENERANDO GUÍA..."
                            
                            color_envio = "#38bdf8"
                            color_guia = "#38bdf8" if tiene_guia else vars_css['border']
                            color_promesa = "#a855f7" if tiene_guia else vars_css['border']
                            linea_1_2 = "#38bdf8" if tiene_guia else vars_css['border']
                            linea_2_3 = "#a855f7" if tiene_guia else vars_css['border']
                            linea_3_4 = "#00FFAA" if entregado_real else vars_css['border']

                            f_promesa_dt = pd.to_datetime(envio["PROMESA DE ENTREGA"], dayfirst=True)
                            hoy = pd.Timestamp(datetime.now())

                            if not tiene_guia:
                                status_text, status_color = ("GENERANDO GUÍA", vars_css['sub'])
                                color_entrega = vars_css['border']
                            elif not entregado_real:
                                status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
                                color_entrega = status_color
                                linea_3_4 = status_color 
                            else:
                                status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.to_datetime(envio["FECHA DE ENTREGA REAL"], dayfirst=True) <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")
                                color_entrega = status_color

                            # RENDER EN UNA SOLA LÍNEA (TODO IGUALITO)
                            timeline_html = f'<div style="background: {vars_css["card"]}; padding: 30px; border-radius: 4px; border: 1px solid {vars_css["border"]}; margin-top: 10px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;"><h2 style="margin:0; color:{vars_css["text"]}; font-size:14px; letter-spacing:2px; text-transform:uppercase; font-weight:800;">{envio["NOMBRE DEL CLIENTE"]}</h2><span style="background:{status_color}15; color:{status_color}; padding: 4px 12px; border-radius: 2px; font-weight:700; font-size:10px; border: 1px solid {status_color}; letter-spacing:1px;">{status_text}</span></div><div style="display: flex; align-items: center; width: 100%; position: relative; padding: 0 10px;"><div style="display: flex; flex-direction: column; align-items: center; min-width: 80px;"><div style="width:12px; height:12px; background:{color_envio}; border-radius:50%;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">ENVÍO</div><div style="font-size:10px; color:white; font-weight:400;">{f_envio}</div></div><div style="flex-grow: 1; height: 2px; background: {linea_1_2}; margin-bottom: 35px;"></div><div style="display: flex; flex-direction: column; align-items: center; min-width: 80px;"><div style="width:12px; height:12px; background:{color_guia}; border-radius:50%;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">GUÍA</div><div style="font-size:10px; color:white; font-weight:400;">{"LISTA" if tiene_guia else "PENDIENTE"}</div></div><div style="flex-grow: 1; height: 2px; background: {linea_2_3}; margin-bottom: 35px;"></div><div style="display: flex; flex-direction: column; align-items: center; min-width: 80px;"><div style="width:12px; height:12px; background:{color_promesa}; border-radius:50%;"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:10px; font-weight:700;">PROMESA</div><div style="font-size:10px; color:white; font-weight:400;">{f_promesa}</div></div><div style="flex-grow: 1; height: 2px; background: {linea_3_4}; margin-bottom: 35px;"></div><div style="display: flex; flex-direction: column; align-items: center; min-width: 80px;"><div style="width:16px; height:16px; background:{color_entrega}; border-radius:50%; box-shadow: {"0 0 10px "+color_entrega+"44" if entregado_real else "none"};"></div><div style="font-size:9px; color:{vars_css["sub"]}; margin-top:8px; font-weight:700;">ENTREGA</div><div style="font-size:10px; color:white; font-weight:400;">{f_entrega_val}</div></div></div><div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 35px; border-top: 1px solid {vars_css["border"]}; padding-top: 20px;"><div style="text-align:left;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">FLETERA</div><div style="color:white; font-size:12px;">{envio["FLETERA"]}</div></div><div style="text-align:left;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">GUÍA</div><div style="color:white; font-size:12px;">{n_guia}</div></div><div style="text-align:left;"><div style="color:{vars_css["sub"]}; font-size:10px; font-weight:700; letter-spacing:1px;">DESTINO</div><div style="color:white; font-size:12px;">{envio["DESTINO"]}</div></div></div></div>'
                            
                            st.markdown(timeline_html, unsafe_allow_html=True)
                        else:
                            st.warning("No se encontró información para esa guía o factura.")
                    
                # PESTAÑA 3: VOLUMEN
                with tab_volumen:
                    st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)
                    st.write("Visualización de Volumen de Carga")
                    
                # PESTAÑA 4: % PARTICIPACIÓN
                with tab_participacion: # Asegúrate que arriba definiste: tab_kpis, tab_rastreo, tab_volumen, tab_participacion = st.tabs([...])
                                        
                    URL_LOGISTICA = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Costo_Logistico_Mensual.csv"
                    
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
                        df_log_filtrado = df_log[df_log["MES"] == mes_sel].copy()

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
                            
                            # --- 4. GRÁFICO DE BARRAS ---
                            fig_bar = px.bar(
                                df_part, x='PORCENTAJE', y='TRANSPORTE', orientation='h',
                                text=df_part['PORCENTAJE'].apply(lambda x: f'{x:.1f}%'),
                                template="plotly_dark", color='PORCENTAJE',
                                color_continuous_scale=['#1a2432', '#00FFAA']
                            )
                            fig_bar.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                xaxis_range=[0, df_part['PORCENTAJE'].max() * 1.2],
                                font=dict(family="Inter", size=11, color="#FFFFFF"),
                                margin=dict(l=20, r=20, t=10, b=10), showlegend=False
                            )
                            # Añadimos key única
                            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False}, key=f"bar_part_{mes_sel}")
    
                            # --- 5. TABLA DE AUDITORÍA ---
                            st.markdown("<p class='op-query-text' style='font-size:10px;'>AUDITORÍA DE DISTRIBUCIÓN LOGÍSTICA</p>", unsafe_allow_html=True)
                            df_tabla = df_part.sort_values(by='PORCENTAJE', ascending=False)
                            
                            st.dataframe(
                                df_tabla,
                                column_config={
                                    "TRANSPORTE": "CARRIER ID",
                                    "CAJAS": st.column_config.NumberColumn("TOTAL UNITS", format="%d"),
                                    "PORCENTAJE": st.column_config.NumberColumn("SHARE VALUE", format="%.2f%%")
                                },
                                use_container_width=True,
                                hide_index=True,
                                key=f"tabla_audit_{mes_sel}" # Key única
                            )

                            # --- 6. EXPANDER: DESGLOSE POR DESTINO CON MULTI-FILTRO ---
                            st.markdown("<br>", unsafe_allow_html=True)
                            with st.expander("🌐 EXPLORADOR DE RUTAS Y DESTINOS"):
                                # Filtro MULTIPLE por Carrier
                                lista_carriers = sorted(df_log_filtrado['TRANSPORTE'].unique())
                                carriers_seleccionados = st.multiselect(
                                    "Filtrar por uno o varios Carriers:", 
                                    options=lista_carriers,
                                    default=None,
                                    placeholder="Selecciona paqueterías para comparar...",
                                    key=f"multi_carrier_{mes_sel}" # Key única
                                )
                                
                                # Aplicar filtro dinámico
                                if carriers_seleccionados:
                                    df_dest_filtered = df_log_filtrado[df_log_filtrado['TRANSPORTE'].isin(carriers_seleccionados)].copy()
                                else:
                                    df_dest_filtered = df_log_filtrado.copy()
                                
                                # Agrupación para la tabla de rutas
                                df_dest_sum = df_dest_filtered.groupby(['TRANSPORTE', 'DESTINO'])['CAJAS'].sum().reset_index()
                                df_dest_sum = df_dest_sum.sort_values(by=['TRANSPORTE', 'CAJAS'], ascending=[True, False])
                                
                                # Métrica rápida de lo seleccionado
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
                                    key=f"tabla_destinos_{mes_sel}" # Key única
                                )

                        else:
                            meses_disponibles = df_log['MES'].unique()
                            st.warning(f"No hay datos para {mes_sel}. ")
                            st.info(f"Meses detectados en el sistema: {list(meses_disponibles)}")

        
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
            if st.session_state.menu_sub == "TRK":
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
                    with st.expander("Filtrar y analizar detalle de retrasos", expanded=False):
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
                            "NOMBRE DEL CLIENTE": ["NOMBRE DEL CLIENTE", "CLIENTE"],
                            "DESTINO": ["DESTINO", "CIUDAD"],
                            "FECHA DE ENVÍO": ["FECHA DE ENVÍO"],
                            "PROMESA DE ENTREGA": ["PROMESA DE ENTREGA"],
                            "FLETERA": ["FLETERA"],
                            "NÚMERO DE GUÍA": ["NÚMERO DE GUÍA", "GUÍA"],
                            "DIAS_TRANS": ["DIAS_TRANS"],
                            "DIAS_ATRASO": ["DIAS_ATRASO"]
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
                        "FECHA","FECHA_FIN","IMPORTANCIA","TAREA","ULTIMO ACCION",
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
                    
                        /* --- ESTILO PARA EL SCROLL DARK --- */
                        ::-webkit-scrollbar {{
                            width: 10px;
                            height: 10px;
                        }}
                        ::-webkit-scrollbar-track {{
                            background: #111827; /* Fondo del scroll igual al body */
                        }}
                        ::-webkit-scrollbar-thumb {{
                            background: #374151; /* Color de la barrita */
                            border-radius: 5px;
                        }}
                        ::-webkit-scrollbar-thumb:hover {{
                            background: #4b5563; /* Color cuando pasas el mouse */
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
                
                # ── 3. DATA EDITOR (DENTRO DE EXPANDER) ───────────────────────────────────────────────
                with st.expander(":material/edit_note: Abrir editor de tareas", expanded=False):
                    st.subheader("EDITOR DE TAREAS")
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
                
                if st.button("SINCRONIZAR CON GITHUB", use_container_width=True):
                    df_guardar = df_editado.drop(columns=["PROGRESO_VIEW"], errors="ignore")
                    if guardar_en_github(df_guardar):
                        st.session_state.df_tareas = df_guardar
                        st.rerun()
    
    
    
            
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
    
            elif st.session_state.menu_sub == "OPS":
                st.subheader("Eficiencia Operativa (OPS)")
                # --- 1. MOTOR DE DATOS NIVEL ELITE ---
                # --- 1. MOTOR DE DATOS ---
                @st.cache_data
                def cargar_datos_maestros():
                    url = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/analisis2026.csv"
                    try:
                        df = pd.read_csv(url, encoding="latin-1", sep=None, engine='python')
                        df.columns = [str(c).strip().upper() for c in df.columns]
                        
                        def fcol(k): 
                            exacta = next((c for c in df.columns if k == c), None)
                            return exacta if exacta else next((c for c in df.columns if k in c), None)
                
                        mapeo = {
                            'MES': fcol('MES'), 'FLETE': fcol('COSTO DE FLETE'), 
                            'FACT': fcol('FACTURACIÓN') or fcol('FACTURACI'),
                            'CAJAS': fcol('CAJAS ENVIADAS'), 'LOGI': fcol('COSTO LOGÍSTICO') or fcol('LOGI'), 
                            'META': fcol('META INDICADOR') or fcol('META'),
                            'CC26': fcol('COSTO POR CAJA') if fcol('COSTO POR CAJA') and '2024' not in fcol('COSTO POR CAJA') else None,
                            'VAL_INC': fcol('VALUACION'), 'POR_INC': fcol('PORCENTAJE DE INCIDENCIAS') or fcol('% DE INC'),
                            'INCR': fcol('INCREMENTO + VI') or fcol('INCREMENTO'), 
                            'VS24': fcol('% DE INCREMENTO'), 'CC24': fcol('COSTO POR CAJA 2025') or fcol('2024')
                        }
                
                        df = df.dropna(subset=[mapeo['MES']])
                        df = df[df[mapeo['MES']].astype(str).str.contains('Unnamed|TOTAL', case=False) == False]
                        
                        def clean(v):
                            if pd.isna(v) or v == '': return 0.0
                            s = str(v).replace('$', '').replace(',', '').replace('%', '').replace('(', '-').replace(')', '').strip()
                            try: return float(s)
                            except: return 0.0
                
                        df_std = pd.DataFrame()
                        df_std['MES'] = df[mapeo['MES']]
                        for key, orig in mapeo.items():
                            if key != 'MES':
                                df_std[key] = df[orig].apply(clean) if orig else 0.0
                        return df_std
                    except Exception as e:
                        st.error(f"Error cargando datos: {e}")
                        return None
                
                # --- 2. CSS DISEÑO (SIN ICONOS, SIN FONDOS, SIN BORDES LATERALES) ---
                st.markdown("""
                    <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
                    
                    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #050505; color: white; }
                    
                    .main-title { font-weight: 900; font-size: 2.5rem; letter-spacing: -1.5px; color: #fff; margin-bottom: 0px; }
                    .sub-title { color: #888; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 25px; }
                
                    /* Tarjetas Superiores */
                    .metric-card {
                        background: rgba(255, 255, 255, 0.03);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        padding: 22px;
                        border-radius: 12px;
                        margin-bottom: 15px;
                        min-height: 150px;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                    }
                    .label { color: #BBB; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; }
                    .value { color: #fff; font-size: 2.1rem; font-weight: 700; margin: 8px 0; }
                    .meta-ind { font-size: 0.75rem; color: #888; font-weight: 600; text-transform: uppercase; }
                
                    /* Bloques de Análisis (LIMPIOS: SIN FONDO, SIN BORDE LATERAL) */
                    .section-box {
                        background: transparent;
                        border-radius: 12px;
                        padding: 25px;
                        margin-top: 20px;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }
                    
                    .section-title { font-size: 1rem; margin-top: 0; margin-bottom: 15px; font-weight: 700; text-transform: uppercase; }
                    </style>
                """, unsafe_allow_html=True)
                
                # --- 3. LÓGICA Y RENDER ---
                df_a = cargar_datos_maestros()
                
                if df_a is not None:
                    st.markdown("<div class='main-title'></div>", unsafe_allow_html=True)
                    col_sel, _ = st.columns([1, 3])
                    with col_sel:
                        mes_sel = st.selectbox("", df_a["MES"].unique(), label_visibility="collapsed")
                    
                    st.markdown(f"<div class='sub-title'>DATA RADIOGRAPHY // PERIODO: {mes_sel}</div>", unsafe_allow_html=True)
                
                    df_m = df_a[df_a["MES"] == mes_sel].iloc[0]
                
                    # --- GRID 9 TARJETAS ---
                    c1, c2, c3 = st.columns(3)
                    eficiencia = df_m['META'] - df_m['LOGI']
                    col_log = "#10b981" if eficiencia >= 0 else "#fb7185"
                    
                    with c1:
                        st.markdown(f"<div class='metric-card'><div class='label'>Costo Logístico</div><div class='value' style='color:{col_log}'>{df_m['LOGI']:.2f}%</div><div class='meta-ind'>Meta Indicador: {df_m['META']}%</div></div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"<div class='metric-card'><div class='label'>Incremento + VI</div><div class='value'>${df_m['INCR']:,.0f}</div><div class='meta-ind'>Impacto Financiero Real</div></div>", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"<div class='metric-card'><div class='label'>% Incr vs 2024</div><div class='value' style='color:#f472b6'>{df_m['VS24']:.1f}%</div><div class='meta-ind'>Variación vs Anterior</div></div>", unsafe_allow_html=True)
                
                    c4, c5, c6 = st.columns(3)
                    with c4:
                        # Ajuste: Texto "Target 2026" y valor fijo "$59.00"
                        st.markdown(f"<div class='metric-card'><div class='label'>Costo por Caja</div><div class='value'>${df_m['CC26']:.2f}</div><div class='meta-ind'>Target 2026: $59.00</div></div>", unsafe_allow_html=True)
                    with c5:
                        st.markdown(f"<div class='metric-card'><div class='label'>Valuación Incidencias</div><div class='value' style='color:#eab308'>${df_m['VAL_INC']:,.0f}</div><div class='meta-ind'>Pérdida Estimada Operativa</div></div>", unsafe_allow_html=True)
                    with c6:
                        st.markdown(f"<div class='metric-card'><div class='label'>% de Incidencias</div><div class='value'>{df_m['POR_INC']:.2f}%</div><div class='meta-ind'>Calidad en Procesos</div></div>", unsafe_allow_html=True)
                
                    c7, c8, c9 = st.columns(3)
                    with c7:
                        st.markdown(f"<div class='metric-card'><div class='label'>Facturación</div><div class='value'>${df_m['FACT']:,.0f}</div><div class='meta-ind'>Ingreso Bruto Mensual</div></div>", unsafe_allow_html=True)
                    with c8:
                        st.markdown(f"<div class='metric-card'><div class='label'>Cajas Enviadas</div><div class='value'>{int(df_m['CAJAS']):,.0f}</div><div class='meta-ind'>Volumen de Despacho</div></div>", unsafe_allow_html=True)
                    with c9:
                        st.markdown(f"<div class='metric-card'><div class='label'>Costo de Flete</div><div class='value'>${df_m['FLETE']:,.0f}</div><div class='meta-ind'>Inversión Logística Directa</div></div>", unsafe_allow_html=True)
                
                    # --- BLOQUES DE ANÁLISIS ---
                    st.markdown(f"""
                    <div class='section-box'>
                        <div class='section-title' style='color:#10b981;'>Metodología de Cálculo para {mes_sel}:</div>
                        <p style='color:#E0E0E0; font-size:0.95rem; font-family:monospace;'>
                        • <b>Logístico:</b> (${df_m['FLETE']:,.2f} / ${df_m['FACT']:,.2f}) = <b>{df_m['LOGI']:.2f}%</b><br>
                        • <b>C/Caja:</b> ${df_m['FLETE']:,.2f} / {int(df_m['CAJAS'])} cajas = <b>${df_m['CC26']:.2f}</b><br>
                        • <b>Impacto:</b> (Ahorro Incidencias) - (Variación Tarifaria vs 2024 * Cajas) = <b>${df_m['INCR']:,.2f}</b>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                    col_inf1, col_inf2 = st.columns(2)
                    with col_inf1:
                        st.markdown(f"""<div class='section-box'>
                            <div class='section-title' style='color:#38bdf8;'>DEEP DIVE</div>
                            <p style='color:#CCC; font-size:0.9rem;'>
                            Durante el mes de <b>{mes_sel}</b>, la operación gestionó un flujo de <b>{int(df_m['CAJAS']):,.0f}</b> paquetes. 
                            El rendimiento financiero muestra una facturación de <b>${df_m['FACT']:,.2f}</b> con un costo unitario por caja de <b>${df_m['CC26']:.2f}</b>.
                            </p>
                        </div>""", unsafe_allow_html=True)
                
                    with col_inf2:
                        estatus = "EFICIENCIA" if eficiencia >= 0 else "DESVIACIÓN"
                        st.markdown(f"""<div class='section-box'>
                            <div class='section-title' style='color:#f472b6;'>RADIOGRAFÍA</div>
                            <p style='color:#CCC; font-size:0.9rem;'>
                            Estado: <b style='color:#fff;'>{estatus} OPERATIVA</b><br>
                            La desviación respecto a la meta es de <b>{abs(eficiencia):.2f}%</b>. <br>
                            Cada $1,000 MXN facturados están consumiendo <b>${(df_m['LOGI']/100)*1000:.2f}</b> de presupuesto logístico.
                            </p>
                        </div>""", unsafe_allow_html=True)
                
                    # Botón de Descarga PDF al final
                    # --- TABLA DE DATOS FINAL (CON NOMBRES REALES Y CONTRAÍDA) ---
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("Ver dataset completo", expanded=False):
                        # Creamos una copia para no afectar la lógica de los cálculos superiores
                        df_visual = df_a.copy()
                        
                        # Renombramos las columnas a los nombres reales solicitados
                        df_visual = df_visual.rename(columns={
                            'MES': 'MES',
                            'FLETE': 'COSTO DE FLETE',
                            'FACT': 'FACTURACIÓN',
                            'CAJAS': 'CAJAS ENVIADAS',
                            'LOGI': 'COSTO LOGISTICO',
                            'CC26': 'COSTO POR CAJA',
                            'META': 'META INDICADOR',
                            'VAL_INC': 'VALUACION INCIDENCIAS',
                            'POR_INC': '% DE INCIDENCIAS',
                            'INCR': 'INCREMENTO + VI',
                            'VS24': '% DE INCREMENTO VS 2025',
                            'CC24': 'COSTO POR CAJA 2025'
                        })
                        
                        # Mostramos la tabla con un estilo limpio
                        st.dataframe(
                            df_visual, 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={
                                "COSTO DE FLETE": st.column_config.NumberColumn(format="$%.2f"),
                                "FACTURACIÓN": st.column_config.NumberColumn(format="$%.2f"),
                                "COSTO LOGISTICO": st.column_config.NumberColumn(format="%.2f%%"),
                                "COSTO POR CAJA": st.column_config.NumberColumn(format="$%.2f"),
                                "INCREMENTO + VI": st.column_config.NumberColumn(format="$%.2f"),
                                "% DE INCREMENTO VS 2025": st.column_config.NumberColumn(format="%.2f%%")
                            }
                        )
                                
                # --- LÓGICA DEL REPORTE PARA IMPRESIÓN ---        
                def generar_reporte_impresion(df_m, mes_sel):
                    estatus_rep = "DENTRO DE PARÁMETROS" if (df_m['META'] - df_m['LOGI']) >= 0 else "FUERA DE PARÁMETROS"
                    
                    # Cálculo para la barra de progreso (invertido porque menor logístico es mejor)
                    pct_cumplimiento = max(0, min(100, (df_m['META'] / df_m['LOGI']) * 100)) if df_m['LOGI'] > 0 else 0
                
                    html_content = f"""
                    <div id="printable-report" style="font-family: Arial, sans-serif; padding: 40px; color: #000; background: #fff; max-width: 800px; margin: auto; border: 1px solid #eee;">
                        
                        <table style="width: 100%; border-bottom: 4px solid #000; margin-bottom: 20px;">
                            <tr>
                                <td style="width: 50%;">
                                    <h1 style="margin: 0; font-size: 28px; font-weight: 900; letter-spacing: -1px;">JYPESA</h1>
                                    <p style="margin: 0; font-size: 11px; font-weight: bold; text-transform: uppercase;">División de Ingeniería Logística | 2026</p>
                                </td>
                                <td style="width: 50%; text-align: right; font-size: 11px;">
                                    <b>REPORTE ID:</b> LOG-{mes_sel[:3].upper()}-2026<br>
                                    <b>FECHA:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
                                    <span style="border: 1px solid #000; padding: 2px 5px; display: inline-block; margin-top: 5px; font-weight: bold;">{estatus_rep}</span>
                                </td>
                            </tr>
                        </table>
                
                        <h2 style="text-align: center; text-transform: uppercase; margin-bottom: 30px; font-size: 18px; text-decoration: underline;">Análisis Operativo Mensual: {mes_sel}</h2>
                
                        <div style="margin-bottom: 40px;">
                            <p style="font-size: 12px; font-weight: bold; margin-bottom: 10px;">RENDIMIENTO VS META (COSTO LOGÍSTICO):</p>
                            <div style="width: 100%; border: 2px solid #000; height: 30px; position: relative; background: #f0f0f0;">
                                <div style="width: {pct_cumplimiento}%; background: #444; height: 100%;"></div>
                                <div style="position: absolute; top: 5px; left: 10px; color: #fff; font-weight: bold; font-size: 14px;">{df_m['LOGI']:.2f}%</div>
                                <div style="position: absolute; top: 5px; right: 10px; color: #000; font-weight: bold; font-size: 14px;">META: {df_m['META']}%</div>
                            </div>
                        </div>
                
                        <div style="display: flex; gap: 20px; margin-bottom: 40px;">
                            <div style="flex: 1; border: 1px solid #000; padding: 10px;">
                                <p style="margin: 0 0 10px 0; font-size: 10px; font-weight: bold; text-align: center; background: #000; color: #fff;">ESTRUCTURA DE COSTOS</p>
                                <table style="width: 100%; font-size: 11px;">
                                    <tr><td>Fletes:</td><td style="text-align: right;"><b>${df_m['FLETE']:,.0f}</b></td></tr>
                                    <tr><td>Incidencias:</td><td style="text-align: right;"><b>${df_m['VAL_INC']:,.0f}</b></td></tr>
                                    <tr style="border-top: 1px solid #000;"><td>Total Op:</td><td style="text-align: right;"><b>${(df_m['FLETE'] + df_m['VAL_INC']):,.0f}</b></td></tr>
                                </table>
                            </div>
                            <div style="flex: 1; border: 1px solid #000; padding: 10px;">
                                <p style="margin: 0 0 10px 0; font-size: 10px; font-weight: bold; text-align: center; background: #000; color: #fff;">EFICIENCIA UNITARIA</p>
                                <div style="text-align: center; padding-top: 5px;">
                                    <span style="font-size: 24px; font-weight: bold;">${df_m['CC26']:.2f}</span><br>
                                    <span style="font-size: 10px;">Costo por Caja</span>
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
                                <tr><td style="padding: 10px; border: 1px solid #000;">Ventas Totales Brutas (Facturación)</td><td style="padding: 10px; border: 1px solid #000; text-align: center;">${df_m['FACT']:,.2f}</td></tr>
                                <tr><td style="padding: 10px; border: 1px solid #000;">Volumen de Despacho (Unidades)</td><td style="padding: 10px; border: 1px solid #000; text-align: center;">{int(df_m['CAJAS']):,.0f} Cajas</td></tr>
                                <tr><td style="padding: 10px; border: 1px solid #000;">Variación vs Histórico (2024)</td><td style="padding: 10px; border: 1px solid #000; text-align: center;">{df_m['VS24']:.1f}%</td></tr>
                                <tr><td style="padding: 10px; border: 1px solid #000;">Impacto Económico Neto (INCR)</td><td style="padding: 10px; border: 1px solid #000; text-align: center;">${df_m['INCR']:,.2f}</td></tr>
                            </tbody>
                        </table>
                
                        <div style="margin-top: 60px; display: flex; justify-content: space-between; text-align: center; font-size: 11px;">
                            <div style="width: 45%;">
                                <div style="border-top: 2px solid #000; padding-top: 10px;">
                                    <b>RIGOBERTO HERNANDEZ</b><br>Coordinación Logística JYPESA
                                </div>
                            </div>
                            <div style="width: 45%;">
                                <div style="border-top: 2px solid #000; padding-top: 10px;">
                                    <b>CONTROL DE CALIDAD</b><br>Validación de Datos Nexion
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 30px; text-align: center; font-size: 9px; color: #666; font-style: italic;">
                            Este documento es una representación técnica oficial generada por el sistema NEXION 2026.
                        </div>
                    </div>
                    """
                    return html_content
                
                # --- INTERFAZ SIN BOTÓN DE EXCEL Y SIN CEROS ---
                st.markdown("""
                <style>
                /* Vacuna contra ceros verdes */
                iframe[data-testid="stHtml"] { display: none !important; }
                </style>
                """, unsafe_allow_html=True)
                
                st.write("---")
                if st.button(":material/print: GENERAR REPORTE GRÁFICO PARA IMPRESIÓN", type="primary", use_container_width=True):
                    reporte_html = generar_reporte_impresion(df_m, mes_sel)
                    
                    st.components.v1.html(f"""
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
                            
            
            elif st.session_state.menu_sub == "OTD":
                st.subheader("On-Time Delivery (OTD)")
                # [Aquí va tu código o función para el reporte OTD]
                st.bar_chart({"Entregas": [10, 20, 15, 30]})



        
    
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
                        # Filtramos en el inventario por código o descripción que contengan la palabra
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
                # --- HTML PARA IMPRESIÓN PT (BLINDAJE TOTAL DE MÁRGENES) ---
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
                        /* El truco maestro: margen @page en 0 elimina los textos del navegador */
                        @page {{ 
                            size: auto;
                            margin: 0mm; 
                        }}
                        @media print {{
                            body {{ 
                                margin: 0; 
                                padding: 15mm; /* Esto crea el margen real de la hoja sin activar basura del navegador */
                            }}
                            .no-print {{ display: none !important; }}
                        }}
                        body {{ font-family: sans-serif; color: black; background: white; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                        th {{ background: #eee; border: 1px solid black; padding: 8px; text-align: left; }}
                        .signature-section {{
                            margin-top: 80px;
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
                # Usamos una sub-llave para rastrear versiones y forzar el refresco del widget
                if 'reset_counter' not in st.session_state:
                    st.session_state.reset_counter = 0
    
                if 'rows_contrarecibo' not in st.session_state:
                    st.session_state.rows_contrarecibo = pd.DataFrame([
                        {"FECHA": now_gdl.strftime('%d/%m/%Y'), "CODIGO": "", "PAQUETERIA": "", "CANTIDAD": ""} 
                    ] * 10)
                
                # ── B. ENCABEZADO Y CONTROLES ──
                with st.container(border=True):
                    col_h1, col_h2 = st.columns([2, 1])
                    with col_h2:
                        hora_reporte = st.text_input("HORA", value=now_gdl.strftime('%I:%M %p').lower(), key="h_contra_val")
                
                # ── C. EDITOR DE DATOS ──
                # Al añadir el counter a la key, Streamlit destruye y recrea el widget al limpiar
                df_edit_c = st.data_editor(
                    st.session_state.rows_contrarecibo, 
                    num_rows="dynamic", 
                    use_container_width=True,
                    key=f"editor_contrarecibo_{st.session_state.reset_counter}",
                    column_config={
                        "FECHA": st.column_config.TextColumn("FECHA"),
                        "CODIGO": st.column_config.TextColumn("CÓDIGO"),
                        "PAQUETERIA": st.column_config.TextColumn("PAQUETERÍA"),
                        "CANTIDAD": st.column_config.TextColumn("CANTIDAD")
                    }
                )
                
                # ── D. RENDERIZADO PARA IMPRESIÓN ──
                filas_c = df_edit_c[df_edit_c["CODIGO"] != ""]
                tabla_c_html = "".join([
                    f"<tr>"
                    f"<td style='border-bottom:1px solid black;padding:8px;'>{r['FECHA']}</td>"
                    f"<td style='border-bottom:1px solid black;padding:8px;'>{r['CODIGO']}</td>"
                    f"<td style='border-bottom:1px solid black;padding:8px;'>{r['PAQUETERIA']}</td>"
                    f"<td style='border-bottom:1px solid black;padding:8px;text-align:center;'>{r['CANTIDAD']}</td>"
                    f"</tr>"
                    for _, r in filas_c.iterrows()
                ])
                
                espacios = "".join(["<tr><td style='border-bottom:1px solid black;height:25px;' colspan='4'></td></tr>"] * (12 - len(filas_c)))
                
                # ── ESTRUCTURA HTML CON CSS PARA QUITAR HEADERS/FOOTERS DEL NAVEGADOR ──
                form_c_html = f"""
                <html>
                <head>
                    <style>
                        @media print {{
                            @page {{ 
                                size: auto;   
                                margin: 0;  /* Esto elimina encabezados y pies de página del navegador */
                            }}
                            body {{ 
                                margin: 0; 
                                padding: 10mm; /* El margen visual lo damos con padding para que no se corten los textos */
                            }}
                            header, footer {{ display: none !important; }}
                        }}
                        
                        body {{ 
                            font-family: Arial, sans-serif; 
                            background: white; 
                            color: black; 
                        }}
                        
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
                                <span style="font-weight:bold; border:1px solid black; padding:2px 10px;">{hora_reporte}</span>
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
    
                # ── E. ACCIONES ──
                st.write("---")
                c_b1, c_b2 = st.columns(2)
                
                with c_b1:
                    if st.button(":material/print: IMPRIMIR CONTRARECIBO", type="primary", use_container_width=True, key="btn_p_c"):
                        components.html(f"<html><body>{form_c_html}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)
                
                with c_b2:
                    if st.button(":material/refresh: BORRAR", use_container_width=True, key="btn_r_c"):
                        # 1. Limpiamos el DataFrame en el estado
                        st.session_state.rows_contrarecibo = pd.DataFrame([
                            {"FECHA": now_gdl.strftime('%d/%m/%Y'), "CODIGO": "", "PAQUETERIA": "", "CANTIDAD": ""}
                        ] * 10)
                        # 2. Aumentamos el contador para forzar el cambio de KEY del editor
                        st.session_state.reset_counter += 1
                        # 3. Recargamos la app
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
    
            elif st.session_state.menu_sub == "DATA MANAGEMENT":
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
                
                            commit_msg = st.text_input("Mensaje de Sincronización", 
                                                     value=f"Update Master {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                
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
                        
                        st.write(f"**Última actualización:** {last_commit.commit.author.date.strftime('%d/%m/%Y %H:%M')}")
                        st.write(f"**Modificado por:** {last_commit.commit.author.name} :material/verified_user:")
                        st.write(f"**Nota:** {last_commit.commit.message}")
                        st.code(f"ID Registro: {last_commit.sha[:7]}", language="bash")
                    except:
                        st.info("Conectando con el servidor de seguridad de GitHub...")
            
            
            elif st.session_state.menu_sub == "ORDER STAGING":
                
                # Sección de instrucciones
                with st.expander("Herramienta para preparar archivo para S&T, ¿Dudas para usar este modulo?", expanded=False):
                    st.markdown(f"""
                    <div style='font-size: 14px; color: {vars_css['sub']}; letter-spacing: 1px;'>
                    1. <b>Cargar Archivo:</b> Sube tu archivo Excel (.xlsx) o CSV.<br>
                    2. <b>Definir Rango:</b> Ingresa el número de folio inicial y final.<br>
                    3. <b>Depurar Lista:</b> Desmarca la casilla de los folios que no necesites.<br>
                    4. <b>Procesar:</b> Haz clic en 'RENDERIZAR TABLA'.<br>
                    5. <b>Descargar:</b> Obtén tu nuevo archivo de Excel filtrado.
                    </div>
                    """, unsafe_allow_html=True)
                
                # 1. ÁREA DE CARGA
                uploaded_file = st.file_uploader("Subir archivo", type=["xlsx", "csv"], label_visibility="collapsed")
                
                if uploaded_file is not None:
                    # Carga con detección automática de delimitador (coma, punto y coma o tab)
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
                        else:
                            df = pd.read_excel(uploaded_file)
                        
                        # --- LIMPIEZA AGRESIVA DE COLUMNAS ---
                        # Eliminamos espacios en blanco, saltos de línea y tabulaciones de los nombres de columnas
                        df.columns = [str(c).strip().replace('\n', '').replace('\t', '') for c in df.columns]
                        
                        # Buscamos coincidencias exactas ignorando mayúsculas
                        col_folio = next((c for c in df.columns if c.lower() == 'factura'), None)
                        col_transporte = next((c for c in df.columns if c.lower() == 'transporte'), None)
            
                        # Si no hay coincidencia exacta, buscamos la que contenga la palabra
                        if not col_folio:
                            col_folio = next((c for c in df.columns if 'factura' in c.lower()), df.columns[0])
                        if not col_transporte:
                            col_transporte = next((c for c in df.columns if 'transporte' in c.lower()), None)
                        
                        st.toast(f"DETECTADO -> Factura: {col_folio} | Transporte: {col_transporte}", icon="🔍")
                    
                        # --- PANEL DE CONTROL ---
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_left, col_right = st.columns([1, 2], gap="large")
                    
                        with col_left:
                            st.markdown(f"<p class='op-query-text' style='text-align:left !important;'>FILTROS DE RANGO</p>", unsafe_allow_html=True)
                            
                            # Conversión numérica segura
                            serie_folios = pd.to_numeric(df[col_folio], errors='coerce').dropna()
                            
                            if not serie_folios.empty:
                                f_min_val = int(serie_folios.min())
                                f_max_val = int(serie_folios.max())
                            else:
                                f_min_val, f_max_val = 0, 0
            
                            inicio = st.number_input("Folio Inicial", value=f_min_val)
                            final = st.number_input("Folio Final", value=f_max_val)
                            
                            # Filtrar asegurando comparación numérica
                            df[col_folio] = pd.to_numeric(df[col_folio], errors='coerce')
                            df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)].copy()
                    
                        with col_right:
                            st.markdown(f"<p class='op-query-text' style='text-align:left !important;'>SELECCIÓN DE FOLIOS</p>", unsafe_allow_html=True)
                            
                            if not df_rango.empty:
                                # Agrupamos para mostrar en el editor
                                cols_to_show = [col_folio]
                                if col_transporte: cols_to_show.append(col_transporte)
                                
                                info_folios = df_rango.drop_duplicates(subset=[col_folio])[cols_to_show]
                                
                                selector_df = info_folios.copy()
                                selector_df.insert(0, "Incluir", True)
                    
                                edited_df = st.data_editor(
                                    selector_df,
                                    column_config={
                                        "Incluir": st.column_config.CheckboxColumn("SEL", default=True),
                                        col_folio: st.column_config.TextColumn("FACTURA", disabled=True),
                                        col_transporte: st.column_config.TextColumn("TRANSPORTE", disabled=True) if col_transporte else "N/A"
                                    },
                                    hide_index=True,
                                    height=300,
                                    use_container_width=True,
                                    key="editor_folio_master_v3"
                                )
                            else:
                                st.warning("Sin datos en el rango seleccionado.")
                                edited_df = pd.DataFrame()
                    
                        # --- ACCIONES ---
                        st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; opacity:0.2;'>", unsafe_allow_html=True)
                        
                        if not edited_df.empty:
                            folios_finales = edited_df[edited_df["Incluir"] == True][col_folio].tolist()
                            c1, c2 = st.columns(2)
                            
                            with c1:
                                render_btn = st.button("RENDERIZAR TABLA")
                            
                            if render_btn:
                                df_final = df_rango[df_rango[col_folio].isin(folios_finales)]
                                
                                if not df_final.empty:
                                    st.markdown(f"<p style='font-size:10px; color:{vars_css['sub']}; letter-spacing:2px; text-align:center;'>VISTA PREVIA</p>", unsafe_allow_html=True)
                                    st.dataframe(df_final, use_container_width=True)
                                    
                                    output = BytesIO()
                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                        df_final.to_excel(writer, index=False)
                                    
                                    with c2:
                                        st.download_button(
                                            label="DESCARGAR EXCEL (.XLSX)",
                                            data=output.getvalue(),
                                            file_name=f"S&T_PREP_{datetime.now().strftime('%d%m%Y')}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                            use_container_width=True
                                        )
                    except Exception as e:
                        st.error(f"Error al procesar el archivo: {e}")
                        
                else:
                    st.markdown(f"<div style='text-align:center; padding:50px; color:{vars_css['sub']}; font-size:10px; letter-spacing:4px;'>WAITING FOR ERP DATA...</div>", unsafe_allow_html=True)


                st.divider()
                # ── MÓDULO REPARADOR DE COSTOS ──
                # --- EXPANDER DE INSTRUCCIONES ---
                with st.expander("Reparador de Costos Logísticos ¿Dudas para usar este módulo?", icon=":material/help:"):
                    st.markdown("""
                    1. **Subida de datos:** Haz clic en el cargador o arrastra tu archivo Excel/CSV. 
                    2. **Configuración de columnas:** Verifica que los selectores coincidan con las columnas de tu archivo.
                    3. **Procesamiento:** El sistema detectará automáticamente si los costos por guía están duplicados.
                    
                    
                    * **Si el costo es idéntico:** Si una guía tiene varias facturas con el mismo costo, el sistema **prorratea** el costo según las cajas.
                    * **Si los costos son diferentes:** Si una guía tiene montos distintos, el sistema **no los toca** (asume cargos independientes).
                    
                    4. **Descarga:** Genera un archivo `.xlsx` listo para reportes.
                    """)
                
                st.info("Esta herramienta detecta costos duplicados por guía y los prorratea proporcionalmente según el número de cajas.", icon=":material/info:")
                
                uploaded_file = st.file_uploader("1. Sube tu archivo de operación (CSV o Excel)", type=["csv", "xlsx"], key="repair_uploader")
                
                if uploaded_file is not None:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.subheader("2. Configuración de Columnas", divider="gray")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        col_factura = st.selectbox("Columna Factura", df.columns, 
                                                 index=df.columns.get_loc("DocNum") if "DocNum" in df.columns else 0)
                    with c2:
                        col_guia = st.selectbox("Columna Guía", df.columns, 
                                              index=df.columns.get_loc("U_BXP_NGUIA") if "U_BXP_NGUIA" in df.columns else 0)
                    with c3:
                        col_costo = st.selectbox("Columna Costo", df.columns, 
                                               index=df.columns.get_loc("U_BXP_COSTO_GUIA") if "U_BXP_COSTO_GUIA" in df.columns else 0)
                    with c4:
                        col_cajas = st.selectbox("Columna Cajas", df.columns, 
                                               index=df.columns.get_loc("U_BXP_CAJAS_ENV") if "U_BXP_CAJAS_ENV" in df.columns else 0)
                
                    if st.button("Procesar y Reparar Datos", use_container_width=True, type="primary", icon=":material/database_gear:"):
                        try:
                            # Lógica de Reparación
                            stats_guia = df.groupby(col_guia).agg({col_costo: 'nunique', col_cajas: 'sum'}).reset_index()
                            stats_guia.columns = [col_guia, 'costos_unicos', 'TOTAL_CAJAS_GUIA']
                            df_final = pd.merge(df, stats_guia, on=col_guia)
                
                            def aplicar_reparacion(row):
                                if row['costos_unicos'] == 1:
                                    return (row[col_costo] / row['TOTAL_CAJAS_GUIA']) * row[col_cajas]
                                return row[col_costo]
                
                            df_final['COSTO_REAL_AJUSTADO'] = df_final.apply(aplicar_reparacion, axis=1)
                            st.success("Proceso completado con éxito.", icon=":material/check_circle:")
                
                            # Descarga
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                df_final.to_excel(writer, index=False, sheet_name='Costos Reparados')
                            
                            st.download_button(
                                label="Descargar Reporte Corregido (.xlsx)",
                                data=output.getvalue(),
                                file_name="reporte_logistico_reparado.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                icon=":material/download_for_offline:",
                                use_container_width=True
                            )
                            
                            st.subheader("Vista Previa del Análisis", divider="blue")
                            columnas_vista = [col_factura, col_guia, col_cajas, col_costo, 'TOTAL_CAJAS_GUIA', 'COSTO_REAL_AJUSTADO']
                            st.dataframe(df_final[columnas_vista].head(20), use_container_width=True)
                
                        except Exception as e:
                            st.error(f"Error al procesar: {e}", icon=":material/error:")
                else:
                    st.info("Esperando archivo de operación...", icon=":material/upload_file:")
    
    # Convertimos tu enlace normal en un enlace de "Embed"
    # Tu enlace original: http://googleusercontent.com/spotify.com/6
    # El ID es: 195v6pT2tA890f5XmG8KzY
    spotify_embed_url = "http://googleusercontent.com/spotify.com/7?utm_source=generator&theme=0"
    
    # ── FOOTER FIJO (REPRODUCTOR + BRANDING) ────────────────────────
    st.markdown(f"""
        <div class="footer">
            <div style="margin-bottom: 12px; width: 100%;">
                <iframe 
                    src="{spotify_embed_url}" 
                    width="100%" 
                    height="80" 
                    frameBorder="0" 
                    allowfullscreen="" 
                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                    style="border-radius:12px; border: none;"
                    loading="lazy">
                </iframe>
            </div>
            
            <div style="line-height: 1.4;">
                NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
                <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
                <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
            </div>
        </div>
    """, unsafe_allow_html=True)




































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































