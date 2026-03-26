import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Etiquetas Centradas Pro")

# --- FUNCIÓN PARA TEXTO MULTILÍNEA CENTRADO ---
def dibujar_texto_bloque(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado):
    texto = str(texto).upper()
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    # Si salen muchas líneas, bajamos un poco la fuente
    if len(lineas) >= 3:
        tamano_max -= 2
        lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)

    c.setFont(fuente, tamano_max)
    y_actual = y_inicio
    for line in lineas[:3]: 
        c.drawCentredString(x_centro, y_actual, line)
        y_actual -= interlineado
    return y_actual # Devolvemos dónde terminó de escribir

def generar_etiquetas_nexion(df):
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    width_carta, height_carta = letter

    # Medidas de la etiqueta (1/4 de media carta aprox: 10.5 x 7.5 cm)
    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    x_offset, y_offset = 1.0 * cm, height_carta - h_rec - 1.0 * cm

    for index, row in df.iterrows():
        try:
            cantidad = int(row['Quantity'])
        except: continue 

        # Datos del destinatario
        nombre_final = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', 'SIN NOMBRE')))
        direccion_final = row.get('DIRECCION', 'DIRECCIÓN NO DISPONIBLE')
        
        # Datos de control
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', '')))

        for i in range(cantidad):
            # Dibujamos el borde
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            # --- CABECERA (DATOS DE TU EMPRESA - CORREGIDOS Y CENTRADOS) ---
            
            # Línea 1: Nombre de la empresa (AQUÍ ESTÁ LA CORRECCIÓN DE CENTRADO)
            c.setFont("Helvetica-Bold", 7)
            nombre_empresa = "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV"
            # Ahora usamos drawCentredString
            c.drawCentredString(x_offset + (w_rec/2), y_offset + h_rec - 0.4*cm, nombre_empresa)
            
            # Línea 2: Dirección y Teléfono (Sigue centrada)
            c.setFont("Helvetica", 6)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            
            dibujar_texto_bloque(
                c, info_contacto, 
                x_offset + (w_rec/2), # Centrado
                y_offset + h_rec - 0.8*cm, 
                10*cm, "Helvetica", 6, 0.3*cm
            )

            # --- DESTINATARIO (DATOS DEL CLIENTE) ---
            # 1. NOMBRE (PROTAGONISTA 1 - Centrado)
            c.setStrokeColorRGB(0.2, 0.2, 0.2) 
            y_termino_nombre = dibujar_texto_bloque(
                c, nombre_final, 
                x_offset + (w_rec/2), 
                y_offset + h_rec - 1.8*cm, 
                10*cm, "Helvetica-Bold", 18, 0.7*cm
            )

            # 2. DIRECCIÓN (PROTAGONISTA 2 - Centrado)
            dibujar_texto_bloque(
                c, direccion_final, 
                x_offset + (w_rec/2), 
                y_offset + 3.0*cm, 
                10*cm, "Helvetica-Bold", 11, 0.4*cm
            )

            # --- PIE DE ETIQUETA (Datos de control) ---
            c.setLineWidth(0.5)
            c.setStrokeColorRGB(0, 0, 0) 
            c.line(x_offset + 0.2*cm, y_offset + 1.4*cm, x_offset + w_rec - 0.2*cm, y_offset + 1.4*cm)

            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.5*cm, y_offset + 1.0*cm, "FACTURA")
            c.drawString(x_offset + 4.0*cm, y_offset + 1.0*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.0*cm, y_offset + 1.0*cm, "TRANSPORTE")

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_offset + 0.5*cm, y_offset + 0.4*cm, str(row.get('Factura', '')))
            
            texto_cajas = f"{i + 1}  /  {cantidad}"
            # Centramos también las cajas
            c.drawCentredString(x_offset + 5.0*cm, y_offset + 0.4*cm, texto_cajas)
            
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_offset + 7.0*cm, y_offset + 0.4*cm, transporte_final[:20])

            c.showPage()

    c.save()
    return output.getvalue()

# --- INTERFAZ ---
st.header("📦 NEXION - Etiquetas Premium (Centrado Pro)")
st.info("Sube tu Excel y tus datos ya están integrados automáticamente y perfectamente CENTRADOS en la cabecera.")

archivo = st.file_uploader("Sube tu Excel de Logística", type=["xlsx"])

if archivo:
    try:
        df = pd.read_excel(archivo, sheet_name=0)
        st.dataframe(df.head(), use_container_width=True)
        
        if st.button("🚀 Generar PDF"):
            with st.spinner("Creando etiquetas perfectas..."):
                pdf_bytes = generar_etiquetas_nexion(df)
                st.success("¡Etiquetas perfectamente centradas listas para descargar!")
                st.download_button("📥 Descargar PDF", pdf_bytes, "etiquetas_centradas_pro.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")






















































































































































