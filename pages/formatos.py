import pandas as pd
import streamlit as st
from github import Github
import io
import base64

# 1. CONFIGURACIÓN DE PÁGINA (ESTO SIEMPRE VA PRIMERO)
st.set_page_config(page_title="Nexion Logística", layout="wide")

# --- PARÁMETROS DE ACCESO (Asegúrate que coincidan en tus Secrets) ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
SAP_FILE = "sapdata.csv"   # El archivo que subes de SAP
BD_FILE = "enviosbd.csv"    # Tu base de datos de trabajo

# --- FUNCIONES DE CONEXIÓN ---
def obtener_repo():
    g = Github(TOKEN)
    return g.get_repo(REPO_NAME)

def cargar_csv(file_path):
    try:
        repo = obtener_repo()
        content = repo.get_contents(file_path)
        # Decodificar contenido crudo para evitar caché y errores de archivo vacío
        data = base64.b64decode(content.content).decode('utf-8')
        
        if not data.strip():
            return pd.DataFrame(), None
            
        df = pd.read_csv(io.StringIO(data))
        
        # LIMPIEZA DE DOCNUM (Quitar decimales .0)
        if 'DocNum' in df.columns:
            df = df.dropna(subset=['DocNum'])
            # Forzamos conversión a entero para quitar el .0 y luego a string
            df['DocNum'] = pd.to_numeric(df['DocNum'], errors='coerce').fillna(0).astype(int).astype(str)
            df = df[df['DocNum'] != "0"]
        
        # Asegurar que existan las columnas de edición
        cols_edit = ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']
        for col in cols_edit:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN', 'NaT'], '')
            
        return df, content.sha
    except Exception as e:
        st.error(f"Error cargando {file_path}: {e}")
        return pd.DataFrame(), None

# --- LÓGICA DE SINCRONIZACIÓN ---
def sincronizar_matrices():
    df_sap, _ = cargar_csv(SAP_FILE)
    df_bd, sha_bd = cargar_csv(BD_FILE)
    
    if df_sap.empty:
        return "⚠️ El archivo SAP parece estar vacío o no se encontró."
    
    # BUSCARV: Encontrar pedidos en SAP que no están en nuestra base actual
    nuevos = df_sap[~df_sap['DocNum'].isin(df_bd['DocNum'])].copy()
    
    if not nuevos.empty:
        # Inicializar columnas de trabajo para los nuevos
        for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
            nuevos[col] = ""
        
        # Unir: Lo que ya teníamos + lo nuevo de SAP
        df_final = pd.concat([df_bd, nuevos], ignore_index=True)
        
        # Guardar en GitHub
        repo = obtener_repo()
        csv_buffer = io.StringIO()
        df_final.to_csv(csv_buffer, index=False)
        repo.update_file(path=BD_FILE, message="Sync SAP Data", content=csv_buffer.getvalue(), sha=sha_bd)
        return f"✅ ¡Éxito! Se agregaron {len(nuevos)} pedidos nuevos."
    
    return "ℹ️ No hay pedidos nuevos en SAP."

# --- MANEJO DE ESTADO (SESSION STATE) ---
if 'df_nexion' not in st.session_state:
    df_init, sha_init = cargar_csv(BD_FILE)
    st.session_state.df_nexion = df_init
    st.session_state.sha_nexion = sha_init

# --- INTERFAZ DE USUARIO ---
st.title("📦 Nexion Logística - JYPESA")
st.markdown(f"**Archivo activo:** `{BD_FILE}`")

# Fila de botones
col1, col2, col3 = st.columns([1, 1, 3])

with col1:
    if st.button("🔄 SINCRONIZAR SAP", use_container_width=True):
        with st.spinner("Comparando matrices..."):
            resultado = sincronizar_matrices()
            st.toast(resultado)
            # Recargar datos tras sincronizar
            df_up, sha_up = cargar_csv(BD_FILE)
            st.session_state.df_nexion = df_up
            st.session_state.sha_nexion = sha_up
            st.rerun()

with col2:
    if st.button("💾 GUARDAR EDICIÓN", type="primary", use_container_width=True):
        with st.spinner("Guardando cambios..."):
            # Jalar cambios del editor
            if "editor_nexion" in st.session_state:
                edits = st.session_state.editor_nexion["edited_rows"]
                for idx, changes in edits.items():
                    for k, v in changes.items():
                        st.session_state.df_nexion.at[idx, k] = v
            
            # Guardar la matriz completa
            repo = obtener_repo()
            csv_buffer = io.StringIO()
            st.session_state.df_nexion.to_csv(csv_buffer, index=False)
            repo.update_file(path=BD_FILE, message="Manual Update", content=csv_buffer.getvalue(), sha=st.session_state.sha_nexion)
            
            # Refrescar SHA y datos
            df_up, sha_up = cargar_csv(BD_FILE)
            st.session_state.df_nexion = df_up
            st.session_state.sha_nexion = sha_up
            st.success("¡Guardado!")
            st.rerun()

st.divider()

# --- EL EDITOR (ANCHO COMPLETO) ---
st.data_editor(
    st.session_state.df_nexion,
    column_config={
        "DocNum": st.column_config.TextColumn("Pedido", disabled=True),
        "CardName": st.column_config.TextColumn("Cliente", disabled=True),
        "FECHA DE ENVIO": st.column_config.TextColumn("Fecha Envío (AAAA-MM-DD)"),
        "FLETERA": st.column_config.SelectboxColumn(
            "Fletera", 
            options=["", "PAQUETEXPRESS", "TRESGUERRAS", "CASTORES", "ESTAFETA", "RECOLECCION", "PROPIA"]
        ),
        "SURTIDOR": st.column_config.TextColumn("Surtidor"),
        "INCIDENCIA": st.column_config.TextColumn("Notas / Incidencias")
    },
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    key="editor_nexion"
)




























































































































































