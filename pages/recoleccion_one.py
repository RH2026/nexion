import base64
import html as _html
import io
import re
import time
from datetime import datetime
from io import BytesIO

import pandas as pd
import requests
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from components.layout import render_layout


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Formato de Recolecciones ONE",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="FORMATOS", submodulo_actual="RECOLECCION ONE")


# ============================================================
# 3. CONFIGURACIÓN GITHUB (MISMO CSV QUE RECOLECCION 3G / SEGUIMIENTO)
# ============================================================
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
BRANCH = "main"

ARCHIVO_FACTURACION = "facturacion_moreno.csv"
ARCHIVO_LOGO_ONE = "one.png"
ARCHIVO_ESTATUS = "recolecciones_estatus.csv"      # <- el mismo que usa 3G y la página de seguimiento

PAQUETERIA = "ONE"
SOLICITANTE = "RIGOBERTO HERNANDEZ"

# Mismas columnas que maneja pages/recolecciones.py (+ "Paqueteria" para distinguir 3G de ONE)
COLUMNAS_ESTATUS = ["Folio", "Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total",
                    "Estatus", "Observaciones", "Solicitante", "Numero de Guia", "Costo de la Guia",
                    "Motivo", "ID_Queja", "Motivo_Devolucion", "Paqueteria"]
COLUMNAS_NUM = ["Peso_Total", "Costo de la Guia"]

TIPOS_BULTO = ["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"]

COMENTARIO_DEFAULT = ("LLAMAR AL REMITENTE UNA HORA ANTES DE LA RECOLECCIÓN, SI NO QUIEREN ENTREGAR "
                      "LLAMAR AL TELÉFONO Cel. 33 19 75 31 22 Rigoberto Hernandez")


def _api_url(archivo):
    return f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{archivo}"


def _gh_headers(extra=None):
    h = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
         "Accept": "application/vnd.github.v3+json"}
    if extra:
        h.update(extra)
    return h


def _normalizar(df, columnas, columnas_num):
    df.columns = df.columns.astype(str).str.strip()
    for col in columnas:
        if col not in df.columns:
            df[col] = 0.0 if col in columnas_num else ""
    for col in columnas_num:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in df.columns:
        if col not in columnas_num:
            df[col] = df[col].fillna("").astype(str)
    return df


def _leer_estatus_fresco():
    """Lee el CSV de estatus por la API de GitHub (sin caché del CDN). Devuelve (df, sha).
    Se lee con dtype=str para que un Folio como 12345 NO se convierta en número
    (si no, nunca se detecta que el folio ya existe y se duplica)."""
    url = _api_url(ARCHIVO_ESTATUS)
    params = {"ref": BRANCH, "t": time.time_ns()}
    r = requests.get(url, headers=_gh_headers(), params=params, timeout=20)
    if r.status_code == 404:
        return _normalizar(pd.DataFrame(columns=COLUMNAS_ESTATUS), COLUMNAS_ESTATUS, COLUMNAS_NUM), None
    r.raise_for_status()
    data = r.json()
    if data.get("content"):
        raw = base64.b64decode(data["content"])
    else:
        r2 = requests.get(url, headers=_gh_headers({"Accept": "application/vnd.github.raw"}),
                          params=params, timeout=30)
        r2.raise_for_status()
        raw = r2.content
    df = pd.read_csv(BytesIO(raw), encoding="utf-8-sig", dtype=str, keep_default_na=False)
    return _normalizar(df, COLUMNAS_ESTATUS, COLUMNAS_NUM), data.get("sha")


def folio_existe(folio):
    try:
        df, _ = _leer_estatus_fresco()
        return bool((df["Folio"].astype(str) == str(folio)).any())
    except Exception:
        return False


