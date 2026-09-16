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
    "Caja de Ahorros": {"color": "#00E5FF", "fondo_base": 0.00},
    "Scottiabank": {"color": "#00FFAA", "fondo_base": 0.00},
    "Santander": {"color": "#FF4B4B", "fondo_base": 0.00},
    "Cartera": {"color": "#8B9BB4", "fondo_base": 0.00},
    "Ahorro Mensual": {"color": "#8B9BB8", "fondo_base": 0.00}
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

st.markdown("""<style>div[data-testid="stBlock"]{max-width:100%!important;padding:0!important;}header[data-testid="stHeader"]{background:#1D2A35!important;border-bottom:2px solid #34495E!important;}.kpi-card,.plan-card{width:100%!important;min-width:0!important;box-sizing:border-box!important;background:#253441!important;border:1px solid #34495E!important;border-radius:8px!important;padding:16px!important;margin:0 0 12px 0!important;overflow:hidden!important;}.kpi-card{text-align:center!important;box-shadow:0 4px 6px rgba(0,0,0,.20)!important;}.kpi-label{color:#8B9BB4!important;font-size:11px!important;font-weight:800!important;text-transform:uppercase!important;letter-spacing:1.4px!important;}.kpi-value{color:#FFFFFF!important;font-size:30px!important;font-weight:800!important;margin:8px 0!important;white-space:nowrap!important;}.kpi-trend{font-size:12px!important;font-weight:800!important;white-space:nowrap!important;}.neon-bar{height:3px!important;border-radius:2px!important;margin-top:9px!important;width:100%!important;}.plan-title{color:#FFFFFF!important;font-size:12px!important;font-weight:800!important;letter-spacing:1px!important;text-transform:uppercase!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;}.plan-value{color:#00FFAA!important;font-size:25px!important;font-weight:800!important;margin-top:7px!important;white-space:nowrap!important;}.plan-sub{color:#8B9BB4!important;font-size:10px!important;text-transform:uppercase!important;letter-spacing:.8px!important;margin-top:4px!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;}div.stButton>button{width:100%!important;background:#2B343B!important;color:#FFFFFF!important;border:1px solid #34495E!important;border-radius:5px!important;font-size:12px!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:1px!important;}div.stButton>button:hover{background:#00A3A3!important;color:#FFFFFF!important;border-color:#00A3A3!important;box-shadow:0 0 15px rgba(0,255,170,.35)!important;}div[data-baseweb="tab-list"]{gap:18px!important;border-bottom:2px solid #34495E!important;margin-bottom:15px!important;}div[data-baseweb="tab"]{background:transparent!important;color:#8B9BB4!important;font-weight:800!important;font-size:12px!important;border:none!important;padding-top:0!important;padding-bottom:10px!important;}div[aria-selected="true"]{color:#00FFAA!important;border-bottom:3px solid #00FFAA!important;}.nx-table-wrap{width:100%;background:#202B33;border:1px solid #34495E;border-radius:8px;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.18);}.nx-table-scroll{width:100%;overflow:auto;scrollbar-width:thin;scrollbar-color:#40525D #182229;}.nx-table-scroll::-webkit-scrollbar{width:7px;height:7px;}.nx-table-scroll::-webkit-scrollbar-track{background:#182229;}.nx-table-scroll::-webkit-scrollbar-thumb{background:#40525D;border-radius:8px;}.nx-table-scroll::-webkit-scrollbar-thumb:hover{background:#00A3A3;}.nx-table{width:100%;border-collapse:separate;border-spacing:0;font-family:Inter,Arial,sans-serif;font-size:11px;color:#E8EEF2;}.nx-table thead{position:sticky;top:0;z-index:3;}.nx-table th{background:#182229;color:#8B9BB4;text-align:left;font-size:9px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;padding:12px 13px;border-bottom:1px solid #34495E;white-space:nowrap;}.nx-table td{padding:11px 13px;border-bottom:1px solid rgba(52,73,94,.55);white-space:nowrap;vertical-align:middle;}.nx-table tbody tr{background:#202B33;transition:background .15s ease,box-shadow .15s ease;}.nx-table tbody tr:nth-child(even){background:#1E2930;}.nx-table tbody tr:hover{background:#263740;box-shadow:inset 3px 0 0 #00FFAA;}.nx-table tbody tr:last-child td{border-bottom:none;}.nx-table td:first-child{color:#B9C5CD;font-weight:600;}.nx-badge{display:inline-flex;align-items:center;justify-content:center;min-width:68px;padding:4px 8px;border-radius:4px;font-size:9px;font-weight:800;letter-spacing:.6px;background:#2B343B;border:1px solid #465762;color:#B9C5CD;}.nx-income{color:#00FFAA;background:rgba(0,255,170,.08);border-color:rgba(0,255,170,.28);}.nx-expense{color:#FF6B6B;background:rgba(255,75,75,.08);border-color:rgba(255,75,75,.28);}.nx-fixed{color:#FFD166;background:rgba(255,209,102,.08);border-color:rgba(255,209,102,.25);}.nx-saving{color:#00E5FF;background:rgba(0,229,255,.08);border-color:rgba(0,229,255,.25);}.nx-free{color:#00FFAA;background:rgba(0,255,170,.08);border-color:rgba(0,255,170,.25);}.nx-neutral{color:#B9C5CD;background:#2B343B;border-color:#465762;}.nx-money-pos{color:#00FFAA!important;font-weight:800!important;text-align:right;}.nx-money-neg{color:#FF6B6B!important;font-weight:800!important;text-align:right;}</style>""", unsafe_allow_html=True)


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
                line=dict(
                    color="#1D2A35",
                    width=2
                )
            ),
            text=valores,
            texttemplate="%{text:$,.2f}",
            textposition="auto",
            textfont=dict(
                color="#FFFFFF",
                size=12
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
# TAB 4
# ============================================================

with tab_plan:

    st.markdown(
        "<div style='background:linear-gradient(135deg,#253441,#1D2830);border:1px solid #34495E;border-radius:8px;padding:18px 22px;margin-bottom:18px;'><div style='color:#00FFAA;font-size:11px;font-weight:800;letter-spacing:2px;'>NEXION // FINANZAS PERSONALES</div><div style='color:#FFFFFF;font-size:24px;font-weight:700;margin-top:4px;'>PLAN SEMANAL</div><div style='color:#8B9BB4;font-size:12px;margin-top:5px;'>Distribución del ingreso · Gastos · Ahorro · Disponible</div></div>",
        unsafe_allow_html=True
    )


    # ========================================================
    # KPI PLAN
    # ========================================================

    c1, c2, c3, c4 = st.columns(
        [1, 1, 1, 1],
        gap="small"
    )

    plan_cards = [
        (
            c1,
            "INGRESO SEMANAL",
            INGRESO_SEMANAL,
            "Ingreso disponible de la semana"
        ),
        (
            c2,
            "GASTOS + AHORRO",
            TOTAL_APARTADO_SEMANAL,
            "Comprometido semanalmente"
        ),
        (
            c3,
            "APARTADO MENSUAL",
            TOTAL_AHORRO_MENSUAL_SEM,
            "Ahorro proporcional semanal"
        ),
        (
            c4,
            "DISPONIBLE",
            DISPONIBLE_SEMANAL,
            "Libre después de apartados"
        )
    ]

    for col, titulo, valor, sub in plan_cards:

        with col:

            st.markdown(
                f"""<div class="plan-card"><div class="plan-title">{titulo}</div><div class="plan-value">${valor:,.2f}</div><div class="plan-sub">{sub}</div></div>""",
                unsafe_allow_html=True
            )


    # ========================================================
    # PAGOS
    # ========================================================

    st.markdown(
        "<div style='color:#FFFFFF;font-size:11px;font-weight:800;letter-spacing:1.5px;margin:18px 0 10px 0;'>CALENDARIO DE PAGOS MENSUALES</div>",
        unsafe_allow_html=True
    )

    pagos = [
        (
            "ABONO TV",
            900.00,
            "25 SEP",
            "VIERNES",
            "Fondo asegurado con cobro del día"
        ),
        (
            "INTERNET",
            1100.00,
            "27 SEP",
            "DOMINGO",
            "Asegurar desde el viernes 25"
        ),
        (
            "PRÉSTAMO",
            1600.00,
            "28 SEP",
            "LUNES",
            "Asegurar desde el viernes 25"
        )
    ]

    p1, p2, p3 = st.columns(
        [1, 1, 1],
        gap="small"
    )

    for col, pago in zip(
        [p1, p2, p3],
        pagos
    ):

        with col:

            concepto, monto, fecha, dia, estado = pago

            st.markdown(
                f"""<div class="plan-card" style="min-height:145px;"><div style="color:#00E5FF;font-size:10px;font-weight:800;letter-spacing:1.5px;">{concepto}</div><div style="color:#FFFFFF;font-size:25px;font-weight:700;margin-top:7px;">${monto:,.2f}</div><div style="color:#FFD700;font-size:11px;font-weight:700;margin-top:4px;">{fecha} · {dia}</div><div style="color:#8B9BB4;font-size:11px;margin-top:8px;">{estado}</div></div>""",
                unsafe_allow_html=True
            )


    # ========================================================
    # DISTRIBUCIÓN
    # ========================================================

    st.markdown(
        "<div style='color:#FFFFFF;font-size:11px;font-weight:800;letter-spacing:1.5px;margin:22px 0 10px 0;'>DISTRIBUCIÓN DEL VIERNES DE PAGO</div>",
        unsafe_allow_html=True
    )

    df_distribucion = pd.DataFrame(
        [
            ["Gastos de Casa / Despensa", 1500, "Gasto Fijo"],
            ["Gasolina", 600, "Gasto Fijo"],
            ["Consulta", 350, "Gasto Fijo"],
            ["Gastos de tu Hija", 250, "Gasto Fijo"],
            ["Ahorro Abono TV", 225, "Ahorro Mensual"],
            ["Ahorro Abono Préstamo", 400, "Ahorro Mensual"],
            ["Ahorro Internet", 275, "Ahorro Mensual"],
            ["LIBRE / DISPONIBLE PARA TI", DISPONIBLE_SEMANAL, "Disponible"]
        ],
        columns=[
            "CONCEPTO",
            "MONTO SEMANAL",
            "TIPO"
        ]
    )

    render_tabla_premium(
        df_distribucion,
        moneda_cols=["MONTO SEMANAL"],
        max_height=330
    )

    st.markdown("<div style='height:26px;border-top:1px solid rgba(52,73,94,.35);margin-top:6px;'></div>", unsafe_allow_html=True)

    # ========================================================
    # RESUMEN
    # ========================================================

    r1, r2, r3 = st.columns(
        [1, 1, 1]
    )

    resumen = [
        (
            r1,
            "GASTOS FIJOS",
            TOTAL_GASTOS_SEMANALES,
            "Casa + gasolina + consulta + hija"
        ),
        (
            r2,
            "AHORRO SEMANAL",
            TOTAL_AHORRO_MENSUAL_SEM,
            "TV + préstamo + internet"
        ),
        (
            r3,
            "LIBRE",
            DISPONIBLE_SEMANAL,
            "Disponible después de apartados"
        )
    ]

    for col, titulo, valor, sub in resumen:

        with col:

            st.markdown(
                f"""<div class="plan-card"><div class="plan-title">{titulo}</div><div class="plan-value">${valor:,.2f}</div><div class="plan-sub">{sub}</div></div>""",
                unsafe_allow_html=True
            )


    # ========================================================
    # REGISTRAR CORTE
    # ========================================================

    btn_corte, info_corte = st.columns(
        [1, 2],
        gap="small"
    )

    with btn_corte:

        registrar_corte = st.button(
            "REGISTRAR CORTE DE ESTA SEMANA",
            use_container_width=True,
            type="primary",
            key="btn_registrar_corte",
            disabled=(
                not TOKEN
                or not puede_editar_efectivo
                or bloqueado_por_otro
            )
        )

    with info_corte:

        if bloqueado_por_otro:

            st.warning(
                "Edición temporalmente bloqueada."
            )

        elif not TOKEN:

            st.warning(
                "GITHUB_TOKEN no está configurado."
            )

        else:

            st.caption(
                "El corte se almacenará en plan_financiero_semanal.csv."
            )


    # ========================================================
    # GUARDAR CORTE
    # ========================================================

    if registrar_corte:

        lock_creado = False

        try:

            lock_creado = crear_lock()

            if not lock_creado:
                st.error(
                    "No fue posible tomar el control de escritura."
                )
                st.stop()

            repo = Github(TOKEN).get_repo(REPO_NAME)

            fecha_corte = datetime.now(
                tz_gdl
            ).strftime("%Y-%m-%d")

            try:

                archivo = repo.get_contents(
                    PLAN_FILE_PATH,
                    ref="main"
                )

                df_plan = pd.read_csv(
                    io.StringIO(
                        archivo.decoded_content.decode("utf-8")
                    ),
                    keep_default_na=False
                )

                sha_plan = archivo.sha

            except:

                df_plan = pd.DataFrame(
                    columns=[
                        "Fecha_Corte",
                        "Semana",
                        "Ingreso_Semanal",
                        "Gastos_Fijos",
                        "Ahorro_Semanal",
                        "Disponible",
                        "Usuario"
                    ]
                )

                sha_plan = None

            if (
                not df_plan.empty
                and "Fecha_Corte" in df_plan.columns
                and fecha_corte in df_plan["Fecha_Corte"].astype(str).tolist()
            ):

                st.warning(
                    f"Ya existe un corte registrado para {fecha_corte}."
                )
                st.stop()

            ahora = datetime.now(tz_gdl)

            semana = (
                f"{ahora.year}-W"
                f"{ahora.isocalendar().week:02d}"
            )

            nuevo = pd.DataFrame(
                [{
                    "Fecha_Corte": fecha_corte,
                    "Semana": semana,
                    "Ingreso_Semanal": INGRESO_SEMANAL,
                    "Gastos_Fijos": TOTAL_GASTOS_SEMANALES,
                    "Ahorro_Semanal": TOTAL_AHORRO_MENSUAL_SEM,
                    "Disponible": DISPONIBLE_SEMANAL,
                    "Usuario": current_user
                }]
            )

            df_plan = pd.concat(
                [
                    df_plan,
                    nuevo
                ],
                ignore_index=True
            )

            csv_plan = df_plan.to_csv(
                index=False,
                encoding="utf-8-sig"
            )

            if sha_plan:

                repo.update_file(
                    path=PLAN_FILE_PATH,
                    message=f"Registro corte semanal {fecha_corte}",
                    content=csv_plan,
                    sha=sha_plan,
                    branch="main"
                )

            else:

                repo.create_file(
                    path=PLAN_FILE_PATH,
                    message=f"Creación plan financiero {fecha_corte}",
                    content=csv_plan,
                    branch="main"
                )

            st.session_state.df_plan_semanal = df_plan
            st.session_state.force_reload_plan = False

            st.success(
                f"Corte {semana} registrado correctamente."
            )

            time.sleep(.7)
            st.rerun()

        except Exception as e:

            st.error(
                f"No fue posible guardar el corte: {e}"
            )

        finally:

            if lock_creado:
                liberar_lock()


    # ========================================================
    # HISTORIAL
    # ========================================================

    st.markdown(
        "<div style='color:#FFFFFF;font-size:11px;font-weight:800;letter-spacing:1.5px;margin:25px 0 10px 0;'>HISTORIAL DE CORTES SEMANALES</div>",
        unsafe_allow_html=True
    )

    df_hist = get_plan_data_from_git()

    if df_hist.empty:

        st.info(
            "Todavía no existen cortes registrados."
        )

    else:

        df_hist = df_hist.copy()

        if "Fecha_Corte" in df_hist.columns:
            df_hist = df_hist.sort_values(
                "Fecha_Corte",
                ascending=False
            )

        columnas = [
            "Fecha_Corte",
            "Semana",
            "Ingreso_Semanal",
            "Gastos_Fijos",
            "Ahorro_Semanal",
            "Disponible",
            "Usuario"
        ]

        columnas = [
            c for c in columnas
            if c in df_hist.columns
        ]

        visual = df_hist[columnas].copy()

        monedas = [
            "Ingreso_Semanal",
            "Gastos_Fijos",
            "Ahorro_Semanal",
            "Disponible"
        ]

        for col in monedas:

            if col in visual.columns:
                visual[col] = pd.to_numeric(
                    visual[col],
                    errors="coerce"
                )

        render_tabla_premium(
            visual,
            moneda_cols=monedas,
            max_height=430
        )
