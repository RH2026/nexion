import streamlit as st
import pandas as pd
from datetime import datetime
import os
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Automatización de Procesos", layout="wide", initial_sidebar_state="collapsed")

# ── 2. TEMA DINÁMICO (Sincronizado) ────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema

if tema == "oscuro":
    v = {
        "bg": "#05070A", "card": "#0D1117", 
        "text": "#F0F6FC", "sub": "#8B949E", 
        "border": "#1B1F24"
    }
else:
    v = {
        "bg": "#E9ECF1", "card": "#FFFFFF", 
        "text": "#111111", "sub": "#2D3136", 
        "border": "#C9D1D9"
    }

# ── 3. CSS MAESTRO (HOVER INVERTIDO + FIX LABELS) ──────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"] {{ 
    display:none !important; 
}}

.block-container {{ padding-top: 1.5rem !important; }}

* {{ transition: background-color .35s ease, color .35s ease, border-color .35s ease; }}

.stApp {{ 
    background:{v["bg"]} !important; 
    color:{v["text"]} !important; 
    font-family:'Inter',sans-serif !important; 
}}

/* VISIBILIDAD DE LABELS (FECHA, TURNO, FOLIO) */
[data-testid="stWidgetLabel"] p {{
    color: {v["text"]} !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
}}

/* BOTONES CON HOVER DE ALTO CONTRASTE INVERTIDO */
div.stButton>button {{
    background:{v["card"]} !important; 
    color:{v["text"]} !important;
    border: 1px solid {v["border"]} !important; 
    border-radius:2px !important;
    font-size:11px !important; font-weight:700 !important; 
    letter-spacing:2px !important; text-transform:uppercase;
    width: 100%;
}}

div.stButton>button:hover {{
    background: {v["text"]} !important;
    color: {v["bg"]} !important;
    border-color: {v["text"]} !important;
}}

/* BOTÓN PRIMARIO (IMPRIMIR) */
div.stButton>button[kind="primary"] {{
    background: {v["text"]} !important;
    color: {v["bg"]} !important;
    border: none !important;
    height: 48px !important;
}}

