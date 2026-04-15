import streamlit as st
import pandas as pd
import datetime
import requests
import base64
import time
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
    timestamp = int(time.time())
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?t={timestamp}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Cache-Control": "no-cache"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        datos = response.json()
        content = base64.b64decode(datos['content']).decode('utf-8')
        df = pd.read_csv(StringIO(content))
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace(['nan', 'None', 'NaN', 'null'], '')
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

if st.button("🔄 RECARGAR MATRIZ (FORCE UPDATE)"):
    st.rerun()

df, sha = descargar_matriz()

if df is not None:
    # --- 1. SECCIÓN DE CARGA ---
    st.header("🚀 1. Salida de Almacén (Carga)")
    disponibles = df[~df['TRIGGER'].isin(['EN RUTA', 'ENTREGADO'])]
    
    if not disponibles.empty:
        pedidos_sel = st.multiselect("Pedidos pendientes:", options=disponibles['NÚMERO DE PEDIDO'].unique())
        
        if pedidos_sel:
            # Aquí usamos el primer pedido seleccionado para refrescar la cámara si cambian de selección
            ref_key = str(pedidos_sel[0])
            f1 = st.camera_input("Foto 1: Producto", key=f"c1_{ref_key}")
            if f1:
                f2 = st.camera_input("Foto 2: Unidad", key=f"c2_{ref_key}")
                if f2:
                    f3 = st.camera_input("Foto 3: Estiba", key=f"c3_{ref_key}")
                    if f3:
                        if st.button("CONFIRMAR SALIDA"):
                            with st.spinner("Actualizando..."):
                                for p in pedidos_sel:
                                    idx = df[df['NÚMERO DE PEDIDO'] == str(p)].index
                                    df.loc[idx, 'TRIGGER'] = 'EN RUTA'
                                    df.loc[idx, 'FECHA DE ENVÍO'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                                if actualizar_github(df, sha, f"Carga: {pedidos_sel}"):
                                    st.success("✅ Ruta iniciada.")
                                    st.rerun()
    else:
        st.write("✅ Todo el material ha sido cargado.")

    st.markdown("---")

    # --- 2. SECCIÓN DE ENTREGA ---
    st.header("📍 2. Entrega en Destino")
    en_ruta = df[df['TRIGGER'] == 'EN RUTA']
    
    if not en_ruta.empty:
        opciones = en_ruta.apply(lambda x: f"{x['NÚMERO DE PEDIDO']} | {x['NOMBRE DEL CLIENTE']}", axis=1)
        seleccion = st.selectbox("Pedido a entregar:", opciones)
        id_p = seleccion.split(" | ")[0].strip()
        
        datos_p = en_ruta[en_ruta['NÚMERO DE PEDIDO'] == id_p].iloc[0]
        st.warning(f"🏨 **{datos_p['DESTINO']}**\n\n🏠 {datos_p['DOMICILIO']}")
        
        # --- EL TRUCO ESTÁ AQUÍ ---
        # Al poner {id_p} en la key, la cámara se RESETEA cada que cambias de pedido en el selectbox
        f_ent = st.camera_input("Evidencia Final", key=f"ce_{id_p}")
        
        obs = st.text_input("Notas:", key=f"obs_{id_p}")

        if st.button("FINALIZAR ENTREGA"):
            if f_ent:
                with st.spinner("Guardando..."):
                    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    idx_f = df[(df['NÚMERO DE PEDIDO'] == id_p) & (df['TRIGGER'] == 'EN RUTA')].index
                    if not idx_f.empty:
                        df.loc[idx_f[0], 'FECHA DE ENTREGA REAL'] = ahora
                        df.loc[idx_f[0], 'TRIGGER'] = 'ENTREGADO'
                        df.loc[idx_f[0], 'INCIDENCIAS'] = obs
                        if actualizar_github(df, sha, f"Entrega: {id_p}"):
                            st.success("✅ Entregado.")
                            st.balloons()
                            st.rerun()
            else:
                st.error("⚠️ La foto es obligatoria.")
    else:
        st.write("💤 No hay pedidos viajando.")
else:
    st.error("Error: No se encontró locales.csv")