def registrar_folio_github(folio, datos):
    """Registra (o actualiza si ya existe) el folio en recolecciones_estatus.csv.
    Relee el archivo justo antes de escribir y reintenta si alguien más guardó al mismo tiempo.
    Devuelve (ok, accion) con accion = 'creado' | 'actualizado'."""
    url = _api_url(ARCHIVO_ESTATUS)
    folio = str(folio).strip()

    for intento in range(4):
        try:
            df, sha = _leer_estatus_fresco()
        except Exception as e:
            st.error(f"No se pudo leer GitHub antes de guardar: {e}")
            return False, ""

        mask = df["Folio"].astype(str) == folio
        if mask.any():
            # Folio ya existente: solo se refrescan los datos del formato.
            # NO se tocan Estatus, Guía, Costo, Motivo, etc. (eso lo edita el seguimiento).
            for col in ["Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total", "Paqueteria"]:
                df.loc[mask, col] = datos[col]
            accion = "actualizado"
        else:
            fila = {c: ("" if c not in COLUMNAS_NUM else 0.0) for c in COLUMNAS_ESTATUS}
            fila.update(datos)
            fila["Folio"] = folio
            df = pd.concat([df, pd.DataFrame([fila])], ignore_index=True)
            accion = "creado"

        df = _normalizar(df, COLUMNAS_ESTATUS, COLUMNAS_NUM)
        payload = {
            "message": f"Registro de folio {folio} ({PAQUETERIA})",
            "content": base64.b64encode(df.to_csv(index=False).encode("utf-8-sig")).decode("utf-8"),
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha

        try:
            r = requests.put(url, headers=_gh_headers(), json=payload, timeout=30)
        except Exception as e:
            st.error(f"No se pudo guardar en GitHub: {e}")
            return False, ""

        if r.status_code in (200, 201):
            return True, accion
        if r.status_code in (409, 422) and intento < 3:
            time.sleep(0.6 * (intento + 1))
            continue
        st.error(f"Error al guardar en GitHub: {r.status_code} - {r.text}")
        return False, ""

    st.error("No se pudo guardar por conflictos repetidos. Intenta de nuevo.")
    return False, ""


# ============================================================
# 4. PDF (ONE PAQUETERÍA)  -> función independiente, recibe todo por parámetro
# ============================================================
def generar_pdf_one(d, lineas, logo_bytes=None):
    """d: dict con los datos del formulario. lineas: lista de renglones de carga."""
    P = lambda t: _html.escape(str(t if t is not None else "")).replace("\n", "<br/>")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=15, leftMargin=15,
                            topMargin=15, bottomMargin=15)
    story = []

    th_style = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=colors.white, alignment=1)
    cell_bold = ParagraphStyle("CB", fontName="Helvetica-Bold", fontSize=6, leading=7.5)
    cell_normal = ParagraphStyle("CN", fontName="Helvetica", fontSize=6, leading=7.5)
    cell_center = ParagraphStyle("CC", fontName="Helvetica", fontSize=6, leading=7.5, alignment=1)
    th_red = ParagraphStyle("THR", fontName="Helvetica-Bold", fontSize=6, leading=7, textColor=colors.white, alignment=1)
    th_blue = ParagraphStyle("THB", fontName="Helvetica-Bold", fontSize=6, leading=7, textColor=colors.white, alignment=1)

    AZUL, ROJO = "#1565c0", "#c62828"
    AZUL_CLARO, ROJO_CLARO = "#e3f2fd", "#ffebee"

    fecha_actual = datetime.now().strftime("%d/%m/%Y")

    # 1. ENCABEZADO (582 pts de ancho total)
    logo_elem = Paragraph("<b>ONE Paquetería</b>", cell_center)
    if logo_bytes:
        try:
            logo_elem = Image(BytesIO(logo_bytes), width=85, height=22)
        except Exception:
            pass

    sub_table_reco = Table([
        [Paragraph("<b>RECOLECCION</b>", ParagraphStyle("RH", alignment=1, fontSize=5.5, fontName="Helvetica-Bold")),
         Paragraph("<b>EMBARQUE EN MOSTRADOR</b>", ParagraphStyle("EM", alignment=1, fontSize=5, fontName="Helvetica-Bold"))],
        [Paragraph("<b>X</b>", ParagraphStyle("MK", alignment=1, fontSize=8, fontName="Helvetica-Bold", textColor=colors.HexColor(ROJO))), ""],
    ], colWidths=[101, 101], style=[
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#f0f0f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ])

    header_table = Table([[
        logo_elem,
        Paragraph("<b>MANIFIESTO DE EMBARQUE</b>", ParagraphStyle("HT", alignment=1, fontSize=10.5, fontName="Helvetica-Bold", textColor=colors.HexColor("#0d47a1"))),
        sub_table_reco,
    ]], colWidths=[130, 250, 202])
    header_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 2))

    # 2. FECHAS / FOLIO
    fechas_table = Table([
        [Paragraph("<b>FECHA DE RECOLECCION:</b>", cell_bold), Paragraph(P(d["fecha_rec"]), cell_center),
         Paragraph("<b>FECHA SOLICITUD</b>", cell_bold), Paragraph(fecha_actual, cell_center)],
        [Paragraph("<b>FOLIO / FACTURA:</b>", cell_bold), Paragraph(P(d["folio"]), cell_center),
         Paragraph("<b>ESTATUS PAGO</b>", cell_bold), Paragraph(P(d["tipo_pago"]), cell_center)],
    ], colWidths=[110, 150, 105, 217])
    fechas_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(AZUL_CLARO)),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor(AZUL_CLARO)),
        ("BACKGROUND", (0, 1), (0, 1), colors.HexColor(ROJO_CLARO)),
        ("BACKGROUND", (2, 1), (2, 1), colors.HexColor(ROJO_CLARO)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]))
    story.append(fechas_table)
    story.append(Spacer(1, 2))

    # 3. REMITENTE Y DESTINATARIO
    def bloque_persona(titulo, color, p):
        data = [
            [Paragraph(titulo, th_style), ""],
            [Paragraph("CLIENTE:", cell_bold), Paragraph(P(p["cliente"]), cell_bold)],
            [Paragraph("CALLE Y NUMERO:", cell_bold), Paragraph(P(p["calle"]), cell_normal)],
            [Paragraph("COLONIA / CP:", cell_bold), Paragraph(f"{P(p['colonia'])} - C.P. {P(p['cp'])}", cell_normal)],
            [Paragraph("CIUDAD / ESTADO:", cell_bold), Paragraph(f"{P(p['ciudad'])}, {P(p['estado'])}", cell_normal)],
            [Paragraph("CONTACTO / TEL:", cell_bold), Paragraph(f"{P(p['contacto'])} - {P(p['tel'])}", cell_normal)],
        ]
        t = Table(data, colWidths=[85, 206])
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (1, 0)),
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor(color)),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ]))
        return t

    t_top = Table([[bloque_persona("REMITENTE - RECOLECCION", ROJO, d["rem"]),
                    bloque_persona("DESTINATARIO - ENTREGA", AZUL, d["dest"])]], colWidths=[291, 291])
    story.append(t_top)
    story.append(Spacer(1, 2))

    # 4. FACTURAR A
    fac_data = [
        [Paragraph("<b>FACTURAR A:</b>", th_style), "", ""],
        [Paragraph(P(d["fac_cliente"]), cell_center), "", ""],
        [Paragraph("<b>DOMICILIO:</b>", cell_bold), Paragraph("Cel. 33 19 75 31 22", cell_center), ""],
        [Paragraph(f"{P(d['fac_domicilio'])}<br/>Tel.. 0152 (33) 35402939<br/>E-mail: rhernandez@jypesa.com",
                   ParagraphStyle("FD", alignment=1, fontSize=6, fontName="Helvetica", leading=7.5)), "", ""],
        [Paragraph("<b>RFC:</b>", cell_bold), Paragraph(f"RFC {P(d['fac_rfc'])}", cell_center), ""],
    ]
    # Etiquetas "DOMICILIO:" y "RFC:" sobre fondo azul -> texto blanco
    fac_data[2][0] = Paragraph("<b>DOMICILIO:</b>", ParagraphStyle("W1", parent=cell_bold, textColor=colors.white))
    fac_data[4][0] = Paragraph("<b>RFC:</b>", ParagraphStyle("W2", parent=cell_bold, textColor=colors.white))
    t_fac = Table(fac_data, colWidths=[75, 407, 100])
    t_fac.setStyle(TableStyle([
        ("SPAN", (0, 0), (2, 0)), ("SPAN", (0, 1), (2, 1)), ("SPAN", (1, 2), (2, 2)),
        ("SPAN", (0, 3), (2, 3)), ("SPAN", (1, 4), (2, 4)),
        ("BACKGROUND", (0, 0), (2, 0), colors.HexColor(AZUL)),
        ("BACKGROUND", (0, 1), (2, 1), colors.HexColor(AZUL_CLARO)),
        ("BACKGROUND", (0, 2), (0, 2), colors.HexColor(AZUL)),
        ("BACKGROUND", (1, 2), (2, 2), colors.white),
        ("BACKGROUND", (0, 3), (2, 3), colors.HexColor(AZUL_CLARO)),
        ("BACKGROUND", (0, 4), (0, 4), colors.HexColor(AZUL)),
        ("BACKGROUND", (1, 4), (2, 4), colors.HexColor(AZUL_CLARO)),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]))
    story.append(t_fac)
    story.append(Spacer(1, 2))

    # 5. TABLA DE EMBARQUE
    emb_headers = ["Cantidad", "TIPO DE BULTOS", "DESCRIPCION", "LARGO x ANCHO", "ALTO", "CUBICAJE (m3)", "PESO (KG)"]
    emb_data = [
        [Paragraph("<b>INFORMACION DE EMBARQUE</b>", th_style), "", "",
         Paragraph("<b>DIMENSIONES (mts)</b>", th_style), "",
         Paragraph("<b>VOLUMEN</b>", th_style), Paragraph("<b>PESO POR BULTO</b>", th_style)],
        [Paragraph(h, th_style) for h in emb_headers],
    ]
    cubicaje_total = 0.0
    peso_total = 0.0
    for l in lineas:
        cub = float(l["largo"]) * float(l["ancho"]) * float(l["alto"]) * int(l["cantidad"])
        cubicaje_total += cub
        peso_total += float(l["peso"]) * int(l["cantidad"])
        emb_data.append([
            Paragraph(str(l["cantidad"]), cell_center),
            Paragraph(P(l["tipo"]), cell_center),
            Paragraph(P(l["descripcion"]), cell_center),
            Paragraph(f"{l['largo']:g} x {l['ancho']:g}", cell_center),
            Paragraph(f"{l['alto']:g}", cell_center),
            Paragraph(f"{cub:,.2f}", cell_center),
            Paragraph(f"{l['peso']:g}", cell_center),
        ])
    for _ in range(max(0, 6 - len(lineas))):
        emb_data.append(["", "", "", "", "", "", ""])
    emb_data.append(["", "", "", "", "",
                     Paragraph(f"<b>{cubicaje_total:,.2f}</b>", cell_center),
                     Paragraph(f"<b>{peso_total:,.1f}</b>", cell_center)])

    t_emb = Table(emb_data, colWidths=[45, 60, 177, 90, 65, 75, 70])
    t_emb.setStyle(TableStyle([
        ("SPAN", (0, 0), (2, 0)),
        ("SPAN", (3, 0), (4, 0)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor(AZUL)),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]))
    story.append(t_emb)
    story.append(Spacer(1, 2))

    # 6. BLOQUE MEDIO  (la X de tipo de pago ahora sale según la condición elegida)
    tp = d["tipo_pago"].upper()
    marca_pago = [("X" if tp.startswith("PAGADO") else ""),
                  ("X" if tp.startswith("POR COBRAR") else ""),
                  ("X" if tp.startswith("CR") else "")]
    estilo_pago = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]
    for i, m in enumerate(marca_pago):
        if m:
            estilo_pago.append(("BACKGROUND", (i, 1), (i, 1), colors.HexColor(ROJO_CLARO)))

    def sub(rows, widths, extra=None, pad=1):
        base = [("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), pad),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad)]
        return Table(rows, colWidths=widths, style=base + (extra or []))

    mid_table_data = [
        [Paragraph("<b>MERCANCIA ASEGURADA</b>", th_red),
         Paragraph("<b>REQUIERE ACUSE DE RECIBO</b>", th_red),
         Paragraph("<b>DESCRIPCION DEL ACUSE:</b>", th_red)],
        [
            sub([[Paragraph("SI", cell_center), "", Paragraph("VALOR DECLARADO", cell_bold)],
                 [Paragraph("NO", cell_center), Paragraph("X", cell_center), Paragraph("POR CUENTA Y RIESGO", cell_bold)]],
                [28, 28, 84], [("BACKGROUND", (2, 0), (2, -1), colors.HexColor(AZUL_CLARO))]),
            sub([[Paragraph("SI", cell_center), Paragraph("X", cell_center), Paragraph("N<br/>O", cell_center)],
                 ["", "", ""]], [28, 28, 24]),
            "",
        ],
        [Paragraph("<b>TIPO DE PAGO MARCAR CON UNA X</b>", th_blue),
         Paragraph("<b>MARCAR CON UNA X (EAD / OCURRE)</b>", th_blue),
         Paragraph("<b>DOCUMENTOS QUE ANEXA</b>", th_red)],
        [
            Table([[Paragraph("pagado (origen)", cell_center), Paragraph("por cobrar (destino)", cell_center), Paragraph("Credito", cell_center)],
                   [Paragraph(m, cell_center) if m else "" for m in marca_pago]],
                  colWidths=[45, 50, 45], style=estilo_pago),
            sub([[Paragraph("Recolección", cell_center), Paragraph("Recepción", cell_center), Paragraph("Entrega Domicilio", cell_center)],
                 [Paragraph("X", cell_center), "", Paragraph("X", cell_center)]],
                [45, 45, 60],
                [("BACKGROUND", (0, 1), (0, 1), colors.HexColor(AZUL_CLARO)),
                 ("BACKGROUND", (2, 1), (2, 1), colors.HexColor(AZUL_CLARO))]),
            sub([[Paragraph("factura", cell_center), Paragraph("orden de compra", cell_center),
                  Paragraph("pedimento", cell_center), Paragraph("otro", cell_center)]],
                [68, 68, 68, 68], pad=4),
        ],
    ]
    t_mid = Table(mid_table_data, colWidths=[140, 150, 292])
    t_mid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (2, 0), colors.HexColor(ROJO)),
        ("BACKGROUND", (2, 1), (2, 1), colors.HexColor(AZUL_CLARO)),
        ("BACKGROUND", (0, 2), (1, 2), colors.HexColor(AZUL)),
        ("BACKGROUND", (2, 2), (2, 2), colors.HexColor(ROJO)),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(t_mid)
    story.append(Spacer(1, 2))

    # 7. BLOQUE FINAL (solicitante + comentarios del usuario)
    t_final = Table([
        [Paragraph("<b>DATOS DE QUIEN SOLICITA EL SERVICIO</b>", th_blue),
         Paragraph("<b>OBSERVACIONES / COMENTARIOS</b>", th_red)],
        [
            Table([
                [Paragraph("<b>NOMBRE:</b>", cell_bold), Paragraph("RIGOBERTO HERNANDEZ", cell_center)],
                [Paragraph("<b>EMPRESA:</b>", cell_bold), Paragraph("JYPESA", cell_center)],
                [Paragraph("<b>E-MAIL:</b>", cell_bold), Paragraph("rhernandez@jypesa.com", cell_center)],
                [Paragraph("<b>TELEFONO:</b>", cell_bold), Paragraph("Cel. 33 19 75 31 22", cell_center)],
            ], colWidths=[65, 225], style=[
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor(AZUL_CLARO)),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]),
            Paragraph(f"<b>{P(d['comentarios'])}</b>", cell_normal),
        ],
    ], colWidths=[290, 292])
    t_final.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(AZUL)),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor(ROJO)),
        ("BACKGROUND", (1, 1), (1, 1), colors.HexColor(ROJO_CLARO)),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t_final)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ============================================================
