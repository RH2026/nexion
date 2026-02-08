import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Corrector Logístico", layout="wide")

st.title("🛠️ Reparador de Costos: Depuración de Columnas")

uploaded_file = st.file_uploader("Sube tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # 1. Intentar leer el archivo con limpieza de espacios iniciales
        if uploaded_file.name.endswith('.csv'):
            # El encoding 'utf-8-sig' elimina el BOM (caracteres invisibles)
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        # 2. LIMPIEZA EXTREMA de nombres de columnas
        # Quitamos espacios, saltos de línea y convertimos todo a MAYÚSCULAS para evitar errores
        df.columns = df.columns.astype(str).str.strip().str.replace('\n', '').str.upper()
        
        # 3. MOSTRAR DIAGNÓSTICO (Para que veas qué ve la IA)
        st.info(f"Columnas detectadas en tu archivo: {list(df.columns)}")
        
        st.subheader("Vista previa de los datos")
        st.dataframe(df.head())

        # 4. CONFIGURACIÓN EN BARRA LATERAL
        st.sidebar.header("📍 Mapeo de Columnas")
        
        # Intentamos pre-seleccionar si existen, si no, el usuario elige
        def find_col(name_list, target):
            for col in name_list:
                if target in col: return col
            return name_list[0]

        col_factura = st.sidebar.selectbox("Columna Factura", df.columns, index=df.columns.get_loc(find_col(df.columns, "FACTURA")))
        col_guia = st.sidebar.selectbox("Columna Guía", df.columns, index=df.columns.get_loc(find_col(df.columns, "GUIA")))
        col_costo = st.sidebar.selectbox("Columna Costo", df.columns, index=df.columns.get_loc(find_col(df.columns, "COSTO")))
        col_cajas = st.sidebar.selectbox("Columna Cajas", df.columns, index=df.columns.get_loc(find_col(df.columns, "CAJA")))

        if st.button("Procesar y Corregir"):
            # Trabajamos sobre una copia
            res_df = df.copy()

            # Asegurar que los datos sean numéricos
            res_df[col_cajas] = pd.to_numeric(res_df[col_cajas], errors='coerce').fillna(0)
            res_df[col_costo] = pd.to_numeric(res_df[col_costo], errors='coerce').fillna(0)

            # Lógica de agrupación (as_index=False para evitar el error anterior)
            # Agrupamos por Guía y sumamos cajas
            df_sumas = res_df.groupby(col_guia, as_index=False)[col_cajas].sum()
            df_sumas = df_sumas.rename(columns={col_cajas: 'TOTAL_CAJAS_GUIA'})

            # Unir resultados
            final_df = pd.merge(res_df, df_sumas, on=col_guia, how='left')

            # Calcular prorrateo
            # Si el total de cajas es > 0, dividimos costo/total y multiplicamos por cajas de la fila
            final_df['COSTO_REAL_PRORRATEADO'] = 0.0
            valid_mask = final_df['TOTAL_CAJAS_GUIA'] > 0
            
            final_df.loc[valid_mask, 'COSTO_REAL_PRORRATEADO'] = (
                final_df.loc[valid_mask, col_costo] / final_df.loc[valid_mask, 'TOTAL_CAJAS_GUIA']
            ) * final_df.loc[valid_mask, col_cajas]

            st.success("✅ ¡Ajuste completado!")

            # Botón de Descarga Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Resultado')
            
            st.download_button(
                label="📥 Descargar Excel Corregido",
                data=output.getvalue(),
                file_name="reparacion_facturas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.dataframe(final_df.head(15))

    except Exception as e:
        st.error(f"Error crítico: {e}")
        st.warning("Prueba lo siguiente: Abre tu Excel, asegúrate de que la primera fila sean los títulos y que no haya celdas combinadas.")



















