import base64
from datetime import datetime, timedelta, timezone
import io
import re
import time
import unicodedata
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas
import pandas as pd
import streamlit as st

# Intentar importar el escáner QR nativo para móviles si está instalado
try:
    from streamlit_qrcode_scanner import qrcode_scanner
    _QR_SCANNER_DISPONIBLE = True
except ImportError:
    _QR_SCANNER_DISPONIBLE = False

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Logistics Mobile",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── TEMA Y CSS MAESTROS (OPTIMIZADO TÁCTIL MÓVIL) ──────────────────────────
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
    animation: fadeInUp 0.5s ease-out;
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
    padding-top: 0.5rem !important;
    padding-bottom: 6rem !important;
    background-color: {vars_css['bg']} !important;
    max-width: 100% !important;
}}

/* --- BOTONES TÁCTILES GRANDES (MOBILE-FIRST) --- */
div.stButton > button, div.stDownloadButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 2px solid {vars_css['border']} !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    font-size: 13px !important;
    height: 48px !important;
    width: 100% !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    transition: all 0.2s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
    transform: scale(1.02);
}}

/* --- CAMPOS DE TEXTO CÓMODOS PARA CELULAR --- */
input[type="text"] {{
    height: 46px !important;
    font-size: 14px !important;
    border-radius: 8px !important;
    background-color: #1E272C !important;
    color: white !important;
}}

/* --- SEPARACIÓN EN POPOVERS --- */
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {{
    gap: 0.6rem !important;
}}

