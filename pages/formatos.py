import streamlit as st
import pandas as pd
import os

# Ver dónde estamos y qué hay
st.write("Carpeta actual:", os.getcwd())
st.write("Archivos en esta carpeta:", os.listdir())

# Cargar CSV desde la raíz
try:
    df_inv = pd.read_csv("inventario.csv")
    st.success("Inventario cargado correctamente")
except Exception as e:
    st.error(f"No se pudo cargar inventario.csv: {e}")
    df_inv = pd.DataFrame(columns=["CODIGO","DESCRIPCION"])
































