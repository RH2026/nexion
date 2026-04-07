import streamlit as st
import pandas as pd

st.title("Carga de Traspasos - Nexion")

uploaded_file = st.file_uploader("Sube tu archivo de Excel aquí", type=["xlsx"])

if uploaded_file is not None:
    # 1. Ajustamos el header. Si con 1 no funciona, prueba con 2.
    # Según tu imagen, los nombres están en la fila 3 (que para Python es índice 2)
    df = pd.read_excel(uploaded_file, header=2)
    
    # Limpiamos espacios y saltos de línea en los nombres de columnas
    df.columns = df.columns.astype(str).str.strip().str.replace('\n', ' ')

    # 2. Nombres EXACTOS según tu imagen
    # Nota: puse 'CÓDIGO' con acento porque así suele estar en esos formatos
    col_desc = 'DESCRIPCION' 
    col_cod = 'CODIGO' # Si falla, intenta cambiándolo a 'CÓDIGO' con acento

    # Verificamos si las columnas existen (si no, las buscamos por aproximación)
    if col_desc not in df.columns:
        # Buscamos una columna que contenga la palabra 'DESCRIP'
        posibles = [c for c in df.columns if 'DESCRIP' in c.upper()]
        if posibles: col_desc = posibles[0]

    if col_cod not in df.columns:
        # Buscamos una columna que contenga la palabra 'COD'
        posibles = [c for c in df.columns if 'COD' in c.upper()]
        if posibles: col_cod = posibles[0]

    try:
        # 3. Transformamos la tabla
        df_unpivoted = df.melt(
            id_vars=[col_desc, col_cod], 
            var_name='nombre del envio', 
            value_name='cantidad'
        )

        # 4. Convertimos a número y quitamos basura
        df_unpivoted['cantidad'] = pd.to_numeric(df_unpivoted['cantidad'], errors='coerce')
        df_final = df_unpivoted[df_unpivoted['cantidad'] > 0].dropna(subset=['cantidad']).copy()

        # 5. Formato final solicitado
        df_final = df_final[['nombre del envio', col_desc, 'cantidad']]
        df_final.columns = ['nombre del envio', 'descripcion producto', 'cantidad']

        st.success("¡Logrado, amor! Aquí tienes los datos:")
        st.dataframe(df_final)

        csv = df_final.to_csv(index=False).encode('utf-8-sig')
        st.download_button("Descargar CSV para Carga", data=csv, file_name='carga_nexion.csv', mime='text/csv')

    except Exception as e:
        st.error(f"Hubo un detalle: {e}")
        st.write("Columnas que detecté en tu archivo:", list(df.columns))
else:
    st.info("Esperando el archivo, corazón. Súbelo y yo me encargo del resto.")







































