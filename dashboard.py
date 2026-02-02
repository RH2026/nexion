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
import pytz
import zipfile
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re
import unicodedata
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# --- MOTOR DE INTELIGENCIA LOGÍSTICA (XENOCODE CORE) ---
def d_local(dir_val):
    """Detecta si una dirección pertenece a la ZMG basada en CPs."""
    # Rangos de Zapopan, Guadalajara, Tonalá y Tlaquepaque
    rangos = [(44100, 44990), (45010, 45245), (45400, 45429), (45500, 45595)]
    cps = re.findall(r'\b\d{5}\b', str(dir_val))
    for cp in cps:
        try:
            if any(inicio <= int(cp) <= fin for inicio, fin in rangos): 
                return "LOCAL"
        except: 
            continue
    return "FORÁNEO"

@st.cache_data
def motor_logistico_central():
    """Carga la matriz historial para recomendaciones de fleteras."""
    try:
        if os.path.exists("matriz_historial.csv"):
            h = pd.read_csv("matriz_historial.csv", encoding='utf-8-sig')
            h.columns = [str(c).upper().strip() for c in h.columns]
            c_pre = [c for c in h.columns if 'PRECIO' in c][0]
            c_flet = [c for c in h.columns if 'FLETERA' in c or 'TRANSPORTE' in c][0]
            c_dir = [c for c in h.columns if 'DIRECCION' in c][0]
            h[c_pre] = pd.to_numeric(h[c_pre], errors='coerce').fillna(0)
            mejores = h.loc[h.groupby(c_dir)[c_pre].idxmin()]
            return mejores.set_index(c_dir)[c_flet].to_dict(), mejores.set_index(c_dir)[c_pre].to_dict()
    except: 
        pass
    return {}, {}

# ── TEMA FIJO (MODO OSCURO FORZADO - ONIX AZULADO) ──────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"

vars_css = {
    "bg": "#0E1117",      # Fondo Onix Azulado
    "card": "#1A1F2B",    # Fondos de tarjetas e inputs
    "text": "#E0E6ED",    # Texto principal
    "sub": "#8892B0",     # Texto secundario
    "border": "#2D333B",  # Bordes y líneas
    "logo": "n1.png"      # Logo
}

# ── CSS MAESTRO INTEGRAL (REPARACIÓN DEFINITIVA Y SIN ERRORES) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* 1. Limpieza de Interfaz */
header, footer, [data-testid="stHeader"] {{
    visibility: hidden;
    height: 0px;
}}

/* APP BASE */
html, body {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
}}

.stApp {{ 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['text']} !important; 
    font-family: 'Inter', sans-serif !important; 
}}

/* CONTENEDOR PRINCIPAL */
.block-container {{ 
    padding-top: 0.8rem !important; 
    padding-bottom: 5rem !important; 
    background-color: {vars_css['bg']} !important;
}}

/* 2. ANIMACIÓN DE ENTRADA (BLINDADA) */
@keyframes fadeInUp {{ 
    from {{ opacity: 0; transform: translateY(15px); }} 
    to {{ opacity: 1; transform: translateY(0); }} 
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

/* 3. TÍTULOS Y OPERATIONAL QUERY */
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

/* 4. BOTONES SLIM */
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

/* 5. INPUTS */
.stTextInput input {{ 
    background-color: {vars_css['card']} !important; 
    color: {vars_css['text']} !important; 
    border: 1px solid {vars_css['border']} !important; 
    border-radius: 2px !important; 
    height: 45px !important; 
    text-align: center !important; 
    letter-spacing: 2px; 
}}

/* DATA EDITOR */
[data-testid="stDataEditor"] {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
}}

[data-testid="stDataEditor"] * {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
}}

/* 6. FOOTER FIJO */
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

/* 7. GRÁFICOS / IFRAME (PLOTLY + FRAPPE) */
.stPlotlyChart {{
    visibility: visible !important;
    opacity: 1 !important;
    min-height: 300px !important;
}}

