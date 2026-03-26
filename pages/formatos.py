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
    texto = str(texto).upper()
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    # Si salen 3 líneas, bajamos un poquito el tamaño para que no ocupe tanto espacio vertical
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

    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    x_offset, y_offset = 1.0 * cm, height_carta - h_rec - 1.0 * cm

    for index, row in df.iterrows():
        try:
            cantidad = int(row['Quantity'])
        except: continue 

        # Datos corregidos
        nombre_final = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', 'SIN NOMBRE')))
        direccion_final = row.get('DIRECCION', 'DIRECCIÓN NO DISPONIBLE')
        # CAMBIO: Ahora usamos RECOMENDACION para el transporte
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', '')))

        for i in range(cantidad):
            # Dibujamos el borde
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            # 1. CLIENTE (Arriba)
            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 0.4*cm, "CLIENTE:")
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 0.8*cm, str(row.get('Nombre_Cliente', ''))[:50])

            # 2. NOMBRE EXTRAN (EL PROTAGONISTA 1)
            # Empezamos un poquito más arriba para dar margen
            y_termino_nombre = dibujar_texto_bloque(
                c, nombre_final, 
                x_offset + (w_rec/2), 
                y_offset + h_rec - 2.0*cm, 
                10*cm, "Helvetica-Bold", 20, 0.75*cm
            )

            # 3. DIRECCIÓN (EL PROTAGONISTA 2)
            # CAMBIO: La bajamos un poco más (y_offset + 3.2 en lugar de 3.8) 
            # para que no se choque con el nombre de 3 líneas
            dibujar_texto_bloque(
                c, direccion_final, 
                x_offset + (w_rec/2), 
                y_offset + 3.2*cm, 
                10*cm, "Helvetica-Bold", 11, 0.4*cm
            )

            # 4. PIE DE ETIQUETA
            c.setLineWidth(0.5)
            c.line(x_offset + 0.2*cm, y_offset + 1.4*cm, x_offset + w_rec - 0.2*cm, y_offset + 1.4*cm)

            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.5*cm, y_offset + 1.0*cm, "FACTURA")
            c.drawString(x_offset + 4.0*cm, y_offset + 1.0*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.0*cm, y_offset + 1.0*cm, "TRANSPORTE")

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_offset + 0.5*cm, y_offset + 0.4*cm, str(row.get('Factura', '')))
            
            texto_cajas = f"{i + 1}  /  {cantidad}"
            c.drawCentredString(x_offset + 5.0*cm, y_offset + 0.4*cm, texto_cajas)
            
            # Aquí imprimimos la RECOMENDACION
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_offset + 7.0*cm, y_offset + 0.4*cm, transporte_final[:20])

            c.showPage()

    c.save()
    return output.getvalue()

# --- INTERFAZ ---
st.header("📦 NEXION - Etiquetas de Alto Impacto (Corregido)")

archivo = st.file_uploader("Sube tu Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo, sheet_name=0)
    st.dataframe(df.head(), use_container_width=True)
    
    if st.button("🚀 Generar Etiquetas"):
        pdf_bytes = generar_etiquetas_nexion(df)
        st.success("¡Etiquetas listas con el espacio corregido!")
        st.download_button("📥 Descargar PDF", pdf_bytes, "etiquetas_nexion_final.pdf", "application/pdf")






















































































































































