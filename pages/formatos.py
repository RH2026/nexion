import pandas as pd
import streamlit as st
import re

def procesar_tabla_nexion(df_original):
    # 1. Definimos cuáles son las columnas que no se deben mover
    columnas_fijas = ['Número de artículo', 'Descripción del artículo']
    
    # 2. Transponemos la tabla (Unpivot)
    # 'var_name' será la columna del destino y 'value_name' la cantidad
    df_flat = df_original.melt(
        id_vars=columnas_fijas, 
        var_name='Pedido_Raw', 
        value_name='Cantidad'
    )
    
    # 3. Quitamos la columna 'TOTAL' si se coló en el proceso
    df_flat = df_flat[df_flat['Pedido_Raw'] != 'TOTAL']
    
    # 4. Limpiamos el texto para dejar solo el número de pedido
    # Usamos regex para extraer el número de 6 dígitos al final
    df_flat['Número de Pedido'] = df_flat['Pedido_Raw'].str.extract(r'(\d+)$')
    
    # 5. Quitamos las filas donde la cantidad sea 0 (para no generar pedidos vacíos)
    df_flat = df_flat[df_flat['Cantidad'] > 0]
    
    # Reordenamos las columnas como las quieres en la imagen 2
    resultado = df_flat[['Número de Pedido', 'Número de artículo', 'Descripción del artículo', 'Cantidad']]
    
    return resultado

# --- Interfaz de Streamlit ---
st.title("Convertidor de Pedidos Nexion")

uploaded_file = st.file_uploader("Sube tu Excel aquí", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Ejecutar la transformación
    df_final = procesar_tabla_nexion(df)
    
    st.write("### Vista previa del formato para Nexion:")
    st.dataframe(df_final)
    
    # Botón para descargar el resultado
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar CSV para Nexion", csv, "pedido_nexion.csv", "text/csv")




























































































































































