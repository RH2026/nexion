import streamlit as st
import pandas as pd
import unicodedata

# 1. CONFIGURACIÓN Y ESTILO ONYX
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1014; }
    .stMetric { background-color: #162129; padding: 20px; border-radius: 12px; border: 1px solid #243441; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    div[data-testid="stMetricValue"] { color: #A4B9C8; font-weight: bold; font-size: 2rem; }
    div[data-testid="stMetricLabel"] { color: #5F7E97; letter-spacing: 1px; text-transform: uppercase; font-size: 0.8rem; }
    .stDataFrame { border: 1px solid #243441; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_columnas(txt):
    if not isinstance(txt, str): return txt
    texto = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

# 2. CARGA Y PROCESAMIENTO
try:
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]

    # --- FILTRO CRÍTICO: FILTRAR POR LA COLUMNA TRANSPORTE ---
    # Solo tomamos lo que JYPESA paga (COBRO REGRESO)
    df_gastos = df_actual[df_actual['TRANSPORTE'].str.contains('REGRESO', na=False, case=False)].copy()
    
    # Vinculamos con Historial 2025
    df_2025_ref = df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'GUIA_2025'})
    df_final = pd.merge(df_gastos, df_2025_ref, on='MES', how='left')

    # --- CÁLCULOS FINANCIEROS COMPLETOS ---
    df_final['COSTOS ADICIONALES'] = df_final.get('COSTOS ADICIONALES', 0).fillna(0)
    df_final['VALUACION'] = df_final.get('VALUACION', 0).fillna(0)
    
    # Costo Flete Real
    df_final['COSTO DE FLETE'] = df_final['COSTO DE LA GUIA'] + df_final['COSTOS ADICIONALES']
    
    # Indicadores Solicitados
    df_final['COSTO LOGISTICO'] = (df_final['COSTO DE FLETE'] / df_final['FACTURACION']) * 100
    df_final['COSTO POR CAJA'] = df_final['COSTO DE FLETE'] / df_final['CAJAS']
    
    # Incremento vs 2025 considerando la Valuación de Incidencias (VI)
    df_final['INCREMENTO_VI'] = (df_final['COSTO DE FLETE'] + df_final['VALUACION']) - df_final['GUIA_2025']
    df_final['% INCREMENTO VS 2025'] = ((df_final['COSTO DE FLETE'] - df_final['GUIA_2025']) / df_final['GUIA_2025']) * 100

    # 3. INTERFAZ DE FILTROS EN EL CUERPO
    st.title("🌌 NEXION LOGISTICS | JYPESA")
    st.markdown("### Control de Operaciones y Costos")
    
    c_f1, c_f2, c_f3 = st.columns([1, 1, 2])
    with c_f1:
        mes_sel = st.selectbox("📅 Seleccionar Mes:", ["TODOS"] + sorted(df_final['MES'].unique().tolist()))
    with c_f2:
        flet_sel = st.selectbox("🚛 Seleccionar Fletera:", ["TODAS"] + sorted(df_final['FLETERA'].unique().tolist()))
    with c_f3:
        search = st.text_input("🔍 Búsqueda rápida (Cliente, Guía, Factura):", "")

    # Aplicar Filtros Dinámicos
    df_filtered = df_final.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
    if search:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    # 4. RENDERIZADO DE MÉTRICAS (KPIs)
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        total_flete = df_filtered['COSTO DE FLETE'].sum()
        st.metric("COSTO FLETE TOTAL", f"${total_flete:,.2f}")
    
    with kpi2:
        inc_vi_total = df_filtered['INCREMENTO_VI'].sum()
        avg_perc = df_filtered['% INCREMENTO VS 2025'].mean()
        st.metric("INCREMENTO + VI", f"${inc_vi_total:,.2f}", delta=f"{avg_perc:.1f}% vs 2025")
        
    with kpi3:
        total_valuacion = df_filtered['VALUACION'].sum()
        num_incidencias = (df_filtered['VALUACION'] > 0).sum()
        st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion:,.2f}", f"{num_incidencias} Eventos")
        
    with kpi4:
        c_log_prom = df_filtered['COSTO LOGISTICO'].mean()
        st.metric("% COSTO LOGÍSTICO", f"{c_log_prom:.2f}%")

    # 5. TABLA DE DATOS CHINGONA
    st.markdown("### 📊 Detalle de Matriz de Datos")
    
    st.dataframe(
        df_filtered.style.format({
            'COSTO DE LA GUIA': '${:,.2f}',
            'COSTO DE FLETE': '${:,.2f}',
            'FACTURACION': '${:,.2f}',
            'VALUACION': '${:,.2f}',
            'COSTO LOGISTICO': '{:.2f}%',
            'COSTO POR CAJA': '${:,.2f}',
            '% INCREMENTO VS 2025': '{:.2f}%'
        }).background_gradient(cmap='Blues', subset=['COSTO LOGISTICO']), 
        use_container_width=True, height=500
    )

    # 6. ALERTAS DE COSTO
    if total_valuacion > (total_flete * 0.1): # Alerta si la valuación supera el 10% del flete
        st.error(f"⚠️ Alerta: Las incidencias representan un alto porcentaje del costo este mes (${total_valuacion:,.2f})")

except Exception as e:
    st.error(f"Error en la matriz, amor. Revisa que las columnas coincidan. Detalle: {e}")


















































































































