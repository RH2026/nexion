import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Formatos", layout="wide", initial_sidebar_state="collapsed")

# ── 2. TEMA ───────────────────────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema
vars_css = {
    "bg": "#05070A" if tema == "oscuro" else "#E9ECF1",
    "card": "#0D1117" if tema == "oscuro" else "#FFFFFF",
    "text": "#F0F6FC" if tema == "oscuro" else "#111111",
    "sub": "#8B949E" if tema == "oscuro" else "#2D3136",
    "border": "#1B1F24" if tema == "oscuro" else "#C9D1D9",
    "hover": "#161B22" if tema == "oscuro" else "#EBEEF2",
    "btn_p_bg": "#F0F6FC" if tema == "oscuro" else "#000000",
    "btn_p_txt": "#05070A" if tema == "oscuro" else "#FFFFFF"
}

# ── 3. CSS MAESTRO + LÓGICA DE IMPRESIÓN ──────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* ESTILO DE IMPRESIÓN (OCULTA TODO LO INNECESARIO) */
@media print {{
    header, footer, [data-testid="stHeader"], [data-testid="stSidebar"], 
    .stButton, .no-print, hr {{ display: none !important; }}
    .stApp {{ background-color: white !important; color: black !important; }}
    .print-container {{ border: 1px solid #000 !important; padding: 20px !important; }}
    .block-container {{ padding-top: 0 !important; }}
}}

:root {{
  --bg:{vars_css["bg"]}; --card:{vars_css["card"]};
  --text:{vars_css["text"]}; --sub:{vars_css["sub"]};
  --border:{vars_css["border"]}; --hover:{vars_css["hover"]};
}}

.block-container {{ padding-top: 1.5rem !important; }}

header, footer, #MainMenu, div[data-testid="stDecoration"] {{ display:none !important; }}

.stApp {{ background:var(--bg) !important; color:var(--text) !important; font-family:'Inter',sans-serif !important; }}

/* NITIDEZ LOGO */
div[data-testid='stImage'] img {{
    image-rendering: -webkit-optimize-contrast !important;
    image-rendering: crisp-edges !important;
    transform: translateZ(0);
}}

/* BOTONES */
div.stButton>button {{
    background:var(--card) !important; color:var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: 2px !important;
    font-size: 11px !important; font-weight: 700 !important; letter-spacing: 2px !important; text-transform: uppercase;
}}

div.stButton>button[kind="primary"] {{
    background: {vars_css["btn_p_bg"]} !important; color: {vars_css["btn_p_txt"]} !important;
    border: none !important; font-weight: 800 !important; height: 48px !important;
}}
</style>
""", unsafe_allow_html=True)

# ── 4. HEADER DINÁMICO (LOGO n1/n2) ──────────────────
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="top")
with c1:
    logo_actual = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo_actual, width=140)
        st.markdown(f"<div style='margin-top:-15px;'><p style='font-size:9px; color:{vars_css['sub']}; letter-spacing:1px; text-transform:uppercase;'>Core Intelligence</p></div>", unsafe_allow_html=True)
    except:
        st.markdown(f"<h2 style='color:{vars_css['text']}; margin-top:-10px;'>NEXION</h2>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        with cols[i]:
            if st.button(b, key=f"nav_form_{b}", use_container_width=True):
                if b != "FORMATOS": st.switch_page("dashboard.py")
                else: st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="theme_toggle"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. BÚSQUEDA EN INVENTARIO.CSV ────────────────────
def buscar_producto(codigo):
    try:
        df_inv = pd.read_csv("inventario.csv")
        # Asegúrate de que el CSV tenga columnas 'codigo' y 'descripcion'
        resultado = df_inv[df_inv['codigo'].astype(str) == str(codigo)]
        if not resultado.empty:
            return resultado.iloc[0]['descripcion']
    except:
        return None
    return None

# ── 6. CUERPO DEL FORMATO ────────────────────────────
st.markdown(f"<div style='text-align:center; margin-bottom:20px;'><p style='color:{vars_css['sub']}; font-size:11px; letter-spacing:3px; text-transform:uppercase;'>SALIDA PRODUCTO TERMINADO</p></div>", unsafe_allow_html=True)

# Datos Generales
with st.container(border=True):
    col_a, col_b = st.columns(2)
    with col_a:
        oc = st.text_input("ORDEN DE CARGA", placeholder="OC-XXXX", key="oc")
        fecha = st.date_input("FECHA", key="fecha")
    with col_b:
        transporte = st.selectbox("TRANSPORTE", ["UNIDAD 01", "UNIDAD 02", "EXTERNO"], key="trans")
        destino = st.text_input("DESTINO", key="dest")

# Detalle de Productos
st.markdown("---")
col_cod, col_desc, col_cant = st.columns([1, 2, 1])
with col_cod:
    codigo_input = st.text_input("CÓDIGO PT")
with col_desc:
    descripcion_auto = buscar_producto(codigo_input) if codigo_input else ""
    st.text_input("DESCRIPCIÓN", value=descripcion_auto, disabled=True)
with col_cant:
    cantidad = st.number_input("CANTIDAD", min_value=0)

# ── 7. BOTONES DE ACCIÓN ─────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
c_save, c_print = st.columns(2)

with c_save:
    if st.button("💾 GUARDAR EN SISTEMA", use_container_width=True, type="primary"):
        st.success("Manifest registrado.")

with c_print:
    # Este botón activa el menú de impresión del navegador
    st.markdown("""
        <button onclick="window.print()" style="width:100%; height:48px; background-color:transparent; 
        color:inherit; border:1px solid gray; cursor:pointer; font-weight:700; letter-spacing:2px;">
            🖨️ IMPRIMIR / PDF
        </button>
    """, unsafe_allow_html=True)

    