# 5. INTERFAZ PRINCIPAL
# ============================================================
def main():
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    st.markdown("""
<style>
    div.stButton > button,
    div.stButton > button:link,
    div.stButton > button:visited {
        background-color: #2B343B !important;
        color: #FFFFFF !important;
        border: 1px solid #2B343B !important;
        border-radius: 5px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        box-shadow: none !important;
    }
    div.stButton > button:hover,
    div.stButton > button:focus {
        background-color: #00A3A3 !important;
        color: #FFFFFF !important;
        border-color: #00A3A3 !important;
        box-shadow: none !important;
    }
    div.stButton > button:active {
        background-color: #00A3A3 !important;
        border-color: #00A3A3 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

    @st.cache_data(ttl=60)
    def cargar_facturacion():
        try:
            url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{ARCHIVO_FACTURACION}"
            headers = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"}
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                # dtype=str: Factura/CP/Teléfono se quedan tal cual (sin ".0")
                df = pd.read_csv(BytesIO(r.content), encoding="utf-8-sig", dtype=str, keep_default_na=False)
                df.columns = [str(c).upper().strip() for c in df.columns]
                return df
            st.error(f"Error al descargar de GitHub (Código {r.status_code}).")
        except Exception as e:
            st.error(f"No se pudo cargar el archivo CSV desde GitHub: {e}")
        return pd.DataFrame()

    @st.cache_data(ttl=300)
    def obtener_logo_one():
        """Devuelve los bytes del logo (no un BytesIO, para poder reutilizarlo sin problemas)."""
        try:
            url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{ARCHIVO_LOGO_ONE}"
            headers = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"}
            r = requests.get(url, headers=headers, timeout=20)
            return r.content if r.status_code == 200 else None
        except Exception:
            return None

    def titulo_seccion(texto, color_fondo="#1565c0"):
        st.markdown(f"""
            <div style="background-color: {color_fondo}; padding: 8px; border-radius: 4px; text-align: center; color: white; font-weight: bold; font-size: 15px; margin-bottom: 10px;">
                {texto}
            </div>
        """, unsafe_allow_html=True)

    df_fact = cargar_facturacion()
    if df_fact.empty or "FACTURA" not in df_fact.columns:
        st.warning("No se encontraron datos en el CSV de facturación de GitHub.")
        return

    df_fact["FACTURA"] = df_fact["FACTURA"].astype(str).str.strip()
    facturas_disponibles = df_fact["FACTURA"].unique().tolist()

    # --- botón para ir al seguimiento ---
    col_espacio, col_regresar = st.columns([5, 1])
    with col_regresar:
        if st.button("⬅️ Seguimiento", use_container_width=True, key="one_btn_ir_seguimiento"):
            st.switch_page("pages/recolecciones.py")

    # --- 4 CONTROLES PRINCIPALES ---
    top1, top2, top3, top4 = st.columns(4)
    with top1:
        fecha_rec_dt = st.date_input("📅 Fecha Recolección", value=datetime.now(), key="one_fecha_rec")
    fecha_rec_str = fecha_rec_dt.strftime("%d/%m/%Y")

    with top2:
        modo = st.selectbox("🔍 Método de Selección", ["Seleccionar de la lista", "Escribir folio manual"], key="one_modo")

    with top3:
        if modo == "Seleccionar de la lista":
            num_factura = st.selectbox("Folio / Factura", facturas_disponibles, key="one_sel_factura")
        else:
            num_factura = st.text_input("✍️ Ingresa Folio Manual", key="one_txt_folio")
    num_factura = str(num_factura or "").strip()

    with top4:
        tipo_pago = st.selectbox("💳 Condición de Pago", ["POR COBRAR (DESTINO)", "PAGADO (ORIGEN)", "CRÉDITO"], key="one_pago")

    # Registro de la factura elegida (si existe en el CSV)
    registro = pd.Series(dtype=str)
    if num_factura:
        match = df_fact[df_fact["FACTURA"] == num_factura]
        if not match.empty:
            registro = match.iloc[0]

    def dato(*cols):
        for c in cols:
            if not registro.empty and c in registro.index:
                v = str(registro[c]).strip()
                if v and v.lower() != "nan":
                    return v
        return ""

    def_extran = dato("NOMBRE_EXTRAN")
    def_dom = dato("DOMICILIO", "CALLE")
    def_col = dato("COLONIA")
    def_cui = dato("CUIDAD", "CIUDAD")
    def_cp = dato("CP")
    def_est = dato("ESTADO")
    def_tel = dato("TELEFONO", "TEL", "TELÉFONO")

    # Sufijo en las llaves => al cambiar de factura los campos SE ACTUALIZAN con los datos nuevos
    k = re.sub(r"\W", "_", num_factura) or "gen"

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        titulo_seccion("REMITENTE - RECOLECCIÓN (PROVEEDOR)", color_fondo="#c62828")
        rem_cliente = st.text_input("Comercializadora / Proveedor", value=def_extran, key=f"one_rem_cli_{k}")
        rem_calle = st.text_input("Calle y Número (Remitente)", value=def_dom, key=f"one_rem_call_{k}")
        a, b = st.columns(2)
        with a:
            rem_colonia = st.text_input("Colonia (Remitente)", value=def_col, key=f"one_rem_col_{k}")
        with b:
            rem_cp = st.text_input("CP (Remitente)", value=def_cp, key=f"one_rem_cp_{k}")
        a, b = st.columns(2)
        with a:
            rem_cui = st.text_input("Ciudad / Municipio", value=def_cui, key=f"one_rem_cui_{k}")
        with b:
            rem_estado = st.text_input("Estado", value=def_est, key=f"one_rem_est_{k}")
        a, b = st.columns(2)
        with a:
            rem_contacto = st.text_input("Persona que entrega", value="", key=f"one_rem_cont_{k}")
        with b:
            rem_tel = st.text_input("Teléfono Remitente", value=def_tel, key=f"one_rem_tel_{k}")

    with col2:
        titulo_seccion("DESTINATARIO - ENTREGA (JYPESA)", color_fondo="#1565c0")
        dest_cliente = st.text_input("Cliente Destino", value="Jabones y productos Especializados", key="one_dest_cli")
        dest_calle = st.text_input("Calle Destino", value="C. Cernícalo 155", key="one_dest_call")
        a, b = st.columns(2)
        with a:
            dest_colonia = st.text_input("Colonia Destino", value="La Aurora", key="one_dest_col")
        with b:
            dest_cp = st.text_input("CP Destino", value="44460", key="one_dest_cp")
        a, b = st.columns(2)
        with a:
            dest_cui = st.text_input("Ciudad Destino", value="Guadalajara", key="one_dest_cui")
        with b:
            dest_estado = st.text_input("Estado Destino", value="Jalisco", key="one_dest_est")
        a, b = st.columns(2)
        with a:
            dest_contacto = st.text_input("Persona que recibe", value="Jazmin Castillo", key="one_dest_cont")
        with b:
            dest_tel = st.text_input("Teléfono Destino", value="33 3540 2939 Ext.123", key="one_dest_tel")

    titulo_seccion("FACTURAR A (DATOS FISCALES JYPESA)", color_fondo="#37474f")
    fac_cliente = st.text_input("Facturar a Nombre de", value="JABONES Y PRODUCTOS ESPECIALIZADOS SA DE CV", key="one_fac_cli")
    fac_domicilio = st.text_input("Domicilio Fiscal", value="Privada del Gallo No. 1525, Col. La Aurora C.P. 44460 Guadalajara, JAL México", key="one_fac_dom")
    fac_rfc = st.text_input("RFC Facturación", value="JPE830408B35", key="one_fac_rfc")

    # --- COMENTARIOS ---
    st.markdown("---")
    titulo_seccion("💬 OBSERVACIONES / COMENTARIOS ADICIONALES", color_fondo="#37474f")
    comentarios = st.text_area("Instrucciones o notas especiales para la recolección",
                               value=COMENTARIO_DEFAULT, key="one_comentarios")

    # --- LÍNEAS DE EMBARQUE ---
    st.markdown("---")
    titulo_seccion("📦 DETALLE DE EMBARQUE Y LÍNEAS DE CARGA", color_fondo="#c62828")

    if "lineas_embarque_one" not in st.session_state:
        st.session_state.lineas_embarque_one = [
            {"id": 0, "cantidad": 1, "tipo": "TARIMA", "descripcion": "AMENIDADES",
             "largo": 1.20, "ancho": 1.20, "alto": 2.00, "peso": 800.0}
        ]
    if "one_next_id" not in st.session_state:
        st.session_state.one_next_id = 1

    for idx, linea in enumerate(st.session_state.lineas_embarque_one):
        rid = linea["id"]
        st.markdown(f"**Renglón {idx + 1}**")
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2, 2, 1, 1, 1, 1])
        with c1:
            linea["cantidad"] = st.number_input("Cant.", min_value=1, value=int(linea["cantidad"]), key=f"one_cant_{rid}")
        with c2:
            i_t = TIPOS_BULTO.index(linea["tipo"]) if linea["tipo"] in TIPOS_BULTO else 0
            linea["tipo"] = st.selectbox("Tipo Bulto", TIPOS_BULTO, index=i_t, key=f"one_tipo_{rid}")
        with c3:
            linea["descripcion"] = st.text_input("Descripción", value=linea["descripcion"], key=f"one_desc_{rid}")
        with c4:
            linea["largo"] = st.number_input("Largo (m)", value=float(linea["largo"]), key=f"one_larg_{rid}")
        with c5:
            linea["ancho"] = st.number_input("Ancho (m)", value=float(linea["ancho"]), key=f"one_anch_{rid}")
        with c6:
            linea["alto"] = st.number_input("Alto (m)", value=float(linea["alto"]), key=f"one_alt_{rid}")
        with c7:
            linea["peso"] = st.number_input("Peso (KG)", value=float(linea["peso"]), key=f"one_pes_{rid}")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("➕ Agregar otra línea de carga", key="one_btn_agregar"):
            st.session_state.lineas_embarque_one.append({
                "id": st.session_state.one_next_id, "cantidad": 1, "tipo": "CAJA", "descripcion": "MERCANCIA",
                "largo": 0.50, "ancho": 0.50, "alto": 0.50, "peso": 50.0})
            st.session_state.one_next_id += 1
            st.rerun()
    with b2:
        if len(st.session_state.lineas_embarque_one) > 1 and st.button("🗑️ Eliminar última línea", key="one_btn_eliminar"):
            st.session_state.lineas_embarque_one.pop()
            st.rerun()

    lineas = st.session_state.lineas_embarque_one
    total_peso_calc = sum(l["peso"] * l["cantidad"] for l in lineas)
    st.info(f"⚖️ **Peso Total Calculado:** {total_peso_calc:,.2f} KG")

    # --- DATOS PARA PDF ---
    datos_pdf = {
        "folio": num_factura or "S/F",
        "fecha_rec": fecha_rec_str,
        "tipo_pago": tipo_pago,
        "rem": {"cliente": rem_cliente, "calle": rem_calle, "colonia": rem_colonia, "cp": rem_cp,
                "ciudad": rem_cui, "estado": rem_estado, "contacto": rem_contacto, "tel": rem_tel},
        "dest": {"cliente": dest_cliente, "calle": dest_calle, "colonia": dest_colonia, "cp": dest_cp,
                 "ciudad": dest_cui, "estado": dest_estado, "contacto": dest_contacto, "tel": dest_tel},
        "fac_cliente": fac_cliente, "fac_domicilio": fac_domicilio, "fac_rfc": fac_rfc,
        "comentarios": comentarios,
    }

    # --- BOTONES DE ACCIÓN ---
    st.markdown("---")
    g1, g2 = st.columns(2)

    with g1:
        if st.button("🚀 Generar Manifiesto de Embarque (ONE Paquetería)", use_container_width=True, key="one_btn_pdf"):
            pdf_buf = generar_pdf_one(datos_pdf, lineas, obtener_logo_one())
            nombre_pdf = "ONE_Manifiesto_" + re.sub(r"[^\w\-]", "_", num_factura or "SF") + ".pdf"
            st.success("¡Manifiesto de ONE Paquetería generado correctamente!")
            st.download_button(
                label="📥 Descargar Manifiesto ONE Paquetería",
                data=pdf_buf,
                file_name=nombre_pdf,
                mime="application/pdf",
                use_container_width=True,
                key="one_dl_pdf",
            )

    with g2:
        if st.button("Registrar Folio en Estatus GitHub", use_container_width=True, key="one_btn_guardar_gh"):
            if not num_factura:
                st.error("Captura o selecciona un Folio / Factura antes de registrar.")
            else:
                obs = "Creado desde solicitud ONE Paquetería"
                if comentarios.strip():
                    obs += f". Comentarios: {comentarios.strip()}"

                datos_registro = {
                    "Fecha_Recoleccion": fecha_rec_str,
                    "Cliente": str(dest_cliente),
                    "Proveedor": str(rem_cliente),
                    "Peso_Total": float(total_peso_calc),
                    "Estatus": "PENDIENTE DE RECOLECCION",
                    "Observaciones": obs,
                    "Solicitante": SOLICITANTE,
                    "Numero de Guia": "",
                    "Costo de la Guia": 0.0,
                    "Paqueteria": PAQUETERIA,
                }
                ok, accion = registrar_folio_github(num_factura, datos_registro)
                if ok:
                    if accion == "actualizado":
                        st.success(f"¡Folio {num_factura} ya existía: se actualizaron fecha, cliente, proveedor y peso en GitHub!")
                    else:
                        st.success(f"¡Folio {num_factura} registrado exitosamente en GitHub (estatus PENDIENTE DE RECOLECCION)!")


if __name__ == "__main__":
    main()
