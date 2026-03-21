import pandas as pd
import streamlit as st
from github import Github
import io
import base64
import time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Nexion Logística", layout="wide")

# --- PARÁMETROS DE ACCESO ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
SAP_FILE = "sapdata.csv"   
BD_FILE = "enviosbd.csv"    

def obtener_repo():
    g = Github(TOKEN)
    return g.get_repo(REPO_NAME)

def cargar_csv(file_path):
    try:
        repo = obtener_repo()
        # El parámetro query_or_ref con un timestamp ayuda a saltar el caché en algunas APIs
        content = repo.get_contents(file_path, ref="main")
        
        # LOG DE DIAGNÓSTICO
        st.sidebar.write(f"📁 {file_path}: {content.size} bytes detectados.")
        
        if content.size == 0:
            return pd.DataFrame(), None

        data = base64.b64decode(content.content).decode('utf-8')
        df = pd.read_csv(io.StringIO(data))
        
        # --- LIMPIEZA AGRESIVA DE COLUMNAS ---
        # Quitamos espacios en blanco de los nombres de las columnas (ej: " DocNum " -> "DocNum")
        df.columns = df.columns.str.strip()
        
        # --- LIMPIEZA DE DATOS ---
        if 'DocNum' in df.columns:
            df = df.dropna(subset=['DocNum'])
            # Convertimos a string, quitamos el .0 y espacios locos
            df['DocNum'] = pd.to_numeric(df['DocNum'], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
            df = df[df['DocNum'] != "0"]
        
        # Asegurar columnas de edición
        for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN', 'NaT'], '')
            
        return df, content.sha
    except Exception as e:
        st.error(f"Error en {file_path}: {str(e)}")
        return pd.DataFrame(), None

def sincronizar_matrices():
    # Cargamos SAP con limpieza de columnas
    df_sap, _ = cargar_csv(SAP_FILE)
    df_bd, sha_bd = cargar_csv(BD_FILE)
    
    if df_sap.empty:
        return "❌ Error: El archivo SAP no tiene datos o no se encontró."

    # Usamos set para comparar rápido y sin errores de formato
    pedidos_en_bd = set(df_bd['DocNum'].unique())
    
    # Filtramos los que NO están en la base de datos
    nuevos = df_sap[~df_sap['DocNum'].isin(pedidos_en_bd)].copy()
    
    if not nuevos.empty:
        # Solo pegamos los pedidos nuevos al final
        df_final = pd.concat([df_bd, nuevos], ignore_index=True)
        
        # Guardar en GitHub
        repo = obtener_repo()
        csv_buffer = io.StringIO()
        df_final.to_csv(csv_buffer, index=False)
        repo.update_file(path=BD_FILE, message="Sync SAP", content=csv_buffer.getvalue(), sha=sha_bd)
        return f"✅ ¡A HUEVO! Se agregaron {len(nuevos)} pedidos nuevos."
    
    return "ℹ️ No hay nada nuevo en SAP que no esté ya en la base."

# --- SESSION STATE ---
if 'df_nexion' not in st.session_state:
    df_i, sha_i = cargar_csv(BD_FILE)
    st.session_state.df_nexion = df_i
    st.session_state.sha_nexion = sha_i

# --- INTERFAZ ---
st.title("📦 Nexion Logística - JYPESA")

col1, col2, col3 = st.columns([1, 1, 3])

with col1:
    if st.button("🔄 SINCRONIZAR SAP", use_container_width=True, type="primary"):
        with st.spinner("Cruzando datos..."):
            res = sincronizar_matrices()
            st.success(res)
            time.sleep(1) # Esperamos un segundo para que GitHub procese
            df_up, sha_up = cargar_csv(BD_FILE)
            st.session_state.df_nexion = df_up
            st.session_state.sha_nexion = sha_up
            st.rerun()

with col2:
    if st.button("💾 GUARDAR EDICIÓN", use_container_width=True):
        if "editor_nexion" in st.session_state:
            edits = st.session_state.editor_nexion["edited_rows"]
            for idx, changes in edits.items():
                for k, v in changes.items():
                    st.session_state.df_nexion.at[idx, k] = v
        
        repo = obtener_repo()
        csv_buffer = io.StringIO()
        st.session_state.df_nexion.to_csv(csv_buffer, index=False)
        repo.update_file(path=BD_FILE, message="Manual Update", content=csv_buffer.getvalue(), sha=st.session_state.sha_nexion)
        st.success("Guardado.")
        time.sleep(1)
        df_up, sha_up = cargar_csv(BD_FILE)
        st.session_state.df_nexion = df_up
        st.session_state.sha_nexion = sha_up
        st.rerun()

st.divider()

# --- EDITOR ---
st.data_editor(
    st.session_state.df_nexion,
    column_config={
        "DocNum": st.column_config.TextColumn("Pedido", disabled=True),
        "CardName": st.column_config.TextColumn("Cliente", disabled=True),
        "FLETERA": st.column_config.SelectboxColumn("Fletera", options=["", "DHL", "FEDEX", "ESTAFETA", "RECOLECCION", "PROPIA"]),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_nexion"
)



























































































































































