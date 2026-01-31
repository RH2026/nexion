# ───────────────────────── IMPORTS ─────────────────────────
import streamlit as st
import pandas as pd
import datetime, time, os, requests
from io import StringIO
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
from github import Github

# ───────────────────── CONFIGURACIÓN ───────────────────────
st.set_page_config(
    page_title="NEXION | Core",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ───────────────────── SESSION STATE ───────────────────────
st.session_state.setdefault("tema", "claro")
st.session_state.setdefault("menu_main", "TRACKING")
st.session_state.setdefault("menu_sub", "GENERAL")
st.session_state.setdefault("splash_completado", False)

# ───────────────────── VARIABLES UI ────────────────────────
vars_css = {
    "bg": "#E3E7ED",
    "card": "#FFFFFF",
    "text": "#111111",
    "sub": "#2D3136",
    "border": "#C9D1D9",
    "logo": "n2.png"
}

# ───────────────────── CSS MAESTRO ─────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, [data-testid="stHeader"] {{visibility:hidden;height:0}}
.stApp {{background:{vars_css['bg']}!important;color:{vars_css['text']}!important;font-family:Inter}}
.block-container {{padding-top:.8rem;padding-bottom:5rem}}

@keyframes fadeInUp{{from{{opacity:0;transform:translateY(15px)}}to{{opacity:1}}}}
[data-testid="stVerticalBlock"]>div:not(.element-container:has(.footer)){{animation:fadeInUp .6s ease-out}}

h3,.op-query-text {{
    font-size:11px;letter-spacing:8px;text-align:center;
    margin:8px 0 18px;color:{vars_css['sub']};width:100%
}}

.stButton>button {{
    background:{vars_css['card']};color:{vars_css['text']};
    border:1px solid {vars_css['border']};
    border-radius:2px;font-weight:700;
    text-transform:uppercase;font-size:10px;
    height:28px;transition:.2s;width:100%
}}
.stButton>button:hover{{background:#000;color:#fff;border-color:#000}}

.stTextInput input {{
    background:{vars_css['card']};color:{vars_css['text']};
    border:1px solid {vars_css['border']};
    border-radius:2px;height:45px;
    text-align:center;letter-spacing:2px
}}

.footer {{
    position:fixed;bottom:0;left:0;width:100%;
    background:{vars_css['bg']};color:{vars_css['sub']};
    text-align:center;padding:12px;
    font-size:9px;letter-spacing:2px;
    border-top:1px solid {vars_css['border']};
    z-index:999999
}}

.stPlotlyChart{{visibility:visible;opacity:1;min-height:300px}}
[data-testid="stVerticalBlock"]>div:has(div.stPlotlyChart){{animation:none;opacity:1}}
</style>
""", unsafe_allow_html=True)

# ───────────────────── SPLASH SCREEN ───────────────────────
if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in [
            "ESTABLISHING SECURE ACCESS",
            "PARSING LOGISTICS DATA",
            "SYSTEM READY"
        ]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;
            justify-content:center;align-items:center">
            <div style="width:40px;height:40px;border:1px solid {vars_css['border']};
            border-top:1px solid {vars_css['text']};border-radius:50%;
            animation:spin 1s linear infinite"></div>
            <p style="margin-top:40px;font-family:monospace;
            font-size:10px;letter-spacing:5px;color:{vars_css['text']}">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.7)
    st.session_state.splash_completado = True
    st.rerun()

# ───────────────────── HEADER ──────────────────────────────
with st.container():
    c1, c2 = st.columns([1.5, 5.4], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=120)
            st.markdown(
                f"<p style='font-size:8px;letter-spacing:2px;color:{vars_css['sub']};margin-top:-22px'>CORE INTELLIGENCE</p>",
                unsafe_allow_html=True
            )
        except:
            st.markdown("<h3>NEXION</h3>", unsafe_allow_html=True)

    with c2:
        main_menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]
        for col, m in zip(st.columns(4), main_menus):
            with col:
                label = f"● {m}" if st.session_state.menu_main == m else m
                if st.button(label, use_container_width=True, key=f"main_{m}"):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()

# ───────────────────── SUBMENÚ ─────────────────────────────
sub_map = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "PAGOS"]
}

subs = sub_map.get(st.session_state.menu_main, [])
if subs:
    with st.container():
        for col, s in zip(st.columns(len(subs) + 4), subs):
            with col:
                label = f"» {s}" if st.session_state.menu_sub == s else s
                if st.button(label, use_container_width=True, key=f"sub_{s}"):
                    st.session_state.menu_sub = s
                    st.rerun()
    st.markdown(
        f"<hr style='border-top:1px solid {vars_css['border']};opacity:.3'>",
        unsafe_allow_html=True
    )

# ───────────────────── CONTENIDO ───────────────────────────
with st.container():

    # TRACKING
    if st.session_state.menu_main == "TRACKING":
        _, c, _ = st.columns([1, 1.6, 1])
        with c:
            st.markdown("<p class='op-query-text'>OPERATIONAL QUERY</p>", unsafe_allow_html=True)
            ref = st.text_input("", placeholder="INGRESE GUÍA O REFERENCIA...")
            if st.button("EXECUTE SYSTEM SEARCH", use_container_width=True):
                st.toast(f"Buscando: {ref}")

    # SEGUIMIENTO
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
                return (datetime.datetime.now(datetime.timezone.utc)
                        - datetime.timedelta(hours=6)).date()

            def cargar_datos_seguro():
                columnas = ['FECHA','FECHA_FIN','IMPORTANCIA','TAREA','ULTIMO ACCION']
                hoy = obtener_fecha_mexico()
                try:
                    r = requests.get(f"{CSV_URL}?t={datetime.datetime.now().timestamp()}")
                    if r.status_code == 200:
                        df = pd.read_csv(StringIO(r.text))
                        df.columns = [c.strip().upper() for c in df.columns]
                        for c in columnas:
                            if c not in df.columns:
                                df[c] = ""
                        for c in ['FECHA','FECHA_FIN']:
                            df[c] = pd.to_datetime(df[c], errors='coerce').dt.date
                            df[c] = df[c].apply(lambda x: x if isinstance(x, datetime.date) else hoy)
                        return df[columnas]
                except:
                    pass
                return pd.DataFrame(columns=columnas)

            if "df_tareas" not in st.session_state:
                st.session_state.df_tareas = cargar_datos_seguro()

            if not st.session_state.df_tareas.empty:
                df = st.session_state.df_tareas.copy()
                df['FECHA'] = pd.to_datetime(df['FECHA'])
                df['FECHA_FIN'] = pd.to_datetime(df['FECHA_FIN'])

                mask = df['FECHA'] == df['FECHA_FIN']
                df.loc[mask, 'FECHA_FIN'] += pd.Timedelta(days=1)

                df = df.dropna(subset=['FECHA','FECHA_FIN','TAREA'])

                if not df.empty:
                    colors = {
                        'Urgente':'#FF3131',
                        'Alta':'#FF914D',
                        'Media':'#00D2FF',
                        'Baja':'#444E5E'
                    }

                    fig = px.timeline(
                        df,
                        x_start="FECHA",
                        x_end="FECHA_FIN",
                        y="TAREA",
                        color="IMPORTANCIA",
                        color_discrete_map=colors,
                        category_orders={"IMPORTANCIA":["Urgente","Alta","Media","Baja"]}
                    )

                    fig.update_yaxes(autorange="reversed", title="")
                    fig.update_traces(marker_line_color="white", marker_line_width=1, width=.6)
                    fig.update_layout(
                        height=300,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10,r=10,t=10,b=10),
                        legend=dict(orientation="h",y=1.1,x=1)
                    )

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

            df_editado = st.data_editor(
                st.session_state.df_tareas,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True
            )

        elif st.session_state.menu_sub == "QUEJAS":
            st.subheader("SEGUIMIENTO > PORTAL DE QUEJAS")
            st.info("Contenedor para registro y seguimiento de quejas")

    # REPORTES
    elif st.session_state.menu_main == "REPORTES":
        st.subheader(f"MÓDULO DE INTELIGENCIA > {st.session_state.menu_sub}")

    # FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        if st.session_state.menu_sub == "SALIDA DE PT":
            st.subheader("FORMATOS > SALIDA DE PRODUCTO TERMINADO")
        elif st.session_state.menu_sub == "PAGOS":
            st.subheader("FORMATOS > CONTROL DE PAGOS")
        else:
            st.subheader("CENTRO DE DOCUMENTACIÓN")

# ───────────────────── FOOTER ──────────────────────────────
st.markdown("""
<div class="footer">
NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
</div>
""", unsafe_allow_html=True)














































































































































































































































































































































































































































































