import streamlit as st
import pandas as pd
import io
from github import Github
from datetime import timedelta

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
    
    # --- FILTRO POR MES (Sobre PROGRAMACION) ---
    df['MES_PROG'] = df['PROGRAMACION'].dt.to_period('M')
    meses_disponibles = sorted(df['MES_PROG'].dropna().unique(), reverse=True)
    
    st.subheader("Filtro de Análisis")
    mes_seleccionado = st.selectbox("Seleccionar Mes de Programación", 
                                    options=["TODOS"] + [m.strftime('%Y-%m') for m in meses_disponibles])
    
    if mes_seleccionado != "TODOS":
        df_filtrado = df[df['MES_PROG'] == pd.Period(mes_seleccionado, freq='M')]
    else:
        df_filtrado = df

    # --- CÁLCULO DE KPIs (Lógica de 24 hrs) ---
    pedidos_con_envio = df_filtrado[df_filtrado['FECHA DE ENVIO'].notna()].copy()
    
    # Lógica de cumplimiento: Diferencia de máximo 1 día (24 horas)
    # Si FECHA_ENVIO <= PROGRAMACION + 1 día, entonces CUMPLE
    pedidos_con_envio['DIFERENCIA'] = pedidos_con_envio['FECHA DE ENVIO'] - pedidos_con_envio['PROGRAMACION']
    pedidos_con_envio['CUMPLE'] = pedidos_con_envio['DIFERENCIA'] <= timedelta(days=1)
    
    total_con_envio = len(pedidos_con_envio)
    pedidos_ok = pedidos_con_envio[pedidos_con_envio['CUMPLE']].shape[0]
    efectividad = (pedidos_ok / total_con_envio * 100) if total_con_envio > 0 else 0
    
    # 2. Precisión Facturación
    verificados = df_filtrado[df_filtrado['ESTATUS'].str.contains('ENTREGADO', na=False)].shape[0]
    precision_fact = (verificados / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0

    # --- INTERFAZ ---
    col1, col2 = st.columns(2)
    col1.metric("Efectividad Despacho (Tolerancia 24h)", f"{efectividad:.2f}%", 
                delta="Meta > 98%" if efectividad >= 98 else "Alerta: < 98%")
    col2.metric("Precisión Facturación", f"{precision_fact:.1f}%")

    st.caption(f"Pedidos considerados para KPI: {total_con_envio}")
    
    st.divider()
    
    st.subheader("Detalle de Cumplimiento")
    st.dataframe(pedidos_con_envio[['FACTURA', 'PROGRAMACION', 'FECHA DE ENVIO', 'CUMPLE']])

except Exception as e:
    st.error(f"Error en Nexion: {e}")














