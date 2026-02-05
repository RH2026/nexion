import streamlit as st
import pandas as pd

# 1. Base de datos de costos (Basada en tu lista)
precios = {
    "Elements": 29.34,
    "Almond Olive": 33.83,
    "Biogena": 48.95,
    "Cava": 34.59,
    "Lavarino": 36.30,
    "Ecologicos": 47.85,
    # ... agregar todos los demás
}

st.title("Generador de Reporte de Muestras - JYPESA")

with st.form("formulario_muestras"):
    st.subheader("Datos del Destinatario")
    hotel = st.text_input("Nombre del Hotel / Destinatario")
    
    st.subheader("Selección de Amenidades (Kits)")
    # Creamos columnas para que el formulario no sea tan largo
    col1, col2 = st.columns(2)
    
    with col1:
        cant_elements = st.number_input("Elements", min_value=0, step=1)
        cant_almond = st.number_input("Almond Olive", min_value=0, step=1)
        
    with col2:
        flete_manual = st.number_input("Costo de Flete (Manual)", min_value=0.0)

    # Botón de envío
    enviar = st.form_submit_button("Calcular y Generar")

if enviar:
    # 2. Cálculo Automático
    costo_muestras = (cant_elements * precios["Elements"]) + (cant_almond * precios["Almond Olive"])
    total_general = costo_muestras + flete_manual
    
    # 3. Mostrar Resultados en pantalla
    st.success(f"Reporte Generado con éxito")
    st.write(f"**Costo Total Muestras:** ${costo_muestras:.2f}")
    st.write(f"**Costo Flete:** ${flete_manual:.2f}")
    st.metric("TOTAL GENERAL", f"${total_general:.2f}")

















