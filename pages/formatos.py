import io
import re
import requests
import pandas as pd
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

# --- 1. FUNCIONES DE CONEXIÓN Y PROCESAMIENTO ---
@st.cache_data(ttl=60)
def cargar_csv_github():
    try:
        repo = "RH2026/nexion"
        filename = "facturacion_moreno.csv"
        branch = "main"
        
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filename}"
        token = st.secrets["GITHUB_TOKEN"]
        headers = {"Authorization": f"token {token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
            df.columns = df.columns.astype(str).str.strip()
            return df
        else:
            st.error(f"Error al descargar de GitHub (Código {response.status_code}).")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"No se pudo cargar el archivo CSV desde GitHub: {e}")
        return pd.DataFrame()

def limpiar_parentesis(texto):
    return re.sub(r'\(.*?\)', '', str(texto)).strip()

def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
    texto = str(texto).upper()
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    tamano_actual = tamano_max
    while len(lineas) > max_lineas and tamano_actual > 7:
        tamano_actual -= 0.5
        lineas = simpleSplit(texto, fuente, tamano_actual, ancho_max)
    
    c.setFont(fuente, tamano_actual)
    y_actual = y_inicio
    for line in lineas[:max_lineas]: 
        c.drawCentredString(x_centro, y_actual, line)
        y_actual -= interlineado
    return y_actual 

def generar_etiquetas_nexion(df_datos):
    output = io.BytesIO()
    
    # Dimensiones exactas de la etiqueta: 10.5 cm x 7.5 cm
    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
    
    # Margen lateral amplio
    margen_h = 0.8 * cm
    w_util = w_rec - (2 * margen_h)
    x_centro = w_rec / 2

    if df_datos.empty:
        c.save()
        return output.getvalue()

    for index, row in df_datos.iterrows():
        try:
            cantidad_real = int(row['Quantity'])
            iteraciones = cantidad_real
        except: 
            continue 

        nombre_crudo = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', row.get('NOMBRE_CLIENTE', 'SIN NOMBRE'))))
        nombre_final = limpiar_parentesis(nombre_crudo)
        direccion_final = row.get('DIRECCION', row.get('Domicilio', row.get('DOMICILIO', 'DIRECCIÓN NO DISPONIBLE')))
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', row.get('PAQUETERIA', 'TRES GUERRAS'))))
        factura_val = str(row.get('Factura', row.get('FOLIO', 'S/F')))

        for i in range(iteraciones):
            # Dibujar contorno de etiqueta
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(0, 0, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            # CABECERA JYPESA
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_centro, h_rec - 0.3*cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            c.setFont("Helvetica", 5.5)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(c, info_contacto, x_centro, h_rec - 0.7*cm, w_util, "Helvetica", 5.5, 0.25*cm, max_lineas=1)
            
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(margen_h, h_rec - 0.95*cm, w_rec - margen_h, h_rec - 0.95*cm)
            c.setStrokeColorRGB(0, 0, 0)

            # NOMBRE CLIENTE
            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_centro, h_rec - 1.8*cm, w_util, "Helvetica-Bold", 22, 0.65*cm, max_lineas=3)
            
            # DIRECCIÓN
            y_inicio_direccion = y_termino_nombre - 0.5*cm
            if y_inicio_direccion > 4.3*cm: y_inicio_direccion = 4.3*cm
            if y_inicio_direccion < 2.9*cm: y_inicio_direccion = 2.9*cm
            dibujar_texto_bloque_pro(c, direccion_final, x_centro, y_inicio_direccion, w_util, "Helvetica-Bold", 12.0, 0.45*cm, max_lineas=3)

            # PIE DE ETIQUETA
            c.setLineWidth(0.6)
            y_linea_pie = 1.4*cm
            c.line(margen_h, y_linea_pie, w_rec - margen_h, y_linea_pie)
            
            x_col1 = margen_h + 0.1*cm         
            x_col2 = 5.25 * cm                 
            x_col3 = w_rec - margen_h - 2.8*cm 

            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_col1, y_linea_pie - 0.4*cm, "FACTURA")
            c.drawCentredString(x_col2, y_linea_pie - 0.4*cm, "CAJAS")
            c.drawString(x_col3, y_linea_pie - 0.4*cm, "TRANSPORTE")
            
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_col1, y_linea_pie - 1.0*cm, factura_val)
            
            c.drawCentredString(x_col2, y_linea_pie - 1.0*cm, f"{i + 1} / {cantidad_real}")
            
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(x_col3, y_linea_pie - 1.0*cm, transporte_final[:16])
            
            c.showPage()

    c.save()
    return output.getvalue()

