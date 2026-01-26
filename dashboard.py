import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

if st.session_state.tema == "oscuro":
    bg_color, card_bg, text_main, text_sub, border_color, btn_hover = "#05070A", "#0D1117", "#F0F6FC", "#8B949E", "#1B1F24", "#161B22"
else:
    bg_color, card_bg, text_main, text_sub, border_color, btn_hover = "#F5F7FA", "#FFFFFF", "#1A1C1E", "#656D76", "#D8DEE4", "#EBEEF2"

# 3. CSS MAESTRO (DISEÑO EXACTO + FUERZA BRUTA PARA ICONOS INFERIORES)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

/* 1. OCULTAR CABECERA, DECORACIÓN Y FOOTER NATIVO */
header, footer, #MainMenu, div[data-testid="stDecoration"] {{ 
    visibility: hidden !important; 
    display: none !important;
}}

/* 2. FUERZA BRUTA PARA ICONOS INFERIORES (Manage App, Streamlit Cloud, etc.) */
/* Atacamos por testid, clases dinámicas y selectores de posición */
[data-testid="stStatusWidget"], 
[data-testid="stCloudGlutton"],
.viewerBadge_container__1QSob, 
.stActionButton,
div[class^="viewerBadge"],
div[class*="StyledStatusWidget"],
div[data-testid="stBaseButton-toolbar"],
#tabs-bue-container + div {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

/* 3. ESTILO BASE DE LA APP */
.stApp {{
    background-color: {bg_color} !important;
    color: {text_main} !important;
    font-family: 'Inter', sans-serif !important;
}}

/* BOTONES Y SELECTORES */
div.stButton > button,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    background-color: {card_bg} !important;
    color: {text_main} !important;
    border: 1px solid {border_color} !important;
    border-radius: 2px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    transition: all 0.3s ease;
}}

div.stButton > button:hover {{
    background-color: {btn_hover} !important;
    border-color: {text_main} !important;
}}

/* BOTÓN DE BÚSQUEDA PRIMARIO */
div.stButton > button[kind="primary"] {{
    background-color: {text_main} !important;
    color: {bg_color} !important;
    border: none !important;
    font-weight: 700 !important;
    height: 48px !important;
}}

.stTextInput input {{
    background-color: {card_bg} !important;
    color: {text_main} !important;
    border: 1px solid {border_color} !important;
    border-radius: 2px !important;
    height: 48px !important;
}}

div[data-testid="stSelectbox"] label p {{
    font-size: 10px !important;
    color: {text_sub} !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}}
