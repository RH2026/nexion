import streamlit as st
import pandas as pd

# --- CARGAR INVENTARIO ---
try:
    df_inv = pd.read_csv("../inventario.csv")  # <-- tu CSV
    st.success("Inventario cargado correctamente")
except FileNotFoundError:
    st.error("No se pudo encontrar inventario.csv")
    df_inv = pd.DataFrame(columns=["CODIGO", "DESCRIPCION"])
except Exception as e:
    st.error(f"Error al cargar inventario.csv: {e}")
    df_inv = pd.DataFrame(columns=["CODIGO", "DESCRIPCION"])

# LIMPIAR INVENTARIO
if not df_inv.empty:
    df_inv["CODIGO"] = df_inv["CODIGO"].astype(str).str.strip().str.upper()
    df_inv["DESCRIPCION"] = df_inv["DESCRIPCION"].astype(str).str.strip()

# --- Session state ---
if "df_final" not in st.session_state:
    st.session_state.df_final = pd.DataFrame(columns=["CODIGO","DESCRIPCION","CANTIDAD"])

# --- Formulario ---
with st.expander("➕ Nuevo Registro de Actividad", expanded=True):
    with st.form("form_nueva_fila", clear_on_submit=True):
        new_codigo = st.text_input("Código / Parte")
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
        submitted = st.form_submit_button("Añadir y Sincronizar")
        
        if submitted:
            cod_upper = new_codigo.strip().upper()
            if cod_upper == "":
                st.warning("Debes ingresar un código válido")
            else:
                # Buscar descripción en inventario
                desc_series = df_inv.loc[df_inv["CODIGO"] == cod_upper, "DESCRIPCION"]
                desc = desc_series.iloc[0] if not desc_series.empty else "NO ENCONTRADO"

                # Añadir fila al dataframe final
                new_row = {"CODIGO": cod_upper, "DESCRIPCION": desc, "CANTIDAD": cantidad}
                st.session_state.df_final = pd.concat([st.session_state.df_final, pd.DataFrame([new_row])], ignore_index=True)
                
                st.success(f"Fila añadida: {cod_upper} → {desc}")

# --- Mostrar tabla final ---
st.dataframe(st.session_state.df_final)































