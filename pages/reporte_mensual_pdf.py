# ============================================================
# NEXION | REPORTE EJECUTIVO MENSUAL
# Generador de PDF para Dirección
# ============================================================

import io
import time
import calendar
from datetime import datetime, date

import pandas as pd
import requests
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)

# Costos de muestras ya existentes en NEXION
from muestras_common import obtener_datos_github


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="NEXION | Reporte Ejecutivo Mensual",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MESES = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
]

URL_DASHBOARD = (
    "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/"
    "Matriz_Excel_Dashboard.csv"
)

# Mismas fleteras principales utilizadas actualmente por el ranking de NEXION.
FLETERAS_PRINCIPALES = [
    "TRES GUERRAS",
    "ONE",
    "TINY PACK",
    "PAQMEX",
    "SANCHEZ",
    "FLETES DE REGRESO",
]

CARRIERS_CARGA = [
    "TRES GUERRAS",
    "ONE",
    "TINY PACK",
    "PAQMEX",
    "PAQUETE",
    "SANCHEZ",
    "FLETES DE REGRESO",
    "FARMASES",
]


# ============================================================
# DATOS
# ============================================================

@st.cache_data(ttl=60)
def cargar_dashboard():
    try:
        t = int(time.time())
        r = requests.get(f"{URL_DASHBOARD}?nocache={t}", timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text), encoding="utf-8-sig")
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()


def parse_fecha(serie):
    s = pd.Series(serie).fillna("").astype(str).str.strip()

    try:
        return pd.to_datetime(s, errors="coerce", format="mixed", dayfirst=True)
    except TypeError:
        return pd.to_datetime(s, errors="coerce", dayfirst=True)


def num(serie):
    return pd.to_numeric(
        pd.Series(serie).astype(str)
        .str.replace(r"[^\d.\-]", "", regex=True)
        .replace("", "0"),
        errors="coerce",
    ).fillna(0.0)


def txt(df, col):
    if col not in df.columns:
        return pd.Series("", index=df.index)
    return df[col].fillna("").astype(str).str.strip()


def money(v):
    return f"${float(v):,.2f}"


def integer(v):
    return f"{int(round(float(v))):,}"


def pct(v):
    return f"{float(v):,.1f}%"


# ============================================================
# PREPARACIÓN PRINCIPAL
# ============================================================

def preparar_envios(df):
    df = df.copy()

    columnas_fecha = [
        "FECHA DE ENVÍO",
        "PROMESA DE ENTREGA",
        "FECHA DE ENTREGA REAL",
    ]

    for c in columnas_fecha:
        if c in df.columns:
            df[c] = parse_fecha(df[c])
        else:
            df[c] = pd.NaT

    columnas_num = [
        "CANTIDAD DE CAJAS",
        "COSTO DE LA GUÍA",
        "COSTOS ADICIONALES",
        "FACTURACION",
        "VALUACION",
    ]

    for c in columnas_num:
        df[c] = num(df[c]) if c in df.columns else 0.0

    for c in [
        "FLETERA", "TRANSPORTE", "FORMA DE ENVIO", "DESTINO",
        "NOMBRE DEL CLIENTE", "INCIDENCIAS", "NÚMERO DE PEDIDO",
        "NÚMERO DE GUÍA", "NO CLIENTE", "COMENTARIOS"
    ]:
        df[c] = txt(df, c)

    df["_COSTO_LOGISTICO"] = df["COSTO DE LA GUÍA"] + df["COSTOS ADICIONALES"]
    df["_ENTREGADO"] = df["FECHA DE ENTREGA REAL"].notna()

    df["_A_TIEMPO"] = (
        df["_ENTREGADO"]
        & df["PROMESA DE ENTREGA"].notna()
        & (df["FECHA DE ENTREGA REAL"] <= df["PROMESA DE ENTREGA"])
    )

    df["_INCIDENCIA"] = ~df["INCIDENCIAS"].str.upper().isin(["", "OK"])

    df["_DIAS_TRANSITO"] = (
        df["FECHA DE ENTREGA REAL"] - df["FECHA DE ENVÍO"]
    ).dt.days

    return df


def obtener_periodo(df, anio, mes):
    inicio = pd.Timestamp(year=anio, month=mes, day=1)
    fin = pd.Timestamp(
        year=anio,
        month=mes,
        day=calendar.monthrange(anio, mes)[1]
    )

    return df[
        (df["FECHA DE ENVÍO"] >= inicio)
        & (df["FECHA DE ENVÍO"] <= fin)
    ].copy()


# ============================================================
# PDF
# ============================================================

