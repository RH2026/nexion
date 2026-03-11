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

# --- MANEJO DE ESTADO (CRÍTICO) ---
# Si no cargamos esto en session_state, Streamlit lo borra cada vez que parpadeas
if 'df_memoria' not in st.session_state:
    t_ini = pd.Timestamp.now().timestamp()
    url_repo = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t_ini}"
    st.session_state.df_memoria = obtener_csv_directo(url_repo)

st.title("🚚 Nexion - Panel Logístico")

if st.session_state.df_memoria is not None:
    # EL EDITOR: Ahora usa df_memoria para no perder datos al recargar
    df_editado = st.data_editor(
        st.session_state.df_memoria,
        column_config={
            "Factura": st.column_config.TextColumn(disabled=True),
            "CAJAS": st.column_config.NumberColumn(disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_nexion"
    )

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 GUARDAR CAMBIOS MANUALES", use_container_width=True):
            with st.spinner("Guardando en GitHub..."):
                if subir_a_github(df_editado, "Guardado manual"):
                    st.session_state.df_memoria = df_editado # Actualizamos la memoria
                    st.success("¡Cambios guardados! ✅")
                    st.rerun()

    with col2:
        if st.button("🔄 SINCRONIZAR CON MORENO", use_container_width=True):
            with st.spinner("Sincronizando..."):
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

                    # 2. CRUCIAL: Cruzamos Moreno contra lo que tienes EN PANTALLA (df_editado)
                    # No contra lo de GitHub, porque lo de la pantalla es lo que acabas de escribir
                    df_editado['Factura'] = df_editado['Factura'].astype(str).str.strip()
                    
                    df_final = pd.merge(
                        df_grouped, 
                        df_editado[['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']], 
                        on='Factura', 
                        how='left'
                    ).fillna("")

                    # 3. Guardar el resultado mezclado
                    if subir_a_github(df_final, "Sincronización Moreno"):
                        st.session_state.df_memoria = df_final # Actualizamos la memoria
                        st.success("¡Sincronizado! Se respetaron tus cambios en pantalla. 🚀")
                        st.rerun()
else:
    st.info("No hay datos. Sincroniza para empezar.")
    if st.button("Sincronizar Moreno por primera vez"):
        # Lógica de sincronización inicial
        pass












































































