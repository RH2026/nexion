import streamlit as st
import pandas as pd

# Configuración de página con estética "Onyx Blue"
st.set_page_config(page_title="Nexion: Control Logístico", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1114; }
    h1, h2, h3 { color: #5DADE2; }
    .stMetric { background-color: #162128; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Nexion: Dashboard de Control Logístico")

# 1. Carga y Limpieza de datos (a prueba de errores)
@st.cache_data
def cargar_datos():
    df = pd.read_csv('pedidos.csv')
    df.columns = df.columns.str.strip()
    
    # Limpieza de fechas: coerce convierte errores en NaT (vacío)
    df['PROGRAMACION'] = pd.to_datetime(df['PROGRAMACION'], dayfirst=True, errors='coerce')
    df['FECHA DE ENVIO'] = pd.to_datetime(df['FECHA DE ENVIO'], dayfirst=True, errors='coerce')
    
    return df

try:
    df = cargar_datos()
    
    # --- AUDITORÍA DE DATOS ---
    fechas_error = df[df['PROGRAMACION'].isna() | df['FECHA DE ENVIO'].isna()]
    if not fechas_error.empty:
        st.error("⚠️ Se detectaron fechas inválidas en las siguientes filas (favor de corregir en el CSV):")
        st.dataframe(fechas_error)
        st.divider()

    # --- CÁLCULO DE KPIs ---
    total_pedidos = len(df)
    
    # KPI 1: Efectividad de Despacho
    pedidos_validos = df.dropna(subset=['FECHA DE ENVIO', 'PROGRAMACION'])
    pedidos_ok = pedidos_validos[pedidos_validos['FECHA DE ENVIO'] <= pedidos_validos['PROGRAMACION']].shape[0]
    efectividad = (pedidos_ok / total_pedidos) * 100 if total_pedidos > 0 else 0
    
    # KPI 2: Precisión Facturación
    verificados = df[(df['FACTURA'].notnull()) & (df['ESTATUS'] == 'ENTREGADO')].shape[0]
    precision_fact = (verificados / total_pedidos) * 100 if total_pedidos > 0 else 0
    
    # KPI 3: Muestras y Documentación
    muestras = df[df['NOMBRE DEL CLIENTE'].astype(str).str.contains('MUESTRA', case=False, na=False)]
    docs_pendientes = df[df['INCIDENCIA'].astype(str).str.contains('DOC', case=False, na=False)]

    # --- VISUALIZACIÓN ---
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Efectividad Despacho", f"{efectividad:.2f}%", 
                delta="Meta > 98%" if efectividad >= 98 else "Alerta: < 98%")
    col2.metric("Precisión Facturación", f"{precision_fact:.1f}%")
    col3.metric("Muestras Despachadas", len(muestras))
    col4.metric("Docs. Pendientes", len(docs_pendientes))

    st.divider()

    # --- TABLAS Y GRÁFICOS ---
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("Eficiencia por Surtidor (Cajas)")
        surtidor_perf = df.groupby('SURTIDOR')['CAJAS'].sum().sort_values(ascending=False)
        st.bar_chart(surtidor_perf)

    with col_der:
        st.subheader("Incidencias Recientes")
        st.dataframe(df[df['INCIDENCIA'].notnull()][['FACTURA', 'NOMBRE DEL CLIENTE', 'INCIDENCIA']])

except Exception as e:
    st.error(f"Error crítico en la carga de datos: {e}")














