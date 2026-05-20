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
# 2. CONFIGURACIÓN DE GITHUB Y PERMISOS (TU MATRIZ DE CONTROL)
# ==============================================================================
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "cartera.csv"
LOCK_FILE_PATH = "lock_cartera.json"  # Archivo testigo para control de acceso
tz_gdl = pytz.timezone('America/Mexico_City')

current_user = st.session_state.get("usuario_activo", "UNKNOWN")
AUTHORIZED_EDITORS = ["Rigoberto"] # ¡Exclusivo para ti, amor!
puede_editar = current_user.upper() == "RIGOBERTO"

# --- OPCIONES DE LA INTERFAZ ---
CUENTAS_MATRIX = {
    "Banco MX (Core)": {"color": "#00FFAA", "fondo_base": 450000.00},
    "USD Wallet (Hedge)": {"color": "#00D4FF", "fondo_base": 12500.00},
    "Crypto Fund (Risk)": {"color": "#BF7AF0", "fondo_base": 3200.00},
    "Caja Fuerte (Physical)": {"color": "#8B949E", "fondo_base": 50000.00}
}
CATEGORIAS = ["Nomina", "Freelance", "Renta", "Servicios", "Supermercado", "Restaurantes", "Transporte", "Inversiones", "Varios"]

# ==============================================================================
# 3. ESTILOS CSS "SILICON VALLEY PRO"
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #C9D1D9; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    
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
    .stButton>button { border-radius: 8px; font-family: monospace; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. CONTROL DE CANDADO EN TIEMPO REAL (RECARGA COLOIDAL)
# ==============================================================================
if 'splash_completado' not in st.session_state: st.session_state.splash_completado = False
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

@st.fragment(run_every=10)
def verificar_y_renderizar_bloqueo():
    lock_info = None
    bloqueado_por_otro = False
    
    if puede_editar:
        try:
            g = Github(TOKEN)
            repo = g.get_repo(REPO_NAME)
            try:
                lock_contents = repo.get_contents(LOCK_FILE_PATH, ref="main")
                lock_info = json.loads(lock_contents.decoded_content.decode('utf-8'))
                
                lock_time = datetime.strptime(lock_info["timestamp"], "%Y-%m-%d %H:%M:%S")
                lock_time = tz_gdl.localize(lock_time)
                ahora = datetime.now(tz_gdl)
                
                if (ahora - lock_time).total_seconds() < 600: # Candado por 10 min
                    if lock_info["usuario"] != current_user:
                        bloqueado_por_otro = True
                else:
                    lock_info = None
            except Exception:
                pass
        except Exception as e:
            st.error(f"Error al verificar estado de bloqueo: {e}")
            
    st.session_state["bloqueado_por_otro_efectivo"] = bloqueado_por_otro
    
    if bloqueado_por_otro:
        st.error(f"⚠️ MÓDULO PAUSADO: El sistema detectó otra sesión activa de **{lock_info['usuario']}** desde las {lock_info['hora']}.")
        st.session_state["puede_editar_efectivo"] = False
    else:
        st.session_state["puede_editar_efectivo"] = puede_editar
        if puede_editar and lock_info is None:
            try:
                g = Github(TOKEN)
                repo = g.get_repo(REPO_NAME)
                ahora_gdl = datetime.now(tz_gdl)
                nuevo_lock = {
                    "usuario": current_user,
                    "timestamp": ahora_gdl.strftime("%Y-%m-%d %H:%M:%S"),
                    "hora": ahora_gdl.strftime("%H:%M:%S")
                }
                lock_string = json.dumps(nuevo_lock, indent=4)
                try:
                    contents_exist = repo.get_contents(LOCK_FILE_PATH)
                    repo.update_file(path=LOCK_FILE_PATH, message=f"LOCK // {current_user}", content=lock_string, sha=contents_exist.sha)
                except Exception:
                    repo.create_file(path=LOCK_FILE_PATH, message=f"LOCK // {current_user}", content=lock_string, branch="main")
                st.toast(f"Llave de seguridad Xenocode activada", icon="🔒")
            except Exception:
                pass

# ==============================================================================
# 5. MOTOR DE LOGÍSTICA DE DATOS (LECTURA / CREACIÓN AUTOMÁTICA EN GITHUB)
# ==============================================================================
def get_wallet_data_from_git():
    if 'df_wallet' not in st.session_state or st.session_state.get('force_reload', False):
        try:
            g = Github(TOKEN)
            repo = g.get_repo(REPO_NAME)
            try:
                # Intenta descargar el archivo existente
                contents = repo.get_contents(FILE_PATH, ref="main")
                df_load = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
            except Exception:
                # SI NO EXISTE LA MATRIZ, SE CREA CON EJEMPLOS EN TU REPOSITORIO AUTOMÁTICAMENTE
                start_date = datetime(2026, 5, 1)
                ejemplos = [
                    {"Fecha": (start_date).strftime("%Y-%m-%d %H:%M"), "Tipo": "Ingreso", "Categoria": "Nomina", "Concepto": "Pago Quincena 1 JYPESA", "Monto": 35000.0, "Cuenta": "Banco MX (Core)"},
                    {"Fecha": (start_date + timedelta(days=5)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Ingreso", "Categoria": "Freelance", "Concepto": "Proyecto Xenocode UI", "Monto": 15000.0, "Cuenta": "USD Wallet (Hedge)"},
                    {"Fecha": (start_date + timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Gasto", "Categoria": "Renta", "Concepto": "Renta Oficinas", "Monto": -18000.0, "Cuenta": "Banco MX (Core)"},
                    {"Fecha": (start_date + timedelta(days=3)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Gasto", "Categoria": "Servicios", "Concepto": "CFE Terminal Nexion", "Monto": -1200.0, "Cuenta": "Banco MX (Core)"},
                    {"Fecha": (start_date + timedelta(days=7)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Gasto", "Categoria": "Restaurantes", "Concepto": "Cena de Negocios", "Monto": -3200.0, "Cuenta": "Banco MX (Core)"},
                    {"Fecha": (start_date + timedelta(days=12)).strftime("%Y-%m-%d %H:%M"), "Tipo": "Gasto", "Categoria": "Inversiones", "Concepto": "Compra Drop BTC", "Monto": -5000.0, "Cuenta": "Crypto Fund (Risk)"},
                ]
                df_load = pd.DataFrame(ejemplos)
                csv_string = df_load.to_csv(index=False)
                repo.create_file(path=FILE_PATH, message="INITIALIZE WALLET MATRIX", content=csv_string, branch="main")
                st.toast("Matriz financiera creada exitosamente en GitHub", icon="🚀")
            
            df_load['Fecha'] = pd.to_datetime(df_load['Fecha'])
            st.session_state.df_wallet = df_load
            st.session_state.force_reload = False
        except Exception as e:
            st.error(f"Error crítico en Matrix-GitHub: {e}")
            return pd.DataFrame()
            
    return st.session_state.df_wallet

# ==============================================================================
# 6. FLUJO DE CONTROL PRINCIPAL
# ==============================================================================

# --- SPLASH SCREEN ---
if not st.session_state.splash_completado:
    p = st.empty()
    for m in ["ESTABLISHING SECURE ACCESS...", "CONNECTING TO GITHUB REPO...", "SYNCING LEDGER MATRIX...", "READY..."]:
        with p.container():
            st.markdown(f"""
            <div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:80px;height:80px;border:2px solid rgba(255,255,255,0.05); border-top:2px solid #00FFAA; border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;letter-spacing:5px;color:white;">{m}</p>
            </div>
            <style> @keyframes spin {{ to {{ transform: rotate(360deg); }} }} </style>
            """, unsafe_allow_html=True)
            time.sleep(0.5)
    p.empty()
    st.session_state.splash_completado = True
    st.rerun()

# --- LOGIN FRAMEWORK ---
elif not st.session_state.autenticado:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        try:
            with open("n2.png", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                st.markdown(f'<div style="text-align:center"><img src="data:image/png;base64,{encoded}" width="180"></div>', unsafe_allow_html=True)
        except: st.markdown("<h1 style='text-align:center; color:#00FFAA;'>NEXION</h1>", unsafe_allow_html=True)

        with st.form("login_form"):
            user_input = st.text_input("USUARIO", placeholder="Rigoberto")
            pass_input = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")
            if st.form_submit_button("VERIFY IDENTITY", use_container_width=True):
                lista_usuarios = st.secrets.get("usuarios", {})
                if user_input in lista_usuarios and str(lista_usuarios[user_input]) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = user_input
                    st.rerun()
                else: st.error("ERROR: ACCESS DENIED.")

# --- PLATAFORMA TERMINAL DE CONTROL ---
else:
    # Verificación estricta de exclusividad
    if st.session_state.usuario_activo.upper() != "RIGOBERTO":
        st.markdown("<div style='text-align:center; padding:50px;'><h2 style='color:#FF3B30;'>⚠️ ACCESO TOTALMENTE RESTRINGIDO</h2><p>Módulo exclusivo de Dirección General.</p></div>", unsafe_allow_html=True)
        if st.button("⬅️ REGRESAR"):
            st.session_state.autenticado = False
            st.rerun()
        st.stop()

    # Lanzar fragmeto de control de candado
    verificar_y_renderizar_bloqueo()
    puede_editar_efectivo = st.session_state.get("puede_editar_efectivo", False)
    bloqueado_por_otro = st.session_state.get("bloqueado_por_otro_efectivo", False)

    # Cargar base de datos desde GitHub
    df_actual = get_wallet_data_from_git()

    # HEADER TERMINAL
    head_l, head_r = st.columns([5, 1])
    with head_l:
        st.markdown(f"<h1 style='color:#00FFAA; margin:0; font-family:monospace;'>XENOCODE // WALLET_MATRIX</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#8B949E; margin-top:5px; font-family:monospace;'>OPERATOR: {current_user} // SOURCE: GITHUB_REPOS // EDIT_MODE: {puede_editar_efectivo}</p>", unsafe_allow_html=True)
    with head_r:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔒 DISCONNECT", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.splash_completado = False
            st.rerun()

    # CALCULAR TOTALES DINÁMICOS
    saldos_actuales = {cuenta: datos['fondo_base'] for cuenta, datos in CUENTAS_MATRIX.items()}
    if not df_actual.empty:
        for cuenta in CUENTAS_MATRIX.keys():
            movs_cuenta = df_actual[df_actual['Cuenta'] == cuenta]
            saldos_actuales[cuenta] += movs_cuenta['Monto'].sum()

    total_general = sum(saldos_actuales.values())
    total_ingresos = df_actual[df_actual['Tipo'] == "Ingreso"]['Monto'].sum() if not df_actual.empty else 0
    total_egresos = abs(df_actual[df_actual['Tipo'] == "Gasto"]['Monto'].sum()) if not df_actual.empty else 0

    # --- KPI CARDS ---
    st.markdown("<br>", unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.markdown(f"<div class='kpi-card'><div class='kpi-label'>PATRIMONIO NETO CONSOLIDADO</div><div class='kpi-value'>${total_general:,.2f}</div><div class='kpi-trend' style='color:#8B949E'>MATRIZ EN NUBE CORE</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi-card' style='border-top:3px solid #00FFAA;'><div class='kpi-label'>INGRESOS HISTÓRICOS TOTALES</div><div class='kpi-value' style='color:#00FFAA;'>${total_ingresos:,.2f}</div><div class='kpi-trend' style='color:#00FFAA;'>▲ COMPILADO OK</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi-card' style='border-top:3px solid #FF3B30;'><div class='kpi-label'>EGRESOS HISTÓRICOS TOTALES</div><div class='kpi-value' style='color:#FF3B30;'>${total_egresos:,.2f}</div><div class='kpi-trend' style='color:#FF3B30;'>▼ AJUSTADO DE MATRIZ</div></div>", unsafe_allow_html=True)

    # --- GRÁFICOS INTERACTIVOS (Sincronizados y sin errores de Ticks) ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1.8])

    with g1:
        st.markdown("<p class='kpi-label' style='text-align:center;'>Estructura de Fondos por Cuenta</p>", unsafe_allow_html=True)
        fig_donut = go.Figure(data=[go.Pie(
            labels=list(saldos_actuales.keys()), values=list(saldos_actuales.values()), hole=.65,
            marker=dict(colors=[CUENTAS_MATRIX[c]['color'] for c in saldos_actuales.keys()], line=dict(color='#0E1117', width=3)),
            textinfo='percent', textfont=dict(family="monospace", size=13, color="white")
        )])
        fig_donut.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center", font=dict(family="monospace", color="#8B949E")),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

    with g2:
        st.markdown("<p class='kpi-label' style='text-align:center;'>Histórico de Flujos Guardados en GitHub</p>", unsafe_allow_html=True)
        if not df_actual.empty:
            df_actual['Fecha_Formato'] = df_actual['Fecha'].dt.strftime('%d/%m %H:%M')
            fig_flow = go.Figure()
            fig_flow.add_trace(go.Bar(name='Ingreso', x=df_actual['Fecha_Formato'], y=[m if m > 0 else 0 for m in df_actual['Monto']], marker_color='#00FFAA'))
            fig_flow.add_trace(go.Bar(name='Gasto', x=df_actual['Fecha_Formato'], y=[abs(m) if m < 0 else 0 for m in df_actual['Monto']], marker_color='#FF3B30'))
            fig_flow.update_layout(barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                   xaxis=dict(showgrid=False, color="#8B949E", tickfont=dict(family="monospace")),
                                   yaxis=dict(showgrid=True, gridcolor="#30363D", color="#8B949E", tickfont=dict(family="monospace"), zeroline=False),
                                   legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(family="monospace", color="#C9D1D9")),
                                   margin=dict(t=10, b=10, l=10, r=10), height=350, hovermode="x unified")
            st.plotly_chart(fig_flow, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")

    # --- OPERACIONES CON EXPORTACIÓN DIRECTA ---
    c_form, c_table = st.columns([1, 1.8])

    with c_form:
        st.markdown("<p class='kpi-label'>Nueva Operación en Nube</p>", unsafe_allow_html=True)
        
        btn_label = "SINCRONIZAR CON GITHUB" if puede_editar_efectivo else "🔒 MODO LECTURA BLOQUEADO"
        
        with st.form("elite_ops", clear_on_submit=True):
            f_monto = st.number_input("Cantidad MXN ($)", min_value=0.0, step=100.0)
            f_cat = st.selectbox("Categoría", CATEGORIAS)
            f_desc = st.text_input("Concepto / Referencia", placeholder="Ej. Gasolina Camión")
            f_cuenta = st.selectbox("Cuenta Destino", list(CUENTAS_MATRIX.keys()))
            
            b1, b2 = st.columns(2)
            gasto_sub = b1.form_submit_button("📉 GASTO", use_container_width=True, disabled=not puede_editar_efectivo)
            ingreso_sub = b2.form_submit_button("📈 INGRESO", use_container_width=True, disabled=not puede_editar_efectivo)
            
            if puede_editar_efectivo and (gasto_sub or ingreso_sub):
                if f_monto > 0 and f_desc:
                    with st.status("Escribiendo en GitHub Matrix...", expanded=True) as status:
                        try:
                            g = Github(TOKEN)
                            repo = g.get_repo(REPO_NAME)
                            
                            # Volver a leer para evitar colisiones
                            contents = repo.get_contents(FILE_PATH)
                            df_latest = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
                            
                            # Formar nueva fila
                            monto_final = -f_monto if gasto_sub else f_monto
                            nueva_fila = {
                                "Fecha": datetime.now(tz_gdl).strftime("%Y-%m-%d %H:%M"),
                                "Tipo": "Gasto" if gasto_sub else "Ingreso",
                                "Categoria": f_cat,
                                "Concepto": f_desc,
                                "Monto": monto_final,
                                "Cuenta": f_cuenta
                            }
                            
                            df_latest = pd.concat([df_latest, pd.DataFrame([nueva_fila])], ignore_index=True)
                            csv_updated = df_latest.to_csv(index=False)
                            
                            # Push a GitHub
                            hora_local = datetime.now(tz_gdl).strftime('%H:%M:%S')
                            repo.update_file(path=FILE_PATH, message=f"WALLET_UPDATE // {hora_local}", content=csv_updated, sha=contents.sha)
                            
                            # Intentar liberar candado de inmediato
                            try:
                                lock_file_now = repo.get_contents(LOCK_FILE_PATH)
                                repo.delete_file(path=LOCK_FILE_PATH, message=f"UNLOCK // {current_user}", sha=lock_file_now.sha)
                            except: pass
                            
                            st.session_state.force_reload = True
                            status.update(label="¡Matriz Sincronizada y Liberada!", state="complete", expanded=False)
                            st.toast("GitHub Actualizado", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fallo en comunicación: {e}")

    with c_table:
        st.markdown("<p class='kpi-label'>Ledger Ledger Consolidado (Historial Completo)</p>", unsafe_allow_html=True)
        if not df_actual.empty:
            df_ledger = df_actual.sort_values(by='Fecha', ascending=False).copy()
            df_ledger['Fecha'] = df_ledger['Fecha'].dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                df_ledger[['Fecha', 'Tipo', 'Categoria', 'Concepto', 'Monto', 'Cuenta']].style
                .format({'Monto': '${:,.2f}'})
                .map(lambda val: 'color: #00FFAA' if val > 0 else 'color: #FF3B30', subset=['Monto']),
                use_container_width=True, hide_index=True, height=300
            )





















































































































































