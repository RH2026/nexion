import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA CON COLORES REFINADOS
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

if st.session_state.tema == "oscuro":
    # MODO ONYX (Midnight)
    bg_color = "#05070A"      
    card_bg = "#0D1117"       
    text_main = "#F0F6FC"
    text_sub = "#8B949E"
    border_color = "#1B1F24"
    btn_hover = "#161B22"
else:
    # MODO PEARL (Zara Style)
    bg_color = "#F5F7FA"      # Blanco Aperlado
    card_bg = "#FFFFFF"       # Blanco puro para tabla/botones
    text_main = "#1A1C1E"     # Texto principal (Negro elegante)
    text_sub = "#656D76"      # Texto secundario (Gris legible)
    border_color = "#D8DEE4"  # Bordes gris seda
    btn_hover = "#EBEEF2"

# 3. CSS MAESTRO (CORREGIDO PARA FORZAR TABLA BLANCA/GRIS)
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

        header, footer, #MainMenu, div[data-testid="stDecoration"] {{visibility: hidden;}}
        
        .stApp {{
            background-color: {bg_color} !important;
            color: {text_main} !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* BOTONES Y SELECTORES UNIFICADOS */
        div.stButton > button, div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
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

        /* --- CORRECCIÓN DE TABLA --- */
        /* Forzamos el fondo de la tabla y celdas */
        div[data-testid="stDataFrame"] {{
            background-color: {card_bg} !important;
        }}
        
        /* Forzamos el color del texto y fondo en las celdas de la tabla para que sea gris legible en blanco */
        div[data-testid="stDataFrame"] [data-testid="stTable"] {{
            background-color: {card_bg} !important;
            color: {text_sub} !important;
        }}

        /* Títulos de filtros */
        div[data-testid="stSelectbox"] label p {{
            font-size: 10px !important;
            color: {text_sub} !important;
            letter-spacing: 2px !important;
            text-transform: uppercase !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 4. HEADER Y NAVEGACIÓN
c_logo, c_nav, c_theme = st.columns([1.5, 4, 0.5])
with c_logo:
    st.markdown(f"<h2 style='color: {text_main}; font-weight: 300; letter-spacing: 4px; margin: 0;'>NEXION</h2><p style='color: {text_sub}; font-size: 9px; margin-top: -5px; letter-spacing: 1px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
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

st.markdown(f"<hr style='border:0; border-top:1px solid {border_color}; margin:10px 0 30px 0;'>", unsafe_allow_html=True)

# 5. MOTOR DE DATOS
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("Matriz_Excel_Dashboard.csv", encoding="utf-8")
        df.columns = df.columns.str.strip().str.upper()
        df["NO CLIENTE"] = df["NO CLIENTE"].astype(str).str.strip()
        columnas_fecha = ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
        hoy = pd.Timestamp.today().normalize()
        df["ESTATUS_CALCULADO"] = df.apply(lambda r: "ENTREGADO" if pd.notna(r["FECHA DE ENTREGA REAL"]) else ("RETRASADO" if pd.notna(r["PROMESA DE ENTREGA"]) and r["PROMESA DE ENTREGA"] < hoy else "EN TRANSITO"), axis=1)
        return df
    except:
        return pd.DataFrame(columns=["NO CLIENTE", "FLETERA", "DESTINO", "ESTATUS_CALCULADO"])

df = cargar_datos()

# 6. RENDERIZADO DE TABLA Y FILTROS
if st.session_state.get("pagina", "RASTREO") == "RASTREO":
    f1, f2, f3, f4 = st.columns(4)
    df_visual = df.copy()
    
    with f1: f_cli = st.selectbox("Client ID", options=["ALL"] + sorted(df_visual["NO CLIENTE"].unique().tolist()))
    with f2: f_car = st.selectbox("Carrier", options=["ALL"] + sorted(df_visual["FLETERA"].unique().tolist()))
    with f3: f_des = st.selectbox("Destination", options=["ALL"] + sorted(df_visual["DESTINO"].unique().tolist()))
    with f4: f_est = st.selectbox("Status", options=["ALL"] + sorted(df_visual["ESTATUS_CALCULADO"].unique().tolist()))

    if f_cli != "ALL": df_visual = df_visual[df_visual["NO CLIENTE"] == f_cli]
    if f_car != "ALL": df_visual = df_visual[df_visual["FLETERA"] == f_car]
    if f_des != "ALL": df_visual = df_visual[df_visual["DESTINO"] == f_des]
    if f_est != "ALL": df_visual = df_visual[df_visual["ESTATUS_CALCULADO"] == f_est]

    st.dataframe(
        df_visual,
        use_container_width=True,
        hide_index=True,
        height=500
    )


















































































































































































































































































































































