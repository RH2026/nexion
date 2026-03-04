import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN Y ESTILO "NEXION PRO + REPORT"
st.set_page_config(page_title="Nexion JYPESA - Executive Report", layout="wide")

st.markdown("""
    <style>
    /* ESTILO EN PANTALLA (Mantenemos tu Onyx DHL amado) */
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

    /* --- DISEÑO DE IMPRESIÓN "PRO INGENIERÍA" (FORMA DE MATRIZ) --- */
    @media print {
        @page { size: portrait; margin: 1cm; }
        header, [data-testid="stSidebar"], .stSelectbox, .stButton, .no-print, iframe, hr { display: none !important; }
        
        /* 1. Reset Total: Hoja Blanca, Texto Negro */
        .main, .stApp { background-color: white !important; color: black !important; }
        
        /* 2. Ocultar métricas web al imprimir */
        [data-testid="stMetric"], .analysis-box { display: none !important; }
        
        /* 3. Título de Reporte */
        h1 { color: black !important; border-bottom: 4px solid black !important; font-size: 1.8rem !important; }
        h3 { color: black !important; margin-top: 20px !important; font-size: 1.2rem !important; }
        .highlight { color: black !important; font-weight: bold; }

        /* 4. Estilo de la Matriz Técnica (La Magia) */
        .tech-matrix {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-family: 'Courier New', monospace; /* Tipografía técnica amor */
            font-size: 0.9rem;
        }
        .tech-matrix th {
            background-color: #f2f2f2 !important;
            color: black !important;
            text-align: left;
            padding: 10px;
            border: 1px solid black;
        }
        .tech-matrix td {
            padding: 10px;
            border: 1px solid black;
            color: black !important;
        }
        .row-total { background-color: #f2f2f2 !important; font-weight: bold; }
        .visible-print { display: block !important; }
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

    # 3. INTERFAZ (TÍTULO Y FILTROS)
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

    # 5. RENDERIZADO WEB (TUS KPIs AMADOS)
    st.markdown("### 📊 RESUMEN EJECUTIVO DE RENDIMIENTO")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}")
    with k2: st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}")
    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%")

    k5, k6, k7, k8 = st.columns(4)
    with k5: st.metric("COSTO POR CAJA", f"${costo_caja_2026:,.2f}")
    with k6: st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion_2026:,.2f}")
    with k7: st.metric("% DE INCIDENCIAS", f"{( (df_filtered['VALUACION']>0).sum()/len(df_filtered)*100 if len(df_filtered)>0 else 0):.1f}%")
    with k8: st.metric("INCREMENTO + VI", f"${(total_flete_2026 + total_valuacion_2026) - total_flete_2025:,.2f}")

    # 6. ANÁLISIS DINÁMICO
    st.markdown("### 🔍 ANÁLISIS DINÁMICO DE OPERACIÓN")
    status_target = "🟢 DENTRO" if costo_log_real <= 7.5 else "🔴 FUERA"
    status_eficiencia = "MÁS EFICIENTE" if var_costo_caja <= 0 else "MENOS EFICIENTE"
    
    html_final = f'<div class="analysis-box"><b>Cumplimiento de Objetivos:</b> Actualmente la operación se encuentra <span class="highlight">{status_target}</span> del target logístico (7.5%), con un costo real del <span class="highlight">{costo_log_real:.2f}%</span> sobre la facturación bruta. <br><br><b>Análisis de Rendimiento Unitario:</b> El costo por caja ha variado un <span class="highlight">{var_costo_caja:+.1f}%</span> respecto al año pasado. Esto indica que operativamente hoy somos <span class="highlight">{status_eficiencia}</span> en la consolidación y despacho de mercancía de JYPESA.</div>'
    st.markdown(html_final, unsafe_allow_html=True)

    # --- 7. MATRIZ TÉCNICA SENIOR (SOLO PARA IMPRESIÓN) ---
    st.markdown(f"""
    <div style="display:none;" class="visible-print">
        <h3>📄 MATRIZ DE RESUMEN TÉCNICO | INGENIERÍA DE COSTOS</h3>
        <table class="tech-matrix">
            <thead>
                <tr>
                    <th>INDICADOR OPERATIVO</th>
                    <th>PERIODO_ACTUAL (2026)</th>
                    <th>PERIODO_REFERENCIA (2025)</th>
                    <th>VARIACIÓN_ABS</th>
                    <th>VARIACIÓN_REL (%)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Gasto Total de Flete (Neto)</td>
                    <td>${total_flete_2026:,.2f}</td>
                    <td>${total_flete_2025:,.2f}</td>
                    <td>${total_flete_2026 - total_flete_2025:,.2f}</td>
                    <td>{((total_flete_2026 - total_flete_2025)/total_flete_2025*100 if total_flete_2025>0 else 0):.2f}%</td>
                </tr>
                <tr>
                    <td>Volumen Despachado (Unidades)</td>
                    <td>{total_cajas_2026:,.0f}</td>
                    <td>{total_cajas_2025:,.0f}</td>
                    <td>{total_cajas_2026 - total_cajas_2025:,.0f}</td>
                    <td>{var_volumen:.2f}%</td>
                </tr>
                <tr>
                    <td>Costo Unitario de Flete (PER_UNIT)</td>
                    <td>${costo_caja_2026:,.2f}</td>
                    <td>${costo_caja_2025:,.2f}</td>
                    <td>${costo_caja_2026 - costo_caja_2025:,.2f}</td>
                    <td>{var_costo_caja:.2f}%</td>
                </tr>
                <tr class="row-total">
                    <td>Costo Logístico vs Ingresos (Target 7.5%)</td>
                    <td colspan="2">{costo_log_real:.2f}%</td>
                    <td>{costo_log_real - 7.5:+.2f} pts</td>
                    <td>TARGET_REF</td>
                </tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # 8. BOTÓN DE IMPRESIÓN PRO
    st.markdown("---")
    components.html("""
        <button style="background-color: #FFCC00; color: #0B1014; border: none; padding: 15px 30px; font-family: 'Arial Black', sans-serif; font-size: 16px; border-radius: 8px; cursor: pointer; width: 100%;" 
        onclick="window.parent.print()">🖨️ GENERAR REPORTE EJECUTIVO TÉCNICO (IMPRIMIR)</button>
    """, height=80)

except Exception as e:
    st.error(f"¡Atención, amor! Hubo un detalle: {e}")














































































































































