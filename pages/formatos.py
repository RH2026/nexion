import pandas as pd
import streamlit as st
from github import Github
import io

# --- CONFIGURACIÓN ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
BD_FILE = "enviosbd.csv"

def cargar_base_datos():
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    content = repo.get_contents(BD_FILE)
    df = pd.read_csv(content.download_url)
    return df, content.sha

def guardar_cambios_github(df_editado, sha_original):
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    csv_buffer = io.StringIO()
    df_editado.to_csv(csv_buffer, index=False)
    
    repo.update_file(
        path=BD_FILE,
        message="Nexion: Edición manual de envíos",
        content=csv_buffer.getvalue(),
        sha=sha_original
    )
    st.success("¡Cambios guardados en GitHub con éxito!")

# --- INTERFAZ DE NEXION ---
st.title("📦 Gestión de Envíos - Nexion")

# 1. Cargar los datos
if 'df_trabajo' not in st.session_state:
    df, sha = cargar_base_datos()
    st.session_state.df_trabajo = df
    st.session_state.sha_actual = sha

# 2. RENDERIZAR LA MATRIZ EDITABLE
st.subheader("Panel de Edición")
# Aquí bloqueamos las columnas de SAP y solo dejamos editar las 4 tuyas
df_editado = st.data_editor(
    st.session_state.df_trabajo,
    column_config={
        "DocNum": st.column_config.Column(disabled=True),
        "CardName": st.column_config.Column(disabled=True),
        "FECHA DE ENVIO": st.column_config.DateColumn("Fecha de Envío"),
        "FLETERA": st.column_config.SelectboxColumn("Fletera", options=["DHL", "FedEx", "Propia", "Otro"]),
        "SURTIDOR": st.column_config.TextColumn("Surtidor"),
        "INCIDENCIA": st.column_config.TextColumn("Incidencia")
    },
    hide_index=True,
    use_container_width=True
)

# 3. BOTÓN PARA GUARDAR
if st.button("💾 Guardar Cambios en GitHub"):
    guardar_cambios_github(df_editado, st.session_state.sha_actual)
    # Actualizamos el estado para la siguiente edición
    st.session_state.df_trabajo = df_editado




























































































































































