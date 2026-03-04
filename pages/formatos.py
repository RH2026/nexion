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

# Función para convertir texto con $ o comas a número real
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

    # LIMPIEZA DE DATOS (Convertir todo a números reales para evitar el error 'subtract')
    columnas_dinero_2026 = ['COSTO DE LA GUIA', 'FACTURACION', 'VALUACION', 'COSTOS ADICIONALES']
    for col in columnas_dinero_2026:
        if col in df_actual.columns:
            df_actual[col] = limpiar_dinero(df_actual[col])
            
    if 'COSTO DE LA GUIA' in df_2025.columns:
        df_2025['COSTO DE LA GUIA'] = limpiar_dinero(df_2025['COSTO DE LA GUIA'])

    # Normalización de Meses
    df_actual['MES'] = df_actual['MES'].astype(str).str.strip().str.upper()
    df_2025['MES'] = df_2025['MES'].astype(str).str.strip().str.upper()

    # --- FILTRO SOLO COBRO REGRESO ---
    df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False)].copy()
    
    # Cálculos 2026
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

    # Aplicar Filtros
    df_filtered = df_gastos.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS": df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
    if search:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    # 4. CÁLCULOS GLOBALES PRECISOS
    total_flete_2026 = df_filtered['COSTO DE FLETE'].sum()
    total_fact_2026 = df_filtered['FACTURACION'].sum()
    total_cajas_2026 = df_filtered['CAJAS'].sum()
    total_valuacion_2026 = df_filtered['VALUACION'].sum()

    # --- DATOS HISTÓRICOS 2025 (MESES SELECCIONADOS) ---
    meses_activos = df_filtered['MES'].unique()
    df_2025_filtrado = df_2025[df_2025['MES'].isin(meses_activos)]
    
    total_flete_2025 = df_2025_filtrado['COSTO DE LA GUIA'].sum()
    total_cajas_2025 = df_2025_filtrado['CAJAS'].sum() # <--- IMPORTANTE

    # --- MÉTRICAS DE EFICIENCIA ---
    costo_caja_2026 = (total_flete_2026 / total_cajas_2026) if total_cajas_2026 > 0 else 0
    costo_caja_2025 = (total_flete_2025 / total_cajas_2025) if total_cajas_2025 > 0 else 0
    
    # Variación del costo por caja (La verdad de la eficiencia)
    var_costo_caja = ((costo_caja_2026 - costo_caja_2025) / costo_caja_2025 * 100) if costo_caja_2025 > 0 else 0
    
    # Variación de volumen (Para explicar por qué bajó el gasto)
    var_volumen = ((total_cajas_2026 - total_cajas_2025) / total_cajas_2025 * 100) if total_cajas_2025 > 0 else 0

    # 5. RENDERIZADO DE KPIs (CON LA VERDAD COMPLETA)
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    with k1: 
        st.metric("COSTO DE FLETE", f"${total_flete_2026:,.2f}", 
                  delta=f"{((total_flete_2026 - total_flete_2025)/total_flete_2025*100):.1f}% vs 2025", delta_color="inverse")
    with k2: 
        st.metric("FACTURACIÓN", f"${total_fact_2026:,.2f}")
    with k3: 
        # Aquí mostramos que el volumen bajó
        st.metric("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}", delta=f"{var_volumen:.1f}% Vol.", delta_color="off")
    with k4: 
        st.metric("COSTO LOGÍSTICO", f"{(total_flete_2026/total_fact_2026*100):.2f}%")

    k5, k6, k7, k8 = st.columns(4)
    with k5: 
        # ESTE ES EL KPI MÁS IMPORTANTE AHORA
        st.metric("COSTO POR CAJA", f"${costo_caja_2026:,.2f}", delta=f"{var_costo_caja:.1f}% vs 2025", delta_color="inverse")
    with k6: 
        st.metric("VALUACIÓN INCIDENCIAS", f"${total_valuacion_2026:,.2f}")
    with k7:
        num_inc = (df_filtered['VALUACION'] > 0).sum()
        st.metric("% DE INCIDENCIAS", f"{(num_inc/len(df_filtered)*100):.1f}%")
    with k8:
        inc_vi_monto = (total_flete_2026 + total_valuacion_2026) - total_flete_2025
        st.metric("INCREMENTO + VI", f"${inc_vi_monto:,.2f}")

    # 6. TABLA
    st.markdown("---")
    st.dataframe(df_filtered.style.format({
        'COSTO DE LA GUIA': '${:,.2f}', 'COSTO DE FLETE': '${:,.2f}',
        'FACTURACION': '${:,.2f}', 'VALUACION': '${:,.2f}', 'COSTO LOGISTICO': '{:.2f}%'
    }), use_container_width=True)

except Exception as e:
    st.error(f"¡Atención, amor! Hubo un detalle: {e}")


























































































































