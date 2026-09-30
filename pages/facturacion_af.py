import base64
from datetime import datetime, timedelta
import io
import re
import time
import unicodedata
import zipfile
import requests
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit as st
import pytz
from reportlab.lib import colors
from auth import exigir_autenticacion
from components.layout import render_layout

exigir_autenticacion("facturacion")

# ==========================================
# LAYOUT MAESTRO (reemplaza CSS + seguridad + header + menú + footer duplicados)
# ==========================================
render_layout("CENTRO DE DATOS", "ASIGNAR FLETERA")

# Paleta mínima que todavía usa esta página (la del layout es la misma)
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
}

GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"


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
    
    # 🔹 FIX: se agregó 'Quantity' para que viaje desde el lote de Cynthia
    # hasta el análisis final de Rigoberto (antes se perdía aquí).
    cols_a_guardar = []
    for c_buscada in ['Factura', 'Fecha_Conta', 'Nombre_Cliente', 'Nombre_Extran', 'Transporte', 'DESTINO', 'DIRECCION', 'Quantity']:
        match_col = next((c for c in df_datos.columns if c.strip().lower() == c_buscada.lower()), None)
        if match_col:
            cols_a_guardar.append(match_col)
    
    df_filtrado_lote = df_datos[cols_a_guardar].copy() if cols_a_guardar else df_datos.copy()

    csv_buffer = io.StringIO()
    df_filtrado_lote.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    content_base64 = base64.b64encode(csv_buffer.getvalue().encode("utf-8")).decode("utf-8")
    
    data = {
        "message": f"Subida de archivo personalizado para Rigoberto con Dirección: {nombre_archivo}",
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


def generar_sellos_emergencia(df_datos, x_pos, y_pos):
    """
    Tacha con línea horizontal el texto viejo y con una cruz (X) el QR viejo,
    dejando el nuevo sello correcto limpio más hacia el centro/izquierda.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(612, 792)) 
    tz_gdl = pytz.timezone("America/Mexico_City")
    fecha_programacion = datetime.now(tz_gdl).strftime("%d/%m/%Y %H:%M")
    
    for _, row in df_datos.iterrows():
        fletera = str(row.get('RECOMENDACION', 'N/A'))
        factura = str(row.get('Factura', 'S/N'))
        
        # --- 1. TACHADO DE EMERGENCIA SOBRE EL SELLO VIEJO ---
        c.saveState()
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.2)
        
        # Línea horizontal tachando el texto del transporte viejo
        c.line(x_pos - 5, y_pos + 1, x_pos + 110, y_pos + 2)
        
        # Cruz / X tachando la zona del QR viejo (aproximadamente de 55x55 píxeles)
        qr_x_inicio = x_pos + 130
        qr_y_inicio = y_pos - 37
        qr_ancho = 55
        qr_alto = 55
        
        # Diagonal 1 del QR
        c.line(qr_x_inicio, qr_y_inicio, qr_x_inicio + qr_ancho, qr_y_inicio + qr_alto)
        # Diagonal 2 del QR (forma la X perfecta de anulación)
        c.line(qr_x_inicio, qr_y_inicio + qr_alto, qr_x_inicio + qr_ancho, qr_y_inicio)
        
        c.restoreState()
        
        # --- 2. NUEVO SELLO CORRECTO MÁS HACIA EL CENTRO ---
        x_nuevo = x_pos - 210
        if x_nuevo < 40:
            x_nuevo = 40  # Margen mínimo de seguridad
            
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawString(x_nuevo, y_pos, f"{fletera}")
        
        texto_qr_nuevo = f"FLETERA: {fletera} | FACTURA: {factura} | PROG: {fecha_programacion}"
        qr_nuevo_io = crear_imagen_qr(texto_qr_nuevo)
        c.drawImage(ImageReader(qr_nuevo_io), x_nuevo + 130, y_pos - 37, width=55, height=55)
        
        c.showPage()
        
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def _acortar_texto_celda(valor, limite=38):
    """Recorta el texto de una celda para que nunca truene línea (mantiene filas bajitas)."""
    texto = "" if valor is None else str(valor)
    texto = texto.replace("\n", " ").replace("\r", " ").strip()
    if len(texto) > limite:
        return texto[: limite - 1].rstrip() + "…"
    return texto


def generar_reporte_pdf_analisis(df_datos, titulo_reporte="REPORTE DE ANÁLISIS DE ASIGNACIÓN"):
    """
    Genera un PDF profesional del Análisis Final, con el MISMO layout de membrete
    que el resto de los formatos del sistema (ej. Orden de Embarque):
    - Izquierda: "Jabones y Productos Especializados" + "DISTRIBUCIÓN Y LOGÍSTICA | 2026"
    - Derecha: título del reporte (subrayado) + fecha/hora de impresión, hora Guadalajara
    - Página en HORIZONTAL (landscape)
    - Celdas de una sola línea (sin saltos de línea) para filas bajitas
    - Fila de encabezado "sticky": se repite en cada página
    """
    buffer = io.BytesIO()
    tz_gdl = pytz.timezone("America/Mexico_City")
    ahora_gdl = datetime.now(tz_gdl)
    fecha_str = ahora_gdl.strftime("%d/%m/%Y")
    hora_str = ahora_gdl.strftime("%H:%M:%S")

    pagesize_h = landscape(letter)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize_h,
        topMargin=1.2 * cm,
        bottomMargin=1.1 * cm,
        leftMargin=1 * cm,
        rightMargin=1 * cm,
    )

    estilo_membrete_izq = ParagraphStyle(
        "MembreteIzq", fontName="Helvetica-Bold", fontSize=14,
        textColor=colors.HexColor("#1B2A2F"), alignment=TA_LEFT, leading=17,
    )
    estilo_membrete_der = ParagraphStyle(
        "MembreteDer", fontName="Helvetica-Bold", fontSize=11,
        textColor=colors.HexColor("#1B2A2F"), alignment=TA_RIGHT, leading=14,
    )

    texto_izq = (
        "<b>Jabones y Productos Especializados</b><br/>"
        "<font color='#00A3A3' size=8><b>DISTRIBUCIÓN Y LOGÍSTICA | 2026</b></font>"
    )
    texto_der = (
        f"<u><b>{titulo_reporte}</b></u><br/>"
        f"<font size=8 color='#555555'>Impreso: {fecha_str} &nbsp;|&nbsp; {hora_str} hrs (Hora Guadalajara)</font>"
    )

    tabla_membrete = Table(
        [[Paragraph(texto_izq, estilo_membrete_izq), Paragraph(texto_der, estilo_membrete_der)]],
        colWidths=[doc.width * 0.6, doc.width * 0.4],
    )
    tabla_membrete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#1B2A2F")),
    ]))

    elementos = [tabla_membrete, Spacer(1, 8)]

    if not df_datos.empty:
        columnas = [str(c) for c in df_datos.columns]
        df_texto = df_datos.astype(str)
        fuente_header, tam_header = "Helvetica-Bold", 7
        fuente_dato, tam_dato = "Helvetica", 6.8
        relleno_pt = 10  # padding izq+der por celda
        ancho_min_pt, ancho_max_pt = 34, 150

        limite_trunc = 42  # tope inicial de caracteres por celda (una sola línea, sin salto)

        def _calcular_anchos(limite):
            fila_hdr = [c.upper() for c in columnas]
            filas_datos_trunc = [
                [_acortar_texto_celda(v, limite) for v in fila] for fila in df_texto.values.tolist()
            ]
            anchos = []
            for i, encabezado in enumerate(fila_hdr):
                ancho_hdr = stringWidth(encabezado, fuente_header, tam_header)
                ancho_dato = max(
                    [stringWidth(f[i], fuente_dato, tam_dato) for f in filas_datos_trunc] or [0]
                )
                ancho = max(ancho_hdr, ancho_dato) + relleno_pt
                anchos.append(min(max(ancho, ancho_min_pt), ancho_max_pt))
            return fila_hdr, filas_datos_trunc, anchos

        fila_hdr, filas_datos_trunc, anchos_col = _calcular_anchos(limite_trunc)
        intentos = 0
        while sum(anchos_col) > doc.width and limite_trunc > 12 and intentos < 6:
            limite_trunc -= 6
            fila_hdr, filas_datos_trunc, anchos_col = _calcular_anchos(limite_trunc)
            intentos += 1

        total_anchos = sum(anchos_col) or 1
        if total_anchos <= doc.width:
            # Rellena el ancho completo de la página horizontal repartiendo el sobrante
            factor = doc.width / total_anchos
            anchos_col = [a * factor for a in anchos_col]
        else:
            # Último recurso: comprimir proporcionalmente para que quepa en la página
            factor = doc.width / total_anchos
            anchos_col = [a * factor for a in anchos_col]

        data_tabla = [fila_hdr] + filas_datos_trunc

        tabla = Table(data_tabla, colWidths=anchos_col, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B343B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("FONTSIZE", (0, 1), (-1, -1), 6.8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#4B5D67")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAEEF0")]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        elementos.append(tabla)
    else:
        elementos.append(Paragraph("Sin datos para mostrar.", getSampleStyleSheet()["Normal"]))

    def _pie_pagina(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(1 * cm, 0.55 * cm, f"Generado {fecha_str} {hora_str} hrs (Hora Guadalajara) · NEXION")
        canvas_obj.drawRightString(pagesize_h[0] - 1 * cm, 0.55 * cm, f"Página {doc_obj.page}")
        canvas_obj.restoreState()

    doc.build(elementos, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
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



# ==========================================
# 5. INTERFAZ PRINCIPAL
# ==========================================
def main():
    usuario_actual = st.session_state.get("usuario_activo", "").upper()
    es_rigoberto = (usuario_actual == "RIGOBERTO")

    st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'></p>", unsafe_allow_html=True)

    if es_rigoberto:
        modo_operacion = st.radio("SELECCIONAR MODO DE TRABAJO:", ["FLUJO DE CYNTHIA (CARGA Y FILTRADO)", "MOTOR DE ASIGNACIÓN Y SELLADO (LOGISTICA)"], horizontal=True)
    else:
        modo_operacion = "FLUJO DE AAC / FACTURACION (CARGA Y FILTRADO)"

    if "FLUJO DE CYNTHIA" in modo_operacion:
        st.markdown("<p style='font-size: 12px; font-weight: 600;'></p>", unsafe_allow_html=True)

        # 🔹 BADGE: ÚLTIMO FOLIO CARGADO (SOLO VISIBLE EN LA SECCIÓN DE CYNTHIA)
        try:
            df_fact_badge = cargar_facturacion_github()
            col_folio_badge = next(
                (c for c in df_fact_badge.columns if "factura" in c.lower() or "folio" in c.lower() or "docnum" in c.lower()),
                None,
            )
            if col_folio_badge is not None and not df_fact_badge.empty:
                ultimo_folio_num = pd.to_numeric(df_fact_badge[col_folio_badge], errors="coerce").dropna().max()
                ultimo_folio_txt = str(int(ultimo_folio_num)) if pd.notna(ultimo_folio_num) else "N/A"
            else:
                ultimo_folio_txt = "N/A"
        except Exception:
            ultimo_folio_txt = "N/A"

        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:flex-end; gap:8px; background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-radius: 8px; padding: 10px 18px; margin-bottom: 16px; width:100%; box-sizing:border-box;">
                <div style="width:8px; height:8px; background:#00FFAA; border-radius:50%; box-shadow:0 0 8px #00FFAA; flex-shrink:0;"></div>
                <span style="color:#82D4E6; font-size:10px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase;">ÚLTIMO FOLIO CARGADO:</span>
                <span style="color:white; font-size:13px; font-weight:800; font-family:monospace; letter-spacing:0.5px;">{ultimo_folio_txt}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # 🔹 SECCIÓN DE DESCARGA LIBRE DE LOTES EXISTENTES (SOLO PARA CYNTHIA)
        archivos_disponibles_cynthia = listar_archivos_rigoberto_github()
        if archivos_disponibles_cynthia:
            st.markdown("<p style='font-size: 11px; font-weight: 700; color: #82D4E6; letter-spacing: 1px;'>📥 DESCARGAR LOTES GUARDADOS</p>", unsafe_allow_html=True)
            col_sel_cyn, col_btn_cyn = st.columns([3, 1], vertical_alignment="bottom")
            with col_sel_cyn:
                lote_elegido_cyn = st.selectbox("Selecciona un lote existente:", archivos_disponibles_cynthia, key="select_descarga_lote_cynthia_libre")
            with col_btn_cyn:
                if lote_elegido_cyn:
                    df_lote_cyn = cargar_archivo_rigoberto_github(lote_elegido_cyn)
                    if not df_lote_cyn.empty:
                        out_bytes_cyn = io.BytesIO()
                        df_lote_cyn.to_excel(out_bytes_cyn, index=False, engine="openpyxl")
                        out_bytes_cyn.seek(0)
                        st.download_button(
                            label="BAJAR LOTE",
                            data=out_bytes_cyn.getvalue(),
                            file_name=lote_elegido_cyn.replace(".csv", ".xlsx"),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="btn_bajar_lote_cynthia_val"
                        )
            st.markdown("---")

        uploaded_file = st.file_uploader("Subir archivo ERP completo en Excel o CSV", type=["xlsx", "csv"], key="erp_file_uploader_cynthia")

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file, sep=None, engine="python") if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                df.columns = [str(c).strip().replace("\n", "") for c in df.columns]
                col_folio = next((c for c in df.columns if "factura" in c.lower() or "docnum" in c.lower() or "folio" in c.lower()), df.columns[0])
                df[col_folio] = pd.to_numeric(df[col_folio], errors="coerce")

                # PASO 1: SELECCIÓN Y GUARDADO EN FACTURACION.CSV (COMPLETO)
                st.markdown("<p><b>PASO 1: SELECCIÓN Y GUARDADO EN FACTURACION.CSV</b></p>", unsafe_allow_html=True)
                
                col_i1, col_i2, col_i3 = st.columns(3, gap="medium")
                with col_i1:
                    folios_manuales = st.text_input("Folios específicos (separados por coma):", placeholder="Ej: 1001, 1002, 1005")
                with col_i2:
                    serie = df[col_folio].dropna()
                    inicio = st.number_input("Desde:", value=int(serie.min()) if not serie.empty else 0)
                with col_i3:
                    final = st.number_input("Hasta:", value=int(serie.max()) if not serie.empty else 0)

                if folios_manuales:
                    lista_manual = [int(x.strip()) for x in folios_manuales.split(",") if x.strip().isdigit()]
                    df_rango = df[df[col_folio].isin(lista_manual)].copy()
                else:
                    df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)].copy()

                st.markdown("")

                if st.button("GUARDAR EN FACTURACION.CSV (SIN DUPLICADOS)", type="primary", use_container_width=True):
                    if df_rango.empty:
                        st.error("El rango está vacío.")
                    else:
                        df_a_guardar = df_rango.rename(columns={col_folio: "Factura"})
                        exito = guardar_facturacion_github(df_a_guardar)
                        if exito:
                            st.success("¡Rango procesado! Se omitieron facturas repetidas y se guardó en `facturacion.csv` con éxito.")

                st.markdown("---")

                # PASO 2: SELECCIÓN Y FILTRADO
                st.markdown("<p><b>PASO 2: SELECCIÓN DE FACTURAS (UNA PARTIDA POR FACTURA)</b></p>", unsafe_allow_html=True)
                if not df_rango.empty:
                    df_unico_factura = df_rango.drop_duplicates(subset=[col_folio]).copy()
                    df_unico_factura = df_unico_factura.rename(columns={col_folio: "Factura"})
                    
                    # 🔹 FIX: se agregó 'Quantity' a las columnas que Cynthia filtra y guarda,
                    # para que llegue completa hasta el análisis final de Rigoberto.
                    cols_deseadas_cynthia = ["Factura", "Fecha_Conta", "Nombre_Cliente", "Nombre_Extran", "Transporte", "Quantity", "DESTINO", "DIRECCION"]
                    cols_existentes_cynthia = []
                    for c_buscada in cols_deseadas_cynthia:
                        match_c = next((c for c in df_unico_factura.columns if c.strip().lower() == c_buscada.lower()), None)
                        if match_c:
                            cols_existentes_cynthia.append(match_c)
                        else:
                            df_unico_factura[c_buscada] = ""
                            cols_existentes_cynthia.append(c_buscada)

                    df_filtrado_columnas = df_unico_factura[cols_existentes_cynthia].copy()
                    df_filtrado_columnas.insert(0, "Incluir_Factura", True)
                    
                    edited_df = st.data_editor(df_filtrado_columnas, hide_index=True, use_container_width=True, key="ed_v_cynthia")
                else:
                    st.warning("Rango vacío")
                    edited_df = pd.DataFrame()

                if not df_rango.empty and not edited_df.empty:
                    df_filtrado_final = edited_df[edited_df["Incluir_Factura"] == True].drop(columns=["Incluir_Factura"])

                    st.markdown("---")
                    st.markdown("<p style='font-size: 16px; font-weight: 400;'>GUARDAR ARCHIVO EN LA NUBE PARA LOGISTICA</p>", unsafe_allow_html=True)
                    
                    # 🔹 NOMBRE AUTOMÁTICO BASADO EN FECHA Y HORA (INVIOLABLE / NUNCA SE REPITE)
                    tz_gdl = pytz.timezone("America/Mexico_City")
                    timestamp_lote = datetime.now(tz_gdl).strftime("%Y%m%d_%H%M%S")
                    nombre_archivo_auto = f"lote_{timestamp_lote}.csv"
                    
                    st.info(f"📁 Nombre de lote generado automáticamente: **{nombre_archivo_auto}**")

                    col_btn1, col_btn2, col_btn3 = st.columns(3, gap="medium")
                    with col_btn1:
                        if st.button("SUBIR A GITHUB", type="primary", use_container_width=True):
                            ok_gh = guardar_archivo_rigoberto_github(df_filtrado_final, nombre_archivo_auto)
                            if ok_gh:
                                st.success(f"¡Lote '{nombre_archivo_auto}' guardado con éxito en en la nube!")
                            else:
                                st.error("Error al guardar en GitHub.")
                    with col_btn2:
                        df_local_sin_dir = df_filtrado_final.copy()
                        cols_a_quitar = [c for c in df_local_sin_dir.columns if c.strip().upper() == "DIRECCION"]
                        if cols_a_quitar:
                            df_local_sin_dir = df_local_sin_dir.drop(columns=cols_a_quitar)

                        towrite = io.BytesIO()
                        df_local_sin_dir.to_excel(towrite, index=False, engine="openpyxl")
                        towrite.seek(0)
                        
                        nombre_limpio_xlsx = nombre_archivo_auto.replace(".csv", ".xlsx")

                        st.download_button(
                            label="📥 DESCARGAR EN EXCEL",
                            data=towrite.getvalue(),
                            file_name=nombre_limpio_xlsx,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                    with col_btn3:
                        # Mismo generador/estilo que el PDF del Análisis de Logística
                        # (membrete, horizontal, encabezado repetido, pie con página).
                        # Se omite DIRECCION igual que en el Excel descargable.
                        st.download_button(
                            label="🧾 GENERAR REPORTE PDF",
                            data=generar_reporte_pdf_analisis(
                                df_local_sin_dir,
                                titulo_reporte="REPORTE DE FACTURAS FILTRADAS",
                            ),
                            file_name=nombre_limpio_xlsx.replace(".xlsx", ".pdf"),
                            mime="application/pdf",
                            use_container_width=True,
                            key="btn_pdf_paso2_cynthia",
                        )

            except Exception as e:
                st.error(f"Error procesando el archivo ERP: {e}")

    else:
        st.markdown("")
        
        # 🔹 NOTA: Se eliminó completamente la sección de descarga libre de lotes en la pestaña de Rigoberto
        archivos_disponibles = listar_archivos_rigoberto_github()
        df_trabajo = pd.DataFrame()

        if archivos_disponibles:
            archivo_elegido = st.selectbox("Seleccionar archivo preparado por AAA / FACTURACIÓN:", archivos_disponibles, key="select_trabajo_activo_rigoberto")
            if archivo_elegido:
                df_trabajo = cargar_archivo_rigoberto_github(archivo_elegido)
        else:
            st.info("No hay archivos en la carpeta de Cynthia. Puedes subir uno localmente si lo prefieres:")
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

                    cols_deseadas = ["Factura", "FECHA DE PROGRAMACION", "RECOMENDACION", "Transporte", "DIRECCION", "COSTO", "Nombre_Extran", "Quantity", "DESTINO"]
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
            
            col_b1, col_b2, col_b3 = st.columns(3, gap="small")

            with col_b1:
                if st.button("FIJAR CAMBIOS Y ACUMULAR EN ENVIOS", use_container_width=True, type="primary"):
                    actualizar_historial_envios_github(p_editado)
                    st.toast("¡Sincronizado en envios.csv!", icon="✅")

            output_xlsx = io.BytesIO()
            p_editado.to_excel(output_xlsx, index=False, engine='openpyxl')
            with col_b2:
                st.download_button(
                    label="DESCARGAR ANÁLISIS FINAL", 
                    data=output_xlsx.getvalue(), 
                    file_name="Analisis_Final.xlsx", 
                    use_container_width=True,
                    type="primary" 
                )

            tz_gdl_pdf = pytz.timezone("America/Mexico_City")
            nombre_pdf_analisis = f"Reporte_Analisis_{datetime.now(tz_gdl_pdf).strftime('%Y%m%d_%H%M%S')}.pdf"
            df_pdf_analisis = p_editado.drop(columns=[c for c in p_editado.columns if c.strip().upper() == "COSTO"])
            with col_b3:
                st.download_button(
                    label="🧾 GENERAR REPORTE PDF",
                    data=generar_reporte_pdf_analisis(df_pdf_analisis, titulo_reporte="REPORTE DE ANÁLISIS DE ASIGNACIÓN LOGÍSTICA"),
                    file_name=nombre_pdf_analisis,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )

            with st.expander("SISTEMA DE SELLADO", expanded=False):
                cx, cy = st.columns(2)
                ax = cx.slider("X", 0, 612, 399)
                ay = cy.slider("Y", 0, 792, 760)
                
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.download_button("SELLOS NORMAL", data=generar_sellos_fisicos(p_editado, ax, ay), file_name="Sellos_Normales.pdf", use_container_width=True, type="primary")
                with s2:
                    p_invertido = p_editado.iloc[::-1].reset_index(drop=True)
                    st.download_button("SELLOS INVERSOS", data=generar_sellos_fisicos(p_invertido, ax, ay), file_name="Sellos_Inversos.pdf", use_container_width=True, type="primary")
                with s3:
                    st.download_button("🚨 EMERGENCIA (TACHADO + RE-SELLO)", data=generar_sellos_emergencia(p_editado, ax, ay), file_name="Sellos_Emergencia.pdf", use_container_width=True)




if __name__ == "__main__":
    main()
