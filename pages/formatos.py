import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

st.subheader("🏷️ Generador de Etiquetas Nexion")

# =========================
# DATOS DE ENTRADA
# =========================

opciones_np = [
    "712117",
    "PT10065",
    "PT10219",
    "PT10264"
]

numero_parte = st.selectbox("Número de Parte", opciones_np)
lote = st.text_input("Lote (Ej. 6181)")
valor_fijo = "140"

if lote:

    texto_qr_inferior = f"{numero_parte} - {lote} - {valor_fijo}C"

    # =========================
    # GENERAR QR
    # =========================

    qr = qrcode.QRCode(
        version=1,
        box_size=15,
        border=1
    )

    qr.add_data(texto_qr_inferior)
    qr.make(fit=True)

    img_qr = qr.make_image(
        fill_color="#27272A",
        back_color="white"
    ).convert("RGB")

    # =========================
    # ETIQUETA 10.40 x 8.50 cm
    # 300 DPI
    # =========================

    ancho_px = 1004
    alto_px = 1228

    etiqueta = Image.new("RGB", (ancho_px, alto_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    # =========================
    # FUENTES
    # =========================

    try:
        font_datos = ImageFont.truetype("arial.ttf", 58)
        font_bottom = ImageFont.truetype("arial.ttf", 52)
    except:
        font_datos = ImageFont.load_default()
        font_bottom = ImageFont.load_default()

    # =========================
    # LOGO
    # =========================

    try:
        logo = Image.open("agc.png").convert("RGBA")

        logo_w, logo_h = logo.size

        target_w = 650
        target_h = int((target_w / logo_w) * logo_h)

        logo = logo.resize(
            (target_w, target_h),
            Image.Resampling.LANCZOS
        )

        logo_x = (ancho_px - target_w) // 2
        logo_y = 35

        etiqueta.paste(
            logo,
            (logo_x, logo_y),
            logo
        )

    except Exception as e:
        st.warning(f"No se pudo cargar el logo AGC ({e})")

    # =========================
    # DATOS
    # =========================

    draw.text(
        (100, 235),
        numero_parte,
        fill="#27272A",
        font=font_datos
    )

    draw.text(
        (100, 305),
        lote,
        fill="#27272A",
        font=font_datos
    )

    draw.text(
        (100, 375),
        valor_fijo,
        fill="#27272A",
        font=font_datos
    )

    # =========================
    # QR
    # =========================

    img_qr = img_qr.resize((580, 580))

    qr_w, qr_h = img_qr.size

    pos_x = (ancho_px - qr_w) // 2
    pos_y = 430

    etiqueta.paste(
        img_qr,
        (pos_x, pos_y)
    )

    # =========================
    # TEXTO INFERIOR
    # =========================

    try:
        bbox = draw.textbbox(
            (0, 0),
            texto_qr_inferior,
            font=font_bottom
        )

        w_texto = bbox[2] - bbox[0]

    except:
        w_texto = len(texto_qr_inferior) * 28

    draw.text(
        (
            (ancho_px - w_texto) // 2,
            1120
        ),
        texto_qr_inferior,
        fill="#27272A",
        font=font_bottom
    )

    # =========================
    # VISTA PREVIA
    # =========================

    st.markdown("### Vista previa")

    buf_preview = BytesIO()
    etiqueta.save(buf_preview, format="PNG")

    st.image(
        buf_preview.getvalue(),
        width=320
    )

    # =========================
    # PDF
    # =========================

    pdf_buffer = BytesIO()

    c = canvas.Canvas(
        pdf_buffer,
        pagesize=letter
    )

    ancho_carta, alto_carta = letter

    ancho_etiq_pt = 8.5 * cm
    alto_etiq_pt = 10.4 * cm

    margen = 0.5 * cm

    buf_preview.seek(0)

    img_reader = ImageReader(buf_preview)

    c.rotate(90)

    x_pos = alto_carta - margen - ancho_etiq_pt
    y_pos = -(margen + alto_etiq_pt)

    c.drawImage(
        img_reader,
        x_pos,
        y_pos,
        width=ancho_etiq_pt,
        height=alto_etiq_pt
    )

    c.showPage()
    c.save()

    # =========================
    # DESCARGA
    # =========================

    st.markdown("---")

    st.download_button(
        label="🖨️ Descargar Etiqueta PDF",
        data=pdf_buffer.getvalue(),
        file_name=f"Etiqueta_{numero_parte}_{lote}.pdf",
        mime="application/pdf"
    )



















































































































































