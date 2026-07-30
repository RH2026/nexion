import io
import re
import pandas as pd
import streamlit as st
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

# --- 1. FUNCIONES DE PROCESAMIENTO ---
def limpiar_parentesis(texto):
    return re.sub(r'\(.*?\)', '', str(texto)).strip()

def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
    texto = str(texto).upper()
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    tamano_actual = tamano_max
    # Reducimos el tamaño un poco más rápido si es necesario para que quepa en las líneas
    while len(lineas) > max_lineas and tamano_actual > 8:
        tamano_actual -= 1
        lineas = simpleSplit(texto, fuente, tamano_actual, ancho_max)
    
    c.setFont(fuente, tamano_actual)
    y_actual = y_inicio
    # Dibujamos solo las líneas permitidas y las centramos
    for line in lineas[:max_lineas]: 
        c.drawCentredString(x_centro, y_actual, line)
        y_actual -= interlineado
    return y_actual 

def generar_etiquetas_nexion(df):
    output = io.BytesIO()
    
    # Dimensiones exactas de la etiqueta: 10.5 cm x 7.5 cm
    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    
    # Configuramos el Canvas con el tamaño exacto de la etiqueta
    c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
    
    # Márgenes internos (AUMENTADOS AHORA)
    margen_h = 0.6 * cm  # Margen horizontal a los lados
    w_util = w_rec - (2 * margen_h)
    x_centro = w_rec / 2
    
    margen_sup = 0.8 * cm # Margen desde arriba
    margen_inf = 0.6 * cm # Margen desde abajo
    
    for index, row in df.iterrows():
        try:
            cantidad_real = int(row['Quantity'])
            iteraciones = cantidad_real
        except: 
            continue 

        nombre_crudo = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', 'SIN NOMBRE')))
        nombre_final = limpiar_parentesis(nombre_crudo)
        direccion_final = row.get('DIRECCION', 'DIRECCIÓN NO DISPONIBLE')
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', 'TRES GUERRAS')))

        for i in range(iteraciones):
            # Dibujar contorno de etiqueta (con guiones)
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(0, 0, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            # --- ZONA DE CABECERA ---
            c.setFont("Helvetica-Bold", 8) # Ligeramente más grande
            c.drawCentredString(x_centro, h_rec - margen_sup, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            
            c.setFont("Helvetica", 7) # Ligeramente más grande
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            # Ajustamos la posición de la línea de contacto y el ancho máximo
            dibujar_texto_bloque_pro(c, info_contacto, x_centro, h_rec - margen_sup - 0.6 * cm, w_util, "Helvetica", 7, 0.3*cm, max_lineas=1)
            
            # Línea divisoria
            c.setLineWidth(0.5)
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.line(margen_h, h_rec - margen_sup - 1.2*cm, w_rec - margen_h, h_rec - margen_sup - 1.2*cm)
            c.setStrokeColorRGB(0, 0, 0)

            # --- ZONA CENTRAL (NOMBRE Y DIRECCIÓN) ---
            # NOMBRE CLIENTE (GIGANTE - ESPACIO AUMENTADO)
            y_base_nombre = h_rec - margen_sup - 2.5 * cm
            # Aumentamos el interlineado para el nombre
            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_centro, y_base_nombre, w_util, "Helvetica-Bold", 24, 0.8*cm, max_lineas=3)
            
            # DIRECCIÓN (16pt - ESPACIO AUMENTADO)
            y_inicio_direccion = y_termino_nombre - 0.6 * cm # Separación extra
            dibujar_texto_bloque_pro(c, direccion_final, x_centro, y_inicio_direccion, w_util, "Helvetica-Bold", 16, 0.6*cm, max_lineas=3)

            # --- ZONA DE PIE ---
            # Línea divisoria del pie
            c.setLineWidth(0.6)
            y_linea_pie = margen_inf + 2.0 * cm # Subimos la línea un poco
            c.line(margen_h, y_linea_pie, w_rec - margen_h, y_linea_pie)
            
            # Cabeceras del pie
            c.setFont("Helvetica-Bold", 9)
            c.drawString(margen_h + 0.2*cm, y_linea_pie - 0.5*cm, "FACTURA")
            c.drawCentredString(x_centro, y_linea_pie - 0.5*cm, "CAJAS / BULTO")
            c.drawString(w_rec - margen_h - 4.0*cm, y_linea_pie - 0.5*cm, "TRANSPORTE")
            
            # Valores del pie
            c.setFont("Helvetica-Bold", 14)
            c.drawString(margen_h + 0.2*cm, y_linea_pie - 1.3*cm, str(row.get('Factura', '')))
            
            # Numeración de cajas actual
            c.drawCentredString(x_centro, y_linea_pie - 1.3*cm, f"{i + 1} / {cantidad_real}")
            
            # Transporte (recortado si es muy largo)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(w_rec - margen_h - 4.0*cm, y_linea_pie - 1.3*cm, transporte_final[:18])
            
            c.showPage()

    c.save()
    return output.getvalue()

# --- 2. INTERFAZ DE USUARIO (STREAMLIT) ---
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
        # Validar columnas necesarias
        columnas_requeridas = ['Quantity', 'DIRECCION', 'Factura']
        if not all(col in df.columns for col in columnas_requeridas):
            st.error(f"El archivo Excel debe contener las columnas: {', '.join(columnas_requeridas)}")
            st.stop()

    except Exception as e:
        st.error(f"Error al leer los pedidos: {e}")
        st.stop()

    st.subheader("Vista previa de datos")
    st.dataframe(df[['Quantity', 'DIRECCION', 'Factura']].head(5), use_container_width=True)

    if st.button("Generar Etiquetas PDF", use_container_width=True):
        with st.spinner("Generando documento con márgenes ajustados..."):
            pdf_data = generar_etiquetas_nexion(df)
            
            if pdf_data:
                st.success("¡Documento generado con éxito!")
                
                st.download_button(
                    label="Descargar PDF para Imprimir",
                    data=pdf_data,
                    file_name="etiquetas_nexion_amplias.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.info("El archivo se guardará en tu carpeta de descargas. Los márgenes han sido ampliados.")












































































































































