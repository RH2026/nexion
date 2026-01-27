import streamlit as st
import pandas as pd

# --- Session state ---
if "df_final" not in st.session_state:
    st.session_state.df_final = pd.DataFrame(columns=["CODIGO","DESCRIPCION","CANTIDAD"])

# --- Formulario mínimo ---
with st.expander("➕ Nuevo Registro de Actividad", expanded=True):
    with st.form("form_nueva_fila"):
        new_codigo = st.text_input("Código / Parte")
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
        submitted = st.form_submit_button("Añadir")
        
        if submitted:
            st.session_state.df_final = pd.concat(
                [st.session_state.df_final, pd.DataFrame([{
                    "CODIGO": new_codigo.strip().upper(),
                    "DESCRIPCION": "TEST",
                    "CANTIDAD": cantidad
                }])],
                ignore_index=True
            )
            st.success(f"Fila añadida: {new_codigo}")

# --- Mostrar tabla ---
st.dataframe(st.session_state.df_final)






























