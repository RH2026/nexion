import streamlit as st
import pandas as pd
import io

st.title("Procesador de Traspasos - Nexion")

uploaded_file = st.file_uploader("Sube el Excel de la matriz, amor", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 1. Cargamos TODO el archivo primero sin encabezados para buscar la fila real
        data = pd.read_excel(uploaded_file, header=None)
        
        # 2. Buscamos en qué fila está la palabra "DESCRIPCION"
        # Esto evita errores si mueven el título amarillo
        row_index = 0
        for i, row in data.iterrows():
            if "DESCRIPCION" in row.astype(str).values:
                row_index = i
                break
        
        # 3. Volvemos a leer el archivo pero empezando desde esa fila
        df = pd.read_excel(uploaded_file, header=row_index)
        
        # Limpiamos nombres de columnas (espacios, saltos de línea)
        df.columns = df.columns.astype(str).str.strip().str.replace('\n', ' ')

        # 4. Definimos las columnas base
        # Usamos nombres parciales por si acaso cambia a "DESCRIPCIÓN" con acento
        col_desc = [c for c in df.columns if 'DESCRIP' in c.upper()][0]
        col_cod = [c for c in df.columns if 'COD' in c.upper()][0]

        # 5. Transformamos de Matriz a Lista (Melt)
        # Las ciudades son todas las columnas EXCEPTO las que ya identificamos
        ciudades = [c for c in df.columns if c not in [col_desc, col_cod] and "Unnamed" not in c]
        
        df_unpivoted = df.melt(
            id_vars=[col_desc, col_cod],
            value_vars=ciudades,
            var_name='nombre del envio',
            value_name='cantidad'
        )

        # 6. Limpieza final de datos
        df_unpivoted['cantidad'] = pd.to_numeric(df_unpivoted['cantidad'], errors='coerce')
        df_final = df_unpivoted[df_unpivoted['cantidad'] > 0].dropna(subset=['cantidad']).copy()

        # Reordenamos como me pediste
        df_final = df_final[['nombre del envio', col_desc, 'cantidad']]
        df_final.columns = ['nombre del envio', 'descripcion producto', 'cantidad']

        # Resultados
        st.success(f"¡Listo! Procesé {len(df_final)} líneas de traspaso.")
        st.dataframe(df_final, use_container_width=True)

        # Botón de descarga
        csv = df_final.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="Descargar CSV para carga masiva",
            data=csv,
            file_name='traspasos_procesados.csv',
            mime='text/csv',
        )

    except Exception as e:
        st.error(f"Hubo un error al procesar, amor: {e}")
        st.info("Asegúrate de que la columna 'DESCRIPCION' esté presente en el Excel.")
else:
    st.info("Sube la matriz de Excel para transformarla al formato de carga de Nexion. 😊")







































