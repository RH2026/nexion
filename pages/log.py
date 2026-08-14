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
# 5. CARGAR DATOS DEL USUARIO (BLINDADO)
# ============================================================
def cargar_datos_usuario(usuario):
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/main/permisos_usuarios.csv?nocache={int(time.time())}"
        df = pd.read_csv(url)
        df.columns = [str(c).upper().strip() for c in df.columns]
        
        user_row = df[df["USUARIO"].str.upper() == usuario.upper()]
        
        if not user_row.empty:
            data = user_row.iloc[0].to_dict()
            st.session_state.permisos = data
            # BLINDAJE: Forzar siempre a texto con str() y strip()
            nombre_raw = data.get("NOMBRE REAL", usuario)
            st.session_state.nombre_completo = str(nombre_raw if pd.notna(nombre_raw) else usuario).strip()
            st.session_state.genero_usuario = str(data.get("GENERO", "M")).strip()
        else:
            st.session_state.permisos = {}
            st.session_state.nombre_completo = str(usuario).strip()
            st.session_state.genero_usuario = "M"
    except Exception:
        st.session_state.permisos = {}
        st.session_state.nombre_completo = str(usuario).strip()
        st.session_state.genero_usuario = "M"

# ============================================================
# 11. LOGIN (CORREGIDO)
# ============================================================
def login_screen():
    _, col, _ = st.columns([2, 2, 2])
    with col:
        # ... (Tu código de logo y formulario se mantiene igual) ...
        with st.form("login_form"):
            user_input = st.text_input("USUARIO", placeholder="Introduce tu usuario")
            pass_input = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")
            submit = st.form_submit_button("VERIFY IDENTITY", use_container_width=True)

            if submit:
                lista_usuarios = st.secrets.get("usuarios", {})
                if user_input in lista_usuarios and str(lista_usuarios[user_input]) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = str(user_input)
                    cargar_datos_usuario(user_input) # Ahora esto es seguro
                    st.session_state.login_exitoso = True
                else:
                    st.error("ERROR: ACCESS DENIED.")

        if st.session_state.get("login_exitoso", False):
            # BLINDAJE FINAL: Conversión explícita a string antes de .upper()
            nombre_limpio = str(st.session_state.get('nombre_completo', 'OPERADOR'))
            st.success(f"¡BIENVENIDO!, {nombre_limpio.upper()}")
            time.sleep(0.8)
            st.session_state.login_exitoso = False
            ir_a_pagina_post_login()

# ... (El resto de tus funciones como obtener_destino, registrar_acceso, etc., se mantienen igual)
