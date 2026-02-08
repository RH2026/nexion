import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Corrector Logístico", layout="wide")

st.title("🛠️ Reparador de Costos: Exportación a Excel")
st.markdown("Sube tu archivo y descarga el resultado corregido en formato **.xlsx**.")

uploaded_file = st.file_uploader("Elige tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
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
            # COPIA de seguridad para no alterar el original durante el proceso
            temp_df = df.copy()

            # Aseguramos que cajas y costo sean numéricos (por si vienen como texto)
            temp_df[col_cajas] = pd.to_numeric(temp_df[col_cajas], errors='coerce').fillna(0)
            temp_df[col_costo] = pd.to_numeric(temp_df[col_costo], errors='coerce').fillna(0)

            # 1. Calculamos el total de cajas por guía de forma segura
            # Usamos as_index=False para evitar el error de reset_index()
            df_totales = temp_df.groupby(col_guia, as_index=False)[col_cajas].sum()
            
            # Renombramos la columna suma para que no choque con la original
            nombre_total_cajas = "TOTAL_CAJAS_DE_ESTA_GUIA"
            df_totales = df_totales.rename(columns={col_cajas: nombre_total_cajas})

            # 2. Unimos los totales al dataframe original
            df_final = pd.merge(temp_df, df_totales, on=col_guia, how='left')
            
            # 3. Cálculo del costo real prorrateado
            # Evitamos división por cero con .where de numpy o una simple máscara
            df_final['COSTO_REAL_AJUSTADO'] = 0.0
            mask = df_final[nombre_total_cajas] > 0
            
            df_final.loc[mask, 'COSTO_REAL_AJUSTADO'] = (
                df_final.loc[mask, col_costo] / df_final.loc[mask, nombre_total_cajas]
            ) * df_final.loc[mask, col_cajas]

            st.success("✅ Cálculos finalizados correctamente.")

            # --- FUNCIÓN PARA CONVERTIR A EXCEL ---
            def to_excel(df_to_save):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_to_save.to_excel(writer, index=False, sheet_name='Costos Corregidos')
                return output.getvalue()

            excel_data = to_excel(df_final)

            st.download_button(
                label="📥 Descargar Reporte en Excel (.xlsx)",
                data=excel_data,
                file_name="costos_reparados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.subheader("Vista Previa del Resultado")
            st.dataframe(df_final[[col_factura, col_guia, col_cajas, col_costo, 'COSTO_REAL_AJUSTADO']])

    except Exception as e:
        st.error(f"Se produjo un error al procesar el archivo: {e}")


















