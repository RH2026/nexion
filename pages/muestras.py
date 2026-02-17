import os
import io
import zipfile
import pandas as pd
import streamlit as st
import time
import requests
import base64
from io import BytesIO
from datetime import datetime
import unicodedata
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

# --- 0. CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="Nexion Hub")

# --- CREDENCIALES GITHUB (Configura esto en Streamlit Secrets) ---
# Necesitas crear un Token en GitHub y ponerlo en Settings > Secrets del Cloud
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_OWNER = "RH2026"
REPO_NAME = "nexion"
FILE_PATH = "matriz_historial.csv"

# --- 1. FUNCIONES DE DATOS ---
@st.cache_data(ttl=10)
def obtener_matriz_github():
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}?nocache={int(time.time())}"
    try:
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except:
        return pd.DataFrame()

def guardar_en_github(df_nuevo):
    if not GITHUB_TOKEN:
        st.error("No hay Token de GitHub configurado.")
        return
    
    # 1. Traer lo que ya existe
    df_actual = obtener_matriz_github()
    
    # 2. Unir y quitar duplicados por la columna que sea el folio/factura
    # Asumimos que la columna se llama 'FACTURA' en la matriz de GitHub
    df_final = pd.concat([df_actual, df_nuevo]).drop_duplicates(subset=['FACTURA'], keep='last')
    
    # 3. Convertir a CSV
    csv_content = df_final.to_csv(index=False)
    
    # 4. Obtener el SHA del archivo actual para poder actualizarlo
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(api_url, headers=headers)
    
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    # 5. Subir
    payload = {
        "message": f"Update matriz {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(csv_content.encode()).decode(),
        "sha": sha
    }
    
    subida = requests.put(api_url, json=payload, headers=headers)
    if subida.status_code in [200, 201]:
        st.success("¡Datos guardados en GitHub exitosamente!")
    else:
        st.error(f"Error al subir: {subida.text}")

# --- 2. INTERFAZ ---
st.title("🚀 NEXION: CARGA Y CONTROL")

tab1, tab2 = st.tabs(["📥 CARGADOR DE FACTURACIÓN", "🧠 SMART ROUTING"])

with tab1:
    st.markdown("### Paso 1: Alimentar la Matriz")
    up_file = st.file_uploader("Subir Excel del RPA", type=["xlsx", "csv"])
    
    if up_file:
        df_rpa = pd.read_excel(up_file) if up_file.name.endswith('.xlsx') else pd.read_csv(up_file)
        df_rpa.columns = [str(c).strip().upper() for c in df_rpa.columns]
        
        # Detectar factura
        col_f = next((c for c in df_rpa.columns if 'FACTURA' in c or 'DOCNUM' in c or 'FOLIO' in c), df_rpa.columns[0])
        
        c1, c2 = st.columns(2)
        inicio = c1.number_input("Folio Desde:", value=int(df_rpa[col_f].min()))
        fin = c2.number_input("Folio Hasta:", value=int(df_rpa[col_f].max()))
        
        # Filtrar rango
        df_filtrado = df_rpa[(df_rpa[col_f] >= inicio) & (df_rpa[col_f] <= fin)].copy()
        
        # Selección manual
        df_filtrado.insert(0, "SELECCION", True)
        edited_cargas = st.data_editor(df_filtrado, hide_index=True, use_container_width=True)
        
        df_para_guardar = edited_cargas[edited_cargas["SELECCION"] == True].drop(columns=["SELECCION"])
        # Estandarizar nombre para la base de datos
        df_para_guardar = df_para_guardar.rename(columns={col_f: "FACTURA"})
        
        b1, b2 = st.columns(2)
        if b1.button("💾 GUARDAR NUEVOS FOLIOS EN GITHUB"):
            with st.spinner("Sincronizando con la nube..."):
                guardar_en_github(df_para_guardar)
        
        if b2.button("🖨️ VISTA PREVIA IMPRESIÓN (ÚNICOS)"):
            st.write("Folios listos para procesar:", df_para_guardar['FACTURA'].unique())
            st.dataframe(df_para_guardar.drop_duplicates(subset=['FACTURA']))

with tab2:
    st.markdown("### Paso 2: Análisis y Ruteo")
    if st.button("🔄 CARGAR DATOS DE GITHUB Y ANALIZAR"):
        matriz = obtener_matriz_github()
        if not matriz.empty:
            # Aquí vive tu motor de SMART ROUTING que ya tenemos
            # El sistema ya sabría qué hay de nuevo porque acabas de actualizar la matriz en el Tab 1
            st.session_state.df_analisis = matriz # O el resultado del motor
            st.write("Datos listos para Smart Routing")
            st.dataframe(matriz)
        else:
            st.warning("La matriz en GitHub está vacía o no se pudo leer.")


















































