import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Etiquetas High-Space")

# --- FUNCIÓN PARA TEXTO MULTILÍNEA DE ALTO IMPACTO ---
def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado):
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

    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    x_offset, y_offset = 1.0 * cm, height_carta - h_rec - 1.0 * cm

    for index, row in df.iterrows():
        try:
            cantidad = int(row['Quantity'])
        except: continue 

        # Datos limpios
        nombre_final = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', 'SIN NOMBRE')))
        direccion_final = row.get('DIRECCION', 'DIRECCIÓN NO DISPONIBLE')
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', 'TRES GUERRAS')))

        for i in range(cantidad):
            # Dibujamos el borde
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            # --- CABECERA (DATOS JYPESA) ---
            # Nombre de la empresa (Perfectamente centrado)
            c.setFont("Helvetica-Bold", 7)
            nombre_empresa = "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV"
            c.drawCentredString(x_offset + (w_rec/2), y_offset + h_rec - 0.3*cm, nombre_empresa)
            
            c.setFont("Helvetica", 6)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(
                c, info_contacto, x_offset + (w_rec/2), y_offset + h_rec - 0.7*cm, 
                10*cm, "Helvetica", 6, 0.25*cm
            )
            
            # Línea divisoria superior sutil
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(x_offset + 0.5*cm, y_offset + h_rec - 1.0*cm, x_offset + w_rec - 0.5*cm, y_offset + h_rec - 1.0*cm)
            c.setStrokeColorRGB(0, 0, 0)

            # --- DESTINATARIO (DATOS DEL CLIENTE) ---
            # 1. NOMBRE (PROTAGONISTA 1 - Centrado)
            # CAMBIO: Bajamos el nombre 0.5 cm (y_offset + h_rec - 2.0*cm en lugar de 1.5)
            # para dar espacio después de la cabecera.
            y_termino_nombre = dibujar_texto_bloque_pro(
                c, nombre_final, 
                x_offset + (w_rec/2), 
                y_offset + h_rec - 2.0*cm, 
                10*cm, "Helvetica-Bold", 18, 0.7*cm
            )

            # --- LA REINA: GIGA-DIRECCIÓN (MEJORADA) ---
            # CAMBIO: La dirección gigante (fuente base 16pt) ocupa el centro.
            # Fuente base 16pt, hasta 4 líneas, con interlineado dinámico.
            # Margen de seguridad dinámico: Empezamos la dirección con un "aire"
            # después del nombre del cliente, pero no muy lejos.
            y_inicio_direccion = y_termino_nombre - 0.4*cm

            # Verificamos que la dirección no empiece *demasiado* abajo
            if y_inicio_direccion < y_offset + 2.8*cm:
                 y_inicio_direccion = y_offset + 3.0*cm # Mínimo garantizado

            dibujar_texto_bloque_pro(
                c, direccion_final, 
                x_offset + (w_rec/2), 
                y_inicio_direccion, 
                10.0 * cm, 
                "Helvetica-Bold", 
                16, # Fuente gigante
                0.55*cm, # Interlineado proporcional
                max_lineas=4 # Máximo 4 líneas para la dirección
            )

            # --- PIE DE ETIQUETA ---
            c.setLineWidth(0.5)
            y_linea_pie = y_offset + 1.2*cm
            c.line(x_offset + 0.2*cm, y_linea_pie, x_offset + w_rec - 0.2*cm, y_linea_pie)

            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.3*cm, "FACTURA")
            c.drawString(x_offset + 4.0*cm, y_linea_pie - 0.3*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.0*cm, y_linea_pie - 0.3*cm, "TRANSPORTE")

            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.8*cm, str(row.get('Factura', '')))
            c.drawCentredString(x_offset + 5.0*cm, y_linea_pie - 0.8*cm, f"{i + 1} / {cantidad}")
            
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_offset + 7.0*cm, y_linea_pie - 0.8*cm, transporte_final[:20])

            c.showPage()

    c.save()
    return output.getvalue()

# --- INTERFAZ ---
st.header("📦 NEXION - Etiquetas con Espacio Inteligente")
st.markdown("Hemos corregido el amontonamiento. El **Nombre** y la **Dirección** (con su fuente monumental) ahora están bajados para dar espacio vital y no amontonarse con las líneas divisoria.")

archivo = st.file_uploader("Sube tu Excel", type=["xlsx"])

if archivo:
    try:
        df = pd.read_excel(archivo, sheet_name=0)
        st.dataframe(df.head(), use_container_width=True)
        
        if st.button("🚀 Generar Etiquetas"):
            with st.spinner("Creando etiquetas monumentales y ordenadas..."):
                pdf_bytes = generar_etiquetas_nexion(df)
                st.success("¡Etiquetas con espacio perfecto listas para descargar!")
                st.download_button("📥 Descargar PDF", pdf_bytes, "etiquetas_nexion_espacio_pro.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")






















































































































































