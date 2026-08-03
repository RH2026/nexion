import base64
from datetime import datetime
import io
import re
import time
import unicodedata
import zipfile
import calendar
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit.components.v1 as components
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Logistics",
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* --- ANIMACIONES DE ENTRADA --- */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(15px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

/* --- OCULTAR ELEMENTOS DE STREAMLIT Y SIDEBAR --- */
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

/* BOTONES SLIM Y BOTONES DE DESCARGA */
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

/* --- SEPARACIÓN EQUILIBRADA EN EL POPOVER --- */
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
    > div {{
        padding: 0 !important;
    }}
}}

/*FOOTER FIJO */
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


# ==========================================
# 2. SISTEMA DE SEGURIDAD PRO (VALIDACIÓN DE SESIÓN Y BLINDAJE)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/entregas_agc.py"
    st.switch_page("pages/log.py")

def verificar_permiso_pagina(modulo, submodulo=None):
    permisos = st.session_state.get("permisos", {})
    
    if not permisos.get(modulo.upper(), False):
        st.markdown(
            f"""
            <div style="
                background: {vars_css['card']}; 
                border: 1px solid {vars_css['border']}; 
                border-left: 5px solid #FFD700; 
                padding: 20px 25px; 
                border-radius: 8px; 
                width: 100%; 
                font-family: 'Inter', sans-serif; 
                color: white; 
                box-sizing: border-box; 
                margin-bottom: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
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
                st.switch_page("indicadores.py")
        st.stop()
            
    if submodulo and not permisos.get(submodulo.upper(), False):
        st.markdown(
            f"""
            <div style="
                background: {vars_css['card']}; 
                border: 1px solid {vars_css['border']}; 
                border-left: 5px solid #FFD700; 
                padding: 20px 25px; 
                border-radius: 8px; 
                width: 100%; 
                font-family: 'Inter', sans-serif; 
                color: white; 
                box-sizing: border-box; 
                margin-bottom: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <div style="width: 10px; height: 10px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 8px #FFD700;"></div>
                    <span style="color: #FFD700; font-size: 13px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">
                        ACCESS RESTRICTED // SECCIÓN BLOQUEADA
                    </span>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 600; padding-left: 20px;">
                    No tienes permisos para acceder a la sección: <b style="color: white; text-transform: uppercase;">{submodulo}</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col_regresar_s, col_vacia_s = st.columns([1.5, 4])
        with col_regresar_s:
            if st.button("REGRESAR AL INICIO", key="btn_regresar_submodulo", use_container_width=True):
                st.switch_page("pages/indicadores.py")
        st.stop()

# Blindaje correcto para la página de Dashboard
verificar_permiso_pagina("DASHBOARD")


# ==========================================
# 3. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================
@st.cache_data(ttl=60)
def obtener_matriz_github():
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv?nocache={int(time.time())}"
    try:
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except Exception as e:
        st.error(f"Error fatal al conectar con GitHub: {e}")
        return pd.DataFrame()


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


def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    ).upper()
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    return " ".join(texto.split())


# Inicialización segura de estados de menú
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "ENTREGAS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "AGC"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1
if "tipo_resultado" not in st.session_state:
    st.session_state.tipo_resultado = "OPERACION"


