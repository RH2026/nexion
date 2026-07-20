from io import BytesIO
import qrcode
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# ==========================
# ESTILO Y DISEÑO NEXION (MATCH VISUAL)
# ==========================
st.markdown("""
    <style>
    .nexion-card {
        background-color: #1e252b;
        border: 1px solid #2d3748;
        border-left: 4px solid #d4af37;
        padding: 20px;
        border-radius: 8px;
        color: #e2e8f0;
        font-family: sans-serif;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .nexion-card h4 {
        color: #f7fafc;
        margin-top: 0;
        font-size: 1.1rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .nexion-card ol {
        margin: 0;
        padding-left: 20px;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #cbd5e0;
    }
    .nexion-card li strong {
        color: #edf2f7;
    }
    </style>
""", unsafe_allow_html=True)

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

    # Vista previa e Instrucciones personalizadas (A juego con la paleta de JYPESA)
    st.markdown("### Vista previa e Instrucciones")
    col1, col2 = st.columns([1, 1.2])
    
    buf_img = BytesIO()
    etiqueta.save(buf_img, format="PNG")
    
    with col1:
        st.image(buf_img.getvalue(), width=280)
        
    with col2:
        st.markdown("""
        <div class="nexion-card">
            <h4>Instrucciones de Impresión</h4>
            <ol>
                <li><strong>Abrir el PDF</strong> generado.</li>
                <li>Presionar <strong>CTRL + P</strong> en el teclado.</li>
                <li>Seleccionar la impresora <strong>Zebra 200</strong>.</li>
                <li>Ajustar la orientación a <strong>Horizontal</strong>.</li>
                <li>Entrar a <strong>Propiedades</strong> y fijar dimensiones en <strong>10.40 x 8.00 cm</strong>.</li>
                <li>Confirmar con <strong>Aceptar</strong> e imprimir.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    # Generación de PDF
    pdf_buf = BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=(8.5 * cm, 10.4 * cm))
    buf_img.seek(0)
    c.drawImage(ImageReader(buf_img), 0, 0, width=8.5 * cm, height=10.4 * cm)
    c.showPage()
    c.save()

    st.markdown("---")
    st.download_button("🖨️ Descargar Etiqueta PDF", pdf_buf.getvalue(), file_name=f"Etiqueta_{numero_parte}_{lote}.pdf", mime="application/pdf")
















































































































































