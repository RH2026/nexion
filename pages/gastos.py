import io
import json
import time
import hashlib
import hmac

from datetime import datetime, timedelta

from github import Github
import pandas as pd
import pytz
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from components.layout import render_layout


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================

st.set_page_config(
    page_title="JYPESA | Ahorros Personales",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. CONFIGURACIÓN DE TIEMPO
# ============================================================

tz_gdl = pytz.timezone("America/Mexico_City")
hoy = datetime.now(tz_gdl)


# ============================================================
# 3. LAYOUT
# ============================================================

render_layout(
    modulo_actual="FINANZAS",
    submodulo_actual="GASTOS"
)


# ============================================================
# 🔐 SEGURIDAD PRIVADA NEXION
# ============================================================

def validar_acceso_privado():

    usuario = st.session_state.get(
        "usuario_activo",
        ""
    )

    if usuario.upper() != "RIGOBERTO":
        st.error("ACCESO NO DISPONIBLE.")
        st.stop()

    if st.session_state.get(
        "wallet_private_access",
        False
    ):
        return True

    hash_guardado = st.secrets.get(
        "NEXION_PRIVATE_GATE_HASH",
        ""
    )

    if not hash_guardado:
        st.error("MÓDULO BLOQUEADO.")
        st.stop()

    if "wallet_gate_attempts" not in st.session_state:
        st.session_state.wallet_gate_attempts = 0

    if st.session_state.wallet_gate_attempts >= 5:
        st.error("ACCESO BLOQUEADO.")
        st.stop()

    st.markdown(
        """
        <div style="
            max-width:420px;
            margin:90px auto 30px auto;
            text-align:center;
        ">
            <div style="
                font-size:34px;
                margin-bottom:18px;
            ">
                🔐
            </div>

            <div style="
                color:#FFFFFF;
                font-size:16px;
                font-weight:700;
                letter-spacing:2px;
                margin-bottom:8px;
            ">
                ACCESO RESTRINGIDO
            </div>

            <div style="
                color:#8B9BB4;
                font-size:11px;
                letter-spacing:1px;
            ">
                AUTORIZACIÓN REQUERIDA
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_izq, col_centro, col_der = st.columns(
        [2, 1, 2]
    )

    with col_centro:

        clave_ingresada = st.text_input(
            "Código de autorización",
            type="password",
            key="wallet_private_gate_input",
            label_visibility="collapsed",
            placeholder="Código de autorización"
        )

        verificar = st.button(
            "AUTORIZAR ACCESO",
            use_container_width=True,
            key="wallet_private_gate_button"
        )

        if verificar:

            if not clave_ingresada:
                st.warning("Código requerido.")
                st.stop()

            hash_ingresado = hashlib.sha256(
                clave_ingresada.encode("utf-8")
            ).hexdigest()

            if hmac.compare_digest(
                hash_ingresado,
                hash_guardado
            ):

                st.session_state.wallet_private_access = True
                st.session_state.wallet_gate_attempts = 0

                st.session_state.pop(
                    "wallet_private_gate_input",
                    None
                )

                st.rerun()

            else:

                st.session_state.wallet_gate_attempts += 1

                restantes = max(
                    0,
                    5 - st.session_state.wallet_gate_attempts
                )

                if restantes > 0:

                    st.error(
                        f"Código no válido. "
                        f"Intentos restantes: {restantes}"
                    )

                else:

                    st.error(
                        "ACCESO BLOQUEADO."
                    )

                st.stop()

    st.stop()


# ============================================================
# 🔐 ACTIVAR EL CANDADO
# ============================================================

validar_acceso_privado()


# ============================================================
# 🔒 DESDE AQUÍ COMIENZA EL CONTENIDO PRIVADO
# ============================================================


# ============================================================
# 4. CONFIGURACIÓN GITHUB
# ============================================================

TOKEN = st.secrets.get(
    "GITHUB_TOKEN",
    None
)

REPO_NAME = "RH2026/nexion"

FILE_PATH = "cartera.csv"

LOCK_FILE_PATH = "lock_cartera.json"

PLAN_FILE_PATH = "plan_financiero_semanal.csv"


# ============================================================
# 5. USUARIO ACTUAL
# ============================================================

current_user = st.session_state.get(
    "usuario_activo",
    "UNKNOWN"
)

puede_editar = (
    current_user.upper() == "RIGOBERTO"
)


# ============================================================
# 6. CUENTAS Y CATEGORÍAS
# ============================================================

CUENTAS_MATRIX = {

    "Caja de Ahorros": {
        "color": "#00E5FF",
        "fondo_base": 0.00
    },

    "Scottiabank": {
        "color": "#00FFAA",
        "fondo_base": 0.00
    },

    "Santander": {
        "color": "#FF4B4B",
        "fondo_base": 0.00
    },

    "Cartera": {
        "color": "#8B9BB4",
        "fondo_base": 0.00
    },

    "Caja Jypesa": {
        "color": "#8B9BB8",
        "fondo_base": 0.00
    }
}


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
# 7. CONFIGURACIÓN DEL PLAN SEMANAL
# ============================================================

INGRESO_SEMANAL = 4450.00

GASTO_CASA = 1500.00

GASOLINA = 600.00

CONSULTA = 350.00

GASTOS_HIJA = 250.00


TOTAL_GASTOS_SEMANALES = (
    GASTO_CASA
    + GASOLINA
    + CONSULTA
    + GASTOS_HIJA
)


AHORRO_TV_SEM = 225.00

AHORRO_PRESTAMO_SEM = 400.00

AHORRO_INTERNET_SEM = 275.00


TOTAL_AHORRO_MENSUAL_SEM = (
    AHORRO_TV_SEM
    + AHORRO_PRESTAMO_SEM
    + AHORRO_INTERNET_SEM
)


TOTAL_APARTADO_SEMANAL = (
    TOTAL_GASTOS_SEMANALES
    + TOTAL_AHORRO_MENSUAL_SEM
)


DISPONIBLE_SEMANAL = (
    INGRESO_SEMANAL
    - TOTAL_APARTADO_SEMANAL
)


# ============================================================
# 8. ESTILOS NEXION
# ============================================================

st.markdown(
    """
    <style>

    div[data-testid="stBlock"] {
        max-width: 100% !important;
        padding: 0 !important;
    }

    header[data-testid="stHeader"] {
        background-color: #1D2A35 !important;
        border-bottom: 2px solid #34495E !important;
    }

    .kpi-card {
        background-color: #253441 !important;
        padding: 20px !important;
        border-radius: 8px !important;
        border: 1px solid #34495E !important;
        text-align: center !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
        margin-bottom: 15px;
    }

    .kpi-label {
        color: #8B9BB4 !important;
        font-size: 12px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
    }

    .kpi-value {
        color: #FFFFFF !important;
        font-size: 34px !important;
        font-weight: bold !important;
        margin: 10px 0 !important;
    }

    .kpi-trend {
        font-size: 13px !important;
        font-weight: bold !important;
    }

    .neon-bar {
        height: 4px !important;
        border-radius: 2px !important;
        margin-top: 10px !important;
        width: 100% !important;
    }

    div.stButton > button {
        background-color: #2B343B !important;
        color: #FFFFFF !important;
        border: 1px solid #34495E !important;
        border-radius: 5px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        font-weight: normal !important;
        font-size: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    div.stButton > button:hover {
        background-color: #00A3A3 !important;
        color: #FFFFFF !important;
        border-color: #00A3A3 !important;
        box-shadow: 0 0 15px rgba(0,255,170,0.4) !important;
    }

    div.stButton > button:active {
        background-color: #00A3A3 !important;
        border-color: #00A3A3 !important;
    }

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

    .plan-card {
        background-color: #253441;
        border: 1px solid #34495E;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .plan-title {
        color: #FFFFFF;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .plan-value {
        color: #00FFAA;
        font-size: 26px;
        font-weight: 800;
        margin-top: 8px;
    }

    .plan-sub {
        color: #8B9BB4;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 9. CANDADO DE ARCHIVO CARTERA
# ============================================================

lock_info = None
bloqueado_por_otro = False


if puede_editar and TOKEN:

    try:

        repo = Github(TOKEN).get_repo(
            REPO_NAME
        )

        try:

            lock_info = json.loads(
                repo.get_contents(
                    LOCK_FILE_PATH,
                    ref="main"
                ).decoded_content.decode("utf-8")
            )

            diferencia = (
                datetime.now(tz_gdl)
                - tz_gdl.localize(
                    datetime.strptime(
                        lock_info["timestamp"],
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            ).total_seconds()

            if diferencia < 600:

                if lock_info["usuario"] != current_user:
                    bloqueado_por_otro = True

            else:

                lock_info = None

        except:

            pass

    except:

        pass


st.session_state[
    "bloqueado_por_otro_efectivo"
] = bloqueado_por_otro


if bloqueado_por_otro:

    st.warning(
        f"⚠️ MÓDULO PAUSADO: Sesión activa de "
        f"**{lock_info['usuario']}**. "
        f"No puedes registrar gastos ahora."
    )

    st.session_state[
        "puede_editar_efectivo"
    ] = False

else:

    st.session_state[
        "puede_editar_efectivo"
    ] = puede_editar

    if (
        puede_editar
        and lock_info is None
        and TOKEN
    ):

        try:

            repo = Github(TOKEN).get_repo(
                REPO_NAME
            )

            ahora_gdl = datetime.now(
                tz_gdl
            )

            lock_string = json.dumps(
                {
                    "usuario": current_user,
                    "timestamp": ahora_gdl.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "hora": ahora_gdl.strftime(
                        "%H:%M:%S"
                    )
                },
                indent=4
            )

            try:

                repo.update_file(
                    path=LOCK_FILE_PATH,
                    message=f"LOCK // {current_user}",
                    content=lock_string,
                    sha=repo.get_contents(
                        LOCK_FILE_PATH
                    ).sha
                )

            except:

                repo.create_file(
                    path=LOCK_FILE_PATH,
                    message=f"LOCK // {current_user}",
                    content=lock_string,
                    branch="main"
                )

        except:

            pass


# ============================================================
# 10. MOTOR DE DATOS CARTERA
# ============================================================

def get_wallet_data_from_git():

    if (
        "df_wallet" not in st.session_state
        or st.session_state.get(
            "force_reload",
            False
        )
    ):

        start_date = datetime.now(
            tz_gdl
        )

        ejemplos = [

            {
                "Fecha": (
                    start_date
                    - timedelta(days=10)
                ).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "Tipo": "Ingreso",
                "Categoria": "Nómina",
                "Concepto": "Pago Quincena 1 JYPESA",
                "Monto": 35000.0,
                "Cuenta": "Caja Jypesa"
            },

            {
                "Fecha": (
                    start_date
                    - timedelta(days=8)
                ).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "Tipo": "Gasto",
                "Categoria": "Renta",
                "Concepto": "Renta Oficinas",
                "Monto": -18000.0,
                "Cuenta": "Santander"
            },

            {
                "Fecha": (
                    start_date
                    - timedelta(days=5)
                ).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "Tipo": "Ingreso",
                "Categoria": "Freelance / Proyectos",
                "Concepto": "Proyecto Xenocode UI",
                "Monto": 15000.0,
                "Cuenta": "Scottiabank"
            },

            {
                "Fecha": (
                    start_date
                    - timedelta(days=1)
                ).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "Tipo": "Gasto",
                "Categoria": "Supermercado",
                "Concepto": "Compras Semanales",
                "Monto": -3500.0,
                "Cuenta": "Cartera"
            }
        ]

        df_load = pd.DataFrame(
            ejemplos
        )

        if TOKEN:

            try:

                repo = Github(
                    TOKEN
                ).get_repo(
                    REPO_NAME
                )

                try:

                    contenido = repo.get_contents(
                        FILE_PATH,
                        ref="main"
                    )

                    df_load = pd.read_csv(
                        io.StringIO(
                            contenido.decoded_content.decode(
                                "utf-8"
                            )
                        ),
                        keep_default_na=False
                    )

                except:

                    repo.create_file(
                        path=FILE_PATH,
                        message="INITIALIZE WALLET MATRIX",
                        content=df_load.to_csv(
                            index=False
                        ),
                        branch="main"
                    )

            except Exception as e:

                st.error(
                    f"Error conexión GitHub: {e}. "
                    f"Usando datos locales."
                )

        df_load["Fecha"] = pd.to_datetime(
            df_load["Fecha"]
        )

        st.session_state.df_wallet = (
            df_load
        )

        st.session_state.force_reload = (
            False
        )

    return st.session_state.df_wallet


# ============================================================
# 11. MOTOR DE DATOS PLAN SEMANAL
# ============================================================

def get_plan_data_from_git(
    force_reload=False
):

    if force_reload:

        st.session_state[
            "force_reload_plan"
        ] = True

    if (
        "df_plan_semanal"
        in st.session_state
        and not st.session_state.get(
            "force_reload_plan",
            False
        )
    ):

        return st.session_state[
            "df_plan_semanal"
        ]

    columnas_plan = [
        "Fecha_Corte",
        "Semana",
        "Ingreso_Semanal",
        "Gastos_Fijos",
        "Ahorro_Semanal",
        "Disponible",
        "Usuario"
    ]

    df_plan = pd.DataFrame(
        columns=columnas_plan
    )

    if TOKEN:

        try:

            repo = Github(
                TOKEN
            ).get_repo(
                REPO_NAME
            )

            try:

                contenido = repo.get_contents(
                    PLAN_FILE_PATH,
                    ref="main"
                )

                df_plan = pd.read_csv(
                    io.StringIO(
                        contenido.decoded_content.decode(
                            "utf-8"
                        )
                    ),
                    keep_default_na=False
                )

            except:

                repo.create_file(
                    path=PLAN_FILE_PATH,
                    message="INITIALIZE WEEKLY FINANCIAL PLAN",
                    content=df_plan.to_csv(
                        index=False
                    ),
                    branch="main"
                )

        except Exception as e:

            st.warning(
                f"No fue posible sincronizar "
                f"el plan financiero: {e}"
            )

    st.session_state[
        "df_plan_semanal"
    ] = df_plan

    st.session_state[
        "force_reload_plan"
    ] = False

    return df_plan


# ============================================================
# 12. RENDERIZADO DE INTERFAZ WALLET
# ============================================================

puede_editar_efectivo = st.session_state.get(
    "puede_editar_efectivo",
    False
)

df_actual = get_wallet_data_from_git()


# ============================================================
# 13. PREPARAR DATOS
# ============================================================

if not df_actual.empty:

    df_actual["Fecha"] = pd.to_datetime(
        df_actual["Fecha"],
        errors="coerce"
    )

    df_actual["Mes"] = (
        df_actual["Fecha"]
        .dt.strftime("%Y-%m")
    )

    current_month = datetime.now(
        tz_gdl
    ).strftime("%Y-%m")

    df_month = df_actual[
        df_actual["Mes"] == current_month
    ]

else:

    df_month = pd.DataFrame()


# ============================================================
# 14. CÁLCULOS DE SALDOS
# ============================================================

saldos_actuales = {
    cuenta: datos["fondo_base"]
    for cuenta, datos
    in CUENTAS_MATRIX.items()
}


if not df_actual.empty:

    for cuenta in CUENTAS_MATRIX.keys():

        saldos_actuales[cuenta] += (
            df_actual[
                df_actual["Cuenta"] == cuenta
            ]["Monto"].sum()
        )


total_general = sum(
    saldos_actuales.values()
)


inc_month = (
    df_month[
        df_month["Tipo"] == "Ingreso"
    ]["Monto"].sum()
    if not df_month.empty
    else 0
)


exp_month = (
    abs(
        df_month[
            df_month["Tipo"] == "Gasto"
        ]["Monto"].sum()
    )
    if not df_month.empty
    else 0
)


net_month = (
    inc_month - exp_month
)


# ============================================================
# 15. SISTEMA DE 4 PESTAÑAS
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
# PESTAÑA 1: KPI'S WALLET
# ============================================================

with tab_kpi:

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:

        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-label'>
                    PATRIMONIO NETO
                </div>

                <div class='kpi-value'>
                    ${total_general:,.2f}
                </div>

                <div class='kpi-trend'
                     style='color:#00E5FF'>
                    BALANCE GLOBAL
                </div>

                <div class='neon-bar'
                     style='background:
                     linear-gradient(
                         90deg,
                         #00E5FF,
                         transparent
                     );'>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi2:

        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-label'>
                    INGRESOS MTD
                </div>

                <div class='kpi-value'>
                    ${inc_month:,.2f}
                </div>

                <div class='kpi-trend'
                     style='color:#00FFAA'>
                    FLUJO DE ENTRADA
                </div>

                <div class='neon-bar'
                     style='background:
                     linear-gradient(
                         90deg,
                         #00FFAA,
                         transparent
                     );'>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi3:

        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-label'>
                    EGRESOS MTD
                </div>

                <div class='kpi-value'>
                    ${exp_month:,.2f}
                </div>

                <div class='kpi-trend'
                     style='color:#FF4B4B'>
                    GASTOS DEL MES
                </div>

                <div class='neon-bar'
                     style='background:
                     linear-gradient(
                         90deg,
                         #FF4B4B,
                         transparent
                     );'>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        "<br><hr style='border-color:#34495E;'>",
        unsafe_allow_html=True
    )

    col_chart, _ = st.columns(
        [2, 1]
    )

    with col_chart:

        st.markdown(
            """
            <p class='kpi-label'
               style='text-align:left;'>
                <span style='color:#00E5FF'>
                    🔍
                </span>
                DISTRIBUCIÓN DE CAPITAL POR CUENTA
            </p>
            """,
            unsafe_allow_html=True
        )

        nombres_cuentas = list(
            saldos_actuales.keys()
        )

        valores_saldos = list(
            saldos_actuales.values()
        )

        colores_barras = [
            CUENTAS_MATRIX[c]["color"]
            for c in nombres_cuentas
        ]

        fig_bars = go.Figure(
            go.Bar(
                x=valores_saldos,
                y=nombres_cuentas,
                orientation="h",

                marker=dict(
                    color=colores_barras,
                    line=dict(
                        color="#1D2A35",
                        width=2
                    )
                ),

                text=valores_saldos,

                texttemplate=(
                    "%{text:$,.2f}"
                ),

                textposition="auto",

                textfont=dict(
                    color="#FFFFFF",
                    size=12,
                    family="monospace"
                ),

                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Saldo: %{x:$,.2f}"
                    "<extra></extra>"
                )
            )
        )

        fig_bars.update_layout(

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
                tickformat="$,.0f",
                title=None
            ),

            yaxis=dict(
                color="#E0E6ED",
                tickfont=dict(size=13),
                title=None,
                autorange="reversed"
            ),

            hoverlabel=dict(
                bgcolor="#253441",
                font=dict(
                    size=13,
                    family="monospace"
                )
            )
        )

        st.plotly_chart(
            fig_bars,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )


# ============================================================
# PESTAÑA 2: FLUJOS DE EFECTIVO
# ============================================================

with tab_flujos:

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    gr_col1, gr_col2 = st.columns(
        [2, 1.5]
    )

    with gr_col1:

        st.markdown(
            """
            <p class='kpi-label'
               style='text-align:left;'>
                TENDENCIA DE FLUJO
                <span style='color:#8B9BB4'>
                    (MES ACTUAL)
                </span>
            </p>
            """,
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

            if "Gasto" in df_daily:

                df_daily["Gasto"] = (
                    abs(df_daily["Gasto"])
                )

            else:

                df_daily["Gasto"] = 0

            if "Ingreso" not in df_daily:

                df_daily["Ingreso"] = 0

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

                    fillcolor=(
                        "rgba(0,255,170,0.05)"
                    )
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

                    fillcolor=(
                        "rgba(255,75,75,0.05)"
                    )
                )
            )

            fig_flow.update_layout(

                paper_bgcolor=(
                    "rgba(0,0,0,0)"
                ),

                plot_bgcolor=(
                    "rgba(0,0,0,0)"
                ),

                xaxis=dict(
                    showgrid=False,
                    color="#8B9BB4",
                    tickformat="%d %b"
                ),

                yaxis=dict(
                    showgrid=True,
                    gridcolor="#34495E",
                    color="#8B9BB4",
                    zeroline=False
                ),

                legend=dict(
                    orientation="h",
                    y=1.1,
                    x=0.5,
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
                config={
                    "displayModeBar": False
                }
            )

        else:

            st.info(
                "Sin movimientos este mes."
            )

    with gr_col2:

        st.markdown(
            """
            <p class='kpi-label'
               style='text-align:left;'>
                ANÁLISIS DE CONSUMO
                POR CATEGORÍA
            </p>
            """,
            unsafe_allow_html=True
        )

        if not df_month.empty:

            df_gastos_cat = (
                df_month[
                    df_month["Tipo"] == "Gasto"
                ]
                .groupby("Categoria")[
                    "Monto"
                ]
                .sum()
                .abs()
                .reset_index()
            )

            if not df_gastos_cat.empty:

                df_gastos_cat = (
                    df_gastos_cat
                    .sort_values(
                        by="Monto",
                        ascending=True
                    )
                )

                fig_cat = px.bar(
                    df_gastos_cat,
                    x="Monto",
                    y="Categoria",
                    orientation="h",
                    text_auto=",.0f"
                )

                num_bars = len(
                    df_gastos_cat
                )

                colors = []

                for i in range(num_bars):

                    if i == num_bars - 1:

                        colors.append(
                            "#44B3E1"
                        )

                    elif i >= num_bars - 3:

                        colors.append(
                            "#4D93D9"
                        )

                    else:

                        colors.append(
                            "#215C98"
                        )

                fig_cat.update_traces(

                    marker_color=colors,

                    hovertemplate=(
                        "%{y}: "
                        "$%{x:,.2f}"
                    ),

                    textposition="outside",

                    textfont=dict(
                        color="#E0E6ED"
                    )
                )

                fig_cat.update_layout(

                    paper_bgcolor=(
                        "rgba(0,0,0,0)"
                    ),

                    plot_bgcolor=(
                        "rgba(0,0,0,0)"
                    ),

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
                    config={
                        "displayModeBar": False
                    }
                )

            else:

                st.info(
                    "Sin gastos registrados "
                    "este mes."
                )

        else:

            st.info(
                "Sin movimientos este mes."
            )


# ============================================================
# PESTAÑA 3: REGISTRO NUBE
# ============================================================

with tab_registro:

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    if not TOKEN:

        st.warning(
            "⚠️ Modo de solo lectura local. "
            "Configure GITHUB_TOKEN para "
            "registrar operaciones."
        )

    st.markdown(
        """
        <p class='kpi-label'
           style='margin-bottom:10px;'>
            <span style='color:#00E5FF'>
                ⚡
            </span>
            EJECUTAR ORDEN DE REGISTRO
        </p>
        """,
        unsafe_allow_html=True
    )

    in_col1, in_col2, in_col3, in_col4 = (
        st.columns(4)
    )

    with in_col1:

        f_monto = st.number_input(
            "Cantidad MXN",
            min_value=0.0,
            step=100.0,
            key="inp_monto_nube"
        )

    with in_col2:

        f_cat = st.selectbox(
            "Categoría",
            CATEGORIAS,
            key="inp_cat_nube"
        )

    with in_col3:

        f_desc = st.text_input(
            "Concepto / Referencia",
            placeholder=(
                "Ej. Gastos de Operación"
            ),
            key="inp_desc_nube"
        )

    with in_col4:

        f_cuenta = st.selectbox(
            "Cuenta Destino/Origen",
            list(
                CUENTAS_MATRIX.keys()
            ),
            key="inp_cuenta_nube"
        )

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    btn_l, btn_r = st.columns(2)

    block_submit = (

        not puede_editar_efectivo

        or st.session_state.get(
            "bloqueado_por_otro_efectivo",
            False
        )

        or not TOKEN
    )

    with btn_l:

        ingreso_sub = st.button(
            "REGISTRAR INGRESO",
            icon=":material/save:",
            use_container_width=True,
            key="btn_ingreso_action",
            disabled=block_submit
        )

    with btn_r:

        gasto_sub = st.button(
            "REGISTRAR GASTO",
            icon=":material/remove:",
            use_container_width=True,
            key="btn_gasto_action",
            disabled=block_submit
        )

    if (
        not block_submit
        and (
            ingreso_sub
            or gasto_sub
        )
        and f_monto > 0
        and f_desc
    ):

        with st.status(
            "Sincronizando con Nube Nexion...",
            expanded=True
        ):

            try:

                repo = Github(
                    TOKEN
                ).get_repo(
                    REPO_NAME
                )

                contents = repo.get_contents(
                    FILE_PATH
                )

                df_latest = pd.read_csv(
                    io.StringIO(
                        contents.decoded_content.decode(
                            "utf-8"
                        )
                    ),
                    keep_default_na=False
                )

                nueva_fila = {

                    "Fecha":
                        datetime.now(
                            tz_gdl
                        ).strftime(
                            "%Y-%m-%d %H:%M"
                        ),

                    "Tipo":
                        "Ingreso"
                        if ingreso_sub
                        else "Gasto",

                    "Categoria":
                        f_cat,

                    "Concepto":
                        f_desc,

                    "Monto":
                        f_monto
                        if ingreso_sub
                        else -f_monto,

                    "Cuenta":
                        f_cuenta
                }

                df_latest = pd.concat(
                    [
                        df_latest,
                        pd.DataFrame(
                            [nueva_fila]
                        )
                    ],
                    ignore_index=True
                )

                repo.update_file(

                    path=FILE_PATH,

                    message=(
                        f"UPDATE // "
                        f"{current_user} // "
                        f"{datetime.now(tz_gdl).strftime('%H:%M:%S')}"
                    ),

                    content=df_latest.to_csv(
                        index=False
                    ),

                    sha=contents.sha
                )

                try:

                    repo.delete_file(

                        path=LOCK_FILE_PATH,

                        message=(
                            f"UNLOCK // "
                            f"{current_user}"
                        ),

                        sha=repo.get_contents(
                            LOCK_FILE_PATH
                        ).sha
                    )

                except:

                    pass

                st.session_state[
                    "force_reload"
                ] = True

                st.success(
                    "OPERACIÓN CLASIFICADA "
                    "EXITOSAMENTE."
                )

                time.sleep(1)

                st.rerun()

            except Exception as e:

                st.error(
                    f"Error crítico de "
                    f"sincronización: {e}"
                )


# ============================================================
# PESTAÑA 4: PLAN SEMANAL
# ============================================================

with tab_plan:

    st.markdown(
        """
        <div style="
            background:linear-gradient(
                135deg,
                #253441,
                #1D2830
            );
            border:1px solid #34495E;
            border-radius:8px;
            padding:18px 22px;
            margin-bottom:18px;
        ">

            <div style="
                color:#00FFAA;
                font-size:11px;
                font-weight:800;
                letter-spacing:2px;
                text-transform:uppercase;
                margin-bottom:6px;
            ">
                NEXION // FINANZAS PERSONALES
            </div>

            <div style="
                color:#FFFFFF;
                font-size:24px;
                font-weight:700;
                letter-spacing:.3px;
            ">
                PLAN SEMANAL
            </div>

            <div style="
                color:#8B9BB4;
                font-size:12px;
                margin-top:5px;
            ">
                Distribución del ingreso · Gastos · Ahorro · Disponible
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # VALORES PRINCIPALES
    # ========================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="plan-card">

                <div class="plan-title">
                    INGRESO SEMANAL
                </div>

                <div class="plan-value">
                    ${INGRESO_SEMANAL:,.2f}
                </div>

                <div class="plan-sub">
                    Ingreso disponible de la semana
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="plan-card">

                <div class="plan-title">
                    GASTOS + AHORRO
                </div>

                <div class="plan-value">
                    ${TOTAL_APARTADO_SEMANAL:,.2f}
                </div>

                <div class="plan-sub">
                    Comprometido semanalmente
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            f"""
            <div class="plan-card">

                <div class="plan-title">
                    APARTADO MENSUAL
                </div>

                <div class="plan-value">
                    ${TOTAL_AHORRO_MENSUAL_SEM:,.2f}
                </div>

                <div class="plan-sub">
                    Ahorro proporcional semanal
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            f"""
            <div class="plan-card">

                <div class="plan-title">
                    DISPONIBLE
                </div>

                <div class="plan-value">
                    ${DISPONIBLE_SEMANAL:,.2f}
                </div>

                <div class="plan-sub">
                    Libre después de apartados
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown(
        "<div style='height:10px'></div>",
        unsafe_allow_html=True
    )


    # ========================================================
    # CALENDARIO DE PAGOS MENSUALES
    # ========================================================

    st.markdown(
        """
        <div style="
            color:#00FFAA;
            font-size:11px;
            font-weight:800;
            letter-spacing:1.5px;
            text-transform:uppercase;
            margin:18px 0 10px 0;
        ">
            CALENDARIO DE PAGOS MENSUALES
        </div>
        """,
        unsafe_allow_html=True
    )


    pagos_mensuales = [

        {
            "concepto": "ABONO TV",
            "monto": 900.00,
            "fecha": "25 SEP",
            "dia": "VIERNES",
            "estado": "Fondo asegurado con cobro del día"
        },

        {
            "concepto": "INTERNET",
            "monto": 1100.00,
            "fecha": "27 SEP",
            "dia": "DOMINGO",
            "estado": "Asegurar desde el viernes 25"
        },

        {
            "concepto": "PRÉSTAMO",
            "monto": 1600.00,
            "fecha": "28 SEP",
            "dia": "LUNES",
            "estado": "Asegurar desde el viernes 25"
        }
    ]


    p1, p2, p3 = st.columns(3)


    for columna, pago in zip(
        [p1, p2, p3],
        pagos_mensuales
    ):

        with columna:

            st.markdown(
                f"""
                <div class="plan-card"
                     style="min-height:145px;">

                    <div style="
                        color:#00E5FF;
                        font-size:10px;
                        font-weight:800;
                        letter-spacing:1.5px;
                        margin-bottom:8px;
                    ">
                        {pago["concepto"]}
                    </div>

                    <div style="
                        color:#FFFFFF;
                        font-size:25px;
                        font-weight:700;
                        margin-bottom:3px;
                    ">
                        ${pago["monto"]:,.2f}
                    </div>

                    <div style="
                        color:#FFD700;
                        font-size:11px;
                        font-weight:700;
                        margin-bottom:8px;
                    ">
                        {pago["fecha"]} · {pago["dia"]}
                    </div>

                    <div style="
                        color:#8B9BB4;
                        font-size:11px;
                        line-height:1.4;
                    ">
                        {pago["estado"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


    # ========================================================
    # DISTRIBUCIÓN SEMANAL
    # ========================================================

    st.markdown(
        """
        <div style="
            color:#00FFAA;
            font-size:11px;
            font-weight:800;
            letter-spacing:1.5px;
            text-transform:uppercase;
            margin:24px 0 10px 0;
        ">
            DISTRIBUCIÓN DEL VIERNES DE PAGO
        </div>
        """,
        unsafe_allow_html=True
    )


    df_distribucion = pd.DataFrame(
        [
            [
                "Gastos de Casa / Despensa",
                1500.00,
                "Gasto Fijo"
            ],

            [
                "Gasolina",
                600.00,
                "Gasto Fijo"
            ],

            [
                "Consulta",
                350.00,
                "Gasto Fijo"
            ],

            [
                "Gastos de tu Hija",
                250.00,
                "Gasto Fijo"
            ],

            [
                "Ahorro Abono TV",
                225.00,
                "Ahorro Mensual"
            ],

            [
                "Ahorro Abono Préstamo",
                400.00,
                "Ahorro Mensual"
            ],

            [
                "Ahorro Internet",
                275.00,
                "Ahorro Mensual"
            ],

            [
                "LIBRE / DISPONIBLE PARA TI",
                850.00,
                "Disponible"
            ],
        ],
        columns=[
            "CONCEPTO",
            "MONTO SEMANAL",
            "TIPO"
        ]
    )


    st.dataframe(
        df_distribucion.style.format(
            {
                "MONTO SEMANAL": "${:,.2f}"
            }
        ),
        use_container_width=True,
        hide_index=True,
        height=330
    )


    # ========================================================
    # RESUMEN MATEMÁTICO
    # ========================================================

    st.markdown(
        "<div style='height:5px'></div>",
        unsafe_allow_html=True
    )


    r1, r2, r3 = st.columns(3)


    with r1:

        st.markdown(
            f"""
            <div class="plan-card">

                <div class="plan-title">
                    GASTOS FIJOS
                </div>

                <div class="plan-value">
                    ${
                        GASTO_CASA
                        + GASOLINA
                        + CONSULTA
                        + GASTOS_HIJA
                    :,.2f}
                </div>

                <div class="plan-sub">
                    Casa + gasolina + consulta + hija
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with r2:

        st.markdown(
            f"""
            <div class="plan-card">

                <div class="plan-title">
                    AHORRO SEMANAL
                </div>

                <div class="plan-value">
                    ${TOTAL_AHORRO_MENSUAL_SEM:,.2f}
                </div>

                <div class="plan-sub">
                    TV + préstamo + internet
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with r3:

        st.markdown(
            f"""
            <div class="plan-card">

                <div class="plan-title">
                    LIBRE
                </div>

                <div class="plan-value">
                    ${DISPONIBLE_SEMANAL:,.2f}
                </div>

                <div class="plan-sub">
                    Disponible después de apartados
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown(
        "<div style='height:10px'></div>",
        unsafe_allow_html=True
    )


    # ========================================================
    # REGISTRAR CORTE
    # ========================================================

    col_btn, col_info = st.columns(
        [1, 2]
    )


    with col_btn:

        registrar_corte = st.button(
            "REGISTRAR CORTE DE ESTA SEMANA",
            use_container_width=True,
            type="primary",
            key="btn_registrar_corte",
            disabled=(
                not TOKEN
                or not puede_editar_efectivo
                or bloqueado_por_otro_efectivo
            )
        )


    with col_info:

        if bloqueado_por_otro_efectivo:

            st.warning(
                "La edición está temporalmente bloqueada porque otra sesión está escribiendo datos."
            )

        elif not TOKEN:

            st.warning(
                "GITHUB_TOKEN no está configurado. "
                "No se puede guardar el corte."
            )

        else:

            st.caption(
                "El corte se almacenará en GitHub dentro de "
                "`plan_financiero_semanal.csv`."
            )


    # ========================================================
    # GUARDADO DEL CORTE EN GITHUB
    # ========================================================

    if registrar_corte:

        if not TOKEN:

            st.error(
                "No existe GITHUB_TOKEN en los Secrets "
                "de Streamlit."
            )

        elif not puede_editar_efectivo:

            st.error(
                "No se puede registrar el corte mientras "
                "la edición esté bloqueada."
            )

        else:

            fecha_corte = datetime.now(
                tz_gdl
            ).strftime(
                "%Y-%m-%d"
            )

            try:

                # ------------------------------------------------
                # OBTENER SIEMPRE LA VERSIÓN ACTUAL DE GITHUB
                # ------------------------------------------------

                g = Github(TOKEN)

                repo = g.get_repo(
                    REPO_NAME
                )

                try:

                    archivo_plan = repo.get_contents(
                        PLAN_FILE_PATH
                    )

                    contenido_plan = (
                        archivo_plan
                        .decoded_content
                        .decode("utf-8")
                    )

                    df_plan_actual = pd.read_csv(
                        io.StringIO(
                            contenido_plan
                        )
                    )

                    sha_plan = archivo_plan.sha

                except Exception:

                    df_plan_actual = pd.DataFrame(
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


                # ------------------------------------------------
                # EVITAR DOBLE REGISTRO EL MISMO DÍA
                # ------------------------------------------------

                if (
                    not df_plan_actual.empty
                    and "Fecha_Corte"
                    in df_plan_actual.columns
                ):

                    fechas_existentes = (
                        df_plan_actual[
                            "Fecha_Corte"
                        ]
                        .astype(str)
                        .tolist()
                    )

                    if fecha_corte in fechas_existentes:

                        st.warning(
                            f"Ya existe un corte registrado "
                            f"para {fecha_corte}."
                        )

                        st.stop()


                # ------------------------------------------------
                # NÚMERO DE SEMANA
                # ------------------------------------------------

                ahora_gdl = datetime.now(
                    tz_gdl
                )

                numero_semana = (
                    ahora_gdl
                    .isocalendar()
                    .week
                )

                semana = (
                    f"{ahora_gdl.year}"
                    f"-W"
                    f"{numero_semana:02d}"
                )


                # ------------------------------------------------
                # NUEVO CORTE
                # ------------------------------------------------

                nuevo_corte = pd.DataFrame(
                    [
                        {
                            "Fecha_Corte":
                                fecha_corte,

                            "Semana":
                                semana,

                            "Ingreso_Semanal":
                                INGRESO_SEMANAL,

                            "Gastos_Fijos":
                                GASTO_CASA
                                + GASOLINA
                                + CONSULTA
                                + GASTOS_HIJA,

                            "Ahorro_Semanal":
                                TOTAL_AHORRO_MENSUAL_SEM,

                            "Disponible":
                                DISPONIBLE_SEMANAL,

                            "Usuario":
                                current_user
                        }
                    ]
                )


                df_plan_actual = pd.concat(
                    [
                        df_plan_actual,
                        nuevo_corte
                    ],
                    ignore_index=True
                )


                # ------------------------------------------------
                # NORMALIZAR NUMÉRICOS
                # ------------------------------------------------

                for columna in [
                    "Ingreso_Semanal",
                    "Gastos_Fijos",
                    "Ahorro_Semanal",
                    "Disponible"
                ]:

                    if columna in df_plan_actual.columns:

                        df_plan_actual[
                            columna
                        ] = pd.to_numeric(
                            df_plan_actual[
                                columna
                            ],
                            errors="coerce"
                        )


                # ------------------------------------------------
                # CSV
                # ------------------------------------------------

                csv_plan = df_plan_actual.to_csv(
                    index=False,
                    encoding="utf-8-sig"
                )


                # ------------------------------------------------
                # ACTUALIZAR GITHUB
                # ------------------------------------------------

                if sha_plan:

                    repo.update_file(
                        PLAN_FILE_PATH,
                        f"Registro corte semanal {fecha_corte}",
                        csv_plan,
                        sha_plan
                    )

                else:

                    repo.create_file(
                        PLAN_FILE_PATH,
                        f"Creación plan financiero {fecha_corte}",
                        csv_plan
                    )


                # ------------------------------------------------
                # ACTUALIZAR SESIÓN
                # ------------------------------------------------

                st.session_state[
                    "df_plan_semanal"
                ] = df_plan_actual

                st.session_state[
                    "force_reload_plan"
                ] = False


                # ------------------------------------------------
                # LIBERAR LOCK
                # ------------------------------------------------

                try:

                    lock_actual = repo.get_contents(
                        LOCK_FILE_PATH
                    )

                    repo.delete_file(
                        path=LOCK_FILE_PATH,

                        message=(
                            f"UNLOCK PLAN // "
                            f"{current_user}"
                        ),

                        sha=lock_actual.sha
                    )

                except:

                    pass


                st.success(
                    f"Corte {semana} registrado "
                    f"correctamente en GitHub."
                )

                time.sleep(1)

                st.rerun()


            except Exception as e:

                st.error(
                    f"No fue posible guardar el corte "
                    f"en GitHub: {e}"
                )


    # ========================================================
    # HISTORIAL DE CORTES
    # ========================================================

    st.markdown(
        """
        <div style="
            color:#00FFAA;
            font-size:11px;
            font-weight:800;
            letter-spacing:1.5px;
            text-transform:uppercase;
            margin:25px 0 10px 0;
        ">
            HISTORIAL DE CORTES SEMANALES
        </div>
        """,
        unsafe_allow_html=True
    )


    df_hist_plan = get_plan_data_from_git(
        force_reload=True
    )


    if df_hist_plan.empty:

        st.info(
            "Todavía no existen cortes registrados."
        )

    else:

        df_hist_plan = df_hist_plan.copy()


        if "Fecha_Corte" in df_hist_plan.columns:

            df_hist_plan = df_hist_plan.sort_values(
                "Fecha_Corte",
                ascending=False
            )


        columnas_mostrar = [

            "Fecha_Corte",

            "Semana",

            "Ingreso_Semanal",

            "Gastos_Fijos",

            "Ahorro_Semanal",

            "Disponible",

            "Usuario"
        ]


        columnas_mostrar = [

            c

            for c in columnas_mostrar

            if c in df_hist_plan.columns

        ]


        df_hist_plan_visual = (
            df_hist_plan[
                columnas_mostrar
            ].copy()
        )


        for columna in [

            "Ingreso_Semanal",

            "Gastos_Fijos",

            "Ahorro_Semanal",

            "Disponible"

        ]:

            if columna in df_hist_plan_visual.columns:

                df_hist_plan_visual[
                    columna
                ] = pd.to_numeric(
                    df_hist_plan_visual[
                        columna
                    ],
                    errors="coerce"
                )


        formato_monedas = {}


        for columna in [

            "Ingreso_Semanal",

            "Gastos_Fijos",

            "Ahorro_Semanal",

            "Disponible"

        ]:

            if columna in df_hist_plan_visual.columns:

                formato_monedas[
                    columna
                ] = "${:,.2f}"


        if formato_monedas:

            st.dataframe(
                df_hist_plan_visual.style.format(
                    formato_monedas
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.dataframe(
                df_hist_plan_visual,
                use_container_width=True,
                hide_index=True
            )
