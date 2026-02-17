import os
import io
import zipfile
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

# --- 0. CONFIGURACIÓN Y ESTILOS (TUS VARIABLES) ---
st.set_page_config(layout="wide")
vars_css = {'sub': '#54AFE7', 'border': '#333'}

st.markdown(f"""
    <style>
    .op-query-text {{ color: #54AFE7; font-weight: bold; letter-spacing: 1px; font-size: 14px; }}
    .stButton>button {{ width: 100%; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 1. FUNCIONES MAESTRAS (CONSERVADAS AL 100%) ---
def motor_logistico_central():
    # Sustituir con tu lógica real de diccionarios
    d_flet = {"MEXICO": "TRES GUERRAS", "GUADALAJARA": "LOCAL"}
    d_price = {"MEXICO": 150.0}
    return d_flet, d_price

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

# --- BLOQUE 1: PREPARACIÓN S&T (CÓDIGO ORIGINAL 1) ---
st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>S&T PREPARATION MODULE</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Subir archivo", type=["xlsx", "csv"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        # Carga con detección automática
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Limpieza agresiva de columnas
        df.columns = [str(c).strip().replace('\n', '').replace('\t', '') for c in df.columns]
        
        col_folio = next((c for c in df.columns if c.lower() == 'factura'), None)
        col_transporte = next((c for c in df.columns if c.lower() == 'transporte'), None)
        if not col_folio:
            col_folio = next((c for c in df.columns if 'factura' in c.lower() or 'docnum' in c.lower()), df.columns[0])
        if not col_transporte:
            col_transporte = next((c for c in df.columns if 'transporte' in c.lower()), None)
        
        st.toast(f"DETECTADO -> Factura: {col_folio}", icon="🔍")

        # PANEL DE CONTROL S&T
        st.markdown("<br>", unsafe_allow_html=True)
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
                cols_to_show = [col_folio]
                if col_transporte: cols_to_show.append(col_transporte)
                info_folios = df_rango.drop_duplicates(subset=[col_folio])[cols_to_show]
                selector_df = info_folios.copy()
                selector_df.insert(0, "Incluir", True)
                
                edited_df = st.data_editor(
                    selector_df,
                    column_config={
                        "Incluir": st.column_config.CheckboxColumn("SEL", default=True),
                        col_folio: st.column_config.TextColumn("FACTURA", disabled=True)
                    },
                    hide_index=True, height=300, use_container_width=True, key="editor_s_t"
                )
            else:
                st.warning("Sin datos en el rango.")
                edited_df = pd.DataFrame()

        # ACCIONES S&T
        st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; opacity:0.2;'>", unsafe_allow_html=True)
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
                
                output_xlsx = BytesIO()
                with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)
                
                with c2:
                    st.download_button("DESCARGAR EXCEL (.XLSX)", output_xlsx.getvalue(), "S&T_PREP.xlsx", use_container_width=True)
                
                # BOTÓN DE CONEXIÓN AL MOTOR SMART
                with c3:
                    if st.button("🚀 ENVIAR A SMART ROUTING (SIN DUPLICADOS)", type="primary", use_container_width=True):
                        # Aquí ocurre la magia: Limpiamos duplicados solo para el análisis logístico
                        st.session_state.df_analisis = df_final.drop_duplicates(subset=[col_folio]).copy()
                        st.success("Datos procesados para Smart Routing. Desliza hacia abajo.")

    except Exception as e:
        st.error(f"Error S&T: {e}")
else:
    st.markdown(f"<div style='text-align:center; padding:50px; color:{vars_css['sub']}; font-size:10px; letter-spacing:4px;'>WAITING FOR ERP DATA...</div>", unsafe_allow_html=True)

# --- BLOQUE 2: SMART ROUTING (CÓDIGO ORIGINAL 2 INTEGRADO) ---
if "df_analisis" in st.session_state:
    st.markdown("---")
    st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>LOGISTICS INTELLIGENCE HUB | XENOCODE CORE</p>", unsafe_allow_html=True)
    
    d_flet, d_price = motor_logistico_central()
    p = st.session_state.df_analisis
    
    # Motor de recomendaciones sobre la tabla limpia
    if 'RECOMENDACION' not in p.columns:
        p.columns = [str(c).upper().strip() for c in p.columns]
        col_id = 'FACTURA' if 'FACTURA' in p.columns else p.columns[0]
        col_dir = next((c for c in p.columns if 'DIRECCION' in c or 'DIR' in c), None)

        def motor_prioridad(row):
            addr = str(row[col_dir]).upper() if col_dir else ""
            if any(loc in addr for loc in ["GDL", "GUADALAJARA", "ZAPOPAN"]): return "LOCAL"
            return "REVISIÓN MANUAL"

        p['RECOMENDACION'] = p.apply(motor_prioridad, axis=1)
        p['COSTO'] = p.apply(lambda r: 0.0 if r['RECOMENDACION'] == "LOCAL" else 0.0, axis=1)
        p['FECHA_HORA'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.df_analisis = p

    st.markdown("### :material/analytics: RECOMENDACIONES GENERADAS")
    modo_edicion = st.toggle(":material/edit_note: EDITAR VALORES")
    
    p_editado = st.data_editor(
        st.session_state.df_analisis,
        use_container_width=True,
        column_config={
            "RECOMENDACION": st.column_config.TextColumn(":material/local_shipping: FLETERA", disabled=not modo_edicion),
            "COSTO": st.column_config.NumberColumn(":material/payments: TARIFA", format="$%.2f", disabled=not modo_edicion),
        },
        key="editor_pro_v11"
    )

    # SISTEMA DE SELLADO (TUS BOTONES Y LÓGICA)
    st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:30px 0; opacity:0.3;'>", unsafe_allow_html=True)
    with st.expander(":material/settings: PANEL DE CALIBRACIÓN", expanded=True):
        col_x, col_y = st.columns(2)
        ajuste_x = col_x.slider("Eje X (Horizontal)", 0, 612, 510)
        ajuste_y = col_y.slider("Eje Y (Vertical)", 0, 792, 760)

    if st.button(":material/article: GENERAR SELLOS PARA FACTURAS (PAPEL)", use_container_width=True):
        sellos = p_editado['RECOMENDACION'].tolist()
        pdf_out = generar_sellos_fisicos(sellos, ajuste_x, ajuste_y)
        st.download_button(":material/download: DESCARGAR PDF DE SELLOS", pdf_out, "Sellos_Fisicos.pdf", use_container_width=True)

    st.markdown("<p style='font-weight: 800; font-size: 12px; letter-spacing: 1px;'>SELLADO DIGITAL (SOBRE PDF)</p>", unsafe_allow_html=True)
    with st.container(border=True):
        pdfs = st.file_uploader("Subir Facturas PDF", type="pdf", accept_multiple_files=True)
        if pdfs and st.button("EJECUTAR ESTAMPADO DIGITAL"):
            mapa = pd.Series(p_editado.RECOMENDACION.values, index=p_editado[p_editado.columns[0]].astype(str)).to_dict()
            z_buf = io.BytesIO()
            with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                for pdf in pdfs:
                    f_id = next((f for f in mapa.keys() if f in pdf.name.upper()), None)
                    if f_id:
                        zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa[f_id], ajuste_x, ajuste_y))
            st.download_button(":material/folder_zip: DESCARGAR ZIP SELLADO", z_buf.getvalue(), "Facturas_Digitales.zip", use_container_width=True)




























































































