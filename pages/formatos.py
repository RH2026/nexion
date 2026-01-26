import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Formatos", layout="wide", initial_sidebar_state="collapsed")

# ── 2. GESTIÓN DE TEMA (IGUAL AL CORE) ────────────────
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
        "bg": "#E9ECF1", # Gris Humo (tu tono preferido)
        "card": "#FFFFFF",
        "text": "#111111", 
        "sub": "#2D3136",
        "border": "#C9D1D9", "hover": "#EBEEF2",
        "btn_primary_bg": "#000000",
        "btn_primary_txt": "#FFFFFF"
    }

# ALIAS DE COMPATIBILIDAD
bg_color = vars_css["bg"]
card_bg = vars_css["card"]
text_main = vars_css["text"]
text_sub = vars_css["sub"]
border_color = vars_css["border"]
btn_hover = vars_css["hover"]
btn_primary_bg = vars_css["btn_primary_bg"]
btn_primary_txt = vars_css["btn_primary_txt"]

# ── 3. CSS MAESTRO (IDÉNTICO AL CORE) ────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

:root {{
  --bg:{bg_color}; --card:{card_bg};
  --text:{text_main}; --sub:{text_sub};
  --border:{border_color}; --hover:{btn_hover};
  --btnp-bg:{btn_primary_bg}; --btnp-txt:{btn_primary_txt};
}}

header, footer, #MainMenu, div[data-testid="stDecoration"] {{
  display:none !important;
}}

.stApp {{
  background:var(--bg) !important;
  color:var(--text) !important;
  font-family:'Inter',sans-serif !important;
}}

div.stButton>button,
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div {{
  background:var(--card) !important;
  color:var(--text) !important;
  border:1px solid var(--border) !important;
  border-radius:2px !important;
  font-size:11px !important;
  font-weight:700 !important;
  letter-spacing:2px !important;
  text-transform:uppercase;
}}

div.stButton>button:hover {{
  background:var(--hover) !important;
  border-color:var(--text) !important;
}}

div.stButton>button[kind="primary"] {{
  background:var(--btnp-bg) !important;
  color:var(--btnp-txt) !important;
  border:none !important;
  font-weight:800 !important;
  height:48px !important;
}}

div[data-testid="stSelectbox"] label p {{
  font-size:10px !important;
  color:var(--text) !important;
  font-weight: 800 !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
}}
</style>
""", unsafe_allow_html=True)

# ── 4. LÓGICA DE SPLASH (INDIVIDUAL PARA ESTA PÁGINA) ──
if "splash_formatos" not in st.session_state:
    st.session_state.splash_formatos = False

if not st.session_state.splash_formatos:
    p = st.empty()
    with p.container():
        for m in ["ACCESSING DOCUMENT CORE", "LOADING OPERATIONAL TEMPLATES", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="width:40px;height:40px;border:1px solid var(--border);
              border-top:1px solid var(--text);border-radius:50%;animation:spin 1s linear infinite;"></div>
              <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:var(--text);">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.8)
    st.session_state.splash_formatos = True
    st.rerun()

# ── 5. HEADER Y NAVEGACIÓN (CONSISTENCIA TOTAL) ────────
c1,c2,c3 = st.columns([1.5,4,.5])
with c1:
    st.markdown(f"<h2 style='letter-spacing:4px;font-weight:300;margin:0;'>NEXION</h2>"
                f"<p style='font-size:9px;margin-top:-5px;letter-spacing:1px;color:{text_sub};'>CORE INTELLIGENCE</p>",
                unsafe_allow_html=True)

with c2:
    # Mantenemos el estado de la página para que el usuario pueda volver
    cols = st.columns(4)
    for i,b in enumerate(["RASTREO","INTELIGENCIA","REPORTES","FORMATOS"]):
        with cols[i]:
            if st.button(b, key=f"nav_form_{b}", use_container_width=True):
                st.session_state.pagina=b
                # Si elige algo distinto a FORMATOS, regresa al archivo principal
                if b != "FORMATOS":
                    st.switch_page("dashboard.py")
                else:
                    st.rerun()

with c3:
    if st.button("☀️" if tema=="oscuro" else "🌙", key="theme_toggle_form"):
        st.session_state.tema = "claro" if tema=="oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {border_color};margin:10px 0 30px;'>", unsafe_allow_html=True)

# ── 6. CUERPO DE LA PÁGINA (SALIDA PT) ────────────────
st.markdown(f"""
    <div style='text-align: center; margin-bottom: 40px;'>
        <p style='color: {text_sub}; font-size: 11px; letter-spacing: 3px; text-transform: uppercase;'>Documento Activo</p>
        <h3 style='font-weight: 300; letter-spacing: 2px;'>SALIDA DE PRODUCTO TERMINADO (PT)</h3>
    </div>
""", unsafe_allow_html=True)

# Ejemplo de Formulario con tu estilo
with st.container():
    col_a, col_b = st.columns(2)
    with col_a:
        st.text_input("ORDEN DE CARGA", placeholder="Ej: OC-9988")
        st.date_input("FECHA DE SALIDA")
    with col_b:
        st.selectbox("CHOFER / TRANSPORTISTA", ["UNIDAD 01", "UNIDAD 02", "EXTERNO"])
        st.text_input("DESTINO FINAL")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("GUARDAR Y GENERAR FOLIO", type="primary", use_container_width=True):
        st.success("Formato guardado en sistema.")
