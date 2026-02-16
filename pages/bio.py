import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración inicial
st.set_page_config(page_title="Corrector Logístico Pro", layout="wide")

st.title("Reparador de Costos Logísticos")

# --- EXPANDER DE INSTRUCCIONES ---
with st.expander("¿Dudas para usar este módulo? Lea las instrucciones aquí", icon=":material/help:"):
    st.markdown("""
    ### Pasos para reparar tu archivo
    1. **Subida de datos:** Haz clic en el cargador o arrastra tu archivo Excel/CSV. 
    2. **Configuración de columnas:** Verifica que los selectores coincidan con las columnas de tu archivo.
    3. **Procesamiento:** El sistema detectará automáticamente si los costos por guía están duplicados.
    
    ### ¿Cómo funciona la reparación?
    * **Si el costo es idéntico:** Si una guía tiene varias facturas con el mismo costo, el sistema **prorratea** el costo según las cajas.
    * **Si los costos son diferentes:** Si una guía tiene montos distintos, el sistema **no los toca** (asume cargos independientes).
    
    4. **Descarga:** Genera un archivo `.xlsx` listo para reportes.
    """)

st.markdown("""
Esta herramienta detecta costos duplicados por guía y los prorratea proporcionalmente según el número de cajas. 
""")

# 1. Subida de archivo
uploaded_file = st.file_uploader("1. Sube tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Cargar archivo
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.subheader("2. Configuración de Columnas", divider="gray")
    st.info("Confirma que las columnas seleccionadas sean las correctas:", icon=":material/settings_suggest:")

    # Selectores en el cuerpo principal
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        col_factura = st.selectbox(
            "Columna Factura", 
            df.columns, 
            index=df.columns.get_loc("DocNum") if "DocNum" in df.columns else 0,
            help="Selecciona la columna de identificador de factura"
        )
    with c2:
        col_guia = st.selectbox(
            "Columna Guía", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_NGUIA") if "U_BXP_NGUIA" in df.columns else 0,
            help="Selecciona la columna de número de guía"
        )
    with c3:
        col_costo = st.selectbox(
            "Columna Costo", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_COSTO_GUIA") if "U_BXP_COSTO_GUIA" in df.columns else 0,
            help="Selecciona la columna del costo repetido"
        )
    with c4:
        col_cajas = st.selectbox(
            "Columna Cajas", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_CAJAS_ENV") if "U_BXP_CAJAS_ENV" in df.columns else 0,
            help="Selecciona la columna de cantidad de cajas"
        )

    st.divider()

    # Botón de proceso con icono
    if st.button("Procesar y Reparar Datos", use_container_width=True, type="primary", icon=":material/database_gear:"):
        try:
            # --- LÓGICA DE REPARACIÓN AVANZADA ---
            stats_guia = df.groupby(col_guia).agg({
                col_costo: 'nunique', 
                col_cajas: 'sum'
            }).reset_index()
            
            stats_guia.columns = [col_guia, 'costos_unicos', 'TOTAL_CAJAS_GUIA']

            df_final = pd.merge(df, stats_guia, on=col_guia)

            def aplicar_reparacion(row):
                if row['costos_unicos'] == 1:
                    return (row[col_costo] / row['TOTAL_CAJAS_GUIA']) * row[col_cajas]
                else:
                    return row[col_costo]

            df_final['COSTO_REAL_AJUSTADO'] = df_final.apply(aplicar_reparacion, axis=1)

            st.success("Proceso completado con éxito.", icon=":material/check_circle:")

            # --- GENERACIÓN DE EXCEL ---
            def to_excel(df_to_save):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_to_save.to_excel(writer, index=False, sheet_name='Costos Reparados')
                return output.getvalue()

            excel_data = to_excel(df_final)

            st.download_button(
                label="Descargar Reporte Corregido (.xlsx)",
                data=excel_data,
                file_name="reporte_logistico_reparado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                icon=":material/download_for_offline:",
                use_container_width=True
            )
            
            # --- VISTA PREVIA ---
            st.subheader("Vista Previa del Análisis", divider="blue")
            columnas_vista = [col_factura, col_guia, col_cajas, col_costo, 'TOTAL_CAJAS_GUIA', 'COSTO_REAL_AJUSTADO']
            st.dataframe(df_final[columnas_vista].head(20), use_container_width=True)

        except Exception as e:
            st.error(f"Error al procesar: {e}", icon=":material/error:")

else:
    st.info("Esperando archivo... Sube un Excel o CSV para comenzar.", icon=":material/upload_file:")
