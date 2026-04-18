import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Nexion Render", layout="wide")

# Estilos CSS personalizados para el look Dark Mode / Neon
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background-color: #121417;
    }
    
    /* Estilo de la Tarjeta (Card) */
    .render-card {
        background-color: #1e2227;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 5px solid #00f2ff; /* Acento Neón */
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    
    .card-header {
        color: #00f2ff;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    
    .card-value {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .grid-container {
        display: grid;
        grid-template-columns: 1fr 2fr 1fr 1fr;
        gap: 20px;
    }
    
    .obs-section {
        background-color: #262c33;
        padding: 10px;
        border-radius: 8px;
        border: 1px dashed #444;
        font-size: 0.9rem;
    }

    /* Ocultar elementos en la impresión */
    @media print {
        .no-print, .stFileUploader, .stButton {
            display: none !important;
        }
        .render-card {
            border: 1px solid #000;
            page-break-inside: avoid;
            color: black !important;
            background-color: white !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Nexion Logistics Renderer")

# Subir archivo
uploaded_file = st.file_uploader("Sube tu archivo de Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Aseguramos que existan las columnas extras si no vienen en el Excel
    if 'OBSERVACIONES DE ALMACEN' not in df.columns:
        df['OBSERVACIONES DE ALMACEN'] = ""
    if 'OBSERVACIONES DE EMBARQUES' not in df.columns:
        df['OBSERVACIONES DE EMBARQUES'] = ""

    # Botón de impresión (usa comando JS de navegador)
    st.button("🖨️ Imprimir Reporte", on_click=lambda: st.write('<script>window.print();</script>', unsafe_allow_html=True))

    st.write(f"Mostrando {len(df)} registros")

    # Renderizado de Tarjetas
    for index, row in df.iterrows():
        # Construcción del HTML para cada registro
        card_html = f"""
        <div class="render-card">
            <div class="grid-container">
                <div>
                    <div class="card-header">PEDIDO / FACTURA</div>
                    <div class="card-value" style="color: #00f2ff;">{row.get('Factura', 'N/A')}</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">RECOMENDACIÓN: {row.get('RECOMENDACION', '')}</div>
                </div>
                
                <div>
                    <div class="card-header">CLIENTE / DESTINO</div>
                    <div class="card-value" style="font-size: 1.1rem;">{row.get('Nombre_Extran', 'N/A')}</div>
                    <div style="font-style: italic; font-size: 0.85rem; opacity: 0.8;">{row.get('DESTINO', 'N/A')}</div>
                </div>

                <div class="obs-section">
                    <div class="card-header" style="color: #a2ff00;">OBS. ALMACÉN</div>
                    <div>{row['OBSERVACIONES DE ALMACEN']}</div>
                </div>

                <div class="obs-section">
                    <div class="card-header" style="color: #ffaa00;">OBS. EMBARQUES</div>
                    <div>{row['OBSERVACIONES DE EMBARQUES']}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

else:
    st.info("Por favor, sube un archivo Excel para procesar los datos.")







































