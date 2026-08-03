import base64
import calendar
from datetime import datetime, date
import io
import re
import time
import unicodedata
import zipfile
import requests
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas
import reportlab.lib.units as units

cm = units.cm

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
                            
                            if s == "ENVIO DE MUESTRAS":
                                st.switch_page("pages/muestras.py")
                            else:
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

                tarjeta_unica_html = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 20px 25px; border-radius: 8px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;"><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #38bdf8; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #38bdf8;"></div><div style="font-size: 9px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;">ENVÍO</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('FECHA DE ENVÍO','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #38bdf8; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #a855f7; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #a855f7;"></div><div style="font-size: 9px; font-weight: 800; color: #a855f7; letter-spacing: 1px;">GUÍA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{n_guia if tiene_guia else 'EN PROCESO'}</div></div><div style="flex-grow: 1; height: 2px; background: #a855f7; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #eab308; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #eab308;"></div><div style="font-size: 9px; font-weight: 800; color: #eab308; letter-spacing: 1px;">PROMESA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('PROMESA DE ENTREGA','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #00FFAA; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: {status_color}; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px {status_color};"></div><div style="font-size: 9px; font-weight: 800; color: {status_color}; letter-spacing: 1px;">ENTREGA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{f_entrega_val}</div></div></div><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;"><div style="flex: 1.2; min-width: 200px;"><div style="color: #00FFAA; font-size: 16px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">{envio.get('FLETERA','N/A')}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">TALÓN / FOLIO</div><div style="color: #00FFAA; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{n_guia}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">REF / PEDIDO: <span style="color: white; font-size: 13px; font-weight: 700;">{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div></div><div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / CLIENTE</div><div style="color: white; font-weight: 800; font-size: 13px; text-transform: uppercase; line-height: 1.3; margin-top: 2px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div><div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 2px;">ID: {envio.get('NO CLIENTE','')} | {envio.get('DOMICILIO','')}</div><div style="font-size: 11px; color: #00FFAA; margin-top: 4px; font-weight: 600;">📍 GDL → {envio.get('DESTINO','N/A')}</div></div><div style="flex: 1.2; min-width: 150px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN CARGA</div><div style="color: white; font-weight: 700; font-size: 11px; margin-top: 2px;">BULTOS: <span style="color: #00FFAA;">{envio.get('CANTIDAD DE CAJAS','0')}</span></div><div style="color: #00FFAA; font-weight: 800; font-size: 13px; margin-top: 2px;">$ {envio.get('COSTO DE LA GUÍA','0.00')}</div></div><div style="text-align: right; min-width: 130px;"><span style="background-color: {status_color}15; color: {status_color}; padding: 5px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; border: 1px solid {status_color}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">ESTATUS: {status_text}</span></div></div></div>"""
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
# 5. INTERFAZ PRINCIPAL (MUESTRAS)
# ==========================================
def main():
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)
    
    if "reset_key" not in st.session_state:
        st.session_state.reset_key = 0
    if "folio_guardado" not in st.session_state:
        st.session_state.folio_guardado = False

    GITHUB_USER = "RH2026"
    GITHUB_REPO = "nexion"
    GITHUB_PATH = "muestras.csv"
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 
    
    precios = {
        "Envio Muestras Especiales": 0.0,
        "Kit Accesorios Ecologicos": 47.85,
        "kit Accesorios Lavarino": 47.85,
        "kit Dispensador Almond 250": 218.33,
        "kit Dispensador Biogena 250": 216.00,
        "kit Dispensador Cava 250": 230.58,
        "kit Dispensador Persea 250": 275.00,
        "kit Dispensador Botánicos 250": 274.17,
        "kit Dispensador Dove 250": 125.00,
        "kit Dispensador Rainforest 250": 216.00,
        "Kit Elements": 29.34,
        "Kit Almond": 33.83,
        "Kit Biogena": 48.95,
        "Kit Cava": 34.59,
        "Kit Persa": 58.02,
        "Kit Lavarino": 36.30,
        "Kit Botánicos": 29.34,
        "Kit Rainforest": 30.34,
        "JHJY-0050 Llave magnetica para soporte JH": 180.00,
        "JHJY-0033 Rack JH  Color Blanco de 2 pzas": 65.00,
        "JHJY-0034 Rack JH  Color Blanco de 1 pzas": 50.00,
        "JHJY-0045 Soporte de acero inoxidable Jypesa INOX Cap lock individual": 679.00,
        "JHJY-0046 Soporte de acero inoxidable Jypesa INOX Cap lock doble": 679.00,
        "JHJY-0047 Soporte de acero inoxidable Jypesa INOX Cap lock triple": 679.00,
        "JHJY-0037 Llave para rack de acero Jypesa": 25.50,
        "JHJY-0026 Rack JH Individual color Negro": 40.28,
        "JHJY-0027 Rack JH Doble color Negro": 40.28,
        "JHJY-0065 KIT Bracket+Key+3M Super Glue/Screw black ANTI-THEFT Emperor Semi circular 12 Piezas/Caja": 418.2,
        "JHJY-0064 KIT Bracket+Key+3M Super Glue/Screw black ANTI-THEFT Easy snap 12 Piezas/Caja": 418.2,
        "4029-A90 NOCEAN Cepillo Dental eco amigable nOcean caja con 144 piezas": 4.1,
        "4029-A91 NOCEAN Peine de bambu eco amigable nOcean caja con 200 piezas": 8.74,
        "4029-A92 NOCEAN Kit de afeitar eco amigable nOcean caja con 200 piezas": 16.60,
        "4029-A93 NOCEAN Kit de vanidad eco amigable nOcean caja con 500 piezas": 3.8,
        "4029-A95 NOCEAN Kit de costura eco amigable nOcean caja con 500 piezas": 2.4,
        "4029-A96 NOCEAN Limpia calzado eco amigable nOcean caja con 500 piezas": 4.4,
        "4029-A97 NOCEAN Toallita desmaquillante comprimida eco amigable nOcean caja con 300 piezas": 5.2,
        "4029-A98 NOCEAN Esponja de celulosa comprimida eco amigable nOcean caja con 500 piezas": 3.95,
        "4052-L17 CAVA Shampoo Cava Nocean 40 ml. Caja con 150 piezas": 5.99,
        "4052-L18 CAVA Acondicionador Cava Nocean 40 ml. Caja con 150 piezas": 5.99,
        "4052-L19 CAVA Gel de baño Cava Nocean 40 ml. Caja con 150 piezas": 5.99,
        "4052-L20 CAVA Crema Humectante Cava Nocean 40 ml. Caja con 150 piezas": 6.44,
        "4018-A23 Limpia calzado Lavarino Cosso. Cajilla Nva. Imagen Caja con 225 piezas": 3.23,
        "4018-A24 Gorra de baño Lavarino Cosso. Cajilla Nva. Imagen Caja con 225 piezas": 2.26,
        "4018-A25 KIT dental Lavarino Cosso. Cajilla Nva. Imagen Caja con 144 piezas": 11.60,
        "4018-A26 KIT de vanidad Lavarino Cosso. Cajilla Nva. Imagen Caja con 150 piezas": 2.95,
        "4018-A27 KIT de afeitar Lavarino Cosso. Cajilla Nva. Imagen Caja con 116 piezas": 7.230,
        "4018-A28 KIT de costura Lavarino Cosso. Cajilla Nva. Imagen Caja con 225 piezas": 1.90,
        "4018-A29 Peine Lavarino Cosso. Manga Nva. Imagen 400 Piezas": 2.44,
        "68829526 Rack Dove Dove Mlac Bracket Metalized Bottle 1 Pieza": 193.90
    }
    
    def limpiar_parentesis(texto):
        return re.sub(r'\(.*?\)', '', str(texto)).strip()
    
    def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
        texto = str(texto).upper()
        lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
        
        tamano_actual = tamano_max
        while len(lineas) > max_lineas and tamano_actual > 8:
            tamano_actual -= 0.5
            lineas = simpleSplit(texto, fuente, tamano_actual, ancho_max)
        
        c.setFont(fuente, tamano_actual)
        y_actual = y_inicio
        for line in lineas[:max_lineas]: 
            c.drawCentredString(x_centro, y_actual, line)
            y_actual -= interlineado
        return y_actual 
    
    def generar_etiquetas_limpias(reg_datos, total_etqs, factura_val, transporte_val):
        output = io.BytesIO()
        c = canvas.Canvas(output, pagesize=letter)
        width_carta, height_carta = letter
        
        w_rec, h_rec = 10.5 * cm, 7.5 * cm
        x_offset, y_offset = 0.3 * cm, height_carta - h_rec - 0.3 * cm
        
        nombre_crudo = reg_datos.get('NOMBRE DEL HOTEL', 'SIN NOMBRE')
        nombre_final = limpiar_parentesis(nombre_crudo)
        direccion_final = reg_datos.get('DESTINO', 'DIRECCIÓN NO DISPONIBLE')
        transporte_final = str(transporte_val if transporte_val else 'TRES GUERRAS')
    
        for i in range(total_etqs):
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)
    
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_offset + (w_rec/2), y_offset + h_rec - 0.3*cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            c.setFont("Helvetica", 6)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(c, info_contacto, x_offset + (w_rec/2), y_offset + h_rec - 0.7*cm, 10*cm, "Helvetica", 6, 0.25*cm, max_lineas=1)
            
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(x_offset + 0.5*cm, y_offset + h_rec - 1.0*cm, x_offset + w_rec - 0.5*cm, y_offset + h_rec - 1.0*cm)
            c.setStrokeColorRGB(0, 0, 0)
    
            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_offset + (w_rec/2), y_offset + h_rec - 2.0*cm, 10*cm, "Helvetica-Bold", 26, 0.75*cm, max_lineas=3)
    
            y_inicio_direccion = y_termino_nombre - 0.7*cm
            if y_inicio_direccion > y_offset + 4.3*cm: y_inicio_direccion = y_offset + 4.3*cm
            if y_inicio_direccion < y_offset + 2.9*cm: y_inicio_direccion = y_offset + 2.9*cm
            dibujar_texto_bloque_pro(c, direccion_final, x_offset + (w_rec/2), y_inicio_direccion, 10.0 * cm, "Helvetica-Bold", 14.5, 0.5*cm, max_lineas=3)
    
            c.setLineWidth(0.6)
            y_linea_pie = y_offset + 1.4*cm
            c.line(x_offset + 0.2*cm, y_linea_pie, x_offset + w_rec - 0.2*cm, y_linea_pie)
            
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.4*cm, "FACTURA")
            c.drawCentredString(x_offset + 5.2*cm, y_linea_pie - 0.4*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.5*cm, y_linea_pie - 0.4*cm, "TRANSPORTE")
    
            c.setFont("Helvetica-Bold", 13)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 1.0*cm, str(factura_val))
    
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(x_offset + 5.2*cm, y_linea_pie - 1.0*cm, f"{i + 1} / {total_etqs}")
    
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_offset + 7.5*cm, y_linea_pie - 1.0*cm, transporte_final[:18])
            c.showPage()
    
        c.save()
        return output.getvalue()

    def obtener_datos_github():
        try:
            url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = r.json()
                df = pd.read_csv(io.BytesIO(base64.b64decode(content['content'])))
                return df, content['sha']
        except:
            pass
        return pd.DataFrame(), None
    
    def subir_a_github(df, sha, msg):
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        csv_string = df.to_csv(index=False)
        payload = {"message": msg, "content": base64.b64encode(csv_string.encode()).decode(), "sha": sha}
        return requests.put(url, json=payload, headers=headers).status_code == 200                        

    def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, tel_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, productos, comentarios, paq_nombre, tipo_pago, total_cajas=1):
        filas_prod = ""
        for p in productos:
            filas_prod += f"""
            <tr>
                <td style='padding: 8px; border: 1px solid black;'>{str(p['desc']).upper()}</td>
                <td style='text-align:center; border: 1px solid black;'>-</td>
                <td style='text-align:center; border: 1px solid black;'>PZAS</td>
                <td style='text-align:center; border: 1px solid black;'>{p['cant']}</td>
            </tr>"""
        
        html = f"""
        <style>
            @media print {{
                @page {{ size: letter; margin: 1cm; }}
                body {{ margin: 0; padding: 0; }}
            }}
        </style>
        
        <div id="printable-area" style="font-family:Arial; width:100%; box-sizing:border-box; background: white; color: black; display: flex; flex-direction: column; min-height: 95vh;">
            
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                <div style="text-align: left;">
                    <h1 style="margin: 0; font-size: 18px; font-weight: 900; color: #000;">Jabones y Productos Especializados</h1>
                    <p style="margin: 0; font-size: 11px; font-weight: bold; text-transform: uppercase; color: #444;">Distribución y Logística | 2026</p>
                </div>
                <div style="text-align: right;">
                    <h2 style="margin: 0; font-size: 16px; text-decoration: underline; font-weight: 900;">ORDEN DE EMBARQUE</h2>
                    <p style="margin: 5px 0 0 0; font-size: 13px;"><b>{paq_nombre} - {tipo_pago}</b></p>
                </div>
            </div>
            
            <table style="width:100%; border-collapse:collapse; margin-bottom:15px; font-size: 12px;">
                <tr>
                    <td style="border:1px solid black; padding:6px;"><b>FOLIO:</b> {folio}</td>
                    <td style="border:1px solid black; padding:6px;"><b>ENVÍO:</b> {str(paq).upper()}</td>
                    <td style="border:1px solid black; padding:6px;"><b>ENTREGA:</b> {str(entrega).upper()}</td>
                    <td style="border:1px solid black; padding:6px;"><b>TOTAL CAJAS:</b> <span style="font-size: 13px; font-weight: 900; color: #000;">{total_cajas} </span></td>
                    <td style="border:1px solid black; padding:6px;"><b>FECHA:</b> {fecha}</td>
                </tr>
            </table>
        
            <div style="display:flex; gap:10px; margin-bottom:15px;">
                <div style="flex:1; border:1px solid black;">
                    <div style="background:withe; color:black; text-align:center; font-weight:bold; font-size:12px; padding:4px;">REMITENTE</div>
                    <div style="padding:8px; font-size:11px; line-height:1.4;">
                        <b>JABONES Y PRODUCTOS ESPECIALIZADOS</b><br>
                        C. Cernícalo 155, La Aurora C.P.: 44460<br>
                        ATN: {str(atn_rem).upper()}<br>
                        TEL: {tel_rem}<br>
                        SOLICITÓ: {str(solicitante).upper()}
                    </div>
                </div>
                <div style="flex:1; border:1px solid black;">
                    <div style="background:#ffffff; color:black; text-align:center; font-weight:bold; font-size:12px; padding:4px;">DESTINATARIO</div>
                    <div style="padding:8px; font-size:11px; line-height:1.4;">
                        <b>{str(hotel).upper()}</b><br>
                        {f"{str(calle).upper()}<br>" if calle and calle != "-" else ""}
                        {f"Col: {str(col).upper()} " if col and col != "-" else ""}
                        {f"C.P.: {cp}" if cp and cp != "-" else ""}
                        {"<br>" if (col and col != "-") or (cp and cp != "-") else ""}
                        {str(ciudad).upper()}{f", {str(estado).upper()}" if estado and estado != "-" else ""}<br>
                        ATN: {str(contacto).upper()}
                    </div>
                </div>
            </div>
        
            <div style="flex-grow: 1;">
                <table style="width:100%; border-collapse:collapse; margin-top:5px; font-size:12px;">
                    <tr style="background:#ffffff; color:black;">
                        <th style="padding: 8px; border: 1px solid black;">DESCRIPCIÓN DEL PRODUCTO</th>
                        <th style="border: 1px solid black; width: 100px;">CÓDIGO</th>
                        <th style="border: 1px solid black; width: 80px;">U.M.</th>
                        <th style="border: 1px solid black; width: 80px;">CANT.</th>
                    </tr>
                    {filas_prod}
                </table>
                
                <div style="border:1px solid black; padding:10px; margin-top:15px; font-size:12px; min-height: 80px;">
                    <b>COMENTARIOS:</b><br>{str(comentarios).upper()}
                </div>
            </div>
        
            <div style="margin-top: 40px; padding-bottom: 20px;">
                <div style="text-align:center; font-size:12px; font-weight:bold; margin-bottom:40px; border-bottom: 2px solid black; padding-bottom: 8px;">
                    RECIBO DE CONFORMIDAD DEL CLIENTE
                </div>
                <div style="display:flex; justify-content:space-between; text-align:center; font-size:11px;">
                    <div style="width:30%;">__________________________<br><b>FECHA RECIBO</b></div>
                    <div style="width:35%;">__________________________<br><b>NOMBRE Y FIRMA</b></div>
                    <div style="width:30%;">__________________________<br><b>SELLO DE RECIBIDO</b></div>
                </div>
            </div>
        </div>
        """
        return html
    
    df_actual, sha_actual = obtener_datos_github()
    
    if not df_actual.empty:
        for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL", "ESTATUS"]:
            if col not in df_actual.columns: 
                if col == "ESTATUS":
                    df_actual[col] = "NO SURTIDO"
                else:
                    df_actual[col] = 0.0
        
        nuevo_num = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1)
    else:
        nuevo_num = 1
    
    st.write("")
    with st.container():
        f_paq_nombre = ""
        f_tipo_pago = ""
        
        c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])
        
        f_folio = c1.text_input("FOLIO", value=f"JYP-{nuevo_num}", disabled=True)
        f_paq_sel = c2.selectbox(
            "FORMA DE ENVÍO", 
            ["Envio Pagado", "Envio por cobrar", "Entrega Personal"]
        )
        f_ent_sel = c3.selectbox(
            "TIPO DE ENTREGA", 
            ["Domicilio", "Ocurre Oficina"]
        )
        f_fecha_sel = c4.date_input("FECHA", date.today())
    
    st.divider()
    
    col_rem, col_dest = st.columns(2)
    with col_rem:
        st.markdown(
            '<div style="background:#4e73df;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">REMITENTE</div>', 
            unsafe_allow_html=True
        )
        st.write("")
        st.text_input("Nombre Remitente", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
        
        c_rem1, c_rem2 = st.columns([2, 1])
        f_atn_rem = c_rem1.text_input("Atención", "RIGOBERTO HERNANDEZ")
        f_tel_rem = c_rem2.text_input("Teléfono", "3319753122")
        f_soli = st.text_input(
            "Solicitante / Agente", 
            placeholder="NOMBRE DE QUIEN SOLICITA LAS MUESTRAS",
            key=f"soli_{st.session_state.reset_key}"
        ).upper()
    
    with col_dest:
        st.markdown(
            '<div style="background:#f6c23e;color:black;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">DESTINATARIO / HOTEL</div>', 
            unsafe_allow_html=True
        )
        st.write("")
        f_h = st.text_input("Hotel / Nombre", key=f"h_{st.session_state.reset_key}").upper()
        f_ca = st.text_input("Calle y Número", key=f"ca_{st.session_state.reset_key}").upper()
        
        cd1, cd2 = st.columns(2)
        f_co = cd1.text_input("Colonia", key=f"co_{st.session_state.reset_key}").upper()
        f_cp = cd2.text_input("C.P.", key=f"cp_{st.session_state.reset_key}")
        
        cd3, cd4 = st.columns(2)
        f_ci = cd3.text_input("Ciudad", key=f"ci_{st.session_state.reset_key}").upper()
        f_es = cd4.text_input("Estado", key=f"es_{st.session_state.reset_key}").upper()
        
        f_con = st.text_input(
            "Contacto Receptor", 
            placeholder="NOMBRE Y TELÉFONO DE QUIEN RECIBE",
            key=f"con_{st.session_state.reset_key}"
        ).upper()
    
    st.divider()
    
    st.markdown("""
        <style>
        .stMultiSelect div[data-baseweb="select"] {
            height: auto !important;
            min-height: 45px !important;
        }
        .stMultiSelect div[data-baseweb="valueContainer"] {
            flex-wrap: wrap !important;
            display: flex !important;
            gap: 5px !important;
            padding: 5px 0 !important;
        }
        .stMultiSelect div[data-baseweb="tag"] {
            background-color: #384A52 !important;
            border-radius: 5px;
            color: white !important;
        }
        div[data-testid="stNumberInput"] {
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.subheader("SELECCION DE PRODUCTOS")
    
    if "seleccionados_muestras" not in st.session_state:
        st.session_state.seleccionados_muestras = []
    
    def eliminar_producto(prod_a_borrar):
        st.session_state.seleccionados_muestras = [p for p in st.session_state.seleccionados_muestras if p != prod_a_borrar]
    
    seleccionados = st.multiselect(
        "Busca y selecciona productos:", 
        list(precios.keys()),
        key=f"prod_select_{st.session_state.reset_key}",
        default=st.session_state.get('seleccionados_muestras', []),
        placeholder="SELECCIONAR PRODUCTOS"
    )
    
    st.session_state.seleccionados_muestras = seleccionados
    
    prods_actuales = []
    total_cantidad = 0
    total_costo_prods = 0
    
    if seleccionados:
        st.info(f"Has seleccionado {len(seleccionados)} productos. Indica las cantidades abajo:")
        
        num_filas = (len(seleccionados) + 2) // 3  
        altura_dinamica = min(max(num_filas * 95, 120), 500) 
        
        with st.container(height=altura_dinamica, border=True):
            col_bloque_1, col_bloque_2, col_bloque_3 = st.columns(3)
            
            for i, p in enumerate(seleccionados):
                if i % 3 == 0:
                    target_col = col_bloque_1
                elif i % 3 == 1:
                    target_col = col_bloque_2
                else:
                    target_col = col_bloque_3
                
                with target_col:
                    c1, c2, c3 = st.columns([1.5, 1.8, 0.5])
                    
                    with c1:
                        st.markdown(f"<div style='padding-top:10px; font-size:10px; line-height:1.1;'><b>{p.upper()}</b></div>", unsafe_allow_html=True)
                    
                    with c2:
                        q = st.number_input("Cant", min_value=0, step=1, key=f"q_{p}", label_visibility="collapsed")
                    
                    with c3:
                        st.button("🗑️", key=f"btn_del_{p}", type="tertiary", on_click=eliminar_producto, args=(p,))
    
                    if q > 0:
                        prods_actuales.append({"desc": p, "cant": q})
                        total_cantidad += q
                        total_costo_prods += (q * (precios.get(p, 0)))
                    
                    st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    
    st.markdown("---")
    f_coment = st.text_area(
        "💬 COMENTARIOS ADICIONALES", 
        height=100, 
        placeholder="SI EL PRODUCTO NO ESTA EN LA LISTA SELECCIONABLE, INGRESALOS AQUI O CUALQUIER COMENTARIO ADICIONAL"
    ).upper()
    
    st.write("")
    st.write("")
    
    col_b1, col_b2, col_b3 = st.columns([1, 1, 0.5]) 

    if col_b1.button("GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
        if not f_h: 
            st.error("Falta el hotel")
        elif not f_soli:
            st.error("Falta el nombre de quien solicita (Solicitante / Agente)")
        elif not f_con: 
            st.error("Falta el nombre y teléfono de quien recibe")
        elif not prods_actuales: 
            st.error("Selecciona al menos un producto")
        else:
            direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()
            
            reg = {
                "FOLIO": nuevo_num, 
                "ESTATUS": "NO SURTIDO",
                "FECHA": f_fecha_sel.strftime("%Y-%m-%d"), 
                "NOMBRE DEL HOTEL": f_h.upper(), 
                "DESTINO": direccion_completa,
                "CONTACTO": f_con.upper(), 
                "SOLICITO": f_soli.upper(),
                "PAQUETERIA": f_paq_sel.upper(),
                "PAQUETERIA_NOMBRE": f_paq_nombre,
                "NUMERO_GUIA": "", 
                "COSTO_GUIA": 0.0,
                "CANTIDAD_TOTAL": total_cantidad,
                "COSTO_TOTAL": round(total_costo_prods, 2),
                "COMENTARIOS": f_coment
            }
            
            for p in precios.keys():
                reg[p] = 0
            for item in prods_actuales:
                reg[item["desc"]] = item["cant"]
            
            df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
            
            if subir_a_github(df_f, sha_actual, f"Folio JYP-{nuevo_num}"):
                st.session_state.folio_actual = nuevo_num
                st.session_state.folio_guardado = True 
                
                st.success(f"¡Guardado correctamente! Folio: JYP-{nuevo_num}")
                time.sleep(1)
                st.rerun()

    if not st.session_state.folio_guardado:
        st.markdown("""
            <div style="background-color: rgba(255, 165, 0, 0.1); border-left: 5px solid #FFA500; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                <span style="color: white; font-size: 14px;">
                    <b style="color: #FFA500;">BLOQUEO DE SEGURIDAD:</b> 
                    Debes guardar el registro antes de poder imprimir.
                </span>
            </div>
        """, unsafe_allow_html=True)

    if col_b2.button("GUARDAR PDF", use_container_width=True, disabled=not st.session_state.folio_guardado):
        folio_final = st.session_state.get("folio_actual", nuevo_num - 1)
        folio_simple = f"JYP-{folio_final}" 
        
        h_print = generar_html_impresion(
            folio_simple, 
            f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem, 
            f_soli, f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, 
            prods_actuales, f_coment, f_paq_nombre, f_tipo_pago
        )
        
        js_code = f"""
            <html>
                <head><title>{folio_simple}_{f_h}</title></head>
                <body>
                    {h_print}
                    <script>setTimeout(function(){{ window.print(); }}, 500);</script>
                </body>
            </html>
        """
        components.html(js_code, height=0)

    if col_b3.button("BORRAR", use_container_width=True):
        st.session_state.folio_guardado = False
        if "folio_actual" in st.session_state:
            del st.session_state.folio_actual
        st.session_state.seleccionados_muestras = []
        st.session_state.reset_key += 1
        st.rerun()

    st.write("")
    st.write("")
    st.write("")                            
    
    with st.expander("🔍 CONSULTA DE FOLIOS Y GUIAS", expanded=True):
        if not df_actual.empty:
            busqueda = st.text_input("Escribe el nombre del Hotel, Solicitante o Folio para filtrar:").upper()
            
            df_vista = df_actual.copy()
            df_vista = df_vista.fillna('') 
            
            if busqueda:
                df_vista = df_vista[df_vista.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            
            df_render = df_vista.sort_values(by="FOLIO", ascending=False)
            data_busqueda = df_render.to_dict('records')
            
            alto_busqueda = min(len(data_busqueda) * 130 + 20, 550) 
            
            tarjetas_busqueda_html = ""
            for item in data_busqueda:
                detalle_p_busqueda = ""
                for p_key in precios.keys():
                    cant_p = pd.to_numeric(item.get(p_key, 0), errors='coerce')
                    if pd.notna(cant_p) and cant_p > 0:
                        detalle_p_busqueda += f"• {int(cant_p)} PZAS {str(p_key).upper()}<br>"
                
                estatus_val = str(item.get('ESTATUS', 'NO SURTIDO')).upper()
                if estatus_val == 'DESPACHADO':
                    badge_status = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:2px 6px; border-radius:10px; font-size:8px; font-weight:800; letter-spacing:1px;'>✓ DESPACHADO</div>"
                else:
                    badge_status = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:2px 6px; border-radius:10px; font-size:8px; font-weight:800; letter-spacing:1px; box-shadow: 0 0 8px rgba(255,68,68,0.4);'>⚠️ NO SURTIDO</div>"
                
                paq_text = item.get('PAQUETERÍA', '') or item.get('PAQUETERIA_NOMBRE', '')
                guia_text = item.get('NÚMERO DE GUÍA', '') or item.get('NUMERO_GUIA', '')
                
                tarjetas_busqueda_html += f"""
                <div class="card-busqueda" style="padding: 15px; margin-bottom: 10px; background: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1.1;">
                        <div class="label-mini">Folio / Fecha</div>
                        <div class="val-folio">#{str(item['FOLIO'])}</div>
                        <div style="color: rgba(255,255,255,0.5); font-size: 10px; margin-bottom: 5px;">{str(item['FECHA'])[:10]}</div>
                        {badge_status}
                    </div>
                    <div style="flex: 2.0; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                        <div class="label-mini">Hotel / Destino</div>
                        <div class="val-hotel">{str(item.get('NOMBRE DEL HOTEL', ''))[:30]}</div>
                        <div class="val-soli">SOLICITÓ: {str(item.get('SOLICITO', ''))[:30]}</div>
                    </div>
                    <div style="flex: 2.5; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                        <div class="label-mini">Productos Solicitados</div>
                        <div style="color: #FFFFFF; font-size: 9px; line-height: 1.4; opacity: 0.9;">{detalle_p_busqueda if detalle_p_busqueda else '<i>Sin detalle</i>'}</div>
                    </div>
                    <div style="flex: 1.6; text-align: right; border-left: 1px solid rgba(255,255,255,0.05); padding-left: 10px;">
                        <div class="val-guia {'pendiente' if not paq_text else ''}">
                            { paq_text if paq_text else 'PAQUETERÍA PENDIENTE' }
                        </div>
                        <div class="val-sub-guia {'pendiente' if not guia_text else ''}">
                            { guia_text if guia_text else 'GUÍA PENDIENTE' }
                        </div>
                    </div>
                </div>
                """

            html_busqueda = f"""
            <div style="font-family: 'Inter', sans-serif; padding-right: 10px; height: {alto_busqueda}px; overflow-y: auto;">
                <style>
                    body {{ background: transparent; margin: 0; padding: 0; }}
                    ::-webkit-scrollbar {{ width: 8px; }}
                    ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                    ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; min-height: 50px; }}
                    ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                    
                    .card-busqueda {{
                        transition: all 0.3s ease;
                    }}
                    .card-busqueda:hover {{ border-color: #38bdf8; background: #2d3b42; transform: translateX(5px); }}
                    .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }}
                    .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }}
                    .val-hotel {{ color: #FFFFFF; font-size: 13px; font-weight: 700; margin-top: 2px; }}
                    .val-soli {{ color: #FFD700; font-size: 10px; font-weight: 600; margin-top: 2px; opacity: 0.8; }}
                    .val-guia {{ color: #38bdf8; font-family: monospace; font-size: 14px; font-weight: 800; line-height: 1.2; }}
                    .val-sub-guia {{ color: #FFFFFF; font-family: monospace; font-size: 12px; font-weight: 700; margin-top: 4px; }}
                    .pendiente {{ color: #f97316 !important; font-style: italic; opacity: 0.8; font-size: 10px; font-weight: 400; }}
                </style>
                {tarjetas_busqueda_html}
            </div>
            """
            components.html(html_busqueda, height=alto_busqueda, scrolling=False)
        else:
            st.info("No hay registros todavía.")
            
    st.divider()
    st.write("")
    
    lista_admins = ["Rigoberto", "JMoreno"]
    usuario_logeado = st.session_state.get('usuario_activo', 'Invitado')
    
    if usuario_logeado in lista_admins:
        st.markdown("### 🛠 PANEL DE ADMINISTRACIÓN, PARA USO EXCLUSIVO DE LOGÍSTICA")
        t1, t2, t3 = st.tabs(["Gestionar Folios Existentes", "Historial y Reportes", "Edicion"])
        
        with t1:
            contenedor_aviso = st.empty()
            if not df_actual.empty:
                st.markdown("""
                <style>
                div[data-testid="stButton"] button {
                    background-color: #263238 !important; 
                    color: #FFFFFF !important;
                    border: 1px solid #44555A !important;
                    transition: all 0.3s ease-in-out !important;
                }
                div[data-testid="stButton"] button:hover {
                    background-color: #00A3A3 !important;
                    color: #FFFFFF !important;
                    border-color: #00A3A3 !important;
                    box-shadow: 0 0 15px rgba(0, 196, 180, 0.5) !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
                opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]
                
                fol_sel_texto = st.selectbox(
                    "Seleccionar Folio para procesar (Logística):", 
                    opciones_folios, 
                    index=None, 
                    placeholder="Busca el folio que envió Ventas..."
                )
                
                datos_fol = None
                fol_edit = None
    
                if fol_sel_texto:
                    fol_edit = int(fol_sel_texto.split(" - ")[0])
                    datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]

                    detalle_p_admin = ""
                    for p in precios.keys():
                        cant_admin = datos_fol.get(p, 0)
                        if cant_admin > 0:
                            detalle_p_admin += f"• {int(cant_admin)} PZAS {str(p).upper()}<br>"
                    
                    estatus_admin = str(datos_fol.get('ESTATUS', 'NO SURTIDO')).upper()
                    if estatus_admin == "DESPACHADO":
                        badge_admin = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:4px 10px; border-radius:12px; font-size:10px; font-weight:800; letter-spacing:1px; margin-top:8px;'>✓ DESPACHADO</div>"
                        borde_color = "#00FFAA"
                    else:
                        badge_admin = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:4px 10px; border-radius:12px; font-size:10px; font-weight:800; letter-spacing:1px; margin-top:8px; box-shadow: 0 0 10px rgba(255,68,68,0.3);'>⚠️ NO SURTIDO</div>"
                        borde_color = "#FF4444"

                    st.markdown(f"""
                    <div style="background: #263238; border: 1px solid rgba(255,255,255,0.05); border-left: 6px solid {borde_color}; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; padding: 20px 30px; margin-top: 15px; margin-bottom: 5px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                        <div style="flex: 1.2;">
                            <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:4px;">FOLIO A PROCESAR</div>
                            <div style="color: {borde_color}; font-family: monospace; font-size: 22px; font-weight: 900; line-height:1;">#{datos_fol['FOLIO']}</div>
                            <div style="color: rgba(255,255,255,0.5); font-size: 11px; margin-top: 4px;">{datos_fol['FECHA']}</div>
                            {badge_admin}
                        </div>
                        <div style="flex: 2.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:4px;">DESTINO / HOTEL</div>
                            <div style="color: #FFFFFF; font-size: 14px; font-weight: 800; margin-bottom: 2px;">{str(datos_fol.get('NOMBRE DEL HOTEL','')).upper()}</div>
                            <div style="color: #38bdf8; font-size: 11px; font-weight: 700; margin-bottom: 4px;">Atn: {str(datos_fol.get('CONTACTO','')).upper()}</div>
                            <div style="color: rgba(255,255,255,0.5); font-size: 10px; line-height:1.4;">{str(datos_fol.get('DESTINO','')).upper()}</div>
                        </div>
                        <div style="flex: 2.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:6px;">PRODUCTOS SOLICITADOS</div>
                            <div style="color: #FFFFFF; font-size: 10px; line-height: 1.6; opacity: 0.9;">{detalle_p_admin if detalle_p_admin else '<i>Sin detalle de productos</i>'}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider() 
                c_adm1, c_adm2 = st.columns(2)
                
                with c_adm1:
                    st.subheader("1. ASIGNAR DATOS DE ENVIO")
                    n_paq_nombre = st.selectbox("Nombre de Paquetería", 
                        ["AEREO", "NO APLICA","TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES", "FEDEX", "PAQMEX", "TINY PACK"],
                        index=None, placeholder="Selecciona paquetería...")
                    
                    n_tipo_pago = st.selectbox("Modalidad de Pago", 
                        ["NO APLICA","CREDITO", "COBRO DESTINO"],
                        index=None, placeholder="¿Cómo se paga?")
                    
                    n_gui = st.text_input("Número de Guía").upper()
                    n_costo_guia = st.number_input("Costo de Flete ($)", min_value=0.0)
                    
                    val_def_cajas = int(datos_fol.get('CANTIDAD_TOTAL', 1)) if datos_fol is not None else 1
                    n_total_cajas = st.number_input("Cantidad Final de Cajas / Bultos", min_value=1, max_value=100, value=max(val_def_cajas, 1), step=1)
                    
                    btn_guardar = st.button("GUARDAR Y ACTUALIZAR FOLIO", 
                                                use_container_width=True, 
                                                disabled=not fol_sel_texto)
                    
                    if btn_guardar and datos_fol is not None:
                        idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                        df_actual.at[idx, "PAQUETERIA_NOMBRE"] = n_paq_nombre
                        df_actual.at[idx, "MODALIDAD_PAGO"] = n_tipo_pago
                        df_actual.at[idx, "NUMERO_GUIA"] = n_gui
                        df_actual.at[idx, "COSTO_GUIA"] = n_costo_guia
                        df_actual.at[idx, "CANTIDAD_TOTAL"] = n_total_cajas 
                        df_actual.at[idx, "ESTATUS"] = "DESPACHADO" 
                        
                        if subir_a_github(df_actual, sha_actual, f"Logistica Folio {fol_edit}"):
                            st.success(f"FOLIO JYP-{fol_edit} GUARDADO")
                            time.sleep(1.5)
                            st.rerun()
                
                with c_adm2:
                    st.subheader("2. IMPRESION FINAL")
                    st.info("Verifica los datos antes de imprimir. La base de datos no se afecta hasta que guardes.")
                    
                    btn_imprimir = st.button("IMPRIMIR FORMATO ACTUALIZADO", 
                                                use_container_width=True, 
                                                disabled=not fol_sel_texto)
                    
                    if btn_imprimir and datos_fol is not None:
                        prods_re = []
                        for p in precios.keys():
                            if p in datos_fol and datos_fol[p] > 0: 
                                prods_re.append({"desc": p, "cant": int(datos_fol[p])})
                        
                        paq_a_imprimir = n_paq_nombre if n_paq_nombre else datos_fol.get("PAQUETERIA_NOMBRE", "S/P")
                        pago_a_imprimir = n_tipo_pago if n_tipo_pago else datos_fol.get("MODALIDAD_PAGO", "PENDIENTE")
                
                        h_re = generar_html_impresion(
                            f"JYP-{int(datos_fol['FOLIO'])}", 
                            datos_fol.get("PAQUETERIA", "ENVIO"), 
                            datos_fol.get("TIPO_ENTREGA", "DOMICILIO"), 
                            datos_fol["FECHA"], 
                            "RIGOBERTO HERNANDEZ", 
                            "3319753122", 
                            datos_fol["SOLICITO"], 
                            datos_fol["NOMBRE DEL HOTEL"], 
                            "", "", "", 
                            datos_fol["DESTINO"], 
                            "", 
                            datos_fol["CONTACTO"], 
                            prods_re, 
                            datos_fol.get("COMENTARIOS", "RE-IMPRESIÓN DE LOGÍSTICA"), 
                            paq_a_imprimir, 
                            pago_a_imprimir,
                            total_cajas=n_total_cajas 
                        )
                        components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)
                    
                    st.write("")
                    
                    if fol_sel_texto and datos_fol is not None:
                        cant_etiquetas_sel = n_total_cajas 
                        transporte_etq = n_paq_nombre if n_paq_nombre else datos_fol.get("PAQUETERIA_NOMBRE", datos_fol.get("PAQUETERIA", "TRES GUERRAS"))
                        
                        pdf_etq_bytes = generar_etiquetas_limpias(
                            reg_datos=datos_fol,
                            total_etqs=int(cant_etiquetas_sel),
                            factura_val=f"JYP-{int(datos_fol['FOLIO'])}",
                            transporte_val=transporte_etq
                        )
                        
                        st.download_button(
                            label="DESCARGAR ETIQUETA PDF",
                            data=pdf_etq_bytes,
                            file_name=f"Etiqueta_JYP-{int(datos_fol['FOLIO'])}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
        
        with t2:
            if not df_actual.empty:
                st.write("")
                df_actual['FECHA'] = df_actual['FECHA'].astype(str).str.strip()
                df_actual['FECHA_DT'] = pd.to_datetime(df_actual['FECHA'], format='%Y-%m-%d', errors='coerce')
                df_actual['FECHA_DT'] = df_actual['FECHA_DT'].fillna(
                    pd.to_datetime(df_actual['FECHA'], dayfirst=True, errors='coerce')
                )
                df_actual['MES_FILTRO'] = df_actual['FECHA_DT'].dt.strftime('%m - %Y').fillna("SIN FECHA")
            
                meses_lista = sorted([m for m in df_actual['MES_FILTRO'].unique() if m != "SIN FECHA"], reverse=True)
                if "SIN FECHA" in df_actual['MES_FILTRO'].values:
                    meses_lista.append("SIN FECHA")
            
                col_f1, col_f2 = st.columns([1.5, 2.5])
                mes_sel = col_f1.selectbox(
                    "FILTRAR PERIODO", 
                    ["MOSTRAR TODO"] + meses_lista
                )
            
                if mes_sel != "MOSTRAR TODO":
                    df_render = df_actual[df_actual['MES_FILTRO'] == mes_sel].copy()
                else:
                    df_render = df_actual.copy()
            
                t_prod = df_render["COSTO_TOTAL"].sum()
                t_flete = df_render["COSTO_GUIA"].sum()
                filas_html = ""
                tarjetas_html = ""
                
                df_render = df_render.fillna(0)
                df_render = df_render.sort_values(by="FOLIO", ascending=False)
                
                for _, r in df_render.iterrows():
                    detalle_p = ""
                    for p in precios.keys():
                        cant = r.get(p, 0)
                        if cant > 0: 
                            detalle_p += f"• {int(cant)} PZAS {str(p).upper()}<br>"
                    
                    estatus_bd = str(r.get('ESTATUS', 'NO SURTIDO')).upper()
                    if estatus_bd == "DESPACHADO":
                        badge_html = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:2px 8px; border-radius:12px; font-size:9px; font-weight:800; letter-spacing:1px; margin-top:5px;'>✓ DESPACHADO</div>"
                    else:
                        badge_html = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:2px 8px; border-radius:12px; font-size:9px; font-weight:800; letter-spacing:1px; margin-top:5px; box-shadow: 0 0 8px rgba(255,68,68,0.4);'>⚠️ NO SURTIDO</div>"
                    
                    filas_html += f"""
                    <tr style="page-break-inside: avoid;">
                        <td style='border:1px solid black; padding:6px; text-align:center; font-size:10px; width:7%;'>{r['FOLIO']}</td>
                        <td style='border:1px solid black; padding:6px; font-size:10px; width:15%;'>
                            <b style='color:black;'>{str(r['SOLICITO']).upper()}</b><br>
                            <small style='font-size:8px; color:#444;'>{r['FECHA']}</small>
                        </td>
                        <td style='border:1px solid black; padding:6px; font-size:10px; width:25%;'>
                            <b>{str(r['NOMBRE DEL HOTEL']).upper()}</b><br>
                            <small style='font-size:8px; color:#333;'>{str(r['DESTINO']).upper()}</small>
                        </td>
                        <td style='border:1px solid black; padding:6px; font-size:9px; line-height:1.3; width:33%;'>
                            {detalle_p}
                        </td>
                        <td style='border:1px solid black; padding:6px; text-align:right; font-size:10px; width:10%; white-space:nowrap;'>
                            <b>${r['COSTO_TOTAL']:,.2f}</b>
                        </td>
                        <td style='border:1px solid black; padding:6px; text-align:right; font-size:10px; width:10%; white-space:nowrap;'>
                            ${r['COSTO_GUIA']:,.2f}
                        </td>
                    </tr>"""

                    tarjetas_html += f"""
                    <div class="card-reporte" style="padding: 20px 30px; margin-bottom: 15px;">
                        <div class="col-folio" style="flex: 1;">
                            <div class="label-mini">FOLIO</div>
                            <div class="val-folio" style="margin-bottom: 5px;">#{r['FOLIO']}</div>
                            <div class="val-sub">{r['FECHA']}</div>
                            {badge_html}
                        </div>
                        <div class="col-info" style="flex: 2.5; padding: 0 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div class="label-mini">SOLICITANTE / DESTINO</div>
                            <div class="val-main" style="margin-bottom: 4px;">{str(r['SOLICITO']).upper()}</div>
                            <div class="val-sub">{str(r['NOMBRE DEL HOTEL']).upper()}</div>
                            <div class="val-sub" style="opacity: 0.7;">{str(r['DESTINO']).upper()}</div>
                        </div>
                        <div class="col-detalle" style="flex: 2.5; padding: 0 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div class="label-mini">DESGLOSE PRODUCTOS</div>
                            <div class="val-list" style="line-height: 1.6;">{detalle_p if detalle_p else 'SIN DETALLE'}</div>
                        </div>
                        <div class="col-costos" style="flex: 1.5; text-align: right; padding-left: 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div class="label-mini">INVERSIÓN</div>
                            <div class="val-costo" style="font-size: 14px; margin-bottom: 5px;">Prod: ${r['COSTO_TOTAL']:,.2f}</div>
                            <div class="val-flete" style="font-size: 14px;">Flete: ${r['COSTO_GUIA']:,.2f}</div>
                        </div>
                    </div>"""

                st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <p style='color:#00FFAA; font-weight:800; letter-spacing:2px; font-size:14px; margin:0;'>VISTA: {mes_sel}</p>
                        <p style='color:#FFFFFF; font-size:12px; opacity:0.6;'>Mostrando {len(df_render)} registros</p>
                    </div>
                """, unsafe_allow_html=True)

                html_final = f"""
                <div style="font-family: 'Inter', sans-serif;">
                    <style>
                        body {{ background: transparent; margin: 0; padding: 0; }}
                        .container-reporte {{ height: 500px; overflow-y: auto; padding-right: 10px; }}
                        .card-reporte {{ background: #263238; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; display: flex; min-width: 800px; justify-content: space-between; align-items: center; transition: 0.3s; }}
                        .card-reporte:hover {{ border-color: #38bdf8; background: #2d3b42; }}
                        .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px; }}
                        .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }}
                        .val-main {{ color: #FFFFFF; font-size: 12px; font-weight: 700; }}
                        .val-sub {{ color: rgba(255,255,255,0.5); font-size: 10px; }}
                        .val-list {{ color: #FFFFFF; font-size: 9px; line-height: 1.4; opacity: 0.8; }}
                        .val-costo {{ color: #38bdf8; font-size: 13px; font-weight: 700; font-family: monospace; }}
                        .val-flete {{ color: #a855f7; font-size: 13px; font-weight: 700; font-family: monospace; }}
                        ::-webkit-scrollbar {{ width: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                    </style>
                    <div class="container-reporte">{tarjetas_html}</div>
                </div>"""
                components.html(html_final, height=520, scrolling=False)

                st.markdown(f"""
                    <div style="background:#263238; border-top: 4px solid #00FFAA; border-radius: 0 0 12px 12px; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                        <div style="color:rgba(255,255,255,0.6); font-size:12px;">PRODUCTOS: <span style="color:white; font-weight:bold;">${t_prod:,.2f}</span></div>
                        <div style="color:rgba(255,255,255,0.6); font-size:12px;">FLETES: <span style="color:white; font-weight:bold;">${t_flete:,.2f}</span></div>
                        <div style="color:#00FFAA; font-size:16px; font-weight:800; letter-spacing:1px;">TOTAL FILTRADO: ${(t_prod+t_flete):,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                with c1:
                    form_pt_html = f"<html><head><style>@media print{{@page{{size:letter landscape;margin:1cm;}} body{{margin:0;padding:0;width:100% !important;font-family:sans-serif;}} .no-print{{display:none;}}}} table{{width:100% !important;border-collapse:collapse;margin-top:15px;table-layout:fixed;}} th{{background:#eee !important;border:1px solid black;padding:8px;font-size:11px;-webkit-print-color-adjust:exact;}} td{{border:1px solid black;padding:6px;font-size:10px;vertical-align:top;word-wrap:break-word;}}</style></head><body><div style='display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px solid black;padding-bottom:10px;'><div><h1 style='margin:0;font-size:18px;font-weight:900;'>Jabones y Productos Especializados</h1><p style='margin:0;font-size:10px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;'>distribucion y Logistica 2026</p></div><div style='text-align:right;'><h2 style='margin:0;font-size:16px;text-decoration:underline;'>Reporte de Envio de Muestras</h2><p style='margin:5px 0 0 0;font-size:12px;'><b>GENERADO: {date.today().strftime('%d/%m/%Y')}</b></p></div></div><table><thead><tr><th style='width:7%;'>FOLIO</th><th style='width:15%;'>SOLICITANTE</th><th style='width:25%;'>DESTINO / HOTEL</th><th style='width:33%;'>DETALLE DE PRODUCTOS</th><th style='width:10%;'>COSTO PROD.</th><th style='width:10%;'>FLETE</th></tr></thead><tbody>{filas_html}</tbody></table><div style='text-align:right;margin-top:20px;border-top:2px solid black;padding-top:10px;font-family:monospace;'><p style='margin:2px 0;'>TOTAL PRODUCTOS: <b>${t_prod:,.2f}</b></p><p style='margin:2px 0;'>TOTAL FLETES: <b>${t_flete:,.2f}</b></p><h3 style='margin:8px 0;font-size:20px;'>INVERSIÓN TOTAL: ${(t_prod+t_flete):,.2f}</h3></div></body></html>"
                    if st.button("IMPRIMIR REPORTE", type="primary", use_container_width=True):
                        components.html(f"{form_pt_html}<script>window.print();</script>", height=0)
                with c2:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_render.drop(columns=['FECHA_DT', 'MES_FILTRO']).to_excel(writer, index=False)
                    st.download_button(f"EXCEL {mes_sel}", data=output.getvalue(), file_name=f"JYPESA_Muestras_{mes_sel}.xlsx", use_container_width=True)
                with c3:
                    if st.button("ACTUALIZAR", use_container_width=True): st.rerun()
            else:
                st.info("No hay registros todavía.")

        with t3:
            st.markdown("### EDICIÓN TOTAL DE MATRIZ DE MUESTRAS")
            st.info("Modifica cualquier registro de la base de datos de manera directa. Los cambios se sincronizarán y actualizarán en GitHub al guardar.")
        
            st.markdown("""
                <style>
                    div[data-testid="stForm"] button,
                    div[data-testid="stForm"] button:focus,
                    div[data-testid="stForm"] button:active {
                        background-color: #263238 !important;
                        color: #FFFFFF !important;
                        border: 1px solid #44555A !important;
                        width: 100% !important;
                        border-radius: 4px !important;
                        font-weight: 400 !important;
                        box-shadow: none !important;
                        outline: none !important;
                    }
                    div[data-testid="stForm"] button:hover {
                        background-color: #00A3A3 !important;
                        border-color: #00A3A3 !important;
                        color: #FFFFFF !important;
                        box-shadow: 0 0 15px rgba(0, 196, 180, 0.5) !important;
                    }
                </style>
            """, unsafe_allow_html=True)
        
            if df_actual.empty:
                st.warning("No hay registros en la matriz de muestras para editar.")
            else:
                df_sorted_edit = df_actual.sort_values(by="FOLIO", ascending=False)
                opciones_edit = [f"Folio #{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']} ({r['FECHA']})" for _, r in df_sorted_edit.iterrows()]
                
                folio_a_editar = st.selectbox(
                    "Selecciona el Folio que deseas modificar o eliminar:",
                    opciones_edit,
                    index=None,
                    placeholder="Escribe el folio o nombre del hotel...",
                    key="select_folio_edicion_total"
                )
        
                if folio_a_editar:
                    num_folio_sel = int(folio_a_editar.split(" - ")[0].replace("Folio #", ""))
                    idx_fila = df_actual.index[df_actual['FOLIO'] == num_folio_sel].tolist()[0]
                    registro_sel = df_actual.loc[idx_fila]
        
                    st.markdown("---")
                    st.subheader(f"Editando: JYP-{num_folio_sel}")
        
                    with st.form(key=f"form_edicion_{num_folio_sel}"):
                        col_e1, col_e2, col_e3 = st.columns(3)
                        
                        with col_e1:
                            nuevo_hotel = st.text_input("Nombre del Hotel", value=str(registro_sel.get("NOMBRE DEL HOTEL", ""))).upper()
                            nuevo_solicito = st.text_input("Solicitante", value=str(registro_sel.get("SOLICITO", ""))).upper()
                            nuevo_estatus = st.selectbox(
                                "Estatus", 
                                ["NO SURTIDO", "DESPACHADO"], 
                                index=0 if str(registro_sel.get("ESTATUS", "NO SURTIDO")) == "NO SURTIDO" else 1
                            )
        
                        with col_e2:
                            nuevo_destino = st.text_area("Destino / Dirección", value=str(registro_sel.get("DESTINO", ""))).upper()
                            nuevo_contacto = st.text_input("Contacto Receptor", value=str(registro_sel.get("CONTACTO", ""))).upper()
        
                        with col_e3:
                            nueva_paqueteria = st.text_input("Paquetería", value=str(registro_sel.get("PAQUETERIA_NOMBRE", registro_sel.get("PAQUETERIA", "")))).upper()
                            nueva_guia = st.text_input("Número de Guía", value=str(registro_sel.get("NUMERO_GUIA", ""))).upper()
                            nuevo_costo_guia = st.number_input("Costo Guía / Flete ($)", min_value=0.0, value=float(registro_sel.get("COSTO_GUIA", 0.0)))
        
                        st.markdown("##### 📦 Modificar Cantidades de Productos")
                        st.write("Ajusta las piezas de los productos incluidos en este folio:")
        
                        nuevas_cantidades = {}
                        cols_prods = st.columns(3)
                        
                        keys_precios = list(precios.keys())
                        for i, prod in enumerate(keys_precios):
                            val_bruto = registro_sel.get(prod, 0)
                            try:
                                cant_actual = int(val_bruto) if pd.notna(val_bruto) and str(val_bruto).strip() != "" else 0
                            except (ValueError, TypeError):
                                cant_actual = 0
        
                            col_target = cols_prods[i % 3]
                            with col_target:
                                nuevas_cantidades[prod] = st.number_input(
                                    f"{prod[:28]}", 
                                    min_value=0, 
                                    step=1, 
                                    value=cant_actual, 
                                    key=f"edit_{num_folio_sel}_{prod}"
                                )
        
                        nuevo_comentario = st.text_area("Comentarios Adicionales", value=str(registro_sel.get("COMENTARIOS", ""))).upper()
        
                        st.markdown("---")
                        
                        col_btn_1, col_btn_2 = st.columns([2, 1])
                        
                        guardar_cambios = col_btn_1.form_submit_button("GUARDAR CAMBIOS EN ESTE FOLIO", use_container_width=True)
                        eliminar_registro = col_btn_2.form_submit_button("ELIMINAR ESTE FOLIO", use_container_width=True)
        
                        if guardar_cambios:
                            total_cants = sum(nuevas_cantidades.values())
                            total_cost_p = sum(qty * precios.get(p_key, 0) for p_key, qty in nuevas_cantidades.items())
        
                            df_actual.at[idx_fila, "NOMBRE DEL HOTEL"] = nuevo_hotel
                            df_actual.at[idx_fila, "SOLICITO"] = nuevo_solicito
                            df_actual.at[idx_fila, "ESTATUS"] = nuevo_estatus
                            df_actual.at[idx_fila, "DESTINO"] = nuevo_destino
                            df_actual.at[idx_fila, "CONTACTO"] = nuevo_contacto
                            df_actual.at[idx_fila, "PAQUETERIA_NOMBRE"] = nueva_paqueteria
                            df_actual.at[idx_fila, "NUMERO_GUIA"] = nueva_guia
                            df_actual.at[idx_fila, "COSTO_GUIA"] = nuevo_costo_guia
                            df_actual.at[idx_fila, "CANTIDAD_TOTAL"] = total_cants
                            df_actual.at[idx_fila, "COSTO_TOTAL"] = round(total_cost_p, 2)
                            df_actual.at[idx_fila, "COMENTARIOS"] = nuevo_comentario
        
                            for p_key, qty in nuevas_cantidades.items():
                                df_actual.at[idx_fila, p_key] = qty
        
                            if subir_a_github(df_actual, sha_actual, f"Edicion total Folio JYP-{num_folio_sel}"):
                                st.success(f"¡Folio JYP-{num_folio_sel} actualizado y sincronizado correctamente!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Error al sincronizar con GitHub. Verifica tus credenciales.")
        
                        if eliminar_registro:
                            df_actual = df_actual.drop(idx_fila).reset_index(drop=True)
                            
                            if subir_a_github(df_actual, sha_actual, f"Eliminacion Folio JYP-{num_folio_sel}"):
                                st.success(f"¡El folio JYP-{num_folio_sel} ha sido eliminado permanentemente!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Error al eliminar el registro en GitHub.")
    else:
        html_restringido = f"""<div style="background-color:{vars_css['card']}; border:1px solid {vars_css['border']}; border-left:8px solid #F7C300; padding:18px 40px; border-radius:10px; margin:15px 0; box-shadow:0 6px 20px rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:space-between;"><div style="display:flex; align-items:center; gap:25px;"><span style="font-size:28px;">🔐</span><div style="text-align:left;"><span style="color:#F7C300; font-weight:900; font-size:14px; letter-spacing:3px; text-transform:uppercase; display:block; margin-bottom:4px;">ÁREA RESTRINGIDA</span><span style="color:{vars_css['text']}; font-size:14px; font-weight:500; opacity:0.9;">El perfil de operador <b>{usuario_logeado}</b> no cuenta con privilegios de nivel <b>Logística</b>.</span></div></div><div style="padding:6px 16px; border:1px solid rgba(247,195,0,0.5); background:rgba(247,195,0,0.1); border-radius:6px; font-size:11px; color:#F7C300; font-weight:900; letter-spacing:1px;">ID ACCESO: {st.session_state.get('usuario_activo', 'ERR')}</div></div>"""
        st.markdown(html_restringido, unsafe_allow_html=True)


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
