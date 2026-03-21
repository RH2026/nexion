import pandas as pd
import streamlit as st
from github import Github
import io

# Configuración de acceso
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
SAP_FILE = "sapdata.xlsx"  # Tu matriz principal de SAP
BD_FILE = "enviosbd.csv"   # Tu matriz editable

def actualizar_base_datos():
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)

    # 1. Cargar sapdata.xlsx (La fuente nueva)
    content_sap = repo.get_contents(SAP_FILE)
    df_sap = pd.read_excel(io.BytesIO(content_sap.decoded_content))

    # 2. Cargar enviosbd.csv (Tu base actual)
    try:
        content_bd = repo.get_contents(BD_FILE)
        df_bd = pd.read_csv(io.StringIO(content_bd.decoded_content.decode('utf-8')))
    except:
        # Si el archivo no existe, lo creamos con las columnas de SAP + las 4 nuevas
        df_bd = df_sap.copy()
        for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
            df_bd[col] = ""

    # 3. IDENTIFICAR FILAS NUEVAS (El "BuscarV" inteligente)
    # Buscamos los DocNum que están en SAP pero NO están en nuestra BD
    nuevos_registros = df_sap[~df_sap['DocNum'].isin(df_bd['DocNum'])].copy()

    if not nuevos_registros.empty:
        # Añadimos las 4 columnas vacías a los nuevos registros
        for col in ['FECHA DE ENVIO', 'FLETERA', 'SURTIDOR', 'INCIDENCIA']:
            nuevos_registros[col] = ""
        
        # Unimos lo viejo con lo nuevo (Concatenar)
        df_final = pd.concat([df_bd, nuevos_registros], ignore_index=True)
        
        # 4. SUBIR A GITHUB
        csv_buffer = io.StringIO()
        df_final.to_csv(csv_buffer, index=False)
        
        repo.update_file(
            path=BD_FILE,
            message=f"Sincronización: {len(nuevos_registros)} nuevos pedidos agregados",
            content=csv_buffer.getvalue(),
            sha=content_bd.sha if 'content_bd' in locals() else None
        )
        return f"¡Éxito! Se agregaron {len(nuevos_registros)} pedidos nuevos a la base."
    else:
        return "No hay pedidos nuevos en SAP para agregar."

# Interfaz en Streamlit
if st.button("Sincronizar SAP con Envios BD"):
    resultado = actualizar_base_datos()
    st.success(resultado)




























































































































































