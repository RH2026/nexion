import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Depurador de Folios", layout="wide")

st.title("📂 Procesador de Folios Automático")
st.markdown("""
Esta herramienta filtra y limpia tus archivos de Excel/CSV de forma sencilla. 
1. Sube el archivo. 2. Selecciona el rango de folios. 3. Descarga el resultado.
""")

# 1. BOTÓN PARA SUBIR ARCHIVO
uploaded_file = st.file_uploader("Subir archivo Excel o CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Leer el archivo según su extensión
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Identificar la columna de folio (asumimos que se llama 'FOLIO' o es la primera)
    col_folio = df.columns[0] 
    st.info(f"Columna detectada como folio: **{col_folio}**")

    st.divider()

    # 2. SELECCIÓN DE RANGO (FOLIO INICIO Y FINAL)
    st.subheader("2. Selecciona el rango de folios a trabajar")
    
    # Obtenemos los folios únicos y ordenados para el filtro
    folios_unicos = sorted(df[col_folio].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        folio_inicio = st.number_input("Folio inicio", value=int(min(folios_unicos)))
    with col2:
        folio_final = st.number_input("Folio final", value=int(max(folios_unicos)))

    # Filtrar el dataframe por el rango seleccionado
    df_filtrado = df[(df[col_folio] >= folio_inicio) & (df[col_folio] <= folio_final)]

    # 3. RENDERIZAR FOLIOS Y OPCIÓN DE ELIMINAR
    st.subheader("3. Revisión de folios seleccionados")
    
    # Creamos la lista depurada (una fila por folio) para que el usuario vea qué hay
    folios_en_rango = sorted(df_filtrado[col_folio].unique())
    
    # Multiselect para que el usuario pueda "borrar" o quitar folios específicos del rango
    folios_a_mantener = st.multiselect(
        "Folios detectados en este rango (quita los que no quieras trabajar):",
        options=folios_en_rango,
        default=folios_en_rango
    )

    # Aplicar el filtro final basado en la selección manual
    df_final = df_filtrado[df_filtrado[col_folio].isin(folios_a_mantener)]

    if st.button("APLICAR CAMBIOS Y RENDERIZAR TABLA"):
        st.write(f"### Tabla Resultante ({len(df_final)} partidas)")
        st.dataframe(df_final, use_container_width=True)

        # 4. BOTÓN DE DESCARGA
        # Convertir dataframe a Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Folios_Filtrados')
        
        processed_data = output.getvalue()

        st.download_button(
            label="📥 DESCARGAR EN .XLSX",
            data=processed_data,
            file_name="folios_procesados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.warning("Por favor, sube un archivo para comenzar.")











































