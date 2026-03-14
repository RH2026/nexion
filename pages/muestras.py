import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import pytesseract

st.set_page_config(page_title="Nexion - Lector JYPESA", layout="centered")

st.title("🚀 Scanner Inteligente Nexion")
st.write("Usa la cámara para leer códigos de barras o texto de las etiquetas.")

# 1. Entrada de cámara
img_file_buffer = st.camera_input("Captura la etiqueta")

if img_file_buffer is not None:
    # Convertir el buffer de la imagen a un formato que OpenCV entienda
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    # --- PARTE 1: LECTURA DE CÓDIGO DE BARRAS ---
    st.subheader("📦 Resultado Código de Barras")
    codigos = decode(cv2_img)
    
    if codigos:
        for obj in codigos:
            puntos = obj.polygon
            codigo_data = obj.data.decode('utf-8')
            tipo_codigo = obj.type
            st.success(f"**Detectado:** {codigo_data} ({tipo_codigo})")
    else:
        st.warning("No se encontró ningún código de barras.")

    # --- PARTE 2: LECTURA DE TEXTO (OCR MEJORADO) ---
    st.subheader("📝 Resultado de Texto")
    
    # Preprocesamiento para evitar que salga "mocho"
    gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY) # Pasar a gris
    # Aumentar contraste y nitidez
    filtro = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Configuración para que lea bloques de texto más completos
    custom_config = r'--oem 3 --psm 6'
    texto = pytesseract.image_to_string(filtro, lang='spa', config=custom_config)

    if texto.strip():
        # Limpiamos un poco el texto de saltos de línea raros
        texto_limpio = texto.replace("\n", " ")
        st.info("Texto encontrado:")
        st.write(texto_limpio)
        
        # Opcional: Botón para copiar el texto
        st.button("Copiar texto leído")
    else:
        st.error("No se pudo leer texto claro. Intenta con más luz.")

    # --- VISUALIZACIÓN DE APOYO ---
    with st.expander("Ver qué está leyendo el sistema"):
        st.image(filtro, caption="Imagen procesada para OCR")























































































