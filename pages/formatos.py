import streamlit as st
import pandas as pd

# --- Inventario de prueba ---
df_inv = pd.DataFrame({
    "CODIGO": ["A001", "B002", "C003"],
    "DESCRIPCION": ["Tornillo 10mm", "Tuerca M8", "Arandela 10mm"]
})

# LIMPIAR INVENTARIO
df_inv["CODIGO"] = df_inv["CODIGO"].astype(str).str.strip().str.upper()
df_inv["DESCRIPCION"] = df_inv["DESCRIPCION"].astype(str).str.strip()

# --- Input de usuario ---
new_codigo = st.text_input("Ingresa el código que quieres buscar").strip().upper()

# --- Mostrar matriz y búsqueda ---
st.write("Códigos en inventario:", df_inv["CODIGO"].tolist())
st.write("Código ingresado:", new_codigo)

# --- Buscar descripción ---
desc_series = df_inv.loc[df_inv["CODIGO"] == new_codigo, "DESCRIPCION"]
desc = desc_series.iloc[0] if not desc_series.empty else "NO ENCONTRADO"

st.write("Descripción encontrada:", desc)





























