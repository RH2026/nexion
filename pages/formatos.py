import streamlit as st
import pandas as pd
import unicodedata

# 1. CONFIGURACIÓN Y ESTILO ONYX
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

# 2. CARGA Y PROCESAMIENTO
try:
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]

    # Limpieza de los datos de la columna MES para que coincidan siempre
    df_actual['MES'] = df_actual['MES'].astype(str).str.strip().str.upper()
    df_2025['MES'] = df_2025['MES'].astype(str).str.strip().str.upper()

    # --- FILTRO CRÍTICO: SOLO COBRO REGRESO ---
    df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False)].copy()
    
    # Cálculos base por fila 2026
    df_gastos['COSTOS ADICIONALES'] = df_gastos.get('COSTOS ADICIONALES', 0).fillna(0)
    df_gastos['VALUACION'] = df_gastos.get('VALUACION', 0).fillna(0)
    df_gastos['COSTO DE FLETE'] = df_gastos['COSTO DE LA GUIA'] + df_gastos['COSTOS ADICIONALES']

    # 3. INTERFAZ DE FILTROS
    st.title("🌌 NEXION LOGISTICS | JYPESA")
    
    c_f1, c_f2, c_f3 = st.columns([1, 1, 2])
    with c_f1:
        mes_sel = st.selectbox("📅 Mes:", ["TODOS"] + sorted(df_gastos['MES'].unique().tolist()))
    with c_f2:
        flet_sel = st.selectbox("🚛 Fletera:", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()))
    with c_f3:
        search = st.text_input("🔍 Buscar Cliente/Factura:", "")

    # Aplicar Filtros a 2026
    df_filtered = df_gastos.copy()
    if mes_sel != "TODOS": 
        df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": 
        df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
    if search:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    # 4. CÁLCULOS GLOBALES PRECISOS
    total_flete_2026 = df_filtered['COSTO DE FLETE'].sum()
    total_fact_2026 = df_filtered['FACTURACION'].sum()
    total_cajas_2026 = df_filtered['CAJAS'].sum()
    total_valuacion_2026 = df_filtered['VALUACION'].sum()

    # --- CÁLCULO DE COMPARATIVA 2025 (LA CLAVE) ---
    # Obtenemos los meses que están en el filtro actual
    meses_activos = df_filtered['MES'].unique()
    # Filtramos la matriz de 2025 para que sume SOLO esos meses
    # Importante: Sumamos la columna 'COSTO DE LA GUIA' del 2025
    total_flete_2025 = df_2025[df_2025['MES'].isin(meses_activos)]['COSTO DE LA GUIA'].sum()
    
    # RESULTADOS DEL ANÁLISIS
    costo_logistico = (total_flete_2026 / total_fact_2026 * 100) if total_fact_2026 > 0 else 0
    costo_por_caja = (total_flete_2026 / total_cajas_2026) if total_cajas_2026 > 0 else 0
    
    # % de Incidencias
    num_incidencias = (df_filtered['VALUACION'] > 0).sum()
    porcentaje_incidencias = (num_incidencias / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
    
    # Incremento + VI (Dinero total extra gastado)
    # Sumamos el flete actual + lo perdido en incidencias y restamos el flete del año pasado
    monto_incremento_vi = (total_flete_2026 + total_valuacion_2026) - total_flete_2025
    
    # % de incremento real (Enero 26 vs Enero 25)
    if total_flete_2025 > 0:
        perc_incremento_final = ((total_flete_2026 - total_flete_2025) / total_flete_2025) * 100
    else:
        perc_incremento_final = 0

    # 5. RENDERIZADO DE KPIs (TARJETAS)
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}")
    with k2: st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}")
    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_logistico:.2f}%")

    k5, k6, k7, k8 = st.columns(4)
    with k5: st.metric("COSTO POR CAJA", f"${costo_por_caja:,.2f}")
    with k6: st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion_2026:,.2f}")
    with k7: st.metric("% DE INCIDENCIAS", f"{porcentaje_incidencias:.1f}%")
    with k8: 
        # Mostramos la diferencia en dinero y el % de incremento comparado
        st.metric("INCREMENTO + VI", f"${monto_incremento_vi:,.2f}", delta=f"{perc_incremento_final:.2f}% vs 2025")

    # 6. TABLA DETALLADA
    st.markdown("---")
    st.subheader("📊 Detalle de Matriz Nexion")
    df_tabla = pd.merge(df_filtered, df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'REF_2025'}), on='MES', how='left')
    
    st.dataframe(df_tabla.style.format({
        'COSTO DE LA GUIA': '${:,.2f}', 'COSTO DE FLETE': '${:,.2f}',
        'FACTURACION': '${:,.2f}', 'VALUACION': '${:,.2f}',
        'COSTO LOGISTICO': '{:.2f}%', 'REF_2025': '${:,.2f}'
    }), use_container_width=True, height=450)

except Exception as e:
    st.error(f"¡Atención, amor! Hubo un detalle: {e}")
























































































































