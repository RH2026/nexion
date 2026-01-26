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
    "border": "#1B1F24" if tema == "oscuro" else "#C9D1D9",
    "btn_p_bg": "#F0F6FC" if tema == "oscuro" else "#000000",
    "btn_p_txt": "#05070A" if tema == "oscuro" else "#FFFFFF"
}

# ── 3. CSS MAESTRO (TOTALMENTE LIMPIO) ────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* OCULTAR ELEMENTOS NATIVOS DE STREAMLIT */
header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"] {{
    display: none !important;
}}

/* AJUSTE DE CONTENEDOR PRINCIPAL */
.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 0rem !important;
}}

.stApp {{
    background: {vars_css["bg"]} !important;
    color: {vars_css["text"]} !important;
    font-family: 'Inter', sans-serif !important;
}}

/* NITIDEZ LOGOS */
div[data-testid='stImage'] img {{
    image-rendering: -webkit-optimize-contrast !important;
    image-rendering: crisp-edges !important;
    transform: translateZ(0);
}}

/* ESTILO DE BOTONES (IDENTICO AL DASHBOARD) */
div.stButton>button {{
    background: {vars_css["card"]} !important;
    color: {vars_css["text"]} !important;
    border: 1px solid {vars_css["border"]} !important;
    border-radius: 2px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    transition: all .3s ease;
}}

div.stButton>button:hover {{
    background: {vars_css["btn_p_bg"]} !important;
    color: {vars_css["btn_p_txt"]} !important;
    border-color: {vars_css["text"]} !important;
}}

/* OPTIMIZACIÓN DE IMPRESIÓN */
@media print {{
    .no-print, .stButton, hr, [data-testid="stHeader"] {{ display: none !important; }}
    .stApp {{ background-color: white !important; color: black !important; }}
    .block-container {{ padding: 0 !important; }}
    .print-format {{ border: 1px solid black !important; padding: 20px; }}
}}
</style>
""", unsafe_allow_html=True)

# ── 4. HEADER Y NAVEGACIÓN (CONSISTENCIA TOTAL) ───────
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="top")
with c1:
    logo_actual = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo_actual, width=140)
        st.markdown(f"""
            <div style='margin-top: -15px;'>
                <p style='font-size:9px; margin:0; letter-spacing:1px; 
                color:{vars_css['sub']}; text-transform:uppercase;'>Core Intelligence</p>
            </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown(f"<h2 style='color:{vars_css['text']}; margin:0;'>NEXION</h2>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    menu = ["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]
    for i, b in enumerate(menu):
        with cols[i]:
            if st.button(b, key=f"nav_form_{b}", use_container_width=True):
                if b != "FORMATOS": st.switch_page("dashboard.py")
                else: st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="theme_toggle"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"; st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. LÓGICA DE BÚSQUEDA (INVENTARIO.CSV) ────────────
@st.cache_data
def get_inventory():
    try: return pd.read_csv("inventario.csv")
    except: return pd.DataFrame(columns=['codigo', 'descripcion'])

df_inv = get_inventory()

# ── 6. CUERPO DEL FORMATO ────────────────────────────
st.markdown(f"<div style='text-align:center;'><p style='color:{vars_css['sub']}; font-size:11px; letter-spacing:3px; text-transform:uppercase;'>Formato de Entrega de Materiales PT</p></div>", unsafe_allow_html=True)

# Encabezado Manual
with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    fecha_entrega = h1.date_input("FECHA", value=datetime.now())
    turno = h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"])
    folio = h3.text_input("FOLIO", value="F-2026-001", disabled=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabla Dinámica de Productos
if 'data_rows' not in st.session_state:
    st.session_state.data_rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0, "MOTIVO": ""}] * 5)

edited_df = st.data_editor(
    st.session_state.data_rows,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "CODIGO": st.column_config.TextColumn("NÚMERO DE PARTE"),
        "DESCRIPCION": st.column_config.TextColumn("DESCRIPCIÓN", disabled=True),
        "CANTIDAD": st.column_config.NumberColumn("CANTIDAD SURTIDA", min_value=0),
        "MOTIVO": st.column_config.TextColumn("MOTIVO")
    },
    key="editor_entrega"
)

# Cruce automático con inventario.csv
for idx, row in edited_df.iterrows():
    cod = str(row["CODIGO"]).strip()
    if cod:
        match = df_inv[df_inv['codigo'].astype(str) == cod]
        if not match.empty:
            edited_df.at[idx, "DESCRIPCION"] = match.iloc[0]['descripcion']

# ── 7. SECCIÓN DE FIRMAS (COMO TU IMAGEN) ─────────────
st.markdown("<br><br>", unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
firma_style = f"border-top: 1px solid {vars_css['sub']}; width: 80%; margin: auto;"

with f1:
    st.markdown(f"<hr style='{firma_style}'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:10px;'>ENTREGO<br><b>Analista de Inventario</b></p>", unsafe_allow_html=True)
with f2:
    st.markdown(f"<hr style='{firma_style}'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:10px;'>AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></p>", unsafe_allow_html=True)
with f3:
    st.markdown(f"<hr style='{firma_style}'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:10px;'>RECIBIÓ<br><b>Jesus Moreno / Aux. Logística</b></p>", unsafe_allow_html=True)

# ── 8. ACCIONES ──────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
b_col1, b_col2 = st.columns(2)
with b_col1:
    if st.button("💾 REGISTRAR EN MATRIZ", use_container_width=True, type="primary"):
        st.toast("Manifest guardado satisfactoriamente.", icon="✅")
with b_col2:
    st.markdown("""
        <button onclick="window.print()" style="width:100%; height:45px; background:none; border:1px solid gray; 
        color:inherit; cursor:pointer; font-weight:700; letter-spacing:2px; text-transform:uppercase;">
            🖨️ IMPRIMIR / PDF
        </button>
    """, unsafe_allow_html=True)

    




