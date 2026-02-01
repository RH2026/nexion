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

vars_css = {
    "bg": "#0E1117",      # Fondo Onix Azulado
    "card": "#1A1F2B",    # Fondos de tarjetas e inputs
    "text": "#E0E6ED",    # Texto principal
    "sub": "#8892B0",     # Texto secundario
    "border": "#2D333B",  # Bordes y líneas
    "logo": "n1.png"      # Logo
}

# ── CSS MAESTRO INTEGRAL ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{
    visibility: hidden;
    height: 0px;
}}

html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}

.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 5rem !important;
}}

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(15px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

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

div.stButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 2px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 28px !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}}

div.stButton > button:hover {{
    background-color: #ffffff !important;
    color: #000000 !important;
    border-color: #ffffff !important;
}}

.stTextInput input {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 2px !important;
    height: 45px !important;
    text-align: center !important;
    letter-spacing: 2px;
}}

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
}}

/* Esto ahora funcionará correctamente dentro de tu f-string */
div[data-testid="stPopoverContent"] {{
    transition: opacity 0.3s ease-in-out !important;
    border: 1px solid {vars_css['border']} !important;
    background-color: {vars_css['bg']} !important;
}}

/* Ajuste opcional para que el expander interno combine con el look NEXION */
.stExpander {{
    border: none !important;
    background-color: transparent !important;
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
                
                # --- SECCIÓN TRACKING ---
                if st.button("TRACKING", use_container_width=True, key="pop_trk"):
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
            st.subheader("SEGUIMIENTO > GANTT")
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
            for i, r in df_gantt.iterrows():
                if not str(r["TAREA"]).strip(): continue
                importancia = str(r["IMPORTANCIA"]).strip().lower()
                tasks_data.append({
                    "id": str(i),
                    "name": f"[{r['GRUPO']}] {r['TAREA']}",
                    "start": str(r["FECHA"]),
                    "end": str(r["FECHA_FIN"]),
                    "progress": int(r["PROGRESO"]),
                    "dependencies": str(r["DEPENDENCIAS"]),
                    "custom_class": f"imp-{importancia}"
                })
            tasks_js_str = json.dumps(tasks_data)
            
            # ── 2. RENDERIZADO GANTT (ARRIBA) ──────────────────────────────────────────
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
                        .grid-line {{ stroke: #1e2530 !important; stroke-opacity: 0.4 !important; }}
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
                            setTimeout(function() {{
                                var lines = document.querySelectorAll('#gantt svg line');
                                lines.forEach(function(line) {{
                                    var x1 = line.getAttribute('x1'), x2 = line.getAttribute('x2');
                                    if(x1 === x2) {{ line.style.display = 'none'; }}
                                }});
                            }}, 100);
                        }}
                    </script>
                </body>
                </html>
                """,
                height=420, scrolling=False
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
            st.subheader("FORMATOS > SALIDA DE PRODUCTO TERMINADO")
        elif st.session_state.menu_sub == "PAGOS":
            st.subheader("FORMATOS > CONTROL DE PAGOS")
        else:
            # MATRIX ANIMATION
            st.subheader("CENTRO DE DOCUMENTACIÓN")
            st.components.v1.html(
                """
                <div id="matrix-container" style="width: 100%;">
                    <canvas id="matrix-canvas"></canvas>
                    <div class="overlay-text">NEXION CORE: ESPERANDO SELECCIÓN</div>
                </div>
                <style>
                    #matrix-container { height: 450px; background: #0E1117; border-radius: 10px; position: relative; border: 1px solid #1e2530; overflow: hidden; width: 100%; }
                    #matrix-canvas { display: block; width: 100%; }
                    .overlay-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #5d6d7e; font-family: sans-serif; font-weight: bold; letter-spacing: 10px; pointer-events: none; font-size: 0.9rem; text-transform: uppercase; text-align: center; width: 100%; animation: pulse-text 4s infinite ease-in-out; z-index: 10; }
                    @keyframes pulse-text { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.7; color: #3b82f6; } }
                </style>
                <script>
                    const canvas = document.getElementById('matrix-canvas');
                    const ctx = canvas.getContext('2d');
                    const container = document.getElementById('matrix-container');
                    function resize() { canvas.width = container.clientWidth; canvas.height = 450; }
                    resize();
                    const alphabet = "01XENOCODENEXION0101";
                    const fontSize = 14;
                    let columns = Math.floor(canvas.width / fontSize);
                    const drops = [];
                    function initDrops() {
                        columns = Math.floor(canvas.width / fontSize);
                        for (let x = 0; x < columns; x++) {
                            drops[x] = { currentX: x * fontSize, baseX: x * fontSize, y: Math.random() * -canvas.height, speed: Math.random() * 1.5 + 1 };
                        }
                    }
                    initDrops();
                    function draw() {
                        ctx.fillStyle = '#0E1117'; ctx.fillRect(0, 0, canvas.width, canvas.height);
                        ctx.font = fontSize + 'px monospace';
                        drops.forEach(drop => {
                            const text = alphabet.charAt(Math.floor(Math.random() * alphabet.length));
                            ctx.fillStyle = 'rgba(45, 55, 72, 0.15)';
                            ctx.fillText(text, drop.currentX, drop.y);
                            drop.y += drop.speed;
                            if (drop.y > canvas.height) drop.y = -20;
                        });
                    }
                    setInterval(draw, 30);
                    window.addEventListener('resize', () => { resize(); initDrops(); });
                </script>
                """, height=470
            )


# ── FOOTER FIJO ────────────────────────
st.markdown(f"""
<div class="footer">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
</div>
""", unsafe_allow_html=True)





































































































































































































































































































































































































































































































































































































