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
    
    # Vinculamos con Historial 2025
    df_2025_ref = df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'GUIA_2025'})
    df_final = pd.merge(df_gastos, df_2025_ref, on='MES', how='left')

    # CÁLCULOS POR FILA
    df_final['COSTOS ADICIONALES'] = df_final.get('COSTOS ADICIONALES', 0).fillna(0)
    df_final['VALUACION'] = df_final.get('VALUACION', 0).fillna(0)
    df_final['COSTO DE FLETE'] = df_final['COSTO DE LA GUIA'] + df_final['COSTOS ADICIONALES']
    
    # Cálculos individuales para la tabla
    df_final['COSTO LOGISTICO'] = (df_final['COSTO DE FLETE'] / df_final['FACTURACION']) * 100
    df_final['COSTO POR CAJA'] = df_final['COSTO DE FLETE'] / df_final['CAJAS']
    df_final['INCREMENTO_VI'] = (df_final['COSTO DE FLETE'] + df_final['VALUACION']) - df_final['GUIA_2025']
    df_final['% INCREMENTO VS 2025'] = ((df_final['COSTO DE FLETE'] - df_final['GUIA_2025']) / df_final['GUIA_2025']) * 100

    # 3. INTERFAZ DE FILTROS
    st.title("🌌 NEXION LOGISTICS | JYPESA")
    
    c_f1, c_f2, c_f3 = st.columns([1, 1, 2])
    with c_f1:
        mes_sel = st.selectbox("📅 Mes:", ["TODOS"] + sorted(df_final['MES'].unique().tolist()))
    with c_f2:
        flet_sel = st.selectbox("🚛 Fletera:", ["TODAS"] + sorted(df_final['FLETERA'].unique().tolist()))
    with c_f3:
        search = st.text_input("🔍 Buscar:", "")

    # Aplicar Filtros
    df_filtered = df_final.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
    if search:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    # 4. CÁLCULOS GLOBALES (Aquí es donde corregimos el error, amor)
    total_flete = df_filtered['COSTO DE FLETE'].sum()
    total_fact = df_filtered['FACTURACION'].sum()
    total_cajas = df_filtered['CAJAS'].sum()
    
    # REGLA DE ORO: Suma total / Suma total
    costo_logistico_real = (total_flete / total_fact) * 100 if total_fact > 0 else 0
    costo_por_caja_real = (total_flete / total_cajas) if total_cajas > 0 else 0

    # 5. RENDERIZADO DE KPIs
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("COSTO DE FLETE", f"${total_flete:,.2f}")
    with k2: st.metric("FACTURACIÓN", f"${total_fact:,.2f}")
    with k3: st.metric("CAJAS ENVIADAS", f"{total_cajas:,.0f}")
    with k4: st.metric("COSTO LOGÍSTICO", f"{costo_logistico_real:.2f}%") # <--- AQUÍ SALDRÁ EL 7.6%

    k5, k6, k7, k8 = st.columns(4)
    with k5: st.metric("COSTO POR CAJA", f"${costo_por_caja_real:,.2f}")
    with k6: st.metric("VALUACIÓN INCIDENCIAS", f"${df_filtered['VALUACION'].sum():,.2f}")
    with k7:
        perc_inc = ((df_filtered['VALUACION'] > 0).sum() / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        st.metric("% DE INCIDENCIAS", f"{perc_inc:.1f}%")
    with k8:
        st.metric("INCREMENTO + VI", f"${df_filtered['INCREMENTO_VI'].sum():,.2f}")

    # 6. TABLA
    st.markdown("---")
    st.dataframe(df_filtered.style.format({
        'COSTO DE LA GUIA': '${:,.2f}', 'COSTO DE FLETE': '${:,.2f}',
        'FACTURACION': '${:,.2f}', 'VALUACION': '${:,.2f}',
        'COSTO LOGISTICO': '{:.2f}%', 'COSTO POR CAJA': '${:,.2f}'
    }), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")




















































































































