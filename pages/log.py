import streamlit as st
import base64
from datetime import datetime
import os
import time
import pytz
import pandas as pd


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================

st.set_page_config(
    page_title="JYPESA | Logistics",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. CONFIGURACIÓN GITHUB
# ============================================================

GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]


# ============================================================
# 3. MAPA DE DESTINOS
# ============================================================

DESTINOS_VALIDOS = {
    "accesscontrol": "pages/accesscontrol.py",
    "asignacionfletera": "pages/asignacionfletera.py",
    "entregas_agc": "pages/entregas_agc.py",
    "envios": "pages/envios.py",
    "etiquetas": "pages/etiquetas.py",
    "dashboard": "dashboard.py",
    "locales": "pages/locales.py",
    "log": "pages/log.py",
    "muestras": "pages/muestras.py",
    "picking": "pages/picking.py",
    "qrup": "pages/qrup.py",
    "facturacion": "pages/facturacion_af.py",
    "main": "pages/main.py",
    "cargardt": "pages/cargardt.py",
    "quejas": "pages/quejas.py",
}


# ============================================================
# 4. OBTENER PÁGINA DE RETORNO
# ============================================================

def obtener_pagina_destino():

    # --------------------------------------------------------
    # 1. PRIMERO: URL
    # --------------------------------------------------------
    try:
        pagina_url = st.query_params.get("return_to", "")

        if pagina_url:
            pagina_url = str(pagina_url).strip().lower()

            if pagina_url in DESTINOS_VALIDOS:
                return pagina_url

    except Exception:
        pass

    # --------------------------------------------------------
    # 2. SEGUNDO: SESSION STATE
    # --------------------------------------------------------
    pagina_session = st.session_state.get("pagina_pendiente", "")

    if pagina_session:
        pagina_session = str(pagina_session).strip().lower()

        if pagina_session in DESTINOS_VALIDOS:
            return pagina_session

    # --------------------------------------------------------
    # 3. SI NO HAY DESTINO: DASHBOARD
    # --------------------------------------------------------
    return "dashboard"


# ============================================================
# 5. REGISTRAR ACCESO (LOCAL)
# ============================================================

def registrar_acceso(usuario):

    archivo_log = "log_accesos.csv"

    zona_horaria = pytz.timezone("America/Mexico_City")

    ahora = datetime.now(zona_horaria).strftime(
        "%Y-%m-%d %I:%M %p"
    )

    nuevo_registro = pd.DataFrame(
        [[usuario, ahora]],
        columns=["Usuario", "Fecha/Hora"]
    )

    if not os.path.isfile(archivo_log):

        nuevo_registro.to_csv(
            archivo_log,
            index=False
        )

    else:

        nuevo_registro.to_csv(
            archivo_log,
            mode="a",
            header=False,
            index=False
        )


# ============================================================
# 6. CARGAR DATOS DEL USUARIO
# ============================================================

def cargar_datos_usuario(usuario):

    try:

        url = (
            f"https://raw.githubusercontent.com/"
            f"{GITHUB_USER}/{GITHUB_REPO}/"
            f"refs/heads/main/permisos_usuarios.csv"
            f"?nocache={int(time.time())}"
        )

        df = pd.read_csv(url)

        df.columns = [
            str(c).upper().strip()
            for c in df.columns
        ]

        user_row = df[
            df["USUARIO"].str.upper() == usuario.upper()
        ]

        if not user_row.empty:

            data = user_row.iloc[0].to_dict()

            st.session_state.permisos = data

            nombre_raw = data.get(
                "NOMBRE REAL",
                usuario
            )

            st.session_state.nombre_completo = str(
                nombre_raw
                if pd.notna(nombre_raw)
                else usuario
            ).strip()

            st.session_state.genero_usuario = str(
                data.get("GENERO", "M")
            ).strip()

        else:

            st.session_state.permisos = {}

            st.session_state.nombre_completo = str(
                usuario
            ).strip()

            st.session_state.genero_usuario = "M"

    except Exception:

        st.session_state.permisos = {}

        st.session_state.nombre_completo = str(
            usuario
        ).strip()

        st.session_state.genero_usuario = "M"


# ============================================================
# 7. SESSION STATE
# ============================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = ""


# ============================================================
# 8. CSS MAESTRO
# ============================================================

vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "border": "#4B5D67"
}

