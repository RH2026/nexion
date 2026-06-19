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
    # Usamos latin1 para evitar problemas con acentos en Excel
    df = pd.read_csv('pedidos.csv', encoding='latin1')
    df.columns = df.columns.str.strip()
    
    # Limpieza extrema de caracteres invisibles
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip()
            
    # Conversión "de fuerza bruta" para las fechas
    for col in ['PROGRAMACION', 'FECHA DE ENVIO']:
        # Quitamos cualquier carácter basura que no sea número o /
        df[col] = df[col].str.replace(r'[^0-9/]', '', regex=True)
        # Convertimos usando formato mixto y día primero
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce', format='mixed')
        
    return df

try:
    df = cargar_datos()
    
    # --- AUDITORÍA DE DATOS ---
    errores = df[df['PROGRAMACION'].isna() | df['FECHA DE ENVIO'].isna()]
    if not errores.empty:
        st.error(f"⚠️ Atención: {len(errores)} registros tienen fechas no reconocidas.")
    
    # --- CÁLCULO DE KPIs ---
    total = len(df)
    validos = df.dropna(subset=['FECHA DE ENVIO', 'PROGRAMACION'])
    
    # Efectividad (>98%)
    pedidos_ok = validos[validos['FECHA DE ENVIO'] <= validos['PROGRAMACION']].shape[0]
    efectividad = (pedidos_ok / total * 100) if total > 0 else 0
    
    # Precisión Facturación (buscando 'ENTREGADO' en ESTATUS)
    verificados = df[df['ESTATUS'].astype(str).str.contains('ENTREGADO', case=False, na=False)].shape[0]
    precision_fact = (verificados / total * 100) if total > 0 else 0
    
    # Muestras y Documentos
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
        # Mostramos detalle de incidencias
        st.dataframe(df[df['INCIDENCIA'].notnull()][['FACTURA', 'NOMBRE DEL CLIENTE', 'INCIDENCIA']])

except Exception as e:
    st.error(f"Error crítico en el motor de Nexion: {e}")














