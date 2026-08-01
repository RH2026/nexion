import base64
from datetime import datetime
import io
import re
import time
import unicodedata
import zipfile
import calendar
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit as st
import streamlit.components.v1 as components
import requests

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Entregas AGC",
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

/* --- OCULTAR ELEMENTOS DE STREAMLIT, GITHUB Y FLECHAS DE SIDEBAR --- */
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
    animation: none !important; 
    transform: none !important; 
}}

div.stButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
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


# Inicialización segura de estados de menú si no existen
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "CENTRO DE DATOS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "ENTREGAS AGC"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "busqueda_input" not in st.session_state:
    st.session_state.busqueda_input = ""


# ==========================================
# 4. HEADER CON 4 COLUMNAS (BÚSQUEDA Y RESULTADO A TODO ANCHO)
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
        azul_nexion = "#38bdf8"
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
        query = st.text_input(
            "BUSQUEDA AUXILIAR DE GUIAS",
            value="",
            placeholder=(
                "🔍 BUSCADOR DESACTIVADO"
                if es_atencion3g
                else "Ingresa el numero de factura..."
            ),
            label_visibility="collapsed",
            key="busqueda_input",
            disabled=es_atencion3g,
        )

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
                <div style='background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin-bottom: 15px; border-left: 3px solid #38bdf8;'>
                    <p style='color:#38bdf8; font-size:9px; font-weight:500; margin:0; letter-spacing:1px;'>USUARIO ACTIVO</p>
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

            if not es_atencion3g:
                with st.expander("CENTRO DE DATOS", expanded=True):
                    for s in ["ASIGNAR FLETERA", "ENTREGAS AGC", "CARGAR DATOS", "ETIQUETAS", "HERRAMIENTAS"]:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_hub_{s}"):
                            st.session_state.menu_main = "CENTRO DE DATOS"
                            st.session_state.menu_sub = s
                            st.session_state.busqueda_activa = False
                            st.rerun()

            st.markdown(
                "<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True
            )
            if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.autenticado = False
                st.rerun()

    st.markdown(
        f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>",
        unsafe_allow_html=True,
    )

