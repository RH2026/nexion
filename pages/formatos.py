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

def cargar_csv_guerrero(file_path):
    try:
        repo = obtener_repo()
        content = repo.get_contents(file_path, ref="main")
        data = base64.b64decode(content.content).decode('utf-8-sig')
        
        # Leemos ignorando líneas en blanco y errores de formato
        df = pd.read_csv(
            io.StringIO(data), 
            skip_blank_lines=True, 
            on_bad_lines='skip',
            engine='python'
        )
        
        # Limpiamos encabezados
        df.columns = df.columns.str.strip()

        if 'DocNum' in df.columns:
            # LIMPIEZA PROFUNDA DE DocNum
            df = df.dropna(subset=['DocNum'])
            # Convertimos a número, quitamos decimales y pasamos a texto limpio
            df['DocNum'] = pd.to_numeric(df['DocNum'], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
            df = df[df['DocNum'] != "0"]
        
        return df, content.sha
    except Exception as e:
        st.error(f"Error en {file_path}: {e}")
        return pd.DataFrame(), None

# --- LÓGICA DE SINCRONIZACIÓN ---
def sincronizar_ahora():
    with st.spinner("Comparando pedidos de SAP..."):
        df_sap, _ = cargar_csv_guerrero(SAP_FILE)
        df_bd, sha_bd = cargar_csv_guerrero(BD_FILE)
        
        if df_sap.empty:
            st.error("No hay datos válidos en sapdata.csv para sincronizar.")
            return

        # Comparamos DocNum contra DocNum
        existentes = set(df_bd['DocNum'].unique())
        nuevos = df_sap[~df_sap['DocNum'].isin(existentes)].copy()
        
        if not nuevos.empty:
            # Añadimos las 4 columnas de edición vacías
            for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
                if col not in nuevos.columns:
                    nuevos[col] = ""
            
            # Pegamos lo nuevo al final de lo viejo
            df_final = pd.concat([df_bd, nuevos], ignore_index=True)
            
            # Subimos a GitHub
            repo = obtener_repo()
            buffer = io.StringIO()
            df_final.to_csv(buffer, index=False)
            repo.update_file(path=BD_FILE, message="Sync SAP", content=buffer.getvalue(), sha=sha_bd)
            st.success(f"¡A HUEVO! Se agregaron {len(nuevos)} pedidos nuevos.")
            time.sleep(1)
            st.rerun()
        else:
            st.info("No hay pedidos nuevos. Todo está al día en Nexion.")

# --- SESSION STATE ---
if 'df_nexion' not in st.session_state:
    df_i, sha_i = cargar_csv_guerrero(BD_FILE)
    st.session_state.df_nexion = df_i
    st.session_state.sha_nexion = sha_i

# --- INTERFAZ ---
st.title("📦 Panel de Control Nexion")

c1, c2 = st.columns([1, 1])
with c1:
    if st.button("🔄 SINCRONIZAR SAP", use_container_width=True, type="primary"):
        sincronizar_ahora()

with c2:
    if st.button("💾 GUARDAR CAMBIOS", use_container_width=True):
        if "editor_nexion" in st.session_state:
            # Procesamos las ediciones antes de guardar
            edits = st.session_state.editor_nexion["edited_rows"]
            for idx, changes in edits.items():
                for k, v in changes.items():
                    st.session_state.df_nexion.at[idx, k] = v
        
        repo = obtener_repo()
        buffer = io.StringIO()
        st.session_state.df_nexion.to_csv(buffer, index=False)
        repo.update_file(path=BD_FILE, message="Update", content=buffer.getvalue(), sha=st.session_state.sha_nexion)
        st.success("Guardado en GitHub.")
        time.sleep(1)
        st.rerun()

st.divider()

# --- TABLA EDITABLE ---
st.data_editor(
    st.session_state.df_nexion,
    column_config={
        "DocNum": st.column_config.TextColumn("Pedido", disabled=True),
        "CardName": st.column_config.TextColumn("Cliente", disabled=True),
        "FLETERA": st.column_config.SelectboxColumn("Fletera", options=["", "DHL", "ESTAFETA", "PAQUETEXPRESS", "TRESGUERRAS", "PROPIA", "CASTORES"]),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_nexion"
)


























































































































































