import streamlit as st
import pandas as pd
import io
from github import Github
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Nexion: Dashboard KPIs", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    h1, h2, h3 { color: #5DADE2; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def cargar_datos_nexion():
    TOKEN = st.secrets.get("GITHUB_TOKEN")
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "pedidos.csv"
    
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(FILE_PATH, ref="main")
    
    df = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
    
    for col in df.columns:
        df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None'], '').str.strip().str.upper()
    
    for col in ['PROGRAMACION', 'FECHA DE ENVIO']:
        df[col] = pd.to_datetime(df[col].str.replace(r'[^0-9/]', '', regex=True), 
                                 dayfirst=True, errors='coerce', format='mixed')
    return df

st.title("📊 Nexion: Dashboard de Control Logístico")

try:
    df = cargar_datos_nexion()
    
    # --- FILTRO POR MES ---
    # Obtenemos meses únicos presentes en los datos (basado en FECHA DE ENVIO)
    df['MES'] = df['FECHA DE ENVIO'].dt.to_period('M')
    meses_disponibles = sorted(df['MES'].dropna().unique(), reverse=True)
    
    mes_seleccionado = st.sidebar.selectbox("Seleccionar Mes de Análisis", 
                                            options=["TODOS"] + [m.strftime('%Y-%m') for m in meses_disponibles])
    
    if mes_seleccionado != "TODOS":
        df_filtrado = df[df['MES'] == pd.Period(mes_seleccionado, freq='M')]
    else:
        df_filtrado = df

    # --- CÁLCULO DE KPIs (Sobre df_filtrado) ---
    
    # Lógica: Solo tomamos en cuenta pedidos con FECHA DE ENVIO
    pedidos_con_envio = df_filtrado[df_filtrado['FECHA DE ENVIO'].notna()].copy()
    total_con_envio = len(pedidos_con_envio)
    
    # 1. Efectividad Despacho
    pedidos_ok = pedidos_con_envio[pedidos_con_envio['FECHA DE ENVIO'] <= pedidos_con_envio['PROGRAMACION']].shape[0]
    efectividad = (pedidos_ok / total_con_envio * 100) if total_con_envio > 0 else 0
    
    # 2. Precisión Facturación
    verificados = df_filtrado[df_filtrado['ESTATUS'].str.contains('ENTREGADO', na=False)].shape[0]
    total_general = len(df_filtrado)
    precision_fact = (verificados / total_general * 100) if total_general > 0 else 0
    
    # 3. Muestras y Documentos
    muestras = df_filtrado[df_filtrado['NOMBRE DEL CLIENTE'].str.contains('MUESTRA', na=False)]
    docs_pendientes = df_filtrado[df_filtrado['INCIDENCIA'].str.contains('DOC', na=False)]

    # --- INTERFAZ ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Efectividad Despacho", f"{efectividad:.2f}%", delta="Meta > 98%" if efectividad >= 98 else "Alerta: < 98%")
    col2.metric("Precisión Facturación", f"{precision_fact:.1f}%")
    col3.metric("Muestras", len(muestras))
    col4.metric("Docs. Pendientes", len(docs_pendientes))

    st.caption(f"Pedidos considerados para KPI de efectividad: {total_con_envio} (Excluidos: {total_general - total_con_envio})")
    
    st.divider()

    # Análisis operativo
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Eficiencia por Surtidor")
        df_filtrado['CAJAS_NUM'] = pd.to_numeric(df_filtrado['CAJAS'], errors='coerce').fillna(0)
        st.bar_chart(df_filtrado.groupby('SURTIDOR')['CAJAS_NUM'].sum())
    
    with c2:
        st.subheader("Incidencias Recientes")
        st.dataframe(df_filtrado[df_filtrado['INCIDENCIA'] != ''][['FACTURA', 'NOMBRE DEL CLIENTE', 'INCIDENCIA']])

except Exception as e:
    st.error(f"Error en Nexion: {e}")














