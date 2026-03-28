import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# --- 1. CONFIGURACIÓN DE PÁGINA (ESTILO NEXION SV) ---
st.set_page_config(
    page_title="NEXION • Logistics Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. UI DESIGN (CSS INYECTADO) ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: #0E1117;
            color: #FAFAFA;
        }
        .block-container { padding-top: 2rem; }
        [data-testid="stMetric"] {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 1.2rem;
        }
        [data-testid="stMetricValue"] { font-weight: 700; font-size: 2rem !important; }
        .chart-card {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        h1 { font-weight: 700; letter-spacing: -1px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ENGINE (BACKEND CORREGIDO) ---
@st.cache_data
def get_nexion_data():
    try:
        GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
        REPO_NAME = "RH2026/nexion"
        FILE_PATH = "Matriz_Excel_Dashboard.csv"
        URL_RAW = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.raw"
        }

        response = requests.get(URL_RAW, headers=headers, timeout=15)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        
        # Limpieza de Fechas
        date_cols = ['FECHA DE ENVÍO', 'PROMESA DE ENTREGA', 'FECHA DE ENTREGA REAL']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Limpieza de Numéricos
        cols_num = ['COSTO DE LA GUÍA', 'COSTOS ADICIONALES', 'FACTURACION', 'CANTIDAD DE CAJAS']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Lógica OTIF
        if 'FECHA DE ENTREGA REAL' in df.columns and 'PROMESA DE ENTREGA' in df.columns:
            df['A_TIEMPO'] = (df['FECHA DE ENTREGA REAL'] <= df['PROMESA DE ENTREGA']).astype(int)
        else:
            df['A_TIEMPO'] = 0
            
        return df
    except Exception as e:
        st.error(f"Error cargando base de datos: {e}")
        return pd.DataFrame()

# --- 4. ORQUESTACIÓN DEL DASHBOARD ---
df = get_nexion_data()

if not df.empty:
    # Header
    st.markdown("<h1>NEXION</h1>", unsafe_allow_html=True)
    st.caption("Logistics & Freight Intelligence Dashboard v2.0")

    # Filtros en Sidebar
    with st.sidebar:
        st.header("Control Panel")
        meses = sorted(df['MES'].dropna().unique())
        mes_sel = st.multiselect("Filtrar por Mes", meses, default=meses)
        
        fleteras = sorted(df['FLETERA'].dropna().unique())
        fletera_sel = st.multiselect("Filtrar por Fletera", fleteras, default=fleteras)

    # Aplicar Filtros
    df_f = df[df['MES'].isin(mes_sel) & df['FLETERA'].isin(fletera_sel)]

    if df_f.empty:
        st.warning("No hay datos que coincidan con los filtros seleccionados.")
        st.stop()

    # --- FILA 1: KPIs ---
    k1, k2, k3, k4, k5 = st.columns(5)
    
    total_rev = df_f['FACTURACION'].sum()
    total_spend = df_f['COSTO DE LA GUÍA'].sum() + df_f['COSTOS ADICIONALES'].sum()
    otif_rate = df_f['A_TIEMPO'].mean() * 100
    volumen = df_f['CANTIDAD DE CAJAS'].sum()
    ratio = (total_spend / total_rev * 100) if total_rev > 0 else 0

    k1.metric("Revenue", f"${total_rev:,.0f}")
    k2.metric("Total Spend", f"${total_spend:,.0f}")
    k3.metric("Spend Ratio", f"{ratio:.1f}%")
    k4.metric("OTIF Rate", f"{otif_rate:.1f}%")
    k5.metric("Boxes Shipped", f"{volumen:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- FILA 2: GRÁFICOS PRINCIPALES ---
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Evolución Financiera
        df_mes = df_f.groupby('MES')[['FACTURACION', 'COSTO DE LA GUÍA']].sum().reset_index()
        fig_evol = go.Figure()
        fig_evol.add_trace(go.Scatter(x=df_mes['MES'], y=df_mes['FACTURACION'], name='Revenue', fill='tozeroy', line=dict(color='#00E676')))
        fig_evol.add_trace(go.Scatter(x=df_mes['MES'], y=df_mes['COSTO DE LA GUÍA'], name='Logistics Spend', fill='tozeroy', line=dict(color='#FF1744')))
        fig_evol.update_layout(
            title="Performance Trend", 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            font_color="#FAFAFA", height=350, margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_evol, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # ESTA ES LA LÍNEA QUE TENÍA EL ERROR (YA CORREGIDA)
        inc_data = df_f['INCIDENCIAS'].value_counts().reset_index()
        inc_data.columns = ['Tipo', 'Cantidad']
        
        fig_pie = px.pie(inc_data, names='Tipo', values='Cantidad', hole=0.7, color_discrete_sequence=['#00D1FF', '#30363D', '#FFD600'])
        fig_pie.update_layout(
            title="Incident Breakdown",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color="#FAFAFA", height=350, showlegend=False
        )
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # --- FILA 3: DESTINOS Y FLETERAS ---
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_dest = df_f.groupby('DESTINO')['CANTIDAD DE CAJAS'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_bar = px.bar(df_dest, x='CANTIDAD DE CAJAS', y='DESTINO', orientation='h', title="Top 10 Destinations")
        fig_bar.update_traces(marker_color='#00D1FF')
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FAFAFA", height=300)
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_d:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_flet = df_f.groupby('FLETERA')['COSTO DE LA GUÍA'].sum().reset_index()
        fig_flet = px.bar(df_flet, x='FLETERA', y='COSTO DE LA GUÍA', title="Spend per Carrier")
        fig_flet.update_traces(marker_color='#30363D')
        fig_flet.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FAFAFA", height=300)
        st.plotly_chart(fig_flet, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- DETALLE ---
    with st.expander("🔍 View Raw Matrix Data"):
        st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("Matrix File not found. Verify 'Matriz_Excel_Dashboard.csv' exists in the GitHub repository.")






















































































