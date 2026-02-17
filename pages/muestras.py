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
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #54AFE7; color: white; }
    .op-query-text { color: #54AFE7; font-weight: bold; letter-spacing: 1px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- MOCKS / FUNCIONES DE APOYO (Sustituir por tus imports) ---
def motor_logistico_central():
    # Simulando tus diccionarios de rutas
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

# --- INICIO DE LA APLICACIÓN ---
st.title("🚀 SMART ROUTING & LOGISTICS HUB")
st.markdown("---")

# 1. ÁREA DE CARGA
uploaded_file = st.file_uploader("📂 SUBIR ARCHIVO ERP (Excel o CSV)", type=["xlsx", "csv"])

if uploaded_file:
    # Carga de datos
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
    else:
        df = pd.read_excel(uploaded_file)

    # Limpieza de columnas
    df.columns = [str(c).strip().replace('\n', '').replace('\t', '') for c in df.columns]
    
    # Identificación de columnas (Factura y Dirección)
    col_folio = next((c for c in df.columns if 'factura' in c.lower() or 'docnum' in c.lower()), df.columns[0])
    col_dir = next((c for c in df.columns if any(x in c.lower() for x in ['dir', 'destin', 'ciudad', 'ubicacion'])), None)

    # 2. SECCIÓN DE PREPARACIÓN (S&T)
    st.subheader("1. Preparación de Documentos (S&T)")
    
    col_f1, col_f2 = st.columns([1, 2])
    
    with col_f1:
        st.markdown("<p class='op-query-text'>FILTROS DE RANGO</p>", unsafe_allow_html=True)
        df[col_folio] = pd.to_numeric(df[col_folio], errors='coerce')
        df_clean = df.dropna(subset=[col_folio])
        
        f_min, f_max = int(df_clean[col_folio].min()), int(df_clean[col_folio].max())
        inicio = st.number_input("Desde Folio:", value=f_min)
        final = st.number_input("Hasta Folio:", value=f_max)
        
        df_rango = df_clean[(df_clean[col_folio] >= inicio) & (df_clean[col_folio] <= final)].copy()

    with col_right := col_f2:
        st.markdown("<p class='op-query-text'>SELECCIÓN INDIVIDUAL DE FOLIOS</p>", unsafe_allow_html=True)
        # Mostramos folios únicos para la selección
        info_folios = df_rango.drop_duplicates(subset=[col_folio])[[col_folio]].copy()
        info_folios.insert(0, "Incluir", True)
        
        edited_selection = st.data_editor(
            info_folios, 
            hide_index=True, 
            use_container_width=True,
            key="selector_master"
        )

    # 3. MOTOR DE RECOMENDACIÓN (LOGÍSTICA)
    st.markdown("---")
    st.subheader("2. Motor de Recomendación Inteligente")
    
    if st.button("🚀 EJECUTAR ANÁLISIS DE RUTAS"):
        # Filtrar solo los folios que el usuario dejó marcados en la tabla de arriba
        folios_ok = edited_selection[edited_selection["Incluir"] == True][col_folio].tolist()
        
        # IMPORTANTE: Eliminamos duplicados de facturas para que el motor trabaje sobre folios únicos
        df_logistica = df_rango[df_rango[col_folio].isin(folios_ok)].drop_duplicates(subset=[col_folio]).copy()
        
        if not df_logistica.empty:
            d_flet, d_price = motor_logistico_central()

            def motor_nexion(row):
                # Obtener dirección, si no existe col_dir usamos un string vacío
                addr = str(row.get(col_dir, "")).upper()
                
                # Regla Local GDL
                locales = ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA", "TLAJOMULCO"]
                if any(loc in addr for loc in locales):
                    return "ENTREGA LOCAL", 0.0
                
                # Búsqueda en Diccionario (Match parcial)
                for ciudad, fletera in d_flet.items():
                    if ciudad.upper() in addr:
                        return fletera, d_price.get(ciudad, 0.0)
                
                return "REVISIÓN MANUAL", 0.0

            # Aplicamos la magia
            resultados = df_logistica.apply(motor_nexion, axis=1)
            df_logistica['RECOMENDACION'] = [r[0] for r in resultados]
            df_logistica['COSTO'] = [r[1] for r in resultados]
            df_logistica['TIMESTAMP'] = datetime.now().strftime("%H:%M:%S")
            
            # Guardamos el resultado en el estado de la sesión
            st.session_state.df_final = df_logistica
            st.success("Análisis completado con éxito.")

    # 4. TABLA DE RESULTADOS EDITABLE
    if "df_final" in st.session_state:
        st.markdown("<p class='op-query-text'>LOGÍSTICA SUGERIDA</p>", unsafe_allow_html=True)
        
        # Permitimos que el usuario corrija la fletera o el costo si es necesario
        df_editado = st.data_editor(
            st.session_state.df_final,
            use_container_width=True,
            column_config={
                "RECOMENDACION": st.column_config.SelectboxColumn(
                    "FLETERA", 
                    options=["ENTREGA LOCAL", "TRES GUERRAS", "PMM", "CASTORES", "REVISIÓN MANUAL"]
                ),
                "COSTO": st.column_config.NumberColumn("TARIFA", format="$%.2f")
            },
            hide_index=True
        )

        # 5. SISTEMA DE SELLADO
        st.markdown("---")
        st.subheader("3. Sellado Digital de Facturas")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            x_pos = st.slider("Posición Horizontal (X)", 0, 612, 510)
        with col_s2:
            y_pos = st.slider("Posición Vertical (Y)", 0, 792, 760)

        pdf_files = st.file_uploader("Subir archivos PDF para sellado", type="pdf", accept_multiple_files=True)
        
        if pdf_files and st.button("⚡ GENERAR FACTURAS SELLADAS"):
            # Mapa de Folio -> Fletera
            mapa_rutas = pd.Series(df_editado.RECOMENDACION.values, index=df_editado[col_folio].astype(str)).to_dict()
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a") as zf:
                for pdf in pdf_files:
                    # Buscamos si el folio está en el nombre del archivo
                    match_folio = next((f for f in mapa_rutas.keys() if f in pdf.name), None)
                    
                    if match_folio:
                        texto_a_imprimir = mapa_rutas[match_folio]
                        pdf_stamped = marcar_pdf_digital(pdf, texto_a_imprimir, x_pos, y_pos)
                        
                        # Guardar PDF en el ZIP
                        pdf_io = io.BytesIO()
                        pdf_stamped.write(pdf_io)
                        zf.writestr(f"SELLADO_{pdf.name}", pdf_io.getvalue())
            
            st.download_button(
                label="📥 DESCARGAR TODAS LAS FACTURAS (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"Rutas_Selladas_{datetime.now().strftime('%d%m%Y')}.zip",
                mime="application/zip"
            )

else:
    # Estado inicial cuando no hay archivo
    st.info("👋 Bienvenida. Por favor sube un archivo Excel o CSV para comenzar el proceso logístico.")

























































































