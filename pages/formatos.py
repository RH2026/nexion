¡Hecho, cielo! Vamos a poner la aplicación en modo "Wide" (ancho completo) para que esa matriz de logística se vea increíble y no tengas que estar desplazándote de izquierda a derecha.

En Streamlit, esto se hace con layout="wide". Aquí tienes el código integrado y optimizado para que sea una herramienta de trabajo real:

Código Maestro: Nexion en Pantalla Completa
Python
import pandas as pd
import streamlit as st
from github import Github
import io

# 1. CONFIGURACIÓN DE PÁGINA (ESTO VA AL PRINCIPIO SIEMPRE)
st.set_page_config(page_title="Nexion Logística", layout="wide")

# --- PARÁMETROS DE ACCESO ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
BD_FILE = "enviosbd.csv"

# Función para leer de GitHub
def cargar_datos():
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    content = repo.get_contents(BD_FILE)
    df = pd.read_csv(content.download_url)
    # Aseguramos que DocNum sea texto para evitar problemas de formato
    df['DocNum'] = df['DocNum'].astype(str)
    return df, content.sha

# Función para guardar en GitHub
def guardar_datos(df_save, sha_save):
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    csv_buffer = io.StringIO()
    df_save.to_csv(csv_buffer, index=False)
    repo.update_file(
        path=BD_FILE,
        message="Nexion: Actualización de matriz de envíos",
        content=csv_buffer.getvalue(),
        sha=sha_save
    )

# --- CUERPO DE LA APP ---
st.title("📦 Panel de Control de Envíos - JYPESA")
st.markdown("---")

# Cargar datos en el estado de la sesión
if 'df_nexion' not in st.session_state:
    df, sha = cargar_datos()
    st.session_state.df_nexion = df
    st.session_state.sha_nexion = sha

# DISEÑO DE COLUMNAS PARA BOTONES
col1, col2 = st.columns([1, 5])

with col1:
    if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
        guardar_datos(st.session_state.df_nexion, st.session_state.sha_nexion)
        st.success("¡Datos guardados!")
        # Recargamos para obtener el nuevo SHA
        df_new, sha_new = cargar_datos()
        st.session_state.df_nexion = df_new
        st.session_state.sha_nexion = sha_new

with col2:
    st.info("💡 Edita las columnas de la derecha y presiona 'Guardar'. Los datos de SAP están protegidos.")

# --- RENDERIZADO DE LA MATRIZ ---
# Definimos qué columnas NO se pueden editar (las de SAP)
cols_bloqueadas = [col for col in st.session_state.df_nexion.columns if col not in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']]

df_editado = st.data_editor(
    st.session_state.df_nexion,
    column_config={
        "DocNum": st.column_config.TextColumn("Pedido", disabled=True),
        "CardName": st.column_config.TextColumn("Cliente", disabled=True),
        # Configuramos tus 4 columnas editables
        "FECHA DE ENVIO": st.column_config.DateColumn("Fecha Envío", format="YYYY-MM-DD"),
        "FLETERA": st.column_config.SelectboxColumn("Fletera", options=["PAQUETEXPRESS", "TRESGUERRAS", "CASTORES", "ESTAFETA", "RECOLECCION"]),
        "SURTIDOR": st.column_config.TextColumn("Surtidor"),
        "INCIDENCIA": st.column_config.TextColumn("Notas / Incidencia")
    },
    hide_index=True,
    use_container_width=True, # Esto hace que use todo el ancho "Wide"
    num_rows="fixed" # No permite borrar filas accidentalmente
)

# Actualizamos el estado interno cuando el usuario escribe
st.session_state.df_nexion = df_editado




























































































































































