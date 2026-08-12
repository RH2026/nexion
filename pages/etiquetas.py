from datetime import datetime
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
from auth import exigir_autenticacion

exigir_autenticacion("etiquetas")



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
                    No tienes permisos para acceder al módulo de <b style="color: white; text-transform: uppercase;">ETIQUETAS</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_regresar_m, _ = st.columns([1.5, 4])
        with col_regresar_m:
            if st.button("REGRESAR AL INICIO", key="btn_regresar_modulo", use_container_width=True):
                st.switch_page("pages/indicadores.py")
        st.stop()

# Blindaje correcto para ETIQUETAS (dentro de CENTRO DE DATOS)
verificar_permiso_pagina("CENTRO DE DATOS", "ETIQUETAS")


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

def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
    texto = str(texto).upper()
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    tamano_actual = tamano_max
    while len(lineas) > max_lineas and tamano_actual > 7:
        tamano_actual -= 0.5
        lineas = simpleSplit(texto, fuente, tamano_actual, ancho_max)
    
    c.setFont(fuente, tamano_actual)
    y_actual = y_inicio
    for line in lineas[:max_lineas]: 
        c.drawCentredString(x_centro, y_actual, line)
        y_actual -= interlineado
    return y_actual 

def generar_etiquetas_nexion(df_datos):
    output = io.BytesIO()
    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
    
    margen_h = 0.8 * cm
    w_util = w_rec - (2 * margen_h)
    x_centro = w_rec / 2

    if df_datos.empty:
        c.save()
        return output.getvalue()

    for index, row in df_datos.iterrows():
        try:
            cantidad_real = int(row['Quantity'])
            iteraciones = cantidad_real
        except: 
            continue 

        nombre_crudo = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', row.get('NOMBRE_CLIENTE', 'SIN NOMBRE'))))
        nombre_final = limpiar_parentesis(nombre_crudo)
        direccion_final = row.get('DIRECCION', row.get('Domicilio', row.get('DOMICILIO', 'DIRECCIÓN NO DISPONIBLE')))
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', 'TRES GUERRAS')))
        factura_val = str(row.get('Factura', row.get('FOLIO', 'S/F')))

        for i in range(iteraciones):
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(0, 0, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_centro, h_rec - 0.3*cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            c.setFont("Helvetica", 5.5)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(c, info_contacto, x_centro, h_rec - 0.7*cm, w_util, "Helvetica", 5.5, 0.25*cm, max_lineas=1)
            
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(margen_h, h_rec - 0.95*cm, w_rec - margen_h, h_rec - 0.95*cm)
            c.setStrokeColorRGB(0, 0, 0)

            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_centro, h_rec - 1.8*cm, w_util, "Helvetica-Bold", 22, 0.65*cm, max_lineas=3)
            
            y_inicio_direccion = y_termino_nombre - 0.5*cm
            if y_inicio_direccion > 4.3*cm: y_inicio_direccion = 4.3*cm
            if y_inicio_direccion < 2.9*cm: y_inicio_direccion = 2.9*cm
            dibujar_texto_bloque_pro(c, direccion_final, x_centro, y_inicio_direccion, w_util, "Helvetica-Bold", 12.0, 0.45*cm, max_lineas=3)

            c.setLineWidth(0.6)
            y_linea_pie = 1.4*cm
            c.line(margen_h, y_linea_pie, w_rec - margen_h, y_linea_pie)
            
            x_col1 = margen_h + 0.1*cm         
            x_col2 = 5.25 * cm                 
            x_col3 = w_rec - margen_h - 2.8*cm 

            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_col1, y_linea_pie - 0.4*cm, "FACTURA")
            c.drawCentredString(x_col2, y_linea_pie - 0.4*cm, "CAJAS")
            c.drawString(x_col3, y_linea_pie - 0.4*cm, "TRANSPORTE")
            
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_col1, y_linea_pie - 1.0*cm, factura_val)
            c.drawCentredString(x_col2, y_linea_pie - 1.0*cm, f"{i + 1} / {cantidad_real}")
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(x_col3, y_linea_pie - 1.0*cm, transporte_final[:16])
            
            c.showPage()

    c.save()
    return output.getvalue()


# Inicialización segura de estados de menú
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "CENTRO DE DATOS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "ETIQUETAS"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1
if "tipo_resultado" not in st.session_state:
    st.session_state.tipo_resultado = "OPERACION"


