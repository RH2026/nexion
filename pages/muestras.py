import pandas as pd
import streamlit as st
import requests
import base64
from io import StringIO

# Configuración de GitHub
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_FACTURACION = "facturacion_moreno.csv"
FILE_BASE_MENSUAL = "basemensual.csv"

def actualizar_base_en_github():
    url_raw_new = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}?nocache={pd.Timestamp.now().timestamp()}"
    url_raw_base = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?nocache={pd.Timestamp.now().timestamp()}"
    headers = {"Authorization": f"token {TOKEN}"}

    try:
        # 1. Cargar Facturación Moreno
        df_new = pd.read_csv(url_raw_new)
        
        # LIMPIEZA: Quitamos espacios vacíos en los nombres de las columnas
        df_new.columns = df_new.columns.str.strip()
        
        # Verificamos si la columna de cantidad existe (por si es Quantity o QUENTITY)
        col_cantidad = None
        for c in ['Quantity', 'QUENTITY', 'QUANTITY', 'Cant']:
            if c in df_new.columns:
                col_cantidad = c
                break
        
        if col_cantidad is None:
            st.error(f"No encontré la columna de cantidad. Las columnas disponibles son: {list(df_new.columns)}")
            return

        # Columnas a agrupar
        cols_agrupar = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                        'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
        
        # Filtrar solo las que existen para evitar errores
        cols_existentes = [c for c in cols_agrupar if c in df_new.columns]
        
        # Agrupamos y sumamos
        df_grouped = df_new.groupby(cols_existentes)[col_cantidad].sum().reset_index()
        df_grouped.rename(columns={col_cantidad: 'CAJAS'}, inplace=True)

        # 2. Cargar Base Mensual Actual para cruzar datos manuales
        try:
            df_actual = pd.read_csv(url_raw_base)
            df_actual.columns = df_actual.columns.str.strip()
            cols_manuales = ['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']
            # Solo tomamos las manuales que existan
            existentes_manuales = [c for c in cols_manuales if c in df_actual.columns]
            df_manual_previo = df_actual[existentes_manuales].drop_duplicates(subset=['Factura'])
            
            df_final = pd.merge(df_grouped, df_manual_previo, on='Factura', how='left')
        except:
            df_final = df_grouped.copy()
            for col in ['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']:
                df_final[col] = ""

        # Asegurar que existan las columnas de edición
        for col in ['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']:
            if col not in df_final.columns:
                df_final[col] = ""
        
        df_final = df_final.fillna("")

        # 3. Subir a GitHub
        csv_content = df_final.to_csv(index=False)
        api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_BASE_MENSUAL}"
        get_file = requests.get(api_url, headers=headers)
        
        if get_file.status_code == 200:
            sha = get_file.json()['sha']
            payload = {
                "message": "Actualización basemensual.csv",
                "content": base64.b64encode(csv_content.encode()).decode(),
                "sha": sha
            }
            res = requests.put(api_url, json=payload, headers=headers)
            if res.status_code == 200:
                st.success("¡Base mensual actualizada con éxito! ✅")
                st.rerun() # Esto refresca la página automáticamente
        
    except Exception as e:
        st.error(f"Error: {e}")

# --- INTERFAZ ---
if st.button("Renderizar y Actualizar Base Mensual"):
    actualizar_base_en_github()

st.divider()

try:
    # Leer el archivo final
    url_final = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?nocache={pd.Timestamp.now().timestamp()}"
    df_ver = pd.read_csv(url_final).fillna("")
    
    st.subheader("📋 Control de Base Mensual")
    st.data_editor(
        df_ver,
        hide_index=True,
        use_container_width=True,
        key="editor_v3"
    )
except:
    st.info("Esperando renderizado de información...")

































































