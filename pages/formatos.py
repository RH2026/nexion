import pandas as pd
import streamlit as st
from github import Github
import io
import base64

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Nexion Logística", layout="wide")

TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
SAP_FILE = "sapdata.csv"   # La que acabas de subir con datos nuevos
BD_FILE = "enviosbd.csv"    # Tu matriz de trabajo

# --- FUNCIONES DE BAJO NIVEL ---
def obtener_repo():
    g = Github(TOKEN)
    return g.get_repo(REPO_NAME)

def cargar_csv(file_path):
    repo = obtener_repo()
    content = repo.get_contents(file_path)
    data = base64.b64decode(content.content).decode('utf-8')
    df = pd.read_csv(io.StringIO(data))
    # Limpieza de DocNum para evitar el .0
    if 'DocNum' in df.columns:
        df = df.dropna(subset=['DocNum'])
        df['DocNum'] = pd.to_numeric(df['DocNum'], errors='coerce').fillna(0).astype(int).astype(str)
    return df, content.sha

# --- FUNCIÓN DE SINCRONIZACIÓN (LA QUE TE FALTA) ---
def sincronizar_matrices():
    df_sap, _ = cargar_csv(SAP_FILE)
    df_bd, sha_bd = cargar_csv(BD_FILE)
    
    # Encontrar qué DocNum están en SAP pero NO en nuestra BD
    nuevos = df_sap[~df_sap['DocNum'].isin(df_bd['DocNum'])].copy()
    
    if not nuevos.empty:
        for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
            nuevos[col] = ""
        
        # Unir sin duplicar
        df_final = pd.concat([df_bd, nuevos], ignore_index=True)
        
        # Guardar el resultado mezclado
        repo = obtener_repo()
        csv_buffer = io.StringIO()
        df_final.to_csv(csv_buffer, index=False)
        repo.update_file(path=BD_FILE, message="Sync SAP", content=csv_buffer.getvalue(), sha=sha_bd)
        return f"✅ Se agregaron {len(nuevos)} filas nuevas."
    return "0 filas nuevas encontradas."

# --- INICIO DE APP ---
if 'df_nexion' not in st.session_state:
    df_init, sha_init = cargar_csv(BD_FILE)
    st.session_state.df_nexion = df_init
    st.session_state.sha_nexion = sha_init

st.title("📦 Nexion: Gestión e Inteligencia de Envíos")

# BOTONES DE CONTROL
col1, col2, col3 = st.columns([1, 1, 3])

with col1:
    if st.button("🔄 SINCRONIZAR SAP", use_container_width=True):
        with st.spinner("Buscando nuevos pedidos..."):
            msj = sincronizar_matrices()
            st.toast(msj)
            # Recargar todo
            df_up, sha_up = cargar_csv(BD_FILE)
            st.session_state.df_nexion = df_up
            st.session_state.sha_nexion = sha_up
            st.rerun()

with col2:
    if st.button("💾 GUARDAR EDICIÓN", type="primary", use_container_width=True):
        # Aplicar cambios del editor al state
        if "editor_nexion" in st.session_state:
            edits = st.session_state.editor_nexion["edited_rows"]
            for idx, changes in edits.items():
                for k, v in changes.items():
                    st.session_state.df_nexion.at[idx, k] = v
        
        # Guardar en GitHub
        repo = obtener_repo()
        csv_buffer = io.StringIO()
        st.session_state.df_nexion.to_csv(csv_buffer, index=False)
        repo.update_file(path=BD_FILE, message="Update", content=csv_buffer.getvalue(), sha=st.session_state.sha_nexion)
        st.success("Guardado.")
        st.rerun()

# --- TABLA ---
st.data_editor(
    st.session_state.df_nexion,
    column_config={
        "DocNum": st.column_config.TextColumn("Pedido", disabled=True),
        "CardName": st.column_config.TextColumn("Cliente", disabled=True),
        "FLETERA": st.column_config.SelectboxColumn("Fletera", options=["", "PAQUETEXPRESS", "TRESGUERRAS", "CASTORES", "ESTAFETA", "RECOLECCION"]),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_nexion"
)




























































































































































