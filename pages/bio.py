import streamlit as st
import pandas as pd
import datetime
import requests
import base64
from io import StringIO

# --- CONFIGURACIÓN DE ACCESO ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = "RH2026/nexion"
FILE_PATH = "locales.csv"

st.set_page_config(page_title="Nexion Logistics", page_icon="🛡️", layout="wide")

# Estilo Nexion Dark
st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    .stButton>button { background-color: #00FFAA; color: #0B1114; font-weight: bold; border-radius: 10px; height: 3em; }
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
        
        # --- PARCHE DE FUERZA BRUTA PARA TIPOS DE DATOS ---
        # Obligamos a estas columnas a ser TEXTO para que no truene al escribir
        columnas_criticas = ['TRIGGER', 'FECHA DE ENVÍO', 'FECHA DE ENTREGA REAL', 'INCIDENCIAS', 'NÚMERO DE PEDIDO']
        for col in columnas_criticas:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN'], '')
        
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

# --- APP PRINCIPAL ---
st.title("🛡️ NEXION SMART LOGISTICS")

df, sha = descargar_matriz()

if df is not None:
    menu = st.sidebar.radio("FLUJO", ["🚀 CARGA", "📍 ENTREGA"])

    if menu == "🚀 CARGA":
        st.header("Salida de Almacén")
        # Filtramos lo que no tiene "EN RUTA" o "ENTREGADO"
        disponibles = df[~df['TRIGGER'].isin(['EN RUTA', 'ENTREGADO'])]
        
        if not disponibles.empty:
            pedidos_sel = st.multiselect("Pedidos a cargar:", options=disponibles['NÚMERO DE PEDIDO'].unique())
            
            if pedidos_sel:
                # FLUJO EN CASCADA PARA EVITAR CIERRE DE CÁMARA
                f1 = st.camera_input("1. Foto Producto", key="c1")
                if f1:
                    st.success("✅ Foto 1 lista")
                    f2 = st.camera_input("2. Foto Unidad", key="c2")
                    if f2:
                        st.success("✅ Foto 2 lista")
                        f3 = st.camera_input("3. Foto Estiba", key="c3")
                        if f3:
                            st.success("✅ Foto 3 lista")
                            if st.button("CONFIRMAR SALIDA"):
                                with st.spinner("Sincronizando..."):
                                    # Convertimos pedidos_sel a string para comparar bien
                                    pedidos_str = [str(p) for p in pedidos_sel]
                                    idx = df[df['NÚMERO DE PEDIDO'].astype(str).isin(pedidos_str)].index
                                    
                                    df.at[idx[0], 'TRIGGER'] = 'EN RUTA' # Usamos .at o aseguramos conversión
                                    # Aplicamos a todos los seleccionados
                                    for i in idx:
                                        df.loc[i, 'TRIGGER'] = 'EN RUTA'
                                        df.loc[i, 'FECHA DE ENVÍO'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                                    
                                    if actualizar_github(df, sha, f"Carga: {pedidos_sel}"):
                                        st.success("Ruta iniciada")
                                        st.rerun()
        else:
            st.info("No hay pedidos pendientes.")

    elif menu == "📍 ENTREGA":
        st.header("Confirmación de Entrega")
        en_ruta = df[df['TRIGGER'] == 'EN RUTA']
        
        if not en_ruta.empty:
            seleccion = st.selectbox("Pedido:", en_ruta.apply(lambda x: f"{x['NÚMERO DE PEDIDO']} - {x['NOMBRE DEL CLIENTE']}", axis=1))
            id_p = seleccion.split(" - ")[0]
            
            f_ent = st.camera_input("Foto Recepción", key="ce")
            obs = st.text_input("Incidencias:")

            if st.button("FINALIZAR"):
                if f_ent:
                    with st.spinner("Guardando..."):
                        idx_f = df[df['NÚMERO DE PEDIDO'].astype(str) == str(id_p)].index
                        df.loc[idx_f, 'FECHA DE ENTREGA REAL'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        df.loc[idx_f, 'TRIGGER'] = 'ENTREGADO'
                        df.loc[idx_f, 'INCIDENCIAS'] = obs
                        
                        if actualizar_github(df, sha, f"Entrega: {id_p}"):
                            st.success("Entregado")
                            st.balloons()
                            st.rerun()
                else:
                    st.error("Falta foto")
else:
    st.error("Revisa tus Secrets de GitHub, amor.")
