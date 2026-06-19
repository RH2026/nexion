import streamlit as st
import pandas as pd

# Configuración de página para ese look "Elite" y minimalista
st.set_page_config(page_title="Dashboard Logístico Nexion", layout="wide")

# Estilo personalizado para un look "Onyx Blue"
st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    h1, h2, h3 { color: #5DADE2; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Nexion: Dashboard de Control Logístico")

# 1. Carga y Limpieza de datos
@st.cache_data
def cargar_datos():
    # Asegúrate que 'pedidos.csv' esté en la misma carpeta que este script
    df = pd.read_csv('pedidos.csv')
    
    # Conversión de fechas con formato mixto y día primero
    df['PROGRAMACION'] = pd.to_datetime(df['PROGRAMACION'], dayfirst=True, format='mixed')
    df['FECHA DE ENVIO'] = pd.to_datetime(df['FECHA DE ENVIO'], dayfirst=True, format='mixed')
    
    # Limpiamos posibles espacios en nombres de columnas
    df.columns = df.columns.str.strip()
    return df

try:
    df = cargar_datos()
    
    # --- CÁLCULO DE KPIs ---
    
    # Totalizadores
    total_pedidos = len(df)
    
    # KPI 1: Efectividad de Despacho (>98%)
    pedidos_ok = df[df['FECHA DE ENVIO'] <= df['PROGRAMACION']].shape[0]
    efectividad = (pedidos_ok / total_pedidos) * 100
    
    # KPI 2: Precisión Facturación
    # (Asumimos que el pedido está bien si tiene factura y estatus OK)
    verificados = df[(df['FACTURA'].notnull()) & (df['ESTATUS'] == 'ENTREGADO')].shape[0]
    precision_fact = (verificados / total_pedidos) * 100
    
    # KPI 3: Muestras y Documentación
    muestras = df[df['NOMBRE DEL CLIENTE'].str.contains('MUESTRA', case=False, na=False)]
    docs_pendientes = df[df['INCIDENCIA'].str.contains('DOC', case=False, na=False)]

    # --- VISUALIZACIÓN ---
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Métricas con lógica de color (si < 98% alerta)
    col1.metric("Efectividad Despacho", f"{efectividad:.2f}%", 
                delta="Meta > 98%" if efectividad >= 98 else "Alerta: < 98%")
    col2.metric("Precisión Facturación", f"{precision_fact:.1f}%")
    col3.metric("Muestras Despachadas", len(muestras))
    col4.metric("Docs. Pendientes", len(docs_pendientes))

    st.divider()

    # --- EFICIENCIA OPERATIVA ---
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("Eficiencia por Surtidor (Cajas)")
        surtidor_perf = df.groupby('SURTIDOR')['CAJAS'].sum().sort_values(ascending=False)
        st.bar_chart(surtidor_perf)

    with col_der:
        st.subheader("Incidencias Recientes")
        # Mostramos solo los que tienen alguna incidencia registrada
        st.dataframe(df[df['INCIDENCIA'].notnull()][['FACTURA', 'NOMBRE DEL CLIENTE', 'INCIDENCIA']])

except Exception as e:
    st.error(f"Error al procesar los datos: {e}")
    st.write("Verifica que tu archivo 'pedidos.csv' contenga las columnas correctas.")














