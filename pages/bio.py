import streamlit as st
import streamlit.components.v1 as components
import base64

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="HERNANPHY | BIO", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. LIMPIEZA DE INTERFAZ
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        header { visibility: hidden; height: 0; }
        footer { visibility: hidden; }
        .block-container { padding: 0rem; }
        [data-testid="stAppViewContainer"] { background-color: #0b1114; overflow: hidden; }
        html, body { overflow: hidden; cursor: none; }
    </style>
""", unsafe_allow_html=True)

# 3. TU HTML (Pégalo aquí adentro)
mi_html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>HERNANPHY</title>
    </head>
<body>
    </body>
</html>
"""

# 4. TRUCO ANTIBUGS: Convertir a Base64 para evitar el SyntaxError
b64_html = base64.b64encode(mi_html.encode('utf-8')).decode('utf-8')
src_data = f"data:text/html;base64,{b64_html}"

# 5. RENDERIZADO INMERSIVO
components.iframe(src=src_data, height=1200, scrolling=False)