div[data-testid="stPopoverBody"] .stButton {{
    margin-bottom: 0rem !important;
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
    padding: 10px 0px !important; 
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
# 2. SISTEMA DE SEGURIDAD (VALIDACIÓN DE SESIÓN Y PERMISOS)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/etiquetas.py"
    st.switch_page("pages/log.py")

def verificar_permiso_pagina(modulo, submodulo=None):
    permisos = st.session_state.get("permisos", {})
    if st.session_state.get("usuario_activo", "").upper() == "RIGOBERTO":
        return True
        
    if not permisos.get(modulo.upper(), False) and not (submodulo and permisos.get(submodulo.upper(), False)):
        st.markdown(
            f"""
            <div style="
                background: {vars_css['card']}; 
                border: 1px solid {vars_css['border']}; 
                border-left: 6px solid #FFD700; 
                padding: 20px; 
                border-radius: 10px; 
                width: 100%; 
                font-family: 'Inter', sans-serif; 
                color: white; 
                box-sizing: border-box; 
                margin-bottom: 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <div style="width: 12px; height: 12px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 10px #FFD700;"></div>
                    <span style="color: #FFD700; font-size: 14px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">
                        ACCESS RESTRICTED // MÓDULO NO AUTORIZADO
                    </span>
                </div>
                <div style="font-size: 12px; color: rgba(255,255,255,0.8); font-weight: 600; padding-left: 22px;">
                    No tienes permisos para acceder al módulo de <b style="color: white; text-transform: uppercase;">ETIQUETAS</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("REGRESAR AL INICIO", key="btn_regresar_modulo", use_container_width=True):
            st.switch_page("pages/indicadores.py")
        st.stop()

verificar_permiso_pagina("CENTRO DE DATOS", "ESCANEAR QR")


# ==========================================
# 3. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================
@st.cache_data(ttl=60)
def cargar_csv_github():
    try:
        repo = "RH2026/nexion"
        filename = "facturacion_moreno.csv"
        branch = "main"
        
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filename}"
        token = st.secrets["GITHUB_TOKEN"]
        headers = {"Authorization": f"token {token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
            df.columns = df.columns.astype(str).str.strip()
            return df
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def cargar_datos_dashboard():
    t = int(time.time())
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
    try:
        df = pd.read_csv(url, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return None

def limpiar_parentesis(texto):
    return re.sub(r'\(.*?\)', '', str(texto)).strip()


# --- LOTE TEMPORAL Y HORA DE MÉXICO ---
if "lote_escaneos_pendientes" not in st.session_state:
    st.session_state.lote_escaneos_pendientes = []

def agregar_escaneo_al_lote(texto_qr):
    match_factura = re.search(r"FACTURA:\s*([^|\n]+)", texto_qr, re.IGNORECASE)
    match_prog = re.search(r"PROG:\s*([^|\n]+)", texto_qr, re.IGNORECASE)

    if not match_factura or not match_prog:
        return False, "Formato QR inválido. Debe contener FACTURA y PROG."

    factura_scans = str(match_factura.group(1)).strip()
    prog_val = str(match_prog.group(1)).strip()

    df_dash_val = cargar_datos_dashboard()
    existe_en_sistema = False
    if df_dash_val is not None and not df_dash_val.empty:
        for col_p in ["NÚMERO DE PEDIDO", "PEDIDO", "FACTURA"]:
            if col_p in df_dash_val.columns:
                if factura_scans in df_dash_val[col_p].astype(str).str.strip().values:
                    existe_en_sistema = True
                    break

    if not existe_en_sistema:
        return False, f"❌ La factura {factura_scans} no existe en la base de datos."

    for item in st.session_state.lote_escaneos_pendientes:
        if item["factura"] == factura_scans:
            return False, f"⚠️ La factura {factura_scans} ya está en el lote pendiente."

    # Hora exacta de México (UTC-6)
    tz_mexico = timezone(timedelta(hours=-6))
    hora_mexico = datetime.now(tz_mexico).strftime("%H:%M:%S")

    st.session_state.lote_escaneos_pendientes.append({
        "factura": factura_scans,
        "fecha_envio": prog_val,
        "qr_completo": texto_qr,
        "hora": hora_mexico
    })

    return True, f"✅ Factura {factura_scans} agregada con éxito."


def sincronizar_lote_con_github():
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "envios.csv"

    if not TOKEN:
        return False, "Falta configurar GITHUB_TOKEN en Secrets."

    if not st.session_state.lote_escaneos_pendientes:
        return False, "No hay escaneos pendientes."

    try:
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"

        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return False, "No se pudo conectar con GitHub."

        file_info = r.json()
        sha = file_info["sha"]
        content_decoded = base64.b64decode(file_info["content"]).decode("utf-8-sig")
        df_envios = pd.read_csv(io.StringIO(content_decoded))
        df_envios.columns = [str(c).strip() for c in df_envios.columns]

        col_fac_encontrada = next((c for c in df_envios.columns if c.lower() in ["factura", "folio", "docnum"]), "FACTURA")
        col_fecha_envio = next((c for c in df_envios.columns if "fecha" in c.lower() and "envio" in c.lower()), "FECHA DE ENVIO")

        if col_fecha_envio not in df_envios.columns:
            df_envios[col_fecha_envio] = ""

        df_envios[col_fecha_envio] = df_envios[col_fecha_envio].astype(str)
        df_envios[col_fac_encontrada] = df_envios[col_fac_encontrada].astype(str).str.strip()

        facturas_actualizadas = []
        for escaneo in st.session_state.lote_escaneos_pendientes:
            fac = escaneo["factura"]
            f_env = escaneo["fecha_envio"]

            en_envios = fac in df_envios[col_fac_encontrada].values
            if en_envios:
                fila_actual = df_envios[df_envios[col_fac_encontrada] == fac].iloc[0]
                val_actual = str(fila_actual[col_fecha_envio]).strip()
                if not val_actual or val_actual.lower() in ["nan", "nat", "none", ""]:
                    df_envios.loc[df_envios[col_fac_encontrada] == fac, col_fecha_envio] = f_env
                    facturas_actualizadas.append(fac)
            else:
                nueva_fila = {col_fac_encontrada: fac, col_fecha_envio: f_env}
                df_envios = pd.concat([df_envios, pd.DataFrame([nueva_fila])], ignore_index=True)
                facturas_actualizadas.append(fac)

        csv_buffer = io.StringIO()
        df_envios.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        content_base64 = base64.b64encode(csv_buffer.getvalue().encode("utf-8")).decode("utf-8")

        data = {
            "message": f"Sincronización móvil de {len(facturas_actualizadas)} folios",
            "content": content_base64,
            "branch": "main",
            "sha": sha
        }

        put_response = requests.put(url, headers=headers, json=data)
        if put_response.status_code in [200, 201]:
            st.session_state.lote_escaneos_pendientes = []
            return True, f"¡Sincronización exitosa! {len(facturas_actualizadas)} folios actualizados."
        else:
            return False, "Error al guardar en GitHub."

    except Exception as e:
        return False, f"Error: {str(e)}"


# Inicialización de estados de menú
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "CENTRO DE DATOS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "ESCANEAR QR"
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1


# ==========================================
# 4. HEADER MÓVIL TÁCTIL (DISEÑO LIMPIO)
# ==========================================
header_zone = st.container()
with header_zone:
    c1, c2 = st.columns([3, 1], vertical_alignment="center")

    with c1:
        azul_nexion = "#82D4E6"
        oro_brillante = "#FFD700"
        st.markdown(
            f"""
            <div style='background: {vars_css['card']}; border: 1px solid {vars_css['border']}; padding: 10px 15px; border-radius: 8px;'>
                <p style='font-size: 10px; color: {azul_nexion}; font-weight: 800; letter-spacing: 2px; margin: 0;'>CENTRO DE DATOS</p>
                <p style='font-size: 14px; color: {oro_brillante}; font-weight: 800; letter-spacing: 1px; margin: 0;'>📱 ESCANEO MÓVIL QR</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with c2:
        with st.popover("☰ MENÚ", use_container_width=True):
            usuario = st.session_state.get("usuario_activo", "GUEST")
            permisos = st.session_state.get("permisos", {})
            nombre_display = st.session_state.get("nombre_completo", "OPERADOR")
        
            st.markdown(
                f"""
                <div style='background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-bottom: 12px; border-left: 3px solid #00D4FF;'>
                    <p style='color:#00D4FF; font-size:9px; font-weight:800; margin:0; letter-spacing:1px;'>USUARIO</p>
                    <p style='color:white; font-size:13px; font-weight:700; margin:0;'>{nombre_display.upper()}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
        
            if permisos.get("DASHBOARD", False):
                if st.button("📊 DASHBOARD", use_container_width=True):
                    st.switch_page("pages/indicadores.py")
            if permisos.get("CENTRO DE DATOS", False):
                if st.button("🏷️ ETIQUETAS", use_container_width=True):
                    st.switch_page("pages/etiquetas.py")
            
            st.markdown("<hr style='margin: 8px 0; opacity: 0.2;'>", unsafe_allow_html=True)
            if st.button("🚪 CERRAR SESIÓN", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.autenticado = False
                st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)


# ==========================================
# 5. INTERFAZ PRINCIPAL OPTIMIZADA PARA CELULAR
# ==========================================
def main():
    # Tarjeta de instrucciones rápida
    st.markdown(
        f"""
        <div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #00D4FF; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: #00D4FF; font-size: 12px; font-weight: 900; letter-spacing: 1px; margin-bottom: 6px; text-transform: uppercase;">
                🎯 MODO DE CAPTURA RÁPIDA
            </p>
            <p style="font-size: 11px; color: rgba(255,255,255,0.9); margin: 0; line-height: 1.4;">
                Apunta con la cámara al QR o usa la entrada manual. Los escaneos se acumulan de forma segura para sincronizarlos en bloque cuando termines.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    qr_detectado = None

    # 1. CÁMARA NATIVA MÓVIL
    if _QR_SCANNER_DISPONIBLE:
        st.markdown("<p style='font-size: 12px; font-weight: 800; color: #82D4E6; margin-bottom: 5px;'>📷 CÁMARA ACTIVA:</p>", unsafe_allow_html=True)
        qr_detectado = qrcode_scanner(key="lector_qr_movil")
        
        if "ultimo_qr_procesado" not in st.session_state:
            st.session_state.ultimo_qr_procesado = ""

        if qr_detectado and qr_detectado != st.session_state.ultimo_qr_procesado:
            st.session_state.ultimo_qr_procesado = qr_detectado
            exito, mensaje = agregar_escaneo_al_lote(qr_detectado)
            if exito:
                st.toast(mensaje, icon="📥")
                time.sleep(0.4)
                st.rerun()
            else:
                st.warning(mensaje)
    else:
        st.info("💡 Tip: Instala `streamlit-qrcode-scanner` para activar la cámara directamente en pantalla.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. ENTRADA MANUAL TÁCTIL GRANDE
    st.markdown("<p style='font-size: 12px; font-weight: 800; color: #82D4E6; margin-bottom: 5px;'>⌨️ ENTRADA MANUAL / PEGADO</p>", unsafe_allow_html=True)
    qr_input_manual = st.text_input("Contenido del QR", placeholder="Pega o escribe el código QR aquí...", label_visibility="collapsed", key="input_manual_qr")

    if st.button("➕ AGREGAR AL LOTE TÁCTIL", key="btn_agregar_qr_manual", type="primary"):
        if qr_input_manual:
            exito, mensaje = agregar_escaneo_al_lote(qr_input_manual)
            if exito:
                st.success(mensaje)
                time.sleep(0.4)
                st.rerun()
            else:
                st.warning(mensaje)
        else:
            st.warning("Ingresa o pega el texto del QR.")

    # ── SECCIÓN DE LOTE PENDIENTE Y BOTÓN DE SINCRONIZACIÓN ──
    if st.session_state.lote_escaneos_pendientes:
        st.markdown("---")
        
        # Panel flotante o destacado superior para el lote
        total_lote = len(st.session_state.lote_escaneos_pendientes)
        st.markdown(
            f"""
            <div style="background: rgba(255, 215, 0, 0.1); border: 2px solid #FFD700; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;">
                <span style="color: #FFD700; font-size: 14px; font-weight: 900; letter-spacing: 1px;">📦 LOTE PENDIENTE: {total_lote} FOLIOS LISTOS</span>
                <div style="font-size: 11px; color: rgba(255,255,255,0.8); margin-top: 4px;">Presiona el botón inferior para enviarlos todos de golpe a la nube.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Botón de sincronización con altura táctil ideal para celular
        if st.button("☁️ SINCRONIZAR LOTE A GITHUB AHORA", key="btn_sync_lote", type="primary"):
            with st.spinner("Sincronizando lote completo..."):
                exito_sync, msg_sync = sincronizar_lote_con_github()
                if exito_sync:
                    st.success(msg_sync)
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.error(msg_sync)

        st.markdown("<br>", unsafe_allow_html=True)
        
        col_t_prev, col_limpiar = st.columns([3, 1], vertical_alignment="center")
        with col_t_prev:
            st.markdown(f"<p style='color:white; font-size:12px; font-weight:800; margin:0;'>📋 VISTA PREVIA DEL LOTE</p>", unsafe_allow_html=True)
        with col_limpiar:
            if st.button("🗑️ VACIAR", key="btn_limpiar_lote"):
                st.session_state.lote_escaneos_pendientes = []
                st.rerun()

        # Tarjetas individuales del lote optimizadas para pantallas verticales
        for item in st.session_state.lote_escaneos_pendientes:
            st.markdown(
                f"""
                <div style="background: rgba(255, 215, 0, 0.05); border: 1px solid rgba(255, 215, 0, 0.3); border-left: 5px solid #FFD700; padding: 12px 15px; border-radius: 8px; margin-bottom: 10px; font-family: 'Inter', sans-serif;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: #FFD700; font-size: 12px; font-weight: 900; letter-spacing: 1px;">FAC: {item['factura']}</span>
                        <span style="color: rgba(255,255,255,0.7); font-size: 10px; font-weight: 700;">🕒 {item['hora']}</span>
                    </div>
                    <div style="font-size: 12px; color: white; font-weight: 700;">Fecha Asignada: <span style="color: #82D4E6;">{item['fecha_envio']}</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<br><br>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# ── FOOTER FIJO MÓVIL ────────────────────────
st.markdown(
    f"""
    <div class="footer">
        NEXION MOBILE HUB // © 2026 <br>
        <span style="color:{vars_css['text']}; font-weight:600; letter-spacing:2px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
