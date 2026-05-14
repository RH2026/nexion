import streamlit as st
import pandas as pd
import re
import requests
from io import BytesIO

def procesar_nexion_v2():
    st.title("Actualizador de Facturas - Nexion")

    # --- CONFIGURACIÓN GITHUB ---
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    REPO_NAME = "RH2026/nexion"
    FILE_PATH_T1 = "T1.xlsx"
    URL_T1 = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH_T1}"

    # 1. Cargar TI.xlsx (El origen de los datos)
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(URL_T1, headers=headers)
        if response.status_code == 200:
            df_t1 = pd.read_excel(BytesIO(response.content))
        else:
            st.error(f"Error al conectar con GitHub (Status: {response.status_code})")
            return
    except Exception as e:
        st.error(f"Error: {e}")
        return

    # 2. Subida del archivo del usuario (El de la imagen image_d92069.png)
    archivo_usuario = st.file_uploader("Sube tu archivo de facturas", type=["xlsx"])

    if archivo_usuario:
        df_user = pd.read_excel(archivo_usuario)
        
        # --- PROCESAMIENTO ---
        
        # A. Limpiamos y preparamos el archivo TI (Origen)
        def extraer_folios(texto):
            if pd.isna(texto): return []
            return re.findall(r'\d+', str(texto))

        # Expandimos OBSERVACION 1 por si vienen varias facturas juntas
        df_t1['factura_busqueda'] = df_t1['OBSERVACION 1'].apply(extraer_folios)
        df_t1_exp = df_t1.explode('factura_busqueda')
        df_t1_exp['factura_busqueda'] = df_t1_exp['factura_busqueda'].astype(str).str.strip()

        # B. Aseguramos que la columna 'factura' del usuario sea texto
        if 'factura' in df_user.columns:
            df_user['factura'] = df_user['factura'].astype(str).str.strip()

            # C. Realizamos el Cruce (Match)
            # Mapeamos: TALON -> guia, SUBTOTAL -> costo, F.DOC -> fecha_envio, BULTOS -> bultos
            resultado = pd.merge(
                df_user[['factura']], # Solo nos quedamos con la columna base para rellenar
                df_t1_exp[['factura_busqueda', 'TALON', 'SUBTOTAL', 'F.DOC', 'BULTOS']],
                left_on='factura',
                right_on='factura_busqueda',
                how='left'
            )

            # D. Renombramos las columnas para que queden como en tu imagen image_d92069.png
            resultado = resultado.rename(columns={
                'TALON': 'guia',
                'SUBTOTAL': 'costo',
                'F.DOC': 'fecha_envio',
                'BULTOS': 'bultos'
            })

            # Quitamos la columna auxiliar de búsqueda
            resultado = resultado.drop(columns=['factura_busqueda'])

            st.success("¡Datos cruzados con éxito!")
            st.dataframe(resultado.head(10))

            # E. Botón de descarga
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                resultado.to_excel(writer, index=False)
            
            st.download_button(
                label="Descargar Reporte para Nexion",
                data=output.getvalue(),
                file_name="nexion_actualizado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("El archivo subido no tiene una columna llamada 'factura'.")

procesar_nexion_v2()







