iframe {{
    background-color: {vars_css['bg']} !important;
    border: 1px solid {vars_css['border']} !important;
}}
</style>
""", unsafe_allow_html=True)

# ── SPLASH SCREEN ──────────────────────────────────────
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

# ── HEADER REESTRUCTURADO (CENTRADITO Y BALANCEADO) ──────────────────────────
header_zone = st.container()
with header_zone:
    # Usamos proporciones que den espacio suficiente a los lados para que el centro sea real
    c1, c2, c3 = st.columns([1.5, 4, 1.5], vertical_alignment="center")
    
    with c1:
        try:
            st.image(vars_css["logo"], width=110)
            st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0; color:{vars_css['text']};'>NEXION</h3>", unsafe_allow_html=True)

    with c2:
        # INDICADOR GENERAL (CENTRADO ABSOLUTO)
        if st.session_state.menu_sub != "GENERAL":
            ruta = f"{st.session_state.menu_main} <span style='color:{vars_css['sub']}; opacity:0.4; margin: 0 10px;'>|</span> {st.session_state.menu_sub}"
        else:
            ruta = st.session_state.menu_main

        st.markdown(f"""
            <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
                <p style='font-size: 12px;  /* ← AQUÍ AJUSTAS EL TAMAÑO */
                          letter-spacing: 5px; 
                          color: {vars_css['sub']}; 
                          margin: 0; 
                          font-weight: 600; 
                          text-transform: uppercase;'>
                    {ruta}
                </p>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        # BOTÓN HAMBURGUESA - Alineado a la derecha del contenedor
        # Usamos una columna anidada o un div para empujar el popover a la derecha
        _, btn_col = st.columns([1, 2]) 
        with btn_col:
            with st.popover("☰", use_container_width=True):
                st.markdown("<p style='color:#64748b; font-size:10px; font-weight:700; margin-bottom:10px; letter-spacing:1px;'>NAVEGACIÓN</p>", unsafe_allow_html=True)
                
                # --- SECCIÓN DASHBOARD ---
                if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                    st.session_state.menu_main = "TRACKING"
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()
                
                # --- SECCIÓN SEGUIMIENTO ---
                with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                    for s in ["TRK", "GANTT", "QUEJAS"]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"pop_sub_{s}"):
                            st.session_state.menu_main = "SEGUIMIENTO"
                            st.session_state.menu_sub = s
                            st.rerun()

                # --- SECCIÓN REPORTES ---
                with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                    for s in ["APQ", "OPS", "OTD"]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"pop_rep_{s}"):
                            st.session_state.menu_main = "REPORTES"
                            st.session_state.menu_sub = s
                            st.rerun()

                # --- SECCIÓN FORMATOS ---
                with st.expander("FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")):
                    for s in ["SALIDA DE PT", "PAGOS"]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"pop_for_{s}"):
                            st.session_state.menu_main = "FORMATOS"
                            st.session_state.menu_sub = s
                            st.rerun()

                # --- SECCIÓN HUB LOG ---
                with st.expander("HUB LOG", expanded=(st.session_state.menu_main == "HUB LOG")):
                    # Definimos las sub-secciones de tu HUB
                    for s in ["ANALISIS", "SISTEMA", "ALERTAS"]:
                        sub_label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(sub_label, use_container_width=True, key=f"pop_hub_{s}"):
                            st.session_state.menu_main = "HUB LOG"
                            st.session_state.menu_sub = s
                            st.rerun()
                

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px; opacity:0.2;'>", unsafe_allow_html=True)

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
            # ── CONFIG GANTT ───────────────────────────────────────────────────────────────
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "tareas.csv"
            CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
            
            # ── FUNCIONES DE FECHA Y CARGA ─────────────────────────────────────────────
            def obtener_fecha_mexico():
                return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=6)).date()
            
            def cargar_datos_seguro():
                columnas = [
                    "FECHA","FECHA_FIN","IMPORTANCIA","TAREA","ULTIMO ACCION",
                    "PROGRESO","DEPENDENCIAS","TIPO","GRUPO"
                ]
                hoy = obtener_fecha_mexico()
                try:
                    # Carga con bust de caché para evitar datos viejos
                    r = requests.get(f"{CSV_URL}?t={int(time.time())}")
                    if r.status_code == 200:
                        df = pd.read_csv(StringIO(r.text))
                        df.columns = [c.strip().upper() for c in df.columns]
                        
                        # Asegurar que todas las columnas existan
                        for c in columnas:
                            if c not in df.columns:
                                df[c] = ""
                        
                        # Normalización de datos para evitar errores de renderizado
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
                    csv_content = df_save.to_csv(index=False)
                    contents = repo.get_contents(FILE_PATH, ref="main")
                    repo.update_file(
                        contents.path,
                        f"Sync NEXION {obtener_fecha_mexico()}",
                        csv_content,
                        contents.sha,
                        branch="main"
                    )
                    st.toast("🚀 Sincronizado con GitHub", icon="✅")
                    return True
                except Exception as e:
                    st.error(f"Error: {e}")
                    return False
            
            # ── GESTIÓN DE ESTADO ──────────────────────────────────────────────────────
            if "df_tareas" not in st.session_state:
                st.session_state.df_tareas = cargar_datos_seguro()
            
            # Copia de trabajo
            df_master = st.session_state.df_tareas.copy()
            
            # ── 1. FILTROS Y CONTROLES (PARTE SUPERIOR) ────────────────────────────────
                      
            c1, c2 = st.columns([1, 2])
            with c1:
                gantt_view = st.radio("Vista", ["Day", "Week", "Month", "Year"], horizontal=True, index=0, key="gantt_v")
            
            with c2:
                grupos_disponibles = sorted(df_master["GRUPO"].astype(str).unique())
                grupos_sel = st.multiselect("Filtrar por grupo", grupos_disponibles, default=grupos_disponibles, key="gantt_g")
            
            # Filtrado de datos para el Gantt
            df_gantt = df_master[df_master["GRUPO"].isin(grupos_sel)].copy()
            
            # 🔒 FORZAR HITOS A DURACIÓN CERO
            mask_hito = df_gantt["TIPO"].str.lower() == "hito"
            df_gantt.loc[mask_hito, "FECHA_FIN"] = df_gantt.loc[mask_hito, "FECHA"]
            
            # Preparar lista de tareas para el JS
            tasks_data = []
            for i, r in enumerate(df_gantt.itertuples(), start=1):
                if not str(r.TAREA).strip(): 
                    continue
            
                importancia = str(r.IMPORTANCIA).strip().lower()
                task_id = f"T{i}"  # id único T1, T2, T3...
                
                # Dependencias deben estar en formato T1,T2,... si vienen como índices
                dependencias = str(r.DEPENDENCIAS).strip()
                if dependencias:
                    # Convertimos índices a ids T#
                    dependencias_ids = []
                    for d in dependencias.split(','):
                        d = d.strip()
                        if d.isdigit():
                            dependencias_ids.append(f"T{int(d)+1}")  # sumamos 1 porque enumerate empieza en 1
                        else:
                            dependencias_ids.append(d)
                    dependencias = ','.join(dependencias_ids)
                
                tasks_data.append({
                    "id": task_id,
                    "name": f"[{r.GRUPO}] {r.TAREA}",
                    "start": str(r.FECHA),
                    "end": str(r.FECHA_FIN),
                    "progress": int(r.PROGRESO),
                    "dependencies": dependencias,
                    "custom_class": f"imp-{importancia}"
                })
            
            tasks_js_str = json.dumps(tasks_data)
            
            # ── 2. RENDERIZADO GANTT REPARADO ───────────────────────────────
            components.html(
                f"""
                <html>
                <head>
                    <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.css'>
                    <script src='https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.js'></script>
                    <style>
                        html, body {{ background:#111827; margin:0; padding:0; }}
                        #gantt {{ background:#0E1117; }}
                        .gantt text {{ fill:#E5E7EB !important; font-size:12px; }}
                        .grid-background {{ fill:#0b0e14 !important; }}
                        .grid-header {{ fill:#151a24 !important; }}
                        .grid-row {{ fill:#0b0e14 !important; }}
                        .grid-row:nth-child(even) {{ fill:#0f131a !important; }}
                        .grid-line {{ stroke: #1e2530 !important; stroke-opacity: 0.1 !important; }}
                        .arrow {{ stroke: #9ca3af !important; stroke-width: 1.6 !important; opacity: 1 !important; fill: none !important; }}
                        .bar-wrapper.imp-urgente .bar {{ fill:#DC2626 !important; }}
                        .bar-wrapper.imp-alta    .bar {{ fill:#F97316 !important; }}
                        .bar-wrapper.imp-media   .bar {{ fill:#3B82F6 !important; }}
                        .bar-wrapper.imp-baja    .bar {{ fill:#22C55E !important; }}
                        .today-highlight {{ fill: #00FF00 !important; opacity: 0.2 !important; }}
                    </style>
                </head>
                <body>
                    <div id='gantt'></div>
                    <script>
                        var tasks = {tasks_js_str};
                        if(tasks.length){{
                            var gantt = new Gantt('#gantt', tasks, {{
                                view_mode: '{gantt_view}',
                                bar_height: 20,
                                padding: 40,
                                date_format: 'YYYY-MM-DD'
                            }});
            
                            // Forzar suavizado de líneas horizontales y ocultar verticales
                            setTimeout(function() {{
                                document.querySelectorAll('#gantt svg line').forEach(function(line) {{
                                    var x1 = parseFloat(line.getAttribute('x1'));
                                    var x2 = parseFloat(line.getAttribute('x2'));
                                    var y1 = parseFloat(line.getAttribute('y1'));
                                    var y2 = parseFloat(line.getAttribute('y2'));
            
                                    if(x1 === x2) {{
                                        // ocultar verticales
                                        line.style.display = 'none';
                                    }}
                                    if(y1 === y2) {{
                                        // suavizar horizontales
                                        line.style.strokeOpacity = '0.1';
                                        line.style.stroke = '#1e2530';
                                    }}
                                }});
                            }}, 200);
                        }}
                    </script>
                </body>
                </html>
                """,
                height=420,
                scrolling=False
            )
            # ── 3. DATA EDITOR (ABAJO) ─────────────────────────────────────────────────
            st.subheader("EDITOR DE TAREAS")
            
            # Normalización para el Data Editor (Evitar strings "nan")
            df_editor = df_master.copy()
            for col in ["IMPORTANCIA","TAREA","ULTIMO ACCION","DEPENDENCIAS","TIPO","GRUPO"]:
                df_editor[col] = df_editor[col].astype(str).replace("nan", "").fillna("")
            
            df_editor["PROGRESO_VIEW"] = df_editor["PROGRESO"]
            
            df_editado = st.data_editor(
                df_editor,
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "FECHA": st.column_config.DateColumn("Inicio"),
                    "FECHA_FIN": st.column_config.DateColumn("Fin"),
                    "IMPORTANCIA": st.column_config.SelectboxColumn("Prioridad", options=["Urgente","Alta","Media","Baja"]),
                    "PROGRESO": st.column_config.NumberColumn("Progreso %", min_value=0, max_value=100, step=5),
                    "PROGRESO_VIEW": st.column_config.ProgressColumn("Avance", min_value=0, max_value=100),
                    "TAREA": st.column_config.TextColumn("Tarea"),
                    "ULTIMO ACCION": st.column_config.TextColumn("Última acción"),
                    "DEPENDENCIAS": st.column_config.TextColumn("Dependencias"),
                    "TIPO": st.column_config.SelectboxColumn("Tipo", options=["Tarea","Hito"]),
                    "GRUPO": st.column_config.TextColumn("Grupo"),
                }
            )
            
            # Sincronizar columna visual
            df_editado["PROGRESO_VIEW"] = df_editado["PROGRESO"]
            
            if st.button("SINCRONIZAR CON GITHUB", use_container_width=True):
                df_guardar = df_editado.drop(columns=["PROGRESO_VIEW"], errors="ignore")
                if guardar_en_github(df_guardar):
                    st.session_state.df_tareas = df_guardar
                    st.rerun()



        
        elif st.session_state.menu_sub == "QUEJAS":
            st.subheader("SEGUIMIENTO > QUEJAS")
            st.info("Gestión de incidencias")
        else:
            st.subheader("MÓDULO DE SEGUIMIENTO")
            st.write("Seleccione una sub-categoría en la barra superior.")

    # 3. REPORTES
    elif st.session_state.menu_main == "REPORTES":
        st.subheader(f"MÓDULO DE INTELIGENCIA > {st.session_state.menu_sub}")

    # 4. FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        if st.session_state.menu_sub == "SALIDA DE PT":
            # ── SALDA DE PT -- GENERACIÓN DE FOLIO CON HORA DE GUADALAJARA ──
            if 'folio_nexion' not in st.session_state:
                # Definimos la zona horaria de Guadalajara/CDMX
                tz_gdl = pytz.timezone('America/Mexico_City') 
                now_gdl = datetime.datetime.now(tz_gdl)
                
                # Formato: F - AÑO MES DÍA - HORA MINUTO (Hora local de GDL)
                st.session_state.folio_nexion = f"F-{now_gdl.strftime('%Y%m%d-%H%M')}"                
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
            
            # Inicialización única de las filas en el session_state
            if 'rows' not in st.session_state:
                st.session_state.rows = pd.DataFrame([
                    {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": "0"} 
                ] * 10)
                                    
            # ── 6. CUERPO DE ENTRADA (REPARADO) ────────────────────────
            with st.container(border=True):
                h1, h2, h3 = st.columns(3)
                
                # Fecha automática
                f_val = h1.date_input("FECHA", value=datetime.datetime.now(), key="f_in")
                
                # Selección de turno
                t_val = h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_in")
                
                # Folio Automático (Se puede editar si es necesario, pero ya viene cargado)
                fol_val = h3.text_input("FOLIO", value=st.session_state.folio_nexion, key="fol_in")
            
            def lookup():
                # 1. Obtener los cambios del editor
                edits = st.session_state["editor_pt"].get("edited_rows", {})
                added = st.session_state["editor_pt"].get("added_rows", [])
                
                # 2. Sincronizar filas añadidas
                for row in added:
                    new_row = {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}
                    new_row.update(row)
                    st.session_state.rows = pd.concat([st.session_state.rows, pd.DataFrame([new_row])], ignore_index=True)
            
                # 3. Procesar ediciones en filas existentes
                for idx_str, info in edits.items():
                    idx = int(idx_str)
                    
                    for col, val in info.items():
                        st.session_state.rows.at[idx, col] = val
                    
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
                    @page {{ margin: 0.5cm; }}
                    header, footer, .no-print {{ display: none !important; }}
                }}
            </style>
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
         
            # ── 8. BOTONES DE ACCIÓN FINAL (CLONADOS) ───────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Columnas 50/50 para asegurar simetría total
            col_pdf, col_reset = st.columns(2) 
            
            with col_pdf:
                # Botón Original de Impresión
                if st.button("🖨️ GENERAR FORMATO (PDF)", 
                             type="primary", 
                             use_container_width=True, 
                             key="btn_pdf_nexion"):
                    components.html(f"<html><body>{form_html}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)
                    st.toast("Renderizando...", icon="⚙️")
            
            with col_reset:
                # CLON DEL BOTÓN: Misma estructura, diferente función
                if st.button("🔄 ACTUALIZAR SISTEMA NEXION", 
                             type="primary", 
                             use_container_width=True, 
                             key="btn_reset_nexion"):
                    # Función de limpieza
                    if 'folio_nexion' in st.session_state:
                        del st.session_state.folio_nexion
                    
                    # Reset de la tabla a su estado inicial
                    st.session_state.rows = pd.DataFrame([
                        {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": "0"} 
                    ] * 10)
                    
                    st.rerun()
                        
                    
    elif st.session_state.menu_sub == "PAGOS":
        st.subheader("FORMATOS > CONTROL DE PAGOS")
    
            
    # 5. HUB LOG
    elif st.session_state.menu_main == "HUB LOG":
        st.subheader(f"🌐 HUB LOG > {st.session_state.menu_sub}")
        
        if st.session_state.menu_sub == "ANALISIS":
            st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>LOGISTICS INTELLIGENCE HUB | XENOCODE CORE</p>", unsafe_allow_html=True)
            
            # --- RUTAS Y MOTOR ---
            archivo_log = "log_maestro_acumulado.csv"
            d_flet, d_price = motor_logistico_central() # Usa la función que definimos antes
            
            if 'db_acumulada' not in st.session_state:
                st.session_state.db_acumulada = pd.read_csv(archivo_log) if os.path.exists(archivo_log) else pd.DataFrame()

            # --- FUNCIONES DE SELLADO INTERNAS ---
            def generar_sellos_fisicos(lista_textos, x, y):
                output = PdfWriter()
                for texto in lista_textos:
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=letter)
                    can.setFont("Helvetica-Bold", 11)
                    can.drawString(x, y, f"{str(texto).upper()}")
                    can.save()
                    packet.seek(0)
                    output.add_page(PdfReader(packet).pages[0])
                out_io = io.BytesIO()
                output.write(out_io)
                return out_io.getvalue()

            def marcar_pdf_digital(pdf_file, texto_sello, x, y):
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.setFont("Helvetica-Bold", 11)
                can.drawString(x, y, f"{str(texto_sello).upper()}")
                can.save()
                packet.seek(0)
                new_pdf = PdfReader(packet)
                existing_pdf = PdfReader(pdf_file)
                output = PdfWriter()
                page = existing_pdf.pages[0]
                page.merge_page(new_pdf.pages[0])
                output.add_page(page)
                for i in range(1, len(existing_pdf.pages)):
                    output.add_page(existing_pdf.pages[i])
                out_io = io.BytesIO()
                output.write(out_io)
                return out_io.getvalue()

            # --- CARGA Y PROCESAMIENTO ERP ---
            file_p = st.file_uploader("📂 SUBIR ARCHIVO ERP (CSV)", type="csv")
            
            if file_p:
                if "archivo_actual" not in st.session_state or st.session_state.archivo_actual != file_p.name:
                    if "df_analisis" in st.session_state: del st.session_state["df_analisis"]
                    st.session_state.archivo_actual = file_p.name
                    st.rerun()

                try:
                    if "df_analisis" not in st.session_state:
                        p = pd.read_csv(file_p, encoding='utf-8-sig')
                        p.columns = [str(c).upper().strip() for c in p.columns]
                        col_id = 'FACTURA' if 'FACTURA' in p.columns else ('DOCNUM' if 'DOCNUM' in p.columns else p.columns[0])
                        
                        if 'DIRECCION' in p.columns:
                            def motor_prioridad(row):
                                es_local = d_local(row['DIRECCION']) # Función ZMG
                                if "LOCAL" in es_local: return "LOCAL"
                                return d_flet.get(row['DIRECCION'], "SIN HISTORIAL")

                            p['RECOMENDACION'] = p.apply(motor_prioridad, axis=1)
                            p['COSTO'] = p.apply(lambda r: 0.0 if r['RECOMENDACION'] == "LOCAL" else d_price.get(r['DIRECCION'], 0.0), axis=1)
                            p['FECHA_HORA'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            cols_sistema = [col_id, 'RECOMENDACION', 'COSTO', 'FECHA_HORA']
                            otras = [c for c in p.columns if c not in cols_sistema]
                            st.session_state.df_analisis = p[cols_sistema + otras]

                    st.markdown("### RECOMENDACIONES GENERADAS")
                    modo_edicion = st.toggle("🔓 EDITAR VALORES")
                    
                    p_editado = st.data_editor(
                        st.session_state.df_analisis,
                        use_container_width=True,
                        num_rows="fixed",
                        column_config={
                            "RECOMENDACION": st.column_config.TextColumn("🚚 FLETERA", disabled=not modo_edicion),
                            "COSTO": st.column_config.NumberColumn("💰 TARIFA", format="$%.2f", disabled=not modo_edicion),
                        },
                        key="editor_pro_v11"
                    )
                   
                    # --- BLOQUE DE ACCIONES FINALES (3 COLUMNAS SIMÉTRICAS) ---
                    with st.container():
                        c1, c2, c3 = st.columns(3)
                        
                        with c1:
                            st.download_button(
                                label="💾 DESCARGAR CSV",
                                data=p_editado.to_csv(index=False).encode('utf-8-sig'),
                                file_name="Analisis_Nexion.csv",
                                use_container_width=True
                            )
                            
                        with c2:
                            if st.button("📌 FIJAR CAMBIOS", use_container_width=True):
                                st.session_state.df_analisis = p_editado
                                st.toast("Cambios aplicados localmente", icon="📌")
                                
                        with c3:
                            id_guardado = f"guardado_{st.session_state.archivo_actual}"
                            if not st.session_state.get(id_guardado, False):
                                if st.button("🚀 GUARDAR REGISTROS", use_container_width=True):
                                    st.session_state[id_guardado] = True
                                    st.snow()
                                    st.rerun()
                            else:
                                st.button("✅ REGISTROS ASEGURADOS", use_container_width=True, disabled=True)
                
                    # --- SISTEMA DE SELLADO (DIVIDIDO EN COLUMNAS) ---
                    st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:30px 0; opacity:0.3;'>", unsafe_allow_html=True)
                    st.markdown("<h3 style='font-size: 16px; color: white;'>🖨️ SOBREIMPRESIÓN Y SELLADO DIGITAL</h3>", unsafe_allow_html=True)
                    
                    with st.expander("⚙️ PANEL DE CALIBRACIÓN (COORDENADAS PDF)", expanded=True):
                        col_x, col_y = st.columns(2)
                        ajuste_x = col_x.slider("Eje X", 0, 612, 510)
                        ajuste_y = col_y.slider("Eje Y", 0, 792, 760)
                    
                    col_izq, col_der = st.columns(2)
                    
                    with col_izq:
                        st.markdown("<p style='font-weight: 800; font-size: 12px; letter-spacing: 1px;'>IMPRESIÓN FÍSICA</p>", unsafe_allow_html=True)
                        if st.button("📄 GENERAR SELLOS PARA FACTURAS", use_container_width=True):
                            sellos = p_editado['RECOMENDACION'].tolist() if 'p_editado' in locals() else []
                            if sellos:
                                pdf_out = generar_sellos_fisicos(sellos, ajuste_x, ajuste_y)
                                st.download_button("⬇️ DESCARGAR SELLOS", pdf_out, "Sellos_Fisicos.pdf", use_container_width=True)
                            else:
                                st.warning("No hay datos cargados para generar sellos.")
                    
                    with col_der:
                        st.markdown("<p style='font-weight: 800; font-size: 12px; letter-spacing: 1px;'>SELLADO DIGITAL</p>", unsafe_allow_html=True)
                        pdfs = st.file_uploader("Subir PDFs para estampar", type="pdf", accept_multiple_files=True, key="uploader_digital")
                        
                        if pdfs:
                            if st.button("🎯 EJECUTAR SELLADO DIGITAL", use_container_width=True):
                                df_ref = st.session_state.get('df_analisis', pd.DataFrame())
                                if not df_ref.empty:
                                    mapa = pd.Series(df_ref.RECOMENDACION.values, index=df_ref[df_ref.columns[0]].astype(str)).to_dict()
                                    z_buf = io.BytesIO()
                                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                                        for pdf in pdfs:
                                            f_id = next((f for f in mapa.keys() if f in pdf.name.upper()), None)
                                            if f_id:
                                                zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ajuste_x, ajuste_y))
                                    st.download_button("⬇️ DESCARGAR ZIP SELLADO", z_buf.getvalue(), "Facturas_Digitales.zip", use_container_width=True)
                                else:
                                    st.error("Faltan datos de referencia para el sellado.")
        
                # --- AQUÍ CERRAMOS EL TRY Y EL IF DE ANALISIS ---
                except Exception as e:
                    st.error(f"Error en procesamiento: {e}")
                    
            # --- SALIMOS AL NIVEL DE MENU_MAIN PARA LOS OTROS SUBMENÚS ---
            elif st.session_state.menu_sub == "SISTEMA":
                st.write("Estado de servidores y conexión con GitHub/SAP.")
                
            elif st.session_state.menu_sub == "ALERTAS":
                st.warning("No hay alertas críticas en el sistema actual.")

# ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
st.markdown(f"""
<div class="footer">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 <br>
    <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY </span>
    <span style="color:{vars_css['text']}; font-weight:800; letter-spacing:3px;">XENOCODE</span>
</div>
""", unsafe_allow_html=True)

# ── FOOTER FIJO ────────────────────────
st.markdown(f"""
<div class="footer">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
</div>
""", unsafe_allow_html=True)






















































































































































































































































































































































































































































































































































































































































