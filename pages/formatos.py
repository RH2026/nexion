import streamlit as st
import pandas as pd
import requests
import base64
from datetime import date
from io import BytesIO

# --- CONFIGURACIÓN Y PRECIOS ---
st.set_page_config(page_title="Captura de Muestras Nexión", layout="wide")

GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_PATH = "muestras.csv"
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

# --- FUNCIONES DE GITHUB ---
def obtener_datos_github():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        df = pd.read_csv(BytesIO(base64.b64decode(content['content'])))
        return df, content['sha']
    return pd.DataFrame(), None

def actualizar_github(df_final, sha, mensaje):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_string = df_final.to_csv(index=False)
    payload = {
        "message": mensaje,
        "content": base64.b64encode(csv_string.encode()).decode(),
        "sha": sha
    }
    r_put = requests.put(url, json=payload, headers=headers)
    return r_put.status_code == 200

# --- LÓGICA DE FOLIO AUTOMÁTICO ---
df_actual, sha_actual = obtener_datos_github()

if not df_actual.empty and "FOLIO" in df_actual.columns:
    try:
        # Intentamos obtener el último número y sumamos 1
        ultimo_folio = pd.to_numeric(df_actual["FOLIO"]).max()
        nuevo_folio = int(ultimo_folio) + 1
    except:
        nuevo_folio = 1
else:
    nuevo_folio = 1

# --- INTERFAZ DE USUARIO ---
st.title("📋 Formulario de Muestras - Nexión")

# Función para limpiar el formulario reiniciando el session_state
def limpiar_formulario():
    for key in st.session_state.keys():
        if key.startswith("input_") or key in ["hotel", "destino", "contacto", "solicito"]:
            st.session_state[key] = 0 if key.startswith("input_") else ""
    st.rerun()

with st.container():
    col1, col2, col3 = st.columns(3)
    # Folio deshabilitado porque es automático
    folio = col1.text_input("FOLIO (Automático)", value=str(nuevo_folio), disabled=True)
    fecha = col1.date_input("FECHA", value=date.today())
    hotel = col2.text_input("NOMBRE DEL HOTEL", key="hotel")
    destino = col2.text_input("DESTINO (CIUDAD)", key="destino")
    contacto = col3.text_input("CONTACTO", key="contacto")
    solicito = col3.text_input("SOLICITÓ", key="solicito")
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

st.sidebar.header("Resumen del Pedido")
st.sidebar.metric("Total Piezas", total_piezas)
st.sidebar.metric("Costo Total", f"${costo_total:,.2f}")

# --- ACCIONES ---
st.write("### Acciones de Registro")
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🚀 GUARDAR EN MATRIZ"):
        if not hotel:
            st.error("Por favor escribe el Nombre del Hotel.")
        else:
            registro = {
                "FOLIO": nuevo_folio, "FECHA": fecha.strftime("%Y-%m-%d"), 
                "NOMBRE DEL HOTEL": hotel, "DESTINO": destino,
                "CONTACTO": contacto, "SOLICITO": solicito, "PAQUETERIA": paqueteria,
                "CANTIDAD": total_piezas, "COSTO": costo_total
            }
            registro.update(cantidades)
            df_nuevo_registro = pd.DataFrame([registro])
            
            # Unimos con lo que ya existe en GitHub
            df_final_acumulado = pd.concat([df_actual, df_nuevo_registro], ignore_index=True)
            
            with st.spinner("Actualizando Matriz..."):
                if actualizar_github(df_final_acumulado, sha_actual, f"Registro Folio {nuevo_folio}"):
                    st.success(f"✅ ¡Folio {nuevo_folio} guardado correctamente!")
                    st.balloons()
                else:
                    st.error("Error al subir a GitHub.")

with c2:
    # DESCARGAR TODO EL ACUMULADO
    if not df_actual.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_actual.to_excel(writer, index=False, sheet_name='Base_Completa')
        
        st.download_button(
            label="📥 DESCARGAR TODA LA MATRIZ (EXCEL)",
            data=output.getvalue(),
            file_name=f"Matriz_Muestras_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with c3:
    if st.button("🧹 LIMPIAR FORMULARIO"):
        limpiar_formulario()





























































