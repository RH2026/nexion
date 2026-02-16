import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración inicial
st.set_page_config(page_title="Corrector Logístico Pro", layout="wide")

st.title("🛠️ Reparador de Costos Logísticos")
with st.expander("¿Dudas para usar este módulo? Lea las instrucciones aquí"):
    st.markdown("""
    ### 📋 Pasos para reparar tu archivo
    
    1. **Subida de datos:** Haz clic en 'Browse files' o arrastra tu archivo Excel/CSV. El sistema cargará una vista previa automática.
    2. **Configuración de columnas:** Verifica que los selectores coincidan con las columnas de tu archivo:
        * **Factura:** Identificador del documento.
        * **Guía:** Número de guía de transporte.
        * **Costo:** El monto que sospechas está duplicado.
        * **Cajas:** Cantidad de bultos por factura.
    3. **Procesamiento:** Haz clic en el botón **🚀 Procesar y Reparar Datos**.
    
    ### 🧠 ¿Cómo funciona la reparación?
    El sistema aplica un filtro de seguridad para no dañar tus datos:
    * **Si el costo es idéntico:** Si una guía tiene varias facturas y todas marcan el mismo costo (ej. $100), el sistema entiende que es un error de duplicidad y **prorratea** el costo según las cajas de cada factura.
    * **Si los costos son diferentes:** Si una guía tiene montos distintos en sus filas, el sistema **no los toca**, asumiendo que son cargos independientes (ej. flete + maniobra).
    
    4. **Descarga:** Una vez finalizado, aparecerá un botón verde para descargar tu nuevo archivo corregido.
    """)

uploaded_file = st.file_uploader("1. Sube tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Cargar archivo
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.subheader("2. Configuración de Columnas")
    st.info("Confirma que las columnas seleccionadas sean las correctas:")

    # Selectores en el cuerpo principal (alineados en columnas)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        col_factura = st.selectbox(
            "Columna Factura", 
            df.columns, 
            index=df.columns.get_loc("DocNum") if "DocNum" in df.columns else 0
        )
    with c2:
        col_guia = st.selectbox(
            "Columna Guía", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_NGUIA") if "U_BXP_NGUIA" in df.columns else 0
        )
    with c3:
        col_costo = st.selectbox(
            "Columna Costo", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_COSTO_GUIA") if "U_BXP_COSTO_GUIA" in df.columns else 0
        )
    with c4:
        col_cajas = st.selectbox(
            "Columna Cajas", 
            df.columns, 
            index=df.columns.get_loc("U_BXP_CAJAS_ENV") if "U_BXP_CAJAS_ENV" in df.columns else 0
        )

    st.divider()

    if st.button("🚀 Procesar y Reparar Datos", use_container_width=True, type="primary"):
        try:
            # --- LÓGICA DE REPARACIÓN AVANZADA ---
            
            # 1. Agrupamos para obtener estadísticas por guía:
            # - nunique en costo: para saber si el costo es siempre el mismo.
            # - sum en cajas: para saber el total de la guía.
            stats_guia = df.groupby(col_guia).agg({
                col_costo: 'nunique', 
                col_cajas: 'sum'
            }).reset_index()
            
            stats_guia.columns = [col_guia, 'costos_unicos', 'TOTAL_CAJAS_GUIA']

            # 2. Unimos las estadísticas con el dataframe original
            df_final = pd.merge(df, stats_guia, on=col_guia)

            # 3. Función de aplicación de la regla de negocio:
            # "Si el costo es idéntico en todas las filas de la guía, prorrateamos. 
            # Si hay costos distintos, los dejamos como están."
            def aplicar_reparacion(row):
                if row['costos_unicos'] == 1:
                    # Cálculo: (Costo Repetido / Total Cajas Guía) * Cajas de esta Factura
                    return (row[col_costo] / row['TOTAL_CAJAS_GUIA']) * row[col_cajas]
                else:
                    # Se mantiene el original porque no parece ser un error de duplicidad
                    return row[col_costo]

            df_final['COSTO_REAL_AJUSTADO'] = df_final.apply(aplicar_reparacion, axis=1)

            st.success("✅ Proceso completado. Se han analizado las duplicidades con éxito.")

            # --- GENERACIÓN DE EXCEL ---
            def to_excel(df_to_save):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_to_save.to_excel(writer, index=False, sheet_name='Costos Reparados')
                return output.getvalue()

            excel_data = to_excel(df_final)

            st.download_button(
                label="📥 Descargar Reporte Corregido (.xlsx)",
                data=excel_data,
                file_name="reporte_logistico_reparado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # --- VISTA PREVIA ---
            st.subheader("Vista Previa del Análisis")
            # Seleccionamos columnas clave para mostrar al usuario
            columnas_vista = [col_factura, col_guia, col_cajas, col_costo, 'TOTAL_CAJAS_GUIA', 'COSTO_REAL_AJUSTADO']
            st.dataframe(df_final[columnas_vista].head(20), use_container_width=True)

        except Exception as e:
            st.error(f"Error al procesar: {e}")
            st.info("Asegúrate de que las columnas de Costo y Cajas contengan solo números.")

else:
    st.info("Sube un archivo de Excel o CSV para comenzar.")
