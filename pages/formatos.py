import pandas as pd
import streamlit as st
from github import Github
import io
import base64
import time

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Nexion Logística", layout="wide")

TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
SAP_FILE = "sapdata.csv"
BD_FILE = "enviosbd.csv"

def obtener_repo():
    return Github(TOKEN).get_repo(REPO_NAME)

def cargar_csv_directo(file_path):
    try:
        repo = obtener_repo()
        content = repo.get_contents(file_path, ref="main")
        # Decodificamos con utf-8 y quitamos espacios en blanco
        data = base64.b64decode(content.content).decode('utf-8-sig').strip()
        
        if not data:
            return pd.DataFrame(), None
            
        df = pd.read_csv(io.StringIO(data))
        df.columns = df.columns.str.strip() # Limpiar encabezados

        if 'DocNum' in df.columns:
            df = df.dropna(subset=['DocNum'])
            # Convertimos a float, luego a int (para quitar el .0) y luego a string
            df['DocNum'] = pd.to_numeric(df['DocNum'], errors='coerce').fillna(0).astype(int).astype(str)
            df = df[df['DocNum'] != "0"]
        
        return df, content.sha
    except Exception as e:
        st.error(f"Error cargando {file_path}: {e}")
        return pd.DataFrame(), None

# --- LÓGICA DE SINCRONIZACIÓN ---
def sincronizar_ahora():
    df_sap, _ = cargar_csv_directo(SAP_FILE)
    df_bd, sha_bd = cargar_csv_directo(BD_FILE)
    
    if df_sap.empty:
        st.error("El archivo sapdata.csv está vacío o no se leyó bien.")
        return

    # Usamos set para comparar rápido
    existentes = set(df_bd['DocNum'].unique())
    nuevos = df_sap[~df_sap['DocNum'].isin(existentes)].copy()
    
    if not nuevos.empty:
        # Agregar columnas de edición
        for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
            if col not in nuevos.columns:
                nuevos[col] = ""
        
        df_final = pd.concat([df_bd, nuevos], ignore_index=True)
        
        # Guardar
        repo = obtener_repo()
        buffer = io.StringIO()
        df_final.to_csv(buffer, index=False)
        repo.update_file(path=BD_FILE, message="Sync SAP", content=buffer.getvalue(), sha=sha_bd)
        st.success(f"¡Se agregaron {len(nuevos)} pedidos nuevos!")
        time.sleep(1)
        st.rerun()
    else:
        st.info("No hay pedidos nuevos que agregar.")

# --- MANEJO DE DATOS ---
if 'df_nexion' not in st.session_state:
    df_i, sha_i = cargar_csv_directo(BD_FILE)
    st.session_state.df_nexion = df_i
    st.session_state.sha_nexion = sha_i

# --- INTERFAZ ---
st.title("📦 Panel de Control Nexion")

col_sync, col_save = st.columns([1, 1])

with col_sync:
    if st.button("🔄 SINCRONIZAR SAP", use_container_width=True, type="primary"):
        sincronizar_ahora()

with col_save:
    if st.button("💾 GUARDAR EDICIÓN", use_container_width=True):
        if "editor_nexion" in st.session_state:
            edits = st.session_state.editor_nexion["edited_rows"]
            for idx, changes in edits.items():
                for k, v in changes.items():
                    st.session_state.df_nexion.at[idx, k] = v
        
        repo = obtener_repo()
        buffer = io.StringIO()
        st.session_state.df_nexion.to_csv(buffer, index=False)
        repo.update_file(path=BD_FILE, message="Update", content=buffer.getvalue(), sha=st.session_state.sha_nexion)
        st.success("Cambios guardados.")
        time.sleep(1)
        st.rerun()

# --- TABLA ---
st.data_editor(
    st.session_state.df_nexion,
    column_config={
        "DocNum": st.column_config.TextColumn("Pedido", disabled=True),
        "FLETERA": st.column_config.SelectboxColumn("Fletera", options=["", "PAQUETEXPRESS", "TRESGUERRAS", "CASTORES", "ESTAFETA", "RECOLECCION", "PROPIA"]),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_nexion"
)


























































































































































