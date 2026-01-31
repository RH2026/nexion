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

/* 4. BOTONES SLIM CON HOVER NEGRO */
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
    background-color: #000000 !important; 
    color: #FFFFFF !important; 
    border-color: #000000 !important; 
}}

/* 6. INPUT DE BÚSQUEDA Y TEXTO OPERATIONAL */
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
            
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "tareas.csv"
            CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/tareas.csv"

            def obtener_fecha_mexico():
                return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=6)).date()

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
                    st.error("GITHUB_TOKEN not configured")
                    return False
                try:
                    g = Github(TOKEN)
                    repo = g.get_repo(REPO_NAME)
                    df_save = df.copy()
                    df_save['FECHA'] = df_save['FECHA'].astype(str)
                    df_save['FECHA_FIN'] = df_save['FECHA_FIN'].astype(str)
                    csv_data = df_save.to_csv(index=False)
                    contents = repo.get_contents(FILE_PATH, ref="main")
                    repo.update_file(contents.path, f"Sync NEXION {obtener_fecha_mexico()}", csv_data, contents.sha, branch="main")
                    st.toast("🚀 ¡Sincronizado!", icon="✅")
                    return True
                except Exception as e:
                    st.error(f"Error: {e}"); return False

            if 'df_tareas' not in st.session_state:
                st.session_state.df_tareas = cargar_datos_seguro()

            # ── 3. RENDERIZADO DEL GANTT (LÍNEAS REALES, SIN ROMPER NADA) ────────
            if not st.session_state.df_tareas.empty:
                try:
                    import plotly.graph_objects as go
            
                    df_p = st.session_state.df_tareas.copy()
                    df_p.columns = [c.strip().upper() for c in df_p.columns]
            
                    df_p['FECHA'] = pd.to_datetime(df_p['FECHA'], errors='coerce')
                    df_p['FECHA_FIN'] = pd.to_datetime(df_p['FECHA_FIN'], errors='coerce')
            
                    df_p = df_p[df_p['TAREA'].astype(str).str.strip() != ""]
            
                    df_p['FECHA_FIN'] = df_p.apply(
                        lambda r: r['FECHA'] + pd.Timedelta(days=1)
                        if pd.isna(r['FECHA_FIN']) or r['FECHA_FIN'] <= r['FECHA']
                        else r['FECHA_FIN'],
                        axis=1
                    )
            
                    df_p = df_p.dropna(subset=['FECHA', 'FECHA_FIN'])
            
                    if df_p.empty:
                        st.info("No hay tareas válidas para mostrar en el Gantt.")
                    else:
                        colors_nexion = {
                            "Urgente": "#FF3131",
                            "Alta": "#FF914D",
                            "Media": "#00D2FF",
                            "Baja": "#4B5563"
                        }
            
                        fig = go.Figure()
            
                        for _, row in df_p.iterrows():
                            fig.add_trace(go.Bar(
                                x=[(row['FECHA_FIN'] - row['FECHA']).days],
                                y=[row['TAREA']],
                                base=row['FECHA'],
                                orientation="h",
                                marker=dict(color=colors_nexion.get(row['IMPORTANCIA'], "#999999")),
                                width=0.18,   # ← AQUÍ está el grosor REAL de la línea
                                hovertemplate=(
                                    f"<b>{row['TAREA']}</b><br>"
                                    f"Inicio: {row['FECHA'].date()}<br>"
                                    f"Fin: {row['FECHA_FIN'].date()}<br>"
                                    f"Prioridad: {row['IMPORTANCIA']}"
                                ),
                                showlegend=False
                            ))
            
                        fig.update_layout(
                            height=200 + len(df_p) * 28,
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            margin=dict(l=20, r=20, t=10, b=20),
                            font=dict(family="Inter", size=11, color=vars_css['text']),
                            xaxis=dict(
                                title="",
                                gridcolor="rgba(0,0,0,0.08)",
                                tickfont=dict(size=10, color=vars_css['sub'])
                            ),
                            yaxis=dict(
                                autorange="reversed",
                                tickfont=dict(size=11, color=vars_css['text'])
                            )
                        )
            
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            
                except Exception as e:
                    st.error(f"Error al generar el Gantt: {e}")

            # 4. EDITOR DE DATOS
            df_editado = st.data_editor(
                st.session_state.df_tareas,
                num_rows="dynamic",
                use_container_width=True,
                key="nexion_editor_v2026",
                column_config={
                    "FECHA": st.column_config.DateColumn("📆 Inicio", required=True),
                    "FECHA_FIN": st.column_config.DateColumn("🏁 Fin", required=True),
                    "IMPORTANCIA": st.column_config.SelectboxColumn("🚦 Prioridad", options=["Baja", "Media", "Alta", "Urgente"]),
                    "TAREA": st.column_config.TextColumn("📝 Tarea"),
                    "ULTIMO ACCION": st.column_config.TextColumn("🚚 Estatus"),
                },
                hide_index=True
            )
            if st.button("💾 SINCRONIZAR CON GITHUB", type="primary", use_container_width=True):
                if guardar_en_github(df_editado):
                    st.session_state.df_tareas = df_editado
                    st.rerun()

        elif st.session_state.menu_sub == "QUEJAS":
            st.subheader("SEGUIMIENTO > PORTAL DE QUEJAS")
            st.info("Contenedor para registro y seguimiento de quejas")

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


















































































































































































































































































































































































































































































