import streamlit as st
import pandas as pd

st.title("Carga de Traspasos - Nexion")

# 1. El usuario sube el archivo directamente desde su PC
uploaded_file = st.file_uploader("Sube tu archivo de Excel aquí, amor", type=["xlsx"])

if uploaded_file is not None:
    # 2. Leemos el archivo que se acaba de subir
    df = pd.read_excel(uploaded_file)
    
    # Mostramos una vista previa para que veas que cargó bien
    st.write("Archivo cargado con éxito. Procesando datos...")

    # 3. Definimos las columnas fijas
    columnas_fijas = ['DESCRIPCION', 'CODIGO']

    # 4. Transformamos la tabla (Melt)
    df_unpivoted = df.melt(
        id_vars=columnas_fijas, 
        var_name='nombre del envio', 
        value_name='cantidad'
    )

    # 5. Quitamos los ceros y vacíos
    df_final = df_unpivoted[df_unpivoted['cantidad'] > 0].copy()

    # 6. Reordenamos y renombramos
    df_final = df_final[['nombre del envio', 'DESCRIPCION', 'cantidad']]
    df_final.columns = ['nombre del envio', 'descripcion producto', 'cantidad']

    # 7. Mostramos el resultado final en la app
    st.subheader("Resultado para cargar al sistema:")
    st.dataframe(df_final)

    # 8. Botón para que puedas descargar el resultado procesado
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar lista procesada (CSV)",
        data=csv,
        file_name='carga_sistema_nexion.csv',
        mime='text/csv',
    )
else:
    st.info("Esperando a que subas el archivo de traspasos... 😊")
  







































