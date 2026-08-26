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

exigir_autenticacion("quejas")



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
    st.session_state.pagina_destino = "pages/envios.py"
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

verificar_permiso_pagina("SEGUIMIENTO", "QUEJAS")


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


# ================================================================================
# 5. INTERFAZ PRINCIPAL 
# ================================================================================

def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    # ── CONFIGURACIÓN DEL REPOSITORIO DE INCIDENCIAS ─────────────────────────────────────
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "incidencias.csv"
    CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
    MATRIZ_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/Matriz_Excel_Dashboard.csv"
    
    # Validamos si el usuario actual es administrador (Rigoberto u otro rol admin según tu lógica)
    usuario_actual = str(st.session_state.get("usuario", st.session_state.get("usuario_activo", ""))).strip()
    es_administrador = es_admin or (usuario_actual in ["Rigoberto", "Rigoberto Hernández"])
    
    # Actualizamos las columnas con los nombres correctos que me pediste amor
    COLUMNAS_INCIDENCIAS = [
        "FOLIO", "USUARIO", "PRIORIDAD", "VINCULO_BUSQUEDA", 
        "CLIENTE_DESTINO", "PEDIDO_GUIA", "ID_SEGUIMIENTO", "ID_QUEJA", 
        "RESPONSABLE", "DETALLE_INCIDENCIA", "ACCIONES", "ESTATUS"
    ]
    
    @st.cache_data(ttl=600)
    def cargar_matriz_global():
        try:
            r = requests.get(f"{MATRIZ_URL}?t={int(time.time())}")
            if r.status_code == 200:
                df = pd.read_csv(StringIO(r.text))
                df.columns = [c.strip().upper() for c in df.columns]
                return df
        except:
            return None
        return None
    
    df_global = cargar_matriz_global()
    
    # ── FUNCIÓN PARA SINCRONIZAR Y CREAR ARCHIVO EN GITHUB ──────────────────────────────
    def guardar_en_github(df):
        """Sincroniza el DataFrame con el repositorio. Crea el archivo si no existe."""
        import base64
        if not TOKEN:
            st.error("No se encontró el GITHUB_TOKEN en los secrets.")
            return False
            
        csv_content = df.to_csv(index=False)
        api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {
            "Authorization": f"token {TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            r = requests.get(api_url, headers=headers)
            sha = r.json().get("sha") if r.status_code == 200 else None
            
            payload = {
                "message": f"Actualización de incidencias {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "content": base64.b64encode(csv_content.encode()).decode(),
                "branch": "main"
            }
            if sha:
                payload["sha"] = sha
                
            response = requests.put(api_url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                st.success("✅ ¡Incidencias sincronizadas con éxito en GitHub!")
                return True
            else:
                st.error(f"Error de GitHub: {response.json().get('message')}")
                return False
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            return False
    
    # ── CARGA SEGURA CON AUTO-CREACIÓN SI NO EXISTE ─────────────────────────────────────
    def cargar_datos_seguro():
        try:
            r = requests.get(f"{CSV_URL}?t={int(time.time())}")
            if r.status_code == 200:
                df = pd.read_csv(StringIO(r.text))
                df.columns = [c.strip().upper() for c in df.columns]
                
                for c in COLUMNAS_INCIDENCIAS:
                    if c not in df.columns:
                        df[c] = ""
                return df[COLUMNAS_INCIDENCIAS]
                
            elif r.status_code == 404:
                df_nuevo = pd.DataFrame(columns=COLUMNAS_INCIDENCIAS)
                guardar_en_github(df_nuevo)
                return df_nuevo
        except Exception as e:
            st.error(f"Error al cargar el módulo de incidencias: {e}")
            
        return pd.DataFrame(columns=COLUMNAS_INCIDENCIAS)
    
    if "df_incidencias" not in st.session_state:
        st.session_state.df_incidencias = cargar_datos_seguro()
    
    # Parche de seguridad para registros viejos en session_state
    for c in COLUMNAS_INCIDENCIAS:
        if c not in st.session_state.df_incidencias.columns:
            st.session_state.df_incidencias[c] = ""
    
    df_master = st.session_state.df_incidencias.copy()
    
    # ── INYECCIÓN DE INTERFAZ CSS LIMPIA ─────────────────────────────────────────────────
    st.markdown("""
        <style>
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }
        .search-container-pro {
            border-left: 4px solid #f43f5e;
            padding-left: 15px;
            margin-bottom: 20px;
            background: rgba(244, 63, 94, 0.05);
            padding-top: 10px;
            padding-bottom: 1px;
            border-radius: 0 10px 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ── 1. PANEL DE CAPTURA INTELIGENTE (EXCLUSIVO PARA ADMIN) ───────────────────────────
    if es_administrador:
        with st.expander("➕ Registrar o Editar Incidencia / Queja", expanded=False):
            
            c1, c2, c3 = st.columns([2, 1, 1])
            
            with c1:
                n_pedido = st.text_input("📦 Vincular Pedido / Factura (Opcional)", placeholder="Escribe pedido para autollenar...").strip().upper()
            
            # Lógica de Folios
            if not st.session_state.df_incidencias.empty and "FOLIO" in st.session_state.df_incidencias.columns:
                folios_numeros = st.session_state.df_incidencias['FOLIO'].str.extract(r'INC-(\d+)')[0].dropna().astype(int)
                if not folios_numeros.empty:
                    ultimo_folio = folios_numeros.max()
                    sugerencia_folio = f"INC-{ultimo_folio + 1:03d}"
                else:
                    sugerencia_folio = "INC-001"
            else:
                sugerencia_folio = "INC-001"
                
            with c2:
                t_folio_input = st.text_input("Folio ID (Buscar o Nuevo)", value=sugerencia_folio).strip().upper()
                
            incidencia_existente = None
            mask = None
            if t_folio_input and not st.session_state.df_incidencias.empty:
                mask = st.session_state.df_incidencias['FOLIO'] == t_folio_input
                if mask.any():
                    incidencia_existente = st.session_state.df_incidencias[mask].iloc[0]
                    st.info(f"Modo Edición Activado: Cargando datos del Folio {t_folio_input}")
                    
            with c3:
                prioridades = ["Media", "Urgente", "Alta", "Baja"]
                idx_prio = prioridades.index(incidencia_existente['PRIORIDAD']) if incidencia_existente is not None and incidencia_existente['PRIORIDAD'] in prioridades else 0
                t_prior = st.selectbox("Gravedad / Prioridad", prioridades, index=idx_prio)
    
            # Auto-relleno desde la Matriz Global
            info_matriz = {"cliente_destino": "", "pedido_guia": ""}
            if n_pedido and df_global is not None:
                res = df_global[df_global["NÚMERO DE PEDIDO"].astype(str).str.contains(n_pedido, na=False)]
                if not res.empty:
                    fila_m = res.iloc[0]
                    guia = fila_m.get('NÚMERO DE GUÍA', 'N/A')
                    cliente = fila_m.get('NOMBRE DEL CLIENTE', 'N/A')
                    destino = fila_m.get('DESTINO', 'N/A')
                    info_matriz["cliente_destino"] = f"CLIENTE: {cliente} | DESTINO: {destino}"
                    info_matriz["pedido_guia"] = f"PEDIDO: {n_pedido} | GUIA: {guia}"
                else:
                    st.warning("⚠️ Pedido no localizado en la Matriz. Puedes llenar o modificar los campos abajo a mano.")
    
            with st.form("form_incidencias", clear_on_submit=False):
                f2_c1, f2_c2 = st.columns([1, 1])
                
                with f2_c1:
                    val_cd = info_matriz["cliente_destino"] if info_matriz["cliente_destino"] else (incidencia_existente['CLIENTE_DESTINO'] if incidencia_existente is not None else "")
                    t_cliente_destino = st.text_input("CLIENTE / DESTINO", value=val_cd)
                    
                    val_pg = info_matriz["pedido_guia"] if info_matriz["pedido_guia"] else (incidencia_existente['PEDIDO_GUIA'] if incidencia_existente is not None else "")
                    t_pedido_guia = st.text_input("PEDIDO / GUÍA", value=val_pg)
                    
                    val_resp = incidencia_existente['RESPONSABLE'] if incidencia_existente is not None else ""
                    t_responsable = st.text_input("RESPONSABLE", value=val_resp)
                    
                with f2_c2:
                    val_id_seg_default = incidencia_existente['ID_SEGUIMIENTO'] if incidencia_existente is not None else t_folio_input
                    val_id_seg = val_id_seg_default if val_id_seg_default else ""
                    t_id_seguimiento = st.text_input("ID SEGUIMIENTO (Sugerido por defecto)", value=val_id_seg)
                    
                    val_id_queja_default = incidencia_existente['ID_QUEJA'] if incidencia_existente is not None else t_folio_input
                    val_id_queja = val_id_queja_default if val_id_queja_default else ""
                    t_id_queja = st.text_input("ID DE QUEJA (Sugerido por defecto)", value=val_id_queja)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                
                val_det = incidencia_existente['DETALLE_INCIDENCIA'] if incidencia_existente is not None else ""
                t_detalle = st.text_area("DETALLE DE INCIDENCIA", value=val_det, key="area_detalle", help="Describe el problema de forma clara.")
                
                val_acc = incidencia_existente['ACCIONES'] if incidencia_existente is not None else ""
                t_acciones = st.text_area("ACCIONES", value=val_acc, key="area_acciones", help="Indica las acciones tomadas para resolver la incidencia.")
                
                estatus_opciones = ["PENDIENTE", "EN PROCESO", "SOLUCIONADO", "RECHAZADO"]
                idx_estatus = estatus_opciones.index(incidencia_existente['ESTATUS']) if incidencia_existente is not None and incidencia_existente['ESTATUS'] in estatus_opciones else 0
                t_estatus = st.selectbox("Estatus de la Incidencia", estatus_opciones, index=idx_estatus)
    
                st.markdown("<br>", unsafe_allow_html=True)
                texto_boton = ":material/sync: ACTUALIZAR INCIDENCIA" if incidencia_existente is not None else ":material/save: REGISTRAR QUEJA / INCIDENCIA"
                enviar = st.form_submit_button(texto_boton, use_container_width=True)
                
                if enviar:
                    folio_final = t_folio_input if t_folio_input else sugerencia_folio
                    
                    valor_busqueda = n_pedido if n_pedido else (incidencia_existente.get('VINCULO_BUSQUEDA', '') if incidencia_existente is not None else "")
                    busqueda_final = str(valor_busqueda).upper() if valor_busqueda is not None else ""
                    
                    nueva_data = {
                        "FOLIO": folio_final,
                        "USUARIO": st.session_state.get('nombre_completo', 'RIGOBERTO HERNÁNDEZ'),
                        "PRIORIDAD": t_prior,
                        "VINCULO_BUSQUEDA": busqueda_final, 
                        "CLIENTE_DESTINO": str(t_cliente_destino).upper(),
                        "PEDIDO_GUIA": str(t_pedido_guia).upper(),
                        "ID_SEGUIMIENTO": str(t_id_seguimiento).upper(),
                        "ID_QUEJA": str(t_id_queja).upper(),
                        "RESPONSABLE": str(t_responsable).upper(),
                        "DETALLE_INCIDENCIA": t_detalle,
                        "ACCIONES": t_acciones,
                        "ESTATUS": t_estatus
                    }
                    
                    if incidencia_existente is not None and mask is not None:
                        df_temp = st.session_state.df_incidencias[~mask]
                        df_final = pd.concat([df_temp, pd.DataFrame([nueva_data])], ignore_index=True)
                    else:
                        df_final = pd.concat([st.session_state.df_incidencias, pd.DataFrame([nueva_data])], ignore_index=True)
                        
                    if guardar_en_github(df_final):
                        st.session_state.df_incidencias = df_final
                        st.success("✅ ¡Registro procesado correctamente, amor!")
                        time.sleep(1)
                        st.rerun()
    
    # ── 2. MONITOR DE QUEJAS Y PENDIENTES (GRID PROFESIONAL - VISIBLE PARA TODOS LOS AUTORIZADOS) ──
    st.markdown("""
        <style>
        .card-hover {
            border: 1px solid #3d474d;
            border-left: 5px solid;
            transition: transform 0.2s, background-color 0.2s, border-color 0.3s !important;
        }
        .card-hover:hover {
            transform: scale(1.01);
            background-color: #313a40 !important;
            border: 1px solid #38bdf8 !important;
            border-left: 5px solid #38bdf8 !important;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)
    
    prioridad_colores = {"Urgente": "#ff4b4b", "Alta": "#f97316", "Media": "#38bdf8", "Baja": "#00FFAA"}
    estatus_colores = {"PENDIENTE": "#fbbf24", "EN PROCESO": "#60a5fa", "SOLUCIONADO": "#22c55e", "RECHAZADO": "#ef4444"}
    
    if df_master.empty:
        st.info("No hay incidencias registradas.")
    else:
        for _, row in df_master.iterrows():
            if not str(row.get("FOLIO", "")).strip(): continue
            
            color_p = prioridad_colores.get(row.get("PRIORIDAD", "Baja"), "#94a3b8")
            f_est = row.get('ESTATUS', 'PENDIENTE')
            color_e = estatus_colores.get(f_est, "#64748b")
            
            st.markdown(f"""<div class="card-hover" style="border-left-color: {color_p}; padding: 12px; margin-bottom: 10px; background: #262e33; border-radius: 5px;"><div style="display: grid; grid-template-columns: 0.8fr 1.5fr 1.2fr 2fr 1fr; gap: 10px; align-items: center;"><div><div style="font-size: 0.65em; color: #888;">FOLIO/EST</div><div style="color: {color_p}; font-weight: bold; font-size: 1em;">{row.get('FOLIO', 'INC-???')}</div><span style="background: {color_e}33; color: {color_e}; padding: 1px 4px; border-radius: 3px; font-weight: bold; font-size: 0.7em;">{f_est}</span></div><div><div style="font-size: 0.65em; color: #888;">CLIENTE/PEDIDO</div><div style="color: #fff; font-size: 0.9em; font-weight: bold;">{row.get('CLIENTE_DESTINO', 'N/A')}</div><div style="font-size: 0.8em; color: #bbb;">📦 {row.get('PEDIDO_GUIA', 'N/A')}</div></div><div><div style="font-size: 0.65em; color: #888;">ID SEGUIMIENTO / QUEJA</div><div style="font-size: 0.85em; color: #eee;"> {row.get('ID_SEGUIMIENTO', 'N/A')}</div><div style="font-size: 0.85em; color: #eee;"> {row.get('ID_QUEJA', 'N/A')}</div></div><div><div style="font-size: 0.65em; color: #888;">DETALLE / ACCIONES</div><div style="font-size: 0.85em; color: #eee;">{row.get('DETALLE_INCIDENCIA', 'Sin detalle...')}</div><div style="font-size: 0.8em; color: #38bdf8;"><i>{row.get('ACCIONES', '')}</i></div></div><div style="text-align: right;"><div style="font-size: 0.65em; color: #888;">RESPONSABLE/REG</div><div style="color: #fff; font-size: 0.85em;">👤 {row.get('RESPONSABLE', 'N/A')}</div><div style="font-size: 0.7em; color: #38bdf8;">📝 {row.get('USUARIO', 'N/A')}</div></div></div></div>""", unsafe_allow_html=True)  
    
    # ── 3. EDITOR DE AVANZADO (EXCLUSIVO PARA ADMIN) ────────────────────────────────────
    if es_administrador:
        with st.expander("⚙️ Editor de datos (Solo Administración)", expanded=False):
            st.subheader("Modo edición avanzada")
            df_editor = df_master.copy()
            
            for col in COLUMNAS_INCIDENCIAS:
                if col not in df_editor.columns: df_editor[col] = ""
                df_editor[col] = df_editor[col].astype(str).replace("nan", "").fillna("")
                
            df_editado = st.data_editor(df_editor, hide_index=True, use_container_width=True, num_rows="dynamic")
            
            cabeceras = "".join([f"<th>{c}</th>" for c in COLUMNAS_INCIDENCIAS if c != 'VINCULO_BUSQUEDA'])
            cuerpo = ""
            for _, fila in df_editado.iterrows():
                cuerpo += "<tr>" + "".join([f"<td>{str(fila.get(c, ''))}</td>" for c in COLUMNAS_INCIDENCIAS if c != 'VINCULO_BUSQUEDA']) + "</tr>"
    
            html_print = f"""
            <div id="printableArea" style="font-family: sans-serif;">
                <h2>JYPESA - Logística NEXION</h2>
                <table border="1" style="width:100%; border-collapse: collapse;">
                    <thead><tr>{cabeceras}</tr></thead>
                    <tbody>{cuerpo}</tbody>
                </table>
            </div>
            """
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(":material/sync: SINCRONIZAR", use_container_width=True):
                    if guardar_en_github(df_editado):
                        st.session_state.df_incidencias = df_editado
                        st.rerun()
            with col2:
                import streamlit.components.v1 as components
                if st.button(":material/print: IMPRIMIR", use_container_width=True):
                    components.html(f"{html_print}<script>window.print();</script>", height=0, width=0)
            with col3:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_editado.to_excel(writer, index=False, sheet_name='Incidencias')
                st.download_button("BAJAR EXCEL", data=buffer.getvalue(), file_name="incidencias_nexion.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)  


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
