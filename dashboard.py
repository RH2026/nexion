import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA ACTUALIZADO (GRIS HUMO + TEXTO ALTO CONTRASTE) ────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema

if tema == "oscuro":
    vars_css = {
        "bg": "#05070A", "card": "#0D1117",
        "text": "#F0F6FC", "sub": "#8B949E",
        "border": "#1B1F24", "hover": "#161B22",
        "btn_primary_bg": "#F0F6FC", "btn_primary_txt": "#05070A"
    }
else:
    vars_css = {
        "bg": "#E9ECF1", 
        "card": "#FFFFFF",
        "text": "#111111", 
        "sub": "#2D3136", 
        "border": "#C9D1D9", 
        "hover": "#EBEEF2",
        "btn_primary_bg": "#000000",
        "btn_primary_txt": "#FFFFFF"
    }

# ── ALIAS DE COMPATIBILIDAD
bg_color      = vars_css["bg"]
card_bg      = vars_css["card"]
text_main    = vars_css["text"]
text_sub     = vars_css["sub"]
border_color = vars_css["border"]
btn_hover    = vars_css["hover"]
btn_primary_bg  = vars_css["btn_primary_bg"]
btn_primary_txt = vars_css["btn_primary_txt"]


# ── 3. CSS MAESTRO (CON HOVER DE ALTO CONTRASTE INVERTIDO) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

:root {{
  --bg: {bg_color}; 
  --card: {card_bg};
  --text: {text_main}; 
  --sub: {text_sub};
  --border: {border_color}; 
  --btnp-bg: {btn_primary_bg};
  --btnp-txt: {btn_primary_txt};
}}

/* ELEVAR HEADER Y OCULTAR ELEMENTOS NATIVOS */
header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .viewerBadge_container__1QSob {{ 
    display:none !important; 
}}

.block-container {{ 
    padding-top: 1.5rem !important; 
    padding-bottom: 0rem !important; 
}}

/* TRANSICIONES GLOBALES */
* {{
    transition: background-color .35s ease, color .35s ease, border-color .35s ease;
}}

.stApp {{ 
    background: var(--bg) !important; 
    color: var(--text) !important; 
    font-family: 'Inter', sans-serif !important; 
}}

/* FIX: VISIBILIDAD DE LETRAS (LABELS) */
[data-testid="stWidgetLabel"] p {{
    color: var(--text) !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
}}

/* NITIDEZ LOGO */
div[data-testid='stImage'] img {{ 
    image-rendering: -webkit-optimize-contrast !important; 
    transform: translateZ(0); 
}}

/* BOTONES CON ESTILO BASE */
div.stButton>button,
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div {{
    background: var(--card) !important; 
    color: var(--text) !important;
    border: 1px solid var(--border) !important; 
    border-radius: 2px !important;
    font-size: 11px !important; 
    font-weight: 700 !important; 
    letter-spacing: 2px !important; 
    text-transform: uppercase;
    width: 100%;
}}

/* ── EL CAMBIO CLAVE: HOVER INVERTIDO ── */
div.stButton>button:hover {{
    background: var(--text) !important;   /* Fondo blanco en oscuro / negro en claro */
    color: var(--bg) !important;         /* Letra negra en oscuro / blanca en claro */
    border-color: var(--text) !important;
}}

/* BOTÓN PRIMARIO MANTIENE SU IDENTIDAD */
div.stButton>button[kind="primary"] {{
    background: var(--btnp-bg) !important;
    color: var(--btnp-txt) !important;
    border: none !important;
    font-weight: 800 !important;
    height: 48px !important;
}}

/* INPUTS */
.stTextInput input {{
    background: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    height: 48px !important;
}}
</style>
""", unsafe_allow_html=True)

# ── SPLASH (MANTENIDO) ───────────────────────────────────
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS","PARSING LOGISTICS DATA","SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="width:40px;height:40px;border:1px solid var(--border);
              border-top:1px solid var(--text);border-radius:50%;animation:spin 1s linear infinite;"></div>
              <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:var(--text);">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.9)
    st.session_state.splash_completado = True
    st.rerun()

# ── 5. HEADER Y NAVEGACIÓN (AJUSTE DE ALTURA) ───────────────
# vertical_alignment="top" asegura que el menú suba al nivel del logo
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="top")

with c1:
    logo_actual = "n1.png" if tema == "oscuro" else "n2.png"
    
    try:
        # Renderizado del Logo
        st.image(logo_actual, width=140)
        
        # El lema con color dinámico
        st.markdown(f"""
            <div style='margin-top: -15px;'>
                <p style='font-size:9px; margin:0; letter-spacing:1px; 
                color:{text_sub}; text-transform:uppercase; font-family: "Inter", sans-serif;'>
                    Core Intelligence
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # AJUSTE DE POSICIÓN + TRUCO DE NITIDEZ (Smoothing)
        st.markdown(f"""
            <style>
                div[data-testid='stImage'] {{
                    margin-top: -15px !important; 
                    margin-bottom: 0px !important;
                }}
                div[data-testid='stImage'] img {{
                    image-rendering: -webkit-optimize-contrast !important; /* Nitidez Chrome/Safari */
                    image-rendering: crisp-edges !important;               /* Nitidez Firefox */
                    transform: translateZ(0);                               /* Fuerza aceleración GPU */
                }}
            </style>
        """, unsafe_allow_html=True)
    except:
        st.markdown(f"<h2 style='letter-spacing:4px; font-weight:300; margin-top:-10px; color:{text_main};'>NEXION</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:9px; margin-top:-5px; color:{text_sub};'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)

with c2:
    if "pagina" not in st.session_state: 
        st.session_state.pagina = "RASTREO"
    
    # Menú Principal
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        with cols[i]:
            if st.button(b, use_container_width=True, key=f"main_nav_{b}"):
                st.session_state.pagina = b
                st.rerun()

with c3:
    # Ajuste de botón de tema para mantener la línea
    if st.button("☀️" if tema == "oscuro" else "🌙", key="theme_toggle"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
        st.rerun()

# Línea divisoria más pegada al menú para ahorrar espacio
st.markdown(f"<hr style='border-top:1px solid {border_color}; margin:5px 0 20px;'>", unsafe_allow_html=True)


# 7. RENDERIZADO RASTREO (CAJA DE BÚSQUEDA DHL)
if st.session_state.pagina == "RASTREO":
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    
    # --- CAJA DE BÚSQUEDA CENTRALIZADA (MINIMALISTA ZARA/DHL STYLE) ---
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    
    _, col_search, _ = st.columns([1, 1.8, 1])
    
    with col_search:
        # Título Operacional con tracking extendido
        st.markdown(f"""
            <p style='
                text-align: center; 
                color: {text_sub}; 
                font-size: 15px; 
                letter-spacing: 10px; 
                text-transform: uppercase; 
                font-weight: 300;
                margin-bottom: 20px;'>
                O P E R A T I O N A L &nbsp; Q U E R Y
            </p>
        """, unsafe_allow_html=True)
        
        # Input de búsqueda (El estilo ya viene del CSS Maestro que inyectamos)
        busqueda = st.text_input("", placeholder="REFERENCIA O NÚMERO DE GUÍA...", label_visibility="collapsed")
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        # Botón de ejecución (Primary)
        btn_search = st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True)
    
    st.markdown("<div style='margin-bottom: 80px;'></div>", unsafe_allow_html=True)


    








































































































































































































































































































































































































