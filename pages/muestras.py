import os
import io
import zipfile
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter
import streamlit as st

if st.session_state.menu_sub == "SMART ROUTING":
    st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>LOGISTICS INTELLIGENCE HUB | XENOCODE CORE</p>", unsafe_allow_html=True)
    
    # --- 1. MOTOR Y FUNCIONES ---
    try:
        d_flet, d_price = motor_logistico_central()
    except:
        d_flet, d_price = {}, {}
        st.warning("Motor logístico no detectado. Cargando modo manual.")

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
        return output

    # --- 2. ÁREA DE CARGA ERP ---
    uploaded_file = st.file_uploader("Subir archivo ERP", type=["xlsx", "csv"], label_visibility="collapsed")
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
            else:
                df = pd.read_excel(uploaded_file)
            
            # Limpieza de columnas
            df.columns = [str(c).strip().replace('\n', '').replace('\t', '') for c in df.columns]
            
            # Identificación de columnas críticas
            col_folio = next((c for c in df.columns if 'factura' in c.lower() or 'docnum' in c.lower()), df.columns[0])
            col_dir = next((c for c in df.columns if any(x in c.lower() for x in ['dir', 'destin', 'ciudad'])), None)
            col_transporte = next((c for c in df.columns if 'transporte' in c.lower()), None)

            # --- 3. PANEL DE CONTROL (FILTROS Y SELECCIÓN) ---
            st.markdown("<br>", unsafe_allow_html=True)
            col_left, col_right = st.columns([1, 2], gap="large")
            
            with col_left:
                st.markdown(f"<p class='op-query-text' style='text-align:left !important;'>FILTROS DE RANGO</p>", unsafe_allow_html=True)
                df[col_folio] = pd.to_numeric(df[col_folio], errors='coerce')
                df_clean = df.dropna(subset=[col_folio])
                
                inicio = st.number_input("Folio Inicial", value=int(df_clean[col_folio].min()))
                final = st.number_input("Folio Final", value=int(df_clean[col_folio].max()))
                df_rango = df_clean[(df_clean[col_folio] >= inicio) & (df_clean[col_folio] <= final)].copy()

            with col_right:
                st.markdown(f"<p class='op-query-text' style='text-align:left !important;'>SELECCIÓN DE FOLIOS</p>", unsafe_allow_html=True)
                if not df_rango.empty:
                    # Agrupamos para mostrar folios únicos
                    info_folios = df_rango.drop_duplicates(subset=[col_folio])[[col_folio]].copy()
                    if col_transporte: info_folios[col_transporte] = df_rango.drop_duplicates(subset=[col_folio])[col_transporte]
                    
                    selector_df = info_folios.copy()
                    selector_df.insert(0, "Incluir", True)
                    
                    edited_df = st.data_editor(selector_df, hide_index=True, use_container_width=True, key="editor_folios_v4")
                else:
                    st.warning("Sin datos en el rango.")

            # --- 4. EJECUCIÓN DEL MOTOR (UNIFICADO) ---
            st.markdown("---")
            if not df_rango.empty and st.button("🚀 EJECUTAR SMART ROUTING", use_container_width=True):
                folios_finales = edited_df[edited_df["Incluir"] == True][col_folio].tolist()
                
                # Tabla base para el motor (Sin duplicados de folios para no repetir análisis)
                df_motor = df_rango[df_rango[col_folio].isin(folios_finales)].drop_duplicates(subset=[col_folio]).copy()

                if not df_motor.empty:
                    def motor_prioridad(row):
                        addr = str(row.get(col_dir, "")).upper()
                        # Lógica Local
                        if any(loc in addr for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA"]):
                            return "LOCAL NEXION", 0.0
                        # Lógica por Diccionario
                        res = d_flet.get(addr, "SIN HISTORIAL")
                        costo = d_price.get(addr, 0.0)
                        return res, costo

                    # Aplicar motor
                    resultados = df_motor.apply(motor_prioridad, axis=1)
                    df_motor['RECOMENDACION'] = [r[0] for r in resultados]
                    df_motor['COSTO'] = [r[1] for r in resultados]
                    df_motor['FECHA_SISTEMA'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Guardar en session_state para persistencia
                    st.session_state.df_analisis = df_motor

            # --- 5. RENDERIZADO DE RESULTADOS Y SELLADO ---
            if "df_analisis" in st.session_state:
                st.markdown("### :material/analytics: RESULTADOS DEL ANÁLISIS")
                
                # Editor para ajustes manuales de fletera o costo
                p_editado = st.data_editor(
                    st.session_state.df_analisis,
                    use_container_width=True,
                    column_config={
                        "RECOMENDACION": st.column_config.TextColumn("FLETERA RECOMENDADA"),
                        "COSTO": st.column_config.NumberColumn("TARIFA", format="$%.2f"),
                    },
                    key="editor_resultados_final"
                )

                # Sistema de Sellado
                st.markdown("---")
                st.markdown("#### :material/print: SISTEMA DE SELLADO")
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    adj_x = st.slider("Ajuste X (Sello)", 0, 600, 510)
                with col_c2:
                    adj_y = st.slider("Ajuste Y (Sello)", 0, 800, 760)

                pdfs = st.file_uploader("Subir Facturas para Sello Digital", type="pdf", accept_multiple_files=True)
                
                if pdfs and st.button("EJECUTAR ESTAMPADO DIGITAL"):
                    # Mapa para buscar fletera por folio
                    mapa_sellos = pd.Series(p_editado.RECOMENDACION.values, index=p_editado[col_folio].astype(str)).to_dict()
                    
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a") as zf:
                        for pdf in pdfs:
                            # Buscar el folio en el nombre del archivo
                            f_id = next((f for f in mapa_sellos.keys() if f in pdf.name), None)
                            if f_id:
                                stamped_pdf = marcar_pdf_digital(pdf, mapa_sellos[f_id], adj_x, adj_y)
                                out_io = io.BytesIO()
                                stamped_pdf.write(out_io)
                                zf.writestr(f"SELLADO_{pdf.name}", out_io.getvalue())
                    
                    st.download_button(":material/folder_zip: DESCARGAR ZIP SELLADO", z_buf.getvalue(), "Facturas_Selladas.zip", use_container_width=True)

        except Exception as e:
            st.error(f"Error en el flujo: {e}")
    else:
        # Tu animación CSS de "Waiting for data" que ya tenías
        st.markdown("<div style='text-align:center; padding:50px; opacity:0.5;'>WAITING FOR ERP DATA...</div>", unsafe_allow_html=True)
























































































