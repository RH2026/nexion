import streamlit as st
import pandas as pd
import unicodedata

# 1. CONFIGURACIÓN Y ESTILO ONYX
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1014; }
    .stMetric { background-color: #162129; padding: 15px; border-radius: 10px; border: 1px solid #243441; }
    div[data-testid="stMetricValue"] { color: #A4B9C8; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #5F7E97; }
    .stDataFrame { border: 1px solid #243441; }
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

    # --- FILTRO CRÍTICO: SOLO COBRO REGRESO PARA GASTOS ---
    # Creamos una copia para cálculos financieros donde omitimos Cobro Destino
    df_gastos = df_actual[df_actual['CLASE DE ENTREGA'].str.contains('REGRESO', na=False, case=False)].copy()
    
    # Vinculamos con Historial 2025
    df_2025_ref = df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'GUIA_2025'})
    df_final = pd.merge(df_gastos, df_2025_ref, on='MES', how='left')

    # --- CÁLCULOS FINANCIEROS ---
    df_final['COSTOS ADICIONALES'] = df_final.get('COSTOS ADICIONALES', 0).fillna(0)
    df_final['VALUACION'] = df_final.get('VALUACION', 0).fillna(0)
    
    # Costo Flete Real (Solo Cobro Regreso)
    df_final['COSTO DE FLETE'] = df_final['COSTO DE LA GUIA'] + df_final['COSTOS ADICIONALES']
    
    # Indicadores
    df_final['COSTO LOGISTICO'] = (df_final['COSTO DE FLETE'] / df_final['FACTURACION']) * 100
    df_final['COSTO POR CAJA'] = df_final['COSTO DE FLETE'] / df_final['CAJAS']
    
    # Incrementos (Costo Flete Actual + Valuación de Incidencias vs 2025)
    df_final['INCREMENTO_VI'] = (df_final['COSTO DE FLETE'] + df_final['VALUACION']) - df_final['GUIA_2025']
    df_final['% INCREMENTO VS 2025'] = ((df_final['COSTO DE FLETE'] - df_final['GUIA_2025']) / df_final['GUIA_2025']) * 100

    # 3. INTERFAZ DE FILTROS (IN-BODY)
    st.title("🌌 NEXION LOGISTICS | JYPESA")
    st.subheader("Filtros de Análisis")
    
    c_f1, c_f2, c_f3 = st.columns([1, 1, 2])
    with c_f1:
        mes_sel = st.selectbox("📅 Mes:", ["TODOS"] + sorted(df_final['MES'].unique().tolist()))
    with c_f2:
        flet_sel = st.selectbox("🚛 Fletera:", ["TODAS"] + sorted(df_final['FLETERA'].unique().tolist()))
    with c_f3:
        search = st.text_input("🔍 Buscar Cliente/Guía:", "")

    # Aplicar Filtros
    df_filtered = df_final.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
    if search:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    # 4. RENDERIZADO DE MÉTRICAS (LO QUE NECESITAS VER)
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        total_flete = df_filtered['COSTO DE FLETE'].sum()
        st.metric("COSTO FLETE (REGRESO)", f"${total_flete:,.2f}")
    
    with kpi2:
        inc_vi = df_filtered['INCREMENTO_VI'].sum()
        st.metric("INCREMENTO + VI", f"${inc_vi:,.2f}", delta=f"{df_filtered['% INCREMENTO VS 2025'].mean():.1f}% vs 2025")
        
    with kpi3:
        total_incidencias = df_filtered['VALUACION'].sum()
        # Calculamos % de incidencias basado en conteo
        num_inc = len(df_filtered[df_filtered['VALUACION'] > 0])
        st.metric("VALUACIÓN INCIDENCIAS", f"${total_incidencias:,.2f}", f"{num_inc} reportes")
        
    with kpi4:
        c_log = df_filtered['COSTO LOGISTICO'].mean()
        st.metric("% COSTO LOGÍSTICO", f"{c_log:.2f}%")

    # 5. TABLA PRINCIPAL
    st.markdown("### 📊 Detalle de Operaciones (Filtrado)")
    
    st.dataframe(
        df_filtered.style.format({
            'COSTO DE LA GUIA': '${:,.2f}',
            'COSTO DE FLETE': '${:,.2f}',
            'FACTURACION': '${:,.2f}',
            'VALUACION': '${:,.2f}',
            'COSTO LOGISTICO': '{:.2f}%',
            '% INCREMENTO VS 2025': '{:.2f}%'
        }).background_gradient(cmap='YlOrRd', subset=['COSTO LOGISTICO']), 
        use_container_width=True, height=400
    )

    # 6. RESUMEN DE INCIDENCIAS
    if total_incidencias > 0:
        st.warning(f"🚨 Atención: Se han detectado {num_inc} incidencias que suman ${total_incidencias:,.2f} en pérdidas.")

except Exception as e:
    st.error(f"¡Algo anda mal con las columnas, amor! Error: {e}")
    st.info("Revisa que la columna 'CLASE DE ENTREGA' tenga los valores 'COBRO REGRESO'.")

















































































































