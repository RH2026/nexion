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
    "bg": "#1B1E23",      # Fondo profundo
    "card": "#282D34",    # Color para las celdas (Azul grisáceo)
    "text": "#FFFAFA",    
    "sub": "#FFFFFF",     
    "border": "#414852",  
    "table_header": "#2D3748", # Encabezados un poco más claros
    "logo": "n1.png"
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
    background-color: #ffffff !important; 
    color: #000000 !important; 
    border-color: #ffffff !important; 
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
    border: 1px solid #2563eb !important;
    box-shadow: 0 0 0 1px #2563eb !important;
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
    background-color: #2563eb !important;
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
    background-color: rgba(37, 99, 235, 0.12) !important;
    border: 1px solid #2563eb !important;
}}

/* Focus */
div[data-baseweb="select"]:focus-within {{
    box-shadow: 0 0 0 1px #2563eb !important;
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
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:40px;height:40px;border:1px solid {vars_css['border']}; border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.10)
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
                st.image(vars_css["logo"], width=110)
                st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>SYSTEM SOLUTIONS</p>", unsafe_allow_html=True)
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
        if st.session_state.menu_main == "DASHBOARD":
            # 1. CONTENIDO DASHBOARD
                    
        
        elif st.session_state.menu_main == "SEGUIMIENTO":
            # 1. CONTENIDO SEGUIMIENTO
            
                   
            
            elif st.session_state.menu_sub == "GANTT":
                # 1. CONTENIDO GANTT                 
    
    
            
            elif st.session_state.menu_sub == "QUEJAS":
                # 1. CONTENIDO QUEJAS─
                
            else:
                st.subheader("MÓDULO DE SEGUIMIENTO")
                st.write("Seleccione una sub-categoría en la barra superior.")
    
        # 3. REPORTES
        elif st.session_state.menu_main == "REPORTES":
            
            # Aquí creamos el "espacio" para cada uno
            if st.session_state.menu_sub == "APQ":
                st.subheader("Análisis de Producto y Quejas (APQ)")
                #CONTENIDO APQ
                
    
            elif st.session_state.menu_sub == "OPS":
                st.subheader("Eficiencia Operativa (OPS)")
                # CONTENIDO OPS ---
                                            
            
            elif st.session_state.menu_sub == "OTD":
                st.subheader("On-Time Delivery (OTD)")
                # CONTENIDO OTD ----



        
    
        # ── 4. MÓDULO DE FORMATOS (BLOQUE MAESTRO CONSOLIDADO) ────────────────────
        elif st.session_state.menu_main == "FORMATOS":
            #CONTENIDO SALIDA PT
            
    
            # --- SUBSECCIÓN B: CONTRARRECIBOS (CONSOLIDADO) ---
            elif st.session_state.menu_sub == "CONTRARRECIBOS":
                # ── CONTENIDO CONTRARECIBOS
                
                
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
                #CONTENIDO SMART ROUTING
                
    
            elif st.session_state.menu_sub == "DATA MANAGEMENT":
                #CONTENIDO DATA MANAGEMENT
                
            
            elif st.session_state.menu_sub == "ORDER STAGING":
                #CONTENIDO ORDE STAGING
                
                
    
    
    # ── FOOTER FIJO (BRANDING) ────────────────────────
    st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
        <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">HERNANPHY</span>
    </div>
    """, unsafe_allow_html=True)






















