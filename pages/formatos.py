import streamlit as st
import pandas as pd
import unicodedata

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ONYX
st.set_page_config(page_title="Nexion JYPESA - Dashboard", layout="wide")

# Estilo personalizado para el color Onyx Black-Blue
st.markdown("""
    <style>
    .main { background-color: #0B1014; }
    .stMetric { background-color: #162129; padding: 15px; border-radius: 10px; border: 1px solid #243441; }
    div[data-testid="stMetricValue"] { color: #A4B9C8; }
    .stDataFrame { border: 1px solid #243441; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_columnas(txt):
    if not isinstance(txt, str): return txt
    texto = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

# 2. CARGA Y LIMPIEZA
try:
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]

    # Cálculos base
    df_2025_ref = df_2025[['MES', 'COSTO DE LA GUIA']].rename(columns={'COSTO DE LA GUIA': 'GUIA_2025'})
    df_final = pd.merge(df_actual, df_2025_ref, on='MES', how='left')
    
    df_final['COSTOS ADICIONALES'] = df_final.get('COSTOS ADICIONALES', 0).fillna(0)
    df_final['COSTO DE FLETE'] = df_final['COSTO DE LA GUIA'] + df_final['COSTOS ADICIONALES']
    df_final['COSTO LOGISTICO'] = (df_final['COSTO DE FLETE'] / df_final['FACTURACION']) * 100
    df_final['COSTO POR CAJA'] = df_final['COSTO DE FLETE'] / df_final['CAJAS']
    df_final['% INCREMENTO VS 2025'] = ((df_final['COSTO DE FLETE'] - df_final['GUIA_2025']) / df_final['GUIA_2025']) * 100

    # 3. FILTROS EN EL CUERPO (NO SIDEBAR)
    st.title("🌌 NEXION LOGISTICS DASHBOARD")
    
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        meses = ["TODOS"] + sorted(df_final['MES'].unique().tolist())
        mes_sel = st.selectbox("📅 Selecciona Mes:", meses)
    with col_f2:
        fleteras = ["TODAS"] + sorted(df_final['FLETERA'].unique().tolist())
        flet_sel = st.selectbox("🚛 Selecciona Fletera:", fleteras)
    with col_f3:
        search = st.text_input("🔍 Buscar Cliente/Factura:", "")

    # Aplicar Filtros
    df_filtered = df_final.copy()
    if mes_sel != "TODOS":
        df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS":
        df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]
    if search:
        df_filtered = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

    # 4. RENDERIZADO DE MÉTRICAS (TARJETAS)
    st.markdown("---")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1:
        st.metric("COSTO FLETE", f"${df_filtered['COSTO DE FLETE'].sum():,.2f}")
    with m2:
        st.metric("FACTURACIÓN", f"${df_filtered['FACTURACION'].sum():,.2f}")
    with m3:
        st.metric("CAJAS ENVIADAS", f"{df_filtered['CAJAS'].sum():,.0f}")
    with m4:
        st.metric("COSTO LOGÍSTICO", f"{df_filtered['COSTO LOGISTICO'].mean():,.2f}%")
    with m5:
        st.metric("COSTO POR CAJA", f"${df_filtered['COSTO POR CAJA'].mean():,.2f}")

    # 5. TABLA PRINCIPAL CON DISEÑO PROFESIONAL
    st.markdown("### 📊 Detalle Operativo")
    
    # Formateo y Estilo
    styled_df = df_filtered.style.format({
        'COSTO DE LA GUIA': '${:,.2f}',
        'COSTO DE FLETE': '${:,.2f}',
        'FACTURACION': '${:,.2f}',
        'COSTO LOGISTICO': '{:.2f}%',
        '% INCREMENTO VS 2025': '{:.2f}%'
    }).background_gradient(cmap='Blues', subset=['COSTO LOGISTICO']) # Degradado en el costo logístico

    st.dataframe(styled_df, use_container_width=True, height=500)

    # 6. INCIDENCIAS E INCREMENTO
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("⚠️ Valuación Incidencias")
        total_inc = df_filtered['VALUACION'].sum()
        st.info(f"Monto total en incidencias para este periodo: **${total_inc:,.2f}**")
        
    with col_b:
        st.subheader("📈 Incremento + VI")
        # Calculamos el Incremento sumando la Valuación de Incidencias
        incremento_total = (df_filtered['COSTO DE FLETE'].sum() + total_inc) - df_filtered['GUIA_2025'].sum()
        st.success(f"Diferencia real vs 2025: **${incremento_total:,.2f}**")

except Exception as e:
    st.error(f"Falta un archivo o columna, amor: {e}")
















































































































