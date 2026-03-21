import pandas as pd
import streamlit as st
from github import Github
import io

# 1. CONFIGURACIÓN DE PÁGINA (DEBE SER LO PRIMERO)
st.set_page_config(page_title="Nexion Logística", layout="wide")

# --- PARÁMETROS DE ACCESO ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
BD_FILE = "enviosbd.csv"

# --- FUNCIONES ---
def cargar_datos():
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        content = repo.get_contents(BD_FILE)
        df = pd.read_csv(content.download_url)
        
        # Limpieza de datos para que el editor no chille
        for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN', 'NaT'], '')
        
        if 'DocNum' in df.columns:
            df['DocNum'] = df['DocNum'].astype(str)
            
        return df, content.sha
    except Exception as e:
        st.error(f"Error al cargar: {e}")
        return pd.DataFrame(), None

def guardar_datos(df_save, sha_save):
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        csv_buffer = io.StringIO()
        df_save.to_csv(csv_buffer, index=False)
        repo.update_file(
            path=BD_FILE,
            message="Nexion: Actualización manual",
            content=csv_buffer.getvalue(),
            sha=sha_save
        )
        st.success("¡Guardado correctamente en GitHub!")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- LÓGICA DE DATOS ---
if 'df_nexion' not in st.session_state:
    df_inicial, sha_inicial = cargar_datos()
    st.session_state.df_nexion = df_inicial
    st.session_state.sha_nexion = sha_inicial

# --- INTERFAZ ---
st.title("📦 Panel de Control de Envíos - JYPESA")

# Botones superiores
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
        guardar_datos(st.session_state.df_nexion, st.session_state.sha_nexion)
        # Recargamos para actualizar el SHA y evitar errores de colisión
        df_update, sha_update = cargar_datos()
        st.session_state.df_nexion = df_update
        st.session_state.sha_nexion = sha_update
        st.rerun()

# --- EL EDITOR (UNA SOLA VEZ Y AL FINAL) ---
st.subheader("Matriz Editable")

# Creamos una copia para el editor
df_para_editar = st.session_state.df_nexion.copy()

df_editado = st.data_editor(
    df_para_editar,
    column_config={
        "DocNum": st.column_config.TextColumn("Pedido", disabled=True),
        "CardName": st.column_config.TextColumn("Cliente", disabled=True),
        "FECHA DE ENVIO": st.column_config.TextColumn("Fecha (AAAA-MM-DD)"), # Texto para evitar error de tipos
        "FLETERA": st.column_config.SelectboxColumn(
            "Fletera", 
            options=["", "PAQUETEXPRESS", "TRESGUERRAS", "CASTORES", "ESTAFETA", "RECOLECCION"]
        ),
        "SURTIDOR": st.column_config.TextColumn("Surtidor"),
        "INCIDENCIA": st.column_config.TextColumn("Notas / Incidencia")
    },
    hide_index=True,
    use_container_width=True,
    num_rows="fixed"
)

# Guardamos lo que el usuario escribe en el state
st.session_state.df_nexion = df_editado




























































































































































