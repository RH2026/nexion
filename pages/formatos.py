import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components
from datetime import datetime

# 1. CONFIGURACIÓN Y ESTILO (ONYX DHL)
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

# ESTILOS PARA LA APP Y PARA LA IMPRESIÓN
st.markdown("""
    <style>
    .main { background-color: #0B1014; }
    [data-testid="stMetric"] { 
        background-color: #162129; 
        padding: 25px; 
        border-radius: 12px; 
        border-left: 5px solid #FFCC00; 
        min-height: 160px !important;
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF; font-weight: 900; }
    div[data-testid="stMetricLabel"] { color: #FFCC00; font-weight: bold; }
    
    .analysis-box {
        background-color: #162129;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #243441;
        color: #A4B9C8;
    }
    
    /* ESTO ES LO QUE CORRIGE LOS MARGENES EN EL NAVEGADOR */
    @media print {
        @page {
            size: landscape;
            margin: 2cm !important; /* Margen forzado de 2cm */
        }
        body {
            margin: 1.6cm !important;
        }
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

    # 3. INTERFAZ
    st.title("📦 NEXION LOGISTICS | JYPESA EXECUTIVE")
    c_f1, c_f2 = st.columns(2)
    with c_f1: mes_sel = st.selectbox("📅 FILTRAR POR MES:", ["TODOS"] + sorted(df_gastos['MES'].unique().tolist()))
    with c_f2: flet_sel = st.selectbox("🚛 FILTRAR POR FLETERA:", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))

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
    var_costo_caja = ((costo_caja_2026 - (total_flete_2025/total_cajas_2025)) / (total_flete_2025/total_cajas_2025) * 100) if total_cajas_2025 > 0 else 0
    costo_log_real = (total_flete_2026/total_fact_2026*100) if total_fact_2026 > 0 else 0
    num_inc = (df_filtered['VALUACION'] > 0).sum()
    pct_inc = (num_inc/len(df_filtered)*100) if len(df_filtered)>0 else 0
    inc_vi_monto = (total_flete_2026 + total_valuacion_2026) - total_flete_2025

    # 5. RENDERIZADO DE KPIs
    st.markdown("### 📊 RESUMEN EJECUTIVO")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}")
    with k2: st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}")
    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%")

    # 6. ANÁLISIS DINÁMICO
    status_target = "🟢 DENTRO" if costo_log_real <= 7.5 else "🔴 FUERA"
    st.markdown(f'<div class="analysis-box"><b>Estatus:</b> Operación {status_target} del target logístico.</div>', unsafe_allow_html=True)

    # 7. LÓGICA DE IMPRESIÓN REESTRUCTURADA
    # Usamos un div contenedor con padding interno para asegurar los márgenes
    reporte_impresion = f"""
    <div id="print-area" style="padding: 40px; background: white; color: black; font-family: sans-serif;">
        <div style="border-bottom: 3px solid black; padding-bottom: 10px; margin-bottom: 20px;">
            <h1 style="margin:0; font-size: 24px;">REPORTE TÉCNICO LOGÍSTICO</h1>
            <p style="font-size: 12px;">FECHA: {datetime.now().strftime('%d/%m/%Y')} | FILTROS: {mes_sel} / {flet_sel}</p>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <tr>
                <td style="border: 1px solid black; padding: 15px; text-align: center;">
                    <small style="display:block; font-weight:bold;">COSTO FLETE</small>
                    <span style="font-size: 20px; font-weight:bold;">${total_flete_2026:,.2f}</span>
                </td>
                <td style="border: 1px solid black; padding: 15px; text-align: center;">
                    <small style="display:block; font-weight:bold;">FACTURACIÓN</small>
                    <span style="font-size: 20px; font-weight:bold;">${total_fact_2026:,.2f}</span>
                </td>
                <td style="border: 1px solid black; padding: 15px; text-align: center;">
                    <small style="display:block; font-weight:bold;">CAJAS</small>
                    <span style="font-size: 20px; font-weight:bold;">{total_cajas_2026:,.0f}</span>
                </td>
                <td style="border: 1px solid black; padding: 15px; text-align: center;">
                    <small style="display:block; font-weight:bold;">LOGÍSTICO</small>
                    <span style="font-size: 20px; font-weight:bold;">{costo_log_real:.2f}%</span>
                </td>
            </tr>
        </table>

        <div style="border: 1px solid black; padding: 20px; background-color: #f0f0f0;">
            <strong>DICTAMEN TÉCNICO:</strong><br>
            La operación se reporta {status_target} del target del 7.5%. 
            Variación de costo por caja: {var_costo_caja:+.1f}%.
        </div>
    </div>
    """

    st.markdown("---")
    # Aumentamos el height a 500 para que el iframe sea visible y el navegador lo procese bien
    if st.button("🖨️ CLIC AQUÍ PARA IMPRIMIR"):
        components.html(f"""
            {reporte_impresion}
            <script>
                // Esperar a que todo cargue y lanzar impresión
                window.onload = function() {{
                    window.print();
                }};
            </script>
        """, height=600, scrolling=True)

except Exception as e:
    st.error(f"Error: {e}")

























































































































































