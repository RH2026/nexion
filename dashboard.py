import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
import plotly.graph_objects as go
import time
from github import Github
import json

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA FIJO (MODO OSCURO FORZADO - ONIX AZULADO) ──────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"

# Variables de diseño (Ajuste a Negro Ónix Azulado)
vars_css = {
    "bg": "#0E1117",      # Fondo Onix Azulado
    "card": "#1A1F2B",    # Fondos de tarjetas e inputs (Sutilmente más claro)
    "text": "#E0E6ED",    # Texto principal (Gris Platino)
    "sub": "#8892B0",     # Texto secundario
    "border": "#2D333B",  # Bordes y líneas
    "logo": "n1.png"      # Logo
}

# ── CSS MAESTRO INTEGRAL (REPARACIÓN DEFINITIVA Y SIN ERRORES) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* 1. Limpieza de Interfaz */
header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}

.stApp {{ 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['text']} !important; 
    font-family: 'Inter', sans-serif !important; 
}}

.block-container {{ 
    padding-top: 0.8rem !important; 
    padding-bottom: 5rem !important; 
}}

/* 2. ANIMACIÓN DE ENTRADA (Sintaxis blindada) */
@keyframes fadeInUp {{ 
    from {{ opacity: 0; transform: translateY(15px); }} 
    to {{ opacity: 1; transform: translateY(0); }} 
}}

[data-testid="stVerticalBlock"] > div:not(.element-container:has(.footer)) {{ 
    animation: fadeInUp 0.6s ease-out; 
}}

/* 3. TÍTULOS Y OPERATIONAL QUERY (Centrado Garantizado) */
h3, .op-query-text {{ 
    font-size: 11px !important; 
    letter-spacing: 8px !important; 
    text-align: center !important; 
    margin-top: 8px !important; 
    margin-bottom: 18px !important; 
    color: {vars_css['sub']} !important; 
    display: block !important; 
    width: 100% !important; 
}}

/* 4. BOTONES SLIM CON HOVER OSCURO */
div.stButton > button {{ 
    background-color: {vars_css['card']} !important; 
    color: {vars_css['text']} !important; 
    border: 1px solid {vars_css['border']} !important; 
    border-radius: 2px !important; 
    font-weight: 700 !important; 
    text-transform: uppercase; 
    font-size: 10px !important; 
    height: 28px !important; 
    min-height: 28px !important; 
    line-height: 28px !important; 
    transition: all 0.2s ease !important; 
    width: 100% !important; 
}}

div.stButton > button:hover {{ 
    background-color: #ffffff !important; 
    color: #000000 !important; 
    border-color: #ffffff !important; 
}}

/* 5. INPUT DE BÚSQUEDA Y TEXTO OPERATIONAL */
.stTextInput input {{ 
    background-color: {vars_css['card']} !important; 
    color: {vars_css['text']} !important; 
    border: 1px solid {vars_css['border']} !important; 
    border-radius: 2px !important; 
    height: 45px !important; 
    text-align: center !important; 
    letter-spacing: 2px; 
}}

/* 6. FOOTER FIJO (Blindado) */
.footer {{ 
    position: fixed; 
    bottom: 0 !important; 
    left: 0 !important; 
    width: 100% !important; 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['sub']} !important; 
    text-align: center; 
    padding: 12px 0px !important; 
    font-size: 9px; 
    letter-spacing: 2px; 
    border-top: 1px solid {vars_css['border']} !important; 
    z-index: 999999 !important; 
    animation: none !important; 
    transform: none !important; 
}}

/* 7. REPARACIÓN PARA GRÁFICOS (Asegura que las barras se vean) */
.stPlotlyChart {{ 
    visibility: visible !important; 
    opacity: 1 !important; 
    min-height: 300px !important; 
}}

