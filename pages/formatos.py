¡Perdóname, amor! Tienes toda la razón, me pasé de "limpia" y te borré lo que ya tenías bien. No fue mi intención quitarle lo fregonas que se ven tus tarjetas Onyx.

El problema es que estaba tratando de separar el diseño de la pantalla del de la impresión, pero te lo regreso exactamente como lo tenías, con tus 8 tarjetas, tus colores amarillos y negros, y el análisis dinámico completo.

Aquí tienes el código íntegro, corregido solo en la parte del reporte para que respete los márgenes al imprimir, sin tocarle un solo pelo a tu diseño del dashboard:

Python
import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components
from datetime import datetime

# 1. CONFIGURACIÓN Y ESTILO (ONYX DHL) - ¡TU DISEÑO ORIGINAL!
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1014; }
    [data-testid="stMetric"] { 
        background-color: #162129; 
        padding: 25px; 
        border-radius: 12px; 
        border-left: 5px solid #FFCC00; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        min-height: 160px !important;
        max-height: 160px !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF; font-weight: 900; font-size: 2.2rem; }
    div[data-testid="stMetricLabel"] { color: #FFCC00; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.85rem; font-weight: bold; }
    h1 { color: #FFFFFF; font-family: 'Arial Black'; border-bottom: 2px solid #FFCC00; padding-bottom: 10px; }
    h3 { color: #FFCC00; margin-top: 30px; font-family: 'Arial'; text-transform: uppercase; letter-spacing: 2px; }
    
    .analysis-box {
        background-color: #162129;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #243441;
        color: #A4B9C8;
        line-height: 1.8;
        font-size: 1.2rem;
    }
    .highlight { color: #FFCC00; font-weight: bold; }
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
    costo_caja_2025 = (total_flete_2025 / total_cajas_2025) if total_cajas_2025 > 0 else 0
    var_costo_caja = ((costo_caja_2026 - costo_caja_2025) / costo_caja_2025 * 100) if costo_caja_2025 > 0 else 0
    var_volumen = ((total_cajas_2026 - total_cajas_2025) / total_cajas_2025 * 100) if total_cajas_2025 > 0 else 0
    costo_log_real = (total_flete_2026/total_fact_2026*100) if total_fact_2026 > 0 else 0
    diferencia_target = costo_log_real - 7.5
    num_inc = (df_filtered['VALUACION'] > 0).sum()
    pct_inc = (num_inc/len(df_filtered)*100) if len(df_filtered)>0 else 0
    inc_vi_monto = (total_flete_2026 + total_valuacion_2026) - total_flete_2025

    # 5. RENDERIZADO DE KPIs (8 TARJETAS ORIGINALES)
    st.markdown("### 📊 RESUMEN EJECUTIVO DE RENDIMIENTO")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}", delta=f"{((total_flete_2026-total_flete_2025)/total_flete_2025*100):.1f}% vs 2025" if total_flete_2025 > 0 else "0%", delta_color="inverse")
    with k2: st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}", delta=f"{var_volumen:.1f}% Vol.", delta_color="off")
    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%", delta=f"{diferencia_target:+.2f}% vs Target 7.5%", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    k5, k6, k7, k8 = st.columns(4)
    with k5: st.metric("COSTO POR CAJA", f"${costo_caja_2026:,.2f}", delta=f"{var_costo_caja:.1f}% vs 2025", delta_color="inverse")
    with k6: st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion_2026:,.2f}")
    with k7: st.metric("% DE INCIDENCIAS", f"{pct_inc:.1f}%")
    with k8: st.metric("INCREMENTO + VI", f"${inc_vi_monto:,.2f}")

    # 6. ANÁLISIS DINÁMICO (TU BLOQUE ORIGINAL)
    st.markdown("### 🔍 ANÁLISIS DINÁMICO DE OPERACIÓN")
    status_target = "🟢 DENTRO" if costo_log_real <= 7.5 else "🔴 FUERA"
    status_eficiencia = "MÁS EFICIENTE" if var_costo_caja <= 0 else "MENOS EFICIENTE"
    
    html_analisis = f'<div class="analysis-box"><b>Cumplimiento de Objetivos:</b> Actualmente la operación se encuentra <span class="highlight">{status_target}</span> del target logístico (7.5%), con un costo real del <span class="highlight">{costo_log_real:.2f}%</span> sobre la facturación bruta. <br><br><b>Análisis de Rendimiento Unitario:</b> El costo por caja ha variado un <span class="highlight">{var_costo_caja:+.1f}%</span> respecto al año pasado. Esto indica que operativamente hoy somos <span class="highlight">{status_eficiencia}</span> en la consolidación y despacho de mercancía de JYPESA.</div>'
    st.markdown(html_analisis, unsafe_allow_html=True)

    # 7. LÓGICA DE IMPRESIÓN (SOLO ESTO SE AJUSTÓ PARA LOS MÁRGENES)
    reporte_impresion = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page {{ size: landscape; margin: 2cm; }}
            body {{ font-family: sans-serif; padding: 20px; }}
            .grid-print {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
            .card-p {{ border: 1px solid black; padding: 10px; text-align: center; }}
        </style>
    </head>
    <body>
        <h2 style="border-bottom: 2px solid black;">REPORTE LOGÍSTICO - {datetime.now().strftime('%d/%m/%Y')}</h2>
        <p>MES: {mes_sel} | FLETERA: {flet_sel}</p>
        <div class="grid-print">
            <div class="card-p"><b>COSTO FLETE</b><br>${total_flete_2026:,.2f}</div>
            <div class="card-p"><b>FACTURACIÓN</b><br>${total_fact_2026:,.2f}</div>
            <div class="card-p"><b>CAJAS</b><br>{total_cajas_2026:,.0f}</div>
            <div class="card-p"><b>LOGÍSTICO</b><br>{costo_log_real:.2f}%</div>
            <div class="card-p"><b>COSTO X CAJA</b><br>${costo_caja_2026:,.2f}</div>
            <div class="card-p"><b>VALUACIÓN</b><br>${total_valuacion_2026:,.2f}</div>
            <div class="card-p"><b>% INCID.</b><br>{pct_inc:.1f}%</div>
            <div class="card-p"><b>INC + VI</b><br>${inc_vi_monto:,.2f}</div>
        </div>
        <div style="border: 1px solid black; padding: 15px; background: #f0f0f0;">
            <strong>DICTAMEN:</strong> Operación {status_target} del target. 
            Eficiencia: {status_eficiencia} ({var_costo_caja:+.1f}%).
        </div>
    </body>
    </html>
    """

    st.markdown("---")
    if st.button("🖨️ GENERAR REPORTE PARA IMPRESIÓN"):
        # El height=1 hace que no estorbe visualmente pero que el navegador lo dispare
        components.html(f"{reporte_impresion}<script>window.print();</script>", height=1)

except Exception as e:
    st.error(f"¡Atención, amor! Detalle: {e}")

























































































































































