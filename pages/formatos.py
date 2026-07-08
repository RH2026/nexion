import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

st.subheader("Generador de Etiquetas Nexion")

# 1. Controles de Entrada
opciones_np = ["712117", "PT10065", "PT10219", "PT10264"]
numero_parte = st.selectbox("Número de Parte", opciones_np)
lote = st.text_input("Lote (Ej. 6181)")
valor_fijo = "140"

if lote:
    # 2. Preparamos el texto final con la "C"
    texto_qr_inferior = f"{numero_parte} - {lote} - {valor_fijo}C"
    
    # 3. Generamos el QR
    qr = qrcode.QRCode(version=1, box_size=15, border=1)
    qr.add_data(texto_qr_inferior)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#27272A", back_color="white").convert("RGB")
    
    # 4. Lienzo de la etiqueta (12 cm x 8.5 cm a 300 DPI)
    ancho_px, alto_px = 1004, 1417
    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    # Reducimos el tamaño de la letra para que se vea más estilizada
    try:
        font_datos = ImageFont.load_default(size=60)
        font_bottom = ImageFont.load_default(size=65)
    except TypeError:
        font_datos = ImageFont.load_default()
        font_bottom = ImageFont.load_default()

    # --- NUEVO: CARGAMOS Y COLOCAMOS EL LOGO ---
    try:
        logo = Image.open("agc.png").convert("RGBA")
        logo_w, logo_h = logo.size
        # Escalamos el logo para que no ocupe todo el ancho
        # Definimos un ancho máximo de 500 px
        target_w = 500
        target_h = int((target_w / logo_w) * logo_h)
        logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Centramos el logo horizontalmente
        logo_x = (ancho_px - target_w) // 2
        logo_y = 30 # Margen superior
        
        etiqueta.paste(logo, (logo_x, logo_y), logo)
        # Calculamos el desplazamiento vertical para el resto de los elementos
        y_offset = target_h + logo_y + 30
    except Exception as e:
        st.warning(f"No se pudo cargar 'agc.png'. Asegúrate de que esté en el archivo raíz. ({e})")
        # Si no hay logo, empezamos más arriba
        y_offset = 120

    # --- DIBUJAMOS LOS ELEMENTOS COMPACTOS (con y_offset) ---
    # Ajustamos coordenadas para que no queden huecos grandes con la letra más chica
    draw.text((100, 150 + y_offset), numero_parte, fill="#27272A", font=font_datos)
    draw.text((100, 230 + y_offset), lote, fill="#27272A", font=font_datos)
    draw.text((100, 310 + y_offset), valor_fijo, fill="#27272A", font=font_datos)
    
    # Subimos el QR un poco más para que quede pegadito a los datos
    img_qr = img_qr.resize((760, 760)) 
    qr_w, qr_h = img_qr.size
    pos_x = (ancho_px - qr_w) // 2
    pos_y = 410 + y_offset 
    etiqueta.paste(img_qr, (pos_x, pos_y))
    
    # Texto inferior ajustado bajo el QR
    try:
        bbox = draw.textbbox((0, 0), texto_qr_inferior, font=font_bottom)
        w_texto = bbox[2] - bbox[0]
    except:
        w_texto = len(texto_qr_inferior) * 35 
        
    draw.text(((ancho_px - w_texto) // 2, 1220 + y_offset), texto_qr_inferior, fill="#27272A", font=font_bottom)

    # 5. Vista Previa en la interfaz de Nexion
    st.markdown("### Vista Previa de la Etiqueta AGC:")
    buf_preview = BytesIO()
    etiqueta.save(buf_preview, format="PNG")
    st.image(buf_preview.getvalue(), width=320)
    
    # 6. Preparación del PDF (Esquina superior izquierda)
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    ancho_carta, alto_carta = letter
    
    ancho_etiq_pt = 8.5 * cm
    alto_etiq_pt = 12 * cm
    margin = 0.5 * cm  # Margen de seguridad para evitar recortes físicos de la impresora
    
    buf_preview.seek(0)
    img_reader = ImageReader(buf_preview)
    
    # Aplicamos la rotación y calculamos la posición exacta en el cuadrante superior izquierdo
    c.rotate(90)
    x_pos = alto_carta - margin - ancho_etiq_pt
    y_pos = -(margin + alto_etiq_pt)
    
    c.drawImage(img_reader, x_pos, y_pos, width=ancho_etiq_pt, height=alto_etiq_pt)
    c.showPage()
    c.save()

    # 7. Botón de Descarga para Impresión
    st.markdown("---")
    st.download_button(
        label="🖨️ Descargar archivo para Imprimir",
        data=pdf_buffer.getvalue(),
        file_name=f"Etiqueta_{numero_parte}_{lote}.pdf",
        mime="application/pdf"
    )



















































































































































