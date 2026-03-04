import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components
from datetime import datetime

# 1. CONFIGURACIÓN Y ESTILO EN PANTALLA
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1014; }
    [data-testid="stMetric"] { 
        background-color: #162129; padding: 25px; border-radius: 12px; border-left: 5px solid #FFCC00; 
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF; font-weight: 900; }
    div[data-testid="stMetricLabel"] { color: #FFCC00; font-weight: bold; }
    .analysis-box { background-color: #162129; padding: 25px; border-radius: 12px; color: #A4B9C8; }
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

# 2. CARGA Y PROCESAMIENTO (LOGICA ORIGINAL SIN TOCAR)
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

    # 3. INTERFAZ Y FILTROS
    st.title("📦 NEXION LOGISTICS | JYPESA EXECUTIVE")
    c_f1, c_f2 = st.columns(2)
    with c_f1: mes_sel = st.selectbox("📅 MES:", ["TODOS"] + sorted(df_gastos['MES'].unique().tolist()))
    with c_f2: flet_sel = st.selectbox("🚛 FLETERA:", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))

    df_filtered = df_gastos.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]

    # 4. CÁLCULOS ORIGINALES (PRESERVADOS TODOS)
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

    # 5. RENDERIZADO EN PANTALLA
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

    # 6. COMPONENTE HTML PARA IMPRESIÓN (LAS 8 TARJETAS TÉCNICAS)
    status_target = "🟢 DENTRO" if costo_log_real <= 7.5 else "🔴 FUERA"
    status_eficiencia = "MÁS EFICIENTE" if var_costo_caja <= 0 else "MENOS EFICIENTE"

    reporte_tecnico_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @media print {{ .no-print {{ display: none !important; }} }}
            body {{ font-family: 'Courier New', monospace; background: white; color: black; padding: 10px; }}
            .header {{ border-bottom: 4px solid black; margin-bottom: 20px; padding-bottom: 10px; }}
            .grid-container {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .card {{ border: 1px solid black; padding: 10px; position: relative; }}
            .card-label {{ font-size: 10px; font-weight: bold; text-transform: uppercase; border-bottom: 1px solid #ccc; margin-bottom: 5px; display: block; }}
            .card-value {{ font-size: 18px; font-weight: bold; display: block; }}
            .card-delta {{ font-size: 10px; color: #333; margin-top: 5px; display: block; font-style: italic; }}
            .analysis-section {{ border: 2px solid black; padding: 15px; background: #f9f9f9; font-size: 13px; line-height: 1.6; }}
            .footer {{ margin-top: 40px; border-top: 1px dashed black; padding-top: 10px; font-size: 10px; }}
            .print-button {{ background: #FFCC00; color: black; border: none; padding: 15px; width: 100%; font-weight: bold; cursor: pointer; text-transform: uppercase; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div style="font-size: 20px; font-weight: bold;">NEXION JYPESA | REPORTE TÉCNICO LOGÍSTICO</div>
            <div style="font-size: 12px;">EMISIÓN: {datetime.now().strftime('%Y-%m-%d %H:%M')} | MES: {mes_sel} | FLETERA: {flet_sel}</div>
        </div>

        <div class="grid-container">
            <div class="card"><span class="card-label">Costo de Flete</span><span class="card-value">${total_flete_2026:,.2f}</span><span class="card-delta">Var: {((total_flete_2026-total_flete_2025)/total_flete_2025*100 if total_flete_2025>0 else 0):.1f}% vs 2025</span></div>
            <div class="card"><span class="card-label">Facturación</span><span class="card-value">${total_fact_2026:,.2f}</span></div>
            <div class="card"><span class="card-label">Cajas Enviadas</span><span class="card-value">{total_cajas_2026:,.0f}</span><span class="card-delta">Vol: {var_volumen:.1f}%</span></div>
            <div class="card"><span class="card-label">Costo Logístico</span><span class="card-value">{costo_log_real:.2f}%</span><span class="card-delta">Delta: {diferencia_target:+.2f}% vs Target</span></div>
            
            <div class="card"><span class="card-label">Costo por Caja</span><span class="card-value">${costo_caja_2026:,.2f}</span><span class="card-delta">Var: {var_costo_caja:.1f}% vs 2025</span></div>
            <div class="card"><span class="card-label">Valuación Incidencias</span><span class="card-value">${total_valuacion_2026:,.2f}</span></div>
            <div class="card"><span class="card-label">% de Incidencias</span><span class="card-value">{pct_inc:.1f}%</span></div>
            <div class="card"><span class="card-label">Incremento + VI</span><span class="card-value">${inc_vi_monto:,.2f}</span></div>
        </div>

        <div class="analysis-section">
            <strong>DICTAMEN TÉCNICO:</strong><br>
            La operación se registra actualmente <strong>{status_target}</strong> del target logístico (7.5%), 
            presentando un costo real del {costo_log_real:.2f}% sobre facturación. 
            El rendimiento unitario se clasifica como <strong>{status_eficiencia}</strong> con una variación del {var_costo_caja:+.1f}% en el costo por caja.
        </div>

        <div class="footer">
            ESTE DOCUMENTO ES UNA REPRESENTACIÓN TÉCNICA DE DATOS PARA AUDITORÍA INTERNA. NEXION LOGISTICS SYSTEM.
        </div>

        <button class="no-print print-button" onclick="window.print()">🖨️ Generar Reporte de Ingeniería (Imprimir)</button>
    </body>
    </html>
    """

    st.markdown("---")
    components.html(reporte_tecnico_html, height=550, scrolling=True)

except Exception as e:
    st.error(f"¡Atención, amor! Detalle en el código: {e}")






















































































































































