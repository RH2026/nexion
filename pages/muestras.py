import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Corrector Logístico", layout="wide")

st.title("🛠️ Reparador de Costos")

uploaded_file = st.file_uploader("Sube tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # 1. Leer archivo
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        st.info(f"Columnas detectadas: {list(df.columns)}")

        # 2. Selección de columnas
        col_factura = st.selectbox("Columna Factura", df.columns)
        col_guia = st.selectbox("Columna Guía", df.columns)
        col_costo = st.selectbox("Columna Costo", df.columns)
        col_cajas = st.selectbox("Columna Cajas", df.columns)

        if st.button("Procesar Datos"):
            res_df = df.copy()

            # Asegurar números
            res_df[col_cajas] = pd.to_numeric(res_df[col_cajas], errors='coerce').fillna(0)
            res_df[col_costo] = pd.to_numeric(res_df[col_costo], errors='coerce').fillna(0)

            # Lógica de prorrateo
            df_sumas = res_df.groupby(col_guia, as_index=False)[col_cajas].sum()
            df_sumas = df_sumas.rename(columns={col_cajas: 'TOTAL_CAJAS_GUIA'})

            final_df = pd.merge(res_df, df_sumas, on=col_guia, how='left')

            final_df['COSTO_REAL_PRORRATEADO'] = 0.0
            mask = final_df['TOTAL_CAJAS_GUIA'] > 0
            final_df.loc[mask, 'COSTO_REAL_PRORRATEADO'] = (
                final_df.loc[mask, col_costo] / final_df.loc[mask, 'TOTAL_CAJAS_GUIA']
            ) * final_df.loc[mask, col_cajas]

            st.success("✅ ¡Cálculo realizado!")
            st.dataframe(final_df.head(10))

            # --- OPCIÓN DESCARGA EXCEL (engine openpyxl) ---
            try:
                output = BytesIO()
                # Cambiamos xlsxwriter por openpyxl que es más común
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    final_df.to_excel(writer, index=False, sheet_name='Resultado')
                
                st.download_button(
                    label="📥 Descargar Excel (.xlsx)",
                    data=output.getvalue(),
                    file_name="reparacion_costos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception:
                st.warning("No pude generar el .xlsx, pero aquí tienes el CSV que Excel abre igual:")
                csv_data = final_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Descargar CSV para Excel",
                    data=csv_data,
                    file_name="reparacion_costos.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"Error: {e}")




















