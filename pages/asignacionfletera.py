import base64
from datetime import datetime, timedelta
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
import pytz
from auth import exigir_autenticacion

exigir_autenticacion("asignacionfletera")

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Almacén Historial",
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

/* SCROLLBAR CHINGÓN Y ELEGANTE */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: {vars_css['bg']};
}}
::-webkit-scrollbar-thumb {{
    background: {vars_css['border']};
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: #00A3A3;
}}

/* CONTENEDOR CON SCROLL PARA LA LISTA DE ALMACÉN */
.scroll-container-almacen {{
    max-height: 70vh;
    overflow-y: auto;
    padding-right: 5px;
    margin-bottom: 20px;
}}

/* ELIMINAR ESPACIOS EXCESIVOS ENTRE ELEMENTOS DE STREAMLIT EN LA LISTA */
div[data-testid="stVerticalBlock"] {{
    gap: 0.2rem !important;
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
    height: 30px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
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
    st.session_state.pagina_destino = "pages/asignacionfletera.py"
    st.switch_page("pages/log.py")

def verificar_permiso_pagina(modulo, submodulo=None):
    permisos = st.session_state.get("permisos", {})
    if st.session_state.get("usuario_activo", "").upper() == "RIGOBERTO":
        return True
        
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
                st.switch_page("dashboard.py")
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
                st.switch_page("dashboard.py")
        st.stop()

verificar_permiso_pagina("CARGAR DATOS", "ASIGNAR FLETERA")

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
    st.session_state.menu_main = "REPORTES"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "ENVIOS"
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
                    res_ops = df_matriz_fresco[mask_ops].copy()

            res_t1 = pd.DataFrame()
            try:
                df_t1_temp = pd.read_excel("T1.xlsx") 
                df_t1_temp.columns = df_t1_temp.columns.str.strip().str.upper()
                
                cols_t1 = [c for c in ["OBSERVACION 1", "TALON", "DESTINATARIO", "DESTINO"] if c in df_t1_temp.columns]
                
                if cols_t1:
                    mask_t1 = df_t1_temp[cols_t1].astype(str).apply(
                        lambda x: x.str.contains(query, case=False, na=False)
                    ).any(axis=1)
                    match_t1 = df_t1_temp[mask_t1].copy()
                    
                    if not match_t1.empty:
                        match_t1 = match_t1.rename(columns={
                            "TALON": "NÚMERO DE GUÍA",
                            "OBSERVACION 1": "NÚMERO DE PEDIDO",
                            "DESTINATARIO": "NOMBRE DEL CLIENTE",
                            "SUBTOTAL": "COSTO DE LA GUÍA",
                            "F.DOC": "FECHA DE ENVÍO",
                            "BULTOS": "CANTIDAD DE CAJAS"
                        })
                        match_t1["FLETERA"] = "TRES GUERRAS"
                        res_t1 = match_t1
            except Exception:
                pass

            if not res_ops.empty and not res_t1.empty:
                for idx, row in res_ops.iterrows():
                    guia_actual = str(row.get("NÚMERO DE GUÍA", "")).strip()
                    if guia_actual in ["", "nan", "0", "None"]:
                        pedido_global = str(row.get("NÚMERO DE PEDIDO", "")).strip()
                        match_en_t1 = res_t1[res_t1["NÚMERO DE PEDIDO"].astype(str).str.strip() == pedido_global]
                        if not match_en_t1.empty:
                            res_ops.loc[idx, "NÚMERO DE GUÍA"] = match_en_t1.iloc[0].get("NÚMERO DE GUÍA", guia_actual)
                            res_ops.loc[idx, "FLETERA"] = match_en_t1.iloc[0].get("FLETERA", "TRES GUERRAS")
                            if "COSTO DE LA GUÍA" in match_en_t1.columns and pd.notna(match_en_t1.iloc[0].get("COSTO DE LA GUÍA")):
                                res_ops.loc[idx, "COSTO DE LA GUÍA"] = match_en_t1.iloc[0].get("COSTO DE LA GUÍA")

            res_inv = pd.DataFrame()
            if res_ops.empty and res_t1.empty:
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
            elif not res_t1.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "OPERACION" 
                st.session_state.resultado_busqueda = res_t1
            elif not res_inv.empty:
                st.session_state.busqueda_activa = True
                st.session_state.tipo_resultado = "INVENTARIO"
                st.session_state.resultado_busqueda = res_inv
            else:
                st.session_state.busqueda_activa = False
                st.session_state.resultado_busqueda = None
                st.toast("Sin resultados: No se encontró en Matriz Global ni en T1", icon="⚠️")

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
                    st.session_state.menu_main = "DASHBOARD"
                    st.session_state.menu_sub = "GENERAL"
                    st.session_state.busqueda_activa = False
                    st.switch_page("dashboard.py")
        
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
                    opciones_ent_posibles = ["AGC", "AMAZON", "BARCELO", "NACIONAL"]
                    opciones_ent = [s for s in opciones_ent_posibles if permisos.get(s, False)]
                    for s in opciones_ent:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_ent_{s}2"):
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
                    opciones_hub_posibles = ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "ESCANEAR QR", "HERRAMIENTAS"]
                    opciones_hub = [s for s in opciones_hub_posibles if permisos.get(s, False)]
                    for s in opciones_hub:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_hub_{s}2"):
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

                tarjeta_unica_html = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 20px 25px; border-radius: 8px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;"><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #38bdf8; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #38bdf8;"></div><div style="font-size: 9px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;">ENVÍO</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('FECHA DE ENVÍO','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #38bdf8; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #a855f7; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #a855f7;"></div><div style="font-size: 9px; font-weight: 800; color: #a855f7; letter-spacing: 1px;">GUÍA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{n_guia if tiene_guia else 'EN PROCESO'}</div></div><div style="flex-grow: 1; height: 2px; background: #a855f7; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #eab308; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #eab308;"></div><div style="font-size: 9px; font-weight: 800; color: #eab308; letter-spacing: 1px;">PROMESA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('PROMESA DE ENTREGA','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #00FFAA; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: {status_color}; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px {status_color};"></div><div style="font-size: 9px; font-weight: 800; color: {status_color}; letter-spacing: 1px;">ENTREGA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{f_entrega_val}</div></div></div><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;"><div style="flex: 1.2; min-width: 200px;"><div style="color: {accent_color}; font-size: 16px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">{envio.get('FLETERA','N/A')}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">TALÓN / FOLIO</div><div style="color: {accent_color}; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{n_guia}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">REF / PEDIDO: <span style="color: white; font-size: 13px; font-weight: 700;">{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div></div><div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / CLIENTE</div><div style="color: white; font-weight: 800; font-size: 13px; text-transform: uppercase; line-height: 1.3; margin-top: 2px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div><div style="font-size: 11px; color: {accent_color}; margin-top: 4px; font-weight: 600;">📍 GDL → {envio.get('DESTINO','N/A')}</div></div><div style="flex: 1.2; min-width: 150px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN CARGA</div><div style="color: white; font-weight: 700; font-size: 11px; margin-top: 2px;">BULTOS: <span style="color: {accent_color};">{envio.get('CANTIDAD DE CAJAS','0')}</span></div><div style="color: {accent_color}; font-weight: 800; font-size: 13px; margin-top: 2px;">$ {envio.get('COSTO DE LA GUÍA','0.00')}</div></div><div style="text-align: right; min-width: 130px;"><span style="background-color: {status_color}15; color: {status_color}; padding: 5px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; border: 1px solid {status_color}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">ESTATUS: {status_text}</span></div></div></div>"""
                st.markdown(tarjeta_unica_html, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'><div style='background: {azul_premium}; width: 5px; height: 22px; border-radius: 3px; box-shadow: 0 0 10px {azul_premium};'></div><span style='color: white; font-size: 15px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;'>MULTIPLE MATCHES DETECTED <span style='color: {azul_premium};'>({total})</span></span></div>", unsafe_allow_html=True)
                st.markdown(f"<style>.card-nexion {{ transition: all 0.3s ease !important; cursor: pointer; }} .card-nexion:hover {{ transform: translateX(10px); border-color: {azul_premium} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(0, 212, 255, 0.2); }}</style>", unsafe_allow_html=True)

                for _, d in resultados.iterrows():
                    status_text = d["COMENTARIOS"] if "COMENTARIOS" in d and pd.notna(d.get("COMENTARIOS")) else "OK"
                    st.markdown(f"<div class='card-nexion' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {azul_premium};border-radius:12px;padding:18px 25px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>PEDIDO / FACTURA</span><br><b style='font-size:18px;color:{azul_premium};letter-spacing:0.5px;'># {d.get('NÚMERO DE PEDIDO','')}</b><br><span style='font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;'>Envío: {d.get('FECHA DE ENVÍO','')}</span></div><div style='flex:2.5;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CLIENTE / DESTINO</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('NOMBRE DEL CLIENTE','')}</b><br><i style='font-size:11px;color:rgba(255,255,255,0.5);font-style:normal;font-weight:600;'>{d.get('DESTINO','')}</i></div><div style='flex:1.8;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>TRANSPORTE Y GUÍA</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('FLETERA', d.get('TRANSPORTE', 'LOGÍSTICA'))}</b><br><span style='font-size:12px;color:{azul_premium};font-weight:700;font-family:monospace;'>{d.get('NÚMERO DE GUÍA','')}</span></div><div style='flex:1.2;text-align:right;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>ESTATUS ENTREGA</span><br><b style='font-size:14px;color:{azul_premium};'>{d.get('FECHA DE ENTREGA REAL','')}</b><br><span style='font-size:10px;color:white;font-weight:800;text-transform:uppercase;opacity:0.8;'>{status_text}</span></div></div>", unsafe_allow_html=True)

        st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)

# ==========================================
# 5. RENDER DE HISTORIAL COMPACTO SIN ESPACIOS VERTICALES
# ==========================================
def render_historial_almacen(data):
    if not data:
        st.markdown("""
            <div style="background-color: #212529; border: 1px solid #ff4d4d; border-radius: 6px; padding: 14px 18px; font-family: 'Inter', sans-serif; box-sizing: border-box; width: 100%;">
                <div style="font-size: 10px; color: #ff4d4d; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px;">AVISO DEL SISTEMA: SIN REGISTROS</div>
                <div style="font-size: 13px; color: #d1d5db; font-weight: 500;">No se encontraron facturas en la matriz de facturación para los filtros seleccionados.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    st.markdown('<p style="color:#FFFFFF; font-weight:800; letter-spacing:2px; font-size:12px; margin-bottom:12px;">HISTORIAL DE ALMACÉN // CONTROL DE FACTURAS</p>', unsafe_allow_html=True)

    opciones_estatus_posibles = [
        "ENVIADA", 
        "CANCELADA", 
        "DETENIDA", 
        "DUPLICADA", 
        "CEDIS", 
        "SOLO FACTURA", 
        "NO ENTREGADA", 
        "MOSTRADOR", 
        "EXPORTACION"
    ]

    st.markdown('<div class="scroll-container-almacen">', unsafe_allow_html=True)

    for idx, item in enumerate(data):
        key_estatus = f"estatus_sel_{idx}_{item['factura']}"
        
        if key_estatus not in st.session_state:
            estatus_base = "ENVIADA" if item.get('fecha_envio') else "PENDIENTE"
            st.session_state[key_estatus] = estatus_base

        estatus_val = st.session_state[key_estatus]
        
        if estatus_val == "ENVIADA":
            color_borde = "#10b981"
            color_texto_estatus = "#34d399"
        elif estatus_val in ["CANCELADA", "NO ENTREGADA"]:
            color_borde = "#ef4444"
            color_texto_estatus = "#f87171"
        elif estatus_val in ["DETENIDA", "SOLO FACTURA"]:
            color_borde = "#f59e0b"
            color_texto_estatus = "#fbbf24"
        elif estatus_val == "DUPLICADA":
            color_borde = "#a855f7"
            color_texto_estatus = "#c084fc"
        elif estatus_val in ["CEDIS", "MOSTRADOR", "EXPORTACION"]:
            color_borde = "#38bdf8"
            color_texto_estatus = "#7dd3fc"
        else:
            color_borde = "#64748b"
            color_texto_estatus = "#94a3b8"

        with st.container():
            col_tarjeta, col_select = st.columns([8.2, 1.8], vertical_alignment="center")

            with col_tarjeta:
                fecha_envio_display = item['fecha_envio'] if item['fecha_envio'] else 'SIN F. ENVÍO'
                transporte_display = item['transporte'] if item['transporte'] else 'S/T'
                
                st.markdown(f"""
                <div style="background-color: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-left: 5px solid {color_borde}; border-radius: 6px; padding: 4px 12px; font-family: 'Inter', sans-serif; width: 100%; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; height: 30px;">
                    <div style="display: flex; align-items: center; gap: 20px; font-size: 11px; width: 100%;">
                        <b style="color: white; font-style: italic; font-size: 12px; white-space: nowrap;">#{item['factura']}</b>
                        <span style="color: #7dd3fc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-grow: 1;">{item['nombre_extran'] if item['nombre_extran'] else 'N/A'}</span>
                        <span style="color: #fde047; font-weight: bold; white-space: nowrap; margin-left: auto; padding-right: 15px;">{transporte_display}</span>
                        <span style="color: #38bdf8; font-weight: 700; font-size: 10px; white-space: nowrap;">📅 {fecha_envio_display}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_select:
                index_actual = opciones_estatus_posibles.index(estatus_val) if estatus_val in opciones_estatus_posibles else 0
                
                st.markdown("""
                <style>
                div[data-baseweb="select"] > div {
                    min-height: 30px !important;
                    height: 30px !important;
                    font-size: 9px !important;
                    padding: 0px 4px !important;
                    background-color: #2B343B !important;
                    color: #ffffff !important;
                    border: 1px solid #4B5D67 !important;
                    border-radius: 6px !important;
                }
                div[data-baseweb="select"] span {
                    line-height: 30px !important;
                    font-size: 9px !important;
                    font-weight: 700 !important;
                }
                </style>
                """, unsafe_allow_html=True)

                nuevo_estatus = st.selectbox(
                    "Estatus",
                    opciones_estatus_posibles,
                    index=index_actual,
                    key=f"sel_estatus_{idx}_{item['factura']}",
                    label_visibility="collapsed"
                )
                if nuevo_estatus != estatus_val:
                    st.session_state[key_estatus] = nuevo_estatus
                    st.rerun()

            # Espacio vertical reducido al mínimo absoluto (3px) para que no queden huecos
            st.markdown("<div style='margin-bottom: 3px;'></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    # ── BOTÓN DE ACTUALIZACIÓN RÁPIDA ────────────────────────
    col_titulo, col_btn_refrescar = st.columns([4, 1.2], vertical_alignment="center")
    with col_titulo:
        st.markdown("""
            <div style='text-align:left; margin-top:15px; margin-bottom:10px;'>
                <span style='color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;'>
                    HISTORIAL DE ALMACÉN // FACTURACIÓN & CRUCE DE ENVÍOS
                </span>
            </div>
        """, unsafe_allow_html=True)
    with col_btn_refrescar:
        if st.button("ACTUALIZAR DATOS", key="btn_refrescar_almacen", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    
    current_t = int(time.time() * 1000)
    URL_FACTURACION = f"https://raw.githubusercontent.com/{REPO_NAME}/main/facturacion.csv?_t={current_t}"
    URL_ENVIOS = f"https://raw.githubusercontent.com/{REPO_NAME}/main/envios.csv?_t={current_t}"

    @st.cache_data(ttl=60)
    def cargar_csv_remoto(url, token):
        headers = {"Authorization": f"token {token}"} if token else {}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text), encoding="utf-8-sig")
        return pd.DataFrame()

    df_fact = cargar_csv_remoto(URL_FACTURACION, TOKEN)
    df_envios = cargar_csv_remoto(URL_ENVIOS, TOKEN)

    if not df_fact.empty:
        df_fact.columns = df_fact.columns.str.strip()

        df_proc = pd.DataFrame()
        df_proc['factura'] = df_fact.get('Factura', df_fact.get('FACTURA', pd.Series(dtype=str))).fillna('').astype(str).str.strip()
        df_proc['nombre_extran'] = df_fact.get('Nombre_Extran', df_fact.get('NOMBRE_EXTRAN', pd.Series(dtype=str))).fillna('').astype(str)
        df_proc['transporte'] = df_fact.get('Transporte', df_fact.get('TRANSPORTE', df_fact.get('FLETERA', pd.Series(dtype=str)))).fillna('').astype(str).str.strip()

        # ── CRUCE DE INFORMACIÓN CON envios.csv (SOLO PARA LA FECHA DE ENVÍO) ──
        mapa_fechas_envio = {}
        if not df_envios.empty:
            df_envios.columns = df_envios.columns.str.strip()
            col_fac_env = None
            for c in ['Factura', 'FACTURA', 'NÚMERO DE PEDIDO', 'PEDIDO']:
                if c in df_envios.columns:
                    col_fac_env = c
                    break
            
            col_fec_env = None
            for c in ['FECHA DE ENVIO', 'FECHA_ENVIO', 'FECHA DE ENVÍO']:
                if c in df_envios.columns:
                    col_fec_env = c
                    break

            if col_fac_env and col_fec_env:
                for _, row in df_envios.iterrows():
                    f_val = str(row.get(col_fac_env, '')).strip()
                    fe_val = str(row.get(col_fec_env, '')).strip()
                    if f_val and fe_val and fe_val.lower() not in ['', 'nan', '0', 'nat', 'none']:
                        mapa_fechas_envio[f_val] = fe_val

        df_proc['fecha_envio'] = df_proc['factura'].map(mapa_fechas_envio).fillna('')

        # Quedarse solo con la primera línea de cada folio (evita duplicados por partidas)
        df_proc = df_proc.drop_duplicates(subset=['factura'], keep='first')
        df_proc = df_proc[df_proc['factura'] != ''].sort_values(by='factura', ascending=True, ignore_index=True)

        # Filtros tácticos de búsqueda para almacén
        f1, f2 = st.columns(2)
        with f1:
            facturas_opts = ["TODAS"] + sorted(list(df_proc['factura'].unique()))
            filtro_factura = st.selectbox("FILTRAR POR FACTURA", facturas_opts, key="filtro_factura_almacen")
        with f2:
            estatus_opts = [
                "TODOS", 
                "ENVIADA", 
                "CANCELADA", 
                "DETENIDA", 
                "DUPLICADA", 
                "CEDIS", 
                "SOLO FACTURA", 
                "NO ENTREGADA", 
                "MOSTRADOR", 
                "EXPORTACION"
            ]
            filtro_estatus = st.selectbox("FILTRAR POR ESTATUS", estatus_opts, key="filtro_estatus_almacen")

        df_filtrado = df_proc.copy()
        if filtro_factura != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['factura'] == filtro_factura]

        data_completa = df_filtrado.to_dict('records')
    else:
        data_completa = []

    render_historial_almacen(data_completa)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# ── FOOTER FIJO ────────────────────────
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
