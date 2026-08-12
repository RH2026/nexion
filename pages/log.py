import base64
from datetime import datetime
import os
import time
import pytz
import requests
import streamlit as st
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
# 3. REGISTRAR ACCESO
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
# 4. CARGAR DATOS DEL USUARIO
# ============================================================

def cargar_datos_usuario(usuario):

    """
    Carga permisos, nombre real y género
    directamente desde el CSV de GitHub.
    """

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

            st.session_state.nombre_completo = (
                data.get("NOMBRE REAL", usuario)
            )

            st.session_state.genero_usuario = (
                data.get("GENERO", "M")
            )

        else:

            st.session_state.permisos = {}

            st.session_state.nombre_completo = usuario

            st.session_state.genero_usuario = "M"

    except Exception:

        st.session_state.permisos = {}

        st.session_state.nombre_completo = usuario

        st.session_state.genero_usuario = "M"


# ============================================================
# 5. INICIALIZACIÓN DE SESSION STATE
# ============================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = ""

if "login_exitoso" not in st.session_state:
    st.session_state.login_exitoso = False


# ============================================================
# 6. MAPA DE PÁGINAS
# ============================================================

PAGINAS = {

    "indicadores":
        "pages/indicadores.py",

    "entregas_agc":
        "pages/entregas_agc.py",

    "corporativos":
        "pages/corporativos.py",

    "control_embarques":
        "pages/control_embarques.py",

    "rastreo":
        "pages/rastreo.py",

}


# ============================================================
# 7. OBTENER PÁGINA GUARDADA
# ============================================================

def obtener_pagina_guardada():

    try:

        pagina = st.query_params.get("page", None)

        if pagina:

            pagina = str(pagina).strip().lower()

            if pagina in PAGINAS:
                return pagina

    except Exception:

        pass

    return None


# ============================================================
# 8. GUARDAR PÁGINA ACTUAL
# ============================================================

def guardar_pagina_actual(pagina):

    pagina = str(pagina).strip().lower()

    if pagina in PAGINAS:

        st.query_params["page"] = pagina


# ============================================================
# 9. REGRESAR A LA PÁGINA GUARDADA DESPUÉS DEL LOGIN
# ============================================================

def ir_a_pagina_post_login():

    usuario = (
        st.session_state
        .get("usuario_activo", "")
        .upper()
    )

    pagina_guardada = obtener_pagina_guardada()


    # --------------------------------------------------------
    # CASO 1
    # AGC SIEMPRE ENTRA A ENTREGAS AGC
    # --------------------------------------------------------

    if usuario == "AGC":

        guardar_pagina_actual("entregas_agc")

        st.switch_page(
            "pages/entregas_agc.py"
        )

        return


    # --------------------------------------------------------
    # CASO 2
    # EXISTE UNA PÁGINA GUARDADA
    # --------------------------------------------------------

    if pagina_guardada:

        ruta = PAGINAS.get(
            pagina_guardada
        )

        if ruta:

            st.switch_page(ruta)

            return


    # --------------------------------------------------------
    # CASO 3
    # PRIMERA ENTRADA
    # --------------------------------------------------------

    guardar_pagina_actual("indicadores")

    st.switch_page(
        "pages/indicadores.py"
    )


# ============================================================
# 10. CSS
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
# 11. PANTALLA DE LOGIN
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

            with open("n2.png", "rb") as f:

                encoded = base64.b64encode(
                    f.read()
                ).decode()

            st.markdown(
                f"""
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
                """,
                unsafe_allow_html=True
            )

        except:

            st.markdown(
                """
                <h1 style="text-align:center;">
                    NEXION
                </h1>
                """,
                unsafe_allow_html=True
            )


        # ----------------------------------------------------
        # FORMULARIO LOGIN
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
                    and
                    str(lista_usuarios[user_input])
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


                    st.session_state.login_exitoso = True


                else:

                    st.error(
                        "ERROR: ACCESS DENIED."
                    )


        # ====================================================
        # LOGIN EXITOSO
        # ====================================================

        if st.session_state.get(
            "login_exitoso",
            False
        ):

            st.success(
                f"¡BIENVENIDO!, "
                f"{st.session_state.get('nombre_completo', '').upper()}"
            )

            time.sleep(0.8)

            st.session_state.login_exitoso = False


            # ------------------------------------------------
            # IR A LA ÚLTIMA PÁGINA
            # ------------------------------------------------

            ir_a_pagina_post_login()


# ============================================================
# 12. SPLASH SCREEN
# ============================================================

if not st.session_state.splash_completado:

    p = st.empty()

    mensajes = [
        "ESTABLISHING SECURE ACCESS...",
        "AUTHENTICATING NEXION GATEWAY...",
        "LOGISTICS DATA FLOW INITIALIZING...",
        "SYSTEM READY..."
    ]


    for m in mensajes:

        p.markdown(
            f'''
            <div style="
                height:70vh;
                display:flex;
                flex-direction:column;
                justify-content:center;
                align-items:center;
            ">

                <div style="
                    width:90px;
                    height:90px;
                    border:2px solid rgba(130,212,230,0.15);
                    border-top:2px solid #82D4E6;
                    border-radius:50%;
                    animation:spin 1s linear infinite;
                    margin-bottom:25px;
                "></div>

                <p style="
                    font-family:monospace;
                    font-size:11px;
                    letter-spacing:4px;
                    color:#FFFFFF;
                    text-transform:uppercase;
                ">
                    {m}
                </p>

            </div>

            <style>

            @keyframes spin {{

                100% {{
                    transform:rotate(360deg);
                }}

            }}

            </style>
            ''',
            unsafe_allow_html=True
        )

        time.sleep(0.4)


    p.empty()

    st.session_state.splash_completado = True

    st.rerun()


# ============================================================
# 13. CONTROL DE AUTENTICACIÓN
# ============================================================

elif not st.session_state.autenticado:

    login_screen()


# ============================================================
# 14. USUARIO AUTENTICADO
# ============================================================

else:

    # --------------------------------------------------------
    # Si ya estamos autenticados en el archivo principal,
    # NO mandar automáticamente a indicadores.
    #
    # Esto es importante para que un refresh no destruya
    # la navegación.
    # --------------------------------------------------------

    st.stop()
