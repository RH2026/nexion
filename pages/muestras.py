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
    """Función para saltarse el caché de GitHub a la fuerza"""
    headers = {
        "Authorization": f"token {TOKEN}",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.read_csv(StringIO(response.text))
    else:
        return None

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
    
    res = requests.put(api_url, json=payload, headers=headers)
    return res.status_code in [200, 201]

def actualizar_matriz():
    # Bypass total de caché
    t = pd.Timestamp.now().timestamp()
    url_moreno = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_FACTURACION}?t={t}"
    url_base = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t}"

    try:
        # 1. Leer Moreno con el nuevo método directo
        df_new = obtener_csv_directo(url_moreno)
        if df_new is None:
            st.error("No se pudo leer el archivo de Moreno desde GitHub.")
            return

        df_new.columns = df_new.columns.str.strip()
        df_new['Factura'] = df_new['Factura'].astype(str).str.strip() # Asegurar llave de cruce

        col_cant = next((c for c in ['Quantity', 'QUENTITY', 'QUANTITY', 'CANTIDAD'] if c in df_new.columns), None)
        if not col_cant:
            st.error(f"Columnas detectadas: {list(df_new.columns)}")
            return

        cols_fijas = ['Factura', 'Almacen', 'Fecha_Conta', 'Cliente', 'Nombre_Cliente', 
                      'Nombre_Extran', 'Domicilio', 'Colonia', 'Cuidad', 'Estado', 'CP']
        
        # Agrupar y sumar cajas
        df_grouped = df_new.groupby(cols_fijas)[col_cant].sum().reset_index()
        df_grouped.rename(columns={col_cant: 'CAJAS'}, inplace=True)

        # 2. Intentar cruzar con manuales previos
        df_actual = obtener_csv_directo(url_base)
        if df_actual is not None:
            df_actual.columns = df_actual.columns.str.strip()
            df_actual['Factura'] = df_actual['Factura'].astype(str).str.strip()
            
            cols_manuales = ['Factura', 'SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']
            # Solo tomamos lo que ya escribiste
            df_previo = df_actual[cols_manuales].drop_duplicates(subset=['Factura'])
            
            # EL CRUCE MÁGICO: Trae todo lo nuevo de Moreno y pégale lo viejo por Factura
            df_final = pd.merge(df_grouped, df_previo, on='Factura', how='left')
        else:
            df_final = df_grouped.copy()
            for c in ['SURTIDOR', 'PAQUETERIA', 'FECHA', 'INCIDENCIA']: df_final[c] = ""

        df_final = df_final.fillna("")
        
        if subir_a_github(df_final, "Sincronización total Moreno"):
            st.success("¡Base actualizada con las nuevas filas! 🚀")
            st.cache_data.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"Error en el cruce: {e}")

# --- INTERFAZ ---
st.title("🚚 Nexion - Sincronización de Logística")

if st.button("🔄 Forzar Sincronización (Moreno -> Base)"):
    with st.spinner("Buscando nuevas facturas y cruzando datos..."):
        actualizar_matriz()

st.divider()

@st.cache_data(ttl=5) # Cache súper corto
def cargar_base():
    t = pd.Timestamp.now().timestamp()
    url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_BASE_MENSUAL}?t={t}"
    df = obtener_csv_directo(url)
    return df if df is not None else pd.DataFrame()

try:
    df_editor = cargar_base()
    if not df_editor.empty:
        st.subheader(f"📝 Registros detectados: {len(df_editor)}")
        df_modificado = st.data_editor(
            df_editor,
            column_config={
                "Factura": st.column_config.TextColumn(disabled=True),
                "CAJAS": st.column_config.NumberColumn(disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key="editor_nexion_v4"
        )

        if st.button("💾 Guardar Cambios Manuales"):
            if subir_a_github(df_modificado, "Cambio manual"):
                st.success("Guardado en GitHub")
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Presiona el botón de sincronización para cargar los datos.")

except Exception as e:
    st.error(f"Error al mostrar tabla: {e}")




































































