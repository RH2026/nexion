import io
import time
from datetime import datetime
from github import Github
import pandas as pd
import pytz
import streamlit as st
from components.layout import render_layout

# ── 1. CONFIGURACIÓN Y PERMISOS ──
tz_gdl = pytz.timezone('America/Mexico_City')
hoy = datetime.now(tz_gdl)

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Ahorros Personales",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="FINANZAS", submodulo_actual="GASTOS")

# ==============================================================================
# 1. CONFIGURACIÓN DE DATOS Y GITHUB PARA WALLET
# ==============================================================================
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "cartera.csv"
LOCK_FILE_PATH = "lock_cartera.json"

# Como ya estás logueado en Nexion, tomamos tu usuario directamente
current_user = st.session_state.get("usuario_activo", "UNKNOWN")
puede_editar = current_user.upper() == "RIGOBERTO"

try:
    tz_gdl = pytz.timezone('America/Mexico_City')
except:
    pass # Por si ya lo tienes definido arriba
    
# Cuentas y Categorías (Colores Neon de Jypesa)
CUENTAS_MATRIX = {
    "Caja de Ahorros": {"color": "#00E5FF", "fondo_base": 0.00},
    "Scottiabank": {"color": "#00FFAA", "fondo_base": 0.00},
    "Santander": {"color": "#FF4B4B", "fondo_base": 0.00},
    "Cartera": {"color": "#8B9BB4", "fondo_base": 0.00},
    "Caja Jypesa": {"color": "#8B9BB8", "fondo_base": 0.00}
}
CATEGORIAS = [
    "Nómina", "Ahorros", "Ventas", "Freelance / Proyectos", "Rendimientos", "Reembolsos", "Ventas",
    "Renta", "Servicios Fijos", "Conectividad", "Mantenimiento",
    "Supermercado", "Restaurantes", "Cafeterías y Snacks",
    "Gasolina", "Mantenimiento Automotriz", "Trámites y Seguros", "Transporte Alternativo",
    "Mascotas", "Gastos Familiares", "Educación",
    "Deportes y Entrenamiento", "Cuidado Personal", "Gastos Médicos",
    "Suscripciones y Software", "Equipo y Gadgets",
    "Entretenimiento", "Ropa y Calzado", "Regalos",
    "Pago de Tarjetas", "Inversiones", "Ahorro", "Comisiones", "Varios"
]