# ── SECCIÓN DE RESULTADO DE BÚSQUEDA GLOBAL CON TIMELINE A TODO ANCHO ──────────────────────────
if query:
    try:
        df_t1 = pd.read_csv("T1.csv") if pd.io.common.file_exists("T1.csv") else None
        df_t2 = pd.read_csv("T2.csv") if pd.io.common.file_exists("T2.csv") else None
        df_t3 = pd.read_csv("T3.csv") if pd.io.common.file_exists("T3.csv") else None
    except:
        df_t1, df_t2, df_t3 = None, None, None

    encontrado = False
    html_resultado = ""

    for df_source, nombre_f in [
        (df_t1, "TRES GUERRAS"),
        (df_t2, "TINY PACK"),
        (df_t3, "ONE"),
    ]:
        if df_source is not None and not encontrado:
            cols_busqueda = [
                "OBSERVACION 1",
                "FACTURA_INTERNA",
                "Observaciones",
                "TALON",
                "CARTA_PORTE",
                "Guia",
            ]
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

                col_f_envio = next((c for c in ['FECHA_ENVIO', 'FECHA DE ENVÍO', 'F.ENVIO', 'FECHA'] if c in df_source.columns), None)
                col_f_entrega = next((c for c in ['F.ENTREGA', 'FECHA_ENTREGA', 'FECHA DE ENTREGA'] if c in df_source.columns), None)

                f_envio = str(f.get(col_f_envio, "N/A")) if col_f_envio else "N/A"
                f_entrega_val = str(f.get(col_f_entrega, "PENDIENTE")) if col_f_entrega else "PENDIENTE"
                
                fecha_valida = False
                if col_f_entrega:
                    fecha_dt = pd.to_datetime(f.get(col_f_entrega), errors="coerce")
                    if pd.notnull(fecha_dt):
                        fecha_valida = True

                estatus = "ESTATUS: ENTREGADO" if fecha_valida else "ESTATUS: EN TRÁNSITO"
                color_estatus = "#00FFAA" if fecha_valida else "#38bdf8"

                guia = f.get("TALON") or f.get("CARTA_PORTE") or f.get("Guia") or "S/N"
                factura = f.get("OBSERVACION 1") or f.get("FACTURA_INTERNA") or f.get("Observaciones") or "S/N"
                cliente = f.get("CLIENTE_DESTINO") or f.get("DESTINATARIO") or f.get("Destinatario") or "CLIENTE NO REGISTRADO"
                destino = f.get("DESTINO") or f.get("CIUDAD") or f.get("Oficina_Destino") or "N/A"
                bultos = f.get("BULTOS") or f.get("PIEZAS") or f.get("Paquetes_Ampara") or "0"
                importe = f.get("Sub total _ Guia") or f.get("TOTAL") or f.get("SUBTOTAL") or "0.00"

                timeline_html = ""
                if col_f_envio or col_f_entrega:
                    c_envio_dot = "#38bdf8" if f_envio != "N/A" else vars_css["border"]
                    c_entrega_dot = color_estatus if fecha_valida else vars_css["border"]
                    linea_col = "#38bdf8" if f_envio != "N/A" else vars_css["border"]

                    timeline_html = f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; position: relative; margin: 20px 0 15px 0; padding: 0 10px;">
                        <div style="display: flex; flex-direction: column; align-items: center; flex: 1; z-index: 2;">
                            <div style="width: 12px; height: 12px; background: {c_envio_dot}; border-radius: 50%;"></div>
                            <div style="font-size: 9px; color: rgba(255,255,255,0.6); margin-top: 6px; font-weight: 800; letter-spacing: 1px;">ENVÍO</div>
                            <div style="font-size: 11px; color: white; font-weight: 600;">{f_envio}</div>
                        </div>
                        <div style="flex-grow: 1; height: 2px; background: {linea_col}; margin-top: -25px;"></div>
                        <div style="display: flex; flex-direction: column; align-items: center; flex: 1; z-index: 2;">
                            <div style="width: 14px; height: 14px; background: {c_entrega_dot}; border-radius: 50%;"></div>
                            <div style="font-size: 9px; color: rgba(255,255,255,0.6); margin-top: 6px; font-weight: 800; letter-spacing: 1px;">ENTREGA</div>
                            <div style="font-size: 11px; color: white; font-weight: 600;">{f_entrega_val}</div>
                        </div>
                    </div>
                    """

                html_resultado = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 22px 25px; border-radius: 8px; margin-bottom: 25px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box;"><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%;"><div style="flex: 1.2; min-width: 200px;"><div style="color: #38bdf8; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">{nombre_f}</div><div style="color: rgba(255,255,255,0.5); font-size: 10px; font-weight: 800; text-transform: uppercase; margin-top: 2px;">TALÓN / FOLIO</div><div style="color: #38bdf8; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{guia}</div><div style="color: rgba(255,255,255,0.5); font-size: 10px; font-weight: 800; text-transform: uppercase; margin-top: 6px;">REF: <span style="color: white; font-size: 12px; font-weight: 700;">{factura}</span></div></div><div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / RUTA</div><div style="color: white; font-weight: 800; font-size: 14px; text-transform: uppercase; line-height: 1.3; margin-top: 2px;">{cliente}</div><div style="font-size: 12px; color: #38bdf8; margin-top: 6px; font-weight: 600;">📍 GDL → {destino}</div></div><div style="flex: 1.2; min-width: 160px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN FINANCIERO</div><div style="color: white; font-weight: 700; font-size: 12px; margin-top: 2px;">BULTOS: <span style="color: #38bdf8;">{bultos}</span></div><div style="color: #38bdf8; font-weight: 800; font-size: 14px; margin-top: 2px;">$ {importe}</div></div><div style="text-align: right; min-width: 140px;"><span style="background-color: {color_estatus}15; color: {color_estatus}; padding: 6px 14px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid {color_estatus}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">{estatus}</span></div></div>{timeline_html}</div>"""

    if encontrado:
        col_espacio_res, col_btn_cerrar = st.columns([10, 1])
        with col_btn_cerrar:
            def limpiar_busqueda():
                st.session_state.busqueda_input = ""
            if st.button("✕ CERRAR", key="btn_cerrar_render", use_container_width=True, on_click=limpiar_busqueda):
                pass
        st.markdown(html_resultado, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="
                background-color: {vars_css['card']}; 
                border-radius: 8px; 
                padding: 20px; 
                border-left: 5px solid #ff4b4b; 
                border: 1px solid {vars_css['border']};
                margin-top: 15px; 
                margin-bottom: 35px;
                width: 100%;
                font-family: 'Inter', sans-serif;
                box-sizing: border-box;
            ">
                <div style="color: #8899a6; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 2px;">Estado de Búsqueda</div>
                <div style="color: #ff4b4b; font-weight: bold; font-size: 1.3rem; line-height: 1.1; letter-spacing: 1px;">SIN COINCIDENCIAS</div>
                <div style="margin-top: 15px; border-top: 1px solid {vars_css['border']}; padding-top: 12px;">
                    <div style="color: #8899a6; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 3px;">Referencia consultada</div>
                    <div style="color: white; font-weight: bold; font-size: 1.1rem;">{query}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ==========================================
# 5. MÓDULO DE ENTREGAS AGC INTEGRADO
# ==========================================
def main():
    st.markdown("""
        <style>
            div[data-testid="stBlock"] { max-width: 100% !important; padding: 0 !important; }
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

    usuario_actual = st.session_state.get("usuario_activo", "").upper()
    es_admin = (usuario_actual == "RIGOBERTO")

    if es_admin:
        with st.expander("🔐 Panel de Seguridad / Modo Edición Admin", expanded=False):
            st.success("Acceso Concedido: Administrador Reconocido 🔓")
            modo_edicion = st.checkbox("Activar Modo Edición de Citas en Pantalla", value=False, key="check_modo_edicion_session")
    else:
        modo_edicion = False

    if 'tipo_entrega' not in st.session_state:
        st.session_state.tipo_entrega = 'C A M I O N'

    if 'mes_calendario' not in st.session_state:
        st.session_state.mes_calendario = 6  # Por defecto inicia en Junio

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

    if st.session_state.tipo_entrega == 'C A M I O N':
        titulo_dinamico = "ENTREGAS DE CAMIONES"
    elif st.session_state.tipo_entrega == 'T R A I L E R':
        titulo_dinamico = "ENTREGAS DE TRAILER"
    else:
        titulo_dinamico = "CALENDARIO DE ENTregas"

    st.markdown(f"""
        <div style='text-align:center; margin-top:25px; margin-bottom:20px;'>
            <span style='color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;'>
                {titulo_dinamico}
            </span>
        </div>
    """, unsafe_allow_html=True)

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
        
        data_camion = df_entregas[df_entregas['tipo'] == 'CAMION'].to_dict('records')
        data_trailer = df_entregas[df_entregas['tipo'] == 'TRAILER'].to_dict('records')
    else:
        data_camion = []
        data_trailer = []

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


if __name__ == "__main__":
    main()

# ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""", unsafe_allow_html=True)
