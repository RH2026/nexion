import streamlit as st
import pandas as pd

st.title("Procesador de Traspasos - Nexion")

uploaded_file = st.file_uploader("Sube el Excel de la matriz, amor", type=["xlsx"])

if uploaded_file is not None:
    try:
        data = pd.read_excel(uploaded_file, header=None)
        
        row_index = 0
        for i, row in data.iterrows():
            if "DESCRIPCION" in row.astype(str).values:
                row_index = i
                break
        
        df = pd.read_excel(uploaded_file, header=row_index)
        df.columns = df.columns.astype(str).str.strip().str.replace('\n', ' ')

        # Identificamos las columnas clave
        col_desc = [c for c in df.columns if 'DESCRIP' in c.upper()][0]
        col_cod = [c for c in df.columns if 'COD' in c.upper()][0]

        # Identificamos las columnas de ciudades
        ciudades = [c for c in df.columns if c not in [col_desc, col_cod] and "Unnamed" not in c]
        
        # Transformamos la tabla incluyendo el código en id_vars
        df_unpivoted = df.melt(
            id_vars=[col_cod, col_desc], # <--- Aquí incluimos el código para que no se pierda
            value_vars=ciudades,
            var_name='nombre del envio',
            value_name='cantidad'
        )

        df_unpivoted['cantidad'] = pd.to_numeric(df_unpivoted['cantidad'], errors='coerce')
        df_final = df_unpivoted[df_unpivoted['cantidad'] > 0].dropna(subset=['cantidad']).copy()

        # Reordenamos las columnas para que el código aparezca
        df_final = df_final[['nombre del envio', col_cod, col_desc, 'cantidad']]
        df_final.columns = ['nombre del envio', 'codigo', 'descripcion producto', 'cantidad']

        st.success(f"¡Ahora sí está completo! Procesé {len(df_final)} líneas.")
        st.dataframe(df_final, use_container_width=True)

        csv = df_final.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="Descargar CSV con Códigos",
            data=csv,
            file_name='traspasos_con_codigo.csv',
            mime='text/csv',
        )

    except Exception as e:
        st.error(f"Hubo un detalle, cielo: {e}")
else:
    st.info("Sube la matriz para generar la lista con códigos.")







































