import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Corrector Logístico", layout="wide")

st.title("🛠️ Reparador de Costos: Exportación a Excel")
st.markdown("Sube tu archivo y selecciona las columnas correspondientes.")

uploaded_file = st.file_uploader("Elige tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Cargar archivo
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # --- LIMPIEZA AUTOMÁTICA DE COLUMNAS ---
        # Esto elimina espacios locos al principio o final de los nombres
        df.columns = [str(c).strip() for c in df.columns]
        
        st.subheader("Datos Originales")
        st.dataframe(df.head())

        # Configuración de columnas con selección manual para evitar el KeyError
        st.sidebar.header("📍 Asignar Columnas")
        st.sidebar.info("Selecciona el nombre real de tus columnas:")
        
        col_factura = st.sidebar.selectbox("¿Cuál es la columna de Factura?", df.columns)
        col_guia = st.sidebar.selectbox("¿Cuál es la columna de Guía?", df.columns)
        col_costo = st.sidebar.selectbox("¿Cuál es la columna de Costo?", df.columns)
        col_cajas = st.sidebar.selectbox("¿Cuál es la columna de Cajas?", df.columns)

        if st.button("Procesar y Generar Excel"):
            temp_df = df.copy()

            # Convertir a números y limpiar nulos
            temp_df[col_cajas] = pd.to_numeric(temp_df[col_cajas], errors='coerce').fillna(0)
            temp_df[col_costo] = pd.to_numeric(temp_df[col_costo], errors='coerce').fillna(0)

            # 1. Calcular total de cajas por guía (as_index=False evita el error de antes)
            df_totales = temp_df.groupby(col_guia, as_index=False)[col_cajas].sum()
            
            # Renombrar para evitar colisión
            nombre_total_cajas = "Suma_Total_Cajas_Guia"
            df_totales = df_totales.rename(columns={col_cajas: nombre_total_cajas})

            # 2. Unir totales
            df_final = pd.merge(temp_df, df_totales, on=col_guia, how='left')
            
            # 3. Lógica de prorrateo
            df_final['COSTO_REAL_AJUSTADO'] = 0.0
            
            # Solo calcular donde el total de cajas sea mayor a 0 para no romper el programa
            mask = df_final[nombre_total_cajas] > 0
            df_final.loc[mask, 'COSTO_REAL_AJUSTADO'] = (
                df_final.loc[mask, col_costo] / df_final.loc[mask, nombre_total_cajas]
            ) * df_final.loc[mask, col_cajas]

            st.success("✅ ¡Hecho! Los costos han sido prorrateados correctamente.")

            # Función de descarga
            def to_excel(df_to_save):
                output = BytesIO()
                # Usamos engine xlsxwriter para mejor compatibilidad
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_to_save.to_excel(writer, index=False, sheet_name='Resultados')
                return output.getvalue()

            excel_data = to_excel(df_final)

            st.download_button(
                label="📥 Descargar Resultado en Excel",
                data=excel_data,
                file_name="reporte_costos_corregidos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.subheader("Vista Previa")
            st.dataframe(df_final.head(20))

    except Exception as e:
        st.error(f"Error detectado: {e}")
        st.info("Asegúrate de que los nombres de las columnas en la barra lateral coincidan con tu archivo.")


















