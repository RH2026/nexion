import streamlit as st
import pandas as pd
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# 2. GESTIÓN DE TEMA REFINADA
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

if st.session_state.tema == "oscuro":
    bg_color, card_bg, text_main, text_sub, border_color = "#05070A", "#0D1117", "#F0F6FC", "#8B949E", "#1B1F24"
    table_theme = "dark"
else:
    # MODO PEARL (Fondo Aperlado + Tabla Blanca Zara)
    bg_color = "#F5F7FA"      
    card_bg = "#FFFFFF"       
    text_main = "#1A1C1E"     
    text_sub = "#656D76"      
    border_color = "#D8DEE4"
    table_theme = "light"

# 3. CSS MAESTRO: FUENTES Y TABLAS
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

        header, footer, #MainMenu, div[data-testid="stDecoration"] {{visibility: hidden;}}
        
        /* Aplicación de Fuente Global */
        .stApp, button, input, select, textarea, div, span {{
            font-family: 'Inter', sans-serif !important;
        }}

        .stApp {{
            background-color: {bg_color} !important;
            color: {text_main} !important;
        }}

        /* BOTONES Y SELECTORES (Look Zara) */
        div.stButton > button, div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            background-color: {card_bg} !important;
            color: {text_main} !important;
            border: 1px solid {border_color} !important;
            border-radius: 2px !important; 
            font-size: 11px !important;
            letter-spacing: 2px !important;
            text-transform: uppercase;
        }}

        /* --- FORZADO DE TABLA BLANCA / GRIS --- */
        /* Esto afecta al contenedor del Dataframe en Modo Claro */
        div[data-testid="stDataFrame"] {{
            background-color: {card_bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 4px;
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
        # Limpieza de fechas para evitar visualización desordenada
        for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime('%d/%m/%Y')
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

# 6. RENDERIZADO DE TABLA
if not df.empty:
    f1, f2, f3, f4 = st.columns(4)
    with f1: st.selectbox("Client ID", ["ALL"])
    with f2: st.selectbox("Carrier", ["ALL"])
    with f3: st.selectbox("Destination", ["ALL"])
    with f4: st.selectbox("Status", ["ALL"])

    # Estilo final de la tabla:
    # Usamos container_width para que se adapte al ancho de Zara
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=500
    )


















































































































































































































































































































































