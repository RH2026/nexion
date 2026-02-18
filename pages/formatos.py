import streamlit as st
import pandas as pd
import requests
import base64
from datetime import date
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Nexión - Muestras", layout="wide")

GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_PATH = "muestras.csv"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

# Diccionario de precios (Simplificado para el código)
precios = {
    "Accesorios Ecologicos": 47.85, "Accesorios Lavarino": 47.85, "Dispensador Almond": 218.33,
    "Dispensador Biogena": 216.00, "Dispensador Cava": 230.58, "Dispensador Persa": 275.00,
    "Dispensador Botánicos L": 274.17, "Dispensador Dove": 125.00, "Dispensador Biogena 400ml": 184.87,
    "Kit Elements": 29.34, "Kit Almond": 33.83, "Kit Biogena": 48.95, "Kit Cava": 34.59,
    "Kit Persa": 58.02, "Kit Lavarino": 36.30, "Kit Botánicos": 29.34, "Llave Macnetica": 180.00,
    "Rack Dove": 0.00, "Rack JH Color Blanco de 2 pzas": 62.00, "Rack JH Color Blanco de 1 pzas": 50.00,
    "Soporte dob INOX": 679.00, "Soporte Ind INOX": 608.00
}

# --- FUNCIONES ---
def obtener_datos_github():
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = r.json()
            df = pd.read_csv(BytesIO(base64.b64decode(content['content'])))
            return df, content['sha']
    except:
        pass
    return pd.DataFrame(), None

def subir_a_github(df, sha, msg):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_string = df.to_csv(index=False)
    payload = {"message": msg, "content": base64.b64encode(csv_string.encode()).decode(), "sha": sha}
    return requests.put(url, json=payload, headers=headers).status_code == 200

# --- LÓGICA DE FOLIO ---
df_actual, sha_actual = obtener_datos_github()
nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1

# --- INTERFAZ ---
st.title("📦 Captura de Muestras Nexión")

# Usamos un st.form para agrupar todo y permitir un botón de reset nativo
with st.form("form_muestras", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    f_folio = col1.text_input("FOLIO", value=str(nuevo_folio), disabled=True)
    f_fecha = col1.date_input("FECHA", value=date.today())
    f_hotel = col2.text_input("NOMBRE DEL HOTEL")
    f_destino = col2.text_input("DESTINO")
    f_contacto = col3.text_input("CONTACTO")
    f_solicito = col3.text_input("SOLICITÓ")
    f_paqueteria = st.selectbox("FORMA DE ENVÍO", ["PAQUETERIA", "ENTREGA DIRECTA", "OTRO"])

    st.divider()
    
    # SIMPLIFICACIÓN: Selección múltiple para no llenar la pantalla
    st.subheader("Selección de Productos")
    seleccionados = st.multiselect("¿Qué productos incluye esta muestra?", list(precios.keys()))
    
    cantidades = {}
    if seleccionados:
        cols = st.columns(3)
        for i, p in enumerate(seleccionados):
            with cols[i % 3]:
                cantidades[p] = st.number_input(f"Cantidad: {p}", min_value=1, step=1)
    
    # Llenar con 0 los no seleccionados para la base de datos
    for p in precios.keys():
        if p not in cantidades:
            cantidades[p] = 0

    enviar = st.form_submit_button("🚀 GUARDAR REGISTRO")

# --- PROCESAMIENTO ---
if enviar:
    if not f_hotel:
        st.error("El nombre del hotel es obligatorio.")
    else:
        total_p = sum(cantidades.values())
        total_c = sum(cantidades[p] * precios[p] for p in precios.keys())
        
        nuevo_reg = {
            "FOLIO": nuevo_folio, "FECHA": f_fecha, "NOMBRE DEL HOTEL": f_hotel,
            "DESTINO": f_destino, "CONTACTO": f_contacto, "SOLICITO": f_solicito,
            "PAQUETERIA": f_paqueteria, "CANTIDAD": total_p, "COSTO": total_c
        }
        nuevo_reg.update(cantidades)
        
        df_final = pd.concat([df_actual, pd.DataFrame([nuevo_reg])], ignore_index=True)
        
        if subir_a_github(df_final, sha_actual, f"Folio {nuevo_folio}"):
            st.success(f"¡Folio {nuevo_folio} guardado! Los campos se han limpiado.")
            st.balloons()
            st.rerun()

# --- BOTÓN DE DESCARGA (Fuera del form) ---
st.divider()
if not df_actual.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_actual.to_excel(writer, index=False)
    st.download_button("📥 DESCARGAR MATRIZ COMPLETA", output.getvalue(), "Matriz_Muestras.xlsx")






























































