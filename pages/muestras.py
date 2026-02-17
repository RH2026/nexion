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

# CREDENCIALES (Asegúrate de tener GITHUB_TOKEN en Settings > Secrets de Streamlit)
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_OWNER = "RH2026"
REPO_NAME = "nexion"
FILE_PATH = "facturacion.csv"

# --- 1. FUNCIONES CORE ---
def obtener_matriz_github():
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}?nocache={int(time.time())}"
    try:
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except:
        return pd.DataFrame()

def guardar_en_github(df_final):
    if not GITHUB_TOKEN:
        st.error("Falta el GITHUB_TOKEN en Secrets.")
        return
    csv_content = df_final.to_csv(index=False)
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(api_url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    payload = {
        "message": f"Update Facturación {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(csv_content.encode()).decode(),
        "sha": sha
    }
    subida = requests.put(api_url, json=payload, headers=headers)
    if subida.status_code in [200, 201]:
        st.success("¡Datos cargados exitosamente a GitHub!")
    else:
        st.error(f"Error al subir: {subida.text}")

def limpiar_texto(texto):
    if pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper()
    texto = re.sub(r'[^A-Z0-9\s]', ' ', texto) 
    return " ".join(texto.split())

def marcar_pdf_digital(pdf_file, texto_sello, x, y):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 11)
    can.drawString(x, y, f"{str(texto_sello).upper()}")
    can.save()
    packet.seek(0)
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(pdf_file)
    output = PdfWriter()
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)
    for i in range(1, len(existing_pdf.pages)):
        output.add_page(existing_pdf.pages[i])
    out_io = io.BytesIO()
    output.write(out_io)
    return out_io.getvalue()

# --- 2. INTERFAZ POR PESTAÑAS ---
st.title("🚀 NEXION LOGISTICS SYSTEM")
tab1, tab2 = st.tabs(["📥 CARGADOR DE DATOS", "🧠 SMART ROUTING & SELLADO"])

# --- TAB 1: EL ALIMENTADOR ---
with tab1:
    st.markdown("### Paso 1: Subir Facturación RPA")
    uploaded_file = st.file_uploader("Arrastra el Excel aquí", type=["xlsx", "csv"])
    
    if uploaded_file:
        df_rpa = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        df_rpa.columns = [str(c).strip().upper() for c in df_rpa.columns]
        
        col_folio = next((c for c in df_rpa.columns if any(x in c for x in ['FACTURA', 'DOCNUM', 'FOLIO'])), df_rpa.columns[0])
        df_rpa[col_folio] = pd.to_numeric(df_rpa[col_folio], errors='coerce')
        
        c1, c2 = st.columns(2)
        inicio = c1.number_input("Desde folio:", value=int(df_rpa[col_folio].min() or 0))
        final = c2.number_input("Hasta folio:", value=int(df_rpa[col_folio].max() or 0))
        
        df_filtrado = df_rpa[(df_rpa[col_folio] >= inicio) & (df_rpa[col_folio] <= final)].copy()
        df_filtrado.insert(0, "INCLUIR", True)
        
        st.write("Selecciona las partidas que deseas subir:")
        editado = st.data_editor(df_filtrado, hide_index=True, use_container_width=True)
        
        if st.button("💾 CARGAR SELECCIÓN A GITHUB"):
            df_final_subir = editado[editado["INCLUIR"] == True].drop(columns=["INCLUIR"])
            df_final_subir = df_final_subir.rename(columns={col_folio: "FACTURA"})
            guardar_en_github(df_final_subir)

# --- TAB 2: EL CEREBRO ---
with tab2:
    st.markdown("### Paso 2: Procesar Smart Routing")
    
    if st.button("🔄 LEER DATOS DE GITHUB Y ANALIZAR"):
        with st.spinner("Conectando con la matriz en GitHub..."):
            matriz_db = obtener_matriz_github()
            
            if not matriz_db.empty:
                # Buscamos columnas para el motor
                col_dir = next((c for c in matriz_db.columns if 'DIRECCION' in c), None)
                col_tarifa = next((c for c in matriz_db.columns if any(x in c for x in ['PRECIO', 'CAJA', 'COSTO'])), None)
                
                def motor_routing(row):
                    if not col_dir: return "ERROR: NO DIR", 0.0
                    d_limpia = limpiar_texto(row[col_dir])
                    # Regla Local
                    if any(loc in d_limpia for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA", "TLAJOMULCO"]):
                        return "LOCAL", 0.0
                    
                    # Regla Foráneo (Cruce de datos)
                    flete = row.get('TRANSPORTE', 'POR ASIGNAR')
                    costo = pd.to_numeric(row.get(col_tarifa, 0.0), errors='coerce') if col_tarifa else 0.0
                    return flete, costo

                res = matriz_db.apply(motor_routing, axis=1)
                matriz_db['RECOMENDACION'] = [r[0] for r in res]
                matriz_db['COSTO'] = [r[1] for r in res]
                
                # Columnas finales para vista
                cols_ok = ["FACTURA", "RECOMENDACION", "COSTO", "NOMBRE_CLIENTE", "DIRECCION", "DESTINO"]
                cols_finales = [c for c in cols_ok if c in matriz_db.columns]
                st.session_state.df_analisis = matriz_db[cols_finales]
                st.success("¡Análisis completado!")
            else:
                st.warning("No se encontraron datos en 'facturacion.csv'. Sube algo en la pestaña 1.")

    # Mostrar resultados si existen
    if "df_analisis" in st.session_state:
        p_editado = st.data_editor(st.session_state.df_analisis, use_container_width=True, hide_index=True)
        
        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            if st.button("📌 FIJAR CAMBIOS"):
                st.session_state.df_analisis = p_editado
                st.toast("Cambios fijados localmente")
        
        with col_acc2:
            towrite = io.BytesIO()
            p_editado.to_excel(towrite, index=False, engine='openpyxl')
            st.download_button("📊 DESCARGAR EXCEL FINAL", towrite.getvalue(), "ST_DATA_FINAL.xlsx")

        # Expander de Sellado
        with st.expander("🖨️ SELLADO DIGITAL"):
            pdfs = st.file_uploader("Subir PDFs para sellar", type="pdf", accept_multiple_files=True)
            ax = st.slider("Posición X", 0, 600, 510)
            ay = st.slider("Posición Y", 0, 800, 760)
            
            if pdfs and st.button("EJECUTAR SELLADO"):
                # Mapa factura -> fletera
                mapa = pd.Series(p_editado.RECOMENDACION.values, index=p_editado["FACTURA"].astype(str)).to_dict()
                z_io = io.BytesIO()
                with zipfile.ZipFile(z_io, "a") as zf:
                    for pdf in pdfs:
                        f_id = next((k for k in mapa.keys() if k in pdf.name.upper()), None)
                        if f_id:
                            zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ax, ay))
                st.download_button("📥 DESCARGAR ZIP", z_io.getvalue(), "Sellado.zip")





















































