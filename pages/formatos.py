import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de página con estilo
st.set_page_config(page_title="Folio Master Pro", layout="wide", page_icon="📊")

# CSS personalizado para mejorar el diseño
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
        border: 1px solid #4x4x4x;
    }
    .stButton>button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Folio Master Pro")
st.subheader("Gestión y Depuración Inteligente de Partidas")

# 1. ÁREA DE CARGA
with st.container():
    uploaded_file = st.file_uploader("📂 Arrastra tu archivo Excel o CSV aquí", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Cargar datos
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Identificación de columnas (ajusta los nombres si son diferentes en tu archivo)
    # Buscamos columnas que se parezcan a 'Folio' y 'Transporte'
    col_folio = next((c for c in df.columns if 'folio' in c.lower() or 'factura' in c.lower()), df.columns[0])
    col_transporte = next((c for c in df.columns if 'transp' in c.lower() or 'flete' in c.lower()), None)
    
    st.success(f"✅ Archivo cargado. Folios detectados en columna: **{col_folio}**")

    # --- PANEL DE CONTROL ---
    st.divider()
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### 🛠️ Filtros de Rango")
        inicio = st.number_input("Folio Inicial", value=int(df[col_folio].min()))
        final = st.number_input("Folio Final", value=int(df[col_folio].max()))
        
        # Filtrar por rango inicial
        df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)]

    with col_right:
        st.markdown("### 🔍 Depuración Específica")
        st.caption("Selecciona/Deselecciona los folios que se incluirán en el reporte final.")
        
        # Crear lista para el selector estilo Excel
        folios_unicos = sorted(df_rango[col_folio].unique())
        
        # Buscamos el transporte para mostrarlo en la tabla de selección como referencia
        if col_transporte:
            info_folios = df_rango.drop_duplicates(subset=[col_folio])[[col_folio, col_transporte]]
        else:
            info_folios = pd.DataFrame({col_folio: folios_unicos})
            info_folios['Info'] = "Sin columna transporte"

        selector_df = info_folios.copy()
        selector_df.insert(0, "Incluir", True)

        # Editor de tabla Pro con Scroll
        edited_df = st.data_editor(
            selector_df,
            column_config={
                "Incluir": st.column_config.CheckboxColumn("Selección", default=True),
                col_folio: st.column_config.TextColumn("Folio", disabled=True),
                col_transporte: st.column_config.TextColumn("Transporte/Referencia", disabled=True)
            },
            hide_index=True,
            height=350,
            use_container_width=True
        )

    # --- ACCIONES ---
    st.divider()
    folios_finales = edited_df[edited_df["Incluir"] == True][col_folio].tolist()
    
    c1, c2, c3 = st.columns([1,1,1])
    
    with c1:
        render_btn = st.button("👁️ RENDERIZAR TABLA")
    
    if render_btn:
        df_final = df_rango[df_rango[col_folio].isin(folios_finales)]
        
        if not df_final.empty:
            st.markdown("### 📋 Vista Previa del Documento")
            st.dataframe(df_final, use_container_width=True, height=400)
            
            # Preparar descarga en la columna central
            with c2:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)
                
                st.download_button(
                    label="💾 DESCARGAR EXCEL (.XLSX)",
                    data=output.getvalue(),
                    file_name=f"Reporte_Folios_{inicio}_{final}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error("No hay folios seleccionados para mostrar.")

else:
    # Estado inicial amigable
    st.info("👋 ¡Bienvenido! Sube un archivo de Excel para empezar a trabajar.")
    st.image("https://img.icons8.com/clouds/200/000000/google-sheets.png", width=150)













































