import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Nexion Logistics OS", layout="wide")

# --- CSS INTEGRADO (PANTALLA Y REPORTE) ---
st.markdown("""
    <style>
    /* VISTA DE PANTALLA (TU ESTILO DARK NEON) */
    .stApp { background-color: #121417; }
    .render-card {
        background-color: #1e2227; border-radius: 8px; padding: 15px;
        margin-bottom: 10px; border-left: 4px solid #00f2ff; color: #e0e0e0;
    }
    .grid-container { display: grid; grid-template-columns: 1fr 2fr 1.5fr 1.5fr; gap: 15px; }
    .card-header { color: #00f2ff; font-size: 0.75rem; font-weight: bold; }
    .card-value { font-size: 1.1rem; font-weight: bold; }

    /* ESTO ES LO QUE SE IMPRIME (LISTADO TÉCNICO) */
    #print-section { display: none; }
    
    @media print {
        /* Ocultar TODO lo de Streamlit */
        body * { visibility: hidden; }
        /* Mostrar SOLO nuestra sección técnica */
        #print-section, #print-section * { visibility: visible; }
        #print-section {
            display: block !important;
            position: absolute;
            left: 0; top: 0; width: 100%;
            background-color: white !important;
            color: black !important;
        }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #000; padding: 6px; text-align: left; font-size: 9pt; color: black; }
        th { background-color: #f0f0f0 !important; -webkit-print-color-adjust: exact; }
        .check-col { width: 30px; text-align: center; font-size: 12pt; }
        .sub-text { font-size: 7pt; color: #444; display: block; }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Nexion Logistics OS")

uploaded_file = st.file_uploader("Sube tu Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file).fillna("")

    # 1. PREPARAMOS EL HTML DEL LISTADO TÉCNICO (Oculto en pantalla)
    filas_html = ""
    for _, row in df.iterrows():
        filas_html += f"""
        <tr>
            <td class='check-col'>[ ]</td>
            <td><b>{row.get('Factura', '')}</b><br><span class='sub-text'>{row.get('RECOMENDACION', '')}</span></td>
            <td><b>{row.get('Nombre_Extran', '')}</b><br><span class='sub-text'>{row.get('DESTINO', '')}</span></td>
            <td>{row.get('OBSERVACIONES DE ALMACEN', '')}</td>
            <td>{row.get('OBSERVACIONES DE EMBARQUES', '')}</td>
        </tr>
        """

    # Inyectamos el área de impresión oculta
    st.markdown(f"""
        <div id="print-section">
            <h2 style="text-align:center;">NEXION - CONTROL DE SALIDA</h2>
            <p style="text-align:right; font-size: 8pt;">Generado: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</p>
            <table>
                <thead>
                    <tr>
                        <th class='check-col'>OK</th>
                        <th>FACTURA / REF</th>
                        <th>CLIENTE Y DESTINO</th>
                        <th>ALMACÉN (MATCH)</th>
                        <th>EMBARQUES (CHECK)</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
            </table>
        </div>
    """, unsafe_allow_html=True)

    # 2. BOTÓN DE IMPRESIÓN (Llamada directa al sistema)
    st.write("### Acciones")
    if st.button("🖨️ ABRIR OPCIONES DE IMPRESIÓN"):
        components.html("<script>window.parent.print();</script>", height=0)

    # 3. RENDER VISUAL PARA TI (LO QUE VES EN PANTALLA)
    st.write(f"Mostrando {len(df)} registros")
    for index, row in df.iterrows():
        st.markdown(f"""
            <div class="render-card">
                <div class="grid-container">
                    <div><div class="card-header">FACTURA</div><div class="card-value">{row.get('Factura', 'N/A')}</div></div>
                    <div><div class="card-header">CLIENTE</div><div class="card-value">{row.get('Nombre_Extran', 'N/A')}</div></div>
                    <div><div class="card-header">ALMACÉN</div><div style="font-size: 0.8rem;">{row.get('OBSERVACIONES DE ALMACEN', '')}</div></div>
                    <div><div class="card-header">EMBARQUES</div><div style="font-size: 0.8rem;">{row.get('OBSERVACIONES DE EMBARQUES', '')}</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)







































