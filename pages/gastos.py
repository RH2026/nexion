import io
import json
import time
import hashlib
import hmac
import html
from datetime import datetime, timedelta

from github import Github
import pandas as pd
import pytz
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from components.layout import render_layout


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(page_title="JYPESA | Ahorros Personales", layout="wide", initial_sidebar_state="collapsed")

tz_gdl = pytz.timezone("America/Mexico_City")
hoy = datetime.now(tz_gdl)

render_layout(modulo_actual="FINANZAS", submodulo_actual="GASTOS")


# ============================================================
# SEGURIDAD PRIVADA
# ============================================================

def validar_acceso_privado():
    usuario = st.session_state.get("usuario_activo", "")

    if usuario.upper() != "RIGOBERTO":
        st.error("ACCESO NO DISPONIBLE.")
        st.stop()

    if st.session_state.get("wallet_private_access", False):
        return

    hash_guardado = st.secrets.get("NEXION_PRIVATE_GATE_HASH", "")

    if not hash_guardado:
        st.error("MÓDULO BLOQUEADO.")
        st.stop()

    intentos = st.session_state.get("wallet_gate_attempts", 0)

    if intentos >= 5:
        st.error("ACCESO BLOQUEADO.")
        st.stop()

    st.markdown("""<div style="max-width:420px;margin:90px auto 30px auto;text-align:center;"><div style="font-size:34px;margin-bottom:18px;">🔐</div><div style="color:#FFFFFF;font-size:16px;font-weight:700;letter-spacing:2px;">ACCESO RESTRINGIDO</div><div style="color:#8B9BB4;font-size:11px;letter-spacing:1px;margin-top:8px;">AUTORIZACIÓN REQUERIDA</div></div>""", unsafe_allow_html=True)

    _, centro, _ = st.columns([2, 1, 2])

    with centro:
        clave = st.text_input("Código de autorización", type="password", key="wallet_private_gate_input", label_visibility="collapsed", placeholder="Código de autorización")
        verificar = st.button("AUTORIZAR ACCESO", use_container_width=True, key="wallet_private_gate_button")

        if verificar:
            if not clave:
                st.warning("Código requerido.")
                st.stop()

            hash_ingresado = hashlib.sha256(clave.encode("utf-8")).hexdigest()

            if hmac.compare_digest(hash_ingresado, hash_guardado):
                st.session_state.wallet_private_access = True
                st.session_state.wallet_gate_attempts = 0
                st.session_state.pop("wallet_private_gate_input", None)
                st.rerun()
            else:
                st.session_state.wallet_gate_attempts = intentos + 1
                restantes = max(0, 5 - st.session_state.wallet_gate_attempts)

                if restantes:
                    st.error(f"Código no válido. Intentos restantes: {restantes}")
                else:
                    st.error("ACCESO BLOQUEADO.")

                st.stop()

    st.stop()


validar_acceso_privado()


# ============================================================
# GITHUB
# ============================================================

TOKEN = st.secrets.get("GITHUB_TOKEN", None)

REPO_NAME = "RH2026/nexion"
FILE_PATH = "cartera.csv"
LOCK_FILE_PATH = "lock_cartera.json"
PLAN_FILE_PATH = "plan_financiero_semanal.csv"

current_user = st.session_state.get("usuario_activo", "UNKNOWN")

puede_editar = current_user.upper() == "RIGOBERTO"


# ============================================================
# CUENTAS
# ============================================================

CUENTAS_MATRIX = {
    "Caja de Ahorros": {"color": "#305496", "fondo_base": 0.00},
    "Scottiabank": {"color": "#0099CC", "fondo_base": 0.00},
    "Santander": {"color": "#5D5B5B", "fondo_base": 0.00},
    "Cartera": {"color": "#8497B0", "fondo_base": 0.00},
    "Ahorro Mensual": {"color": "#2F75B5", "fondo_base": 0.00}
}


# ============================================================
# CATEGORÍAS
# ============================================================

CATEGORIAS = [
    "Nómina",
    "Ahorros",
    "Ventas",
    "Freelance / Proyectos",
    "Rendimientos",
    "Reembolsos",
    "Renta",
    "Servicios Fijos",
    "Conectividad",
    "Mantenimiento",
    "Supermercado",
    "Restaurantes",
    "Cafeterías y Snacks",
    "Gasolina",
    "Mantenimiento Automotriz",
    "Trámites y Seguros",
    "Transporte Alternativo",
    "Mascotas",
    "Gastos Familiares",
    "Educación",
    "Deportes y Entrenamiento",
    "Cuidado Personal",
    "Gastos Médicos",
    "Suscripciones y Software",
    "Equipo y Gadgets",
    "Entretenimiento",
    "Ropa y Calzado",
    "Regalos",
    "Pago de Tarjetas",
    "Inversiones",
    "Ahorro",
    "Comisiones",
    "Varios"
]


# ============================================================
# PLAN SEMANAL
# ============================================================

INGRESO_SEMANAL = 4450.00
GASTO_CASA = 1500.00
GASOLINA = 600.00
CONSULTA = 350.00
GASTOS_HIJA = 250.00

TOTAL_GASTOS_SEMANALES = GASTO_CASA + GASOLINA + CONSULTA + GASTOS_HIJA

AHORRO_TV_SEM = 225.00
AHORRO_PRESTAMO_SEM = 400.00
AHORRO_INTERNET_SEM = 275.00

TOTAL_AHORRO_MENSUAL_SEM = AHORRO_TV_SEM + AHORRO_PRESTAMO_SEM + AHORRO_INTERNET_SEM

TOTAL_APARTADO_SEMANAL = TOTAL_GASTOS_SEMANALES + TOTAL_AHORRO_MENSUAL_SEM

DISPONIBLE_SEMANAL = INGRESO_SEMANAL - TOTAL_APARTADO_SEMANAL

# ============================================================
# CSS
# ============================================================

