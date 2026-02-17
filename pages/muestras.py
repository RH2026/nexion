import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Smart Routing Hub", layout="wide", page_icon="🚀")

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #54AFE7; color: white; }
    .op-query-text { color: #54AFE7; font-weight: bold; letter-spacing: 1px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES MAESTRAS ---
def motor_logistico_central():
    # Diccionarios de ejemplo (Sustituye por tu lógica real)
    d_flet = {"MEXICO": "TRES GUERRAS", "MONTERREY": "PMM", "QUERETARO": "CASTORES"}
    d_price = {"MEXICO": 150.0, "MONTERREY": 200.0}
    return d_flet, d_price

def marcar_pdf_digital(pdf_file, texto_sello, x, y):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 12)
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
    return output

# --- INTERFAZ ---
st.title("🚀 SMART ROUTING & LOGISTICS")
st.markdown("---")

uploaded_file = st.file_uploader("📂 SUBIR ARCHIVO ERP", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Carga
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)

        # Limpieza
        df.columns = [str(c).strip().replace('\n', '') for c in df.columns]
        
        # Detección de columnas
        col_folio = next((c for c in df.columns if 'factura' in c.lower() or 'docnum' in c.lower()), df.columns[0])
        col_dir = next((c for c in df.columns if any(x in c.lower() for x in ['dir', 'destin', 'ciudad'])), None)

        # 1. PREPARACIÓN (S&T)
        st.subheader("1. Selección de Folios")
        c1, c2 = st.columns([1, 2])
        
        with c1:
            df[col_folio] = pd.to_numeric(df[col_folio], errors='coerce')
            df_clean = df.dropna(subset=[col_folio])
            f_min, f_max = int(df_clean[col_folio].min()), int(df_clean[col_folio].max())
            inicio = st.number_input("Desde:", value=f_min)
            final = st.number_input("Hasta:", value=f_max)
            df_rango = df_clean[(df_clean[col_folio] >= inicio) & (df_clean[col_folio] <= final)].copy()

        with c2:
            info_folios = df_rango.drop_duplicates(subset=[col_folio])[[col_folio]].copy()
            info_folios.insert(0, "Incluir", True)
            edited_selection = st.data_editor(info_folios, hide_index=True, use_container_width=True, key="sel_master")

        # 2. MOTOR
        st.markdown("---")
        if st.button("🚀 EJECUTAR RECOMENDACIÓN SMART"):
            folios_ok = edited_selection[edited_selection["Incluir"] == True][col_folio].tolist()
            # Aquí aplicamos el drop_duplicates para que el motor trabaje sobre folios únicos
            df_motor = df_rango[df_rango[col_folio].isin(folios_ok)].drop_duplicates(subset=[col_folio]).copy()
            
            if not df_motor.empty:
                d_flet, d_price = motor_logistico_central()
                
                def logic(row):
                    addr = str(row.get(col_dir, "")).upper()
                    if any(l in addr for l in ["GDL", "GUADALAJARA", "ZAPOPAN"]):
                        return "LOCAL", 0.0
                    for k, v in d_flet.items():
                        if k.upper() in addr: return v, d_price.get(k, 0.0)
                    return "REVISIÓN MANUAL", 0.0

                res = df_motor.apply(logic, axis=1)
                df_motor['RECOMENDACION'] = [r[0] for r in res]
                df_motor['COSTO'] = [r[1] for r in res]
                st.session_state.df_final = df_motor

        # 3. RESULTADOS Y SELLADO
        if "df_final" in st.session_state:
            st.subheader("2. Resultados Logística")
            df_final_ed = st.data_editor(st.session_state.df_final, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("3. Sellado Digital")
            pdfs = st.file_uploader("Subir PDFs", type="pdf", accept_multiple_files=True)
            
            if pdfs and st.button("Estampar Sellos"):
                mapa = pd.Series(df_final_ed.RECOMENDACION.values, index=df_final_ed[col_folio].astype(str)).to_dict()
                z_buf = io.BytesIO()
                with zipfile.ZipFile(z_buf, "a") as zf:
                    for p in pdfs:
                        f_id = next((f for f in mapa.keys() if f in p.name), None)
                        if f_id:
                            stamped = marcar_pdf_digital(p, mapa[f_id], 510, 760)
                            p_io = io.BytesIO()
                            stamped.write(p_io)
                            zf.writestr(f"SELLADO_{p.name}", p_io.getvalue())
                st.download_button("Descargar ZIP", z_buf.getvalue(), "Sellado.zip")

    except Exception as e:
        st.error(f"Error de datos: {e}")
else:
    st.info("Esperando archivo ERP...")



























































































