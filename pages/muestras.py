import streamlit as st
import pandas as pd

st.title("Carga de Traspasos - Nexion")

uploaded_file = st.file_uploader("Sube tu archivo de Excel aquí", type=["xlsx"])

if uploaded_file is not None:
    # 1. Usamos header=1 para decirle que los títulos reales están en la segunda fila
    # (donde dice DESCRIPCION, CODIGO, etc.)
    df = pd.read_excel(uploaded_file, header=1)
    
    st.write("Archivo leído, procesando...")

    # 2. Definimos las columnas de información
    columnas_fijas = ['DESCRIPCION', 'CODIGO']

    # 3. Transformamos la tabla (Melt)
    df_unpivoted = df.melt(
        id_vars=columnas_fijas, 
        var_name='nombre del envio', 
        value_name='cantidad'
    )

    # --- AQUÍ ESTÁ EL TRUCO PARA EL ERROR ---
    # 4. Convertimos 'cantidad' a número a la fuerza. 
    # Si encuentra texto, lo convierte en "NaN" (vacío) para que no truene.
    df_unpivoted['cantidad'] = pd.to_numeric(df_unpivoted['cantidad'], errors='coerce')

    # 5. Quitamos los ceros y los vacíos (NaN) que generamos arriba
    df_final = df_unpivoted[df_unpivoted['cantidad'] > 0].dropna(subset=['cantidad']).copy()

    # 6. Limpiamos la descripción (por si tiene saltos de línea raros)
    df_final['DESCRIPCION'] = df_final['DESCRIPCION'].astype(str).str.replace('\n', ' ', regex=True)

    # 7. Reordenamos y renombramos
    df_final = df_final[['nombre del envio', 'DESCRIPCION', 'cantidad']]
    df_final.columns = ['nombre del envio', 'descripcion producto', 'cantidad']

    # Mostramos el resultado
    st.subheader("Lista lista para cargar:")
    st.dataframe(df_final)

    # Botón de descarga
    csv = df_final.to_csv(index=False).encode('utf-8-sig') # utf-8-sig para que Excel lo lea bien
    st.download_button(
        label="Descargar CSV para Nexion",
        data=csv,
        file_name='carga_traspasos.csv',
        mime='text/csv',
    )
else:
    st.info("Sube el Excel para empezar, corazón. 😊")
  







