class ReportePDF:
    BG = colors.HexColor("#384A52")
    CARD = colors.HexColor("#263238")
    DARK = colors.HexColor("#182229")
    BORDER = colors.HexColor("#60737D")
    WHITE = colors.white
    MUTED = colors.HexColor("#B7C4CA")
    CYAN = colors.HexColor("#38BDF8")
    GREEN = colors.HexColor("#00C98B")
    GOLD = colors.HexColor("#E8C15A")
    RED = colors.HexColor("#D96C6C")

    def __init__(self, buffer, mes_nombre, anio):
        self.mes_nombre = mes_nombre
        self.anio = anio

        self.doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"NEXION | Reporte Ejecutivo Mensual | {mes_nombre} {anio}",
            author="NEXION // JYPESA Logistics",
        )

        styles = getSampleStyleSheet()

        self.title = ParagraphStyle(
            "NEXIONTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=25,
            textColor=self.WHITE,
            alignment=TA_LEFT,
            spaceAfter=5,
        )

        self.subtitle = ParagraphStyle(
            "NEXIONSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=self.MUTED,
            alignment=TA_LEFT,
        )

        self.section = ParagraphStyle(
            "Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=self.GOLD,
            spaceBefore=4,
            spaceAfter=9,
        )

        self.h3 = ParagraphStyle(
            "H3",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=self.WHITE,
            spaceBefore=5,
            spaceAfter=5,
        )

        self.body = ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=self.DARK,
        )

        self.small = ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=8.5,
            textColor=self.DARK,
        )

        self.small_white = ParagraphStyle(
            "SmallWhite",
            parent=self.small,
            textColor=self.WHITE,
        )

        self.center = ParagraphStyle(
            "Center",
            parent=self.small,
            alignment=TA_CENTER,
        )

        self.right = ParagraphStyle(
            "Right",
            parent=self.small,
            alignment=TA_RIGHT,
        )

        self.story = []

    # --------------------------------------------------------
    # ENCABEZADO / PIE
    # --------------------------------------------------------

    def page_header_footer(self, canvas, doc):
        canvas.saveState()

        width, height = letter

        # Encabezado superior
        canvas.setFillColor(self.DARK)
        canvas.rect(0, height - 11 * mm, width, 11 * mm, stroke=0, fill=1)

        canvas.setFillColor(self.WHITE)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawString(
            14 * mm,
            height - 7.2 * mm,
            "NEXION // SMART LOGISTICS"
        )

        canvas.setFillColor(self.GOLD)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawRightString(
            width - 14 * mm,
            height - 7.2 * mm,
            f"{self.mes_nombre} {self.anio}"
        )

        # Pie
        canvas.setStrokeColor(self.BORDER)
        canvas.line(
            14 * mm,
            10 * mm,
            width - 14 * mm,
            10 * mm
        )

        canvas.setFillColor(self.MUTED)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(
            14 * mm,
            6 * mm,
            "JYPESA // DISTRIBUCIÓN Y LOGÍSTICA"
        )

        canvas.drawRightString(
            width - 14 * mm,
            6 * mm,
            f"PÁGINA {doc.page}"
        )

        canvas.restoreState()

    # --------------------------------------------------------
    # ELEMENTOS
    # --------------------------------------------------------

    def portada(self, resumen):
        width, _ = letter

        data = [
            [
                Paragraph(
                    "NEXION",
                    ParagraphStyle(
                        "CoverBig",
                        parent=self.title,
                        fontSize=30,
                        leading=34,
                        textColor=self.WHITE,
                    )
                ),
                ""
            ],
            [
                Paragraph(
                    "REPORTE EJECUTIVO MENSUAL",
                    ParagraphStyle(
                        "CoverReport",
                        parent=self.title,
                        fontSize=17,
                        leading=21,
                        textColor=self.GOLD,
                    )
                ),
                ""
            ],
            [
                Paragraph(
                    f"{self.mes_nombre} {self.anio}",
                    ParagraphStyle(
                        "CoverMonth",
                        parent=self.subtitle,
                        fontSize=11,
                        textColor=self.WHITE,
                    )
                ),
                ""
            ],
        ]

        table = Table(data, colWidths=[width - 28 * mm, 0])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 10 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 8 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ]))

        self.story.append(Spacer(1, 18 * mm))
        self.story.append(table)
        self.story.append(Spacer(1, 10 * mm))

        kpi_data = [
            ["ENVÍOS", "ENTREGADOS", "A TIEMPO", "FACTURACIÓN", "COSTO LOGÍSTICO"],
            [
                integer(resumen["envios"]),
                integer(resumen["entregados"]),
                pct(resumen["efectividad_entrega"]),
                money(resumen["facturacion"]),
                money(resumen["costo_logistico"]),
            ],
        ]

        t = Table(
            kpi_data,
            colWidths=[35 * mm] * 5,
            repeatRows=1,
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.DARK),
            ("BACKGROUND", (0, 1), (-1, 1), self.CARD),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.MUTED),
            ("TEXTCOLOR", (0, 1), (-1, 1), self.WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, self.BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, self.BORDER),
        ]))

        self.story.append(t)
        self.story.append(Spacer(1, 12 * mm))

        self.story.append(
            Paragraph(
                "Documento ejecutivo generado directamente desde las bases operativas de NEXION. "
                "Las métricas se calculan sobre los registros correspondientes al periodo seleccionado.",
                self.small_white,
            )
        )

        self.story.append(PageBreak())

    def section_title(self, title):
        self.story.append(Paragraph(title, self.section))

    def table(self, headers, rows, widths=None, font_size=6.8):
        data = [[Paragraph(str(h), self.small_white) for h in headers]]

        for row in rows:
            data.append([
                Paragraph(str(v), self.small) for v in row
            ])

        if widths is None:
            widths = [((letter[0] - 28 * mm) / len(headers))] * len(headers)

        t = Table(
            data,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
        )

        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F4F6F7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.HexColor("#F4F6F7"),
                colors.white,
            ]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D1D5")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))

        self.story.append(t)
        self.story.append(Spacer(1, 5 * mm))

    def kpi_grid(self, items, columns=4):
        rows = []
        for i in range(0, len(items), columns):
            chunk = items[i:i + columns]
            while len(chunk) < columns:
                chunk.append(("", ""))

            rows.append([
                Paragraph(
                    f"<b>{label}</b><br/><font size='12'>{value}</font>",
                    self.center
                )
                for label, value in chunk
            ])

        t = Table(
            rows,
            colWidths=[(letter[0] - 28 * mm) / columns] * columns,
        )

        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF2F3")),
            ("BOX", (0, 0), (-1, -1), 0.5, self.BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCD5D9")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))

        self.story.append(t)
        self.story.append(Spacer(1, 6 * mm))

    # --------------------------------------------------------
    # SECCIONES DEL REPORTE
    # --------------------------------------------------------

    def resumen_mes(self, df):
        total = len(df)
        entregados = int(df["_ENTREGADO"].sum())
        a_tiempo = int(df["_A_TIEMPO"].sum())
        pendientes = total - entregados
        costo_guia = df["COSTO DE LA GUÍA"].sum()
        adicionales = df["COSTOS ADICIONALES"].sum()
        costo_log = costo_guia + adicionales
        facturacion = df["FACTURACION"].sum()
        cajas = df["CANTIDAD DE CAJAS"].sum()

        efectividad = a_tiempo / entregados * 100 if entregados else 0
        costo_pct = costo_log / facturacion * 100 if facturacion else 0
        costo_prom = costo_log / total if total else 0
        costo_caja = costo_log / cajas if cajas else 0

        self.section_title("01 // RESUMEN DEL MES")

        self.kpi_grid([
            ("ENVÍOS", integer(total)),
            ("ENTREGADOS", integer(entregados)),
            ("PENDIENTES", integer(pendientes)),
            ("A TIEMPO", integer(a_tiempo)),
            ("EFECTIVIDAD DE ENTREGA", pct(efectividad)),
            ("FACTURACIÓN", money(facturacion)),
            ("COSTO DE GUÍAS", money(costo_guia)),
            ("COSTOS ADICIONALES", money(adicionales)),
            ("COSTO LOGÍSTICO", money(costo_log)),
            ("COSTO / ENVÍO", money(costo_prom)),
            ("CAJAS", integer(cajas)),
            ("COSTO / CAJA", money(costo_caja)),
        ], columns=4)

        resumen_rows = [
            ["Indicador", "Resultado"],
            ["Costo logístico / facturación", pct(costo_pct)],
            ["Incidencias", integer(df["_INCIDENCIA"].sum())],
            ["Incidencias sobre envíos", pct(
                df["_INCIDENCIA"].mean() * 100 if total else 0
            )],
        ]

        self.table(
            resumen_rows[0],
            [r for r in resumen_rows[1:]],
            widths=[100 * mm, 70 * mm],
        )

    def efectividad_envios(self, df):
        self.section_title("02 // EFECTIVIDAD DE ENVÍOS")

        total = len(df)
        entregados = int(df["_ENTREGADO"].sum())
        a_tiempo = int(df["_A_TIEMPO"].sum())
        retraso = max(entregados - a_tiempo, 0)
        pendientes = total - entregados

        self.kpi_grid([
            ("TOTAL DE ENVÍOS", integer(total)),
            ("ENTREGADOS", integer(entregados)),
            ("A TIEMPO", integer(a_tiempo)),
            ("CON RETRASO", integer(retraso)),
            ("PENDIENTES", integer(pendientes)),
            ("EFECTIVIDAD", pct(
                a_tiempo / entregados * 100 if entregados else 0
            )),
        ], columns=3)

        por_destino = (
            df.groupby("DESTINO", as_index=False)
            .size()
            .rename(columns={"size": "ENVÍOS"})
            .query("DESTINO != ''")
            .sort_values("ENVÍOS", ascending=False)
            .head(10)
        )

        self.story.append(Paragraph("Distribución operativa por destino", self.h3))

        self.table(
            ["DESTINO", "ENVÍOS", "% DEL TOTAL"],
            [
                [
                    r["DESTINO"],
                    integer(r["ENVÍOS"]),
                    pct(r["ENVÍOS"] / total * 100 if total else 0),
                ]
                for _, r in por_destino.iterrows()
            ],
            widths=[105 * mm, 30 * mm, 35 * mm],
        )

    def inteligencia_negocio(self, df):
        self.section_title("03 // INTELIGENCIA DE NEGOCIO")

        fact = df["FACTURACION"].sum()
        costo = df["_COSTO_LOGISTICO"].sum()
        cajas = df["CANTIDAD DE CAJAS"].sum()

        self.kpi_grid([
            ("FACTURACIÓN", money(fact)),
            ("COSTO LOGÍSTICO", money(costo)),
            ("% COSTO LOGÍSTICO", pct(costo / fact * 100 if fact else 0)),
            ("CAJAS MOVILIZADAS", integer(cajas)),
            ("COSTO / CAJA", money(costo / cajas if cajas else 0)),
            ("INCIDENCIAS", integer(df["_INCIDENCIA"].sum())),
        ], columns=3)

        por_fletera = (
            df[df["FLETERA"] != ""]
            .groupby("FLETERA", as_index=False)
            .agg(
                ENVIOS=("FLETERA", "size"),
                COSTO=(" _COSTO_LOGISTICO".strip(), "sum"),
                CAJAS=("CANTIDAD DE CAJAS", "sum"),
            )
            .sort_values("COSTO", ascending=False)
            .head(10)
        )

        self.story.append(Paragraph("Costo operativo por fletera", self.h3))

        self.table(
            ["FLETERA", "ENVÍOS", "CAJAS", "COSTO", "COSTO / ENVÍO"],
            [
                [
                    r["FLETERA"],
                    integer(r["ENVIOS"]),
                    integer(r["CAJAS"]),
                    money(r["COSTO"]),
                    money(r["COSTO"] / r["ENVIOS"] if r["ENVIOS"] else 0),
                ]
                for _, r in por_fletera.iterrows()
            ],
            widths=[55 * mm, 25 * mm, 25 * mm, 35 * mm, 30 * mm],
        )

    def top_clientes(self, df):
        self.section_title("04 // TOP 20 CLIENTES DE DISTRIBUCIÓN")

        clientes = (
            df[df["NOMBRE DEL CLIENTE"] != ""]
            .groupby("NOMBRE DEL CLIENTE", as_index=False)
            .agg(
                ENVIOS=("NOMBRE DEL CLIENTE", "size"),
                FACTURACION=("FACTURACION", "sum"),
                CAJAS=("CANTIDAD DE CAJAS", "sum"),
                COSTO_LOGISTICO=("_COSTO_LOGISTICO", "sum"),
            )
            .sort_values(
                ["FACTURACION", "ENVIOS"],
                ascending=[False, False]
            )
            .head(20)
        )

        total_fact = df["FACTURACION"].sum()

        self.table(
            ["#", "CLIENTE", "ENVÍOS", "CAJAS", "FACTURACIÓN", "% FACT.", "COSTO LOG."],
            [
                [
                    i,
                    r["NOMBRE DEL CLIENTE"][:42],
                    integer(r["ENVIOS"]),
                    integer(r["CAJAS"]),
                    money(r["FACTURACION"]),
                    pct(r["FACTURACION"] / total_fact * 100 if total_fact else 0),
                    money(r["COSTO_LOGISTICO"]),
                ]
                for i, (_, r) in enumerate(clientes.iterrows(), start=1)
            ],
            widths=[10 * mm, 65 * mm, 20 * mm, 20 * mm, 32 * mm, 25 * mm, 32 * mm],
        )

    def distribucion_regreso(self, df):
        self.section_title("05 // DISTRIBUCIÓN DE CARGA · COBRO REGRESO")

        mask = (
            df["FORMA DE ENVIO"].str.contains("REGRESO", case=False, na=False)
            | df["TRANSPORTE"].str.contains("COBRO REGRESO", case=False, na=False)
            | df["FLETERA"].str.contains("FLETES DE REGRESO", case=False, na=False)
        )

        regreso = df[mask].copy()

        if regreso.empty:
            self.story.append(
                Paragraph(
                    "No se encontraron registros identificados como COBRO REGRESO en el periodo seleccionado.",
                    self.body
                )
            )
            return

        total_cajas = regreso["CANTIDAD DE CAJAS"].sum()
        total_envios = len(regreso)
        total_costo = regreso["_COSTO_LOGISTICO"].sum()

        self.kpi_grid([
            ("ENVÍOS REGRESO", integer(total_envios)),
            ("CAJAS", integer(total_cajas)),
            ("COSTO", money(total_costo)),
            ("COSTO / ENVÍO", money(total_costo / total_envios if total_envios else 0)),
        ], columns=4)

        por_transportista = (
            regreso.groupby("TRANSPORTE", as_index=False)
            .agg(
                ENVIOS=("TRANSPORTE", "size"),
                CAJAS=("CANTIDAD DE CAJAS", "sum"),
                COSTO=("_COSTO_LOGISTICO", "sum"),
            )
            .sort_values("CAJAS", ascending=False)
        )

        self.table(
            ["TRANSPORTE", "ENVÍOS", "CAJAS", "% CAJAS", "COSTO", "COSTO / ENVÍO"],
            [
                [
                    r["TRANSPORTE"] or "SIN TRANSPORTE",
                    integer(r["ENVIOS"]),
                    integer(r["CAJAS"]),
                    pct(r["CAJAS"] / total_cajas * 100 if total_cajas else 0),
                    money(r["COSTO"]),
                    money(r["COSTO"] / r["ENVIOS"] if r["ENVIOS"] else 0),
                ]
                for _, r in por_transportista.iterrows()
            ],
            widths=[50 * mm, 22 * mm, 22 * mm, 25 * mm, 32 * mm, 35 * mm],
        )

    def ranking_fleteras(self, df):
        self.section_title("06 // RANKING OPERATIVO DE FLETERAS")

        mask = df["FLETERA"].str.upper().apply(
            lambda x: any(c in x for c in FLETERAS_PRINCIPALES)
        )

        base = df[mask].copy()

        if base.empty:
            self.story.append(
                Paragraph("Sin registros de las fleteras principales en el periodo.", self.body)
            )
            return

        filas = []

        for fletera, g in base.groupby("FLETERA"):
            entregados = int(g["_ENTREGADO"].sum())
            a_tiempo = int(g["_A_TIEMPO"].sum())
            costo = g["_COSTO_LOGISTICO"].sum()
            cajas = g["CANTIDAD DE CAJAS"].sum()
            dias = g.loc[
                g["_ENTREGADO"] & (g["_DIAS_TRANSITO"] >= 0),
                "_DIAS_TRANSITO"
            ]

            filas.append({
                "FLETERA": fletera,
                "ENVIOS": len(g),
                "ENTREGADOS": entregados,
                "A_TIEMPO": a_tiempo,
                "RETRASO": max(entregados - a_tiempo, 0),
                "EFECTIVIDAD": a_tiempo / entregados * 100 if entregados else 0,
                "INCIDENCIAS": g["_INCIDENCIA"].mean() * 100 if len(g) else 0,
                "TRANSITO": dias.mean() if not dias.empty else 0,
                "COSTO": costo,
                "COSTO_PROM": costo / len(g) if len(g) else 0,
                "COSTO_CAJA": costo / cajas if cajas else 0,
            })

        ranking = pd.DataFrame(filas).sort_values(
            ["EFECTIVIDAD", "ENVIOS"],
            ascending=[False, False]
        )

        self.table(
            [
                "FLETERA", "ENVÍOS", "ENTREG.", "A TIEMPO",
                "% A TIEMPO", "RETRASO", "INCID.", "DÍAS PROM.",
                "COSTO", "COSTO/ENV."
            ],
            [
                [
                    r["FLETERA"],
                    integer(r["ENVIOS"]),
                    integer(r["ENTREGADOS"]),
                    integer(r["A_TIEMPO"]),
                    pct(r["EFECTIVIDAD"]),
                    integer(r["RETRASO"]),
                    pct(r["INCIDENCIAS"]),
                    f'{r["TRANSITO"]:.1f}',
                    money(r["COSTO"]),
                    money(r["COSTO_PROM"]),
                ]
                for _, r in ranking.iterrows()
            ],
            widths=[38 * mm, 18 * mm, 20 * mm, 20 * mm, 25 * mm,
                    20 * mm, 20 * mm, 20 * mm, 30 * mm, 30 * mm],
        )

    def efectividad_entregas(self, df):
        self.section_title("07 // EFECTIVIDAD DE ENTREGAS")

        entregados = int(df["_ENTREGADO"].sum())
        a_tiempo = int(df["_A_TIEMPO"].sum())
        retraso = max(entregados - a_tiempo, 0)

        self.kpi_grid([
            ("ENTREGADOS", integer(entregados)),
            ("A TIEMPO", integer(a_tiempo)),
            ("CON RETRASO", integer(retraso)),
            ("EFECTIVIDAD", pct(
                a_tiempo / entregados * 100 if entregados else 0
            )),
        ], columns=4)

        filas = (
            df[df["FLETERA"] != ""]
            .groupby("FLETERA", as_index=False)
            .agg(
                ENTREGADOS=("_ENTREGADO", "sum"),
                A_TIEMPO=("_A_TIEMPO", "sum"),
            )
        )

        filas["RETRASO"] = filas["ENTREGADOS"] - filas["A_TIEMPO"]
        filas["EFECTIVIDAD"] = (
            filas["A_TIEMPO"] / filas["ENTREGADOS"] * 100
        ).where(filas["ENTREGADOS"] > 0, 0)

        filas = filas.sort_values("EFECTIVIDAD", ascending=False)

        self.table(
            ["FLETERA", "ENTREGADOS", "A TIEMPO", "RETRASO", "% EFECTIVIDAD"],
            [
                [
                    r["FLETERA"],
                    integer(r["ENTREGADOS"]),
                    integer(r["A_TIEMPO"]),
                    integer(r["RETRASO"]),
                    pct(r["EFECTIVIDAD"]),
                ]
                for _, r in filas.iterrows()
            ],
            widths=[70 * mm, 28 * mm, 28 * mm, 28 * mm, 36 * mm],
        )

    def tiempos(self, df):
        self.section_title("08 // TIEMPOS DE TRÁNSITO")

        validos = df[
            df["_ENTREGADO"]
            & df["_DIAS_TRANSITO"].notna()
            & (df["_DIAS_TRANSITO"] >= 0)
        ].copy()

        if validos.empty:
            self.story.append(
                Paragraph(
                    "No existen entregas con fechas suficientes para calcular tránsito.",
                    self.body
                )
            )
            return

        promedio = validos["_DIAS_TRANSITO"].mean()
        minimo = validos["_DIAS_TRANSITO"].min()
        maximo = validos["_DIAS_TRANSITO"].max()
        mediana = validos["_DIAS_TRANSITO"].median()

        self.kpi_grid([
            ("TRÁNSITO PROMEDIO", f"{promedio:.1f} días"),
            ("MEDIANA", f"{mediana:.1f} días"),
            ("MÍNIMO", f"{int(minimo)} días"),
            ("MÁXIMO", f"{int(maximo)} días"),
        ], columns=4)

        por_fletera = (
            validos.groupby("FLETERA", as_index=False)
            .agg(
                ENTREGADOS=("_ENTREGADO", "sum"),
                DIAS_PROM=("_DIAS_TRANSITO", "mean"),
            )
            .sort_values("DIAS_PROM")
        )

        self.table(
            ["FLETERA", "ENTREGADOS", "TRÁNSITO PROMEDIO"],
            [
                [
                    r["FLETERA"],
                    integer(r["ENTREGADOS"]),
                    f'{r["DIAS_PROM"]:.1f} días',
                ]
                for _, r in por_fletera.iterrows()
            ],
            widths=[80 * mm, 35 * mm, 55 * mm],
        )

    def costo_promedio_paqueteria(self, df):
        self.section_title("09 // COSTO PROMEDIO POR PAQUETERÍA")

        resumen = (
            df[df["FLETERA"] != ""]
            .groupby("FLETERA", as_index=False)
            .agg(
                ENVIOS=("FLETERA", "size"),
                CAJAS=("CANTIDAD DE CAJAS", "sum"),
                COSTO=("_COSTO_LOGISTICO", "sum"),
            )
        )

        resumen["COSTO_PROM_ENVIO"] = (
            resumen["COSTO"] / resumen["ENVIOS"]
        ).where(resumen["ENVIOS"] > 0, 0)

        resumen["COSTO_PROM_CAJA"] = (
            resumen["COSTO"] / resumen["CAJAS"]
        ).where(resumen["CAJAS"] > 0, 0)

        resumen = resumen.sort_values("COSTO_PROM_ENVIO", ascending=False)

        self.table(
            [
                "PAQUETERÍA", "ENVÍOS", "CAJAS",
                "COSTO TOTAL", "COSTO / ENVÍO", "COSTO / CAJA"
            ],
            [
                [
                    r["FLETERA"],
                    integer(r["ENVIOS"]),
                    integer(r["CAJAS"]),
                    money(r["COSTO"]),
                    money(r["COSTO_PROM_ENVIO"]),
                    money(r["COSTO_PROM_CAJA"]),
                ]
                for _, r in resumen.iterrows()
            ],
            widths=[48 * mm, 20 * mm, 20 * mm, 35 * mm, 35 * mm, 35 * mm],
        )

    def costos_muestras(self, df_muestras, anio, mes):
        self.section_title("10 // COSTOS DE MUESTRAS")

        if df_muestras is None or df_muestras.empty:
            self.story.append(
                Paragraph(
                    "No se encontraron registros en la base de costos de muestras.",
                    self.body
                )
            )
            return

        df = df_muestras.copy()

        if "FECHA" not in df.columns:
            self.story.append(
                Paragraph(
                    "La base de muestras no contiene la columna FECHA requerida para el corte mensual.",
                    self.body
                )
            )
            return

        df["FECHA_DT"] = parse_fecha(df["FECHA"])

        df = df[
            (df["FECHA_DT"].dt.year == anio)
            & (df["FECHA_DT"].dt.month == mes)
        ].copy()

        if df.empty:
            self.story.append(
                Paragraph(
                    "No existen registros de muestras para el periodo seleccionado.",
                    self.body
                )
            )
            return

        df["COSTO_TOTAL"] = num(df["COSTO_TOTAL"]) if "COSTO_TOTAL" in df.columns else 0
        df["COSTO_GUIA"] = num(df["COSTO_GUIA"]) if "COSTO_GUIA" in df.columns else 0

        total_prod = df["COSTO_TOTAL"].sum()
        total_flete = df["COSTO_GUIA"].sum()
        total = total_prod + total_flete
        folios = len(df)
        despachados = (
            df["ESTATUS"].astype(str).str.upper().eq("DESPACHADO").sum()
            if "ESTATUS" in df.columns else 0
        )

        self.kpi_grid([
            ("FOLIOS", integer(folios)),
            ("COSTO PRODUCTO", money(total_prod)),
            ("FLETES", money(total_flete)),
            ("INVERSIÓN TOTAL", money(total)),
            ("COSTO PROM / FOLIO", money(total / folios if folios else 0)),
            ("% DESPACHADO", pct(despachados / folios * 100 if folios else 0)),
        ], columns=3)

        paq = "PAQUETERIA_NOMBRE"
        if paq not in df.columns:
            paq = "PAQUETERIA"

        if paq in df.columns:
            df[paq] = df[paq].fillna("").astype(str).str.upper().str.strip()

            resumen = (
                df[df[paq] != ""]
                .groupby(paq, as_index=False)
                .agg(
                    FOLIOS=(paq, "size"),
                    FLETE=("COSTO_GUIA", "sum"),
                )
                .sort_values("FLETE", ascending=False)
            )

            self.table(
                ["PAQUETERÍA", "FOLIOS", "FLETE", "FLETE / FOLIO"],
                [
                    [
                        r[paq],
                        integer(r["FOLIOS"]),
                        money(r["FLETE"]),
                        money(r["FLETE"] / r["FOLIOS"] if r["FOLIOS"] else 0),
                    ]
                    for _, r in resumen.iterrows()
                ],
                widths=[80 * mm, 30 * mm, 40 * mm, 40 * mm],
            )

        self.story.append(Paragraph("Detalle de inversión del periodo", self.h3))

        self.table(
            ["FOLIO", "FECHA", "DESTINO / HOTEL", "PAQUETERÍA", "PRODUCTO", "FLETE", "TOTAL"],
            [
                [
                    r.get("FOLIO", ""),
                    r["FECHA_DT"].strftime("%d/%m/%Y") if pd.notna(r["FECHA_DT"]) else "",
                    str(r.get("NOMBRE DEL HOTEL", ""))[:32],
                    str(r.get(paq, ""))[:20],
                    money(r.get("COSTO_TOTAL", 0)),
                    money(r.get("COSTO_GUIA", 0)),
                    money(r.get("COSTO_TOTAL", 0) + r.get("COSTO_GUIA", 0)),
                ]
                for _, r in df.sort_values("FECHA_DT").iterrows()
            ],
            widths=[18 * mm, 25 * mm, 55 * mm, 35 * mm, 30 * mm, 25 * mm, 30 * mm],
        )

    def construir(self, df, df_muestras):
        resumen = {
            "envios": len(df),
            "entregados": int(df["_ENTREGADO"].sum()),
            "efectividad_entrega": (
                df["_A_TIEMPO"].sum() / df["_ENTREGADO"].sum() * 100
                if df["_ENTREGADO"].sum() else 0
            ),
            "facturacion": df["FACTURACION"].sum(),
            "costo_logistico": df["_COSTO_LOGISTICO"].sum(),
        }

        self.portada(resumen)
        self.resumen_mes(df)
        self.story.append(PageBreak())

        self.efectividad_envios(df)
        self.story.append(PageBreak())

        self.inteligencia_negocio(df)
        self.story.append(PageBreak())

        self.top_clientes(df)
        self.story.append(PageBreak())

        self.distribucion_regreso(df)
        self.story.append(PageBreak())

        self.ranking_fleteras(df)
        self.story.append(PageBreak())

        self.efectividad_entregas(df)
        self.story.append(PageBreak())

        self.tiempos(df)
        self.story.append(PageBreak())

        self.costo_promedio_paqueteria(df)
        self.story.append(PageBreak())

        self.costos_muestras(df_muestras, df["FECHA DE ENVÍO"].dt.year.iloc[0], df["FECHA DE ENVÍO"].dt.month.iloc[0])

        self.doc.build(
            self.story,
            onFirstPage=self.page_header_footer,
            onLaterPages=self.page_header_footer,
        )


# ============================================================
# INTERFAZ MÍNIMA DE GENERACIÓN
# ============================================================

def main():
    st.markdown(
        """
        <style>
        .stApp { background:#384A52 !important; }
        .block-container { max-width:1100px; padding-top:40px; }
        h1,h2,h3,p,label { color:#FFFFFF !important; }
        div[data-testid="stDownloadButton"] button,
        div[data-testid="stButton"] button {
            background:#628290 !important;
            color:#FFFFFF !important;
            border:1px solid #628290 !important;
            border-radius:4px !important;
        }
        div[data-testid="stDownloadButton"] button:hover,
        div[data-testid="stButton"] button:hover {
            background:#4E6772 !important;
            border-color:#4E6772 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "## NEXION // REPORTE EJECUTIVO MENSUAL",
        unsafe_allow_html=True,
    )
    st.caption("Generador de PDF para Dirección · sin gráficas · métricas y tablas ejecutivas")

    df_raw = cargar_dashboard()

    if df_raw.empty:
        st.error("No fue posible cargar Matriz_Excel_Dashboard.csv.")
        return

    df = preparar_envios(df_raw)

    fechas_validas = df["FECHA DE ENVÍO"].dropna()

    if fechas_validas.empty:
        st.error("La base no contiene fechas válidas de envío.")
        return

    anios = sorted(fechas_validas.dt.year.unique().tolist(), reverse=True)

    c1, c2 = st.columns(2)

    with c1:
        anio = st.selectbox(
            "AÑO",
            anios,
            index=0,
        )

    with c2:
        mes_nombre = st.selectbox(
            "MES",
            MESES,
            index=datetime.now().month - 1,
        )

    mes = MESES.index(mes_nombre) + 1

    df_mes = obtener_periodo(df, anio, mes)

    # Filtros opcionales, sin cambiar el contenido del PDF base.
    c3, c4 = st.columns(2)

    with c3:
        paqueterias = sorted(
            [x for x in df_mes["FLETERA"].unique() if str(x).strip()]
        )
        filtro_paq = st.multiselect(
            "PAQUETERÍA / FLETERA",
            paqueterias,
            default=[],
        )

    with c4:
        clientes = sorted(
            [x for x in df_mes["NOMBRE DEL CLIENTE"].unique() if str(x).strip()]
        )
        filtro_cliente = st.multiselect(
            "CLIENTES",
            clientes,
            default=[],
        )

    df_reporte = df_mes.copy()

    if filtro_paq:
        df_reporte = df_reporte[df_reporte["FLETERA"].isin(filtro_paq)]

    if filtro_cliente:
        df_reporte = df_reporte[
            df_reporte["NOMBRE DEL CLIENTE"].isin(filtro_cliente)
        ]

    st.markdown(
        f"**PERIODO:** {mes_nombre} {anio} · "
        f"**REGISTROS:** {len(df_reporte):,}",
        unsafe_allow_html=True,
    )

    if df_reporte.empty:
        st.warning("No existen registros con los filtros seleccionados.")
        return

    if st.button(
        "GENERAR REPORTE EJECUTIVO PDF",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Construyendo reporte ejecutivo NEXION..."):
            df_muestras, _ = obtener_datos_github()

            buffer = io.BytesIO()

            reporte = ReportePDF(
                buffer,
                mes_nombre,
                anio,
            )

            # El PDF se construye con el mismo año/mes seleccionado.
            reporte.costos_muestras = reporte.costos_muestras

            reporte.story = []
            reporte.portada({
                "envios": len(df_reporte),
                "entregados": int(df_reporte["_ENTREGADO"].sum()),
                "efectividad_entrega": (
                    df_reporte["_A_TIEMPO"].sum()
                    / df_reporte["_ENTREGADO"].sum()
                    * 100
                    if df_reporte["_ENTREGADO"].sum() else 0
                ),
                "facturacion": df_reporte["FACTURACION"].sum(),
                "costo_logistico": df_reporte["_COSTO_LOGISTICO"].sum(),
            })

            reporte.resumen_mes(df_reporte)
            reporte.story.append(PageBreak())
            reporte.efectividad_envios(df_reporte)
            reporte.story.append(PageBreak())
            reporte.inteligencia_negocio(df_reporte)
            reporte.story.append(PageBreak())
            reporte.top_clientes(df_reporte)
            reporte.story.append(PageBreak())
            reporte.distribucion_regreso(df_reporte)
            reporte.story.append(PageBreak())
            reporte.ranking_fleteras(df_reporte)
            reporte.story.append(PageBreak())
            reporte.efectividad_entregas(df_reporte)
            reporte.story.append(PageBreak())
            reporte.tiempos(df_reporte)
            reporte.story.append(PageBreak())
            reporte.costo_promedio_paqueteria(df_reporte)
            reporte.story.append(PageBreak())
            reporte.costos_muestras(df_muestras, anio, mes)

            reporte.doc.build(
                reporte.story,
                onFirstPage=reporte.page_header_footer,
                onLaterPages=reporte.page_header_footer,
            )

            pdf_bytes = buffer.getvalue()

        st.success("Reporte ejecutivo generado correctamente.")

        st.download_button(
            "DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"NEXION_Reporte_Ejecutivo_{mes_nombre}_{anio}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
