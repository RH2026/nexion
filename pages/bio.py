import streamlit as st
import pandas as pd
import datetime
import requests
import base64
from io import StringIO

# --- CONFIGURACIÓN DE ACCESO (GITHUB SECRETS) ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = "RH2026/nexion"
FILE_PATH = "locales.csv"

# --- CONFIGURACIÓN DE INTERFAZ NEXION ---
st.set_page_config(page_title="Nexion Logistics", page_icon="🚚", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    .stButton>button { background-color: #00FFAA; color: #0B1114; font-weight: bold; width: 100%; border-radius: 10px; }
    h1, h2, h3 { color: #00FFAA; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE GITHUB ---
def descargar_matriz():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        datos = response.json()
        content = base64.b64decode(datos['content']).decode('utf-8')
        return pd.read_csv(StringIO(content)), datos['sha']
    return None, None

def actualizar_github(df, sha, mensaje):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False)
    encoded = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    payload = {"message": mensaje, "content": encoded, "sha": sha}
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code == 200

# --- LÓGICA DE LA APP ---
st.title("🛡️ NEXION SMART LOGISTICS")

# Usamos session_state para mantener las facturas cargadas en la pantalla
if 'en_ruta' not in st.session_state:
    st.session_state.en_ruta = []

menu = st.sidebar.radio("Menú de Operación", ["Carga de Unidad", "Entregas en Hotel"])

# --- MODULO 1: CARGA (3 FOTOS) ---
if menu == "Carga de Unidad":
    st.header("📦 Registro de Salida - JYPESA")
    
    with st.container():
        facturas_texto = st.text_area("Ingresa los Números de Pedido (uno por línea)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            foto1 = st.camera_input("Foto 1: Producto", key="f1")
        with col2:
            foto2 = st.camera_input("Foto 2: Unidad/Caja", key="f2")
        with col3:
            foto3 = st.camera_input("Foto 3: Estiba", key="f3")

        if st.button("INICIAR RUTA Y GUARDAR CARGA"):
            if facturas_texto and foto1 and foto2 and foto3:
                lista = [f.strip() for f in facturas_texto.split('\n') if f.strip()]
                st.session_state.en_ruta = lista
                st.success(f"✅ {len(lista)} pedidos listos para entrega. ¡Buen viaje!")
            else:
                st.warning("Amor, faltan las fotos de carga o los números de pedido.")

# --- MODULO 2: ENTREGAS (1 FOTO) ---
elif menu == "Entregas en Hotel":
    st.header("📍 Confirmación de Entrega")
    
    df, sha = descargar_matriz()
    
    if df is not None:
        # Solo mostramos los pedidos que están en la "lista de carga" y no tienen fecha de entrega
        pendientes = df[df['FECHA DE ENTREGA REAL'].isna()]
        
        if not pendientes.empty:
            opcion = st.selectbox("Selecciona el pedido a entregar:", pendientes['NOMBRE DEL CLIENTE'] + " - " + pendientes['NÚMERO DE PEDIDO'].astype(str))
            id_pedido = opcion.split(" - ")[1]
            
            st.info(f"Destino: {pendientes[pendientes['NÚMERO DE PEDIDO'].astype(str) == id_pedido]['DOMICILIO'].values[0]}")
            
            foto_entrega = st.camera_input("Foto de Evidencia (Recepción)", key="f_ent")
            comentario = st.text_input("Comentarios/Incidencias")

            if st.button("FINALIZAR ENTREGA"):
                if foto_entrega:
                    with st.spinner("Actualizando matriz en tiempo real..."):
                        ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Actualizamos los campos en el DataFrame
                        idx = df[df['NÚMERO DE PEDIDO'].astype(str) == id_pedido].index
                        df.loc[idx, 'FECHA DE ENTREGA REAL'] = ahora
                        df.loc[idx, 'TRIGGER'] = 'ENTREGADO'
                        df.loc[idx, 'INCIDENCIAS'] = comentario
                        
                        if actualizar_github(df, sha, f"Entrega Pedido {id_pedido}"):
                            st.success(f"✅ Pedido {id_pedido} actualizado en locales.csv")
                            st.balloons()
                            st.rerun()
                else:
                    st.warning("Amor, la foto de entrega es obligatoria para el KPI.")
        else:
            st.success("No hay pedidos pendientes en la matriz.")
    else:
        st.error("No se pudo cargar locales.csv. Revisa tus Tokens.")
