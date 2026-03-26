import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Etiquetas Responsive")

# --- FUNCIÓN PARA AJUSTAR TEXTO AL ANCHO (RESPONSIVE) ---
def dibujar_texto_ajustado(c, texto, x_centro, y, ancho_max, fuente_bol, tamano_ideal):
    """
    Reduce el tamaño de la fuente automáticamente si el texto es más ancho que ancho_max.
    """
    texto = str(texto)
    fontSize = tamano_ideal
    # Medir cuánto mide el texto con la fuente actual
    while c.stringWidth(texto, fuente_bol, fontSize) > ancho_max and fontSize > 6:
        fontSize -= 0.5  # Ir bajando el tamaño poco a poco
    
    c.setFont(fuente_bol, fontSize)
    c.drawCentredString(x_centro, y, texto)

def generar_etiquetas_nexion(df):
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    width_carta, height_carta = letter

    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    x_offset = 1.0 * cm
    y_offset = height_carta - h_rec - 1.0 * cm

    for index, row in df.iterrows():
        try:
            cantidad = int(row['Quantity'])
        except:
            continue 

        # Lógica de nombre (Nombre_Extran o Nombre_Ext)
        nombre_ext_val = row.get('Nombre_Extran', row.get('Nombre_Ext', ''))
        if pd.isna(nombre_ext_val) or str(nombre_ext_val).strip() == '':
            nombre_grande_final = str(row.get('Nombre_Cliente', 'SIN NOMBRE'))
        else:
            nombre_grande_final = str(nombre_ext_val)

        for i in range(cantidad):
            # Recuadro guía
            c.setDash(1, 2) 
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([]) 
            c.setStrokeColorRGB(0, 0, 0)

            # 1. Cliente (chiquito arriba)
            c.setFont("Helvetica", 8)
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 0.5*cm, "Cliente")
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 1.0*cm, str(row.get('Nombre_Cliente', ''))[:50])

            # 2. NOMBRE GRANDE (AQUÍ ESTÁ LO RESPONSIVE)
            # El ancho máximo es el ancho del recuadro menos unos márgenes (9.5 cm)
            dibujar_texto_ajustado(
                c, 
                nombre_grande_final, 
                x_offset + (w_rec/2), 
                y_offset + h_rec - 2.5*cm, 
                9.5 * cm, 
                "Helvetica-Bold", 
                18
            )

            # 3. Dirección (También con ajuste si es muy larga)
            direccion = str(row.get('DIRECCION', ''))
            dibujar_texto_ajustado(
                c, 
                direccion, 
                x_offset + (w_rec/2), 
                y_offset + h_rec - 4.5*cm, 
                10.0 * cm, 
                "Helvetica-Bold", 
                10
            )

            # 4. Pie de etiqueta
            c.setFont("Helvetica", 8)
            c.drawString(x_offset + 0.5*cm, y_offset + 1.2*cm, "Factura")
            c.drawString(x_offset + 4.5*cm, y_offset + 1.2*cm, "Cajas")
            c.drawString(x_offset + 7.5*cm, y_offset + 1.2*cm, "Transporte")

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_offset + 0.5*cm, y_offset + 0.6*cm, str(row.get('Factura', '')))
            c.drawString(x_offset + 4.5*cm, y_offset + 0.6*cm, f"{i + 1}  /  {cantidad}")
            
            c.setFont("Helvetica-Bold", 9)
            transporte = str(row.get('Transporte', row.get('RECOMENDACION', 'TRES GUERRAS')))
            c.drawString(x_offset + 7.5*cm, y_offset + 0.6*cm, transporte[:15])

            c.showPage()

    c.save()
    return output.getvalue()

# --- INTERFAZ ---
st.header("📦 NEXION - Generador de Etiquetas Inteligentes")

archivo = st.file_uploader("Sube tu Excel", type=["xlsx"])

if archivo:
    try:
        df = pd.read_excel(archivo, sheet_name=0)
        st.write("### Datos detectados")
        st.dataframe(df.head(10), use_container_width=True) 

        if st.button("🚀 Generar Etiquetas"):
            pdf_bytes = generar_etiquetas_nexion(df)
            st.success("¡Etiquetas ajustadas perfectamente!")
            st.download_button("📥 Descargar PDF", pdf_bytes, "etiquetas_ajustadas.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")























































































































































