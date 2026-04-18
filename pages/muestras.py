import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# Configuración de la página
st.set_page_config(page_title="Nexion Logistics OS", layout="wide")

# CSS Avanzado: Separamos el diseño de Pantalla del diseño de Impresión
st.markdown("""
    <style>
    /* --- DISEÑO PARA PANTALLA (MODO DARK/NEON) --- */
    .stApp { background-color: #121417; }
    .render-card {
        background-color: #1e2227;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 5px solid #00f2ff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    .card-header { color: #00f2ff; font-size: 0.8rem; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .card-value { font-size: 1.3rem; font-weight: bold; margin-bottom: 10px; }
    .grid-container { display: grid; grid-template-columns: 1fr 2fr 1fr 1fr; gap: 20px; }
    .obs-section { background-color: #262c33; padding: 10px; border-radius: 8px; border: 1px dashed #444; font-size: 0.9rem; }

    /* --- DISEÑO PARA IMPRESIÓN (CHECKLIST TÉCNICO) --- */
    @media print {
        /* Ocultar todo lo innecesario de la web */
        header, footer, .stFileUploader, button, [data-testid="stSidebar"], .stMarkdown div:empty { 
            display: none !important; 
        }
        
        /* Forzar fondo blanco y texto negro para el papel */
        body, .stApp { background-color: white !important; color: black !important; }
        
        /* Transformar las tarjetas en filas de una tabla técnica */
        .render-card {
            display: block !important;
            border: 1px solid #000 !important;
            border-left: 10px solid #000 !important;
            margin: 0 !important;
            padding: 10px !important;
            border-radius: 0 !important;
            page-break-inside: avoid;
            background-color: white !important;
            box-shadow: none !important;
        }

        .grid-container {
            display: flex !important;
            justify-content: space-between;
            gap: 10px;
        }

        .card-header { color: #333 !important; font-size: 7pt !important; border-bottom: 0.5px solid #ccc; }
        .card-value { color: black !important; font-size: 11pt !important; margin-bottom: 2px; }
        .obs-section { 
            border: 1px solid #000 !important; 
            min-width: 150px; 
            height: 50px; /* Espacio para que firmen o anoten */
            background-color: transparent !important;
        }
        
        /* Agregar un cuadrito de Checkbox solo para la impresión */
        .render-card::before {
            content: " [  ] ";
            float: left;
            font-size: 20pt;
            margin-right: 10px;
            font-weight: normal;
        }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Nexion Logistics OS")

uploaded_file = st.file_uploader("Sube tu Excel de Operaciones", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Aseguramos columnas de observaciones
    if 'OBSERVACIONES DE ALMACEN' not in df.columns: df['OBSERVACIONES DE ALMACEN'] = ""
    if 'OBSERVACIONES DE EMBARQUES' not in df.columns: df['OBSERVACIONES DE EMBARQUES'] = ""

    # Botón de impresión profesional
    components.html(
        """
        <div style="display: flex; gap: 10px;">
            <button onclick="window.parent.print()" style="
                background-color: #00f2ff; color: #000; border: none; 
                padding: 12px; border-radius: 8px; font-weight: bold; 
                cursor: pointer; width: 100%; font-family: sans-serif;">
                🖨️ GENERAR LISTADO TÉCNICO (CHECKLIST)
            </button>
        </div>
        """, height=70
    )

    st.write(f"Mostrando **{len(df)}** registros en Nexion")

    for index, row in df.iterrows():
        # HTML compacto en una sola línea para evitar errores de renderizado
        card_html = f'<div class="render-card"><div class="grid-container"><div><div class="card-header">FACTURA / PEDIDO</div><div class="card-value">{row.get("Factura", "N/A")}</div><div style="font-size: 0.7rem;">REF: {row.get("RECOMENDACION", "")}</div></div><div><div class="card-header">CLIENTE Y DESTINO</div><div class="card-value" style="font-size: 1rem;">{row.get("Nombre_Extran", "N/A")}</div><div style="font-size: 0.8rem;">{row.get("DESTINO", "N/A")}</div></div><div class="obs-section"><div class="card-header">ALMACÉN (MATCH)</div><div style="font-size: 0.8rem;">{row["OBSERVACIONES DE ALMACEN"]}</div></div><div class="obs-section"><div class="card-header">EMBARQUES (CHECK)</div><div style="font-size: 0.8rem;">{row["OBSERVACIONES DE EMBARQUES"]}</div></div></div></div>'
        
        st.markdown(card_html, unsafe_allow_html=True)
else:
    st.info("Esperando archivo Excel...")







