st.markdown("""<style>div[data-testid="stBlock"]{max-width:100%!important;padding:0!important;}header[data-testid="stHeader"]{background:#1D2A35!important;border-bottom:2px solid #34495E!important;}.kpi-card,.plan-card{width:100%!important;min-width:0!important;box-sizing:border-box!important;background:#253441!important;border:1px solid #34495E!important;border-radius:8px!important;padding:16px!important;margin:0 0 12px 0!important;overflow:hidden!important;}.kpi-card{text-align:center!important;box-shadow:0 4px 6px rgba(0,0,0,.20)!important;}.kpi-label{color:#8B9BB4!important;font-size:11px!important;font-weight:800!important;text-transform:uppercase!important;letter-spacing:1.4px!important;}.kpi-value{color:#FFFFFF!important;font-size:30px!important;font-weight:800!important;margin:8px 0!important;white-space:nowrap!important;}.kpi-trend{font-size:12px!important;font-weight:800!important;white-space:nowrap!important;}.neon-bar{height:3px!important;border-radius:2px!important;margin-top:9px!important;width:100%!important;}.plan-title{color:#FFFFFF!important;font-size:12px!important;font-weight:800!important;letter-spacing:1px!important;text-transform:uppercase!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;}.plan-value{color:#00FFAA!important;font-size:25px!important;font-weight:800!important;margin-top:7px!important;white-space:nowrap!important;}.plan-sub{color:#8B9BB4!important;font-size:10px!important;text-transform:uppercase!important;letter-spacing:.8px!important;margin-top:4px!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;}div.stButton>button{width:100%!important;background:#2B343B!important;color:#FFFFFF!important;border:1px solid #34495E!important;border-radius:5px!important;font-size:12px!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:1px!important;}div.stButton>button:hover{background:#00A3A3!important;color:#FFFFFF!important;border-color:#00A3A3!important;box-shadow:0 0 15px rgba(0,255,170,.35)!important;}div[data-baseweb="tab-list"]{gap:18px!important;border-bottom:2px solid #34495E!important;margin-bottom:15px!important;}div[data-baseweb="tab"]{background:transparent!important;color:#8B9BB4!important;font-weight:800!important;font-size:12px!important;border:none!important;padding-top:0!important;padding-bottom:10px!important;}div[aria-selected="true"]{color:#00FFAA!important;border-bottom:3px solid #00FFAA!important;}.nx-table-wrap{width:100%;background:#202B33;border:1px solid #34495E;border-radius:8px;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.18);}.nx-table-scroll{width:100%;overflow:auto;scrollbar-width:thin;scrollbar-color:#40525D #182229;}.nx-table-scroll::-webkit-scrollbar{width:7px;height:7px;}.nx-table-scroll::-webkit-scrollbar-track{background:#182229;}.nx-table-scroll::-webkit-scrollbar-thumb{background:#40525D;border-radius:8px;}.nx-table-scroll::-webkit-scrollbar-thumb:hover{background:#00A3A3;}.nx-table{width:100%;border-collapse:separate;border-spacing:0;font-family:Inter,Arial,sans-serif;font-size:11px;color:#E8EEF2;}.nx-table thead{position:sticky;top:0;z-index:3;}.nx-table th{background:#182229;color:#8B9BB4;text-align:left;font-size:9px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;padding:12px 13px;border-bottom:1px solid #34495E;white-space:nowrap;}.nx-table td{padding:11px 13px;border-bottom:1px solid rgba(52,73,94,.55);white-space:nowrap;vertical-align:middle;}.nx-table tbody tr{background:#202B33;transition:background .15s ease,box-shadow .15s ease;}.nx-table tbody tr:nth-child(even){background:#1E2930;}.nx-table tbody tr:hover{background:#263740;box-shadow:inset 3px 0 0 #00FFAA;}.nx-table tbody tr:last-child td{border-bottom:none;}.nx-table td:first-child{color:#B9C5CD;font-weight:600;}.nx-badge{display:inline-flex;align-items:center;justify-content:center;min-width:68px;padding:4px 8px;border-radius:4px;font-size:9px;font-weight:800;letter-spacing:.6px;background:#2B343B;border:1px solid #465762;color:#B9C5CD;}.nx-income{color:#00FFAA;background:rgba(0,255,170,.08);border-color:rgba(0,255,170,.28);}.nx-expense{color:#FF6B6B;background:rgba(255,75,75,.08);border-color:rgba(255,75,75,.28);}.nx-fixed{color:#FFD166;background:rgba(255,209,102,.08);border-color:rgba(255,209,102,.25);}.nx-saving{color:#00E5FF;background:rgba(0,229,255,.08);border-color:rgba(0,229,255,.25);}.nx-free{color:#00FFAA;background:rgba(0,255,170,.08);border-color:rgba(0,255,170,.25);}.nx-transfer{color:#B388FF;background:rgba(179,136,255,.10);border-color:rgba(179,136,255,.30);}.nx-neutral{color:#B9C5CD;background:#2B343B;border-color:#465762;}.nx-money-pos{color:#00FFAA!important;font-weight:800!important;text-align:right;}.nx-money-neg{color:#FF6B6B!important;font-weight:800!important;text-align:right;}</style>""", unsafe_allow_html=True)


# ============================================================
# RENDER PREMIUM DE TABLAS
# ============================================================

def render_tabla_premium(df, moneda_cols=None, max_height=430):
    if df is None or df.empty:
        st.info("No existen registros para mostrar.")
        return

    moneda_cols = moneda_cols or []
    html_table = f'<div class="nx-table-wrap"><div class="nx-table-scroll" style="max-height:{max_height}px;"><table class="nx-table"><thead><tr>'

    for col in df.columns:
        html_table += f"<th>{html.escape(str(col))}</th>"

    html_table += "</tr></thead><tbody>"

    for _, row in df.iterrows():
        html_table += "<tr>"

        for col in df.columns:
            valor = "" if pd.isna(row[col]) else row[col]
            texto = html.escape(str(valor))

            if col in moneda_cols:
                try:
                    numero = float(valor)
                    clase = "nx-money-pos" if numero >= 0 else "nx-money-neg"
                    texto = f"${numero:,.2f}"
                    html_table += f'<td class="{clase}">{texto}</td>'
                except:
                    html_table += f"<td>{texto}</td>"

            elif str(col).upper() == "TIPO":
                tipo = str(valor).strip()
                tipo_lower = tipo.lower()

                if tipo_lower == "ingreso":
                    clase = "nx-income"
                elif tipo_lower == "gasto":
                    clase = "nx-expense"
                elif tipo_lower == "gasto fijo":
                    clase = "nx-fixed"
                elif tipo_lower == "ahorro mensual":
                    clase = "nx-saving"
                elif tipo_lower == "disponible":
                    clase = "nx-free"
                elif tipo_lower == "transferencia":
                    clase = "nx-transfer"
                else:
                    clase = "nx-neutral"

                html_table += f'<td><span class="nx-badge {clase}">{html.escape(tipo.upper())}</span></td>'

            else:
                html_table += f"<td>{texto}</td>"

        html_table += "</tr>"

    html_table += "</tbody></table></div></div>"
    st.markdown(html_table, unsafe_allow_html=True)


# ============================================================
# LOCK
# SOLO SE CONSULTA. NO SE CREA AL ENTRAR.
# ============================================================

