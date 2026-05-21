import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import base64
import io
import json
import pytz
from github import Github

# ==============================================================================
# 1. CONFIGURACIÓN SUPREMA (Layout Wide Absoluto)
# ==============================================================================
st.set_page_config(page_title="Nexion Terminal | Wallet Élite", page_icon="🧮", layout="wide")

# ==============================================================================
# 2. CONFIGURACIÓN DE GITHUB Y PERMISOS
# ==============================================================================
# Intentar obtener el token de secrets, si no, usar None para evitar crash en local
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "cartera.csv"
LOCK_FILE_PATH = "lock_cartera.json"
tz_gdl = pytz.timezone('America/Mexico_City')

current_user = st.session_state.get("usuario_activo", "UNKNOWN")
puede_editar = current_user.upper() == "RIGOBERTO"

# Cuentas y Categorías (Ajustados a los colores Neon de Jypesa)
CUENTAS_MATRIX = {
    "Banco MX (Core)": {"color": "#00E5FF", "fondo_base": 450000.00},
    "USD Wallet (Hedge)": {"color": "#00FFAA", "fondo_base": 12500.00},
    "Crypto Fund (Risk)": {"color": "#FF4B4B", "fondo_base": 3200.00},
    "Caja Fuerte (Physical)": {"color": "#8B9BB4", "fondo_base": 50000.00}
}
CATEGORIAS = ["Nomina", "Freelance", "Renta", "Servicios", "Supermercado", "Restaurantes", "Transporte", "Inversiones", "Varios"]

