import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
import io

# --- CONFIGURACIÓN DE PÁGINA (PANTALLA ANCHA) ---
st.set_page_config(layout="wide", page_title="Generador de Etiquetas NEXION")

# --- FUNCIÓN PARA GENERAR EL PDF ---
def generar_etiquetas_nexion(df):
    output = io.BytesIO()
    # Tamaño carta estándar
    c = canvas.Canvas(output, pagesize=letter)
    width_carta, height_carta = letter

    # Definimos el área de impresión (1/4 de media carta aprox: 10.5 x 7.5 cm)
    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    
    # Margen para que no quede pegado a la orilla
    x_offset = 1.0 * cm
    y_offset = height_carta - h_rec - 1.0 * cm

    for index, row in df.iterrows():
        # Validar que Quantity sea un número
        try:
            cantidad = int(row['Quantity'])
        except:
            continue # Si no hay número, salta a la siguiente fila

        # --- CORRECCIÓN DE DATOS TOLERANTE ---
        # Buscamos Nombre_Extran (con 'n' final como tu Excel) o Nombre_Ext
        nombre_ext_val = row.get('Nombre_Extran', row.get('Nombre_Ext', ''))
        
        # Si de plano está vacío en ambas columnas, usamos Nombre_Cliente
        if pd.isna(nombre_ext_val) or str(nombre_ext_val).strip() == '':
            nombre_grande_final = str(row.get('Nombre_Cliente', 'SIN NOMBRE'))
        else:
            nombre_grande_final = str(nombre_ext_val)

        for i in range(cantidad):
            # 1. Dibujar el recuadro de la etiqueta (opcional, ayuda a cortar)
            c.setDash(1, 2) 
            c.setStrokeColorRGB(0.7, 0.7, 0.7) # Gris clarito
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([]) 
            c.setStrokeColorRGB(0, 0, 0) # Volver a negro

            # 2. Encabezado: "Cliente" y el ID/Nombre
            c.setFont("Helvetica", 8)
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 0.5*cm, "Cliente")
            
            c.setFont("Helvetica-Bold", 10)
            cliente_texto = f"{row.get('Nombre_Cliente', 'N/A')}"
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 1.0*cm, cliente_texto[:40])

            # 3. Nombre_Ext (EL TITULO GRANDE de la foto)
            # Usamos un tamaño de fuente grande para que resalte
            c.setFont("Helvetica-Bold", 18)
            
            # --- USAMOS LA VARIABLE CORREGIDA AQUÍ ---
            # Centramos el texto en el recuadro
            c.drawCentredString(x_offset + (w_rec/2), y_offset + h_rec - 2.5*cm, nombre_grande_final[:25])

            # 4. Dirección (Bloque central)
            c.setFont("Helvetica-Bold", 11)
            direccion = str(row.get('DIRECCION', 'Dirección no disponible'))
            # Dividir en dos líneas si es muy larga para que no se salga
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 4.2*cm, direccion[:48])
            c.drawString(x_offset + 0.3*cm, y_offset + h_rec - 4.7*cm, direccion[48:96])

            # 5. Pie de etiqueta: Factura y Cajas (como en tu imagen)
            c.setFont("Helvetica", 8)
            c.drawString(x_offset + 0.5*cm, y_offset + 1.2*cm, "Factura")
            c.drawString(x_offset + 4.5*cm, y_offset + 1.2*cm, "Cajas")
            c.drawString(x_offset + 7.5*cm, y_offset + 1.2*cm, "Transporte")

            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_offset + 0.5*cm, y_offset + 0.6*cm, str(row.get('Factura', '000000')))
            
            # Formato: 1 / 40, 2 / 40...
            texto_cajas = f"{i + 1}  /  {cantidad}"
            c.drawString(x_offset + 4.5*cm, y_offset + 0.6*cm, texto_cajas)
            
            c.setFont("Helvetica-Bold", 9)
            transporte = str(row.get('Transporte', 'TRES GUERRAS'))
            c.drawString(x_offset + 7.5*cm, y_offset + 0.6*cm, transporte[:15])

            # Finalizar página (una etiqueta por hoja para evitar líos de alineación en esta versión)
            c.showPage()

    c.save()
    return output.getvalue()

# --- INTERFAZ DE USUARIO EN STREAMLIT ---
st.header("📦 Generador de Etiquetas de Logística")
st.info("Sube tu Excel y generaré un PDF con el número de etiquetas exacto según la columna 'Quantity'.")

archivo = st.file_uploader("Selecciona el archivo Excel", type=["xlsx"])

if archivo:
    try:
        # Usamos sheet_name=0 para que lea la PRIMERA pestaña siempre
        df = pd.read_excel(archivo, sheet_name=0)
        
        st.write("### Vista previa de los datos")
        # Mostramos la tabla al ancho completo de la pantalla
        st.dataframe(df.head(10), use_container_width=True) 

        if st.button("🚀 Generar PDF de Etiquetas"):
            with st.spinner("Procesando etiquetas... esto puede tardar si son muchas"):
                pdf_bytes = generar_etiquetas_nexion(df)
                
                st.success("¡Etiquetas generadas con éxito!")
                st.download_button(
                    label="📥 Descargar PDF para Imprimir",
                    data=pdf_bytes,
                    file_name="etiquetas_embarque_nexion.pdf",
                    mime="application/pdf"
                )
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo: {e}")























































































































































