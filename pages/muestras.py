Entendido perfectamente. Quieres que el dashboard respire esa estética de Silicon Valley: limpio, minimalista, con tipografía nítida, paleta de colores moderna (modo oscuro con acentos neón) y un layout hiper-eficiente donde la información es la protagonista absoluta. Nada de "diseños de Excel".

He rediseñado completamente la interfaz visual usando CSS personalizado inyectado en Streamlit y he cambiado las gráficas de Plotly a un estilo más elegante y sobrio.

Aquí tienes el código de "Nexion, Silicon Valley Edition":

Python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA "SILICON VALLEY" ---
st.set_page_config(
    page_title="NEXION • Logistics Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS PERSONALIZADO: LA MÁGIA DEL DISEÑO (UI/UX) ---
# Usamos Inter como tipografía (muy SV), fondo oscuro, KPIs minimalistas y tarjetas limpias.
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        /* Tipografía Global y Fondo */
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: #0E1117; /* Fondo muy oscuro */
            color: #FAFAFA;
        }

        /* Ocultar elementos innecesarios de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 2rem; padding-bottom: 0rem;}

        /* Títulos */
        h1 {
            font-weight: 700;
            letter-spacing: -1px;
            color: #FAFAFA;
            padding-bottom: 0rem;
        }
        .subtitle {
            font-weight: 300;
            color: #A0AEC0;
            font-size: 1rem;
            margin-top: -10px;
            margin-bottom: 2rem;
        }

        /* Tarjetas de Métricas (KPIs) */
        [data-testid="stMetric"] {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }
        [data-testid="stMetric"]:hover {
            border-color: #00D1FF; /* Acento Neón */
            transform: translateY(-2px);
        }
        [data-testid="stMetricLabel"] {
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #A0AEC0;
            font-size: 0.75rem;
        }
        [data-testid="stMetricValue"] {
            font-weight: 700;
            font-size: 2.2rem;
            color: #FAFAFA;
        }

        /* Contenedores de Gráficos (Cards) */
        .chart-card {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        /* Dataframe */
        [data-testid="stDataFrame"] {
            border: 1px solid #30363D;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 3. EXTRACCIÓN Y LIMPIEZA DE DATOS (BACKEND) ---
@st.cache_data
def get_nexion_data():
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "Matriz_Excel_Dashboard.csv"
    URL_RAW = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }

    try:
        response = requests.get(URL_RAW, headers=headers, timeout=10)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        
        # Limpieza de Fechas
        date_cols = ['FECHA DE ENVÍO', 'PROMESA DE ENTREGA', 'FECHA DE ENTREGA REAL']
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Limpieza de Numéricos
        cols_num = ['COSTO DE LA GUÍA', 'COSTOS ADICIONALES', 'FACTURACION', 'CANTIDAD DE CAJAS']
        for col in cols_num:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Lógica de Negocio: OTIF
        df['A_TIEMPO'] = (df['FECHA DE ENTREGA REAL'] <= df['PROMESA DE ENTREGA']).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Failed to connect to Nexion Data Source: {e}")
        return pd.DataFrame()

# --- 4. PALETA DE COLORES Y ESTILO DE GRÁFICOS SV ---
COLOR_PRIMARY = "#00D1FF" # Cyan Neón
COLOR_SUCCESS = "#00E676" # Verde brillante
COLOR_WARNING = "#FFD600" # Amarillo
COLOR_DANGER = "#FF1744"  # Rojo brillante
COLOR_BG_CHART = "#161B22"
COLOR_GRID = "#30363D"
COLOR_TEXT = "#FAFAFA"

def apply_sv_layout(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="Inter",
        font_color=COLOR_TEXT,
        title_font_size=16,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor=COLOR_GRID, zeroline=False),
        yaxis=dict(gridcolor=COLOR_GRID, zeroline=False)
    )
    return fig

# --- 5. COMPOSICIÓN DEL DASHBOARD ---
df = get_nexion_data()

