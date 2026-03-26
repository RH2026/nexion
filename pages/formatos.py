import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Etiquetas High Impact")

# --- FUNCIÓN PARA TEXTO MULTILÍNEA DE ALTO IMPACTO ---
def dibujar_texto_bloque(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado):
    """
    Divide el texto en líneas y las dibuja centradas, manteniendo un tamaño de fuente legible.
    """
    texto = str(texto).upper()
    # Dividir el texto para que quepa en el ancho
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    # Si salen muchas líneas, bajamos un poco la fuente
    if len(lineas) > 2:
        tamano_max -= 2
        lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)

    c.setFont(fuente, tamano_max)
    y_actual = y_inicio
    for line in lineas[:3]: # Limitamos a 3 líneas para no encimar con el pie
        c.drawCentredString(x_centro, y_actual, line)
        y_actual -= interlineado
    return y_actual

def generar_etiquetas_nexion(df):
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    width_carta, height_carta = letter

    # Medidas de 1/4 de media carta (Aprox 10.5 x 7.5 cm)
    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    x_offset, y_offset = 1.0 * cm, height_carta - h_rec - 1.0 * cm

    for index, row in df.iterrows():
        try:
            cantidad = int(row['Quantity'])
        except: continue 

        # Prioridad de Nombre
        nombre_final = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', 'SIN NOMBRE')))
        direccion_final = row.get('DIRECCION', 'DIRECCIÓN NO DISPONIBLE')

        for i in range(cantidad):
            # Dibujamos el borde de la etiqueta
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            # 1. CLIENTE (Dato de referencia, arriba a la izquierda)
            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 0.4*cm, "CLIENTE:")
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 0.8*cm, str(row.get('Nombre_Cliente', ''))[:50])

            # 2. NOMBRE EXTRAN (EL PROTAGONISTA 1)
            # Posicionado arriba, fuente muy grande
            y_despues_nombre = dibujar_texto_bloque(
                c, nombre_final, 
                x_offset + (w_rec/2), 
                y_offset + h_rec - 2.2*cm, 
                10*cm, "Helvetica-Bold", 22, 0.8*cm
            )

            # 3. DIRECCIÓN (EL PROTAGONISTA 2)
            # Posicionada en el centro del espacio restante
            dibujar_texto_bloque(
                c, direccion_final, 
                x_offset + (w_rec/2), 
                y_offset + 3.8*cm, 
                10*cm, "Helvetica-Bold", 12, 0.45*cm
            )

            # 4. PIE DE ETIQUETA (Datos de control)
            # Línea divisoria para el pie
            c.setLineWidth(0.5)
            c.line(x_offset + 0.2*cm, y_offset + 1.4*cm, x_offset + w_rec - 0.2*cm, y_offset + 1.4*cm)

            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.5*cm, y_offset + 1.0*cm, "FACTURA")
            c.drawString(x_offset + 4.0*cm, y_offset + 1.0*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.5*cm, y_offset + 1.0*cm, "TRANSPORTE")

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_offset + 0.5*cm, y_offset + 0.4*cm, str(row.get('Factura', '')))
            
            # Cajas con formato resaltado
            texto_cajas = f"{i + 1}  /  {cantidad}"
            c.drawCentredString(x_offset + 5.2*cm, y_offset + 0.4*cm, texto_cajas)
            
            c.setFont("Helvetica-Bold", 8)
            trans = str(row.get('Transporte', row.get('RECOMENDACION', 'TRES GUERRAS')))
            c.drawString(x_offset + 7.5*cm, y_offset + 0.4*cm, trans[:18])

            c.showPage()

    c.save()
    return output.getvalue()

# --- INTERFAZ ---
st.header("📦 NEXION - Etiquetas de Alto Impacto")
st.markdown("La dirección y el nombre ahora son los **protagonistas** de la impresión.")

archivo = st.file_uploader("Sube tu Excel de Logística", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo, sheet_name=0)
    st.dataframe(df.head(), use_container_width=True)
    
    if st.button("🚀 Generar Etiquetas Premium"):
        with st.spinner("Diseñando etiquetas..."):
            pdf_bytes = generar_etiquetas_nexion(df)
            st.success("¡Etiquetas listas para imprimir!")
            st.download_button("📥 Descargar PDF", pdf_bytes, "etiquetas_nexion_pro.pdf", "application/pdf")






















































































































































