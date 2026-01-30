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

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA FIJO (MODO CLARO FORZADO) ──────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "claro"
if "menu_main" not in st.session_state: 
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"

# Variables de diseño
vars_css = {
    "bg": "#E3E7ED",      # Fondo principal solicitado
    "card": "#FFFFFF",    # Fondos de tarjetas e inputs
    "text": "#111111",    # Texto principal
    "sub": "#2D3136",     # Texto secundario
    "border": "#C9D1D9",  # Bordes y líneas
    "logo": "n2.png"      # Logo
}

# ── CSS MAESTRO INTEGRAL (80% ZOOM + ESTILO NEXION FINAL) ──
# ── CSS MAESTRO (HEADER FULL WIDTH + CONTENIDO DINÁMICO CENTRADO) ──
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* 1. Limpieza y Fondo */
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    
    .stApp {{ 
        zoom: 0.8; 
        -moz-transform: scale(0.8); 
        -moz-transform-origin: top center;
        background-color: {vars_css['bg']} !important; 
    }}

    /* 2. CONTENEDOR PRINCIPAL: Permite que el header use todo el ancho */
    .block-container {{ 
        max-width: 95% !important; 
        margin: 0 auto !important;
        padding-top: 1rem !important; 
    }}

    /* 3. CENTRADO EXCLUSIVO DEL CONTENIDO DINÁMICO */
    /* Usamos el contenedor principal de contenido para limitar su ancho y centrarlo */
    /* Esto no afectará al header_zone porque el header está en su propio contenedor superior */
    [data-testid="stVerticalBlock"] > div.element-container {{
        width: 100%;
    }}

    /* Ajustamos el ancho de la zona de trabajo (tablas, gráficas, buscador) */
    /* Dejamos el header fuera de esta regla mediante la estructura del código */
    .dynamic-content-area {{
        max-width: 1100px;
        margin: 0 auto;
    }}

    /* 4. REPARACIÓN DE TABLA Y GANTT (Full Width dentro de su centro) */
    [data-testid="stDataFrame"], .js-plotly-plot {{
        width: 100% !important;
    }}
    
    [data-testid="stDataFrame"] canvas {{
        width: 100% !important;
    }}

    /* 5. TÍTULOS (S e g u i m i e n t o...) */
    h3 {{
        font-size: 13px !important; 
        font-weight: 400 !important;
        letter-spacing: 8px !important;
        text-align: center !important;
        margin-top: -5px !important;
        margin-bottom: 20px !important;
        color: {vars_css['sub']} !important;
        width: 100%;
    }}

    /* 6. BOTONES Y FOOTER (Sin cambios) */
    div.stButton > button {{
        background-color: {vars_css['card']} !important; 
        color: {vars_css['text']} !important;
        border: 1px solid {vars_css['border']} !important; 
        border-radius: 2px !important;
        font-weight: 700 !important; 
        height: 38px !important;
        width: 100% !important;
    }}

    .footer {{
        position: fixed;
        bottom: 0 !important; 
        left: 0 !important; 
        width: 100% !important;
        background-color: {vars_css['bg']} !important;
        text-align: center;
        padding: 15px 0px !important;
        font-size: 9px;
        letter-spacing: 2px;
        border-top: 1px solid {vars_css['border']} !important;
        z-index: 999999 !important;
        animation: none !important;
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
              <div style="width:40px;height:40px;border:1px solid {vars_css['border']};
              border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
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
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>", unsafe_allow_html=True)

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

# ── CONTENEDOR DE CONTENIDO (DINÁMICO CON CENTRADO REPARADO) ──
main_container = st.container()
with main_container:
    # 1. Envolvemos el contenido en el div de área dinámica para el centrado CSS
    st.markdown('<div class="dynamic-content-area">', unsafe_allow_html=True)
    
    # ── BLOQUE 1: TRACKING ──
    if st.session_state.menu_main == "TRACKING":
        st.markdown("<div style='margin-top: 5vh;'></div>", unsafe_allow_html=True)
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"<p class='op-query-text'>O P E R A T I O N A L &nbsp; Q U E R Y</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")

    # ── BLOQUE 2: SEGUIMIENTO ──
    elif st.session_state.menu_main == "SEGUIMIENTO":
        if st.session_state.menu_sub == "TRK":
            st.subheader("SEGUIMIENTO > TRK")
            st.info("Espacio para contenido de Tracking Operativo")
            
        elif st.session_state.menu_sub == "GANTT":
            st.subheader("SEGUIMIENTO > GANTT")
            
            # ---GANTT---CONFIGURACIÓN ---
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "tareas.csv"
            CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/tareas.csv"
            
            def obtener_fecha_mexico():
                utc_ahora = datetime.datetime.now(datetime.timezone.utc)
                return (utc_ahora - datetime.timedelta(hours=6)).date()
            
            def cargar_datos_seguro():
                columnas_base = ['FECHA', 'FECHA_FIN', 'IMPORTANCIA', 'TAREA', 'ULTIMO ACCION']
                hoy = obtener_fecha_mexico()
                try:
                    response = requests.get(f"{CSV_URL}?t={datetime.datetime.now().timestamp()}")
                    if response.status_code == 200:
                        df = pd.read_csv(StringIO(response.text))
                        df.columns = [c.strip().upper() for c in df.columns]
                        for col in columnas_base:
                            if col not in df.columns: df[col] = ""
                        for col in ['FECHA', 'FECHA_FIN']:
                            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
                            df[col] = df[col].apply(lambda x: x if isinstance(x, datetime.date) else hoy)
                        return df[columnas_base]
                    return pd.DataFrame(columns=columnas_base)
                except:
                    return pd.DataFrame(columns=columnas_base)
            
            def guardar_en_github(df):
                if not TOKEN:
                    st.error("Error: GITHUB_TOKEN no configurado"); return False
                try:
                    from github import Github
                    g = Github(TOKEN)
                    repo = g.get_repo(REPO_NAME)
                    df_save = df.copy()
                    df_save['FECHA'] = df_save['FECHA'].astype(str)
                    df_save['FECHA_FIN'] = df_save['FECHA_FIN'].astype(str)
                    csv_data = df_save.to_csv(index=False)
                    contents = repo.get_contents(FILE_PATH, ref="main")
                    repo.update_file(contents.path, f"Actualización NEXION {obtener_fecha_mexico()}", csv_data, contents.sha, branch="main")
                    st.toast("🚀 ¡Sincronizado con GitHub!", icon="✅")
                    return True
                except Exception as e:
                    st.error(f"Error al sincronizar: {e}")
                    return False
            
            if 'df_tareas' not in st.session_state:
                st.session_state.df_tareas = cargar_datos_seguro()
            
            # --- 4. GRÁFICO GANTT ---
            if not st.session_state.df_tareas.empty:
                try:
                    df_p = st.session_state.df_tareas.copy()
                    df_p['FECHA'] = pd.to_datetime(df_p['FECHA'])
                    df_p['FECHA_FIN'] = pd.to_datetime(df_p['FECHA_FIN'])
                    df_p = df_p.rename(columns={'TAREA':'Task', 'FECHA':'Start', 'FECHA_FIN':'Finish', 'IMPORTANCIA':'Resource'})
                    colors = {'Urgente': '#FF3131', 'Alta': '#FF914D', 'Media': '#00D2FF', 'Baja': '#444E5E'}
                    
                    import plotly.figure_factory as ff
                    fig = ff.create_gantt(df_p, colors=colors, index_col='Resource', group_tasks=True, showgrid_x=True, showgrid_y=True)
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)', 
                        font=dict(color=vars_css['text'], family="Inter"),
                        height=350,
                        margin=dict(l=100, r=20, t=20, b=50),
                        autosize=True
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                except Exception as e:
                    st.info("💡 Consejo: Completa las fechas de Inicio y Fin para ver el gráfico.")
            
            # --- 5. EDITOR ---
            with st.container():
                df_editado = st.data_editor(
                    st.session_state.df_tareas,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="nexion_editor_v8",
                    column_config={
                        "FECHA": st.column_config.DateColumn("📆 Inicio", required=True),
                        "FECHA_FIN": st.column_config.DateColumn("🏁 Fin", required=True),
                        "IMPORTANCIA": st.column_config.SelectboxColumn("🚦 Prioridad", options=["Baja", "Media", "Alta", "Urgente"]),
                        "TAREA": st.column_config.TextColumn("📝 Tarea"),
                        "ULTIMO ACCION": st.column_config.TextColumn("🚚 Estatus"),
                    },
                    hide_index=True
                )
                if st.button("💾 GUARDAR Y ACTUALIZAR CRONOGRAMA", use_container_width=True, type="primary"):
                    if guardar_en_github(df_editado):
                        st.session_state.df_tareas = df_editado
                        st.rerun()
        
        elif st.session_state.menu_sub == "QUEJAS":
            st.subheader("SEGUIMIENTO > PORTAL DE QUEJAS")
            st.info("Contenedor para registro y seguimiento de quejas")

    # ── BLOQUE 3: REPORTES ──
    elif st.session_state.menu_main == "REPORTES":
        st.subheader(f"MÓDULO DE INTELIGENCIA > {st.session_state.menu_sub}")

    # ── BLOQUE 4: FORMATOS ──
    elif st.session_state.menu_main == "FORMATOS":
        if st.session_state.menu_sub == "SALIDA DE PT":
            st.subheader("FORMATOS > SALIDA DE PRODUCTO TERMINADO")
        elif st.session_state.menu_sub == "PAGOS":
            st.subheader("FORMATOS > CONTROL DE PAGOS")
        else:
            st.subheader("CENTRO DE DOCUMENTACIÓN")
            st.write("Seleccione un formato del submenú superior.")

    # 2. Cerramos el área dinámica
    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER FIJO (SOLUCIÓN DEFINITIVA) ────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
    </div>
""", unsafe_allow_html=True)



























































































































































































































































































































































































































































