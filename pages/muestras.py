import streamlit as st
import pandas as pd

# Configuración de página con estética "Onyx Blue"
st.set_page_config(page_title="Nexion: Dashboard Logístico", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    h1, h2, h3 { color: #5DADE2; }
    .stMetric { background-color: #162128; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Nexion: Dashboard de Control Logístico")

# 1. Carga y Limpieza PROFUNDA de datos
@st.cache_data
def cargar_datos():
    df = pd.read_csv('pedidos.csv')
    df.columns = df.columns.str.strip()
    
    # Limpieza "a prueba de balas"
    for col in ['PROGRAMACION', 'FECHA DE ENVIO']:
        # Convertir a texto, limpiar espacios y forzar fecha
        df[col] = df[col].astype(str).str.strip()
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    
    return df

try:
    df = cargar_datos()
    
    # --- AUDITORÍA DE DATOS (Detectar errores de captura) ---
    errores = df[df['PROGRAMACION'].isna() | df['FECHA DE ENVIO'].isna()]
    if not errores.empty:
        st.error(f"⚠️ Atención: {len(errores)} registros tienen problemas de formato en fechas.")
        with st.expander("Ver registros con errores para corregir en origen"):
            st.dataframe(errores)

    # --- CÁLCULO DE KPIs ---
    total = len(df)
    validos = df.dropna(subset=['FECHA DE ENVIO', 'PROGRAMACION'])
    
    # 1. Efectividad de Despacho
    pedidos_ok = validos[validos['FECHA DE ENVIO'] <= validos['PROGRAMACION']].shape[0]
    efectividad = (pedidos_ok / total * 100) if total > 0 else 0
    
    # 2. Precisión Facturación
    verificados = df[(df['FACTURA'].notnull()) & (df['ESTATUS'].astype(str).str.contains('ENTREGADO', case=False, na=False))].shape[0]
    precision_fact = (verificados / total * 100) if total > 0 else 0
    
    # 3. Muestras y Documentación
    muestras = df[df['NOMBRE DEL CLIENTE'].astype(str).str.contains('MUESTRA', case=False, na=False)]
    docs_pendientes = df[df['INCIDENCIA'].astype(str).str.contains('DOC', case=False, na=False)]

    # --- VISUALIZACIÓN ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Efectividad Despacho", f"{efectividad:.2f}%", delta="Meta > 98%" if efectividad >= 98 else "Alerta: < 98%")
    col2.metric("Precisión Facturación", f"{precision_fact:.1f}%")
    col3.metric("Muestras", len(muestras))
    col4.metric("Docs. Pendientes", len(docs_pendientes))

    st.divider()

    # --- ANÁLISIS OPERATIVO ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Eficiencia por Surtidor")
        surtidores = df.groupby('SURTIDOR')['CAJAS'].sum().sort_values(ascending=False)
        st.bar_chart(surtidores)
    
    with c2:
        st.subheader("Incidencias Recientes")
        st.dataframe(df[df['INCIDENCIA'].notnull()][['FACTURA', 'NOMBRE DEL CLIENTE', 'INCIDENCIA']])

except Exception as e:
    st.error(f"Error crítico en el motor de Nexion: {e}")














