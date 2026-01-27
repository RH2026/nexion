import streamlit as st
import pandas as pd

# --- CARGAR INVENTARIO ---
try:
    df_inv = pd.read_csv("../inventario.csv")
except FileNotFoundError:
    st.error("No se pudo cargar inventario.csv")
    df_inv = pd.DataFrame(columns=["CODIGO", "DESCRIPCION"])

df_inv["CODIGO"] = df_inv["CODIGO"].astype(str).str.strip().str.upper()
df_inv["DESCRIPCION"] = df_inv["DESCRIPCION"].astype(str).str.strip()

# --- Session state ---
if "df_final" not in st.session_state:
    st.session_state.df_final = pd.DataFrame(columns=["CODIGO","DESCRIPCION","CANTIDAD"])

# --- Formulario ---
with st.expander("➕ Nuevo Registro de Actividad", expanded=True):
    with st.form("form_nueva_fila"):  # <-- quité clear_on_submit por ahora
        new_codigo = st.text_input("Código / Parte")
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
        submitted = st.form_submit_button("Añadir y Sincronizar")
        
        if submitted:
            if new_codigo.strip() == "":
                st.warning("Ingresa un código antes de añadir")
            else:
                cod_upper = new_codigo.strip().upper()
                desc_series = df_inv.loc[df_inv["CODIGO"] == cod_upper, "DESCRIPCION"]
                desc = desc_series.iloc[0] if not desc_series.empty else "NO ENCONTRADO"
                
                new_row = {"CODIGO": cod_upper, "DESCRIPCION": desc, "CANTIDAD": cantidad}
                st.session_state.df_final = pd.concat([st.session_state.df_final, pd.DataFrame([new_row])], ignore_index=True)
                
                st.success(f"Fila añadida: {cod_upper} → {desc}")

# --- Mostrar tabla ---
st.dataframe(st.session_state.df_final)

































