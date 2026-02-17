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

# --- 0. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(layout="wide", page_title="Nexion Hub")
vars_css = {'sub': '#54AFE7', 'border': '#333'}

st.markdown(f"""
    <style>
    .op-query-text {{ color: #54AFE7; font-weight: bold; letter-spacing: 1px; font-size: 14px; }}
    .stButton>button {{ width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- CREDENCIALES GITHUB ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_OWNER = "RH2026"
REPO_NAME = "nexion"
FILE_PATH = "facturacion.csv"  # <--- ACTUALIZADO: Nuevo nombre del archivo

# --- 1. FUNCIONES DE DATOS Y GITHUB ---
@st.cache_data(ttl=2) # Caché mínima para ver cambios al instante
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
        st.error("❌ Token de GitHub no configurado en Secrets.")
        return
    
    df_actual = obtener_matriz_github()
    
    # Unir y asegurar que no haya duplicados por factura
    if not df_actual.empty:
        df_final = pd.concat([df_actual, df_nuevo]).drop_duplicates(subset=['FACTURA'], keep='last')
    else:
        df_final = df_nuevo

    # Convertir a CSV plano para GitHub
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
        st.success(f"✅ ¡{FILE_PATH} actualizado en GitHub!")
        st.balloons()
    else:
        st.error(f"❌ Error al subir: {subida.text}")

def limpiar_texto(texto):
    if pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper()
    texto = re.sub(r'[^A-Z0-9\s]', ' ', texto) 
    return " ".join(texto.split())

# --- 2. FUNCIONES PDF ---
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

# --- 3. INTERFAZ ---
st.title("🚀 NEXION HUB: CONTROL LOGÍSTICO")
tab1, tab2 = st.tabs(["📥 CARGADOR RPA", "🧠 SMART ROUTING"])

with tab1:
    st.markdown(f"<p class='op-query-text'>PASO 1: SUBIR NUEVOS FOLIOS A GITHUB</p>", unsafe_allow_html=True)
    up_file = st.file_uploader("Subir Excel del RPA", type=["xlsx", "csv"], label_visibility="collapsed")
    
    if up_file:
        df_rpa = pd.read_excel(up_file) if up_file.name.endswith('.xlsx') else pd.read_csv(up_file)
        df_rpa.columns = [str(c).strip().upper() for c in df_rpa.columns]
        
        # Identificar columna de factura
        col_f = next((c for c in df_rpa.columns if any(x in c for x in ['FACTURA', 'DOCNUM', 'FOLIO'])), df_rpa.columns[0])
        
        c1, c2 = st.columns(2)
        df_rpa[col_f] = pd.to_numeric(df_rpa[col_f], errors='coerce')
        inicio = c1.number_input("Desde Folio:", value=int(df_rpa[col_f].min() or 0))
        fin = c2.number_input("Hasta Folio:", value=int(df_rpa[col_f].max() or 0))
        
        df_filtrado = df_rpa[(df_rpa[col_f] >= inicio) & (df_rpa[col_f] <= fin)].copy()
        
        df_filtrado.insert(0, "INCLUIR", True)
        edited = st.data_editor(df_filtrado, hide_index=True, use_container_width=True)
        
        if st.button("💾 GUARDAR SELECCIÓN EN GITHUB"):
            df_para_github = edited[edited["INCLUIR"] == True].drop(columns=["INCLUIR"])
            df_para_github = df_para_github.rename(columns={col_f: "FACTURA"})
            # Aseguramos que existan las columnas de salida para que el motor no truene
            if 'RECOMENDACION' not in df_para_github.columns: df_para_github['RECOMENDACION'] = ""
            if 'COSTO' not in df_para_github.columns: df_para_github['COSTO'] = 0.0
            
            guardar_en_github(df_para_github)

with tab2:
    st.markdown(f"<p class='op-query-text'>PASO 2: ANÁLISIS DE FOLIOS NUEVOS</p>", unsafe_allow_html=True)
    if st.button("🔄 EJECUTAR SMART ROUTING"):
        matriz_db = obtener_matriz_github()
        if not matriz_db.empty:
            col_dir = next((c for c in matriz_db.columns if 'DIRECCION' in c), None)
            col_precio_matriz = 'PRECIO POR CAJA' if 'PRECIO POR CAJA' in matriz_db.columns else 'COSTO'
            
            def motor(row):
                # Si ya tiene una fletera asignada, no la recalculamos (mantenemos lo anterior)
                if pd.notna(row.get('RECOMENDACION')) and str(row.get('RECOMENDACION')).strip() != "":
                    return row['RECOMENDACION'], row.get('COSTO', 0.0)

                if not col_dir: return "REVISAR DIR", 0.0
                
                dir_limpia = limpiar_texto(row[col_dir])
                # Lógica de Local
                if any(x in dir_limpia for x in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA"]):
                    return "LOCAL", 0.0
                
                # Aquí puedes añadir más lógica de cruce de tarifas si tienes otra tabla
                return "POR ASIGNAR", pd.to_numeric(row.get(col_precio_matriz, 0.0), errors='coerce')

            res = matriz_db.apply(motor, axis=1)
            matriz_db['RECOMENDACION'] = [r[0] for r in res]
            matriz_db['COSTO'] = [r[1] for r in res]
            
            st.session_state.df_analisis = matriz_db
        else:
            st.warning("No hay datos en GitHub para analizar.")

    if "df_analisis" in st.session_state:
        # Mostrar solo las columnas relevantes para tu logística
        cols_log = ["FACTURA", "RECOMENDACION", "COSTO", "NOMBRE_CLIENTE", "DIRECCION", "DESTINO"]
        cols_finales = [c for c in cols_log if c in st.session_state.df_analisis.columns]
        
        modo_edit = st.toggle("Habilitar Edición Manual")
        p_editado = st.data_editor(
            st.session_state.df_analisis[cols_finales], 
            use_container_width=True, 
            hide_index=True,
            disabled=not modo_edit
        )
        
        if st.button("📌 FIJAR CAMBIOS Y ACTUALIZAR GITHUB"):
            # Combinamos los cambios manuales de vuelta a la matriz principal
            df_sync = st.session_state.df_analisis.copy()
            for idx, row in p_editado.iterrows():
                df_sync.loc[df_sync['FACTURA'] == row['FACTURA'], ['RECOMENDACION', 'COSTO']] = [row['RECOMENDACION'], row['COSTO']]
            guardar_en_github(df_sync)

        with st.expander("🖨️ SELLADO DE PDFs"):
            pdfs = st.file_uploader("Subir Facturas", type="pdf", accept_multiple_files=True)
            ax = st.slider("X", 0, 600, 510); ay = st.slider("Y", 0, 800, 760)
            if pdfs and st.button("EJECUTAR SELLADO"):
                mapa = pd.Series(p_editado.RECOMENDACION.values, index=p_editado["FACTURA"].astype(str)).to_dict()
                z_io = io.BytesIO()
                with zipfile.ZipFile(z_io, "a") as zf:
                    for pdf in pdfs:
                        f_id = next((k for k in mapa.keys() if k in pdf.name.upper()), None)
                        if f_id: zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ax, ay))
                st.download_button("Descargar Sellados", z_io.getvalue(), "Sellado.zip")



















































