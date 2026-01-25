import streamlit as st
import pandas as pd
import altair as alt
import time
import base64
import textwrap
import streamlit.components.v1 as components
import numpy as np
import datetime
import io
import os
import re
import unicodedata
import requests
from io import StringIO
from github import Github
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection



# --- FUNCIÓN PARA CARGAR EL LOGO ---
def get_base64_bin(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

# CARGAMOS LA VARIABLE ANTES DE USARLA
logo_b64 = get_base64_bin("n1.png")# --- NUEVO PROTOCOLO DE IMPORTACIÓN PARA FPDF2 (BLOQUE ELITE) ---
# --- PROTOCOLO DE CONEXIÓN FINAL ---
try:
    from fpdf import FPDF
    PDF_READY = True
except (ImportError, ModuleNotFoundError):
    PDF_READY = False

# --- FUNCIÓN ELITE DE RENDERIZADO ---REPORTE DE OTS
def render_card(label, value, footer, target_val=None, actual_val=None, inverse=False, border_base="border-blue"):
    if target_val is None or actual_val is None:
        color = "#f0f6fc"
        border = border_base
    else:
        # Lógica: Si inverse=True (ej. OTD), mayor es mejor.
        if inverse:
            is_alert = actual_val < target_val
        else:
            is_alert = actual_val > target_val
            
        color = "#fb7185" if is_alert else "#00ffa2"
        border = "border-red" if is_alert else "border-green"
    
    st.markdown(f"""
        <div class='card-container {border}'>
            <div class='card-label'>{label}</div>
            <div class='card-value' style='color:{color}'>{value}</div>
            <div class='card-footer'>{footer}</div>
        </div>
    """, unsafe_allow_html=True)

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Distribucion y Logística Inteligente", layout="wide", initial_sidebar_state="expanded")


# 2. ESTADOS DE SESIÓN
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False
if "motivo_splash" not in st.session_state:
    st.session_state.motivo_splash = "inicio"
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "principal"  # Controla qué sección del dashboard se ve
if "ultimo_movimiento" not in st.session_state:
    st.session_state.ultimo_movimiento = time.time() # Para control de inactividad
if "tabla_expandida" not in st.session_state:
    st.session_state.tabla_expandida = False


# --- 2. LÓGICA DE MÁRGENES Y ALTURA (Flecha visible y espacios respetados) ---
st.markdown("""
    <style>
        /* Margen general del dashboard */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }

        /* Ocultamos solo el footer (la marca de Streamlit) */
        footer {visibility: hidden;}
        
        /* ESPACIO DE BOTONES: Mantiene la cercanía profesional a la tabla */
        div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
            margin-bottom: -0.5rem !important;
        }
        
        /* ESPACIO DE DONITAS: Mantiene el despegue de los indicadores */
        div[data-testid="stHorizontalBlock"]:has(div[style*="text-align:center"]) {
            margin-bottom: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# Altura dinámica según el botón presionado (Esto no cambia)
if st.session_state.tabla_expandida:
    h_dinamica = 850
else:
    h_dinamica = 200

#---------------------------------------------------

# Colores
color_fondo_nativo = "#0e1117" 
color_blanco = "#FFFFFF"
color_verde = "#00FF00" 
color_borde_gris = "#00ffa2"
# --------------------------------------------------
# 3. ESTILOS CSS (Corregido para NO ocultar la flecha)
# --------------------------------------------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');
    
    .stApp {{ background-color: {color_fondo_nativo} !important; }}
    
    /* Mostrar flecha de sidebar pero ocultar decoradores innecesarios */
    header[data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    footer {{ visibility: hidden !important; }}
    div[data-testid="stDecoration"] {{ display: none !important; }}

    /* Caja 3D Logística Sellada */
    .scene {{ width: 100%; height: 120px; perspective: 600px; display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }}
    .cube {{ width: 60px; height: 60px; position: relative; transform-style: preserve-3d; transform: rotateX(-20deg) rotateY(45deg); animation: move-pkg 6s infinite ease-in-out; }}
    .cube-face {{ position: absolute; width: 60px; height: 60px; background: #d2a679; border: 1.5px solid #b08d5c; box-shadow: inset 0 0 15px rgba(0,0,0,0.1); }}
    .cube-face::after {{ content: ''; position: absolute; top: 45%; width: 100%; height: 6px; background: rgba(0,0,0,0.15); }}
    
    .front  {{ transform: rotateY(0deg) translateZ(30px); }}
    .back   {{ transform: rotateY(180deg) translateZ(30px); }}
    .right  {{ transform: rotateY(90deg) translateZ(30px); }}
    .left   {{ transform: rotateY(-90deg) translateZ(30px); }}
    .top    {{ transform: rotateX(90deg) translateZ(30px); background: #e3bc94; }}
    .bottom {{ transform: rotateX(-90deg) translateZ(30px); background: #b08d5c; }}
    
    @keyframes move-pkg {{ 0%, 100% {{ transform: translateY(0px) rotateX(-20deg) rotateY(45deg); }} 50% {{ transform: translateY(-15px) rotateX(-20deg) rotateY(225deg); }} }}
    
    /* Login Form */
    .stForm {{ background-color: {color_fondo_nativo} !important; border: 1.5px solid {color_borde_gris} !important; border-radius: 20px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
    .login-header {{ text-align: center; color: white; font-family: Arial; font-size: 24px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }}
    input {{ font-family: 'Arial', monospace !important; color: white !important; }}
</style>
""", unsafe_allow_html=True)

placeholder = st.empty()

# --------------------------------------------------
# 4. FLUJO DE PANTALLAS
# --------------------------------------------------

# --- 1. PREPARACIÓN DE RECURSOS (Asegúrate de tener esto al inicio) ---
import base64
import streamlit as st

def get_base64_file(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

logo_b64 = get_base64_file("n1.png")

# --- 2. CASO A: LOGIN (ENSAMBLADO FINAL) ---
if not st.session_state.logueado:
    with placeholder.container():
        col1, col2, col3 = st.columns([1.5, 1, 1.5])
        with col2:
            st.markdown('<div style="height:10vh"></div>', unsafe_allow_html=True)
            with st.form("login_form"):
                
                # --- SECCIÓN VISUAL: LOGO + ANIMACIÓN ---
                if logo_b64:
                    st.markdown(f'<div style="text-align:center;margin-bottom:20px;"><img src="data:image/png;base64,{logo_b64}" style="width:250px;mix-blend-mode:screen;display:block;margin:0 auto;"><div style="width:160px;height:2px;background:#00FFAA;margin:15px auto 5px auto;box-shadow:0 0 12px #00FFAA;animation:s 2.5s infinite ease-in-out;"></div><div style="font-family:monospace;color:#00FFAA;font-size:11px;letter-spacing:4px;animation:b 1.5s infinite;">Distribucion y Logística: Inteligente</div></div><style>@keyframes s{{0%,100%{{width:0%;opacity:0;}}50%{{width:80%;opacity:1;}}}}@keyframes b{{0%,100%{{opacity:1;}}50%{{opacity:0.3;}}}}</style>', unsafe_allow_html=True)
                
                # --- EL RESTO DEL FORMULARIO SE QUEDA IGUAL ---
                u_input = st.text_input("Usuario")
                c_input = st.text_input("Contraseña", type="password")
                
                if st.form_submit_button("INGRESAR", use_container_width=True):
                    usuarios = st.secrets["usuarios"]
                    if u_input in usuarios and str(usuarios[u_input]) == str(c_input):
                        st.session_state.logueado = True
                        st.session_state.usuario_actual = u_input
                        st.session_state.splash_completado = False
                        st.session_state.motivo_splash = "inicio"
                        st.rerun()
                    else:
                        st.error("Acceso Denegado")
    st.stop()

# CASO B: SPLASH SCREEN (Versión NEXION Premium - Con Círculo de Carga)
elif not st.session_state.splash_completado:
    with placeholder.container():
        # El nombre del usuario resaltado en Blanco
        usuario_highlight = st.session_state.usuario_actual.upper() if st.session_state.usuario_actual else "CLIENTE"
        
        color_fondo_st = "#0e1117" 
        color_neon = "#00FFAA" 
        
        if st.session_state.motivo_splash == "logout":
            mensajes = ["CERRANDO SESIÓN SEGURA", "RESGUARDANDO REGISTROS", "CONEXIÓN FINALIZADA"]
        else:
            mensajes = [
                f"BIENVENIDO DE VUELTA, <span style='color:white; font-weight:700;'>{usuario_highlight}</span>",
                "SINCRONIZANDO MANIFIESTOS NEXION",
                "ACTUALIZANDO ESTATUS DE ENVÍOS",
                "AUTENTICACIÓN COMPLETADA"
            ]

        splash_placeholder = st.empty()

        for i, msg in enumerate(mensajes):
            progreso = int(((i + 1) / len(mensajes)) * 100)
            
            splash_placeholder.markdown(f"""
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;700&display=swap');

                    .corporate-splash {{
                        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                        background-color: {color_fondo_st}; 
                        z-index: 999999;
                        display: flex; flex-direction: column; justify-content: center; align-items: center;
                        font-family: 'Inter', sans-serif;
                    }}

                    .branding-box {{
                        text-align: center;
                        width: 450px;
                        padding: 20px;
                    }}

                    .logo-placeholder {{
                        font-weight: 700;
                        font-size: 11px;
                        letter-spacing: 6px;
                        color: rgba(255, 255, 255, 0.4);
                        margin-bottom: 30px;
                        justify-content: center;
                        display: flex;
                        align-items: center;
                    }}

                    /* --- CÍRCULO DE CARGA (SPINNER) --- */
                    .loader-circle {{
                        border: 3px solid rgba(255, 255, 255, 0.1);
                        border-top: 3px solid {color_neon};
                        border-radius: 50%;
                        width: 90px;
                        height: 90px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 30px auto;
                        box-shadow: 0 0 15px {color_neon}33;
                    }}

                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}

                    .main-msg {{
                        color: {color_neon};
                        font-size: 1.1rem;
                        font-weight: 300;
                        letter-spacing: 1.5px;
                        margin-bottom: 25px;
                        min-height: 60px;
                        line-height: 1.4;
                        text-shadow: 0 0 15px {color_neon}33;
                    }}

                    .footer-info {{
                        margin-top: 30px;
                        display: flex;
                        justify-content: space-between;
                        color: rgba(255, 255, 255, 0.3);
                        font-size: 10px;
                        font-weight: 700;
                        font-family: monospace;
                        border-top: 1px solid rgba(255,255,255,0.05);
                        padding-top: 15px;
                    }}
                </style>
                
                <div class="corporate-splash">
                    <div class="branding-box">
                        <div class="logo-placeholder">NEXION LOGISTICS CORE</div>
                        <div class="loader-circle"></div>
                        <div class="main-msg">{msg}</div>
                        <div class="footer-info">
                            <span>SESSION_ID: NX-2026</span>
                            <span style="color: {color_neon}">{progreso}%</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # --- LÓGICA DE TIEMPO PERSONALIZADA ---
            if i == 0 and st.session_state.motivo_splash != "logout":
                time.sleep(2.5) 
            else:
                time.sleep(0.7 if i < len(mensajes)-1 else 1.2)
        
        # Lógica de cierre de sesión
        if st.session_state.motivo_splash == "logout":
            st.session_state.logueado = False
            st.session_state.usuario_actual = None
            st.session_state.pagina = "principal"
            st.session_state.motivo_splash = "inicio"
            st.cache_data.clear()
        
        st.session_state.splash_completado = True
        st.rerun()
    st.stop()

# 3. CONTENIDO PRIVADO (DASHBOARD)
else:      
    # --- MOTOR DE DATOS ---
    @st.cache_data
    def cargar_datos():
        df = pd.read_csv("Matriz_Excel_Dashboard.csv", encoding="utf-8")
        df.columns = df.columns.str.strip().str.upper()
        df["NO CLIENTE"] = df["NO CLIENTE"].astype(str).str.strip()
        df["FECHA DE ENVÍO"] = pd.to_datetime(df["FECHA DE ENVÍO"], errors="coerce", dayfirst=True)
        df["PROMESA DE ENTREGA"] = pd.to_datetime(df["PROMESA DE ENTREGA"], errors="coerce", dayfirst=True)
        df["FECHA DE ENTREGA REAL"] = pd.to_datetime(df["FECHA DE ENTREGA REAL"], errors="coerce", dayfirst=True)
        
        hoy = pd.Timestamp.today().normalize()
        def calcular_estatus(row):
            if pd.notna(row["FECHA DE ENTREGA REAL"]): return "ENTREGADO"
            if pd.notna(row["PROMESA DE ENTREGA"]) and row["PROMESA DE ENTREGA"] < hoy: return "RETRASADO"
            return "EN TRANSITO"
        
        df["ESTATUS_CALCULADO"] = df.apply(calcular_estatus, axis=1)
        return df

    df = cargar_datos()

    # BARRA LATERAL
    
    # --- RECONEXIÓN DE LOGO NEXION (FUERZA BRUTA) ---
    import base64
    def get_base64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    try:
        logo_base64 = get_base64("n1.png")
        # Inyectamos el logo como un bloque HTML real, no como fondo de CSS
        st.sidebar.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0px;">
                <img src="data:image/png;base64,{logo_base64}" width="220">
            </div>
            <style>
                /* Esto elimina el espacio vacío que Streamlit deja arriba por defecto */
                [data-testid="stSidebarNav"] {{
                    padding-top: 20px !important;
                }}
            </style>
            """, 
            unsafe_allow_html=True
        )
    except Exception as e:
        st.sidebar.warning("Logo n1.png no detectado en el radar.")
    
    st.sidebar.markdown(f'<div style="display:flex;align-items:center;justify-content:center;gap:10px;margin-top:12px;margin-left:-8px;"><svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="8" r="4" stroke="#00FFAA" stroke-width="1.8"/><path d="M4 20c0-3.5 3.6-6 8-6s8 2.5 8 6" stroke="#00FFAA" stroke-width="1.8" stroke-linecap="round"/></svg><span style="color:#999;font-size:16px;">Sesión: <span style="color:#00FFAA;font-weight:500;">{st.session_state.usuario_actual}</span></span></div>', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state.splash_completado = False 
        st.session_state.motivo_splash = "logout"
        st.rerun()
    
    
            
    # --------------------------------------------------
    # 🛣️ INICIO DE LA LÓGICA DE NAVEGACIÓN
    # --------------------------------------------------
    if st.session_state.pagina == "principal":
        # A partir de aquí pondremos todo lo del Dashboard Principal
        # --------------------------------------------------
        # TÍTULO Y ENCABEZADO
        # --------------------------------------------------
        st.markdown("<style>@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}</style>", unsafe_allow_html=True)
        # --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (Sube el contenido y estiliza el menú) ---
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 0rem !important;
                    max-width: 95% !important;
                }

                .header-wrapper {
                    display: flex;
                    align-items: baseline;
                    gap: 12px;
                    font-family: 'Inter', sans-serif;
                }

                /* TITULO PRINCIPAL: Gris Oscuro */
                .header-wrapper h1 {
                    font-size: 22px !important;
                    font-weight: 800;
                    margin: 0;
                    color: #4b5563; /* Gris oscuro */
                    letter-spacing: -0.8px;
                }

                /* INDICADOR: Blanco */
                .header-wrapper span {
                    font-size: 14px;
                    font-weight: 300;
                    color: #ffffff; /* Blanco */
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                /* BOTÓN DE MENÚ MINIMALISTA */
                div[data-testid="stPopover"] > button {
                    background-color: transparent !important;
                    border: 1px solid rgba(0, 255, 162, 0.3) !important;
                    padding: 2px 10px !important;
                    border-radius: 6px !important;
                    height: 32px !important;
                    transition: all 0.3s ease;
                }
                
                div[data-testid="stPopover"] > button:hover {
                    border: 1px solid #00ffa2 !important;
                    box-shadow: 0 0 10px rgba(0, 255, 162, 0.2);
                }

                div[data-testid="stPopoverContent"] button {
                    text-align: left !important;
                    justify-content: flex-start !important;
                    border: none !important;
                    background: transparent !important;
                    font-size: 13px !important;
                    padding: 8px 10px !important;
                }

                div[data-testid="stPopoverContent"] button:hover {
                    color: #00ffa2 !important;
                    background: rgba(0, 255, 162, 0.05) !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # --- 2. POSICIONAMIENTO DEL ENCABEZADO ---
        c1, c2 = st.columns([0.88, 0.12], vertical_alignment="bottom")

        with c1:
            st.markdown("""
                <div class="header-wrapper">
                    <h1>TRACKING</h1>
                    <span>INDICATOR</span>
                    <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #00ffa2; opacity: 0.7; margin-left: 10px; padding-left: 10px; border-left: 1px solid #334155;">
                        LOGÍSTICA & RENDIMIENTO
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            with st.popover("☰", use_container_width=True):
                st.markdown("<p style='color:#64748b; font-size:10px; font-weight:700; margin-bottom:10px; letter-spacing:1px;'>NAVEGACIÓN</p>", unsafe_allow_html=True)
                
                paginas = {
                "TRACKING": ("principal", "radar_btn_aac"),
                "SEGUIMIENTO": ("KPIs", "radar_btn_kpi"),
                "REPORTE OPS": ("Reporte", "radar_btn_rep"),
                "HUB LOGISTIC": ("HubLogistico", "radar_btn_hub"),
                "OTD": ("RadarRastreo", "radar_btn_radar"), # <--- ASEGÚRATE DE QUE ESTA COMA ESTÉ AQUÍ
                "MCONTROL": ("MControl", "radar_btn_mcontrol")
            }

                for nombre, (v_state, v_key) in paginas.items():
                    if st.button(nombre, use_container_width=True, key=v_key):
                        st.session_state.pagina = v_state
                        st.rerun()

        # Línea divisoria
        st.markdown("<hr style='margin: 8px 0 20px 0; border: none; border-top: 1px solid rgba(148, 163, 184, 0.1);'>", unsafe_allow_html=True)
        # =========================================================
        # ARRIBA - MENÚ DE NAVEGACIÓN FLOTANTE (ESTILO HAMBURGUESA)
        # =========================================================
        
        
        # 1. FUNCIÓN DE LIMPIEZA
        def limpiar_filtros():
            st.session_state.filtro_cliente_actual = ""
            st.session_state.filtro_cliente_input = ""
            f_min_res = df["FECHA DE ENVÍO"].min()
            f_max_res = df["FECHA DE ENVÍO"].max()
            st.session_state["fecha_filtro"] = (f_min_res, f_max_res)
            st.session_state["fletera_filtro"] = ""
            st.rerun()
    
        if st.sidebar.button("Limpiar Filtros", use_container_width=True):
            limpiar_filtros()
    
        st.sidebar.markdown("---")
                
        # 3. CALENDARIO
        f_min_data = df["FECHA DE ENVÍO"].min()
        f_max_data = df["FECHA DE ENVÍO"].max()
    
        if "fecha_filtro" not in st.session_state:
            st.session_state["fecha_filtro"] = (f_min_data, f_max_data)
    
        rango_fechas = st.sidebar.date_input(
            "Fecha de envío",
            min_value=f_min_data,
            max_value=f_max_data,
            key="fecha_filtro"
        )
    
         # 2. BUSCADOR (CLIENTE O GUÍA)
        if "filtro_cliente_actual" not in st.session_state:
            st.session_state.filtro_cliente_actual = ""
    
        
                
        # 4. SELECTOR DE FLETERA
        fletera_sel = st.sidebar.selectbox(
            "Selecciona Fletera",
            options=[""] + sorted(df["FLETERA"].dropna().unique()),
            index=0,
            key="fletera_filtro"
        )
             
        
        # --------------------------------------------------
        # APLICACIÓN DE FILTROS (CORREGIDO Y REFORZADO)
        # --------------------------------------------------
        df_filtrado = df.copy()
        
        # 1. Limpiamos el valor buscado para evitar errores de espacios
        valor_buscado = str(st.session_state.filtro_cliente_actual).strip().lower()
    
        # PRIORIDAD 1: Si el usuario escribió algo en el buscador
        if valor_buscado != "":
            # Convertimos las columnas a texto y quitamos el .0 que pone Excel a veces
            col_cliente_txt = df_filtrado["NO CLIENTE"].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower()
            col_guia_txt = df_filtrado["NÚMERO DE GUÍA"].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower()
            
            # Creamos la máscara de búsqueda
            mask_cliente = col_cliente_txt.str.contains(valor_buscado, na=False)
            mask_guia = col_guia_txt.str.contains(valor_buscado, na=False)
            
            # Filtramos (Si coincide con cliente O con guía)
            df_filtrado = df_filtrado[mask_cliente | mask_guia]
            
        # PRIORIDAD 2: Si el buscador está vacío, aplicamos fechas y fletera
        else:
            # Validación de fechas
            if isinstance(rango_fechas, (list, tuple)) and len(rango_fechas) == 2:
                f_inicio, f_fin = rango_fechas
                f_ini_dt = pd.to_datetime(f_inicio)
                f_fin_dt = pd.to_datetime(f_fin)
                
                df_filtrado = df_filtrado[
                    (df_filtrado["FECHA DE ENVÍO"] >= f_ini_dt) & 
                    (df_filtrado["FECHA DE ENVÍO"] <= f_fin_dt)
                ]
            
            # Filtro de fletera
            if fletera_sel != "":
                df_filtrado = df_filtrado[df_filtrado["FLETERA"].astype(str).str.strip() == fletera_sel]
    
            # --------------------------------------------------
            # ACTUALIZACIÓN DE MÉTRICAS (Para que los círculos cambien)
            # --------------------------------------------------
            total = len(df_filtrado)
            entregados = (df_filtrado["ESTATUS_CALCULADO"] == "ENTREGADO").sum()
            en_transito = (df_filtrado["ESTATUS_CALCULADO"] == "EN TRANSITO").sum()
            retrasados = (df_filtrado["ESTATUS_CALCULADO"] == "RETRASADO").sum()
    
        # --------------------------------------------------------------------
        # --- BLINDAJE MAESTRO: ELIMINACIÓN DE CAJA FANTASMA Y SINCRONIZACIÓN
        #---------------------------------------------------------------------
        st.markdown("""
        <style>
        /* 1. Contenedores (Sin cambios para mantener estabilidad) */
        div[data-testid="stTextInput"], 
        div[data-testid="stTextInput"] > div, 
        div[data-testid="stTextInput"] > div > div {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            height: auto !important;
        }

        /* 2. EL TEXTO INGRESADO (VALOR REAL) */
        div[data-testid="stTextInput"] input {
            height: 85px !important; 
            font-size: 30px !important; /* <--- TAMAÑO GIGANTE AL ESCRIBIR */
            font-weight: 800 !important;
            color: #FFFFFF !important; 
            background-color: rgba(17, 24, 39, 1) !important;
            border: 1px solid #38bdf8 !important; 
            border-radius: 20px !important;
            text-align: center !important;
            outline: none !important;
            box-sizing: border-box !important;
        }

        /* 3. EL TEXTO ANTES DE INGRESAR (PLACEHOLDER) */
        /* Aquí ajustamos el tamaño de "--- ESPERANDO COMANDO ---" */
        div[data-testid="stTextInput"] input::placeholder {
            font-size: 16px !important;  /* <--- MÁS PEQUEÑO Y DISCRETO */
            font-weight: 400 !important;
            color: rgba(255, 255, 255, 0.3) !important; /* Un blanco más transparente */
            letter-spacing: 4px !important; /* Estilo cinemático */
        }

        /* 4. Focus (Efecto Neón al escribir) */
        div[data-testid="stTextInput"] input:focus {
            outline: none !important;
            border: 1px solid #00FFAA !important;
            box-shadow: 0 0 20px rgba(0, 255, 170, 0.5) !important;
        }

        /* 5. Estilo del Label (El título de arriba) */
        div[data-testid="stTextInput"] label {
            min-height: 0px !important;
            margin-bottom: 15px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # --- DISTRIBUCIÓN DE MANDO ---
        c_left, c_main, c_right = st.columns([0.4, 1.2, 0.4])
        
        with c_main:
            # Actualizamos el Label para que el usuario sepa que puede buscar ambos
            pedido_buscar = st.text_input(
                "",
                value="",
                placeholder="--- INGRESA NUMERO DE FACTURA O GUIA ---",
                key="buscador_compacto"
            )
        
        df_busqueda = pd.DataFrame() # Blindaje inicial
    
        if pedido_buscar.strip() != "":
            # --- MANIOBRA MULTI-FILTRO (PEDIDO | GUÍA) ---
            query = pedido_buscar.strip().lower()
            
            df_busqueda = df_filtrado[
                (df_filtrado["NÚMERO DE PEDIDO"].astype(str).str.contains(query, case=False, na=False)) |
                (df_filtrado["NÚMERO DE GUÍA"].astype(str).str.contains(query, case=False, na=False))
            ].copy()
    
            if df_busqueda.empty:
                st.warning(f"No se encontró registro para: {pedido_buscar}")
            else:
                # RELOJ DE SEGURIDAD
                hoy = pd.Timestamp.today().normalize()
                                                              
                # CÁLCULOS DE TIEMPO
                df_busqueda["DIAS_TRANSCURRIDOS"] = ((df_busqueda["FECHA DE ENTREGA REAL"].fillna(hoy) - df_busqueda["FECHA DE ENVÍO"]).dt.days)
                df_busqueda["DIAS_RETRASO"] = ((df_busqueda["FECHA DE ENTREGA REAL"].fillna(hoy) - df_busqueda["PROMESA DE ENTREGA"]).dt.days)
                df_busqueda["DIAS_RETRASO"] = df_busqueda["DIAS_RETRASO"].apply(lambda x: x if x > 0 else 0)
    
                for index, row in df_busqueda.iterrows():
                    st.markdown(f'<p style="font-size:14px; font-weight:normal; color:gray; margin-bottom:-10px;">Resultados para: {row["NÚMERO DE PEDIDO"]}</p>', unsafe_allow_html=True)
                    
                    # --- ESTILOS CSS ANIMADOS (Círculos Blindados) ---
                    st.markdown("""<style>
                        @keyframes p-green { 0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); } 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); } } 
                        @keyframes p-blue { 0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); } 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); } } 
                        @keyframes p-orange { 0% { box-shadow: 0 0 0 0 rgba(249, 115, 22, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(249, 115, 22, 0); } 100% { box-shadow: 0 0 0 0 rgba(249, 115, 22, 0); } } 
                        @keyframes p-red { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } } 
                        .dot-green { border-radius: 50% !important; animation: p-green 2s infinite; } 
                        .dot-blue { border-radius: 50% !important; animation: p-blue 2s infinite; } 
                        .dot-orange { border-radius: 50% !important; animation: p-orange 2s infinite; } 
                        .dot-red { border-radius: 50% !important; animation: p-red 2s infinite; } 
                        .dot-gray { border-radius: 50% !important; background: #374151 !important; }
                        .elite-card{transition:all 0.4s ease;display:flex;flex-direction:column;justify-content:space-between;}.elite-card:hover{transform:translateY(-8px);box-shadow:0 20px 40px rgba(0,0,0,0.7)!important;border:1px solid rgba(255,255,255,0.25)!important;background:rgba(255,255,255,0.04)!important;}
                    </style>""", unsafe_allow_html=True)
                    
                    # --- LÓGICA DE NODOS ---
                    f_envio_dt = pd.to_datetime(row.get("FECHA DE ENVÍO"), errors='coerce')
                    f_promesa_dt = pd.to_datetime(row.get("PROMESA DE ENTREGA"), errors='coerce')
                    f_real_dt = pd.to_datetime(row.get("FECHA DE ENTREGA REAL"), errors='coerce')
                    entregado = pd.notna(f_real_dt)
                    
                    guia_val = str(row.get("NÚMERO DE GUÍA", "")).strip().upper()
                    tiene_guia = pd.notna(row.get("NÚMERO DE GUÍA")) and guia_val not in ["", "NAN", "0", "PENDIENTE"]
                    
                    # Nodo 2: Paquetería (Siempre se activa si el pedido salió)
                    t_env = "ENTREGADO A PAQUETERÍA"
                    c_env = "#22c55e"
                    anim_env = "dot-green"
                    
                    # Nodo 3: Tránsito o Proceso de Guía (Círculo Reparado)
                    if entregado:
                        t_medio, c_medio, anim_medio = ("ENTREGADA EN TIEMPO", "#22c55e", "dot-green") if f_real_dt <= f_promesa_dt else ("ENTREGADA CON RETRASO", "#ef4444", "dot-red")
                    elif not tiene_guia:
                        t_medio, c_medio, anim_medio = "PROCESANDO GUÍA", "#374151", "dot-gray"
                    else:
                        if pd.notna(f_promesa_dt) and f_promesa_dt < hoy:
                            t_medio, c_medio, anim_medio = "RETRASO EN TRÁNSITO", "#f97316", "dot-orange"
                        else:
                            t_medio, c_medio, anim_medio = "EN TRÁNSITO", "#3b82f6", "dot-blue"
                    
                    # Nodo 4
                    t_fin, c_fin, anim_fin = ("ENTREGADO", "#22c55e", "dot-green") if entregado else ("EN ESPERA", "#374151", "dot-gray")

                    # Formateo de textos
                    txt_f_env = f_envio_dt.strftime('%d/%m/%Y') if pd.notna(f_envio_dt) else "S/D"
                    txt_f_pro = f_promesa_dt.strftime('%d/%m/%Y') if pd.notna(f_promesa_dt) else "S/D"
                    txt_f_rea = f_real_dt.strftime('%d/%m/%Y') if entregado else "PENDIENTE"
                    
                    # --- RENDER TIMELINE (UNA SOLA LÍNEA) ---
                    html_timeline = f'<div style="background:#111827;padding:25px;border-radius:12px;border:1px solid #374151;margin-top:15px;margin-bottom:20px;"><div style="display:flex;justify-content:space-between;align-items:flex-start;position:relative;width:100%;"><div style="position:absolute;top:20px;left:10%;right:10%;height:6px;background:#374151;z-index:0;"></div><div style="text-align:center;z-index:1;width:25%;"><div class="dot-green" style="width:40px;height:40px;background:#22c55e;margin:0 auto 10px auto;border:4px solid #111827;"></div><div style="color:white;font-size:11px;font-weight:bold;">SALIDA</div><div style="color:gray;font-size:12px;">{txt_f_env}</div></div><div style="text-align:center;z-index:1;width:25%;"><div class="{anim_env}" style="width:40px;height:40px;background:{c_env};margin:0 auto 10px auto;border:4px solid #111827;"></div><div style="color:white;font-size:11px;font-weight:bold;">{t_env}</div><div style="color:gray;font-size:12px;">&nbsp;</div></div><div style="text-align:center;z-index:1;width:25%;"><div class="{anim_medio}" style="width:40px;height:40px;background:{c_medio};margin:0 auto 10px auto;border:4px solid #111827;"></div><div style="color:white;font-size:11px;font-weight:bold;">{t_medio}</div><div style="color:gray;font-size:12px;">PROMESA: {txt_f_pro}</div></div><div style="text-align:center;z-index:1;width:25%;"><div class="{anim_fin}" style="width:40px;height:40px;background:{c_fin};margin:0 auto 10px auto;border:4px solid #111827;"></div><div style="color:white;font-size:11px;font-weight:bold;">{t_fin}</div><div style="color:gray;font-size:12px;">{txt_f_rea}</div></div></div></div>'
                    st.markdown(html_timeline, unsafe_allow_html=True)
                    
                    # --- TARJETAS ELITE ---
                    c1, c2, c3 = st.columns(3)
                    h_size = "360px"
                    with c1:
                        costo = f"${float(row.get('COSTO DE LA GUÍA', 0)):,.2f}"
                        html_c1 = f"<div class='elite-card' style='background:#11141C;padding:24px;border-radius:20px;border:1px solid rgba(255,255,255,0.08);border-top:4px solid #38bdf8;min-height:{h_size};'><div style='display:flex;align-items:center;margin-bottom:15px;'><div style='background:#38bdf822;padding:10px;border-radius:12px;margin-right:15px;'>📦</div><div style='color:white;font-weight:800;font-size:14px;'>DATOS DEL CLIENTE</div></div><div style='display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Tracking</span><span style='color:#38bdf8;font-size:13px;font-weight:800;'>{row.get('NÚMERO DE GUÍA','—')}</span></div><div style='display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Cliente</span><span style='color:#e2e8f0;font-size:13px;'>{row.get('NOMBRE DEL CLIENTE','—')}</span></div><div style='display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Destino</span><span style='color:#e2e8f0;font-size:13px;'>{row.get('DESTINO','—')}</span></div><div style='display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Fletera</span><span style='color:#fbbf24;font-size:13px;font-weight:700;'>{row.get('FLETERA','—')}</span></div><div style='margin-top:auto;text-align:right;'><div style='color:#64748b;font-size:12px;font-weight:800;'>Costo Guia</div><div style='color:#00FFAA;font-size:26px;font-weight:900;'>{costo}</div></div></div>"
                        st.markdown(html_c1, unsafe_allow_html=True)
                    with c2:
                        retraso_v = row.get('DIAS_RETRASO', 0)
                        color_t = "#fb7185" if retraso_v > 0 else "#00FFAA"
                        html_c2 = f"<div class='elite-card' style='background:#11141C;padding:24px;border-radius:20px;border:1px solid rgba(255,255,255,0.08);border-top:4px solid #fbbf24;min-height:{h_size};'><div style='display:flex;align-items:center;margin-bottom:15px;'><div style='background:#fbbf2422;padding:10px;border-radius:12px;margin-right:15px;'>⏱️</div><div style='color:white;font-weight:800;font-size:14px;'>TIEMPOS</div></div><div style='display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Fecha de Envio</span><span style='color:#e2e8f0;font-size:13px;'>{txt_f_env}</span></div><div style='display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Promesa</span><span style='color:#e2e8f0;font-size:13px;'>{txt_f_pro}</span></div><div style='display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Entrega Real</span><span style='color:#00FFAA;font-size:13px;'>{txt_f_rea}</span></div><div style='margin-top:auto;background:rgba(255,255,255,0.03);padding:15px;border-radius:12px;border-left:4px solid {color_t};'><div style='color:{color_t};font-size:10px;font-weight:800;'>DESVIACIÓN</div><div style='color:white;font-size:22px;font-weight:900;'>{retraso_v} DÍAS</div></div></div>"
                        st.markdown(html_c2, unsafe_allow_html=True)
                    with c3:
                        est_v = row.get('ESTATUS_CALCULADO', '—')
                        color_e = "#00FFAA" if est_v == "ENTREGADO" else "#fb7185" if est_v == "RETRASADO" else "#3b82f6"
                        html_c3 = f"<div class='elite-card' style='background:#11141C;padding:24px;border-radius:20px;border:1px solid rgba(255,255,255,0.08);border-top:4px solid #a855f7;min-height:{h_size};'><div style='display:flex;align-items:center;margin-bottom:15px;'><div style='background:#a855f722;padding:10px;border-radius:12px;margin-right:15px;'>📊</div><div style='color:white;font-weight:800;font-size:14px;'>ESTATUS</div></div><div style='display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Estatus</span><span style='color:{color_e};font-size:13px;font-weight:800;'>{est_v}</span></div><div style='display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.03);'><span style='color:#64748b;font-size:14px;font-weight:700;text-transform:uppercase;'>Prioridad</span><span style='color:#e2e8f0;font-size:13px;'>{row.get('PRIORIDAD','NORMAL')}</span></div><div style='margin-top:auto;'><div style='color:#64748b;font-size:14px;font-weight:700;margin-bottom:8px;'>NOTAS</div><div style='background:rgba(0,0,0,0.3);padding:12px;border-radius:10px;border:1px dashed rgba(255,255,255,0.1);color:#cbd5e1;font-size:12px;min-height:90px;'>{row.get('COMENTARIOS','Sin incidencias.')}</div></div></div>"
                        st.markdown(html_c3, unsafe_allow_html=True)
        
              
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        # --- 1. CÁLCULO DE MÉTRICAS ---
        st.markdown("<style>.elite-card{transition:all 0.4s ease;padding:20px;border-radius:20px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);text-align:center;margin-bottom:10px;}.elite-card:hover{transform:translateY(-8px);box-shadow:0 20px 40px rgba(0,0,0,0.7)!important;border:1px solid rgba(255,255,255,0.25)!important;}</style>", unsafe_allow_html=True)
        
        total = int(len(df_filtrado))
        entregados = int((df_filtrado["ESTATUS_CALCULADO"] == "ENTREGADO").sum())
        en_transito = int((df_filtrado["ESTATUS_CALCULADO"] == "EN TRANSITO").sum())
        retrasados = int((df_filtrado["ESTATUS_CALCULADO"] == "RETRASADO").sum())

        # --- 2. COLORES ---
        COLOR_AVANCE_ENTREGADOS = "#00FFAA" 
        COLOR_AVANCE_TRANSITO   = "#38bdf8" 
        COLOR_AVANCE_RETRASADOS = "#fb7185" 
        COLOR_TOTAL             = "#fbbf24" 
        COLOR_FALTANTE          = "#262730" 

        # --- 3. FUNCIÓN CORREGIDA (Sintaxis simplificada para evitar el TypeError) ---
        def donut_con_numero(avance, total_val, color_avance, color_faltante):
            porcentaje = int((avance / total_val) * 100) if total_val > 0 else 0
            
            # DataFrame con tipos de datos limpios
            data_dona = pd.DataFrame({
                "segmento": ["A", "B"], 
                "valor": [float(avance), float(max(total_val - avance, 0))]
            })
            
            # 1. El arco (Dona) con sintaxis explícita
            donut = alt.Chart(data_dona).mark_arc(innerRadius=52, outerRadius=65, cornerRadius=10).encode(
                theta=alt.Theta(field="valor", type="quantitative"),
                color=alt.Color(field="segmento", type="nominal", 
                                scale=alt.Scale(domain=["A", "B"], range=[color_avance, color_faltante]), 
                                legend=None),
                tooltip=alt.value(None) # Forma segura de desactivar tooltip
            )
            
            # 2. Número central
            texto_n = alt.Chart(pd.DataFrame({"t": [str(avance)]})).mark_text(
                align="center", baseline="middle", fontSize=28, fontWeight=800, dy=-6, color="white"
            ).encode(text=alt.Text(field="t", type="nominal"))
            
            # 3. Porcentaje inferior
            texto_p = alt.Chart(pd.DataFrame({"t": [f"{porcentaje}%"]})).mark_text(
                align="center", baseline="middle", fontSize=12, fontWeight=400, dy=18, color="#94a3b8"
            ).encode(text=alt.Text(field="t", type="nominal"))
            
            return (donut + texto_n + texto_p).properties(width=180, height=180).configure_view(strokeOpacity=0)

        # --- 4. RENDERIZADO DE COLUMNAS ---
        st.markdown("<div style='background:rgba(255,255,255,0.02);padding:15px;border-radius:15px;border-left:5px solid #38bdf8;margin-bottom:25px;'><span style='color:white;font-size:16px;font-weight:800;letter-spacing:1.5px;'>CONSOLA GLOBAL DE RENDIMIENTO</span></div>", unsafe_allow_html=True)
    
        c1, c2, c3, c4 = st.columns(4)
        l_style = "color:##e2e8f0;font-size:14px;font-weight:800;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;"

        with c1:
            st.markdown(f"<div class='elite-card'><p style='{l_style}'>Total Pedidos</p>", unsafe_allow_html=True)
            st.altair_chart(donut_con_numero(total, total, COLOR_TOTAL, COLOR_FALTANTE), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
        with c2:
            st.markdown(f"<div class='elite-card'><p style='{l_style}'>Entregados</p>", unsafe_allow_html=True)
            st.altair_chart(donut_con_numero(entregados, total, COLOR_AVANCE_ENTREGADOS, COLOR_FALTANTE), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
        with c3:
            st.markdown(f"<div class='elite-card'><p style='{l_style}'>En Tránsito en tiempo</p>", unsafe_allow_html=True)
            st.altair_chart(donut_con_numero(en_transito, total, COLOR_AVANCE_TRANSITO, COLOR_FALTANTE), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
        with c4:
            st.markdown(f"<div class='elite-card'><p style='{l_style}'>En Tránsito con retraso</p>", unsafe_allow_html=True)
            st.altair_chart(donut_con_numero(retrasados, total, COLOR_AVANCE_RETRASADOS, COLOR_FALTANTE), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # --------------------------------------------------
        # TABLA DE ENVÍOS – DISEÑO PREMIUM ELITE (SIN CAJA)
        # --------------------------------------------------
        # Espaciador para separar de las donas
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.divider() 
        # Estructura de 3 columnas para centrado perfecto
        col_izq, col_centro, col_der = st.columns([2, 3, 2])
        
        with col_izq:
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if st.button("BD Completa", use_container_width=True, key="btn_full_v3"):
                    st.session_state.tabla_expandida = True
                    st.rerun()
            with btn_c2:
                if st.button("BD Vista Normal", use_container_width=True, key="btn_norm_v3"):
                    st.session_state.tabla_expandida = False
                    st.rerun()
        
        with col_centro:
            # Título con padding-bottom para empujar la tabla hacia abajo
            st.markdown("""
                <div style="text-align:center; padding-bottom: 25px;">
                    <span style="color:white; font-size:24px; font-weight:800; letter-spacing:3px; text-transform:uppercase;">
                        REGISTRO DE ENVIOS
                    </span>
                </div>
            """, unsafe_allow_html=True)

        with col_der:
            # Columna de equilibrio
            st.write("")
        
        # Lógica de altura dinámica
        h_dinamica = 850 if st.session_state.get('tabla_expandida', False) else 400
        
        # Preparación de datos final
        df_visual = df_filtrado.copy()
        hoy_t = pd.Timestamp.today().normalize()
        
        # Cálculos de tiempo para las barras de progreso y métricas
        df_visual["DIAS_TRANSCURRIDOS"] = ((df_visual["FECHA DE ENTREGA REAL"].fillna(hoy_t) - df_visual["FECHA DE ENVÍO"]).dt.days)
        df_visual["DIAS_RETRASO_VAL"] = ((df_visual["FECHA DE ENTREGA REAL"].fillna(hoy_t) - df_visual["PROMESA DE ENTREGA"]).dt.days).clip(lower=0)
        
        
        # --- FILTROS DE CUBIERTA (ENCIMA DE LA TABLA) ---
        st.markdown("""
        <style>
        /* Tamaño y color del texto dentro del selector (Cerrado) */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            font-size: 12px !important; /* <--- AJUSTE EL TAMAÑO AQUÍ */
            color: #D1D5DB !important;  /* Color Verde Neón */
            font-weight: 500 !important;
            text-transform: uppercase !important;
        }

        /* Tamaño y color de las opciones en la lista (Abierta) */
        div[data-baseweb="popover"] li {
            font-size: 13px !important;
            color: #e2e8f0 !important; /* Gris claro para las opciones */
            background-color: #111827 !important;
        }

        /* Color cuando pasas el ratón sobre una opción (Hover) */
        div[data-baseweb="popover"] li:hover {
            background-color: rgba(0, 255, 170, 0.2) !important;
            color: #00FFAA !important;
        }
        
        /* Ajuste del título (Label) del selector */
        div[data-testid="stSelectbox"] label p {
            font-size: 13px !important;
            color: #FFFFFF !important; /* Azul para los títulos de los filtros */
            letter-spacing: 1px !important;
            font-weight: 700 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        c_f1, c_f2, c_f3, c_f4 = st.columns(4)

        with c_f1:
            # Seleccionamos uno a la vez y se cierra solo
            f_cli = st.selectbox("No. Cliente", options=["---TODOS---"] + sorted(df_visual["NO CLIENTE"].unique()), key="f_cli_tab")
        with c_f2:
            f_flet = st.selectbox("Fletera", options=["---TODAS---"] + sorted(df_visual["FLETERA"].unique()), key="f_flet_tab")
        with c_f3:
            f_dest = st.selectbox("Destino", options=["---TODOS---"] + sorted(df_visual["DESTINO"].unique()), key="f_dest_tab")
        with c_f4:
            f_est = st.selectbox("Estatus", options=["---TODOS---"] + sorted(df_visual["ESTATUS_CALCULADO"].unique()), key="f_est_tab")

        if f_cli != "---TODOS---":
            df_visual = df_visual[df_visual["NO CLIENTE"] == f_cli]
            
        if f_flet != "---TODAS---":
            df_visual = df_visual[df_visual["FLETERA"] == f_flet]
            
        if f_dest != "---TODOS---":
            df_visual = df_visual[df_visual["DESTINO"] == f_dest]
            
        if f_est != "---TODOS---":
            df_visual = df_visual[df_visual["ESTATUS_CALCULADO"] == f_est]
        
        # --- 1. REORDENAMIENTO FÍSICO (Siguiendo su orden exacto) ---
        orden_capitan = [
            "NO CLIENTE", 
            "NÚMERO DE PEDIDO", 
            "FECHA DE ENVÍO", 
            "PROMESA DE ENTREGA", 
            "FECHA DE ENTREGA REAL", 
            "DIAS_TRANSCURRIDOS", 
            "DIAS_RETRASO_VAL", 
            "DESTINO", 
            "FLETERA", 
            "NÚMERO DE GUÍA", 
            "COSTO DE LA GUÍA", 
            "CANTIDAD DE CAJAS", 
            "NOMBRE DEL CLIENTE", 
            "COMENTARIOS",
            "ESTATUS_CALCULADO" # La dejamos al final como cierre de fila
        ]
        
        # Aplicamos el filtro de seguridad por si alguna columna no existe en el CSV
        df_visual = df_visual[[c for c in orden_capitan if c in df_visual.columns]]
        
        # --- 2. RENDERIZADO CON CONFIGURACIÓN DE COLUMNAS ---
        st.dataframe(
            df_visual,
            column_config={
                "NO CLIENTE": st.column_config.TextColumn("NO. CLIENTE"),
                "NÚMERO DE PEDIDO": st.column_config.TextColumn("PEDIDO"),
                "FECHA DE ENVÍO": st.column_config.DateColumn("FECHA ENVÍO", format="DD/MM/YYYY"),
                "PROMESA DE ENTREGA": st.column_config.DateColumn("PROMESA", format="DD/MM/YYYY"),
                "FECHA DE ENTREGA REAL": st.column_config.DateColumn("ENTREGA REAL", format="DD/MM/YYYY"),
                "DIAS_TRANSCURRIDOS": st.column_config.NumberColumn("DIAS TRANSCURRIDOS", format="%d d"),
                "DIAS_RETRASO_VAL": st.column_config.ProgressColumn(
                    "RETRASO",
                    format="%d d",
                    min_value=0,
                    max_value=15,
                    color="red",
                ),
                "DESTINO": st.column_config.TextColumn("DESTINO"),
                "FLETERA": st.column_config.TextColumn("FLETERA"),
                "NÚMERO DE GUÍA": st.column_config.TextColumn("GUÍA"),
                "COSTO DE LA GUÍA": st.column_config.NumberColumn("COSTO", format="$ %.2f"),
                "CANTIDAD DE CAJAS": st.column_config.NumberColumn("CAJAS", format=""),
                "NOMBRE DEL CLIENTE": st.column_config.TextColumn("👤 CLIENTE"),
                "COMENTARIOS": st.column_config.TextColumn("ULTIMO MOVIMIENTO"),
                "ESTATUS_CALCULADO": st.column_config.SelectboxColumn(
                    "ESTATUS",
                    options=["ENTREGADO", "EN TRANSITO", "RETRASADO"],
                    required=True,
                )
            },
            hide_index=True,
            use_container_width=True,
            height=h_dinamica
        )
        
        st.divider()
        # --------------------------------------------------
        # GRÁFICOS DE BARRAS POR PAQUETERÍA (RESPONSIVE)
        # --------------------------------------------------
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.02); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-top: 30px; margin-bottom: 25px;'>
                <span style='color: #e2e8f0; font-weight: 700; font-size: 15px; letter-spacing: 1.5px;'>🚀 ESTADO DE CARGA EN TIEMPO REAL</span>
            </div>
        """, unsafe_allow_html=True)
        
        color_transito = "#fbbf24" 
        color_retraso = "#fb7185"  
        
        col1, col2 = st.columns(2)
        
        # --- COLUMNA 1: EN TRÁNSITO ---
        with col1:
            df_t = df_filtrado[df_filtrado["ESTATUS_CALCULADO"] == "EN TRANSITO"].groupby("FLETERA").size().reset_index(name="CANTIDAD")
            total_t = df_t["CANTIDAD"].sum()
            
            st.markdown(f"""
                <div style='background: linear-gradient(90deg, rgba(251, 191, 36, 0.1) 0%, transparent 100%); padding: 15px; border-radius: 10px; border-bottom: 2px solid {color_transito}33;'>
                    <p style='margin:0; color:{color_transito}; font-size:12px; font-weight:800; text-transform:uppercase;'>🟡 En Movimiento</p>
                    <h2 style='margin:0; color:white; font-size:32px;'>{total_t} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                </div>
            """, unsafe_allow_html=True)
        
            if not df_t.empty:
                # ALTURA DINÁMICA: 40px por fletera + 50px de base para que no se encimen
                dinamic_height_t = len(df_t) * 40 + 50
                
                base_t = alt.Chart(df_t).encode(
                    x=alt.X("CANTIDAD:Q", title=None, axis=None),
                    y=alt.Y("FLETERA:N", title=None, sort='-x', 
                            axis=alt.Axis(labelColor='white', labelFontSize=12, labelLimit=200))
                )
                
                bars_t = base_t.mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5, size=20, color=color_transito)
                text_t = base_t.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700, fontSize=13).encode(text="CANTIDAD:Q")
                
                chart_t = (bars_t + text_t).properties(
                    height=dinamic_height_t
                ).configure_view(
                    strokeOpacity=0
                ).configure_axis(
                    grid=False
                )
                
                st.altair_chart(chart_t, use_container_width=True)
            else:
                st.markdown(f"<div style='padding:40px; text-align:center; color:#475569;'>Sin carga activa</div>", unsafe_allow_html=True)
        
        # --- COLUMNA 2: RETRASADOS ---
        with col2:
            df_r = df_filtrado[df_filtrado["ESTATUS_CALCULADO"] == "RETRASADO"].groupby("FLETERA").size().reset_index(name="CANTIDAD")
            total_r = df_r["CANTIDAD"].sum()
            
            st.markdown(f"""
                <div style='background: linear-gradient(90deg, rgba(251, 113, 133, 0.1) 0%, transparent 100%); padding: 15px; border-radius: 10px; border-bottom: 2px solid {color_retraso}33;'>
                    <p style='margin:0; color:{color_retraso}; font-size:12px; font-weight:800; text-transform:uppercase;'>🔴 Alerta de Retraso</p>
                    <h2 style='margin:0; color:white; font-size:32px;'>{total_r} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                </div>
            """, unsafe_allow_html=True)
        
            if not df_r.empty:
                # ALTURA DINÁMICA: Evita que las barras se encimen si hay muchas fleteras
                dinamic_height_r = len(df_r) * 40 + 50
                
                base_r = alt.Chart(df_r).encode(
                    x=alt.X("CANTIDAD:Q", title=None, axis=None),
                    y=alt.Y("FLETERA:N", title=None, sort='-x', 
                            axis=alt.Axis(labelColor='white', labelFontSize=12, labelLimit=200))
                )
                
                bars_r = base_r.mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5, size=20, color=color_retraso)
                text_r = base_r.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700, fontSize=13).encode(text="CANTIDAD:Q")
                
                chart_r = (bars_r + text_r).properties(
                    height=dinamic_height_r
                ).configure_view(
                    strokeOpacity=0
                ).configure_axis(
                    grid=False
                )
                
                st.altair_chart(chart_r, use_container_width=True)
            else:
                st.markdown(f"<div style='padding:40px; text-align:center; color:#059669; font-weight:bold;'>✓ Operación al día</div>", unsafe_allow_html=True)
               
        # --------------------------------------------------
        # SECCIÓN UNIFICADA: ANÁLISIS DE EXPERIENCIA (LUPA)
        # --------------------------------------------------
        
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.02); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #00FFAA; margin-top: 30px; margin-bottom: 20px;'>
                <span style='color: #e2e8f0; font-weight: 700; font-size: 15px; letter-spacing: 1.5px;'>Cumplimiento de tiempos de transito, precisión y calidad del servicio.</span>
            </div>
        """, unsafe_allow_html=True)
        
        # 1. Definición de colores (Esto evita el NameError)
        color_perfecto = "#48C9B0"    # Verde
        color_con_fallo = "#ef4444"   # Rojo
        
        # 2. Selector Elite
        lista_fleteras = ["TODAS"] + sorted(df_filtrado["FLETERA"].unique().tolist())
        fletera_seleccionada = st.selectbox("Filtrar por Paquetería:", lista_fleteras, key="lupa_selector")
        
        # 3. Procesamiento
        df_lupa = df_filtrado[df_filtrado["FECHA DE ENTREGA REAL"].notna()].copy()
        if fletera_seleccionada != "TODAS":
            df_lupa = df_lupa[df_lupa["FLETERA"] == fletera_seleccionada]
        
        # Asegurar que las fechas sean datetime y calcular diferencia
        df_lupa["DIAS_DIF"] = (pd.to_datetime(df_lupa["FECHA DE ENTREGA REAL"]) - 
                               pd.to_datetime(df_lupa["PROMESA DE ENTREGA"])).dt.days
        
        if not df_lupa.empty:
            df_dist_lupa = df_lupa.groupby("DIAS_DIF").size().reset_index(name="PEDIDOS")
            
            # Aquí se usan las variables definidas arriba
            df_dist_lupa["COLOR_HEX"] = df_dist_lupa["DIAS_DIF"].apply(
                lambda x: color_perfecto if x <= 0 else color_con_fallo
            )
        
            # 4. Gráfico de Histograma Técnico RESPONSIVE
            base_lupa = alt.Chart(df_dist_lupa).encode(
                x=alt.X("DIAS_DIF:O", 
                        title="Días vs Promesa (← Antes | Retraso →)", 
                        axis=alt.Axis(labelAngle=0, labelColor='#94a3b8', labelOverlap='parity')),
                y=alt.Y("PEDIDOS:Q", title=None, axis=alt.Axis(gridOpacity=0.05, labelColor='#94a3b8', format='~s')),
                color=alt.Color("COLOR_HEX:N", scale=None) # scale=None permite usar los hex directamente
            )
        
            bars_lupa = base_lupa.mark_bar(
                cornerRadiusTopLeft=6, 
                cornerRadiusTopRight=6
            )
        
            text_lupa = base_lupa.mark_text(
                align='center', baseline='bottom', dy=-8, fontWeight=700, color='white', fontSize=12
            ).encode(text=alt.Text("PEDIDOS:Q", format='~s'))
        
            st.altair_chart((bars_lupa + text_lupa).properties(height=350).configure_view(strokeOpacity=0), use_container_width=True)
        
            st.markdown(f"""
                <div style='background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); padding: 15px; border-radius: 10px;'>
                    <p style='margin:0; color:#38bdf8; font-size:13px; font-weight:600;'>💡 TIP DE OPERACIONES:</p>
                    <p style='margin:5px 0 0 0; color:#e2e8f0; font-size:14px;'>
                        Las barras a la derecha del '0' representan promesas incumplidas. 
                        Busca reducir la dispersión hacia el lado rojo para mejorar la lealtad del cliente.
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Sin registros de entrega para los filtros seleccionados.")
        
        # ----------------------------------------------------------
        # GRÁFICO EXCLUSIVO: RETRASO PROMEDIO (DÍAS) + NOTA
        # ----------------------------------------------------------
        verde_esmeralda = "#48C9B0"
        naranja_ambar = "#d97706"
        rojo_coral = "#fb7185"

        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.02); padding: 12px 20px; border-radius: 8px; border-left: 4px solid {rojo_coral}; margin-bottom: 20px;'>
                <span style='color: #e2e8f0; font-weight: 700; font-size: 15px; letter-spacing: 1.5px;'>Retrasos en tiempo real</span>
            </div>
        """, unsafe_allow_html=True)

        # 1. Preparar el DataFrame de análisis
        df_analisis_real = df_filtrado.copy()
        
        # Asegurar que las columnas sean datetime (crucial para el cálculo)
        df_analisis_real["PROMESA DE ENTREGA"] = pd.to_datetime(df_analisis_real["PROMESA DE ENTREGA"])
        df_analisis_real["FECHA DE ENTREGA REAL"] = pd.to_datetime(df_analisis_real["FECHA DE ENTREGA REAL"])
        
        # Obtener fecha de hoy para el cálculo de pendientes
        hoy_dt = pd.Timestamp.now().normalize()

        # 2. Lógica Maestra: Si es nulo, usamos hoy. Si no, usamos la fecha real.
        def calcular_dias_reales(row):
            meta = row["PROMESA DE ENTREGA"]
            final = row["FECHA DE ENTREGA REAL"]
            
            if pd.isna(final):
                # Pedido sigue en tránsito: comparamos contra hoy
                desviacion = (hoy_dt - meta).days
            else:
                # Pedido entregado: comparamos contra su entrega
                desviacion = (final - meta).days
            return desviacion

        df_analisis_real["DIAS_DESVIACION"] = df_analisis_real.apply(calcular_dias_reales, axis=1)

        # 3. Agrupamos por Fletera
        df_prom = df_analisis_real.groupby("FLETERA")["DIAS_DESVIACION"].mean().reset_index(name="PROMEDIO")
        
        if not df_prom.empty:
            # Asignación de colores dinámica
            # <= 0: Verde (A tiempo), 1-2: Naranja (Alerta), >2: Rojo (Crítico)
            def asignar_color(x):
                if x <= 0: return verde_esmeralda
                elif x <= 2: return naranja_ambar
                else: return rojo_coral
            
            df_prom["COLOR_HEX"] = df_prom["PROMEDIO"].apply(asignar_color)

            # --- GRÁFICO ALTAIR ---
            bars = alt.Chart(df_prom).mark_bar(
                cornerRadiusTopRight=10, 
                cornerRadiusBottomRight=10,
                size=22
            ).encode(
                y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='white', labelFontSize=12)),
                x=alt.X("PROMEDIO:Q", title="Días de Desviación (Promedio)", axis=alt.Axis(gridOpacity=0.05, labelColor='#94a3b8')),
                color=alt.Color("COLOR_HEX:N", scale=None)
            )
            
            text_labels = bars.mark_text(
                align='left', baseline='middle', dx=10, fontSize=14, fontWeight=700, color='white'
            ).encode(text=alt.Text("PROMEDIO:Q", format='.1f'))
            
            st.altair_chart((bars + text_labels).properties(height=400).configure_view(strokeOpacity=0), use_container_width=True)

            # --- DIAGNÓSTICO ELITE ---
            peor_fletera = df_prom.sort_values(by="PROMEDIO", ascending=False).iloc[0]
            fecha_actual = datetime.date.today().strftime('%d/%m/%Y')
            
            if peor_fletera["PROMEDIO"] > 0:
                st.markdown(f"""
                    <div style='background: rgba(251, 113, 133, 0.1); border: 1px solid {rojo_coral}; padding: 20px; border-radius: 12px; margin-top: 20px;'>
                        <p style='margin:0; color:{rojo_coral}; font-weight:800; font-size:14px; text-transform:uppercase;'>🔍 Diagnóstico de Emergencia al {fecha_actual}</p>
                        <p style='margin:10px 0 0 0; color:white; font-size:16px;'>
                            Atención: <b>{peor_fletera['FLETERA']}</b> presenta la mayor desviación crítica. 
                            Considerando pedidos en tránsito, el retraso promedio es de <span style='color:{rojo_coral}; font-weight:bold;'>{peor_fletera['PROMEDIO']:.1f} días</span>.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
    
        # --------------------------------------------------
        # RANKING DE CALIDAD: MEJOR A PEOR FLETERA
        # --------------------------------------------------
        
        # Estética de colores de la central de monitoreo
        color_perfecto = "#059669"  # Esmeralda (Cero fallos)
        color_con_fallo = "#fb7185" # Coral/Rojo (Con retrasos)
        
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.02); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #00FFAA; margin-top: 30px; margin-bottom: 20px;'>
                <span style='color: #e2e8f0; font-weight: 700; font-size: 15px; letter-spacing: 1.5px;'>Total de Entregas con retraso</span>
            </div>
        """, unsafe_allow_html=True)
        
        # 1. Procesamiento de incidencias
        df_entregas_tarde = df_filtrado[
            (df_filtrado["FECHA DE ENTREGA REAL"].notna()) & 
            (df_filtrado["FECHA DE ENTREGA REAL"] > df_filtrado["PROMESA DE ENTREGA"])
        ].copy()
        
        df_ranking = df_entregas_tarde.groupby("FLETERA").size().reset_index(name="FALLOS")
        todas_f = pd.DataFrame(df_filtrado["FLETERA"].unique(), columns=["FLETERA"])
        df_rk = pd.merge(todas_f, df_ranking, on="FLETERA", how="left").fillna(0)
        
        if not df_rk.empty:
            df_rk["COLOR_HEX"] = df_rk["FALLOS"].apply(lambda x: color_perfecto if x == 0 else color_con_fallo)
        
            # 2. Gráfico Vertical Premium RESPONSIVE
            chart_base = alt.Chart(df_rk).encode(
                x=alt.X("FLETERA:N", 
                        title=None, 
                        sort='y', 
                        scale=alt.Scale(paddingInner=0.2), # Espaciado dinámico
                        axis=alt.Axis(
                            labelAngle=-90, # <--- Títulos Verticales para Móvil
                            labelColor='white', 
                            labelFontSize=11,
                            labelOverlap='parity'
                        )),
                y=alt.Y("FALLOS:Q", title=None, axis=alt.Axis(gridOpacity=0.05, labelColor='#94a3b8', format='d')),
                color=alt.Color("COLOR_HEX:N", scale=None)
            )
        
            bars = chart_base.mark_bar(
                cornerRadiusTopLeft=10, 
                cornerRadiusTopRight=10
                # Eliminamos 'size' fijo para que sea responsivo
            )
        
            labels = chart_base.mark_text(
                align='center', baseline='bottom', dy=-10, fontSize=14, fontWeight=700, color='white'
            ).encode(text=alt.Text("FALLOS:Q", format='d'))
        
            st.altair_chart((bars + labels).properties(height=450).configure_view(strokeOpacity=0), use_container_width=True)
            
            st.markdown(f"""
                <p style='text-align:center; color:#94a3b8; font-size:12px; font-style:italic;'>
                    <span style='color:{color_perfecto};'>●</span> <b>Cero Incidencias</b> | 
                    <span style='color:{color_con_fallo};'>●</span> <b>Con Pedidos Tarde</b> <br>
                    Las fleteras a la izquierda son las de mayor confianza operativa.
                </p>
            """, unsafe_allow_html=True)
        else:
            st.info("No se detectaron entregas fuera de tiempo en el periodo actual.")
                
        

        # =========================================================
        # --- BLOQUE 2: LEAD TIME (ESTILO UNIFICADO) ---
        # =========================================================
        
        # 1. Definición de colores y variables necesarias
        verde_esmeralda_elec = "#48C9B0"
        
        with st.container():
            # Título con el mismo diseño que el gráfico superior
            st.markdown(f"""
                <div style='background: rgba(255,255,255,0.02); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #48C9B0; margin-top: 30px; margin-bottom: 20px;'>
                    <span style='color: #e2e8f0; font-weight: 700; font-size: 15px; letter-spacing: 1.5px;'>Días Promedio de Entrega, capacidad y velocidad (Lead Time)</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Procesamiento de datos (usando df_filtrado para consistencia)
            df_lt = df_filtrado.copy()
            
            # Asegurar formato fecha (importante para evitar errores de cálculo)
            df_lt['FECHA DE entrega real'] = pd.to_datetime(df_lt['FECHA DE ENTREGA REAL'], errors='coerce')
            df_lt['FECHA DE ENVÍO'] = pd.to_datetime(df_lt['FECHA DE ENVÍO'], errors='coerce')
        
            # Filtrar solo los que tienen ambas fechas
            df_entregados = df_lt[df_lt['FECHA DE ENTREGA REAL'].notna() & df_lt['FECHA DE ENVÍO'].notna()].copy()
            
            if not df_entregados.empty:
                # Calcular Lead Time
                df_entregados['LEAD_TIME'] = (df_entregados['FECHA DE ENTREGA REAL'] - df_entregados['FECHA DE ENVÍO']).dt.days
                
                # Agrupar por fletera
                lead_data = df_entregados.groupby('FLETERA')['LEAD_TIME'].mean().reset_index()
                
                # Capa de Barras
                bars_lead = alt.Chart(lead_data).mark_bar(
                    cornerRadiusTopRight=10,
                    cornerRadiusBottomRight=10,
                    size=25
                ).encode(
                    x=alt.X('LEAD_TIME:Q', title="Días promedio en Tránsito"),
                    y=alt.Y('FLETERA:N', sort='x', title=None),
                    color=alt.value(verde_esmeralda_elec)
                )
            
                # Capa de Etiquetas (Texto sobre las barras)
                text_lead = bars_lead.mark_text(
                    align='left', baseline='middle', dx=8,
                    color='white', fontSize=13, fontWeight='bold'
                ).encode(
                    text=alt.Text('LEAD_TIME:Q', format='.1f')
                )
            
                # Renderizado del gráfico
                st.altair_chart((bars_lead + text_lead).properties(height=400), use_container_width=True)
                
                # Tip informativo inferior
                st.markdown(f"""
                    <div style='background: rgba(0, 255, 170, 0.05); border: 1px solid rgba(0, 255, 170, 0.2); padding: 15px; border-radius: 10px;'>
                        <p style='margin:0; color:#00FFAA; font-size:13px; font-weight:600;'>Definicion:</p>
                        <p style='margin:5px 0 0 0; color:#e2e8f0; font-size:14px;'>
                            Este gráfico muestra el tiempo real desde que el paquete sale del almacén hasta que llega al cliente. 
                            <b>Menor tiempo = Mayor satisfacción.</b>
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
            else:
                st.info("No hay datos suficientes de envío y entrega para calcular el Lead Time.")
        
        
        # --------------------------------------------------
        # TABLA SCORECARD: CALIFICACIÓN DE FLETERAS
        # --------------------------------------------------
        # --- 🏆 SCORECARD DE DESEMPEÑO LOGÍSTICO (INTEGRADO & DESPLEGABLE) ---
        
        # 1. Preparación de datos (Cálculos Pro)
        resumen_score = df_filtrado[df_filtrado["FECHA DE ENTREGA REAL"].notna()].copy()
        resumen_score["ES_TARDE"] = (resumen_score["FECHA DE ENTREGA REAL"] > resumen_score["PROMESA DE ENTREGA"])
        resumen_score["DIAS_DIF"] = (resumen_score["FECHA DE ENTREGA REAL"] - resumen_score["PROMESA DE ENTREGA"]).dt.days

        df_score = resumen_score.groupby("FLETERA").agg(
            Total_Entregas=('FLETERA', 'count'),
            Pedidos_Tarde=('ES_TARDE', 'sum'),
            Promedio_Dias=('DIAS_DIF', 'mean')
        ).reset_index()

        df_score["Eficiencia"] = ((1 - (df_score["Pedidos_Tarde"] / df_score["Total_Entregas"])) * 100).round(1)
        df_score = df_score.sort_values(by="Eficiencia", ascending=False)

        # # 2. CSS para el Botón Desplegable Ultra-Moderno
        st.markdown("""
        <style>
            /* Estilo para la cabecera del expander */
            .streamlit-expanderHeader {
                background-color: rgba(255, 255, 255, 0.03) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 12px !important;
                padding: 18px !important;
                color: #00FFAA !important;
                font-weight: 800 !important;
                transition: 0.3s all ease;
            }
        
            /* Efecto Hover */
            .streamlit-expanderHeader:hover {
                background-color: rgba(0, 255, 170, 0.05) !important;
                border: 1px solid #00FFAA !important;
            }
        
            /* Estilo para el contenido de adentro */
            .streamlit-expanderContent {
                border: none !important;
                background-color: transparent !important;
                padding-top: 20px !important;
            }
            
            /* Eliminar la línea predeterminada de Streamlit */
            .streamlit-expanderHeader + div {
                border: none !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # 3. El Botón y el Contenido
        with st.expander("🏆 CLASIFICACIÓN DE SOCIOS LOGÍSTICOS (SCORECARD)"):
            st.markdown("<p style='color: #94a3b8; font-size: 13px; margin-bottom: 25px; margin-left: 5px;'>Análisis profundo de rendimiento y cumplimiento de promesas de entrega.</p>", unsafe_allow_html=True)
            
            for _, row in df_score.iterrows():
                # Colores Dinámicos
                if row["Eficiencia"] >= 95:
                    s_color, s_bg, label = "#059669", "rgba(5, 150, 105, 0.1)", "⭐ EXCELENTE"
                elif row["Eficiencia"] >= 80:
                    s_color, s_bg, label = "#3b82f6", "rgba(59, 130, 246, 0.1)", "✅ CONFIABLE"
                elif row["Eficiencia"] >= 60:
                    s_color, s_bg, label = "#f59e0b", "rgba(245, 158, 11, 0.1)", "⚠️ OBSERVACIÓN"
                else:
                    s_color, s_bg, label = "#fb7185", "rgba(251, 113, 133, 0.1)", "🚨 CRÍTICO"

                # Render de Tarjeta Amazon Style
                st.markdown(f"""
                    <div style='background: {s_bg}; border: 1px solid {s_color}33; padding: 20px; border-radius: 15px; margin-bottom: 15px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div style='flex-grow: 1;'>
                                <h3 style='margin:0; color:white; font-size:18px; font-family:"Inter", sans-serif;'>{row['FLETERA']}</h3>
                                <span style='background: {s_color}; color: white; padding: 2px 10px; border-radius: 20px; font-size: 10px; font-weight: 800;'>{label}</span>
                            </div>
                            <div style='text-align: right; margin-right: 30px;'>
                                <p style='margin:0; color:#94a3b8; font-size:10px; text-transform:uppercase;'>Eficiencia</p>
                                <h2 style='margin:0; color:{s_color}; font-size:28px; font-weight:800;'>{row['Eficiencia']}%</h2>
                            </div>
                            <div style='text-align: right; min-width: 100px;'>
                                <p style='margin:0; color:#94a3b8; font-size:10px; text-transform:uppercase;'>Días Prom.</p>
                                <h2 style='margin:0; color:white; font-size:24px;'>{row['Promedio_Dias']:.1f}</h2>
                            </div>
                        </div>
                        <div style='width: 100%; height: 4px; background: rgba(255,255,255,0.05); margin-top: 15px; border-radius: 10px;'>
                            <div style='width: {row['Eficiencia']}%; height: 100%; background: {s_color}; border-radius: 10px; box-shadow: 0 0 10px {s_color}55;'></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        # --------------------------------------------------
        # FINAL DE PÁGINA FOOTER
        # --------------------------------------------------
                
        st.markdown("<div style='text-align:center; color:#475569; font-size:10px; margin-top:20px;'>LOGISTICS INTELLIGENCE UNIT - CONFIDENTIAL</div>", unsafe_allow_html=True)

    
    # ------------------------------------------------------------------
    # MAIN 2: SEGUIMIENTO
    # ------------------------------------------------------------------
    elif st.session_state.pagina == "KPIs":
        # 1. Fuerza el scroll hacia arriba
        st.markdown("<style>@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}</style>", unsafe_allow_html=True)
        # --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 0rem !important;
                    max-width: 95% !important;
                }
    
                .header-wrapper {
                    display: flex;
                    align-items: baseline;
                    gap: 12px;
                    font-family: 'Inter', sans-serif;
                }
    
                .header-wrapper h1 {
                    font-size: 22px !important;
                    font-weight: 800;
                    margin: 0;
                    color: #4b5563;
                    letter-spacing: -0.8px;
                }
    
                .header-wrapper span {
                    font-size: 14px;
                    font-weight: 300;
                    color: #ffffff;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
    
                div[data-testid="stPopover"] > button {
                    background-color: transparent !important;
                    border: 1px solid rgba(0, 255, 162, 0.3) !important;
                    padding: 2px 10px !important;
                    border-radius: 6px !important;
                    height: 32px !important;
                    transition: all 0.3s ease;
                }
    
                div[data-testid="stPopover"] > button:hover {
                    border: 1px solid #00ffa2 !important;
                    box-shadow: 0 0 10px rgba(0, 255, 162, 0.2);
                }
    
                div[data-testid="stPopoverContent"] button {
                    text-align: left !important;
                    justify-content: flex-start !important;
                    border: none !important;
                    background: transparent !important;
                    font-size: 13px !important;
                    padding: 8px 10px !important;
                }
    
                div[data-testid="stPopoverContent"] button:hover {
                    color: #00ffa2 !important;
                    background: rgba(0, 255, 162, 0.05) !important;
                }
            </style>
        """, unsafe_allow_html=True)
    
        # --- 2. POSICIONAMIENTO DEL ENCABEZADO ---
        c1, c2 = st.columns([0.88, 0.12], vertical_alignment="bottom")
    
        with c1:
            st.markdown("""
                <div class="header-wrapper">
                    <h1>SHIPMENT MONITORING</h1>
                    <span>& Delays</span>
                    <div style="font-family:'JetBrains Mono'; font-size:11px; color:#00ffa2; opacity:0.7;
                                margin-left:10px; padding-left:10px; border-left:1px solid #334155;">
                        LOGÍSTICA & RENDIMIENTO
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
        with c2:
            with st.popover("☰", use_container_width=True):
                st.markdown(
                    "<p style='color:#64748b; font-size:10px; font-weight:700; "
                    "margin-bottom:10px; letter-spacing:1px;'>NAVEGACIÓN</p>",
                    unsafe_allow_html=True
                )
    
                paginas = {
                    "TRACKING": ("principal", "kpi_btn_aac"),
                    "SEGUIMIENTO": ("KPIs", "kpi_btn_kpi"),
                    "REPORTE OPS": ("Reporte", "kpi_btn_rep"),
                    "HUB LOGISTIC": ("HubLogistico", "kpi_btn_hub"),
                    "OTD": ("RadarRastreo", "kpi_btn_radar")
                }
    
                for nombre, (v_state, v_key) in paginas.items():
                    if st.button(nombre, use_container_width=True, key=v_key):
                        st.session_state.pagina = v_state
                        st.rerun()
    
        # Línea divisoria
        st.markdown(
            "<hr style='margin:8px 0 20px 0; border:none; "
            "border-top:1px solid rgba(148,163,184,0.1);'>",
            unsafe_allow_html=True
        )
        # =========================================================
        # --- 1. FILTRO DE FECHAS EN LA SIDEBAR (CONTROL MAESTRO) ---
        # =========================================================
        with st.sidebar:
                       
            # Aseguramos que la columna sea datetime para el filtro
            df["FECHA DE ENVÍO"] = pd.to_datetime(df["FECHA DE ENVÍO"])
            
            # Definimos el rango mínimo y máximo basado en los datos
            f_inicio_default = df["FECHA DE ENVÍO"].min().date()
            f_fin_default = df["FECHA DE ENVÍO"].max().date()
            
            st.divider()
            
            # El filtro de calendario
            rango_fechas = st.date_input(
                "  Seleccionar Fecha:",
                value=(f_inicio_default, f_fin_default),
                min_value=f_inicio_default,
                max_value=f_fin_default,
                help="Todas las métricas y tablas mostrarán solo pedidos enviados en este rango."
            )
        
        
        # --- 1. CONFIGURACIÓN DE CRÉDENCIALES Y REPO ---
        TOKEN = st.secrets.get("GITHUB_TOKEN", None)
        REPO_NAME = "RH2026/dashboard-logistica"
        FILE_PATH = "tareas.csv"
        CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/tareas.csv"
        
        # --- 2. AJUSTE DE ZONA HORARIA MÉXICO ---
        def obtener_fecha_mexico():
            utc_ahora = datetime.datetime.now(datetime.timezone.utc)
            mexico_ahora = utc_ahora - datetime.timedelta(hours=6) 
            return mexico_ahora.date()
        
        # --- 3. FUNCIONES DE DATOS (LECTURA Y ESCRITURA) ---
        def obtener_datos_github():
            try:
                response = requests.get(CSV_URL)
                if response.status_code == 200:
                    df = pd.read_csv(StringIO(response.text))
                    if 'FECHA' in df.columns and not df.empty:
                        df['FECHA'] = pd.to_datetime(df['FECHA']).dt.date
                    return df
                return pd.DataFrame(columns=['FECHA', 'IMPORTANCIA', 'TAREA', 'ULTIMO ACCION'])
            except Exception:
                return pd.DataFrame(columns=['FECHA', 'IMPORTANCIA', 'TAREA', 'ULTIMO ACCION'])
        
        def guardar_en_github(df):
            if not TOKEN:
                st.error("No se encontró el GITHUB_TOKEN.")
                return
            try:
                g = Github(TOKEN)
                repo = g.get_repo(REPO_NAME)
                contents = repo.get_contents(FILE_PATH, ref="main")
                csv_data = df.to_csv(index=False)
                repo.update_file(
                    path=contents.path,
                    message=f"Sincronización NEXION - {obtener_fecha_mexico()}",
                    content=csv_data,
                    sha=contents.sha,
                    branch="main"
                )
                st.toast("✅ Sincronizado con GitHub")
            except Exception as e:
                st.error(f"❌ Error al sincronizar: {e}")
        
        # --- 4. INICIALIZACIÓN DEL ESTADO ---
        if 'df_tareas' not in st.session_state:
            st.session_state.df_tareas = obtener_datos_github()
        
        # --- 5. VENTANA EMERGENTE (DIALOG) ---
        @st.dialog(" Pendientes", width="large")
        def ventana_pendientes():
            st.write("### Bitácora de Operaciones")
            
            df_pro = st.session_state.df_tareas.copy()
            if not df_pro.empty:
                df_pro['FECHA'] = pd.to_datetime(df_pro['FECHA']).dt.date
        
            edited_df = st.data_editor(
                df_pro,
                use_container_width=True,
                num_rows="dynamic",
                key="workspace_editor",
                column_config={
                    "FECHA": st.column_config.DateColumn("📆 Fecha", format="DD/MM/YYYY", default=obtener_fecha_mexico()),
                    "IMPORTANCIA": st.column_config.SelectboxColumn("🚦 Prioridad", options=["Baja", "Media", "Alta", "Urgente"], required=True),
                    "TAREA": st.column_config.TextColumn("📝 Tarea Principal", width="large"),
                    "ULTIMO ACCION": st.column_config.TextColumn("🚚 Último Estatus", width="medium"),
                },
                hide_index=True,
            )
        
            if st.button("Guardar cambios manuales realizados en la tabla", use_container_width=True):
                st.session_state.df_tareas = edited_df
                guardar_en_github(st.session_state.df_tareas)
        
            st.divider()
        
            with st.form("form_nueva_tarea", clear_on_submit=True):
                st.markdown("**➕ Nuevo Registro de Actividad**")
                c1, c2 = st.columns(2)
                with c1:
                    f_nueva = st.date_input("Fecha de hoy", value=obtener_fecha_mexico())
                    i_nueva = st.selectbox("Importancia", ["Baja", "Media", "Alta", "Urgente"])
                with c2:
                    t_nueva = st.text_input("¿Qué hay que hacer?")
                    a_nueva = st.text_input("Última acción tomada")
                
                if st.form_submit_button("Añadir y Sincronizar", use_container_width=True):
                    if t_nueva:
                        t_limpia = t_nueva.replace(",", "-")
                        a_limpia = a_nueva.replace(",", "-")
                        nueva_fila = pd.DataFrame([{'FECHA': str(f_nueva), 'IMPORTANCIA': i_nueva, 'TAREA': t_limpia, 'ULTIMO ACCION': a_limpia}])
                        st.session_state.df_tareas = pd.concat([st.session_state.df_tareas, nueva_fila], ignore_index=True)
                        guardar_en_github(st.session_state.df_tareas)
                        st.rerun()
                    else:
                        st.warning("Escribe una tarea.")
        
        # --- 6. INTERFAZ EN LA BARRA LATERAL (SIDEBAR) ---
        with st.sidebar:
            if st.button("Pendientes", use_container_width=True):
                ventana_pendientes()
         
        
        # =========================================================
        # --- 2. LÓGICA DE DATOS FILTRADA (POR FECHA) ---
        # =========================================================
        hoy = pd.Timestamp.today().normalize()
        
        # Creamos la copia de trabajo y estandarizamos columnas
        df_kpi = df.copy()
        df_kpi.columns = [c.upper() for c in df_kpi.columns]
        
        # APLICAMOS EL FILTRO DE FECHAS ANTES DE CUALQUIER CÁLCULO
        if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
            start_date, end_date = rango_fechas
            df_kpi = df_kpi[
                (df_kpi["FECHA DE ENVÍO"].dt.date >= start_date) & 
                (df_kpi["FECHA DE ENVÍO"].dt.date <= end_date)
            ]
        
        # Cálculos sobre los datos (YA FILTRADOS POR FECHA)
        df_kpi["COSTO DE LA GUÍA"] = pd.to_numeric(df_kpi["COSTO DE LA GUÍA"], errors='coerce').fillna(0)
        df_kpi["CANTIDAD DE CAJAS"] = pd.to_numeric(df_kpi["CANTIDAD DE CAJAS"], errors='coerce').fillna(1).replace(0, 1)
        df_kpi["COSTO_UNITARIO"] = df_kpi["COSTO DE LA GUÍA"] / df_kpi["CANTIDAD DE CAJAS"]
        
        # Segmentación de pendientes (solo los del rango de fecha seleccionado)
        df_sin_entregar = df_kpi[df_kpi["FECHA DE ENTREGA REAL"].isna()].copy()
        df_sin_entregar["DIAS_ATRASO_KPI"] = (hoy - df_sin_entregar["PROMESA DE ENTREGA"]).dt.days
        df_sin_entregar["DIAS_ATRASO_KPI"] = df_sin_entregar["DIAS_ATRASO_KPI"].apply(lambda x: x if x > 0 else 0)
        df_sin_entregar["DIAS_TRANS"] = (hoy - df_sin_entregar["FECHA DE ENVÍO"]).dt.days
        
        # =========================================================
        # --- 4. CÁLCULO DE MÉTRICAS PARA TARJETAS ---
        # =========================================================
        total_p = len(df_kpi)
        pend_p = len(df_sin_entregar)
        eficiencia_p = (len(df_kpi[df_kpi['ESTATUS_CALCULADO'] == 'ENTREGADO']) / total_p * 100) if total_p > 0 else 0
        
        # --- LÓGICA DE RANGOS CORREGIDA ---
        a1_val = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO_KPI"] == 1])
        # Captura el rango intermedio de 2 a 4 días
        a2_val = len(df_sin_entregar[(df_sin_entregar["DIAS_ATRASO_KPI"] >= 2) & (df_sin_entregar["DIAS_ATRASO_KPI"] <= 4)])
        # Captura retrasos críticos de 5 días en adelante
        a5_val = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO_KPI"] >= 5])
        
        # --- ESTILO CSS (MANTENIDO) ---
        st.markdown("""
            <style>
            .main-card-kpi {
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border-left: 6px solid #38bdf8;
                border-radius: 15px; padding: 45px 25px; min-height: 140px;        
                display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;
                box-shadow: 0 15px 30px rgba(0,0,0,0.3); margin-bottom: 15px;
            }
            .kpi-label { color: #94a3b8; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; }
            .kpi-value { color: #f8fafc; font-size: 32px; font-weight: 800; line-height: 1; }
            .card-alerta { background-color:#161B22; padding:25px; border-radius:12px; border:1px solid #2D333F; text-align:center; }
            </style>
        """, unsafe_allow_html=True)
        
        # --- DIBUJAR TARJETAS (MANTENIDO) ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"<div class='main-card-kpi' style='border-left-color: #f1f5f9;'><div class='kpi-label'>Pedidos Totales</div><div class='kpi-value'>{total_p}</div></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='main-card-kpi' style='border-left-color: #38bdf8;'><div class='kpi-label'>Sin Entregar</div><div class='kpi-value' style='color:#38bdf8;'>{pend_p}</div></div>", unsafe_allow_html=True)
        with m3:
            color_ef = "#00FFAA" if eficiencia_p >= 95 else "#f97316"
            st.markdown(f"<div class='main-card-kpi' style='border-left-color: {color_ef};'><div class='kpi-label'>% de entregas</div><div class='kpi-value' style='color:{color_ef};'>{eficiencia_p:.1f}%</div></div>", unsafe_allow_html=True)
        
       
        
        # --- DIBUJAR FILA DE ATRASOS (ACTUALIZADO CON RANGOS) ---
        st.markdown("<p style='color:#9CA3AF; font-size:13px; font-weight:bold; letter-spacing:1px; margin-bottom:20px;'>⚠️ MONITOREO DE ATRASOS (PERIODO ACTUAL)</p>", unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3)
        a1.markdown(f"<div class='card-alerta' style='border-left: 6px solid yellow;'><div style='color:#9CA3AF; font-size:11px;'>1 Día Retraso</div><div style='color:white; font-size:36px; font-weight:bold;'>{a1_val}</div></div>", unsafe_allow_html=True)
        # Se ajustó el texto a '2-4 Días' para ser coherente con la nueva lógica
        a2.markdown(f"<div class='card-alerta' style='border-left: 6px solid #f97316;'><div style='color:#9CA3AF; font-size:11px;'>2-4 Días Retraso</div><div style='color:white; font-size:36px; font-weight:bold;'>{a2_val}</div></div>", unsafe_allow_html=True)
        a3.markdown(f"<div class='card-alerta' style='border-left: 6px solid #FF4B4B;'><div style='color:#9CA3AF; font-size:11px;'>+5 Días Retraso</div><div style='color:white; font-size:36px; font-weight:bold;'>{a5_val}</div></div>", unsafe_allow_html=True)

        st.divider()
        
        # =========================================================
        # --- 3. SECCIÓN DE ALERTAS (FILTROS DE MANDO SIMPLIFICADOS) ---
        # =========================================================
        df_criticos = df_sin_entregar[df_sin_entregar["DIAS_ATRASO_KPI"] > 0].copy()
        
        if not df_criticos.empty:
            # Estilo para las etiquetas de los multiselect (Color Verde Esmeralda)
            st.markdown("""
                <style>
                span[data-baseweb="tag"] {
                    background-color: #00FFAA !important;
                    color: #000000 !important;
                    font-weight: bold !important;
                }
                </style>
            """, unsafe_allow_html=True)

            with st.expander("GESTIÓN DE PEDIDOS CRÍTICOS", expanded=True):
                
                # --- FILTROS DE OPERACIÓN ---
                c1, c2 = st.columns(2)
                with c1:
                    filtro_flete = st.multiselect("Filtrar Paquetería:", 
                                                options=sorted(df_criticos["FLETERA"].unique()),
                                                key="filter_alert_flete_v2")
                with c2:
                    opciones_retraso = ["1 Día de Retraso", "2 a 4 Días de Retraso", "Más de 5 Días de Retraso"]
                    filtro_rango = st.multiselect("Filtrar por Gravedad:", 
                                                options=opciones_retraso,
                                                key="filter_alert_range")

                # --- LÓGICA DE FILTRADO DINÁMICO ---
                df_ver = df_criticos.copy()
                
                if filtro_flete:
                    df_ver = df_ver[df_ver["FLETERA"].isin(filtro_flete)]
                
                if filtro_rango:
                    mask_rango = pd.Series(False, index=df_ver.index)
                    if "1 Día de Retraso" in filtro_rango:
                        mask_rango |= (df_ver["DIAS_ATRASO_KPI"] == 1)
                    if "2 a 4 Días de Retraso" in filtro_rango:
                        mask_rango |= (df_ver["DIAS_ATRASO_KPI"] >= 2) & (df_ver["DIAS_ATRASO_KPI"] <= 4)
                    if "Más de 5 Días de Retraso" in filtro_rango:
                        mask_rango |= (df_ver["DIAS_ATRASO_KPI"] >= 5)
                    df_ver = df_ver[mask_rango]

                # Preparación de tabla
                df_ver["FECHA DE ENVÍO"] = df_ver["FECHA DE ENVÍO"].dt.strftime('%d/%m/%Y')
                df_ver["PROMESA DE ENTREGA"] = df_ver["PROMESA DE ENTREGA"].dt.strftime('%d/%m/%Y')
                
                columnas_finales = [
                    "NÚMERO DE PEDIDO", "NOMBRE DEL CLIENTE", "FLETERA", 
                    "FECHA DE ENVÍO", "PROMESA DE ENTREGA", "NÚMERO DE GUÍA", 
                    "DIAS_TRANS", "DIAS_ATRASO_KPI"
                ]
                
                df_tabla_ver = df_ver[columnas_finales].rename(columns={
                    "DIAS_ATRASO_KPI": "DÍAS ATRASO",
                    "DIAS_TRANS": "DÍAS TRANS."
                })
        
                # --- TABLA PREMIUM CON INDICADORES DE BARRA ---
                st.dataframe(
                    df_tabla_ver.sort_values("DÍAS ATRASO", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "NOMBRE DEL CLIENTE": st.column_config.TextColumn("👤 CLIENTE", width="large"),
                        "DÍAS TRANS.": st.column_config.ProgressColumn(
                            "⏳ TRANS.",
                            format="%d",
                            min_value=0,
                            max_value=int(df_tabla_ver["DÍAS TRANS."].max() + 1) if not df_tabla_ver.empty else 10,
                            color="orange"
                        ),
                        "DÍAS ATRASO": st.column_config.ProgressColumn(
                            "⚠️ ATRASO",
                            format="%d",
                            min_value=0,
                            max_value=int(df_tabla_ver["DÍAS ATRASO"].max() + 1) if not df_tabla_ver.empty else 10,
                            color="red"
                        )
                    }
                )
        else:
            st.success("✅ Protocolo de Alertas: Limpio.")

        st.divider()
        
        # --------------------------------------------------
        # GRÁFICOS DE BARRAS POR PAQUETERÍA (CONECTADO A FILTRO DE FECHAS)
        # --------------------------------------------------
        
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.02); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-top: 30px; margin-bottom: 25px;'>
                <span style='color: #e2e8f0; font-weight: 700; font-size: 15px; letter-spacing: 1.5px;'>ESTADO DE CARGA EN TIEMPO REAL</span>
            </div>
        """, unsafe_allow_html=True)
        
        color_transito = "#fbbf24" 
        color_retraso = "#fb7185"  
        
        col1, col2 = st.columns(2)
        
        # --- COLUMNA 1: EN TRÁNSITO (Basado en df_kpi filtrado por fecha) ---
        with col1:
            # Agrupamos usando df_kpi que es el que ya tiene el filtro de fechas aplicado arriba
            df_t = df_kpi[df_kpi["ESTATUS_CALCULADO"] == "EN TRANSITO"].groupby("FLETERA").size().reset_index(name="CANTIDAD")
            total_t = df_t["CANTIDAD"].sum()
        
            st.markdown(f"""
                <div style='background: linear-gradient(90deg, rgba(251, 191, 36, 0.1) 0%, transparent 100%); padding: 15px; border-radius: 10px; border-bottom: 2px solid {color_transito}33;'>
                    <p style='margin:0; color:{color_transito}; font-size:12px; font-weight:800; text-transform:uppercase;'>🟡 En Movimiento</p>
                    <h2 style='margin:0; color:white; font-size:32px;'>{total_t} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                </div>
            """, unsafe_allow_html=True)
        
            if not df_t.empty:
                # Altura dinámica para evitar que las barras se encimen
                h_t = len(df_t) * 40 + 50
                chart_t = alt.Chart(df_t).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5, size=20, color=color_transito).encode(
                    x=alt.X("CANTIDAD:Q", title=None, axis=None),
                    y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='white', labelFontSize=12))
                )
                text_t = chart_t.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700).encode(text="CANTIDAD:Q")
                
                st.altair_chart((chart_t + text_t).properties(height=h_t).configure_view(strokeOpacity=0).configure_axis(grid=False), use_container_width=True)
            else:
                st.markdown(f"<div style='padding:40px; text-align:center; color:#475569;'>Sin carga activa en este rango</div>", unsafe_allow_html=True)
        
        # --- COLUMNA 2: RETRASADOS (Basado en df_kpi filtrado por fecha) ---
        with col2:
            df_r = df_kpi[df_kpi["ESTATUS_CALCULADO"] == "RETRASADO"].groupby("FLETERA").size().reset_index(name="CANTIDAD")
            total_r = df_r["CANTIDAD"].sum()
        
            st.markdown(f"""
                <div style='background: linear-gradient(90deg, rgba(251, 113, 133, 0.1) 0%, transparent 100%); padding: 15px; border-radius: 10px; border-bottom: 2px solid {color_retraso}33;'>
                    <p style='margin:0; color:{color_retraso}; font-size:12px; font-weight:800; text-transform:uppercase;'>🔴 Alerta de Retraso</p>
                    <h2 style='margin:0; color:white; font-size:32px;'>{total_r} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                </div>
            """, unsafe_allow_html=True)
        
            if not df_r.empty:
                h_r = len(df_r) * 40 + 50
                chart_r = alt.Chart(df_r).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5, size=20, color=color_retraso).encode(
                    x=alt.X("CANTIDAD:Q", title=None, axis=None),
                    y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='white', labelFontSize=12))
                )
                text_r = chart_r.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700).encode(text="CANTIDAD:Q")
                
                st.altair_chart((chart_r + text_r).properties(height=h_r).configure_view(strokeOpacity=0).configure_axis(grid=False), use_container_width=True)
            else:
                st.markdown(f"<div style='padding:40px; text-align:center; color:#059669; font-weight:bold;'>✓ Operación al día en este rango</div>", unsafe_allow_html=True)
        
        # --- 8. SECCIÓN DE GRÁFICOS ELITE (CONTROL & RENDIMIENTO) ---
                       
        # Paleta de colores ejecutiva (Semáforo de alto contraste)
        color_excelencia = "#FFD700" # Esmeralda (>= 95%)
        color_alerta = "#fbbf24"     # Ámbar (85% - 94%)
        color_critico = "#fb7185"    # Coral/Rojo (< 85%)

        # DEFINICIÓN DE LA FUNCIÓN (Debe ir antes de usarse)
        def titulo_grafico_elite(texto, emoji):
            st.markdown(f"""
                <div style='background: rgba(255,255,255,0.02); padding: 12px 20px; border-radius: 8px; border-left: 4px solid {color_excelencia}; margin-bottom: 20px;'>
                    <span style='color: #e2e8f0; font-weight: 700; font-size: 15px; letter-spacing: 1.5px;'>{emoji} {texto.upper()}</span>
                </div>
            """, unsafe_allow_html=True)

        # --- GRÁFICO 1: VOLUMEN DE OPERACIÓN (ENFOQUE DIARIO) ---
        titulo_grafico_elite("Volumen Diario de Envíos", "")
        
        # Agrupamos estrictamente por fecha (día)
        df_vol = df_kpi.groupby(df_kpi["FECHA DE ENVÍO"].dt.date).size().reset_index(name="Pedidos")
        df_vol.columns = ["Fecha", "Pedidos"]
        
        # Base del gráfico con eje X configurado para días
        line_base = alt.Chart(df_vol).encode(
            x=alt.X('Fecha:T', 
                    title=None, 
                    axis=alt.Axis(
                        format='%d %b', # Muestra "12 Jan" por ejemplo
                        grid=False, 
                        labelColor='#94a3b8',
                        labelAngle=-45 # Inclinación para mejor lectura si hay muchos días
                    )),
            y=alt.Y('Pedidos:Q', title=None, axis=alt.Axis(gridOpacity=0.05, labelColor='#94a3b8'))
        )
        
        # Capa 1: Área sombreada con degradado dorado (Trading Style)
        area = line_base.mark_area(
            line={'color': '#FFD700', 'strokeWidth': 2.5},
            color=alt.Gradient(
                gradient='linear',
                stops=[
                    alt.GradientStop(color='rgba(255, 215, 0, 0.4)', offset=0), 
                    alt.GradientStop(color='rgba(255, 215, 0, 0.0)', offset=1)
                ],
                x1=1, x2=1, y1=1, y2=0
            ),
            interpolate='linear'
        )
        
        # Capa 2: Puntos de impacto en cada día
        points = line_base.mark_point(
            color='#FFFF00', 
            size=80, 
            fill="#0f172a", 
            strokeWidth=2
        )
        
        # Capa 3: ETIQUETAS DE DATOS (Frecuencia diaria)
        labels = line_base.mark_text(
            align='center',
            baseline='bottom',
            dy=-15, 
            color='#e2e8f0',
            fontWeight=700,
            fontSize=13
        ).encode(
            text='Pedidos:Q'
        )
        
        # Renderizado con ajuste de altura para enfoque en datos
        st.altair_chart(
            (area + points + labels).properties(height=300).configure_view(strokeOpacity=0), 
            use_container_width=True
        )
        
        st.write("##")

        # --- GRÁFICO 2: EFICIENCIA POR FLETERA (SEMÁFORO) ---
        titulo_grafico_elite("Ranking de Eficiencia por Fletera", "")
        df_ent = df_kpi[df_kpi["FECHA DE ENTREGA REAL"].notna()].copy()
        
        if not df_ent.empty:
            df_ent["AT"] = df_ent["FECHA DE ENTREGA REAL"] <= df_ent["PROMESA DE ENTREGA"]
            df_p = (df_ent.groupby("FLETERA")["AT"].mean() * 100).reset_index()
            
            # Asignación de colores para el semáforo
            def asignar_color(valor):
                if valor >= 95: return color_excelencia
                if valor >= 85: return color_alerta
                return color_critico
            
            df_p["COLOR_HEX"] = df_p["AT"].apply(asignar_color)

            # Gráfico de barras con etiquetas
            bars = alt.Chart(df_p).mark_bar(
                cornerRadiusTopRight=8,
                cornerRadiusBottomRight=8,
                size=24
            ).encode(
                x=alt.X('AT:Q', title='Cumplimiento (%)', scale=alt.Scale(domain=[0, 118]), axis=alt.Axis(gridOpacity=0.05)),
                y=alt.Y('FLETERA:N', sort='-x', title=None, axis=alt.Axis(labelColor='white', labelFontSize=12)),
                color=alt.Color('COLOR_HEX:N', scale=None) 
            )

            chart_text = bars.mark_text(
                align='left',
                baseline='middle',
                dx=12,
                color='white',
                fontWeight=700,
                fontSize=13
            ).encode(text=alt.Text('AT:Q', format='.1f'))

            st.altair_chart((bars + chart_text).properties(height=400), use_container_width=True)
                    
        
        # --- PALETA DE COLORES ELÉCTRICA ---
        azul_volt = "#00D4FF"        # Para Costos
        verde_esmeralda = "#00FF9F"  # Esmeralda Eléctrico (Versión vibrante)
        
        # --- PALETA DE COLORES ELÉCTRICA ---
        azul_volt = "#00D4FF"        # Para Costos
        verde_esmeralda = "#00FF9F"  # Esmeralda Eléctrico
        
        # =========================================================
        # --- BLOQUE 1: COSTO PROMEDIO POR CAJA (AZUL VOLT) ---
        # =========================================================
        with st.container():
            titulo_grafico_elite("Costo Promedio por Caja", "💰")
            
            # --- PROCESAMIENTO CON FILTRO DE SEGURIDAD ---
            # Solo tomamos filas donde ya exista un costo registrado (> 0)
            df_filtrado_costo = df_kpi[df_kpi['COSTO DE LA GUÍA'] > 0].copy()
            
            # Calculamos el costo por caja sobre el set filtrado
            df_filtrado_costo['COSTO_X_CAJA'] = (
                df_filtrado_costo['COSTO DE LA GUÍA'] / 
                df_filtrado_costo['CANTIDAD DE CAJAS'].replace(0, 1)
            )
            
            # Agrupamos por Fletera y sacamos el promedio real
            costo_data = df_filtrado_costo.groupby('FLETERA')['COSTO_X_CAJA'].mean().reset_index()
            # ----------------------------------------------
        
            # Capa de Barras
            bars_costo = alt.Chart(costo_data).mark_bar(
                cornerRadiusTopRight=10,
                cornerRadiusBottomRight=10,
                size=25
            ).encode(
                x=alt.X('COSTO_X_CAJA:Q', title="Inversión Promedio ($)"),
                y=alt.Y('FLETERA:N', sort='-x', title=None),
                color=alt.value(azul_volt)
            )
        
            # Capa de Etiquetas (Texto)
            text_costo = bars_costo.mark_text(
                align='left', baseline='middle', dx=8,
                color='white', fontSize=13, fontWeight='bold'
            ).encode(
                text=alt.Text('COSTO_X_CAJA:Q', format='$.2f')
            )
        
            st.altair_chart((bars_costo + text_costo).properties(height=400), use_container_width=True)
        
        st.write("##")
        
        
                        
        
        # --- NAVEGACIÓN DESDE KPIs ---
        

        # Pie de página
        st.markdown("<div style='text-align:center; color:#475569; font-size:10px; margin-top:20px;'>LOGISTICS INTELLIGENCE UNIT - CONFIDENTIAL</div>", unsafe_allow_html=True)
    

    # ------------------------------------------------------------------
    # MAIN 03: REPORTE OPS
    # ------------------------------------------------------------------
    elif st.session_state.pagina == "Reporte":
        st.components.v1.html("<script>parent.window.scrollTo(0,0);</script>", height=0)
        
        # --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (Sube el contenido y estiliza el menú) ---
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 0rem !important;
                    max-width: 95% !important;
                }

                .header-wrapper {
                    display: flex;
                    align-items: baseline;
                    gap: 12px;
                    font-family: 'Inter', sans-serif;
                }

                /* TITULO PRINCIPAL: Gris Oscuro */
                .header-wrapper h1 {
                    font-size: 22px !important;
                    font-weight: 800;
                    margin: 0;
                    color: #4b5563; /* Gris oscuro */
                    letter-spacing: -0.8px;
                }

                /* INDICADOR: Blanco */
                .header-wrapper span {
                    font-size: 14px;
                    font-weight: 300;
                    color: #ffffff; /* Blanco */
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                /* BOTÓN DE MENÚ MINIMALISTA */
                div[data-testid="stPopover"] > button {
                    background-color: transparent !important;
                    border: 1px solid rgba(0, 255, 162, 0.3) !important;
                    padding: 2px 10px !important;
                    border-radius: 6px !important;
                    height: 32px !important;
                    transition: all 0.3s ease;
                }
                
                div[data-testid="stPopover"] > button:hover {
                    border: 1px solid #00ffa2 !important;
                    box-shadow: 0 0 10px rgba(0, 255, 162, 0.2);
                }

                div[data-testid="stPopoverContent"] button {
                    text-align: left !important;
                    justify-content: flex-start !important;
                    border: none !important;
                    background: transparent !important;
                    font-size: 13px !important;
                    padding: 8px 10px !important;
                }

                div[data-testid="stPopoverContent"] button:hover {
                    color: #00ffa2 !important;
                    background: rgba(0, 255, 162, 0.05) !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # --- 2. POSICIONAMIENTO DEL ENCABEZADO ---
        c1, c2 = st.columns([0.88, 0.12], vertical_alignment="bottom")

        with c1:
            st.markdown("""
                <div class="header-wrapper">
                    <h1>Operations </h1>
                    <span>Report</span>
                    <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #00ffa2; opacity: 0.7; margin-left: 10px; padding-left: 10px; border-left: 1px solid #334155;">
                        LOGÍSTICA & RENDIMIENTO
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            with st.popover("☰", use_container_width=True):
                st.markdown("<p style='color:#64748b; font-size:10px; font-weight:700; margin-bottom:10px; letter-spacing:1px;'>NAVEGACIÓN</p>", unsafe_allow_html=True)
                
                paginas = {
                    "TRACKING": ("principal", "kpi_btn_aac"),
                    "SEGUIMIENTO": ("KPIs", "kpi_btn_kpi"),
                    "REPORTE OPS": ("Reporte", "kpi_btn_rep"),
                    "HUB LOGISTIC": ("HubLogistico", "kpi_btn_hub"),
                    "OTD": ("RadarRastreo", "kpi_btn_radar")
                }

                for nombre, (v_state, v_key) in paginas.items():
                    if st.button(nombre, use_container_width=True, key=v_key):
                        st.session_state.pagina = v_state
                        st.rerun()

        # Línea divisoria
        st.markdown("<hr style='margin: 8px 0 20px 0; border: none; border-top: 1px solid rgba(148, 163, 184, 0.1);'>", unsafe_allow_html=True)
               
        # --- 1. MOTOR DE DATOS NIVEL ELITE ---
        @st.cache_data
        def cargar_analisis_elite():
            try:
                df = pd.read_csv("analisis.csv", encoding="utf-8")
                df.columns = [str(c).strip().upper() for c in df.columns]
                df = df.dropna(subset=['MES'])
                df = df[df['MES'].str.contains('Unnamed|TOTAL', case=False) == False]
                
                def limpiar_a_numero(v):
                    if pd.isna(v): return 0.0
                    if isinstance(v, (int, float)): return float(v)
                    s = str(v).replace('$', '').replace(',', '').replace('%', '').replace('(', '-').replace(')', '').strip()
                    try: return float(s)
                    except: return 0.0
        
                cols_numericas = [
                    "COSTO DE FLETE", "FACTURACIÓN", "CAJAS ENVIADAS", "COSTO LOGÍSTICO", 
                    "COSTO POR CAJA", "META INDICADOR", "VALUACION INCIDENCIAS", 
                    "INCREMENTO + VI", "% DE INCREMENTO VS 2024", "COSTO POR CAJA 2024", "PORCENTAJE DE INCIDENCIAS"
                ]
                
                for col in cols_numericas:
                    if col in df.columns:
                        df[col] = df[col].apply(limpiar_a_numero)
                return df
            except Exception as e:
                st.error(f"Error en Motor: {e}")
                return None
        
        # --- 2. FUNCIÓN DE RENDERIZADO BLINDADA ---
        def render_card(label, value, footer, target_val=None, actual_val=None, inverse=False, border_base="border-blue"):
            if target_val is None or actual_val is None:
                color = "#f0f6fc"
                border = border_base
            else:
                is_alert = actual_val > target_val if not inverse else actual_val < target_val
                color = "#fb7185" if is_alert else "#00ffa2"
                border = "border-red" if is_alert else "border-green"
            
            st.markdown(f"""
                <div class='card-container {border}'>
                    <div class='card-label'>{label}</div>
                    <div class='card-value' style='color:{color}'>{value}</div>
                    <div class='card-footer'>{footer}</div>
                </div>
            """, unsafe_allow_html=True)
        
        df_a = cargar_analisis_elite()
        
        if df_a is not None:
            # --- 3. SIDEBAR ---
            st.sidebar.markdown("## ")
            meses_limpios = [m for m in df_a["MES"].unique() if str(m).strip() != ""]
            mes_sel = st.sidebar.selectbox("MES ACTUAL / BASE", meses_limpios)
            df_mes = df_a[df_a["MES"] == mes_sel].iloc[0]
            
            modo_comp = st.sidebar.checkbox("Activar comparativa Mes vs Mes")
            if modo_comp:
                mes_comp = st.sidebar.selectbox("COMPARAR CONTRA:", meses_limpios, index=0)
                df_mes_b = df_a[df_a["MES"] == mes_comp].iloc[0]
        
            # --- 4. CSS PREMIUM ELITE ---
            st.markdown("""
                <style>
                @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@400;800&display=swap');
                .premium-header { font-family: 'Orbitron', sans-serif; color: #f8fafc; letter-spacing: 2px; text-transform: uppercase; border-bottom: 2px solid #38bdf8; padding-bottom: 8px; margin: 25px 0; }
                .card-container { background-color: #0d1117; border-radius: 10px; padding: 15px; border: 1px solid #30363d; height: 125px; margin-bottom: 10px; transition: all 0.3s; margin-top: 10px;}
                .card-label { color: #8b949e; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; }
                .card-value { font-size: 1.6rem; font-weight: 800; margin: 4px 0; font-family: 'Inter', sans-serif; }
                .card-footer { color: #484f58; font-size: 0.6rem; font-weight: 600; }
                .border-blue { border-left: 5px solid #38bdf8; } .border-green { border-left: 5px solid #00ffa2; }
                .border-red { border-left: 5px solid #fb7185; } .border-purple { border-left: 5px solid #a78bfa; }
                .border-yellow { border-left: 5px solid #eab308; } .border-pink { border-left: 5px solid #f472b6; }
                .insight-box { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-top: 10px; }
                .calc-box { background: rgba(56, 189, 248, 0.05); border: 1px dashed #38bdf8; border-radius: 10px; padding: 15px; margin: 20px 0; font-family: 'Inter', sans-serif; color: #94a3b8; font-size: 0.85rem; }
                </style>
            """, unsafe_allow_html=True)
                       
                   
            header_txt = f"Resultados: {mes_sel}" if not modo_comp else f"Comparativa Mode: {mes_sel} VS {mes_comp}"

            # Aplicamos un reseteo total de bordes, sombras y elementos decorativos internos
            st.markdown(f"""
            <style>
            .premium-header {{
                font-size: 12px !important;   /* 👈 AQUÍ */
                font-weight: 600;
                letter-spacing: 0.4px;
                margin-top: 4px;
                margin-bottom: 8px;
                border: none !important;
                box-shadow: none !important;
            }}
        </style>
        
        <h4 class="premium-header">
            {header_txt}
        </h4>
        """, unsafe_allow_html=True)

                
            
                        
            if not modo_comp:
                # --- VISTA NORMAL 9 TARJETAS ---
                c1, c2, c3 = st.columns(3)
                with c1: render_card("Costo Logístico", f"{df_mes['COSTO LOGÍSTICO']:.1f}%", f"META: {df_mes['META INDICADOR']}%", df_mes['META INDICADOR'], df_mes['COSTO LOGÍSTICO'])
                with c2: render_card("Incremento + VI", f"${df_mes['INCREMENTO + VI']:,.0f}", "Impacto Real", 0, df_mes['INCREMENTO + VI'], inverse=True)
                with c3: render_card("% Incr. vs 2024", f"{df_mes['% DE INCREMENTO VS 2024']:.1f}%", "Inflación", border_base="border-pink")
        
                c4, c5, c6 = st.columns(3)
                with c4: render_card("Costo por Caja", f"${df_mes['COSTO POR CAJA']:.1f}", f"Target 2024: ${df_mes['COSTO POR CAJA 2024']:.1f}", df_mes['COSTO POR CAJA 2024'], df_mes['COSTO POR CAJA'])
                with c5: render_card("Valuación Incidencias", f"${df_mes['VALUACION INCIDENCIAS']:,.0f}", "Mermas", border_base="border-yellow")
                with c6: render_card("% Incidencias", f"{df_mes['PORCENTAJE DE INCIDENCIAS']:.2f}%", "Calidad", border_base="border-purple")
        
                c7, c8, c9 = st.columns(3)
                with c7: render_card("Facturación", f"${df_mes['FACTURACIÓN']:,.0f}", "Venta Mes", border_base="border-blue")
                with c8: render_card("Cajas Enviadas", f"{int(df_mes['CAJAS ENVIADAS']):,.0f}", "Volumen", border_base="border-purple")
                with c9: render_card("Costo de Flete", f"${df_mes['COSTO DE FLETE']:,.0f}", "Inversión", border_base="border-blue")
                
                                             
                
                # --- BLOQUE PREMIUM DE CÁLCULOS ---
                st.markdown(f"""
                <div class="calc-box">
                    <b style="color:#38bdf8; text-transform:uppercase;">Metodología de Cálculo para {mes_sel}:</b><br><br>
                    • <b>Logístico:</b> (${df_mes['COSTO DE FLETE']:,.2f} / ${df_mes['FACTURACIÓN']:,.2f}) = {df_mes['COSTO LOGÍSTICO']:.2f}%<br>
                    • <b>C/Caja:</b> ${df_mes['COSTO DE FLETE']:,.2f} / {int(df_mes['CAJAS ENVIADAS'])} cajas = ${df_mes['COSTO POR CAJA']:.2f}<br>
                    • <b>Impacto:</b> (Ahorro Incidencias) - (Variación Tarifaria vs 2024 * Cajas) = ${df_mes['INCREMENTO + VI']:,.2f}
                </div>
                """, unsafe_allow_html=True)
        
               # --- LÓGICA DE NARRATIVA DINÁMICA (EL CEREBRO DEL CAPITÁN) ---
                impacto_1k = (df_mes['COSTO DE FLETE'] / df_mes['FACTURACIÓN']) * 1000
                eficiencia_vs_meta = df_mes['META INDICADOR'] - df_mes['COSTO LOGÍSTICO']
                
                # Definición de Tono y Mensaje según Desempeño
                if eficiencia_vs_meta >= 0.5:
                    msg_clase = "OPTIMIZACIÓN RADICAL"
                    msg_color = "#00ffa2"
                    msg_desc = f"La operación está en zona de alta rentabilidad. Estamos operando {eficiencia_vs_meta:.1f}% por debajo del techo presupuestal, lo que inyecta liquidez directa al Bottom Line."
                elif eficiencia_vs_meta >= 0:
                    msg_clase = "ESTABILIDAD OPERATIVA"
                    msg_color = "#38bdf8"
                    msg_desc = "Cumplimiento de objetivos en curso. El control de fletes se mantiene alineado con la facturación, asegurando un margen neto previsible."
                else:
                    msg_clase = "EROSIÓN DE MARGEN"
                    msg_color = "#fb7185"
                    msg_desc = f"Alerta roja: La logística está devorando el margen bruto. Superamos el target por {abs(eficiencia_vs_meta):.1f}%, lo que requiere una intervención inmediata en el mix de transporte."
        
                # --- VISUALIZACIÓN DE ANÁLISIS DINÁMICO ---
                r1, r2 = st.columns(2)
                with r1:
                    st.markdown(f"""<div class="insight-box" style="border-left: 5px solid #38bdf8; height:240px;">
                        <h4 style="color:#38bdf8; margin:0; font-family:Orbitron; font-size:0.9rem;">DEEP DIVE: EFICIENCIA FINANCIERA</h4>
                        <p style="color:#94a3b8; font-size:0.85rem; margin-top:15px; line-height:1.6;">
                        • <b>Métrica de Consumo:</b> Cada <b>$1,000</b> de venta genera un 'impuesto logístico' de <b>${impacto_1k:.2f}</b>.<br>
                        • <b>Punto de Fuga:</b> El desvío tarifario vs 2024 representa una fuga de <b>${abs(df_mes['INCREMENTO + VI']):,.0f}</b>. <br>
                        • <b>Diagnóstico:</b> El costo por unidad está <b>{'sobre la media' if df_mes['COSTO POR CAJA'] > df_mes['COSTO POR CAJA 2024'] else 'bajo control'}</b>, lo que indica una {'necesidad de renegociación' if df_mes['COSTO POR CAJA'] > df_mes['COSTO POR CAJA 2024'] else 'gestión óptima de activos'}.
                        </p></div>""", unsafe_allow_html=True)
                
                with r2:
                    st.markdown(f"""<div class="insight-box" style="border-top: 4px solid {msg_color}; height:240px;">
                        <h4 style="color:{msg_color}; margin:0; font-family:Orbitron; font-size:0.9rem;">🩺 RADIOGRAFÍA: {msg_clase}</h4>
                        <p style="color:#f1f5f9; font-size:0.85rem; margin-top:15px; line-height:1.6;">
                        <b>DICTAMEN TÉCNICO:</b> {msg_desc}<br><br>
                        <b>ANÁLISIS DE BRECHA:</b> Estamos operando con un incremento unitario del <b>{df_mes['% DE INCREMENTO VS 2024']:.1f}%</b>. Este nivel de inflación logística 
                        {'es insostenible' if df_mes['% DE INCREMENTO VS 2024'] > 10 else 'es manejable'} bajo el esquema actual de precios de venta.
                        </p></div>""", unsafe_allow_html=True)
        
            else:
                # --- VISTA COMPARATIVA 3 VS 3 ---
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown(f"#### 📍 {mes_sel}")
                    render_card("Costo Logístico", f"{df_mes['COSTO LOGÍSTICO']:.1f}%", "Actual", df_mes['META INDICADOR'], df_mes['COSTO LOGÍSTICO'])
                    render_card("Costo por Caja", f"${df_mes['COSTO POR CAJA']:.1f}", "Actual", df_mes['COSTO POR CAJA 2024'], df_mes['COSTO POR CAJA'])
                    render_card("Incremento + VI", f"${df_mes['INCREMENTO + VI']:,.0f}", "Actual", 0, df_mes['INCREMENTO + VI'], inverse=True)
        
                with col_b:
                    st.markdown(f"#### 📍 {mes_comp}")
                    render_card("Costo Logístico", f"{df_mes_b['COSTO LOGÍSTICO']:.1f}%", "Comparativo", df_mes_b['META INDICADOR'], df_mes_b['COSTO LOGÍSTICO'])
                    render_card("Costo por Caja", f"${df_mes_b['COSTO POR CAJA']:.1f}", "Comparativo", df_mes_b['COSTO POR CAJA 2024'], df_mes_b['COSTO POR CAJA'])
                    render_card("Incremento + VI", f"${df_mes_b['INCREMENTO + VI']:,.0f}", "Comparativo", 0, df_mes_b['INCREMENTO + VI'], inverse=True)
        
                # --- ANÁLISIS DE COMBATE (DEEP DIVE COMPARATIVO) ---
                delta_log = df_mes["COSTO LOGÍSTICO"] - df_mes_b["COSTO LOGÍSTICO"]
                mejor_mes = mes_sel if delta_log < 0 else mes_comp
                
                st.markdown(f"""
                <div class="insight-box" style="border-top: 5px solid #a78bfa;">
                    <h4 style="color:#a78bfa; margin:0; font-family:Orbitron; font-size:0.9rem;">ANÁLISIS FORENSE: COMPARATIVA DE RENDIMIENTO</h4>
                    <p style="color:#f1f5f9; font-size:0.9rem; margin-top:10px; line-height:1.6;">
                    La telemetría indica que <b>{mejor_mes}</b> es el referente de eficiencia. 
                    <br>• <b>Variación Estratégica:</b> Existe un diferencial de <b>{abs(delta_log):.2f}%</b> en la absorción del costo sobre la venta bruta.<br>
                    • <b>Factor Determinante:</b> La diferencia no es el volumen, sino la <b>densidad de costo por caja</b>. {'Mantener el modelo de ' + mejor_mes if delta_log != 0 else 'Ambos periodos presentan paridad operativa'}.
                    </p>
                </div>
                """, unsafe_allow_html=True)

            def crear_pdf_logistico(df_mes, mes_sel, impacto_1k, veredicto):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                
                # --- ENCABEZADO ---
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, f"REPORTE EJECUTIVO DE LOGISTICA: {mes_sel}", ln=True, align='C')
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 10, "Intelligence Operations Command - Logistic Performance Analysis", ln=True, align='C')
                pdf.ln(5)
                pdf.line(10, 32, 200, 32) # Línea divisoria
                pdf.ln(10)
                
                # --- TABLA DE KPIS CRITICOS ---
                pdf.set_fill_color(240, 240, 240)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(100, 10, "INDICADOR CLAVE (KPI)", 1, 0, 'C', True)
                pdf.cell(90, 10, "VALOR REPORTADO", 1, 1, 'C', True)
                
                pdf.set_font("Arial", '', 11)
                kpis = [
                    ("Costo Logistico (%)", f"{df_mes['COSTO LOGÍSTICO']:.2f}%"),
                    ("Costo por Caja ($)", f"${df_mes['COSTO POR CAJA']:.2f}"),
                    ("Facturacion Mensual", f"${df_mes['FACTURACIÓN']:,.2f}"),
                    ("Volumen (Cajas)", f"{int(df_mes['CAJAS ENVIADAS']):,.0f}"),
                    ("Fuga de Utilidad (Delta)", f"${abs(df_mes['INCREMENTO + VI']):,.2f}"),
                    ("Inflacion vs 2024", f"{df_mes['% DE INCREMENTO VS 2024']:.1f}%")
                ]
                
                for kpi, valor in kpis:
                    pdf.cell(100, 10, kpi, 1)
                    pdf.cell(90, 10, valor, 1, 1, 'C')
                
                pdf.ln(10)
                
                # --- METODOLOGIA DE CALCULO ---
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "METODOLOGIA DE CALCULO Y AUDITORIA:", ln=True)
                pdf.set_font("Arial", '', 10)
                metodologia = (
                    f"1. Costo Logistico: Se determina dividiendo el gasto total de fletes (${df_mes['COSTO DE FLETE']:,.2f}) "
                    f"entre la facturacion bruta (${df_mes['FACTURACIÓN']:,.2f}).\n"
                    f"2. Costo por Caja: Gasto total entre {int(df_mes['CAJAS ENVIADAS'])} unidades despachadas.\n"
                    f"3. Impacto de Utilidad: Cruce de valuacion de incidencias contra desviacion tarifaria base 2024."
                )
                pdf.multi_cell(0, 8, metodologia)
                pdf.ln(5)
            
                # --- RADIOGRAFIA Y DIAGNOSTICO ---
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "DIAGNOSTICO ESTRATEGICO FINAL:", ln=True)
                pdf.set_fill_color(245, 245, 255)
                pdf.set_font("Arial", 'I', 11)
                diagnostico = (
                    f"Por cada $1,000 MXN de venta, la operacion consume ${impacto_1k:.2f}.\n\n"
                    f"VERDICTO: {veredicto}"
                )
                pdf.multi_cell(0, 10, diagnostico, border=1, fill=True)
                
                return pdf.output()
        
            # --- PROTOCOLO DE EXTRACCIÓN SEGURO (LAS 9 TARJETAS) ---
            st.write("---")

            if not modo_comp:
                if PDF_READY:
                    if st.button("GENERAR REPORTE"):
                        try:
                            st.toast("Compilando información...", icon="⚙️")
                            
                            # RE-CÁLCULO DE SEGURIDAD
                            impacto_1k = (df_mes['COSTO DE FLETE'] / df_mes['FACTURACIÓN']) * 1000 if df_mes['FACTURACIÓN'] > 0 else 0
                            
                            pdf = FPDF()
                            pdf.add_page()
                            
                            # --- ENCABEZADO INSTITUCIONAL ---
                            pdf.set_fill_color(13, 17, 23)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font("Arial", 'B', 16)
                            pdf.cell(0, 15, f"REPORTE EJECUTIVO DE LOGÍSTICA - {mes_sel}", 0, 1, 'C', True)
                            
                            pdf.ln(5)
                            pdf.set_text_color(0, 0, 0)
                            
                            # --- SECCIÓN 1: RENTABILIDAD (TARJETAS 1, 2, 3) ---
                            pdf.set_font("Arial", 'B', 11)
                            pdf.set_fill_color(240, 240, 240)
                            pdf.cell(0, 8, "  I. INDICADORES DE RENTABILIDAD Y COSTO", 0, 1, 'L', True)
                            pdf.ln(1)
                            pdf.set_font("Arial", '', 10)
                            pdf.cell(63, 10, f"Costo Logistico: {df_mes['COSTO LOGÍSTICO']:.1f}%", 1, 0, 'C')
                            pdf.cell(63, 10, f"Incr. vs 2024: {df_mes['% DE INCREMENTO VS 2024']:.1f}%", 1, 0, 'C')
                            pdf.cell(63, 10, f"Meta Mes: {df_mes['META INDICADOR']}%", 1, 1, 'C')
                            
                            pdf.ln(3)
                            
                            # --- SECCIÓN 2: IMPACTO Y DESVIACIÓN (TARJETAS 4, 5, 6) ---
                            pdf.set_font("Arial", 'B', 11)
                            pdf.cell(0, 8, "  II. IMPACTO EN UTILIDAD Y CALIDAD", 0, 1, 'L', True)
                            pdf.ln(1)
                            pdf.set_font("Arial", '', 10)
                            pdf.cell(63, 10, f"Costo por Caja: ${df_mes['COSTO POR CAJA']:.1f}", 1, 0, 'C')
                            pdf.cell(63, 10, f"Incidencias: {df_mes['PORCENTAJE DE INCIDENCIAS']:.2f}%", 1, 0, 'C')
                            pdf.cell(63, 10, f"Val. Incidencias: ${df_mes['VALUACION INCIDENCIAS']:,.0f}", 1, 1, 'C')
                            
                            pdf.ln(3)

                            # --- SECCIÓN 3: OPERACIÓN (TARJETAS 7, 8, 9) --- [NUEVA SECCIÓN AGREGADA]
                            pdf.set_font("Arial", 'B', 11)
                            pdf.cell(0, 8, "  III. DATOS DE OPERACIÓN Y VOLUMETRÍA", 0, 1, 'L', True)
                            pdf.ln(1)
                            pdf.set_font("Arial", '', 10)
                            pdf.cell(63, 10, f"Facturacion: ${df_mes['FACTURACIÓN']:,.0f}", 1, 0, 'C')
                            pdf.cell(63, 10, f"Cajas Enviadas: {int(df_mes['CAJAS ENVIADAS']):,.0f}", 1, 0, 'C')
                            pdf.cell(63, 10, f"Gasto Flete: ${df_mes['COSTO DE FLETE']:,.0f}", 1, 1, 'C')
                            
                            pdf.ln(6)

                            # --- BLOQUE DE ANÁLISIS ---
                            pdf.set_font("Arial", 'B', 12)
                            pdf.set_text_color(30, 58, 138)
                            pdf.cell(0, 10, "DIAGNÓSTICO ESTRATÉGICO FINAL", ln=True)
                            
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font("Arial", 'I', 11)
                            pdf.set_fill_color(245, 247, 250)
                            
                            status_txt = "CRÍTICO" if df_mes['COSTO LOGÍSTICO'] > df_mes['META INDICADOR'] else "ÓPTIMO"
                            analisis_pro = (
                                f"En el periodo de {mes_sel}, la operacion registra un estado {status_txt}. "
                                f"Cada $1,000 MXN de venta consumen ${impacto_1k:.2f} de flete. "
                                f"El impacto acumulado por desviacion y mermas asciende a ${abs(df_mes['INCREMENTO + VI']):,.2f} MXN."
                            )
                            pdf.multi_cell(0, 10, analisis_pro, 1, 'L', True)

                            # --- SALIDA SEGURA ---
                            pdf_raw = pdf.output()
                            pdf_final = bytes(pdf_raw) if isinstance(pdf_raw, bytearray) else pdf_raw.encode('latin-1')
                            
                            st.download_button(
                                label="DESCARGAR REPORTE",
                                data=pdf_final,
                                file_name=f"Reporte_Elite_{mes_sel}.pdf",
                                mime="application/pdf"
                            )
                            
                        except Exception as e:
                            st.error(f"Falla en diseño: {e}")
                else:
                    st.warning("⚠️ Sistema PDF no detectado.")
            else:
                st.info("💡 **INFO DE COMANDO:** El PDF requiere una vista de mes individual.")
                  
            

            def generar_grafico_fleteras_elite_v3_final():
                import os
                import pandas as pd
                import altair as alt
                import streamlit as st
                
                try:
                    # 1. CARGA DE SEGURIDAD
                    posibles_nombres = ["matriz_mensual.scv", "matriz_mensual.csv"]
                    archivo_encontrado = next((n for n in posibles_nombres if os.path.exists(n)), None)
                    
                    if not archivo_encontrado:
                        st.error("🚨 RADAR: Base de fleteras no detectada.")
                        return
            
                    df = pd.read_csv(archivo_encontrado, encoding='latin-1')
                    df.columns = [c.strip().upper() for c in df.columns]
                    df['COSTO DE GUIA'] = pd.to_numeric(df['COSTO DE GUIA'].replace('[\$,]', '', regex=True), errors='coerce').fillna(0)
                    
                    df['FECHA DE FACTURA'] = pd.to_datetime(df['FECHA DE FACTURA'], dayfirst=True, errors='coerce')
                    df = df.dropna(subset=['FECHA DE FACTURA'])
                    df['MES_LABEL'] = df['FECHA DE FACTURA'].dt.strftime('%B').str.upper()
                    
                    # 2. FILTRO
                    meses = df['MES_LABEL'].unique().tolist()
                    sel_mes = alt.selection_point(fields=['MES_LABEL'], bind=alt.binding_select(options=meses, name="MES: "), value=meses[-1])
            
                    # 3. CONSTRUCCIÓN RESPONSIVA VERTICAL
                    base = alt.Chart(df).transform_filter(sel_mes)
            
                    columnas = base.mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10
                    ).encode(
                        x=alt.X('FLETERA:N', 
                                title=None, 
                                sort='-y',
                                scale=alt.Scale(paddingInner=0.15, paddingOuter=0.2),
                                axis=alt.Axis(
                                    labelAngle=-90, # <--- CAMBIO TÁCTICO: Títulos en Vertical
                                    labelFontSize=11, 
                                    labelColor='#FFFFFF', 
                                    labelFontWeight='bold',
                                    labelOverlap='parity'
                                )),
                        y=alt.Y('sum(COSTO DE GUIA):Q', 
                                title=None, 
                                axis=alt.Axis(format="$,.0s", gridColor='#262730', labelColor='#94a3b8')),
                        color=alt.Color('FLETERA:N', scale=alt.Scale(scheme='goldorange'), legend=None)
                    )
            
                    texto = columnas.mark_text(align='center', baseline='bottom', dy=-10, color='#FFFFFF', fontWeight='bold', fontSize=12
                    ).encode(text=alt.Text('sum(COSTO DE GUIA):Q', format="$,.2s"))
            
                    # ENSAMBLAJE
                    grafico = (columnas + texto).add_params(sel_mes).properties(
                        width='container', height=450, # Aumentamos altura para dar espacio a los títulos verticales
                        title=alt.TitleParams(text="INVERSIÓN POR FLETERA", color='#eab308', anchor='start')
                    ).configure_view(strokeWidth=0)
            
                    st.altair_chart(grafico, use_container_width=True)
            
                except Exception as e:
                    st.error(f"⚠️ FALLA EN FLETERAS: {e}")
            
            def generar_ranking_destinos_v3_final():
                import os
                try:
                    archivo = "matriz_mensual.scv" if os.path.exists("matriz_mensual.scv") else "matriz_mensual.csv"
                    df = pd.read_csv(archivo, encoding='latin-1')
                    df.columns = [c.strip().upper() for c in df.columns]
                    df['VALOR FACTURA'] = pd.to_numeric(df['VALOR FACTURA'].replace('[\$,]', '', regex=True), errors='coerce').fillna(0)
                    
                    df_geo = df.groupby('ESTADO')['VALOR FACTURA'].sum().reset_index().sort_values('VALOR FACTURA', ascending=False).head(15)
            
                    base = alt.Chart(df_geo).encode(
                        x=alt.X('ESTADO:N', 
                                title=None, 
                                sort='-y',
                                scale=alt.Scale(paddingInner=0.2),
                                axis=alt.Axis(
                                    labelAngle=-90, # <--- CAMBIO TÁCTICO: Títulos en Vertical
                                    labelFontSize=10, 
                                    labelColor='#FFFFFF',
                                    labelFontWeight='bold',
                                    labelOverlap='parity')),
                        y=alt.Y('VALOR FACTURA:Q', title=None, axis=alt.Axis(format="$,.0s", labelColor='#94a3b8'))
                    )
            
                    barras = base.mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color='#EAB308')
                    texto = base.mark_text(align='center', baseline='bottom', dy=-10, color='#FFFFFF', fontWeight='bold', fontSize=11
                    ).encode(text=alt.Text('VALOR FACTURA:Q', format="$,.2s"))
            
                    radar = (barras + texto).properties(width='container', height=450,
                        title=alt.TitleParams(text="TOP 20: FACTURACION POR DESTINOS", color='#EAB308', anchor='start')
                    ).configure_view(strokeWidth=0)
            
                    st.altair_chart(radar, use_container_width=True)
                except Exception as e:
                    st.error(f"⚠️ FALLA EN DESTINOS: {e}")
            
            # --- ACTIVACIÓN ---
            st.write("---")
            generar_grafico_fleteras_elite_v3_final()
            st.write("---")
            generar_ranking_destinos_v3_final()

            def generar_top_comercial_elite_v3():
                import os
                import pandas as pd
                import altair as alt
                import streamlit as st
                
                try:
                    # 1. LOCALIZACIÓN DE INTELIGENCIA (matriz_mensual)
                    posibles = ["matriz_mensual.csv", "matriz_mensual.scv"]
                    archivo = next((n for n in posibles if os.path.exists(n)), None)
                    
                    if not archivo:
                        st.error("🚨 RADAR: No se detectó 'matriz_mensual' en la carpeta raíz.")
                        return
            
                    # 2. PROCESAMIENTO DE DATOS
                    df = pd.read_csv(archivo, encoding='latin-1')
                    df.columns = [c.strip().upper() for c in df.columns]
                    
                    # Limpieza de valores monetarios (VALOR FACTURA)
                    if 'VALOR FACTURA' in df.columns:
                        df['VALOR FACTURA'] = pd.to_numeric(
                            df['VALOR FACTURA'].replace('[\$,]', '', regex=True), 
                            errors='coerce'
                        ).fillna(0)
                    else:
                        st.error("🚨 ERROR: No se encontró la columna 'VALOR FACTURA'.")
                        return
                        
                    # Filtro de seguridad para NOMBRE COMERCIAL
                    if 'NOMBRE COMERCIAL' not in df.columns:
                        st.error("🚨 ERROR: No se encontró la columna 'NOMBRE COMERCIAL'.")
                        return
            
                    # Agrupación y extracción del Top 20
                    df_top = df.groupby('NOMBRE COMERCIAL')['VALOR FACTURA'].sum().reset_index()
                    df_top = df_top.sort_values('VALOR FACTURA', ascending=False).head(20)
            
                    # 3. DISEÑO DE COMBATE RESPONSIVO
                    base = alt.Chart(df_top).encode(
                        x=alt.X('NOMBRE COMERCIAL:N', 
                                title=None, 
                                sort='-y',
                                scale=alt.Scale(paddingInner=0.2), 
                                axis=alt.Axis(
                                    labelAngle=-90,         # Alineación vertical táctica
                                    labelFontSize=10, 
                                    labelColor='#FFFFFF', 
                                    labelFontWeight='bold',
                                    labelOverlap='parity'
                                )),
                        y=alt.Y('VALOR FACTURA:Q', 
                                title=None, 
                                axis=alt.Axis(
                                    format="$,.0s",         # Formato compacto (k, M)
                                    gridColor='#262730', 
                                    labelColor='#94a3b8'
                                ))
                    )
            
                    # CAPA 1: Columnas "Torre de Energía"
                    columnas = base.mark_bar(
                        cornerRadiusTopLeft=8, 
                        cornerRadiusTopRight=8,
                        color='#00D4FF' # Dorado OPS
                    )
            
                    # CAPA 2: Etiquetas de Datos (Blanco Premium)
                    texto = base.mark_text(
                        align='center', 
                        baseline='bottom', 
                        dy=-10, 
                        color='#FFFFFF', 
                        fontWeight='bold', 
                        fontSize=11
                    ).encode(
                        text=alt.Text('VALOR FACTURA:Q', format="$,.2s")
                    )
            
                    # ENSAMBLAJE FINAL
                    radar_comercial = (columnas + texto).properties(
                        width='container', 
                        height=450,
                        title=alt.TitleParams(
                            text="TOP 20: FACTURACIÓN POR CLIENTE",
                            subtitle="Análisis comercial de alto nivel - Matriz Mensual",
                            fontSize=20,
                            color='#00D4FF',
                            anchor='start'
                        )
                    ).configure_view(strokeWidth=0)
            
                    st.altair_chart(radar_comercial, use_container_width=True)
            
                except Exception as e:
                    st.error(f"⚠️ FALLA EN RADAR COMERCIAL: {e}")
            
            # --- ACTIVACIÓN ---
            st.write("---")
            generar_top_comercial_elite_v3()
        
        # --- PIE DE PAGINA------------------------------------------- ---
               
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#475569; font-size:10px; margin-top:20px;'>LOGISTICS INTELLIGENCE UNIT - CONFIDENTIAL</div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # MAIN 4: LOGISTICS INTELLIGENCE HUB (MOTOR DE RECOMENDACIÓN
    # ------------------------------------------------------------------
    elif st.session_state.pagina == "HubLogistico":
        import streamlit as st
        import pandas as pd
        import datetime
        import os
        import io
        import zipfile
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        # --- FUNCIÓN DE LIMPIEZA TÁCTICA (Evita fallos de recomendación) ---
        def limpiar_texto(texto):
            if not isinstance(texto, str): return str(texto)
            # Quita acentos, convierte a mayúsculas y limpia espacios
            texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
            return texto.upper().strip()
        
        # --- RUTAS Y ESTILOS ---
        archivo_log = "log_maestro_acumulado.csv"
        
        if 'db_acumulada' not in st.session_state:
            if os.path.exists(archivo_log):
                st.session_state.db_acumulada = pd.read_csv(archivo_log)
            else:
                st.session_state.db_acumulada = pd.DataFrame()     
        
        # --- ENCABEZADO MINIMALISTA (ESTILO PRO) ---
        # --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (Sube el contenido y estiliza el menú) ---
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 0rem !important;
                    max-width: 95% !important;
                }

                .header-wrapper {
                    display: flex;
                    align-items: baseline;
                    gap: 12px;
                    font-family: 'Inter', sans-serif;
                }

                /* TITULO PRINCIPAL: Gris Oscuro */
                .header-wrapper h1 {
                    font-size: 22px !important;
                    font-weight: 800;
                    margin: 0;
                    color: #4b5563; /* Gris oscuro */
                    letter-spacing: -0.8px;
                }

                /* INDICADOR: Blanco */
                .header-wrapper span {
                    font-size: 14px;
                    font-weight: 300;
                    color: #ffffff; /* Blanco */
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                /* BOTÓN DE MENÚ MINIMALISTA */
                div[data-testid="stPopover"] > button {
                    background-color: transparent !important;
                    border: 1px solid rgba(0, 255, 162, 0.3) !important;
                    padding: 2px 10px !important;
                    border-radius: 6px !important;
                    height: 32px !important;
                    transition: all 0.3s ease;
                }
                
                div[data-testid="stPopover"] > button:hover {
                    border: 1px solid #00ffa2 !important;
                    box-shadow: 0 0 10px rgba(0, 255, 162, 0.2);
                }

                div[data-testid="stPopoverContent"] button {
                    text-align: left !important;
                    justify-content: flex-start !important;
                    border: none !important;
                    background: transparent !important;
                    font-size: 13px !important;
                    padding: 8px 10px !important;
                }

                div[data-testid="stPopoverContent"] button:hover {
                    color: #00ffa2 !important;
                    background: rgba(0, 255, 162, 0.05) !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # --- 2. POSICIONAMIENTO DEL ENCABEZADO ---
        c1, c2 = st.columns([0.88, 0.12], vertical_alignment="bottom")

        with c1:
            st.markdown("""
                <div class="header-wrapper">
                    <h1>LOGISTIC</h1>
                    <span>HUB</span>
                    <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #00ffa2; opacity: 0.7; margin-left: 10px; padding-left: 10px; border-left: 1px solid #334155;">
                        LOGÍSTICA & RENDIMIENTO
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            with st.popover("☰", use_container_width=True):
                st.markdown("<p style='color:#64748b; font-size:10px; font-weight:700; margin-bottom:10px; letter-spacing:1px;'>NAVEGACIÓN</p>", unsafe_allow_html=True)
                
                paginas = {
                    "TRACKING": ("principal", "kpi_btn_aac"),
                    "SEGUIMIENTO": ("KPIs", "kpi_btn_kpi"),
                    "REPORTE OPS": ("Reporte", "kpi_btn_rep"),
                    "HUB LOGISTIC": ("HubLogistico", "kpi_btn_hub"),
                    "OTD": ("RadarRastreo", "kpi_btn_radar")
                }

                for nombre, (v_state, v_key) in paginas.items():
                    if st.button(nombre, use_container_width=True, key=v_key):
                        st.session_state.pagina = v_state
                        st.rerun()

        # Línea divisoria
        st.markdown("<hr style='margin: 8px 0 20px 0; border: none; border-top: 1px solid rgba(148, 163, 184, 0.1);'>", unsafe_allow_html=True)       
        
        # --- FUNCIONES TÉCNICAS (SELLADO) ---
        # --- RANGOS DE CÓDIGOS POSTALES DE LA ZMG (PERÍMETROS DE SEGURIDAD) ---
        RANGOS_CP_AMG = [
            (44100, 44990),  # Guadalajara
            (45010, 45245),  # Zapopan
            (45400, 45429),  # Tonalá
            (45500, 45595)   # Tlaquepaque
        ]
        
        archivo_log = "log_maestro_acumulado.csv"
        
        # --- FUNCIONES TÉCNICAS (SELLADO CON CALIBRACIÓN) ---
        def generar_sellos_fisicos(lista_textos, x, y):
            output = PdfWriter()
            for texto in lista_textos:
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.setFont("Helvetica-Bold", 11)
                # Posicionamiento dinámico basado en sliders
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
        
        # --- RADAR DE DETECCIÓN LOCAL ---
        def detectar_local(direccion):
            dir_str = str(direccion)
            cps_encontrados = re.findall(r'\b\d{5}\b', dir_str)
            for cp_str in cps_encontrados:
                try:
                    cp_num = int(cp_str)
                    for inicio, fin in RANGOS_CP_AMG:
                        if inicio <= cp_num <= fin:
                            return "LOCAL"
                except:
                    continue
            return None
        
        # --- MOTOR DE RECOMENDACIÓN ---
        @st.cache_data
        def motor_logistico_central():
            try:
                if os.path.exists("matriz_historial.csv"):
                    h = pd.read_csv("matriz_historial.csv", encoding='utf-8-sig')
                    h.columns = h.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.strip().str.upper()
                    c_pre = [c for c in h.columns if 'PRECIO' in c][0]
                    c_flet = [c for c in h.columns if 'FLETERA' in c or 'TRANSPORTE' in c][0]
                    c_dir = [c for c in h.columns if 'DIRECCION' in c][0]
                    h[c_pre] = pd.to_numeric(h[c_pre], errors='coerce').fillna(0)
                    mejores = h.loc[h.groupby(c_dir)[c_pre].idxmin()]
                    return mejores.set_index(c_dir)[c_flet].to_dict(), mejores.set_index(c_dir)[c_pre].to_dict()
            except Exception as e:
                st.error(f"Error en matriz: {e}")
            return {}, {}
        
        d_flet, d_price = motor_logistico_central()
        
        # --- ESTILOS PERSONALIZADOS ---
        st.markdown("""
            <style>
            .main { background-color: #0e1117; }
            div[data-testid="stPopover"] > button {
                background-color: #0d1117 !important; border: 1px solid #00ffa2 !important;
                padding: 5px 15px !important; border-radius: 8px !important;
            }
            .footer-minimal {
                position: fixed; left: 0; bottom: 0; width: 100%;
                color: #555; text-align: center; font-size: 8px; padding: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # TÍTULO Y LÍNEA DE PODER
        
        
        if 'db_acumulada' not in st.session_state:
            st.session_state.db_acumulada = pd.read_csv(archivo_log) if os.path.exists(archivo_log) else pd.DataFrame()
        
        # --- CARGA Y PROCESAMIENTO ---
        file_p = st.file_uploader("1. SUBIR ARCHIVO ERP (CSV)", type="csv")
        
        if file_p:
            if "archivo_actual" not in st.session_state or st.session_state.archivo_actual != file_p.name:
                if "df_analisis" in st.session_state: del st.session_state["df_analisis"]
                st.session_state.archivo_actual = file_p.name
                st.rerun()
        
            try:
                if "df_analisis" not in st.session_state:
                    p = pd.read_csv(file_p, encoding='utf-8-sig')
                    p.columns = p.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.strip().str.upper()
                    col_id = 'FACTURA' if 'FACTURA' in p.columns else ('DOCNUM' if 'DOCNUM' in p.columns else p.columns[0])
                    
                    if 'DIRECCION' in p.columns:
                        def motor_prioridad(row):
                            es_local = detectar_local(row['DIRECCION'])
                            if es_local: return "LOCAL"
                            return d_flet.get(row['DIRECCION'], "SIN HISTORIAL")
        
                        p['RECOMENDACION'] = p.apply(motor_prioridad, axis=1)
                        p['COSTO'] = p.apply(lambda r: 0.0 if r['RECOMENDACION'] == "LOCAL" else d_price.get(r['DIRECCION'], 0.0), axis=1)
                        p['FECHA_HORA'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        cols_sistema = [col_id, 'RECOMENDACION', 'COSTO', 'FECHA_HORA']
                        otras = [c for c in p.columns if c not in cols_sistema]
                        st.session_state.df_analisis = p[cols_sistema + otras]
                
                st.markdown("### Revisar tabla con recomendaciones")
                modo_edicion = st.toggle("🔓 Activar modo edición")
                
                p_editado = st.data_editor(
                    st.session_state.df_analisis,
                    use_container_width=True,
                    num_rows="fixed",
                    column_config={
                        "RECOMENDACION": st.column_config.TextColumn("🚚 RECOMENDACION", disabled=not modo_edicion),
                        "COSTO": st.column_config.NumberColumn("💰 COSTO", format="$%.2f", disabled=not modo_edicion),
                    },
                    key="editor_pro_v11"
                )
        
                c1, c2, c3 = st.columns(3)
                with c1:
                    csv_out = p_editado.to_csv(index=False).encode('utf-8-sig')
                    # AGREGUE: use_container_width=True
                    st.download_button("Descargar Analisis", csv_out, "Analisis.csv", use_container_width=True)
                with c2:
                    # ESTE YA DEBE TENER: use_container_width=True
                    if st.button("Fijar cambios en la tabla", use_container_width=True):
                        st.session_state.df_analisis = p_editado
                        st.toast("Cambios fijados", icon="📌")
                with c3:
                    id_guardado = f"guardado_{st.session_state.archivo_actual}"
                    if st.session_state.get(id_guardado, False):
                        # PARA EL BOTÓN DESHABILITADO TAMBIÉN: use_container_width=True
                        st.button("✅ Registros Asegurados", use_container_width=True, disabled=True)
                    else:
                        if st.button("Guardar registros", use_container_width=True):
                            ant = pd.read_csv(archivo_log) if os.path.exists(archivo_log) else pd.DataFrame()
                            acum = pd.concat([ant, p_editado], ignore_index=True)
                            acum.to_csv(archivo_log, index=False, encoding='utf-8-sig')
                            st.session_state.db_acumulada = acum
                            st.session_state[id_guardado] = True
                            st.snow()
                            st.rerun()
        
            except Exception as e:
                st.error(f"Error en procesamiento: {e}")
        
        # --- SECCIÓN DE SELLADO (ORDEN VERTICAL POR BLOQUES) ---
        st.markdown("---")
        st.markdown("<h3 style='font-size: 16px; color: white; margin-bottom: 10px;'> Sistema de impresión de fleteras en factura</h3>", unsafe_allow_html=True)
        
        # PANEL DE CALIBRACIÓN DE POSICIÓN
        with st.expander("⚙️ PANEL DE CALIBRACIÓN DEL SELLO"):
            col_x, col_y = st.columns(2)
            with col_x:
                ajuste_x = st.slider("Eje X (Izquierda - Derecha)", 0, 612, 510, help="Eje horizontal: 0 es izquierda total.")
            with col_y:
                ajuste_y = st.slider("Eje Y (Abajo - Arriba)", 0, 792, 760, help="Eje vertical: 792 es el tope superior.")
        
        if not st.session_state.db_acumulada.empty:
            # --- SOBREIMPRESIÓN ---
            st.markdown("<p style='font-size: 16px; font-weight: bold; color: #FFFFFF; margin-bottom: 0px;'>Sobreimpresión (FÍSICA)</p>", unsafe_allow_html=True)
            st.info("Genera sellos para imprimir sobre papel físico.")
            if st.button("Generar PDF con fletera", use_container_width=True):
                sellos = p_editado['RECOMENDACION'].tolist() if 'p_editado' in locals() else st.session_state.db_acumulada['RECOMENDACION'].tolist()
                pdf_out = generar_sellos_fisicos(sellos, ajuste_x, ajuste_y)
                st.download_button("Descargar PDF para Impresora", pdf_out, "Sellos_Fisicos.pdf", "application/pdf", use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True) 
        
            # --- SELLADO DIGITAL ---
            st.markdown("<p style='font-size: 16px; font-weight: bold; color: #FFFFFF; margin-bottom: 0px;'>Sellado Digital (PDF)</p>", unsafe_allow_html=True)
            st.info("Estampa la fletera en sus archivos PDF digitales.")
            pdfs = st.file_uploader("Suba Facturas en PDF para sellado digital", type="pdf", accept_multiple_files=True)
            
            if pdfs:
                if st.button("Ejecutar Sellado Digital en PDFs", use_container_width=True):
                    df_referencia = p_editado if 'p_editado' in locals() else st.session_state.db_acumulada
                    col_fac = df_referencia.columns[0]
                    mapa = pd.Series(df_referencia.RECOMENDACION.values, index=df_referencia[col_fac].astype(str)).to_dict()
                    
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        for pdf in pdfs:
                            f_id = next((f for f in mapa.keys() if f in pdf.name.upper()), None)
                            if f_id:
                                zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ajuste_x, ajuste_y))
                    st.download_button("Descargar Facturas Selladas (ZIP)", z_buf.getvalue(), "Facturas_Digitalizadas.zip", use_container_width=True)
        
        with st.expander("Ver historial acumulado"):
            if not st.session_state.db_acumulada.empty:
                st.dataframe(st.session_state.db_acumulada, use_container_width=True)
                if st.button("Borrar registros"):
                    if os.path.exists(archivo_log): os.remove(archivo_log)
                    st.session_state.db_acumulada = pd.DataFrame()
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#475569; font-size:10px; margin-top:20px;'>LOGISTICS INTELLIGENCE UNIT - CONFIDENTIAL</div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # MAIN 05: SEGUIMIENTO 2 (RadarRastreo)
    # ------------------------------------------------------------------
    elif st.session_state.pagina == "RadarRastreo":
        st.components.v1.html("<script>parent.window.scrollTo(0,0);</script>", height=0)
        
        # --- 1. CONFIGURACIÓN DE ESTILOS UNIFICADA ---
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 0rem !important;
                    max-width: 95% !important;
                }
                
                /* Estilo del Header Minimalista */
                .header-wrapper {
                    display: flex;
                    align-items: baseline;
                    gap: 12px;
                    font-family: 'Inter', sans-serif;
                }

                .header-wrapper h1 {
                    font-size: 22px !important;
                    font-weight: 800;
                    margin: 0;
                    color: #4b5563; /* Gris oscuro */
                    letter-spacing: -0.8px;
                }

                .header-wrapper span {
                    font-size: 14px;
                    font-weight: 300;
                    color: #ffffff; /* Blanco */
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                /* Botón Popover Navegación */
                div[data-testid="stPopover"] > button {
                    background-color: transparent !important;
                    border: 1px solid rgba(0, 255, 162, 0.3) !important;
                    padding: 2px 10px !important;
                    border-radius: 6px !important;
                    height: 32px !important;
                    transition: all 0.3s ease;
                }
                
                div[data-testid="stPopover"] > button:hover {
                    border: 1px solid #00ffa2 !important;
                    box-shadow: 0 0 10px rgba(0, 255, 162, 0.2);
               
                }

                /* Estilo de Tarjetas de Reporte */
                .card-container { 
                    background-color: #0d1117; 
                    border-radius: 10px; 
                    padding: 15px; 
                    border: 1px solid #30363d; 
                    height: 130px; 
                    margin-bottom: 15px;
                }
                .border-red { border-left: 5px solid #fb7185; }
                .border-green { border-left: 5px solid #00ffa2; }
                .border-blue { border-left: 5px solid #38bdf8; }
                .border-purple { border-left: 5px solid #a78bfa; }
                
                .card-label { color: #8b949e; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; }
                .card-value { font-size: 1.6rem; font-weight: 800; margin: 4px 0; font-family: 'Inter', sans-serif; }
                .card-footer { color: #FFFFFF; font-size: 0.6rem; font-weight: 600; }
            </style>
        """, unsafe_allow_html=True)

       
        
        # --- 2. ENCABEZADO MINIMALISTA Y NAVEGACIÓN ---
        c1, c2 = st.columns([0.88, 0.12], vertical_alignment="bottom")

        with c1:
            st.markdown("""
                <div class="header-wrapper">
                    <h1>On-Time Delivery</h1>
                    <span> Report</span>
                    <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #00ffa2; opacity: 0.7; margin-left: 10px; padding-left: 10px; border-left: 1px solid #334155;">
                        ANÁLISIS DE EFICIENCIA & RENTABILIDAD
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            with st.popover("☰", use_container_width=True):
                st.markdown("<p style='color:#64748b; font-size:10px; font-weight:700; margin-bottom:10px; letter-spacing:1px;'>NAVEGACIÓN</p>", unsafe_allow_html=True)
                paginas = {
                    "TRACKING": ("principal", "radar_btn_aac"),
                    "SEGUIMIENTO": ("KPIs", "radar_btn_kpi"),
                    "REPORTE OPS": ("Reporte", "radar_btn_rep"),
                    "HUB LOGISTIC": ("HubLogistico", "radar_btn_hub"),
                    "OTD": ("RadarRastreo", "radar_btn_radar")
                }
                for nombre, (v_state, v_key) in paginas.items():
                    if st.button(nombre, use_container_width=True, key=v_key):
                        st.session_state.pagina = v_state
                        st.rerun()

        # Línea divisoria
        st.markdown("<hr style='margin: 8px 0 20px 0; border: none; border-top: 1px solid rgba(148, 163, 184, 0.1);'>", unsafe_allow_html=True)
        
        # 3. Función de Renderizado Interna (Blindada)====
        # ============================================================================================
        def render_card(label, value, footer, target_val=None, actual_val=None, inverse=False, border_base="border-blue"):
            if target_val is None or actual_val is None:
                color, border = "#f0f6fc", border_base
            else:
                # Lógica: Si inverse=True (ej. OTD), mayor es mejor.
                is_alert = actual_val < target_val if inverse else actual_val > target_val
                color = "#fb7185" if is_alert else "#00ffa2"
                border = "border-red" if is_alert else "border-green"
            
            st.markdown(f"""
                <div class='card-container {border} animated-card'>
                    <div class='card-label'>{label}</div>
                    <div class='card-value' style='color:{color}'>{value}</div>
                    <div class='card-footer'>{footer}</div>
                </div>
            """, unsafe_allow_html=True)
        
        # =========================================================
        # 4. MOTOR DE DATOS Y CÁLCULOS ELITE
        # =========================================================
        try:
            df_matriz = pd.read_csv("Matriz_Excel_Dashboard.csv", encoding="utf-8")
            df_matriz.columns = [str(c).strip().upper() for c in df_matriz.columns]
            
            cols_f = ['FECHA DE ENVÍO', 'PROMESA DE ENTREGA', 'FECHA DE ENTREGA REAL']
            for col in cols_f:
                df_matriz[col] = pd.to_datetime(df_matriz[col], dayfirst=True, errors='coerce')
            
            df_matriz = df_matriz.dropna(subset=['FECHA DE ENVÍO'])
            df_matriz['MES_TX'] = df_matriz['FECHA DE ENVÍO'].dt.month_name()
        
            if not df_matriz.empty:
                with st.sidebar:
                    st.markdown("<h3 style='color:#50C878;'> </h3>", unsafe_allow_html=True)
                    fletera_f = st.selectbox("Seleccionar Fletera", sorted(df_matriz['FLETERA'].unique()))
                    mes_f = st.selectbox("Mes de analisis", df_matriz['MES_TX'].unique())
        
                # Filtrado reactivo
                df_f = df_matriz[(df_matriz['MES_TX'] == mes_f) & (df_matriz['FLETERA'] == fletera_f)]
                df_mes_global = df_matriz[df_matriz['MES_TX'] == mes_f]
        
                if not df_f.empty:
                    # --- CÁLCULOS ---
                    total_enviados = len(df_f)
                    pedidos_mes_global = len(df_mes_global)
                    participacion = (total_enviados / pedidos_mes_global * 100) if pedidos_mes_global > 0 else 0
                    
                    df_costos = df_f[(df_f['COSTO DE LA GUÍA'] > 0) & (df_f['CANTIDAD DE CAJAS'] > 0)].copy()
                    costo_por_caja_prom = df_costos['COSTO DE LA GUÍA'].sum() / df_costos['CANTIDAD DE CAJAS'].sum() if not df_costos.empty else 0.0
        
                    df_entregados = df_f.dropna(subset=['FECHA DE ENTREGA REAL'])
                    total_entregados = len(df_entregados)
                    eficiencia_val = (len(df_entregados[df_entregados['FECHA DE ENTREGA REAL'] <= df_entregados['PROMESA DE ENTREGA']]) / total_entregados * 100) if total_entregados > 0 else 0.0
        
                    df_retraso = df_entregados[df_entregados['FECHA DE ENTREGA REAL'] > df_entregados['PROMESA DE ENTREGA']].copy()
                    num_retrasos = len(df_retraso)
                    dias_retraso_prom = (df_retraso['FECHA DE ENTREGA REAL'] - df_retraso['PROMESA DE ENTREGA']).dt.days.mean() if not df_retraso.empty else 0
                    lead_time_prom = (df_entregados['FECHA DE ENTREGA REAL'] - df_entregados['FECHA DE ENVÍO']).dt.days.mean() if total_entregados > 0 else 0
                    destinos = df_f.groupby('DESTINO')['COSTO DE LA GUÍA'].sum()
                    g_total = df_f['COSTO DE LA GUÍA'].sum()
        
                    # --- INICIO DE INTERFAZ DENTRO DEL CONTENEDOR ---
                    with st.container(key=f"kpi_sector_{fletera_f}_{mes_f}"):
                        # 1. ESTILOS UNIFICADOS (Fuentes y Animaciones)
                        st.markdown("""
                            <style>
                                .premium-header { color: #94a3b8; font-size: 14px !important; font-weight: 700; letter-spacing: 1.2px; margin: 30px 0 15px 0; text-transform: uppercase; }
                                .card-value { font-size: 28px !important; }
                                .card-label { font-size: 11px !important; }
                                .mosaico-container { background-color: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 30px 30px 30px 40px; text-align: justify; position: relative; overflow: hidden; }
                                .mosaico-glow { position: absolute; left: 0; top: 10%; height: 80%; width: 5px; background-color: #00ffa2; box-shadow: 0px 0px 15px #00ffa2; border-radius: 0 4px 4px 0; }
                                .mosaico-tag { display: inline; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 26px; letter-spacing: -1.5px; transition: all 0.3s ease; cursor: crosshair; }
                                .mosaico-tag:hover { color: #00FFAA !important; text-shadow: 0px 0px 8px rgba(0, 255, 170, 0.5); }
                            </style>
                        """, unsafe_allow_html=True)

                        # FILA 1: NEGOCIO
                        st.markdown("<h4 class='premium-header'>NEGOCIO Y PARTICIPACIÓN</h4>", unsafe_allow_html=True)
                        n1, n2, n3 = st.columns(3)
                        with n1: render_card("COSTO TOTAL INVERSIÓN", f"${g_total:,.0f}", f"Promedio: ${costo_por_caja_prom:,.2f}")
                        with n2: render_card("% PARTICIPACIÓN", f"{participacion:.1f}%", "Cuota de Mercado", border_base="border-purple")
                        with n3: render_card("% EFICIENCIA", f"{eficiencia_val:.1f}%", "Entregas Reales", 95, eficiencia_val, True)

                        # FILA 2: CUMPLIMIENTO
                        st.markdown("<h4 class='premium-header'>CUMPLIMIENTO Y SERVICIO</h4>", unsafe_allow_html=True)
                        c1, c2, c3 = st.columns(3)
                        with c1: render_card("OTD (PUNTUALIDAD)", f"{eficiencia_val:.1f}%", "Cumplimiento", 95, eficiencia_val, True)
                        with c2: render_card("CON RETRASO", f"{num_retrasos}", "Pedidos tarde", 0, num_retrasos)
                        with c3: render_card("RETRASO PROM.", f"{dias_retraso_prom:.1f} DÍAS", "Severidad", 1.5, dias_retraso_prom)

                        # FILA 3: OPERACIÓN
                        st.markdown("<h4 class='premium-header'>VOLUMEN Y VELOCIDAD</h4>", unsafe_allow_html=True)
                        o1, o2, o3 = st.columns(3)
                        with o1: render_card("PEDIDOS ENVIADOS", f"{total_enviados}", "Total guías")
                        with o2: render_card("LEAD TIME", f"{lead_time_prom:.1f} DÍAS", "Promedio", border_base="border-green")
                        with o3: 
                            top_dest = destinos.idxmax() if not destinos.empty else "N/A"
                            render_card("DESTINO TOP", f"{top_dest}", f"Gasto: ${destinos.max() if not destinos.empty else 0:,.0f}", border_base="border-red")

                        # --- 5. RADAR DE DESTINOS (INTEGRADO CORRECTAMENTE) ---
                        st.markdown("<h4 class='premium-header'>COBERTURA: MOSAICO DE DESTINOS</h4>", unsafe_allow_html=True)
                        
                        ciudades_raw = df_f['DESTINO'].unique()
                        ciudades_final = sorted(list(set([str(c).split(',')[0].split('-')[0].strip().upper() for c in ciudades_raw])))
                        
                        grises_elite = ["#30363d", "#484f58", "#6e7681", "#8b949e", "#21262d"]
                        html_mosaico = "<div class='mosaico-container'><div class='mosaico-glow'></div>"
                        for i, ciudad in enumerate(ciudades_final):
                            color_gris = grises_elite[i % len(grises_elite)]
                            html_mosaico += f"<span class='mosaico-tag' style='color: {color_gris};'>{ciudad.replace(' ', '')}</span> "
                        html_mosaico += "</div>"
                        
                        st.markdown(html_mosaico, unsafe_allow_html=True)

                else:
                    st.info(f"Sin registros para {fletera_f} en {mes_f}.")
        
        except Exception as e:
            st.error(f"Error crítico en el motor de datos: {e}")      
        
        # --- PIE DE PAGINA------------------------------------------- ---
                   
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#475569; font-size:10px; margin-top:20px;'>LOGISTICS INTELLIGENCE UNIT - CONFIDENTIAL</div>", unsafe_allow_html=True)
    
    # ------------------------------------------------------------------
    # MAIN 06: MATRIZ DE CONTROL (MControl) - VERSIÓN PRO CON FILTROS
    # ------------------------------------------------------------------
    elif st.session_state.pagina == "MControl":
        st.components.v1.html("<script>parent.window.scrollTo(0,0);</script>", height=0)
    
        # --- 1. CONFIGURACIÓN DE ESTILOS UNIFICADA ---
        st.markdown("""
            <style>
                /* 1. CONFIGURACIÓN DE CONTENEDOR Y TABLA */
                .block-container { padding-top: 1rem !important; max-width: 95% !important; }
                
                div[data-testid="stDataEditor"] div[role="rowgroup"] div[role="row"]:nth-child(even) {
                    background-color: rgba(255, 255, 255, 0.03) !important;
                }

                /* 2. INPUTS: FONDO GRIS MÁS CLARO Y BORDES ORIGINALES */
                .stTextInput input, .stDateInput input {
                    background-color: #2d333b !important; /* Gris más claro que el fondo general */
                    color: #ffffff !important;           /* Texto blanco para legibilidad */
                    border-radius: 8px !important;
                    border: 1px solid #444c56 !important; /* Borde sutil que permite ver alertas */
                }
                
                /* 3. ENCABEZADO ORIGINAL RIGOBERTO */
                .header-wrapper {
                    display: flex;
                    align-items: baseline;
                    gap: 12px;
                    font-family: 'Inter', sans-serif;
                }
                .header-wrapper h1 {
                    font-size: 22px !important;
                    font-weight: 800;
                    margin: 0;
                    color: #4b5563; /* Gris original */
                    letter-spacing: -0.8px;
                }
                .header-wrapper span {
                    font-size: 14px;
                    font-weight: 300;
                    color: #ffffff; /* Blanco original */
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                /* 4. BOTONES: ESTILO REDONDEADO LIMPIO */
                div.stButton > button[kind="primary"] {
                    background-color: #00ffa2 !important;
                    color: #0d1117 !important;
                    font-weight: 800 !important;
                    border: none !important;
                    height: 45px !important;
                    border-radius: 10px !important;
                }

                div.stButton > button:not([kind="primary"]) {
                    border: 1px solid #475569 !important;
                    color: #f1f5f9 !important;
                    background-color: rgba(71, 85, 105, 0.2) !important;
                    height: 45px !important;
                    border-radius: 10px !important;
                }

                /* 5. MENÚ NAVEGACIÓN (POPOVER) */
                div[data-testid="stPopover"] > button {
                    background-color: #1e293b !important;
                    border: 1px solid #334155 !important;
                    border-radius: 8px !important;
                    color: white !important;
                }

                div[data-testid="stDataEditor"] {
                    border: 1px solid #30363d !important;
                    border-radius: 12px !important;
                }
                
            </style>
            """, unsafe_allow_html=True)

        if "filtros_version" not in st.session_state:
            st.session_state.filtros_version = 0

        # --- 2. ENCABEZADO Y NAVEGACIÓN ---
        c1, c2 = st.columns([0.88, 0.12], vertical_alignment="bottom")
    
        with c1:
            st.markdown("""
                <div class="header-wrapper">
                    <h1>Matriz de Control</h1>
                    <span>NEXION</span>
                    <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #00ffa2; opacity: 0.7; margin-left: 10px; padding-left: 10px; border-left: 1px solid #334155;">
                        GESTIÓN DE SURTIDO & ASIGNACIÓN DE FLETES (SAP LIVE)
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
        with c2:
            with st.popover("☰", use_container_width=True):
                st.markdown("<p style='color:#64748b;font-size:10px;font-weight:700;margin-bottom:10px;letter-spacing:1px;'>NAVEGACIÓN</p>", unsafe_allow_html=True)
                paginas = {
                    "TRACKING": "principal", "SEGUIMIENTO": "KPIs", "REPORTE OPS": "Reporte",
                    "HUB LOGISTIC": "HubLogistico", "OTD": "RadarRastreo", "MCONTROL": "MControl"
                }
                for nombre, v_state in paginas.items():
                    if st.button(nombre, use_container_width=True, key=f"nav_{nombre.lower()}"):
                        st.session_state.pagina = v_state
                        st.rerun()
    
        st.markdown("<hr style='margin:8px 0 20px 0;border:none;border-top:1px solid rgba(148,163,184,0.1);'>", unsafe_allow_html=True)

        # --- 3. MOTOR DE DATOS ---
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            # Carga de datos con limpieza de columnas inmediata
            df_sap = conn.read(worksheet="DATOS_SAP").copy()
            df_sap.columns = df_sap.columns.str.strip()
            
            df_control = conn.read(worksheet="CONTROL_NEXION").copy()
            df_control.columns = df_control.columns.str.strip()

            # --- CORRECCIÓN CRÍTICA DE FECHAS ---
            if "DocDate" in df_sap.columns:
                df_sap["DocDate"] = pd.to_numeric(df_sap["DocDate"], errors='coerce')
                df_sap["DocDate"] = pd.to_datetime(df_sap["DocDate"], unit='D', origin='1899-12-30').dt.date

            # --- FORMATEO DE LLAVES (Para que el Merge nunca falle) ---
            # Convertimos a string, quitamos decimales (.0) y espacios
            df_sap["DocNum"] = df_sap["DocNum"].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_control["DocNum"] = df_control["DocNum"].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

            # Asegurar que las columnas de control existan en df_control
            cols_control = ["DocNum", "Fletera", "Surtidor", "Estatus", "Observaciones"]
            for col in cols_control:
                if col not in df_control.columns:
                    df_control[col] = ""

            # --- UNIÓN DE DATOS (Merge) ---
            # Usamos 'left' para mantener siempre lo de SAP y traer lo de Control
            df_master = pd.merge(df_sap, df_control[cols_control], on="DocNum", how="left")
            
            # Rellenar vacíos para que no aparezcan como 'NaN' al filtrar
            for col in ["Fletera", "Surtidor", "Estatus", "Observaciones"]:
                df_master[col] = df_master[col].fillna("").astype(str).replace(['None', 'nan', 'NaN'], '')

            # Reordenar: Control primero
            cols_sap_restantes = [c for c in df_sap.columns if c != "DocNum"]
            df_master = df_master[cols_control + cols_sap_restantes]

            # --- 4. PANEL DE HERRAMIENTAS ---
            v = st.session_state.filtros_version
            st.markdown("<p style='color:#8b949e;font-size:12px;font-weight:600;letter-spacing:0.5px;'>PANEL DE HERRAMIENTAS Y FILTROS</p>", unsafe_allow_html=True)
            
            h1, h2, h3, h4, h5 = st.columns(5)
            with h1: f_ini = st.date_input("Inicio", value=None, key=f"f_a_{v}")
            with h2: f_fin = st.date_input("Fin", value=None, key=f"f_b_{v}")
            with h3: search_sur = st.text_input("Operador Log.", key=f"inp_s_{v}")
            with h4: 
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("BORRAR FILTROS", use_container_width=True, key=f"reset_{v}"):
                    st.cache_data.clear()
                    st.session_state.filtros_version += 1
                    st.rerun()
            with h5:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                btn_save = st.button("GUARDAR CAMBIOS", use_container_width=True, type="primary", key=f"save_{v}")

            s1, s2, s3, s4 = st.columns(4)
            with s1: search_flet = st.text_input("Transporte", key=f"inp_f_{v}")
            with s2: search_doc = st.text_input("Ref. SAP", key=f"inp_d_{v}")
            with s3: search_code = st.text_input("Cod. Cliente", key=f"inp_c_{v}")
            with s4: search_name = st.text_input("Razón Social", key=f"inp_n_{v}")

            # --- 5. FILTRADO SEGURO ---
            df_filtrado = df_master.copy()
            
            if f_ini: df_filtrado = df_filtrado[df_filtrado["DocDate"] >= f_ini]
            if f_fin: df_filtrado = df_filtrado[df_filtrado["DocDate"] <= f_fin]
            if search_sur: df_filtrado = df_filtrado[df_filtrado["Surtidor"].str.contains(search_sur, case=False, na=False)]
            if search_flet: df_filtrado = df_filtrado[df_filtrado["Fletera"].str.contains(search_flet, case=False, na=False)]
            if search_doc: df_filtrado = df_filtrado[df_filtrado["DocNum"].str.contains(search_doc, case=False, na=False)]
            if search_code: df_filtrado = df_filtrado[df_filtrado["CardCode"].astype(str).str.contains(search_code, case=False, na=False)]
            if search_name:
                t_col = "CardFName" if "CardFName" in df_filtrado.columns else "CardName"
                df_filtrado = df_filtrado[df_filtrado[t_col].astype(str).str.contains(search_name, case=False, na=False)]

            # --- 6. EDITOR ---
            df_editado = st.data_editor(
                df_filtrado,
                use_container_width=True,
                num_rows="dynamic",
                key=f"ed_v_{v}_{st.session_state.get('usuario_actual', 'u')}",
                hide_index=True,
                height=550
            )
            
            # --- 7. GUARDADO ---
            if btn_save:
                with st.spinner("Sincronizando..."):
                    datos_save = df_editado[cols_control].copy()
                    datos_save = datos_save[datos_save["DocNum"] != ""]
                    conn.update(worksheet="CONTROL_NEXION", data=datos_save)
                    st.toast("✅ GUARDADO CORRECTO")
                    st.cache_data.clear()
                    st.rerun()

        except Exception as e:
            st.error(f"⚠️ Error: {e}")

        # --- 8. PIE DE PÁGINA (FUERA DEL BLOQUE TRY) ---
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align:center; color:#475569; font-size:10px; border-top: 1px solid rgba(148, 163, 184, 0.1); padding-top:10px;'>
                LOGISTICS INTELLIGENCE UNIT - NEXION CONTROL CENTER | RIGOBERTO HERNANDEZ 2026
            </div>
        """, unsafe_allow_html=True)
    
   
        


















































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































