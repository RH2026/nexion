import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components
from datetime import datetime

# 1. CONFIGURACIÓN Y ESTILO "NEXION PRO + ENGINEERING PRINT"
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

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
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF; font-weight: 900; }
    div[data-testid="stMetricLabel"] { color: #FFCC00; font-weight: bold; }
    h1 { color: #FFFFFF; font-family: 'Arial Black'; border-bottom: 2px solid #FFCC00; }
    
    .analysis-box {
        background-color: #162129;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #243441;
        color: #A4B9C8;
    }
    .highlight { color: #FFCC00; font-weight: bold; }

    /* --- DISEÑO DE IMPRESIÓN NIVEL INGENIERÍA --- */
    @media print {
        @page { size: letter portrait; margin: 1cm; }
        
        /* Ocultar elementos web innecesarios */
        header, [data-testid="stSidebar"], .stSelectbox, .stButton, footer, iframe, hr, .no-print {
            display: none !important;
        }

        .stApp { background-color: white !important; color: black !important; }
        
        /* Contenedor Principal de Impresión */
        .print-container {
            display: block !important;
            font-family: "Helvetica", "Arial", sans-serif !important;
        }

        /* Encabezado Técnico */
        .print-header {
            border-bottom: 3px solid #000;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding-bottom: 5px;
        }
        .print-header h1 { 
            color: black !important; 
            margin: 0; 
            font-size: 22pt !important;
            border: none !important;
        }
        .print-meta { text-align: right; font-size: 9pt; color: #555; }

        /* Cuadrícula de KPIs Tipo Formulario */
        .print-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0;
            border: 1px solid black;
            margin-bottom: 20px;
        }
        .print-kpi-item {
            border: 0.5px solid #ccc;
            padding: 10px;
            display: flex;
            flex-direction: column;
        }
        .print-kpi-label { 
            font-size: 8pt; 
            text-transform: uppercase; 
            color: #444; 
            font-weight: bold;
        }
        .print-kpi-value { 
            font-size: 14pt; 
            font-family: "Courier New", monospace; 
            font-weight: bold; 
        }

        /* Bloque de Análisis Técnico */
        .print-analysis {
            border: 1px solid black;
            background-color: #f2f2f2 !important;
            padding: 15px;
            font-size: 10pt;
            line-height: 1.5;
            margin-bottom: 20px;
        }
        
        /* Tabla de Datos Maestra */
        .print-table { 
            width: 100%; 
            border-collapse: collapse; 
            font-size: 9pt;
        }
        .print-table th { 
            background-color: #000 !important; 
            color: white !important; 
            text-align: left; 
            padding: 8px;
            border: 1px solid black;
        }
        .print-table td { 
            border: 1px solid black; 
            padding: 6px; 
        }
        .print-table tr:nth-child(even) { background-color: #f9f9f9 !important; }
        
        /* Forzar visibilidad de elementos de impresión */
        .visible-print { display: block !important; }
    }
    
    /* Ocultar el layout de impresión en la web */
    .visible-print { display: none; }
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

# 2. CARGA Y PROCESAMIENTO (Tu lógica original intacta)
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

    # 3. INTERFAZ EN PANTALLA
    st.title("📦 NEXION LOGISTICS | JYPESA EXECUTIVE")
    
    c_f1, c_f2 = st.columns(2)
    with c_f1: mes_sel = st.selectbox("📅 FILTRAR POR MES:", ["TODOS"] + sorted(df_gastos['MES'].unique().tolist()))
    with c_f2: flet_sel = st.selectbox("🚛 FILTRAR POR FLETERA:", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))

    df_filtered = df_gastos.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]

    # 4. CÁLCULOS (Tu lógica original intacta)
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

    # --- FILA 1: KPIs PRIMARIOS ---
    st.markdown("### 📊 RESUMEN OPERATIVO")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}")
    with k2: st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}")
    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%")
    
    st.markdown("<br>", unsafe_allow_html=True) # Espacio entre filas
    
    # --- FILA 2: KPIs DE EFICIENCIA (LAS OTRAS 4) ---
    k5, k6, k7, k8 = st.columns(4) # ¡IMPORTANTE: Usar k5 a k8!
    with k5: st.metric("COSTO POR CAJA", f"${costo_caja_2026:,.2f}")
    with k6: st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion_2026:,.2f}")
    with k7: st.metric("% DE INCIDENCIAS", f"{( (df_filtered['VALUACION']>0).sum()/len(df_filtered)*100 if len(df_filtered)>0 else 0):.1f}%")
    with k8: st.metric("INCREMENTO + VI", f"${(total_flete_2026 + total_valuacion_2026) - total_flete_2025:,.2f}")

    status_target = "🟢 DENTRO" if costo_log_real <= 7.5 else "🔴 FUERA"
    status_eficiencia = "MÁS EFICIENTE" if var_costo_caja <= 0 else "MENOS EFICIENTE"
    
    html_analisis = f'<div class="analysis-box"><b>Estatus:</b> Operación <span class="highlight">{status_target}</span> del target. Eficiencia unitaria: <span class="highlight">{status_eficiencia}</span> ({var_costo_caja:+.1f}% vs 2025).</div>'
    st.markdown(html_analisis, unsafe_allow_html=True)

    # 6. ESTRUCTURA PARA IMPRESIÓN (Nivel Ingeniería)
    fecha_reporte = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    st.markdown(f"""
    <div class="visible-print print-container">
        <div class="print-header">
            <h1>REPORTE TÉCNICO DE LOGÍSTICA: NEXION-JYPESA</h1>
            <div class="print-meta">
                <b>FECHA EMISIÓN:</b> {fecha_reporte}<br>
                <b>FILTRO MES:</b> {mes_sel} | <b>FLETERA:</b> {flet_sel}
            </div>
        </div>

        <div class="print-grid">
            <div class="print-kpi-item"><span class="print-kpi-label">Gasto Total Flete (CY 2026)</span><span class="print-kpi-value">${total_flete_2026:,.2f}</span></div>
            <div class="print-kpi-item"><span class="print-kpi-label">Venta Bruta (Base de Cálculo)</span><span class="print-kpi-value">${total_fact_2026:,.2f}</span></div>
            <div class="print-kpi-item"><span class="print-kpi-label">Costo Logístico Real</span><span class="print-kpi-value">{costo_log_real:.2f}%</span></div>
            <div class="print-kpi-item"><span class="print-kpi-label">Desviación vs Target (7.5%)</span><span class="print-kpi-value">{diferencia_target:+.2f}%</span></div>
            <div class="print-kpi-item"><span class="print-kpi-label">Costo por Unidad (Caja)</span><span class="print-kpi-value">${costo_caja_2026:,.2f}</span></div>
            <div class="print-kpi-item"><span class="print-kpi-label">Variación vs Periodo Anterior</span><span class="print-kpi-value">{var_costo_caja:+.2f}%</span></div>
        </div>

        <div class="print-analysis">
            <strong>DICTAMEN OPERATIVO:</strong><br>
            La auditoría de costos indica que la operación se encuentra <strong>{status_target}</strong> de los parámetros establecidos. 
            El volumen de cajas registrado es de {total_cajas_2026:,.0f} unidades, representando una variación de volumen del {var_volumen:.2f}% respecto al ejercicio 2025. 
            La valuación de incidencias asciende a ${total_valuacion_2026:,.2f}.
        </div>

        <table class="print-table">
            <thead>
                <tr>
                    <th>INDICADOR TÉCNICO</th>
                    <th>EJERCICIO 2026</th>
                    <th>EJERCICIO 2025 (REF)</th>
                    <th>VARIACIÓN Δ</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Costo de Flete Neto</td><td>${total_flete_2026:,.2f}</td><td>${total_flete_2025:,.2f}</td><td>{((total_flete_2026-total_flete_2025)/total_flete_2025*100 if total_flete_2025>0 else 0):.2f}%</td></tr>
                <tr><td>Volumen Operativo (Cajas)</td><td>{total_cajas_2026:,.0f}</td><td>{total_cajas_2025:,.0f}</td><td>{var_volumen:.2f}%</td></tr>
                <tr><td>Costo Unitario por Caja</td><td>${costo_caja_2026:,.2f}</td><td>${costo_caja_2025:,.2f}</td><td>{var_costo_caja:.2f}%</td></tr>
                <tr><td>Ratio de Incidencias</td><td>{( (df_filtered['VALUACION']>0).sum()/len(df_filtered)*100 if len(df_filtered)>0 else 0):.2f}%</td><td>N/A</td><td>--</td></tr>
            </tbody>
        </table>
        
        <div style="margin-top: 50px; display: flex; justify-content: space-around;">
            <div style="border-top: 1px solid black; width: 200px; text-align: center; font-size: 8pt;">FIRMA RESPONSABLE LOGÍSTICA</div>
            <div style="border-top: 1px solid black; width: 200px; text-align: center; font-size: 8pt;">VALIDACIÓN CONTADURÍA</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 7. BOTÓN DE IMPRESIÓN (Al final)
    st.markdown("<br><br>", unsafe_allow_html=True)
    components.html("""
        <button style="
            background-color: #FFCC00; 
            color: #0B1014; 
            border: none; 
            padding: 15px 30px; 
            font-family: 'Arial Black', sans-serif; 
            font-size: 16px; 
            border-radius: 8px; 
            cursor: pointer; 
            width: 100%;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        " onclick="window.parent.print()">🖨️ GENERAR REPORTE TÉCNICO PARA IMPRESIÓN</button>
    """, height=100)

except Exception as e:
    st.error(f"Hubo un error en el procesamiento: {e}")



















































































































































