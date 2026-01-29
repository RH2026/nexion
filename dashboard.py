import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
from github import Github
import plotly.figure_factory as ff
import plotly.graph_objects as go
import time

# ── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────
st.set_page_config(
    page_title="NEXION | Core",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── ESTADO GLOBAL ────────────────────────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

tema = st.session_state.tema

vars_css = {
    "oscuro": {
        "bg": "#0E1117",
        "card": "#111827",
        "text": "#F0F6FC",
        "sub": "#8B949E",
        "border": "#1B1F24",
        "logo": "n1.png"
    },
    "claro": {
        "bg": "#E3E7ED",
        "card": "#FFFFFF",
        "text": "#111111",
        "sub": "#2D3136",
        "border": "#C9D1D9",
        "logo": "n2.png"
    }
}[tema]

# ── CSS MAESTRO ESTABILIZADO ──────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{
    visibility: hidden;
    height: 0px;
}}

.block-container {{
    padding-top: 0.5rem !important;
    padding-bottom: 0rem !important;
}}

.stApp {{
    background: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
    transition: background-color .6s ease, color .6s ease;
}}

/* ── CONTENIDO ANIMADO SOLAMENTE ── */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.main-content > div {{
    animation: fadeInUp .45s ease-out;
}}

/* INPUT */
.stTextInput input {{
    background: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    height: 42px !important;
    font-size: 11px !important;
    text-align: center !important;
    letter-spacing: 2px;
}}

/* BOTONES */
div.stButton > button {{
    background: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    font-size: 10px !important;
    height: 32px !important;
    font-weight: 700 !important;
    width: 100%;
    min-width: 40px;
}}

div.stButton > button:hover {{
    background: {vars_css['text']} !important;
    color: {vars_css['bg']} !important;
}}

/* LOGO ESTABLE */
div[data-testid="stImage"] img {{
    height: 48px !important;
    object-fit: contain !important;
}}

.footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: {vars_css['bg']};
    color: {vars_css['sub']};
    font-size: 9px;
    letter-spacing: 2px;
    text-align: center;
    padding: 10px;
    border-top: 1px solid {vars_css['border']};
    z-index: 100;
}}

/* PLACEHOLDER FIX (CLARO + OSCURO) */
    .stTextInput input::placeholder {{
        color: {vars_css['sub']} !important;
        opacity: 1 !important;
    }}

    .stTextInput input::-webkit-input-placeholder {{
        color: {vars_css['sub']} !important;
    }}

    .stTextInput input:-ms-input-placeholder {{
        color: {vars_css['sub']} !important;
    }}
