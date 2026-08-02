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

# ── TEMA Y CSS MAESTROS (ESTILO CHIC / MINIMALISTA / HIGH-FASHION & LOGISTICS) ──
vars_css = {
    "bg": "#FAFAFA",         # Fondo blanco marfil ultra limpio (Estilo Zara / Portales de Alta Gama)
    "card": "#FFFFFF",       # Tarjetas blancas puras
    "text": "#111111",       # Texto negro absoluto de alto contraste
    "sub": "#666666",        # Gris neutral técnico
    "border": "#E5E5E5",     # Líneas sutiles casi imperceptibles
    "logo": "n1.png",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* --- ANIMACIONES DE ENTRADA --- */
@keyframes fadeInSlideDown {{
    0% {{
        opacity: 0;
        transform: translateY(-8px);
    }}
    100% {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.animate-fade-in {{
    animation: fadeInSlideDown 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
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

/* APP BASE CHIC & MINIMAL */
html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}

.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
    background-color: {vars_css['bg']} !important;
}}

/* ==========================================================
   ESTILO NAVEGACIÓN MINIMALISTA TIPO ZARA / PORTALES CHIC
   ================================================---------- */
div[data-testid="stHorizontalBlock"] > div > div.stButton > button {{
    background-color: transparent !important;
    color: #555555 !important;
    border: none !important;
    border-radius: 0px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    height: 36px !important;
    width: 100% !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}}

div[data-testid="stHorizontalBlock"] > div > div.stButton > button:hover {{
    color: #000000 !important;
    background-color: #F0F0F0 !important;
}}

/* Pestaña Activa con línea inferior minimalista nítida */
div[data-testid="stHorizontalBlock"] > div > div.stButton > button[kind="primary"] {{
    color: #000000 !important;
    font-weight: 700 !important;
    background-color: transparent !important;
    border-bottom: 2px solid #000000 !important;
    border-radius: 0px !important;
}}

/* BOTONES DE SUBMENÚS (Estilo Cápsula Editorial) */
.sub-menu-container div.stButton > button {{
    background-color: #FFFFFF !important;
    color: #333333 !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 20px !important;
    font-weight: 600 !important;
    font-size: 10px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    height: 32px !important;
    transition: all 0.2s ease !important;
}}

.sub-menu-container div.stButton > button:hover {{
    background-color: #000000 !important;
    border-color: #000000 !important;
    color: #FFFFFF !important;
}}

.sub-menu-container div.stButton > button[kind="primary"] {{
    background-color: #111111 !important;
    border-color: #111111 !important;
    color: #FFFFFF !important;
}}

/* BUSCADOR ESTILO PORTAL PREMIUM */
div[data-baseweb="input"] {{
    background-color: #FFFFFF !important;
    border-radius: 4px !important;
    border: 1px solid #D1D1D1 !important;
}}
div[data-baseweb="input"]:focus-within {{
    border-color: #000000 !important;
    box-shadow: none !important;
}}

/* FOOTER CHIC */
.footer {{ 
    position: fixed; 
    bottom: 0 !important; 
    left: 0 !important; 
    width: 100% !important; 
    background-color: #FFFFFF !important; 
    color: #888888 !important; 
    text-align: center; 
    padding: 10px 0px !important; 
    font-size: 9px; 
    letter-spacing: 3px; 
    border-top: 1px solid #E5E5E5 !important; 
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
# 4. HEADER EDITORIAL / MINIMALISTA CHIC
# ==========================================
header_zone = st.container()
with header_zone:
    c_logo, c_search, c_exit = st.columns([1.2, 7.5, 1.3], vertical_alignment="center")

    with c_logo:
        try:
            st.image(vars_css["logo"], width=120)
        except:
            st.markdown("<span style='font-weight: 800; letter-spacing: 2px; color: #111;'>NEXION</span>", unsafe_allow_html=True)

    with c_search:
        es_atencion3g = st.session_state.get("usuario_activo", "").upper() == "ATENCION3G"
        key_actual = f"main_search_v{st.session_state.search_key_version}"

        query = st.text_input(
            "Buscar",
            placeholder="BUSCADOR DESACTIVADO" if es_atencion3g else "Buscar guía, pedido o cliente...",
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
                cols_op = ["NÚMERO DE GUÍA", "NÚMERO DE PEDIDO", "NO CLIENTE", "NOMBRE DEL CLIENTE", "DESTINO"]
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

    with c_exit:
        if st.button("SALIR", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.autenticado = False
            st.session_state.splash_completado = False
            st.rerun()

    st.markdown(f"<hr style='border-top: 1px solid {vars_css['border']}; margin: 6px 0 2px; opacity: 0.6;'>", unsafe_allow_html=True)

    # 6 Botones Principales Estilo Portal de Alta Gama (Editorial Tabs)
    usuario = st.session_state.get("usuario_activo", "GUEST").upper()
    es_admin = usuario == "RIGOBERTO"

    cols_menu = st.columns(6)
    
    botones_nav = [
        ("DASHBOARD", "DASHBOARD", "GENERAL", True),
        ("ENTREGAS", "ENTREGAS", "AGC", True),
        ("REPORTES", "REPORTES", "ENVIO DE MUESTRAS", True),
        ("CENTRO DATOS", "CENTRO DE DATOS", "ASIGNAR FLETERA", True),
        ("FORMATOS", "FORMATOS", "SALIDA DE PT", False),
        ("FINANZAS", "FINANZAS", "WALLET", False),
    ]

    for idx, (label, main_val, sub_val, is_page) in enumerate(botones_nav):
        with cols_menu[idx]:
            activo = st.session_state.menu_main == main_val
            tipo_btn = "primary" if activo else "secondary"
            if st.button(label, use_container_width=True, key=f"nav_chic_{main_val}", type=tipo_btn):
                st.session_state.menu_main = main_val
                st.session_state.menu_sub = sub_val
                st.session_state.busqueda_activa = False
                if main_val == "ENTREGAS":
                    st.switch_page("pages/entregas_agc.py")
                elif main_val == "REPORTES":
                    st.switch_page("pages/muestras.py")
                elif main_val == "CENTRO DE DATOS":
                    st.switch_page("pages/asignacionfletera.py")
                else:
                    st.rerun()

    st.markdown(f"<hr style='border-top: 1px solid {vars_css['border']}; margin: 0px 0 10px; opacity: 0.4;'>", unsafe_allow_html=True)

    # Submenús contextuales dinámicos en formato de píldoras flotantes modernas
    cat_activa = st.session_state.menu_main
    submenus_map = {
        "DASHBOARD": ["GENERAL"],
        "SEGUIMIENTO": ["ALERTAS", "GANTT", "QUEJAS"],
        "ENTREGAS": ["AGC", "AMAZON", "BARCELO"],
        "REPORTES": ["COSTOS CEDIS", "ANALISIS MENSUAL", "DETALLE COSTOS", "ENVIOS ESPECIALES", "ENVIO DE MUESTRAS"],
        "FORMATOS": ["SALIDA DE PT", "CHECK LIST AGC", "QR AGC", "PREGUIA PAQMEX", "RECOLECCION 3G", "RECOLECCION ONE", "CARTA RECLAMO", "COTIZACIONES"],
        "CENTRO DE DATOS": ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "HERRAMIENTAS"],
        "FINANZAS": ["WALLET", "CAJA CHICA", "GASTOS"],
        "ENFOQUE": ["MORENO", "VAZQUEZ", "MIGUEL"]
    }

    if cat_activa in submenus_map:
        sub_opciones = submenus_map[cat_activa]
        st.markdown('<div class="sub-menu-container" style="display: flex; gap: 8px; justify-content: center; margin-bottom: 8px;">', unsafe_allow_html=True)
        sub_cols = st.columns(len(sub_opciones))
        for idx, sub in enumerate(sub_opciones):
            with sub_cols[idx]:
                is_selected = st.session_state.menu_sub == sub
                btn_type = "primary" if is_selected else "secondary"
                if st.button(sub, use_container_width=True, key=f"sub_chic_{cat_activa}_{sub}", type=btn_type):
                    st.session_state.menu_sub = sub
                    st.session_state.busqueda_activa = False
                    if sub == "ENVIO DE MUESTRAS":
                        st.switch_page("pages/muestras.py")
                    elif sub == "AGC":
                        st.switch_page("pages/entregas_agc.py")
                    elif sub == "ASIGNAR FLETERA":
                        st.switch_page("pages/asignacionfletera.py")
                    else:
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<hr style='border-top: 1px solid {vars_css['border']}; margin: 8px 0 12px; opacity: 0.4;'>", unsafe_allow_html=True)

    # ── RENDERIZADO DE RESULTADOS DE BÚSQUEDA ──
    if st.session_state.busqueda_activa and st.session_state.resultado_busqueda is not None:
        resultados = st.session_state.resultado_busqueda
        total = len(resultados)
        tipo = st.session_state.get("tipo_resultado", "OPERACION")
        accent_color = "#000000"
        inv_color = "#333333"

        col_espacio, col_cerrar = st.columns([0.85, 0.15])
        with col_cerrar:
            if st.button("✕ CERRAR", key="btn_cerrar_top", use_container_width=True):
                st.session_state.busqueda_activa = False
                st.session_state.resultado_busqueda = None
                st.session_state.search_key_version += 1
                st.rerun()

        if tipo == "INVENTARIO":
            st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:15px;'><div style='background:{inv_color};width:4px;height:18px;'></div><span style='color:#111;font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;'>EXISTENCIAS EN INVENTARIO <span style='color:#666;'>({total})</span></span></div>", unsafe_allow_html=True)
            for _, i in resultados.iterrows():
                st.markdown(f"<div style='background:#FFFFFF;border:1px solid #E5E5E5;border-left:3px solid #111;border-radius:4px;padding:12px 20px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:#888;font-size:9px;font-weight:700;letter-spacing:1px;'>SKU</span><br><b style='font-size:15px;color:#111;'>{i.get('CODIGO','')}</b></div><div style='flex:3;padding-left:20px;'><span style='color:#888;font-size:9px;font-weight:700;letter-spacing:1px;'>DESCRIPCIÓN</span><br><span style='font-size:12px;color:#222;font-weight:600;'>{i.get('DESCRIPCION','')}</span></div><div style='flex:1;text-align:right;'><span style='background:#F0F0F0;color:#111;padding:4px 10px;border-radius:2px;font-size:9px;font-weight:700;'>DISPONIBLE</span></div></div>", unsafe_allow_html=True)
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
                    n_guia = "EN ESPERA"

                tarjeta_chic_html = f"""<div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-left: 4px solid #111111; padding: 22px; border-radius: 6px; width: 100%; color: #111; margin-bottom: 20px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #F0F0F0; padding-bottom: 12px;"><div style="font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #555;">PEDIDO: <span style="color:#000;">#{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div><div style="font-size: 11px; font-weight: 700; color: #000; background: #F4F4F4; padding: 4px 10px; border-radius: 3px;">FLETERA: {envio.get('FLETERA','N/A')}</div></div><div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px;"><div style="flex: 1;"><span style="font-size: 9px; color: #777; font-weight: 700; letter-spacing: 1px;">CLIENTE</span><div style="font-size: 13px; font-weight: 700; color: #111; margin-top: 2px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div><div style="font-size: 11px; color: #555; margin-top: 2px;">{envio.get('DOMICILIO','')}</div></div><div style="flex: 1; border-left: 1px solid #E5E5E5; padding-left: 15px;"><span style="font-size: 9px; color: #777; font-weight: 700; letter-spacing: 1px;">GUÍA / RASTREO</span><div style="font-size: 14px; font-weight: 800; font-family: monospace; color: #111; margin-top: 2px;">{n_guia}</div><div style="font-size: 11px; color: #555; margin-top: 2px;">DESTINO: {envio.get('DESTINO','N/A')}</div></div><div style="flex: 0.8; text-align: right;"><span style="font-size: 9px; color: #777; font-weight: 700; letter-spacing: 1px;">ESTATUS</span><div style="font-size: 12px; font-weight: 700; color: #111; margin-top: 4px; background: #EFEFEF; padding: 6px 12px; border-radius: 4px; display: inline-block;">{f_entrega_val}</div></div></div></div>"""
                st.markdown(tarjeta_chic_html, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='font-size: 13px; font-weight: 700; color: #111; margin-bottom: 15px; letter-spacing: 1px;'>COINCIDENCIAS ENCONTRADAS ({total})</div>", unsafe_allow_html=True)
                for _, d in resultados.iterrows():
                    st.markdown(f"<div style='background:#FFFFFF;border:1px solid #E5E5E5;border-radius:6px;padding:15px 20px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='font-size:9px;color:#777;font-weight:700;'>PEDIDO</span><br><b style='font-size:14px;color:#111;'>#{d.get('NÚMERO DE PEDIDO','')}</b></div><div style='flex:2;'><span style='font-size:9px;color:#777;font-weight:700;'>CLIENTE</span><br><b style='font-size:12px;color:#222;'>{d.get('NOMBRE DEL CLIENTE','')}</b></div><div style='flex:1;'><span style='font-size:9px;color:#777;font-weight:700;'>GUÍA</span><br><b style='font-size:12px;color:#111;font-family:monospace;'>{d.get('NÚMERO DE GUÍA','')}</b></div><div style='flex:1;text-align:right;'><span style='font-size:11px;color:#111;font-weight:700;'>{d.get('DESTINO','')}</span></div></div>", unsafe_allow_html=True)

        st.markdown(f"<hr style='border-top: 1px solid {vars_css['border']}; margin: 10px 0 15px; opacity: 0.4;'>", unsafe_allow_html=True)

# ==========================================
# 5. INTERFAZ PRINCIPAL
# ==========================================
def main():
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
st.markdown(
    f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.6; font-size:8px; letter-spacing:3px;">ENGINEERED BY</span>
        <span style="color:#111111; font-weight:600; letter-spacing:2px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
