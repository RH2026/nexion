import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Depurador Pro", layout="wide")

st.title("📂 Procesador de Folios Estilo Excel")

# 1. CARGA DE ARCHIVO
uploaded_file = st.file_uploader("Subir archivo Excel o CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Cargar datos
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Intentamos detectar la columna de folio
    col_folio = df.columns[0]
    st.info(f"Columna de folio detectada: **{col_folio}**")

    # --- SECCIÓN DE FILTRO DE RANGO ---
    st.subheader("1. Definir Rango de Folios")
    c1, c2 = st.columns(2)
    with c1:
        inicio = st.number_input("Folio inicio", value=int(df[col_folio].min()))
    with c2:
        final = st.number_input("Folio final", value=int(df[col_folio].max()))

    # Filtrar por rango numérico primero
    df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)]
    
    st.divider()

    # --- SECCIÓN DE DEPURACIÓN ESTILO EXCEL ---
    st.subheader("2. Seleccionar folios específicos (Estilo Filtro Excel)")
    
    # Creamos un dataframe de folios únicos para el selector
    folios_unicos = sorted(df_rango[col_folio].unique())
    selector_df = pd.DataFrame({
        "Incluir": [True] * len(folios_unicos),
        "Folio": folios_unicos
    })

    st.write("Desmarca los folios que NO quieres incluir en el reporte final:")
    
    # El data_editor crea la lista con scroll y checkboxes
    # Altura de 300px es ideal para ver unos 10 folios a la vez con scroll
    edited_df = st.data_editor(
        selector_df,
        column_config={
            "Incluir": st.column_config.CheckboxColumn(help="Selecciona para mantener"),
            "Folio": st.column_config.TextColumn(disabled=True)
        },
        disabled=["Folio"],
        hide_index=True,
        height=300 
    )

    # Obtener la lista de folios que quedaron marcados como True
    folios_finales = edited_df[edited_df["Incluir"] == True]["Folio"].tolist()

    st.divider()

    # --- RENDERIZAR Y DESCARGAR ---
    if st.button("APLICAR CAMBIOS Y RENDERIZAR TABLA"):
        df_resultado = df_rango[df_rango[col_folio].isin(folios_finales)]
        
        if not df_resultado.empty:
            st.success(f"Se han filtrado {len(df_resultado)} partidas.")
            st.dataframe(df_resultado, use_container_width=True)

            # Preparar descarga
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_resultado.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 DESCARGAR RESULTADO (.XLSX)",
                data=output.getvalue(),
                file_name="folios_filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No hay datos para mostrar con los filtros seleccionados.")

else:
    st.info("Esperando archivo... Por favor sube tu Excel o CSV para comenzar.")












































