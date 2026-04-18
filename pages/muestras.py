import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Nexion Logistics OS", layout="wide")

# CSS para la PANTALLA (Modo Dark Neon)
st.markdown("""
    <style>
    .stApp { background-color: #121417; }
    .render-card {
        background-color: #1e2227; border-radius: 8px; padding: 15px;
        margin-bottom: 10px; border-left: 4px solid #00f2ff; color: #e0e0e0;
    }
    .grid-container { display: grid; grid-template-columns: 1fr 2fr 1.5fr 1.5fr; gap: 15px; }
    .card-header { color: #00f2ff; font-size: 0.75rem; font-weight: bold; }
    .card-value { font-size: 1.1rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Nexion Logistics OS")

uploaded_file = st.file_uploader("Sube tu Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("")
    
    # --- CONSTRUCCIÓN DEL DOCUMENTO DE IMPRESIÓN (OCULTO) ---
    # Creamos una tabla HTML pura, sin estilos de Streamlit
    tabla_html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #333; padding: 8px; text-align: left; font-size: 10pt; }
            th { background-color: #eee; }
            .ch { width: 30px; text-align: center; font-weight: bold; }
            .header-info { font-size: 8pt; color: #666; display: block; }
        </style>
    </head>
    <body>
        <h2 style='text-align:center;'>Nexion Logistics - Listado Técnico de Embarques</h2>
        <table>
            <tr>
                <th class='ch'>[ ]</th>
                <th>FACTURA / REF</th>
                <th>CLIENTE Y DESTINO</th>
                <th>ALMACÉN (MATCH)</th>
                <th>EMBARQUES (CHECK)</th>
            </tr>
    """
    
    for _, row in df.iterrows():
        tabla_html += f"""
            <tr>
                <td class='ch'>[ ]</td>
                <td><b>{row.get('Factura', '')}</b><br><span class='header-info'>{row.get('RECOMENDACION', '')}</span></td>
                <td><b>{row.get('Nombre_Extran', '')}</b><br><span class='header-info'>{row.get('DESTINO', '')}</span></td>
                <td>{row.get('OBSERVACIONES DE ALMACEN', '')}</td>
                <td>{row.get('OBSERVACIONES DE EMBARQUES', '')}</td>
            </tr>
        """
    
    tabla_html += "</table><script>window.onload = function() { window.print(); window.close(); }</script></body></html>"

    # --- BOTÓN DE IMPRESIÓN "PERRÓN" ---
    # Este botón abre una ventana nueva con el HTML técnico puro
    if st.button("🖨️ GENERAR REPORTE TÉCNICO LIMPIO"):
        components.html(f"""
            <script>
                var printWindow = window.open('', '_blank');
                printWindow.document.write(`{tabla_html}`);
                printWindow.document.close();
            </script>
        """, height=0)

    # --- RENDERIZADO EN PANTALLA (LO QUE TÚ VES) ---
    for index, row in df.iterrows():
        card_html = f'<div class="render-card"><div class="grid-container"><div><div class="card-header">FACTURA</div><div class="card-value">{row.get("Factura", "N/A")}</div></div><div><div class="card-header">CLIENTE</div><div class="card-value">{row.get("Nombre_Extran", "N/A")}</div></div><div><div class="card-header">ALMACÉN</div><div>{row.get("OBSERVACIONES DE ALMACEN", "")}</div></div><div><div class="card-header">EMBARQUES</div><div>{row.get("OBSERVACIONES DE EMBARQUES", "")}</div></div></div></div>'
        st.markdown(card_html, unsafe_allow_html=True)







































