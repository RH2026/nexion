import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuración de página
st.set_page_config(page_title="Folio Master Pro", layout="wide")

# Inyectar Google Material Icons y CSS Pro
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
    .material-icons { vertical-align: middle; margin-right: 8px; }
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def icon(name):
    """Función para insertar iconos de Material Design"""
    return f'<span class="material-icons">{name}</span>'

st.markdown(f"<h1>{icon('dashboard')} Folio Master Pro</h1>", unsafe_allow_html=True)
st.markdown("---")

# 1. CARGA DE ARCHIVO
uploaded_file = st.file_uploader("Subir archivo Excel o CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Lectura de datos
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Detección inteligente de columnas
    col_folio = next((c for c in df.columns if 'folio' in c.lower() or 'factura' in c.lower()), df.columns[0])
    col_transp = next((c for c in df.columns if 'transp' in c.lower() or 'flete' in c.lower()), None)

    # --- MÉTRICAS Y GRÁFICOS ---
    st.markdown(f"### {icon('analytics')} Análisis Rápido de Carga")
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.metric("Total de Partidas", len(df))
    with m2:
        st.metric("Folios Únicos", df[col_folio].nunique())
    with m3:
        if col_transp:
            st.metric("Transportistas Detectados", df[col_transp].nunique())

    if col_transp:
        # Gráfico Pro de partidas por transporte
        conteo_transp = df[col_transp].value_counts().reset_index()
        conteo_transp.columns = ['Transporte', 'Partidas']
        fig = px.bar(conteo_transp, x='Transporte', y='Partidas', 
                     title="Distribución de Partidas por Transporte",
                     template="plotly_dark", color='Partidas')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- PANEL DE CONTROL ---
    col_filtros, col_depuracion = st.columns([1, 2])

    with col_filtros:
        st.markdown(f"#### {icon('filter_alt')} Rango Numérico")
        inicio = st.number_input("Desde el folio:", value=int(df[col_folio].min()))
        final = st.number_input("Hasta el folio:", value=int(df[col_folio].max()))
        
        df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)]

    with col_depuracion:
        st.markdown(f"#### {icon('checklist')} Selección Individual de Folios")
        
        # Preparar data para el editor
        if col_transp:
            info_folios = df_rango.drop_duplicates(subset=[col_folio])[[col_folio, col_transp]]
        else:
            info_folios = pd.DataFrame({col_folio: sorted(df_rango[col_folio].unique())})
            info_folios['Info'] = "N/A"

        selector_df = info_folios.copy()
        selector_df.insert(0, "Seleccionar", True)

        # Editor estilo Excel con scroll
        edited_df = st.data_editor(
            selector_df,
            column_config={
                "Seleccionar": st.column_config.CheckboxColumn(icon="check_box"),
                col_folio: st.column_config.TextColumn("Folio de Documento", disabled=True),
                col_transp if col_transp else 'Info': st.column_config.TextColumn("Referencia/Transporte", disabled=True)
            },
            hide_index=True,
            height=300,
            use_container_width=True
        )

    # --- RENDER Y DESCARGA ---
    folios_finales = edited_df[edited_df["Seleccionar"] == True][col_folio].tolist()
    
    st.markdown("---")
    c_btn1, c_btn2 = st.columns(2)

    with c_btn1:
        if st.button(f"👁️ Visualizar Tabla Seleccionada"):
            df_final = df_rango[df_rango[col_folio].isin(folios_finales)]
            st.markdown(f"#### {icon('table_view')} Vista Previa")
            st.dataframe(df_final, use_container_width=True)
            
            # Botón de descarga después de renderizar
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.download_button(
                label=f"📥 DESCARGAR {len(df_final)} PARTIDAS (.XLSX)",
                data=output.getvalue(),
                file_name="reporte_folios_pro.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    # Estado vacío con icono de Material
    st.markdown(
        f"<div style='text-align:center; padding:50px;'>"
        f"<h2 style='color:#555;'>{icon('upload_file')} Por favor, cargue un archivo para comenzar</h2>"
        f"</div>", 
        unsafe_allow_html=True
    )














