# ==========================================
# 4. HEADER CON 4 COLUMNAS, BUSCADOR Y MENÚ BLINDADO
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
        ruta = f"CENTRO DE DATOS <span style='color: {azul_nexion}; opacity: 0.8; margin: 0 15px;'>/</span> <span style='color: {oro_brillante}; font-weight: 500; text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);'>ETIQUETAS</span>"

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

            # 1. Búsqueda en Matriz Principal (Global)
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

            # 2. Búsqueda en Archivo T1.xlsx
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

            # 3. CRUCE DE INFORMACIÓN (Si está en Matriz Global pero le falta la guía, se la inyectamos desde T1)
            if not res_ops.empty and not res_t1.empty:
                for idx, row in res_ops.iterrows():
                    guia_actual = str(row.get("NÚMERO DE GUÍA", "")).strip()
                    # Si en la matriz global la guía está vacía, NaN o ceros, la buscamos en T1
                    if guia_actual in ["", "nan", "0", "None"]:
                        pedido_global = str(row.get("NÚMERO DE PEDIDO", "")).strip()
                        # Buscamos coincidencia en T1 por número de pedido/factura
                        match_en_t1 = res_t1[res_t1["NÚMERO DE PEDIDO"].astype(str).str.strip() == pedido_global]
                        if not match_en_t1.empty:
                            # Tomamos la guía y los datos clave de T1 y se los asignamos al registro de la matriz global
                            res_ops.loc[idx, "NÚMERO DE GUÍA"] = match_en_t1.iloc[0].get("NÚMERO DE GUÍA", guia_actual)
                            res_ops.loc[idx, "FLETERA"] = match_en_t1.iloc[0].get("FLETERA", "TRES GUERRAS")
                            if "COSTO DE LA GUÍA" in match_en_t1.columns and pd.notna(match_en_t1.iloc[0].get("COSTO DE LA GUÍA")):
                                res_ops.loc[idx, "COSTO DE LA GUÍA"] = match_en_t1.iloc[0].get("COSTO DE LA GUÍA")

            # 4. Búsqueda en Inventario (Por si acaso se busca un SKU/Código)
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

            # Asignación final de resultados
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
                                st.switch_page("pages/asignacionfletera.py")
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

    # RENDERIZADO DE RESULTADOS DE BÚSQUEDA
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
                    status_text = d["COMENTARIOS"] if "COMENTARIOS" in d and pd.notna(d.get("COMENTARIOS")) else "OK"
                    st.markdown(f"<div class='card-nexion' style='background:rgba(30,39,46,0.7);border:1px solid rgba(255,255,255,0.05);border-left:4px solid {azul_premium};border-radius:12px;padding:18px 25px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;'><div style='flex:1;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>PEDIDO / FACTURA</span><br><b style='font-size:18px;color:{azul_premium};letter-spacing:0.5px;'># {d.get('NÚMERO DE PEDIDO','')}</b><br><span style='font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;'>Envío: {d.get('FECHA DE ENVÍO','')}</span></div><div style='flex:2.5;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>CLIENTE / DESTINO</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('NOMBRE DEL CLIENTE','')}</b><br><i style='font-size:11px;color:rgba(255,255,255,0.5);font-style:normal;font-weight:600;'>{d.get('DESTINO','')}</i></div><div style='flex:1.8;padding-left:25px;border-left:1px solid rgba(255,255,255,0.08);'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>TRANSPORTE Y GUÍA</span><br><b style='font-size:13px;color:white;text-transform:uppercase;'>{d.get('FLETERA', d.get('TRANSPORTE', 'LOGÍSTICA'))}</b><br><span style='font-size:12px;color:{azul_premium};font-weight:700;font-family:monospace;'>{d.get('NÚMERO DE GUÍA','')}</span></div><div style='flex:1.2;text-align:right;'><span style='color:rgba(255,255,255,0.4);font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;'>ESTATUS ENTREGA</span><br><b style='font-size:14px;color:{azul_premium};'>{d.get('FECHA DE ENTREGA REAL','')}</b><br><span style='font-size:10px;color:white;font-weight:800;text-transform:uppercase;opacity:0.8;'>{status_text}</span></div></div>", unsafe_allow_html=True)

        st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-top:1px solid #ffffff; margin:5px 0 15px; opacity:0.1;'>", unsafe_allow_html=True)


