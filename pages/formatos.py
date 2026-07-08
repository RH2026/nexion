import streamlit as st
import qrcode
from io import BytesIO

st.subheader("Generador de Etiquetas QR")

# Campos de entrada sencillos
numero_parte = st.text_input("Número de Parte")
lote = st.text_input("Lote")

if st.button("Generar Código QR"):
    if numero_parte and lote:
        # 1. Unimos la información (puedes darle el formato que necesites)
        info_logistica = f"NP:{numero_parte} | LOTE:{lote}"
        
        # 2. Configuramos el QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M, # Nivel de corrección medio
            box_size=10,
            border=4,
        )
        qr.add_data(info_logistica)
        qr.make(fit=True)
        
        # 3. Creamos la imagen con la paleta Onyx/Neón de Nexion
        # Nota: Si los lectores de código de barras fallan, cambia a fill_color="black", back_color="white"
        img_qr = qr.make_image(fill_color="#00FFAA", back_color="#0B1114")
        
        # 4. Lo preparamos para mostrarlo en Streamlit
        buffer = BytesIO()
        img_qr.save(buffer, format="PNG")
        
        # 5. ¡Lo mostramos!
        st.image(buffer.getvalue(), caption=f"Info: {info_logistica}", width=250)
        st.success("¡QR generado exitosamente!")
    else:
        st.warning("Por favor, ingresa el Número de Parte y el Lote.")



















































































































































