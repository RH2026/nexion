import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. CONFIGURACIÓN DE PÁGINA (Fundamental para que quepa en una pantalla)
st.set_page_config(
    page_title="Nexion Logística Dashboard",
    layout="wide", # Esto expande el contenido a todo lo ancho
    initial_sidebar_state="collapsed"
)

# Cambia 'unsafe_allow_stdio' por 'unsafe_allow_html'
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    [data-testid="stMetricValue"] { font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def get_nexion_data():
    """Carga y limpia los datos desde el repositorio privado"""
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    REPO_NAME = "RH2026/nexion"
    # Actualizado al nuevo nombre de archivo que me diste
    FILE_PATH = "Matriz_Excel_Dashboard.csv" 
    URL_RAW = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }

    try:
        response = requests.get(URL_RAW, headers=headers)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        
        # Limpieza de Fechas
        date_cols = ['FECHA DE ENVÍO', 'PROMESA DE ENTREGA', 'FECHA DE ENTREGA REAL', 'EMISION']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Limpieza de Numéricos
        cols_num = ['COSTO DE LA GUÍA', 'COSTOS ADICIONALES', 'FACTURACION', 'CANTIDAD DE CAJAS']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Cálculo de OTIF (On Time In Full - A tiempo)
        # Es 1 si se entregó antes o el mismo día que la promesa
        df['A_TIEMPO'] = (df['FECHA DE ENTREGA REAL'] <= df['PROMESA DE ENTREGA']).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# --- INICIO DE LA APP ---
df = get_nexion_data()

if not df.empty:
    # FILTROS EN BARRA LATERAL (Para no estorbar en el dashboard principal)
    st.sidebar.header("🔍 Filtros Globales")
    meses = sorted(df['MES'].dropna().unique())
    mes_sel = st.sidebar.multiselect("Mes", meses, default=meses)
    
    fleteras = sorted(df['FLETERA'].dropna().unique())
    fletera_sel = st.sidebar.multiselect("Fletera", fleteras, default=fleteras)

    # Aplicar Filtros
    df_f = df[df['MES'].isin(mes_sel) & df['FLETERA'].isin(fletera_sel)]

    st.title("🚚 Panel de Control Nexion")

    # --- FILA 1: KPIs (Cintillo superior) ---
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    total_fact = df_f['FACTURACION'].sum()
    total_costo = df_f['COSTO DE LA GUÍA'].sum() + df_f['COSTOS ADICIONALES'].sum()
    porc_gasto = (total_costo / total_fact * 100) if total_fact > 0 else 0
    cumplimiento = (df_f['A_TIEMPO'].mean() * 100)
    cajas = df_f['CANTIDAD DE CAJAS'].sum()

    kpi1.metric("Facturación Total", f"${total_fact:,.0f}")
    kpi2.metric("Costo Total Flete", f"${total_costo:,.0f}")
    kpi3.metric("% Gasto Envío", f"{porc_gasto:.1f}%")
    kpi4.metric("Nivel OTIF", f"{cumplimiento:.1f}%")
    kpi5.metric("Total Cajas", f"{cajas:,.0f}")

    st.markdown("---")

    # --- FILA 2: Análisis de Costos e Incidencias ---
    col_a, col_b = st.columns([2, 1])

    with col_a:
        # Gráfico comparativo de Facturación vs Costo por Mes
        df_mes = df_f.groupby('MES')[['FACTURACION', 'COSTO DE LA GUÍA']].sum().reset_index()
        fig_evol = px.line(df_mes, x='MES', y=['FACTURACION', 'COSTO DE LA GUÍA'], 
                           title="Evolución: Venta vs Gasto Logístico", markers=True,
                           color_discrete_sequence=["#2ECC71", "#E74C3C"])
        fig_evol.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_evol, use_container_width=True)

    with col_b:
        # Donut chart de incidencias
        fig_inc = px.pie(df_f, names='INCIDENCIAS', title="Estado de Incidencias", hole=0.5)
        fig_inc.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_inc, use_container_width=True)

    # --- FILA 3: Destinos y Transporte ---
    col_c, col_d, col_e = st.columns(3)

    with col_c:
        # Top 10 Destinos
        df_dest = df_f.groupby('DESTINO')['CANTIDAD DE CAJAS'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_dest = px.bar(df_dest, y='DESTINO', x='CANTIDAD DE CAJAS', orientation='h', 
                          title="Top 10 Destinos", color='CANTIDAD DE CAJAS')
        fig_dest.update_layout(height=300)
        st.plotly_chart(fig_dest, use_container_width=True)

    with col_d:
        # Gasto por Fletera
        df_flet = df_f.groupby('FLETERA')['COSTO DE LA GUÍA'].sum().reset_index()
        fig_flet = px.bar(df_flet, x='FLETERA', y='COSTO DE LA GUÍA', title="Gasto por Fletera")
        fig_flet.update_layout(height=300)
        st.plotly_chart(fig_flet, use_container_width=True)

    with col_e:
        # Volumen por Forma de Envío
        df_env = df_f.groupby('FORMA DE ENVIO')['CANTIDAD DE CAJAS'].sum().reset_index()
        fig_env = px.bar(df_env, x='FORMA DE ENVIO', y='CANTIDAD DE CAJAS', title="Cajas por Forma de Envío")
        fig_env.update_layout(height=300)
        st.plotly_chart(fig_env, use_container_width=True)

    # --- FILA 4: Tabla de detalle (Pequeña al final) ---
    with st.expander("🔍 Ver detalle de pedidos y comentarios"):
        st.dataframe(df_f[['NÚMERO DE PEDIDO', 'NOMBRE DEL CLIENTE', 'DESTINO', 'FECHA DE ENTREGA REAL', 'COMENTARIOS', 'TRIGGER']], 
                     use_container_width=True)

else:
    st.error("No se pudo cargar la matriz. Revisa que el nombre del archivo en GitHub sea 'Matriz_Excel_Dashboard.csv'.")






















































































