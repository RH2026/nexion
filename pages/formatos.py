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
    
    # 4. Lienzo de la etiqueta (12 cm x 8.5 cm)
    ancho_px, alto_px = 1004, 1417
    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    # Hacemos la letra un poco más grande para que luzca más
    try:
        font_datos = ImageFont.load_default(size=85)
        font_bottom = ImageFont.load_default(size=90)
    except TypeError:
        font_datos = ImageFont.load_default()
        font_bottom = ImageFont.load_default()

    # --- DIBUJAMOS LOS ELEMENTOS EXACTOS ---
    
    # Juntamos los textos y respetamos el espacio vacío superior donde iría el logo
    draw.text((100, 180), numero_parte, fill="#27272A", font=font_datos)
    draw.text((100, 270), lote, fill="#27272A", font=font_datos)
    draw.text((100, 360), valor_fijo, fill="#27272A", font=font_datos)
    
    # Subimos el QR para que empiece pegadito al texto "140"
    img_qr = img_qr.resize((760, 760)) 
    qr_w, qr_h = img_qr.size
    pos_x = (ancho_px - qr_w) // 2
    pos_y = 470  # <-- Aquí es donde lo subimos
    etiqueta.paste(img_qr, (pos_x, pos_y))
    
    # Subimos también el texto inferior para que quede justo debajo del QR
    try:
        bbox = draw.textbbox((0, 0), texto_qr_inferior, font=font_bottom)
        w_texto = bbox[2] - bbox[0]
    except:
        w_texto = len(texto_qr_inferior) * 45 
        
    draw.text(((ancho_px - w_texto) // 2, 1260), texto_qr_inferior, fill="#27272A", font=font_bottom)

    # 5. Vista Previa en Nexion
    st.markdown("### Vista Previa de la Etiqueta:")
    buf_preview = BytesIO()
    etiqueta.save(buf_preview, format="PNG")
    st.image(buf_preview.getvalue(), width=320)
    
    # 6. Preparación del PDF (Volteado para Zebra)
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    ancho_carta, alto_carta = letter
    
    ancho_etiq_pt = 8.5 * cm
    alto_etiq_pt = 12 * cm
    
    buf_preview.seek(0)
    img_reader = ImageReader(buf_preview)
    
    c.translate(ancho_carta / 2, alto_carta / 2)
    c.rotate(90)
    c.drawImage(img_reader, -ancho_etiq_pt / 2, -alto_etiq_pt / 2, width=ancho_etiq_pt, height=alto_etiq_pt)
    c.showPage()
    c.save()

    # 7. Botón de Impresión
    st.markdown("---")
    st.download_button(
        label="🖨️ Descargar archivo para Imprimir",
        data=pdf_buffer.getvalue(),
        file_name=f"Etiqueta_{numero_parte}_{lote}.pdf",
        mime="application/pdf"
    )



















































































































































