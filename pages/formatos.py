import io
import re
import pandas as pd
import streamlit as st
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

# --- 1. FUNCIONES DE PROCESAMIENTO ---
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

def generar_etiquetas_nexion(df):
    output = io.BytesIO()
    
    # Dimensiones exactas de la etiqueta: 10.5 cm x 7.5 cm
    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
    
    # Margen lateral un poco más amplio (0.8 cm a cada lado para dejar más espacio)
    margen_h = 0.8 * cm
    w_util = w_rec - (2 * margen_h)
    x_centro = w_rec / 2

    for index, row in df.iterrows():
        try:
            cantidad_real = int(row['Quantity'])
            iteraciones = cantidad_real
        except: 
            continue 

        nombre_crudo = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', 'SIN NOMBRE')))
        nombre_final = limpiar_parentesis(nombre_crudo)
        direccion_final = row.get('DIRECCION', 'DIRECCIÓN NO DISPONIBLE')
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', 'TRES GUERRAS')))

        for i in range(iteraciones):
            # Dibujar contorno de etiqueta
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(0, 0, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            # CABECERA JYPESA
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_centro, y_rec_sup := (h_rec - 0.3*cm), "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            c.setFont("Helvetica", 5.5)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(c, info_contacto, x_centro, h_rec - 0.7*cm, w_util, "Helvetica", 5.5, 0.25*cm, max_lineas=1)
            
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(margen_h, h_rec - 0.95*cm, w_rec - margen_h, h_rec - 0.95*cm)
            c.setStrokeColorRGB(0, 0, 0)

            # NOMBRE CLIENTE (Ligeramente más chico para que quepa holGado con más margen)
            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_centro, h_rec - 1.8*cm, w_util, "Helvetica-Bold", 22, 0.65*cm, max_lineas=3)
            
            # DIRECCIÓN (Reducida a 12pt para dar espacio y evitar que pegue abajo)
            y_inicio_direccion = y_termino_nombre - 0.5*cm
            if y_inicio_direccion > 4.3*cm: y_inicio_direccion = 4.3*cm
            if y_inicio_direccion < 2.9*cm: y_inicio_direccion = 2.9*cm
            dibujar_texto_bloque_pro(c, direccion_final, x_centro, y_inicio_direccion, w_util, "Helvetica-Bold", 12.0, 0.45*cm, max_lineas=3)

            # PIE DE ETIQUETA
            c.setLineWidth(0.6)
            y_linea_pie = 1.4*cm
            c.line(margen_h, y_linea_pie, w_rec - margen_h, y_linea_pie)
            
            c.setFont("Helvetica-Bold", 8)
            c.drawString(margen_h, y_linea_pie - 0.4*cm, "FACTURA")
            c.drawCentredString(x_centro, y_linea_pie - 0.4*cm, "CAJAS / BULTO")
            c.drawString(w_rec - margen_h - 3.5*cm, y_linea_pie - 0.4*cm, "TRANSPORTE")
            
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margen_h, y_linea_pie - 1.0*cm, str(row.get('Factura', '')))
            
            c.drawCentredString(x_centro, y_linea_pie - 1.0*cm, f"{i + 1} / {cantidad_real}")
            
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(w_rec - margen_h - 3.5*cm, y_linea_pie - 1.0*cm, transporte_final[:16])
            
            c.showPage()

    c.save()
    return output.getvalue()

# --- 2. INTERFAZ DE USUARIO ---
st.markdown("""
    <div style="
        background: linear-gradient(90deg, #2e3b4e 0%, #263243 100%);
        padding: 15px 25px;
        border-radius: 8px;
        border-left: 6px solid #4a90e2;
        margin-top: 20px;
        margin-bottom: 10px;
    ">
        <div style="color: #ffffff; font-size: 20px; font-weight: 300; margin-bottom: 2px;">
            Creador de Etiquetas de Embarque
        </div>
        <div style="color: #808495; font-size: 14px; font-weight: 400;">
            Cargar Excel de Pedidos para procesamiento
        </div>
    </div>
    """, unsafe_allow_html=True)

archivo = st.file_uploader("", type=["xlsx"], label_visibility="collapsed", key="creador_etiquetas")

if archivo:
    try:
        df = pd.read_excel(archivo, sheet_name=0)
    except Exception as e:
        st.error(f"Error al leer los pedidos: {e}")

    st.subheader("Vista previa de datos")
    st.dataframe(df[['Quantity', 'DIRECCION', 'Factura']].head(5), use_container_width=True)

    if st.button("Generar Etiquetas", use_container_width=True):
        with st.spinner("Generando documento..."):
            pdf_data = generar_etiquetas_nexion(df)
            
            if pdf_data:
                st.success("¡Documento generado con éxito!")
                st.download_button(
                    label="Descargar PDF para Imprimir",
                    data=pdf_data,
                    file_name="etiquetas_nexion.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )












































































































































