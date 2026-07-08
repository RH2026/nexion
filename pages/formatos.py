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
    
    # 2. Generamos el QR
    qr = qrcode.QRCode(version=1, box_size=15, border=1)
    qr.add_data(texto_qr_inferior)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#27272A", back_color="white").convert("RGB")
    
    # 3. Lienzo de la etiqueta (10.40 cm x 8.5 cm)
    # Ancho 8.5cm -> ~1004px, Alto 10.4cm -> ~1228px
    ancho_px, alto_px = 1004, 1228
    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    # Fuentes
    try:
        font_datos = ImageFont.load_default(size=60)
        font_bottom = ImageFont.load_default(size=65)
    except TypeError:
        font_datos = ImageFont.load_default()
        font_bottom = ImageFont.load_default()

    # --- AJUSTE AL MÍNIMO (QUITANDO ESPACIOS) ---
    margen_izquierdo = 10
    
    # --- LOGO (PEGADO AL BORDE SUPERIOR Y=0) ---
    try:
        logo = Image.open("agc.png").convert("RGBA")
        logo_w, logo_h = logo.size
        target_w = 750
        target_h = int((target_w / logo_w) * logo_h)
        logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
        # Y=0 para que no haya margen arriba
        etiqueta.paste(logo, (margen_izquierdo, 0), logo)
    except Exception as e:
        st.warning(f"No se pudo cargar 'agc.png'. ({e})")

    # --- TEXTOS Y QR ---
    # Ajustados para que quepan bien debajo del logo
    draw.text((margen_izquierdo, 180), numero_parte, fill="#27272A", font=font_datos)
    draw.text((margen_izquierdo, 250), lote, fill="#27272A", font=font_datos)
    draw.text((margen_izquierdo, 320), valor_fijo, fill="#27272A", font=font_datos)
    
    img_qr = img_qr.resize((650, 650))
    pos_x = (ancho_px - 650) // 2
    pos_y = 390
    etiqueta.paste(img_qr, (pos_x, pos_y))
    
    try:
        bbox = draw.textbbox((0, 0), texto_qr_inferior, font=font_bottom)
        w_texto = bbox[2] - bbox[0]
    except:
        w_texto = len(texto_qr_inferior) * 35
        
    draw.text(((ancho_px - w_texto) // 2, 1100), texto_qr_inferior, fill="#27272A", font=font_bottom)

    # 4. Vista Previa
    st.image(etiqueta, width=300)
    
    # 5. PDF (Márgenes de impresión en cero absoluto)
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(8.5*cm, 10.4*cm))
    
    buf_img = BytesIO()
    etiqueta.save(buf_img, format="PNG")
    buf_img.seek(0)
    
    c.drawImage(ImageReader(buf_img), 0, 0, width=8.5*cm, height=10.4*cm)
    c.save()

    st.download_button("🖨️ Descargar Etiqueta", pdf_buffer.getvalue(), "Etiqueta_Final.pdf", "application/pdf")



















































































































































