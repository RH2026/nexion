import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuración de página
st.set_page_config(page_title="Folio Master Pro", layout="wide")

# CSS personalizado para estilo oscuro y botones limpios
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #262730;
        color: white;
        border: 1px solid #444;
    }
    .stButton>button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Folio Master Pro")
st.subheader("Gestión y Depuración de Partidas")

# 1. ÁREA DE CARGA
uploaded_file = st.file_uploader("Subir archivo Excel o CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Cargar datos
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Identificación automática de columnas
    col_folio = next((c for c in df.columns if 'folio' in c.lower() or 'factura' in c.lower()), df.columns[0])
    col_transporte = next((c for c in df.columns if 'transp' in c.lower() or 'flete' in c.lower()), None)
    
    st.success(f"Archivo cargado. Columna de folio: {col_folio}")

    # --- ANÁLISIS VISUAL (GRÁFICO) ---
    if col_transporte:
        st.markdown("---")
        conteo_transp = df[col_transporte].value_counts().reset_index()
        conteo_transp.columns = ['Transporte', 'Partidas']
        fig = px.bar(conteo_transp, x='Transporte', y='Partidas', 
                     title="Partidas por Transporte",
                     template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    # --- PANEL DE CONTROL ---
    st.divider()
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### Filtros de Rango")
        inicio = st.number_input("Folio Inicial", value=int(df[col_folio].min()))
        final = st.number_input("Folio Final", value=int(df[col_folio].max()))
        
        # Filtrar por rango numérico
        df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)]

    with col_right:
        st.markdown("### Depuración Específica")
        st.caption("Desmarca los folios que no deseas incluir.")
        
        # Preparar datos para el selector
        if col_transporte:
            info_folios = df_rango.drop_duplicates(subset=[col_folio])[[col_folio, col_transporte]]
        else:
            info_folios = pd.DataFrame({col_folio: sorted(df_rango[col_folio].unique())})
            info_folios['Info'] = "N/A"

        selector_df = info_folios.copy()
        selector_df.insert(0, "Incluir", True)

        # Editor de tabla con Scroll (Estilo Excel)
        edited_df = st.data_editor(
            selector_df,
            column_config={
                "Incluir": st.column_config.CheckboxColumn("Selección", default=True),
                col_folio: st.column_config.TextColumn("Folio", disabled=True),
                col_transporte if col_transporte else 'Info': st.column_config.TextColumn("Referencia", disabled=True)
            },
            hide_index=True,
            height=350,
            use_container_width=True
        )

    # --- ACCIONES ---
    st.divider()
    folios_finales = edited_df[edited_df["Incluir"] == True][col_folio].tolist()
    
    c1, c2 = st.columns(2)
    
    with c1:
        render_btn = st.button("RENDERIZAR TABLA")
    
    if render_btn:
        df_final = df_rango[df_rango[col_folio].isin(folios_finales)]
        
        if not df_final.empty:
            st.markdown("### Vista Previa")
            st.dataframe(df_final, use_container_width=True)
            
            # Preparar descarga
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            with c2:
                st.download_button(
                    label="DESCARGAR EXCEL (.XLSX)",
                    data=output.getvalue(),
                    file_name="reporte_folios.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error("No hay folios seleccionados.")
else:
    st.info("Sube un archivo de Excel o CSV para comenzar.")















































