import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Etiquetas Giga-Dirección")

# --- FUNCIÓN PARA TEXTO MULTILÍNEA DE ALTO IMPACTO (MEJORADA) ---
def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
    """
    Dibuja texto centrado y multilínea, ajustando la fuente *solo si es necesario* para que quepa en max_lineas.
    """
    texto = str(texto).upper()
    
    # Primero intentamos con el tamaño máximo
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    # Si salen más líneas de las permitidas, bajamos la fuente poco a poco
    tamano_actual = tamano_max
    while len(lineas) > max_lineas and tamano_actual > 8:
        tamano_actual -= 0.5
        lineas = simpleSplit(texto, fuente, tamano_actual, ancho_max)
        # Reducimos proporcionalmente el interlineado si bajamos la fuente
        # interlineado = (tamano_actual / tamano_max) * interlineado

    # Si aún con la fuente mínima sale más de lo que cabe verticalmente en el bloque,
    # cortamos las líneas para evitar encimamientos.
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]

    c.setFont(fuente, tamano_actual)
    y_actual = y_inicio
    
    # Dibujamos las líneas centradas
    for line in lineas: 
        c.drawCentredString(x_centro, y_actual, line)
        y_actual -= interlineado
    return y_actual # Devolvemos dónde terminó de escribir

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

        # Datos limpios y normalizados
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

            # --- CABECERA (DATOS JYPESA - COMPRIMIDOS) ---
            # Reducimos los espacios para ganar milímetros
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_offset + (w_rec/2), y_offset + h_rec - 0.3*cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            
            c.setFont("Helvetica", 6)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(
                c, info_contacto, x_offset + (w_rec/2), y_offset + h_rec - 0.6*cm, 
                10*cm, "Helvetica", 6, 0.25*cm, max_lineas=1
            )
            
            # Línea divisoria superior sutil
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(x_offset + 0.5*cm, y_offset + h_rec - 1.0*cm, x_offset + w_rec - 0.5*cm, y_offset + h_rec - 1.0*cm)
            c.setStrokeColorRGB(0, 0, 0)

            # --- DESTINATARIO (NOMBRE CLIENTE - COMPRIMIDO) ---
            # Empezamos el nombre justo después de la línea
            y_termino_nombre = dibujar_texto_bloque_pro(
                c, nombre_final, 
                x_offset + (w_rec/2), 
                y_offset + h_rec - 1.5*cm, # Empezamos más arriba
                10*cm, "Helvetica-Bold", 17, 0.65*cm, max_lineas=2 # Máximo 2 líneas para el nombre
            )

            # --- LA REINA: GIGA-DIRECCIÓN (MEJORADA) ---
            # Ocupamos el centro de la etiqueta.
            # Fuente base gigante (16pt), hasta 4 líneas, con interlineado dinámico.
            
            # Margen de seguridad dinámico: Empezamos la dirección con un "aire"
            # después del nombre del cliente, pero no muy lejos.
            y_inicio_direccion = y_termino_nombre - 0.3*cm

            # Verificamos que la dirección no empiece *demasiado* abajo
            if y_inicio_direccion < y_offset + 2.8*cm:
                 y_inicio_direccion = y_offset + 3.0*cm # Mínimo garantizado

            dibujar_texto_bloque_pro(
                c, direccion_final, 
                x_offset + (w_rec/2), 
                y_inicio_direccion, 
                10.0 * cm, # Usamos casi todo el ancho
                "Helvetica-Bold", 
                16, # Fuente gigante
                0.55*cm, # Interlineado proporcional
                max_lineas=4 # Máximo 4 líneas para la dirección
            )

            # --- PIE DE ETIQUETA (COMPRIMIDO) ---
            c.setLineWidth(0.5)
            # Subimos el pie para que ocupe menos espacio vertical
            y_linea_pie = y_offset + 1.2*cm
            c.line(x_offset + 0.2*cm, y_linea_pie, x_offset + w_rec - 0.2*cm, y_linea_pie)

            # Textos de referencia
            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.3*cm, "FACTURA")
            c.drawString(x_offset + 4.0*cm, y_linea_pie - 0.3*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.0*cm, y_linea_pie - 0.3*cm, "TRANSPORTE")

            # Datos reales
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.8*cm, str(row.get('Factura', '')))
            
            # Cajas
            c.drawCentredString(x_offset + 5.0*cm, y_linea_pie - 0.8*cm, f"{i + 1} / {cantidad}")
            
            # Transporte
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_offset + 7.0*cm, y_linea_pie - 0.8*cm, transporte_final[:20])

            c.showPage()

    c.save()
    return output.getvalue()

# --- INTERFAZ ---
st.header("📦 NEXION - Etiquetas Premium 'Giga-Dirección'")
st.markdown("Hemos **maximizado la dirección** al máximo nivel legible (**fuente base 16pt**) en un bloque central de **hasta 4 líneas**, comprimiendo el resto de la etiqueta para evitar encimamientos. ¡Pruébala con tus direcciones más largas!")

archivo = st.file_uploader("Sube tu Excel de Logística", type=["xlsx"])

if archivo:
    try:
        df = pd.read_excel(archivo, sheet_name=0)
        st.dataframe(df.head(), use_container_width=True)
        
        if st.button("🚀 Generar Etiquetas High-Impact"):
            with st.spinner("Diseñando etiquetas monumentales..."):
                pdf_bytes = generar_etiquetas_nexion(df)
                st.success("¡Etiquetas con dirección monumental listas para descargar!")
                st.download_button("📥 Descargar PDF", pdf_bytes, "etiquetas_giga_direccion.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")






















































































































































