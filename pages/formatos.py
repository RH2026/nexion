import pandas as pd
import streamlit as st
from github import Github
import io
import base64

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Nexion Logística", layout="wide")

# --- PARÁMETROS DE ACCESO ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
BD_FILE = "enviosbd.csv"

def cargar_datos():
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        content = repo.get_contents(BD_FILE)
        data = base64.b64decode(content.content).decode('utf-8')
        df = pd.read_csv(io.StringIO(data))
        
        if 'DocNum' in df.columns:
            df = df.dropna(subset=['DocNum'])
            df['DocNum'] = pd.to_numeric(df['DocNum'], errors='coerce').fillna(0).astype(int).astype(str)
            df = df[df['DocNum'] != "0"]
        
        cols_edit = ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']
        for col in cols_edit:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN', 'NaT'], '')
            
        return df, content.sha
    except Exception as e:
        st.error(f"Error al cargar: {e}")
        return pd.DataFrame(), None

def guardar_datos(df_save, sha_save):
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        if 'DocNum' in df_save.columns:
            df_save = df_save.dropna(subset=['DocNum'])
            df_save = df_save[df_save['DocNum'].astype(str).str.strip() != ""]
            
        csv_buffer = io.StringIO()
        df_save.to_csv(csv_buffer, index=False)
        repo.update_file(path=BD_FILE, message="Nexion: Sync", content=csv_buffer.getvalue(), sha=sha_save)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- LÓGICA DE ESTADO ---
if 'df_nexion' not in st.session_state:
    df_init, sha_init = cargar_datos()
    st.session_state.df_nexion = df_init
    st.session_state.sha_nexion = sha_init

# --- INTERFAZ ---
st.title("📦 Panel de Control de Envíos - JYPESA")

col_btn, col_info = st.columns([1, 4])
with col_btn:
    # EL CAMBIO: Ahora guardamos lo que esté en el editor al momento del clic
    if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
        with st.spinner("Guardando..."):
            # Usamos los datos actuales del editor que Streamlit guarda en su memoria interna
            df_a_guardar = st.session_state.editor_nexion["edited_rows"]
            
            # Aplicamos los cambios del editor al dataframe original antes de subir
            for index, changes in df_a_guardar.items():
                for key, value in changes.items():
                    st.session_state.df_nexion.at[index, key] = value
            
            exito = guardar_datos(st.session_state.df_nexion, st.session_state.sha_nexion)
            if exito:
                df_up, sha_up = cargar_datos()
                st.session_state.df_nexion = df_up
                st.session_state.sha_nexion = sha_up
                st.success("¡Guardado!")
                st.rerun()

with col_info:
    st.info(f"Registros: {len(st.session_state.df_nexion)} | Modo: Edición Fluida")

st.markdown("---")

# --- EL EDITOR (TRUCO DE ESTABILIDAD) ---
# NO asignamos el resultado a una variable directamente. 
# Streamlit manejará los cambios internamente a través de la 'key'.
st.data_editor(
    st.session_state.df_nexion, 
    column_config={
        "DocNum": st.column_config.TextColumn("Pedido", disabled=True),
        "CardName": st.column_config.TextColumn("Cliente", disabled=True),
        "FECHA DE ENVIO": st.column_config.TextColumn("Fecha (AAAA-MM-DD)"),
        "FLETERA": st.column_config.SelectboxColumn(
            "Fletera", 
            options=["", "PAQUETEXPRESS", "TRESGUERRAS", "CASTORES", "ESTAFETA", "RECOLECCION"]
        ),
        "SURTIDOR": st.column_config.TextColumn("Surtidor"),
        "INCIDENCIA": st.column_config.TextColumn("Notas / Incidencia")
    },
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    key="editor_nexion" # LA KEY ES SAGRADA
)




























































































































































