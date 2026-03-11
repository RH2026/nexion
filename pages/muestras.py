import pandas as pd
import streamlit as st
import requests
import base64
from io import StringIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Nexion Logistics - Facturación")

# Configuración de GitHub
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_FACTURACION = "facturacion_moreno.csv"
FILE_BASE_MENSUAL = "basemensual.csv"

def obtener_csv_directo(url):
    headers = {"Authorization": f"token {TOKEN}", "Cache-Control": "no-cache"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text)).fillna("")
    except: pass
    return None

def subir_a_github_turbo(df, mensaje):
    """Versión optimizada: obtiene SHA y sube en una sola lógica"""
    headers = {"Authorization": f"token {TOKEN}"}
    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_BASE_MENSUAL}"
    
    # 1. Obtener SHA rápido
    res_get = requests.get(api_url, headers=headers, timeout=5)
    sha = res_get.json()['sha'] if res_get.status_code == 200 else None
    
    # 2. Subir inmediato
    csv_content = df.fillna("").to_csv(index=False)
    payload = {
        "message": mensaje,
        "content": base64.b64encode(csv_content.encode()).decode(),
        "sha": sha
    }
    res_put = requests.put(api_url, json=payload, headers=headers, timeout=10)
    return res_put.status_code in [200, 201]

def actualizar_matriz():
    t = pd.Timestamp.now().timestamp()
    url_moreno = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}?t={t}"
    url_base = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t}"

    df_new = obtener_csv_directo(url_moreno)
    if df_new is None: return
    
    df_new.columns = df_new.columns.str.strip()
    df_new['Factura'] = df_new['Factura'].astype(str).str.strip()
    col_cant = next((c for c in ['Quantity', 'QUENTITY', 'QUANTITY', 'CANTIDAD'] if c in df_new.columns), 'Quantity')
    
    cols_fijas = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                  'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
    
    df_grouped = df_new.groupby(cols_fijas)[col_cant].sum().reset_index()
    df_grouped.rename(columns={col_cant: 'CAJAS'}, inplace=True)

    df_actual = obtener_csv_directo(url_base)
    if df_actual is not None:
        df_actual.columns = df_actual.columns.str.strip()
        df_actual['Factura'] = df_actual['Factura'].astype(str).str.strip()
        cols_manuales = ['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']
        df_previo = df_actual[cols_manuales].drop_duplicates(subset=['Factura'])
        df_final = pd.merge(df_grouped, df_previo, on='Factura', how='left')
    else:
        df_final = df_grouped.copy()
        for c in ['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']: df_final[c] = ""

    if subir_a_github_turbo(df_final.fillna(""), "Sincronización Moreno"):
        st.cache_data.clear()
        st.rerun()

# --- INTERFAZ ---
st.title("🚚 Nexion - Sincronización de Logística")

if st.button("🔄 Sincronizar con Moreno"):
    with st.spinner("Sincronizando..."):
        actualizar_matriz()

st.divider()

# CARGAR DATOS PARA EL EDITOR
if 'df_memoria' not in st.session_state:
    t_now = pd.Timestamp.now().timestamp()
    url_final = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t_now}"
    st.session_state.df_memoria = obtener_csv_directo(url_final)

if st.session_state.df_memoria is not None:
    # Detectar cambios en el editor
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

    # LÓGICA DE COLOR PARA EL BOTÓN
    # Comparamos si el editor tiene cambios respecto a la memoria original
    hay_cambios = st.session_state.editor_nexion["edited_rows"]
    
    if hay_cambios:
        # Botón Rojo si hay cambios
        estilo_boton = """
            <style>
            div.stButton > button:first-child {
                background-color: #FF4B4B;
                color: white;
                border: 2px solid #FF4B4B;
                width: 100%;
                font-weight: bold;
            }
            </style>
        """
        st.markdown(estilo_boton, unsafe_allow_html=True)
        texto_boton = "⚠️ GUARDAR CAMBIOS PENDIENTES ⚠️"
    else:
        texto_boton = "💾 Guardar Cambios Manuales"

    if st.button(texto_boton):
        with st.spinner("Guardando rápido..."):
            if subir_a_github_turbo(df_editado, "Update manual"):
                st.toast("¡Guardado!", icon="✅")
                # Limpiar memoria para forzar recarga
                del st.session_state.df_memoria
                st.cache_data.clear()
                st.rerun()
else:
    st.info("Presiona Sincronizar para cargar.")







































































