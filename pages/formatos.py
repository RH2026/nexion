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
    ancho_px, alto_px = 1004, 1228
    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    try:
        font_datos = ImageFont.load_default(size=60)
        font_bottom = ImageFont.load_default(size=65)
    except:
        font_datos = ImageFont.load_default()
        font_bottom = ImageFont.load_default()

    # --- MÁRGENES INTERNOS ---
    m_izq = 15
    m_top = 15

    # --- LOGO AGC ---
    try:
        logo = Image.open("agc.png").convert("RGBA")
        logo_w, logo_h = logo.size
        target_w = 750
        target_h = int((target_w / logo_w) * logo_h)
        logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
        etiqueta.paste(logo, (m_izq, m_top), logo)
    except:
        pass

    # --- TEXTOS Y QR ---
    draw.text((m_izq, 200), numero_parte, fill="#27272A", font=font_datos)
    draw.text((m_izq, 270), lote, fill="#27272A", font=font_datos)
    draw.text((m_izq, 340), valor_fijo, fill="#27272A", font=font_datos)
    
    img_qr = img_qr.resize((680, 680))
    pos_x = (ancho_px - 680) // 2
    pos_y = 410
    etiqueta.paste(img_qr, (pos_x, pos_y))
    
    try:
        bbox = draw.textbbox((0, 0), texto_qr_inferior, font=font_bottom)
        w_texto = bbox[2] - bbox[0]
    except:
        w_texto = len(texto_qr_inferior) * 35
        
    draw.text(((ancho_px - w_texto) // 2, 1130), texto_qr_inferior, fill="#27272A", font=font_bottom)

    # 4. Vista Previa
    st.image(etiqueta, width=320)
    
    # 5. PDF ROTADO Y PEGADO ARRIBA-IZQUIERDA
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    ancho_carta, alto_carta = letter
    
    buf_img = BytesIO()
    etiqueta.save(buf_img, format="PNG")
    buf_img.seek(0)
    img_reader = ImageReader(buf_img)
    
    # Dimensiones
    ancho_etiq_pt = 8.5 * cm
    alto_etiq_pt = 10.4 * cm
    
    # ROTACIÓN: Cambiamos el sistema de coordenadas
    c.saveState()
    c.translate(0, alto_carta) # Movemos el origen arriba
    c.rotate(-90)              # Rotamos el lienzo
    
    # Ahora dibujamos en (0,0) que es la esquina superior izquierda
    c.drawImage(img_reader, 0, 0, width=alto_etiq_pt, height=ancho_etiq_pt)
    c.restoreState()
    c.save()

    st.download_button("🖨️ Descargar Etiqueta Acostada", pdf_buffer.getvalue(), "Etiqueta_Acostada.pdf", "application/pdf")



















































































































































