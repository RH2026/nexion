import streamlit as st
import pandas as pd
import unicodedata

# 1. CONFIGURACIÓN Y ESTILO ONYX (EL RENDER CHINGÓN)
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1014; }
    .stMetric { background-color: #162129; padding: 20px; border-radius: 12px; border: 1px solid #243441; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    div[data-testid="stMetricValue"] { color: #A4B9C8; font-weight: bold; font-size: 1.8rem; }
    div[data-testid="stMetricLabel"] { color: #5F7E97; letter-spacing: 1px; text-transform: uppercase; font-size: 0.75rem; }
    .stDataFrame { border: 1px solid #243441; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_columnas(txt):
    if not isinstance(txt, str): return txt
    texto = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

# 2. CARGA Y PROCESAMIENTO CRUZADO
try:
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]

    # --- FILTRO CRÍTICO: SOLO COBRO REGRESO DESDE "FORMA DE ENVIO" ---
    # Nota: Usamos FORMA DE ENVIO (sin acento por la limpieza)
    df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('COBRO REGRESO', na=False, case=False)].copy()
    
    # Vinculamos con Historial 2025 por MES
    df_2025_ref = df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'GUIA_2025'})
    df_final = pd.merge(df_gastos, df_2025_ref, on='MES', how='left')

    # --- CÁLCULOS DE LOS RESULTADOS QUE PEDISTE ---
    df_final['COSTOS ADICIONALES'] = df_final.get('COSTOS ADICIONALES', 0).fillna(0)
    df_final['VALUACION'] = df_final.get('VALUACION', 0).fillna(0)
    
    # 1. COSTO DE FLETE
    df_final['COSTO DE FLETE'] = df_final['COSTO DE LA GUIA'] + df_final['COSTOS ADICIONALES']
    
    # 2. COSTO LOGÍSTICO
    df_final['COSTO LOGISTICO'] = (df_final['COSTO DE FLETE'] / df_final['FACTURACION']) * 100
    
    # 3. COSTO POR CAJA
    df_final['COSTO POR CAJA'] = df_final['COSTO DE FLETE'] / df_final['CAJAS']
    
    # 4. INCREMENTO + VI (Costo Flete + Valuación Incidencias vs Guía 2025)
    df_final['INCREMENTO_VI'] = (df_final['COSTO DE FLETE'] + df_final['VALUACION']) - df_final['GUIA_2025']
    
    # 5. % DE INCREMENTO VS 2025
    df_final['% INCREMENTO VS 2025'] = ((df_final['COSTO DE FLETE'] - df_final['GUIA_2025']) / df_final['GUIA_2025']) * 100

    # 3. INTERFAZ DE FILTROS
    st.title("🌌 NEXION LOGISTICS | JYPESA")
    st.markdown("### Análisis Cruzado de Costos e Incidencias")
    
    c_f1, c_f2, c_f3 = st.columns([1, 1, 2])
    with c_f1:
        mes_sel = st.selectbox("📅 Seleccionar Mes:", ["TODOS"] + sorted(df_final['MES'].unique().tolist()))
    with c_f2:
        flet_sel = st.selectbox("🚛 Seleccionar Fletera:", ["TODAS"] + sorted(df_final['FLETERA'].unique().tolist()))
    with c_f3:
        search = st.text_input("🔍 Buscar Cliente o Factura:", "")

    # Aplicar Filtros
    df_filtered = df_final.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
    if search:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    # 4. RENDERIZADO DE RESULTADOS (KPIs)
    st.markdown("---")
    
    # Fila 1 de Métricas
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("COSTO DE FLETE", f"${df_filtered['COSTO DE FLETE'].sum():,.2f}")
    with k2:
        st.metric("FACTURACIÓN", f"${df_filtered['FACTURACION'].sum():,.2f}")
    with k3:
        st.metric("CAJAS ENVIADAS", f"{df_filtered['CAJAS'].sum():,.0f}")
    with k4:
        st.metric("COSTO LOGÍSTICO", f"{df_filtered['COSTO LOGISTICO'].mean():,.2f}%")

    # Fila 2 de Métricas
    k5, k6, k7, k8 = st.columns(4)
    with k5:
        st.metric("COSTO POR CAJA", f"${df_filtered['COSTO POR CAJA'].mean():,.2f}")
    with k6:
        val_inc = df_filtered['VALUACION'].sum()
        st.metric("VALUACIÓN INCIDENCIAS", f"${val_inc:,.2f}")
    with k7:
        # % de Incidencias: (Envíos con valuación > 0 / Total de envíos) * 100
        total_envios = len(df_filtered)
        envios_con_inc = (df_filtered['VALUACION'] > 0).sum()
        perc_inc = (envios_con_inc / total_envios * 100) if total_envios > 0 else 0
        st.metric("% DE INCIDENCIAS", f"{perc_inc:.1f}%")
    with k8:
        inc_total = df_filtered['INCREMENTO_VI'].sum()
        avg_perc_25 = df_filtered['% INCREMENTO VS 2025'].mean()
        st.metric("INCREMENTO + VI", f"${inc_total:,.2f}", delta=f"{avg_perc_25:.1f}% vs 2025")

    # 5. TABLA DETALLADA
    st.markdown("---")
    st.subheader("📊 Detalle de Matriz Nexion")
    
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
        use_container_width=True, height=450
    )

except Exception as e:
    st.error(f"¡Atención, amor! Revisa las columnas de tus archivos. Error: {e}")
    st.info("Asegúrate que la columna se llame 'FORMA DE ENVÍO' en tu Excel.")


















































































