/* Evitar que la animación oculte el gráfico */
[data-testid="stVerticalBlock"] > div:has(div.stPlotlyChart) {{ 
    animation: none !important; 
    transform: none !important; 
    opacity: 1 !important; 
}}
</style>
""", unsafe_allow_html=True)

# ── 4. SPLASH SCREEN ──────────────────────────────────────
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:40px;height:40px;border:1px solid {vars_css['border']}; border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.7)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER Y NAVEGACIÓN (LÍNEA 1) ──────────────────────────
header_zone = st.container()
with header_zone:
    c1, c2 = st.columns([1.5, 5.4], vertical_alignment="center")
    with c1:
        try:
            st.image(vars_css["logo"], width=120)
            st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0; color:{vars_css['text']};'>NEXION</h3>", unsafe_allow_html=True)
    with c2:
        cols_main = st.columns(4)
        main_menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]
        for i, m in enumerate(main_menus):
            with cols_main[i]:
                seleccionado = st.session_state.menu_main == m
                btn_label = f"● {m}" if seleccionado else m
                if st.button(btn_label, use_container_width=True, key=f"main_{m}"):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()

# ── SUBMENÚS (LÍNEA 2 COMPLETA) ────────────────────────────
sub_map = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "PAGOS"]
}

current_subs = sub_map.get(st.session_state.menu_main, [])
if current_subs:
    sub_zone = st.container()
    with sub_zone:
        cols_sub = st.columns(len(current_subs) + 4)
        for i, s in enumerate(current_subs):
            with cols_sub[i]:
                sub_activo = st.session_state.menu_sub == s
                sub_label = f"» {s}" if sub_activo else s
                if st.button(sub_label, use_container_width=True, key=f"sub_{s}"):
                    st.session_state.menu_sub = s
                    st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px; opacity:0.3;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO ──────────────────────────────────
main_container = st.container()
with main_container:
    # 1. TRACKING
    if st.session_state.menu_main == "TRACKING":
        st.markdown("<div style='margin-top: 5vh;'></div>", unsafe_allow_html=True)
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"<p class='op-query-text'>O P E R A T I O N A L &nbsp; Q U E R Y</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")

    # 2. SEGUIMIENTO
    elif st.session_state.menu_main == "SEGUIMIENTO":
        if st.session_state.menu_sub == "TRK":
            st.subheader("SEGUIMIENTO > TRK")
            st.info("Espacio para contenido de Tracking Operativo")
        elif st.session_state.menu_sub == "GANTT":
            st.subheader("SEGUIMIENTO > GANTT")
            # ── CONFIG ───────────────────────────────────────────────────────────────
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "tareas.csv"
            CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
            
            # ── FECHA MX ────────────────────────────────────────────────
            def obtener_fecha_mexico():
                return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=6)).date()
            
            # ── CARGA SEGURA ────────────────────────────────────────────
            def cargar_datos_seguro():
                columnas = [
                    "FECHA","FECHA_FIN","IMPORTANCIA","TAREA","ULTIMO ACCION",
                    "PROGRESO","DEPENDENCIAS","TIPO","GRUPO"
                ]
                hoy = obtener_fecha_mexico()
            
                try:
                    r = requests.get(f"{CSV_URL}?t={int(time.time())}")
                    if r.status_code == 200:
                        df = pd.read_csv(StringIO(r.text))
                        df.columns = [c.strip().upper() for c in df.columns]
            
                        for c in columnas:
                            if c not in df.columns:
                                df[c] = ""
            
                        df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce").dt.date
                        df["FECHA_FIN"] = pd.to_datetime(df["FECHA_FIN"], errors="coerce").dt.date
            
                        df["FECHA"] = df["FECHA"].apply(lambda x: x if isinstance(x, datetime.date) else hoy)
                        df["FECHA_FIN"] = df["FECHA_FIN"].apply(
                            lambda x: x if isinstance(x, datetime.date) else hoy + datetime.timedelta(days=1)
                        )
            
                        df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors="coerce").fillna(0).astype(int)
                        df["IMPORTANCIA"] = df["IMPORTANCIA"].fillna("Media")
                        df["TIPO"] = df["TIPO"].fillna("Tarea")
                        df["GRUPO"] = df["GRUPO"].fillna("General")
                        df["DEPENDENCIAS"] = df["DEPENDENCIAS"].fillna("")
            
                        return df[columnas]
                except:
                    pass
            
                return pd.DataFrame(columns=columnas)
            
            # ── GUARDAR ────────────────────────────────────────────────
            def guardar_en_github(df):
                if not TOKEN:
                    st.error("GITHUB_TOKEN no configurado")
                    return False
                try:
                    g = Github(TOKEN)
                    repo = g.get_repo(REPO_NAME)
            
                    df_save = df.copy()
                    df_save["FECHA"] = df_save["FECHA"].astype(str)
                    df_save["FECHA_FIN"] = df_save["FECHA_FIN"].astype(str)
            
                    csv = df_save.to_csv(index=False)
                    contents = repo.get_contents(FILE_PATH, ref="main")
            
                    repo.update_file(
                        contents.path,
                        f"Sync NEXION {obtener_fecha_mexico()}",
                        csv,
                        contents.sha,
                        branch="main"
                    )
                    st.toast("🚀 Sincronizado con GitHub", icon="✅")
                    return True
                except Exception as e:
                    st.error(e)
                    return False
            
            # ── SESSION ────────────────────────────────────────────────
            if "df_tareas" not in st.session_state:
                st.session_state.df_tareas = cargar_datos_seguro()
            
            df = st.session_state.df_tareas.copy()
            
            # ── TABLA EDITABLE ─────────────────────────────────────────
            df_editado = st.data_editor(
                df,
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "FECHA": st.column_config.DateColumn("Inicio"),
                    "FECHA_FIN": st.column_config.DateColumn("Fin"),
                    "IMPORTANCIA": st.column_config.SelectboxColumn(
                        "Importancia",
                        options=["Urgente","Alta","Media","Baja"]
                    ),
                    "PROGRESO": st.column_config.ProgressColumn(
                        "Progreso", min_value=0, max_value=100
                    ),
                    "TAREA": st.column_config.TextColumn("Tarea"),
                    "ULTIMO ACCION": st.column_config.TextColumn("Última acción"),
                    "DEPENDENCIAS": st.column_config.TextColumn("Dependencias"),
                    "TIPO": st.column_config.SelectboxColumn(
                        "Tipo", options=["Tarea","Hito"]
                    ),
                    "GRUPO": st.column_config.TextColumn("Grupo"),
                }
            )
            
            if st.button("💾 SINCRONIZAR CON GITHUB", use_container_width=True):
                if guardar_en_github(df_editado):
                    st.session_state.df_tareas = df_editado
                    st.rerun()
            
            # ── FRAPPE GANTT ───────────────────────────────────────────
            tasks = []
            for i, r in df_editado.iterrows():
                if str(r["TAREA"]).strip() == "":
                    continue
                tasks.append({
                    "id": str(i),
                    "name": f"[{r['GRUPO']}] {r['TAREA']}",
                    "start": str(r["FECHA"]),
                    "end": str(r["FECHA_FIN"]),
                    "progress": int(r["PROGRESO"]),
                    "dependencies": r["DEPENDENCIAS"],
                    "custom_class": r["IMPORTANCIA"].lower()
                })
            
            components.html(f"""
            <link rel="stylesheet" href="https://unpkg.com/frappe-gantt/dist/frappe-gantt.css">
            <script src="https://unpkg.com/frappe-gantt/dist/frappe-gantt.min.js"></script>
            
            <style>
            .bar.urgente {{ fill:#FF3131; }}
            .bar.alta {{ fill:#FF914D; }}
            .bar.media {{ fill:#00D2FF; }}
            .bar.baja {{ fill:#4B5563; }}
            </style>
            
            <div id="gantt"></div>
            
            <script>
            const gantt = new Gantt("#gantt", {json.dumps(tasks)}, {{
              view_mode: "Day",
              bar_height: 16,
              padding: 40
            }});
            </script>
            """, height=320 + len(tasks)*28)


        
        elif st.session_state.menu_sub == "QUEJAS":
            st.subheader("SEGUIMIENTO > QUEJAS")
            st.info("Gestión de incidencias")

    # 3. REPORTES
    elif st.session_state.menu_main == "REPORTES":
        st.subheader(f"MÓDULO DE INTELIGENCIA > {st.session_state.menu_sub}")

    # 4. FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        if st.session_state.menu_sub == "SALIDA DE PT":
            st.subheader("FORMATOS > SALIDA DE PRODUCTO TERMINADO")
        elif st.session_state.menu_sub == "PAGOS":
            st.subheader("FORMATOS > CONTROL DE PAGOS")
        else:
            st.subheader("CENTRO DE DOCUMENTACIÓN")
            st.write("Seleccione un formato del submenú superior.")

# ── FOOTER FIJO ────────────────────────
st.markdown(f"""
<div class="footer">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
</div>
""", unsafe_allow_html=True)






































































































































































































































































































































































































































































































