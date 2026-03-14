import streamlit as st
import cv2
from pyzbar.pyzbar import decode
import numpy as np

st.title("Lector de Muestras - JYPESA")

# Usamos el input de cámara de Streamlit que es muy compatible con Android
img_file_buffer = st.camera_input("Escanea el código de barras de la muestra")

if img_file_buffer is not None:
    # Convertir la imagen para que OpenCV la entienda
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    # Buscar códigos de barras en la imagen
    objetos_detectados = decode(cv2_img)

    if objetos_detectados:
        for obj in objetos_detectados:
            codigo_leido = obj.data.decode("utf-8")
            st.success(f"✅ Código detectado: {codigo_leido}")
            
            # Aquí puedes poner tu lógica para buscar en el inventario
            st.write(f"Buscando información para el código {codigo_leido}...")
    else:
        st.warning("No se detectó ningún código. Intenta acercar más la cámara o mejorar la iluminación.")























































































