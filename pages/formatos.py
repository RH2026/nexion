import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

st.subheader("Generador de Etiquetas AGC")

# 1. Controles de Entrada
opciones_np = ["712117", "PT10065", "PT10219", "PT10264"]
numero_parte = st.selectbox("Número de Parte", opciones_np)
lote = st.text_input("Lote (Ej. 6181)")
valor_fijo = "140"

if lote:
    # 2. Preparamos el texto final (agregando la "C" al final como en tu foto)
    texto_qr_inferior = f"{numero_parte} - {lote} - {valor_fijo}C"
    
    # 3. Generamos el QR puro
    qr = qrcode.QRCode(version=1, box_size=15, border=1)
    qr.add_data(texto_qr_inferior)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#374151", back_color="white").convert("RGB")
    
    # 4. Creamos el lienzo de la etiqueta en alta resolución (12 cm alto x 8.5 cm ancho)
    # A 300 DPI, esto equivale a unos 1004 x 1417 pixeles
    ancho_px, alto_px = 1004, 1417
    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)
    
    # Intentamos usar la fuente Arial si está en tu Windows, si no, usa la básica
    try:
        font_logo = ImageFont.truetype("arialbd.ttf", 110)
        font_slogan = ImageFont.truetype("arial.ttf", 35)
        font_datos = ImageFont.truetype("arialbd.ttf", 65)
        font_bottom = ImageFont.truetype("arial.ttf", 75)
    except IOError:
        font_logo = font_slogan = font_datos = font_bottom = ImageFont.load_default()

    # --- DIBUJAMOS LOS ELEMENTOS ---
    
    # Textos Estáticos (Logo AGC)
    draw.text((80, 100), "AGC", fill="#1E3A8A", font=font_logo) # Azul oscuro
    draw.text((80, 220), "ARTÍCULOS DE GRAN CONSUMO", fill="#1E3A8A", font=font_slogan)
    
    # Variables a un costado
    draw.text((80, 320), numero_parte, fill="#374151", font=font_datos)
    draw.text((80, 400), lote, fill="#374151", font=font_datos)
    draw.text((80, 480), valor_fijo, fill="#374151", font=font_datos)
    
    # Pegamos el QR en el centro
    img_qr = img_qr.resize((750, 750)) # Hacemos el QR más grande
    qr_w, qr_h = img_qr.size
    pos_x = (ancho_px - qr_w) // 2
    pos_y = 550
    etiqueta.paste(img_qr, (pos_x, pos_y))
    
    # Texto inferior centrado
    bbox = draw.textbbox((0, 0), texto_qr_inferior, font=font_bottom)
    w_texto = bbox[2] - bbox[0]
    draw.text(((ancho_px - w_texto) // 2, 1320), texto_qr_inferior, fill="#374151", font=font_bottom)

    # 5. Renderizamos en pantalla para que la veas primero
    st.markdown("### Vista Previa:")
    # Usamos BytesIO para pasar la imagen a Streamlit sin guardarla en disco
    buf_preview = BytesIO()
    etiqueta.save(buf_preview, format="PNG")
    st.image(buf_preview.getvalue(), width=350)
    
    # 6. Preparamos el PDF en Tamaño Carta con la etiqueta volteada
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    ancho_carta, alto_carta = letter
    
    ancho_etiq_pt = 8.5 * cm
    alto_etiq_pt = 12 * cm
    
    # Preparamos la imagen para ReportLab
    buf_preview.seek(0)
    img_reader = ImageReader(buf_preview)
    
    # Nos movemos al centro de la hoja carta, rotamos 90 grados y dibujamos
    c.translate(ancho_carta / 2, alto_carta / 2)
    c.rotate(90)
    c.drawImage(img_reader, -ancho_etiq_pt / 2, -alto_etiq_pt / 2, width=ancho_etiq_pt, height=alto_etiq_pt)
    c.showPage()
    c.save()

    # 7. Botón para imprimir (descargar el PDF)
    st.markdown("---")
    st.download_button(
        label="🖨️ Imprimir Etiqueta (PDF Tamaño Carta)",
        data=pdf_buffer.getvalue(),
        file_name=f"Etiqueta_{numero_parte}_Lote{lote}.pdf",
        mime="application/pdf"
    )



















































































































































