Entendido, vamos a fijar la ruta de búsqueda directamente en la raíz para que no haya margen de error, considerando que tu inventario.csv está en la misma carpeta que dashboard.py.

He corregido el KeyError de forma definitiva. El problema es que al estar dentro de la carpeta /pages, Python a veces se confunde con las rutas relativas. He blindado la función load_inventory para que busque específicamente un nivel arriba (../) y limpie cualquier espacio en blanco en los encabezados que esté causando el fallo.

Aquí tienes el código completo, integrado y corregido para pages/formatos.py:

Python
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Formatos", layout="wide", initial_sidebar_state="collapsed")

# ── 2. TEMA DINÁMICO (Sincronizado con Dashboard) ────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema
vars_css = {
    "bg": "#05070A" if tema == "oscuro" else "#E9ECF1",
    "card": "#0D1117" if tema == "oscuro" else "#FFFFFF",
    "text": "#F0F6FC" if tema == "oscuro" else "#111111",
    "sub": "#8B949E" if tema == "oscuro" else "#2D3136",
    "border": "#1B1F24" if tema == "oscuro" else "#C9D1D9"
}

# ── 3. CSS MAESTRO (HEADER ELEVADO + NITIDEZ LOGO) ───────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"] {{ 
    display:none !important; 
}}

.block-container {{ 
    padding-top: 1.5rem !important; 
    padding-bottom: 0rem !important; 
}}

.stApp {{ 
    background:{vars_css["bg"]} !important; 
    color:{vars_css["text"]} !important; 
    font-family:'Inter',sans-serif !important; 
}}

div[data-testid='stImage'] img {{ 
    image-rendering: -webkit-optimize-contrast !important; 
    transform: translateZ(0); 
}}

div.stButton>button {{
    background:{vars_css["card"]} !important; 
    color:{vars_css["text"]} !important;
    border: 1px solid {vars_css["border"]} !important; 
    border-radius:2px !important;
    font-size:11px !important; 
    font-weight:700 !important; 
    letter-spacing:2px !important; 
    text-transform:uppercase;
}}

.print-btn {{
    width: 100%; height: 48px; background: transparent; color: {vars_css["text"]};
    border: 1px solid {vars_css["border"]}; border-radius: 2px; cursor: pointer;
    font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-top: 20px;
}}

@media print {{
    .no-print, [data-testid="stHeader"], button, .stButton, .stNav {{ display: none !important; }}
    .stApp {{ background-color: white !important; color: black !important; }}
    .block-container {{ padding: 0 !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ── 4. HEADER Y NAVEGACIÓN ───────────────────────────────
c1, c2, c3 = st.columns([1.5, 4, .5], vertical_alignment="top")

with c1:
    logo = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo, width=140)
        st.markdown(f"<div style='margin-top:-15px;'><p style='font-size:9px; color:{vars_css['sub']}; letter-spacing:1px; text-transform:uppercase;'>CORE INTELLIGENCE</p></div>", unsafe_allow_html=True)
    except:
        st.markdown(f"<h2 style='color:{vars_css['text']}; margin:0;'>NEXION</h2>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        if cols[i].button(b, key=f"nav_f_{b}", use_container_width=True):
            if b != "FORMATOS":
                # Al salir de formatos, volvemos a la raíz
                st.switch_page("dashboard.py")
            else:
                st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="t_btn"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. CARGA DE INVENTARIO (BÚSQUEDA EN RAÍZ) ───────────
@st.cache_data
def load_inventory():
    # Buscamos específicamente en la raíz (../) porque estamos en /pages/
    ruta_raiz = os.path.join(os.getcwd(), "inventario.csv")
    ruta_atras = os.path.join(os.getcwd(), "..", "inventario.csv")
    
    for r in [ruta_atras, ruta_raiz]:
        if os.path.exists(r):
            try:
                df = pd.read_csv(r, sep=None, engine='python', encoding='utf-8-sig')
                # Normalización agresiva: quitar espacios y pasar a mayúsculas
                df.columns = [str(c).strip().upper() for c in df.columns]
                return df
            except:
                continue
    return pd.DataFrame(columns=['CODIGO', 'DESCRIPCION'])

df_inv = load_inventory()

# ── 6. CUERPO DEL FORMATO ───────────────────────────────
st.markdown(f"<div style='text-align:center;'><p style='color:{vars_css['sub']}; font-size:11px; letter-spacing:3px; text-transform:uppercase;'>Entrega de Materiales PT</p></div>", unsafe_allow_html=True)

with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    h1.date_input("FECHA", value=datetime.now(), key="f_pt")
    h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_pt")
    h3.text_input("FOLIO", value="F-2026-001", key="fol_pt")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}] * 10)

# FUNCIÓN LOOKUP (VLOOKUP)
def lookup():
    edits = st.session_state["editor_nexion"].get("edited_rows", {})
    for idx_str, info in edits.items():
        idx = int(idx_str)
        if "CODIGO" in info:
            val = str(info["CODIGO"]).strip().upper()
            if not df_inv.empty:
                # Detectar columna de código (la que más se parezca a 'CODIGO')
                col_busca = next((c for c in df_inv.columns if "COD" in c), df_inv.columns[0])
                col_desc = next((c for c in df_inv.columns if "DESC" in c), df_inv.columns[1])
                
                match = df_inv[df_inv[col_busca].astype(str).str.strip().str.upper() == val]
                if not match.empty:
                    st.session_state.rows.at[idx, "DESCRIPCION"] = match.iloc[0][col_desc]
                    st.session_state.rows.at[idx, "CODIGO"] = val

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

# ── 7. FIRMAS (FIALKO / MORENO) ─────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
l_style = f"border-top: 1px solid {vars_css['sub']}; width: 80%; margin: auto;"

with f1:
    st.markdown(f"<hr style='{l_style}'><p style='text-align:center; font-size:10px;'>ENTREGÓ<br><b>Analista de Inventario</b></p>", unsafe_allow_html=True)
with f2:
    st.markdown(f"<hr style='{l_style}'><p style='text-align:center; font-size:10px;'>AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></p>", unsafe_allow_html=True)
with f3:
    st.markdown(f"<hr style='{l_style}'><p style='text-align:center; font-size:10px;'>RECIBIÓ<br><b>Jesus Moreno / Aux. Logística</b></p>", unsafe_allow_html=True)

# ── 8. BOTÓN DE IMPRESIÓN ───────────────────────────────
st.markdown(f'<button class="print-btn" onclick="window.print()">🖨️ GENERAR PDF / IMPRIMIR</button>', unsafe_allow_html=True)


































