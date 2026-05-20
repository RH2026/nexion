import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import base64

# ==============================================================================
# 1. CONFIGURACIÓN SUPREMA (Layout Wide Absoluto)
# ==============================================================================
st.set_page_config(page_title="Nexion Terminal | Wallet Élite", page_icon="🧮", layout="wide")

# ==============================================================================
# 2. ESTILOS CSS "SILICON VALLEY PRO" (Deeper Dark & Vibrant Accents)
# ==============================================================================
# Paleta: Fondo #0E1117 | Cards #161B22 | Borde #30363D | Texto #C9D1D9 | Accent #00FFAA
st.markdown("""
    <style>
    /* Fondo General y Fuentes Monospace para Datos */
    .stApp { background-color: #0E1117; color: #C9D1D9; }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}

    /* Estilo de Tarjetas KPI Xenocode */
    .kpi-card {
        background-color: #161B22;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #30363D;
        text-align: left;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-3px); border-color: #00FFAA; }
    .kpi-label { color: #8B949E; font-size: 14px; font-family: monospace; text-transform: uppercase; letter-spacing: 2px;}
    .kpi-value { color: #E6F1FF; font-size: 32px; font-weight: bold; font-family: 'Courier New', monospace; margin: 10px 0;}
    .kpi-trend { font-size: 14px; font-family: monospace; }

    /* Inputs Ultra Oscuros y Bordes Neon en Focus */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: #090C10 !important;
        border: 1px solid #30363D !important;
        color: white !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
        border-color: #00FFAA !important;
        box-shadow: 0 0 10px rgba(0, 255, 170, 0.2) !important;
    }
    
    /* Botones Pro */
    .stButton>button {
        border-radius: 8px;
        font-family: monospace;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. LÓGICA DE DATOS Y PERSISTENCIA (In-Memory con Auto-Llenado)
# ==============================================================================

# Cuentas Élite
CUENTAS_MATRIX = {
    "Banco MX (Core)": {"color": "#00FFAA", "fondo": 450000.00},
    "USD Wallet (Hedge)": {"color": "#00D4FF", "fondo": 12500.00}, # Equivalente aproximado
    "Crypto Fund (Risk)": {"color": "#BF7AF0", "fondo": 3200.00},  # Equivalente aproximado
    "Caja Fuerte (Physical)": {"color": "#8B949E", "fondo": 50000.00}
}

CATEGORIAS = ["Nomina", "Freelance", "Renta", "Servicios", "Supermercado", "Restaurantes", "Transporte", "Inversiones", "Varios"]

# Inicializar Estado
if 'movimientos' not in st.session_state:
    st.session_state.movimientos = []
    
# --- FUNCIÓN DE AUTO-LLENADO (Para que los gráficos se vean PRO al instante) ---
def auto_llenar_ejemplos():
    if len(st.session_state.movimientos) > 0: return # No llenar si ya hay datos
    
    start_date = datetime(2026, 5, 1)
    ejemplos = []
    
    # INGRESOS
    ejemplos.append({"Fecha": start_date, "Tipo": "Ingreso", "Categoria": "Nomina", "Concepto": "Pago Quincena 1 JYPESA", "Monto": 35000.0, "Cuenta": "Banco MX (Core)"})
    ejemplos.append({"Fecha": start_date + timedelta(days=14), "Tipo": "Ingreso", "Categoria": "Nomina", "Concepto": "Pago Quincena 2 JYPESA", "Monto": 35000.0, "Cuenta": "Banco MX (Core)"})
    ejemplos.append({"Fecha": start_date + timedelta(days=5), "Tipo": "Ingreso", "Categoria": "Freelance", "Concepto": "Proyecto Xenocode UI", "Monto": 15000.0, "Cuenta": "USD Wallet (Hedge)"})
    
    # GASTOS FIJOS/VARIABLES
    fechas_gastos = [
        (1, "Renta", "Renta Departamento", -18000.0, "Banco MX (Core)"),
        (2, "Servicios", "Pago CFE", -1200.0, "Banco MX (Core)"),
        (2, "Servicios", "Internet Fiber", -600.0, "Banco MX (Core)"),
        (3, "Supermercado", "Super Semanal 1", -2500.0, "Banco MX (Core)"),
        (5, "Transporte", "Gasolina Pro", -900.0, "Banco MX (Core)"),
        (7, "Restaurantes", "Cena Negocios Manigoldo", -3200.0, "Banco MX (Core)"),
        (10, "Varios", "Suscripción AWS Élite", -850.0, "USD Wallet (Hedge)"),
        (12, "Inversiones", "Compra BTC Drop", -5000.0, "Crypto Fund (Risk)"),
        (15, "Supermercado", "Super Semanal 2", -2100.0, "Banco MX (Core)"),
        (18, "Transporte", "Gasolina Pro 2", -850.0, "Banco MX (Core)"),
        (20, "Restaurantes", "Comida Equipo Nexion", -4500.0, "Caja Fuerte (Physical)"),
        (22, "Varios", "Compra Amazon Gear", -6200.0, "USD Wallet (Hedge)"),
        (25, "Supermercado", "Super Semanal 3", -1900.0, "Banco MX (Core)"),
    ]
    
    for dia, cat, conc, monto, cuenta in fechas_gastos:
        ejemplos.append({"Fecha": start_date + timedelta(days=dia-1), "Tipo": "Gasto", "Categoria": cat, "Concepto": conc, "Monto": monto, "Cuenta": cuenta})

    # Asegurar orden cronológico para los gráficos
    st.session_state.movimientos = sorted(ejemplos, key=lambda x: x['Fecha'])

# Ejecutar auto-llenado
auto_llenar_ejemplos()

# Preparar DataFrame Central
df = pd.DataFrame(st.session_state.movimientos)
if not df.empty:
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')
    current_month = datetime(2026, 5, 1).strftime('%Y-%m') # Forzamos mayo 2026 para el ejemplo
    df_month = df[df['Mes'] == current_month]
else:
    df_month = pd.DataFrame()

# Cálculos de Saldos Actuales (Sumando fondos base + movimientos)
saldos_actuales = {cuenta: datos['fondo'] for cuenta, datos in CUENTAS_MATRIX.items()}
if not df.empty:
    for cuenta in CUENTAS_MATRIX.keys():
        movs_cuenta = df[df['Cuenta'] == cuenta]
        saldos_actuales[cuenta] += movs_cuenta['Monto'].sum()

# ==============================================================================
# 4. DASHBOARD ÉLITE (WIDE LAYOUT)
# ==============================================================================

# --- HEADER ÉLITE ---
head_l, head_r = st.columns([6, 1])
with head_l:
    st.markdown(f"<h1 style='color:#00FFAA; margin: 0; font-family: monospace; letter-spacing: -1px;'>XENOCODE//FINANCIAL_TERMINAL_v1.0</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#8B949E; margin-top: 5px; font-family: monospace;'>OPERATOR: RIGOBERTO HERNÁNDEZ // SYSTEM_STATUS: <span style='color:#00FFAA'>ONLINE</span></p>", unsafe_allow_html=True)
with head_r:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 DISCONNECT", use_container_width=True): st.stop()

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# --- FILA 1: TARJETAS KPI (MÉTRICAS CLAVE MAYO 2026) ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_general = sum(saldos_actuales.values())
inc_month = df_month[df_month['Tipo'] == "Ingreso"]['Monto'].sum() if not df_month.empty else 0
exp_month = abs(df_month[df_month['Tipo'] == "Gasto"]['Monto'].sum()) if not df_month.empty else 0
net_month = inc_month - exp_month
perc_ahorro = (net_month / inc_month * 100) if inc_month > 0 else 0

with kpi1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">PATRIMONIO NETO TOTAL (MXN)</div>
            <div class="kpi-value">${total_general:,.2f}</div>
            <div class="kpi-trend" style="color:#8B949E">FONDOS CONSOLIDADOS</div>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">INGRESOS MTD (MAYO 2026)</div>
            <div class="kpi-value" style="color:#00FFAA">${inc_month:,.2f}</div>
            <div class="kpi-trend" style="color:#00FFAA">▲ FLUJO POSITIVO</div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">EGRESOS MTD (MAYO 2026)</div>
            <div class="kpi-value" style="color:#FF3B30">${exp_month:,.2f}</div>
            <div class="kpi-trend" style="color:#FF3B30">▼ CONSUMO CAPITAL</div>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    color_net = "#00FFAA" if net_month >= 0 else "#FF3B30"
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">FLUJO NETO / TASA AHORRO</div>
            <div class="kpi-value" style="color:{color_net}">${net_month:,.2f}</div>
            <div class="kpi-trend" style="color:{color_net}">{perc_ahorro:.1f}% EFICIENCIA</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- FILA 2: GRÁFICOS MAESTROS (LOS QUE QUERÍAS VER LLENOS) ---
gr_col1, gr_col2 = st.columns([1.2, 2])

with gr_col1:
    st.markdown("<p class='kpi-label' style='text-align:center;'>Asignación de Capital por Cuenta</p>", unsafe_allow_html=True)
    # Gráfico de Dona Plotly Pro
    fig_donut = go.Figure(data=[go.Pie(
        labels=list(saldos_actuales.keys()),
        values=list(saldos_actuales.values()),
        hole=.65,
        marker=dict(colors=[CUENTAS_MATRIX[c]['color'] for c in saldos_actuales.keys()], line=dict(color='#0E1117', width=3)),
        textinfo='percent',
        hoverinfo='label+value',
        textfont=dict(family="monospace", size=14, color="white")
    )])
    fig_donut.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center", font=dict(family="monospace", color="#8B949E")),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=10, l=10, r=10), height=380
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

with gr_col2:
    st.markdown("<p class='kpi-label' style='text-align:center;'>Evolución de Flujo de Efectivo (Mayo 2026)</p>", unsafe_allow_html=True)
    # Gráfico de Área/Línea Plotly Pro
    if not df_month.empty:
        df_daily = df_month.groupby([df_month['Fecha'].dt.date, 'Tipo'])['Monto'].sum().unstack().fillna(0)
        df_daily['Gasto'] = abs(df_daily['Gasto'])
        
        fig_flow = go.Figure()
        fig_flow.add_trace(go.Scatter(x=df_daily.index, y=df_daily['Ingreso'], name='Ingresos', mode='lines', line=dict(width=3, color='#00FFAA'), fill='tozeroy', fillcolor='rgba(0, 255, 170, 0.1)'))
        fig_flow.add_trace(go.Scatter(x=df_daily.index, y=df_daily['Gasto'], name='Egresos', mode='lines', line=dict(width=3, color='#FF3B30'), fill='tozeroy', fillcolor='rgba(255, 59, 48, 0.1)'))
        
        fig_flow.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color="#8B949E", tickfont=dict(family="monospace"), tickformat="%d %b"),
            yaxis=dict(showgrid=True, gridcolor="#30363D", color="#8B949E", tickfont=dict(family="monospace"), zeroline=False),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(family="monospace", color="#C9D1D9")),
            margin=dict(t=10, b=10, l=10, r=10), height=380, hovermode="x unified"
        )
        st.plotly_chart(fig_flow, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("Esperando datos del mes...")

st.markdown("---")

# --- FILA 3: OPERACIONES Y ANÁLISIS CATEGÓRICO ---
op_col1, op_col2 = st.columns([1, 1.8])

with op_col1:
    st.markdown("<p class='kpi-label'>Ejecutar Nueva Orden</p>", unsafe_allow_html=True)
    with st.form("elite_ops", clear_on_submit=True):
        f_date = st.date_input("Fecha Orden", datetime.now())
        f_monto = st.number_input("Cantidad MXN", min_value=0.0, step=100.0)
        f_cat = st.selectbox("Categoría Élite", CATEGORIAS)
        f_desc = st.text_input("Concepto / Referencia", placeholder="Ej. AWS Server Costs")
        f_cuenta = st.selectbox("Cuenta Destino/Origen", list(CUENTAS_MATRIX.keys()))
        
        btn_l, btn_r = st.columns(2)
        with btn_l:
            # Botón Rojo para Gasto
            if st.form_submit_button("📉 REGISTRAR GASTO", use_container_width=True):
                if f_monto > 0 and f_desc:
                    st.session_state.movimientos.append({"Fecha": pd.to_datetime(f_date), "Tipo": "Gasto", "Categoria": f_cat, "Concepto": f_desc, "Monto": -f_monto, "Cuenta": f_cuenta})
                    st.toast("Gasto registrado en la Matrix", icon="📉")
                    time.sleep(1)
                    st.rerun()
        with btn_r:
            # Botón Neon para Ingreso
            if st.form_submit_button("📈 REGISTRAR INGRESO", use_container_width=True):
                if f_monto > 0 and f_desc:
                    st.session_state.movimientos.append({"Fecha": pd.to_datetime(f_date), "Tipo": "Ingreso", "Categoria": f_cat, "Concepto": f_desc, "Monto": f_monto, "Cuenta": f_cuenta})
                    st.toast("Ingreso consolidado", icon="📈")
                    time.sleep(1)
                    st.rerun()

with op_col2:
    st.markdown("<p class='kpi-label'>Análisis de Consumo por Categoría (Mayo 2026)</p>", unsafe_allow_html=True)
    if not df_month.empty:
        df_gastos_cat = df_month[df_month['Tipo'] == "Gasto"].groupby('Categoria')['Monto'].sum().abs().reset_index()
        df_gastos_cat = df_gastos_cat.sort_values(by='Monto', ascending=True) # Ascending para que la barra más larga quede arriba en h-bar
        
        # Gráfico de Barras Horizontales Pro
        fig_cat = px.bar(df_gastos_cat, x='Monto', y='Categoria', orientation='h', text_auto=',.0f')
        fig_cat.update_traces(marker_color='#30363D', hovertemplate="%{y}: $%{x:,.2f}", textposition='outside', textfont=dict(family="monospace", color="#C9D1D9"))
        # Resaltar la categoría más alta con color Neon
       # Resaltar la categoría más alta con color Neon
        if not df_gastos_cat.empty:
            # Creamos la lista de colores: gris oscuro para todas, neón para la más alta
            colors = ['#30363D'] * len(df_gastos_cat)
            colors[-1] = '#00FFAA' 
            fig_cat.update_traces(marker_color=colors)

        fig_cat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title=None, showgrid=True, gridcolor="#30363D", color="#8B949E", font=dict(family="monospace"), tickformat="$,.0f"),
            yaxis=dict(title=None, color="#C9D1D9", font=dict(family="monospace")),
            margin=dict(t=10, b=10, l=10, r=10), height=410
        )
        st.plotly_chart(fig_cat, use_container_width=True, config={'displayModeBar': False})

st.markdown("---")

# --- FILA 4: LIBRO MAYOR (HISTORIAL TOTAL) ---
st.markdown("<p class='kpi-label'>Libro Mayor Consolidado (Xenocode Ledger)</p>", unsafe_allow_html=True)
if not df.empty:
    df_ledger = df.sort_values(by='Fecha', ascending=False)
    
    # Estilar la tabla con CSS ultra-clean
    def style_ledger(row):
        color = '#00FFAA' if row['Tipo'] == 'Ingreso' else '#FF3B30'
        return [f'color: {color} if row.name == "Monto" else ""'] * len(row) # Esto no funciona bien en apply, usamos map en la col

    # Formatear columnas
    df_ledger['Fecha'] = df_ledger['Fecha'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Mostrar DataFrame estilizado
    st.dataframe(
        df_ledger[['Fecha', 'Tipo', 'Categoria', 'Concepto', 'Monto', 'Cuenta']].style
        .format({'Monto': '${:,.2f}'})
        .map(lambda val: 'color: #00FFAA' if val > 0 else 'color: #FF3B30', subset=['Monto']),
        use_container_width=True, hide_index=True
    )






















































































































