</style>
""", unsafe_allow_html=True)


# ── SPLASH ───────────────────────────────────────────────────
if not st.session_state.splash_completado:
    splash = st.empty()
    with splash.container():
        for txt in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;
                        justify-content:center;align-items:center;">
                <div style="width:40px;height:40px;border:1px solid {vars_css['border']};
                            border-top:1px solid {vars_css['text']};
                            border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-size:10px;letter-spacing:5px;
                          color:{vars_css['text']};">{txt}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.6)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER Y NAVEGACIÓN PRINCIPAL ──────────────────────────
header_zone = st.container()
with header_zone:
    c1, c2, c3 = st.columns([1.5, 5, 0.4], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=120)
            st.markdown(
                f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; "
                f"margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>",
                unsafe_allow_html=True
            )
        except:
            st.markdown(
                "<h3 style='letter-spacing:4px; font-weight:800; margin:0;'>NEXION</h3>",
                unsafe_allow_html=True
            )

    with c2:
        cols_main = st.columns(4)
        main_menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]

        for i, m in enumerate(main_menus):
            with cols_main[i]:
                label = f"● {m}" if st.session_state.menu_main == m else m
                if st.button(label, key=f"main_{m}", use_container_width=True):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()

    with c3:
        icon = "☾" if tema == "oscuro" else "☀"
        if st.button(icon, key="theme_btn"):
            st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
            st.rerun()

st.markdown(
    f"<hr style='border-top:1px solid {vars_css['border']}; margin:-5px 0 10px;'>",
    unsafe_allow_html=True
)

# ── SUB MENÚS (RESTAURADOS, ESTABLES, SIN ANIMACIÓN) ─────────
sub_zone = st.container()
with sub_zone:
    sub_map = {
        "TRACKING": [],
        "SEGUIMIENTO": ["TRK", "GANTT"],
        "REPORTES": ["APQ", "OPS", "OTD"],
        "FORMATOS": ["SALIDA DE PT"]
    }

    current_subs = sub_map.get(st.session_state.menu_main, [])

    if current_subs:
        cols_sub = st.columns(len(current_subs) + 4)

        for i, s in enumerate(current_subs):
            with cols_sub[i]:
                label = f"» {s}" if st.session_state.menu_sub == s else s
                if st.button(label, key=f"sub_{s}", use_container_width=True):
                    st.session_state.menu_sub = s
                    st.rerun()

        st.markdown(
            f"<hr style='border-top:1px solid {vars_css['border']}; "
            f"opacity:0.3; margin:0px 0 20px;'>",
            unsafe_allow_html=True
        )

# ── CONTENIDO (ÚNICO BLOQUE ANIMADO) ────────────────────────
st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# 1. TRACKING
if st.session_state.menu_main == "TRACKING":
    st.markdown("<div style='margin-top: 8vh;'></div>", unsafe_allow_html=True)
    _, col_search, _ = st.columns([1, 1.6, 1])

    with col_search:
        st.markdown(
            f"<p style='text-align:center; color:{vars_css['sub']}; "
            f"font-size:11px; letter-spacing:8px; margin-bottom:20px;'>"
            f"O P E R A T I O N A L &nbsp; Q U E R Y</p>",
            unsafe_allow_html=True
        )

        busqueda = st.text_input(
            "REF",
            placeholder="INGRESE GUÍA O REFERENCIA...",
            label_visibility="collapsed"
        )

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
            st.toast(f"Buscando: {busqueda}")

# 2. SEGUIMIENTO
elif st.session_state.menu_main == "SEGUIMIENTO":

    if st.session_state.menu_sub == "TRK":
        st.subheader("SEGUIMIENTO > TRK")

    elif st.session_state.menu_sub == "GANTT":
        st.subheader("SEGUIMIENTO > GANTT")
        # ─────────────────────────────────────────────
        # 1. CONFIGURACIÓN GENERAL
        # ─────────────────────────────────────────────
        TOKEN = st.secrets.get("GITHUB_TOKEN", None)
        REPO_NAME = "RH2026/nexion"
        FILE_PATH = "tareas.csv"
        CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/tareas.csv"
        
        # ─────────────────────────────────────────────
        # 2. TEMA (FUENTE ÚNICA DE VERDAD)
        # ─────────────────────────────────────────────
        vars_css = {
            "bg": "#05070A",
            "card": "#0D1117",
            "text": "#F0F6FC",
            "sub": "#8B949E",
            "border": "#30363D"
        }
        
        # ─────────────────────────────────────────────
        # 3. CSS MAESTRO (UNA SOLA VEZ, BIEN CERRADO)
        # ─────────────────────────────────────────────
        st.markdown(f"""
        <style>
        :root {{
            --bg: {vars_css['bg']};
            --card: {vars_css['card']};
            --text: {vars_css['text']};
            --sub: {vars_css['sub']};
            --border: {vars_css['border']};
        }}
        
        html, body {{
            background-color: var(--bg);
            color: var(--text);
        }}
        
        .stTextInput input,
        .stTextArea textarea {{
            color: var(--text) !important;
        }}
        
        .stTextInput input::placeholder {{
            color: var(--sub) !important;
            opacity: 1 !important;
        }}
        
        [data-testid="stDataEditor"] thead tr th {{
            background-color: var(--card) !important;
            color: var(--text) !important;
            border-bottom: 1px solid var(--border) !important;
        }}
        
        [data-testid="stDataEditor"] tbody tr td {{
            background-color: var(--bg) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }}
        
        [data-testid="stDataEditor"] input,
        [data-testid="stDataEditor"] textarea {{
            background-color: transparent !important;
            color: var(--text) !important;
        }}
        
        [data-testid="stDataEditor"] input::placeholder {{
            color: var(--sub) !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # ─────────────────────────────────────────────
        # 4. FECHA MÉXICO
        # ─────────────────────────────────────────────
        def obtener_fecha_mexico():
            utc = datetime.datetime.now(datetime.timezone.utc)
            return (utc - datetime.timedelta(hours=6)).date()
        
        # ─────────────────────────────────────────────
        # 5. CARGA DE DATOS SEGURA
        # ─────────────────────────────────────────────
        def cargar_datos_seguro():
            columnas = ['FECHA', 'FECHA_FIN', 'IMPORTANCIA', 'TAREA', 'ULTIMO ACCION']
            hoy = obtener_fecha_mexico()
        
            try:
                r = requests.get(f"{CSV_URL}?t={datetime.datetime.now().timestamp()}")
                if r.status_code == 200:
                    df = pd.read_csv(StringIO(r.text))
                    df.columns = [c.strip().upper() for c in df.columns]
        
                    for col in columnas:
                        if col not in df.columns:
                            df[col] = ""
        
                    for col in ['FECHA', 'FECHA_FIN']:
                        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
                        df[col] = df[col].fillna(hoy)
        
                    return df[columnas]
            except:
                pass
        
            return pd.DataFrame(columns=columnas)
        
        # ─────────────────────────────────────────────
        # 6. GUARDAR EN GITHUB
        # ─────────────────────────────────────────────
        def guardar_en_github(df):
            if not TOKEN:
                st.error("GITHUB_TOKEN no configurado")
                return False
        
            try:
                g = Github(TOKEN)
                repo = g.get_repo(REPO_NAME)
        
                df_save = df.copy()
                df_save['FECHA'] = df_save['FECHA'].astype(str)
                df_save['FECHA_FIN'] = df_save['FECHA_FIN'].astype(str)
        
                csv = df_save.to_csv(index=False)
                contents = repo.get_contents(FILE_PATH, ref="main")
        
                repo.update_file(
                    contents.path,
                    f"Actualización {obtener_fecha_mexico()}",
                    csv,
                    contents.sha,
                    branch="main"
                )
        
                st.toast("Sincronizado con GitHub", icon="✅")
                return True
        
            except Exception as e:
                st.error(f"Error GitHub: {e}")
                return False
        
        # ─────────────────────────────────────────────
        # 7. ESTADO
        # ─────────────────────────────────────────────
        if "df_tareas" not in st.session_state:
            st.session_state.df_tareas = cargar_datos_seguro()
        
        # ─────────────────────────────────────────────
        # 8. GANTT (TOTALMENTE ADAPTADO AL TEMA)
        # ─────────────────────────────────────────────
        if not st.session_state.df_tareas.empty:
            df_p = st.session_state.df_tareas.rename(columns={
                "TAREA": "Task",
                "FECHA": "Start",
                "FECHA_FIN": "Finish",
                "IMPORTANCIA": "Resource"
            })
        
            colors = {
                "Urgente": "#FF3131",
                "Alta": "#FF914D",
                "Media": "#00D2FF",
                "Baja": "#444E5E"
            }
        
            fig = ff.create_gantt(
                df_p,
                colors=colors,
                index_col="Resource",
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True
            )
        
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=vars_css["text"], family="Inter", size=11),
                hoverlabel=dict(
                    bgcolor=vars_css["card"],
                    font=dict(color=vars_css["text"]),
                    bordercolor=vars_css["border"]
                ),
                height=450,
                margin=dict(l=180, r=20, t=40, b=80)
            )
        
            fig.update_xaxes(
                tickfont=dict(color=vars_css["sub"]),
                gridcolor=vars_css["border"],
                linecolor=vars_css["border"]
            )
        
            fig.update_yaxes(
                tickfont=dict(color=vars_css["text"]),
                gridcolor=vars_css["border"],
                linecolor=vars_css["border"],
                autorange="reversed"
            )
        
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        
        # ─────────────────────────────────────────────
        # 9. EDITOR
        # ─────────────────────────────────────────────
        df_editado = st.data_editor(
            st.session_state.df_tareas,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_tareas",
            column_config={
                "FECHA": st.column_config.DateColumn("Inicio"),
                "FECHA_FIN": st.column_config.DateColumn("Fin"),
                "IMPORTANCIA": st.column_config.SelectboxColumn(
                    "Prioridad",
                    options=["Baja", "Media", "Alta", "Urgente"]
                ),
                "TAREA": st.column_config.TextColumn("Tarea"),
                "ULTIMO ACCION": st.column_config.TextColumn("Estatus")
            },
            hide_index=True
        )
        
        if st.button("GUARDAR Y ACTUALIZAR", type="primary", use_container_width=True):
            if guardar_en_github(df_editado):
                st.session_state.df_tareas = df_editado
                st.rerun()


# 3. REPORTES
elif st.session_state.menu_main == "REPORTES":

    if st.session_state.menu_sub == "APQ":
        st.subheader("REPORTES > APQ")

    elif st.session_state.menu_sub == "OPS":
        st.subheader("REPORTES > OPS")

    elif st.session_state.menu_sub == "OTD":
        st.subheader("REPORTES > OTD")

# 4. FORMATOS
elif st.session_state.menu_main == "FORMATOS":

    if st.session_state.menu_sub == "SALIDA DE PT":
        st.subheader("FORMATOS > SALIDA DE PT")

st.markdown("</div>", unsafe_allow_html=True)











































































































































































































































































































































































































































