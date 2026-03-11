import pandas as pd
import streamlit as st
import requests
import base64
from io import StringIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Nexion Logistics - Facturación")

# Configuración de GitHub
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_FACTURACION = "facturacion_moreno.csv"
FILE_BASE_MENSUAL = "basemensual.csv"

# Función rápida para subir a GitHub
def subir_a_github(df, mensaje):
    headers = {"Authorization": f"token {TOKEN}"}
    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_BASE_MENSUAL}"
    
    csv_content = df.to_csv(index=False)
    get_file = requests.get(api_url, headers=headers)
    
    sha = get_file.json()['sha'] if get_file.status_code == 200 else None
    
    payload = {
        "message": mensaje,
        "content": base64.b64encode(csv_content.encode()).decode(),
    }
    if sha: payload["sha"] = sha
    
    res = requests.put(api_url, json=payload, headers=headers)
    return res.status_code == 200 or res.status_code == 201

# Función para actualizar (se llama solo al presionar el botón)
def actualizar_matriz():
    t = pd.Timestamp.now().timestamp()
    url_moreno = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}?t={t}"
    url_base = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t}"

    try:
        # Cargar Moreno
        df_new = pd.read_csv(url_moreno)
        df_new.columns = df_new.columns.str.strip()

        col_cant = next((c for c in ['Quantity', 'QUENTITY', 'QUANTITY', 'CANTIDAD'] if c in df_new.columns), None)
        if not col_cant:
            st.error("No encontré la columna de cantidad.")
            return

        cols_fijas = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                      'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
        
        # Agrupar rápido
        df_grouped = df_new.groupby(cols_fijas)[col_cant].sum().reset_index()
        df_grouped.rename(columns={col_cant: 'CAJAS'}, inplace=True)

        # Intentar traer manuales previos
        try:
            df_actual = pd.read_csv(url_base)
            df_actual.columns = df_actual.columns.str.strip()
            cols_manuales = ['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']
            df_previo = df_actual[cols_manuales].drop_duplicates(subset=['Factura'])
            df_final = pd.merge(df_grouped, df_previo, on='Factura', how='left')
        except:
            df_final = df_grouped.copy()
            for c in ['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']: df_final[c] = ""

        df_final = df_final.fillna("")
        
        if subir_a_github(df_final, "Auto-update"):
            st.success("¡Renderizado completo! Actualizando vista...")
            st.cache_data.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# --- INTERFAZ ---
st.title("🚚 Nexion - Control de Facturación")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Renderizar Moreno"):
        actualizar_matriz()

st.divider()

# CARGA RÁPIDA DE LA TABLA
@st.cache_data(ttl=10) # Cache de solo 10 segundos para que sea veloz
def cargar_base_mensual():
    t = pd.Timestamp.now().timestamp()
    url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t}"
    return pd.read_csv(url).fillna("")

try:
    df_editor = cargar_base_mensual()
    
    st.subheader("📝 Edición de Información")
    df_modificado = st.data_editor(
        df_editor,
        column_config={
            "Factura": st.column_config.TextColumn(disabled=True),
            "CAJAS": st.column_config.NumberColumn(disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_nexion"
    )

    if st.button("💾 Guardar Cambios"):
        if subir_a_github(df_modificado, "Manual update"):
            st.success("¡Guardado!")
            st.cache_data.clear()
            st.rerun()

except Exception:
    st.info("Renderiza los datos para ver la tabla.")




































































