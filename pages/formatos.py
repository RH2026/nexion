import pandas as pd
import streamlit as st
from github import Github
import io

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
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
        
        # LIMPIEZA DE FILAS FANTASMA (nan/vacías)
        # Solo mantenemos filas que tengan un número de pedido real
        if 'DocNum' in df.columns:
            df = df.dropna(subset=['DocNum'])
            df['DocNum'] = df['DocNum'].astype(str).str.strip()
            df = df[df['DocNum'] != ""]
        
        # Asegurar columnas de edición y limpiar textos feos
        cols_edit = ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']
        for col in cols_edit:
            if col not in df.columns:
                df[col] = ""
            # Convertimos a string y quitamos los "nan" visuales
            df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN', 'NaT'], '')
            
        return df, content.sha
    except Exception as e:
        st.error(f"Error al cargar: {e}")
        return pd.DataFrame(), None

def guardar_datos(df_save, sha_save):
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Limpieza final antes de enviar a GitHub para no guardar basura
        if 'DocNum' in df_save.columns:
            df_save = df_save.dropna(subset=['DocNum'])
            df_save = df_save[df_save['DocNum'].astype(str).str.strip() != ""]
            
        csv_buffer = io.StringIO()
        df_save.to_csv(csv_buffer, index=False)
        
        repo.update_file(
            path=BD_FILE,
            message="Nexion: Actualización de matriz",
            content=csv_buffer.getvalue(),
            sha=sha_save
        )
        st.success("¡Datos guardados en GitHub!")
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- LÓGICA DE ESTADO (Session State) ---
if 'df_nexion' not in st.session_state:
    df_init, sha_init = cargar_datos()
    st.session_state.df_nexion = df_init
    st.session_state.sha_nexion = sha_init

# --- INTERFAZ ---
st.title("📦 Panel de Control de Envíos - JYPESA")

# Botones de Acción
col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
        exito = guardar_datos(st.session_state.df_nexion, st.session_state.sha_nexion)
        if exito:
            # Refrescamos datos y SHA para la siguiente vuelta
            df_up, sha_up = cargar_datos()
            st.session_state.df_nexion = df_up
            st.session_state.sha_nexion = sha_up
            st.rerun()

with col_info:
    st.info(f"Total de registros: {len(st.session_state.df_nexion)} | Editando archivo: {BD_FILE}")

st.markdown("---")

# --- EL EDITOR DE DATOS ---
# Usamos una copia para que el editor trabaje fluido
df_para_editar = st.session_state.df_nexion.copy()

df_editado = st.data_editor(
    df_para_editar,
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
    num_rows="fixed" # Esto evita que se creen filas nan manualmente
)

# Sincronizamos lo que escribes con el estado de la sesión
st.session_state.df_nexion = df_editado




























































































































































