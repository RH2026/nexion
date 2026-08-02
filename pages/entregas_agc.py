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
@keyframes fadeInSlideDown {{
    0% {{
        opacity: 0;
        transform: translateY(-20px);
    }}
    100% {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.animate-fade-in {{
    animation: fadeInSlideDown 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
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
    height: 34px !important;
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
# 2. SISTEMA DE SEGURIDAD PRO (VALIDACIÓN DE SESIÓN)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/entregas_agc.py"
    st.switch_page("pages/log.py")


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
# 4. HEADER CON 4 COLUMNAS (BÚSQUEDA GLOBAL TRIPLE RENDER)
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
            es_admin = usuario.upper() == "RIGOBERTO"
            es_ventas = usuario.upper() == "VENTAS"
            es_atencion3g = usuario.upper() == "ATENCION3G"
        
            nombre_display = st.session_state.get(
                "nombre_completo", "OPERADOR DESCONOCIDO"
            )
        
            st.markdown(
                f"""
                <div style='background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin-bottom: 15px; border-left: 3px solid #00D4FF;'>
                    <p style='color:#00D4FF; font-size:9px; font-weight:500; margin:0; letter-spacing:1px;'>USUARIO ACTIVO</p>
                    <p style='color:{vars_css['text']}; font-size:14px; font-weight:500; margin:0;'>{nombre_display.upper()}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
        
            st.markdown(
                "<p style='color:#f0f0f0; font-size:10px; font-weight:400; text-align:center; margin:10px 0; letter-spacing:1px;'>MENÚ PRINCIPAL</p>",
                unsafe_allow_html=True,
            )
        
            if not es_ventas and not es_atencion3g:
                if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                    st.session_state.menu_main = "DASHBOARD"
                    st.session_state.menu_sub = "GENERAL"
                    st.session_state.busqueda_activa = False
                    st.rerun()
        
            if not es_ventas:
                with st.expander(
                    "SEGUIMIENTO",
                    expanded=(st.session_state.menu_main == "SEGUIMIENTO"),
                ):
                    usuario_actual = str(
                        st.session_state.get(
                            "usuario", st.session_state.get("usuario_activo", "")
                        )
                    ).strip()
                    if es_admin:
                        opciones_seg = ["ALERTAS", "GANTT", "QUEJAS"]
                    elif usuario_actual == "Cynthia":
                        opciones_seg = ["ALERTAS", "QUEJAS"]
                    else:
                        opciones_seg = ["ALERTAS"]
        
                    for s in opciones_seg:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_sub_{s}"):
                            st.session_state.menu_main = "SEGUIMIENTO"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if not es_ventas and not es_atencion3g:
                with st.expander(
                    "ENTREGAS", expanded=(st.session_state.menu_main == "ENTREGAS")
                ):
                    opciones_ent = ["AGC", "AMAZON", "BARCELO"]
                    for s in opciones_ent:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_ent_{s}"):
                            st.session_state.menu_main = "ENTREGAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            
                            if s == "AGC":
                                st.switch_page("pages/entregas_agc.py")
                            else:
                                st.rerun()
        
            if not es_atencion3g:
                with st.expander(
                    "REPORTES", expanded=(st.session_state.menu_main == "REPORTES")
                ):
                    usuario_actual = str(
                        st.session_state.get(
                            "usuario", st.session_state.get("usuario_activo", "")
                        )
                    ).strip()
                    if es_admin or usuario_actual == "Carlos":
                        opciones_rep = [
                            "COSTOS CEDIS",
                            "ANALISIS MENSUAL",
                            "DETALLE COSTOS",
                            "ENVIOS ESPECIALES",
                            "ENVIO DE MUESTRAS",
                        ]
                    else:
                        opciones_rep = ["ENVIO DE MUESTRAS"]
        
                    for s in opciones_rep:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_rep_{s}"):
                            st.session_state.menu_main = "REPORTES"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if not es_ventas and not es_atencion3g:
                with st.expander(
                    "FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")
                ):
                    opciones_for = [
                        "SALIDA DE PT",
                        "CHECK LIST AGC",
                        "QR AGC",
                        "PREGUIA PAQMEX",
                        "RECOLECCION 3G",
                        "RECOLECCION ONE",
                        "CARTA RECLAMO",
                        "COTIZACIONES",
                    ]
                    for s in opciones_for:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_for_{s}"):
                            st.session_state.menu_main = "FORMATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            if not es_ventas and not es_atencion3g:
                with st.expander(
                    "CENTRO DE DATOS",
                    expanded=(st.session_state.menu_main == "CENTRO DE DATOS"),
                ):
                    for s in ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "HERRAMIENTAS"]:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_hub_{s}"):
                            st.session_state.menu_main = "CENTRO DE DATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            
                            if s == "ASIGNAR FLETERA":
                                st.switch_page("pages/asignacionfletera.py")
                            else:
                                st.rerun()
        
            if st.session_state.get("usuario_activo") == "Rigoberto":
                with st.expander(
                    "FINANZAS", expanded=(st.session_state.menu_main == "FINANZAS")
                ):
                    opciones_fin = ["WALLET", "CAJA CHICA", "GASTOS"]
                    for s in opciones_fin:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_fin_{s}"):
                            st.session_state.menu_main = "FINANZAS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()
        
            usuario_actual = st.session_state.get("usuario_activo", "").upper()
            if usuario_actual in ["RIGOBERTO", "JMORENO", "CARLOS"]:
                with st.expander(
                    "ENFOQUE", expanded=(st.session_state.get("menu_main") == "ENFOQUE")
                ):
                    for s in ["MORENO", "VAZQUEZ", "MIGUEL"]:
                        label = f"» {s}" if st.session_state.get("menu_sub") == s else s
                        if st.button(label, use_container_width=True, key=f"pop_enf_{s}"):
                            st.session_state.menu_main = "ENFOQUE"
                            st.session_state.menu_sub = s
                            st.rerun()
        
            st.markdown(
                "<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True
            )
            if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.autenticado = False
                st.session_state.splash_completado = False
                st.rerun()

    # ── RENDERIZADO DE RESULTADOS ──────────────────────────────────────────
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

        # RENDER 1: INVENTARIO
        if tipo == "INVENTARIO":
            st.markdown(f"<style>.card-inv {{ transition: all 0.3s ease; cursor: pointer; }} .card-inv:hover {{ transform: translateX(8px); border-color: {inv_color} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(54, 185, 204, 0.1); }}</style>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:15px;'><div style='background:{inv_color};width:5px;height:20px;border-radius:2px;box-shadow:0 0 10px {inv_color};'></div><span style='color:white;font-size:14px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;'>EXISTENCIAS EN INVENTARIO <span style='color:{inv_color};'>({total})</span></span></div>", unsafe_allow_html=True)
            for _, i in resultados.iterrows():
                st.markdown(f"<div class='card-inv' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {inv_color};border-radius:10px;padding:10px 20px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CÓDIGO / SKU</span><br><b style='font-size:16px;color:{inv_color};letter-spacing:1px;'>{i.get('CODIGO','')}</b></div><div style='flex:3;padding-left:20px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>DESCRIPCIÓN</span><br><span style='font-size:13px;color:white;font-weight:600;line-height:1.2;'>{i.get('DESCRIPCION','')}</span></div><div style='flex:1;text-align:right;'><span style='background:{inv_color}15;color:{inv_color};padding:3px 8px;border-radius:4px;font-size:9px;font-weight:800;border:1px solid {inv_color}30;text-transform:uppercase;'>DISPONIBLE</span></div></div>", unsafe_allow_html=True)
        else:
            # RENDER 2: RESULTADO ÚNICO UNIFICADO
            if total == 1:
                envio = resultados.iloc[0]
                f_envio = envio.get("FECHA DE ENVÍO", "N/A")
                f_promesa = envio.get("PROMESA DE ENTREGA", "N/A")
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

                d = envio

                tarjeta_unica_html = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 20px 25px; border-radius: 8px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;"><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #38bdf8; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #38bdf8;"></div><div style="font-size: 9px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;">ENVÍO</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('FECHA DE ENVÍO','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #38bdf8; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #a855f7; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #a855f7;"></div><div style="font-size: 9px; font-weight: 800; color: #a855f7; letter-spacing: 1px;">GUÍA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{n_guia if tiene_guia else 'EN PROCESO'}</div></div><div style="flex-grow: 1; height: 2px; background: #a855f7; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #eab308; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #eab308;"></div><div style="font-size: 9px; font-weight: 800; color: #eab308; letter-spacing: 1px;">PROMESA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('PROMESA DE ENTREGA','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #00FFAA; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: {status_color}; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px {status_color};"></div><div style="font-size: 9px; font-weight: 800; color: {status_color}; letter-spacing: 1px;">ENTREGA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{f_entrega_val}</div></div></div><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;"><div style="flex: 1.2; min-width: 200px;"><div style="color: {accent_color}; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">{envio.get('FLETERA','N/A')}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 2px;">TALÓN / FOLIO</div><div style="color: {accent_color}; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{n_guia}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">REF / PEDIDO: <span style="color: white; font-size: 11px; font-weight: 700;">{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div></div><div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / CLIENTE</div><div style="color: white; font-weight: 800; font-size: 13px; text-transform: uppercase; line-height: 1.3; margin-top: 2px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div><div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 2px;">ID: {envio.get('NO CLIENTE','')} | {envio.get('DOMICILIO','')}</div><div style="font-size: 11px; color: {accent_color}; margin-top: 4px; font-weight: 600;">📍 GDL → {envio.get('DESTINO','N/A')}</div></div><div style="flex: 1.2; min-width: 150px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN CARGA</div><div style="color: white; font-weight: 700; font-size: 11px; margin-top: 2px;">BULTOS: <span style="color: {accent_color};">{envio.get('CANTIDAD DE CAJAS','0')}</span></div><div style="color: {accent_color}; font-weight: 800; font-size: 13px; margin-top: 2px;">$ {envio.get('COSTO DE LA GUÍA','0.00')}</div></div><div style="text-align: right; min-width: 130px;"><span style="background-color: {status_color}15; color: {status_color}; padding: 5px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; border: 1px solid {status_color}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">ESTATUS: {status_text}</span></div></div></div>"""
                st.markdown(tarjeta_unica_html, unsafe_allow_html=True)
            else:
                # RENDER 3: LISTADO MÚLTIPLE
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

    # Contenedor animado con estilos limpios
    st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)
    
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

    # --- Lógica de Navegación de Vistas ---
    if 'tipo_vista_agc' not in st.session_state:
        st.session_state.tipo_vista_agc = 'ENTREGAS'

    if 'mes_calendario' not in st.session_state:
        st.session_state.mes_calendario = datetime.now().month  # Mes en curso dinámico

    # Creamos DOS botones principales superiores
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        btn_type_1 = "primary" if st.session_state.tipo_vista_agc == 'ENTREGAS' else "secondary"
        if st.button("VISTA DE ENTREGAS", use_container_width=True, type=btn_type_1):
            st.session_state.tipo_vista_agc = 'ENTREGAS'
            st.rerun()

    with col_btn2:
        btn_type_2 = "primary" if st.session_state.tipo_vista_agc == 'CALENDARIO' else "secondary"
        if st.button("VISTA CALENDARIO GLOBAL", use_container_width=True, type=btn_type_2):
            st.session_state.tipo_vista_agc = 'CALENDARIO'
            st.rerun()

    # --- Encabezado de Texto Dinámico ---
    if st.session_state.tipo_vista_agc == 'ENTREGAS':
        titulo_dinamico = "PANEL DE ENTREGAS PENDIENTES (AGC)"
    else:
        titulo_dinamico = "CALENDARIO DE ENTREGAS GLOBAL"

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
                            <div class="label-mini md:mb-1">Tipo / Estatus</div>
                            <div class="text-[10px] font-bold text-emerald-300 uppercase">{item['tipo']}</div>
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

    # --- Generador de PDF para Citas del Mes ---
    def generar_pdf_citas_mes(data_completa, mes_num, anio=2026):
        meses_nombres = {
            1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
            7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
        }
        nombre_mes = meses_nombres.get(mes_num, "MES")

        citas_filtradas = []
        for item in data_completa:
            if item.get('estatus') == 'ENTREGADA':
                continue
            try:
                fecha_str = str(item['cita']).split(" - ")[0].strip()
                dt = datetime.strptime(fecha_str, "%d/%m/%m" if len(fecha_str.split('/')[2])==2 else "%d/%m/%Y")
                if dt.month == mes_num and dt.year == anio:
                    citas_filtradas.append(item)
            except:
                pass

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        pdf.setFillColorRGB(0.21, 0.28, 0.32) # #384A52
        pdf.rect(0, height - 80, width, 80, fill=1, stroke=0)
        
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, height - 35, "JYPESA | REPORTE DE CITAS PENDIENTES")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, height - 55, f"PERIODO: {nombre_mes} {anio} — NEXION SUPPLY CHAIN INTELLIGENCE")

        y = height - 120
        pdf.setFillColorRGB(0.1, 0.1, 0.1)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(40, y, "FECHA / CITA")
        pdf.drawString(140, y, "OC / PEDIDO")
        pdf.drawString(240, y, "TIPO UNIDAD")
        pdf.drawString(330, y, "VOLUMEN")
        pdf.drawString(430, y, "PRODUCTO")
        
        y -= 8
        pdf.setStrokeColorRGB(0.7, 0.7, 0.7)
        pdf.line(40, y, width - 40, y)
        y -= 20

        pdf.setFont("Helvetica", 8)
        for item in citas_filtradas:
            if y < 50:
                pdf.showPage()
                y = height - 50
            
            pdf.drawString(40, y, str(item.get('cita', ''))[:22])
            pdf.drawString(140, y, str(item.get('oc', ''))[:18])
            pdf.drawString(240, y, str(item.get('tipo', ''))[:15])
            pdf.drawString(330, y, str(item.get('cantidad', ''))[:20])
            pdf.drawString(430, y, str(item.get('producto', ''))[:25])
            y -= 18

        if not citas_filtradas:
            pdf.setFont("Helvetica-Oblique", 10)
            pdf.drawString(40, y, "No hay citas pendientes registradas para este mes.")

        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()

    # --- Función: Renderizado de Calendario ---
    def render_calendario_visual(data_completa, mes_num, anio=2026):
        meses_nombres = {
            1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
            7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
        }
        nombre_mes = meses_nombres.get(mes_num, "MES")
        
        eventos_dias = {}
        for item in data_completa:
            if item.get('estatus') == 'ENTREGADA':
                continue
            try:
                fecha_str = str(item['cita']).split(" - ")[0].strip()
                dt = datetime.strptime(fecha_str, "%d/%m/%m" if len(fecha_str.split('/')[2])==2 else "%d/%m/%Y")
                if dt.month == mes_num and dt.year == anio:
                    if dt.day not in eventos_dias: 
                        eventos_dias[dt.day] = []
                    eventos_dias[dt.day].append({"tipo": item['tipo'], "oc": item['oc'], "estatus": item['estatus']})
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
                            bg_badge = "bg-sky-600/90 border-sky-400" if ev['tipo'] == "CAMION" else "bg-emerald-700/90 border-emerald-500"
                            texto_badge = f"{ev['tipo']} - {ev['oc']}"
                            
                            eventos_del_dia_html += f'''
                            <div class="text-[10px] font-bold text-white px-1.5 py-0.5 rounded border mb-1 truncate tracking-tight {bg_badge}">
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
                        <div class="flex items-center gap-1.5"><div class="w-3 h-3 bg-sky-600 rounded"></div>CAMION</div>
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

        if modo_edicion:
            st.warning("⚠️ Modo edición activo. Modifica las celdas abajo y haz clic en el botón de guardar para actualizar GitHub automáticamente.")
            
            df_editado = st.data_editor(df_raw, use_container_width=True, num_rows="dynamic", key="editor_agc_admin_session")
            
            if st.button("💾 Guardar Cambios en GitHub", key="btn_guardar_github_session"):
                if guardar_cambios_github(df_editado):
                    st.rerun()
            st.markdown("---")

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
        
        data_completa = df_entregas.to_dict('records')
        data_pendientes = [item for item in data_completa if item['estatus'] != 'ENTREGADA']
    else:
        data_completa = []
        data_pendientes = []

    # --- Lógica de Renderizado Condicional de Vistas ---
    if st.session_state.tipo_vista_agc == 'ENTREGAS':
        render_logistica_flow_responsive(data_pendientes)
    elif st.session_state.tipo_vista_agc == 'CALENDARIO':
        col_mes_sel, col_btn_pdf = st.columns([3, 3])
        
        with col_mes_sel:
            opciones_meses = {
                "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
                "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
            }
            
            if st.session_state.mes_calendario not in opciones_meses.values():
                st.session_state.mes_calendario = datetime.now().month

            nombre_mes_actual = [k for k, v in opciones_meses.items() if v == st.session_state.mes_calendario][0]
            
            mes_seleccionado = st.selectbox(
                "SELECCIONAR MES A VISUALIZAR", 
                list(opciones_meses.keys()),
                index=list(opciones_meses.keys()).index(nombre_mes_actual)
            )
            
            if opciones_meses[mes_seleccionado] != st.session_state.mes_calendario:
                st.session_state.mes_calendario = opciones_meses[mes_seleccionado]
                st.rerun()

        with col_btn_pdf:
            st.markdown("<div style='margin-top: 27px;'></div>", unsafe_allow_html=True)
            pdf_bytes = generar_pdf_citas_mes(data_completa, st.session_state.mes_calendario)
            nombre_archivo_pdf = f"citas_pendientes_{nombre_mes_actual.lower()}_2026.pdf"
            
            st.download_button(
                label="📥 DESCARGAR PDF DE CITAS DEL MES",
                data=pdf_bytes,
                file_name=nombre_archivo_pdf,
                mime="application/pdf",
                use_container_width=True
            )
            
        render_calendario_visual(data_completa, st.session_state.mes_calendario)

    st.markdown('</div>', unsafe_allow_html=True)


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