# --- 2. INTERFAZ DE USUARIO CON TABS ---
st.markdown("""
    <div style="
        background: linear-gradient(90deg, #2e3b4e 0%, #263243 100%);
        padding: 15px 25px;
        border-radius: 8px;
        border-left: 6px solid #4a90e2;
        margin-top: 20px;
        margin-bottom: 15px;
    ">
        <div style="color: #ffffff; font-size: 20px; font-weight: 300; margin-bottom: 2px;">
            Creador de Etiquetas de Embarque (NEXION)
        </div>
        <div style="color: #808495; font-size: 14px; font-weight: 400;">
            Generación y control de etiquetas por lote, base de datos o captura libre
        </div>
    </div>
    """, unsafe_allow_html=True)

# Creación de las tres pestañas
tab1, tab2, tab3 = st.tabs([
    "📁 Carga por Excel (Lote)", 
    "☁️ Base de Datos GitHub", 
    "✍️ Captura Manual Libre"
])

with tab1:
    st.subheader("Cargar Archivo Excel de Pedidos")
    archivo = st.file_uploader("Sube tu archivo .xlsx", type=["xlsx"], key="creador_etiquetas_excel")
    
    if archivo:
        try:
            df_excel = pd.read_excel(archivo, sheet_name=0)
            st.subheader("Vista previa de datos")
            st.dataframe(df_excel[['Quantity', 'DIRECCION', 'Factura']].head(5), use_container_width=True)

            if st.button("Generar Etiquetas desde Excel", use_container_width=True, key="btn_gen_excel"):
                with st.spinner("Generando documento..."):
                    pdf_data = generar_etiquetas_nexion(df_excel)
                    if pdf_data:
                        st.success("¡Documento generado con éxito!")
                        st.download_button(
                            label="Descargar PDF de Etiquetas",
                            data=pdf_data,
                            file_name="etiquetas_nexion_excel.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="dl_excel"
                        )
        except Exception as e:
            st.error(f"Error al leer los pedidos: {e}")

