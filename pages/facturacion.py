import base64
from datetime import datetime, timedelta
import io
import re
import time
import unicodedata
import zipfile
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit as st
import pytz
from auth import exigir_autenticacion

exigir_autenticacion("facturacion")

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

[data-testid="stVerticalBlock"] > div:not(:has(.footer)) {{
    animation: fadeInUp 0.6s ease-out;
}}

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

div.stButton > button {{
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

div.stButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

.footer {{ 
    position: fixed !important; 
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
# 2. SISTEMA DE SEGURIDAD PRO
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/facturacion.py"
    st.switch_page("pages/log.py")

def verificar_permiso_pagina(modulo, submodulo=None):
    usuario_actual = st.session_state.get("usuario_activo", "").upper()
    if usuario_actual == "RIGOBERTO":
        return True
    
    permisos = st.session_state.get("permisos", {})
    if not permisos.get(modulo.upper(), False):
        st.stop()
    if submodulo and not permisos.get(submodulo.upper(), False):
        st.stop()

verificar_permiso_pagina("CENTRO DE DATOS", "FACTURACIÓN")


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
    url = f"https://raw.githubusercontent.com/{globals().get('GITHUB_USER', 'RH2026')}/{globals().get('GITHUB_REPO', 'nexion')}/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
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


def calcular_fecha_programacion():
    tz_gdl = pytz.timezone("America/Mexico_City")
    ahora_gdl = datetime.now(tz_gdl)
    hora_actual = ahora_gdl.hour
    
    if hora_actual < 12:
        return ahora_gdl.strftime("%d/%m/%Y")
    elif hora_actual >= 15:
        return (ahora_gdl + timedelta(days=1)).strftime("%d/%m/%Y")
    else:
        return ahora_gdl.strftime("%d/%m/%Y")


# ==========================================
# 3.1 GESTIÓN DE ARCHIVOS GITHUB
# ==========================================
def guardar_facturacion_github(df_nuevos):
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "facturacion.csv"
    
    if not TOKEN:
        st.error("Falta configurar el GITHUB_TOKEN en los Secrets de Streamlit.")
        return False

    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    
    df_procesado = df_nuevos.copy()
    r = requests.get(url, headers=headers)
    df_existente = pd.DataFrame()
    sha = None
    
    if r.status_code == 200:
        file_info = r.json()
        sha = file_info["sha"]
        content_decoded = base64.b64decode(file_info["content"]).decode("utf-8-sig")
        df_existente = pd.read_csv(io.StringIO(content_decoded))
    
    col_fact_nuevos = next((c for c in df_procesado.columns if "FACTURA" in c.upper() or c.upper() == "FACTURA"), None)
    
    if not df_existente.empty and col_fact_nuevos:
        col_fact_existente = next((c for c in df_existente.columns if "FACTURA" in c.upper() or c.upper() == "FACTURA"), col_fact_nuevos)
        facturas_existentes_set = set(df_existente[col_fact_existente].astype(str).str.strip().unique())
        df_procesado = df_procesado[~df_procesado[col_fact_nuevos].astype(str).str.strip().isin(facturas_existentes_set)].copy()
        
        if df_procesado.empty:
            st.warning("Todas las facturas de este rango ya existen previamente en `facturacion.csv`. No se agregaron duplicados.")
            return True

        df_combinado = pd.concat([df_existente, df_procesado], ignore_index=True)
    else:
        df_combinado = df_procesado

    csv_buffer = io.StringIO()
    df_combinado.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    content_base64 = base64.b64encode(csv_buffer.getvalue().encode("utf-8")).decode("utf-8")
    
    data = {
        "message": "Actualización limpia de facturacion.csv sin duplicados",
        "content": content_base64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha 

    put_response = requests.put(url, headers=headers, json=data)
    return put_response.status_code in [200, 201]


def guardar_archivo_rigoberto_github(df_datos, nombre_archivo):
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    
    if not nombre_archivo.endswith(".csv"):
        nombre_archivo = nombre_archivo.split(".")[0] + ".csv"
        
    FILE_PATH = f"lotes_rigoberto/{nombre_archivo}"
    
    if not TOKEN:
        st.error("Falta configurar el GITHUB_TOKEN.")
        return False

    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    
    csv_buffer = io.StringIO()
    df_datos.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    content_base64 = base64.b64encode(csv_buffer.getvalue().encode("utf-8")).decode("utf-8")
    
    data = {
        "message": f"Subida de archivo personalizado para Rigoberto: {nombre_archivo}",
        "content": content_base64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha 

    put_response = requests.put(url, headers=headers, json=data)
    return put_response.status_code in [200, 201]


def listar_archivos_rigoberto_github():
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FOLDER_PATH = "lotes_rigoberto"
    
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"} if TOKEN else {}
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FOLDER_PATH}"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            files = r.json()
            return [f["name"] for f in files if f["name"].endswith(".csv")]
    except Exception:
        pass
    return []


def cargar_archivo_rigoberto_github(nombre_archivo):
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = f"lotes_rigoberto/{nombre_archivo}"
    
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"} if TOKEN else {}
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content_decoded = base64.b64decode(r.json()["content"]).decode("utf-8-sig")
            return pd.read_csv(io.StringIO(content_decoded))
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=30)
def cargar_facturacion_github():
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "facturacion.csv"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"} if TOKEN else {}
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content_decoded = base64.b64decode(r.json()["content"]).decode("utf-8-sig")
            return pd.read_csv(io.StringIO(content_decoded))
    except Exception:
        pass
    return pd.DataFrame()


def actualizar_historial_envios_github(df_nuevos):
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "envios.csv"
    
    if not TOKEN:
        return False

    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    
    df_procesado = df_nuevos.copy()
    if "FECHA DE PROGRAMACION" not in df_procesado.columns:
        df_procesado["FECHA DE PROGRAMACION"] = calcular_fecha_programacion()
    for col in ["FECHA DE ENVIO", "ESTATUS", "FECHA ACTUAL", "SERVICIO"]:
        if col not in df_procesado.columns:
            df_procesado[col] = ""

    r = requests.get(url, headers=headers)
    df_existente = pd.DataFrame()
    sha = None
    
    if r.status_code == 200:
        file_info = r.json()
        sha = file_info["sha"]
        content_decoded = base64.b64decode(file_info["content"]).decode("utf-8-sig")
        df_existente = pd.read_csv(io.StringIO(content_decoded))
    
    if not df_existente.empty:
        df_combinado = pd.concat([df_existente, df_procesado], ignore_index=True)
    else:
        df_combinado = df_procesado

    if "Factura" in df_combinado.columns:
        df_combinado = df_combinado.drop_duplicates(subset=["Factura"], keep="last")

    csv_buffer = io.StringIO()
    df_combinado.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    content_base64 = base64.b64encode(csv_buffer.getvalue().encode("utf-8")).decode("utf-8")
    
    data = {
        "message": "Actualización automática en envios.csv",
        "content": content_base64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha 

    put_response = requests.put(url, headers=headers, json=data)
    return put_response.status_code in [200, 201]


# ==========================================
# 3.2 FUNCIONES DE SELLADO CON QR
# ==========================================
def crear_imagen_qr(contenido_qr):
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(contenido_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generar_sellos_fisicos(df_datos, x_pos, y_pos):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(612, 792)) 
    tz_gdl = pytz.timezone("America/Mexico_City")
    fecha_programacion = datetime.now(tz_gdl).strftime("%d/%m/%Y %H:%M")
    
    for _, row in df_datos.iterrows():
        fletera = str(row.get('RECOMENDACION', 'N/A'))
        factura = str(row.get('Factura', 'S/N'))
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x_pos, y_pos, f"{fletera}")
        
        texto_qr = f"FLETERA: {fletera} | FACTURA: {factura} | PROG: {fecha_programacion}"
        qr_io = crear_imagen_qr(texto_qr)
        c.drawImage(ImageReader(qr_io), x_pos + 130, y_pos - 37, width=55, height=55)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def marcar_pdf_digital(pdf_file, fletera_val, factura_val, x_pos, y_pos):
    reader = PdfReader(pdf_file)
    writer = PdfWriter()
    tz_gdl = pytz.timezone("America/Mexico_City")
    fecha_programacion = datetime.now(tz_gdl).strftime("%d/%m/%Y %H:%M")
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter) 
    can.setFont("Helvetica-Bold", 12)
    can.drawString(x_pos, y_pos, f"{fletera_val}")
    
    texto_qr = f"FLETERA: {fletera_val} | FACTURA: {factura_val} | PROG: {fecha_programacion}"
    qr_io = crear_imagen_qr(texto_qr)
    can.drawImage(ImageReader(qr_io), x_pos + 130, y_pos - 14, width=35, height=35)
    can.save()
    packet.seek(0)
    
    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]
    for page in reader.pages:
        page.merge_page(overlay_page)
        writer.add_page(page)
        
    output_pdf = io.BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf.getvalue()


# Inicialización segura de estados de menú
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "CENTRO DE DATOS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "FACTURACIÓN"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1


# ==========================================
# 4. HEADER Y NAVEGACIÓN
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
        if st.session_state.menu_sub != "GENERAL":
            ruta = f"{texto_principal} <span style='color: {azul_nexion}; opacity: 0.8; margin: 0 15px;'>/</span> <span style='color: {oro_brillante}; font-weight: 500;'>{st.session_state.menu_sub}</span>"
        else:
            ruta = texto_principal

        st.markdown(f"<div style='display: flex; justify-content: center;'><p style='font-size: 13px; letter-spacing: 5px; color: {vars_css['sub']}; margin: 0; font-weight: 500; text-transform: uppercase;'>{ruta}</p></div>", unsafe_allow_html=True)

    with c3:
        query = st.text_input("Buscar", placeholder="🔍 Buscar...", label_visibility="collapsed", key=f"main_search_v{st.session_state.search_key_version}")

    with c4:
        with st.popover("☰ Menú", use_container_width=True):
            if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.autenticado = False
                st.rerun()

# ==========================================
# 5. INTERFAZ PRINCIPAL
# ==========================================
def main():
    usuario_actual = st.session_state.get("usuario_activo", "").upper()
    es_rigoberto = (usuario_actual == "RIGOBERTO")

    st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'></p>", unsafe_allow_html=True)

    if es_rigoberto:
        modo_operacion = st.radio("SELECCIONAR MODO DE TRABAJO:", ["FLUJO DE CYNTHIA (CARGA Y FILTRADO)", "MOTOR DE ASIGNACIÓN Y SELLADO (RIGOBERTO)"], horizontal=True)
    else:
        modo_operacion = "FLUJO DE CYNTHIA (CARGA Y FILTRADO)"

    if "FLUJO DE CYNTHIA" in modo_operacion:
        st.markdown("<p style='font-size: 12px; font-weight: 600;'></p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Subir archivo ERP completo en Excel o CSV", type=["xlsx", "csv"], key="erp_file_uploader_cynthia")

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file, sep=None, engine="python") if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                df.columns = [str(c).strip().replace("\n", "") for c in df.columns]
                col_folio = next((c for c in df.columns if "factura" in c.lower() or "docnum" in c.lower() or "folio" in c.lower()), df.columns[0])
                df[col_folio] = pd.to_numeric(df[col_folio], errors="coerce")

                col_left, col_right = st.columns([1, 2], gap="large")

                with col_left:
                    st.markdown("<p><b>PASO 1: SELECCIÓN Y GUARDADO EN FACTURACION.CSV</b></p>", unsafe_allow_html=True)
                    folios_manuales = st.text_input("Folios específicos (separados por coma):", placeholder="Ej: 1001, 1002, 1005")
                    serie = df[col_folio].dropna()
                    inicio = st.number_input("Desde:", value=int(serie.min()) if not serie.empty else 0)
                    final = st.number_input("Hasta:", value=int(serie.max()) if not serie.empty else 0)

                    if folios_manuales:
                        lista_manual = [int(x.strip()) for x in folios_manuales.split(",") if x.strip().isdigit()]
                        df_rango = df[df[col_folio].isin(lista_manual)].copy()
                    else:
                        df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)].copy()

                    st.markdown("---")
                    if st.button("GUARDAR EN FACTURACION.CSV (SIN DUPLICADOS)", type="primary", use_container_width=True):
                        if df_rango.empty:
                            st.error("El rango está vacío.")
                        else:
                            df_a_guardar = df_rango.rename(columns={col_folio: "Factura"})
                            exito = guardar_facturacion_github(df_a_guardar)
                            if exito:
                                st.success("¡Rango procesado! Se omitieron facturas repetidas y se guardó en `facturacion.csv` con éxito.")

                with col_right:
                    st.markdown("<p><b>PASO 2: SELECCIÓN DE FACTURAS (UNA PARTIDA POR FACTURA)</b></p>", unsafe_allow_html=True)
                    if not df_rango.empty:
                        df_unico_factura = df_rango.drop_duplicates(subset=[col_folio]).copy()
                        df_unico_factura.insert(0, "Incluir_Factura", True)
                        
                        edited_df = st.data_editor(df_unico_factura, hide_index=True, use_container_width=True, key="ed_v_cynthia")
                    else:
                        st.warning("Rango vacío")
                        edited_df = pd.DataFrame()

                if not df_rango.empty and not edited_df.empty:
                    df_filtrado_final = edited_df[edited_df["Incluir_Factura"] == True].drop(columns=["Incluir_Factura"])

                    st.markdown("---")
                    st.markdown("<p style='font-size: 14px; font-weight: 700;'>Guardar Archivo Personalizado en GitHub para Rigoberto</p>", unsafe_allow_html=True)
                    nombre_archivo_custom = st.text_input("Nombre del archivo (ej. lote_matutino.csv):", value="lote_rigoberto.csv")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("SUBIR A GITHUB", type="primary", use_container_width=True):
                            if not nombre_archivo_custom.strip():
                                st.error("Ingresa un nombre de archivo válido.")
                            else:
                                ok_gh = guardar_archivo_rigoberto_github(df_filtrado_final, nombre_archivo_custom.strip())
                                if ok_gh:
                                    st.success(f"¡Archivo '{nombre_archivo_custom.strip()}' guardado con éxito en GitHub!")
                                else:
                                    st.error("Error al guardar en GitHub.")
                    with col_btn2:
                        towrite = io.BytesIO()
                        df_filtrado_final.to_excel(towrite, index=False, engine="openpyxl")
                        st.download_button(
                            label="📥 DESCARGAR LOCAL",
                            data=towrite.getvalue(),
                            file_name=nombre_archivo_custom.strip().replace(".csv", ".xlsx"),
                            use_container_width=True
                        )

            except Exception as e:
                st.error(f"Error procesando el archivo ERP: {e}")

    else:
        st.markdown("")
        
        archivos_disponibles = listar_archivos_rigoberto_github()
        
        if archivos_disponibles:
            archivo_elegido = st.selectbox("Seleccionar archivo preparado por Cynthia desde GitHub:", archivos_disponibles)
            if archivo_elegido:
                df_trabajo = cargar_archivo_rigoberto_github(archivo_elegido)
        else:
            st.info("No hay archivos en la carpeta de GitHub de Cynthia. Puedes subir uno localmente si lo prefieres:")
            uploaded_rigoberto = st.file_uploader("Subir archivo preparado", type=["xlsx", "csv"], key="uploader_rigoberto")
            if uploaded_rigoberto is not None:
                df_trabajo = pd.read_csv(uploaded_rigoberto, sep=None, engine="python") if uploaded_rigoberto.name.endswith(".csv") else pd.read_excel(uploaded_rigoberto)
            else:
                df_trabajo = pd.DataFrame()

        if not df_trabajo.empty:
            df_trabajo.columns = [str(c).strip().replace("\n", "") for c in df_trabajo.columns]
            if "Factura" not in df_trabajo.columns:
                col_f = next((c for c in df_trabajo.columns if "factura" in c.lower() or "docnum" in c.lower() or "folio" in c.lower()), df_trabajo.columns[0])
                df_trabajo = df_trabajo.rename(columns={col_f: "Factura"})

            st.dataframe(df_trabajo, use_container_width=True)

            if st.button("EJECUTAR SMART ROUTING (MOTOR DE ASIGNACIÓN)", type="primary", use_container_width=True):
                try:
                    matriz_db = obtener_matriz_github()
                    col_dir_erp = next((c for c in df_trabajo.columns if "DIRECCION" in c.upper()), None)
                    col_dest_matriz = "DESTINO" if "DESTINO" in matriz_db.columns else matriz_db.columns[0]
                    col_flet_matriz = "TRANSPORTE" if "TRANSPORTE" in matriz_db.columns else "FLETERA"
                    col_tarifa_matriz = "PRECIO POR CAJA" if "PRECIO POR CAJA" in matriz_db.columns else "COSTO"

                    def motor_v4(row):
                        if not col_dir_erp:
                            return "ERROR: COL DIRECCION", 0.0
                        dir_limpia = limpiar_texto(row[col_dir_erp])
                        if any(loc in dir_limpia for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA", "TLAJOMULCO"]):
                            return "LOCAL", 0.0
                        for _, fila in matriz_db.iterrows():
                            dest_key = limpiar_texto(fila[col_dest_matriz])
                            if dest_key and (dest_key in dir_limpia):
                                return fila.get(col_flet_matriz, "ASIGNADO"), pd.to_numeric(fila.get(col_tarifa_matriz, 0.0), errors="coerce")
                        return "REVISIÓN MANUAL", 0.0

                    res = df_trabajo.apply(motor_v4, axis=1)
                    df_trabajo["RECOMENDACION"] = [r[0] for r in res]
                    df_trabajo["COSTO"] = [r[1] for r in res]
                    df_trabajo["FECHA DE PROGRAMACION"] = calcular_fecha_programacion()

                    cols_deseadas = ["Factura", "FECHA DE PROGRAMACION", "RECOMENDACION", "Transporte", "DIRECCION", "COSTO", "Nombre_Cliente", "DESTINO"]
                    cols_finales = [c for c in cols_deseadas if c in df_trabajo.columns]

                    st.session_state.df_analisis = df_trabajo[cols_finales]
                    st.success("¡Motor sincronizado con éxito!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error en el motor de asignación: {e}")

        if "df_analisis" in st.session_state:
            st.markdown("---")
            p = st.session_state.df_analisis.copy()
            modo_edicion = st.toggle("HABILITAR EDICIÓN MANUAL")
            
            p_editado = st.data_editor(p, use_container_width=True, hide_index=True, key="editor_final_github")
            
            if st.button("FIJAR CAMBIOS Y ACUMULAR EN ENVIOS", use_container_width=True, type="primary"):
                actualizar_historial_envios_github(p_editado)
                st.toast("¡Sincronizado en envios.csv!", icon="✅")

            st.write("")
            output_xlsx = io.BytesIO()
            p_editado.to_excel(output_xlsx, index=False, engine='openpyxl')
            st.download_button(
                label="DESCARGAR ANÁLISIS FINAL", 
                data=output_xlsx.getvalue(), 
                file_name="Analisis_Final.xlsx", 
                use_container_width=True,
                type="primary" 
            )

            with st.expander("SISTEMA DE SELLADO", expanded=False):
                cx, cy = st.columns(2)
                ax = cx.slider("X", 0, 612, 399)
                ay = cy.slider("Y", 0, 792, 760)
                
                s1, s2 = st.columns(2)
                with s1:
                    st.download_button("GENERAR SELLOS NORMAL", data=generar_sellos_fisicos(p_editado, ax, ay), file_name="Sellos_Normales.pdf", use_container_width=True, type="primary")
                with s2:
                    p_invertido = p_editado.iloc[::-1].reset_index(drop=True)
                    st.download_button("GENERAR SELLOS MODO INVERSO", data=generar_sellos_fisicos(p_invertido, ax, ay), file_name="Sellos_Inversos.pdf", use_container_width=True, type="primary")


if __name__ == "__main__":
    main()

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