st.markdown(
    f"""
<style>

header,
[data-testid="stHeader"],
[data-testid="collapsedControl"],
[data-testid="stSidebar"],
.viewerBadge_container__1QSob {{
    visibility: hidden !important;
    display: none !important;
}}

html,
body,
.stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif;
}}

.block-container {{
    padding-top: 0.8rem !important;
    background-color: {vars_css['bg']} !important;
}}

div.stButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 34px !important;
    width: 100% !important;
}}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# 9. PANTALLA DE LOGIN
# ============================================================

def login_screen():

    _, col, _ = st.columns([2, 2, 2])

    with col:

        st.markdown(
            "<br><br><br>",
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        try:

            if os.path.exists("n2.png"):

                with open("n2.png", "rb") as f:
                    encoded = base64.b64encode(
                        f.read()
                    ).decode()

                st.markdown(
                    f'''
                    <div style="
                        display:flex;
                        justify-content:center;
                        margin-bottom:30px;
                    ">
                        <img
                            src="data:image/png;base64,{encoded}"
                            width="180"
                        >
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

            elif os.path.exists("n1.png"):

                with open("n1.png", "rb") as f:
                    encoded = base64.b64encode(
                        f.read()
                    ).decode()

                st.markdown(
                    f'''
                    <div style="
                        display:flex;
                        justify-content:center;
                        margin-bottom:30px;
                    ">
                        <img
                            src="data:image/png;base64,{encoded}"
                            width="180"
                        >
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    "<h1 style='text-align:center;'>NEXION</h1>",
                    unsafe_allow_html=True
                )

        except Exception:

            st.markdown(
                "<h1 style='text-align:center;'>NEXION</h1>",
                unsafe_allow_html=True
            )


        # ----------------------------------------------------
        # FORMULARIO
        # ----------------------------------------------------

        with st.form("login_form"):

            user_input = st.text_input(
                "USUARIO",
                placeholder="Introduce tu usuario"
            )

            pass_input = st.text_input(
                "CONTRASEÑA",
                type="password",
                placeholder="••••••••"
            )

            submit = st.form_submit_button(
                "VERIFY IDENTITY",
                use_container_width=True
            )


            # ------------------------------------------------
            # VALIDAR LOGIN
            # ------------------------------------------------

            if submit:

                lista_usuarios = st.secrets.get(
                    "usuarios",
                    {}
                )

                if (
                    user_input in lista_usuarios
                    and str(lista_usuarios[user_input])
                    == pass_input
                ):

                    # ----------------------------------------
                    # AUTENTICACIÓN
                    # ----------------------------------------

                    st.session_state.autenticado = True

                    st.session_state.usuario_activo = (
                        user_input
                    )


                    # ----------------------------------------
                    # CARGAR DATOS
                    # ----------------------------------------

                    cargar_datos_usuario(
                        user_input
                    )


                    # ----------------------------------------
                    # REGISTRAR ACCESO
                    # ----------------------------------------

                    registrar_acceso(
                        user_input
                    )


                    # ----------------------------------------
                    # MENSAJE
                    # ----------------------------------------

                    nombre_limpio = str(
                        st.session_state.get(
                            "nombre_completo",
                            user_input
                        )
                    )


                    st.success(
                        f"¡BIENVENIDO!, "
                        f"{nombre_limpio.upper()}"
                    )


                    time.sleep(0.8)


                    # ----------------------------------------
                    # RECUPERAR DESTINO
                    # ----------------------------------------

                    pagina_destino = (
                        obtener_pagina_destino()
                    )


                    # ----------------------------------------
                    # GUARDAR DESTINO
                    # ----------------------------------------

                    st.session_state[
                        "pagina_pendiente"
                    ] = pagina_destino


                    # ----------------------------------------
                    # LIMPIAR RETURN_TO
                    # NO LO HACEMOS ANTES DEL SWITCH
                    # ----------------------------------------

                    destino_archivo = (
                        DESTINOS_VALIDOS[
                            pagina_destino
                        ]
                    )


                    # ----------------------------------------
                    # IR A LA PÁGINA ORIGINAL
                    # ----------------------------------------

                    st.switch_page(
                        destino_archivo
                    )

                else:

                    st.error(
                        "ERROR: ACCESS DENIED."
                    )


# ============================================================
# 10. FLUJO DE EJECUCIÓN
# ============================================================

if not st.session_state.splash_completado:

    p = st.empty()

    for m in [
        "ESTABLISHING SECURE ACCESS...",
        "AUTHENTICATING NEXION GATEWAY...",
        "LOGISTICS DATA FLOW INITIALIZING...",
        "SYSTEM READY..."
    ]:

        html_splash = f'<div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;"><div style="width:90px;height:90px;border:2px solid rgba(130,212,230,0.15);border-top:2px solid #82D4E6;border-radius:50%;animation:nexionSpin 1s linear infinite;margin-bottom:25px;"></div><p style="font-family:monospace;font-size:11px;letter-spacing:4px;color:#FFFFFF;text-transform:uppercase;">{m}</p></div><style>@keyframes nexionSpin{{100%{{transform:rotate(360deg);}}}}</style>'

        p.markdown(
            html_splash,
            unsafe_allow_html=True
        )

        time.sleep(0.4)

    p.empty()

    st.session_state.splash_completado = True

    st.rerun()


elif not st.session_state.autenticado:

    login_screen()


else:

    # ========================================================
    # SI YA ESTÁ AUTENTICADO Y LLEGA DIRECTAMENTE A LOG
    # ========================================================

    pagina_destino = obtener_pagina_destino()

    st.session_state[
        "pagina_pendiente"
    ] = pagina_destino

    st.switch_page(
        DESTINOS_VALIDOS[pagina_destino]
    )
