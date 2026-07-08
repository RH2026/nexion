import streamlit as st
import qrcode
import os
import urllib.request
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

st.subheader("Generador de Etiquetas AGC")

# --- NUEVO: Función para descargar la fuente automáticamente ---
def cargar_fuente(nombre, url, size):
    if not os.path.exists(nombre):
        try:
            urllib.request.urlretrieve(url, nombre)
        except Exception as e:
            st.error("Hubo un detalle descargando la fuente, pero seguimos trabajando.")
            return ImageFont.load_default()
    try:
        return ImageFont.truetype(nombre, size)
    except:
        return ImageFont.load_default()

# Enlaces directos a las fuentes de Google
url_bold = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
url_regular = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"

# Configuramos los tamaños exactos de las letras
font_logo = cargar_fuente("Roboto-Bold.ttf", url_bold, 120)
font_slogan = cargar_fuente("Roboto-Regular.ttf", url_regular, 35)
font_datos = cargar_fuente("Roboto-Bold.ttf", url_bold, 75) 
font_bottom = cargar_fuente("Roboto-Regular.ttf", url_regular, 75)
# ---------------------------------------------------------------

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
    
    # 4. Creamos el lienzo de la etiqueta (12 cm x 8.5 cm a 300 DPI)
    ancho_px, alto_px = 1004, 1417
    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    # --- DIBUJAMOS LOS ELEMENTOS CON LA FUENTE NUEVA ---
    
    # Logo y Slogan
    draw.text((80, 100), "AGC", fill="#1E3A8A", font=font_logo)
    draw.text((80, 230), "ARTÍCULOS DE GRAN CONSUMO", fill="#1E3A8A", font=font_slogan)
    
    # Variables de logística
    draw.text((80, 350), numero_parte, fill="#27272A", font=font_datos)
    draw.text((80, 440), lote, fill="#27272A", font=font_datos)
    draw.text((80, 530), valor_fijo, fill="#27272A", font=font_datos)
    
    # Pegamos el QR centrado
    img_qr = img_qr.resize((700, 700)) 
    qr_w, qr_h = img_qr.size
    pos_x = (ancho_px - qr_w) // 2
    pos_y = 600
    etiqueta.paste(img_qr, (pos_x, pos_y))
    
    # Texto inferior centrado
    bbox = draw.textbbox((0, 0), texto_qr_inferior, font=font_bottom)
    w_texto = bbox[2] - bbox[0]
    draw.text(((ancho_px - w_texto) // 2, 1320), texto_qr_inferior, fill="#27272A", font=font_bottom)

    # 5. Mostramos la vista previa en pantalla
    st.markdown("### Vista Previa:")
    buf_preview = BytesIO()
    etiqueta.save(buf_preview, format="PNG")
    st.image(buf_preview.getvalue(), width=350)
    
    # 6. Preparamos el PDF final para la Zebra
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    ancho_carta, alto_carta = letter
    
    ancho_etiq_pt = 8.5 * cm
    alto_etiq_pt = 12 * cm
    
    buf_preview.seek(0)
    img_reader = ImageReader(buf_preview)
    
    # Rotamos y acomodamos la etiqueta
    c.translate(ancho_carta / 2, alto_carta / 2)
    c.rotate(90)
    c.drawImage(img_reader, -ancho_etiq_pt / 2, -alto_etiq_pt / 2, width=ancho_etiq_pt, height=alto_etiq_pt)
    c.showPage()
    c.save()

    # 7. Botón de descarga
    st.markdown("---")
    st.download_button(
        label="🖨️ Imprimir Etiqueta (PDF Tamaño Carta)",
        data=pdf_buffer.getvalue(),
        file_name=f"Etiqueta_{numero_parte}_Lote{lote}.pdf",
        mime="application/pdf"
    )



















































































































































