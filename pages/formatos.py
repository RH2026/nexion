import os
from io import BytesIO

import qrcode
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

st.subheader("🏷️ Generador de Etiquetas Nexion")

# ==========================
# DATOS
# ==========================

opciones_np = [
    "712117",
    "PT10065",
    "PT10219",
    "PT10264"
]

numero_parte = st.selectbox("Número de Parte", opciones_np)
lote = st.text_input("Lote (Ej. 6181)")
valor_fijo = "140"

# ==========================
# FUNCIÓN PARA CARGAR FUENTE
# ==========================

def cargar_fuente(size):
    posibles = [
        "DejaVuSans-Bold.ttf",
        "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial.ttf"
    ]

    for ruta in posibles:
        try:
            return ImageFont.truetype(ruta, size)
        except:
            pass

    return ImageFont.load_default()


if lote:
    texto_qr = f"{numero_parte} - {lote} - {valor_fijo}C"

    # ==========================
    # QR
    # ==========================

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=1
    )

    qr.add_data(texto_qr)
    qr.make(fit=True)

    qr_img = qr.make_image(
        fill_color="#27272A",
        back_color="white"
    ).convert("RGB")

    # ==========================
    # TAMAÑO ETIQUETA
    # 8.50 x 10.40 cm (Vertical)
    # ==========================

    ancho_px = 1004
    alto_px = 1228

    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    font_np = cargar_fuente(54)
    font_info = cargar_fuente(46)
    font_bottom = cargar_fuente(42)

    # ==========================
    # LOGO
    # ==========================

    try:
        logo = Image.open("agc.png").convert("RGBA")
        logo_w, logo_h = logo.size

        nuevo_ancho = 620
        nuevo_alto = int(logo_h * nuevo_ancho / logo_w)

        logo = logo.resize(
            (nuevo_ancho, nuevo_alto),
            Image.Resampling.LANCZOS
        )

        etiqueta.paste(
            logo,
            ((ancho_px - nuevo_ancho)//2, 30),
            logo
        )

    except Exception as e:
        st.warning(f"No se encontró agc.png ({e})")

    # ==========================
    # TEXTO
    # ==========================

    x = 90

    draw.text(
        (x, 210),
        numero_parte,
        fill="#222222",
        font=font_np
    )

    draw.text(
        (x, 280),
        f"Lote: {lote}",
        fill="#222222",
        font=font_info
    )

    draw.text(
        (x, 345),
        f"Cantidad: {valor_fijo}",
        fill="#222222",
        font=font_info
    )

    # ==========================
    # QR
    # ==========================

    qr_img = qr_img.resize(
        (560, 560),
        Image.Resampling.NEAREST
    )

    etiqueta.paste(
        qr_img,
        ((ancho_px-560)//2, 420)
    )

    # ==========================
    # TEXTO INFERIOR
    # ==========================

    bbox = draw.textbbox(
        (0, 0),
        texto_qr,
        font=font_bottom
    )

    ancho_texto = bbox[2] - bbox[0]

    draw.text(
        (
            (ancho_px-ancho_texto)//2,
            1080
        ),
        texto_qr,
        fill="#222222",
        font=font_bottom
    )

    # ==========================
    # VISTA PREVIA
    # ==========================

    st.markdown("### Vista previa")

    buffer_img = BytesIO()
    etiqueta.save(buffer_img, format="PNG")

    st.image(
        buffer_img.getvalue(),
        width=340
    )

    # ==========================
    # PDF (A medida de la etiqueta, vertical)
    # ==========================

    pdf_buffer = BytesIO()

    ancho_pdf = 8.5 * cm
    alto_pdf = 10.4 * cm

    # Se crea el lienzo con el tamaño exacto de la etiqueta (vertical)
    c = canvas.Canvas(
        pdf_buffer,
        pagesize=(ancho_pdf, alto_pdf)
    )

    buffer_img.seek(0)
    img_reader = ImageReader(buffer_img)

    # Se dibuja la imagen ocupando todo el espacio de la página sin rotaciones
    c.drawImage(
        img_reader,
        0,
        0,
        width=ancho_pdf,
        height=alto_pdf
    )

    c.showPage()
    c.save()

    # ==========================
    # DESCARGA
    # ==========================

    st.markdown("---")

    st.download_button(
        "🖨️ Descargar Etiqueta PDF",
        pdf_buffer.getvalue(),
        file_name=f"Etiqueta_{numero_parte}_{lote}.pdf",
        mime="application/pdf"
    )


















































































































































