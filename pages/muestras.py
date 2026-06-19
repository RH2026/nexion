import streamlit as st
import pandas as pd
import io
from github import Github
import pytz
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Nexion: Dashboard KPIs", layout="wide")

# Estilos Onyx Blue
st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    h1, h2, h3 { color: #5DADE2; }
    </style>
    """, unsafe_allow_html=True)

# 1. CARGA DE DATOS (Mismo motor que tu módulo funcional)
@st.cache_data
def cargar_datos_nexion():
    TOKEN = st.secrets.get("GITHUB_TOKEN")
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "pedidos.csv"
    
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(FILE_PATH, ref="main")
    
    # Carga cruda tipo texto para evitar errores de pandas con fechas
    df = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
    
    # Limpieza idéntica a tu otro módulo
    for col in df.columns:
        df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None'], '').str.strip().str.upper()
    
    # Conversión segura de fechas para los cálculos de KPIs
    for col in ['PROGRAMACION', 'FECHA DE ENVIO']:
        # Quitamos basura y convertimos
        df[col] = pd.to_datetime(df[col].str.replace(r'[^0-9/]', '', regex=True), 
                                 dayfirst=True, errors='coerce', format='mixed')
    
    return df

# 2. PROCESAMIENTO
st.title("📊 Nexion: Dashboard de Control Logístico")

try:
    df = cargar_datos_nexion()
    
    # --- CÁLCULO DE KPIs ---
    total = len(df)
    # Filtramos filas donde tengamos ambas fechas para el KPI de efectividad
    validos = df.dropna(subset=['FECHA DE ENVIO', 'PROGRAMACION'])
    
    # KPI: Efectividad > 98%
    pedidos_ok = validos[validos['FECHA DE ENVIO'] <= validos['PROGRAMACION']].shape[0]
    efectividad = (pedidos_ok / total * 100) if total > 0 else 0
    
    # KPI: Precisión Facturación (Buscando 'ENTREGADO' en columna ESTATUS)
    verificados = df[df['ESTATUS'].str.contains('ENTREGADO', na=False)].shape[0]
    precision_fact = (verificados / total * 100) if total > 0 else 0
    
    # KPI: Muestras y Documentación
    muestras = df[df['NOMBRE DEL CLIENTE'].str.contains('MUESTRA', na=False)]
    docs_pendientes = df[df['INCIDENCIA'].str.contains('DOC', na=False)]

    # 3. INTERFAZ VISUAL
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Efectividad Despacho", f"{efectividad:.2f}%", delta="Meta > 98%" if efectividad >= 98 else "Alerta: < 98%")
    col2.metric("Precisión Facturación", f"{precision_fact:.1f}%")
    col3.metric("Muestras", len(muestras))
    col4.metric("Docs. Pendientes", len(docs_pendientes))

    st.divider()

    # Análisis operativo
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Eficiencia por Surtidor (Cajas)")
        # Convertimos CAJAS a numérico para la gráfica
        df['CAJAS_NUM'] = pd.to_numeric(df['CAJAS'], errors='coerce').fillna(0)
        surtidores = df.groupby('SURTIDOR')['CAJAS_NUM'].sum().sort_values(ascending=False)
        st.bar_chart(surtidores)
    
    with c2:
        st.subheader("Incidencias Recientes")
        st.dataframe(df[df['INCIDENCIA'] != ''][['FACTURA', 'NOMBRE DEL CLIENTE', 'INCIDENCIA']])

except Exception as e:
    st.error(f"Error crítico en la carga de datos: {e}")
    st.write("Asegúrate de que tus secretos de GitHub estén configurados correctamente.")