@media print {{ .no-print {{ display: none !important; }} }}
</style>
""", unsafe_allow_html=True)

# ── 4. HEADER NEXION ──────────────────────────────────
c1, c2, c3 = st.columns([2, 3.5, .5], vertical_alignment="top")
with c1:
    logo = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo, width=140)
        st.markdown(f"<div style='margin-top:-15px;'><p style='font-size:9px; color:{v['sub']}; letter-spacing:1px; text-transform:uppercase;'>Core Intelligence</p></div>", unsafe_allow_html=True)
    except: st.title("NEXION")

with c2:
    cols = st.columns(4)
    menu_superior = ["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]
    for i, b in enumerate(menu_superior):
        if cols[i].button(b, key=f"nav_{b}", use_container_width=True):
            if b != "FORMATOS": st.switch_page("dashboard.py")
            else: st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="t_btn"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"; st.rerun()

st.markdown(f"<hr class='no-print' style='border-top:1px solid {v['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 4.1 SUBMENÚ OPERATIVO (REPLICANDO DASHBOARD) ──────
st.markdown(f"<p style='text-align: center; color: {v['sub']}; font-size: 10px; letter-spacing: 5px; text-transform: uppercase; margin-top: 10px;'>Submenú Formatos</p>", unsafe_allow_html=True)

_, col_sub, _ = st.columns([1, 1.8, 1])
with col_sub:
    opcion_seleccionada = st.selectbox(
        "", 
        ["SELECCIONE...", "ENTREGA MATERIALES PT", "SALIDA PT", "ENTRADA MP", "INVENTARIOS"], 
        index=0, 
        label_visibility="collapsed",
        key="sub_menu_selector"
    )

st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

# ── 5. LÓGICA DINÁMICA DE CONTENIDO ───────────────────

if opcion_seleccionada == "SELECCIONE...":
    st.markdown(f"""
        <div style="text-align: center; margin-top: 100px;">
            <p style="color: {v['sub']}; font-size: 11px; letter-spacing: 2px; text-transform: uppercase;">
                Módulo de Formatos Operativos
            </p>
            <p style="color: {v['sub']}; font-size: 9px; opacity: 0.6;">
                Seleccione un documento en el menú superior para continuar.
            </p>
        </div>
    """, unsafe_allow_html=True)

elif opcion_seleccionada == "ENTREGA MATERIALES PT":
    # Título Minimalista Zara/DHL Style
    st.markdown(f"""
        <div style="text-align: center; margin-top: 10px; margin-bottom: 25px;">
            <h1 style="font-weight: 300; letter-spacing: 12px; text-transform: uppercase; font-size: 15px; color: {v['text']}; opacity: 0.9;">
                E N T R E G A &nbsp; D E &nbsp; M A T E R I A L E S &nbsp; P T
            </h1>
        </div>
    """, unsafe_allow_html=True)

    @st.cache_data
    def load_inv():
        ruta = "inventario.csv"
        if not os.path.exists(ruta): ruta = os.path.join(os.getcwd(), "inventario.csv")
        try:
            df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [str(c).strip().upper() for c in df.columns]
            return df
        except: return pd.DataFrame(columns=['CODIGO', 'DESCRIPCION'])

    df_inv = load_inv()

    with st.container(border=True):
        h1, h2, h3 = st.columns(3)
        fecha_val = h1.date_input("FECHA", value=datetime.now())
        turno_val = h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"])
        folio_val = h3.text_input("FOLIO", value="F-2026-001")

    if 'rows' not in st.session_state:
        st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}] * 10)

    def lookup():
        edits = st.session_state["editor_pt"].get("edited_rows", {})
        for idx_str, info in edits.items():
            idx = int(idx_str)
            if "CODIGO" in info:
                val = str(info["CODIGO"]).strip().upper()
                match = df_inv[df_inv['CODIGO'].astype(str).str.strip().str.upper() == val] if not df_inv.empty else pd.DataFrame()
                if not match.empty:
                    st.session_state.rows.at[idx, "DESCRIPCION"] = match.iloc[0]['DESCRIPCION']
                    st.session_state.rows.at[idx, "CODIGO"] = val

    df_final = st.data_editor(st.session_state.rows, num_rows="dynamic", use_container_width=True, key="editor_pt", on_change=lookup)

    if "print_counter" not in st.session_state: st.session_state.print_counter = 0

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🖨️ GENERAR FORMATO PROFESIONAL", type="primary", use_container_width=True):
        st.session_state.print_counter += 1
        filas = df_final[df_final["CODIGO"].str.strip() != ""]
        tabla = "".join([f"<tr><td style='border:1px solid black;padding:8px;'>{r['CODIGO']}</td><td style='border:1px solid black;padding:8px;'>{r['DESCRIPCION']}</td><td style='border:1px solid black;padding:8px;text-align:center;'>{r['CANTIDAD']}</td></tr>" for _, r in filas.iterrows()])
        
        form_html = f"""
        <div style="font-family:sans-serif; padding:20px; color:black; background:white;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:10px;">
                <div><h2 style="margin:0;">NEXION LOGISTICS</h2><p style="margin:0; font-size:10px;">CORE INTELLIGENCE</p></div>
                <div style="text-align:right; font-size:12px;">
                    <p style="margin:0;"><b>FOLIO:</b> {folio_val}</p><p style="margin:0;"><b>FECHA:</b> {fecha_val}</p><p style="margin:0;"><b>TURNO:</b> {turno_val}</p>
                </div>
            </div>
            <h3 style="text-align:center; letter-spacing:5px; margin-top:30px; text-decoration:underline;">ENTREGA DE MATERIALES PT</h3>
            <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                <thead><tr style="background:#f2f2f2;"><th style="border:1px solid black;padding:10px;">CÓDIGO</th><th style="border:1px solid black;padding:10px;">DESCRIPCIÓN</th><th style="border:1px solid black;padding:10px;text-align:center;">CANTIDAD</th></tr></thead>
                <tbody>{tabla}</tbody>
            </table>
            <div style="margin-top:80px; display:flex; justify-content:space-around; text-align:center; font-size:10px;">
                <div style="width:30%; border-top:1px solid black;">ENTREGÓ<br><b>Analista de Inventario</b></div>
                <div style="width:30%; border-top:1px solid black;">AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></div>
                <div style="width:30%; border-top:1px solid black;">RECIBIÓ<br><b>Jesus Moreno / Aux. Logística</b></div>
            </div>
        </div>
        """
        components.html(f"{form_html}<script>window.onload = function() {{ window.print(); }}</script>", height=1, key=f"p_{st.session_state.print_counter}")

else:
    st.markdown(f"<div style='text-align:center; margin-top:50px; color:{v['sub']}; font-size:11px;'>Módulo de {opcion_seleccionada} en desarrollo.</div>", unsafe_allow_html=True)





















































