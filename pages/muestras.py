import streamlit as st
import pandas as pd
import datetime

# Configuración de página
st.set_page_config(page_title="Dashboard Logístico JYPESA", layout="wide")
st.title("📊 Control de KPIs Logísticos - JYPESA")

# 1. Carga de datos
@st.cache_data
def cargar_datos():
    # Asumimos que el archivo pedidos.csv está en la misma carpeta
    df = pd.read_csv('pedidos.csv')
    df['PROGRAMACION'] = pd.to_datetime(df['PROGRAMACION'])
    df['FECHA DE ENVIO'] = pd.to_datetime(df['FECHA DE ENVIO'])
    return df

try:
    df = cargar_datos()
    
    # --- CÁLCULO DE KPIs ---
    
    # KPI: Despacho Oportuno (>98%)
    total_pedidos = len(df)
    pedidos_ok = df[df['FECHA DE ENVIO'] <= df['PROGRAMACION']].shape[0]
    efectividad = (pedidos_ok / total_pedidos) * 100
    
    # KPI: Verificación vs Facturación
    # (Asumimos que un pedido verificado tiene 'FACTURA' no nula y estatus 'ENTREGADO')
    verificados = df[(df['FACTURA'].notnull()) & (df['ESTATUS'] == 'ENTREGADO')].shape[0]
    
    # KPI: Muestras
    muestras = df[df['NOMBRE DEL CLIENTE'].str.contains('MUESTRA', case=False, na=False)]
    
    # KPI: Control Documental (Incidencias tipo 'DOC')
    docs_pendientes = df[df['INCIDENCIA'].str.contains('DOC', case=False, na=False)]

    # --- VISUALIZACIÓN ---
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Efectividad Despacho", f"{efectividad:.2f}%", 
                delta="Meta > 98%" if efectividad >= 98 else "Alerta: < 98%")
    col2.metric("Precisión Facturación", f"{(verificados/total_pedidos)*100:.1f}%")
    col3.metric("Muestras Despachadas", len(muestras))
    col4.metric("Docs. Pendientes", len(docs_pendientes))

    st.divider()

    # --- EFICIENCIA OPERATIVA (Surtidores) ---
    st.subheader("Eficiencia Operativa por Surtidor")
    surtidor_perf = df.groupby('SURTIDOR')['CAJAS'].sum().sort_values(ascending=False)
    st.bar_chart(surtidor_perf)

    # --- TABLA DE DETALLE ---
    with st.expander("Ver detalle de pedidos con incidencias"):
        st.dataframe(df[df['INCIDENCIA'].notnull()])

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.info("Asegúrate de que el archivo 'pedidos.csv' esté en la misma carpeta.")














