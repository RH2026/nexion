import pandas as pd
import streamlit as st
import requests
import base64
from io import StringIO

# --- CONFIGURACIÓN DE PÁGINA (ESTA ES LA LÍNEA QUE FALTABA) ---
st.set_page_config(layout="wide", page_title="Nexion Logistics - Facturación")
# Configuración de GitHub
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_FACTURACION = "facturacion_moreno.csv"
FILE_BASE_MENSUAL = "basemensual.csv"

def actualizar_matriz():
    # URLs con bypass de caché
    t = pd.Timestamp.now().timestamp()
    url_moreno = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}?t={t}"
    url_base = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t}"
    headers = {"Authorization": f"token {TOKEN}"}

    try:
        # 1. Leer Moreno
        df_new = pd.read_csv(url_moreno)
        df_new.columns = df_new.columns.str.strip() # Limpiar nombres de columnas

        # Identificar columna de cantidad (por si es Quantity o QUENTITY)
        col_cant = next((c for c in ['Quantity', 'QUENTITY', 'QUANTITY', 'CANTIDAD'] if c in df_new.columns), None)
        
        if not col_cant:
            st.error(f"No hallé la columna de cantidad. Columnas: {list(df_new.columns)}")
            return

        # Columnas fijas que queremos traer
        cols_fijas = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                      'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
        
        # Agrupar y sumar cajas
        df_grouped = df_new.groupby(cols_fijas)[col_cant].sum().reset_index()
        df_grouped.rename(columns={col_cant: 'CAJAS'}, inplace=True)

        # 2. Leer Base Mensual Actual para no perder lo editado
        try:
            df_actual = pd.read_csv(url_base)
            df_actual.columns = df_actual.columns.str.strip()
            # Columnas que el usuario llena manualmente
            cols_manuales = ['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']
            df_previo = df_actual[cols_manuales].drop_duplicates(subset=['Factura'])
            
            # Unir lo nuevo con lo viejo
            df_final = pd.merge(df_grouped, df_previo, on='Factura', how='left')
        except:
            df_final = df_grouped.copy()
            for c in ['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']: df_final[c] = ""

        # Limpieza final de nulos
        df_final = df_final.fillna("")
        
        # 3. Guardar en GitHub
        subir_a_github(df_final, "Actualización automática desde Moreno")
        st.success("¡Información renderizada y actualizada! ✅")
        st.rerun()

    except Exception as e:
        st.error(f"Error al procesar: {e}")

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
    
    requests.put(api_url, json=payload, headers=headers)

# --- INTERFAZ STREAMLIT ---
st.title("🚚 Gestión de Facturación")

if st.button("🔄 Renderizar Datos de Moreno"):
    actualizar_matriz()

st.divider()

try:
    # Cargar para mostrar en el editor
    url_final = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={pd.Timestamp.now().timestamp()}"
    df_editor = pd.read_csv(url_final).fillna("")

    st.subheader("📝 Edición de Base Mensual")
    
    # Editor interactivo
    df_modificado = st.data_editor(
        df_editor,
        column_config={
            "CAJAS": st.column_config.NumberColumn(disabled=True),
            "Factura": st.column_config.TextColumn(disabled=True),
            "SURTIDOR": st.column_config.TextColumn(help="Escribe el nombre del surtidor"),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_principal"
    )

    if st.button("💾 Guardar Cambios Manuales"):
        with st.spinner("Guardando en GitHub..."):
            subir_a_github(df_modificado, "Cambios manuales en editor")
            st.success("¡Cambios guardados correctamente! 📁")
            st.cache_data.clear()

except Exception as e:
    st.info("No hay datos en la base mensual. Haz clic en 'Renderizar' para comenzar.")



































































