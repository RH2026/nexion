import streamlit as st
import pandas as pd

st.subheader("Conciliación de Costos: Operación vs Tresguerras")

# 1. Cargadores de archivos interactivos
col1, col2 = st.columns(2)
with col1:
    archivo_matriz = st.file_uploader("📥 Sube tu Matriz Operativa", type=["xlsx", "xls"])
with col2:
    archivo_tg = st.file_uploader("📥 Sube el reporte de Tresguerras", type=["xlsx", "xls"])

# 2. Procesamos la información cuando subas ambos archivos
if archivo_matriz and archivo_tg:
    try:
        df_matriz = pd.read_excel(archivo_matriz)
        df_tg = pd.read_excel(archivo_tg)
        
        # Limpiamos espacios invisibles en los encabezados por seguridad
        df_matriz.columns = df_matriz.columns.str.strip()
        df_tg.columns = df_tg.columns.str.strip()
        
        # 3. Hacemos el Match usando los nombres EXACTOS de tus columnas
        df_match = pd.merge(
            df_matriz, 
            df_tg, 
            on=['FACTURA', 'NÚMERO DE GUÍA'], 
            how='outer', 
            suffixes=('_Matriz', '_TG'),
            indicator=True
        )
        
        # 4. Función lógica para encontrar las diferencias de costos
        def revisar_estatus(fila):
            if fila['_merge'] == 'left_only':
                return 'Falta en reporte Tresguerras'
            elif fila['_merge'] == 'right_only':
                return 'Falta en tu Matriz'
            elif fila['COSTO DE LA GUÍA_Matriz'] == fila['COSTO DE LA GUÍA_TG']:
                return '¡Cuadra perfecto!'
            else:
                matriz_val = fila['COSTO DE LA GUÍA_Matriz']
                tg_val = fila['COSTO DE LA GUÍA_TG']
                return f"Diferencia de costo: Matriz(${matriz_val}) vs TG(${tg_val})"

        # Aplicamos la revisión fila por fila
        df_match['Estatus_Match'] = df_match.apply(revisar_estatus, axis=1)
        
        # Limpiamos la columna interna de Pandas para el resultado final
        df_resultado = df_match.drop(columns=['_merge'])
        
        st.success("¡Conciliación completada con éxito, corazón!")
        
        # 5. Mostramos el resultado en una tabla premium de Streamlit
        st.dataframe(df_resultado, use_container_width=True)
        
        # Botón elegante para que descargues el reporte listo para el contador
        csv = df_resultado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte de Diferencias (CSV)",
            data=csv,
            file_name="Conciliacion_Matriz_vs_Tresguerras.csv",
            mime="text/csv",
        )
        
    except KeyError as e:
        st.error(f"¡Ups! Asegúrate de que ambos archivos tengan las columnas escritas igual. Error en: {e}")
    except Exception as e:
        st.error(f"Hubo un detalle inesperado: {e}")
else:
    st.info("Esperando a que subas ambos archivos para ejecutar el cruce de datos, mi vida.")






