def leer_lock():
    if not TOKEN:
        return None

    try:
        repo = Github(TOKEN).get_repo(REPO_NAME)
        contenido = repo.get_contents(LOCK_FILE_PATH, ref="main")
        data = json.loads(contenido.decoded_content.decode("utf-8"))
        timestamp = data.get("timestamp")

        if not timestamp:
            return None

        momento = tz_gdl.localize(datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"))
        edad = (datetime.now(tz_gdl) - momento).total_seconds()

        if edad >= 600:
            return None

        return data

    except:
        return None


def crear_lock():
    if not TOKEN:
        return False

    try:
        repo = Github(TOKEN).get_repo(REPO_NAME)
        ahora = datetime.now(tz_gdl)

        lock_data = {
            "usuario": current_user,
            "timestamp": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "hora": ahora.strftime("%H:%M:%S")
        }

        contenido = json.dumps(lock_data, indent=4)

        try:
            archivo = repo.get_contents(LOCK_FILE_PATH, ref="main")

            repo.update_file(
                path=LOCK_FILE_PATH,
                message=f"LOCK // {current_user}",
                content=contenido,
                sha=archivo.sha,
                branch="main"
            )

        except:
            repo.create_file(
                path=LOCK_FILE_PATH,
                message=f"LOCK // {current_user}",
                content=contenido,
                branch="main"
            )

        return True

    except:
        return False


def liberar_lock():
    if not TOKEN:
        return

    try:
        repo = Github(TOKEN).get_repo(REPO_NAME)
        archivo = repo.get_contents(LOCK_FILE_PATH, ref="main")

        repo.delete_file(
            path=LOCK_FILE_PATH,
            message=f"UNLOCK // {current_user}",
            sha=archivo.sha,
            branch="main"
        )

    except:
        pass


lock_info = leer_lock()

bloqueado_por_otro = bool(
    lock_info and
    lock_info.get("usuario", "").upper() != current_user.upper()
)

puede_editar_efectivo = (
    puede_editar and
    not bloqueado_por_otro and
    bool(TOKEN)
)

st.session_state["bloqueado_por_otro_efectivo"] = bloqueado_por_otro
st.session_state["puede_editar_efectivo"] = puede_editar_efectivo

if bloqueado_por_otro:
    st.warning(
        f"⚠️ MÓDULO PAUSADO: sesión activa de **{lock_info.get('usuario','OTRO USUARIO')}**."
    )


# ============================================================
# DATOS CARTERA
# ============================================================

def get_wallet_data_from_git():
    if "df_wallet" in st.session_state and not st.session_state.get("force_reload", False):
        return st.session_state.df_wallet

    ahora = datetime.now(tz_gdl)

    ejemplos = [
        {
            "Fecha": (ahora - timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
            "Tipo": "Ingreso",
            "Categoria": "Nómina",
            "Concepto": "Pago Quincena 1 JYPESA",
            "Monto": 35000.0,
            "Cuenta": "Caja Jypesa"
        },
        {
            "Fecha": (ahora - timedelta(days=8)).strftime("%Y-%m-%d %H:%M"),
            "Tipo": "Gasto",
            "Categoria": "Renta",
            "Concepto": "Renta Oficinas",
            "Monto": -18000.0,
            "Cuenta": "Santander"
        },
        {
            "Fecha": (ahora - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
            "Tipo": "Ingreso",
            "Categoria": "Freelance / Proyectos",
            "Concepto": "Proyecto Xenocode UI",
            "Monto": 15000.0,
            "Cuenta": "Scottiabank"
        },
        {
            "Fecha": (ahora - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "Tipo": "Gasto",
            "Categoria": "Supermercado",
            "Concepto": "Compras Semanales",
            "Monto": -3500.0,
            "Cuenta": "Cartera"
        }
    ]

    df = pd.DataFrame(ejemplos)

    if TOKEN:
        try:
            repo = Github(TOKEN).get_repo(REPO_NAME)

            try:
                archivo = repo.get_contents(FILE_PATH, ref="main")
                df = pd.read_csv(
                    io.StringIO(archivo.decoded_content.decode("utf-8")),
                    keep_default_na=False
                )

            except:
                repo.create_file(
                    path=FILE_PATH,
                    message="INITIALIZE WALLET MATRIX",
                    content=df.to_csv(index=False),
                    branch="main"
                )

        except Exception as e:
            st.warning(f"GitHub no disponible: {e}")

    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    if "Monto" in df.columns:
        df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0)

    st.session_state.df_wallet = df
    st.session_state.force_reload = False

    return df


# ============================================================
# DATOS PLAN
# ============================================================

def get_plan_data_from_git(force_reload=False):
    if force_reload:
        st.session_state.force_reload_plan = True

    if "df_plan_semanal" in st.session_state and not st.session_state.get("force_reload_plan", False):
        return st.session_state.df_plan_semanal

    columnas = [
        "Fecha_Corte",
        "Semana",
        "Ingreso_Semanal",
        "Gastos_Fijos",
        "Ahorro_Semanal",
        "Disponible",
        "Usuario"
    ]

    df = pd.DataFrame(columns=columnas)

    if TOKEN:
        try:
            repo = Github(TOKEN).get_repo(REPO_NAME)

            try:
                archivo = repo.get_contents(PLAN_FILE_PATH, ref="main")
                df = pd.read_csv(
                    io.StringIO(archivo.decoded_content.decode("utf-8")),
                    keep_default_na=False
                )

            except:
                repo.create_file(
                    path=PLAN_FILE_PATH,
                    message="INITIALIZE WEEKLY FINANCIAL PLAN",
                    content=df.to_csv(index=False),
                    branch="main"
                )

        except Exception as e:
            st.warning(f"No fue posible sincronizar el plan: {e}")

    st.session_state.df_plan_semanal = df
    st.session_state.force_reload_plan = False

    return df


# ============================================================
# PREPARAR CARTERA
# ============================================================

df_actual = get_wallet_data_from_git()

if not df_actual.empty:
    df_actual["Mes"] = pd.to_datetime(
        df_actual["Fecha"],
        errors="coerce"
    ).dt.strftime("%Y-%m")

    mes_actual = datetime.now(tz_gdl).strftime("%Y-%m")

    df_month = df_actual[
        df_actual["Mes"] == mes_actual
    ].copy()

else:
    df_month = pd.DataFrame()


# ============================================================
# SALDOS
# ============================================================

saldos_actuales = {
    cuenta: datos["fondo_base"]
    for cuenta, datos in CUENTAS_MATRIX.items()
}

if not df_actual.empty:
    for cuenta in CUENTAS_MATRIX:
        saldos_actuales[cuenta] += pd.to_numeric(
            df_actual.loc[
                df_actual["Cuenta"] == cuenta,
                "Monto"
            ],
            errors="coerce"
        ).fillna(0).sum()

total_general = sum(saldos_actuales.values())

inc_month = (
    df_month.loc[
        df_month["Tipo"] == "Ingreso",
        "Monto"
    ].sum()
    if not df_month.empty else 0
)

exp_month = (
    abs(
        df_month.loc[
            df_month["Tipo"] == "Gasto",
            "Monto"
        ].sum()
    )
    if not df_month.empty else 0
)

net_month = inc_month - exp_month


# ============================================================
# TABS
# ============================================================

tab_kpi, tab_flujos, tab_registro, tab_plan = st.tabs(
    [
        "KPI'S WALLET",
        "FLUJOS DE EFECTIVO",
        "REGISTRO NUBE",
        "PLAN SEMANAL"
    ]
)


# ============================================================
# TAB 1
# ============================================================

with tab_kpi:

    st.markdown("<br>", unsafe_allow_html=True)

    k1, k2, k3 = st.columns(
        [1, 1, 1],
        gap="small"
    )

    tarjetas_kpi = [
        (
            k1,
            "PATRIMONIO NETO",
            total_general,
            "#00E5FF",
            "BALANCE GLOBAL"
        ),
        (
            k2,
            "INGRESOS MTD",
            inc_month,
            "#00FFAA",
            "FLUJO DE ENTRADA"
        ),
        (
            k3,
            "EGRESOS MTD",
            exp_month,
            "#FF4B4B",
            "GASTOS DEL MES"
        )
    ]

    for col, titulo, valor, color, sub in tarjetas_kpi:

        with col:

            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-label">{titulo}</div><div class="kpi-value">${valor:,.2f}</div><div class="kpi-trend" style="color:{color}">{sub}</div><div class="neon-bar" style="background:linear-gradient(90deg,{color},transparent);"></div></div>""",
                unsafe_allow_html=True
            )

    st.markdown(
        "<hr style='border-color:#34495E;'>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p class='kpi-label'><span style='color:#00E5FF'>🔍</span> DISTRIBUCIÓN DE CAPITAL POR CUENTA</p>",
        unsafe_allow_html=True
    )

    nombres = list(saldos_actuales.keys())
    valores = list(saldos_actuales.values())
    colores = [
        CUENTAS_MATRIX[x]["color"]
        for x in nombres
    ]

    fig = go.Figure(
        go.Bar(
            x=valores,
            y=nombres,
            orientation="h",
            marker=dict(
                color=colores,
                line=dict(width=0)            
            ),
            text=valores,
            texttemplate="%{text:$,.2f}",
            textposition="auto",
            textfont=dict(
                color="#FFFFFF",
                size=14
            ),
            hovertemplate="<b>%{y}</b><br>Saldo: %{x:$,.2f}<extra></extra>"
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(
            t=10,
            b=10,
            l=10,
            r=10
        ),
        height=350,
        xaxis=dict(
            showgrid=True,
            gridcolor="#34495E",
            color="#8B9BB4",
            tickformat="$,.0f"
        ),
        yaxis=dict(
            color="#E0E6ED",
            autorange="reversed"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# ============================================================
# TAB 2
# ============================================================

with tab_flujos:

    st.markdown("<br>", unsafe_allow_html=True)

    flujo1, flujo2 = st.columns(
        [2, 1.5],
        gap="small"
    )

    with flujo1:

        st.markdown(
            "<p class='kpi-label'>TENDENCIA DE FLUJO <span style='color:#8B9BB4'>(MES ACTUAL)</span></p>",
            unsafe_allow_html=True
        )

        if not df_month.empty:

            df_daily = (
                df_month
                .groupby(
                    [
                        df_month["Fecha"].dt.date,
                        "Tipo"
                    ]
                )["Monto"]
                .sum()
                .unstack()
                .fillna(0)
            )

            if "Ingreso" not in df_daily:
                df_daily["Ingreso"] = 0

            if "Gasto" not in df_daily:
                df_daily["Gasto"] = 0

            df_daily["Gasto"] = abs(
                df_daily["Gasto"]
            )

            fig_flow = go.Figure()

            fig_flow.add_trace(
                go.Scatter(
                    x=df_daily.index,
                    y=df_daily["Ingreso"],
                    name="Ingresos",
                    mode="lines",
                    line=dict(
                        width=3,
                        color="#00FFAA"
                    ),
                    fill="tozeroy",
                    fillcolor="rgba(0,255,170,.05)"
                )
            )

            fig_flow.add_trace(
                go.Scatter(
                    x=df_daily.index,
                    y=df_daily["Gasto"],
                    name="Egresos",
                    mode="lines",
                    line=dict(
                        width=3,
                        color="#FF4B4B"
                    ),
                    fill="tozeroy",
                    fillcolor="rgba(255,75,75,.05)"
                )
            )

            fig_flow.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=False,
                    color="#8B9BB4"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#34495E",
                    color="#8B9BB4"
                ),
                legend=dict(
                    orientation="h",
                    y=1.1,
                    x=.5,
                    xanchor="center",
                    font=dict(
                        color="#E0E6ED"
                    )
                ),
                margin=dict(
                    t=10,
                    b=10,
                    l=10,
                    r=10
                ),
                height=350,
                hovermode="x unified"
            )

            st.plotly_chart(
                fig_flow,
                use_container_width=True,
                config={"displayModeBar": False}
            )

        else:
            st.info("Sin movimientos este mes.")

    with flujo2:

        st.markdown(
            "<p class='kpi-label'>ANÁLISIS DE CONSUMO POR CATEGORÍA</p>",
            unsafe_allow_html=True
        )

        if not df_month.empty:

            gastos = (
                df_month[
                    df_month["Tipo"] == "Gasto"
                ]
                .groupby("Categoria")["Monto"]
                .sum()
                .abs()
                .reset_index()
                .sort_values("Monto")
            )

            if not gastos.empty:

                fig_cat = px.bar(
                    gastos,
                    x="Monto",
                    y="Categoria",
                    orientation="h",
                    text_auto=",.0f"
                )

                n = len(gastos)

                colors = [
                    "#44B3E1"
                    if i == n - 1
                    else "#4D93D9"
                    if i >= n - 3
                    else "#215C98"
                    for i in range(n)
                ]

                fig_cat.update_traces(
                    marker_color=colors,
                    textposition="outside",
                    hovertemplate="%{y}: $%{x:,.2f}"
                )

                fig_cat.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(
                        title=None,
                        showgrid=True,
                        gridcolor="#34495E",
                        color="#8B9BB4",
                        tickformat="$,.0f"
                    ),
                    yaxis=dict(
                        title=None,
                        color="#E0E6ED"
                    ),
                    margin=dict(
                        t=10,
                        b=10,
                        l=10,
                        r=10
                    ),
                    height=350
                )

                st.plotly_chart(
                    fig_cat,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

            else:
                st.info("Sin gastos registrados este mes.")

        else:
            st.info("Sin movimientos este mes.")


# ============================================================
# TAB 3
# ============================================================

with tab_registro:

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "<p class='kpi-label'><span style='color:#00E5FF'>⚡</span> EJECUTAR ORDEN DE REGISTRO</p>",
        unsafe_allow_html=True
    )

    if not TOKEN:
        st.warning(
            "GITHUB_TOKEN no está configurado. El módulo funciona en modo lectura."
        )

    f1, f2, f3, f4 = st.columns(
        [1, 1, 1, 1],
        gap="small"
    )

    with f1:
        f_monto = st.number_input(
            "Cantidad MXN",
            min_value=0.0,
            step=100.0,
            key="inp_monto_nube"
        )

    with f2:
        f_cat = st.selectbox(
            "Categoría",
            CATEGORIAS,
            key="inp_cat_nube"
        )

    with f3:
        f_desc = st.text_input(
            "Concepto / Referencia",
            placeholder="Ej. Gastos de Operación",
            key="inp_desc_nube"
        )

    with f4:
        f_cuenta = st.selectbox(
            "Cuenta Destino/Origen",
            list(CUENTAS_MATRIX.keys()),
            key="inp_cuenta_nube"
        )

    st.markdown(
        "<div style='height:8px'></div>",
        unsafe_allow_html=True
    )

    b1, b2 = st.columns(
        [1, 1],
        gap="small"
    )

    bloquear = (
        not puede_editar_efectivo
        or bloqueado_por_otro
        or not TOKEN
    )

    with b1:
        ingreso_sub = st.button(
            "REGISTRAR INGRESO",
            icon=":material/save:",
            use_container_width=True,
            key="btn_ingreso_action",
            disabled=bloquear
        )

    with b2:
        gasto_sub = st.button(
            "REGISTRAR GASTO",
            icon=":material/remove:",
            use_container_width=True,
            key="btn_gasto_action",
            disabled=bloquear
        )

    if not bloquear and (ingreso_sub or gasto_sub):

        if f_monto <= 0:
            st.error("Captura una cantidad mayor a cero.")

        elif not f_desc.strip():
            st.error("Captura el concepto o referencia.")

        else:

            lock_creado = False

            try:

                lock_creado = crear_lock()

                if not lock_creado:
                    st.error(
                        "No fue posible tomar el control de escritura en GitHub."
                    )
                    st.stop()

                repo = Github(TOKEN).get_repo(REPO_NAME)

                archivo = repo.get_contents(
                    FILE_PATH,
                    ref="main"
                )

                df_latest = pd.read_csv(
                    io.StringIO(
                        archivo.decoded_content.decode("utf-8")
                    ),
                    keep_default_na=False
                )

                nueva_fila = {
                    "Fecha": datetime.now(tz_gdl).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "Tipo": "Ingreso" if ingreso_sub else "Gasto",
                    "Categoria": f_cat,
                    "Concepto": f_desc.strip(),
                    "Monto": f_monto if ingreso_sub else -f_monto,
                    "Cuenta": f_cuenta
                }

                df_latest = pd.concat(
                    [
                        df_latest,
                        pd.DataFrame([nueva_fila])
                    ],
                    ignore_index=True
                )

                repo.update_file(
                    path=FILE_PATH,
                    message=f"UPDATE // {current_user} // {datetime.now(tz_gdl).strftime('%H:%M:%S')}",
                    content=df_latest.to_csv(index=False),
                    sha=archivo.sha,
                    branch="main"
                )

                st.session_state.force_reload = True

                st.success(
                    "OPERACIÓN CLASIFICADA EXITOSAMENTE."
                )

                time.sleep(.7)
                st.rerun()

            except Exception as e:

                st.error(
                    f"Error de sincronización: {e}"
                )

            finally:

                if lock_creado:
                    liberar_lock()


    # ========================================================
    # TRANSFERENCIA ENTRE CUENTAS
    # ========================================================

    st.markdown(
        "<div style='height:22px;border-top:1px solid rgba(52,73,94,.35);margin-top:18px;'></div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p class='kpi-label'><span style='color:#B388FF'>🔁</span> TRANSFERENCIA ENTRE CUENTAS</p>",
        unsafe_allow_html=True
    )

    t1, t2, t3, t4 = st.columns(
        [1, 1, 1, 1],
        gap="small"
    )

    with t1:
        t_origen = st.selectbox(
            "Cuenta Origen",
            list(CUENTAS_MATRIX.keys()),
            key="inp_origen_transferencia"
        )

    with t2:
        opciones_destino = [
            c for c in CUENTAS_MATRIX.keys()
            if c != t_origen
        ]

        t_destino = st.selectbox(
            "Cuenta Destino",
            opciones_destino,
            key="inp_destino_transferencia"
        )

    with t3:
        t_monto = st.number_input(
            "Cantidad MXN",
            min_value=0.0,
            step=100.0,
            key="inp_monto_transferencia"
        )

    with t4:
        t_desc = st.text_input(
            "Referencia (opcional)",
            placeholder="Ej. Reacomodo de fondos",
            key="inp_desc_transferencia"
        )

    st.caption(
        f"Saldo actual en {t_origen}: ${saldos_actuales.get(t_origen, 0):,.2f}"
        f"  ·  Saldo actual en {t_destino}: ${saldos_actuales.get(t_destino, 0):,.2f}"
    )

    st.markdown(
        "<div style='height:8px'></div>",
        unsafe_allow_html=True
    )

    bloquear_transferencia = (
        not puede_editar_efectivo
        or bloqueado_por_otro
        or not TOKEN
    )

    transferir_sub = st.button(
        "REALIZAR TRANSFERENCIA",
        icon=":material/sync_alt:",
        use_container_width=True,
        key="btn_transferencia_action",
        disabled=bloquear_transferencia
    )

    if not bloquear_transferencia and transferir_sub:

        if t_monto <= 0:
            st.error("Captura una cantidad mayor a cero.")

        elif t_origen == t_destino:
            st.error("La cuenta origen y la cuenta destino no pueden ser la misma.")

        else:

            lock_creado = False

            try:

                lock_creado = crear_lock()

                if not lock_creado:
                    st.error(
                        "No fue posible tomar el control de escritura en GitHub."
                    )
                    st.stop()

                repo = Github(TOKEN).get_repo(REPO_NAME)

                archivo = repo.get_contents(
                    FILE_PATH,
                    ref="main"
                )

                df_latest = pd.read_csv(
                    io.StringIO(
                        archivo.decoded_content.decode("utf-8")
                    ),
                    keep_default_na=False
                )

                fecha_movimiento = datetime.now(tz_gdl).strftime(
                    "%Y-%m-%d %H:%M"
                )

                referencia = t_desc.strip() or "Transferencia entre cuentas"

                fila_salida = {
                    "Fecha": fecha_movimiento,
                    "Tipo": "Transferencia",
                    "Categoria": "Transferencia entre Cuentas",
                    "Concepto": f"Transferencia a {t_destino} · {referencia}",
                    "Monto": -t_monto,
                    "Cuenta": t_origen
                }

                fila_entrada = {
                    "Fecha": fecha_movimiento,
                    "Tipo": "Transferencia",
                    "Categoria": "Transferencia entre Cuentas",
                    "Concepto": f"Transferencia de {t_origen} · {referencia}",
                    "Monto": t_monto,
                    "Cuenta": t_destino
                }

                df_latest = pd.concat(
                    [
                        df_latest,
                        pd.DataFrame([fila_salida, fila_entrada])
                    ],
                    ignore_index=True
                )

                repo.update_file(
                    path=FILE_PATH,
                    message=f"TRANSFER // {current_user} // {t_origen} -> {t_destino} // {datetime.now(tz_gdl).strftime('%H:%M:%S')}",
                    content=df_latest.to_csv(index=False),
                    sha=archivo.sha,
                    branch="main"
                )

                st.session_state.force_reload = True

                st.success(
                    f"TRANSFERENCIA REGISTRADA: ${t_monto:,.2f} de {t_origen} a {t_destino}."
                )

                time.sleep(.7)
                st.rerun()

            except Exception as e:

                st.error(
                    f"Error de sincronización: {e}"
                )

            finally:

                if lock_creado:
                    liberar_lock()


    # ========================================================
    # TABLA REAL DE CARTERA
    # ========================================================

    st.markdown(
        "<div style='color:#00FFAA;font-size:11px;font-weight:800;letter-spacing:1.5px;margin:25px 0 10px 0;'>REGISTROS DE CARTERA</div>",
        unsafe_allow_html=True
    )

    actualizar = st.button(
        "ACTUALIZAR REGISTROS",
        use_container_width=True,
        key="btn_refresh_wallet"
    )

    if actualizar:
        st.session_state.force_reload = True
        st.rerun()

    df_registros = get_wallet_data_from_git()

    if df_registros.empty:

        st.info("No existen movimientos registrados.")

    else:

        tabla = df_registros.copy()

        if "Fecha" in tabla.columns:

            tabla["Fecha"] = pd.to_datetime(
                tabla["Fecha"],
                errors="coerce"
            )

            tabla = tabla.sort_values(
                "Fecha",
                ascending=False
            )

            tabla["Fecha"] = tabla["Fecha"].dt.strftime(
                "%Y-%m-%d %H:%M"
            )

        if "Monto" in tabla.columns:
            tabla["Monto"] = pd.to_numeric(
                tabla["Monto"],
                errors="coerce"
            )

        columnas = [
            "Fecha",
            "Tipo",
            "Categoria",
            "Concepto",
            "Monto",
            "Cuenta"
        ]

        columnas = [
            c for c in columnas
            if c in tabla.columns
        ]

        tabla = tabla[columnas]

        render_tabla_premium(tabla, moneda_cols=["Monto"], max_height=430)

# ============================================================
# TAB 4 · PLAN SEMANAL
# ============================================================

with tab_plan:

    # ========================================================
    # CÁLCULO DEL FONDO DE PAGOS
    # ========================================================

    PAGO_TV = 900.00
    PAGO_INTERNET = 1100.00
    PAGO_PRESTAMO = 1600.00

    META_PAGOS_MES = PAGO_TV + PAGO_INTERNET + PAGO_PRESTAMO

    FECHA_TV = datetime(2026, 9, 25)
    FECHA_INTERNET = datetime(2026, 9, 27)
    FECHA_PRESTAMO = datetime(2026, 9, 28)

    FECHA_INICIO_CICLO = datetime(2026, 8, 28)

    hoy_sin_tz = hoy.replace(tzinfo=None)

    dias_desde_inicio = (hoy_sin_tz - FECHA_INICIO_CICLO).days

    if dias_desde_inicio < 0:
        viernes_transcurridos = 0
    else:
        viernes_transcurridos = (dias_desde_inicio // 7) + 1

    APARTADO_ACUMULADO = min(
        viernes_transcurridos * TOTAL_AHORRO_MENSUAL_SEM,
        META_PAGOS_MES
    )

    FALTA_META = max(
        0,
        META_PAGOS_MES - APARTADO_ACUMULADO
    )

    PORCENTAJE_META = (
        APARTADO_ACUMULADO / META_PAGOS_MES * 100
        if META_PAGOS_MES > 0
        else 0
    )

    progreso = min(PORCENTAJE_META, 100)

    dias_tv = (FECHA_TV - hoy_sin_tz).days
    dias_internet = (FECHA_INTERNET - hoy_sin_tz).days
    dias_prestamo = (FECHA_PRESTAMO - hoy_sin_tz).days

    # ========================================================
    # PRÓXIMO VIERNES
    # ========================================================

    dias_hasta_viernes = (4 - hoy_sin_tz.weekday()) % 7

    fecha_proximo_apartado = (
        hoy_sin_tz + timedelta(days=dias_hasta_viernes)
    )

    if dias_hasta_viernes == 0:
        proximo_viernes = "HOY"
    else:
        proximo_viernes = fecha_proximo_apartado.strftime("%d %b").upper()

    # ========================================================
    # ENCABEZADO
    # ========================================================

    st.markdown(
        "<div style='margin-bottom:18px;'>"
        "<div style='color:#FFFFFF;font-size:19px;font-weight:800;letter-spacing:.3px;'>PLAN SEMANAL</div>"
        "<div style='color:#8B9BB4;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>CONTROL DE FLUJO · APARTADOS · PAGOS PROGRAMADOS</div>"
        "</div>",
        unsafe_allow_html=True
    )

    # ========================================================
    # FONDO DE PAGOS
    # ========================================================

    color_progreso = "#00FFAA" if progreso >= 75 else "#00E5FF"

    fondo_html = (
        "<div style='background:linear-gradient(135deg,#202B33 0%,#182229 100%);"
        "border:1px solid #34495E;border-radius:10px;padding:20px 22px;"
        "box-shadow:0 10px 30px rgba(0,0,0,.20);margin-bottom:22px;'>"

        "<div style='display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:16px;'>"

        "<div>"
        "<div style='color:#FFFFFF;font-size:13px;font-weight:800;letter-spacing:1px;'>FONDO DE PAGOS</div>"
        "<div style='color:#8B9BB4;font-size:9px;font-weight:700;letter-spacing:1.3px;margin-top:4px;'>SEPTIEMBRE 2026 · META MENSUAL</div>"
        "</div>"

        "<div style='text-align:right;'>"
        f"<div style='color:{color_progreso};font-size:24px;font-weight:900;line-height:1;'>{progreso:.0f}%</div>"
        "<div style='color:#70808B;font-size:8px;font-weight:700;letter-spacing:1px;margin-top:4px;'>COBERTURA</div>"
        "</div>"

        "</div>"

        "<div style='display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:10px;'>"

        "<div>"
        f"<div style='color:#FFFFFF;font-size:28px;font-weight:900;line-height:1;'>${APARTADO_ACUMULADO:,.0f}</div>"
        f"<div style='color:#70808B;font-size:9px;font-weight:700;letter-spacing:1px;margin-top:6px;'>DE ${META_PAGOS_MES:,.0f} PROGRAMADOS</div>"
        "</div>"

        "<div style='text-align:right;'>"
        "<div style='color:#8B9BB4;font-size:9px;font-weight:800;letter-spacing:1px;'>FALTA</div>"
        f"<div style='color:#FFD166;font-size:17px;font-weight:900;margin-top:3px;'>${FALTA_META:,.0f}</div>"
        "</div>"

        "</div>"

        "<div style='height:8px;background:#111A20;border-radius:8px;overflow:hidden;border:1px solid #2F404A;'>"
        f"<div style='width:{progreso:.2f}%;height:100%;background:linear-gradient(90deg,#00A3A3,{color_progreso});border-radius:8px;box-shadow:0 0 12px rgba(0,255,170,.22);'></div>"
        "</div>"

        "<div style='display:flex;justify-content:space-between;align-items:center;margin-top:17px;padding-top:15px;border-top:1px solid rgba(52,73,94,.45);'>"

        "<div>"
        "<div style='color:#70808B;font-size:8px;font-weight:800;letter-spacing:1px;'>PRÓXIMO APARTADO</div>"
        f"<div style='color:#FFFFFF;font-size:13px;font-weight:800;margin-top:4px;'>{proximo_viernes} · ${TOTAL_AHORRO_MENSUAL_SEM:,.0f}</div>"
        "</div>"

        "<div style='display:flex;gap:22px;align-items:center;'>"

        "<div style='text-align:right;'>"
        "<div style='color:#70808B;font-size:8px;font-weight:800;letter-spacing:1px;'>TV</div>"
        f"<div style='color:#FFFFFF;font-size:11px;font-weight:800;margin-top:3px;'>{FECHA_TV.strftime('%d %b').upper()} · ${PAGO_TV:,.0f}</div>"
        "</div>"

        "<div style='text-align:right;'>"
        "<div style='color:#70808B;font-size:8px;font-weight:800;letter-spacing:1px;'>INTERNET</div>"
        f"<div style='color:#FFFFFF;font-size:11px;font-weight:800;margin-top:3px;'>{FECHA_INTERNET.strftime('%d %b').upper()} · ${PAGO_INTERNET:,.0f}</div>"
        "</div>"

        "<div style='text-align:right;'>"
        "<div style='color:#70808B;font-size:8px;font-weight:800;letter-spacing:1px;'>PRÉSTAMO</div>"
        f"<div style='color:#FFFFFF;font-size:11px;font-weight:800;margin-top:3px;'>{FECHA_PRESTAMO.strftime('%d %b').upper()} · ${PAGO_PRESTAMO:,.0f}</div>"
        "</div>"

        "</div>"
        "</div>"
        "</div>"
    )

    st.markdown(fondo_html, unsafe_allow_html=True)

    # ========================================================
    # DISTRIBUCIÓN DEL VIERNES DE PAGO
    # ========================================================

    st.markdown(
        "<div style='color:#FFFFFF;font-size:13px;font-weight:800;letter-spacing:1px;margin:4px 0 12px 0;'>DISTRIBUCIÓN DEL VIERNES DE PAGO</div>",
        unsafe_allow_html=True
    )

    disponible_color = "#00FFAA" if DISPONIBLE_SEMANAL >= 0 else "#FF6B6B"

    distribucion_html = (
        "<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;'>"

        "<div style='background:#202B33;border:1px solid #34495E;border-radius:7px;padding:13px 15px;'>"
        "<div style='color:#70808B;font-size:8px;font-weight:800;letter-spacing:1px;'>INGRESO</div>"
        f"<div style='color:#FFFFFF;font-size:18px;font-weight:900;margin-top:5px;'>${INGRESO_SEMANAL:,.0f}</div>"
        "</div>"

        "<div style='background:#202B33;border:1px solid #34495E;border-radius:7px;padding:13px 15px;'>"
        "<div style='color:#70808B;font-size:8px;font-weight:800;letter-spacing:1px;'>GASTOS</div>"
        f"<div style='color:#FF6B6B;font-size:18px;font-weight:900;margin-top:5px;'>${TOTAL_GASTOS_SEMANALES:,.0f}</div>"
        "</div>"

        "<div style='background:#202B33;border:1px solid #34495E;border-radius:7px;padding:13px 15px;'>"
        "<div style='color:#70808B;font-size:8px;font-weight:800;letter-spacing:1px;'>APARTADO</div>"
        f"<div style='color:#00E5FF;font-size:18px;font-weight:900;margin-top:5px;'>${TOTAL_AHORRO_MENSUAL_SEM:,.0f}</div>"
        "</div>"

        "<div style='background:#202B33;border:1px solid #34495E;border-radius:7px;padding:13px 15px;'>"
        "<div style='color:#70808B;font-size:8px;font-weight:800;letter-spacing:1px;'>DISPONIBLE</div>"
        f"<div style='color:{disponible_color};font-size:18px;font-weight:900;margin-top:5px;'>${DISPONIBLE_SEMANAL:,.0f}</div>"
        "</div>"

        "</div>"
    )

    st.markdown(distribucion_html, unsafe_allow_html=True)

    # ========================================================
    # TABLA DISTRIBUCIÓN
    # ========================================================

    df_distribucion = pd.DataFrame(
        [
            ["Gasto casa", GASTO_CASA],
            ["Gasolina", GASOLINA],
            ["Consulta", CONSULTA],
            ["Gastos hija", GASTOS_HIJA],
            ["TV", AHORRO_TV_SEM],
            ["Préstamo", AHORRO_PRESTAMO_SEM],
            ["Internet", AHORRO_INTERNET_SEM],
            ["Disponible", DISPONIBLE_SEMANAL],
        ],
        columns=["Concepto", "Monto"]
    )

    render_tabla_premium(
        df_distribucion,
        moneda_cols=["Monto"],
        max_height=330
    )

    st.markdown(
        "<div style='height:26px;border-top:1px solid rgba(52,73,94,.35);margin-top:6px;'></div>",
        unsafe_allow_html=True
    )

    # ========================================================
    # CALENDARIO DE PAGOS MENSUALES
    # ========================================================

    st.markdown(
        "<div style='color:#FFFFFF;font-size:13px;font-weight:800;letter-spacing:1px;margin:4px 0 12px 0;'>CALENDARIO DE PAGOS MENSUALES</div>",
        unsafe_allow_html=True
    )

    def estado_pago(fecha_pago):
        if hoy_sin_tz.date() > fecha_pago.date():
            return "VENCIDO"
        elif hoy_sin_tz.date() == fecha_pago.date():
            return "HOY"
        else:
            return "PENDIENTE"

    calendario_pagos = pd.DataFrame(
        [
            ["TV", FECHA_TV.strftime("%d/%m/%Y"), PAGO_TV, dias_tv, estado_pago(FECHA_TV)],
            ["Internet", FECHA_INTERNET.strftime("%d/%m/%Y"), PAGO_INTERNET, dias_internet, estado_pago(FECHA_INTERNET)],
            ["Préstamo", FECHA_PRESTAMO.strftime("%d/%m/%Y"), PAGO_PRESTAMO, dias_prestamo, estado_pago(FECHA_PRESTAMO)],
        ],
        columns=["Concepto", "Fecha", "Monto", "Días", "Estado"]
    )

    render_tabla_premium(
        calendario_pagos,
        moneda_cols=["Monto"],
        max_height=220
    )

    # ========================================================
    # REGISTRAR CORTE SEMANAL
    # ========================================================

    st.markdown(
        "<div style='height:26px;border-top:1px solid rgba(52,73,94,.35);margin-top:6px;'></div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='color:#FFFFFF;font-size:13px;font-weight:800;letter-spacing:1px;margin:4px 0 12px 0;'>REGISTRO DE CORTE SEMANAL</div>",
        unsafe_allow_html=True
    )

    fecha_corte = hoy_sin_tz.strftime("%d/%m/%Y")

    corte_actual = pd.DataFrame(
        [
            [
                fecha_corte,
                viernes_transcurridos,
                INGRESO_SEMANAL,
                TOTAL_GASTOS_SEMANALES,
                TOTAL_AHORRO_MENSUAL_SEM,
                DISPONIBLE_SEMANAL,
            ]
        ],
        columns=[
            "Fecha",
            "Semana",
            "Ingreso",
            "Gastos",
            "Apartado",
            "Disponible",
        ]
    )

    render_tabla_premium(
        corte_actual,
        moneda_cols=[
            "Ingreso",
            "Gastos",
            "Apartado",
            "Disponible",
        ],
        max_height=160
    )

    # ========================================================
    # BOTÓN REGISTRAR CORTE
    # ========================================================

    st.markdown(
        "<div style='height:8px'></div>",
        unsafe_allow_html=True
    )

    if puede_editar:

        if st.button(
            "REGISTRAR CORTE SEMANAL",
            key="btn_registrar_corte_semanal",
            use_container_width=True
        ):

            try:

                if TOKEN:

                    github = Github(TOKEN)
                    repo = github.get_repo(REPO_NAME)

                    try:
                        archivo_plan = repo.get_contents(PLAN_FILE_PATH)

                        contenido_actual = archivo_plan.decoded_content.decode(
                            "utf-8"
                        )

                        try:
                            df_plan_existente = pd.read_csv(
                                io.StringIO(contenido_actual)
                            )
                        except Exception:
                            df_plan_existente = pd.DataFrame()

                    except Exception:
                        archivo_plan = None
                        df_plan_existente = pd.DataFrame()

                    nuevo_corte = pd.DataFrame(
                        [
                            {
                                "Fecha": fecha_corte,
                                "Semana": viernes_transcurridos,
                                "Ingreso": INGRESO_SEMANAL,
                                "Gastos": TOTAL_GASTOS_SEMANALES,
                                "Apartado": TOTAL_AHORRO_MENSUAL_SEM,
                                "Disponible": DISPONIBLE_SEMANAL,
                            }
                        ]
                    )

                    if not df_plan_existente.empty:

                        columnas_plan = [
                            "Fecha",
                            "Semana",
                            "Ingreso",
                            "Gastos",
                            "Apartado",
                            "Disponible",
                        ]

                        for columna in columnas_plan:
                            if columna not in df_plan_existente.columns:
                                df_plan_existente[columna] = None

                        df_plan_existente = df_plan_existente[
                            columnas_plan
                        ]

                        existe_corte = (
                            df_plan_existente["Fecha"]
                            .astype(str)
                            .eq(fecha_corte)
                            & df_plan_existente["Semana"]
                            .astype(str)
                            .eq(str(viernes_transcurridos))
                        ).any()

                        if existe_corte:

                            st.warning(
                                "El corte de esta semana ya se encuentra registrado."
                            )

                        else:

                            df_plan_final = pd.concat(
                                [
                                    df_plan_existente,
                                    nuevo_corte
                                ],
                                ignore_index=True
                            )

                            contenido_nuevo = df_plan_final.to_csv(
                                index=False
                            )

                            if archivo_plan:

                                repo.update_file(
                                    archivo_plan.path,
                                    f"Registro corte semanal {fecha_corte}",
                                    contenido_nuevo,
                                    archivo_plan.sha
                                )

                            else:

                                repo.create_file(
                                    PLAN_FILE_PATH,
                                    f"Creación plan semanal {fecha_corte}",
                                    contenido_nuevo
                                )

                            st.success(
                                "Corte semanal registrado correctamente."
                            )

                            time.sleep(1)

                            st.rerun()

                    else:

                        contenido_nuevo = nuevo_corte.to_csv(
                            index=False
                        )

                        if archivo_plan:

                            repo.update_file(
                                archivo_plan.path,
                                f"Registro corte semanal {fecha_corte}",
                                contenido_nuevo,
                                archivo_plan.sha
                            )

                        else:

                            repo.create_file(
                                PLAN_FILE_PATH,
                                f"Creación plan semanal {fecha_corte}",
                                contenido_nuevo
                            )

                        st.success(
                            "Corte semanal registrado correctamente."
                        )

                        time.sleep(1)

                        st.rerun()

                else:

                    st.error(
                        "No se encontró GITHUB_TOKEN en los secrets."
                    )

            except Exception as e:

                st.error(
                    f"No fue posible registrar el corte: {e}"
                )

    else:

        st.info(
            "Solo RIGOBERTO puede registrar cortes semanales."
        )

    # ========================================================
    # HISTORIAL DE CORTES SEMANALES
    # ========================================================

    st.markdown(
        "<div style='height:26px;border-top:1px solid rgba(52,73,94,.35);margin-top:6px;'></div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='color:#FFFFFF;font-size:13px;font-weight:800;letter-spacing:1px;margin:4px 0 12px 0;'>HISTORIAL DE CORTES SEMANALES</div>",
        unsafe_allow_html=True
    )

    try:

        df_historial_plan = get_plan_data_from_git(
            force_reload=True
        )

        if df_historial_plan is not None and not df_historial_plan.empty:

            render_tabla_premium(
                df_historial_plan,
                moneda_cols=[
                    "Ingreso",
                    "Gastos",
                    "Apartado",
                    "Disponible",
                ],
                max_height=300
            )

        else:

            st.info(
                "Todavía no existen cortes semanales registrados."
            )

    except Exception as e:

        st.warning(
            f"No fue posible cargar el historial de cortes: {e}"
        )
