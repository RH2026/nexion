import streamlit as st
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Logistics Core", layout="wide", initial_sidebar_state="collapsed")

# 2. PALETA DE COLORES SOFISTICADA
# Fondo: Negro Azulado Profundo (#0A0C10)
# Tarjetas: Gris Antracita (#161B22)
# Acento: Plata / Gris Frío (#8B949E)
# Texto: Blanco Humo (#F0F6FC)

st.markdown(f"""
    <style>
        /* Fondo Principal Estilo Dark Premium */
        .stApp {{
            background-color: #0A0C10 !important;
            color: #F0F6FC !important;
            font-family: 'Inter', -apple-system, sans-serif;
        }}

        /* Ocultar elementos de Streamlit */
        header, footer, #MainMenu, div[data-testid="stDecoration"] {{visibility: hidden;}}

        /* --- NAVEGACIÓN SUPERIOR MINIMALISTA --- */
        .nav-block {{
            display: flex;
            justify-content: center;
            gap: 20px;
            padding: 20px 0;
            border-bottom: 1px solid #21262D;
        }}

        /* BOTONES GRISES FORMALES */
        div.stButton > button {{
            background-color: #161B22 !important;
            color: #C9D1D9 !important;
            border: 1px solid #30363D !important;
            border-radius: 6px !important;
            padding: 0.5rem 1.5rem !important;
            font-weight: 500 !important;
            font-size: 13px !important;
            letter-spacing: 0.5px;
            transition: all 0.2s ease;
        }}

        div.stButton > button:hover {{
            background-color: #21262D !important;
            border-color: #8B949E !important;
            color: #FFFFFF !important;
        }}

        /* Inputs de búsqueda serios */
        .stTextInput input {{
            background-color: #0D1117 !important;
            color: #F0F6FC !important;
            border: 1px solid #30363D !important;
            border-radius: 4px !important;
            height: 45px !important;
        }}

        .stTextInput input:focus {{
            border-color: #58A6FF !important; /* Azul sutil para foco */
            box-shadow: none !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 3. HEADER Y MENÚ
# Logo minimalista y serio
c_logo, c_nav = st.columns([1, 4])

with c_logo:
    st.markdown("<h2 style='color: #F0F6FC; font-weight: 200; letter-spacing: 3px; margin: 0;'>NEXION</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8B949E; font-size: 10px; margin-top: -5px;'>CORE LOGISTICS UNIT</p>", unsafe_allow_html=True)

with c_nav:
    # Usamos columnas internas para el menú horizontal
    m1, m2, m3, m4, m5 = st.columns(5)
    if "pagina" not in st.session_state: st.session_state.pagina = "RASTREO"
    
    with m1: 
        if st.button("RASTREO", use_container_width=True): st.session_state.pagina = "RASTREO"
    with m2: 
        if st.button("INTELIGENCIA", use_container_width=True): st.session_state.pagina = "KPIs"
    with m3: 
        if st.button("REPORTES", use_container_width=True): st.session_state.pagina = "REPORTES"
    with m4:
        if st.button("ESTATUS", use_container_width=True): st.session_state.pagina = "ESTATUS"
    with m5:
        # Botón de reset o salida
        if st.button("✕", use_container_width=True): st.session_state.clear()

st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

# 4. BUSCADOR CENTRAL SOFISTICADO
_, col_search, _ = st.columns([1, 1.5, 1])

with col_search:
    st.markdown("<h3 style='font-weight: 300; color: #8B949E; text-align: center; font-size: 18px;'>CONSULTA DE OPERACIONES</h3>", unsafe_allow_html=True)
    guia = st.text_input("", placeholder="Referencia de envío o número de guía...", label_visibility="collapsed")
    
    # Botón de acción con estilo formal
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #F0F6FC !important;
            color: #0A0C10 !important;
            border: none !important;
            font-weight: 800 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("EJECUTAR BÚSQUEDA", type="primary", use_container_width=True):
        with st.spinner("Localizando unidad..."):
            time.sleep(1)
            st.session_state.busqueda = guia

# 5. LÍNEA DE SEPARACIÓN ELEGANTE
st.markdown("<hr style='border: 0; border-top: 1px solid #21262D; margin: 40px 0;'>", unsafe_allow_html=True)










































































































































































































































































































































