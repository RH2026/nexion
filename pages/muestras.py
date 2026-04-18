import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Nexion Logistics OS", layout="wide")

# CSS Ajustado: Líneas finas y diseño compacto para impresión
st.markdown("""
    <style>
    /* --- VISTA PANTALLA (TU LOOK DARK NEON) --- */
    .stApp { background-color: #121417; }
    .render-card {
        background-color: #1e2227;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #00f2ff;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    .grid-container { display: grid; grid-template-columns: 1fr 2fr 1.5fr 1.5fr; gap: 15px; }
    .card-header { color: #00f2ff; font-size: 0.75rem; font-weight: bold; }
    .card-value { font-size: 1.1rem; font-weight: bold; }

    /* --- VISTA IMPRESIÓN (LISTADO TÉCNICO COMPACTO) --- */
    @media print {
        header, footer, .stFileUploader, button, [data-testid="stSidebar"] { display: none !important; }
        .stApp { background-color: white !important; padding: 0 !important; }
        
        /* Convertimos la tarjeta en una fila de tabla fina */
        .render-card {
            display: block !important;
            border: 0.5px solid #333 !important; /* Línea muy fina */
            border-radius: 0 !important;
            margin: -0.5px 0 0 0 !important; /* Colapsar bordes para que no se vean dobles */
            padding: 5px 10px !important;
            background-color: white !important;
            color: black !important;
        }

        .grid-container {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 0 !important;
        }

        /* Ajuste de anchos para que todo quepa en una línea */
        .grid-container > div:nth-child(1) { width: 15%; }
        .grid-container > div:nth-child(2) { width: 35%; border-left: 0.5px solid #ccc; padding-left: 10px; }
        .grid-container > div:nth-child(3) { width: 25%; border-left: 0.5px solid #ccc; padding-left: 10px; }
        .grid-container > div:nth-child(4) { width: 25%; border-left: 0.5px solid #ccc; padding-left: 10px; }

        .card-header { color: #555 !important; font-size: 7pt !important; text-transform: uppercase; }
        .card-value { color: black !important; font-size: 9pt !important; }
        
        /* El cuadro de Checkbox más pequeño */
        .render-card::before {
            content: "[ ]";
            font-family: monospace;
            font-size: 12pt;
            margin-right: 8px;
            vertical-align: middle;
        }

        .obs-section {
            height: 35px !important; /* Altura controlada para que no ocupe toda la hoja */
            background-color: transparent !important;
            border: none !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Nexion Logistics OS")

uploaded_file = st.file_uploader("Sube tu Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if 'OBSERVACIONES DE ALMACEN' not in df.columns: df['OBSERVACIONES DE ALMACEN'] = ""
    if 'OBSERVACIONES DE EMBARQUES' not in df.columns: df['OBSERVACIONES DE EMBARQUES'] = ""

    components.html(
        """<button onclick="window.parent.print()" style="background-color: #00f2ff; color: #000; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; font-family: sans-serif;">🖨️ IMPRIMIR LISTADO TÉCNICO</button>""", 
        height=60
    )

    for index, row in df.iterrows():
        # HTML en una sola línea
        card_html = f'<div class="render-card"><div class="grid-container"><div><div class="card-header">FACTURA</div><div class="card-value">{row.get("Factura", "N/A")}</div><div style="font-size: 0.6rem;">{row.get("RECOMENDACION", "")}</div></div><div><div class="card-header">CLIENTE Y DESTINO</div><div class="card-value" style="font-size: 0.9rem;">{row.get("Nombre_Extran", "N/A")}</div><div style="font-size: 0.7rem;">{row.get("DESTINO", "N/A")}</div></div><div class="obs-section"><div class="card-header">ALMACÉN (MATCH)</div><div style="font-size: 0.7rem;">{row["OBSERVACIONES DE ALMACEN"]}</div></div><div class="obs-section"><div class="card-header">EMBARQUES (CHECK)</div><div style="font-size: 0.7rem;">{row["OBSERVACIONES DE EMBARQUES"]}</div></div></div></div>'
        st.markdown(card_html, unsafe_allow_html=True)







































