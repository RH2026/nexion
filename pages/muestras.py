import streamlit as st
from streamlit_barcode_reader import barcode_reader

st.title("Scanner Nexion - JYPESA")

st.write("Haz clic en el botón para activar la cámara y escanear:")

# Este componente abre la cámara en el navegador de Android
barcode_value = barcode_reader()

if barcode_value:
    st.success(f"¡Código detectado!: {barcode_value}")
    
    # Aquí podrías buscar el código en tu base de datos de inventario
    st.info(f"Buscando producto {barcode_value} en el sistema...")
else:
    st.warning("Esperando a que escanees un código...")
























































































