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
    "text": "#F0F6FC" if tema == "oscuro" else "#111111",
    "sub": "#8B949E" if tema == "oscuro" else "#2D3136",
    "border": "#1B1F24" if tema == "oscuro" else "#C9D1D9",
    "card": "#0D1117" if tema == "oscuro" else "#FFFFFF"
}

# ── 3. CSS MAESTRO + OPTIMIZACIÓN DE IMPRESIÓN ────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

@media print {{
    header, footer, [data-testid="stHeader"], .stButton, .no-print {{ display: none !important; }}
    .stApp {{ background-color: white !important; color: black !important; }}
    .block-container {{ padding: 0 !important; margin: 0 !important; }}
    table {{ width: 100% !important; border-collapse: collapse !important; }}
    th, td {{ border: 1px solid black !important; padding: 5px !important; font-size: 10px !important; }}
}}

.stApp {{ background: {vars_css["bg"]} !important; color: {vars_css["text"]} !important; font-family: 'Inter', sans-serif; }}
.block-container {{ padding-top: 1.5rem !important; }}

/* NITIDEZ LOGO */
div[data-testid='stImage'] img {{
    image-rendering: -webkit-optimize-contrast !important;
    image-rendering: crisp-edges !important;
}}
</style>
""", unsafe_allow_html=True)

# ── 4. HEADER (LOGO DINÁMICO + NAV) ──────────────────
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="top")
with c1:
    logo_actual = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo_actual, width=140)
        st.markdown(f"<p style='font-size:9px; color:{vars_css['sub']}; margin-top:-15px; letter-spacing:1px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
    except: st.title("NEXION")

with c2:
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        if cols[i].button(b, key=f"nav_{b}", use_container_width=True):
            if b != "FORMATOS": st.switch_page("dashboard.py")
            else: st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"; st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:10px 0 20px;'>", unsafe_allow_html=True)

# ── 5. CARGA DE BASE DE DATOS (INVENTARIO.CSV) ────────
@st.cache_data
def load_inventory():
    try: return pd.read_csv("inventario.csv")
    except: return pd.DataFrame(columns=['codigo', 'descripcion'])

df_inv = load_inventory()

# ── 6. CUERPO DEL FORMATO (ENTREGA DE MATERIALES PT) ──
st.markdown(f"<div style='text-align:center;'><h3 style='font-weight:300; letter-spacing:3px;'>FORMATO DE ENTREGA DE MATERIALES PT</h3></div>", unsafe_allow_html=True)

# Encabezado del Formato
with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    fecha_doc = h1.date_input("FECHA", value=datetime.now())
    turno = h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"])
    folio = h3.text_input("FOLIO", placeholder="AUTOMÁTICO", disabled=True)

st.markdown("<br>", unsafe_allow_html=True)

# Área de Tabla Dinámica (Simulando tu ejemplo de imagen)
if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame([{"NUMERO DE PARTE": "", "DESCRIPCION": "", "CANTIDAD SURTIDA": 0, "MOTIVO": ""}] * 5)

# Editor de datos con búsqueda automática
edited_df = st.data_editor(
    st.session_state.rows,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "NUMERO DE PARTE": st.column_config.TextColumn("NÚMERO DE PARTE", help="Ingresa el código del producto"),
        "DESCRIPCION": st.column_config.TextColumn("DESCRIPCIÓN", width="large", disabled=True),
        "CANTIDAD SURTIDA": st.column_config.NumberColumn("CANTIDAD SURTIDA", min_value=0),
        "MOTIVO": st.column_config.TextColumn("MOTIVO")
    },
    key="tabla_entrega"
)

# Lógica para autocompletar descripciones
for index, row in edited_df.iterrows():
    cod = str(row["NUMERO DE PARTE"]).strip()
    if cod:
        match = df_inv[df_inv['codigo'].astype(str) == cod]
        if not match.empty:
            edited_df.at[index, "DESCRIPCION"] = match.iloc[0]['descripcion']

# ── 7. FIRMAS (IGUAL QUE TU IMAGEN) ──────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)

with f1:
    st.markdown("<hr style='border-top:1px solid gray; width:80%; margin:auto;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:10px;'>ENTREGO<br><b>Analista de Inventario</b></p>", unsafe_allow_html=True)

with f2:
    st.markdown("<hr style='border-top:1px solid gray; width:80%; margin:auto;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:10px;'>AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></p>", unsafe_allow_html=True)

with f3:
    st.markdown("<hr style='border-top:1px solid gray; width:80%; margin:auto;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:10px;'>RECIBIÓ<br><b>Jesus Moreno / Aux. Logística</b></p>", unsafe_allow_html=True)

# ── 8. BOTONES DE ACCIÓN ─────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
b1, b2 = st.columns(2)
with b1:
    if st.button("💾 REGISTRAR EN SISTEMA", use_container_width=True, type="primary"):
        st.toast("Datos guardados en Matriz_Excel_Dashboard.csv", icon="✅")
with b2:
    st.markdown("""
        <button onclick="window.print()" style="width:100%; height:45px; background:none; border:1px solid gray; 
        color:inherit; cursor:pointer; font-weight:700; letter-spacing:2px; text-transform:uppercase;">
            🖨️ IMPRIMIR FORMATO
        </button>
    """, unsafe_allow_html=True)

    



