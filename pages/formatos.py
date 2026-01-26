import streamlit as st
import pandas as pd

# --- CARGAR INVENTARIO ---
# Simulamos la matriz de inventario
df_inv = pd.DataFrame({
    "CODIGO": ["A001", "B002", "C003"],
    "DESCRIPCION": ["Tornillo 10mm", "Tuerca M8", "Arandela 10mm"]
})

# LIMPIAR INVENTARIO
df_inv["CODIGO"] = df_inv["CODIGO"].astype(str).str.strip().str.upper()
df_inv["DESCRIPCION"] = df_inv["DESCRIPCION"].astype(str).str.strip()

# --- SESSION STATE ---
st.session_state.setdefault("df_final", pd.DataFrame(columns=["CODIGO","DESCRIPCION","CANTIDAD"]))

# --- FORMULARIO ---
new_codigo = st.text_input("Código / Parte")
cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)

# --- BOTÓN AÑADIR ---
if st.button("Añadir y Sincronizar"):
    if new_codigo.strip() != "":
        cod_upper = new_codigo.strip().upper()
        
        # BUSCAR DESCRIPCION EN LA MATRIZ
        desc_series = df_inv.loc[df_inv["CODIGO"] == cod_upper, "DESCRIPCION"]
        desc = desc_series.iloc[0] if not desc_series.empty else "NO ENCONTRADO"
        
        # AÑADIR FILA AL DATAFRAME FINAL
        new_row = {"CODIGO": cod_upper, "DESCRIPCION": desc, "CANTIDAD": cantidad}
        st.session_state.df_final = pd.concat([st.session_state.df_final, pd.DataFrame([new_row])], ignore_index=True)
        
        st.success(f"Fila añadida: {cod_upper} → {desc}")
        # Limpiar input manualmente
        st.experimental_set_query_params(new_codigo="")  # o st.session_state["new_codigo"]="" si quieres

# --- MOSTRAR TABLA ---
st.dataframe(st.session_state.df_final)






























