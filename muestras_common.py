"""
============================================================
 MODULO COMPARTIDO - MUESTRAS
============================================================
Contiene todo lo que usan en comun:
  - muestras.py            (captura de agentes)
  - costos_muestras.py     (reportes / gestion / edicion admin)

No es una pagina de Streamlit por si sola (no lleva
st.set_page_config ni render_layout). Solo se importa.
============================================================
"""

import base64
import io
import re
import time
import unicodedata

import pandas as pd
import requests
import streamlit as st
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
import reportlab.lib.units as units

# ============================================================
# 1. CONFIGURACIÓN DE CONEXIÓN A GITHUB
# ============================================================
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_PATH = "muestras.csv"


def _github_token():
    return st.secrets["GITHUB_TOKEN"]


# ============================================================
# 2. CATÁLOGO DE PRODUCTOS Y PRECIOS
# ============================================================
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
    "68829526 Rack Dove Dove Mlac Bracket Metalized Bottle 1 Pieza": 193.90,
}


# ============================================================
# 3. FUNCIONES DE DATOS (GITHUB)
# ============================================================
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
    except Exception:
        return None


def obtener_datos_github():
    """Descarga el CSV de muestras.csv desde GitHub (sin caché, fuente viva)."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {_github_token()}"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = r.json()
            df = pd.read_csv(io.BytesIO(base64.b64decode(content["content"])))
            return df, content["sha"]
    except Exception:
        pass
    return pd.DataFrame(), None


def subir_a_github(df, sha, msg):
    """Sube el DataFrame actualizado de muestras.csv a GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {"Authorization": f"token {_github_token()}"}
    csv_string = df.to_csv(index=False)
    payload = {
        "message": msg,
        "content": base64.b64encode(csv_string.encode()).decode(),
        "sha": sha,
    }
    return requests.put(url, json=payload, headers=headers).status_code == 200


# ============================================================
# 4. UTILIDADES DE TEXTO
# ============================================================
def limpiar_parentesis(texto):
    return re.sub(r"\(.*?\)", "", str(texto)).strip()


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


# ============================================================
# 5. ETIQUETAS PDF (10.40cm x 8.08cm)
# ============================================================
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
    w_rec, h_rec = 10.40 * units.cm, 8.08 * units.cm
    c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
    x_offset, y_offset = 0.0 * units.cm, 0.0 * units.cm

    nombre_crudo = reg_datos.get("NOMBRE DEL HOTEL", "SIN NOMBRE")
    nombre_final = limpiar_parentesis(nombre_crudo)
    direccion_final = reg_datos.get("DESTINO", "DIRECCIÓN NO DISPONIBLE")
    transporte_final = str(transporte_val if transporte_val else "TRES GUERRAS")

    for i in range(total_etqs):
        c.setDash(1, 2)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.rect(x_offset, y_offset, w_rec, h_rec)
        c.setDash([])
        c.setStrokeColorRGB(0, 0, 0)

        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x_offset + (w_rec / 2), y_offset + h_rec - 0.3 * units.cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
        c.setFont("Helvetica", 6)
        info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
        dibujar_texto_bloque_pro(c, info_contacto, x_offset + (w_rec / 2), y_offset + h_rec - 0.7 * units.cm, 10 * units.cm, "Helvetica", 6, 0.25 * units.cm, max_lineas=1)

        c.setLineWidth(0.3)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.line(x_offset + 0.5 * units.cm, y_offset + h_rec - 1.0 * units.cm, x_offset + w_rec - 0.5 * units.cm, y_offset + h_rec - 1.0 * units.cm)
        c.setStrokeColorRGB(0, 0, 0)

        y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_offset + (w_rec / 2), y_offset + h_rec - 2.0 * units.cm, 10 * units.cm, "Helvetica-Bold", 26, 0.75 * units.cm, max_lineas=3)

        y_inicio_direccion = y_termino_nombre - 0.7 * units.cm
        if y_inicio_direccion > y_offset + 4.3 * units.cm:
            y_inicio_direccion = y_offset + 4.3 * units.cm
        if y_inicio_direccion < y_offset + 2.9 * units.cm:
            y_inicio_direccion = y_offset + 2.9 * units.cm
        dibujar_texto_bloque_pro(c, direccion_final, x_offset + (w_rec / 2), y_inicio_direccion, 10.0 * units.cm, "Helvetica-Bold", 14.5, 0.5 * units.cm, max_lineas=3)

        c.setLineWidth(0.6)
        y_linea_pie = y_offset + 1.4 * units.cm
        c.line(x_offset + 0.2 * units.cm, y_linea_pie, x_offset + w_rec - 0.2 * units.cm, y_linea_pie)

        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x_offset + 0.5 * units.cm, y_linea_pie - 0.4 * units.cm, "FACTURA")
        c.drawCentredString(x_offset + 5.2 * units.cm, y_linea_pie - 0.4 * units.cm, "CAJAS / BULTO")
        c.drawString(x_offset + 7.5 * units.cm, y_linea_pie - 0.4 * units.cm, "TRANSPORTE")

        c.setFont("Helvetica-Bold", 13)
        c.drawString(x_offset + 0.5 * units.cm, y_linea_pie - 1.0 * units.cm, str(factura_val))

        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x_offset + 5.2 * units.cm, y_linea_pie - 1.0 * units.cm, f"{i + 1} / {total_etqs}")

        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_offset + 7.5 * units.cm, y_linea_pie - 1.0 * units.cm, transporte_final[:18])
        c.showPage()

    c.save()
    return output.getvalue()


