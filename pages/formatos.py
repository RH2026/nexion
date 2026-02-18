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

# Diccionario de precios con los nombres EXACTOS de tus columnas de GitHub
precios = {
    "Accesorios Ecologicos": 47.85,
    "Accesorios Lavarino": 47.85,
    "Dispensador Almond ": 218.33,
    "Dispensador Biogena": 216.00,
    "Dispensador Cava": 230.58,
    "Dispensador Persa": 275.00,
    "Dispensador Botánicos L": 274.17,
    "Dispensador Dove": 125.00,
    "Dispensador Biogena 400ml": 184.87,
    "Kit Elements ": 29.34,
    "Kit Almond ": 33.83,
    "Kit Biogena": 48.95,
    "Kit Cava": 34.59,
    "Kit Persa": 58.02,
    "Kit Lavarino": 36.30,
    "Kit Botánicos": 29.34,
    "Llave Magnetica": 180.00,
    "Rack Dove": 0.00,
    "Rack JH  Color Blanco de 2 pzas": 62.00,
    "Rack JH  Color Blanco de 1 pzas": 50.00,
    "Soporte dob  INOX Cap lock": 679.00,
    "Soporte Ind  INOX Cap lock": 608.00
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

# --- LÓGICA DE DATOS ---
df_actual, sha_actual = obtener_datos_github()
nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1

# --- INTERFAZ ---
st.title("📦 Captura de Muestras Nexión")

# 1. Datos Generales
col1, col2, col3 = st.columns(3)
f_folio = col1.text_input("FOLIO", value=str(nuevo_folio), disabled=True)
f_fecha = col1.date_input("FECHA", value=date.today())
f_hotel = col2.text_input("NOMBRE DEL HOTEL", key="hotel")
f_destino = col2.text_input("DESTINO", key="destino")
f_contacto = col3.text_input("CONTACTO", key="contacto")
f_solicito = col3.text_input("SOLICITÓ", key="solicito")
f_paqueteria = st.selectbox("FORMA DE ENVÍO", ["PAQUETERIA", "ENTREGA DIRECTA", "OTRO"], key="envio")

st.divider()

# 2. Selección de Productos
st.subheader("Selección de Productos")
seleccionados = st.multiselect("Busca y selecciona los productos:", list(precios.keys()), key="multiselect_prod")

cantidades_input = {}
if seleccionados:
    st.info("Escribe las cantidades para cada producto seleccionado:")
    cols_q = st.columns(3)
    for i, p in enumerate(seleccionados):
        with cols_q[i % 3]:
            cantidades_input[p] = st.number_input(f"Cantidad: {p}", min_value=1, step=1, key=f"q_{p}")

st.divider()

# 3. Botones de Acción
if st.button("🚀 GUARDAR REGISTRO", use_container_width=True):
    if not f_hotel:
        st.error("Por favor, ingresa el nombre del hotel.")
    elif not seleccionados:
        st.error("Debes seleccionar al menos un producto.")
    else:
        # Preparamos el registro
        registro_completo = {
            "FOLIO": nuevo_folio,
            "FECHA": f_fecha.strftime("%Y-%m-%d"),
            "NOMBRE DEL HOTEL": f_hotel,
            "DESTINO": f_destino,
            "CONTACTO": f_contacto,
            "SOLICITO": f_solicito,
            "PAQUETERIA": f_paqueteria,
        }
        
        # Totales
        total_piezas = sum(cantidades_input.values())
        total_costo = sum(cantidades_input[p] * precios[p] for p in cantidades_input)
        
        registro_completo["CANTIDAD"] = total_piezas
        registro_completo["COSTO"] = total_costo
        
        # Mapeo de columnas de productos (0 si no se eligió)
        for producto in precios.keys():
            registro_completo[producto] = cantidades_input.get(producto, 0)
        
        df_nuevo = pd.DataFrame([registro_completo])
        df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
        
        with st.spinner("Guardando en la matriz de GitHub..."):
            if subir_a_github(df_final, sha_actual, f"Registro Folio {nuevo_folio}"):
                st.success(f"✅ ¡Folio {nuevo_folio} guardado exitosamente!")
                st.balloons()
                # El rerun limpia automáticamente todos los campos al reiniciar la app
                st.rerun()
            else:
                st.error("Error al conectar con GitHub.")

# --- SECCIÓN DE REPORTE Y DESCARGA ---
st.divider()
if not df_actual.empty:
    with st.expander("📊 VER REGISTROS ACUMULADOS", expanded=False):
        st.dataframe(df_actual, use_container_width=True)
        
        st.write("---")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_actual.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 DESCARGAR MATRIZ COMPLETA (EXCEL)",
            data=output.getvalue(),
            file_name=f"Matriz_Muestras_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

































































