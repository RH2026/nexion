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

    # FILTRO SOLO COBRO REGRESO
    df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False)].copy()
    
    # Pre-procesamiento de datos 2026
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
        search = st.text_input("🔍 Buscar:", "")

    # Aplicar Filtros a la matriz 2026
    df_filtered = df_gastos.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
    if search:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    # 4. CÁLCULOS GLOBALES (LA CORRECCIÓN CLAVE)
    # Totales 2026
    total_flete_2026 = df_filtered['COSTO DE FLETE'].sum()
    total_fact = df_filtered['FACTURACION'].sum()
    total_cajas = df_filtered['CAJAS'].sum()
    total_valuacion = df_filtered['VALUACION'].sum()

    # Totales 2025 (Cruce inteligente)
    # Obtenemos los meses que están en el filtro actual
    meses_activos = df_filtered['MES'].unique()
    # Filtramos la matriz de 2025 por esos mismos meses y sumamos sus guías
    total_flete_2025 = df_2025[df_2025['MES'].isin(meses_activos)]['COSTO DE LA GUIA'].sum()
    
    # KPIs Logísticos
    costo_logistico_real = (total_flete_2026 / total_fact) * 100 if total_fact > 0 else 0
    costo_por_caja_real = (total_flete_2026 / total_cajas) if total_cajas > 0 else 0
    
    # INCREMENTO % VS 2025 (Ejemplo: de 100 a 120 = 20%)
    if total_flete_2025 > 0:
        perc_incremento_vs_2025 = ((total_flete_2026 - total_flete_2025) / total_flete_2025) * 100
    else:
        perc_incremento_vs_2025 = 0

    # INCREMENTO + VI (Monto monetario de la diferencia incluyendo incidencias)
    incremento_vi_monto = (total_flete_2026 + total_valuacion) - total_flete_2025

    # 5. RENDERIZADO DE KPIs
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}")
    with k2: st.metric("FACTURACIÓN", f"${total_fact:,.2f}")
    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas:,.0f}")
    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_logistico_real:.2f}%")

    k5, k6, k7, k8 = st.columns(4)
    with k5: st.metric("COSTO POR CAJA", f"${costo_por_caja_real:,.2f}")
    with k6: st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion:,.2f}")
    with k7:
        perc_inc = ((df_filtered['VALUACION'] > 0).sum() / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        st.metric("% DE INCIDENCIAS", f"{perc_inc:.1f}%")
    with k8:
        # Aquí mostramos el monto de incremento y el % como delta
        st.metric("INCREMENTO + VI", f"${incremento_vi_monto:,.2f}", delta=f"{perc_incremento_2025:.2f}% VS 2025")

    # 6. TABLA DETALLADA
    st.markdown("---")
    # Cálculos para la tabla
    df_final_table = pd.merge(df_filtered, df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'GUIA_2025'}), on='MES', how='left')
    df_final_table['COSTO LOGISTICO'] = (df_final_table['COSTO DE FLETE'] / df_final_table['FACTURACION']) * 100
    
    st.dataframe(df_final_table.style.format({
        'COSTO DE LA GUIA': '${:,.2f}', 'COSTO DE FLETE': '${:,.2f}',
        'FACTURACION': '${:,.2f}', 'VALUACION': '${:,.2f}',
        'COSTO LOGISTICO': '{:.2f}%', 'GUIA_2025': '${:,.2f}'
    }), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")






















































































