# ==============================================================================
# 2. ESTILOS CSS "JYPESA NEXION CORE" (BOTONES Y RESET)
# ==============================================================================
st.markdown("""
    <style>
    /* Reset para que el contenedor use todo el ancho */
    div[data-testid="stBlock"] { max-width: 100% !important; padding: 0 !important; }
    
    /* Barra superior del dashboard Jypesa */
    header[data-testid="stHeader"] { background-color: #1D2A35 !important; border-bottom: 2px solid #34495E !important;}
    
    /* Tarjetas estilo Nexion Jypesa */
    .kpi-card {
        background-color: #253441 !important; 
        padding: 20px !important; 
        border-radius: 8px !important;
        border: 1px solid #34495E !important; 
        text-align: center !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
        margin-bottom: 15px;
    }
    .kpi-label { color: #8B9BB4 !important; font-size: 12px !important; font-weight: bold !important; text-transform: uppercase !important; letter-spacing: 1.5px !important;}
    .kpi-value { color: #FFFFFF !important; font-size: 34px !important; font-weight: bold !important; margin: 10px 0 !important;}
    .kpi-trend { font-size: 13px !important; font-weight: bold !important; }
    .neon-bar { height: 4px !important; border-radius: 2px !important; margin-top: 10px !important; width: 100% !important; }

    /* --- ESTILO CHINGÓN PARA LOS BOTONES PERSONALIZADOS --- */
    div.stButton > button {
        background-color: #2B343B !important; 
        color: #FFFFFF !important;            
        border: 1px solid #34495E !important; 
        border-radius: 5px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        font-weight: normal !important;
        font-size: 12px !important; /* <--- AQUÍ CAMBIAS EL TAMAÑO (ej. 12px, 14px, etc.) */
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    div.stButton > button:hover {
        background-color: #00A3A3 !important; 
        color: #ffffff !important;            
        border-color: #00A3A3 !important;
        box-shadow: 0 0 15px rgba(0, 255, 170, 0.4) !important;
    }
    div.stButton > button:active {
        background-color: #00A3A3 !important;
        border-color: #00A3A3 !important;
    }

    /* --- PESTAÑAS (TABS) ESTILO JYPESA --- */
    div[data-baseweb="tab-list"] {
        gap: 20px !important;
        border-bottom: 2px solid #34495E !important;
        margin-bottom: 15px !important;
    }
    div[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #8B9BB4 !important;
        font-weight: bold !important;
        font-size: 13px !important;
        border: none !important;
        padding-top: 0px !important;
        padding-bottom: 10px !important;
    }
    div[aria-selected="true"] {
        color: #00FFAA !important;
        border-bottom: 3px solid #00FFAA !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CONTROL DE CANDADO DE ARCHIVO (Para evitar que 2 editen el CSV a la vez)
# ==============================================================================
lock_info, bloqueado_por_otro = None, False
if puede_editar and TOKEN:
    try:
        repo = Github(TOKEN).get_repo(REPO_NAME)
        try:
            lock_info = json.loads(repo.get_contents(LOCK_FILE_PATH, ref="main").decoded_content.decode('utf-8'))
            if (datetime.now(tz_gdl) - tz_gdl.localize(datetime.strptime(lock_info["timestamp"], "%Y-%m-%d %H:%M:%S"))).total_seconds() < 600:
                if lock_info["usuario"] != current_user: bloqueado_por_otro = True
            else: lock_info = None
        except: pass
    except: pass
        
st.session_state["bloqueado_por_otro_efectivo"] = bloqueado_por_otro
if bloqueado_por_otro:
    st.warning(f"⚠️ MÓDULO PAUSADO: Sesión activa de **{lock_info['usuario']}**. No puedes registrar gastos ahora.")
    st.session_state["puede_editar_efectivo"] = False
else:
    st.session_state["puede_editar_efectivo"] = puede_editar
    if puede_editar and lock_info is None and TOKEN:
        try:
            repo = Github(TOKEN).get_repo(REPO_NAME)
            ahora_gdl = datetime.now(tz_gdl)
            lock_string = json.dumps({"usuario": current_user, "timestamp": ahora_gdl.strftime("%Y-%m-%d %H:%M:%S"), "hora": ahora_gdl.strftime("%H:%M:%S")}, indent=4)
            try: repo.update_file(path=LOCK_FILE_PATH, message=f"LOCK // {current_user}", content=lock_string, sha=repo.get_contents(LOCK_FILE_PATH).sha)
            except: repo.create_file(path=LOCK_FILE_PATH, message=f"LOCK // {current_user}", content=lock_string, branch="main")
        except: pass

# ==============================================================================
# 4. MOTOR DE DATOS (GITHUB O LOCAL FALLBACK)
# ==============================================================================
def get_wallet_data_from_git():
    if 'df_wallet' not in st.session_state or st.session_state.get('force_reload', False):
        start_date = datetime.now(tz_gdl)
        ejemplos = [
            {"Fecha": (start_date - timedelta(days=10)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Ingreso", "Categoria": "Nomina", "Concepto": "Pago Quincena 1 JYPESA", "Monto": 35000.0, "Cuenta": "Banco MX (Core)"},
            {"Fecha": (start_date - timedelta(days=8)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Gasto", "Categoria": "Renta", "Concepto": "Renta Oficinas", "Monto": -18000.0, "Cuenta": "Banco MX (Core)"},
            {"Fecha": (start_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Ingreso", "Categoria": "Freelance", "Concepto": "Proyecto Xenocode UI", "Monto": 15000.0, "Cuenta": "USD Wallet (Hedge)"},
            {"Fecha": (start_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Gasto", "Categoria": "Supermercado", "Concepto": "Compras Semanales", "Monto": -3500.0, "Cuenta": "Banco MX (Core)"},
        ]
        df_load = pd.DataFrame(ejemplos)

        if TOKEN:
            try:
                repo = Github(TOKEN).get_repo(REPO_NAME)
                try:
                    df_load = pd.read_csv(io.StringIO(repo.get_contents(FILE_PATH, ref="main").decoded_content.decode('utf-8')), keep_default_na=False)
                except:
                    repo.create_file(path=FILE_PATH, message="INITIALIZE WALLET MATRIX", content=df_load.to_csv(index=False), branch="main")
            except Exception as e:
                st.error(f"Error conexión GitHub: {e}. Usando datos locales.")

        df_load['Fecha'] = pd.to_datetime(df_load['Fecha'])
        st.session_state.df_wallet = df_load
        st.session_state.force_reload = False
        
    return st.session_state.df_wallet

# ==============================================================================
# 5. RENDERIZADO DE INTERFAZ WALLET
# ==============================================================================
puede_editar_efectivo = st.session_state.get("puede_editar_efectivo", False)
df_actual = get_wallet_data_from_git()

if not df_actual.empty:
    df_actual['Mes'] = df_actual['Fecha'].dt.strftime('%Y-%m')
    current_month = datetime.now(tz_gdl).strftime('%Y-%m')
    df_month = df_actual[df_actual['Mes'] == current_month]
else:
    df_month = pd.DataFrame()

# Cálculos de saldos
saldos_actuales = {cuenta: datos['fondo_base'] for cuenta, datos in CUENTAS_MATRIX.items()}
if not df_actual.empty:
    for cuenta in CUENTAS_MATRIX.keys():
        saldos_actuales[cuenta] += df_actual[df_actual['Cuenta'] == cuenta]['Monto'].sum()

total_general = sum(saldos_actuales.values())
inc_month = df_month[df_month['Tipo'] == "Ingreso"]['Monto'].sum() if not df_month.empty else 0
exp_month = abs(df_month[df_month['Tipo'] == "Gasto"]['Monto'].sum()) if not df_month.empty else 0
net_month = inc_month - exp_month

# SISTEMA DE PESTAÑAS
tab_kpi, tab_flujos, tab_registro = st.tabs(["KPI'S WALLET", "FLUJOS DE EFECTIVO", "REGISTRO NUBE"])

# --- PESTAÑA 1: KPI'S WALLET ---
with tab_kpi:
    st.markdown("<br>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-label'>PATRIMONIO NETO</div>
                <div class='kpi-value'>${total_general:,.2f}</div>
                <div class='kpi-trend' style='color:#00E5FF'>BALANCE GLOBAL</div>
                <div class='neon-bar' style='background: linear-gradient(90deg, #00E5FF, transparent);'></div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-label'>INGRESOS MTD</div>
                <div class='kpi-value'>${inc_month:,.2f}</div>
                <div class='kpi-trend' style='color:#00FFAA'>FLUJO DE ENTRADA</div>
                <div class='neon-bar' style='background: linear-gradient(90deg, #00FFAA, transparent);'></div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-label'>EGRESOS MTD</div>
                <div class='kpi-value'>${exp_month:,.2f}</div>
                <div class='kpi-trend' style='color:#FF4B4B'>GASTOS DEL MES</div>
                <div class='neon-bar' style='background: linear-gradient(90deg, #FF4B4B, transparent);'></div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><hr style='border-color: #34495E;'>", unsafe_allow_html=True)
    
    col_chart, _ = st.columns([2, 1]) 
    with col_chart:
        st.markdown("<p class='kpi-label' style='text-align:left;'><span style='color:#00E5FF'>🔍</span> DISTRIBUCIÓN DE CAPITAL POR CUENTA</p>", unsafe_allow_html=True)
        
        nombres_cuentas = list(saldos_actuales.keys())
        valores_saldos = list(saldos_actuales.values())
        colores_barras = [CUENTAS_MATRIX[c]['color'] for c in nombres_cuentas]

        fig_bars = go.Figure(go.Bar(
            x=valores_saldos, y=nombres_cuentas, orientation='h',
            marker=dict(color=colores_barras, line=dict(color='#1D2A35', width=2)),
            text=valores_saldos, texttemplate='%{text:$,.2f}', textposition='auto',
            textfont=dict(color='#FFFFFF', size=12, family="monospace"),
            hovertemplate="<b>%{y}</b><br>Saldo: %{x:$,.2f}<extra></extra>"
        ))

        fig_bars.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10), height=350,
            xaxis=dict(showgrid=True, gridcolor="#34495E", color="#8B9BB4", tickformat="$,.0f", title=None),
            yaxis=dict(color="#E0E6ED", tickfont=dict(size=13), title=None, autorange="reversed"),
            hoverlabel=dict(bgcolor="#253441", font=dict(size=13, family="monospace"))
        )
        
        st.plotly_chart(fig_bars, use_container_width=True, config={'displayModeBar': False})

# --- PESTAÑA 2: FLUJOS DE EFECTIVO ---
with tab_flujos:
    st.markdown("<br>", unsafe_allow_html=True)
    gr_col1, gr_col2 = st.columns([2, 1.5])
    
    with gr_col1:
        st.markdown("<p class='kpi-label' style='text-align:left;'><span style='color:#ffffff'></span> TENDENCIA DE FLUJO (MES ACTUAL)</p>", unsafe_allow_html=True)
        if not df_month.empty:
            df_daily = df_month.groupby([df_month['Fecha'].dt.date, 'Tipo'])['Monto'].sum().unstack().fillna(0)
            if 'Gasto' in df_daily: df_daily['Gasto'] = abs(df_daily['Gasto'])
            else: df_daily['Gasto'] = 0
            if 'Ingreso' not in df_daily: df_daily['Ingreso'] = 0
            
            fig_flow = go.Figure()
            fig_flow.add_trace(go.Scatter(x=df_daily.index, y=df_daily['Ingreso'], name='Ingresos', mode='lines', line=dict(width=3, color='#00FFAA'), fill='tozeroy', fillcolor='rgba(0, 255, 170, 0.05)'))
            fig_flow.add_trace(go.Scatter(x=df_daily.index, y=df_daily['Gasto'], name='Egresos', mode='lines', line=dict(width=3, color='#FF4B4B'), fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.05)'))
            
            fig_flow.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color="#8B9BB4", tickformat="%d %b"),
                yaxis=dict(showgrid=True, gridcolor="#34495E", color="#8B9BB4", zeroline=False),
                legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(color="#E0E6ED")),
                margin=dict(t=10, b=10, l=10, r=10), height=350, hovermode="x unified"
            )
            st.plotly_chart(fig_flow, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sin movimientos este mes.")

    with gr_col2:
        st.markdown("<p class='kpi-label' style='text-align:left;'><span style='color:#ffffff'></span> ANÁLISIS DE CONSUMO POR CATEGORÍA</p>", unsafe_allow_html=True)
        if not df_month.empty:
            df_gastos_cat = df_month[df_month['Tipo'] == "Gasto"].groupby('Categoria')['Monto'].sum().abs().reset_index()
            if not df_gastos_cat.empty:
                df_gastos_cat = df_gastos_cat.sort_values(by='Monto', ascending=True)
                fig_cat = px.bar(df_gastos_cat, x='Monto', y='Categoria', orientation='h', text_auto=',.0f')
                
                # --- NUEVA PALETA DE COLORES ESTILO NEXION ---
                # Generamos un degradé dinámico desde un cian/turquesa suave hasta el verde principal (#00FFAA)
                # o bien usando los tonos de la paleta corporativa de la interfaz.
                num_bars = len(df_gastos_cat)
                colors = []
                for i in range(num_bars):
                    # Hacemos que la barra más alta sea brillante (#00FFAA) y las demás varíen 
                    # entre tonos azules/grises estilizados (#34495E, #1F618D, #00E5FF)
                    if i == num_bars - 1:
                        colors.append('#44B3E1')  # La más alta destaca en verde Nexion
                    elif i >= num_bars - 3:
                        colors.append('#4D93D9')  # Las siguientes altas en cian brillante
                    else:
                        colors.append('#215C98')  # Las menores conservan el tono base elegante
                
                fig_cat.update_traces(marker_color=colors, hovertemplate="%{y}: $%{x:,.2f}", textposition='outside', textfont=dict(color="#E0E6ED"))
                fig_cat.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(title=None, showgrid=True, gridcolor="#34495E", color="#8B9BB4", tickformat="$,.0f"),
                    yaxis=dict(title=None, color="#E0E6ED"),
                    margin=dict(t=10, b=10, l=10, r=10), height=350
                )
                st.plotly_chart(fig_cat, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Sin gastos registrados este mes.")

# --- PESTAÑA 3: REGISTRO NUBE ---
with tab_registro:
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not TOKEN:
        st.warning("⚠️ Modo de solo lectura local. Configure GITHUB_TOKEN para registrar operaciones.")
    
    st.markdown("<p class='kpi-label' style='margin-bottom: 10px;'><span style='color:#00E5FF'>⚡</span> EJECUTAR ORDEN DE REGISTRO</p>", unsafe_allow_html=True)
    
    # 4 CONTROLES EN LÍNEA
    in_col1, in_col2, in_col3, in_col4 = st.columns(4)
    with in_col1:
        f_monto = st.number_input("Cantidad MXN", min_value=0.0, step=100.0, key="inp_monto_nube")
    with in_col2:
        f_cat = st.selectbox("Categoría", CATEGORIAS, key="inp_cat_nube")
    with in_col3:
        f_desc = st.text_input("Concepto / Referencia", placeholder="Ej. Gastos de Operación", key="inp_desc_nube")
    with in_col4:
        f_cuenta = st.selectbox("Cuenta Destino/Origen", list(CUENTAS_MATRIX.keys()), key="inp_cuenta_nube")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2 BOTONES ABAJO
    btn_l, btn_r = st.columns(2)
    block_submit = (not puede_editar_efectivo) or st.session_state.get("bloqueado_por_otro_efectivo", False) or (not TOKEN)
    
    with btn_l:
        gasto_sub = st.button("REGISTRAR INGRESO", icon=":material/save:", use_container_width=True, key="btn_ingreso_action")
    with btn_r:
        ingreso_sub = st.button("REGISTRAR GASTO", icon=":material/remove:", use_container_width=True, key="btn_gasto_action")
    
    if not block_submit and (gasto_sub or ingreso_sub) and f_monto > 0 and f_desc:
        with st.status("Sincronizando con Nube Nexion...", expanded=True):
            try:
                repo = Github(TOKEN).get_repo(REPO_NAME)
                contents = repo.get_contents(FILE_PATH)
                df_latest = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
                
                nueva_fila = {
                    "Fecha": datetime.now(tz_gdl).strftime("%Y-%m-%d %H:%M"),
                    "Tipo": "Gasto" if gasto_sub else "Ingreso",
                    "Categoria": f_cat,
                    "Concepto": f_desc,
                    "Monto": -f_monto if gasto_sub else f_monto,
                    "Cuenta": f_cuenta
                }
                
                df_latest = pd.concat([df_latest, pd.DataFrame([nueva_fila])], ignore_index=True)
                repo.update_file(path=FILE_PATH, message=f"UPDATE // {current_user} // {datetime.now(tz_gdl).strftime('%H:%M:%S')}", content=df_latest.to_csv(index=False), sha=contents.sha)
                
                try: repo.delete_file(path=LOCK_FILE_PATH, message=f"UNLOCK // {current_user}", sha=repo.get_contents(LOCK_FILE_PATH).sha)
                except: pass
                
                st.session_state.force_reload = True
                st.success("OPERACIÓN CLASIFICADA EXITOSAMENTE.")
                time.sleep(1)
                st.rerun()
            except Exception as e: st.error(f"Error crítico de sincronización: {e}")

    # Título del historial
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p class='kpi-label'><span style='color:#00E5FF'>🔍</span> DETALLE DE OPERACIONES EN TIEMPO REAL</p>", unsafe_allow_html=True)
    
    # --- RENDER DE REGISTROS CON SCROLL INTEGRADO (ESTILO AGC TAILWIND) ---
    def render_wallet_flow_responsive(df_data):
        df_clean = df_data.fillna('')
        data_records = df_clean.to_dict('records')
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
            <style>
                body {{ 
                    font-family: 'Inter', sans-serif; 
                    background-color: #384A52; 
                    color: #e2e8f0; 
                    margin: 0; 
                    padding: 5px; 
                    width: 100%; 
                }}
                ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.2); border-radius: 10px; }}
                ::-webkit-scrollbar-thumb {{ background: #3b82f6; border-radius: 10px; border: 2px solid #384A52; }}
                ::-webkit-scrollbar-thumb:hover {{ background: #10b981; }}
                
                .list-row {{
                    background-color: #263238;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    transition: all 0.2s ease;
                    margin-bottom: 8px;
                    border-radius: 8px;
                    overflow: hidden;
                    width: 100%;
                }}
                .list-row:hover {{
                    background-color: #2c3b42;
                    border-color: rgba(0, 229, 255, 0.4);
                }}
                .label-mini {{
                    font-size: 9px;
                    text-transform: uppercase;
                    font-weight: 800;
                    color: #BFBFBF;
                    letter-spacing: 1px;
                }}
            </style>
        </head>
        <body>
            <div class="w-full space-y-2">
                {"".join([f'''
                <div class="list-row flex items-stretch">
                    <div class="w-2 shrink-0 {"bg-[#00FFAA]" if float(item['Monto']) > 0 else "bg-[#FF4B4B]"} shadow-[2px_0_10px_rgba(0,0,0,0.3)]"></div>
                    <div class="flex flex-col md:flex-row flex-1 p-3 items-start md:items-center justify-between gap-4">
                        
                        <div class="w-full md:w-36 shrink-0">
                            <div class="label-mini">Fecha y Hora</div>
                            <div class="text-xs font-bold text-white font-mono mt-1">
                                {str(item['Fecha'])[:16]}
                            </div>
                        </div>

                        <div class="w-full md:w-28 shrink-0">
                            <div class="label-mini">Tipo</div>
                            <div class="mt-1">
                                <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase {"bg-[#00FFAA]/15 text-[#00FFAA]" if float(item['Monto']) > 0 else "bg-[#FF4B4B]/15 text-[#FF4B4B]"}"">
                                    {str(item['Tipo']).upper()}
                                </span>
                            </div>
                        </div>

                        <div class="w-full md:flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                            <div>
                                <div class="label-mini">Categoría</div>
                                <div class="text-xs font-bold text-slate-200 truncate">
                                    {str(item['Categoria'])}
                                </div>
                            </div>
                            <div>
                                <div class="label-mini">Concepto</div>
                                <div class="text-xs font-semibold text-sky-200 truncate">
                                    {str(item['Concepto'])}
                                </div>
                            </div>
                        </div>

                        <div class="w-full md:w-40 shrink-0">
                            <div class="label-mini">Cuenta</div>
                            <div class="text-xs font-bold text-slate-300 truncate mt-1">
                                {str(item['Cuenta'])}
                            </div>
                        </div>

                        <div class="w-full md:w-32 text-right shrink-0">
                            <div class="label-mini">Monto</div>
                            <div class="text-sm font-black font-mono mt-0.5 {"text-[#00FFAA]" if float(item['Monto']) > 0 else "text-[#FF4B4B]"}"">
                                ${float(item['Monto']):,.2f}
                            </div>
                        </div>

                    </div>
                </div>
                ''' for item in data_records])}
            </div>
        </body>
        </html>
        """
        return st.components.v1.html(html_content, height=450, scrolling=True)

    if not df_actual.empty:
        df_ledger = df_actual.sort_values(by='Fecha', ascending=False).copy()
        render_wallet_flow_responsive(df_ledger)
    else:
        st.info("No hay registros en la nube actualmente.")