# ==============================================================================
# 3. ESTILOS CSS "JYPESA NEXION CORE"
# ==============================================================================
st.markdown("""
    <style>
    /* Fondo General Azul Petróleo */
    .stApp { background-color: #1D2A35; color: #E0E6ED; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Tarjetas estilo Nexion Jypesa */
    .kpi-card {
        background-color: #253441; 
        padding: 20px; 
        border-radius: 8px;
        border: 1px solid #34495E; 
        text-align: center; 
        transition: transform 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .kpi-card:hover { transform: translateY(-2px); border-color: #00E5FF; }
    .kpi-label { color: #8B9BB4; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 1.5px;}
    .kpi-value { color: #FFFFFF; font-size: 34px; font-weight: bold; margin: 10px 0;}
    .kpi-trend { font-size: 13px; font-weight: bold; }

    /* Barra de progreso / Línea inferior neón estilo Jypesa */
    .neon-bar { height: 4px; border-radius: 2px; margin-top: 10px; width: 100%; }

    /* Inputs Estilo Jypesa */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: #17222B !important; 
        border: 1px solid #34495E !important;
        color: white !important; 
        border-radius: 6px !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
        border-color: #00E5FF !important; 
        box-shadow: 0 0 8px rgba(0, 229, 255, 0.3) !important;
    }
    
    /* Botones Pro */
    .stButton>button { 
        border-radius: 6px; font-weight: bold; background-color: #253441;
        border: 1px solid #34495E; color: white;
    }
    .stButton>button:hover { border-color: #00E5FF; color: #00E5FF; }

    /* --- PESTAÑAS (TABS) ESTILO JYPESA --- */
    div[data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 2px solid #34495E;
        margin-bottom: 20px;
    }
    div[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #8B9BB4 !important;
        font-weight: bold;
        font-size: 13px;
        border: none !important;
        padding-top: 0px;
        padding-bottom: 10px;
    }
    div[aria-selected="true"] {
        color: #00FFAA !important;
        border-bottom: 3px solid #00FFAA !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. CONTROL DE CANDADO EN TIEMPO REAL
# ==============================================================================
if 'splash_completado' not in st.session_state: st.session_state.splash_completado = False
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

@st.fragment(run_every=10)
def verificar_y_renderizar_bloqueo():
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
        st.error(f"⚠️ MÓDULO PAUSADO: Sesión activa de **{lock_info['usuario']}**.")
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
# 5. MOTOR DE DATOS (GITHUB O LOCAL FALLBACK)
# ==============================================================================
def get_wallet_data_from_git():
    if 'df_wallet' not in st.session_state or st.session_state.get('force_reload', False):
        # Fallback de datos si no hay token (para desarrollo local sin secrets)
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
                    # Si no existe el archivo en Git, crearlo con los ejemplos
                    repo.create_file(path=FILE_PATH, message="INITIALIZE WALLET MATRIX", content=df_load.to_csv(index=False), branch="main")
            except Exception as e:
                st.error(f"Error conexión GitHub: {e}. Usando datos locales.")
        
        df_load['Fecha'] = pd.to_datetime(df_load['Fecha'])
        st.session_state.df_wallet = df_load
        st.session_state.force_reload = False
        
    return st.session_state.df_wallet

# ==============================================================================
# 6. FLUJO DE CONTROL PRINCIPAL
# ==============================================================================

if not st.session_state.splash_completado:
    p = st.empty()
    for m in ["ESTABLISHING SECURE ACCESS...", "CONNECTING TO GITHUB...", "SYNCING LEDGER MATRIX...", "READY..."]:
        with p.container():
            st.markdown(f"""
            <div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:80px;height:80px;border:2px solid rgba(255,255,255,0.05); border-top:2px solid #00E5FF; border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;letter-spacing:5px;color:white;">{m}</p>
            </div>
            <style> @keyframes spin {{ to {{ transform: rotate(360deg); }} }} </style>
            """, unsafe_allow_html=True)
            time.sleep(0.4) # Un poco más rápido amor
    p.empty()
    st.session_state.splash_completado = True
    st.rerun()

elif not st.session_state.autenticado:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Intento de logo, si no texto neón
        try:
            encoded = base64.b64encode(open("n2.png", "rb").read()).decode()
            st.markdown(f'<div style="text-align:center"><img src="data:image/png;base64,{encoded}" width="180"></div>', unsafe_allow_html=True)
        except: st.markdown("<h1 style='text-align:center; color:#00E5FF; font-family:monospace; letter-spacing:10px;'>NEXION</h1>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("<p class='kpi-label' style='text-align:center;'>SECURITY CHECKPOINT</p>", unsafe_allow_html=True)
            user_input = st.text_input("USUARIO", placeholder="Rigoberto")
            pass_input = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")
            if st.form_submit_button("VERIFY IDENTITY", use_container_width=True):
                # Fallback credenciales si no hay secrets
                lista_usuarios = st.secrets.get("usuarios", {"Rigoberto": "demo123"})
                if user_input in lista_usuarios and str(lista_usuarios[user_input]) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = user_input
                    st.rerun()
                else: st.error("ERROR: ACCESS DENIED.")

else:
    # Restricción de usuario Hardcoded solicitada
    if st.session_state.usuario_activo.upper() != "RIGOBERTO":
        st.markdown("<div style='text-align:center; padding:50px;'><h2 style='color:#FF4B4B;'>⚠️ ACCESO RESTRINGIDO</h2><p>Solo personal autorizado.</p></div>", unsafe_allow_html=True)
        st.stop()

    verificar_y_renderizar_bloqueo()
    puede_editar_efectivo = st.session_state.get("puede_editar_efectivo", False)
    df_actual = get_wallet_data_from_git()
    
    if not df_actual.empty:
        df_actual['Mes'] = df_actual['Fecha'].dt.strftime('%Y-%m')
        current_month = datetime.now(tz_gdl).strftime('%Y-%m')
        df_month = df_actual[df_actual['Mes'] == current_month]
    else:
        df_month = pd.DataFrame()

    # --- CÁLCULOS PRINCIPALES ---
    saldos_actuales = {cuenta: datos['fondo_base'] for cuenta, datos in CUENTAS_MATRIX.items()}
    if not df_actual.empty:
        for cuenta in CUENTAS_MATRIX.keys():
            saldos_actuales[cuenta] += df_actual[df_actual['Cuenta'] == cuenta]['Monto'].sum()

    total_general = sum(saldos_actuales.values())
    inc_month = df_month[df_month['Tipo'] == "Ingreso"]['Monto'].sum() if not df_month.empty else 0
    exp_month = abs(df_month[df_month['Tipo'] == "Gasto"]['Monto'].sum()) if not df_month.empty else 0
    net_month = inc_month - exp_month

    # --- HEADER ESTILO JYPESA ---
    head_l, head_r = st.columns([6, 1])
    with head_l:
        st.markdown(f"<h3 style='color:#FFFFFF; margin: 0; font-weight: 300; letter-spacing: 2px;'>D A S H B O A R D <span style='color:#00E5FF'>|</span> WALLET <span style='color:#8B9BB4; font-size:14px;'>v2.0</span></h3>", unsafe_allow_html=True)
    with head_r:
        if st.button("🔒 DISCONNECT", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario_activo = "UNKNOWN"
            st.rerun()

    # ==========================================================================
    # --- SISTEMA DE PESTAÑAS (TABS REALES) ---
    # ==========================================================================
    tab_kpi, tab_flujos, tab_registro = st.tabs(["KPI'S WALLET", "FLUJOS DE EFECTIVO", "REGISTRO NUBE"])

    # --------------------------------------------------------------------------
    # PESTAÑA 1: KPI'S WALLET (Resumen)
    # --------------------------------------------------------------------------
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
        
        # ======================================================================
        # 🔥 EL NUEVO GRÁFICO: BARRAS HORIZONTALES ÉLITE (Adiós Donita) 🔥
        # ======================================================================
        col_chart, _ = st.columns([2, 1]) # Le damos más espacio a lo ancho
        with col_chart:
            st.markdown("<p class='kpi-label' style='text-align:left;'><span style='color:#00E5FF'>🔍</span> DISTRIBUCIÓN DE CAPITAL POR CUENTA</p>", unsafe_allow_html=True)
            
            # Preparar datos para el gráfico de barras
            nombres_cuentas = list(saldos_actuales.keys())
            valores_saldos = list(saldos_actuales.values())
            colores_barras = [CUENTAS_MATRIX[c]['color'] for c in nombres_cuentas]

            # Crear Gráfico de Barras Horizontales con go.Figure para control total
            fig_bars = go.Figure(go.Bar(
                x=valores_saldos,
                y=nombres_cuentas,
                orientation='h',
                marker=dict(
                    color=colores_barras, # Colores neón asignados
                    line=dict(color='#1D2A35', width=2) # Borde oscuro para resaltar
                ),
                text=valores_saldos,
                texttemplate='%{text:$,.2f}', # Formato moneda en la barra
                textposition='auto',
                textfont=dict(color='#FFFFFF', size=12, family="monospace"),
                hovertemplate="<b>%{y}</b><br>Saldo: %{x:$,.2f}<extra></extra>"
            ))

            fig_bars.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', # Fondo transparente
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=350,
                xaxis=dict(
                    showgrid=True, 
                    gridcolor="#34495E", # Rejilla sutil
                    color="#8B9BB4", 
                    tickformat="$,.0f",
                    title=None
                ),
                yaxis=dict(
                    color="#E0E6ED", 
                    font=dict(size=13),
                    title=None,
                    autorange="reversed" # La cuenta principal arriba
                ),
                hoverlabel=dict(bgcolor="#253441", font_size=13, font_family="monospace")
            )
            
            st.plotly_chart(fig_bars, use_container_width=True, config={'displayModeBar': False})

    # --------------------------------------------------------------------------
    # PESTAÑA 2: FLUJOS DE EFECTIVO (Gráficos)
    # --------------------------------------------------------------------------
    with tab_flujos:
        st.markdown("<br>", unsafe_allow_html=True)
        gr_col1, gr_col2 = st.columns([2, 1.5])
        
        with gr_col1:
            st.markdown("<p class='kpi-label' style='text-align:left;'><span style='color:#00E5FF'>📉</span> TENDENCIA DE FLUJO (MES ACTUAL)</p>", unsafe_allow_html=True)
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
            st.markdown("<p class='kpi-label' style='text-align:left;'><span style='color:#00E5FF'>📊</span> ANÁLISIS DE CONSUMO POR CATEGORÍA</p>", unsafe_allow_html=True)
            if not df_month.empty:
                df_gastos_cat = df_month[df_month['Tipo'] == "Gasto"].groupby('Categoria')['Monto'].sum().abs().reset_index()
                if not df_gastos_cat.empty:
                    df_gastos_cat = df_gastos_cat.sort_values(by='Monto', ascending=True)
                    fig_cat = px.bar(df_gastos_cat, x='Monto', y='Categoria', orientation='h', text_auto=',.0f')
                    
                    colors = ['#34495E'] * len(df_gastos_cat)
                    if len(colors) > 0: colors[-1] = '#00FFAA' # La barra más grande en verde neón Jypesa
                    
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

    # --------------------------------------------------------------------------
    # PESTAÑA 3: REGISTRO NUBE (Formulario y Tabla)
    # --------------------------------------------------------------------------
    with tab_registro:
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not TOKEN:
            st.warning("⚠️ Modo de solo lectura local. Configure GITHUB_TOKEN para registrar operaciones.")
        
        op_col1, op_col2 = st.columns([1, 2])

        with op_col1:
            st.markdown("<p class='kpi-label'><span style='color:#00E5FF'>⚡</span> EJECUTAR ORDEN</p>", unsafe_allow_html=True)
            with st.form("elite_ops", clear_on_submit=True):
                f_monto = st.number_input("Cantidad MXN", min_value=0.0, step=100.0)
                f_cat = st.selectbox("Categoría", CATEGORIAS)
                f_desc = st.text_input("Concepto / Referencia", placeholder="Ej. Gastos de Operación")
                f_cuenta = st.selectbox("Cuenta Destino/Origen", list(CUENTAS_MATRIX.keys()))
                
                btn_l, btn_r = st.columns(2)
                # Deshabilitar si no tiene permisos O si está bloqueado por otro O si no hay token
                block_submit = (not puede_editar_efectivo) or st.session_state.get("bloqueado_por_otro_efectivo", False) or (not TOKEN)
                
                gasto_sub = btn_l.form_submit_button("📉 REGISTRAR GASTO", use_container_width=True, disabled=block_submit)
                ingreso_sub = btn_r.form_submit_button("📈 REGISTRAR INGRESO", use_container_width=True, disabled=block_submit)
                
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
                            
                            # Liberar candado inmediatamente después de escribir
                            try: repo.delete_file(path=LOCK_FILE_PATH, message=f"UNLOCK // {current_user}", sha=repo.get_contents(LOCK_FILE_PATH).sha)
                            except: pass
                            
                            st.session_state.force_reload = True
                            st.success("OPERACIÓN CLASIFICADA EXITOSAMENTE.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Error crítico de sincronización: {e}")

        with op_col2:
            st.markdown("<p class='kpi-label'><span style='color:#00E5FF'>🔍</span> DETALLE DE OPERACIÓN EN TIEMPO REAL</p>", unsafe_allow_html=True)
            if not df_actual.empty:
                df_ledger = df_actual.sort_values(by='Fecha', ascending=False).copy()
                df_ledger['Fecha'] = df_ledger['Fecha'].dt.strftime('%d/%m/%Y %H:%M')
                
                # Estilo de tabla avanzada
                st.dataframe(
                    df_ledger[['Fecha', 'Tipo', 'Categoria', 'Concepto', 'Monto', 'Cuenta']].style
                    .format({'Monto': '${:,.2f}'})
                    .map(lambda val: 'color: #00FFAA; font-weight: bold;' if val > 0 else 'color: #FF4B4B; font-weight: bold;', subset=['Monto'])
                    .map(lambda val: 'background-color: rgba(0, 229, 255, 0.05);' if val == "Ingreso" else '', subset=['Tipo']),
                    use_container_width=True, hide_index=True, height=400
                )




















































































































































