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
    headers = {"Authorization": f"token {TOKEN}", "Cache-Control": "no-cache"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text)).fillna("")
    except: pass
    return None

def guardar_y_sincronizar(df_actual_del_editor):
    """Sincroniza con Moreno y guarda todo en un solo paso"""
    t = pd.Timestamp.now().timestamp()
    url_moreno = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}?t={t}"
    
    # 1. Leer Moreno para ver si hay facturas nuevas
    df_moreno = obtener_csv_directo(url_moreno)
    if df_moreno is None:
        st.error("No se pudo leer Moreno para sincronizar.")
        return

    # Preparar Moreno
    df_moreno.columns = df_moreno.columns.str.strip()
    df_moreno['Factura'] = df_moreno['Factura'].astype(str).str.strip()
    col_cant = next((c for c in ['Quantity', 'QUENTITY', 'QUANTITY', 'CANTIDAD'] if c in df_moreno.columns), 'Quantity')
    
    cols_fijas = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                  'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
    
    # Agrupar Moreno
    df_grouped = df_moreno.groupby(cols_fijas)[col_cant].sum().reset_index()
    df_grouped.rename(columns={col_cant: 'CAJAS'}, inplace=True)

    # 2. Cruzar con lo que el usuario tiene actualmente en el editor (para no perder cambios)
    df_actual_del_editor['Factura'] = df_actual_del_editor['Factura'].astype(str).str.strip()
    cols_manuales = ['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']
    df_manual = df_actual_del_editor[cols_manuales].drop_duplicates(subset=['Factura'])
    
    # Unimos: Mantenemos estructura de Moreno y pegamos lo editado
    df_final = pd.merge(df_grouped, df_manual, on='Factura', how='left').fillna("")

    # 3. Subir a GitHub
    headers = {"Authorization": f"token {TOKEN}"}
    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_BASE_MENSUAL}"
    
    res_get = requests.get(api_url, headers=headers)
    sha = res_get.json()['sha'] if res_get.status_code == 200 else None
    
    csv_content = df_final.to_csv(index=False)
    payload = {
        "message": "Sincronización y Guardado Automático",
        "content": base64.b64encode(csv_content.encode()).decode(),
        "sha": sha
    }
    
    res_put = requests.put(api_url, json=payload, headers=headers)
    if res_put.status_code in [200, 201]:
        st.success("¡Sincronizado y Guardado en GitHub! ✅")
        st.cache_data.clear()
        st.rerun()

# --- INTERFAZ ---
st.title("🚚 Nexion - Panel Logístico Único")

# Carga inicial de datos
t_ini = pd.Timestamp.now().timestamp()
url_ini = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t_ini}"
df_inicial = obtener_csv_directo(url_ini)

if df_inicial is not None:
    # Mostramos el editor
    df_editado = st.data_editor(
        df_inicial,
        column_config={
            "Factura": st.column_config.TextColumn(disabled=True),
            "CAJAS": st.column_config.NumberColumn(disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        key="main_editor"
    )

    st.divider()

    # EL BOTÓN ÚNICO
    # Si hay cambios detectados, se pone rojo
    hay_cambios = len(st.session_state.main_editor["edited_rows"]) > 0
    
    if hay_cambios:
        st.markdown("""<style>div.stButton > button {background-color: #FF4B4B !important; color: white !important; font-weight: bold !important; width: 100% !important;}</style>""", unsafe_allow_html=True)
        label = "⚠️ DETECTO CAMBIOS: GUARDAR Y SINCRONIZAR ⚠️"
    else:
        label = "🔄 GUARDAR Y SINCRONIZAR CON MORENO"

    if st.button(label):
        with st.spinner("Procesando todo en un paso..."):
            guardar_y_sincronizar(df_editado)
else:
    st.warning("No se pudo cargar la base mensual. Verifica tu archivo en GitHub.")







































































