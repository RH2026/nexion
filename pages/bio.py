import streamlit as st
import pandas as pd
import datetime
import requests
import base64
from io import StringIO

# --- CONFIGURACIÓN GITHUB ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = "RH2026/nexion"
FILE_PATH = "locales.csv"

st.set_page_config(page_title="Nexion Logistics", page_icon="🛡️", layout="wide")

# Estilo Nexion
st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    .stButton>button { background-color: #00FFAA; color: #0B1114; font-weight: bold; border-radius: 10px; height: 3.5em; width: 100%; }
    .stSelectbox label, .stMultiSelect label { color: #00FFAA !important; font-weight: bold; }
    hr { border: 1px solid #00FFAA; }
    </style>
    """, unsafe_allow_html=True)

def descargar_matriz():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        datos = response.json()
        content = base64.b64decode(datos['content']).decode('utf-8')
        df = pd.read_csv(StringIO(content))
        # Forzamos columnas a texto y limpiamos espacios para evitar errores de coincidencia
        for col in ['TRIGGER', 'FECHA DE ENVÍO', 'FECHA DE ENTREGA REAL', 'INCIDENCIAS', 'NÚMERO DE PEDIDO']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().replace(['nan', 'None', 'NaN'], '')
        return df, datos['sha']
    return None, None

def actualizar_github(df, sha, mensaje):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False)
    encoded = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    payload = {"message": mensaje, "content": encoded, "sha": sha}
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code == 200

# --- INICIO DE LA APP ---
st.title("🛡️ NEXION SMART LOGISTICS")

df, sha = descargar_matriz()

if df is not None:
    # --- SECCIÓN 1: CARGA ---
    st.header("🚀 1. Salida de Almacén (Carga)")
    disponibles = df[df['TRIGGER'] == ''] # Solo los que están vacíos de verdad
    
    if not disponibles.empty:
        pedidos_sel = st.multiselect("Pedidos para cargar:", options=disponibles['NÚMERO DE PEDIDO'].unique(), key="ms_carga")
        
        if pedidos_sel:
            f1 = st.camera_input("Foto 1: Producto", key="c1")
            if f1:
                f2 = st.camera_input("Foto 2: Unidad", key="c2")
                if f2:
                    f3 = st.camera_input("Foto 3: Estiba", key="c3")
                    if f3:
                        if st.button("CONFIRMAR CARGA"):
                            with st.spinner("Sincronizando..."):
                                # ACTUALIZACIÓN SEGURA POR FILA
                                for p in pedidos_sel:
                                    idx = df[df['NÚMERO DE PEDIDO'] == str(p)].index
                                    df.loc[idx, 'TRIGGER'] = 'EN RUTA'
                                    df.loc[idx, 'FECHA DE ENVÍO'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                                
                                if actualizar_github(df, sha, f"Carga: {pedidos_sel}"):
                                    st.success("✅ ¡Ruta Iniciada!")
                                    st.rerun()
    else:
        st.write("✅ Todo cargado.")

    st.markdown("---")

    # --- SECCIÓN 2: ENTREGA ---
    st.header("📍 2. Entrega en Destino")
    en_ruta = df[df['TRIGGER'] == 'EN RUTA']
    
    if not en_ruta.empty:
        # Aquí es donde estaba el peligro, vamos a ser MUY específicos
        seleccion = st.selectbox("Pedido en tránsito:", 
                                 en_ruta.apply(lambda x: f"{x['NÚMERO DE PEDIDO']} | {x['NOMBRE DEL CLIENTE']}", axis=1),
                                 key="sb_entrega")
        
        id_p = seleccion.split(" | ")[0].strip() # Limpiamos espacios
        
        f_ent = st.camera_input("Foto Recepción", key="ce")
        obs = st.text_input("Comentarios:", key="ti_obs")

        if st.button("FINALIZAR ENTREGA"):
            if f_ent:
                with st.spinner("Guardando..."):
                    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # BUSQUEDA QUIRÚRGICA: Solo donde el pedido coincida Y el estado sea EN RUTA
                    idx_f = df[(df['NÚMERO DE PEDIDO'] == str(id_p)) & (df['TRIGGER'] == 'EN RUTA')].index
                    
                    if not idx_f.empty:
                        df.loc[idx_f[0], 'FECHA DE ENTREGA REAL'] = ahora
                        df.loc[idx_f[0], 'TRIGGER'] = 'ENTREGADO'
                        df.loc[idx_f[0], 'INCIDENCIAS'] = obs
                        
                        if actualizar_github(df, sha, f"Entrega: {id_p}"):
                            st.success(f"✅ Pedido {id_p} registrado.")
                            st.balloons()
                            st.rerun()
                    else:
                        st.error("No encontré el pedido en la base de datos.")
            else:
                st.error("⚠️ La foto es obligatoria.")
    else:
        st.write("💤 No hay nada 'En Ruta'.")

else:
    st.error("Error de conexión.")
