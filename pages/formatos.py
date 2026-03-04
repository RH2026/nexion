import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN Y ESTILO "NEXION PRO + REPORT"
st.set_page_config(page_title="Nexion JYPESA - Executive Report", layout="wide")

st.markdown("""
    <style>
    /* --- ESTILO EN PANTALLA (ONYX DHL) --- */
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
    div[data-testid="stMetricValue"] { color: #FFFFFF; font-weight: 900; font-size: 2.2rem; }
    div[data-testid="stMetricLabel"] { color: #FFCC00; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.8rem; font-weight: bold; }
    h1 { color: #FFFFFF; font-family: 'Arial Black'; border-bottom: 2px solid #FFCC00; padding-bottom: 10px; }
    
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

    /* --- DISEÑO DE IMPRESIÓN "PRO INGENIERÍA" (LA CLAVE) --- */
    @media print {
        /* 1. Borramos TODO lo que huela a página web */
        header, footer, [data-testid="stSidebar"], .stSelectbox, .stButton, 
        .no-print, iframe, hr, [data-testid="stMetric"], .analysis-box, .stMarkdown { 
            display: none !important; 
        }

        /* 2. Forzamos fondo blanco y mostramos SOLO la matriz técnica */
        .main, .stApp { background-color: white !important; color: black !important; }
        
        .visible-print { 
            display: block !important; 
            width: 100% !important;
        }

        /* 3. Estilo de Hoja de Ingeniería */
        .print-header {
            border-bottom: 3px solid black;
            margin-bottom: 30px;
            padding-bottom: 10px;
        }
        .tech-matrix {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Courier New', Courier, monospace;
            font-size: 10pt;
        }
        .tech-matrix th {
            background-color: #E0E0E0 !important;
            border: 1px solid black;
            padding: 12px;
            text-align: left;
            -webkit-print-color-adjust: exact;
        }
        .tech-matrix td {
            border: 1px solid black;
            padding: 10px;
            color: black !important;
        }
        .footer-print {
            margin-top: 50px;
            font-size: 8pt;
            text-align: right;
            border-top: 1px solid #CCC;
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

    # 3. INTERFAZ WEB
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
    var_volumen = ((total_cajas_2026 - total_cajas_2025) / total_cajas_2025 * 100) if total_cajas_2025 > 0 else 0
    var_costo_caja = ((costo_caja_2026 - costo_caja_2025) / costo_caja_2025 * 100) if costo_caja_2025 > 0 else 0
    costo_log_real = (total_flete_2026/total_fact_2026*100) if total_fact_2026 > 0 else 0

    # 5. RENDERIZADO WEB
    st.markdown("### 📊 RESUMEN EJECUTIVO")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}")
    with k2: st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}")
    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%")

    # 6. ANÁLISIS DINÁMICO WEB
    status_target = "🟢 DENTRO" if costo_log_real <= 7.5 else "🔴 FUERA"
    status_eficiencia = "MÁS EFICIENTE" if var_costo_caja <= 0 else "MENOS EFICIENTE"
    html_final = f'<div class="analysis-box"><b>Cumplimiento:</b> {status_target} (Target 7.5%). <br><b>Rendimiento:</b> Hoy somos {status_eficiencia} en consolidación.</div>'
    st.markdown(html_final, unsafe_allow_html=True)

    # --- 7. REPORTE TÉCNICO (HIDDEN EN WEB, VISIBLE EN IMPRESIÓN) ---
    # Esto es lo que se imprimirá, ignorando todo lo demás
    st.markdown(f"""
    <div style="display:none;" class="visible-print">
        <div class="print-header">
            <h1 style="color:black;">JYPESA | LOGISTICS ENGINEERING REPORT</h1>
            <p><b>PERIODO ANALIZADO:</b> {mes_sel} 2026 | <b>OPERADOR:</b> JYPESA LOGISTICS DEPT.</p>
        </div>
        
        <table class="tech-matrix">
            <thead>
                <tr>
                    <th>KPI - INDICADOR TÉCNICO</th>
                    <th>ACTUAL (2026)</th>
                    <th>ANTERIOR (2025)</th>
                    <th>VAR. ABSOLUTA</th>
                    <th>VAR. (%)</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Inversión Total en Fletes</td><td>${total_flete_2026:,.2f}</td><td>${total_flete_2025:,.2f}</td><td>${total_flete_2026 - total_flete_2025:,.2f}</td><td>{((total_flete_2026-total_flete_2025)/total_flete_2025*100):.2f}%</td></tr>
                <tr><td>Volumen Despachado (Cajas)</td><td>{total_cajas_2026:,.0f}</td><td>{total_cajas_2025:,.0f}</td><td>{total_cajas_2026 - total_cajas_2025:,.0f}</td><td>{var_volumen:.2f}%</td></tr>
                <tr><td>Costo de Flete por Caja</td><td>${costo_caja_2026:,.2f}</td><td>${costo_caja_2025:,.2f}</td><td>${costo_caja_2026 - costo_caja_2025:,.2f}</td><td>{var_costo_caja:.2f}%</td></tr>
                <tr><td>Ratio Logístico / Ventas</td><td>{costo_log_real:.2f}%</td><td>Target: 7.5%</td><td>{costo_log_real - 7.5:+.2f} pts</td><td>ESTADO: {status_target}</td></tr>
            </tbody>
        </table>

        <div style="margin-top:30px; border: 1px solid black; padding: 15px;">
            <p><b>NOTAS TÉCNICAS:</b> Análisis de variación basado en el flete acumulado del periodo. El ratio logístico refleja la eficiencia directa sobre la facturación bruta. Se recomienda vigilar la consolidación para optimizar el costo unitario por caja.</p>
        </div>
        
        <div class="footer-print">Generado por NEXION JYPESA Dashboard | 2026</div>
    </div>
    """, unsafe_allow_html=True)

    # 8. BOTÓN DE IMPRESIÓN PRO
    st.markdown("---")
    components.html("""
        <button style="background-color: #FFCC00; color: #0B1014; border: none; padding: 15px 30px; font-family: 'Arial Black', sans-serif; font-size: 16px; border-radius: 8px; cursor: pointer; width: 100%;" 
        onclick="window.parent.print()">🖨️ GENERAR REPORTE OFICIAL (IMPRIMIR)</button>
    """, height=80)

except Exception as e:
    st.error(f"SYSTEM_ERROR: {e}")















































































































































