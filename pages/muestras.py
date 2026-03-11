import pandas as pd
import streamlit as st
import requests
import base64
from io import StringIO

# Configuración de GitHub desde tus secrets
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_FACTURACION = "facturacion_moreno.csv"
FILE_BASE_MENSUAL = "basemensual.csv"

def actualizar_base_en_github():
    # 1. URLs para lectura (Raw)
    url_raw_new = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}"
    url_raw_base = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}"
    
    headers = {"Authorization": f"token {TOKEN}"}

    try:
        # Cargar Facturación Moreno
        df_new = pd.read_csv(url_raw_new)
        
        # Columnas a agrupar y sumar Quantity como CAJAS
        cols_agrupar = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                        'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
        
        # Agrupamos para consolidar partidas en una sola línea por factura
        df_grouped = df_new.groupby(cols_agrupar)['Quantity'].sum().reset_index()
        df_grouped.rename(columns={'Quantity': 'CAJAS'}, inplace=True)

        # 2. Cargar Base Mensual Actual para no perder SURTIDOR, PAQUETERIA, etc.
        try:
            # Añadimos un timestamp para evitar que GitHub nos devuelva una versión vieja de la caché
            url_cache_bypass = f"{url_raw_base}?nocache={pd.Timestamp.now().timestamp()}"
            df_actual = pd.read_csv(url_cache_bypass)
            
            # Solo nos interesan las columnas manuales de la base vieja para cruzarlas
            cols_manuales = ['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']
            df_manual_previo = df_actual[cols_manuales].drop_duplicates(subset=['Factura'])
            
            # Unir: Mantenemos lo nuevo (Moreno) y le pegamos lo que ya estaba escrito en la base mensual
            df_final = pd.merge(df_grouped, df_manual_previo, on='Factura', how='left')
        except:
            # Si el archivo no existe o falla, creamos las columnas vacías
            df_final = df_grouped.copy()
            for col in ['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']:
                df_final[col] = ""

        # Llenar nulos con vacío en caso de facturas nuevas que no tienen datos previos
        df_final[['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']] = df_final[['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']].fillna("")

        # 3. SUBIR A GITHUB (API)
        csv_content = df_final.to_csv(index=False)
        
        # Necesitamos el SHA del archivo actual para poder sobreescribirlo
        api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_BASE_MENSUAL}"
        get_file = requests.get(api_url, headers=headers)
        
        if get_file.status_code == 200:
            sha = get_file.json()['sha']
            payload = {
                "message": "Actualización automática de basemensual.csv",
                "content": base64.b64encode(csv_content.encode()).decode(),
                "sha": sha
            }
            res = requests.put(api_url, json=payload, headers=headers)
            if res.status_code == 200:
                st.success("¡Base mensual actualizada en GitHub con éxito! ✅")
                # Limpiamos caché para que el editor cargue los datos nuevos
                st.cache_data.clear()
            else:
                st.error("Error al subir el archivo.")
        
    except Exception as e:
        st.error(f"Hubo un error, amor: {e}")

# --- INTERFAZ DE USUARIO ---

# Botón para ejecutar el proceso
if st.button("Renderizar y Actualizar Base Mensual"):
    actualizar_base_en_github()

st.divider()

# Cargar y mostrar los datos para edición
try:
    # Leemos la base mensual actualizada de GitHub
    CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?nocache={pd.Timestamp.now().timestamp()}"
    df_visualizar = pd.read_csv(CSV_URL)

    st.subheader("📋 Control de Base Mensual")
    
    # El data_editor permite ver y editar la información
    df_editado = st.data_editor(
        df_visualizar,
        column_config={
            "CAJAS": st.column_config.NumberColumn(disabled=True),
            "Factura": st.column_config.TextColumn(disabled=True),
            "Fecha_Conta": st.column_config.TextColumn(disabled=True)
        },
        hide_index=True,
        use_container_width=True,
        key="editor_mensual"
    )

except Exception as e:
    st.info("Haz clic en el botón superior para generar o visualizar la base mensual.")

































































