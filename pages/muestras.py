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
    # URLs con bypass de caché para obligar a GitHub a darnos lo último
    t = pd.Timestamp.now().timestamp()
    url_moreno = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}?t={t}"
    url_base = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t}"
    headers = {"Authorization": f"token {TOKEN}"}

    try:
        # 1. Leer Moreno
        df_new = pd.read_csv(url_moreno)
        df_new.columns = df_new.columns.str.strip() # Limpiar espacios en nombres

        # Identificar columna de cantidad
        col_cant = next((c for c in ['Quantity', 'QUENTITY', 'QUANTITY', 'CANTIDAD'] if c in df_new.columns), None)
        
        if not col_cant:
            st.error(f"No hallé la columna de cantidad. Columnas detectadas: {list(df_new.columns)}")
            return

        # Columnas fijas que queremos renderizar
        cols_fijas = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                      'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
        
        # Agrupar por factura y sumar cajas
        df_grouped = df_new.groupby(cols_fijas)[col_cant].sum().reset_index()
        df_grouped.rename(columns={col_cant: 'CAJAS'}, inplace=True)

        # 2. Leer Base Mensual Actual para NO perder lo que ya escribiste
        try:
            df_actual = pd.read_csv(url_base)
            df_actual.columns = df_actual.columns.str.strip()
            # Columnas manuales que queremos preservar
            cols_manuales = ['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']
            df_previo = df_actual[cols_manuales].drop_duplicates(subset=['Factura'])
            
            # Unir lo nuevo (Moreno) con lo viejo (tu edición manual)
            df_final = pd.merge(df_grouped, df_previo, on='Factura', how='left')
        except:
            # Si no existe basemensual.csv, creamos las columnas vacías
            df_final = df_grouped.copy()
            for c in ['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']: 
                df_final[c] = ""

        # Limpiar valores nulos para que el CSV se vea limpio
        df_final = df_final.fillna("")
        
        # 3. Guardar el render en GitHub
        subir_a_github(df_final, "Actualización automática desde Moreno")
        st.success("¡Información renderizada y actualizada! ✅")
        st.rerun()

    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")

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
st.title("🚚 Nexion - Gestión de Facturación Moreno")

# Botón principal
if st.button("🔄 Renderizar y Actualizar Base Mensual"):
    with st.spinner("Procesando matriz..."):
        actualizar_matriz()

st.divider()

try:
    # Cargar para mostrar en el editor (siempre lo más reciente)
    t_now = pd.Timestamp.now().timestamp()
    url_final = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t_now}"
    df_editor = pd.read_csv(url_final).fillna("")

    st.subheader("📝 Edición de Información (Surtidor, Paquetería, etc.)")
    
    # Editor interactivo en pantalla ancha
    df_modificado = st.data_editor(
        df_editor,
        column_config={
            "Factura": st.column_config.TextColumn(disabled=True),
            "CAJAS": st.column_config.NumberColumn(disabled=True),
            "SURTIDOR": st.column_config.TextColumn(help="Asigna un surtidor"),
            "PAQUETERIA": st.column_config.TextColumn(help="Fletera o Paquetería"),
            "FECHA": st.column_config.TextColumn(help="Fecha de salida"),
        },
        hide_index=True,
        use_container_width=True, # Esto hace que use todo el ancho
        key="editor_principal"
    )

    # Botón para salvar lo que escribas en la tabla
    if st.button("💾 Guardar Cambios Manuales"):
        with st.spinner("Guardando en GitHub..."):
            subir_a_github(df_modificado, "Cambios manuales en editor")
            st.success("¡Cambios guardados correctamente en GitHub! 📁")
            st.cache_data.clear()

except Exception as e:
    st.info("La base mensual está lista para ser generada. Haz clic en el botón de arriba.")













































































