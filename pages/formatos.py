import streamlit as st
import pandas as pd
import unicodedata

# 1. CONFIGURACIÓN TÉCNICA Y ESTILO DE INGENIERÍA
st.set_page_config(page_title="Nexion JYPESA - Engineering Report", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    .main { background-color: #0E1117; }
    
    /* Contenedor de Reporte tipo Ingeniería */
    .report-container {
        border: 1px solid #30363D;
        background-color: #161B22;
        padding: 20px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Estilo de métricas tipo "Data Point" */
    [data-testid="stMetric"] {
        border: 1px solid #30363D !important;
        background-color: #0D1117 !important;
        border-radius: 0px !important;
        padding: 15px !important;
    }
    
    div[data-testid="stMetricValue"] {
        color: #58A6FF !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #8B949E !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.7rem !important;
    }

    /* Tabla Técnica HTML */
    .tech-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }
    .tech-table th {
        background-color: #21262D;
        color: #C9D1D9;
        text-align: left;
        padding: 10px;
        border: 1px solid #30363D;
    }
    .tech-table td {
        padding: 10px;
        border: 1px solid #30363D;
        color: #8B949E;
    }
    
    .status-ok { color: #3FB950; font-weight: bold; }
    .status-warn { color: #F85149; font-weight: bold; }

    /* Estilo de Impresión */
    @media print {
        header, .stSelectbox { display: none !important; }
        .main, .stApp { background-color: white !important; }
        .report-container { border: 2px solid black !important; }
        div[data-testid="stMetricValue"] { color: black !important; }
        .tech-table th { background-color: #eee !important; color: black !important; }
        .tech-table td { color: black !important; border: 1px solid black !important; }
    }
    </style>
    """, unsafe_allow_html=True)

def limpiar_columnas(txt):
    if not isinstance(txt, str): return txt
    texto = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

def limpiar_dinero(col):
    if col.dtype == object:
        return pd.to_numeric(col.str.replace('$', '').str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    return col.fillna(0)

# 2. CARGA Y PROCESAMIENTO
try:
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]

    columnas_dinero = ['COSTO DE LA GUIA', 'FACTURACION', 'VALUACION', 'COSTOS ADICIONALES']
    for col in columnas_dinero:
        if col in df_actual.columns: df_actual[col] = limpiar_dinero(df_actual[col])
    if 'COSTO DE LA GUIA' in df_2025.columns: df_2025['COSTO DE LA GUIA'] = limpiar_dinero(df_2025['COSTO DE LA GUIA'])

    df_actual['MES'] = df_actual['MES'].astype(str).str.strip().str.upper()
    df_2025['MES'] = df_2025['MES'].astype(str).str.strip().str.upper()

    df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False)].copy()
    df_gastos['COSTO DE FLETE'] = df_gastos['COSTO DE LA GUIA'] + df_gastos['COSTOS ADICIONALES']

    # 3. HEADER TÉCNICO
    st.markdown(f"""
        <div style="border-left: 4px solid #58A6FF; padding-left: 15px; margin-bottom: 25px;">
            <h1 style="margin:0; color:#F0F6FC; font-size:1.5rem;">NEXION | LOGISTICS ENGINEERING REPORT</h1>
            <p style="margin:0; color:#8B949E; font-size:0.8rem;">ENGINEER IN CHARGE: {st.experimental_user.email if hasattr(st, 'experimental_user') else 'LOGISTICS MANAGER'}</p>
        </div>
    """, unsafe_allow_html=True)

    c_f1, c_f2 = st.columns(2)
    with c_f1: mes_sel = st.selectbox("OPERATIONAL_PERIOD (MONTH):", ["TODOS"] + sorted(df_gastos['MES'].unique().tolist()))
    with c_f2: flet_sel = st.selectbox("CARRIER_ID (FLETERA):", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))

    df_filtered = df_gastos.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]

    # 4. CÁLCULOS
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
    costo_log_real = (total_flete_2026/total_fact_2026*100) if total_fact_2026 > 0 else 0

    # 5. DATA GRID (KPIs)
    st.markdown("<div class='report-container'>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("FREIGHT_COST_TOTAL", f"${total_flete_2026:,.2f}")
    with k2: st.metric("REVENUE_TOTAL", f"${total_fact_2026:,.2f}")
    with k3: st.metric("UNITS_SHIPPED (CAJAS)", f"{total_cajas_2026:,.0f}")
    with k4: st.metric("LOG_COST_RATIO", f"{costo_log_real:.2f}%")

    k5, k6, k7, k8 = st.columns(4)
    with k5: st.metric("UNIT_COST (PER_BOX)", f"${costo_caja_2026:,.2f}")
    with k6: st.metric("INCIDENT_VALUATION", f"${total_valuacion_2026:,.2f}")
    with k7: st.metric("INCIDENT_RATE", f"{( (df_filtered['VALUACION']>0).sum()/len(df_filtered)*100 if len(df_filtered)>0 else 0):.1f}%")
    with k8: st.metric("YOY_VARIANCE (INC+VI)", f"${(total_flete_2026 + total_valuacion_2026) - total_flete_2025:,.2f}")
    
    # 6. MATRIZ DE COMPARATIVO TÉCNICO (HTML COMPONENT)
    st.markdown("### 🛠 COMPARATIVE OPERATIONAL MATRIX")
    
    status_class = "status-ok" if costo_log_real <= 7.5 else "status-warn"
    
    table_html = f"""
    <table class="tech-table">
        <thead>
            <tr>
                <th>PARAMETER</th>
                <th>PERIOD_2025 (REF)</th>
                <th>PERIOD_2026 (ACTUAL)</th>
                <th>VARIANCE_ABS</th>
                <th>VARIANCE_REL (%)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Freight Expenditure</td>
                <td>${total_flete_2025:,.2f}</td>
                <td>${total_flete_2026:,.2f}</td>
                <td>${total_flete_2026 - total_flete_2025:,.2f}</td>
                <td>{((total_flete_2026 - total_flete_2025)/total_flete_2025*100 if total_flete_2025>0 else 0):.2f}%</td>
            </tr>
            <tr>
                <td>Volume (Units)</td>
                <td>{total_cajas_2025:,.0f}</td>
                <td>{total_cajas_2026:,.0f}</td>
                <td>{total_cajas_2026 - total_cajas_2025:,.0f}</td>
                <td>{((total_cajas_2026 - total_cajas_2025)/total_cajas_2025*100 if total_cajas_2025>0 else 0):.2f}%</td>
            </tr>
            <tr>
                <td>Unit Efficiency (Cost/Box)</td>
                <td>${costo_caja_2025:,.2f}</td>
                <td>${costo_caja_2026:,.2f}</td>
                <td>${costo_caja_2026 - costo_caja_2025:,.2f}</td>
                <td>{((costo_caja_2026 - costo_caja_2025)/costo_caja_2025*100 if costo_caja_2025>0 else 0):.2f}%</td>
            </tr>
            <tr>
                <td>Logistics Ratio (Target: 7.5%)</td>
                <td>N/A</td>
                <td class="{status_class}">{costo_log_real:.2f}%</td>
                <td>{costo_log_real - 7.5:+.2f}</td>
                <td>TARGET_REF</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"SYSTEM_ERROR: {e}")





































































































































