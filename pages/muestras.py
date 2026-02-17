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
        st.error("Token no configurado.")
        return
    csv_content = df_final.to_csv(index=False)
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(api_url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    payload = {
        "message": f"Update {datetime.now()}",
        "content": base64.b64encode(csv_content.encode()).decode(),
        "sha": sha
    }
    requests.put(api_url, json=payload, headers=headers)

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

# --- 2. INTERFAZ ---
st.title("🚀 NEXION HUB")
tab1, tab2 = st.tabs(["📥 CARGADOR", "🧠 SMART ROUTING & S&T"])

# --- TAB 1: CARGADOR (Igual que antes) ---
with tab1:
    st.subheader("Subir información al Repositorio")
    up = st.file_uploader("Excel del RPA", type=["xlsx", "csv"])
    if up:
        df_rpa = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        df_rpa.columns = [str(c).upper() for c in df_rpa.columns]
        col_f = next((c for c in df_rpa.columns if 'FACTURA' in c or 'DOCNUM' in c), df_rpa.columns[0])
        
        # Selección de folios
        c1, c2 = st.columns(2)
        ini = c1.number_input("Desde:", value=int(pd.to_numeric(df_rpa[col_f]).min()))
        fin = c2.number_input("Hasta:", value=int(pd.to_numeric(df_rpa[col_f]).max()))
        
        df_sel = df_rpa[(pd.to_numeric(df_rpa[col_f]) >= ini) & (pd.to_numeric(df_rpa[col_f]) <= fin)].copy()
        df_sel.insert(0, "INCLUIR", True)
        edit_c = st.data_editor(df_sel, hide_index=True)
        
        if st.button("SUBIR A GITHUB"):
            df_push = edit_c[edit_c["INCLUIR"]==True].drop(columns=["INCLUIR"]).rename(columns={col_f: "FACTURA"})
            guardar_en_github(df_push)
            st.success("Archivo 'facturacion.csv' actualizado.")

# --- TAB 2: PROCESAMIENTO (TU CÓDIGO REPARADO) ---
with tab2:
    st.subheader("Preparación de S&T y Ruteo Inteligente")
    
    if st.button("🔄 CARGAR DATOS DESDE GITHUB"):
        st.session_state.matriz_raw = obtener_matriz_github()

    if "matriz_raw" in st.session_state and not st.session_state.matriz_raw.empty:
        df_m = st.session_state.matriz_raw
        
        # --- PARTE 1: PREPARAR S&T DATA ---
        st.markdown("### 1. Preparar S&T Data")
        col_fact = "FACTURA"
        
        c1, c2 = st.columns(2)
        v_ini = c1.number_input("Filtrar Desde:", value=int(df_m[col_fact].min()), key="s1")
        v_fin = c2.number_input("Filtrar Hasta:", value=int(df_m[col_fact].max()), key="s2")
        
        df_filtro_st = df_m[(df_m[col_fact] >= v_ini) & (df_m[col_fact] <= v_fin)].copy()
        df_filtro_st.insert(0, "Incluir", True)
        
        # Editor para elegir partidas
        st.info("Selecciona las partidas para el archivo S&T y el Smart Routing")
        edit_st = st.data_editor(df_filtro_st, hide_index=True, key="editor_st")
        
        if st.button("🚀 RENDERIZAR Y EJECUTAR SMART ROUTING"):
            # Filtrar solo lo seleccionado
            df_final_st = edit_st[edit_st["Incluir"] == True].copy()
            
            # --- MOTOR SMART ROUTING ---
            col_dir = next((c for c in df_final_st.columns if 'DIRECCION' in c), None)
            col_tarifa = next((c for c in df_final_st.columns if any(x in c for x in ['PRECIO', 'CAJA', 'COSTO'])), None)

            def motor(row):
                if not col_dir: return "REVISAR DIR", 0.0
                d_limpia = limpiar_texto(row[col_dir])
                if any(loc in d_limpia for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA"]):
                    return "LOCAL", 0.0
                
                flete = row.get('TRANSPORTE', 'POR ASIGNAR')
                costo = pd.to_numeric(row.get(col_tarifa, 0.0), errors='coerce')
                return flete, costo

            res = df_final_st.apply(motor, axis=1)
            df_final_st['RECOMENDACION'] = [r[0] for r in res]
            df_final_st['COSTO'] = [r[1] for r in res]
            
            st.session_state.df_analisis = df_final_st
            st.success("S&T Data y Smart Routing procesados.")

    # --- RESULTADOS, DESCARGAS Y SELLADO ---
    if "df_analisis" in st.session_state:
        st.markdown("---")
        p = st.session_state.df_analisis
        
        # Mostrar tabla ruteada
        cols_v = ["FACTURA", "RECOMENDACION", "COSTO", "NOMBRE_CLIENTE", "DIRECCION", "DESTINO"]
        cols_existentes = [c for c in cols_v if c in p.columns]
        
        st.write("### Análisis Final")
        p_editado = st.data_editor(p[cols_existentes], hide_index=True, use_container_width=True)

        # Botones de Acción
        ba1, ba2 = st.columns(2)
        with ba1:
            towrite = io.BytesIO()
            p_editado.to_excel(towrite, index=False)
            st.download_button("📥 DESCARGAR EXCEL S&T", towrite.getvalue(), "ST_DATA_FINAL.xlsx")
        
        # Sistema de Sellado
        with st.expander("🖨️ SELLADO DIGITAL"):
            pdfs = st.file_uploader("Subir PDFs", type="pdf", accept_multiple_files=True)
            ax = st.slider("X", 0, 600, 510); ay = st.slider("Y", 0, 800, 760)
            if pdfs and st.button("EJECUTAR SELLADO"):
                mapa = pd.Series(p_editado.RECOMENDACION.values, index=p_editado["FACTURA"].astype(str)).to_dict()
                z_io = io.BytesIO()
                with zipfile.ZipFile(z_io, "a") as zf:
                    for pdf in pdfs:
                        f_id = next((k for k in mapa.keys() if k in pdf.name.upper()), None)
                        if f_id: zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ax, ay))
                st.download_button("DESCARGAR ZIP", z_io.getvalue(), "Sellado.zip")






















