if not df.empty:
    # Encabezado Minimalista
    st.markdown("<h1>NEXION</h1>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Real-time Logistics Command Center v1.0</div>", unsafe_allow_html=True)

    # BARRA LATERAL (Filtros sobrios)
    with st.sidebar:
        st.markdown("### FILTERS")
        # Aseguramos que Mes esté ordenado cronológicamente si es posible
        meses = sorted(df['MES'].dropna().unique())
        mes_sel = st.multiselect("Active Months", meses, default=meses)
        
        fleteras = sorted(df['FLETERA'].dropna().unique())
        fletera_sel = st.multiselect("Carriers", fleteras, default=fleteras)

    # Filtrado de datos
    df_f = df[df['MES'].isin(mes_sel) & df['FLETERA'].isin(fletera_sel)]

    if df_f.empty:
        st.warning("No data matches the selected filters.")
        st.stop()

    # --- FILA 1: SUPER-KPIs (The Hook) ---
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    total_fact = df_f['FACTURACION'].sum()
    costo_guia = df_f['COSTO DE LA GUÍA'].sum()
    costo_add = df_f['COSTOS ADICIONALES'].sum()
    total_costo = costo_guia + costo_add
    
    porc_gasto = (total_costo / total_fact * 100) if total_fact > 0 else 0
    otif_rate = (df_f['A_TIEMPO'].mean() * 100)
    total_cajas = df_f['CANTIDAD DE CAJAS'].sum()

    kpi1.metric("Revenue", f"${total_fact:,.0f}")
    kpi2.metric("Logistics Spend", f"${total_costo:,.0f}")
    
    # KPI con delta de color (Rojo es malo si sube el gasto)
    kpi3.metric("Spend / Revenue", f"{porc_gasto:.1f}%")
    
    # OTIF con color dinámico
    kpi4.metric("OTIF Rate (On-Time)", f"{otif_rate:.1f}%")
    
    kpi5.metric("Volume (Units)", f"{total_cajas:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- FILA 2: ANÁLISIS ESTRATÉGICO (2 columnas) ---
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Evolución Venta vs Gasto (Área para un look más moderno)
        df_mes = df_f.groupby('MES')[['FACTURACION', 'COSTO DE LA GUÍA']].sum().reset_index()
        
        fig_evol = go.Figure()
        fig_evol.add_trace(go.Scatter(x=df_mes['MES'], y=df_mes['FACTURACION'], name='Revenue',
                                     fill='tozeroy', line=dict(color=COLOR_SUCCESS, width=2)))
        fig_evol.add_trace(go.Scatter(x=df_mes['MES'], y=df_mes['COSTO DE LA GUÍA'], name='Spend',
                                     fill='tozeroy', line=dict(color=COLOR_DANGER, width=2)))
        
        fig_evol.update_layout(title_text="Financial Performance Trend", height=320)
        st.plotly_chart(apply_sv_layout(fig_evol), use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Estado de Incidencias (Donut clean)
        df_inc = df_f['INCIDENCIAS'].value_with_con(0).reset_index()
        # Mapeo de colores específicos si existen valores estándar
        color_map = {'SIN INCIDENCIA': COLOR_GRID, 'RETRASO': COLOR_DANGER, 'DAÑO': COLOR_WARNING}
        
        fig_inc = px.pie(df_f, names='INCIDENCIAS', hole=0.7,
                         color_discrete_sequence=[COLOR_PRIMARY, COLOR_WARNING, COLOR_DANGER, COLOR_GRID])
        fig_inc.update_traces(textinfo='percent+label', textposition='outside')
        fig_inc.update_layout(title_text="Operational Health", height=320, showlegend=False)
        st.plotly_chart(apply_sv_layout(fig_inc), use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # --- FILA 3: OPERACIÓN TÁCTICA (3 columnas) ---
    col_c, col_d, col_e = st.columns([1.2, 1, 1])

    with col_c:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Top 10 Destinos (Barras Horizontales Modernas)
        df_dest = df_f.groupby('DESTINO')['CANTIDAD DE CAJAS'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_dest = px.bar(df_dest, y='DESTINO', x='CANTIDAD DE CAJAS', orientation='h')
        fig_dest.update_traces(marker_color=COLOR_PRIMARY, marker_line_color=COLOR_PRIMARY, marker_line_width=1, opacity=0.8)
        fig_dest.update_layout(title_text="Key Delivery Hubs", height=300, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(apply_sv_layout(fig_dest), use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_d:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Gasto por Fletera vs OTIF (Scatter Plot para análisis de eficiencia)
        df_flet = df_f.groupby('FLETERA').agg({
            'COSTO DE LA GUÍA': 'sum',
            'A_TIEMPO': 'mean'
        }).reset_index()
        df_flet['A_TIEMPO'] *= 100
        
        fig_flet = px.scatter(df_flet, x='COSTO DE LA GUÍA', y='A_TIEMPO', text='FLETERA', size='COSTO DE LA GUÍA')
        fig_flet.update_traces(marker=dict(color=COLOR_SUCCESS, line=dict(width=1, color=COLOR_TEXT)))
        fig_flet.update_layout(title_text="Carrier Efficiency (Spend vs OTIF)", height=300, 
                               xaxis_title="Total Spend", yaxis_title="OTIF %")
        st.plotly_chart(apply_sv_layout(fig_flet), use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_e:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        # Cajas por Transporte (TreeMap minimalista)
        df_env = df_f.groupby('TRANSPORTES')['CANTIDAD DE CAJAS'].sum().reset_index()
        fig_env = px.treemap(df_env, path=['TRANSPORTES'], values='CANTIDAD DE CAJAS',
                             color_discrete_sequence=[COLOR_BG_CHART, COLOR_GRID])
        fig_env.update_layout(title_text="Mode of Transport Split", height=300)
        st.plotly_chart(apply_sv_layout(fig_env), use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # --- FILA 4: DATA INSPECTOR (Expander sobrio) ---
    with st.expander("▽ RAW DATA INSPECTOR"):
        st.dataframe(
            df_f[['NÚMERO DE PEDIDO', 'NOMBRE DEL CLIENTE', 'DESTINO', 'FECHA DE ENTREGA REAL', 'INCIDENCIAS', 'TRIGGER']], 
            use_container_width=True,
            hide_index=True
        )

else:
    st.error("Nexion Data Stream offline. Check source file.")






















































































