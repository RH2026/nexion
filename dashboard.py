import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

if st.session_state.tema == "oscuro":
    bg_color = "#05070A"
    card_bg = "#0D1117"
    text_main = "#F0F6FC"
    text_sub = "#8B949E"
    border_color = "#1B1F24"
    btn_hover = "#161B22"
else:
    bg_color = "#F5F7FA"
    card_bg = "#FFFFFF"
    text_main = "#1A1C1E"
    text_sub = "#656D76"
    border_color = "#D8DEE4"
    btn_hover = "#EBEEF2"

# 3. CSS MAESTRO (AJUSTADO SIN CAMBIAR DISEÑO)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

header, footer, #MainMenu, div[data-testid="stDecoration"] {{ visibility: hidden; }}

.stApp {{
    background-color: {bg_color} !important;
    color: {text_main} !important;
    font-family: 'Inter', sans-serif !important;
}}

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
}}

div.stButton > button:hover {{
    background-color: {btn_hover} !important;
}}

div[data-testid="stSelectbox"] label p {{
    font-size: 10px !important;
    color: {text_sub} !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}}

/* OCULTAR NUMERACIÓN DE FILAS */
div[data-testid="stDataFrame"] th.row_heading,
div[data-testid="stDataFrame"] td.row_heading,
div[data-testid="stDataFrame"] th.blank {{
    display: none !important;
}}

/* CONTENEDOR TABLA – ALTURA DINÁMICA */
div[data-testid="stDataFrame"] {{
    max-height: calc(100vh - 330px) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}}

/* TABLA */
div[data-testid="stDataFrame"] table {{
    width: 100% !important;
    margin-left: 0 !important;
    border-collapse: collapse !important;
    table-layout: auto !important;
}}

/* CELDAS */
th, td {{
    white-space: normal !important;
    word-break: break-word !important;
    line-height: 1.2 !important;
}}

/* HEADERS */
thead th {{
    letter-spacing: 2px !important;
}}

/* SCROLLBAR DINÁMICO POR TEMA */
div[data-testid="stDataFrame"]::-webkit-scrollbar {{
    width: 6px;
}}

div[data-testid="stDataFrame"]::-webkit-scrollbar-track {{
    background: transparent;
}}

div[data-testid="stDataFrame"]::-webkit-scrollbar-thumb {{
    background-color: {border_color};
    border-radius: 6px;
}}

div[data-testid="stDataFrame"]:hover::-webkit-scrollbar-thumb {{
    background-color: {text_sub};
}}

</style>
""", unsafe_allow_html=True)



# 4. HEADER
c_logo, c_nav, c_theme = st.columns([1.5, 4, 0.5])
with c_logo:
    st.markdown(
        f"<h2 style='color:{text_main};font-weight:300;letter-spacing:4px;margin:0;'>NEXION</h2>"
        f"<p style='color:{text_sub};font-size:9px;margin-top:-5px;'>CORE INTELLIGENCE</p>",
        unsafe_allow_html=True
    )
with c_nav:
    m = st.columns(4)
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
    































































































































































































































































































































































