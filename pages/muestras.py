import pandas as pd
import streamlit as st
import requests
import base64
from io import StringIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Nexion Logistics")

# Configuración de GitHub
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_FACTURACION = "facturacion_moreno.csv"
FILE_BASE_MENSUAL = "basemensual.csv"

def obtener_csv_directo(url):
    headers = {"Authorization": f"token {TOKEN}", "Cache-Control": "no-cache", "Pragma": "no-cache"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text)).fillna("")
    except: pass
    return None

def subir_a_github(df, mensaje):
    headers = {"Authorization": f"token {TOKEN}"}
    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_BASE_MENSUAL}"
    res_get = requests.get(api_url, headers=headers)
    sha = res_get.json()['sha'] if res_get.status_code == 200 else None
    
    csv_content = df.to_csv(index=False)
    payload = {
        "message": mensaje,
        "content": base64.b64encode(csv_content.encode()).decode(),
        "sha": sha
    }
    res_put = requests.put(api_url, json=payload, headers=headers)
    return res_put.status_code in [200, 201]

# --- MANEJO DE ESTADO ---
if 'version_editor' not in st.session_state:
    st.session_state.version_editor = 0

# Carga inicial (Siempre lee de GitHub al abrir la página)
t_ini = pd.Timestamp.now().timestamp()
url_repo = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t_ini}"
df_actual_github = obtener_csv_directo(url_repo)

st.title("🚚 Nexion - Panel Logístico")

if df_actual_github is not None:
    # EL EDITOR: Siempre muestra lo más reciente de GitHub
    df_editado = st.data_editor(
        df_actual_github,
        column_config={
            "Factura": st.column_config.TextColumn(disabled=True),
            "CAJAS": st.column_config.NumberColumn(disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        key=f"editor_v{st.session_state.version_editor}"
    )

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 GUARDAR CAMBIOS MANUALES", use_container_width=True):
            with st.spinner("Guardando en GitHub..."):
                if subir_a_github(df_editado, "Guardado manual"):
                    st.success("¡Cambios guardados! ✅")
                    st.cache_data.clear()
                    st.rerun()

    with col2:
        if st.button("🔄 SINCRONIZAR CON MORENO", use_container_width=True):
            with st.spinner("Sincronizando... (Recuperando datos de GitHub)"):
                # 1. Traer Moreno
                t = pd.Timestamp.now().timestamp()
                url_moreno = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}?t={t}"
                df_moreno = obtener_csv_directo(url_moreno)
                
                if df_moreno is not None:
                    df_moreno.columns = df_moreno.columns.str.strip()
                    df_moreno['Factura'] = df_moreno['Factura'].astype(str).str.strip()
                    col_cant = next((c for c in ['Quantity', 'QUENTITY', 'QUANTITY', 'CANTIDAD'] if c in df_moreno.columns), 'Quantity')
                    
                    cols_fijas = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                                  'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
                    
                    df_grouped = df_moreno.groupby(cols_fijas)[col_cant].sum().reset_index()
                    df_grouped.rename(columns={col_cant: 'CAJAS'}, inplace=True)

                    # 2. IMPORTANTE: Cruzamos Moreno contra lo que YA está en GitHub
                    # Así, si cerraste la página, recuperamos lo que guardaste antes.
                    df_actual_github['Factura'] = df_actual_github['Factura'].astype(str).str.strip()
                    
                    df_final = pd.merge(
                        df_grouped, 
                        df_actual_github[['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']], 
                        on='Factura', 
                        how='left'
                    ).fillna("")

                    # 3. Guardar el resultado mezclado
                    if subir_a_github(df_final, "Sincronización Moreno"):
                        st.success("¡Sincronizado! Se recuperaron tus capturas previas de GitHub. 🚀")
                        st.cache_data.clear()
                        st.rerun()
else:
    st.info("No hay datos en la base mensual. Sincroniza para empezar.")
    if st.button("Sincronizar Moreno por primera vez"):
        # (Aquí podrías poner la misma lógica de sincronización arriba)
        pass











































































