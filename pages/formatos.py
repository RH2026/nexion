import streamlit as st
import pandas as pd
import time
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Formatos", layout="wide", initial_sidebar_state="collapsed")

# ── 2. TEMA DINÁMICO ──────────────────────────────────
if "tema" not in st.session_state: st.session_state.tema = "oscuro"
tema = st.session_state.tema
vars_css = {
    "bg": "#05070A" if tema == "oscuro" else "#E9ECF1",
    "card": "#0D1117" if tema == "oscuro" else "#FFFFFF",
    "text": "#F0F6FC" if tema == "oscuro" else "#111111",
    "sub": "#8B949E" if tema == "oscuro" else "#2D3136",
    "border": "#1B1F24" if tema == "oscuro" else "#C9D1D9"
}

# ── 3. CSS MAESTRO (TOTALMENTE LIMPIO + FIX IMPRESIÓN) ─
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* OCULTAR ELEMENTOS NATIVOS */
header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"] {{
    display: none !important;
}}

.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 0rem !important;
}}

.stApp {{
    background: {vars_css["bg"]} !important;
    color: {vars_css["text"]} !important;
    font-family: 'Inter', sans-serif !important;
}}

/* NITIDEZ LOGO */
div[data-testid='stImage'] img {{
    image-rendering: -webkit-optimize-contrast !important;
    image-rendering: crisp-edges !important;
    transform: translateZ(0);
}}

/* BOTÓN DE IMPRESIÓN ESTILO NEXION */
.print-btn {{
    width: 100%;
    height: 48px;
    background-color: transparent;
    color: {vars_css["text"]};
    border: 1px solid {vars_css["border"]};
    border-radius: 2px;
    cursor: pointer;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 20px;
    transition: all 0.3s ease;
}}

.print-btn:hover {{
    background-color: {vars_css["text"]};
    color: {vars_css["bg"]};
}}

@media print {{
    header, footer, .no-print, [data-testid="stHeader"], button, .stButton {{ display: none !important; }}
    .stApp {{ background-color: white !important; color: black !important; }}
    .block-container {{ padding: 0 !important; }}
    hr {{ border-top: 1px solid #000 !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ── 4. HEADER ────────────────────────────────────────
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="top")
with c1:
    logo_actual = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo_actual, width=140)
        st.markdown(f"<div style='margin-top:-15px;'><p style='font-size:9px; color:{vars_css['sub']}; letter-spacing:1px; text-transform:uppercase;'>Core Intelligence</p></div>", unsafe_allow_html=True)
    except:
        st.markdown(f"<h2 style='color:{vars_css['text']}; margin:0;'>NEXION</h2>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    menu_names = ["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]
    for i, b in enumerate(menu_names):
        with cols[i]:
            if st.button(b, key=f"nav_fmt_{b}", use_container_width=True):
                if b != "FORMATOS": st.switch_page("dashboard.py")
                else: st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="t_btn_fmt"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"; st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. CARGA DE INVENTARIO (PROTECCIÓN CONTRA KEYERROR) ──
@st.cache_data
def get_inventory():
    rutas = ["inventario.csv", "../inventario.csv", "pages/inventario.csv"]
    for r in rutas:
        try: 
            # sep=None permite detectar si es , o ; automáticamente
            df = pd.read_csv(r, sep=None, engine='python')
            # Forzamos limpieza de nombres de columnas
            df.columns = df.columns.str.strip().str.lower()
            return df
        except: continue
    return pd.DataFrame(columns=['codigo', 'descripcion'])

df_inv = get_inventory()

# ── 6. CUERPO DEL FORMATO ────────────────────────────
st.markdown(f"<div style='text-align:center;'><p style='color:{vars_css['sub']}; font-size:11px; letter-spacing:3px; text-transform:uppercase;'>Entrega de Materiales PT</p></div>", unsafe_allow_html=True)

with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    fecha = h1.date_input("FECHA", key="f_pt_date")
    turno = h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO"], key="t_pt_sel")
    folio = h3.text_input("FOLIO", value="F-2026-001", key="fol_pt_in")

# Inicializar datos en sesión para el editor
if 'data_rows' not in st.session_state:
    st.session_state.data_rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}] * 8)

# EDITOR DE DATOS
edited_df = st.data_editor(
    st.session_state.data_rows,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "CODIGO": st.column_config.TextColumn("CÓDIGO / PARTE"),
        "DESCRIPCION": st.column_config.TextColumn("DESCRIPCIÓN"),
        "CANTIDAD": st.column_config.NumberColumn("CANTIDAD")
    },
    key="editor_pt_final"
)

# LÓGICA DE BÚSQUEDA AUTOMÁTICA
if not df_inv.empty and 'codigo' in df_inv.columns:
    for idx, row in edited_df.iterrows():
        cod = str(row["CODIGO"]).strip()
        if cod:
            # Buscamos ignorando espacios y asegurando que ambos sean texto
            match = df_inv[df_inv['codigo'].astype(str).str.strip() == cod]
            if not match.empty and 'descripcion' in df_inv.columns:
                desc_encontrada = match.iloc[0]['descripcion']
                if edited_df.at[idx, "DESCRIPCION"] != desc_encontrada:
                    edited_df.at[idx, "DESCRIPCION"] = desc_encontrada

# ── 7. FIRMAS ────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
linea_firma = f"border-top: 1px solid {vars_css['sub']}; width: 80%; margin: auto;"

with f1:
    st.markdown(f"<hr style='{linea_firma}'><p style='text-align:center; font-size:10px;'>ENTREGÓ</p>", unsafe_allow_html=True)
with f2:
    st.markdown(f"<hr style='{linea_firma}'><p style='text-align:center; font-size:10px;'>AUTORIZÓ</p>", unsafe_allow_html=True)
with f3:
    st.markdown(f"<hr style='{linea_firma}'><p style='text-align:center; font-size:10px;'>RECIBIÓ</p>", unsafe_allow_html=True)

# ── 8. BOTÓN DE IMPRESIÓN ────────────────────────────
st.markdown(f"""
    <button class="print-btn" onclick="window.print()">
        🖨️ GENERAR PDF / IMPRIMIR
    </button>
""", unsafe_allow_html=True)

    