with tab2:
    st.subheader("Base de Datos - facturacion_moreno.csv")
    df_facturacion = cargar_csv_github()
    
    if not df_facturacion.empty:
        df_facturacion["Factura"] = df_facturacion["Factura"].astype(str)
        facturas_disponibles = df_facturacion["Factura"].unique()

        c_col1, c_col2 = st.columns(2)
        with c_col1:
            modo_busqueda = st.selectbox(
                "🔍 Método de Selección", 
                ["Seleccionar de la lista", "Escribir folio manual"],
                key="modo_busq_etq_github"
            )

        num_factura_seleccionada = None
        with c_col2:
            if modo_busqueda == "Seleccionar de la lista":
                num_factura_seleccionada = st.selectbox("📦 Selecciona Factura / Folio", facturas_disponibles, key="sel_factura_etq_github")
            else:
                num_factura_seleccionada = st.text_input("✍️ Ingresa Folio Manual", key="txt_folio_manual_etq_github")

        if num_factura_seleccionada:
            df_encontrado = df_facturacion[df_facturacion["Factura"] == str(num_factura_seleccionada).strip()]
            
            if not df_encontrado.empty:
                row_data = df_encontrado.iloc[0].copy()
                
                st.markdown("---")
                st.info(f"📋 **Cliente encontrado:** {row_data.get('Nombre_Extran', row_data.get('Nombre_Cliente', 'SIN NOMBRE'))}")
                
                col_c, col_t = st.columns(2)
                with col_c:
                    cajas_manual = st.number_input("📦 Cantidad de Cajas / Bultos", min_value=1, value=1, step=1, key="num_cajas_manual_db")
                with col_t:
                    transporte_manual = st.text_input("🚛 Transporte / Paquetería", value=str(row_data.get('RECOMENDACION', row_data.get('Transporte', 'TRES GUERRAS'))), key="txt_transporte_manual_db")
                
                row_data['Quantity'] = cajas_manual
                row_data['RECOMENDACION'] = transporte_manual
                
                df_procesar_individual = pd.DataFrame([row_data])

                if st.button("Generar Etiqueta Individual", use_container_width=True, key="btn_gen_moreno"):
                    with st.spinner("Generando etiqueta..."):
                        pdf_data_moreno = generar_etiquetas_nexion(df_procesar_individual)
                        if pdf_data_moreno:
                            st.success("¡Etiqueta generada con éxito!")
                            st.download_button(
                                label="Descargar PDF de Etiqueta",
                                data=pdf_data_moreno,
                                file_name=f"etiqueta_factura_{num_factura_seleccionada}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="dl_moreno"
                            )
            else:
                st.warning("El folio ingresado no se encontró en la base de datos de GitHub.")
    else:
        st.warning("No se pudieron cargar los datos de GitHub. Verifica tu token o conexión.")

with tab3:
    st.markdown("""
        <div style="background-color: #263243; padding: 10px 15px; border-radius: 5px; color: #ffffff; font-size: 14px; margin-bottom: 20px;">
            Ingresa los datos del envío manualmente (sin necesidad de archivos).
        </div>
    """, unsafe_allow_html=True)

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        manual_factura = st.text_input("NÚMERO DE FACTURA / FOLIO", value="JYP-100", key="man_factura")
        manual_nombre = st.text_input("NOMBRE DEL CLIENTE / HOTEL", value="HOTEL EJEMPLO", key="man_nombre")
        manual_cajas = st.number_input("CANTIDAD DE CAJAS / BULTOS", min_value=1, value=1, step=1, key="man_cajas")

    with col_m2:
        manual_direccion = st.text_area("DIRECCIÓN COMPLETA DE DESTINO", value="Av. Principal #123, Col. Centro, C.P. 44100, Guadalajara, Jal.", height=107, key="man_direccion")
        manual_transporte = st.text_input("TRANSPORTE / PAQUETERÍA", value="TRES GUERRAS", key="man_transporte")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Generar Etiqueta Manual", use_container_width=True, key="btn_gen_manual_libre"):
        if not manual_factura or not manual_nombre or not manual_direccion:
            st.error("Por favor completa los campos obligatorios (Factura, Nombre y Dirección).")
        else:
            # Creamos un DataFrame con una sola fila usando los datos manuales
            dict_manual = {
                'Factura': str(manual_factura),
                'Nombre_Cliente': str(manual_nombre),
                'DIRECCION': str(manual_direccion),
                'Quantity': int(manual_cajas),
                'RECOMENDACION': str(manual_transporte)
            }
            df_manual_pro = pd.DataFrame([dict_manual])

            with st.spinner("Generando etiqueta manual..."):
                pdf_data_manual = generar_etiquetas_nexion(df_manual_pro)
                if pdf_data_manual:
                    st.success("¡Etiqueta manual generada con éxito!")
                    st.download_button(
                        label="Descargar PDF de Etiqueta Manual",
                        data=pdf_data_manual,
                        file_name=f"etiqueta_manual_{manual_factura}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_manual_libre"
                    )












































































































































