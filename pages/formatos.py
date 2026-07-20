from io import BytesIO
import qrcode
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

st.subheader("🏷️ Generador de Etiquetas Nexion")

# Datos y selección
np_opt = ["712117", "PT10065", "PT10219", "PT10264"]
numero_parte = st.selectbox("Número de Parte", np_opt)
lote = st.text_input("Lote (Ej. 6181)")
valor_fijo = "140"

def get_font(size):
    for ruta in ["DejaVuSans-Bold.ttf", "arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/Arial.ttf"]:
        try: return ImageFont.truetype(ruta, size)
        except: pass
    return ImageFont.load_default()

if lote:
    texto_qr = f"{numero_parte} - {lote} - {valor_fijo}C"
    
    # Generación QR
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=15, border=1)
    qr.add_data(texto_qr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#27272A", back_color="white").convert("RGB")

    # Lienzo de Etiqueta (1004 x 1228 px)
    w_px, h_px = 1004, 1228
    etiqueta = Image.new("RGB", (w_px, h_px), "white")
    draw = ImageDraw.Draw(etiqueta)

    # Fuentes
    f_np, f_info, f_bot = get_font(54), get_font(46), get_font(42)

    # Logo
    try:
        logo = Image.open("agc.png").convert("RGBA")
        nw = 560
        nh = int(logo.size[1] * nw / logo.size[0])
        etiqueta.paste(logo.resize((nw, nh), Image.Resampling.LANCZOS), ((w_px - nw) // 2, 150), logo.resize((nw, nh), Image.Resampling.LANCZOS))
    except Exception as e:
        st.warning(f"No se encontró agc.png ({e})")

    # Textos principales
    x = 90
    draw.text((x, 300), numero_parte, fill="#222222", font=f_np)
    draw.text((x, 370), f"Lote: {lote}", fill="#222222", font=f_info)
    draw.text((x, 435), f"Cantidad: {valor_fijo}", fill="#222222", font=f_info)

    # Pegar QR
    qr_sz = 450
    etiqueta.paste(qr_img.resize((qr_sz, qr_sz), Image.Resampling.NEAREST), ((w_px - qr_sz) // 2, 510))

    # Texto inferior centrado
    bbox = draw.textbbox((0, 0), texto_qr, font=f_bot)
    draw.text(((w_px - (bbox[2] - bbox[0])) // 2, 980), texto_qr, fill="#222222", font=f_bot)

    # Vista previa e Instrucciones lado a lado
    st.markdown("### Vista previa e Instrucciones")
    col1, col2 = st.columns([1, 1.2])
    
    buf_img = BytesIO()
    etiqueta.save(buf_img, format="PNG")
    
    with col1:
        st.image(buf_img.getvalue(), width=280)
    with col2:
        st.info("""
        **Instrucciones de impresión:**
        1. **Abrir el PDF** descargado.
        2. Presionar **CTRL + P** (imprimir).
        3. Seleccionar la impresora **Zebra 200**.
        4. Configurar la orientación en **Horizontal**.
        5. Entrar a **Propiedades** y ajustar tamaño a **10.40 x 8.00 cm**.
        6. Dar clic en **Aceptar** y **Imprimir**. ¡Listo! 🚀
        """)

    # Generación de PDF
    pdf_buf = BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=(8.5 * cm, 10.4 * cm))
    buf_img.seek(0)
    c.drawImage(ImageReader(buf_img), 0, 0, width=8.5 * cm, height=10.4 * cm)
    c.showPage()
    c.save()

    st.markdown("---")
    st.download_button("🖨️ Descargar Etiqueta PDF", pdf_buf.getvalue(), file_name=f"Etiqueta_{numero_parte}_{lote}.pdf", mime="application/pdf")
















































































































































