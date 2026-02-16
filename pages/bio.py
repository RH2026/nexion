import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Corrector Logístico", layout="wide")

st.title("🛠️ Reparador de Costos: Exportación a Excel")
st.markdown("Sube tu archivo y personaliza las columnas directamente aquí debajo.")

uploaded_file = st.file_uploader("1. Elige tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Cargar archivo
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.subheader("2. Configurar Columnas")
    st.info("Selecciona las columnas correspondientes de tu archivo para realizar el cálculo.")

    # Creamos 4 columnas en el cuerpo de la app para que los selectores queden alineados
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        col_factura = st.selectbox(
            "Factura (DocNum)", 
            df.columns, 
            index=df.columns.get_loc("DocNum") if "DocNum" in df.columns else 0
        )
    with c2:
        col_guia = st.selectbox(
            "Guía (U_BXP_NGUIA)", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_NGUIA") if "U_BXP_NGUIA" in df.columns else 0
        )
    with c3:
        col_costo = st.selectbox(
            "Costo Repetido", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_COSTO_GUIA") if "U_BXP_COSTO_GUIA" in df.columns else 0
        )
    with c4:
        col_cajas = st.selectbox(
            "Cajas", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_CAJAS_ENV") if "U_BXP_CAJAS_ENV" in df.columns else 0
        )

    st.divider() # Línea divisoria visual

    if st.button("🚀 Procesar y Generar Excel", use_container_width=True):
        try:
            # --- Lógica de cálculo corregida ---
            # Agrupamos usando as_index=False para evitar el ValueError original
            df_totales = df.groupby(col_guia, as_index=False)[col_cajas].sum()
            df_totales.columns = [col_guia, 'TOTAL_CAJAS_POR_GUIA']

            # Unir datos
            df_final = pd.merge(df, df_totales, on=col_guia)
            
            # Cálculo del costo prorrateado
            df_final['COSTO_REAL_AJUSTADO'] = (df_final[col_costo] / df_final['TOTAL_CAJAS_POR_GUIA']) * df_final[col_cajas]

            st.success("✅ Cálculos finalizados con éxito.")

            # --- Preparación del Excel ---
            def to_excel(df_to_save):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_to_save.to_excel(writer, index=False, sheet_name='Reporte Corregido')
                return output.getvalue()

            excel_data = to_excel(df_final)

            st.download_button(
                label="📥 Descargar Reporte en Excel (.xlsx)",
                data=excel_data,
                file_name="costos_reparados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary" # Lo hace resaltar en color
            )
            
            # Vista previa del resultado final
            st.subheader("Vista Previa del Resultado")
            cols_mostrar = [col_factura, col_guia, col_cajas, col_costo, 'TOTAL_CAJAS_POR_GUIA', 'COSTO_REAL_AJUSTADO']
            st.dataframe(df_final[cols_mostrar].head(15), use_container_width=True)

        except Exception as e:
            st.error(f"Ups, algo salió mal: {e}")
            st.warning("Asegúrate de que las columnas seleccionadas contengan números para poder sumar y dividir.")

else:
    st.write("Esperando a que subas un archivo... 🕒")
