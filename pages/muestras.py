import os
import io
import zipfile
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
import unicodedata
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

# --- 0. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(layout="wide")
vars_css = {'sub': '#54AFE7', 'border': '#333'}

st.markdown(f"""
    <style>
    .op-query-text {{ color: #54AFE7; font-weight: bold; letter-spacing: 1px; font-size: 14px; }}
    .stButton>button {{ width: 100%; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 1. CARGA DE DATOS EXTERNOS (MATRIZ GITHUB) ---
@st.cache_data
def obtener_matriz_logistica():
    url = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv"
    try:
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except:
        return pd.DataFrame()

def normalizar(texto):
    if pd.isna(texto): return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper().strip()

# --- 2. FUNCIONES MAESTRAS ---
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

uploaded_file = st.file_uploader("Subir archivo", type=["xlsx", "csv"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        df.columns = [str(c).strip().replace('\n', '').replace('\t', '') for c in df.columns]
        col_folio = next((c for c in df.columns if c.lower() == 'factura'), None)
        if not col_folio:
            col_folio = next((c for c in df.columns if 'factura' in c.lower() or 'docnum' in c.lower()), df.columns[0])
        
        st.toast(f"DETECTADO -> Factura: {col_folio}", icon="🔍")

        col_left, col_right = st.columns([1, 2], gap="large")
        with col_left:
            st.markdown(f"<p class='op-query-text'>FILTROS DE RANGO</p>", unsafe_allow_html=True)
            serie_folios = pd.to_numeric(df[col_folio], errors='coerce').dropna()
            f_min_val, f_max_val = (int(serie_folios.min()), int(serie_folios.max())) if not serie_folios.empty else (0,0)
            inicio = st.number_input("Folio Inicial", value=f_min_val)
            final = st.number_input("Folio Final", value=f_max_val)
            df[col_folio] = pd.to_numeric(df[col_folio], errors='coerce')
            df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)].copy()

        with col_right:
            st.markdown(f"<p class='op-query-text'>SELECCIÓN DE FOLIOS</p>", unsafe_allow_html=True)
            if not df_rango.empty:
                selector_df = df_rango.drop_duplicates(subset=[col_folio])[[col_folio]]
                selector_df.insert(0, "Incluir", True)
                edited_df = st.data_editor(selector_df, hide_index=True, height=300, use_container_width=True, key="editor_s_t")
            else:
                st.warning("Sin datos en el rango.")
                edited_df = pd.DataFrame()

        if not edited_df.empty:
            folios_finales = edited_df[edited_df["Incluir"] == True][col_folio].tolist()
            c1, c2, c3 = st.columns([1,1,2])
            
            with c1:
                render_btn = st.button("RENDERIZAR TABLA COMPLETA")
            
            if render_btn or "df_final_st" in st.session_state:
                if render_btn:
                    st.session_state.df_final_st = df_rango[df_rango[col_folio].isin(folios_finales)]
                
                df_final = st.session_state.df_final_st
                st.dataframe(df_final, use_container_width=True)
                
                with c3:
                    if st.button("🚀 ENVIAR A SMART ROUTING (DIRECCION MATCH)", type="primary", use_container_width=True):
                        # Aquí disparamos la conexión con la matriz de GitHub
                        df_analisis = df_final.drop_duplicates(subset=[col_folio]).copy()
                        
                        # Buscamos la columna de Dirección en el archivo subido
                        col_dir = next((c for c in df_analisis.columns if 'DIRECCION' in c.upper()), None)
                        matriz_db = obtener_matriz_logistica()
                        
                        # Identificamos columnas en la matriz de GitHub (Destino y Transporte)
                        col_dest_db = next((c for c in matriz_db.columns if 'DESTINO' in c), matriz_db.columns[0])
                        col_flet_db = next((c for c in matriz_db.columns if 'TRANSPORTE' in c or 'FLETERA' in c), matriz_db.columns[-1])

                        def recomendar(row):
                            if not col_dir: return "REVISIÓN MANUAL"
                            txt_dir = normalizar(row[col_dir])
                            
                            # 1. Regla Local Directa
                            if any(loc in txt_dir for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA"]):
                                return "LOCAL"
                            
                            # 2. Match contra Matriz GitHub
                            for _, fila_db in matriz_db.iterrows():
                                keyword = normalizar(fila_db[col_dest_db])
                                if keyword and (keyword in txt_dir):
                                    return fila_db[col_flet_db]
                                    
                            return "REVISIÓN MANUAL"

                        df_analisis['RECOMENDACION'] = df_analisis.apply(recomendar, axis=1)
                        df_analisis['COSTO'] = 0.0
                        df_analisis['FECHA_HORA'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        st.session_state.df_analisis = df_analisis
                        st.success("Recomendaciones generadas desde la matriz histórica.")
                        st.rerun()

    except Exception as e:
        st.error(f"Error S&T: {e}")

# --- BLOQUE 2: SMART ROUTING ---
if "df_analisis" in st.session_state:
    st.markdown("---")
    st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>LOGISTICS INTELLIGENCE HUB | XENOCODE CORE</p>", unsafe_allow_html=True)
    
    p = st.session_state.df_analisis
    modo_edicion = st.toggle(":material/edit_note: EDITAR VALORES")
    
    p_editado = st.data_editor(
        p, use_container_width=True, hide_index=True,
        column_config={
            "RECOMENDACION": st.column_config.TextColumn(":material/local_shipping: FLETERA", disabled=not modo_edicion),
            "COSTO": st.column_config.NumberColumn(":material/payments: TARIFA", format="$%.2f", disabled=not modo_edicion),
        },
        key="editor_pro_v11"
    )

    # SISTEMA DE SELLADO
    st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:30px 0; opacity:0.3;'>", unsafe_allow_html=True)
    with st.expander(":material/settings: PANEL DE CALIBRACIÓN", expanded=True):
        col_x, col_y = st.columns(2)
        ajuste_x = col_x.slider("Eje X", 0, 612, 510)
        ajuste_y = col_y.slider("Eje Y", 0, 792, 760)

    if st.button(":material/article: GENERAR SELLOS PARA FACTURAS (PAPEL)", use_container_width=True):
        sellos_pdf = generar_sellos_fisicos(p_editado['RECOMENDACION'].tolist(), ajuste_x, ajuste_y)
        st.download_button(":material/download: DESCARGAR PDF", sellos_pdf, "Sellos.pdf")

    with st.container(border=True):
        pdfs = st.file_uploader("Subir Facturas PDF", type="pdf", accept_multiple_files=True)
        if pdfs and st.button("EJECUTAR ESTAMPADO DIGITAL"):
            col_id = p_editado.columns[0]
            mapa = pd.Series(p_editado.RECOMENDACION.values, index=p_editado[col_id].astype(str)).to_dict()
            z_buf = io.BytesIO()
            with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                for pdf in pdfs:
                    f_id = next((k for k in mapa.keys() if k in pdf.name.upper()), None)
                    if f_id:
                        zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ajuste_x, ajuste_y))
            st.download_button(":material/folder_zip: DESCARGAR ZIP", z_buf.getvalue(), "Facturas_Digitales.zip")






























































































