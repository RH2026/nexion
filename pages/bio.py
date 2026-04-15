import streamlit as st
import pandas as pd
import datetime
import requests
import base64
from io import StringIO
# Este es el refuerzo para la cámara trasera
from camera_input_live import camera_input_live

# --- CONFIGURACIÓN DE ACCESO (PROBADO CON TUS TOKENS) ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = "RH2026/nexion"
FILE_PATH = "locales.csv"

# --- CONFIGURACIÓN ESTÉTICA SILICON VALLEY ---
st.set_page_config(page_title="Nexion Smart Logistics", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    .stButton>button { 
        background-color: #00FFAA; 
        color: #0B1114; 
        font-weight: bold; 
        border-radius: 15px; 
        border: none;
        height: 3em;
    }
    .stSelectbox label, .stMultiSelect label { color: #00FFAA !important; font-size: 1.2rem; }
    div[data-baseweb="select"] { background-color: #1A2226; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES CORE (GITHUB API) ---
def descargar_matriz():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
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

# --- INTERFAZ PRINCIPAL ---
st.title("🛡️ NEXION SMART LOGISTICS")
st.subheader("Control de Última Milla - JYPESA")

df, sha = descargar_matriz()

if df is not None:
    menu = st.sidebar.radio("FLUJO DE TRABAJO", ["🚀 SALIDA DE ALMACÉN", "📍 ENTREGA EN DESTINO"])

    # --- MÓDULO 1: CARGA (Fuerza la selección desde el CSV) ---
    if menu == "🚀 SALIDA DE ALMACÉN":
        st.header("Registro de Carga")
        # Solo lo que no tiene TRIGGER (está limpio)
        disponibles = df[df['TRIGGER'].isna() | (df['TRIGGER'] == '')]
        
        if not disponibles.empty:
            pedidos = st.multiselect("Pedidos a cargar en unidad:", options=disponibles['NÚMERO DE PEDIDO'].unique())
            
            if pedidos:
                st.warning("📸 EVIDENCIA DE CARGA (Cámara Trasera Forzada)")
                col1, col2, col3 = st.columns(3)
                
               with col1:
                    f1 = st.camera_input("Foto 1: Producto", key="c1")
                with col2:
                    f2 = st.camera_input("Foto 2: Unidad", key="c2")
                with col3:
                    f3 = st.camera_input("Foto 3: Estiba", key="c3")

                if st.button("CONFIRMAR SALIDA DE JYPESA"):
                    if f1 and f2 and f3:
                        with st.spinner("Sincronizando con Nexion Cloud..."):
                            idx = df[df['NÚMERO DE PEDIDO'].isin(pedidos)].index
                            df.loc[idx, 'TRIGGER'] = 'EN RUTA'
                            df.loc[idx, 'FECHA DE ENVÍO'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                            
                            if actualizar_github(df, sha, f"Carga Pedidos: {pedidos}"):
                                st.success("¡Ruta iniciada! La matriz se actualizó.")
                                st.rerun()
                    else:
                        st.error("Amor, las 3 fotos de carga son obligatorias.")
        else:
            st.info("No hay pedidos nuevos en locales.csv listos para cargar.")

    # --- MÓDULO 2: ENTREGA (Evidencia Final) ---
    elif menu == "📍 ENTREGA EN DESTINO":
        st.header("Evidencia de Entrega")
        # Solo lo que el chófer ya marcó como 'EN RUTA'
        en_ruta = df[df['TRIGGER'] == 'EN RUTA']
        
        if not en_ruta.empty:
            seleccion = st.selectbox("Selecciona Pedido a entregar:", 
                                     en_ruta.apply(lambda x: f"{x['NÚMERO DE PEDIDO']} - {x['NOMBRE DEL CLIENTE']}", axis=1))
            id_p = seleccion.split(" - ")[0]
            info = en_ruta[en_ruta['NÚMERO DE PEDIDO'].astype(str) == id_p].iloc[0]
            
            st.info(f"🏠 **Domicilio:** {info['DOMICILIO']} \n\n 🏨 **Destino:** {info['DESTINO']}")
            
            st.write("📸 **FOTO DE RECEPCIÓN (Cámara Trasera)**")
            f_entrega = camera_input_live(facing_mode="environment", key="ce")
            
            obs = st.text_area("Comentarios o Incidencias:")

            if st.button("FINALIZAR ENTREGA (KPI 24H)"):
                if f_entrega:
                    with st.spinner("Guardando evidencia final..."):
                        ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        idx_f = df[df['NÚMERO DE PEDIDO'].astype(str) == id_p].index
                        
                        df.loc[idx_f, 'FECHA DE ENTREGA REAL'] = ahora
                        df.loc[idx_f, 'TRIGGER'] = 'ENTREGADO'
                        df.loc[idx_f, 'INCIDENCIAS'] = obs
                        
                        if actualizar_github(df, sha, f"Entrega Final: {id_p}"):
                            st.success(f"¡Pedido {id_p} entregado y registrado!")
                            st.balloons()
                            st.rerun()
                else:
                    st.error("Amor, falta la foto de entrega para validar el KPI.")
        else:
            st.info("No hay pedidos 'En Ruta'. Registra la carga primero.")

else:
    st.error("Error crítico: No se pudo leer locales.csv. Revisa tus GitHub Secrets.")
