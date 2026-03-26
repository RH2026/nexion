import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
import io

def generar_pdf_en_memoria(df):
    output = io.BytesIO()
    # Tamaño carta: 21.59 x 27.94 cm
    c = canvas.Canvas(output, pagesize=letter)
    width_carta, height_carta = letter

    # Definimos el cuarto de media carta (aprox 10.5 x 7 cm)
    w_rec, h_rec = 10.5 * cm, 7.0 * cm
    
    # Lo posicionamos en la parte superior izquierda de la hoja carta
    x_offset = 0.5 * cm
    y_offset = height_carta - h_rec - 0.5 * cm

    for _, row in df.iterrows():
        try:
            cantidad = int(row['Quantity'])
        except:
            continue

        for i in range(cantidad):
            # Dibujamos el contorno del cuarto de hoja
            c.setDash(1, 2) # Línea punteada para corte
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([]) # Volver a línea sólida

            # --- DATOS ESTILO TU IMAGEN ---
            # Encabezado "Cliente"
            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.2*cm, y_offset + h_rec - 0.4*cm, "Cliente")
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_offset + 0.2*cm, y_offset + h_rec - 0.8*cm, str(row['Nombre_Cliente'])[:30])

            # Nombre_Ext (Grande como en tu foto)
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(x_offset + (w_rec/2), y_offset + h_rec - 2.2*cm, str(row['Nombre_Ext'])[:20])

            # Dirección
            c.setFont("Helvetica-Bold", 10)
            # Dividimos la dirección en dos líneas si es muy larga
            dir_completa = str(row['DIRECCION'])
            c.drawString(x_offset + 0.2*cm, y_offset + h_rec - 3.5*cm, dir_completa[:45])
            c.drawString(x_offset + 0.2*cm, y_offset + h_rec - 4.0*cm, dir_completa[45:90])

            # Pie de etiqueta: Factura y Cajas
            c.setFont("Helvetica", 7)
            c.drawString(x_offset + 0.5*cm, y_offset + 1.2*cm, "Factura")
            c.drawString(x_offset + 4.0*cm, y_offset + 1.2*cm, "Cajas")
            
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_offset + 0.5*cm, y_offset + 0.6*cm, str(row['Factura']))
            c.drawString(x_offset + 4.0*cm, y_offset + 0.6*cm, f"{i+1} / {cantidad}")

            c.showPage() # Nueva hoja por cada etiqueta (o puedes acomodar 8 por hoja si prefieres)

    c.save()
    return output.getvalue()

# --- INTERFAZ EN STREAMLIT ---
st.title("Generador de Etiquetas NEXION 🚀")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer específicamente la pestaña que me dijiste
    df = pd.read_excel(uploaded_file, sheet_name='Analisis_Final')
    st.success("¡Archivo cargado correctamente!")
    st.write("Vista previa de datos:", df.head())

    if st.button("Generar PDF de Etiquetas"):
        pdf_data = generar_pdf_en_memoria(df)
        
        st.download_button(
            label="📥 Descargar Etiquetas PDF",
            data=pdf_data,
            file_name="etiquetas_logistica.pdf",
            mime="application/pdf"
        )























































































































































