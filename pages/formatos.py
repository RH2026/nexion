import streamlit as st
import pandas as pd
import time
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA (Idéntica a Dashboard)
st.set_page_config(page_title="NEXION | Formatos", layout="wide", initial_sidebar_state="collapsed")

# ── 2. TEMA DINÁMICO (Sincronizado con Dashboard) ────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema

if tema == "oscuro":
    vars_css = {
        "bg": "#05070A", "card": "#0D1117",
        "text": "#F0F6FC", "sub": "#8B949E",
        "border": "#1B1F24", "hover": "#161B22",
        "btn_p_bg": "#F0F6FC", "btn_p_txt": "#05070A"
    }
else:
    vars_css = {
        "bg": "#E9ECF1", "card": "#FFFFFF",
        "text": "#111111", "sub": "#2D3136",
        "border": "#C9D1D9", "hover": "#EBEEF2",
        "btn_p_bg": "#000000", "btn_p_txt": "#FFFFFF"
    }

# ── 3. CSS MAESTRO (HEADER ELEVADO + NITIDEZ LOGO) ───────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

:root {{
  --bg:{vars_css["bg"]}; --card:{vars_css["card"]};
  --text:{vars_css["text"]}; --sub:{vars_css["sub"]};
  --border:{vars_css["border"]}; --hover:{vars_css["hover"]};
  --btnp-bg:{vars_css["btn_p_bg"]}; --btnp-txt:{vars_css["btn_p_txt"]};
}}

.block-container {{ padding-top: 1.5rem !important; padding-bottom: 0rem !important; }}

header, footer, #MainMenu, div[data-testid="stDecoration"] {{ display:none !important; }}

.stApp {{
  background:var(--bg) !important;
  color:var(--text) !important;
  font-family:'Inter',sans-serif !important;
}}

/* BOTONES ESTILO NEXION */
div.stButton>button {{
  background:var(--card) !important;
  color:var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius:2px !important;
  font-size:11px !important;
  font-weight:700 !important;
  letter-spacing:2px !important;
  text-transform:uppercase;
}}

div.stButton>button:hover {{ background:var(--hover) !important; border-color:var(--text) !important; }}

/* ESTILO PARA TABLA (DATA EDITOR) */
div[data-testid="stDataEditor"] {{ border: 1px solid var(--border) !important; }}

/* BOTÓN DE IMPRESIÓN PERSONALIZADO */
.print-btn {{
    width: 100%; height: 48px; background-color: transparent; 
    color: var(--text); border: 1px solid var(--border); 
    border-radius: 2px; cursor: pointer; font-weight: 700; 
    letter-spacing: 2px; text-transform: uppercase; margin-top: 20px;
}}

@media print {{
    .no-print, [data-testid="stHeader"], button, .stButton {{ display: none !important; }}
    .stApp {{ background-color: white !important; color: black !important; }}
    .block-container {{ padding: 0 !important; }}
    hr {{ border-top: 1px solid #000 !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ── 4. HEADER Y NAVEGACIÓN (ELEVAR HEADER) ───────────────
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="top")

with c1:
    logo_actual = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo_actual, width=140)
        st.markdown(f"<div style='margin-top: -15px;'><p style='font-size:9px; color:{vars_css['sub']}; letter-spacing:1px; text-transform:uppercase;'>Core Intelligence</p></div>", unsafe_allow_html=True)
        st.markdown("<style>div[data-testid='stImage'] img { image-rendering: -webkit-optimize-contrast !important; }</style>", unsafe_allow_html=True)
    except:
        st.markdown(f"<h2 style='color:{vars_css['text']}; margin:0;'>NEXION</h2>", unsafe_allow_html=True)

with c2:
    # Menú Principal que redirige a dashboard.py
    cols = st.columns(4)
    menu = ["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]
    for i, b in enumerate(menu):
        with cols[i]:
            if st.button(b, key=f"nav_f_{b}", use_container_width=True):
                # Si presionamos cualquier cosa que no sea FORMATOS, volvemos a la raíz
                if b != "FORMATOS":
                    st.switch_page("dashboard.py")
                else:
                    st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="theme_f"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"; st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. CARGA DE INVENTARIO (PROTECCIÓN TOTAL) ───────────
@st.cache_data
def get_inventory():
    for r in ["inventario.csv", "../inventario.csv"]:
        try: 
            df = pd.read_csv(r, sep=None, engine='python')
            df.columns = df.columns.str.strip().str.upper() # CODIGO, DESCRIPCION
            return df
        except: continue
    return pd.DataFrame(columns=['CODIGO', 'DESCRIPCION'])

df_inv = get_inventory()

# ── 6. CUERPO DEL FORMATO: SALIDA PT ────────────────────
st.markdown(f"<div style='text-align:center;'><p style='color:{vars_css['sub']}; font-size:11px; letter-spacing:3px; text-transform:uppercase;'>Formato de Entrega de Materiales PT</p></div>", unsafe_allow_html=True)

with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    h1.date_input("FECHA", value=datetime.now(), key="f_pt")
    h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_pt")
    h3.text_input("FOLIO", value="F-2026-001", key="fol_pt")

# Lógica de Datos
if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}] * 10)

# BUSQUEDA AUTOMÁTICA (on_change)
def lookup():
    edits = st.session_state["editor_nexion"].get("edited_rows", {})
    for idx_str, info in edits.items():
        idx = int(idx_str)
        if "CODIGO" in info:
            val = str(info["CODIGO"]).strip().upper()
            if not df_inv.empty:
                match = df_inv[df_inv['CODIGO'].astype(str).str.strip().str.upper() == val]
                if not match.empty:
                    st.session_state.rows.at[idx, "DESCRIPCION"] = match.iloc[0]['DESCRIPCION']
                    st.session_state.rows.at[idx, "CODIGO"] = val

# Editor de datos
st.data_editor(
    st.session_state.rows,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "CODIGO": st.column_config.TextColumn("CÓDIGO / PARTE"),
        "DESCRIPCION": st.column_config.TextColumn("DESCRIPCIÓN"),
        "CANTIDAD": st.column_config.NumberColumn("CANTIDAD")
    },
    key="editor_nexion",
    on_change=lookup
)

# ── 7. FIRMAS OFICIALES ────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
l_style = f"border-top: 1px solid {vars_css['sub']}; width: 80%; margin: auto;"

with f1:
    st.markdown(f"<hr style='{l_style}'><p style='text-align:center; font-size:10px;'>ENTREGÓ<br><b>Analista de Inventario</b></p>", unsafe_allow_html=True)
with f2:
    st.markdown(f"<hr style='{l_style}'><p style='text-align:center; font-size:10px;'>AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></p>", unsafe_allow_html=True)
with f3:
    st.markdown(f"<hr style='{l_style}'><p style='text-align:center; font-size:10px;'>RECIBIÓ<br><b>Jesus Moreno / Aux. Logística</b></p>", unsafe_allow_html=True)

# ── 8. BOTÓN IMPRESIÓN ─────────────────────────────────
st.markdown(f'<button class="print-btn" onclick="window.print()">🖨️ GENERAR PDF / IMPRIMIR</button>', unsafe_allow_html=True)


































