import pandas as pd
import streamlit as st
from github import Github
import io

# Configuración (Asegúrate de que los nombres coincidan en tu GitHub)
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
SAP_FILE = "sapdata.csv"   # Tu matriz principal (la que no se edita)
BD_FILE = "enviosbd.csv"    # Tu matriz de trabajo (la editable)

def actualizar_base_datos():
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # 1. LEER SAPDATA.CSV (La fuente de datos)
        try:
            content_sap = repo.get_contents(SAP_FILE)
            # Usamos download_url para evitar errores de archivos grandes
            df_sap = pd.read_csv(content_sap.download_url)
        except Exception as e:
            return f"Error: No se pudo leer '{SAP_FILE}'. Revisa si existe en GitHub."

        # 2. LEER ENVIOSBD.CSV (Tu base editable)
        try:
            content_bd = repo.get_contents(BD_FILE)
            df_bd = pd.read_csv(content_bd.download_url)
            sha_bd = content_bd.sha
        except:
            # Si no existe todavía, la creamos con las columnas de SAP + las 4 nuevas
            st.warning("Creando 'enviosbd.csv' por primera vez...")
            columnas_finales = list(df_sap.columns) + ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']
            df_bd = pd.DataFrame(columns=columnas_finales)
            sha_bd = None

        # 3. CRUCE DE DATOS (BUSCARV)
        # Convertimos DocNum a texto para que el cruce sea exacto
        df_sap['DocNum'] = df_sap['DocNum'].astype(str)
        df_bd['DocNum'] = df_bd['DocNum'].astype(str)

        # Filtramos: "Dame los de SAP que NO estén en mi BD editable"
        nuevos_registros = df_sap[~df_sap['DocNum'].isin(df_bd['DocNum'])].copy()

        if not nuevos_registros.empty:
            # Agregamos las 4 columnas de edición vacías a los nuevos
            for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
                nuevos_registros[col] = ""
            
            # Concatenamos (pegamos abajo) sin tocar lo que ya habías editado
            df_final = pd.concat([df_bd, nuevos_registros], ignore_index=True)
            
            # 4. SUBIR CAMBIOS A GITHUB
            csv_buffer = io.StringIO()
            df_final.to_csv(csv_buffer, index=False)
            
            repo.update_file(
                path=BD_FILE,
                message=f"Nexion: Agregados {len(nuevos_registros)} pedidos nuevos",
                content=csv_buffer.getvalue(),
                sha=sha_bd
            )
            return f"¡Hecho amor! Se sumaron {len(nuevos_registros)} filas nuevas a tu base de envíos."
        else:
            return "Tu base ya está al día, no hay pedidos nuevos en SAP."

    except Exception as e:
        return f"Ocurrió un detalle: {str(e)}"

# Botón en tu página de Formatos
if st.button("🔄 Sincronizar Matrices"):
    with st.spinner("Buscando pedidos nuevos..."):
        resultado = actualizar_base_datos()
        st.info(resultado)




























































































































































