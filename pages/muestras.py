import os
import io
import zipfile
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
import unicodedata
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

# --- 0. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(layout="wide")
vars_css = {'sub': '#54AFE7', 'border': '#333'}

st.markdown(f"""
    <style>
    .op-query-text {{ color: #54AFE7; font-weight: bold; letter-spacing: 1px; font-size: 14px; }}
    .stButton>button {{ width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 1. CARGA DE MATRIZ DESDE GITHUB ---
@st.cache_data
def obtener_matriz_github():
    url = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv"
    try:
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except Exception as e:
        st.error(f"Error fatal al conectar con GitHub: {e}")
        return pd.DataFrame()

def limpiar_texto(texto):
    if pd.isna(texto): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper()
    texto = re.sub(r'[^A-Z0-9\s]', ' ', texto) # Corregido A-Z0-9
    return " ".join(texto.split())

# --- 2. FUNCIONES MAESTRAS PDF ---
def generar_sellos_fisicos(lista_textos, x, y):
    output = PdfWriter()
    for texto in lista_textos:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 11)
        can.drawString(x, y, f"{str(texto).upper()}")
        can.save()
        packet.seek(0)
        output.add_page(PdfReader(packet).pages[0])
    out_io = io.BytesIO()
    output.write(out_io)
    return out_io.getvalue()

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

# --- BLOQUE 1: PREPARACIÓN S&T ---
st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>S&T PREPARATION MODULE</p>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Subir archivo ERP", type=["xlsx", "csv"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = [str(c).strip().replace('\n', '') for c in df.columns]
        col_folio = next((c for c in df.columns if 'factura' in c.lower() or 'docnum' in c.lower()), df.columns[0])
        
        col_left, col_right = st.columns([1, 2], gap="large")
        with col_left:
            st.markdown(f"<p class='op-query-text'>FILTROS</p>", unsafe_allow_html=True)
            serie = pd.to_numeric(df[col_folio], errors='coerce').dropna()
            inicio = st.number_input("Desde:", value=int(serie.min()) if not serie.empty else 0)
            final = st.number_input("Hasta:", value=int(serie.max()) if not serie.empty else 0)
            df[col_folio] = pd.to_numeric(df[col_folio], errors='coerce')
            df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)].copy()

        with col_right:
            st.markdown(f"<p class='op-query-text'>SELECCIÓN</p>", unsafe_allow_html=True)
            if not df_rango.empty:
                info = df_rango.drop_duplicates(subset=[col_folio])[[col_folio]]
                info.insert(0, "Incluir", True)
                edited_df = st.data_editor(info, hide_index=True, use_container_width=True, key="ed_v4")
            else: st.warning("Rango vacío")

        if not df_rango.empty and not edited_df.empty:
            folios_ok = edited_df[edited_df["Incluir"] == True][col_folio].tolist()
            c1, c2, c3 = st.columns([1,1,2])
            
            if c1.button("RENDERIZAR"):
                st.session_state.df_final_st = df_rango[df_rango[col_folio].isin(folios_ok)]
            
            if "df_final_st" in st.session_state:
                df_st = st.session_state.df_final_st
                st.dataframe(df_st, use_container_width=True)
                
                with c3:
                    if st.button("🚀 SMART ROUTING (CRUCE GITHUB)", type="primary"):
                        df_log = df_st.drop_duplicates(subset=[col_folio]).copy()
                        matriz_db = obtener_matriz_github()
                        
                        col_dir_erp = next((c for c in df_log.columns if 'DIRECCION' in c.upper()), None)
                        col_dest_matriz = 'DESTINO' if 'DESTINO' in matriz_db.columns else matriz_db.columns[0]
                        col_flet_matriz = 'TRANSPORTE' if 'TRANSPORTE' in matriz_db.columns else 'FLETERA'

                        def motor_v4(row):
                            if not col_dir_erp: return "ERROR: COL DIRECCION", 0.0
                            dir_limpia = limpiar_texto(row[col_dir_erp])
                            if any(loc in dir_limpia for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA", "TLAJOMULCO"]):
                                return "LOCAL", 0.0
                            for _, fila in matriz_db.iterrows():
                                dest_key = limpiar_texto(fila[col_dest_matriz])
                                if dest_key and (dest_key in dir_limpia):
                                    flet = fila.get(col_flet_matriz, "ASIGNADO")
                                    costo = fila.get('COSTO', 0.0) if 'COSTO' in matriz_db.columns else 0.0
                                    return flet, costo
                            return "REVISIÓN MANUAL", 0.0

                        res = df_log.apply(motor_v4, axis=1)
                        df_log['RECOMENDACION'] = [r[0] for r in res]
                        df_log['COSTO'] = [r[1] for r in res]
                        df_log['FECHA_HORA'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        st.session_state.df_analisis = df_log
                        st.success("¡Motor sincronizado con GitHub!")
                        st.rerun()

    except Exception as e: st.error(f"Error: {e}")

# --- BLOQUE 2: SMART ROUTING ---
if "df_analisis" in st.session_state:
    st.markdown("---")
    st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>LOGISTICS INTELLIGENCE HUB</p>", unsafe_allow_html=True)
    
    # 1. Edición de datos
    modo_edicion = st.toggle("MODO EDICIÓN (HABILITAR CAMBIOS MANUALES)")
    
    p_editado = st.data_editor(
        st.session_state.df_analisis,
        use_container_width=True,
        hide_index=True,
        column_config={
            "RECOMENDACION": st.column_config.TextColumn("FLETERA", disabled=not modo_edicion),
            "COSTO": st.column_config.NumberColumn("TARIFA", format="$%.2f", disabled=not modo_edicion),
        },
        key="editor_final_github"
    )

    # 2. Botones de Acción (Fijar y Descargar)
    col_btn1, col_btn2, col_btn3 = st.columns([1,1,2])
    
    with col_btn1:
        if st.button("📌 FIJAR CAMBIOS", use_container_width=True):
            st.session_state.df_analisis = p_editado
            st.toast("Cambios fijados en memoria", icon="✅")

    with col_btn2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            p_editado.to_excel(writer, index=False, sheet_name='Analisis_Logistico')
        st.download_button(
            label="📊 DESCARGAR ANÁLISIS",
            data=output.getvalue(),
            file_name=f"Analisis_Ruteo_{datetime.now().strftime('%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # 3. Sellado
    with st.expander("SISTEMA DE SELLADO PDF", expanded=False):
        cx, cy = st.columns(2); ax = cx.slider("Eje X", 0, 612, 510); ay = cy.slider("Eje Y", 0, 792, 760)
        if st.button("GENERAR SELLOS PAPEL"):
            st.download_button("Descargar PDF de Sellos", generar_sellos_fisicos(p_editado['RECOMENDACION'].tolist(), ax, ay), "Sellos.pdf")
        
        st.markdown("---")
        pdfs = st.file_uploader("Subir Facturas para Sellado Digital", type="pdf", accept_multiple_files=True)
        if pdfs and st.button("EJECUTAR SELLADO DIGITAL"):
            col_id = p_editado.columns[0]
            mapa = pd.Series(p_editado.RECOMENDACION.values, index=p_editado[col_id].astype(str)).to_dict()
            z_io = io.BytesIO()
            with zipfile.ZipFile(z_io, "a") as zf:
                for pdf in pdfs:
                    f_id = next((k for k in mapa.keys() if k in pdf.name.upper()), None)
                    if f_id: zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ax, ay))
            st.download_button("DESCARGAR ZIP", z_io.getvalue(), "Sellado.zip")
































































































