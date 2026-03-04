import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

# Estilo solo para la pantalla
st.markdown("""
    <style>
    .main { background-color: #0B1014; }
    [data-testid="stMetric"] { 
        background-color: #162129; padding: 25px; border-radius: 12px; border-left: 5px solid #FFCC00; 
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF; font-weight: 900; }
    div[data-testid="stMetricLabel"] { color: #FFCC00; font-weight: bold; }
    .analysis-box {
        background-color: #162129; padding: 25px; border-radius: 12px; border: 1px solid #243441; color: #A4B9C8;
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

# 2. CARGA Y PROCESAMIENTO (Tu lógica original)
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

    # 3. INTERFAZ
    st.title("📦 NEXION LOGISTICS | JYPESA EXECUTIVE")
    c_f1, c_f2 = st.columns(2)
    with c_f1: mes_sel = st.selectbox("📅 MES:", ["TODOS"] + sorted(df_gastos['MES'].unique().tolist()))
    with c_f2: flet_sel = st.selectbox("🚛 FLETERA:", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))

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
    var_costo_caja = ((costo_caja_2026 - costo_caja_2025) / costo_caja_2025 * 100) if costo_caja_2025 > 0 else 0
    var_volumen = ((total_cajas_2026 - total_cajas_2025) / total_cajas_2025 * 100) if total_cajas_2025 > 0 else 0
    costo_log_real = (total_flete_2026/total_fact_2026*100) if total_fact_2026 > 0 else 0
    
    # 5. RENDERIZADO PANTALLA
    st.markdown("### 📊 RESUMEN EJECUTIVO")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}")
    k2.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    k3.metric("CAJAS", f"{total_cajas_2026:,.0f}")
    k4.metric("COSTO LOG.", f"{costo_log_real:.2f}%")

    status_target = "🟢 DENTRO" if costo_log_real <= 7.5 else "🔴 FUERA"
    html_analisis = f'<div class="analysis-box">Operación <b>{status_target}</b> del target (7.5%).</div>'
    st.markdown(html_analisis, unsafe_allow_html=True)

    # 6. GENERACIÓN DEL REPORTE TÉCNICO (HTML COMPONENT)
    # Aquí construimos el diseño "Super Técnico" para papel
    reporte_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', Courier, monospace; color: black; background: white; padding: 0; }}
            .report-header {{ border-bottom: 3px solid black; padding-bottom: 10px; margin-bottom: 20px; }}
            .report-title {{ font-size: 22px; font-weight: bold; }}
            .tech-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .tech-table th, .tech-table td {{ border: 1px solid black; padding: 10px; text-align: left; font-size: 12px; }}
            .tech-table th {{ background-color: #eeeeee; text-transform: uppercase; }}
            .kpi-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; border: 1px solid black; margin-bottom: 20px; }}
            .kpi-box {{ border: 0.5px solid black; padding: 10px; }}
            .kpi-label {{ font-size: 10px; font-weight: bold; display: block; margin-bottom: 5px; }}
            .kpi-value {{ font-size: 16px; font-weight: bold; }}
            .stamp {{ border: 2px solid black; padding: 10px; width: fit-content; margin-top: 30px; font-weight: bold; text-transform: uppercase; }}
            @media print {{ .no-print {{ display: none; }} }}
        </style>
    </head>
    <body>
        <div class="report-header">
            <div class="report-title">NEXION JYPESA - REPORTE DE INGENIERÍA LOGÍSTICA</div>
            <div style="font-size: 12px;">EJERCICIO FISCAL 2026 | FILTRO: {mes_sel} / {flet_sel}</div>
        </div>

        <div class="kpi-grid">
            <div class="kpi-box"><span class="kpi-label">COSTO FLETE NETO</span><span class="kpi-value">${total_flete_2026:,.2f}</span></div>
            <div class="kpi-box"><span class="kpi-label">BASE FACTURACIÓN</span><span class="kpi-value">${total_fact_2026:,.2f}</span></div>
            <div class="kpi-box"><span class="kpi-label">TOTAL UNIDADES (CAJAS)</span><span class="kpi-value">{total_cajas_2026:,.0f}</span></div>
            <div class="kpi-box"><span class="kpi-label">RATIO LOGÍSTICO</span><span class="kpi-value">{costo_log_real:.2f}%</span></div>
        </div>

        <table class="tech-table">
            <thead>
                <tr>
                    <th>INDICADOR TÉCNICO</th>
                    <th>VALOR ACTUAL (2026)</th>
                    <th>REFERENCIA (2025)</th>
                    <th>VARIACIÓN Δ</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>COSTO POR UNIDAD DESPACHADA</td><td>${costo_caja_2026:,.2f}</td><td>${costo_caja_2025:,.2f}</td><td>{var_costo_caja:+.2f}%</td></tr>
                <tr><td>VOLUMEN TOTAL DE CARGA</td><td>{total_cajas_2026:,.0f}</td><td>{total_cajas_2025:,.0f}</td><td>{var_volumen:+.2f}%</td></tr>
                <tr><td>VALUACIÓN DE INCIDENCIAS</td><td>${total_valuacion_2026:,.2f}</td><td>N/A</td><td>-</td></tr>
                <tr><td>EFICIENCIA VS VENTAS</td><td>{costo_log_real:.2f}%</td><td>TARGET: 7.5%</td><td>{costo_log_real - 7.5:+.2f}%</td></tr>
            </tbody>
        </table>

        <div class="stamp">ESTATUS OPERATIVO: {status_target}</div>

        <div style="margin-top: 50px; border-top: 1px dashed black; width: 250px; font-size: 10px; text-align: center; padding-top: 5px;">
            FIRMA DE VALIDACIÓN TÉCNICA
        </div>

        <button class="no-print" onclick="window.print()" style="margin-top: 30px; padding: 15px 30px; background: #FFCC00; border: none; font-weight: bold; cursor: pointer; width: 100%;">
            🖨️ CONFIRMAR E IMPRIMIR REPORTE TÉCNICO
        </button>
    </body>
    </html>
    """

    st.markdown("---")
    # El componente HTML renderiza el reporte de forma independiente
    components.html(reporte_html, height=600, scrolling=True)

except Exception as e:
    st.error(f"Error: {e}")





















































































































































