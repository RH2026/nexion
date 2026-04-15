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
    .stMultiSelect span { color: black !important; }
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

# Descargamos la matriz al inicio para tener los datos frescos
df, sha = descargar_matriz()

if df is not None:
    menu = st.sidebar.radio("Menú de Operación", ["Carga de Unidad", "Entregas en Hotel"])

    # --- MODULO 1: CARGA (SELECCIÓN DESDE TABLA) ---
    if menu == "Carga de Unidad":
        st.header("📦 Registro de Salida - JYPESA")
        
        # Filtramos pedidos que NO han sido entregados ni cargados (basado en TRIGGER)
        disponibles = df[df['TRIGGER'].isna()]
        
        if not disponibles.empty:
            st.subheader("Selecciona los pedidos que vas a subir a la unidad:")
            
            # El chófer elige de una lista desplegable (Multi-selección)
            pedidos_seleccionados = st.multiselect(
                "Pedidos disponibles en locales.csv:",
                options=disponibles['NÚMERO DE PEDIDO'].tolist(),
                help="Selecciona todos los pedidos que estás cargando físicamente."
            )
            
            if pedidos_seleccionados:
                st.write(f"Has seleccionado {len(pedidos_seleccionados)} pedidos.")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    foto1 = st.camera_input("Foto 1: Producto", key="f1")
                with col2:
                    foto2 = st.camera_input("Foto 2: Unidad/Caja", key="f2")
                with col3:
                    foto3 = st.camera_input("Foto 3: Estiba", key="f3")

                if st.button("CONFIRMAR CARGA Y SALIDA"):
                    if foto1 and foto2 and foto3:
                        with st.spinner("Marcando pedidos como 'En Ruta'..."):
                            # Actualizamos el TRIGGER a 'EN RUTA' para que ya no aparezcan en carga
                            idx = df[df['NÚMERO DE PEDIDO'].isin(pedidos_seleccionados)].index
                            df.loc[idx, 'TRIGGER'] = 'EN RUTA'
                            
                            if actualizar_github(df, sha, f"Carga de {len(pedidos_seleccionados)} pedidos"):
                                st.success("¡Ruta iniciada! Los datos se actualizaron en GitHub.")
                                st.balloons()
                                st.rerun()
                    else:
                        st.warning("Amor, faltan las fotos de evidencia de la carga.")
        else:
            st.info("No hay pedidos nuevos pendientes de carga en locales.csv.")

    # --- MODULO 2: ENTREGAS (SOLO LO QUE ESTÁ 'EN RUTA') ---
    elif menu == "Entregas en Hotel":
        st.header("📍 Confirmación de Entrega")
        
        # Solo mostramos lo que el chófer ya marcó como 'EN RUTA'
        en_ruta = df[df['TRIGGER'] == 'EN RUTA']
        
        if not en_ruta.empty:
            opcion = st.selectbox("¿Qué pedido estás entregando?", en_ruta['NOMBRE DEL CLIENTE'] + " - " + en_ruta['NÚMERO DE PEDIDO'].astype(str))
            id_pedido = opcion.split(" - ")[1]
            
            datos = en_ruta[en_ruta['NÚMERO DE PEDIDO'].astype(str) == id_pedido].iloc[0]
            st.warning(f"Destino: {datos['DESTINO']} | Domicilio: {datos['DOMICILIO']}")
            
            foto_entrega = st.camera_input("Foto de Evidencia (Recepción)", key="f_ent")
            comentario = st.text_input("Comentarios/Incidencias")

            if st.button("FINALIZAR ENTREGA"):
                if foto_entrega:
                    with st.spinner("Guardando entrega final..."):
                        ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        idx = df[df['NÚMERO DE PEDIDO'].astype(str) == id_pedido].index
                        df.loc[idx, 'FECHA DE ENTREGA REAL'] = ahora
                        df.loc[idx, 'TRIGGER'] = 'ENTREGADO'
                        df.loc[idx, 'INCIDENCIAS'] = comentario
                        
                        if actualizar_github(df, sha, f"Entrega Final {id_pedido}"):
                            st.success(f"¡Pedido {id_pedido} entregado!")
                            st.rerun()
                else:
                    st.warning("Amor, la foto de entrega es obligatoria.")
        else:
            st.info("No tienes pedidos 'En Ruta'. Primero registra la carga.")

else:
    st.error("No pude leer locales.csv. Revisa el Token y el Repo en Secrets.")
