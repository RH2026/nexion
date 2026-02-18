import streamlit as st
import pandas as pd
import requests
import base64
from datetime import date
from io import BytesIO

# --- CONFIGURACIÓN Y PRECIOS ---
st.set_page_config(page_title="Captura de Muestras Nexión", layout="wide")

# URL de tu archivo y datos de API
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_PATH = "muestras.csv"
# NOTA: El token debe manejarse como un "Secret" en Streamlit Cloud por seguridad
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

precios = {
    "Accesorios Ecologicos": 47.85, "Accesorios Lavarino": 47.85, "Dispensador Almond": 218.33,
    "Dispensador Biogena": 216.00, "Dispensador Cava": 230.58, "Dispensador Persa": 275.00,
    "Dispensador Botánicos L": 274.17, "Dispensador Dove": 125.00, "Dispensador Biogena 400ml": 184.87,
    "Kit Elements": 29.34, "Kit Almond": 33.83, "Kit Biogena": 48.95, "Kit Cava": 34.59,
    "Kit Persa": 58.02, "Kit Lavarino": 36.30, "Kit Botánicos": 29.34, "Llave Macnetica": 180.00,
    "Rack Dove": 0.00, "Rack JH Color Blanco de 2 pzas": 62.00, "Rack JH Color Blanco de 1 pzas": 50.00,
    "Soporte dob INOX": 679.00, "Soporte Ind INOX": 608.00
}

# --- INTERFAZ DE USUARIO ---
st.title("📋 Formulario de Muestras - Nexión")

with st.container():
    col1, col2, col3 = st.columns(3)
    folio = col1.text_input("FOLIO")
    fecha = col1.date_input("FECHA", value=date.today())
    hotel = col2.text_input("NOMBRE DEL HOTEL")
    destino = col2.text_input("DESTINO (CIUDAD)")
    contacto = col3.text_input("CONTACTO")
    solicito = col3.text_input("SOLICITÓ")
    paqueteria = st.selectbox("FORMA DE ENVÍO", ["PAQUETERIA", "ENTREGA DIRECTA", "OTRO"])

st.divider()

st.subheader("Cantidades por Producto")
cantidades = {}
cols = st.columns(3)
items = list(precios.keys())

for i, prod in enumerate(items):
    with cols[i % 3]:
        cantidades[prod] = st.number_input(f"{prod}", min_value=0, step=1, key=f"input_{prod}")

# --- CÁLCULOS ---
total_piezas = sum(cantidades.values())
costo_total = sum(cantidades[p] * precios[p] for p in items)

# Sidebar con resumen
st.sidebar.header("Resumen del Pedido")
st.sidebar.metric("Total Piezas", total_piezas)
st.sidebar.metric("Costo Total", f"${costo_total:,.2f}")

# --- LÓGICA DE GITHUB ---
def actualizar_github(nueva_fila_df):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # 1. Obtener el archivo actual y su SHA
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        csv_actual = pd.read_csv(BytesIO(base64.b64decode(content['content'])))
        sha = content['sha']
        
        # 2. Concatenar nueva fila
        df_final = pd.concat([csv_actual, nueva_fila_df], ignore_index=True)
        csv_string = df_final.to_csv(index=False)
        
        # 3. Subir de nuevo a GitHub
        payload = {
            "message": f"Nuevo registro folio: {folio}",
            "content": base64.b64encode(csv_string.encode()).decode(),
            "sha": sha
        }
        r_put = requests.put(url, json=payload, headers=headers)
        return r_put.status_code == 200
    return False

# --- ACCIONES ---
if st.button("🚀 GUARDAR EN MATRIZ Y GENERAR EXCEL"):
    if not folio or not hotel:
        st.error("Por favor llena el Folio y Nombre del Hotel.")
    else:
        # Preparar dataframe
        registro = {
            "FOLIO": folio, "FECHA": fecha, "NOMBRE DEL HOTEL": hotel, "DESTINO": destino,
            "CONTACTO": contacto, "SOLICITO": solicito, "PAQUETERIA": paqueteria,
            "CANTIDAD": total_piezas, "COSTO": costo_total
        }
        registro.update(cantidades)
        df_nuevo = pd.DataFrame([registro])

        # Guardar en GitHub
        with st.spinner("Subiendo a GitHub..."):
            if actualizar_github(df_nuevo):
                st.success("✅ ¡Guardado en la matriz de GitHub con éxito!")
                
                # Botón de descarga de Excel una vez guardado
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_nuevo.to_excel(writer, index=False)
                st.download_button("📥 Descargar este registro en Excel", output.getvalue(), f"Muestra_{folio}.xlsx")
            else:
                st.error("Hubo un error al conectar con GitHub. Revisa tu Token.")




























































