import base64
from datetime import datetime
import html
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

@st.cache_data(ttl=60, show_spinner=False)
def _leer_csv_remoto_o_local(nombre_archivo):
    """Lee un CSV del repo en GitHub (dato fresco) y, si falla, de la carpeta local.
    Acepta UTF-8 / Latin-1 y separadores distintos a coma. Devuelve (df, error)."""
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/{nombre_archivo}"
    ultimo_error = ""
    for origen in (url, nombre_archivo):
        for enc in ("utf-8-sig", "latin-1"):
            try:
                df = pd.read_csv(origen, dtype=str, encoding=enc)
                if df.shape[1] == 1:  # separador distinto a coma (; o tab)
                    df = pd.read_csv(origen, dtype=str, encoding=enc, sep=None, engine="python")
                df.columns = df.columns.astype(str).str.strip()
                return df, ""
            except Exception as e_read:
                ultimo_error = f"{origen} [{enc}]: {e_read}"
    return None, ultimo_error


def render_layout(modulo_actual: str, submodulo_actual: str = "GENERAL"):
    """
    Layout maestro de NEXION: incluye estilos, sesión, control de permisos, 
    bitácora de GitHub, header, buscador y menú desplegable unificado.
    """
    
    # ── TEMA Y CSS MAESTROS ──────────────────────────────────────────
    vars_css = {
        "bg": "#384A52",           # Fondo profundo (Base)
        "card": "#2B343B",         # Azul grisáceo oscuro para celdas
        "text": "#FFFFFF",         # Blanco Perla Ultra Chic (Texto principal)
        "sub": "#FFFFFF",          # Gris Azulado Claro (Subtítulos/Secundario)
        "border": "#4B5D67",       # Contorno sutil para elevación
        "table_header": "#ffffff",
        "table_bg": "#2B343B",     # Tono profundo para encabezados de tabla
        "logo": "n1.png"           # Tu archivo de imagen
    }
    
    st.markdown(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap');
    
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
    
   div.stButton > button, div.stDownloadButton > button {{
        background-color: #628290 !important;
        color: #ffffff !important;
        border: 1px solid #628290 !important;
        border-radius: 7px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 10px !important;
        height: 32px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }}
    
    div.stButton > button:hover, div.stDownloadButton > button:hover {{
        background-color: #4E6772 !important;
        color: #ffffff !important;
        border-color: #4E6772 !important;  
    }}
        
    /* --- SEPARACIÓN EQUILIBRADA EN EL POPOVER --- */
    div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {{
        gap: 0.45rem !important;
    }}
    
    div[data-testid="stPopoverBody"] .stButton {{
        margin-bottom: 0rem !important;
    }}
    
    /* ============================================================
   EXPANDERS DEL MENÚ
   ============================================================ */

    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details > summary p {{
    color: #ffffff !important;
    font-family: inherit !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: normal !important;
    line-height: normal !important;
    margin: 0 !important;
    }}
    
    /* ENCABEZADO DEL EXPANDER */
    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details > summary {{
        background: #628290 !important;
        border-radius: 7px !important;
        padding: 8px 10px !important;
        color: #ffffff !important;
        transition: all 0.25s ease !important;
    }}
    
    /* TEXTO DEL EXPANDER */
    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details > summary p {{
        color: #ffffff !important;
        font-size: 12.5px !important;
        font-weight: 500 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }}
    
    /* HOVER DEL EXPANDER */
    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details > summary:hover {{
        background: #1E272E !important;
        border: #1E272E !important;
        
    }}
    
    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details > summary:hover p {{
        color: #ffffff !important;
    }}
    
    /* EXPANDER ABIERTO / ACTIVO */
    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details[open] > summary {{
        background: #1E272E !important;
        border-color: #1E272E !important;
    }}
    
    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details[open] > summary p {{
        color: #FFFFFF !important;
    }}
    /* FLECHA DEL EXPANDER ABIERTO */
    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details[open] > summary svg {{
        color: #000000 !important;
        fill: #000000 !important;
        stroke: #000000 !important;
    }}
    
    div[data-testid="stPopoverBody"] [data-testid="stExpander"] details[open] > summary svg path {{
        fill: #000000 !important;
        stroke: #000000 !important;
    }}
    
    /* --- TOAST ESTILO TARJETA (MÓDULO BLOQUEADO) --- */
    div[data-testid="stToast"] {{
        background-color: {vars_css['card']} !important;
        border: 1px solid {vars_css['border']} !important;
        border-left: 5px solid #FF4B4B !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.35) !important;
    }}
    
    div[data-testid="stToast"] p {{
        color: #FFFFFF !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        font-size: 12px !important;
    }}
    
    /* ===================== TABS - ESTILO NEXION (IGUAL A TÍTULOS DINÁMICOS) ===================== */
    
    /* CONTENEDOR DE LAS PESTAÑAS */
    div[data-testid="stTabs"] [role="tablist"] {{
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        gap: 36px !important;
        margin: 0 !important;
        padding: 0 !important;
        background-color: transparent !important;
        border-bottom: 1px solid {vars_css['border']} !important;
    }}
    
    /* CADA PESTAÑA (INACTIVA / BASE) */
    div[data-testid="stTabs"] button,
    div[data-testid="stTabs"] div[data-baseweb="tab"],
    div[data-testid="stTabs"] [role="tab"] {{
        min-height: 30px !important;
        height: 30px !important;
        padding: 0px 4px !important;
        margin: 0 !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        transition: all .25s ease !important;
        flex: 0 0 auto !important;
    }}
    
    /* TEXTO INTERNO DE LAS PESTAÑAS (IGUALADO A TÍTULOS DINÁMICOS: 13px y 5px de espacio) */
    div[data-testid="stTabs"] [role="tab"] p,
    div[data-testid="stTabs"] [role="tab"] span {{
        color: #FFFFFF !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        letter-spacing: 0px !important;
        text-transform: uppercase !important;
        margin: 0 !important;
    }}
    
    /* HOVER EN PESTAÑAS */
    div[data-testid="stTabs"] [role="tab"]:hover p,
    div[data-testid="stTabs"] [role="tab"]:hover span {{
        color: #FFD700 !important;
    }}
    
    /* TAB ACTIVA (TEXTO BLANCO PURO IDÉNTICO AL HEADER) */
    div[data-testid="stTabs"] button[aria-selected="true"],
    div[data-testid="stTabs"] div[aria-selected="true"],
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] p,
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] span {{
        color: #FFFFFF !important;
        font-weight: 400 !important;
        letter-spacing: 0px !important;
    }}
    
    /* ELIMINAR FOCUS / SOMBRAS DE STREAMLIT */
    div[data-testid="stTabs"] button:focus,
    div[data-testid="stTabs"] button:active,
    div[data-testid="stTabs"] [role="tab"]:focus {{
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }}
    
    /* LÍNEA INFERIOR DE SELECCIÓN (INDICADOR DE COLOR) */
    div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {{
        background-color: #38bdf8 !important;
        height: 2px !important;
    }}
    
    /* FOOTER FIJO */
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
        opacity: 0;
        animation: fadeInFooter 0.4s ease-out 0.3s forwards;
    }}

    @keyframes fadeInFooter {{
        to {{
            opacity: 1;
        }}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ── REGISTRO DE ACCESOS GITHUB ──
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
    # SISTEMA DE SEGURIDAD Y PERMISOS PRO
    # ==========================================
    if not st.session_state.get("autenticado", False):
        # Capturamos el archivo actual desde el que se dispara la seguridad
        import inspect
        frame_actual = inspect.currentframe().f_back
        nombre_archivo = inspect.getfile(frame_actual)
        
        # Guardamos la ruta relativa exacta para volver aquí tras loguearte
        st.session_state.pagina_destino = nombre_archivo
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
                        No cuentas con los permisos activos en la matriz para acceder al módulo: <b style="color: white; text-transform: uppercase;">{modulo}</b>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_regresar_m, _ = st.columns([1.5, 4])
            with col_regresar_m:
                if st.button("REGRESAR AL INICIO", key="btn_regresar_modulo", use_container_width=True):
                    st.switch_page("dashboard.py")
            st.stop()
            
        if submodulo and submodulo != "GENERAL" and not permisos.get(submodulo.upper(), False):
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
                        No cuentas con los privilegios necesarios para visualizar la sección: <b style="color: white; text-transform: uppercase;">{submodulo}</b>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_regresar_s, _ = st.columns([1.5, 4])
            with col_regresar_s:
                if st.button("REGRESAR AL INICIO", key="btn_regresar_submodulo", use_container_width=True):
                    st.switch_page("dashboard.py")
            st.stop()

    # Validación automática de permisos al renderizar
    verificar_permiso_pagina(modulo_actual, submodulo_actual)

    # Inicialización de estados de menú
    st.session_state.menu_main = modulo_actual
    st.session_state.menu_sub = submodulo_actual
    if "busqueda_activa" not in st.session_state:
        st.session_state.busqueda_activa = False
    if "resultado_busqueda" not in st.session_state:
        st.session_state.resultado_busqueda = None
    if "search_key_version" not in st.session_state:
        st.session_state.search_key_version = 1
    if "tipo_resultado" not in st.session_state:
        st.session_state.tipo_resultado = "OPERACION"

    # ==========================================
    # HEADER CON 4 COLUMNAS Y MENÚ BLINDADO
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
            # Validamos si el usuario activo es Cinthia o AGC (ignorando mayúsculas/minúsculas)
            usuario_actual = st.session_state.get("usuario_activo", "").strip()
            bloquear_busqueda = usuario_actual.upper() in ["CINTHIA", "AGC"]
            
            key_actual = f"main_search_v{st.session_state.search_key_version}"

            query = st.text_input(
                "Buscar",
                placeholder="🔍 BUSCADOR DESACTIVADO" if bloquear_busqueda else "🔍 Buscar...",
                label_visibility="collapsed",
                key=key_actual,
                disabled=bloquear_busqueda,
            )

            if query:
                url_raw = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
                try:
                    df_matriz_fresco = pd.read_csv(url_raw)
                    df_matriz_fresco.columns = df_matriz_fresco.columns.str.strip()
                except Exception:
                    df_matriz_fresco = None

                res_ops = pd.DataFrame()
                if df_matriz_fresco is not None:
                    cols_op = ["NÚMERO DE GUÍA", "NÚMERO DE PEDIDO", "NO CLIENTE", "NOMBRE DEL CLIENTE", "DESTINO"]
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

                # ── Tercer nivel: envios.csv (envío registrado; se adapta al MISMO render de Matriz/T1) ──
                res_env = pd.DataFrame()
                if res_ops.empty and res_t1.empty:
                    try:
                        df_env, err_env = _leer_csv_remoto_o_local("envios.csv")
                        if df_env is None:
                            st.toast("No se pudo leer envios.csv: " + err_env[-120:], icon="⚠️")
                        else:
                            mapa_env = {c.upper(): c for c in df_env.columns}
                            claves_busq_env = ["FACTURA", "NOMBRE_CLIENTE", "NOMBRE_EXTRAN", "DESTINO"]
                            cols_env = [mapa_env[k] for k in claves_busq_env if k in mapa_env]
                            if cols_env:
                                mask_env = df_env[cols_env].astype(str).apply(
                                    lambda x: x.str.contains(query, case=False, na=False, regex=False)
                                ).any(axis=1)
                                match_env = df_env[mask_env].copy()
                                if not match_env.empty:
                                    # envios.csv -> nombres de columna que ya usa el render de Matriz/T1
                                    equivalencias = {
                                        "FACTURA": "NÚMERO DE PEDIDO",
                                        "NOMBRE_CLIENTE": "NOMBRE DEL CLIENTE",
                                        "DESTINO": "DESTINO",
                                        "DIRECCION": "DOMICILIO",
                                        "TRANSPORTE": "FLETERA",
                                        "COSTO": "COSTO DE LA GUÍA",
                                        "QUANTITY": "CANTIDAD DE CAJAS",
                                        "FECHA DE ENVIO": "FECHA DE ENVÍO",
                                        "FECHA DE PROGRAMACION": "PROMESA DE ENTREGA",
                                        "ESTATUS": "COMENTARIOS",
                                    }
                                    match_env = match_env.rename(columns={mapa_env[k]: v for k, v in equivalencias.items() if k in mapa_env})

                                    # Si hay varias filas por partida, se agrupan en una sola tarjeta por envío
                                    llaves_env = [c for c in ["NÚMERO DE PEDIDO", "FECHA DE ENVÍO", "FLETERA", "COMENTARIOS"] if c in match_env.columns]
                                    if llaves_env:
                                        match_env = match_env.drop_duplicates(subset=llaves_env).reset_index(drop=True)

                                    # Celdas vacías: que no se pinte "nan" en la tarjeta
                                    match_env = match_env.fillna("")

                                    # Lo que trae envios.csv en bultos y costo no es el dato real: se deja PENDIENTE
                                    match_env["CANTIDAD DE CAJAS"] = "PENDIENTE"
                                    match_env["COSTO DE LA GUÍA"] = "PENDIENTE"
                                    if "FECHA DE ENVÍO" in match_env.columns:
                                        match_env["FECHA DE ENVÍO"] = match_env["FECHA DE ENVÍO"].replace("", "PENDIENTE")
                                    if "PROMESA DE ENTREGA" in match_env.columns:
                                        match_env["PROMESA DE ENTREGA"] = match_env["PROMESA DE ENTREGA"].replace("", "N/A")

                                    match_env["_ORIGEN"] = "ENVIOS"
                                    res_env = match_env
                            else:
                                st.toast("envios.csv no trae las columnas esperadas (Factura, Nombre_Cliente, DESTINO...)", icon="⚠️")
                    except Exception as e_env:
                        st.toast(f"Error buscando en envios.csv: {str(e_env)[:120]}", icon="⚠️")

                # ── Cuarto nivel: facturacion.csv (facturado pero aún NO procesado para envío) ──
                res_fact = pd.DataFrame()
                if res_ops.empty and res_t1.empty and res_env.empty:
                    try:
                        df_fact_temp, err_fact = _leer_csv_remoto_o_local("facturacion.csv")
                        if df_fact_temp is None:
                            st.toast("No se pudo leer facturacion.csv: " + err_fact[-120:], icon="⚠️")
                        else:
                            mapa_cols = {c.upper(): c for c in df_fact_temp.columns}
                            claves_busq = ["FACTURA", "REFERENCIA", "PEDIDO", "CLIENTE", "NOMBRE_CLIENTE", "DESTINO"]
                            cols_fact = [mapa_cols[k] for k in claves_busq if k in mapa_cols]

                            if cols_fact:
                                mask_fact = df_fact_temp[cols_fact].astype(str).apply(
                                    lambda x: x.str.contains(query, case=False, na=False, regex=False)
                                ).any(axis=1)
                                res_fact = df_fact_temp[mask_fact].copy()

                                # Facturación viene por partida (una fila por producto):
                                # se agrupa por Factura + Pedido para no repetir la tarjeta.
                                llaves = [mapa_cols[k] for k in ("FACTURA", "PEDIDO") if k in mapa_cols]
                                if llaves and not res_fact.empty:
                                    res_fact["_PARTIDAS"] = res_fact.groupby(llaves, dropna=False)[llaves[0]].transform("size")
                                    res_fact = res_fact.drop_duplicates(subset=llaves).reset_index(drop=True)
                            else:
                                st.toast("facturacion.csv no trae las columnas esperadas (Factura, Pedido, Cliente...)", icon="⚠️")
                    except Exception as e_fact:
                        st.toast(f"Error buscando en facturacion.csv: {str(e_fact)[:120]}", icon="⚠️")

                res_inv = pd.DataFrame()
                if res_ops.empty and res_t1.empty and res_env.empty and res_fact.empty:
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
                elif not res_env.empty:
                    st.session_state.busqueda_activa = True
                    st.session_state.tipo_resultado = "OPERACION"
                    st.session_state.resultado_busqueda = res_env
                elif not res_fact.empty:
                    st.session_state.busqueda_activa = True
                    st.session_state.tipo_resultado = "FACTURACION"
                    st.session_state.resultado_busqueda = res_fact
                elif not res_inv.empty:
                    st.session_state.busqueda_activa = True
                    st.session_state.tipo_resultado = "INVENTARIO"
                    st.session_state.resultado_busqueda = res_inv
                else:
                    st.session_state.busqueda_activa = False
                    st.session_state.resultado_busqueda = None
                    st.toast("Sin resultados: No se encontró en Matriz Global, T1, Envíos ni Facturación", icon="⚠️")

        with c4:
            with st.popover("🎛️ Módulos", use_container_width=True):
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
            
                # ── Helper único de bloqueo visual ───────────────────────────
                # Se usa en TODOS los módulos/submenús para que el comportamiento
                # sea idéntico en toda la app: el menú siempre se ve completo,
                # y solo al hacer click se avisa si no hay permiso (sin redirigir).
                def _sin_acceso(nombre):
                    st.toast(f"MÓDULO BLOQUEADO", icon="🔒")

                if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
                    if permisos.get("DASHBOARD", False) or usuario.upper() == "RIGOBERTO":
                        registrar_acceso_github(usuario, "DASHBOARD")
                        st.session_state.menu_main = "DASHBOARD"
                        st.session_state.menu_sub = "GENERAL"
                        st.session_state.busqueda_activa = False
                        st.switch_page("dashboard.py")
                    else:
                        _sin_acceso("DASHBOARD")

                with st.expander("SEGUIMIENTO", expanded=(st.session_state.menu_main == "SEGUIMIENTO")):
                    opciones_seg = ["RECOLECCIONES", "ALERTAS", "GANTT", "INCIDENCIAS"]
                    for s in opciones_seg:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_sub_{s}2"):
                            if permisos.get("SEGUIMIENTO", False) and (permisos.get(s, False) or usuario.upper() == "RIGOBERTO"):
                                registrar_acceso_github(usuario, f"SEGUIMIENTO - {s}")
                                st.session_state.menu_main = "SEGUIMIENTO"
                                st.session_state.menu_sub = s
                                st.session_state.busqueda_activa = False
                                if s == "RECOLECCIONES":
                                    st.switch_page("pages/recolecciones.py")
                                elif s == "ALERTAS":
                                    st.switch_page("pages/alertas.py")
                                elif s == "INCIDENCIAS":
                                    st.switch_page("pages/incidencias_tr.py")
                                else:
                                    st.rerun()
                            else:
                                _sin_acceso(s)

                with st.expander("ENTREGAS", expanded=(st.session_state.menu_main == "ENTREGAS")):
                    opciones_ent = ["AGC", "AMAZON", "BARCELO", "NACIONAL"]
                    for s in opciones_ent:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_ent_{s}2"):
                            if permisos.get("ENTREGAS", False) and (permisos.get(s, False) or usuario.upper() == "RIGOBERTO"):
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
                            else:
                                _sin_acceso(s)

                with st.expander("REPORTES", expanded=(st.session_state.menu_main == "REPORTES")):
                    opciones_rep = ["COSTOS CEDIS", "ANALISIS MENSUAL", "DETALLE COSTOS", "ENVIOS ESPECIALES", "COSTOS DE MUESTRAS"]
                    for s in opciones_rep:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_rep_{s}2"):
                            if permisos.get("REPORTES", False) and (permisos.get(s, False) or usuario.upper() == "RIGOBERTO"):
                                registrar_acceso_github(usuario, f"REPORTES - {s}")
                                st.session_state.menu_main = "REPORTES"
                                st.session_state.menu_sub = s
                                st.session_state.busqueda_activa = False
                                if s == "ANALISIS MENSUAL":
                                    st.switch_page("pages/analisis_mensual.py")
                                elif s == "COSTOS DE MUESTRAS":
                                    st.switch_page("pages/costos_muestras.py")
                                elif s == "ENVIOS ESPECIALES":
                                    st.switch_page("pages/envios_especiales.py")
                                else:
                                    st.toast(f"Módulo {s} en desarrollo...", icon="🚧")
                                    st.rerun()
                            else:
                                _sin_acceso(s)

                with st.expander("FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")):
                    opciones_for = ["SALIDA DE PT", "CHECK LIST AGC", "QR AGC", "PREGUIA PAQMEX", "RECOLECCION 3G", "RECOLECCION ONE", "CARTA RECLAMO", "COTIZACIONES", "ENVIO DE MUESTRAS"]
                    for s in opciones_for:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_for_{s}2"):
                            if permisos.get("FORMATOS", False) and (permisos.get(s, False) or usuario.upper() == "RIGOBERTO"):
                                registrar_acceso_github(usuario, f"FORMATOS - {s}")
                                st.session_state.menu_main = "FORMATOS"
                                st.session_state.menu_sub = s
                                st.session_state.busqueda_activa = False
                                if s == "SALIDA DE PT":
                                    st.switch_page("pages/salida_pt.py")
                                elif s == "CHECK LIST AGC":
                                    st.switch_page("pages/check_agc.py")
                                elif s == "PREGUIA PAQMEX":
                                    st.switch_page("pages/preguia_paqmex.py")
                                elif s == "RECOLECCION 3G":
                                    st.switch_page("pages/recoleccion_3g.py")
                                elif s == "COTIZACIONES":
                                    st.switch_page("pages/cotizaciones.py")
                                elif s == "ENVIO DE MUESTRAS":
                                    st.switch_page("pages/muestras.py")
                                else:
                                    st.toast(f"Módulo {s} en desarrollo...", icon="🚧")
                                    st.rerun()
                            else:
                                _sin_acceso(s)

                with st.expander("CENTRO DE DATOS", expanded=(st.session_state.menu_main == "CENTRO DE DATOS")):
                    opciones_hub = ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "ESCANEAR QR", "HERRAMIENTAS"]
                    for s in opciones_hub:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_hub_{s}2"):
                            if permisos.get("CENTRO DE DATOS", False) and (permisos.get(s, False) or usuario.upper() == "RIGOBERTO"):
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
                            else:
                                _sin_acceso(s)

                with st.expander("FINANZAS", expanded=(st.session_state.menu_main == "FINANZAS")):
                    opciones_fin = ["WALLET", "CAJA CHICA", "GASTOS"]
                    for s in opciones_fin:
                        label = f"» {s}" if st.session_state.menu_sub == s else s
                        if st.button(label, use_container_width=True, key=f"pop_fin_{s}2"):
                            if permisos.get("FINANZAS", False) and (permisos.get(s, False) or usuario.upper() == "RIGOBERTO"):
                                registrar_acceso_github(usuario, f"FINANZAS - {s}")
                                st.session_state.menu_main = "FINANZAS"
                                st.session_state.menu_sub = s
                                st.session_state.busqueda_activa = False
                                if s == "GASTOS":
                                    st.switch_page("pages/gastos.py")
                                st.rerun()
                            else:
                                _sin_acceso(s)

                with st.expander("ENFOQUE", expanded=(st.session_state.get("menu_main") == "ENFOQUE")):
                    opciones_enf = ["MORENO", "VAZQUEZ", "MIGUEL"]
                    for s in opciones_enf:
                        label = f"» {s}" if st.session_state.get("menu_sub") == s else s
                        if st.button(label, use_container_width=True, key=f"pop_enf_{s}2"):
                            if permisos.get("ENFOQUE", False) and (permisos.get(s, False) or usuario.upper() == "RIGOBERTO"):
                                registrar_acceso_github(usuario, f"ENFOQUE - {s}")
                                st.session_state.menu_main = "ENFOQUE"
                                st.session_state.menu_sub = s
                                st.rerun()
                            else:
                                _sin_acceso(s)

                if st.button("ACCESS CONTROL", use_container_width=True, key="pop_access_ctrl2"):
                    if permisos.get("ACCESS CONTROL", False) or usuario.upper() == "RIGOBERTO":
                        registrar_acceso_github(usuario, "ACCESS CONTROL")
                        st.session_state.menu_main = "ACCESS CONTROL"
                        st.session_state.menu_sub = "SETTINGS"
                        st.switch_page("pages/accesscontrol.py")
                    else:
                        _sin_acceso("ACCESS CONTROL")
            
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
            elif tipo == "FACTURACION":
                fact_color = "#F59E0B"  # ámbar: información encontrada, pero sin envío procesado
                # Tipos de TRANSPORTE que por regla NO se procesan para envío (editable)
                TRANSPORTES_SIN_ENVIO = ["CEDIS", "LOCAL", "CLIENTE PASA"]

                def _val(row, nombre_col):
                    """Valor limpio de una columna (sin importar mayúsculas/espacios en el encabezado)."""
                    for col in row.index:
                        if str(col).strip().upper() == nombre_col:
                            v = str(row[col]).strip()
                            return "" if v.lower() in ("", "nan", "none", "nat") else v
                    return ""

                st.markdown(
                    f"<style>.card-fact {{ transition: all 0.3s ease; }} .card-fact:hover {{ transform: translateX(8px); border-color: {fact_color} !important; background: rgba(38, 32, 20, 0.95) !important; box-shadow: 0 0 15px rgba(245, 158, 11, 0.15); }}</style>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"""<div style="background: rgba(245,158,11,0.08); border: 1px solid {fact_color}; border-left: 5px solid {fact_color}; padding: 16px 22px; border-radius: 8px; margin-bottom: 18px; font-family: 'Inter', sans-serif; color: white;">
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                            <div style="width:9px; height:9px; background:{fact_color}; border-radius:50%; box-shadow:0 0 8px {fact_color};"></div>
                            <span style="font-size:12px; font-weight:800; color:{fact_color}; letter-spacing:1.5px; text-transform:uppercase;">INFORMACIÓN ENCONTRADA EN FACTURACIÓN ({total})</span>
                        </div>
                        <div style="font-size:12px; color:rgba(255,255,255,0.85); font-weight:600; margin-left:19px; line-height:1.5;">
                            El registro fue localizado; sin embargo, <b>aún no ha sido procesado para envío</b>.<br>
                            Revisa el <b>TRANSPORTE</b> para conocer el motivo o comunícate con <b>Facturación</b> o <b>Logística</b>.
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                for _, f in resultados.iterrows():
                    pedido_f = html.escape(_val(f, "PEDIDO") or "S/N")
                    factura_f = html.escape(_val(f, "FACTURA"))
                    no_cliente_f = html.escape(_val(f, "CLIENTE"))
                    cliente_f = html.escape(_val(f, "NOMBRE_CLIENTE") or "N/A")
                    destino_f = html.escape(_val(f, "DESTINO") or _val(f, "CUIDAD"))
                    fecha_f = html.escape(_val(f, "FECHA_CONTA"))
                    partidas_f = _val(f, "_PARTIDAS")
                    clase_raw = _val(f, "TRANSPORTE")
                    clase_f = html.escape(clase_raw.upper() if clase_raw else "NO ESPECIFICADA")

                    # ¿El transporte es de los que no generan envío?
                    sin_envio_por_clase = any(k in clase_raw.upper() for k in TRANSPORTES_SIN_ENVIO) if clase_raw else False
                    if sin_envio_por_clase:
                        motivo_html = f"Este tipo de transporte <b>no se procesa para envío</b>"
                        clase_color = "#FF6B6B"
                    elif clase_raw:
                        motivo_html = "Transporte sin regla de exclusión: confirmar con Facturación / Logística"
                        clase_color = fact_color
                    else:
                        motivo_html = "Sin transporte registrado: confirmar con Facturación / Logística"
                        clase_color = fact_color

                    linea_cliente = f"ID: {no_cliente_f}" if no_cliente_f else ""
                    detalle_pedido = []
                    if factura_f:
                        detalle_pedido.append(f"Factura: {factura_f}")
                    if fecha_f:
                        detalle_pedido.append(f"Fecha: {fecha_f}")
                    if partidas_f and partidas_f != "1":
                        detalle_pedido.append(f"{partidas_f} partidas")
                    linea_guia = f"<span style='font-size:11px;color:rgba(255,255,255,0.5);font-weight:600;'>{' | '.join(detalle_pedido)}</span>" if detalle_pedido else ""

                    st.markdown(
                        f"<div class='card-fact' style='background:rgba(38,32,20,0.75);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {fact_color};border-radius:12px;padding:16px 24px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;'>"
                        f"<div style='flex:1.2;min-width:150px;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>PEDIDO</span><br><b style='font-size:17px;color:{fact_color};letter-spacing:0.5px;'># {pedido_f}</b><br>{linea_guia}</div>"
                        f"<div style='flex:2.4;min-width:220px;padding-left:22px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CLIENTE / DESTINO</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{cliente_f}</b><br><span style='font-size:11px;color:rgba(255,255,255,0.5);font-weight:600;'>{linea_cliente}{' | ' if linea_cliente and destino_f else ''}{destino_f}</span></div>"
                        f"<div style='flex:1.8;min-width:200px;padding-left:22px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>TRANSPORTE</span><br><span style='background:{clase_color}20;color:{clase_color};padding:4px 12px;border-radius:6px;font-size:13px;font-weight:900;border:1px solid {clase_color};letter-spacing:1px;display:inline-block;margin-top:3px;'>{clase_f}</span><br><span style='font-size:10px;color:rgba(255,255,255,0.7);font-weight:600;display:inline-block;margin-top:5px;'>{motivo_html}</span></div>"
                        f"<div style='flex:1.2;min-width:140px;text-align:right;'><span style='background:{fact_color}15;color:{fact_color};padding:5px 12px;border-radius:6px;font-size:10px;font-weight:800;border:1px solid {fact_color};text-transform:uppercase;letter-spacing:1px;display:inline-block;'>SIN PROCESAR PARA ENVÍO</span></div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                if total == 1:
                    envio = resultados.iloc[0]
                    es_envios = str(envio.get("_ORIGEN", "")) == "ENVIOS"
                    entregado_real = pd.notna(envio.get("FECHA DE ENTREGA REAL"))
                    f_entrega_val = envio["FECHA DE ENTREGA REAL"] if entregado_real else "PENDIENTE"
                    trigger_val = str(envio.get("TRIGGER", "")).strip()
                    tiene_guia = pd.notna(envio.get("NÚMERO DE GUÍA")) and str(envio.get("NÚMERO DE GUÍA")).strip() not in ["", "0", "nan"]

                    if tiene_guia:
                        n_guia = envio["NÚMERO DE GUÍA"]
                    elif trigger_val == "Enviada":
                        n_guia = "GENERANDO GUÍA..."
                    elif es_envios:
                        n_guia = "POR ASIGNAR"
                    else:
                        n_guia = "EN ESPERA DE SURTIDO"

                    f_promesa_dt = pd.to_datetime(envio.get("PROMESA DE ENTREGA"), dayfirst=True, errors="coerce")
                    if pd.notnull(f_promesa_dt):
                        f_promesa_dt = f_promesa_dt.normalize()
                    hoy = pd.Timestamp(datetime.now()).normalize()

                    if es_envios:
                        # El estatus viene directo de envios.csv (columna ESTATUS)
                        status_text = str(envio.get("COMENTARIOS", "")).strip().upper()
                        if status_text in ("", "NAN", "NONE"):
                            status_text = "EN PROCESO"
                        if "ENTREGAD" in status_text:
                            status_color, f_entrega_val = "#00FFAA", "ENTREGADO"
                        elif any(k in status_text for k in ("CANCEL", "RETRAS", "INCIDENC")):
                            status_color = "#ff4b4b"
                        elif any(k in status_text for k in ("TRANSIT", "TRÁNSIT", "RUTA", "ENVIAD", "EMBARC")):
                            status_color = "#38bdf8"
                        else:
                            status_color = "#FFA500"
                    elif not tiene_guia:
                        status_text, status_color = ("GENERANDO GUÍA", "#38bdf8") if trigger_val == "Enviada" else ("SURTIENDO", "#FFA500")
                    elif not entregado_real:
                        status_text, status_color = ("EN TRÁNSITO", "#38bdf8") if pd.isna(f_promesa_dt) or hoy <= f_promesa_dt else ("RETRASO EN TRÁNSITO", "#ff4b4b")
                    else:
                        f_entrega_dt = pd.to_datetime(envio.get("FECHA DE ENTREGA REAL"), dayfirst=True, errors="coerce")
                        if pd.notnull(f_entrega_dt):
                            f_entrega_dt = f_entrega_dt.normalize()
                        status_text, status_color = ("ENTREGADO", "#00FFAA") if pd.isna(f_promesa_dt) or f_entrega_dt <= f_promesa_dt else ("ENTREGA CON RETRASO", "#ff4b4b")

                    costo_txt = "PENDIENTE" if es_envios else f"$ {envio.get('COSTO DE LA GUÍA','0.00')}"
                    tarjeta_unica_html = f"""<div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; padding: 20px 25px; border-radius: 8px; width: 100%; font-family: 'Inter', sans-serif; color: white; box-sizing: border-box; margin-bottom: 25px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;"><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #38bdf8; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #38bdf8;"></div><div style="font-size: 9px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;">ENVÍO</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('FECHA DE ENVÍO','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #38bdf8; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #a855f7; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #a855f7;"></div><div style="font-size: 9px; font-weight: 800; color: #a855f7; letter-spacing: 1px;">GUÍA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{n_guia if tiene_guia else 'EN PROCESO'}</div></div><div style="flex-grow: 1; height: 2px; background: #a855f7; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: #eab308; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px #eab308;"></div><div style="font-size: 9px; font-weight: 800; color: #eab308; letter-spacing: 1px;">PROMESA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{envio.get('PROMESA DE ENTREGA','N/A')}</div></div><div style="flex-grow: 1; height: 2px; background: #00FFAA; margin: 0 5px; opacity: 0.6; transform: translateY(-10px);"></div><div style="text-align: center;"><div style="width: 10px; height: 10px; background: {status_color}; border-radius: 50%; margin: 0 auto 6px auto; box-shadow: 0 0 8px {status_color};"></div><div style="font-size: 9px; font-weight: 800; color: {status_color}; letter-spacing: 1px;">ENTREGA</div><div style="font-size: 10px; color: rgba(255,255,255,0.7); font-weight: 600; margin-top: 2px;">{f_entrega_val}</div></div></div><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; width: 100%; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 15px;"><div style="flex: 1.2; min-width: 200px;"><div style="color: {accent_color}; font-size: 16px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">{envio.get('FLETERA','N/A')}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">TALÓN / FOLIO</div><div style="color: {accent_color}; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 0.5px; line-height: 1.2;">{n_guia}</div><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 4px;">REF / PEDIDO: <span style="color: white; font-size: 13px; font-weight: 700;">{envio.get('NÚMERO DE PEDIDO','S/N')}</span></div></div><div style="flex: 2.5; min-width: 280px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">DESTINATARIO / CLIENTE</div><div style="color: white; font-weight: 800; font-size: 13px; text-transform: uppercase; line-height: 1.3; margin-top: 2px;">{envio.get('NOMBRE DEL CLIENTE','N/A')}</div><div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 2px;">ID: {envio.get('NO CLIENTE','')} | {envio.get('DOMICILIO','')}</div><div style="font-size: 11px; color: {accent_color}; margin-top: 4px; font-weight: 600;">📍 GDL → {envio.get('DESTINO','N/A')}</div></div><div style="flex: 1.2; min-width: 150px; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;"><div style="color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">RESUMEN CARGA</div><div style="color: white; font-weight: 700; font-size: 11px; margin-top: 2px;">BULTOS: <span style="color: {accent_color};">{envio.get('CANTIDAD DE CAJAS','0')}</span></div><div style="color: {accent_color}; font-weight: 800; font-size: 13px; margin-top: 2px;">{costo_txt}</div></div><div style="text-align: right; min-width: 130px;"><span style="background-color: {status_color}15; color: {status_color}; padding: 5px 12px; border-radius: 6px; font-size: 10px; font-weight: 800; border: 1px solid {status_color}; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">ESTATUS: {status_text}</span></div></div></div>"""
                    st.markdown(tarjeta_unica_html, unsafe_allow_html=True)

                    if es_envios:
                        def _dato_env(nombre):
                            v = str(envio.get(nombre, "")).strip()
                            return "" if v.lower() in ("", "nan", "none", "nat") else html.escape(v)

                        extras_env = [
                            ("ESTATUS ALMACÉN", _dato_env("ESTATUS ALMACEN")),
                            ("ESTATUS LOGÍSTICA", _dato_env("ESTATUS LOGISTICA")),
                            ("RECOMENDACIÓN", _dato_env("RECOMENDACION")),
                            ("NOMBRE EXTRANJERO", _dato_env("Nombre_Extran")),
                        ]
                        chips_env = "".join(
                            f"<div style='flex:1;min-width:160px;'><div style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>{etq}</div>"
                            f"<div style='color:white;font-size:12px;font-weight:700;margin-top:2px;'>{val}</div></div>"
                            for etq, val in extras_env if val
                        )
                        if chips_env:
                            st.markdown(
                                f"<div style=\"background:{vars_css['card']};border:1px solid {vars_css['border']};border-left:5px solid #a855f7;border-radius:8px;padding:12px 25px;margin:-15px 0 25px 0;display:flex;gap:20px;flex-wrap:wrap;font-family:'Inter',sans-serif;\">{chips_env}</div>",
                                unsafe_allow_html=True,
                            )
                else:
                    st.markdown(f"<div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'><div style='background: {azul_premium}; width: 5px; height: 22px; border-radius: 3px; box-shadow: 0 0 10px {azul_premium};'></div><span style='color: white; font-size: 15px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;'>MULTIPLE MATCHES DETECTED <span style='color: {azul_premium};'>({total})</span></span></div>", unsafe_allow_html=True)
                    st.markdown(f"<style>.card-nexion {{ transition: all 0.3s ease !important; cursor: pointer; }} .card-nexion:hover {{ transform: translateX(10px); border-color: {azul_premium} !important; background: rgba(30, 39, 46, 0.9) !important; box-shadow: 0 0 15px rgba(0, 212, 255, 0.2); }}</style>", unsafe_allow_html=True)

                    for _, d in resultados.iterrows():
                        status_text = d["COMENTARIOS"] if "COMENTARIOS" in d and pd.notna(d.get("COMENTARIOS")) else "OK"
                        st.markdown(f"<div class='card-nexion' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {azul_premium};border-radius:12px;padding:18px 25px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>PEDIDO / FACTURA</span><br><b style='font-size:18px;color:{azul_premium};letter-spacing:0.5px;'># {d.get('NÚMERO DE PEDIDO','')}</b><br><span style='font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;'>Envío: {d.get('FECHA DE ENVÍO','')}</span></div><div style='flex:2.5;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CLIENTE / DESTINO</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('NOMBRE DEL CLIENTE','')}</b><br><i style='font-size:11px;color:rgba(255,255,255,0.5);font-style:normal;font-weight:600;'>{d.get('DESTINO','')}</i></div><div style='flex:1.8;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>TRANSPORTE Y GUÍA</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('FLETERA', d.get('TRANSPORTE', 'LOGÍSTICA'))}</b><br><span style='font-size:12px;color:{azul_premium};font-weight:700;font-family:monospace;'>{d.get('NÚMERO DE GUÍA','')}</span></div><div style='flex:1.2;text-align:right;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>ESTATUS ENTREGA</span><br><b style='font-size:14px;color:{azul_premium};'>{d.get('FECHA DE ENTREGA REAL','')}</b><br><span style='font-size:10px;color:white;font-weight:800;text-transform:uppercase;opacity:0.8;'>{status_text}</span></div></div>", unsafe_allow_html=True)

        st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)

    # ── FOOTER FIJO ────────────────────────
    st.markdown(
        f"""
        <div class="footer">
            NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
            <span style="opacity:0.7; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
            <span style="color:{vars_css['text']}; font-weight:600; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
        </div>
    """,
        unsafe_allow_html=True,
    )
