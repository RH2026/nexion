import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components

# --------------------------------------------------
# 1. CONFIGURACIÓN GENERAL
# --------------------------------------------------
st.set_page_config(page_title="Nexion JYPESA - Executive Report", layout="wide")

st.markdown("""
<style>

/* ------------------ ESTILO WEB ------------------ */
.main { background-color: #0B1014; }

[data-testid="stMetric"] { 
    background-color: #162129; 
    padding: 25px; 
    border-radius: 12px; 
    border-left: 5px solid #FFCC00; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    min-height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

div[data-testid="stMetricValue"] { 
    color: #FFFFFF; 
    font-weight: 900; 
    font-size: 2.2rem; 
}

div[data-testid="stMetricLabel"] { 
    color: #FFCC00; 
    letter-spacing: 1.5px; 
    text-transform: uppercase; 
    font-size: 0.8rem; 
    font-weight: bold; 
}

h1 { 
    color: #FFFFFF; 
    font-family: 'Arial Black'; 
    border-bottom: 2px solid #FFCC00; 
    padding-bottom: 10px; 
}

h3 { 
    color: #FFCC00; 
    margin-top: 30px; 
    text-transform: uppercase; 
    letter-spacing: 2px; 
}

.analysis-box {
    background-color: #162129;
    padding: 25px;
    border-radius: 12px;
    border: 1px solid #243441;
    color: #A4B9C8;
    line-height: 1.8;
    font-size: 1.1rem;
}

.highlight { color: #FFCC00; font-weight: bold; }

/* ------------------ MODO IMPRESIÓN ------------------ */
@media print {

    @page { 
        size: A4 portrait; 
        margin: 1.5cm; 
    }

    header, 
    [data-testid="stSidebar"], 
    .stSelectbox, 
    .stButton, 
    iframe, 
    hr,
    .print-button { 
        display: none !important; 
    }

    .main, .stApp { 
        background-color: white !important; 
        color: black !important; 
    }

    [data-testid="stMetric"], 
    .analysis-box { 
        display: none !important; 
    }

    h1 { 
        color: black !important; 
        border-bottom: 3px solid black !important; 
        font-size: 20px !important;
        letter-spacing: 1px;
    }

    h3 { 
        color: black !important; 
        margin-top: 25px !important; 
        font-size: 14px !important; 
        letter-spacing: 2px;
    }

    .tech-matrix {
        width: 100%;
        border-collapse: collapse;
        margin-top: 25px;
        font-family: 'Courier New', monospace;
        font-size: 11px;
    }

    .tech-matrix th {
        background-color: #EAEAEA !important;
        color: black !important;
        text-align: center;
        padding: 8px;
        border: 1.5px solid black;
    }

    .tech-matrix td {
        padding: 8px;
        border: 1px solid black;
        text-align: right;
    }

    .tech-matrix td:first-child {
        text-align: left;
        font-weight: bold;
    }

    .row-total { 
        background-color: #DCDCDC !important; 
        font-weight: bold; 
    }

    .firma-section {
        margin-top: 70px;
        font-family: Arial, sans-serif;
        font-size: 12px;
    }

    .firma-line {
        margin-top: 60px;
        border-top: 1px solid black;
        width: 250px;
    }

    .visible-print { 
        display: block !important; 
    }
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------------------
def limpiar_columnas(txt):
    if not isinstance(txt, str): return txt
    texto = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

def limpiar_dinero(col):
    if col.dtype == object:
        return pd.to_numeric(col.str.replace('$', '').str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    return col.fillna(0)


# --------------------------------------------------
# CARGA DE DATOS
# --------------------------------------------------
try:
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]

    columnas_dinero = ['COSTO DE LA GUIA', 'FACTURACION', 'VALUACION', 'COSTOS ADICIONALES']
    for col in columnas_dinero:
        if col in df_actual.columns:
            df_actual[col] = limpiar_dinero(df_actual[col])

    if 'COSTO DE LA GUIA' in df_2025.columns:
        df_2025['COSTO DE LA GUIA'] = limpiar_dinero(df_2025['COSTO DE LA GUIA'])

    df_actual['MES'] = df_actual['MES'].astype(str).str.strip().str.upper()
    df_2025['MES'] = df_2025['MES'].astype(str).str.strip().str.upper()

    df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False)].copy()
    df_gastos['COSTO DE FLETE'] = df_gastos['COSTO DE LA GUIA'] + df_gastos['COSTOS ADICIONALES']


    # --------------------------------------------------
    # INTERFAZ
    # --------------------------------------------------
    st.title("📦 NEXION LOGISTICS | JYPESA EXECUTIVE REPORT")

    c1, c2 = st.columns(2)
    with c1:
        mes_sel = st.selectbox("FILTRAR POR MES", ["TODOS"] + sorted(df_gastos['MES'].unique().tolist()))
    with c2:
        flet_sel = st.selectbox("FILTRAR POR FLETERA", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))

    df_filtered = df_gastos.copy()

    if mes_sel != "TODOS":
        df_filtered = df_filtered[df_filtered['MES'] == mes_sel]

    if flet_sel != "TODAS":
        df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]


    # --------------------------------------------------
    # CÁLCULOS
    # --------------------------------------------------
    total_flete_2026 = df_filtered['COSTO DE FLETE'].sum()
    total_fact_2026 = df_filtered['FACTURACION'].sum()
    total_cajas_2026 = df_filtered['CAJAS'].sum()
    total_valuacion_2026 = df_filtered['VALUACION'].sum()

    meses_activos = df_filtered['MES'].unique()
    df_2025_filtrado = df_2025[df_2025['MES'].isin(meses_activos)]

    total_flete_2025 = df_2025_filtrado['COSTO DE LA GUIA'].sum()
    total_cajas_2025 = df_2025_filtrado['CAJAS'].sum()

    costo_caja_2026 = (total_flete_2026 / total_cajas_2026) if total_cajas_2026 > 0 else 0
    costo_caja_2025 = (total_flete_2025 / total_cajas_2025) if total_cajas_2025 > 0 else 0
    var_costo_caja = ((costo_caja_2026 - costo_caja_2025) / costo_caja_2025 * 100) if costo_caja_2025 > 0 else 0
    var_volumen = ((total_cajas_2026 - total_cajas_2025) / total_cajas_2025 * 100) if total_cajas_2025 > 0 else 0
    costo_log_real = (total_flete_2026/total_fact_2026*100) if total_fact_2026 > 0 else 0


    # --------------------------------------------------
    # KPIs WEB
    # --------------------------------------------------
    st.markdown("### 📊 RESUMEN EJECUTIVO")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}")
    k2.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    k3.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}")
    k4.metric("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%")

    # --------------------------------------------------
    # MATRIZ PARA IMPRESIÓN
    # --------------------------------------------------
    st.markdown(f"""
    <div style="display:none;" class="visible-print">

        <h3>REPORTE TÉCNICO DE INGENIERÍA DE COSTOS</h3>

        <p style="font-size:11px;">
        Empresa: NEXION LOGISTICS<br>
        Cliente: JYPESA<br>
        Fecha de emisión: {pd.Timestamp.today().strftime("%d/%m/%Y")}<br>
        Periodo Analizado: {mes_sel}
        </p>

        <table class="tech-matrix">
            <thead>
                <tr>
                    <th>INDICADOR</th>
                    <th>2026</th>
                    <th>2025</th>
                    <th>Δ ABS</th>
                    <th>Δ %</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Gasto Total de Flete</td>
                    <td>${total_flete_2026:,.2f}</td>
                    <td>${total_flete_2025:,.2f}</td>
                    <td>${total_flete_2026-total_flete_2025:,.2f}</td>
                    <td>{((total_flete_2026-total_flete_2025)/total_flete_2025*100 if total_flete_2025>0 else 0):.2f}%</td>
                </tr>
                <tr>
                    <td>Volumen (Cajas)</td>
                    <td>{total_cajas_2026:,.0f}</td>
                    <td>{total_cajas_2025:,.0f}</td>
                    <td>{total_cajas_2026-total_cajas_2025:,.0f}</td>
                    <td>{var_volumen:.2f}%</td>
                </tr>
                <tr>
                    <td>Costo Unitario</td>
                    <td>${costo_caja_2026:,.2f}</td>
                    <td>${costo_caja_2025:,.2f}</td>
                    <td>${costo_caja_2026-costo_caja_2025:,.2f}</td>
                    <td>{var_costo_caja:.2f}%</td>
                </tr>
                <tr class="row-total">
                    <td>Costo Logístico vs Facturación (Meta 7.5%)</td>
                    <td colspan="2" style="text-align:center;">{costo_log_real:.2f}%</td>
                    <td>{costo_log_real-7.5:+.2f} pts</td>
                    <td>Target</td>
                </tr>
            </tbody>
        </table>

        <div class="firma-section">
            <div class="firma-line"></div>
            Responsable de Análisis

            <div class="firma-line"></div>
            Dirección Operativa
        </div>

    </div>
    """, unsafe_allow_html=True)


    # --------------------------------------------------
    # BOTÓN DE IMPRESIÓN
    # --------------------------------------------------
    st.markdown("---")

    components.html("""
        <div class="print-button" style="text-align:center;">
            <button 
                style="
                    background-color:#FFCC00;
                    color:#0B1014;
                    border:none;
                    padding:18px 40px;
                    font-family:'Arial Black';
                    font-size:18px;
                    border-radius:10px;
                    cursor:pointer;
                    width:100%;
                    box-shadow:0 6px 20px rgba(0,0,0,0.4);
                "
                onclick="window.parent.print()">
                🖨️ GENERAR REPORTE EJECUTIVO (IMPRIMIR)
            </button>
        </div>
    """, height=100)

except Exception as e:
    st.error(f"Error detectado: {e}")















































































































































