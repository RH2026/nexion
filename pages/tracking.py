import base64
from datetime import datetime
import io
import re
import time
import unicodedata
import requests
import pandas as pd
import streamlit as st
import math

from auth import exigir_autenticacion

exigir_autenticacion("tracking")

st.set_page_config(
    page_title="JYPESA | Tracking",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── TEMA Y CSS MAESTROS ──────────────────────────────────────────
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
    "logo": "n1.png",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap');

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(15px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

header, footer, [data-testid="stHeader"] {{
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}}

[data-testid="collapsedControl"], 
[data-testid="stSidebar"], 
[data-testid="stToolbar"], 
.viewerBadge_container__1QSob, 
#MainMenu, 
button[kind="header"] {{
    visibility: hidden !important;
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

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

div.stButton > button, div.stDownloadButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 32px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {{
    gap: 0.45rem !important;
}}

div[data-testid="stPopoverBody"] .stButton {{
    margin-bottom: 0rem !important;
}}

div[data-testid="stPopoverBody"] [data-testid="stExpander"] {{
    border: none !important;
    background: transparent !important;
    margin-bottom: 0rem !important;
    > div {{ padding: 0 !important; }}
}}

.footer {{ 
    position: fixed; 
    bottom: 0 !important; 
    left: 0 !important; 
    width: 100% !important; 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['sub']} !important; 
    text-align: center; 
    padding: 12px 0px !important; 
    font-size: 9px; 
    letter-spacing: 2px; 
    border-top: 1px solid {vars_css['border']} !important; 
    z-index: 999999 !important; 
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---- REGISTRAR ACCESO GITHUB ----
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

def registrar_acceso_github(usuario, modulo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/auditoria_accesos.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if r.status_code == 200:
        file_data = r.json()
        sha = file_data.get("sha", "")
        content_decoded = base64.b64decode(file_data.get("content", "")).decode("utf-8")
        df_aud = pd.read_csv(io.StringIO(content_decoded))
    else:
        df_aud = pd.DataFrame(columns=["FECHA_HORA", "USUARIO", "MODULO"])
        sha = ""

    nuevo_registro = pd.DataFrame([{"FECHA_HORA": fecha_hora, "USUARIO": usuario, "MODULO": modulo}])
    df_aud = pd.concat([df_aud, nuevo_registro], ignore_index=True)
    csv_string = df_aud.to_csv(index=False)
    payload = {
        "message": f"Registro de acceso de {usuario} al módulo {modulo}",
        "content": base64.b64encode(csv_string.encode()).decode()
    }
    if sha:
        payload["sha"] = sha
    requests.put(url, json=payload, headers=headers)

# ==========================================
# SISTEMA DE SEGURIDAD PRO (VALIDACIÓN DE SESIÓN Y BLINDAJE)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "tracking.py"
    st.switch_page("log.py")

def verificar_permiso_pagina(modulo, submodulo=None):
    permisos = st.session_state.get("permisos", {})
    if st.session_state.get("usuario_activo", "").upper() == "RIGOBERTO":
        return True
        
    if not permisos.get(modulo.upper(), False):
        st.markdown(
            f"""
            <div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #FFD700; padding: 20px 25px; border-radius: 8px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <div style="width: 10px; height: 10px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 8px #FFD700;"></div>
                    <span style="color: #FFD700; font-size: 13px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">
                        ACCESS RESTRICTED // MÓDULO NO AUTORIZADO
                    </span>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 600; padding-left: 20px;">
                    No tienes permisos para acceder al módulo: <b style="color: white; text-transform: uppercase;">{modulo}</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_regresar_m, col_vacia_m = st.columns([1.5, 4])
        with col_regresar_m:
            if st.button("REGRESAR AL INICIO", key="btn_regresar_modulo", use_container_width=True):
                st.switch_page("dashboard.py")
        st.stop()

verificar_permiso_pagina("tracking")

# ==========================================
# FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================
@st.cache_data(ttl=60)
def cargar_datos_dashboard():
    t = int(time.time())
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
    try:
        df = pd.read_csv(url, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return None

if "menu_main" not in st.session_state:
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1
if "tipo_resultado" not in st.session_state:
    st.session_state.tipo_resultado = "OPERACION"

# ==========================================
# HEADER CON 4 COLUMNAS (ESPACIOS CONSERVADOS SIN CAJA DE BÚSQUEDA)
# ==========================================
header_zone = st.container()
with header_zone:
    c1, c2, c3, c4 = st.columns([1.5, 3.5, 0.9, 0.9], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=160)
        except:
            st.write("**NEXION**")

    with c2:
        azul_nexion = "#82D4E6"
        oro_brillante = "#FFD700"
        ruta = f"NEXION <span style='color: {azul_nexion}; font-weight: 500; margin: 0 10px; font-size: 16px;'>|</span> <span style='color: {oro_brillante}; font-weight: 500;'>TRACKING & TRAYECTORIA</span>"
        st.markdown(
            f"""
            <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
                <p style='font-size: 13px; letter-spacing: 5px; color: {vars_css['sub']}; margin: 0; font-weight: 500; text-transform: uppercase; text-align: center;'>
                    {ruta}
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with c3:
        # Espacio conservado exactamente idéntico al original, sin la caja de búsqueda en el header
        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

    with c4:
        with st.popover("☰ Menú", use_container_width=True):
            usuario = st.session_state.get("usuario_activo", "GUEST")
            permisos = st.session_state.get("permisos", {})
            nombre_display = st.session_state.get("nombre_completo", "OPERADOR DESCONOCIDO")
        
            st.markdown(
                f"""
                <div style='background-color: rgba(255,255,255,0.05); padding: 8px 10px; border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #00D4FF;'>
                    <p style='color:#00D4FF; font-size:9px; font-weight:500; margin:0; letter-spacing:1px;'>USUARIO ACTIVO</p>
                    <p style='color:{vars_css['text']}; font-size:13px; font-weight:500; margin:0;'>{nombre_display.upper()}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
        
            if permisos.get("DASHBOARD", False):
                if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                    registrar_acceso_github(usuario, "DASHBOARD")
                    st.session_state.menu_main = "DASHBOARD"
                    st.session_state.menu_sub = "GENERAL"
                    st.session_state.busqueda_activa = False
                    st.switch_page("dashboard.py")
        
            if permisos.get("SEGUIMIENTO", False):
                with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                    opciones_seg_posibles = ["ALERTAS", "GANTT", "INCIDENCIAS"]
                    opciones_seg = [s for s in opciones_seg_posibles if permisos.get(s, False)]
                    for s in opciones_seg:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_sub_{s}2"):
                            registrar_acceso_github(usuario, f"SEGUIMIENTO - {s}")
                            st.session_state.menu_main = "SEGUIMIENTO"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "INCIDENCIAS":
                                st.switch_page("pages/incidencias_tr.py")
                            else:
                                st.rerun()
        
            if permisos.get("ENTREGAS", False):
                with st.expander("ENTREGAS", expanded=(st.session_state.menu_main == "ENTREGAS")):
                    opciones_ent_posibles = ["AGC", "AMAZON", "BARCELO", "NACIONAL"]
                    opciones_ent = [s for s in opciones_ent_posibles if permisos.get(s, False)]
                    for s in opciones_ent:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_ent_{s}2"):
                            registrar_acceso_github(usuario, f"ENTREGAS - {s}")
                            st.session_state.menu_main = "ENTREGAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "AGC":
                                st.switch_page("pages/entregas_agc.py")
                            elif s == "NACIONAL":
                                st.switch_page("pages/envios.py")
                            else:
                                st.rerun()
        
            if permisos.get("REPORTES", False):
                with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                    opciones_rep_posibles = ["COSTOS CEDIS", "ANALISIS MENSUAL", "DETALLE COSTOS", "ENVIOS ESPECIALES", "ENVIO DE MUESTRAS"]
                    opciones_rep = [s for s in opciones_rep_posibles if permisos.get(s, False)]
                    for s in opciones_rep:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_rep_{s}2"):
                            registrar_acceso_github(usuario, f"REPORTES - {s}")
                            st.session_state.menu_main = "REPORTES"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "ENVIO DE MUESTRAS":
                                st.switch_page("pages/muestras.py")
                            else:
                                st.rerun()
        
            if permisos.get("FORMATOS", False):
                with st.expander("FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")):
                    opciones_for_posibles = ["SALIDA DE PT", "CHECK LIST AGC", "QR AGC", "PREGUIA PAQMEX", "RECOLECCION 3G", "RECOLECCION ONE", "CARTA RECLAMO", "COTIZACIONES"]
                    opciones_for = [s for s in opciones_for_posibles if permisos.get(s, False)]
                    for s in opciones_for:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_for_{s}2"):
                            registrar_acceso_github(usuario, f"FORMATOS - {s}")
                            st.session_state.menu_main = "FORMATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if permisos.get("CENTRO DE DATOS", False):
                with st.expander("CENTRO DE DATOS", expanded=(st.session_state.menu_main == "CENTRO DE DATOS")):
                    opciones_hub_posibles = ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "ESCANEAR QR", "HERRAMIENTAS"]
                    opciones_hub = [s for s in opciones_hub_posibles if permisos.get(s, False)]
                    for s in opciones_hub:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_hub_{s}2"):
                            registrar_acceso_github(usuario, f"CENTRO DE DATOS - {s}")
                            st.session_state.menu_main = "CENTRO DE DATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "ASIGNAR FLETERA":
                                st.switch_page("pages/facturacion_af.py")
                            elif s == "CARGAR DATOS":
                                st.switch_page("pages/cargardt.py")
                            elif s == "ETIQUETAS":
                                st.switch_page("pages/etiquetas.py")
                            elif s == "ESCANEAR QR":
                                st.switch_page("pages/qrup.py")
                            else:
                                st.rerun()

            if permisos.get("ACCESS CONTROL", False) or usuario.upper() == "RIGOBERTO":
                if st.button("ACCESS CONTROL", use_container_width=True, key="pop_access_ctrl2"):
                    registrar_acceso_github(usuario, "ACCESS CONTROL")
                    st.session_state.menu_main = "ACCESS CONTROL"
                    st.session_state.menu_sub = "SETTINGS"
                    st.switch_page("pages/accesscontrol.py")
        
            st.markdown("<hr style='margin: 4px 0; opacity: 0.1;'>", unsafe_allow_html=True)
            if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.autenticado = False
                st.session_state.splash_completado = False
                st.rerun()

st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:15px 0; opacity:0.1;'>", unsafe_allow_html=True)


# ==========================================
# CUERPO PRINCIPAL: CENTRO DE BÚSQUEDA TIPO TRES GUERRAS (ESTILO NEXION)
# ==========================================
def main():
    # ── BLOQUE DE BÚSQUEDA CENTRALIZADO E IMPRESIONANTE ────────────────────────
    st.markdown("""
        <div style="text-align: center; padding: 20px 0 25px 0; font-family: 'Inter', sans-serif;">
            <p style="color: #00FFAA; font-size: 11px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">
                NEXION SMART LOGISTICS // RASTREO
            </p>
            <h1 style="color: white; font-size: 32px; font-weight: 800; margin: 0; letter-spacing: 1px;">
                Para realizar la <span style="color: #00FFAA;">búsqueda</span> ingrese el <span style="color: #82D4E6;">talón o pedido</span>
            </h1>
        </div>
    """, unsafe_allow_html=True)

    # Contenedor centrado para la caja de búsqueda y botón
    col_l, col_c, col_r = st.columns([1, 2.5, 1])
    with col_c:
        es_atencion3g = st.session_state.get("usuario_activo", "").upper() == "ATENCION3G"
        key_actual = f"main_search_v{st.session_state.search_key_version}"

        query = st.text_input(
            "Buscar en central",
            placeholder="🔍 INGRESE NÚMERO DE GUÍA, PEDIDO O CLIENTE..." if not es_atencion3g else "🔍 BUSCADOR DESACTIVADO",
            label_visibility="collapsed",
            key=key_actual,
            disabled=es_atencion3g,
        )

        btn_buscar = st.button("RASTREAR ➔", use_container_width=True, type="primary")

        if query or btn_buscar:
            if query:
                url_raw = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
                try:
                    df_matriz_fresco = pd.read_csv(url_raw)
                    df_matriz_fresco.columns = df_matriz_fresco.columns.str.strip()
                except Exception:
                    df_matriz_fresco = cargar_datos_dashboard()

                res_ops = pd.DataFrame()
                if df_matriz_fresco is not None:
                    cols_op = ["NÚMERO DE GUÍA", "NÚMERO DE PEDIDO", "NO CLIENTE", "NOMBRE DEL CLIENTE", "DESTINO"]
                    cols_op_disp = [c for c in cols_op if c in df_matriz_fresco.columns]
                    if cols_op_disp:
                        mask_ops = df_matriz_fresco[cols_op_disp].astype(str).apply(
                            lambda x: x.str.contains(query, case=False, na=False)
                        ).any(axis=1)
                        res_ops = df_matriz_fresco[mask_ops].copy()

                if not res_ops.empty:
                    st.session_state.busqueda_activa = True
                    st.session_state.tipo_resultado = "OPERACION"
                    st.session_state.resultado_busqueda = res_ops
                else:
                    st.session_state.busqueda_activa = False
                    st.session_state.resultado_busqueda = None
                    st.toast("Sin resultados en Matriz Global", icon="⚠️")

    # ── RENDERIZADO DE RESULTADOS DE BÚSQUEDA (TIMELINE DETALLADO) ────────────────────────
    if st.session_state.busqueda_activa and st.session_state.resultado_busqueda is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        resultados = st.session_state.resultado_busqueda
        total = len(resultados)
        azul_premium = "#00D4FF"

        col_espacio, col_cerrar = st.columns([0.85, 0.15])
        with col_cerrar:
            if st.button("✕ CERRAR RESULTADOS", key="btn_cerrar_top", use_container_width=True):
                st.session_state.busqueda_activa = False
                st.session_state.resultado_busqueda = None
                st.session_state.search_key_version += 1
                st.rerun()

        if total == 1:
            envio = resultados.iloc[0]
            entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
            f_entrega_val = envio["FECHA DE ENTREGA REAL"] if entregado_real else "PENDIENTE"
            trigger_val = str(envio.get("TRIGGER", "")).strip()
            tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]

            n_guia = envio["NÚMERO DE GUÍA"] if tiene_guia else ("GENERANDO GUÍA..." if trigger_val == "Enviada" else "EN ESPERA DE SURTIDO")
            f_promesa_dt = pd.to_datetime(envio.get("PROMESA DE ENTREGA"), dayfirst=True, errors="coerce")
            if pd.notnull(f_promesa_dt):
                f_promesa_dt = f_promesa_dt.normalize()
            hoy = pd.Timestamp(datetime.now()).normalize()

            if not tiene_guia:
                status_text, status_color = ("GENERANDO GUÍA", "#38bdf8") if trigger_val == "Enviada" else ("SURTIENDO", "#FFA500")
            elif not entregado_real:
                status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if pd.isna(f_promesa_dt) or hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
            else:
                f_entrega_dt = pd.to_datetime(envio.get("FECHA DE ENTREGA REAL"), dayfirst=True, errors="coerce")
                if pd.notnull(f_entrega_dt):
                    f_entrega_dt = f_entrega_dt.normalize()
                status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.isna(f_promesa_dt) or f_entrega_dt <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")

            tarjeta_unica_html = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 25px 30px; border-radius: 12px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px; box-shadow: 0 8px 25px rgba(0,0,0,0.4);">
                <div style="font-size: 14px; font-weight: 800; color: #00FFAA; margin-bottom: 18px; letter-spacing: 1px; text-transform: uppercase;">⚡ SEGUIMIENTO DETALLADO DE TRAYECTORIA</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;">
                    <div style="text-align: center;"><div style="width: 12px; height: 12px; background: #38bdf8; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 10px #38bdf8;"></div><div style="font-size: 10px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;">ENVÍO</div><div style="font-size: 11px; color: rgba(255,255,255,0.8); font-weight: 600; margin-top: 2px;">{envio.get('FECHA DE ENVÍO','N/A')}</div></div>
                    <div style="flex-grow: 1; height: 3px; background: #38bdf8; margin: 0 8px; opacity: 0.6; transform: translateY(-10px);"></div>
                    <div style="text-align: center;"><div style="width: 12px; height: 12px; background: #a855f7; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 10px #a855f7;"></div><div style="font-size: 10px; font-weight: 800; color: #a855f7; letter-spacing: 1px;">GUÍA</div><div style="font-size: 11px; color: rgba(255,255,255,0.8); font-weight: 600; margin-top: 2px;">{n_guia if tiene_guia else 'EN PROCESO'}</div></div>
                    <div style="flex-grow: 1; height: 3px; background: #a855f7; margin: 0 8px; opacity: 0.6; transform: translateY(-10px);"></div>
                    <div style="text-align: center;"><div style="width: 12px; height: 12px; background: #eab308; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 10px #eab308;"></div><div style="font-size: 10px; font-weight: 800; color: #eab308; letter-spacing: 1px;">PROMESA</div><div style="font-size: 11px; color: rgba(255,255,255,0.8); font-weight: 600; margin-top: 2px;">{envio.get('PROMESA DE ENTREGA','N/A')}</div></div>
                    <div style="flex-grow: 1; height: 3px; background: #00FFAA; margin: 0 8px; opacity: 0.6; transform: translateY(-10px);"></div>
                    <div style="text-align: center;"><div style="width: 12px; height: 12px; background: {status_color}; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 10px {status_color};"></div><div style="font-size: 10px; font-weight: 800; color: {status_color}; letter-spacing: 1px;">ENTREGA</div><div style="font-size: 11px; color: rgba(255,255,255,0.8); font-weight: 600; margin-top: 2px;">{f_entrega_val}</div></div>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
                    <div style="flex: 1.2; min-width: 200px;">
                        <div style="color: #00FFAA; font-size: 16px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">{envio.get('FLETERA','N/A')}</div>
                        <div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 6px;">TALÓN / FOLIO</div>
                        <div style="color: #00FFAA; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{n_guia}</div>
                        <div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 6px;">REF / PEDIDO: <span style="color: white; font-size: 13px; font-weight: 700;">{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div>
                    </div>
                    <div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;">
                        <div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / CLIENTE</div>
                        <div style="color: white; font-weight: 800; font-size: 14px; text-transform: uppercase; line-height: 1.3; margin-top: 4px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div>
                        <div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 4px;">ID: {envio.get('NO CLIENTE','')} | {envio.get('DOMICILIO','')}</div>
                        <div style="font-size: 11px; color: #00FFAA; margin-top: 6px; font-weight: 600;">📍 GDL → {envio.get('DESTINO','N/A')}</div>
                    </div>
                    <div style="flex: 1.2; min-width: 150px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;">
                        <div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN CARGA</div>
                        <div style="color: white; font-weight: 700; font-size: 12px; margin-top: 4px;">BULTOS: <span style="color: #00FFAA;">{envio.get('CANTIDAD DE CAJAS','0')}</span></div>
                        <div style="color: #00FFAA; font-weight: 800; font-size: 14px; margin-top: 4px;">$ {envio.get('COSTO DE LA GUÍA','0.00')}</div>
                    </div>
                    <div style="text-align: right; min-width: 140px;">
                        <span style="background-color: {status_color}20; color: {status_color}; padding: 6px 14px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid {status_color}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">ESTATUS: {status_text}</span>
                    </div>
                </div>
            </div>"""
            st.markdown(tarjeta_unica_html, unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'><div style='background: {azul_premium}; width: 5px; height: 22px; border-radius: 3px; box-shadow: 0 0 10px {azul_premium};'></div><span style='color: white; font-size: 15px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;'>COINCIDENCIAS ENCONTRADAS <span style='color: {azul_premium};'>({total})</span></span></div>", unsafe_allow_html=True)
            for _, d in resultados.iterrows():
                status_text = d["COMENTARIOS"] if "COMENTARIOS" in d and pd.notna(d.get("COMENTARIOS")) else "OK"
                st.markdown(f"<div style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {azul_premium};border-radius:12px;padding:18px 25px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>PEDIDO / FACTURA</span><br><b style='font-size:18px;color:{azul_premium};letter-spacing:0.5px;'># {d.get('NÚMERO DE PEDIDO','')}</b><br><span style='font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;'>Envío: {d.get('FECHA DE ENVÍO','')}</span></div><div style='flex:2.5;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CLIENTE / DESTINO</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('NOMBRE DEL CLIENTE','')}</b><br><i style='font-size:11px;color:rgba(255,255,255,0.5);font-style:normal;font-weight:600;'>{d.get('DESTINO','')}</i></div><div style='flex:1.8;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>TRANSPORTE Y GUÍA</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('FLETERA', 'LOGÍSTICA')}</b><br><span style='font-size:12px;color:{azul_premium};font-weight:700;font-family:monospace;'>{d.get('NÚMERO DE GUÍA','')}</span></div><div style='flex:1.2;text-align:right;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>ESTATUS ENTREGA</span><br><b style='font-size:14px;color:{azul_premium};'>{d.get('FECHA DE ENTREGA REAL','')}</b><br><span style='font-size:10px;color:white;font-weight:800;text-transform:uppercase;opacity:0.8;'>{status_text}</span></div></div>", unsafe_allow_html=True)

    st.markdown("<br><hr style='border-top:1px solid #ffffff; opacity:0.1;'><br>", unsafe_allow_html=True)

    # ── SECCIÓN INFERIOR: ÚLTIMOS ENVÍOS ACTIVOS ────────────────────────
    df_raw = cargar_datos_dashboard()
    if df_raw is not None:
        st.markdown("<p style='color: #00D4FF; font-weight: 800; font-size: 14px; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 20px;'>📋 ÚLTIMOS ENVÍOS ACTIVOS EN TRAYECTORIA</p>", unsafe_allow_html=True)
        
        df_recientes = df_raw.head(8).copy()
        for _, row in df_recientes.iterrows():
            pedido = row.get('NÚMERO DE PEDIDO', 'S/N')
            cliente = row.get('NOMBRE DEL CLIENTE', 'N/A')
            destino = row.get('DESTINO', 'N/A')
            guia = row.get('NÚMERO DE GUÍA', 'EN PROCESO')
            fletera = row.get('FLETERA', 'LOGÍSTICA')
            estatus_real = row.get('FECHA DE ENTREGA REAL', 'EN TRÁNSITO')
            if pd.isna(estatus_real) or str(estatus_real).strip() == "":
                estatus_real = "EN TRÁNSITO"
                color_estatus = "#38bdf8"
            else:
                estatus_real = f"ENTREGADO: {estatus_real}"
                color_estatus = "#00FFAA"

            st.markdown(f"""
                <div style="background: #263238; border: 1px solid rgba(255,255,255,0.06); border-left: 4px solid #38bdf8; border-radius: 10px; padding: 18px 22px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    <div style="flex: 1;">
                        <span style="font-size: 9px; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px;">PEDIDO / FACTURA</span>
                        <br><b style="font-size: 16px; color: #00FFAA; font-family: monospace;">#{pedido}</b>
                    </div>
                    <div style="flex: 2.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.06);">
                        <span style="font-size: 9px; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px;">CLIENTE / DESTINO</span>
                        <br><span style="font-size: 13px; color: white; font-weight: 700; text-transform: uppercase;">{str(cliente)[:45]}</span>
                        <br><span style="font-size: 11px; color: #38bdf8; font-weight: 600;">📍 {destino}</span>
                    </div>
                    <div style="flex: 1.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.06);">
                        <span style="font-size: 9px; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px;">TRANSPORTISTA / GUÍA</span>
                        <br><b style="font-size: 13px; color: white; text-transform: uppercase;">{fletera}</b>
                        <br><span style="font-size: 12px; color: #00D4FF; font-family: monospace; font-weight: 700;">{guia}</span>
                    </div>
                    <div style="text-align: right; padding-left: 15px; border-left: 1px solid rgba(255,255,255,0.06); min-width: 150px;">
                        <span style="background: {color_estatus}15; color: {color_estatus}; border: 1px solid {color_estatus}40; padding: 6px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; display: inline-block;">{estatus_real}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# ── FOOTER FIJO ────────────────────────
st.markdown(
    f"""
    <div class="footer">
        NEXION // TRACKING SYSTEM // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
