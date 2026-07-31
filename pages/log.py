import base64
from datetime import datetime
import os
import time
import pytz
import requests
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Logistics",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def registrar_acceso(usuario):
  archivo_log = "log_accesos.csv"
  zona_horaria = pytz.timezone("America/Mexico_City")
  ahora = datetime.now(zona_horaria).strftime("%Y-%m-%d %I:%M %p")
  nuevo_registro = pd.DataFrame(
      [[usuario, ahora]], columns=["Usuario", "Fecha/Hora"]
  )
  if not os.path.isfile(archivo_log):
    nuevo_registro.to_csv(archivo_log, index=False)
  else:
    nuevo_registro.to_csv(archivo_log, mode="a", header=False, index=False)


# Inicialización de estados de sesión
if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
if "splash_completado" not in st.session_state:
  st.session_state.splash_completado = False

# Estilos CSS Globales (Tema Ónix Azulado)
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* --- OCULTAR ELEMENTOS DE STREAMLIT Y GITHUB --- */
header, footer, [data-testid="stHeader"] {{
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}}

/* Ocultar el botón de la barra lateral (Sidebar toggle) */
[data-testid="collapsedControl"] {{
    display: none !important;
}}

/* Ocultar la barra lateral por completo */
[data-testid="stSidebar"] {{
    display: none !important;
}}

/* Ocultar elementos flotantes de GitHub / Deploy de Streamlit */
[data-testid="stToolbar"], 
.viewerBadge_container__1QSob, 
#MainMenu {{
    visibility: hidden !important;
    display: none !important;
}}

/* APP BASE */
html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}

.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 5rem !important;
    background-color: {vars_css['bg']} !important;
}}

/* BOTONES SLIM */
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

div.stButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
}}
</style>
""",
    unsafe_allow_html=True,
)


def login_screen():
  _, col, _ = st.columns([2, 2, 2])
  with col:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    try:
      with open("n2.png", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
      st.markdown(
          f"""
            <div style="display: flex; justify-content: center; margin-bottom: 30px;">
                <img src="data:image/png;base64,{encoded}" width="180">
            </div>
            """,
          unsafe_allow_html=True,
      )
    except Exception:
      st.markdown(
          "<h1 style='text-align:center;'>NEXION</h1>", unsafe_allow_html=True
      )

    with st.form("login_form", clear_on_submit=False):
      user_input = st.text_input("USUARIO", placeholder="Introduce tu usuario")
      pass_input = st.text_input(
          "CONTRASEÑA", type="password", placeholder="••••••••"
      )
      submit_button = st.form_submit_button(
          "VERIFY IDENTITY", use_container_width=True
      )

      if submit_button:
        lista_usuarios = st.secrets.get("usuarios", {})
        if (
            user_input in lista_usuarios
            and str(lista_usuarios[user_input]) == pass_input
        ):
          st.session_state.autenticado = True
          st.session_state.usuario_activo = user_input
          st.success(f"¡BIENVENIDO!, {user_input.upper()}")
          time.sleep(1)
          st.rerun()
        else:
          st.error("ERROR: ACCESS DENIED. INVALID CREDENTIALS.")


# FLUJO DE CONTROL: SPLASH -> LOGIN -> MULTIPÁGINA
if not st.session_state.get("splash_completado", False):
  p = st.empty()
  mensajes = [
      "ESTABLISHING SECURE ACCESS...",
      "AUTHENTICATING NEXION GATEWAY...",
      "LOGISTICS DATA FLOW INITIALIZING...",
      "SYSTEM READY...",
  ]
  for m in mensajes:
    splash_html = f"""
        <div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
            <div style="width:90px;height:90px;border:2px solid rgba(130, 212, 230, 0.15);border-top:2px solid #82D4E6;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:25px;"></div>
            <p style="font-family:monospace;font-size:11px;letter-spacing:4px;color:#FFFFFF;text-transform:uppercase;">{m}</p>
        </div>
        <style>@keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}</style>
        """
    with p.container():
      st.markdown(splash_html, unsafe_allow_html=True)
      time.sleep(0.5)
  p.empty()
  st.session_state.splash_completado = True
  st.rerun()

elif not st.session_state.get("autenticado", False):
  login_screen()

else:
  # Una vez autenticado, redirigimos limpiamente a tu primera página de la carpeta pages/
  st.switch_page("pages/asignacionfletera.py")