# ============================================================
# 6. ORDEN DE EMBARQUE (HTML PARA IMPRESIÓN)
# ============================================================
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


# ============================================================
# 7. HELPER DE PERMISOS (usado por costos_muestras.py)
# ============================================================
def es_usuario_logistica():
    """True si el usuario logeado tiene privilegios de Logística/Admin."""
    usuario_logeado = st.session_state.get("usuario_activo", "Invitado")
    permisos_usuario = st.session_state.get("permisos", {})

    es_admin_general = (
        usuario_logeado.upper() == "RIGOBERTO"
        or permisos_usuario.get("ACCESS CONTROL", False)
        or permisos_usuario.get("PANEL MUESTRAS", False)
        or "LOGISTICA" in usuario_logeado.upper()
    )
    return es_admin_general or usuario_logeado in ["Rigoberto", "JMoreno"], usuario_logeado


def bloque_acceso_restringido(usuario_logeado):
    vars_css = {"card": "#263238", "border": "rgba(255,255,255,0.05)", "text": "#FFFFFF"}
    html_restringido = f"""<div style="background-color:{vars_css['card']}; border:1px solid {vars_css['border']}; border-left:8px solid #F7C300; padding:18px 40px; border-radius:10px; margin:15px 0; box-shadow:0 6px 20px rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:space-between;"><div style="display:flex; align-items:center; gap:25px;"><span style="font-size:28px;">🔐</span><div style="text-align:left;"><span style="color:#F7C300; font-weight:900; font-size:14px; letter-spacing:3px; text-transform:uppercase; display:block; margin-bottom:4px;">ÁREA RESTRINGIDA</span><span style="color:{vars_css['text']}; font-size:14px; font-weight:500; opacity:0.9;">El perfil de operador <b>{usuario_logeado}</b> no cuenta con privilegios de nivel <b>Logística</b>.</span></div></div><div style="padding:6px 16px; border:1px solid rgba(247,195,0,0.5); background:rgba(247,195,0,0.1); border-radius:6px; font-size:11px; color:#F7C300; font-weight:900; letter-spacing:1px;">ID ACCESO: {st.session_state.get('usuario_activo', 'ERR')}</div></div>"""
    st.markdown(html_restringido, unsafe_allow_html=True)