# ==========================================
# 5. INTERFAZ PRINCIPAL (PESTAÑAS DE ETIQUETAS)
# ==========================================
def main():    
    tab1, tab2, tab3 = st.tabs([
        "CARGAR POR EXCEL (Lote)", 
        "BASE DE DATOS GITHUB", 
        "CAPTURA MANUAL"
    ])
    
    with tab1:
        st.subheader("Cargar Archivo Excel de Pedidos")
        archivo = st.file_uploader("Sube tu archivo .xlsx", type=["xlsx"], key="creador_etiquetas_excel")
        
        if archivo:
            try:
                df_excel = pd.read_excel(archivo, sheet_name=0)
                st.subheader("Vista previa de datos")
                st.dataframe(df_excel[['Quantity', 'DIRECCION', 'Factura']].head(5), use_container_width=True)

                if st.button("Generar Etiquetas desde Excel", use_container_width=True, key="btn_gen_excel"):
                    with st.spinner("Generando documento..."):
                        pdf_data = generar_etiquetas_nexion(df_excel)
                        if pdf_data:
                            st.success("¡Documento generado con éxito!")
                            st.download_button(
                                label="Descargar PDF de Etiquetas",
                                data=pdf_data,
                                file_name="etiquetas_nexion_excel.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="dl_excel"
                            )
            except Exception as e:
                st.error(f"Error al leer los pedidos: {e}")
    
    with tab2:
        st.subheader("Base de Datos - facturacion_moreno.csv")
        df_facturacion = cargar_csv_github()
        
        if not df_facturacion.empty:
            df_facturacion["Factura"] = df_facturacion["Factura"].astype(str)
            facturas_disponibles = df_facturacion["Factura"].unique()

            c_col1, c_col2 = st.columns(2)
            with c_col1:
                modo_busqueda = st.selectbox(
                    "🔍 Método de Selección", 
                    ["Seleccionar de la lista", "Escribir folio manual"],
                    key="modo_busq_etq_github"
                )

            num_factura_seleccionada = None
            with c_col2:
                if modo_busqueda == "Seleccionar de la lista":
                    num_factura_seleccionada = st.selectbox("📦 Selecciona Factura / Folio", facturas_disponibles, key="sel_factura_etq_github")
                else:
                    num_factura_seleccionada = st.text_input("✍️ Ingresa Folio Manual", key="txt_folio_manual_etq_github")

            if num_factura_seleccionada:
                df_encontrado = df_facturacion[df_facturacion["Factura"] == str(num_factura_seleccionada).strip()]
                
                if not df_encontrado.empty:
                    row_data = df_encontrado.iloc[0].copy()
                    
                    st.markdown("---")
                    st.info(f"📋 **Cliente encontrado:** {row_data.get('Nombre_Extran', row_data.get('Nombre_Cliente', 'SIN NOMBRE'))}")
                    
                    col_c, col_t = st.columns(2)
                    with col_c:
                        cajas_manual = st.number_input("📦 Cantidad de Cajas / Bultos", min_value=1, value=1, step=1, key="num_cajas_manual_db")
                    with col_t:
                        transporte_manual = st.text_input("🚛 Transporte / Paquetería", value=str(row_data.get('RECOMENDACION', row_data.get('Transporte', 'TRES GUERRAS'))), key="txt_transporte_manual_db")
                    
                    row_data['Quantity'] = cajas_manual
                    row_data['RECOMENDACION'] = transporte_manual
                    
                    df_procesar_individual = pd.DataFrame([row_data])

                    if st.button("Generar Etiqueta Individual", use_container_width=True, key="btn_gen_moreno"):
                        with st.spinner("Generando etiqueta..."):
                            pdf_data_moreno = generar_etiquetas_nexion(df_procesar_individual)
                            if pdf_data_moreno:
                                st.success("¡Etiqueta generada con éxito!")
                                st.download_button(
                                    label="Descargar PDF de Etiqueta",
                                    data=pdf_data_moreno,
                                    file_name=f"etiqueta_factura_{num_factura_seleccionada}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key="dl_moreno"
                                )
                else:
                    st.warning("El folio ingresado no se encontró en la base de datos de GitHub.")
        else:
            st.warning("No se pudieron cargar los datos de GitHub. Verifica tu token o conexión.")
    
    with tab3:
        st.markdown("""
            <div style="background-color: #263243; padding: 10px 15px; border-radius: 5px; color: #ffffff; font-size: 14px; margin-bottom: 20px;">
                Ingresa los datos del envío manualmente (sin necesidad de archivos).
            </div>
        """, unsafe_allow_html=True)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            manual_factura = st.text_input("NÚMERO DE FACTURA / FOLIO", value="235050", key="man_factura")
            manual_nombre = st.text_input("NOMBRE DEL CLIENTE / HOTEL", value="HOTEL EJEMPLO", key="man_nombre")
            manual_cajas = st.number_input("CANTIDAD DE CAJAS / BULTOS", min_value=1, value=1, step=1, key="man_cajas")

        with col_m2:
            manual_direccion = st.text_area("DIRECCIÓN COMPLETA DE DESTINO", value="Av. Principal #123, Col. Centro, C.P. 44100, Guadalajara, Jal.", height=107, key="man_direccion")
            manual_transporte = st.text_input("TRANSPORTE / PAQUETERÍA", value="TRES GUERRAS", key="man_transporte")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generar Etiqueta Manual", use_container_width=True, key="btn_gen_manual_libre"):
            if not manual_factura or not manual_nombre or not manual_direccion:
                st.error("Por favor completa los campos obligatorios (Factura, Nombre y Dirección).")
            else:
                dict_manual = {
                    'Factura': str(manual_factura),
                    'Nombre_Cliente': str(manual_nombre),
                    'DIRECCION': str(manual_direccion),
                    'Quantity': int(manual_cajas),
                    'RECOMENDACION': str(manual_transporte)
                }
                df_manual_pro = pd.DataFrame([dict_manual])

                with st.spinner("Generando etiqueta manual..."):
                    pdf_data_manual = generar_etiquetas_nexion(df_manual_pro)
                    if pdf_data_manual:
                        st.success("¡Etiqueta manual generada con éxito!")
                        st.download_button(
                            label="Descargar PDF de Etiqueta Manual",
                            data=pdf_data_manual,
                            file_name=f"etiqueta_manual_{manual_factura}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="dl_manual_libre"
                        )

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