# ==========================================
# 4. HEADER CON 4 COLUMNAS Y MENÚ BLINDADO
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
        texto_principal = st.session_state.menu_main
        azul_nexion = "#82D4E6"
        oro_brillante = "#FFD700"

        if texto_principal == "DASHBOARD":
            texto_principal = f"NEXION <span style='color: {azul_nexion}; font-weight: 500; margin: 0 10px; font-size: 16px;'>|</span> SMART LOGISTICS"

        if st.session_state.menu_sub != "GENERAL":
            ruta = (
                f"{texto_principal} "
                f"<span style='color: {azul_nexion}; opacity: 0.8; margin: 0 15px;'>/</span> "
                f"<span style='color: {oro_brillante}; font-weight: 500; text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);'>"
                f"{st.session_state.menu_sub}</span>"
            )
        else:
            ruta = texto_principal

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
        es_atencion3g = (
            st.session_state.get("usuario_activo", "").upper() == "ATENCION3G"
        )
        key_actual = f"main_search_v{st.session_state.search_key_version}"

        query = st.text_input(
            "Buscar",
            placeholder="🔍 BUSCADOR DESACTIVADO" if es_atencion3g else "🔍 Buscar...",
            label_visibility="collapsed",
            key=key_actual,
            disabled=es_atencion3g,
        )

        if query:
            url_raw = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
            try:
                df_matriz_fresco = pd.read_csv(url_raw)
                df_matriz_fresco.columns = df_matriz_fresco.columns.str.strip()
            except Exception:
                df_matriz_fresco = cargar_datos_dashboard()

            res_ops = pd.DataFrame()
            if df_matriz_fresco is not None:
                cols_op = [
                    "NÚMERO DE GUÍA",
                    "NÚMERO DE PEDIDO",
                    "NO CLIENTE",
                    "NOMBRE DEL CLIENTE",
                    "DESTINO",
                ]
                cols_op_disp = [c for c in cols_op if c in df_matriz_fresco.columns]
                if cols_op_disp:
                    mask_ops = df_matriz_fresco[cols_op_disp].astype(str).apply(
                        lambda x: x.str.contains(query, case=False, na=False)
                    ).any(axis=1)
                    res_ops = df_matriz_fresco[mask_ops]

            res_inv = pd.DataFrame()
            try:
                df_inv_temp = pd.read_csv("inventario.csv")
                df_inv_temp.columns = df_inv_temp.columns.str.strip()
                cols_inv = [c for c in ["CODIGO", "DESCRIPCION"] if c in df_inv_temp.columns]
                if cols_inv:
                    mask_inv = df_inv_temp[cols_inv].astype(str).apply(
                        lambda x: x.str.contains(query, case=False, na=False)
                    ).any(axis=1)
                    res_inv = df_inv_temp[mask_inv]
            except Exception:
                pass

            if not res_ops.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "OPERACION"
                st.session_state.resultado_busqueda = res_ops
            elif not res_inv.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "INVENTARIO"
                st.session_state.resultado_busqueda = res_inv
            else:
                st.session_state.busqueda_activa = False
                st.toast("No se encontró ningún registro", icon="🔍")

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
        
            # MÓDULOS Y SUBMENÚS CONDICIONADOS POR PERMISOS DE GITHUB
            if permisos.get("DASHBOARD", False):
                if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                    st.session_state.menu_main = "DASHBOARD"
                    st.session_state.menu_sub = "GENERAL"
                    st.session_state.busqueda_activa = False
                    st.switch_page("pages/indicadores.py")
        
            if permisos.get("SEGUIMIENTO", False):
                with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                    opciones_seg_posibles = ["ALERTAS", "GANTT", "QUEJAS"]
                    opciones_seg = [s for s in opciones_seg_posibles if permisos.get(s, False)]
                    for s in opciones_seg:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_sub_{s}2"):
                            st.session_state.menu_main = "SEGUIMIENTO"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if permisos.get("ENTREGAS", False):
                with st.expander("ENTREGAS", expanded=(st.session_state.menu_main == "ENTREGAS")):
                    opciones_ent_posibles = ["AGC", "AMAZON", "BARCELO"]
                    opciones_ent = [s for s in opciones_ent_posibles if permisos.get(s, False)]
                    for s in opciones_ent:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_ent_{s}2"):
                            st.session_state.menu_main = "ENTREGAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "AGC":
                                st.switch_page("pages/entregas_agc.py")
                            else:
                                st.rerun()
        
            if permisos.get("REPORTES", False):
                with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                    opciones_rep_posibles = ["COSTOS CEDIS", "ANALISIS MENSUAL", "DETALLE COSTOS", "ENVIOS ESPECIALES", "ENVIO DE MUESTRAS"]
                    opciones_rep = [s for s in opciones_rep_posibles if permisos.get(s, False)]
                    for s in opciones_rep:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_rep_{s}2"):
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
                            st.session_state.menu_main = "FORMATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if permisos.get("CENTRO DE DATOS", False):
                with st.expander("CENTRO DE DATOS", expanded=(st.session_state.menu_main == "CENTRO DE DATOS")):
                    opciones_hub_posibles = ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "HERRAMIENTAS"]
                    opciones_hub = [s for s in opciones_hub_posibles if permisos.get(s, False)]
                    for s in opciones_hub:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_hub_{s}2"):
                            st.session_state.menu_main = "CENTRO DE DATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            if s == "ASIGNAR FLETERA":
                                st.switch_page("pages/asignacionfletera.py")
                            else:
                                st.rerun()
        
            if permisos.get("FINANZAS", False):
                with st.expander("FINANZAS", expanded=(st.session_state.menu_main == "FINANZAS")):
                    opciones_fin_posibles = ["WALLET", "CAJA CHICA", "GASTOS"]
                    opciones_fin = [s for s in opciones_fin_posibles if permisos.get(s, False)]
                    for s in opciones_fin:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_fin_{s}2"):
                            st.session_state.menu_main = "FINANZAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()

            if permisos.get("ENFOQUE", False):
                with st.expander("ENFOQUE", expanded=(st.session_state.get("menu_main") == "ENFOQUE")):
                    opciones_enf_posibles = ["MORENO", "VAZQUEZ", "MIGUEL"]
                    opciones_enf = [s for s in opciones_enf_posibles if permisos.get(s, False)]
                    for s in opciones_enf:
                        label = f"» {s}" if st.session_state.get("menu_sub") == s else s
                        if st.button(label, use_container_width=True, key=f"pop_enf_{s}2"):
                            st.session_state.menu_main = "ENFOQUE"
                            st.session_state.menu_sub = s
                            st.rerun()
        
            if permisos.get("ACCESS CONTROL", False) or usuario.upper() == "RIGOBERTO":
                if st.button("ACCESS CONTROL", use_container_width=True, key="pop_access_ctrl2"):
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

    # ── RENDERIZADO DE RESULTADOS DE BÚSQUEDA ──────────────────────────────
    if st.session_state.busqueda_activa and st.session_state.resultado_busqueda is not None:
        resultados = st.session_state.resultado_busqueda
        total = len(resultados)
        tipo = st.session_state.get("tipo_resultado", "OPERACION")
        accent_color = "#00FFAA"
        inv_color = "#36b9cc"
        azul_premium = "#00D4FF"

        col_espacio, col_cerrar = st.columns([0.85, 0.15])
        with col_cerrar:
            if st.button("✕ CERRAR", key="btn_cerrar_top", use_container_width=True):
                st.session_state.busqueda_activa = False
                st.session_state.resultado_busqueda = None
                st.session_state.search_key_version += 1
                st.rerun()

        if tipo == "INVENTARIO":
            st.markdown(f"<style>.card-inv {{ transition: all 0.3s ease; cursor: pointer; }} .card-inv:hover {{ transform: translateX(8px); border-color: {inv_color} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(54, 185, 204, 0.1); }}</style>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:15px;'><div style='background:{inv_color};width:5px;height:20px;border-radius:2px;box-shadow:0 0 10px {inv_color};'></div><span style='color:white;font-size:14px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;'>EXISTENCIAS EN INVENTARIO <span style='color:{inv_color};'>({total})</span></span></div>", unsafe_allow_html=True)
            for _, i in resultados.iterrows():
                st.markdown(f"<div class='card-inv' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {inv_color};border-radius:10px;padding:10px 20px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CÓDIGO / SKU</span><br><b style='font-size:16px;color:{inv_color};letter-spacing:1px;'>{i.get('CODIGO','')}</b></div><div style='flex:3;padding-left:20px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>DESCRIPCIÓN</span><br><span style='font-size:13px;color:white;font-weight:600;line-height:1.2;'>{i.get('DESCRIPCION','')}</span></div><div style='flex:1;text-align:right;'><span style='background:{inv_color}15;color:{inv_color};padding:3px 8px;border-radius:4px;font-size:9px;font-weight:800;border:1px solid {inv_color}30;text-transform:uppercase;'>DISPONIBLE</span></div></div>", unsafe_allow_html=True)
        else:
            if total == 1:
                envio = resultados.iloc[0]
                entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
                f_entrega_val = envio["FECHA DE ENTREGA REAL"] if entregado_real else "PENDIENTE"
                trigger_val = str(envio.get("TRIGGER", "")).strip()
                tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]

                if tiene_guia:
                    n_guia = envio["NÚMERO DE GUÍA"]
                elif trigger_val == "Enviada":
                    n_guia = "GENERANDO GUÍA..."
                else:
                    n_guia = "EN ESPERA DE SURTIDO"

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

                tarjeta_unica_html = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 20px 25px; border-radius: 8px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;"><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #38bdf8; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #38bdf8;"></div><div style="font-size: 9px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;">ENVÍO</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('FECHA DE ENVÍO','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #38bdf8; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #a855f7; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #a855f7;"></div><div style="font-size: 9px; font-weight: 800; color: #a855f7; letter-spacing: 1px;">GUÍA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{n_guia if tiene_guia else 'EN PROCESO'}</div></div><div style="flex-grow: 1; height: 2px; background: #a855f7; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #eab308; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #eab308;"></div><div style="font-size: 9px; font-weight: 800; color: #eab308; letter-spacing: 1px;">PROMESA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('PROMESA DE ENTREGA','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #00FFAA; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: {status_color}; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px {status_color};"></div><div style="font-size: 9px; font-weight: 800; color: {status_color}; letter-spacing: 1px;">ENTREGA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{f_entrega_val}</div></div></div><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;"><div style="flex: 1.2; min-width: 200px;"><div style="color: {accent_color}; font-size: 16px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">{envio.get('FLETERA','N/A')}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">TALÓN / FOLIO</div><div style="color: {accent_color}; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{n_guia}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">REF / PEDIDO: <span style="color: white; font-size: 13px; font-weight: 700;">{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div></div><div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / CLIENTE</div><div style="color: white; font-weight: 800; font-size: 13px; text-transform: uppercase; line-height: 1.3; margin-top: 2px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div><div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 2px;">ID: {envio.get('NO CLIENTE','')} | {envio.get('DOMICILIO','')}</div><div style="font-size: 11px; color: {accent_color}; margin-top: 4px; font-weight: 600;">📍 GDL → {envio.get('DESTINO','N/A')}</div></div><div style="flex: 1.2; min-width: 150px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN CARGA</div><div style="color: white; font-weight: 700; font-size: 11px; margin-top: 2px;">BULTOS: <span style="color: {accent_color};">{envio.get('CANTIDAD DE CAJAS','0')}</span></div><div style="color: {accent_color}; font-weight: 800; font-size: 13px; margin-top: 2px;">$ {envio.get('COSTO DE LA GUÍA','0.00')}</div></div><div style="text-align: right; min-width: 130px;"><span style="background-color: {status_color}15; color: {status_color}; padding: 5px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; border: 1px solid {status_color}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">ESTATUS: {status_text}</span></div></div></div>"""
                st.markdown(tarjeta_unica_html, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'><div style='background: {azul_premium}; width: 5px; height: 22px; border-radius: 3px; box-shadow: 0 0 10px {azul_premium};'></div><span style='color: white; font-size: 15px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;'>MULTIPLE MATCHES DETECTED <span style='color: {azul_premium};'>({total})</span></span></div>", unsafe_allow_html=True)
                st.markdown(f"<style>.card-nexion {{ transition: all 0.3s ease !important; cursor: pointer; }} .card-nexion:hover {{ transform: translateX(10px); border-color: {azul_premium} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(0, 212, 255, 0.2); }}</style>", unsafe_allow_html=True)

                for _, d in resultados.iterrows():
                    status_text = d["COMENTARIOS"] if pd.notna(d.get("COMENTARIOS")) else "OK"
                    st.markdown(f"<div class='card-nexion' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {azul_premium};border-radius:12px;padding:18px 25px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>PEDIDO / FACTURA</span><br><b style='font-size:18px;color:{azul_premium};letter-spacing:0.5px;'># {d.get('NÚMERO DE PEDIDO','')}</b><br><span style='font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;'>Envío: {d.get('FECHA DE ENVÍO','')}</span></div><div style='flex:2.5;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CLIENTE / DESTINO</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('NOMBRE DEL CLIENTE','')}</b><br><i style='font-size:11px;color:rgba(255,255,255,0.5);font-style:normal;font-weight:600;'>{d.get('DESTINO','')}</i></div><div style='flex:1.8;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>TRANSPORTE Y GUÍA</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('FLETERA', d.get('TRANSPORTE', 'LOGÍSTICA'))}</b><br><span style='font-size:12px;color:{azul_premium};font-weight:700;font-family:monospace;'>{d.get('NÚMERO DE GUÍA','')}</span></div><div style='flex:1.2;text-align:right;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>ESTATUS ENTREGA</span><br><b style='font-size:14px;color:{azul_premium};'>{d.get('FECHA DE ENTREGA REAL','')}</b><br><span style='font-size:10px;color:white;font-weight:800;text-transform:uppercase;opacity:0.8;'>{status_text}</span></div></div>", unsafe_allow_html=True)

        st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)


# ==========================================
# 5. INTERFAZ PRINCIPAL (ENTREGAS AGC)
# ==========================================
def main():
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    # --- 1. DEFINICIÓN DE FUNCIONES ---
    def cargar_datos():
        import time
        t = int(time.time())
        url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
        try:
            df = pd.read_csv(url, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            return None
    
    def render_listado_operativo_premium(df):
    # --- FORMATEO DE FECHAS ANTES DE CONVERTIR ---
        df_display = df.copy()
        for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
            if col in df_display.columns:
                df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%d-%m-%Y').fillna('')
    
        data = df_display.fillna('').to_dict('records')
        
        # Construcción segura de la variable local para evitar NameError
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{ background-color: transparent; color: #e2e8f0; font-family: 'Inter', sans-serif; margin: 0; }}
                .row-logistica {{
                    background-color: #263238;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 12px;
                    margin-bottom: 10px;
                    padding: 16px;
                    transition: all 0.3s ease;
                }}
                .row-logistica:hover {{
                    border-color: #00FFAA;
                    transform: translateX(5px);
                    background-color: #2d3b42;
                }}
                .label-mini {{
                    font-size: 8px;
                    text-transform: uppercase;
                    color: rgba(255,255,255,0.5);
                    font-weight: 800;
                    letter-spacing: 1px;
                }}
                .valor {{ font-size: 13px; font-weight: 700; color: #FFFFFF; }}
                .highlight {{ color: #00FFAA; font-family: monospace; }}
                
                ::-webkit-scrollbar {{ width: 8px; }}
                ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.2); }}
                ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
            </style>
        </head>
        <body>
            <div style="padding: 10px;">
                {"".join([f'''
                <div class="row-logistica">
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 items-center">
                        <div>
                            <div class="label-mini">Pedido / Factura</div>
                            <div class="valor highlight text-lg">{str(item.get('NÚMERO DE PEDIDO', ''))}</div>
                            <div class="text-[10px] text-blue-300 opacity-80">Envío: {str(item.get('FECHA DE ENVÍO', ''))}</div>
                        </div>
                        
                        <div>
                            <div class="label-mini">Cliente / Destino</div>
                            <div class="valor truncate text-xs uppercase">{str(item.get('NOMBRE DEL CLIENTE', ''))[:40]}</div>
                            <div class="text-[10px] text-white/50 italic">{str(item.get('DESTINO', ''))}</div>
                        </div>
    
                        <div class="border-x border-white/5 px-4">
                            <div class="label-mini">Transporte y Guía</div>
                            <div class="valor text-[11px]">{str(item.get('FLETERA', ''))}</div>
                            <div class="text-[10px] {"text-emerald-400" if item.get('NÚMERO DE GUÍA') else "text-orange-400"}">
                                {str(item.get('NÚMERO DE GUÍA', 'PENDIENTE'))}
                            </div>
                        </div>
    
                        <div class="text-right">
                            <div class="label-mini">Estatus Entrega</div>
                            <div class="valor text-sm {"text-emerald-400" if item.get('FECHA DE ENTREGA REAL') else "text-orange-400"}">
                                {str(item.get('FECHA DE ENTREGA REAL', 'EN TRÁNSITO'))}
                            </div>
                            <div class="text-[9px] text-white/40 uppercase">Promesa: {str(item.get('PROMESA DE ENTREGA', ''))}</div>
                        </div>
                    </div>
                </div>
                ''' for item in data])}
            </div>
        </body>
        </html>
        """
        return components.html(html_content, height=600, scrolling=True)
    
    # --- EJECUCIÓN DEL MÓDULO ---
    # --- EJECUCIÓN DEL MÓDULO ---
    df_raw = cargar_datos()

    if df_raw is not None:
        # 1. Convertimos la columna a formato fecha (ajusta el nombre si es necesario)
        # Usamos errors='coerce' por si hay celdas vacías o con texto extraño
        df_raw["FECHA DE ENVÍO"] = pd.to_datetime(df_raw["FECHA DE ENVÍO"], dayfirst=True, errors='coerce')
    
        # 2. Ordenamos: el más reciente (fecha más grande) arriba
        df_raw = df_raw.sort_values(by="FECHA DE ENVÍO", ascending=False)
            
    
    if df_raw is not None:               
        with st.expander("Ver / Ocultar, Listado de pedidos completo", expanded=False):
            # --- BÚSQUEDA MAESTRA ---
            busqueda_manual = st.text_input("", key="bus_maestra_log", placeholder="🔍 Buscar por pedido, guía o cliente...").strip()
            
            df_final = df_raw.copy() 
            
            # Solo ejecutamos la lógica del Timeline si el usuario escribió algo
            if busqueda_manual:
                mask = (
                    df_raw["NÚMERO DE PEDIDO"].astype(str).str.contains(busqueda_manual, case=False, na=False) |
                    df_raw["NÚMERO DE GUÍA"].astype(str).str.contains(busqueda_manual, case=False, na=False) |
                    df_raw["NOMBRE DEL CLIENTE"].astype(str).str.contains(busqueda_manual, case=False, na=False)
                )
                df_final = df_raw[mask].copy()
            
                st.markdown(f"<p style='color:#00FFAA; font-size:11px; font-style:italic;'>Mostrando {len(df_final)} registros</p>", unsafe_allow_html=True)
                
                if not df_final.empty:
                    # --- PREPARACIÓN DE DATOS ---
                    envio = df_final.iloc[0]
                    
                    # Función auxiliar interna para no repetir código y evitar errores
                    def formatear_fecha_safe(valor):
                        if pd.isna(valor) or valor == "":
                            return "N/A"
                        try:
                            return pd.to_datetime(valor, errors='coerce').strftime('%d-%m-%Y')
                        except:
                            return str(valor)
                
                    f_envio = formatear_fecha_safe(envio.get("FECHA DE ENVÍO"))
                    f_promesa = formatear_fecha_safe(envio.get("PROMESA DE ENTREGA"))
                    
                    entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
                    f_entrega_val = formatear_fecha_safe(envio.get("FECHA DE ENTREGA REAL")) if entregado_real else "PENDIENTE"
                    
                    trigger_val = str(envio.get("TRIGGER", "")).strip()
                    tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]
                    
                    if tiene_guia:
                        n_guia = envio["NÚMERO DE GUÍA"]
                    elif trigger_val == "Enviada":
                        n_guia = "GENERANDO GUÍA..."
                    else:
                        n_guia = "EN ESPERA DE SURTIDO"
        
                    # --- LÓGICA DE FECHAS (ANTICRASH) ---
                    f_promesa_dt = pd.to_datetime(envio.get("PROMESA DE ENTREGA"), dayfirst=True, errors='coerce')
                    if pd.notnull(f_promesa_dt): f_promesa_dt = f_promesa_dt.normalize()
                    hoy = pd.Timestamp(datetime.now()).normalize()
                    
                    v_border = "rgba(255,255,255,0.1)"
                    v_sub = "rgba(255,255,255,0.6)"
        
                    # --- LÓGICA DE ESTATUS Y COLORES ---
                    if not tiene_guia:
                        status_text, status_color = ("GENERANDO GUÍA", "#38bdf8") if trigger_val == "Enviada" else ("SURTIENDO", "#FFA500")
                        color_envio, color_guia, color_promesa, color_entrega = "#38bdf8", v_border, v_border, v_border
                        linea_1_2, linea_2_3, linea_3_4 = v_border, v_border, v_border
                    elif not entregado_real:
                        status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if pd.isna(f_promesa_dt) or hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
                        color_envio, color_guia, color_promesa, color_entrega = "#38bdf8", "#38bdf8", "#a855f7", v_border
                        linea_1_2, linea_2_3, linea_3_4 = "#38bdf8", "#a855f7", v_border
                    else:
                        f_entrega_dt = pd.to_datetime(envio.get("FECHA DE ENTREGA REAL"), dayfirst=True, errors='coerce')
                        if pd.notnull(f_entrega_dt): f_entrega_dt = f_entrega_dt.normalize()
                        status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.isna(f_promesa_dt) or f_entrega_dt <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")
                        color_envio, color_guia, color_promesa, color_entrega = "#38bdf8", "#38bdf8", "#a855f7", status_color
                        linea_1_2, linea_2_3, linea_3_4 = "#38bdf8", "#a855f7", status_color
        
                    # --- RENDERIZADO COMPACTO (UNA SOLA LÍNEA) ---
                    t_html = f'<div style="background:#263238; padding:20px; border-radius:12px; border:1px solid {v_border}; margin-bottom:25px; font-family:sans-serif;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:25px;"><h2 style="margin:0; color:white; font-size:14px; letter-spacing:1px; text-transform:uppercase; font-weight:800;">{envio["NOMBRE DEL CLIENTE"]}</h2><span style="background:{status_color}15; color:{status_color}; padding:4px 12px; border-radius:4px; font-weight:700; font-size:10px; border:1px solid {status_color}; letter-spacing:1px;">{status_text}</span></div><div style="display:flex; align-items:center; justify-content:space-between; width:100%; position:relative; margin-bottom:10px;"><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_envio}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">ENVÍO</div><div style="font-size:10px; color:white; font-weight:600;">{f_envio}</div></div><div style="flex-grow:1; height:2px; background:{linea_1_2}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_guia}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">GUÍA</div><div style="font-size:10px; color:white; font-weight:600;">{"LISTA" if tiene_guia else "PENDIENTE"}</div></div><div style="flex-grow:1; height:2px; background:{linea_2_3}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_promesa}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">PROMESA</div><div style="font-size:10px; color:white; font-weight:600;">{f_promesa}</div></div><div style="flex-grow:1; height:2px; background:{linea_3_4}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:16px; height:16px; background:{color_entrega}; border-radius:50%; z-index:2; box-shadow:0 0 12px {color_entrega if entregado_real else "#00000000"}"></div><div style="font-size:9px; color:{v_sub}; margin-top:8px; font-weight:800; letter-spacing:1px;">ENTREGA</div><div style="font-size:10px; color:white; font-weight:600;">{f_entrega_val}</div></div></div><div style="display:flex; justify-content:space-between; border-top:1px solid rgba(255,255,255,0.05); padding-top:15px; margin-top:15px;"><div style="text-align:left;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">FLETERA</div><div style="color:white; font-size:12px; font-weight:700;">{envio["FLETERA"]}</div></div><div style="text-align:center;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">GUÍA</div><div style="color:white; font-size:12px; font-weight:700;">{n_guia}</div></div><div style="text-align:right;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">DESTINO</div><div style="color:white; font-size:12px; font-weight:700;">{envio["DESTINO"]}</div></div></div></div>'
                    st.markdown(t_html, unsafe_allow_html=True)
                else:
                    st.warning("No se encontraron resultados para tu búsqueda.")
            
                
            # --- RENDER DEL LISTADO CHINGÓN ---
            st.markdown(f"<p style='color:#00FFAA; font-size:11px; italic;'>Mostrando {len(df_final)} registros</p>", unsafe_allow_html=True)
            render_listado_operativo_premium(df_final)
        
           
    
    #INICIO DONITAS-------------------
    def render_kpi(valor, total, titulo, color):
        porc = (valor / total * 100) if total > 0 else 0
        # Circunferencia basada en radio 38
        circunferencia = 238.76
        offset = circunferencia - (porc / 100 * circunferencia)
        
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">{titulo}</div>
                <div style="position: relative; width: 160px; height: 160px; display: flex; align-items: center; justify-content: center;">
                    <svg class="stat-circle" viewBox="0 0 100 100">
                        <circle class="stat-bg" cx="50" cy="50" r="38"></circle>
                        <circle class="stat-progress" cx="50" cy="50" r="38" 
                                style="stroke: {color}; 
                                       stroke-dasharray: {circunferencia}; 
                                       stroke-dashoffset: {offset};">
                        </circle>
                    </svg>
                    <div class="stat-value">{valor}</div>
                </div>
                <div class="stat-percent" style="color: {color};">{porc:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    # --- 2. CONFIGURACIÓN DE ESTILOS (CSS) ---
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {vars_css['bg']} !important; }}
        
        /* ESPACIO EXTRA ENTRE EL MENÚ Y LAS DONAS */
        .spacer-menu {{
            margin-top: 50px; /* Ajusta este valor si quieres más o menos espacio */
        }}

        /* ESTILOS DE LOS TABS (SUBMENÚ) */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 15px;
            border-bottom: 1px solid #1e293b;
        }}

        .stTabs [data-baseweb="tab"] {{
            background-color: #1a2432;
            border-radius: 4px 4px 0px 0px;
            color: #94a3b8;
            padding: 10px 20px;
            transition: all 0.3s ease;
        }}

        /* EFECTO HOVER */
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: #26354a;
            color: #ffffff;
        }}

        /* ESTADO ACTIVO (DÓNDE ESTÁS) */
        .stTabs [aria-selected="true"] {{
            background-color: #003399 !important; /* El azul de tu imagen */
            color: white !important;
            border-bottom: 2px solid #00FFAA !important;
        }}

        /* ESTILOS DE TUS DONAS (KPIs) */
        .metric-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 100%;
        }}
        .metric-title {{ color: #94a3b8; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; font-weight: 600; }}
        .stat-circle {{ transform: rotate(-90deg); width: 160px; height: 160px; overflow: visible; }}
        .stat-circle circle {{ fill: none; stroke-width: 15; }}
        .stat-bg {{ stroke: #2F3E45; }}
        .stat-progress {{ transition: stroke-dashoffset 0.8s ease-in-out; stroke-linecap: butt; }}
        .stat-value {{ position: absolute; color: white; font-size: 22px; font-weight: 800; top: 50%; left: 50%; transform: translate(-50%, -50%); }}
        .stat-percent {{ font-size: 16px; margin-top: 5px; font-weight: 700; }}
    </style>
    """, unsafe_allow_html=True)

    # --- 3. CARGA Y PROCESAMIENTO ---
    df_raw = cargar_datos()
    
    if df_raw is not None:
        import pytz
        from datetime import datetime
        tz_gdl = pytz.timezone('America/Mexico_City')
        hoy_gdl = datetime.now(tz_gdl).date()
        hoy_dt = pd.Timestamp(hoy_gdl)
        meses = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO","JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]
        
        # BUSCAR GUIA INTELIGENTE--- CSS GLOBAL PARA EL EFECTO HOVER ---
        st.markdown("""
            <style>
            /* Efecto Hover para las tarjetas Nexion */
            .nexion-hover-card {
                transition: transform 0.3s ease, background-color 0.3s ease, box-shadow 0.3s ease;
                cursor: pointer;
            }
            .nexion-hover-card:hover {
                transform: translateY(-5px); /* Se levanta un poquito */
                background-color: #252e35 !important; /* Se aclara el fondo */
                box-shadow: 0px 10px 20px rgba(0, 255, 204, 0.1); /* Brillo neón sutil */
            }
            </style>
            """, unsafe_allow_html=True)
        
        # --- 2. FUNCIÓN PARA CARGAR DESDE REPOSITORIO ---
        def cargar_desde_repo(archivo):
            if os.path.exists(archivo):
                try:
                    df_preview = pd.read_excel(archivo, nrows=50, header=None)
                    claves = ['CARTA_PORTE', 'FACTURA_INTERNA', 'TALON', 'OBSERVACION 1', 'OBSERVACIONES', 'GUIA', 'PAQUETES_AMPARA', 'SUB TOTAL _ GUIA']
                    fila_head = -1
                    for i, row in df_preview.iterrows():
                        row_str = row.astype(str).str.upper().tolist()
                        if any(clave in s for s in row_str for clave in claves):
                            fila_head = i
                            break
                    df = pd.read_excel(archivo, header=fila_head if fila_head != -1 else 0)
                    df.columns = df.columns.astype(str).str.strip()
                    return df
                except:
                    return None
            return None
        
        # --- 3. CARGA DE DATOS ---
        df_t1 = cargar_desde_repo("T1.xlsx")
        df_t2 = cargar_desde_repo("T2.xlsx")
        df_t3 = cargar_desde_repo("T3.xlsx")
        
        
        # --- ZONA DE CONTROL (FILTROS + BUSCADOR) ---
        col_f1, col_busqueda_zona = st.columns([1, 2])  
        
        with col_f1:
            mes_sel = st.selectbox("PERÍODO", meses, index=hoy_gdl.month - 1)
        
        with col_busqueda_zona:
            # Inicializamos el estado del input si no existe
            if "busqueda_input" not in st.session_state:
                st.session_state.busqueda_input = ""
                
            # Usamos st.text_input conectado al session_state mediante key
            query = st.text_input(
                "BUSQUEDA AUXILIAR DE GUIAS", 
                placeholder="Ingresa el numero de factura...",
                key="busqueda_input"
            )

        # Si el usuario escribió algo, evaluamos la búsqueda y mostramos el render + botón de cierre
        if query:
            encontrado = False
            html_resultado = ""
            
            # --- PASO 1: BUSCAR EN LAS FLETERAS (T1, T2, T3) ---
            for df_source, nombre_f in [(df_t1, "TRES GUERRAS"), (df_t2, "TINY PACK"), (df_t3, "ONE")]:
                if df_source is not None and not encontrado:
                    cols_busqueda = ['OBSERVACION 1', 'FACTURA_INTERNA', 'Observaciones', 'TALON', 'CARTA_PORTE', 'Guia']
                    cols_presentes = [c for c in cols_busqueda if c in df_source.columns]
                    
                    if cols_presentes:
                        mask = df_source[cols_presentes].astype(str).apply(
                            lambda x: x.str.contains(query, case=False, na=False)
                        ).any(axis=1)
                        res = df_source[mask]
                    else:
                        res = pd.DataFrame()
                    
                    if not res.empty:
                        encontrado = True
                        f = res.iloc[0]
                        
                        # --- LÓGICA DE ESTATUS CORREGIDA ---
                        col_fechas = ['F.ENTREGA', 'FECHA_ENTREGA', 'FECHA DE ENTREGA']
                        columnas_presentes = [col for col in col_fechas if col in df_source.columns]
                        
                        fecha_valida = False
                        if columnas_presentes:
                            for col in columnas_presentes:
                                valor = f[col]
                                fecha_dt = pd.to_datetime(valor, errors='coerce')
                                if pd.notnull(fecha_dt):
                                    fecha_valida = True
                                    break
                            estatus = "ESTATUS: ENTREGADO" if fecha_valida else "ESTATUS: EN TRANSITO"
                        else:
                            estatus = "ESTATUS: ACTUALIZANDO DATOS"
                        
                        # --- MAPEO DATOS ---
                        guia = f.get("TALON") or f.get("CARTA_PORTE") or f.get("Guia") or "S/N"
                        factura = f.get("OBSERVACION 1") or f.get("FACTURA_INTERNA") or f.get("Observaciones") or "S/N"
                        cliente = f.get("CLIENTE_DESTINO") or f.get("DESTINATARIO") or f.get("Destinatario") or "CLIENTE NO REGISTRADO"
                        origen = f.get("ORIGEN") or "PLANTA GDL"
                        destino = f.get("DESTINO") or f.get("CIUDAD") or f.get("Oficina_Destino") or "N/A"
                        bultos = f.get("BULTOS") or f.get("PIEZAS") or f.get("Paquetes_Ampara") or "0"
                        importe = f.get("Sub total _ Guia") or f.get("TOTAL") or f.get("SUBTOTAL") or "0.00"
                        
                        color_estatus = "#004d40" if "ENTREGADO" in estatus else ("#ff9800" if "TRANSITO" in estatus else "#1e262c")
                        html_resultado = f'<div class="nexion-hover-card" style="background-color:#1e262c; border-radius:10px; padding:20px; border-left:5px solid {color_estatus}; margin-top:5px; margin-bottom:20px; color:white; font-family:sans-serif;"><div style="display:flex; justify-content:space-between; align-items:flex-start;"><div style="min-width:150px; flex:1;"><div style="color:#00ffcc; font-size:0.7rem; font-weight:bold; letter-spacing:1.5px; margin-bottom:5px;">{nombre_f}</div><div style="color:#8899a6; font-size:0.75rem; text-transform:uppercase;">TALÓN / FOLIO</div><div style="color:#00ffcc; font-size:1.6rem; font-weight:bold; line-height:1.2;">{guia}</div><div style="color:#8899a6; font-size:0.75rem; text-transform:uppercase; margin-top:5px;">REF: <span style="color:white; font-size:1rem;">{factura}</span></div></div><div style="min-width:200px; flex:1.5;"><div style="color:#8899a6; font-size:0.75rem; text-transform:uppercase;">DESTINATARIO / RUTA</div><div style="color:white; font-weight:bold; font-size:1.2rem;">{cliente}</div><div style="font-size:0.9rem; color:#8899a6; margin-top:5px;"><span style="color:#00ffcc;">📍</span> GDL ➔ {destino}</div></div><div style="min-width:150px; flex:1; border-left:2px solid #3d464d; padding-left:15px;"><div style="color:#8899a6; font-size:0.75rem; text-transform:uppercase;">RESUMEN FINANCIERO</div><div style="color:white; font-weight:bold; font-size:0.95rem;">BULTOS: <span style="color:#00ffcc;">{bultos}</span></div><div style="color:#00ffcc; font-weight:bold; font-size:1.2rem; margin-top:10px;">$ {importe}</div></div><div><span style="background-color:{color_estatus}; color:white; padding:4px 12px; border-radius:15px; font-size:0.85rem; font-weight:bold; text-transform:uppercase; white-space:nowrap;">{estatus}</span></div></div></div>'
            
            # --- PASO 2: SI NO SE HALLÓ EN FLETERAS, BUSCAR EN EL LISTADO MAESTRO (df_raw) ---
            if not encontrado and df_raw is not None:
                mask_i = (
                    df_raw["NÚMERO DE PEDIDO"].astype(str).str.contains(query, case=False, na=False) |
                    df_raw["NÚMERO DE GUÍA"].astype(str).str.contains(query, case=False, na=False) |
                    df_raw["NOMBRE DEL CLIENTE"].astype(str).str.contains(query, case=False, na=False)
                )
                res_i = df_raw[mask_i].copy()
                
                if not res_i.empty:
                    encontrado = True
                    envio = res_i.iloc[0] 
                    f_envio = envio.get("FECHA DE ENVÍO", "N/A")
                    f_promesa = envio.get("PROMESA DE ENTREGA", "N/A")
                    entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
                    f_entrega_val = envio["FECHA DE ENTREGA REAL"] if entregado_real else "PENDIENTE"
                    trigger_val = str(envio.get("TRIGGER", "")).strip()
                    tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]
                    n_guia = envio["NÚMERO DE GUÍA"] if tiene_guia else ("GENERANDO GUÍA..." if trigger_val == "Enviada" else "EN ESPERA DE SURTIDO")
        
                    f_promesa_dt = pd.to_datetime(envio.get("PROMESA DE ENTREGA"), dayfirst=True, errors='coerce')
                    if pd.notnull(f_promesa_dt): f_promesa_dt = f_promesa_dt.normalize()
                    hoy = pd.Timestamp(datetime.now()).normalize()
                    v_border, v_sub = "rgba(255,255,255,0.1)", "rgba(255,255,255,0.6)"
        
                    if not tiene_guia:
                        status_text, status_color = ("GENERANDO GUÍA", "#38bdf8") if trigger_val == "Enviada" else ("SURTIENDO", "#FFA500")
                        color_envio, color_guia, color_promesa, color_entrega = "#38bdf8", v_border, v_border, v_border
                        linea_1_2, linea_2_3, linea_3_4 = v_border, v_border, v_border
                    elif not entregado_real:
                        status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if pd.isna(f_promesa_dt) or hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
                        color_envio, color_guia, color_promesa, color_entrega = "#38bdf8", "#38bdf8", "#a855f7", v_border
                        linea_1_2, linea_2_3, linea_3_4 = "#38bdf8", "#a855f7", v_border
                    else:
                        f_entrega_dt = pd.to_datetime(envio.get("FECHA DE ENTREGA REAL"), dayfirst=True, errors='coerce')
                        if pd.notnull(f_entrega_dt): f_entrega_dt = f_entrega_dt.normalize()
                        status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.isna(f_promesa_dt) or f_entrega_dt <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")
                        color_envio, color_guia, color_promesa, color_entrega = "#38bdf8", "#38bdf8", "#a855f7", status_color
                        linea_1_2, linea_2_3, linea_3_4 = "#38bdf8", "#a855f7", status_color
        
                    html_resultado = f'<div class="nexion-hover-card" style="background:#263238; padding:20px; border-radius:12px; border:1px solid {v_border}; margin-bottom:25px; font-family:sans-serif;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:25px;"><h2 style="margin:0; color:white; font-size:14px; letter-spacing:1px; text-transform:uppercase; font-weight:800;">{envio["NOMBRE DEL CLIENTE"]}</h2><span style="background:{status_color}15; color:{status_color}; padding:4px 12px; border-radius:4px; font-weight:700; font-size:10px; border:1px solid {status_color}; letter-spacing:1px;">{status_text}</span></div><div style="display:flex; align-items:center; justify-content:space-between; width:100%; position:relative; margin-bottom:10px;"><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_envio}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">ENVÍO</div><div style="font-size:10px; color:white; font-weight:600;">{f_envio}</div></div><div style="flex-grow:1; height:2px; background:{linea_1_2}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_guia}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">GUÍA</div><div style="font-size:10px; color:white; font-weight:600;">{"LISTA" if tiene_guia else "PENDIENTE"}</div></div><div style="flex-grow:1; height:2px; background:{linea_2_3}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:12px; height:12px; background:{color_promesa}; border-radius:50%; z-index:2;"></div><div style="font-size:9px; color:{v_sub}; margin-top:10px; font-weight:800; letter-spacing:1px;">PROMESA</div><div style="font-size:10px; color:white; font-weight:600;">{f_promesa}</div></div><div style="flex-grow:1; height:2px; background:{linea_3_4}; margin-top:-38px;"></div><div style="display:flex; flex-direction:column; align-items:center; flex:1;"><div style="width:16px; height:16px; background:{color_entrega}; border-radius:50%; z-index:2; box-shadow:0 0 12px {color_entrega if entregado_real else "#00000000"}"></div><div style="font-size:9px; color:{v_sub}; margin-top:8px; font-weight:800; letter-spacing:1px;">ENTREGA</div><div style="font-size:10px; color:white; font-weight:600;">{f_entrega_val}</div></div></div><div style="display:flex; justify-content:space-between; border-top:1px solid rgba(255,255,255,0.05); padding-top:15px; margin-top:15px;"><div style="text-align:left;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">FLETERA</div><div style="color:white; font-size:12px; font-weight:700;">{envio["FLETERA"]}</div></div><div style="text-align:center;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">GUÍA</div><div style="color:white; font-size:12px; font-weight:700;">{n_guia}</div></div><div style="text-align:right;"><div style="color:{v_sub}; font-size:8px; font-weight:800; letter-spacing:1px;">DESTINO</div><div style="color:white; font-size:12px; font-weight:700;">{envio["DESTINO"]}</div></div></div></div>'
            
            # --- RENDERIZADO DEL BOTÓN Y RESULTADOS ---
            if encontrado:
                _, col_btn_cerrar = st.columns([5, 1])
                with col_btn_cerrar:
                    st.markdown('<div style="margin-top: -5px;"></div>', unsafe_allow_html=True)
                    
                    # Función interna para limpiar el estado de forma segura antes del rerun
                    def limpiar_busqueda():
                        st.session_state.busqueda_input = ""

                    # Usamos on_click para limpiar el input limpiamente sin romper las reglas de Streamlit
                    if st.button("✕ CERRAR", key="btn_cerrar_render", use_container_width=True, on_click=limpiar_busqueda):
                        pass
                
                st.markdown(html_resultado, unsafe_allow_html=True)
            
            else:
                st.markdown(f"""
                    <div class="nexion-hover-card" style="
                        background-color: #1e262c; 
                        border-radius: 8px; 
                        padding: 20px; 
                        border-left: 5px solid #ff4b4b; 
                        margin-top: 15px; 
                        margin-bottom: 35px;
                    ">
                        <div style="color: #8899a6; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 2px;">Estado de Búsqueda</div>
                        <div style="color: #ff4b4b; font-weight: bold; font-size: 1.3rem; line-height: 1.1; letter-spacing: 1px;">SIN COINCIDENCIAS</div>
                        <div style="margin-top: 15px; border-top: 1px solid #3d464d; padding-top: 12px;">
                            <div style="color: #8899a6; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 3px;">Referencia consultada</div>
                            <div style="color: white; font-weight: bold; font-size: 1.1rem;">{query}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        #AQUI TERMINA LA BUSQUEDA INTELIGENTE DE GUIAS
        
        df = df_raw.copy()
        for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    
        df_mes = df[df["FECHA DE ENVÍO"].dt.month == (meses.index(mes_sel) + 1)].copy()
    
        total_p = len(df_mes)
        entregados = len(df_mes[df_mes["FECHA DE ENTREGA REAL"].notna()])
        df_trans = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna()]
        en_tiempo = len(df_trans[df_trans["PROMESA DE ENTREGA"] >= hoy_dt])
        retrasados = len(df_trans[df_trans["PROMESA DE ENTREGA"] < hoy_dt])
        total_t = len(df_trans)  

        # --- 4. SUBMENÚ Y RENDERIZADO ---
        # Definimos las pestañas base que todos ven
        nombres_tabs = ["KPI´S", "TIEMPOS DE TRÁNSITO", "EFICIENCIA DESPACHOS", "DIST. CARGA", "ENTREGAS AGC", "CONSIGNAS", "AMAZON","DESPACHOS"]
        
        # Si eres tú, Rigoberto, añadimos la pestaña secreta al final
        es_admin = st.session_state.get("usuario_activo") == "Rigoberto"
        if es_admin:
            nombres_tabs.append("🔒 ADMIN CONTROL")

        if st.session_state.get("ir_a_entregas_agc", False):
            st.session_state.ir_a_entregas_agc = False

        # Creamos las pestañas dinámicamente
        tabs = st.tabs(nombres_tabs)
        
        # Asignamos las variables de siempre
        tab_kpis = tabs[0]
        tab_tiempos = tabs[1]
        tab_despachos = tabs[2]
        tab_participacion = tabs[3]
        tab_entregas_agc = tabs[4]
        tab_consignas = tabs[5]
        tab_amazon = tabs[6]
        tab_pedidos = tabs[7]
        
        
        # Si eres admin, creamos la variable para la séptima pestaña
        if es_admin:
            tab_admin = tabs[8]

        # PESTAÑA 1: KPI'S (Tus donitas)
        with tab_kpis:
            st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: render_kpi(total_p, total_p, "Pedidos", "#f6c23e")      # El Amarillo que te encantó
            with c2: render_kpi(entregados, total_p, "Entregados", "#1cc88a") # Verde Esmeralda (Éxito)
            with c3: render_kpi(total_t, total_p, "Tránsito", "#4e73df")    # Azul Real (Logística)
            with c4: render_kpi(en_tiempo, total_p, "En Tiempo", "#36b9cc")  # Turquesa (Precisión)
            with c5: render_kpi(retrasados, total_p, "Retraso", "#fb7185")   # Rojo Coral (Alerta)
                            
            # Espacio estético al final para que no se vea cortado el contenedor
            st.markdown("<br>", unsafe_allow_html=True)
    
            #--- SEPARADOR Y GRÁFICOS DE CARGA ACTIVA POR FLETERA ------
            st.markdown(f"""
                <hr style="border: 0; height: 1px; background: {vars_css['border']}; margin: 40px 0; opacity: 0.3;">
                <div style="
                    color: {vars_css['sub']}; 
                    font-size: 14px; 
                    font-weight: 500; 
                    letter-spacing: 2px; 
                    margin-bottom: 20px; 
                    text-transform: uppercase;
                ">
                    Distribución de Carga actual
                </div>
            """, unsafe_allow_html=True)
            # Definimos los colores del estilo actual
            color_transito = "#36b9cc" # Azul claro
            color_retraso = "#fb7185"  # Rojo
            
            # Creamos las dos columnas directas en el contenedor
            col_graf1, col_graf2 = st.columns(2)
            
            # --- COLUMNA 1: EN TRÁNSITO ---
            with col_graf1:
                df_t = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna() & (df_mes["PROMESA DE ENTREGA"] >= hoy_dt)].copy()
                df_t_count = df_t.groupby("FLETERA").size().reset_index(name="CANTIDAD")
                total_t_graf = df_t_count["CANTIDAD"].sum()
            
                st.markdown(f"""
                    <div style='background: linear-gradient(90deg, {color_transito}15 0%, transparent 100%); padding: 15px; border-radius: 4px; border-left: 4px solid {color_transito};'>
                        <p style='margin:0; color:{color_transito}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;'>🔵 En tránsito en tiempo</p>
                        <h2 style='margin:0; color:white; font-size:28px;'>{total_t_graf} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                    </div>
                """, unsafe_allow_html=True)
            
                if not df_t_count.empty:
                    h_t = len(df_t_count) * 35 + 50
                    chart_t = alt.Chart(df_t_count).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=18, color=color_transito).encode(
                        x=alt.X("CANTIDAD:Q", title=None, axis=None),
                        y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='#94a3b8', labelFontSize=11))
                    )
                    text_t = chart_t.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700).encode(text="CANTIDAD:Q")
                    st.altair_chart((chart_t + text_t).properties(height=h_t).configure_view(strokeOpacity=0), use_container_width=True)
                else:
                    st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin carga en tránsito</div>", unsafe_allow_html=True)
            
            # --- COLUMNA 2: RETRASADOS ---
            with col_graf2:
                df_r = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna() & (df_mes["PROMESA DE ENTREGA"] < hoy_dt)].copy()
                df_r_count = df_r.groupby("FLETERA").size().reset_index(name="CANTIDAD")
                total_r_graf = df_r_count["CANTIDAD"].sum()
            
                st.markdown(f"""
                    <div style='background: linear-gradient(90deg, {color_retraso}15 0%, transparent 100%); padding: 15px; border-radius: 4px; border-left: 4px solid {color_retraso};'>
                        <p style='margin:0; color:{color_retraso}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;'>🔴 En tránsito con Retraso</p>
                        <h2 style='margin:0; color:white; font-size:28px;'>{total_r_graf} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                    </div>
                """, unsafe_allow_html=True)
            
                if not df_r_count.empty:
                    h_r = len(df_r_count) * 35 + 50
                    chart_r = alt.Chart(df_r_count).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=18, color=color_retraso).encode(
                        x=alt.X("CANTIDAD:Q", title=None, axis=None),
                        y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='#94a3b8', labelFontSize=11))
                    )
                    text_r = chart_r.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700).encode(text="CANTIDAD:Q")
                    st.altair_chart((chart_r + text_r).properties(height=h_r).configure_view(strokeOpacity=0), use_container_width=True)
                else:
                    st.markdown("<div style='padding:20px; color:#00FFAA; font-size:12px; font-weight:bold;'>✓ Todo entregado a tiempo</div>", unsafe_allow_html=True)
    
        # PESTAÑA 2: RASTREO (Donde pondremos el buscador tipo DHL)
        with tab_tiempos: 
            st.write("") 
            # =========================================================
            # 1. PROCESAMIENTO DE DATOS
            # =========================================================
            df['FECHA DE ENVÍO'] = pd.to_datetime(df['FECHA DE ENVÍO'], errors='coerce')
            df['FECHA DE ENTREGA REAL'] = pd.to_datetime(df['FECHA DE ENTREGA REAL'], errors='coerce')
            df['DIAS_REALES'] = (df['FECHA DE ENTREGA REAL'] - df['FECHA DE ENVÍO']).dt.days
            
            # =========================================================
            # 2. SECCIÓN DEL CALCULADOR INTELIGENTE
            # =========================================================                
            usuario_actual = st.session_state.get('usuario_activo', 'Cielo')
            
            c1, c2, c3 = st.columns([1, 1, 0.8])
            
            with c1:
                st.text_input("ORIGEN", value="GUADALAJARA (GDL)", disabled=True, key="orig_fix")
            
            with c2:
                busqueda_manual = st.text_input(
                    "BUSCAR POR DESTINO, CP O DOMICILIO", 
                    placeholder="Ej: 63734, Litibu, Cancún...",
                    key="busqueda_manual_v6"
                )
            
            with c3:
                num_cajas = st.number_input("CANTIDAD DE CAJAS", min_value=1, value=1, step=1)
            
            # --- LÓGICA DE VISUALIZACIÓN POR DEFECTO ---
            if not busqueda_manual:
                df_validos = df[df['DIAS_REALES'].notna()]
                rutas_dos_dias = df_validos[df_validos['DIAS_REALES'] == 2]
                if not rutas_dos_dias.empty:
                    busqueda_activa = rutas_dos_dias['DESTINO'].iloc[0]
                    texto_mostrar = f"{busqueda_activa}"
                elif not df_validos.empty:
                    busqueda_activa = df_validos.groupby('DESTINO')['DIAS_REALES'].mean().idxmin()
                    texto_mostrar = f"{busqueda_activa} (Ruta sugerida)"
                else:
                    busqueda_activa = ""
                    texto_mostrar = "CONSULTA DE RUTA"
            else:
                busqueda_activa = busqueda_manual
                texto_mostrar = busqueda_manual.upper()
            
            # --- FILTRADO ORIGINAL (SIN ROMPER NADA) ---                   
            # Validamos que busqueda_activa no sea nula y la forzamos a ser texto seguro
            busqueda_aux = str(busqueda_activa).lower() if pd.notna(busqueda_activa) else ""
            mask = (
                df['DESTINO'].astype(str).str.lower().str.contains(busqueda_aux, na=False) |
                df['DOMICILIO'].astype(str).str.lower().str.contains(busqueda_aux, na=False)
            )
            
            historial = df[mask & (df['DIAS_REALES'].notna())].copy()
            
            if not historial.empty:
                # --- CÁLCULO DE TIEMPOS ---
                fletera_recomendada = historial['FLETERA'].value_counts().idxmax()
                promedio_dias = historial['DIAS_REALES'].mean()
                total_viajes = len(historial)
                dias_redondeados = math.ceil(promedio_dias)
        
                # --- MOTOR LÓGICO DE PRECIOS NEXION ELITE ---

                # 1. Preparación del texto de búsqueda
                texto_domicilio = str(historial['DOMICILIO'].iloc[0]).upper()
                
                # 2. Lista Maestra de Región $65 (Convenio Especial + Bajío/Centro)
                regiones_65 = [
                    # TUS DESTINOS DEL NORTE/PACÍFICO (FORMATO DOBLE)
                    "HERMOSILLO", "HERMOSILLO, SON", "GUAYMAS", "GUAYMAS, SON", 
                    "DURANGO", "DURANGO, DUR", "SALTILLO", "SALTILLO, COA", 
                    "TEPIC", "TEPIC, NAY", "MAZATLAN", "MAZATLAN, SIN", 
                    "CANANEA", "CANANEA, SON", "TORREON", "TORREON, COA", 
                    "CULIACAN", "CULIACAN, SIN", "CIUDAD OBREGON", "CIUDAD OBREGON, SON", 
                    "LOS MOCHIS", "LOS MOCHIS, SIN", "OBREGON", "OBREGON, SON", 
                    "CABORCA", "CABORCA, SON", "NOGALES", "NOGALES, SON", 
                    "NAVOJOA", "NAVOJOA, SON", "MONTERREY", "MONTERREY, NL",
                    "APODACA", "APODACA, NL", "PIEDRAS NEGRAS", "PIEDRAS NEGRAS, COA",
                    "NUEVO VALLARTA", "NUEVO VALLARTA, NAY", "RINCON DE GUAYABITOS", "RINCON DE GUAYABITOS, NAY",
                    "CAJEME, CIUDAD OBREGON, SON", "TORREON COAHUILA, COA",
                
                    # ESTADOS Y ABREVIACIONES GENERALES (CENTRO/BAJÍO)
                    "QUERETARO", "QRO", "QUE", "GUANAJUATO", "GTO", "LEON", "CELAYA", 
                    "AGUASCALIENTES", "AGS", "SAN LUIS POTOSI", "SLP", "HIDALGO", "HID", 
                    "PUEBLA", "PUE", "JALISCO", "JAL", "ESTADO DE MEXICO", "EDOMEX",
                    "TLAXCALA", "TLA", "MORELOS", "MOR", "CDMX", "CMX", "DF", "DF2",
                    
                    # VARIANTES CDMX Y CIUDAD DE MÉXICO
                    "MEXICO, DF", "MEXICO, DF2", "CIUDAD DE MEXICO", "MÉXICO, DF2", ", CMX",
                    "CIUDAD DE MÉXICO, DF2", "DELEGACION CUAUHTEMOC, CMX", "ALCALDIA CUAUHTEMOC, CMX",
                    "ALCALDIA CUAJIMALPA DE MORELOS, CMX", "CUAJIMALPA DE MORELOS, DF2",
                    
                    # CIUDADES ESPECÍFICAS DE TU IMAGEN
                    "MATEHUALA, SLP", "IXTAPAN DE LA SAL, MEX", "QUERETARO, QUE", "ATITALAQUIA, HID",
                    "MORELIA, MCH", "SILAO, GTO", "TOLUCA, MEX", "SALAMANCA, GTO", "SANTIAGO DE QUERETARO, QUE",
                    "JURIQUILLA, QUE", "PACHUCA, HID", "CALVILLO, AGS", "PUEBLA, PUE", "AMEALCO DE BONFIL, QUE",
                    "TULA DE ALLENDE, HID", "ACAMBARO, GTO", "CUAUTLANCINGO, PUE", "NUEVA ITALIA, MCH", 
                    "JACONA, MCH", "CORONANGO, PUE", "IRAPUATO, GTO", "GUANAJUATO, GTO", 
                    "SAN MIGUEL DE ALLENDE, GTO", "ZAMORA, MCH", "CUERNAVACA, MOR", "TOLUCA, DF2", 
                    "IXTAPALUCA, MEX", "IZTACALCO, CMX", "TETLATLAHUACA, TLA", "NAUCALPAN DE JUAREZ, MEX", 
                    "NICOLAS ROMERO, MEX", "SAN ANDRES, PUE", "TLANEPANTLA, MEX", "TEPOTZOTLAN, MEX", 
                    "VALLE DE BRAVO, MEX", "PATZCUARO, MCH", "ALVARO OBREGON, CMX", "TLALPAN, DF2", 
                    "SAN ANDRES CHOLULA, PUE", "TOLUCA DE LERDO, MEX", "CEDRAL, SLP", "TEQUISQUIAPAN, QUE", 
                    "TLALNEPANTLA DE BAZ, CMX", "MÉXICO, DF2", "BERNAL, QUE", "SILAO DE LA VICTORIA, GTO", 
                    "SAN JUAN DEL RIO, QUE", "CUAHUTEMOC, CMX", "METEPEC, MEX", "PACHUCA de SOTO, HID", 
                    "MUNICIPIO ALVARO OBREGON, MCH", "TLANEPANTLA, CMX", "ATLIXCO, PUE", "MIGUEL HIDALGO, CMX", 
                    "SANTA CRUZ TECÁMAC, MEX", "EL MARQUES, QUE", "MARINA NACIONAL, CMX", "MEXICO, DF2", 
                    "CUAJIMALPA DE MORELOS, CMX", "URUAPAN, MCH", "CIUDAD DE MEXICO, DF2", "BENITO JUAREZ, CMX", 
                    "YAUHQUEMEHCAN, TLA", "NAUCALPAN DE JUAREZ, CMX", "GUADALAJARA, JAL", "ZAPOTLAN EL GRANDE, JAL",
                    "ARANDAS, JAL", "SAN JUAN DE LOS LAGOS, JAL", "JOCOTEPEC, JAL", "CD GUZMAN, JAL"
                ]
                
                # 3. Aplicación del "SEGURO VERACRUZ" y Evaluación de Región
                # Si detecta Veracruz en el domicilio, bloquea los $65 inmediatamente
                if any(x in texto_domicilio for x in ["VERACRUZ", " VER ", " VER.", ", VER"]):
                    es_region_65 = False
                else:
                    es_region_65 = any(region in texto_domicilio for region in regiones_65)
                
                # 4. Cálculo de Tarifas según cantidad de cajas
                if 1 <= num_cajas <= 4:
                    precio_unitario = 450 / num_cajas
                    total_sin_iva = 450
                    leyenda_region = "Tarifa Plana Nacional (1-4 cajas)"
                else:
                    if es_region_65:
                        precio_unitario = 65
                        leyenda_region = "Zona con Tarifa Preferencial"
                    else:
                        precio_unitario = 95
                        leyenda_region = "Zona Norte / Sur / Costa"
                    total_sin_iva = num_cajas * precio_unitario
                
                # 5. Impuesto y Total Final
                total_con_iva = total_sin_iva * 1.16
        
                # --- RENDERIZADO ESTILO ONYX REPOTENCIADO ---
                st.markdown(f"""<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 25px;"><div class="kpi-ruta-card" style="flex: 1; min-width: 280px; border-left: 5px solid #A4B9C8; position: relative; overflow: hidden;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;"><span style="font-size: 0.7rem; color: #A4B9C8; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">Tiempo Estimado</span><span style="font-size: 1.1rem; color: #FFFFFF; font-weight: 900;">{fletera_recomendada}</span></div><div class="kpi-route-flow" style="margin: 15px 0;"><span class="city" style="font-size: 1.2rem;">GDL</span><div style="flex-grow: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;"><span style="font-size: 0.7rem; color: #A4B9C8; letter-spacing: 2px;">TRANSIT</span><div style="width: 80%; height: 2px; background: linear-gradient(90deg, transparent, #A4B9C8, transparent);"></div></div><span class="city" style="font-size: 1.2rem; color: #FFFFFF;">{texto_mostrar[:15]}</span></div><div style="display: flex; align-items: baseline; gap: 8px;"><span style="font-size: 2.2rem; font-weight: 900; color: #FFFFFF;">{dias_redondeados}</span><span style="font-size: 1rem; color: #A4B9C8; font-weight: bold;">DÍAS HÁBILES</span></div><div style="margin-top: 10px; font-size: 0.9rem; color: #A4B9C8; border-top: 1px solid rgba(164, 185, 200, 0.1); padding-top: 8px;">Basado en {total_viajes} entregas exitosas a esta zona.</div></div><div class="kpi-ruta-card" style="flex: 1; min-width: 280px; border-left: 5px solid #D4AF37; background: linear-gradient(145deg, #1c2a35, #111b22);"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;"><span style="color: #D4AF37; font-weight: 900; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1.5px;">Costo de Flete</span></div><div style="margin-top: 5px;"><div style="font-size: 0.75rem; color: #A4B9C8; text-transform: uppercase; letter-spacing: 1px;">Inversión Total</div><div style="display: flex; align-items: baseline; gap: 5px;"><span style="font-size: 2.2rem; font-weight: 400; color: #D4AF37;">${total_con_iva:,.2f}</span><span style="font-size: 0.8rem; color: #A4B9C8;">MXN</span></div></div><div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 10px; margin-top: 10px; border: 1px solid rgba(212, 175, 55, 0.1);"><div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #E0E6ED;"><span>Cajas: <b>{num_cajas}</b></span><span>Unit: <b>${precio_unitario:,.2f}</b></span></div><div style="font-size: 0.7rem; color: #D4AF37; margin-top: 5px; text-transform: uppercase; font-weight: bold;">✓ {leyenda_region}</div></div><div style="text-align: right; margin-top: 8px; font-size: 0.6rem; color: #A4B9C8; font-style: italic;">*Incluye 16% de IVA</div></div></div>""", unsafe_allow_html=True) # 3. Tabla de Detalles (Tu código original)
                #------------
                # --- HISTORIAL DE ENVÍOS ENCONTRADOS (DISEÑO PREMIUM) ---
                if not historial.empty:
                    st.markdown('<p style="color:#FFFFFF; font-weight:800; letter-spacing:2px; font-size:14px; margin-bottom:15px; border-left: 4px solid #00FFAA; padding-left: 10px;">HISTORIAL DE ENVÍOS ENCONTRADOS</p>', unsafe_allow_html=True)
                    
                    # Preparación de datos
                    historial_sorted = historial[['NÚMERO DE PEDIDO','NOMBRE DEL CLIENTE','DOMICILIO','FECHA DE ENVÍO','FLETERA']].sort_values(by='FECHA DE ENVÍO', ascending=False).copy()
                    historial_sorted['FECHA_STR'] = historial_sorted['FECHA DE ENVÍO'].dt.strftime('%d/%m/%Y')
                    data_hist = historial_sorted.fillna('').to_dict('records')
                
                    # Renderizado de Tarjetas
                    html_historial = f"""
                    <div style="padding: 5px; font-family: 'Inter', sans-serif;">
                        <style>
                            .card-historial {{
                                background-color: #263238;
                                border: 1px solid rgba(255, 255, 255, 0.05);
                                border-radius: 10px;
                                padding: 14px 20px;
                                margin-bottom: 10px;
                                transition: all 0.3s ease;
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                width: 100%;
                                box-sizing: border-box;
                            }}
                            .card-historial:hover {{
                                border-color: #38bdf8;
                                background-color: #2d3b42;
                                transform: translateX(4px);
                            }}
                            .label-mini {{ font-size: 8px; text-transform: uppercase; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px; }}
                            .valor-id {{ font-size: 15px; font-weight: 800; color: #00FFAA; font-family: monospace; }}
                            .valor-text {{ font-size: 12px; font-weight: 600; color: #FFFFFF; }}
                            .sub-text {{ font-size: 10px; color: rgba(255,255,255,0.6); font-style: italic; }}
                            
                            /* Scrollbar */
                            ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                            ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); }}
                            ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                            ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                        </style>
                        {"".join([f'''
                        <div class="card-historial">
                            <div style="flex: 1;">
                                <div class="label-mini">Pedido</div>
                                <div class="valor-id">{str(item.get('NÚMERO DE PEDIDO', ''))}</div>
                            </div>
                            <div style="flex: 2; padding: 0 15px;">
                                <div class="label-mini">Cliente / Domicilio</div>
                                <div class="valor-text uppercase truncate">{str(item.get('NOMBRE DEL CLIENTE', ''))[:35]}</div>
                                <div class="sub-text truncate">{str(item.get('DOMICILIO', ''))[:50]}</div>
                            </div>
                            <div style="flex: 1; text-align: right;">
                                <div class="label-mini">Fletera / Fecha</div>
                                <div style="color: #38bdf8; font-size: 12px; font-weight: 700;">{str(item.get('FLETERA', ''))}</div>
                                <div class="valor-text" style="font-size: 11px; opacity: 0.8;">{item.get('FECHA_STR', '')}</div>
                            </div>
                        </div>
                        ''' for item in data_hist])}
                    </div>
                    """
                    components.html(html_historial, height=450, scrolling=True)
                
                else:
                    st.info(f"Lo siento **{usuario_actual}**, no encontré historial para: **{busqueda_manual}**")   
        
       
        # PESTAÑA 3: DESPACHOS (Análisis de Despachos 24h)-
        with tab_despachos:
            st.markdown("""
                <style>
                    div[data-testid="stDownloadButton"] > button {
                        background-color: #2B343B !important; 
                        color: #FFFFFF !important;            
                        border: 1px solid #2B343B !important; 
                        border-radius: 5px !important;
                        transition: all 0.3s ease !important;
                        width: 100% !important;
                    }
                    div[data-testid="stDownloadButton"] > button:hover {
                        background-color: #00A3A3 !important; 
                        color: #FFFFFF !important;            
                        border-color: #00A3A3 !important;
                    }
                    div[data-testid="stDownloadButton"] > button:active {
                        background-color: #00A3A3 !important;
                        border-color: #00A3A3 !important;
                    }
                    /* Forzamos que el texto interno no se ponga gris/transparente */
                    div[data-testid="stDownloadButton"] > button p {
                        color: #FFFFFF !important;
                    }
                </style>
            """, unsafe_allow_html=True)
        
            # 1. Copia y limpieza inmediata
            df_vol = df_mes.copy()
            
            # Forzamos la lectura de fechas ignorando errores de formato
            df_vol['EMISION'] = pd.to_datetime(df_vol['EMISION'], dayfirst=True, errors='coerce')
            df_vol['FECHA DE ENVÍO'] = pd.to_datetime(df_vol['FECHA DE ENVÍO'], dayfirst=True, errors='coerce')
        
            # 2. Configuración de Feriados
            lista_feriados = ['2026-01-01', '2026-02-02', '2026-03-16', '2026-05-01']
            feriados_np = np.array(lista_feriados, dtype='datetime64[D]')
        
            # 3. Función de Cálculo (Sin rodeos)
            def calcular_kpi_24h(row):
                ini = row['EMISION']
                fin = row['FECHA DE ENVÍO']
                
                # Si en tu matriz ves el dato pero Python dice NaT, usamos 'fin' para rescatar la fila
                if pd.isna(ini) and not pd.isna(fin):
                    ini = fin
                    
                if pd.isna(ini) or pd.isna(fin):
                    return "Sin Datos"
                
                try:
                    # Comparación directa
                    if fin <= ini: return "A Tiempo"
                    
                    # Días hábiles (Lunes a Sábado '1111110')
                    d = np.busday_count(ini.date(), fin.date(), weekmask='1111100', holidays=feriados_np)
                    
                    if d == 0: return "A Tiempo"
                    if d == 1 and fin.time() <= ini.time(): return "A Tiempo"
                    return "Fuera de Tiempo"
                except:
                    return "Sin Datos"
        
            # 4. Ejecución del cálculo
            df_vol['Estado_KPI'] = df_vol.apply(calcular_kpi_24h, axis=1)
            
            # 5. Métricas para las tarjetas
            validos = df_vol[df_vol['Estado_KPI'] != "Sin Datos"]
            tot_v = len(validos)
            ok_v = len(validos[validos['Estado_KPI'] == "A Tiempo"])
            no_v = tot_v - ok_v
            
            # 6. Interfaz Visual
            st.markdown(f'<div style="text-align:center;margin-bottom:30px;"><p style="color:{vars_css["sub"]};font-size:11px;letter-spacing:3px;font-weight:700;text-transform:uppercase;">Desempeño Despachos 24h — {mes_sel}</p></div>', unsafe_allow_html=True)
            
            c_v1, c_v2, c_v3 = st.columns(3)
            
            def render_modern_bar(valor, total, label, color):
                porcentaje = (valor / total * 100) if total > 0 else 0
                st.markdown(f"""
                    <div style="background: rgba(26, 37, 47, 0.6); padding: 20px; border-radius: 15px; border: 1px solid #243441; text-align: center;">
                        <p style="color: #A4B9C8; font-size: 10px; margin-bottom: 5px; font-weight: bold;">{label.upper()}</p>
                        <h2 style="color: white; margin: 0; font-size: 24px;">{valor}</h2>
                        <p style="color: {color}; font-size: 16px; margin-top: 5px; font-weight: bold;">{porcentaje:.1f}%</p>
                        <div style="background-color: #0B1014; border-radius: 10px; height: 8px; width: 100%; margin-top: 10px;">
                            <div style="background-color: {color}; height: 8px; width: {porcentaje}%; border-radius: 10px; box-shadow: 0 0 10px {color}88;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c_v1: render_modern_bar(tot_v, tot_v, "Total Facturas", "#5a8dee")
            with c_v2: render_modern_bar(ok_v, tot_v, "A Tiempo", "#39da8a")
            with c_v3: render_modern_bar(no_v, tot_v, "Fuera de Meta", "#ff5b5c")
        
            # --- 7. DETALLE DE OPERACIÓN (SIEMPRE VISIBLE - COLOR SMART) ---
            st.markdown("<p style='font-size:12px; font-weight:bold; color:#54AFE7; letter-spacing:2px; margin-top:20px; margin-bottom:15px;'>🔍 DETALLE DE OPERACIÓN EN TIEMPO REAL</p>", unsafe_allow_html=True)
            
            if not df_vol.empty:
                # 1. Preparación de datos
                df_display = df_vol[['NÚMERO DE PEDIDO','EMISION', 'FECHA DE ENVÍO', 'Estado_KPI']].copy()
                
                # Formateo para visualización
                df_display['EMISION_STR'] = df_display['EMISION'].dt.strftime('%d/%m/%Y %H:%M').fillna("S/D")
                df_display['ENVIO_STR'] = df_display['FECHA DE ENVÍO'].dt.strftime('%d/%m/%Y %H:%M').fillna("S/D")
                
                data_detalle = df_display.to_dict('records')
                alto_detalle = min(len(data_detalle) * 90 + 20, 550)
            
                # 2. Renderizado de Tarjetas
                html_detalle = f"""
                <div style="font-family: 'Inter', sans-serif; padding-right: 10px;">
                    <style>
                        body {{ background: transparent; margin: 0; padding: 0; }}
                        ::-webkit-scrollbar {{ width: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.05); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; min-height: 50px; }}
                        ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
            
                        .card-detalle {{
                            background: #263238;
                            border: 1px solid rgba(255, 255, 255, 0.05);
                            border-left: 5px solid #94a3b8;
                            border-radius: 10px;
                            padding: 12px 20px;
                            margin-bottom: 8px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            transition: 0.3s;
                        }}
                        .card-detalle:hover {{ border-color: #38bdf8; background: #2d3b42; transform: translateX(5px); }}
                        .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: normal; letter-spacing: 1px; text-transform: uppercase; }}
                        .val-pedido {{ color: #00FFAA; font-family: monospace; font-size: 15px; font-weight: 800; }}
                        .val-fecha {{ color: #FFFFFF; font-size: 11px; font-weight: 400; opacity: 0.9; }}
                        
                        .badge-kpi {{ padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; text-align: center; min-width: 100px; }}
                        
                        .st-entregado {{ background: rgba(0, 255, 170, 0.1); color: #00FFAA; border: 1px solid rgba(0, 255, 170, 0.2); }}
                        .st-transito {{ background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.2); }}
                        .st-fuera {{ background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid rgba(255, 75, 75, 0.2); }}
                        .st-otro {{ background: rgba(255, 255, 255, 0.05); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.1); }}
                    </style>
                    
                    {"".join([f'''
                    <div class="card-detalle" style="border-left-color: {
                        '#00FFAA' if 'ENTREGADO' in str(item['Estado_KPI']).upper() else 
                        '#38bdf8' if 'TRANS' in str(item['Estado_KPI']).upper() else 
                        '#FF4B4B' if 'FUERA DE TIEMPO' in str(item['Estado_KPI']).upper() else '#94a3b8'};">
                        
                        <div style="flex: 1;">
                            <div class="label-mini">Pedido</div>
                            <div class="val-pedido">{item['NÚMERO DE PEDIDO']}</div>
                        </div>
                        
                        <div style="flex: 1.5; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                            <div class="label-mini">Emisión</div>
                            <div class="val-fecha">{item['EMISION_STR']}</div>
                        </div>
            
                        <div style="flex: 1.5; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                            <div class="label-mini">Salida de Almacén</div>
                            <div class="val-fecha">{item['ENVIO_STR']}</div>
                        </div>
            
                        <div style="flex: 1; text-align: right;">
                            <div class="badge-kpi {
                                'st-entregado' if 'ENTREGADO' in str(item['Estado_KPI']).upper() else 
                                'st-transito' if 'TRANS' in str(item['Estado_KPI']).upper() else 
                                'st-fuera' if 'FUERA DE TIEMPO' in str(item['Estado_KPI']).upper() else 'st-otro'}">
                                {str(item['Estado_KPI']).upper()}
                            </div>
                        </div>
                    </div>
                    ''' for item in data_detalle])}
                </div>
                """
                import streamlit.components.v1 as components
                components.html(html_detalle, height=alto_detalle, scrolling=True)
            
                # 3. Botón de Descarga Excel
                import io
                df_excel = df_display.copy()
                # Limpiamos fechas para el Excel (solo fecha sin hora o como prefieras)
                df_excel['EMISION'] = df_excel['EMISION'].dt.strftime('%d/%m/%Y')
                df_excel['FECHA DE ENVÍO'] = df_excel['FECHA DE ENVÍO'].dt.strftime('%d/%m/%Y')
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_excel.to_excel(writer, index=False, sheet_name='Detalle_Operacion')
                buffer.seek(0)
            
                # Aquí también le pusimos type="primary" para forzar a Streamlit a darle fondo oscuro
                st.download_button(
                    label="DESCARGAR REPORTE DE OPERACIÓN (EXCEL)",
                    data=buffer,
                    file_name=f"Detalle_Operacion_{mes_sel}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.info("No hay datos disponibles para el detalle.")
            
        # PESTAÑA 4: % PARTICIPACIÓN-
        with tab_participacion:
            # --- CSS BLINDADO: Clases específicas para resultados ---
            st.markdown("""
                <style>
                    .metric-card-agc {
                        background-color: #263238;
                        border: 1px solid rgba(255, 255, 255, 0.05);
                        border-radius: 12px;
                        padding: 12px;
                        text-align: center;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                    }
                    /* Título de la tarjeta (Blanco, pequeño) */
                    .op-query-text {
                        color: #FFFFFF !important;
                        font-weight: 700 !important;
                        font-size: 10px !important;
                        letter-spacing: 1.5px !important;
                        text-transform: uppercase !important;
                        margin-bottom: 8px !important;
                        opacity: 0.8;
                    }
                    /* CLASE NUEVA: Para los números del Volumen */
                    .valor-volumen {
                        color: #FFFFFF !important;
                        font-weight: 800 !important;
                        font-family: monospace !important;
                        font-size: 26px !important; 
                        letter-spacing: 2px !important;
                        margin: 0 !important;
                    }
                    /* CLASE NUEVA: Para el nombre de la Paquetería */
                    .valor-carrier {
                        color: #00FFAA !important;
                        font-weight: 500 !important;
                        font-size: 26px !important;
                        font-style: italic !important;
                        letter-spacing: 1px !important;
                        margin: 0 !important;
                    }
                    /* Estilo para los Radio Buttons */
                    div[data-testid="stRadio"] > label {
                        color: #00FFAA !important;
                        font-family: 'Inter', sans-serif;
                        font-weight: 800 !important;
                        font-size: 11px !important;
                        text-transform: uppercase;
                    }
                </style>
            """, unsafe_allow_html=True)
        
            URL_LOGISTICA = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
            
            @st.cache_data
            def load_data_logistica():
                try:
                    df_l = pd.read_csv(URL_LOGISTICA, low_memory=False)
                    df_l.columns = [c.replace('_x000D_', '').strip() for c in df_l.columns]
                    if 'MES' in df_l.columns:
                        df_l['MES'] = df_l['MES'].astype(str).str.upper().str.strip()
                    if 'FORMA DE ENVIO' in df_l.columns:
                        df_l['FORMA DE ENVIO'] = df_l['FORMA DE ENVIO'].astype(str).str.strip()
                    df_l['CAJAS'] = pd.to_numeric(df_l['CAJAS'], errors='coerce').fillna(0)
                    return df_l
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
                    return None
            
            df_log = load_data_logistica()
            
            if df_log is not None:
                st.markdown("<p class='op-query-text' style='text-align:center;'>DISTRIBUCION DE CARGA MENSUAL</p>", unsafe_allow_html=True)
                
                tipo_mov = st.radio(
                    "Selecciona el flujo:",
                    ["TODOS", "COBRO DESTINO", "COBRO REGRESO"],
                    index=0,
                    horizontal=True,
                    key=f"tipo_mov_{mes_sel}"
                )
        
                df_log_filtrado = df_log[df_log["MES"] == mes_sel].copy()
        
                if tipo_mov == "COBRO DESTINO":
                    df_log_filtrado = df_log_filtrado[df_log_filtrado['FORMA DE ENVIO'].str.contains('DESTINO', case=False, na=False)]
                elif tipo_mov == "COBRO REGRESO":
                    df_log_filtrado = df_log_filtrado[df_log_filtrado['FORMA DE ENVIO'].str.contains('REGRESO', case=False, na=False)]
        
                if not df_log_filtrado.empty:
                    total_cajas_mes = df_log_filtrado['CAJAS'].sum()
                    df_part = df_log_filtrado.groupby('TRANSPORTE')['CAJAS'].sum().reset_index()
                    df_part['PORCENTAJE'] = (df_part['CAJAS'] / total_cajas_mes) * 100
                    df_part = df_part.sort_values(by='PORCENTAJE', ascending=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.markdown(f"""
                            <div class="metric-card-agc">
                                <p class="op-query-text">VOLUMEN TOTAL (UNIT)</p>
                                <p class="valor-volumen">{int(total_cajas_mes):,}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                    with c2:
                        lider_n = df_part.iloc[-1]['TRANSPORTE'] if not df_part.empty else "N/A"
                        st.markdown(f"""
                            <div class="metric-card-agc">
                                <p class="op-query-text">CARRIER DOMINANTE</p>
                                <p class="valor-carrier">{lider_n}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # --- GRÁFICO DE BARRAS ---
                    altura_ajustada = max(400, len(df_part) * 40)

                    fig_bar = go.Figure(go.Bar(
                        x=df_part['PORCENTAJE'],
                        y=df_part['TRANSPORTE'],
                        orientation='h',
                        marker=dict(
                            color=df_part['PORCENTAJE'],
                            # Cambié el inicio de la escala para que combine mejor con el fondo oscuro
                            colorscale=['#2c3e50', '#1cc88a'], 
                            line=dict(color='rgba(255, 255, 255, 0.1)', width=1) # Un borde sutil
                        ),
                        text=df_part['PORCENTAJE'].apply(lambda x: f'{x:.1f}%'),
                        textposition='outside',
                        cliponaxis=False 
                    ))
                    
                    fig_bar.update_layout(
                        height=altura_ajustada,
                        # El color exacto de tus tarjetas AGC
                        paper_bgcolor='#263238', 
                        plot_bgcolor='#263238', 
                        font=dict(family="Inter", size=12, color="#FFFFFF"),
                        margin=dict(l=200, r=60, t=30, b=20),
                        # Añadimos bordes redondeados visuales (vía Streamlit container usualmente)
                        # pero aquí forzamos que el texto y ejes se vean impecables
                        xaxis=dict(
                            showgrid=False, 
                            zeroline=False, 
                            showticklabels=True,
                            tickfont=dict(color='rgba(255,255,255,0.5)')
                        ),
                        yaxis=dict(
                            showgrid=False, 
                            automargin=True,
                            tickfont=dict(color='#FFFFFF', size=11)
                        ),
                        showlegend=False,
                        # Este paso es clave para que no se vea el recuadro blanco al hacer hover
                        hoverlabel=dict(
                            bgcolor='#1a2432',
                            font_size=12,
                            font_family="Inter"
                        )
                    )
                    
                    # Renderizado con un toque extra de estilo AGC
                    st.plotly_chart(
                        fig_bar, 
                        use_container_width=True, 
                        config={'displayModeBar': False}, 
                        key=f"bar_part_{mes_sel}_{tipo_mov}"
                    )
        
                    # --- EXPANDER: DESGLOSE POR DESTINO ---
                    # --- EXPANDER: DESGLOSE POR DESTINO ---
                    st.markdown("<h3 style='color:white; font-size:16px; letter-spacing:2px; font-weight:800; border-left:4px solid #38bdf8; padding-left:10px; margin-bottom:20px;'>🌐 EXPLORADOR DE RUTAS Y DESTINOS</h3>", unsafe_allow_html=True)
                    
                    lista_carriers = ["TODOS"] + sorted(df_log_filtrado['TRANSPORTE'].unique())
                    
                    # --- AQUÍ ESTÁ EL TRUCO PARA LA ALINEACIÓN PERFECTA ---
                    # Usamos label_visibility="collapsed" para que el selectbox no tenga espacio arriba
                    col_sel, col_dl = st.columns([3, 1])
                    
                    with col_sel:
                        carrier_sel = st.selectbox(
                            "Selecciona un Carrier:", # Este texto no se verá pero es necesario
                            options=lista_carriers,
                            key=f"select_carrier_{mes_sel}_{tipo_mov}",
                            label_visibility="collapsed" # <--- Esto quita el espacio de arriba
                        )
                    
                    # Lógica de filtrado (se mantiene igual)
                    if carrier_sel != "TODOS":
                        df_dest_filtered = df_log_filtrado[df_log_filtrado['TRANSPORTE'] == carrier_sel].copy()
                    else:
                        df_dest_filtered = df_log_filtrado.copy()
                    
                    if not df_dest_filtered.empty:
                        df_dest_sum = df_dest_filtered.groupby(['TRANSPORTE', 'DESTINO', 'FORMA DE ENVIO'])['CAJAS'].sum().reset_index()
                        df_dest_sum = df_dest_sum.sort_values(by=['TRANSPORTE', 'CAJAS'], ascending=[True, False])
                        total_sel = df_dest_sum['CAJAS'].sum()
                    
                        with col_dl:
                            csv_data = df_dest_sum.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 DESCARGAR",
                                data=csv_data,
                                file_name=f"reporte_{carrier_sel}_{mes_sel}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        # Bajamos la métrica para que no estorbe la fila de arriba
                        st.markdown(f"<p style='color:#00FFAA; font-size:13px; font-weight:800; letter-spacing:1px; margin-top:10px; margin-bottom:15px;'>UNIDADES EN SELECCIÓN ACTUAL: {int(total_sel):,}</p>", unsafe_allow_html=True)
                                                
                        data_rutas = df_dest_sum.to_dict('records')
                    
                        # --- TU DISEÑO HTML PREMIUM SIGUE IGUAL ABAJO ---
                        html_rutas = f"""
                        <div style="font-family: 'Inter', sans-serif; padding-right: 10px;">
                            <style>
                                body {{ background: transparent; margin: 0; padding: 0; }}
                                ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                                ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                                ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; }}
                                ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; box-shadow: 0 0 10px rgba(46, 204, 113, 0.5); }}
                                .carrier-group {{ background: #263238; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; margin-bottom: 12px; overflow: hidden; width: 100%; transition: all 0.3s ease; }}
                                .carrier-group:hover {{ border-color: rgba(0, 255, 170, 0.3); }}
                                .carrier-header {{ background: rgba(56, 189, 248, 0.1); padding: 10px 15px; border-bottom: 1px solid rgba(56, 189, 248, 0.2); display: flex; justify-content: space-between; align-items: center; }}
                                .carrier-name {{ color: #38bdf8; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
                                .route-row {{ display: flex; justify-content: space-between; padding: 12px 15px; align-items: center; }}
                                .dest-name {{ color: #FFFFFF; font-size: 12px; font-weight: 600; }}
                                .method-tag {{ background: rgba(168, 85, 247, 0.1); color: #a855f7; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: 700; margin-left: 8px; }}
                                .unit-badge {{ background: rgba(0, 255, 170, 0.1); color: #00FFAA; padding: 5px 12px; border-radius: 8px; font-family: monospace; font-weight: 800; font-size: 13px; border: 1px solid rgba(0, 255, 170, 0.2); }}
                            </style>
                            {"".join([f'''
                            <div class="carrier-group">
                                <div class="carrier-header">
                                    <span class="carrier-name">{item['TRANSPORTE']}</span>
                                    <span style="color:rgba(255,255,255,0.3); font-size:8px; font-weight:800;">DETALLE DE RUTA</span>
                                </div>
                                <div class="route-row">
                                    <div>
                                        <span class="dest-name">{item['DESTINO']}</span>
                                        <span class="method-tag">{item['FORMA DE ENVIO']}</span>
                                    </div>
                                    <div class="unit-badge">{int(item['CAJAS']):,} u.</div>
                                </div>
                            </div>
                            ''' for item in data_rutas])}
                        </div>
                        """
                        import streamlit.components.v1 as components
                        components.html(html_rutas, height=500, scrolling=True)
                        
                    else:
                        st.warning(f"No se encontraron registros para '{tipo_mov}' en el mes seleccionado.")
        
        # PESTAÑA 5: AGC---
        # PESTAÑA 5: AGC ---
        with tab_entregas_agc:
        
            st.markdown("""
                <style>
                    /* 1. Reset para que el contenedor use todo el ancho */
                    div[data-testid="stBlock"] { max-width: 100% !important; padding: 0 !important; }
                    
                    /* 2. Estilo para los botones personalizados */
                    div.stButton > button {
                        background-color: #2B343B !important; 
                        color: #FFFFFF !important;            
                        border: 1px solid #2B343B !important; 
                        border-radius: 5px !important;
                        transition: all 0.3s ease !important;
                        width: 100% !important;
                    }
            
                    div.stButton > button:hover {
                        background-color: #00A3A3 !important; 
                        color: #FFFFFF !important;            
                        border-color: #00A3A3 !important;
                    }
                    
                    div.stButton > button:active {
                        background-color: #00A3A3 !important;
                        border-color: #00A3A3 !important;
                    }
                </style>
            """, unsafe_allow_html=True)
        
            # --- VALIDACIÓN DIRECTA CON TU VARIABLE DE SESIÓN DE ADMINISTRADOR ---
            usuario_actual = st.session_state.get("usuario_activo", "").upper()
            es_admin = (usuario_actual == "RIGOBERTO")
        
            if es_admin:
                with st.expander("🔐 Panel de Seguridad / Modo Edición Admin", expanded=False):
                    st.success("Acceso Concedido: Administrador Reconocido 🔓")
                    modo_edicion = st.checkbox("Activar Modo Edición de Citas en Pantalla", value=False, key="check_modo_edicion_session")
            else:
                modo_edicion = False
        
            # --- Lógica de Navegación ---
            if 'tipo_entrega' not in st.session_state:
                st.session_state.tipo_entrega = 'C A M I O N'
        
            if 'mes_calendario' not in st.session_state:
                st.session_state.mes_calendario = 6  # Por defecto inicia en Junio
        
            # Creamos TRES columnas para los botones de navegación superiores
            col_btn1, col_btn2, col_btn3 = st.columns(3)
        
            with col_btn1:
                btn_type_1 = "primary" if st.session_state.tipo_entrega == 'C A M I O N' else "secondary"
                if st.button("ENTREGAS AGC CAMIÓN", use_container_width=True, type=btn_type_1):
                    st.session_state.tipo_entrega = 'C A M I O N'
                    st.rerun()
        
            with col_btn2:
                btn_type_2 = "primary" if st.session_state.tipo_entrega == 'T R A I L E R' else "secondary"
                if st.button("ENTREGAS AGC TRAILER", use_container_width=True, type=btn_type_2):
                    st.session_state.tipo_entrega = 'T R A I L E R'
                    st.rerun()
        
            with col_btn3:
                btn_type_3 = "primary" if st.session_state.tipo_entrega == 'C A L E N D A R I O' else "secondary"
                if st.button("VISTA CALENDARIO GLOBAL", use_container_width=True, type=btn_type_3):
                    st.session_state.tipo_entrega = 'C A L E N D A R I O'
                    st.rerun()
        
            # --- Encabezado de Texto Dinámico ---
            if st.session_state.tipo_entrega == 'C A M I O N':
                titulo_dinamico = "ENTREGAS DE CAMIONES"
            elif st.session_state.tipo_entrega == 'T R A I L E R':
                titulo_dinamico = "ENTREGAS DE TRAILER"
            else:
                titulo_dinamico = "CALENDARIO DE ENTREGAS"
        
            st.markdown(f"""
                <div style='text-align:center; margin-top:25px; margin-bottom:20px;'>
                    <span style='color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;'>
                        {titulo_dinamico}
                    </span>
                </div>
            """, unsafe_allow_html=True)
        
            # --- Función de Renderizado (Tarjetas de Entregas) ---
            def render_logistica_flow_responsive(data):
                html_content = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://cdn.tailwindcss.com"></script>
                    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
                    <style>
                        body {{ 
                            font-family: 'Inter', sans-serif; 
                            background-color: #384A52; 
                            color: #e2e8f0; 
                            margin: 0;
                            padding: 5px;
                            width: 100%;
                        }}
                        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; }}
                        ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                        .list-row {{
                            background-color: #263238;
                            border: 1px solid rgba(255, 255, 255, 0.05);
                            transition: all 0.2s ease;
                            margin-bottom: 8px;
                            border-radius: 10px;
                            overflow: hidden;
                            width: 100%;
                        }}
                        .list-row:hover {{
                            background-color: #2c3b42;
                            border-color: rgba(56, 189, 248, 0.3);
                        }}
                        .label-mini {{
                            font-size: 9px;
                            text-transform: uppercase;
                            font-weight: 800;
                            color: #BFBFBF;
                            letter-spacing: 0.5px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="w-full space-y-2">
                        {"".join([f'''
                        <div class="list-row flex items-stretch">
                            <div class="w-2 shrink-0 {"bg-emerald-500" if item['estatus'] == "ENTREGADA" else "bg-amber-500"} shadow-[2px_0_10px_rgba(0,0,0,0.3)]"></div>
                            <div class="flex flex-col md:flex-row flex-1 p-3 items-start md:items-center justify-between gap-4">
                                
                                <div class="w-full md:w-44 shrink-0">
                                    <div class="label-mini">{item['semana']}</div>
                                    <div class="text-sm font-black text-white italic tracking-tighter leading-none min-h-[20px]">
                                        {item['oc']}
                                    </div>
                                    <div class="text-[12px] text-sky-400 font-bold mt-1">
                                        ITEM: {item['item_no']}
                                    </div>
                                </div>
                                
                                <div class="w-full md:flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                                    <div>
                                        <div class="label-mini">Fecha Compromiso</div>
                                        <div class="text-xs text-slate-300 italic truncate min-h-[16px]">
                                            {item['entrega_texto']}
                                        </div>
                                    </div>
                                    <div>
                                        <div class="label-mini">Producto</div>
                                        <div class="text-xs font-semibold text-sky-200 truncate min-h-[16px]">
                                            {item['producto']}
                                        </div>
                                    </div>
                                </div>
        
                                <div class="w-full md:w-[420px] shrink-0 flex gap-4 py-2 md:py-0 border-y md:border-y-0 md:border-x border-white/5 md:px-8">
                                    <div class="w-2/5 shrink-0">
                                        <div class="label-mini">Volumen</div>
                                        <div class="text-sm font-bold text-white min-h-[20px] truncate">{item['cantidad']}</div>
                                    </div>
                                    <div class="w-3/5 shrink-0">
                                        <div class="label-mini">Cita</div>
                                        <div class="text-sm font-mono font-bold min-h-[20px] truncate {"text-slate-500" if "PENDIENTE" in str(item['cita']).upper() else "text-sky-400"}">
                                            {item['cita']}
                                        </div>
                                    </div>
                                </div>
        
                                <div class="w-full md:w-40 flex justify-between md:block text-right shrink-0">
                                    <div class="label-mini md:mb-1">Estatus de Logística</div>
                                    <div class="text-[11px] font-black uppercase {"text-emerald-400" if item['estatus'] == "ENTREGADA" else "text-orange-400"} tracking-tighter min-h-[16px]">
                                        {item['estatus']}
                                    </div>
                                </div>
        
                            </div>
                        </div>
                        ''' for item in data])}
                    </div>
                </body>
                </html>
                """
                return components.html(html_content, height=800, scrolling=True)
        
            # --- Función: Renderizado de Calendario ---
            def render_calendario_visual(data_camion, data_trailer, mes_num, anio=2026):
                meses_nombres = {5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE"}
                nombre_mes = meses_nombres.get(mes_num, "MES")
                
                eventos_dias = {}
                for item in data_camion:
                    try:
                        fecha_str = str(item['cita']).split(" - ")[0].strip()
                        dt = datetime.strptime(fecha_str, "%d/%m/%m" if len(fecha_str.split('/')[2])==2 else "%d/%m/%Y")
                        if dt.month == mes_num and dt.year == anio:
                            if dt.day not in eventos_dias: 
                                eventos_dias[dt.day] = []
                            eventos_dias[dt.day].append({"tipo": "CAMIÓN", "oc": item['oc'], "estatus": item['estatus']})
                    except:
                        pass 
        
                for item in data_trailer:
                    try:
                        fecha_str = str(item['cita']).split(" - ")[0].strip()
                        dt = datetime.strptime(fecha_str, "%d/%m/%Y")
                        if dt.month == mes_num and dt.year == anio:
                            if dt.day not in eventos_dias: 
                                eventos_dias[dt.day] = []
                            eventos_dias[dt.day].append({"tipo": "TRAILER", "oc": item['oc'], "estatus": item['estatus']})
                    except:
                        pass
        
                cal = calendar.Calendar(firstweekday=6) 
                semanas_mes = cal.monthdayscalendar(anio, mes_num)
        
                grid_html = ""
                for semana in semanas_mes:
                    for dia in semana:
                        if dia == 0:
                            grid_html += '<div class="bg-[#2a373d]/40 min-h-[115px] p-1 border border-white/5"></div>'
                        else:
                            eventos_del_dia_html = ""
                            if dia in eventos_dias:
                                for ev in eventos_dias[dia]:
                                    bg_badge = "bg-sky-600/90 border-sky-400" if ev['tipo'] == "CAMIÓN" else "bg-emerald-700/90 border-emerald-500"
                                    texto_badge = f"{ev['tipo']} - {ev['oc']}"
                                    opacity = "opacity-60" if ev['estatus'] == "ENTREGADA" else "opacity-100 animate-pulse"
                                    
                                    eventos_del_dia_html += f'''
                                    <div class="text-[10px] font-bold text-white px-1.5 py-0.5 rounded border mb-1 truncate tracking-tight {bg_badge} {opacity}">
                                        {texto_badge}
                                    </div>
                                    '''
        
                            grid_html += f'''
                            <div class="bg-[#263238] min-h-[115px] p-2 border border-white/5 flex flex-col justify-between hover:bg-[#2c3b42] transition-colors">
                                <span class="text-xs font-black text-slate-400 text-left">{dia}</span>
                                <div class="overflow-y-auto max-h-[85px] space-y-1 mt-1 pr-0.5">
                                    {eventos_del_dia_html}
                                </div>
                            </div>
                            '''
        
                html_calendario = f"""
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://cdn.tailwindcss.com"></script>
                    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
                    <style>
                        body {{ font-family: 'Inter', sans-serif; background-color: #384A52; color: #e2e8f0; margin:0; padding:0; width: 100%; }}
                        ::-webkit-scrollbar {{ width: 4px; }}
                        ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 4px; }}
                    </style>
                </head>
                <body class="p-0">
                    <div class="w-full bg-[#1e272c] rounded-xl border border-white/10 shadow-2xl overflow-hidden">
                        <div class="bg-[#263238] px-6 py-4 border-b border-white/10 flex justify-between items-center">
                            <h2 class="text-xl font-black text-white tracking-widest italic">{nombre_mes} <span style="color: #34D399;" class="font-light">{anio}</span></h2>
                            <div class="flex items-center gap-4 text-xs font-semibold">
                                <div class="flex items-center gap-1.5"><div class="w-3 h-3 bg-sky-600 rounded"></div>CAMIÓN</div>
                                <div class="flex items-center gap-1.5"><div class="w-3 h-3 bg-emerald-700 rounded"></div>TRAILER</div>
                            </div>
                        </div>
                        
                        <div class="grid grid-cols-7 bg-[#212c31] text-center py-2 text-xs font-black text-slate-400 tracking-wider uppercase border-b border-white/5">
                            <div>Dom</div><div>Lun</div><div>Mar</div><div>Mié</div><div>Jue</div><div>Vie</div><div>Sáb</div>
                        </div>
                        
                        <div class="grid grid-cols-7 bg-[#1a2327]">
                            {grid_html}
                        </div>
                    </div>
                </body>
                </html>
                """
                return components.html(html_calendario, height=750, scrolling=True)
        
            # =====================================================================
            # --- EXTRACCIÓN Y GUARDADO AUTOMÁTICO EN GITHUB ---
            # =====================================================================
            
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "agc.csv"
            CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
        
            def get_github_data():
                headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
                response = requests.get(CSV_URL, headers=headers)
                if response.status_code == 200:
                    return pd.read_csv(io.StringIO(response.text))
                else:
                    st.error(f"Hubo un error al cargar los datos: {response.status_code}")
                    return pd.DataFrame()
        
            def guardar_cambios_github(df_nuevo):
                import base64
                headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
                api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
                
                r_get = requests.get(api_url, headers=headers)
                if r_get.status_code != 200:
                    st.error("No se pudo obtener el identificador actual del archivo en GitHub.")
                    return False
                sha_actual = r_get.json().get("sha")
                
                csv_buffer = io.StringIO()
                df_nuevo.to_csv(csv_buffer, index=False)
                csv_content = csv_buffer.getvalue()
                
                content_encoded = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
                
                payload = {
                    "message": "Actualización automática de citas desde panel admin seguro de Rigoberto",
                    "content": content_encoded,
                    "sha": sha_actual
                }
                
                r_put = requests.put(api_url, json=payload, headers=headers)
                if r_put.status_code in [200, 201]:
                    st.success("¡Citas y cambios guardados en GitHub con éxito, mi amor! 🚀")
                    st.cache_data.clear()
                    return True
                else:
                    st.error(f"Error al guardar en GitHub: {r_put.json().get('message', 'Desconocido')}")
                    return False
        
            df_raw = get_github_data()
        
            if not df_raw.empty:
                df_raw.columns = df_raw.columns.str.strip()
        
                # --- MODO EDICIÓN BASADO EN TU SESIÓN DE ADMIN ---
                if modo_edicion:
                    st.warning("⚠️ Modo edición activo. Modifica las celdas abajo y haz clic en el botón de guardar para actualizar GitHub automáticamente.")
                    
                    df_editado = st.data_editor(df_raw, use_container_width=True, num_rows="dynamic", key="editor_agc_admin_session")
                    
                    if st.button("💾 Guardar Cambios en GitHub", key="btn_guardar_github_session"):
                        if guardar_cambios_github(df_editado):
                            st.rerun()
                    st.markdown("---")
        
                # --- PROCESAMIENTO PARA LAS TARJETAS Y CALENDARIO ---
                df_entregas = pd.DataFrame()
                df_entregas['oc'] = df_raw.get('PO Customer', pd.Series(dtype=str)).fillna('').astype(str)
                df_entregas['item_no'] = df_raw.get('Item No.', pd.Series(dtype=str)).fillna('').astype(str)
                df_entregas['producto'] = df_raw.get('PRODUCTO', pd.Series(dtype=str)).fillna('').astype(str)
                
                cajas = df_raw.get('Cajas a Entregar', pd.Series(dtype=str)).fillna('').astype(str).str.lower().str.replace('nan', '0').str.strip()
                tarimas = df_raw.get('Tarimas', pd.Series(dtype=str)).fillna('').astype(str).str.lower().str.replace('nan', '0').str.strip()
                cajas = cajas.replace({'': '0', '0.0': '0'})
                tarimas = tarimas.replace({'': '0', '0.0': '0'})
                
                df_entregas['cantidad'] = cajas + " CXS / " + tarimas + " TAR"
                df_entregas['semana'] = "OV: " + df_raw.get('OV Jypesa', pd.Series(dtype=str)).fillna('').astype(str)
                df_entregas['entrega_texto'] = df_raw.get('FECHA HORACIO', pd.Series(dtype=str)).fillna('').astype(str)
                
                cita_series = df_raw.get('CITA', pd.Series(dtype=str)).fillna('').astype(str).str.strip()
                hora_series = df_raw.get('HORA', pd.Series(dtype=str)).fillna('').astype(str).str.strip()
                
                valores_nulos = ['', 'nan', '0', '0.0', '-', 'nat']
                citas_combinadas = []
                for c, h in zip(cita_series, hora_series):
                    es_cita_vacia = str(c).lower() in valores_nulos
                    es_hora_vacia = str(h).lower() in valores_nulos
                    
                    if es_cita_vacia and es_hora_vacia:
                        citas_combinadas.append("PENDIENTE DE CITA")
                    elif not es_cita_vacia and es_hora_vacia:
                        citas_combinadas.append(f"{c} - POR ASIGNAR")
                    elif es_cita_vacia and not es_hora_vacia:
                        citas_combinadas.append(f"PENDIENTE - {h}")
                    else:
                        citas_combinadas.append(f"{c} - {h}")
                        
                df_entregas['cita'] = citas_combinadas
                df_entregas['estatus'] = df_raw.get('ESTATUS', pd.Series(dtype=str)).fillna('').astype(str).str.upper().str.strip()
                df_entregas['estatus'] = df_entregas['estatus'].replace('NAN', 'PENDIENTE')
                
                df_entregas['tipo'] = df_raw.get('Unidad', pd.Series(dtype=str)).fillna('').astype(str).str.upper().str.strip()
                df_entregas['tipo'] = df_entregas['tipo'].str.replace('Ó', 'O') 
                
                df_entregas = df_entregas.replace(r'(?i)^nan$', '', regex=True)
                
                data_camion = df_entregas[df_entregas['tipo'] == 'CAMION'].to_dict('records')
                data_trailer = df_entregas[df_entregas['tipo'] == 'TRAILER'].to_dict('records')
            else:
                data_camion = []
                data_trailer = []
        
            # --- Lógica de Renderizado Condicional ---
            if st.session_state.tipo_entrega == 'C A M I O N':
                render_logistica_flow_responsive(data_camion)
            elif st.session_state.tipo_entrega == 'T R A I L E R':
                render_logistica_flow_responsive(data_trailer)
            elif st.session_state.tipo_entrega == 'C A L E N D A R I O':
                col_mes_sel, _ = st.columns([2, 4])
                with col_mes_sel:
                    opciones_meses = {"MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9}
                    
                    nombre_mes_actual = [k for k, v in opciones_meses.items() if v == st.session_state.mes_calendario][0]
                    
                    mes_seleccionado = st.selectbox(
                        "SELECCIONAR MES A VISUALIZAR", 
                        list(opciones_meses.keys()),
                        index=list(opciones_meses.keys()).index(nombre_mes_actual)
                    )
                    
                    if opciones_meses[mes_seleccionado] != st.session_state.mes_calendario:
                        st.session_state.mes_calendario = opciones_meses[mes_seleccionado]
                        st.rerun()
                    
                render_calendario_visual(data_camion, data_trailer, st.session_state.mes_calendario)
        
        
        # PESTAÑA 6: CONSIGNAS
        with tab_consignas:
            # --- CONFIGURACIÓN DE CONEXIÓN (GITHUB) ---
            GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
            REPO_NAME = "RH2026/nexion"
            FILE_PATH_CON = "consignas.csv"
            URL_CONSIGNAS = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH_CON}"
            
            @st.cache_data(ttl=600)
            def load_consignas():
                try:
                    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
                    df = pd.read_csv(URL_CONSIGNAS, storage_options=headers, low_memory=False)
                    df.columns = [c.strip() for c in df.columns]
                    
                    # Lógica de ordenamiento por fecha
                    if 'F.DOC' in df.columns:
                        df['F_TEMP'] = pd.to_datetime(df['F.DOC'], errors='coerce', dayfirst=True)
                        df = df.sort_values(by='F_TEMP', ascending=False).drop(columns=['F_TEMP'])
                    return df
                except Exception as e:
                    st.error(f"Error cargando consignas: {e}")
                    return None
            
            def render_expediente_chingon(df):
                df_clean = df.fillna('')
                data = df_clean.to_dict('records')
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <script src="https://cdn.tailwindcss.com"></script>
                    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
                    <style>
                        body {{ background-color: #384A52; color: #e2e8f0; font-family: 'Inter', sans-serif; margin: 0; padding: 10px 15px; }}
                        ::-webkit-scrollbar {{ width: 8px; height: 10px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.2); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ background: rgba(56, 189, 248, 0.6); border-radius: 10px; border: 2px solid #384A52; }}
                        ::-webkit-scrollbar-thumb:hover {{ background: rgba(0, 255, 170, 0.8); }}
                        .row-expediente {{ background-color: #263238; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; margin-bottom: 12px; padding: 18px 24px; transition: all 0.3s ease; width: 100%; box-sizing: border-box; }}
                        .row-expediente:hover {{ border-color: #00FFAA; background-color: #2d3b42; transform: scale(1.001); }}
                        .label-mini {{ font-size: 8px; text-transform: uppercase; color: rgba(255,255,255,0.6); font-weight: 800; letter-spacing: 1.5px; }}
                        .valor {{ font-size: 14px; font-weight: 700; color: #FFFFFF; }}
                        .highlight {{ color: #00FFAA; font-family: monospace; }}
                        .text-muted-claro {{ color: rgba(255,255,255,0.7); font-style: italic; }}
                    </style>
                </head>
                <body>
                    <div class="w-full">
                        {"".join([f'''
                        <div class="row-expediente">
                            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
                                <div>
                                    <div class="label-mini">Talon / Folio</div>
                                    <div class="valor highlight text-xl leading-none">{str(item.get('TALON', ''))}</div>
                                    <div class="text-[10px] text-blue-300 mt-1 opacity-90 italic">F. Doc: {str(item.get('F.DOC', ''))}</div>
                                </div>
                                <div class="md:border-l md:border-white/10 md:pl-6">
                                    <div class="label-mini">Destinatario</div>
                                    <div class="valor truncate text-sm uppercase">{str(item.get('DESTINATARIO', ''))[:45]}</div>
                                    <div class="text-[10px] text-muted-claro">{str(item.get('ORIGEN', ''))} → {str(item.get('DESTINO', ''))}</div>
                                </div>
                                <div class="md:border-l md:border-white/10 md:pl-6">
                                    <div class="label-mini">Resumen Financiero</div>
                                    <div class="flex justify-between items-center"><span class="label-mini">Bultos:</span> <span class="valor text-xs">{str(item.get('BULTOS', '0'))}</span></div>
                                    <div class="flex justify-between items-center"><span class="label-mini">Total Cargo:</span> <span class="valor text-emerald-400 text-sm">${str(item.get('TOTAL', '0'))}</span></div>
                                </div>
                                <div class="text-right md:border-l md:border-white/10 md:pl-6">
                                    <div class="label-mini">Estatus Entrega</div>
                                    <div class="valor text-sm {'text-orange-400' if not item.get('F.ENTREGA') else 'text-white'}">{str(item.get('F.ENTREGA', 'PENDIENTE'))}</div>
                                    <div class="text-[10px] text-blue-300 font-bold uppercase tracking-tighter">{str(item.get('QUIEN RECIBIO', ''))[:25]}</div>
                                </div>
                            </div>
                            <div class="mt-4 pt-3 border-t border-white/10 flex flex-col md:flex-row justify-between gap-4">
                                <div class="flex-1"><span class="label-mini text-blue-200">Domicilio:</span> <span class="text-[11px] text-white/80 ml-2">{str(item.get('DOMICILIO DEL DESTINATARIO', ''))}</span></div>
                                <div class="text-right flex gap-4">
                                    <div><span class="label-mini text-orange-200">Ref:</span> <span class="text-[11px] text-white/80 italic ml-1">{str(item.get('REFERENCIA', '--'))}</span></div>
                                    <div><span class="label-mini text-white/60">Notas:</span> <span class="text-[11px] text-white/70 italic ml-1">{str(item.get('OBSERVACION 1', '--'))}</span></div>
                                </div>
                            </div>
                        </div>
                        ''' for item in data])}
                    </div>
                </body>
                </html>
                """
                return components.html(html_content, height=1200, scrolling=True)
            
            # --- EJECUCIÓN PRINCIPAL ---
            df_consignas = load_consignas()
            
            if df_consignas is not None:
                st.markdown("<h3 style='text-align:center; color:white; font-size:18px; letter-spacing:4px; font-weight:900;'>CONSIGNAS BARCELO</h3>", unsafe_allow_html=True)
                
                # --- FILTROS LINEALES ---
                df_filtrado = df_consignas.copy()
                
                # Preparamos la columna de mes para el filtro
                df_filtrado['MES_TEMP'] = pd.to_datetime(df_filtrado['F.DOC'], errors='coerce', dayfirst=True).dt.strftime('%B')
                
                col1, col2, col3, col4 = st.columns(4)
                
                # Filtro Mes (Selectbox única)
                with col1:
                    meses_opciones = ["TODOS"] + sorted([m for m in df_filtrado['MES_TEMP'].dropna().unique()])
                    mes_sel = st.selectbox("Mes", meses_opciones)
                    
                # Filtros de búsqueda libre
                with col2:
                    cliente_busq = st.text_input("Buscar Cliente")
                with col3:
                    talon_busq = st.text_input("Buscar Talón")
                with col4:
                    ref_busqueda = st.text_input("Ref. (Observación 1)")
            
                # Aplicar filtros
                if mes_sel != "TODOS":
                    df_filtrado = df_filtrado[df_filtrado['MES_TEMP'] == mes_sel]
                if cliente_busq:
                    df_filtrado = df_filtrado[df_filtrado['DESTINATARIO'].astype(str).str.contains(cliente_busq, case=False, na=False)]
                if talon_busq:
                    df_filtrado = df_filtrado[df_filtrado['TALON'].astype(str).str.contains(talon_busq, case=False, na=False)]
                if ref_busqueda:
                    df_filtrado = df_filtrado[df_filtrado['OBSERVACION 1'].astype(str).str.contains(ref_busqueda, case=False, na=False)]
            
                # Renderizado final
                render_expediente_chingon(df_filtrado)
        
        # PESTAÑA 7: AMAZON
        with tab_amazon:
        # 1. CSS BLINDADO, RESPONSIVE Y SCROLL DINÁMICO
        # 1. CARGA Y LIMPIEZA DE DATOS (Tu lógica original intacta)
           
            # 1. CARGA Y LIMPIEZA DE DATOS (Tu lógica original intacta)
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "amazon.csv"
            API_URL = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
            headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
            
            try:
                response = requests.get(API_URL, headers=headers)
                if response.status_code == 200:
                    csv_bytes = base64.b64decode(response.json()['content'])
                    df = pd.read_csv(io.BytesIO(csv_bytes), engine='python')
                    df.columns = df.columns.str.strip()
                    df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
                    df = df.dropna(subset=['FECHA'])
                    cols_num = ['TOTAL', 'COSTO DE DISTRIBUCION POR CAJA', 'CAJAS', 'VALOR MERCANCIA', 'PORCENTAJE LOGISTICO']
                    for col in cols_num:
                        if col in df.columns:
                            df[col] = df[col].astype(str).str.replace(r'[\$,%, ]', '', regex=True).replace(['nan', '', 'None'], '0').astype(float)
                    df = df.sort_values(by='FECHA', ascending=False)
            
                    # --- 1. DASHBOARD PANTALLA ---
                    st.markdown("<h3 style='text-align:center; color:#eceff1; font-size:12px; letter-spacing:3px; font-weight:800; margin-bottom:15px;'>DASHBOARD OPERATIVO AMAZON</h3>", unsafe_allow_html=True)
                    
                    m1, m2, m3, m4 = st.columns(4)
                    card_style = "background:#1c252c; border-radius:8px; padding:15px 10px; border-bottom:3px solid #2ecc71; text-align:center;"
                    
                    m1.markdown(f'<div style="{card_style}"><div style="color:#90a4ae; font-size:9px; text-transform:uppercase;">Cajas Totales</div><div style="color:white; font-size:22px; font-weight:800;">{int(df["CAJAS"].sum()):,}</div></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div style="{card_style}"><div style="color:#90a4ae; font-size:9px; text-transform:uppercase;">Valor Carga</div><div style="color:white; font-size:22px; font-weight:800;">${df["VALOR MERCANCIA"].sum():,.0f}</div></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div style="{card_style}"><div style="color:#90a4ae; font-size:9px; text-transform:uppercase;">Costo Flete</div><div style="color:#2ecc71; font-size:22px; font-weight:800;">${df["TOTAL"].sum():,.0f}</div></div>', unsafe_allow_html=True)
                    m4.markdown(f'<div style="{card_style}"><div style="color:#90a4ae; font-size:9px; text-transform:uppercase;">% Logístico</div><div style="color:#2ecc71; font-size:22px; font-weight:800;">{df["PORCENTAJE LOGISTICO"].mean():.2f}%</div></div>', unsafe_allow_html=True)
            
                    # --- 2. FILTRO ---
                    st.divider()
                    df['MES'] = df['FECHA'].dt.strftime('%B %Y')
                    opciones_mes = ["TODO EL HISTÓRICO"] + list(df['MES'].unique())
                    mes_sel = st.selectbox("📅 FILTRAR POR MES:", opciones_mes)
                    df_mes = df if mes_sel == "TODO EL HISTÓRICO" else df[df['MES'] == mes_sel]
            
                    # --- 3. CONTENIDO HTML ---
                    data_dict = df_mes.fillna('').to_dict('records')
                    costo_log_real = df_mes["PORCENTAJE LOGISTICO"].mean()
                    fecha_reporte = datetime.now().strftime('%d/%m/%Y')
                    
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <script src="https://cdn.tailwindcss.com"></script>
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
                            body {{ background: transparent; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }}
                            #screen-view {{ display: block; }}
                            #print-view {{ display: none; }}
                            .scroller {{ height: 480px; overflow-y: auto; padding-right: 10px; margin-bottom: 10px; }}
                            ::-webkit-scrollbar {{ width: 6px; }}
                            ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                            .scroller:hover::-webkit-scrollbar-thumb {{ background: #2ecc71; }}
                            .card-row {{ background: #243038; border-radius: 12px; margin-bottom: 10px; padding: 15px 25px; display: grid; grid-template-columns: 1fr 1.5fr 1fr 1fr 1fr; gap: 15px; align-items: center; border: 1px solid rgba(255,255,255,0.05); }}
                            .label {{ font-size: 8px; color: #90a4ae; font-weight: 800; text-transform: uppercase; }}
                            .v-main {{ font-size: 14px; font-weight: 800; color: #2ecc71; }}
                            .v-txt {{ font-size: 12px; font-weight: 600; color: #ffffff; }}
                            .btn-print-master {{ background-color: #243038; color: #ffffff; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 6px 20px; font-size: 12px; font-weight: 400; cursor: pointer; width: 100%; transition: all 0.3s ease; display: flex; justify-content: center; align-items: center; text-transform: uppercase; letter-spacing: 1px; }}
                            .btn-print-master:hover {{ background-color: #00A0A8; color: #ffffff; border-color: #00A0A8; }}
                            @media print {{ @page {{ size: A4; margin: 10mm; }} #screen-view {{ display: none !important; }} #print-view {{ display: block !important; color: black !important; background: white !important; }} table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }} th {{ background: #f0f0f0 !important; border: 1px solid #000; padding: 6px; font-size: 8px; text-transform: uppercase; }} td {{ border: 1px solid #ddd; padding: 6px; font-size: 8px; }} .header-print {{ border-bottom: 3px solid #000; padding-bottom: 8px; margin-bottom: 15px; }} .resumen-caja {{ border: 1.5px solid #000; padding: 10px; margin: 15px 0; font-size: 11px; }} }}
                        </style>
                    </head>
                    <body>
                        <div id="screen-view">
                            <div class="scroller">
                                {"".join([f'''
                                <div class="card-row">
                                    <div>
                                        <div class="label">FOLIO</div>
                                        <div class="v-main">{item.get('IDENTIFICADOR ENVIO', 'N/A')}</div>
                                        <div style="font-size:10px; color:#94a3b8;">{item.get('FECHA').strftime('%d/%m/%Y') if hasattr(item.get('FECHA'), 'strftime') else item.get('FECHA')}</div>
                                    </div>
                                    <div style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 15px;">
                                        <div class="label">DESTINO / ESTATUS</div>
                                        <div class="v-txt">{item.get('AMAZON', 'AMAZON')}</div>
                                        <div style="font-size:10px; color:{'#f39c12' if item.get('ESTATUS') == 'PENDIENTE' else '#2ecc71' if item.get('ESTATUS') == 'ENTREGADA' else '#3498db'};">
                                            {item.get('ESTATUS', 'PROCESADO')}
                                        </div>
                                    </div>
                                    <div style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 15px;">
                                        <div class="label">BULTOS / COSTO CAJA</div>
                                        <div class="v-txt">{int(item.get('CAJAS', 0))} BULTOS</div>
                                        <div style="font-size:10px; color:#94a3b8;">$ {float(item.get('COSTO DE DISTRIBUCION POR CAJA', 0)):,.2f} c/u</div>
                                    </div>
                                    <div style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 15px;">
                                        <div class="label">VALOR CARGA / KPI</div>
                                        <div style="color:white; font-size:11px;">$ {float(item.get('VALOR MERCANCIA', 0)):,.0f}</div>
                                        <div style="color:#2ecc71; font-weight:800; font-size:12px;">{float(item.get('PORCENTAJE LOGISTICO', 0)):,.2f}%</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div class="label">TOTAL FLETE</div>
                                        <div style="color:white; font-size:16px; font-weight:900;">$ {float(item.get('TOTAL', 0)):,.2f}</div>
                                    </div>
                                </div>
                                ''' for item in data_dict])}
                            </div>
                            <div style="padding: 10px 0;">
                                <button class="btn-print-master" onclick="window.print()">GENERAR REPORTE DE OPERACIÓN (PDF)</button>
                            </div>
                        </div>
                        <div id="print-view">
                            <div class="header-print">
                                <table style="border:none;">
                                    <tr style="border:none;">
                                        <td style="border:none; width:65%;">
                                            <h1 style="margin:0; font-size:16px; font-weight:900;">JABONES Y PRODUCTOS ESPECIALIZADOS</h1>
                                            <p style="margin:0; font-size:11px; color:#444;">Distribución y Logística Nacional | JYPESA 2026</p>
                                        </td>
                                        <td style="border:none; text-align:right; font-size:10px;">
                                            <b>FECHA EMISIÓN:</b> {fecha_reporte}<br>
                                            <b>PERIODO:</b> {mes_sel.upper()}<br>
                                            <b>RESULTADO:</b> {"DENTRO DE PARÁMETROS" if costo_log_real <= 7.5 else "FUERA DE PARÁMETROS"}
                                        </td>
                                    </tr>
                                </table>
                            </div>
                            <h2 style="text-align:center; text-decoration:underline; font-size:16px; margin: 15px 0;">REPORTE OPERATIVO DE CONSIGNAS AMAZON</h2>
                            <div class="resumen-caja">
                                <b>RESUMEN EJECUTIVO:</b> El KPI logístico promedio del periodo es de <b>{costo_log_real:.2f}%</b> contra un target objetivo del <b>7.50%</b>. 
                                Se movilizaron un total de <b>{int(df_mes["CAJAS"].sum()):,}</b> cajas con un valor de mercancía de <b>${df_mes["VALOR MERCANCIA"].sum():,.2f}</b>.
                            </div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>FOLIO</th>
                                        <th>FECHA</th>
                                        <th>DESTINATARIO</th>
                                        <th>ESTATUS</th>
                                        <th>BULTOS</th>
                                        <th>$ ECaja</th>
                                        <th>TOTAL FLETE</th>
                                        <th>KPI %</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join([f'''
                                    <tr>
                                        <td style="font-weight:bold;">{item.get('IDENTIFICADOR ENVIO')}</td>
                                        <td>{item.get('FECHA').strftime('%d/%m/%Y') if hasattr(item.get('FECHA'), 'strftime') else item.get('FECHA')}</td>
                                        <td>{item.get('AMAZON')}</td>
                                        <td>{item.get('ESTATUS')}</td>
                                        <td style="text-align:center;">{int(item.get('CAJAS', 0))}</td>
                                        <td style="text-align:right;">$ {float(item.get('COSTO DE DISTRIBUCION POR CAJA', 0)):,.2f}</td>
                                        <td style="text-align:right;">${float(item.get('TOTAL', 0)):,.2f}</td>
                                        <td style="text-align:center; font-weight:bold;">{float(item.get('PORCENTAJE LOGISTICO', 0)):,.2f}%</td>
                                    </tr>
                                    ''' for item in data_dict])}
                                </tbody>
                            </table>
                            <div style="margin-top: 60px; display: flex; justify-content: space-between;">
                                <div style="width: 220px; border-top: 1.5px solid #000; text-align: center; font-size: 10px;">
                                    <br><b>Rigoberto Hernández</b><br>Coordinador Logística Nacional
                                </div>
                                <div style="width: 220px; border-top: 1.5px solid #000; text-align: center; font-size: 10px;">
                                    <br><b>Dirección General</b><br>Autorización JYPESA
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    components.html(html_content, height=650, scrolling=False)
                else:
                    st.error("Error al conectar con GitHub.")
            except Exception as e:
                st.error(f"Error crítico: {e}")
        
        with tab_pedidos:
            # ── 1. CONFIGURACIÓN Y PERMISOS ──
            TOKEN = st.secrets.get("GITHUB_TOKEN", None)
            REPO_NAME = "RH2026/nexion"
            FILE_PATH = "pedidos.csv"
            tz_gdl = pytz.timezone('America/Mexico_City')
            
            current_user = st.session_state.get("usuario_activo", "UNKNOWN")
            
            # 🔒 CONTROL DE ACCESO ABSOLUTO: Solo tú puedes editar
            AUTHORIZED_EDITORS = ["Rigoberto"]
            puede_editar = current_user in AUTHORIZED_EDITORS
            
            # LISTA CON ICONOS PARA LA VISTA DE LA APP
            OPCIONES_ESTATUS = ["🆕 PENDIENTE", "🛑 DETENIDO", "✅ ENVIADO", "❌ CANCELADO"]
            OPCIONES_PAQUETERIA = ["", "MAS APRISA", "CANCELADO", "TRES GUERRAS", "CLIENTE PASA", "LOCAL", "CASTORES", "ONE", "PAQMEX", "TAMAZULA", "FLETES REGRESO", "TIBSA", "KORA", "SANCHEZ", "TINY", "POTOSINOS", "FEDEX", "EXPORTACION", "CEDIS CANCUN", "CEDIS MONTERREY", "SOLO FACTURA", "DETENIDA"]
            OPCIONES_SURTIDOR = ["", "MARCOS", "SANDRA", "YAZMIN", "KEVIN", "FELIX", "MARISOL", "CANCELADO", "LOCAL", "SOLO FACTURA", "CEDIS", "EXPORTACION"]
            
            # Función auxiliar global para limpiar textos antes de exportar o guardar
            def quitar_iconos(val):
                return str(val).replace("🆕 ", "").replace("🛑 ", "").replace("✅ ", "").replace("❌ ", "").strip()
            
            # Variables directas (ya no hay bloqueos de concurrencia)
            puede_editar_efectivo = puede_editar
            bloqueado_por_otro = False
            
            st.markdown(f"### PANEL DE ENVIOS DIARIO {'(MODO EDICIÓN)' if puede_editar_efectivo else '(MODO LECTURA)'}")
            
            # ── 2. LÓGICA DE CARGA ──
            def get_data_nexion_brute():
                if 'df_pedidos' not in st.session_state or st.session_state.get('force_reload', False):
                    try:
                        g = Github(TOKEN)
                        repo = g.get_repo(REPO_NAME)
                        contents = repo.get_contents(FILE_PATH, ref="main")
                        df = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
                        
                        columnas_lectura = ["NO CLIENTE", "FACTURA", "NOMBRE DEL CLIENTE", "DESTINO", "PROGRAMACION", "ESTATUS"]
                        columnas_nuevas = ["FECHA DE ENVIO", "SURTIDOR", "CAJAS", "PAQUETERIA", "HORA PROGRAMADA", "HORA REAL", "INCIDENCIA"]
                        all_cols = columnas_lectura + columnas_nuevas
                        
                        for col in all_cols:
                            if col not in df.columns:
                                df[col] = ""
                            else:
                                df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None'], '').str.strip().str.upper()
                        
                        if "ESTATUS" in df.columns:
                            def poner_iconos(val):
                                if "PENDIENTE" in val: return "🆕 PENDIENTE"
                                if "DETENIDO" in val: return "🛑 DETENIDO"
                                if "ENVIADO" in val: return "✅ ENVIADO"
                                if "CANCELADO" in val: return "❌ CANCELADO"
                                return "🆕 PENDIENTE"
                            df['ESTATUS'] = df['ESTATUS'].apply(poner_iconos)
                        
                        st.session_state.df_pedidos = df[all_cols]
                        st.session_state.force_reload = False 
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
                        return pd.DataFrame()
                return st.session_state.df_pedidos
            
            # ── 3. BOTÓN RECARGAR ──
            if st.button("CLICK PARA OBTENER DATOS ACTUALIZADOS", use_container_width=True):
                if 'df_pedidos' in st.session_state: del st.session_state.df_pedidos
                st.session_state.force_reload = True
                st.cache_data.clear()
                st.rerun()
            
            st.markdown("---")
            
            # ── 4. FILTROS Y TABLA ──
            df_actual = get_data_nexion_brute()
            
            if not df_actual.empty:
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                
                with col_f1:
                    f_cliente = st.text_input("Filtrar No Cliente", value="", placeholder="Ej: 1234").upper()
                with col_f2:
                    f_factura = st.text_input("Filtrar Factura", value="", placeholder="Ej: F-99").upper()
                with col_f3:
                    f_prog = st.text_input("Filtrar Programación", value="", placeholder="Ej: 2024-05-15").upper()
                with col_f4:
                    f_estatus = st.selectbox("Filtrar Estatus", ["TODOS"] + OPCIONES_ESTATUS)
                
                df_filtrado = df_actual.copy()
                if f_cliente:
                    df_filtrado = df_filtrado[df_filtrado["NO CLIENTE"].str.contains(f_cliente, na=False)]
                if f_factura:
                    df_filtrado = df_filtrado[df_filtrado["FACTURA"].str.contains(f_factura, na=False)]
                if f_prog:
                    df_filtrado = df_filtrado[df_filtrado["PROGRAMACION"].str.contains(f_prog, na=False)]
                if f_estatus != "TODOS":
                    df_filtrado = df_filtrado[df_filtrado["ESTATUS"] == f_estatus]
                
                with st.form("nexion_editor_form_safe"):

                    # CSS para forzar el hover sólido cyan/esmeralda de la foto
                    st.markdown("""
                    <style>
                    /* ESTADO NORMAL: Gris oscuro con borde sutil */
                    div[data-testid="stFormSubmitButton"] button {
                        background-color: #506874 !important; 
                        border: 1px solid rgba(255, 255, 255, 0.2) !important;
                        transition: all 0.2s ease-in-out !important;
                        box-shadow: none !important;
                    }
                    div[data-testid="stFormSubmitButton"] button p {
                        color: #ffffff !important;
                        font-weight: 600 !important;
                    }
                    
                    /* ESTADO HOVER: Fondo relleno sólido exacto como la foto */
                    div[data-testid="stFormSubmitButton"] button:hover {
                        background-color: #00a896 !important; /* Tono cyan/esmeralda sólido */
                        border-color: #00a896 !important;
                    }
                    div[data-testid="stFormSubmitButton"] button:hover p {
                        color: #ffffff !important; /* Letra blanca pura */
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    edited_df = st.data_editor(
                        df_filtrado,
                        use_container_width=True,
                        hide_index=True,
                        height=900,
                        column_config={
                            "ESTATUS": st.column_config.SelectboxColumn("ESTATUS", options=OPCIONES_ESTATUS, width="medium", disabled=not puede_editar_efectivo),
                            "SURTIDOR": st.column_config.SelectboxColumn("SURTIDOR", options=OPCIONES_SURTIDOR, width="medium", disabled=not puede_editar_efectivo),
                            "CAJAS": st.column_config.TextColumn("CAJAS", width="small", disabled=not puede_editar_efectivo),
                            "PAQUETERIA": st.column_config.SelectboxColumn("PAQUETERIA", options=OPCIONES_PAQUETERIA, width="medium", disabled=not puede_editar_efectivo),
                            "FECHA DE ENVIO": st.column_config.TextColumn("FECHA DE ENVIO", width="small", disabled=not puede_editar_efectivo),
                            "HORA PROGRAMADA": st.column_config.TextColumn("HORA PROGRAMADA", width="medium", disabled=not puede_editar_efectivo),
                            "HORA REAL": st.column_config.TextColumn("HORA REAL", width="medium", disabled=not puede_editar_efectivo),
                            "INCIDENCIA": st.column_config.TextColumn("INCIDENCIA", width="large", disabled=not puede_editar_efectivo),
                            "NOMBRE DEL CLIENTE": st.column_config.TextColumn("NOMBRE DEL CLIENTE", width="medium", disabled=True),
                            "NO CLIENTE": st.column_config.TextColumn(disabled=True),
                            "FACTURA": st.column_config.TextColumn(disabled=True),
                            "DESTINO": st.column_config.TextColumn(disabled=True),
                            "PROGRAMACION": st.column_config.TextColumn("PROGRAMACION", width="small", disabled=True),
                        }
                    )
                    
                    btn_label = "ACTUALIZAR EN LA NUBE" if puede_editar_efectivo else "🔒 MODO LECTURA"
                    submit_button = st.form_submit_button(btn_label, use_container_width=True, disabled=not puede_editar_efectivo)
                
                # ── BOTÓN DE DESCARGA (SOLO VISIBLE SI TIENES PERMISO DE EDICIÓN) ──
                if puede_editar_efectivo:
                    st.markdown("<br>", unsafe_allow_html=True)
                    df_descarga_limpio = df_filtrado.copy()
                    if 'ESTATUS' in df_descarga_limpio.columns:
                        df_descarga_limpio['ESTATUS'] = df_descarga_limpio['ESTATUS'].apply(quitar_iconos)
                    
                    csv_descarga = df_descarga_limpio.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 DESCARGAR TABLA ACTUAL EN CSV",
                        data=csv_descarga,
                        file_name=f"pedidos_nexion_{datetime.now(tz_gdl).strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                # ── 5. LÓGICA DE ACTUALIZACIÓN LIMPIA ──
                if puede_editar_efectivo and submit_button:
                    with st.status("Sincronizando...", expanded=True) as status:
                        try:
                            df_final_a_subir = st.session_state.df_pedidos.copy()
                            df_final_a_subir.update(edited_df)
                            
                            df_limpio_git = df_final_a_subir.copy()
                            df_limpio_git['ESTATUS'] = df_limpio_git['ESTATUS'].apply(quitar_iconos)
                            
                            g = Github(TOKEN)
                            repo = g.get_repo(REPO_NAME)
                            csv_string = df_limpio_git.to_csv(index=False)
                            contents = repo.get_contents(FILE_PATH)
                            hora_local = datetime.now(tz_gdl).strftime('%H:%M:%S')
                            
                            # Guardar base de datos actualizada
                            repo.update_file(path=FILE_PATH, message=f"UPDATE // {hora_local}", content=csv_string, sha=contents.sha)
                            
                            st.session_state.df_pedidos = df_final_a_subir
                            status.update(label="¡Guardado Exitosamente!", state="complete", expanded=False)
                            st.toast("GitHub Actualizado Exitosamente", icon="✅")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")
        
        
        
        # NUEVA PESTAÑA SOLO PARA TI
        if es_admin:
            with tab_admin:
                st.markdown(f"""
                    <div style='display:flex;align-items:center;gap:10px;margin:20px 0;'>
                        <div style='background:#FF4B4B;width:5px;height:25px;border-radius:2px;box-shadow:0 0 10px #FF4B4B;'></div>
                        <span style='color:white;font-size:18px;font-weight:500;letter-spacing:2px;'>NEXION SENSITIVE DATA - ADMIN ONLY</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # --- 🕵️ MONITOR DE ACTIVIDAD (LOGS) ---
                try:
                    # 1. Cargamos el archivo de logs (Asegúrate de haber guardado el CSV antes)
                    df_logs = pd.read_csv("log_accesos.csv")
                    
                    # 2. Inyectamos el estilo hover para los logs
                    st.markdown(f"<style>.card-log {{ transition: all 0.3s ease; cursor: pointer; }} .card-log:hover {{ transform: translateX(5px); border-color: #FF4B4B !important; background: rgba(255, 75, 75, 0.05) !important; }}</style>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # 3. Mostramos los últimos 10 accesos con estilo pro
                    # Ponemos los más nuevos arriba (.iloc[::-1])
                    for index, row in df_logs.iloc[::-1].head(10).iterrows():
                        st.markdown(f"""
                            <div class='card-log' style='background:rgba(30,39,46,0.5); border:1px solid rgba(255,255,255,0.05); border-left:4px solid #FF4B4B; border-radius:8px; padding:10px 20px; margin-bottom:8px; display:flex; align-items:center; justify-content:space-between;'>
                                <div style='flex:1;'>
                                    <span style='color:rgba(255,255,255,0.4); font-size:8px; font-weight:800; letter-spacing:1px; text-transform:uppercase;'>OPERADOR</span><br>
                                    <b style='font-size:14px; color:white; letter-spacing:0.5px;'>{row['Usuario'].upper()}</b>
                                </div>
                                <div style='flex:2; padding-left:20px; border-left:1px solid rgba(255,255,255,0.08);'>
                                    <span style='color:rgba(255,255,255,0.4); font-size:8px; font-weight:800; letter-spacing:1px; text-transform:uppercase;'>FECHA Y HORA DE ACCESO</span><br>
                                    <span style='font-size:12px; color:#FF4B4B; font-family:monospace; font-weight:700;'>{row['Fecha/Hora']}</span>
                                </div>
                                <div style='flex:0.5; text-align:right;'>
                                    <span style='background:rgba(0,255,170,0.1); color:#00FFAA; padding:3px 8px; border-radius:4px; font-size:8px; font-weight:800;'>ENTRY OK</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.warning("Esperando el primer registro de acceso para mostrar el historial...")


if __name__ == "__main__":
    main()

# ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
st.markdown(
    f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
