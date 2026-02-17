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
FILE_PATH = "facturacion.csv"

# --- 1. FUNCIONES MAESTRAS ---
@st.cache_data(ttl=2)
def obtener_datos_github():
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}?nocache={int(time.time())}"
    try:
        m = pd.read_csv(url)
        # Limpieza básica de columnas
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except Exception as e:
        st.error(f"Error al leer GitHub: {e}")
        return pd.DataFrame()

def guardar_en_github(df_final):
    if not GITHUB_TOKEN:
        st.error("❌ Token de GitHub no configurado.")
        return
    csv_content = df_final.to_csv(index=False)
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(api_url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    payload = {
        "message": f"Update Logística {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(csv_content.encode()).decode(),
        "sha": sha
    }
    res_put = requests.put(api_url, json=payload, headers=headers)
    if res_put.status_code in [200, 201]:
        st.success("✅ ¡Base de datos actualizada!")
    else:
        st.error(f"Error: {res_put.text}")

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

# --- 2. LOGICA DE NEGOCIO (SMART ROUTING) ---
def ejecutar_routing(df):
    # Buscamos columnas clave
    col_dir = next((c for c in df.columns if 'DIRECCION' in c), None)
    col_precio = next((c for c in df.columns if 'PRECIO' in c or 'CAJA' in c or 'COSTO' in c), None)
    
    def motor(row):
        # Si ya tiene una fletera, no la tocamos
        if pd.notna(row.get('RECOMENDACION')) and str(row.get('RECOMENDACION')).strip() not in ["", "REVISAR"]:
            return row['RECOMENDACION'], row.get('COSTO', 0.0)
        
        if not col_dir: return "ERROR DIR", 0.0
        
        dir_limpia = limpiar_texto(row[col_dir])
        # Regla Local
        if any(x in dir_limpia for x in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA", "TLAJOMULCO"]):
            return "LOCAL", 0.0
        
        # Tomamos el precio por caja que viene de la base
        costo_val = pd.to_numeric(row.get(col_precio, 0.0), errors='coerce') if col_precio else 0.0
        flet_val = row.get('TRANSPORTE', 'POR ASIGNAR')
        
        return flet_val, costo_val

    df['RECOMENDACION'], df['COSTO'] = zip(*df.apply(motor, axis=1))
    return df

# --- 3. INTERFAZ STREAMLIT ---
st.title("🚀 NEXION HUB: LOGÍSTICA CENTRALIZADA")

# Botón global para refrescar datos de la nube
if st.button("🔄 SINCRONIZAR CON GITHUB (LEER FACTURACION.CSV)"):
    st.session_state.db_master = obtener_datos_github()
    st.toast("Datos cargados", icon="☁️")

if "db_master" in st.session_state:
    df_m = st.session_state.db_master

    # --- BLOQUE 1: S&T PREPARATION (FILTROS) ---
    st.markdown(f"<p class='op-query-text'>FILTRADO DE FOLIOS PARA S&T DATA</p>", unsafe_allow_html=True)
    
    col_f = next((c for c in df_m.columns if any(x in c for x in ['FACTURA', 'FOLIO', 'DOCNUM'])), df_m.columns[0])
    df_m[col_f] = pd.to_numeric(df_m[col_f], errors='coerce')
    
    c1, c2 = st.columns(2)
    f_min = c1.number_input("Desde Folio:", value=int(df_m[col_f].min() or 0))
    f_max = c2.number_input("Hasta Folio:", value=int(df_m[col_f].max() or 0))
    
    df_rango = df_m[(df_m[col_f] >= f_min) & (df_m[col_f] <= f_max)].copy()
    df_rango.insert(0, "SELECCIONAR", True)
    
    st.markdown("### Selecciona los folios a procesar")
    edit_st = st.data_editor(df_rango, hide_index=True, use_container_width=True)
    
    # --- BLOQUE 2: SMART ROUTING ---
    if st.button("🚀 EJECUTAR SMART ROUTING & GENERAR ANALISIS", type="primary"):
        df_para_ruta = edit_st[edit_st["SELECCIONAR"] == True].drop(columns=["SELECCIONAR"])
        # Renombramos a FACTURA para consistencia
        df_para_ruta = df_para_ruta.rename(columns={col_f: "FACTURA"})
        
        # Ejecutamos motor
        st.session_state.df_analisis = ejecutar_routing(df_para_ruta)
        st.success("Análisis generado correctamente.")

    # --- BLOQUE 3: RESULTADOS Y SELLADO ---
    if "df_analisis" in st.session_state:
        st.markdown("---")
        st.markdown(f"<p class='op-query-text'>LOGISTICS INTELLIGENCE HUB (ANÁLISIS FINAL)</p>", unsafe_allow_html=True)
        
        cols_log = ["FACTURA", "RECOMENDACION", "COSTO", "NOMBRE_CLIENTE", "DIRECCION", "DESTINO"]
        cols_finales = [c for c in cols_log if c in st.session_state.df_analisis.columns]
        
        modo_edit = st.toggle("Habilitar Edición Manual de Fletera/Tarifa")
        
        p_editado = st.data_editor(
            st.session_state.df_analisis[cols_finales],
            use_container_width=True,
            hide_index=True,
            disabled=not modo_edit,
            column_config={
                "COSTO": st.column_config.NumberColumn("TARIFA", format="$%.2f"),
                "RECOMENDACION": st.column_config.TextColumn("FLETERA")
            }
        )
        
        b1, b2 = st.columns(2)
        with b1:
            if st.button("📌 GUARDAR CAMBIOS EN GITHUB"):
                # Sincronizamos los cambios manuales al master y subimos
                df_sync = st.session_state.db_master.copy()
                for _, fila in p_editado.iterrows():
                    df_sync.loc[df_sync[col_f] == fila['FACTURA'], ['RECOMENDACION', 'COSTO']] = [fila['RECOMENDACION'], fila['COSTO']]
                guardar_en_github(df_sync)
        
        with b2:
            towrite = io.BytesIO()
            p_editado.to_excel(towrite, index=False, engine='openpyxl')
            st.download_button("📊 DESCARGAR EXCEL S&T", towrite.getvalue(), "ST_DATA_FINAL.xlsx")

        # --- SELLADO ---
        with st.expander("🖨️ SISTEMA DE SELLADO DIGITAL"):
            pdfs = st.file_uploader("Subir Facturas PDF", type="pdf", accept_multiple_files=True)
            ax = st.slider("Posición X", 0, 600, 510); ay = st.slider("Posición Y", 0, 800, 760)
            if pdfs and st.button("SELLAR DOCUMENTOS"):
                mapa = pd.Series(p_editado.RECOMENDACION.values, index=p_editado["FACTURA"].astype(str)).to_dict()
                z_io = io.BytesIO()
                with zipfile.ZipFile(z_io, "a") as zf:
                    for pdf in pdfs:
                        f_id = next((k for k in mapa.keys() if k in pdf.name.upper()), None)
                        if f_id: zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ax, ay))
                st.download_button("Descargar ZIP Sellado", z_io.getvalue(), "Facturas_Selladas.zip")
else:
    st.info("💡 Haz clic en 'Sincronizar con GitHub' para cargar la facturación actual.")




















