</style>
""", unsafe_allow_html=True)

# 4. LÓGICA DE SPLASH SCREEN
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    placeholder = st.empty()
    with placeholder.container():
        mensajes = ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]
        for m in mensajes:
            st.markdown(f"""
                <div style="height: 80vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: {bg_color};">
                    <div style="width: 30px; height: 30px; border: 1px solid {border_color}; border-top: 1px solid {text_main}; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    <p style="color: {text_main}; font-family: monospace; font-size: 10px; letter-spacing: 5px; margin-top: 40px; font-weight: 200;">{m}</p>
                </div>
                <style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
            """, unsafe_allow_html=True)
            time.sleep(0.9)
    st.session_state.splash_completado = True
    st.rerun()

# 5. HEADER
c_logo, c_nav, c_theme = st.columns([1.5, 4, 0.5])
with c_logo:
    st.markdown(f"<h2 style='color: {text_main}; font-weight: 300; letter-spacing: 4px; margin: 0;'>NEXION</h2><p style='color: {text_sub}; font-size: 9px; margin-top: -5px; letter-spacing: 1px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)

with c_nav:
    m = st.columns(4)
    if "pagina" not in st.session_state: st.session_state.pagina = "RASTREO"
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "ESTATUS"]):
        with m[i]:
            if st.button(b, use_container_width=True):
                st.session_state.pagina = b
                st.rerun()

with c_theme:
    if st.button("☀️" if st.session_state.tema == "oscuro" else "🌙"):
        st.session_state.tema = "claro" if st.session_state.tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {border_color}; margin:10px 0 30px;'>", unsafe_allow_html=True)

# 5. DATOS
@st.cache_data
def cargar_datos():
    df = pd.DataFrame()  # <-- GARANTÍA DE EXISTENCIA

    try:
        df = pd.read_csv("Matriz_Excel_Dashboard.csv", encoding="utf-8")
        df.columns = df.columns.str.strip().str.upper()

        if "NO CLIENTE" in df.columns:
            df["NO CLIENTE"] = df["NO CLIENTE"].astype(str).str.strip()

        # Normalizar fechas SOLO si existen
        for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

        hoy = pd.Timestamp.today().normalize()

        # Columna siempre creada
        df["ESTATUS_CALCULADO"] = "EN TRANSITO"

        if "FECHA DE ENTREGA REAL" in df.columns:
            df.loc[df["FECHA DE ENTREGA REAL"].notna(), "ESTATUS_CALCULADO"] = "ENTREGADO"

        if "PROMESA DE ENTREGA" in df.columns:
            df.loc[
                df["FECHA DE ENTREGA REAL"].isna()
                & df["PROMESA DE ENTREGA"].notna()
                & (df["PROMESA DE ENTREGA"] < hoy),
                "ESTATUS_CALCULADO"
            ] = "RETRASADO"

        return df

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return df

df = cargar_datos()

# 6. FUNCIÓN DE TABLA DINÁMICA (CLAVE)
def tabla_estilizada(df):
    return (
        df.style
        .set_properties(**{
            "background-color": card_bg,
            "color": text_sub,
            "border": f"1px solid {border_color}",
            "font-size": "11px"
        })
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", card_bg),
                    ("color", text_main),
                    ("border", f"1px solid {border_color}"),
                    ("font-size", "11px"),
                    ("text-transform", "uppercase"),
                    ("letter-spacing", "2px")
                ]
            }
        ])
        .hide(axis="index")
    )

# 7. RENDERIZADO RASTREO (CAJA DE BÚSQUEDA DHL)
if st.session_state.pagina == "RASTREO":
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    
    # --- CAJA DE BÚSQUEDA CENTRALIZADA ---
    _, col_search, _ = st.columns([1, 1.8, 1])
    with col_search:
        st.markdown(f"<p style='text-align: center; color: {text_sub}; font-size: 11px; letter-spacing: 3px; text-transform: uppercase;'>Operational Query</p>", unsafe_allow_html=True)
        busqueda = st.text_input("", placeholder="REFERENCIA O NÚMERO DE GUÍA...", label_visibility="collapsed")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        btn_search = st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True)

    st.markdown("<div style='margin-bottom: 60px;'></div>", unsafe_allow_html=True)


# 7. RENDER
if st.session_state.get("pagina", "RASTREO") == "RASTREO":

    f1, f2, f3, f4 = st.columns(4)
    df_visual = df.copy().reset_index(drop=True)

    # FILTROS
    with f1:
        f_cli = st.selectbox(
            "Client ID",
            ["ALL"] + sorted(df_visual["NO CLIENTE"].dropna().unique())
        )
    with f2:
        f_car = st.selectbox(
            "Carrier",
            ["ALL"] + sorted(df_visual["FLETERA"].dropna().unique())
        )
    with f3:
        f_des = st.selectbox(
            "Destination",
            ["ALL"] + sorted(df_visual["DESTINO"].dropna().unique())
        )
    with f4:
        f_est = st.selectbox(
            "Status",
            ["ALL"] + sorted(df_visual["ESTATUS_CALCULADO"].dropna().unique())
        )

    if f_cli != "ALL":
        df_visual = df_visual[df_visual["NO CLIENTE"] == f_cli]
    if f_car != "ALL":
        df_visual = df_visual[df_visual["FLETERA"] == f_car]
    if f_des != "ALL":
        df_visual = df_visual[df_visual["DESTINO"] == f_des]
    if f_est != "ALL":
        df_visual = df_visual[df_visual["ESTATUS_CALCULADO"] == f_est]

    # COLUMNAS A MOSTRAR
    COLUMNAS_VISTA = [
        "NO CLIENTE",
        "NÚMERO DE PEDIDO",
        "NOMBRE DEL CLIENTE",
        "DESTINO",
        "FECHA DE ENVÍO",
        "PROMESA DE ENTREGA",
        "FLETERA",
        "NÚMERO DE GUÍA",
        "ESTATUS_CALCULADO"
    ]

    df_visual = df_visual.reset_index(drop=True)

    # FORMATO FECHAS (SOLO FECHA, SIN HORA)
    for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA"]:
        df_visual[col] = (
            pd.to_datetime(df_visual[col], errors="coerce")
            .dt.strftime("%d/%m/%Y")
        )

    components.html(
    f"""
    <div style="
        width:100%;
        height:600px;
        display:flex;
        flex-direction:column;
    ">
        <div style="flex:0 0 auto;">
            {tabla_estilizada(df_visual[COLUMNAS_VISTA]).to_html()}
        </div>

        <!-- ESPACIADOR INVISIBLE -->
        <div style="flex:1 1 auto;"></div>
    </div>
    """,
    height=600,
    scrolling=True
)
    





































































































































































































































































































































































