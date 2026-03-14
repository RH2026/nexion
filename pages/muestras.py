import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import pytesseract

st.title("Scanner Inteligente Nexion")

img_file_buffer = st.camera_input("Captura la etiqueta de la muestra")

if img_file_buffer is not None:
    # Convertir imagen
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    # 1. Intentar leer Código de Barras
    codigos = decode(cv2_img)
    if codigos:
        for obj in codigos:
            st.success(f"📦 Código de barras: {obj.data.decode('utf-8')}")

    # 2. Intentar leer Texto (OCR)
    # Convertimos a escala de grises para que sea más fácil leer letras
    gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
    texto_detectado = pytesseract.image_to_string(gray, lang='spa')

    if texto_detectado.strip():
        st.info("📝 Texto detectado en la etiqueta:")
        st.text(texto_detectado)
    else:
        st.warning("No se detectó texto claro, intenta enfocar mejor.")























































































