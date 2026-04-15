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

# Estilo Nexion Silicon Valley
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
        # Parche de tipos de datos
        for col in ['TRIGGER', 'FECHA DE ENVÍO', 'FECHA DE ENTREGA REAL', 'INCIDENCIAS', 'NÚMERO DE PEDIDO']:
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

# --- INICIO DE LA APP ---
st.title("🛡️ NEXION SMART LOGISTICS")

df, sha = descargar_matriz()

if df is not None:
    # ---------------------------------------------------------
    # SECCIÓN 1: CARGA DE UNIDAD (SALIDA DE JYPESA)
    # ---------------------------------------------------------
    st.header("🚀 1. Salida de Almacén (Carga)")
    disponibles = df[~df['TRIGGER'].isin(['EN RUTA', 'ENTREGADO'])]
    
    if not disponibles.empty:
        pedidos_sel = st.multiselect("Pedidos listos para subir a unidad:", options=disponibles['NÚMERO DE PEDIDO'].unique(), key="ms_carga")
        
        if pedidos_sel:
            st.info("📸 Toma las 3 fotos de evidencia para iniciar ruta")
            f1 = st.camera_input("Foto 1: Producto", key="c1")
            if f1:
                f2 = st.camera_input("Foto 2: Unidad", key="c2")
                if f2:
                    f3 = st.camera_input("Foto 3: Estiba", key="c3")
                    if f3:
                        if st.button("CONFIRMAR CARGA Y SALIDA"):
                            with st.spinner("Actualizando Matriz..."):
                                p_str = [str(p) for p in pedidos_sel]
                                idx = df[df['NÚMERO DE PEDIDO'].astype(str).isin(p_str)].index
                                for i in idx:
                                    df.loc[i, 'TRIGGER'] = 'EN RUTA'
                                    df.loc[i, 'FECHA DE ENVÍO'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                                if actualizar_github(df, sha, f"Carga: {pedidos_sel}"):
                                    st.success("✅ ¡Ruta Iniciada!")
                                    st.rerun()
    else:
        st.write("✅ No hay pedidos pendientes de carga.")

    st.markdown("---") # Separador visual

    # ---------------------------------------------------------
    # SECCIÓN 2: ENTREGA EN DESTINO (EL CHÓFER EN RUTA)
    # ---------------------------------------------------------
    st.header("📍 2. Entrega en Destino")
    en_ruta = df[df['TRIGGER'] == 'EN RUTA']
    
    if not en_ruta.empty:
        st.subheader("Selecciona el pedido que estás entregando ahora:")
        seleccion = st.selectbox("Pedidos en tránsito:", 
                                 en_ruta.apply(lambda x: f"{x['NÚMERO DE PEDIDO']} - {x['NOMBRE DEL CLIENTE']}", axis=1),
                                 key="sb_entrega")
        
        id_p = seleccion.split(" - ")[0]
        datos = en_ruta[en_ruta['NÚMERO DE PEDIDO'].astype(str) == str(id_p)].iloc[0]
        
        st.warning(f"🏨 **Destino:** {datos['DESTINO']} \n\n🏠 **Domicilio:** {datos['DOMICILIO']}")
        
        f_ent = st.camera_input("Foto de Recepción (Evidencia Final)", key="ce")
        obs = st.text_input("Comentarios / Incidencias:", key="ti_obs")

        if st.button("FINALIZAR ENTREGA (KPI 24H)"):
            if f_ent:
                with st.spinner("Guardando evidencia final..."):
                    idx_f = df[df['NÚMERO DE PEDIDO'].astype(str) == str(id_p)].index
                    df.loc[idx_f, 'FECHA DE ENTREGA REAL'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    df.loc[idx_f, 'TRIGGER'] = 'ENTREGADO'
                    df.loc[idx_f, 'INCIDENCIAS'] = obs
                    
                    if actualizar_github(df, sha, f"Entrega: {id_p}"):
                        st.success(f"✅ ¡Pedido {id_p} Entregado!")
                        st.balloons()
                        st.rerun()
            else:
                st.error("⚠️ Amor, la foto es obligatoria para cerrar el proceso.")
    else:
        st.write("💤 No hay pedidos en ruta actualmente.")

else:
    st.error("Error de conexión con locales.csv")
