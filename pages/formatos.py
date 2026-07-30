import io
import re
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.utils import simpleSplit

# --- 1. FUNCIONES DE PROCESAMIENTO ---
def limpiar_parentesis(texto):
    return re.sub(r'\(.*?\)', '', str(texto)).strip()

def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
    texto = str(texto).upper()
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    tamano_actual = tamano_max
    while len(lineas) > max_lineas and tamano_actual > 8:
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
    
    # Configuramos el Canvas con el tamaño exacto de la etiqueta (sin hoja carta completa)
    c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
    
    # Como el canvas mide exactamente la etiqueta, el offset inicial es 0,0
    x_offset, y_offset = 0.0, 0.0

    for index, row in df.iterrows():
        try:
            cantidad_real = int(row['Quantity'])
            iteraciones = cantidad_real  # Sin la copia extra de Moreno
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
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            # CABECERA JYPESA
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_offset + (w_rec/2), y_offset + h_rec - 0.3*cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            c.setFont("Helvetica", 6)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(c, info_contacto, x_offset + (w_rec/2), y_offset + h_rec - 0.7*cm, 10*cm, "Helvetica", 6, 0.25*cm, max_lineas=1)
            
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(x_offset + 0.5*cm, y_offset + h_rec - 1.0*cm, x_offset + w_rec - 0.5*cm, y_offset + h_rec - 1.0*cm)
            c.setStrokeColorRGB(0, 0, 0)

            # NOMBRE CLIENTE (GIGANTE)
            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_offset + (w_rec/2), y_offset + h_rec - 2.0*cm, 10*cm, "Helvetica-Bold", 26, 0.75*cm, max_lineas=3)
            
            # DIRECCIÓN (14.5pt)
            y_inicio_direccion = y_termino_nombre - 0.7*cm
            if y_inicio_direccion > y_offset + 4.3*cm: y_inicio_direccion = y_offset + 4.3*cm
            if y_inicio_direccion < y_offset + 2.9*cm: y_inicio_direccion = y_offset + 2.9*cm
            dibujar_texto_bloque_pro(c, direccion_final, x_offset + (w_rec/2), y_inicio_direccion, 10.0 * cm, "Helvetica-Bold", 14.5, 0.5*cm, max_lineas=3)

            # PIE DE ETIQUETA
            c.setLineWidth(0.6)
            y_linea_pie = y_offset + 1.4*cm
            c.line(x_offset + 0.2*cm, y_linea_pie, x_offset + w_rec - 0.2*cm, y_linea_pie)
            
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.4*cm, "FACTURA")
            c.drawCentredString(x_offset + 5.2*cm, y_linea_pie - 0.4*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.5*cm, y_linea_pie - 0.4*cm, "TRANSPORTE")
            
            c.setFont("Helvetica-Bold", 13)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 1.0*cm, str(row.get('Factura', '')))
            
            # Numeración de cajas actual (ej. 1/3, 2/3, etc.)
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(x_offset + 5.2*cm, y_linea_pie - 1.0*cm, f"{i + 1} / {cantidad_real}")
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_offset + 7.5*cm, y_linea_pie - 1.0*cm, transporte_final[:18])
            
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
                
                st.info("El archivo se guardará en tu carpeta de descargas.")












































































































































