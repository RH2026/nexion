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
    texto_qr_inferior = f"{numero_parte} - {lote} - {valor_fijo}C"
    
    # --- DISEÑO ORIGINAL (Versión anterior) ---
    qr = qrcode.QRCode(version=1, box_size=15, border=1)
    qr.add_data(texto_qr_inferior)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#27272A", back_color="white").convert("RGB")
    
    # Lienzo de etiqueta base (10.4 cm x 8.5 cm)
    ancho_px, alto_px = 1004, 1228
    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    try:
        font_datos = ImageFont.load_default(size=60)
        font_bottom = ImageFont.load_default(size=65)
    except:
        font_datos = ImageFont.load_default()
        font_bottom = ImageFont.load_default()

    # --- ELEMENTOS DEL DISEÑO ---
    try:
        logo = Image.open("agc.png").convert("RGBA")
        logo_w, logo_h = logo.size
        target_w = 750
        target_h = int((target_w / logo_w) * logo_h)
        logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
        etiqueta.paste(logo, (50, 50), logo)
    except:
        pass

    draw.text((50, 250), numero_parte, fill="#27272A", font=font_datos)
    draw.text((50, 320), lote, fill="#27272A", font=font_datos)
    draw.text((50, 390), valor_fijo, fill="#27272A", font=font_datos)
    
    img_qr = img_qr.resize((650, 650))
    etiqueta.paste(img_qr, (170, 450))
    
    draw.text((50, 1120), texto_qr_inferior, fill="#27272A", font=font_bottom)

    # 2. PDF TAMAÑO CARTA CON ETIQUETA EN ESQUINA SUPERIOR IZQUIERDA
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    
    buf_img = BytesIO()
    etiqueta.save(buf_img, format="PNG")
    buf_img.seek(0)
    
    # Coordenadas: x=0 (pegado a la izquierda), y=carta_alto - etiqueta_alto (pegado arriba)
    # letter es (612, 792) puntos aprox.
    ancho_etiq_pt = 8.5 * cm
    alto_etiq_pt = 10.4 * cm
    
    c.drawImage(ImageReader(buf_img), 0, 792 - alto_etiq_pt, width=ancho_etiq_pt, height=alto_etiq_pt)
    c.save()

    st.download_button("🖨️ Descargar PDF (Esquina Superior Izquierda)", pdf_buffer.getvalue(), "Etiqueta_Carta.pdf", "application/pdf")



















































































































































