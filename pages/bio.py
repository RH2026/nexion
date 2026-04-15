import streamlit as st
import pandas as pd
import datetime
import requests
import base64
from io import StringIO

# --- CONFIGURACIÓN DE ACCESO (TU REPO RH2026/NEXION) ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = "RH2026/nexion"
FILE_PATH = "locales.csv"

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Nexion Smart Logistics", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    .stButton>button { 
        background-color: #00FFAA; 
        color: #0B1114; 
        font-weight: bold; 
        border-radius: 10px; 
        border: none;
        height: 3em;
    }
    .stSelectbox label, .stMultiSelect label { color: #00FFAA !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE GITHUB ---
def descargar_matriz():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
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

# --- LÓGICA PRINCIPAL ---
st.title("🛡️ NEXION SMART LOGISTICS")

df, sha = descargar_matriz()

if df is not None:
    menu = st.sidebar.radio("FLUJO DE TRABAJO", ["🚀 CARGA DE UNIDAD", "📍 ENTREGA EN DESTINO"])

    # --- SUSTITUYE EL BLOQUE DE CARGA DE UNIDAD POR ESTE ---

    if menu == "🚀 CARGA DE UNIDAD":
        st.header("Registro de Carga - JYPESA")
        
        disponibles = df[df['TRIGGER'].isna() | (df['TRIGGER'] == '')]
        
        if not disponibles.empty:
            pedidos_sel = st.multiselect("Selecciona los pedidos a cargar:", options=disponibles['NÚMERO DE PEDIDO'].unique())
            
            if pedidos_sel:
                st.divider()
                # Creamos contenedores para que no se amontonen
                
                # FOTO 1
                st.subheader("1. Evidencia de Producto")
                f1 = st.camera_input("Capturar Producto", key="c1")
                
                # Solo si ya tomó la foto 1, mostramos la 2
                if f1:
                    st.success("✅ Foto de Producto capturada")
                    st.subheader("2. Evidencia de Unidad")
                    f2 = st.camera_input("Capturar Unidad/Caja", key="c2")
                    
                    # Solo si ya tomó la foto 2, mostramos la 3
                    if f2:
                        st.success("✅ Foto de Unidad capturada")
                        st.subheader("3. Evidencia de Estiba")
                        f3 = st.camera_input("Capturar Estiba Final", key="c3")
                        
                        if f3:
                            st.success("✅ Foto de Estiba capturada")
                            if st.button("CONFIRMAR CARGA Y SALIDA"):
                                with st.spinner("Sincronizando con Nexion..."):
                                    idx = df[df['NÚMERO DE PEDIDO'].isin(pedidos_sel)].index
                                    df.loc[idx, 'TRIGGER'] = 'EN RUTA'
                                    df.loc[idx, 'FECHA DE ENVÍO'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                                    
                                    if actualizar_github(df, sha, f"Carga Pedidos: {pedidos_sel}"):
                                        st.success("¡Ruta Iniciada con éxito!")
                                        st.balloons()
                                        st.rerun()
                else:
                    st.info("📸 Por favor, toma la primera foto para continuar.")
        else:
            st.info("No hay pedidos nuevos pendientes de carga.")

    # --- MÓDULO 2: ENTREGA ---
    elif menu == "📍 ENTREGA EN DESTINO":
        st.header("Confirmación de Entrega")
        
        # Solo lo que está 'EN RUTA'
        en_ruta = df[df['TRIGGER'] == 'EN RUTA']
        
        if not en_ruta.empty:
            seleccion = st.selectbox("Selecciona Pedido:", en_ruta.apply(lambda x: f"{x['NÚMERO DE PEDIDO']} - {x['NOMBRE DEL CLIENTE']}", axis=1))
            id_p = seleccion.split(" - ")[0]
            info = en_ruta[en_ruta['NÚMERO DE PEDIDO'].astype(str) == id_p].iloc[0]
            
            st.info(f"📍 **Destino:** {info['DESTINO']}\n\n🏠 **Domicilio:** {info['DOMICILIO']}")
            
            f_entrega = st.camera_input("Foto de Evidencia (Recepción)", key="ce")
            obs = st.text_area("Comentarios:")

            if st.button("FINALIZAR ENTREGA"):
                if f_entrega:
                    with st.spinner("Guardando en locales.csv..."):
                        ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        idx_f = df[df['NÚMERO DE PEDIDO'].astype(str) == id_p].index
                        
                        df.loc[idx_f, 'FECHA DE ENTREGA REAL'] = ahora
                        df.loc[idx_f, 'TRIGGER'] = 'ENTREGADO'
                        df.loc[idx_f, 'INCIDENCIAS'] = obs
                        
                        if actualizar_github(df, sha, f"Entrega Final: {id_p}"):
                            st.success(f"¡Pedido {id_p} entregado!")
                            st.balloons()
                            st.rerun()
                else:
                    st.error("Amor, la foto de entrega es obligatoria.")
        else:
            st.info("No hay pedidos en ruta actualmente.")
else:
    st.error("No pude conectar con locales.csv. Revisa tus GitHub Secrets.")
