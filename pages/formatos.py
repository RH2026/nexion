import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
import io
import re  # Importamos para limpiar los paréntesis

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Etiquetas Clean")

# --- FUNCIÓN PARA LIMPIAR PARÉNTESIS ---
def limpiar_parentesis(texto):
    # Esta línea borra todo lo que esté entre ( ) incluyendo los paréntesis
    return re.sub(r'\(.*?\)', '', str(texto)).strip()

# --- FUNCIÓN PARA TEXTO MULTILÍNEA DE ALTO IMPACTO ---
def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
    texto = str(texto).upper()
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    tamano_actual = tamano_max
    while len(lineas) > max_lineas and tamano_actual > 8:
        tamano_actual -= 0.5
        lineas = simpleSplit(texto, fuente, tamano_actual, ancho_max)

    c.setFont(fuente, tamano_actual)
    y_actual = y_inicio
    for line in lineas[:3]: 
        c.drawCentredString(x_centro, y_actual, line)
        y_actual -= interlineado
    return y_actual

def generar_etiquetas_nexion(df):
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    width_carta, height_carta = letter

    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    x_offset, y_offset = 1.0 * cm, height_carta - h_rec - 1.0 * cm

    for index, row in df.iterrows():
        try:
            cantidad_real = int(row['Quantity'])
            iteraciones = cantidad_real + 1 
        except: continue 

        # --- LIMPIEZA DEL NOMBRE ---
        # Primero agarramos el dato del Excel
        nombre_crudo = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', 'SIN NOMBRE')))
        # ¡Aquí le quitamos los paréntesis, amor!
        nombre_final = limpiar_parentesis(nombre_crudo)
        
        direccion_final = row.get('DIRECCION', 'DIRECCIÓN NO DISPONIBLE')
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', 'TRES GUERRAS')))

        for i in range(iteraciones):
            es_archivo = (i == cantidad_real)
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

            if es_archivo:
                c.setFont("Helvetica-Bold", 35)
                c.setStrokeColorRGB(0.9, 0.9, 0.9)
                c.setFillColorRGB(0.9, 0.9, 0.9)
                c.drawCentredString(x_offset + (w_rec/2), y_offset + (h_rec/2) - 1*cm, "ARCHIVO")
                c.setFillColorRGB(0, 0, 0)

            # NOMBRE (Sin paréntesis y en gigante)
            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_offset + (w_rec/2), y_offset + h_rec - 2.5*cm, 10*cm, "Helvetica-Bold", 26, 0.8*cm, max_lineas=3)

            # DIRECCIÓN (Bajada para espacio vital)
            y_inicio_direccion = y_termino_nombre - 0.8*cm
            if y_inicio_direccion < y_offset + 2.8*cm: y_inicio_direccion = y_offset + 3.0*cm 

            dibujar_texto_bloque_pro(c, direccion_final, x_offset + (w_rec/2), y_inicio_direccion, 10.0 * cm, "Helvetica-Bold", 12, 0.45*cm, max_lineas=3)

            # PIE DE ETIQUETA
            c.setLineWidth(0.5)
            y_linea_pie = y_offset + 1.2*cm
            c.line(x_offset + 0.2*cm, y_linea_pie, x_offset + w_rec - 0.2*cm, y_linea_pie)
            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.3*cm, "FACTURA")
            c.drawString(x_offset + 4.0*cm, y_linea_pie - 0.3*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.0*cm, y_linea_pie - 0.3*cm, "TRANSPORTE")
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.8*cm, str(row.get('Factura', '')))
            
            if es_archivo:
                c.drawCentredString(x_offset + 5.0*cm, y_linea_pie - 0.8*cm, "COPIA CONTROL")
            else:
                c.drawCentredString(x_offset + 5.0*cm, y_linea_pie - 0.8*cm, f"{i + 1} / {cantidad_real}")
            
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_offset + 7.0*cm, y_linea_pie - 0.8*cm, transporte_final[:20])
            c.showPage()

    c.save()
    return output.getvalue()

# INTERFAZ
st.header("📦 NEXION - Etiquetas Clean")
archivo = st.file_uploader("Sube tu Excel", type=["xlsx"])
if archivo:
    df = pd.read_excel(archivo, sheet_name=0)
    st.dataframe(df.head(), use_container_width=True)
    if st.button("🚀 Generar Etiquetas"):
        pdf_bytes = generar_etiquetas_nexion(df)
        st.success("¡Etiquetas generadas sin paréntesis!")
        st.download_button("📥 Descargar PDF", pdf_bytes, "etiquetas_nexion_clean.pdf", "application/pdf")






















































































































































