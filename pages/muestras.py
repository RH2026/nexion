import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Corrector Logístico", layout="wide")

st.title("🛠️ Reparador de Costos: Exportación a Excel")
st.markdown("Sube tu archivo y descarga el resultado corregido en formato **.xlsx**.")

uploaded_file = st.file_uploader("Elige tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Cargar archivo dependiendo de la extensión
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.subheader("Datos Originales")
    st.dataframe(df.head())

    # Configuración de columnas
    st.sidebar.header("Configurar Columnas")
    col_factura = st.sidebar.selectbox("Factura", df.columns)
    col_guia = st.sidebar.selectbox("Guía", df.columns)
    col_costo = st.sidebar.selectbox("Costo Repetido", df.columns)
    col_cajas = st.sidebar.selectbox("Cajas", df.columns)

    if st.button("Procesar y Generar Excel"):
        # Lógica de cálculo
        df_totales = df.groupby(col_guia)[col_cajas].sum().reset_index()
        df_totales.columns = [col_guia, 'TOTAL_CAJAS_GUIA']

        df_final = pd.merge(df, df_totales, on=col_guia)
        
        # Cálculo del costo real prorrateado
        df_final['COSTO_REAL_AJUSTADO'] = (df_final[col_costo] / df_final['TOTAL_CAJAS_GUIA']) * df_final[col_cajas]

        st.success("✅ Cálculos finalizados.")

        # --- FUNCIÓN PARA CONVERTIR A EXCEL ---
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Costos Corregidos')
            processed_data = output.getvalue()
            return processed_data

        excel_data = to_excel(df_final)

        st.download_button(
            label="📥 Descargar Reporte en Excel (.xlsx)",
            data=excel_data,
            file_name="costos_logisticos_reparados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("Vista Previa del Resultado")
        st.write(df_final[[col_factura, col_guia, col_cajas, col_costo, 'COSTO_REAL_AJUSTADO']])

















