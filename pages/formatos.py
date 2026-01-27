import streamlit as st
import pandas as pd
from datetime import datetime
import os
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN DE PÁGINA
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

# ── 3. CSS MAESTRO (HEADER ELEVADO + MOTOR DE IMPRESIÓN) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* OCULTAR ELEMENTOS NATIVOS */
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

/* NITIDEZ LOGO */
div[data-testid='stImage'] img {{ 
    image-rendering: -webkit-optimize-contrast !important; 
    transform: translateZ(0); 
}}

/* ESTILO DE BOTONES NATIVOS */
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

/* LÓGICA DE IMPRESIÓN PRO */
@media print {{
    .no-print, .stButton, [data-testid="stHeader"], header {{ 
        display: none !important; 
    }}
    .stApp {{ 
        background: white !important; 
        color: black !important; 
    }}
    .print-only {{
        display: block !important;
        position: relative;
    }}
    .block-container {{ padding: 0 !important; }}
}}
.print-only {{ display: none; }}
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
    menu_items = ["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]
    for i, item in enumerate(menu_items):
        if cols[i].button(item, key=f"btn_{item}", use_container_width=True):
            if item != "FORMATOS":
                st.switch_page("dashboard.py")
            else:
                st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="toggle_theme"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr class='no-print' style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. CARGA DE INVENTARIO (BÚSQUEDA EN RAÍZ) ───────────
@st.cache_data
def load_inventory():
    ruta = os.path.join(os.getcwd(), "inventario.csv")
    if not os.path.exists(ruta):
        ruta = os.path.join(os.getcwd(), "..", "inventario.csv")
    try:
        df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except:
        return pd.DataFrame(columns=['CODIGO', 'DESCRIPCION'])

df_inv = load_inventory()

# ── 6. CUERPO DEL FORMULARIO (INTERFAZ WEB) ──────────────
st.markdown("<p class='no-print' style='text-align:center; font-size:11px; letter-spacing:3px; text-transform:uppercase;'>Entrega de Materiales PT</p>", unsafe_allow_html=True)

with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    fecha_val = h1.date_input("FECHA", value=datetime.now(), key="f_input")
    turno_val = h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_input")
    folio_val = h3.text_input("FOLIO", value="F-2026-001", key="fol_input")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}] * 10)

def handle_lookup():
    edits = st.session_state["editor_pt"].get("edited_rows", {})
    for idx_str, info in edits.items():
        idx = int(idx_str)
        if "CODIGO" in info:
            val = str(info["CODIGO"]).strip().upper()
            if not df_inv.empty:
                col_cod = next((c for c in df_inv.columns if "COD" in c), df_inv.columns[0])
                col_des = next((c for c in df_inv.columns if "DESC" in c), df_inv.columns[1])
                match = df_inv[df_inv[col_cod].astype(str).str.strip().str.upper() == val]
                if not match.empty:
                    st.session_state.rows.at[idx, "DESCRIPCION"] = match.iloc[0][col_des]
                    st.session_state.rows.at[idx, "CODIGO"] = val

df_final = st.data_editor(
    st.session_state.rows,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_pt",
    on_change=handle_lookup
)

# ── 7. GENERACIÓN DEL HTML DE IMPRESIÓN (PRO RENDER) ──
# Filtramos solo las filas que tienen datos para un reporte limpio
filas_llenas = df_final[df_final["CODIGO"] != ""]
tabla_html = "".join([f"""
    <tr>
        <td style="border:1px solid black; padding:8px;">{r['CODIGO']}</td>
        <td style="border:1px solid black; padding:8px;">{r['DESCRIPCION']}</td>
        <td style="border:1px solid black; padding:8px; text-align:center;">{r['CANTIDAD']}</td>
    </tr>""" for _, r in filas_llenas.iterrows()])

form_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; padding: 20px; color: black; background: white; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid black; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background-color: #f2f2f2; border: 1px solid black; padding: 10px; text-align: left; font-size: 12px; }}
        .signatures {{ margin-top: 80px; display: flex; justify-content: space-around; text-align: center; font-size: 10px; }}
        .sig-box {{ width: 30%; border-top: 1px solid black; padding-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <div><h2 style="margin:0; letter-spacing:2px;">NEXION LOGISTICS</h2><p style="margin:0; font-size:10px;">CORE INTELLIGENCE</p></div>
        <div style="text-align: right; font-size: 12px;">
            <p style="margin:0;"><b>FOLIO:</b> {folio_val}</p>
            <p style="margin:0;"><b>FECHA:</b> {fecha_val}</p>
            <p style="margin:0;"><b>TURNO:</b> {turno_val}</p>
        </div>
    </div>
    <h3 style="text-align:center; letter-spacing:5px; margin-top:40px; text-decoration: underline;">ENTREGA DE MATERIALES PT</h3>
    <table>
        <thead><tr><th>CÓDIGO</th><th>DESCRIPCIÓN</th><th style="text-align:center;">CANTIDAD</th></tr></thead>
        <tbody>{tabla_html}</tbody>
    </table>
    <div class="signatures">
        <div class="sig-box">ENTREGÓ<br><b>Analista de Inventario</b></div>
        <div class="sig-box">AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></div>
        <div class="sig-box">RECIBIÓ<br><b>Jesus Moreno / Aux. Logística</b></div>
    </div>
</body>
</html>
"""

# ── 8. BOTÓN Y COMPONENTE DE DISPARO (RENDERIZADO FORZADO) ──
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🖨️ GENERAR FORMATO PROFESIONAL (PDF)", type="primary", use_container_width=True):
    # El IFrame aísla el contenido de Streamlit para que el navegador lo renderice 1:1
    components.html(f"{form_html}<script>window.onload = function() {{ window.print(); }}</script>", height=0)
    st.toast("Preparando documento para impresión...", icon="📄")





































