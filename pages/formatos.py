import streamlit as st
import pandas as pd
from datetime import datetime
import os
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Automatizacion de Procesos", layout="wide", initial_sidebar_state="collapsed")

# ── 2. TEMA DINÁMICO ────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema

if tema == "oscuro":
    v = {
        "bg": "#05070A", 
        "card": "#0D1117", 
        "text": "#F0F6FC", 
        "sub": "#8B949E", 
        "border": "#1B1F24"
    }
else:
    v = {
        "bg": "#E9ECF1", 
        "card": "#FFFFFF", 
        "text": "#111111", 
        "sub": "#2D3136", 
        "border": "#C9D1D9"
    }

# ── 3. CSS MAESTRO (ALINEACIÓN DE LOGO Y UNIFICACIÓN TOTAL) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* 1. LIMPIEZA Y OCULTAR ELEMENTOS NATIVOS */
header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"] {{ 
    display:none !important; 
}}

.block-container {{ 
    padding-top: 1rem !important; 
    padding-bottom: 0rem !important;
}}

/* 2. FONDO Y TEXTO GLOBAL */
.stApp {{ 
    background: {v["bg"]} !important; 
    color: {v["text"]} !important; 
    font-family: 'Inter', sans-serif !important; 
}}

/* 3. ARREGLO DE ALINEACIÓN LOGO Y SUBTÍTULO */
div[data-testid="stImage"] {{
    text-align: left !important;
    width: fit-content !important;
}}

div[data-testid="stImage"] img {{ 
    image-rendering: -webkit-optimize-contrast !important; 
    transform: translateZ(0);
    margin-left: 0 !important;
}}

.stMarkdown p {{
    margin-left: 0 !important;
    text-align: left !important;
}}

/* 4. TÍTULOS DE CAMPOS */
[data-testid="stWidgetLabel"] p {{
    color: {v["text"]} !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    text-align: left !important;
}}

/* 5. UNIFICACIÓN DE CAJAS (CORREGIDO PARA GROSOR IDENTICO) */
/* Aplicamos el borde al contenedor raíz de cada widget para que pesen lo mismo visualmente */
div[data-baseweb="input"], 
div[data-baseweb="select"] > div, 
div[data-baseweb="calendar"] {{
    background-color: {v["card"]} !important;
    border: 1px solid {v["border"]} !important; /* Mismo grosor para todos */
    border-radius: 4px !important;
    min-height: 42px !important;
}}

/* Forzamos que los inputs internos no tengan borde propio para no sumar grosores */
.stTextInput input, .stDateInput input {{
    border: none !important;
    background-color: transparent !important;
    color: {v["text"]} !important;
}}

/* Ajuste específico para el texto del selectbox */
div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    color: {v["text"]} !important;
}}

/* 6. BOTONES CON HOVER INVERTIDO */
div.stButton>button {{
    background: {v["card"]} !important; 
    color: {v["text"]} !important;
    border: 1px solid {v["border"]} !important;
    border-radius: 4px !important;
    width: 100%;
    transition: all .3s ease;
    height: 42px !important;
}}

div.stButton>button:hover {{
    background: {v["text"]} !important;
    color: {v["bg"]} !important;
    border-color: {v["text"]} !important;
}}

</style>
""", unsafe_allow_html=True)

# ── 4. HEADER Y NAVEGACIÓN (Título Visual Actualizado) ───
c1, c2, c3 = st.columns([2, 3.5, .5], vertical_alignment="top")
with c1:
    logo = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo, width=140)
        # Actualización de subtítulo visual
        st.markdown(f"<div style='margin-top:-15px;'><p style='font-size:9px; color:{v['sub']}; letter-spacing:1px; text-transform:uppercase;'>Automatización de Procesos</p></div>", unsafe_allow_html=True)
    except: 
        st.markdown(f"<h2 style='color:{v['text']}; margin:0;'>NEXION</h2>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        if cols[i].button(b, key=f"nav_{b}", use_container_width=True):
            if b != "FORMATOS": st.switch_page("dashboard.py")
            else: st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="t_btn"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"; st.rerun()

st.markdown(f"<hr style='border-top:1px solid {v['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. TÍTULO MINIMALISTA (ZARA / DHL STYLE) ──────────
st.markdown(f"""
    <div style="text-align: center; margin-top: 10px; margin-bottom: 25px;">
        <h1 style="font-weight: 300; letter-spacing: 12px; text-transform: uppercase; font-size: 15px; color: {v['text']}; opacity: 0.9;">
            E N T R E G A &nbsp; D E &nbsp; M A T E R I A L E S &nbsp; P T
        </h1>
    </div>
