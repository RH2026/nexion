import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="JYPESA | Logistics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("JYPESA // NEXION SMART LOGISTICS")
st.write(
    "Sistema limpio de respaldo para sincronización de código y evitar errores"
    " de sintaxis."
)

uploaded_file = st.file_uploader(
    "Subir archivo ERP", type=["xlsx", "csv"], key="erp_file_clean"
)

if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)
    st.success("¡Archivo cargado correctamente!")
    st.dataframe(df)
  except Exception as e:
    st.error(f"Error al leer el archivo: {e}")
