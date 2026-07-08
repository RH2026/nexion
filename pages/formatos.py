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
    # 2. Preparamos el texto final con la "C" para el QR e inferior
    texto_qr_inferior = f"{numero_parte} - {lote} - {valor_fijo}C"
    
    # 3. Generamos el QR puro
    qr = qrcode.QRCode(version=1, box_size=15, border=1)
    qr.add_data(texto_qr_inferior)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#27272A", back_color="white").convert("RGB")
    
    # 4. Lienzo de la etiqueta (12 cm alto x 8.5 cm ancho a 300 DPI)
    ancho_px, alto_px = 1004, 1417
    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    # Escalamos la fuente interna del sistema para evitar descargas
    try:
        font_datos = ImageFont.load_default(size=75)
        font_bottom = ImageFont.load_default(size=85)
    except TypeError:
        # Respaldo por si la versión del entorno fuera muy antigua
        font_datos = ImageFont.load_default()
        font_bottom = ImageFont.load_default()

    # --- DIBUJAMOS LOS ELEMENTOS ---
    
    # Datos superiores (Cambiables y fijos, directo como en tu foto)
    draw.text((100, 120), numero_parte, fill="#27272A", font=font_datos)
    draw.text((100, 220), lote, fill="#27272A", font=font_datos)
    draw.text((100, 320), valor_fijo, fill="#27272A", font=font_datos)
    
    # Ajustamos y pegamos el QR al centro
    img_qr = img_qr.resize((700, 700)) 
    qr_w, qr_h = img_qr.size
    pos_x = (ancho_px - qr_w) // 2
    pos_y = 480
    etiqueta.paste(img_qr, (pos_x, pos_y))
    
    # Texto inferior centrado
    try:
        bbox = draw.textbbox((0, 0), texto_qr_inferior, font=font_bottom)
        w_texto = bbox[2] - bbox[0]
    except:
        w_texto = len(texto_qr_inferior) * 45 # Ajuste estimado si falla el calculador
        
    draw.text(((ancho_px - w_texto) // 2, 1280), texto_qr_inferior, fill="#27272A", font=font_bottom)

    # 5. Renderizamos la Vista Previa en la pantalla de Nexion
    st.markdown("### Vista Previa de la Etiqueta:")
    buf_preview = BytesIO()
    etiqueta.save(buf_preview, format="PNG")
    st.image(buf_preview.getvalue(), width=320)
    
    # 6. Creamos el PDF listo para la impresora Zebra (Tamaño Carta, Volteada 90°)
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    ancho_carta, alto_carta = letter
    
    ancho_etiq_pt = 8.5 * cm
    alto_etiq_pt = 12 * cm
    
    buf_preview.seek(0)
    img_reader = ImageReader(buf_preview)
    
    # Centramos en la hoja carta, rotamos y dibujamos con las medidas exactas
    c.translate(ancho_carta / 2, alto_carta / 2)
    c.rotate(90)
    c.drawImage(img_reader, -ancho_etiq_pt / 2, -alto_etiq_pt / 2, width=ancho_etiq_pt, height=alto_etiq_pt)
    c.showPage()
    c.save()

    # 7. Botón para mandar a la fila de impresión
    st.markdown("---")
    st.download_button(
        label="🖨️ Descargar archivo para Imprimir",
        data=pdf_buffer.getvalue(),
        file_name=f"Etiqueta_{numero_parte}_{lote}.pdf",
        mime="application/pdf"
    )



















































































































