""", unsafe_allow_html=True)


# ── 5. CARGA DE INVENTARIO (RAÍZ) ──────────────────────
@st.cache_data
def load_inventory():
    ruta = os.path.join(os.getcwd(), "inventario.csv")
    if not os.path.exists(ruta): ruta = os.path.join(os.getcwd(), "..", "inventario.csv")
    try:
        df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip().upper() for c in df.columns] # CODIGO, DESCRIPCION
        return df
    except: return pd.DataFrame(columns=['CODIGO', 'DESCRIPCION'])

df_inv = load_inventory()

if 'rows' not in st.session_state:
    # Mantenemos tu orden: CODIGO, DESCRIPCION, CANTIDAD
    st.session_state.rows = pd.DataFrame([
        {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": "0"} 
    ] * 10)

# ── 6. CUERPO DE ENTRADA (WEB) ────────────────────────
with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    f_val = h1.date_input("FECHA", value=datetime.now(), key="f_in")
    t_val = h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_in")
    fol_val = h3.text_input("FOLIO", value="F-2026-001", key="fol_in")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}] * 10)

def lookup():
    # 1. Obtener los cambios del editor
    edits = st.session_state["editor_pt"].get("edited_rows", {})
    added = st.session_state["editor_pt"].get("added_rows", [])
    
    # 2. Sincronizar filas añadidas (si las hay) para que coincidan con la estructura
    for row in added:
        new_row = {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}
        new_row.update(row)
        st.session_state.rows = pd.concat([st.session_state.rows, pd.DataFrame([new_row])], ignore_index=True)

    # 3. Procesar ediciones en filas existentes
    for idx_str, info in edits.items():
        idx = int(idx_str)
        
        # Sincronizamos cualquier cambio (Cantidad, Código, etc.) al session_state
        for col, val in info.items():
            st.session_state.rows.at[idx, col] = val
        
        # Si el cambio fue en el CÓDIGO, hacemos el lookup de la DESCRIPCIÓN
        if "CODIGO" in info:
            val_codigo = str(info["CODIGO"]).strip().upper()
            if not df_inv.empty:
                match = df_inv[df_inv['CODIGO'].astype(str).str.strip().str.upper() == val_codigo]
                if not match.empty:
                    st.session_state.rows.at[idx, "DESCRIPCION"] = match.iloc[0]['DESCRIPCION']
                    st.session_state.rows.at[idx, "CODIGO"] = val_codigo

df_final = st.data_editor(
    st.session_state.rows, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="editor_pt", 
    on_change=lookup,
    column_config={
        "CODIGO": st.column_config.TextColumn("CÓDIGO"),
        "DESCRIPCION": st.column_config.TextColumn("DESCRIPCIÓN"),
        "CANTIDAD": st.column_config.TextColumn(
            "CANTIDAD", 
            width="small"
        )
    }
)
# ── 7. RENDERIZADO PRO (HTML PARA IMPRESIÓN) ───────────
filas_print = df_final[df_final["CODIGO"] != ""]
tabla_html = "".join([f"<tr><td style='border:1px solid black;padding:8px;'>{r['CODIGO']}</td><td style='border:1px solid black;padding:8px;'>{r['DESCRIPCION']}</td><td style='border:1px solid black;padding:8px;text-align:center;'>{r['CANTIDAD']}</td></tr>" for _, r in filas_print.iterrows()])

form_html = f"""
<style>
    @media print {{
        @page {{ 
            margin: 0.5cm; /* Ajusta el margen a tu gusto */
        }}
        /* Oculta encabezados y pies de página en algunos navegadores */
        header, footer, .no-print {{
            display: none !important;
        }}
    }}
</style>
<div style="font-family:sans-serif; padding:20px; color:black; background:white;">

<div style="font-family:sans-serif; padding:20px; color:black; background:white;">
    <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:10px;">
        <div>
            <h2 style="margin:0; letter-spacing:2px;">JYPESA</h2>
            <p style="margin:0; font-size:10px; letter-spacing:1px;">AUTOMATIZACIÓN DE PROCESOS</p>
        </div>
        <div style="text-align:right; font-size:12px;">
            <p style="margin:0;"><b>FOLIO:</b> {fol_val}</p>
            <p style="margin:0;"><b>FECHA:</b> {f_val}</p>
            <p style="margin:0;"><b>TURNO:</b> {t_val}</p>
        </div>
    </div>
    <h3 style="text-align:center; letter-spacing:5px; margin-top:30px; text-decoration:underline;">ENTREGA DE MATERIALES PT</h3>
    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
        <thead><tr style="background:#f2f2f2;">
            <th style="border:1px solid black;padding:10px;">CÓDIGO</th>
            <th style="border:1px solid black;padding:10px;">DESCRIPCIÓN</th>
            <th style="border:1px solid black;padding:10px;text-align:center;">CANTIDAD</th>
        </tr></thead>
        <tbody>{tabla_html}</tbody>
    </table>
    <div style="margin-top:80px; display:flex; justify-content:space-around; text-align:center; font-size:10px;">
        <div style="width:30%; border-top:1px solid black;">ENTREGÓ<br><b>Analista de Inventario</b></div>
        <div style="width:30%; border-top:1px solid black;">AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></div>
        <div style="width:30%; border-top:1px solid black;">RECIBIÓ<br><b>Rigoberto Hernandez / Cord.Logística</b></div>
    </div>
</div>
"""

# ── 8. BOTÓN DE ACCIÓN FINAL ───────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🖨️ GENERAR FORMATO PROFESIONAL (PDF)", type="primary", use_container_width=True):
    components.html(f"{form_html}<script>window.onload = function() {{ window.print(); }}</script>", height=0)
    st.toast("Renderizando Automatización de Procesos...", icon="⚙️")



























































