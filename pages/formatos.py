import streamlit as st
import pandas as pd

# --- CARGAR INVENTARIO REAL DESDE LA CARPETA SUPERIOR ---
try:
    df_inv = pd.read_csv("../inventario.csv")  # <-- aquí la ruta correcta
except FileNotFoundError:
    st.error("No se pudo cargar inventario.csv")
    df_inv = pd.DataFrame(columns=["CODIGO", "DESCRIPCION"])

# LIMPIAR INVENTARIO
df_inv["CODIGO"] = df_inv["CODIGO"].astype(str).str.strip().str.upper()
df_inv["DESCRIPCION"] = df_inv["DESCRIPCION"].astype(str).str.strip()

# --- Session state para prueba ---
st.session_state.setdefault("df_final", pd.DataFrame(columns=["CODIGO","DESCRIPCION","CANTIDAD"]))

# --- Inputs ---
new_codigo = st.text_input("Ingresa el código que quieres probar").strip().upper()
cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)

# --- Mostrar matriz y búsqueda ---
st.write("Códigos disponibles en inventario:", df_inv["CODIGO"].tolist())
st.write("Código ingresado:", new_codigo)

# --- Buscar descripción ---
desc_series = df_inv.loc[df_inv["CODIGO"] == new_codigo, "DESCRIPCION"]
desc = desc_series.iloc[0] if not desc_series.empty else "NO ENCONTRADO"

st.write("Descripción encontrada:", desc)

# --- Botón añadir a la tabla ---
if st.button("Añadir a tabla") and new_codigo:
    new_row = {"CODIGO": new_codigo, "DESCRIPCION": desc, "CANTIDAD": cantidad}
    st.session_state.df_final = pd.concat([st.session_state.df_final, pd.DataFrame([new_row])], ignore_index=True)
    st.success(f"Fila añadida: {new_codigo} → {desc}")

# --- Mostrar tabla final ---
st.dataframe(st.session_state.df_final)































