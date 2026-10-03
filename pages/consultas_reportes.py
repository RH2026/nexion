"""
JYPESA | Reportes - CONSULTAS (arma tu reporte en pantalla y luego imprímelo)

Una sola página donde:
  1. FILTRAS: año(s), mes(es), cobro regreso / cobro destino, fletera, transporte, destino, cliente, concepto,
     número de cajas (1 a 4, 5 o más, rango), estatus de entrega, semáforo, % logístico mínimo, búsqueda por factura/cliente.
  2. ARMAS tu reporte marcando los bloques que quieras (la "ensalada"): tarjetas resumen, análisis por fletera / transporte /
     destino / cliente / modalidad / concepto / mes / nº de cajas / semáforo, pequeños vs grandes, pedido por pedido
     (de mayor a menor costo logístico), efectividad de entrega, costos extras, costos de muestras y tabla cruzada.
  3. LO VES en pantalla (tarjetas premium + tablas con encabezado fijo) y lo IMPRIMES: PDF de análisis (mismo estilo que el
     reporte mensual) o Excel con una hoja por tabla.

Usa las MISMAS matrices y reglas que reporte_mensual_pdf.py:
  - Matriz_Excel_Dashboard.csv (GitHub RH2026/nexion) y muestras_common.py (costos de muestras).
  - Recolecciones / maniobras (columna CONCEPTO) NO son pedidos: se muestran como costo extra aparte.
  - Periodo = columna MES + validación de año; modalidad = FORMA DE ENVIO contiene REGRESO / DESTINO.
  - % logístico = costo / facturación (target 7.5 %).
"""
import hashlib
import html as _html
import json
import time
import unicodedata
from datetime import datetime
from io import BytesIO

import numpy as np
import pandas as pd
import requests
import streamlit as st

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, NextPageTemplate, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

from components.layout import render_layout

try:
    from muestras_common import obtener_datos_github, precios as PRECIOS_MUESTRAS
    MUESTRAS_OK, MUESTRAS_ERR = True, ""
except Exception as _e_m:
    obtener_datos_github, PRECIOS_MUESTRAS = None, {}
    MUESTRAS_OK, MUESTRAS_ERR = False, str(_e_m)


# ============================================================
# 1. PÁGINA Y LAYOUT
# ============================================================
st.set_page_config(page_title="JYPESA | Reportes - Consultas", layout="wide", initial_sidebar_state="collapsed")
render_layout(modulo_actual="REPORTES", submodulo_actual="CONSULTAS")


# ============================================================
# 2. CONSTANTES
# ============================================================
GITHUB_USER, GITHUB_REPO, BRANCH = "RH2026", "nexion", "main"
ARCHIVO_MATRIZ = "Matriz_Excel_Dashboard.csv"
ARCHIVO_LOGO = "n1.png"

MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO",
         "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
TARGET = 7.5                    # % meta de costo logístico
EXTRA_REGEX = "RECOLECCI|MANIOBRA"
CLASES = ["SALUDABLE", "EN ALERTA", "CRÍTICO", "PÉRDIDA", "SIN FACTURACIÓN", "SIN DATOS"]
CLASES_FUERA = ["EN ALERTA", "CRÍTICO", "PÉRDIDA", "SIN FACTURACIÓN"]
ESTATUS = ["ENTREGADO A TIEMPO", "ENTREGADO CON RETRASO", "EN TRÁNSITO EN TIEMPO", "EN TRÁNSITO RETRASADO", "EN TRÁNSITO"]
SCREEN_MAX, PDF_MAX = 1500, 1200   # filas máximas por tabla en pantalla / PDF
TOPS = [5, 10, 15, 20, 30, 50, 100, "TODOS"]

HEX = dict(teal="#00A3A3", green="#2E9E6B", red="#D64545", blue="#3B82F6", gold="#FFC000", purple="#7C5CBF",
           orange="#E8833A", gray="#6B7A86", slate="#2B343B")
C_NAVY, C_SLATE, C_TEAL, C_GOLD = (colors.HexColor(x) for x in ("#384A52", "#2B343B", "#00A3A3", "#FFC000"))
C_GREEN, C_RED, C_GRAY = colors.HexColor("#2E9E6B"), colors.HexColor("#D64545"), colors.HexColor("#6B7A86")
C_LIGHT, C_BORDER, C_TEXT = colors.HexColor("#F3F6F8"), colors.HexColor("#D5DDE2"), colors.HexColor("#1F2D35")
C_AMBER = colors.HexColor("#C98A00")
TONO_COLOR = {"good": C_GREEN, "bad": C_RED, "warn": C_AMBER, "mute": C_GRAY, "": C_TEXT}

# Dimensiones para agrupar / cruzar: nombre -> columna interna
DIMS = {"Fletera": "_FLE", "Transporte": "_TR", "Destino": "_DE", "Cliente": "_CLI", "Modalidad (cobro)": "_MOD",
        "Concepto": "_CONC", "Mes": "_MESN", "Nº de cajas": "_CAJB", "Semáforo": "_CLASE",
        "Estatus de entrega": "_EST", "Año": "_ANIOT"}
NATURALES = {"_MESN", "_CAJB", "_CLASE", "_ANIOT"}      # dimensiones con orden propio (no por métrica)

# Métricas por las que se puede ordenar / graficar: etiqueta -> (clave, tipo de formato)
METRICAS = {"Costo logístico ($)": ("costo", "money"), "% logístico": ("pct_log", "pct2"),
            "Facturación": ("fact", "money"), "Pedidos": ("n", "int"), "Cajas": ("cajas", "int"),
            "Costo por caja": ("costo_caja", "money2"), "Exceso sobre target ($)": ("exceso", "money")}

SECCIONES = [  # (clave, nombre, descripción corta)
    ("kpi", "Tarjetas resumen", "Pedidos, facturación, costo, % logístico, extras, entregas"),
    ("peq", "Pequeños vs grandes", "Comparativo 1 a N cajas contra más de N (ignora el filtro de cajas)"),
    ("flet", "Por fletera", "Costo, % logístico y exceso por fletera"),
    ("tran", "Por transporte", "Por tipo de transporte"),
    ("dest", "Por destino", "Por destino"),
    ("clie", "Por cliente", "Por cliente"),
    ("moda", "Cobro regreso vs cobro destino", "Por modalidad de cobro"),
    ("conc", "Por concepto", "Por concepto del envío"),
    ("mes", "Por mes (tendencia)", "Mes a mes"),
    ("caja", "Por número de cajas", "1, 2, 3, 4, 5 o más…"),
    ("sema", "Semáforo de salud", "Saludable / alerta / crítico / pérdida"),
    ("rank", "Pedido por pedido", "Lista ordenada de mayor a menor costo logístico (o lo que elijas)"),
    ("entr", "Efectividad de entrega", "A tiempo, retrasos, días promedio e incidencias por fletera"),
    ("extr", "Costos extras", "Recolecciones y maniobras (no son pedidos)"),
    ("mues", "Costos de muestras", "Envíos de muestra: producto, flete e inversión"),
    ("cruz", "Tabla cruzada", "Elige filas, columnas y métrica"),
]
PRESETS = {"Ejecutivo": ["kpi", "peq", "flet", "mes", "sema", "extr"],
           "Costos": ["kpi", "flet", "tran", "dest", "clie", "rank", "extr"],
           "Todo": [k for k, _, _ in SECCIONES]}


# ============================================================
# 3. UTILIDADES
# ============================================================
def esc(t):
    return _html.escape("" if t is None else str(t))


def trunc(t, n):
    t = "" if t is None else str(t)
    return t if len(t) <= n else t[: n - 1] + "."


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t)) if unicodedata.category(c) != "Mn")


def isnum(v):
    try:
        return v is not None and not pd.isna(v)
    except Exception:
        return False


def parse_fecha_segura(serie):
    serie = pd.Series(serie)
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    s_txt = serie.fillna("").astype(str).str.strip()
    es_iso = s_txt.str.match(r"^\d{4}-\d{1,2}-\d{1,2}")

    def _conv(x, **kw):
        try:
            return pd.to_datetime(x, errors="coerce", format="mixed", **kw)
        except (TypeError, ValueError):
            return pd.to_datetime(x, errors="coerce", **kw)
    out = pd.Series(pd.NaT, index=s_txt.index, dtype="datetime64[ns]")
    if es_iso.any():
        out.loc[es_iso] = _conv(s_txt[es_iso]).astype("datetime64[ns]")
    if (~es_iso).any():
        out.loc[~es_iso] = _conv(s_txt[~es_iso], dayfirst=True).astype("datetime64[ns]")
    return out


def limpiar_moneda(serie):
    return pd.to_numeric(serie.astype(str).str.replace(r"[^\d\.\-]", "", regex=True).replace("", "0"),
                         errors="coerce").fillna(0.0)


def fmt(kind, v):
    """Formato único para pantalla y PDF. Devuelve (texto, tono) con tono en '', good, bad, warn, mute."""
    if kind in ("txt", "cls", "est", "docs"):
        s = "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
        tono = ""
        if kind == "cls":
            tono = {"SALUDABLE": "good", "EN ALERTA": "warn", "CRÍTICO": "bad", "PÉRDIDA": "bad"}.get(s, "mute")
        elif kind == "est":
            tono = "good" if s == "ENTREGADO A TIEMPO" else ("bad" if "RETRASO" in s or "RETRASADO" in s else "")
        return s, tono
    if kind == "date":
        return ("-", "mute") if not isnum(v) else (pd.Timestamp(v).strftime("%d/%m/%Y"), "")
    if not isnum(v):
        return "-", "mute"
    v = float(v)
    if kind == "int":
        return f"{v:,.0f}", ""
    if kind == "num1":
        return f"{v:,.1f}", ""
    if kind == "money":
        return f"${v:,.0f}", ""
    if kind == "money2":
        return f"${v:,.2f}", ""
    if kind == "pct":
        return f"{v:.1f}%", ""
    if kind == "pct2":
        return f"{v:.2f}%", ""
    if kind == "pctlog":
        return f"{v:.2f}%", ("good" if v <= TARGET else "bad")
    if kind == "vs":
        return f"{v:+.2f} pp", ("good" if v <= 0 else "bad")
    if kind == "pctok":   # efectividad: más es mejor
        return f"{v:.1f}%", ("good" if v >= 90 else ("warn" if v >= 80 else "bad"))
    return str(v), ""


# ============================================================
# 4. CARGA Y PREPARACIÓN (mismas reglas que reporte_mensual_pdf.py)
# ============================================================
def _headers_github():
    try:
        token = st.secrets.get("GITHUB_TOKEN", None)
    except Exception:
        token = None
    return {"Authorization": f"token {token}"} if token else {}


@st.cache_data(ttl=300)
def cargar_matriz():
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{ARCHIVO_MATRIZ}?v={int(time.time())}"
    try:
        r = requests.get(url, headers=_headers_github(), timeout=40)
        r.raise_for_status()
        df = pd.read_csv(BytesIO(r.content), encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(url, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    return df


@st.cache_data(ttl=3600)
def obtener_logo_bytes():
    try:
        import os
        if os.path.exists(ARCHIVO_LOGO):
            with open(ARCHIVO_LOGO, "rb") as f:
                return f.read()
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{ARCHIVO_LOGO}"
        r = requests.get(url, headers=_headers_github(), timeout=20)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None


def preparar_base(df_raw):
    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for c in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL", "EMISION"]:
        df[c] = parse_fecha_segura(df[c]) if c in df.columns else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    for c in ["FLETERA", "FORMA DE ENVIO", "TRANSPORTE", "DESTINO", "NOMBRE DEL CLIENTE", "INCIDENCIAS", "MES", "NÚMERO DE PEDIDO"]:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].fillna("").astype(str).str.strip()
        df.loc[df[c].str.lower() == "nan", c] = ""
    df["MES"] = df["MES"].str.upper()
    for c in ["COSTO DE LA GUÍA", "FACTURACION", "VALUACION", "COSTOS ADICIONALES", "CANTIDAD DE CAJAS"]:
        df[c] = limpiar_moneda(df[c]) if c in df.columns else 0.0
    df["CAJAS"] = pd.to_numeric(df["CAJAS"], errors="coerce").fillna(0) if "CAJAS" in df.columns else 0.0
    col_c = next((c for c in df.columns if "CONCEPTO" in str(c).upper()), None)
    if col_c:
        conc = df[col_c].fillna("").astype(str).map(sin_acentos).str.strip().str.upper()
        df["_CONC"] = conc.replace("", "SIN CONCEPTO")
        df["ES_EXTRA"] = conc.str.contains(EXTRA_REGEX, regex=True).astype(bool)
    else:
        df["_CONC"], df["ES_EXTRA"] = "SIN CONCEPTO", False
    return df


@st.cache_data(ttl=300)
def datos_base():
    return preparar_base(cargar_matriz())


def _col_factura(df):
    exactos = {"FACTURA", "NUMERO DE FACTURA", "NUMERO FACTURA", "NO FACTURA", "NO. FACTURA", "NUM FACTURA",
               "NUM. FACTURA", "FOLIO FACTURA", "FOLIO DE FACTURA", "N FACTURA"}
    for c in df.columns:
        if sin_acentos(c).strip().upper() in exactos:
            return c
    return "NÚMERO DE PEDIDO"


def preparar_universo(df, incluir_adic, hoy, max_peq):
    """Agrega a TODA la matriz las columnas de análisis (un renglón = un envío). Vectorizado."""
    u = df.copy()
    u["_CAJ"] = np.where(u["CANTIDAD DE CAJAS"] > 0, u["CANTIDAD DE CAJAS"], u["CAJAS"]).astype(float).round()
    u["_COSTO"] = u["COSTO DE LA GUÍA"] + (u["COSTOS ADICIONALES"] if incluir_adic else 0.0)
    fact, costo = u["FACTURACION"], u["_COSTO"]
    u["_PCT"] = costo / fact.where(fact > 0) * 100
    conds = [(fact <= 0) & (costo <= 0), fact <= 0, u["_PCT"] >= 100, u["_PCT"] > 2 * TARGET, u["_PCT"] > TARGET]
    u["_CLASE"] = np.select(conds, ["SIN DATOS", "SIN FACTURACIÓN", "PÉRDIDA", "CRÍTICO", "EN ALERTA"], default="SALUDABLE")
    u["_EXC"] = (costo - TARGET / 100 * fact).clip(lower=0)
    u["_FUERA"] = u["_CLASE"].isin(CLASES_FUERA)
    u["_CPC"] = costo / u["_CAJ"].where(u["_CAJ"] > 0)
    u["_MOD"] = u["FORMA DE ENVIO"].str.upper().map(
        lambda x: "COBRO REGRESO" if "REGRESO" in x else ("COBRO DESTINO" if "DESTINO" in x else (x or "SIN FORMA")))
    u["_DE"] = u["DESTINO"].str.upper().replace("", "SIN DESTINO")
    u["_TR"] = u["TRANSPORTE"].str.upper().replace("", "SIN TRANSPORTE")
    u["_FLE"] = u["FLETERA"].str.upper().replace("", "SIN ASIGNAR")
    u["_CLI"] = u["NOMBRE DEL CLIENTE"].replace("", "SIN CLIENTE")
    col_f = _col_factura(u)
    u["_FAC"] = u[col_f].fillna("").astype(str).str.strip().replace("nan", "")
    u["_PED"] = u["NÚMERO DE PEDIDO"].fillna("").astype(str).str.strip().replace("nan", "")
    u["_DOC"] = u["_FAC"].where(u["_FAC"] != "", u["_PED"])      # factura; si no hay, número de pedido
    # cajas en etiquetas con orden natural
    cap = max_peq + 1
    n = np.minimum(u["_CAJ"], cap).astype(int)
    u["_CAJN"] = n
    u["_CAJB"] = np.where(n < 1, "SIN CAJAS", np.where(n >= cap, f"{cap}+ CAJAS", n.astype(str) + np.where(n == 1, " CAJA", " CAJAS")))
    # fechas / mes / año
    u["_ANIO"] = u["FECHA DE ENVÍO"].dt.year.fillna(0).astype(int)
    u["_ANIOT"] = np.where(u["_ANIO"] > 0, u["_ANIO"].astype(str), "S/F")
    u["_MESN"] = u["MES"].replace("", "SIN MES").str.title()
    # entrega
    ent = u["FECHA DE ENTREGA REAL"].notna()
    prom = u["PROMESA DE ENTREGA"]
    u["_ENT"] = ent
    u["_ATIEMPO"] = ent & (prom.isna() | (u["FECHA DE ENTREGA REAL"] <= prom))
    u["_RETR_TR"] = (~ent) & prom.notna() & (prom < hoy)
    u["_EST"] = np.select(
        [ent & u["_ATIEMPO"], ent, (~ent) & prom.notna() & (prom >= hoy), u["_RETR_TR"]],
        ESTATUS[:4], default="EN TRÁNSITO")
    d_ent = (u["FECHA DE ENTREGA REAL"] - u["FECHA DE ENVÍO"]).dt.days
    u["_DIAS"] = d_ent.where(ent & (d_ent >= 0))
    u["_INC"] = ~u["INCIDENCIAS"].astype(str).str.strip().str.upper().isin(["", "OK"])
    return u


# ============================================================
# 5. FILTROS
# ============================================================
def aplicar_filtros(u, f):
    """u: universo preparado. f: dict de filtros. Devuelve (d, ext, d_sin_cajas)."""
    ok_anio = u["FECHA DE ENVÍO"].isna() | u["_ANIO"].isin(f["anios"])
    ok_mes = u["MES"].isin([MESES[m - 1] for m in f["meses"]]) if f["meses"] else (u["MES"] != "")
    m = ok_anio & ok_mes
    if f["modalidad"] != "TODAS":
        m &= u["_MOD"] == f["modalidad"]
    for k, col in (("fleteras", "_FLE"), ("transportes", "_TR"), ("destinos", "_DE"), ("conceptos", "_CONC")):
        if f[k]:
            m &= u[col].isin(f[k])
    ext = u[m & u["ES_EXTRA"]].copy()

    p = m & ~u["ES_EXTRA"]
    if f["clientes"]:
        p &= u["_CLI"].isin(f["clientes"])
    if f["estatus"]:
        p &= u["_EST"].isin(f["estatus"])
    if f["clases"]:
        p &= u["_CLASE"].isin(f["clases"])
    if f["pct_min"] and f["pct_min"] > 0:
        p &= u["_PCT"] > f["pct_min"]
    if f["solo_fuera"]:
        p &= u["_FUERA"]
    if f["buscar"]:
        b = sin_acentos(f["buscar"]).upper()
        txt = (u["_FAC"] + " " + u["_CLI"] + " " + u["NÚMERO DE PEDIDO"]).map(lambda x: sin_acentos(x).upper())
        p &= txt.str.contains(b, regex=False)
    d0 = u[p].copy()

    modo, n = f["cajas_modo"], f["max_peq"]
    if modo == "PEQUEÑOS":
        mc = (d0["_CAJ"] >= 1) & (d0["_CAJ"] <= n)
    elif modo == "GRANDES":
        mc = d0["_CAJ"] > n
    elif modo == "RANGO":
        mc = d0["_CAJ"] >= f["caj_min"]
        if f["caj_max"] > 0:
            mc &= d0["_CAJ"] <= f["caj_max"]
    else:
        mc = pd.Series(True, index=d0.index)
    return d0[mc].copy(), ext, d0


def texto_filtros(f):
    per = ("AÑO " + ", ".join(str(a) for a in f["anios"])) if not f["meses"] else \
        f"{', '.join(MESES[m - 1].title() for m in f['meses'])} {', '.join(str(a) for a in f['anios'])}"
    if not f["meses"]:
        per += " (acumulado)"

    def lst(x):
        return ", ".join(x) if len(x) <= 3 else f"{len(x)} seleccionados"
    p = [per, "Todas las modalidades" if f["modalidad"] == "TODAS" else f["modalidad"].title()]
    n = f["max_peq"]
    cj = {"PEQUEÑOS": f"1 a {n} cajas", "GRANDES": f"{n + 1} o más cajas",
          "RANGO": f"{f['caj_min']} a {f['caj_max'] or 'más'} cajas"}.get(f["cajas_modo"])
    if cj:
        p.append(cj)
    for lab, k in (("Fletera", "fleteras"), ("Transporte", "transportes"), ("Destino", "destinos"),
                   ("Cliente", "clientes"), ("Concepto", "conceptos"), ("Entrega", "estatus"), ("Semáforo", "clases")):
        if f[k]:
            p.append(f"{lab}: {lst(f[k])}")
    if f["pct_min"]:
        p.append(f"% log. > {f['pct_min']}")
    if f["solo_fuera"]:
        p.append("solo fuera de target")
    if f["buscar"]:
        p.append(f"búsqueda: {f['buscar']}")
    p.append("costo = " + ("guía + adicionales" if f["incluir_adic"] else "solo guía"))
    return "  ·  ".join(p)


# ============================================================
# 6. CÁLCULOS: agrupaciones
# ============================================================
def _derivar(r, costo_total=None):
    r = r.copy()
    r["pct_log"] = r["costo"] / r["fact"].where(r["fact"] > 0) * 100
    r["vs"] = r["pct_log"] - TARGET
    r["costo_caja"] = r["costo"] / r["cajas"].where(r["cajas"] > 0)
    r["costo_ped"] = r["costo"] / r["n"].where(r["n"] > 0)
    tot = costo_total if costo_total is not None else r["costo"].sum()
    r["pct_gasto"] = r["costo"] / tot * 100 if tot else np.nan
    r["pct_fuera"] = r["fuera"] / r["n"].where(r["n"] > 0) * 100
    r["pct_tiempo"] = r["atiempo"] / r["ent"].where(r["ent"] > 0) * 100
    r["ticket"] = r["fact"] / r["n"].where(r["n"] > 0)
    r["ticket_min"] = r["costo_ped"] / (TARGET / 100)
    return r


def agrupar(d, col):
    g = d.groupby(col, dropna=False).agg(
        n=("_COSTO", "size"), cajas=("_CAJ", "sum"), fact=("FACTURACION", "sum"), guia=("COSTO DE LA GUÍA", "sum"),
        adic=("COSTOS ADICIONALES", "sum"), costo=("_COSTO", "sum"), exceso=("_EXC", "sum"), fuera=("_FUERA", "sum"),
        ent=("_ENT", "sum"), atiempo=("_ATIEMPO", "sum"), retr=("_RETR_TR", "sum"), inc=("_INC", "sum"),
        dias=("_DIAS", "mean")).reset_index().rename(columns={col: "K"})
    return _derivar(g)


def total_de(r):
    s = {c: r[c].sum() for c in ("n", "cajas", "fact", "guia", "adic", "costo", "exceso", "fuera", "ent", "atiempo", "retr", "inc")}
    t = _derivar(pd.DataFrame([s]), costo_total=s["costo"]).iloc[0].to_dict()
    t["K"] = "TOTAL"
    return t


def lista_docs(serie, corto=4):
    """Facturas / pedidos únicos de un grupo: (texto corto para tabla, texto completo)."""
    v = sorted({str(x).strip() for x in serie if str(x).strip() not in ("", "nan")})
    if not v:
        return "-", "-"
    full = ", ".join(v)
    return (", ".join(v[:corto]) + (f"  +{len(v) - corto} más" if len(v) > corto else "")), full


def agregar_docs(filas, d, col, key="docs", kcol="K"):
    """Agrega a cada fila agrupada sus facturas/pedidos (o folios) para rastreo."""
    mapa = {k: lista_docs(g) for k, g in d.groupby(col)["_DOC"]}
    for r in filas:
        corto, full = mapa.get(r[kcol], ("-", "-"))
        r[key], r[key + "_full"] = corto, full
    return filas


def _filas(df):
    return df.replace({np.nan: None}).to_dict("records")


# ============================================================
# 7. BLOQUES (elementos neutrales que se dibujan en pantalla y en PDF)
#    ("kpis", [(etiqueta, valor_texto, tono_color, subtexto)])
#    ("table", dict(title, cols=[(hdr,key,kind,align,wide_only)], rows, total, note, landscape))
#    ("bars", dict(title, items=[(label, valor, color_tono)], kind))
#    ("note", texto)
# ============================================================
def E_kpis(items):
    return ("kpis", items)


def E_table(title, cols, rows, total=None, note="", landscape=False):
    return ("table", dict(title=title, cols=cols, rows=rows, total=total, note=note, landscape=landscape))


def E_bars(title, items, kind):
    return ("bars", dict(title=title, items=items, kind=kind))


def E_note(t):
    return ("note", t)


def _cols_grupo(nombre_dim, kind_k="txt"):
    return [(nombre_dim, "K", kind_k, "L", False), ("PEDIDOS", "n", "int", "R", False), ("CAJAS", "cajas", "int", "R", False),
            ("FACTURACIÓN", "fact", "money", "R", False), ("GUÍA", "guia", "money", "R", True),
            ("ADIC.", "adic", "money", "R", True), ("COSTO", "costo", "money", "R", False),
            ("% LOG.", "pct_log", "pctlog", "R", False), ("VS TARGET", "vs", "vs", "R", False),
            ("COSTO/CAJA", "costo_caja", "money2", "R", False), ("COSTO/PED.", "costo_ped", "money2", "R", True),
            ("% GASTO", "pct_gasto", "pct", "R", True), ("EXCESO $", "exceso", "money", "R", False),
            ("% FUERA", "pct_fuera", "pct", "R", True)]


def _orden_tabla(r, col, ctx):
    """Ordena un agrupado: orden natural para meses/cajas/semáforo, o por la métrica elegida."""
    o = ctx["opts"]
    if col == "_MESN":
        orden = {m.title(): i for i, m in enumerate(MESES)}
        return r.assign(_o=r["K"].map(orden).fillna(99)).sort_values("_o").drop(columns="_o")
    if col == "_CAJB":
        return r.assign(_o=r["K"].map(lambda x: 0 if x == "SIN CAJAS" else int(str(x).split("+")[0].split(" ")[0]))).sort_values("_o").drop(columns="_o")
    if col == "_CLASE":
        return r.assign(_o=r["K"].map(lambda x: CLASES.index(x) if x in CLASES else 99)).sort_values("_o").drop(columns="_o")
    if col == "_ANIOT":
        return r.sort_values("K")
    key = METRICAS[o["orden_met"]][0]
    return r.sort_values(key, ascending=(o["orden_dir"] == "MENOR A MAYOR"), na_position="last")


def sec_dim(ctx, titulo, dim, d=None, con_top=True):
    d = ctx["d"] if d is None else d
    col = DIMS[dim]
    if d.empty:
        return [E_note("Sin pedidos con los filtros elegidos.")]
    r = agrupar(d, col)
    tot = total_de(r)
    r = _orden_tabla(r, col, ctx)
    nat = col in NATURALES
    top = ctx["opts"]["top"]
    mostrados = r if (nat or top == "TODOS" or not con_top) else r.head(int(top))
    nota = f"Mostrando {len(mostrados)} de {len(r)} · ordenado por {ctx['opts']['orden_met'].lower()}" if len(mostrados) < len(r) else ""
    kind_k = "cls" if col == "_CLASE" else ("est" if col == "_EST" else "txt")
    cols_g, filas_g = _cols_grupo(dim.upper(), kind_k), _filas(mostrados)
    if col == "_CLI":     # trazabilidad: factura(s) / pedido(s) de cada cliente
        filas_g = agregar_docs(filas_g, d, col)
        cols_g.insert(1, ("FACTURA / PEDIDO", "docs", "docs", "L", False))
    out = [E_table(titulo, cols_g, filas_g, total=tot, note=nota)]
    # gráfica de la métrica elegida (top 12 o natural)
    mkey, mkind = METRICAS[ctx["opts"]["orden_met"]]
    gb = mostrados.head(12) if not nat or len(mostrados) <= 12 else mostrados.head(12)
    items = []
    for _, x in gb.iterrows():
        v = x[mkey]
        if not isnum(v):
            continue
        if mkey == "pct_log":
            tono = "green" if v <= TARGET else "red"
        elif col == "_CLASE":
            tono = {"SALUDABLE": "green", "EN ALERTA": "gold", "CRÍTICO": "orange", "PÉRDIDA": "red"}.get(x["K"], "gray")
        else:
            tono = "teal"
        items.append((str(x["K"]), float(v), tono))
    if items:
        out.append(E_bars(f"{ctx['opts']['orden_met']} · {dim}", items, mkind))
    return out


def sec_kpi(ctx):
    d, ext = ctx["d"], ctx["ext"]
    if d.empty and ext.empty:
        return [E_note("Sin información con los filtros elegidos.")]
    n, cajas, fact = len(d), d["_CAJ"].sum(), d["FACTURACION"].sum()
    guia, adic, costo = d["COSTO DE LA GUÍA"].sum(), d["COSTOS ADICIONALES"].sum(), d["_COSTO"].sum()
    c_ext = (ext["COSTO DE LA GUÍA"] + ext["COSTOS ADICIONALES"]).sum() if len(ext) else 0.0
    pct = costo / fact * 100 if fact > 0 else np.nan
    pct_t = (costo + c_ext) / fact * 100 if fact > 0 else np.nan
    ent, at = int(d["_ENT"].sum()), int(d["_ATIEMPO"].sum())
    fuera, exc = int(d["_FUERA"].sum()), d["_EXC"].sum()
    tono = lambda v: "green" if isnum(v) and v <= TARGET else "red"
    txt = lambda k, v: fmt(k, v)[0]
    fila1 = [("Pedidos", txt("int", n), "blue", f"{txt('int', cajas)} cajas"),
             ("Facturación", txt("money", fact), "green", f"ticket prom. {txt('money', fact / n if n else np.nan)}"),
             ("Costo logístico", txt("money", costo), "slate", f"guía {txt('money', guia)} · adic. {txt('money', adic)}"),
             (f"% logístico (target {TARGET}%)", txt("pct2", pct), tono(pct), f"{pct - TARGET:+.2f} pp vs target" if isnum(pct) else "")]
    fila2 = [("Costo por caja", txt("money2", costo / cajas if cajas else np.nan), "orange", ""),
             ("Costo por pedido", txt("money2", costo / n if n else np.nan), "purple", ""),
             ("Costos extras", txt("money", c_ext), "gold", f"{len(ext)} registros · % log. total {txt('pct2', pct_t)}"),
             ("Fuera de target", f"{fuera} de {n}", "red" if fuera else "green", f"exceso pagado {txt('money', exc)}"),
             ("Entregados", txt("int", ent), "teal", f"{(ent / n * 100 if n else 0):.1f}% del total"),
             ("Entregas a tiempo", txt("pct", at / ent * 100 if ent else np.nan), "green" if ent and at / ent >= .9 else "gold",
              f"{at} de {ent}")]
    return [E_kpis(fila1), E_kpis(fila2)]


def sec_peq(ctx):
    d0, n = ctx["d_nocaj"], ctx["f"]["max_peq"]
    d0 = d0[d0["_CAJ"] >= 1]
    if d0.empty:
        return [E_note("Sin pedidos con cajas registradas.")]
    peq, gra = d0[d0["_CAJ"] <= n], d0[d0["_CAJ"] > n]
    filas, tot_costo = [], d0["_COSTO"].sum()
    for lab, g in ((f"1 A {n} CAJAS (PEQUEÑOS)", peq), (f"{n + 1} O MÁS CAJAS (GRANDES)", gra), ("TOTAL", d0)):
        if g.empty:
            continue
        r = _derivar(pd.DataFrame([dict(n=len(g), cajas=g["_CAJ"].sum(), fact=g["FACTURACION"].sum(), guia=g["COSTO DE LA GUÍA"].sum(),
                                        adic=g["COSTOS ADICIONALES"].sum(), costo=g["_COSTO"].sum(), exceso=g["_EXC"].sum(),
                                        fuera=g["_FUERA"].sum(), ent=g["_ENT"].sum(), atiempo=g["_ATIEMPO"].sum(), retr=0, inc=0, dias=0)]),
                     costo_total=tot_costo).iloc[0].to_dict()
        r["K"] = lab
        r["pct_ped"] = r["n"] / len(d0) * 100
        r["pct_bajo"] = (g["FACTURACION"] < r["ticket_min"]).mean() * 100
        filas.append(r)
    cols = [("GRUPO", "K", "txt", "L", False), ("PEDIDOS", "n", "int", "R", False), ("% PEDIDOS", "pct_ped", "pct", "R", False),
            ("CAJAS", "cajas", "int", "R", False), ("FACTURACIÓN", "fact", "money", "R", False), ("COSTO", "costo", "money", "R", False),
            ("% LOG.", "pct_log", "pctlog", "R", False), ("COSTO/CAJA", "costo_caja", "money2", "R", False),
            ("COSTO/PED.", "costo_ped", "money2", "R", False), ("TICKET PROM.", "ticket", "money", "R", True),
            ("TICKET MÍN. TARGET", "ticket_min", "money", "R", True), ("% BAJO MÍNIMO", "pct_bajo", "pct", "R", True),
            ("EXCESO $", "exceso", "money", "R", False)]
    out = []
    if not peq.empty:
        p = filas[0]
        out.append(E_kpis([("Pedidos pequeños", fmt("int", p["n"])[0], "blue", f"{p['pct_ped']:.1f}% de los pedidos"),
                           ("% logístico pequeños", fmt("pct2", p["pct_log"])[0], "green" if isnum(p["pct_log"]) and p["pct_log"] <= TARGET else "red",
                            f"target {TARGET}%"),
                           ("Ticket mínimo para estar en target", fmt("money", p["ticket_min"])[0], "gold", f"ticket actual {fmt('money', p['ticket'])[0]}"),
                           ("Exceso pagado (pequeños)", fmt("money", p["exceso"])[0], "red", "sobre el target")]))
    out.append(E_table("Pequeños vs grandes", cols, [x for x in filas[:-1]], total=filas[-1],
                       note=f"Pequeño = de 1 a {n} cajas. El filtro de cajas no aplica a este bloque; los demás filtros sí."))
    out += sec_dim(ctx, "Detalle por número de cajas", "Nº de cajas", d=d0)
    return out


COLS_RANK = [("FACTURA", "_FAC", "txt", "L", False), ("PEDIDO", "_PED", "txt", "L", True),
             ("CLIENTE", "_CLI", "txt", "L", False), ("FECHA", "FECHA DE ENVÍO", "date", "L", False), ("DESTINO", "_DE", "txt", "L", False), ("CJ.", "_CAJ", "int", "R", False),
             ("COBRO", "_MODC", "txt", "L", False), ("TRANSPORTE", "_TR", "txt", "L", False), ("FLETERA", "_FLE", "txt", "L", True),
             ("FACTURACIÓN", "FACTURACION", "money", "R", False), ("GUÍA", "COSTO DE LA GUÍA", "money", "R", True),
             ("ADIC.", "COSTOS ADICIONALES", "money", "R", True), ("COSTO", "_COSTO", "money", "R", False),
             ("% LOG.", "_PCT", "pctlog", "R", False), ("VS TGT", "_VS", "vs", "R", False),
             ("EXCESO $", "_EXC", "money", "R", False), ("SEMÁFORO", "_CLASE", "cls", "L", False),
             ("ENTREGA", "_EST", "est", "L", True)]
ORDEN_RANK = {"% logístico": "_PCT", "Costo logístico ($)": "_COSTO", "Exceso sobre target ($)": "_EXC", "Facturación": "FACTURACION",
              "Costo por caja": "_CPC", "Cajas": "_CAJ", "Fecha de envío": "FECHA DE ENVÍO"}


def sec_rank(ctx):
    d, o = ctx["d"], ctx["opts"]
    if d.empty:
        return [E_note("Sin pedidos con los filtros elegidos.")]
    r = d.copy()
    r["_MODC"] = r["_MOD"].map({"COBRO REGRESO": "REGRESO", "COBRO DESTINO": "DESTINO"}).fillna(r["_MOD"])
    r["_VS"] = r["_PCT"] - TARGET
    r = r.sort_values(ORDEN_RANK[o["rank_orden"]], ascending=(o["rank_dir"] == "MENOR A MAYOR"), na_position="last")
    total_n = len(r)
    top = o["rank_top"]
    sel = r if top == "TODOS" else r.head(int(top))
    sel = sel.head(SCREEN_MAX)
    cols_rank = COLS_RANK if (sel["_PED"] != sel["_FAC"]).any() else [c for c in COLS_RANK if c[1] != "_PED"]
    rows = sel[[c[1] for c in cols_rank]].replace({np.nan: None, pd.NaT: None}).to_dict("records")
    tot = dict(_FAC="TOTAL", _CAJ=sel["_CAJ"].sum(), FACTURACION=sel["FACTURACION"].sum(), **{"COSTO DE LA GUÍA": sel["COSTO DE LA GUÍA"].sum(),
               "COSTOS ADICIONALES": sel["COSTOS ADICIONALES"].sum()}, _COSTO=sel["_COSTO"].sum(),
               _PCT=(sel["_COSTO"].sum() / sel["FACTURACION"].sum() * 100) if sel["FACTURACION"].sum() > 0 else None,
               _EXC=sel["_EXC"].sum())
    tot["_VS"] = tot["_PCT"] - TARGET if tot["_PCT"] is not None else None
    nota = (f"Mostrando {len(sel)} de {total_n} pedidos · ordenado por {o['rank_orden'].lower()} ({o['rank_dir'].lower()}). "
            f"Pedidos = envíos sin recolecciones/maniobras.")
    return [E_table(f"Pedido por pedido · {o['rank_orden']}", cols_rank, rows, total=tot, note=nota, landscape=True)]


def sec_entr(ctx):
    d = ctx["d"]
    if d.empty:
        return [E_note("Sin pedidos con los filtros elegidos.")]
    r = agrupar(d, "_FLE")
    tot = total_de(r)
    r["trans"], tot["trans"] = r["n"] - r["ent"], tot["n"] - tot["ent"]
    r["retraso"], tot["retraso"] = r["ent"] - r["atiempo"], tot["ent"] - tot["atiempo"]
    r["pct_inc"], tot["pct_inc"] = r["inc"] / r["n"] * 100, tot["inc"] / tot["n"] * 100 if tot["n"] else None
    tot["dias"] = d["_DIAS"].mean()
    r = r.sort_values("pct_tiempo", ascending=False, na_position="last")
    cols = [("FLETERA", "K", "txt", "L", False), ("PEDIDOS", "n", "int", "R", False), ("ENTREGADOS", "ent", "int", "R", False),
            ("A TIEMPO", "atiempo", "int", "R", False), ("CON RETRASO", "retraso", "int", "R", False),
            ("% A TIEMPO", "pct_tiempo", "pctok", "R", False), ("EN TRÁNSITO", "trans", "int", "R", False),
            ("TRÁNSITO RETRASADO", "retr", "int", "R", True), ("DÍAS PROM.", "dias", "num1", "R", False),
            ("% INCIDENCIAS", "pct_inc", "pct", "R", False)]
    items = [(str(x.K), float(x.pct_tiempo), "green" if x.pct_tiempo >= 90 else ("gold" if x.pct_tiempo >= 80 else "red"))
             for x in r.itertuples() if isnum(x.pct_tiempo)][:12]
    out = [E_table("Efectividad de entrega por fletera", cols, _filas(r), total=tot,
                   note="Semáforo de % a tiempo: verde ≥ 90 %, ámbar ≥ 80 %, rojo menor. A tiempo = entrega real ≤ promesa.")]
    if items:
        out.append(E_bars("% de entregas a tiempo por fletera", items, "pct"))
    return out


def sec_extr(ctx):
    ext = ctx["ext"]
    if ext.empty:
        return [E_note("No hay recolecciones ni maniobras con los filtros elegidos.")]
    e = ext.assign(_ECOSTO=ext["COSTO DE LA GUÍA"] + ext["COSTOS ADICIONALES"])
    costo_ped = ctx["d"]["_COSTO"].sum()
    fact = ctx["d"]["FACTURACION"].sum()
    tot = e["_ECOSTO"].sum()
    out = [E_kpis([("Costo extra total", fmt("money", tot)[0], "gold", f"{len(e)} registros"),
                   ("% del costo logístico total", fmt("pct", tot / (tot + costo_ped) * 100 if tot + costo_ped else np.nan)[0], "orange", ""),
                   ("% logístico solo pedidos", fmt("pct2", costo_ped / fact * 100 if fact > 0 else np.nan)[0], "teal", ""),
                   ("% logístico con extras", fmt("pct2", (costo_ped + tot) / fact * 100 if fact > 0 else np.nan)[0],
                    "green" if fact > 0 and (costo_ped + tot) / fact * 100 <= TARGET else "red", f"target {TARGET}%")])]
    for titulo, col in (("Costos extras por concepto", "_CONC"), ("Costos extras por fletera", "_FLE")):
        g = e.groupby(col).agg(n=("_ECOSTO", "size"), guia=("COSTO DE LA GUÍA", "sum"), adic=("COSTOS ADICIONALES", "sum"),
                               costo=("_ECOSTO", "sum")).reset_index().sort_values("costo", ascending=False)
        g["pct"] = g["costo"] / tot * 100 if tot else np.nan
        cols = [(col.strip("_").replace("CONC", "CONCEPTO").replace("FLE", "FLETERA"), col, "txt", "L", False), ("REGISTROS", "n", "int", "R", False),
                ("GUÍA", "guia", "money", "R", False), ("ADIC.", "adic", "money", "R", False), ("COSTO", "costo", "money", "R", False),
                ("% DEL EXTRA", "pct", "pct", "R", False)]
        out.append(E_table(titulo, cols, _filas(g), total=dict(**{col: "TOTAL"}, n=len(e), guia=e["COSTO DE LA GUÍA"].sum(),
                                                               adic=e["COSTOS ADICIONALES"].sum(), costo=tot, pct=100.0)))
    return out


# --- Muestras ---------------------------------------------------------------
@st.cache_data(ttl=300)
def datos_muestras():
    """Devuelve (df_preparado | None, mensaje)."""
    if not MUESTRAS_OK:
        return None, f"No se pudo importar muestras_common: {MUESTRAS_ERR}"
    try:
        df_m, _sha = obtener_datos_github()
    except Exception as e:
        return None, f"No se pudo leer el registro de muestras: {e}"
    if df_m is None or df_m.empty:
        return None, "No hay registros de muestras cargados."
    d = df_m.copy()
    for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL", "ESTATUS", "SOLICITO",
                "NOMBRE DEL HOTEL", "FOLIO", "FECHA"]:
        if col not in d.columns:
            d[col] = "NO SURTIDO" if col == "ESTATUS" else (0.0 if col in ("COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL") else "")
    d["FECHA_DT"] = parse_fecha_segura(d["FECHA"].astype(str).str.strip())
    d["COSTO_TOTAL"] = pd.to_numeric(d["COSTO_TOTAL"], errors="coerce").fillna(0)
    d["COSTO_GUIA"] = pd.to_numeric(d["COSTO_GUIA"], errors="coerce").fillna(0)
    d["INVERSION"] = d["COSTO_TOTAL"] + d["COSTO_GUIA"]
    d["_SOL"] = d["SOLICITO"].astype(str).str.upper().replace("", "SIN DATO")
    col_paq = "PAQUETERIA_NOMBRE" if "PAQUETERIA_NOMBRE" in d.columns else "PAQUETERIA"
    d["_PAQ"] = d[col_paq].astype(str).str.upper().replace({"": "SIN ASIGNAR", "0.0": "SIN ASIGNAR", "NAN": "SIN ASIGNAR"})
    d["_HOT"] = d["NOMBRE DEL HOTEL"].astype(str).str.upper().replace("", "SIN DATO")
    d["_STAT"] = d["ESTATUS"].astype(str).str.upper()
    return d, ""


def sec_mues(ctx):
    dm, msg = datos_muestras()
    if dm is None:
        return [E_note(f"Costos de muestras sin datos: {msg}")]
    f, o = ctx["f"], ctx["opts"]
    m = dm["FECHA_DT"].dt.year.isin(f["anios"])
    if f["meses"]:
        m &= dm["FECHA_DT"].dt.month.isin(f["meses"])
    if o["mu_sol"]:
        m &= dm["_SOL"].isin(o["mu_sol"])
    d = dm[m].copy()
    if d.empty:
        return [E_note("No hay muestras en el periodo elegido (se usan los mismos mes y año del filtro general).")]
    n, prod, flete, inv = len(d), d["COSTO_TOTAL"].sum(), d["COSTO_GUIA"].sum(), d["INVERSION"].sum()
    desp = (d["_STAT"] == "DESPACHADO").mean() * 100
    out = [E_kpis([("Envíos de muestra", fmt("int", n)[0], "blue", f"{desp:.0f}% despachado"),
                   ("Costo de producto", fmt("money", prod)[0], "purple", ""),
                   ("Costo de flete", fmt("money", flete)[0], "orange", ""),
                   ("Inversión total", fmt("money", inv)[0], "red", f"prom. {fmt('money', inv / n)[0]} por envío")])]

    def grp(col, titulo, nombre):
        g = d.groupby(col).agg(envios=("INVERSION", "size"), prod=("COSTO_TOTAL", "sum"), flete=("COSTO_GUIA", "sum"),
                               inv=("INVERSION", "sum")).reset_index().sort_values("inv", ascending=False)
        g["prom"] = g["inv"] / g["envios"]
        g["pct"] = g["inv"] / inv * 100 if inv else np.nan
        top = o["top"]
        gm = g if top == "TODOS" else g.head(int(top))
        cols = [(nombre, col, "txt", "L", False), ("ENVÍOS", "envios", "int", "R", False), ("PRODUCTO", "prod", "money", "R", False),
                ("FLETE", "flete", "money", "R", False), ("INVERSIÓN", "inv", "money", "R", False),
                ("PROM./ENVÍO", "prom", "money", "R", False), ("% DEL TOTAL", "pct", "pct", "R", False)]
        tot = dict(**{col: "TOTAL"}, envios=n, prod=prod, flete=flete, inv=inv, prom=inv / n, pct=100.0)
        filas_m = _filas(gm)
        if col == "_HOT":     # trazabilidad: folios de cada destino
            mapa = {k: lista_docs(x["FOLIO"]) for k, x in d.groupby(col)}
            for r_ in filas_m:
                r_["docs"], r_["docs_full"] = mapa.get(r_[col], ("-", "-"))
            cols.insert(1, ("FOLIOS", "docs", "docs", "L", False))
        res = [E_table(titulo, cols, filas_m, total=tot, note=f"Mostrando {len(gm)} de {len(g)}" if len(gm) < len(g) else "")]
        return res, [(str(x[col]), float(x["inv"]), "red") for _, x in gm.head(12).iterrows()]

    t1, b1 = grp("_SOL", "Muestras por solicitante", "SOLICITÓ")
    out += t1
    if b1:
        out.append(E_bars("Inversión en muestras por solicitante", b1, "money"))
    out += grp("_PAQ", "Muestras por paquetería", "PAQUETERÍA")[0]
    out += grp("_HOT", "Muestras por destino / hotel", "HOTEL")[0]
    d["_MM"] = d["FECHA_DT"].dt.year.astype(int).astype(str) + "-" + d["FECHA_DT"].dt.month.astype(int).map("{:02d}".format)
    mm = d.groupby("_MM").agg(envios=("INVERSION", "size"), prod=("COSTO_TOTAL", "sum"), flete=("COSTO_GUIA", "sum"),
                              inv=("INVERSION", "sum")).reset_index().sort_values("_MM")
    mm["prom"] = mm["inv"] / mm["envios"]
    mm["pct"] = mm["inv"] / inv * 100 if inv else np.nan
    out.append(E_table("Muestras por mes", [("MES", "_MM", "txt", "L", False), ("ENVÍOS", "envios", "int", "R", False),
                                           ("PRODUCTO", "prod", "money", "R", False), ("FLETE", "flete", "money", "R", False),
                                           ("INVERSIÓN", "inv", "money", "R", False), ("PROM./ENVÍO", "prom", "money", "R", False),
                                           ("% DEL TOTAL", "pct", "pct", "R", False)], _filas(mm)))
    if o["mu_detalle"]:
        det = d.sort_values("INVERSION", ascending=False)
        det = det.head(SCREEN_MAX if o["top"] == "TODOS" else max(int(o["top"]), 20))
        det = det.assign(_FOL=det["FOLIO"].astype(str))
        cols = [("FOLIO", "_FOL", "txt", "L", False), ("FECHA", "FECHA_DT", "date", "L", False), ("SOLICITÓ", "_SOL", "txt", "L", False),
                ("HOTEL / DESTINO", "_HOT", "txt", "L", False), ("PAQUETERÍA", "_PAQ", "txt", "L", True), ("ESTATUS", "_STAT", "txt", "L", True),
                ("PRODUCTO", "COSTO_TOTAL", "money", "R", False), ("FLETE", "COSTO_GUIA", "money2", "R", False), ("INVERSIÓN", "INVERSION", "money", "R", False)]
        out.append(E_table("Detalle de muestras (mayor inversión primero)", cols,
                           det[[c[1] for c in cols]].replace({np.nan: None, pd.NaT: None}).to_dict("records"), landscape=True))
    return out


# --- Tabla cruzada ----------------------------------------------------------
CRUCE_MET = {"Costo logístico ($)": ("costo", "money"), "% logístico": ("pct_log", "pctlog"), "Facturación": ("fact", "money"),
             "Pedidos": ("n", "int"), "Cajas": ("cajas", "int"), "Costo por caja": ("costo_caja", "money2"),
             "Exceso sobre target ($)": ("exceso", "money")}


def sec_cruz(ctx):
    d, o = ctx["d"], ctx["opts"]
    rdim, cdim = o["cz_filas"], o["cz_cols"]
    if d.empty:
        return [E_note("Sin pedidos con los filtros elegidos.")]
    if rdim == cdim:
        return [E_note("Elige dimensiones distintas para filas y columnas.")]
    rcol, ccol = DIMS[rdim], DIMS[cdim]
    mkey, mkind = CRUCE_MET[o["cz_met"]]
    x = d[[rcol, ccol, "_COSTO", "FACTURACION", "_CAJ", "_EXC"]].copy()
    x["n"] = 1
    # columnas: máx. 12 (el resto va a OTROS)
    cnat = ccol in NATURALES
    orden_c = x.groupby(ccol)["_COSTO"].sum().sort_values(ascending=False).index.tolist()
    if ccol == "_MESN":
        orden_c = [m.title() for m in MESES if m.title() in set(x[ccol])] + [c for c in orden_c if c not in [m.title() for m in MESES]]
    elif ccol == "_CAJB":
        orden_c = sorted(orden_c, key=lambda s: 0 if s == "SIN CAJAS" else int(str(s).split("+")[0].split(" ")[0]))
    elif ccol == "_CLASE":
        orden_c = [c for c in CLASES if c in orden_c]
    elif ccol == "_ANIOT":
        orden_c = sorted(orden_c)
    if len(orden_c) > 12:
        keep = orden_c[:11]
        x[ccol] = np.where(x[ccol].isin(keep), x[ccol], "OTROS")
        orden_c = keep + ["OTROS"]
    sums = {k: pd.pivot_table(x, index=rcol, columns=ccol, values=v, aggfunc="sum", fill_value=0)
            for k, v in (("costo", "_COSTO"), ("fact", "FACTURACION"), ("cajas", "_CAJ"), ("exceso", "_EXC"), ("n", "n"))}
    sums = {k: v.reindex(columns=orden_c, fill_value=0) for k, v in sums.items()}

    def valor(s):   # s: dict de sumas (escalar/Series) -> métrica
        if mkey == "pct_log":
            return s["costo"] / s["fact"] * 100 if np.all(np.asarray(s["fact"]) > 0) else None
        if mkey == "costo_caja":
            return s["costo"] / s["cajas"] if np.all(np.asarray(s["cajas"]) > 0) else None
        return s[mkey]

    filas_idx = sums["costo"].sum(axis=1).sort_values(ascending=False).index.tolist()
    if rcol == "_MESN":
        filas_idx = [m.title() for m in MESES if m.title() in set(x[rcol])] + [r for r in filas_idx if r not in [m.title() for m in MESES]]
    elif rcol == "_CAJB":
        filas_idx = sorted(filas_idx, key=lambda s: 0 if s == "SIN CAJAS" else int(str(s).split("+")[0].split(" ")[0]))
    elif rcol == "_CLASE":
        filas_idx = [c for c in CLASES if c in filas_idx]
    elif rcol == "_ANIOT":
        filas_idx = sorted(filas_idx)
    elif o["top"] != "TODOS":
        filas_idx = filas_idx[: int(o["top"])]

    def fila(idx):
        r = {"K": idx}
        for i, c in enumerate(orden_c):
            s = {k: float(v.at[idx, c]) if idx in v.index else 0.0 for k, v in sums.items()}
            r[f"c{i}"] = (valor(s) if (mkey in ("pct_log", "costo_caja") or s["n"] > 0) else None)
        s = {k: float(v.loc[idx].sum()) for k, v in sums.items()}
        r["tot"] = valor(s)
        return r
    rows = [fila(i) for i in filas_idx]
    stot = {k: float(v.loc[filas_idx].sum().sum()) for k, v in sums.items()}
    tr = {"K": "TOTAL", "tot": valor(stot)}
    for i, c in enumerate(orden_c):
        s = {k: float(v.loc[filas_idx, c].sum()) for k, v in sums.items()}
        tr[f"c{i}"] = valor(s)
    cols = [(rdim.upper(), "K", "txt", "L", False)] + [(trunc(str(c), 14), f"c{i}", mkind, "R", False) for i, c in enumerate(orden_c)] + \
           [("TOTAL", "tot", mkind, "R", False)]
    if rcol == "_CLI":    # trazabilidad
        rows = agregar_docs(rows, d, rcol)
        cols.append(("FACTURA / PEDIDO", "docs", "docs", "L", False))
    return [E_table(f"Tabla cruzada · {o['cz_met']} · {rdim} × {cdim}", cols, rows, total=tr, landscape=len(cols) > 9,
                    note="Las columnas se limitan a 12; lo demás se agrupa en OTROS.")]


def construir(ctx, activas):
    """Devuelve [(clave, titulo, subtitulo, [elementos])] en el orden de SECCIONES."""
    dims = {"flet": ("Por fletera", "Fletera"), "tran": ("Por transporte", "Transporte"), "dest": ("Por destino", "Destino"),
            "clie": ("Por cliente", "Cliente"), "moda": ("Cobro regreso vs cobro destino", "Modalidad (cobro)"),
            "conc": ("Por concepto", "Concepto"), "mes": ("Por mes", "Mes"), "caja": ("Por número de cajas", "Nº de cajas"),
            "sema": ("Semáforo de salud", "Semáforo")}
    out = []
    for key, nombre, desc in SECCIONES:
        if key not in activas:
            continue
        if key in dims:
            els = sec_dim(ctx, dims[key][0], dims[key][1])
        else:
            els = {"kpi": sec_kpi, "peq": sec_peq, "rank": sec_rank, "entr": sec_entr, "extr": sec_extr,
                   "mues": sec_mues, "cruz": sec_cruz}[key](ctx)
        out.append((key, nombre.upper(), desc, els))
    return out


# ============================================================
# 8. RENDER EN PANTALLA (tarjetas premium + tablas con encabezado sticky)
# ============================================================
CSS = """
<style>
.jq-sec{display:flex;align-items:baseline;gap:12px;margin:34px 0 14px 0;padding:12px 16px;border-radius:10px;
 background:linear-gradient(90deg,#2B343B 0%,#232B31 100%);border-left:5px solid #00A3A3;box-shadow:0 4px 14px rgba(0,0,0,.25)}
.jq-sec .n{color:#FFC000;font-weight:800;font-size:13px;letter-spacing:1px}
.jq-sec .t{color:#fff;font-weight:800;font-size:15px;letter-spacing:1.5px}
.jq-sec .s{color:#9FB3BF;font-size:11px;margin-left:auto}
.jq-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:6px 0 14px 0}
.jq-card{position:relative;overflow:hidden;padding:16px 18px 15px 18px;border-radius:14px;
 background:linear-gradient(145deg,#2F3A42 0%,#1F282D 100%);border:1px solid rgba(255,255,255,.07);
 box-shadow:0 8px 22px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.05);transition:transform .2s,box-shadow .2s}
.jq-card:before{content:"";position:absolute;left:0;top:0;right:0;height:3px;background:var(--c)}
.jq-card:after{content:"";position:absolute;right:-30px;top:-30px;width:110px;height:110px;border-radius:50%;
 background:radial-gradient(circle,var(--c) 0%,transparent 70%);opacity:.14}
.jq-card .l{color:#9FB3BF;font-size:10px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase}
.jq-card .v{color:var(--c);font-size:26px;font-weight:800;margin:7px 0 3px 0;line-height:1.1}
.jq-card .v.sm{font-size:19px}
.jq-card .sub{color:#8497A3;font-size:11px;min-height:14px}
.jq-h{color:#E8EEF1;font-weight:800;font-size:12px;letter-spacing:1.4px;text-transform:uppercase;margin:20px 0 8px 2px}
.jq-tw{max-height:520px;overflow:auto;border-radius:12px;border:1px solid rgba(255,255,255,.08);
 box-shadow:0 8px 22px rgba(0,0,0,.28);background:#1B2328}
.jq-t{border-collapse:separate;border-spacing:0;width:100%;font-size:12.5px;color:#DCE5EA}
.jq-t th{position:sticky;top:0;z-index:3;background:#2B343B;color:#fff;font-size:10.5px;letter-spacing:1px;font-weight:800;
 padding:10px 12px;border-bottom:2px solid #00A3A3;white-space:nowrap;text-transform:uppercase}
.jq-t td{padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.05);white-space:nowrap;background:#1B2328}
.jq-t tbody tr:nth-child(even) td{background:#202A30}
.jq-t tbody tr:hover td{background:#2A3840}
.jq-t th:first-child,.jq-t td:first-child{position:sticky;left:0;z-index:2}
.jq-t th:first-child{z-index:4}
.jq-t td:first-child{font-weight:700;color:#fff;box-shadow:2px 0 0 rgba(0,0,0,.25);max-width:260px;overflow:hidden;text-overflow:ellipsis}
.jq-t tfoot td{position:sticky;bottom:0;z-index:3;background:#2B343B!important;color:#fff;font-weight:800;border-top:2px solid #FFC000}
.jq-t tfoot td:first-child{z-index:4}
.jq-t .r{text-align:right;font-variant-numeric:tabular-nums}
.jq-t td.docs{color:#9FB3BF;font-size:11.5px;max-width:300px;overflow:hidden;text-overflow:ellipsis}
.jq-t .good{color:#4FD1A0;font-weight:700}.jq-t .bad{color:#FF6B6B;font-weight:700}
.jq-t .warn{color:#FFC000;font-weight:700}.jq-t .mute{color:#6F808B}
.jq-pill{font-size:11px;font-weight:800;letter-spacing:.6px}
.jq-pill:before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:7px;background:currentColor}
.jq-nota{color:#8497A3;font-size:11px;margin:6px 2px 0 2px;font-style:italic}
.jq-aviso{padding:12px 16px;border-radius:10px;background:#2B343B;border-left:4px solid #FFC000;color:#DCE5EA;font-size:13px;margin:8px 0}
.jq-bars{background:linear-gradient(145deg,#2F3A42,#1F282D);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:14px 18px;
 box-shadow:0 8px 22px rgba(0,0,0,.28)}
.jq-b{display:grid;grid-template-columns:minmax(120px,230px) 1fr 100px;gap:12px;align-items:center;margin:7px 0;font-size:12px;color:#DCE5EA}
.jq-b .lab{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.jq-b .tr{height:13px;background:rgba(255,255,255,.06);border-radius:8px;overflow:hidden}
.jq-b .fi{height:100%;border-radius:8px;background:linear-gradient(90deg,var(--c),var(--c2))}
.jq-b .val{text-align:right;font-weight:800;color:#fff;font-variant-numeric:tabular-nums}
.jq-chips{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 10px 0}
.jq-chip{padding:5px 12px;border-radius:6px;background:#2B343B;border-left:3px solid #00A3A3;color:#DCE5EA;font-size:11px}
</style>
"""


def _s(t):
    """Texto seguro para st.markdown (escapa HTML y el signo $ que Streamlit toma como LaTeX)."""
    return esc(t).replace("$", "&#36;")


def html_kpis(items):
    out = ['<div class="jq-cards">']
    for lab, val, tono, sub in items:
        c = HEX.get(tono, HEX["teal"])
        sm = " sm" if len(str(val)) > 12 else ""
        out.append(f'<div class="jq-card" style="--c:{c}"><div class="l">{_s(lab)}</div><div class="v{sm}">{_s(val)}</div>'
                   f'<div class="sub">{_s(sub)}</div></div>')
    out.append("</div>")
    return "".join(out)


def _td(kind, align, v, full=None):
    txt, tono = fmt(kind, v)
    if kind == "docs":
        return f'<td class="docs" title="{esc(full or txt)}">{_s(txt)}</td>'
    cls = ("r " if align == "R" else "") + tono
    if kind in ("cls", "est") and txt:
        return f'<td class="{cls.strip()}"><span class="jq-pill {tono}">{_s(txt)}</span></td>'
    return f'<td class="{cls.strip()}">{_s(txt)}</td>'


def html_table(t):
    cols, rows = t["cols"], t["rows"][:SCREEN_MAX]
    out = []
    if t["title"]:
        out.append(f'<div class="jq-h">{_s(t["title"])}</div>')
    out.append('<div class="jq-tw"><table class="jq-t"><thead><tr>')
    out += [f'<th class="{"r" if c[3] == "R" else ""}">{_s(c[0])}</th>' for c in cols]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join(_td(c[2], c[3], r.get(c[1]), r.get(c[1] + "_full")) for c in cols) + "</tr>")
    out.append("</tbody>")
    if t["total"]:
        out.append("<tfoot><tr>" + "".join(
            f'<td class="{"r" if c[3] == "R" else ""}">{_s(fmt(c[2], t["total"].get(c[1]))[0]) if c[2] not in ("cls", "est") else _s(t["total"].get(c[1]) or "")}</td>'
            for c in cols) + "</tr></tfoot>")
    out.append("</table></div>")
    if t["note"]:
        out.append(f'<div class="jq-nota">{_s(t["note"])}</div>')
    return "".join(out)


def html_bars(b):
    items = b["items"]
    vmax = max([v for _, v, _ in items] + [1e-9])
    out = [f'<div class="jq-h">{_s(b["title"])}</div><div class="jq-bars">']
    for lab, v, tono in items:
        c = HEX.get(tono, HEX["teal"])
        w = max(v / vmax * 100, 1.5) if v > 0 else 0
        out.append(f'<div class="jq-b" style="--c:{c};--c2:{c}99"><div class="lab" title="{esc(lab)}">{_s(lab)}</div>'
                   f'<div class="tr"><div class="fi" style="width:{w:.1f}%"></div></div><div class="val">{_s(fmt(b["kind"], v)[0])}</div></div>')
    out.append("</div>")
    return "".join(out)


def render_pantalla(secciones, resumen_filtros, f):
    st.markdown(CSS, unsafe_allow_html=True)
    chips = "".join(f'<span class="jq-chip">{_s(p.strip())}</span>' for p in resumen_filtros.split("  ·  "))
    st.markdown(f'<div class="jq-chips">{chips}</div>', unsafe_allow_html=True)
    for i, (key, nombre, desc, els) in enumerate(secciones, 1):
        st.markdown(f'<div class="jq-sec"><span class="n">{i:02d}</span><span class="t">{_s(nombre)}</span>'
                    f'<span class="s">{_s(desc)}</span></div>', unsafe_allow_html=True)
        for kind, payload in els:
            if kind == "kpis":
                st.markdown(html_kpis(payload), unsafe_allow_html=True)
            elif kind == "table":
                st.markdown(html_table(payload), unsafe_allow_html=True)
            elif kind == "bars":
                st.markdown(html_bars(payload), unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="jq-aviso">{_s(payload)}</div>', unsafe_allow_html=True)


# ============================================================
# 9. PDF DE ANÁLISIS (mismo estilo que el reporte mensual)
# ============================================================
def _estilos():
    b = dict(fontName="Helvetica", textColor=C_TEXT)
    return {"sec_t": ParagraphStyle("sec_t", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.white),
            "sec_s": ParagraphStyle("sec_s", fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#B7C4CC")),
            "sub": ParagraphStyle("sub", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=C_SLATE, spaceBefore=6, spaceAfter=4),
            "kpi_l": ParagraphStyle("kpi_l", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=C_GRAY),
            "kpi_v": ParagraphStyle("kpi_v", fontName="Helvetica-Bold", fontSize=15, leading=18),
            "kpi_v_s": ParagraphStyle("kpi_v_s", fontName="Helvetica-Bold", fontSize=10.5, leading=13),
            "kpi_s": ParagraphStyle("kpi_s", fontName="Helvetica", fontSize=6.5, leading=8, textColor=C_GRAY),
            "nota": ParagraphStyle("nota", fontName="Helvetica-Oblique", fontSize=7.5, leading=10, textColor=C_GRAY),
            "body": ParagraphStyle("body", fontSize=8.5, leading=11.5, **b)}


ST = _estilos()


class _Canvas(rl_canvas.Canvas):
    titulo_pie, pw = "", letter[0]

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for s_ in self._saved:
            self.__dict__.update(s_)
            self.setStrokeColor(C_BORDER)
            self.setLineWidth(0.5)
            self.line(36, 34, self.pw - 36, 34)
            self.setFont("Helvetica", 7)
            self.setFillColor(C_GRAY)
            self.drawString(36, 23, f"JYPESA | Logística  -  {self.titulo_pie}  -  Generado e impreso con Nexion Smart Logistic")
            self.drawRightString(self.pw - 36, 23, f"Página {self._pageNumber} de {n}")
            super().showPage()
        super().save()


def _pdf_sec(num_, titulo, sub, W):
    cont = [Paragraph(f"{num_:02d}&nbsp;&nbsp;{esc(titulo)}", ST["sec_t"])]
    if sub:
        cont.append(Paragraph(esc(sub), ST["sec_s"]))
    t = Table([[cont]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C_SLATE), ("LINEBEFORE", (0, 0), (0, 0), 5, C_TEAL),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return [CondPageBreak(110), t, Spacer(1, 9)]


def _pdf_kpis(items, W, gap=8):
    n = len(items)
    ncols = min(n, 4) if n != 5 else 3
    cw = (W - gap * (ncols - 1)) / ncols
    out = []
    for i in range(0, n, ncols):
        chunk = items[i:i + ncols]
        row, widths, style = [], [], []
        for j, (lab, val, tono, sub) in enumerate(chunk):
            c = j * 2
            col = HEX.get(tono, HEX["teal"])
            row.append([Paragraph(esc(lab).upper(), ST["kpi_l"]), Spacer(1, 3),
                        Paragraph(f'<font color="{col}">{esc(val)}</font>', ST["kpi_v"] if len(str(val)) <= 13 else ST["kpi_v_s"]),
                        Paragraph(esc(sub), ST["kpi_s"])])
            widths.append(cw)
            style += [("BACKGROUND", (c, 0), (c, 0), C_LIGHT), ("LINEABOVE", (c, 0), (c, 0), 3, colors.HexColor(col)),
                      ("BOX", (c, 0), (c, 0), 0.5, C_BORDER)]
            if j < len(chunk) - 1:
                row.append("")
                widths.append(gap)
        t = Table([row], colWidths=widths, hAlign="LEFT")
        t.setStyle(TableStyle(style + [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                       ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                       ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        out += [t, Spacer(1, 8)]
    return out


def _pdf_table(t, W, wide):
    cols = [c for c in t["cols"] if wide or not c[4]]
    rows = t["rows"][:PDF_MAX]
    nc = len(cols)
    font = 7.5 if nc <= 8 else (7 if nc <= 11 else (6.3 if nc <= 14 else 5.6))
    pesos = []
    for c in cols:
        k = c[2]
        if (k == "txt" and c[1] in ("_CLI", "K", "_HOT")) or c[0] in ("CLIENTE", "HOTEL / DESTINO"):
            pesos.append(2.6)
        elif k == "docs":
            pesos.append(2.4)
        elif k == "date":
            pesos.append(1.7)
        elif k in ("vs", "pctlog", "pctok"):
            pesos.append(1.45)
        elif k in ("money", "money2"):
            pesos.append(1.25)
        elif k in ("cls", "est"):
            pesos.append(1.9)
        elif k == "txt":
            pesos.append(1.7)
        else:
            pesos.append(0.9 if len(c[0]) <= 4 else 1.1)
    sw = W / sum(pesos)
    widths = [p * sw for p in pesos]
    amap = {"L": 0, "C": 1, "R": 2}

    def cell(txt, a, tono="", bold=False):
        return Paragraph(esc(txt), ParagraphStyle("c", fontName="Helvetica-Bold" if bold or tono in ("good", "bad", "warn") else "Helvetica",
                                                  fontSize=font, leading=font + 2, alignment=amap[a], textColor=TONO_COLOR.get(tono, C_TEXT)))
    head = [Paragraph(esc(c[0]), ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=font - 0.3, leading=font + 1.5,
                                                 textColor=colors.white, alignment=amap[c[3]])) for c in cols]
    data = [head]
    for r in rows:
        fila = []
        for c in cols:
            txt, tono = fmt(c[2], r.get(c[1]))
            fila.append(cell(txt, c[3], tono))
        data.append(fila)
    if t["total"]:
        data.append([cell(fmt(c[2], t["total"].get(c[1]))[0] if c[2] not in ("cls", "est") else str(t["total"].get(c[1]) or ""),
                          c[3], bold=True) for c in cols])
    tb = Table(data, colWidths=widths, repeatRows=1)
    sty = [("BACKGROUND", (0, 0), (-1, 0), C_SLATE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("LINEBELOW", (0, 0), (-1, -1), 0.3, C_BORDER), ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    for i in range(2, len(data), 2):
        sty.append(("BACKGROUND", (0, i), (-1, i), C_LIGHT))
    if t["total"]:
        sty += [("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), colors.HexColor("#E3EAEE")),
                ("LINEABOVE", (0, len(data) - 1), (-1, len(data) - 1), 0.8, C_SLATE)]
    tb.setStyle(TableStyle(sty))
    out = [CondPageBreak(90)]
    if t["title"]:
        out.append(Paragraph(esc(t["title"]).upper(), ST["sub"]))
    out.append(tb)
    nota = t["note"] + (f"  ·  PDF limitado a {PDF_MAX} filas; el Excel trae todas." if len(t["rows"]) > PDF_MAX else "")
    if nota.strip():
        out.append(Paragraph(esc(nota.strip(" ·")), ST["nota"]))
    out.append(Spacer(1, 10))
    return out


def _pdf_bars(b, W, label_w=170, bar_h=11, gap=4):
    items = b["items"]
    h = len(items) * (bar_h + gap) + gap
    d = Drawing(W, h)
    vmax = max([v for _, v, _ in items] + [1e-9])
    area = W - label_w - 70
    y = h - gap - bar_h
    pal = {k: colors.HexColor(v) for k, v in HEX.items()}
    for lab, v, tono in items:
        d.add(String(label_w - 6, y + bar_h / 2 - 2.5, trunc(lab, int(label_w / 4.1)), fontName="Helvetica", fontSize=7,
                     textAnchor="end", fillColor=C_TEXT))
        w = max(area * v / vmax, 0.8) if v > 0 else 0
        d.add(Rect(label_w, y, w, bar_h, fillColor=pal.get(tono, C_TEAL), strokeColor=None))
        d.add(String(label_w + w + 4, y + bar_h / 2 - 2.5, fmt(b["kind"], v)[0], fontName="Helvetica-Bold", fontSize=7, fillColor=C_TEXT))
        y -= bar_h + gap
    return [Paragraph(esc(b["title"]).upper(), ST["sub"]), d, Spacer(1, 10)]


def generar_pdf(secciones, resumen_filtros, titulo, logo_bytes, orientacion):
    hay_ancho = any(k == "table" and p.get("landscape") for _, _, _, els in secciones for k, p in els)
    horiz = orientacion == "HORIZONTAL" or (orientacion == "AUTOMÁTICA" and hay_ancho)
    pw, ph = landscape(letter) if horiz else letter
    W = pw - 72
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    BH = 120

    def portada(c, doc):
        c.saveState()
        c.setFillColor(C_NAVY)
        c.rect(0, ph - BH, pw, BH, stroke=0, fill=1)
        c.setFillColor(C_TEAL)
        c.rect(0, ph - BH, pw, 5, stroke=0, fill=1)
        c.setFillColor(C_GOLD)
        c.rect(36, ph - 52, 38, 3, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#9FB3BF"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(36, ph - 42, "JYPESA  |  LOGÍSTICA Y DISTRIBUCIÓN")
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(36, ph - 80, "REPORTE DE ANÁLISIS")
        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(36, ph - 100, titulo)
        if logo_bytes:
            try:
                c.drawImage(ImageReader(BytesIO(logo_bytes)), pw - 36 - 110, ph - 84, width=102, height=48,
                            preserveAspectRatio=True, mask="auto", anchor="c")
            except Exception:
                pass
        c.restoreState()

    def normal(c, doc):
        c.saveState()
        c.setFillColor(C_NAVY)
        c.rect(0, ph - 30, pw, 30, stroke=0, fill=1)
        c.setFillColor(C_TEAL)
        c.rect(0, ph - 30, pw, 2.5, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(36, ph - 19, "REPORTE DE ANÁLISIS · CONSULTAS")
        c.setFillColor(C_GOLD)
        c.drawRightString(pw - 36, ph - 19, titulo)
        c.restoreState()

    buf = BytesIO()
    doc = BaseDocTemplate(buf, pagesize=(pw, ph), leftMargin=36, rightMargin=36, topMargin=48, bottomMargin=44,
                          title="Reporte de análisis · Consultas", author="JYPESA | Nexion")
    doc.addPageTemplates([
        PageTemplate(id="portada", frames=[Frame(36, 44, W, ph - BH - 44 - 14, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=portada),
        PageTemplate(id="normal", frames=[Frame(36, 44, W, ph - 44 - 48, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=normal)])
    caja = Table([[Paragraph("<b>FILTROS APLICADOS</b><br/>" + esc(resumen_filtros) + f"<br/><font color='#6B7A86'>Generado el {ahora}</font>", ST["body"])]],
                 colWidths=[W])
    caja.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C_LIGHT), ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                              ("LINEBEFORE", (0, 0), (0, 0), 4, C_GOLD), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                              ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story = [NextPageTemplate("normal"), caja, Spacer(1, 12)]
    for i, (key, nombre, desc, els) in enumerate(secciones, 1):
        story += _pdf_sec(i, nombre, desc, W)
        for kind, p in els:
            if kind == "kpis":
                story += _pdf_kpis(p, W)
            elif kind == "table":
                story += _pdf_table(p, W, wide=horiz)
            elif kind == "bars":
                story += _pdf_bars(p, W)
            else:
                story += [Paragraph(esc(p), ST["nota"]), Spacer(1, 8)]
    if not secciones:
        story.append(Paragraph("No se eligió ningún bloque.", ST["nota"]))
    cv = type("CV", (_Canvas,), {"titulo_pie": f"Consultas · {titulo}", "pw": pw})
    doc.build(story, canvasmaker=cv)
    buf.seek(0)
    return buf


def generar_excel(secciones, resumen_filtros):
    buf = BytesIO()
    usados = set()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame({"FILTROS APLICADOS": [resumen_filtros], "GENERADO": [datetime.now().strftime("%d/%m/%Y %H:%M")]}).to_excel(
            xw, sheet_name="Filtros", index=False)
        for _, nombre, _, els in secciones:
            for kind, p in els:
                if kind != "table":
                    continue
                nom = "".join(ch for ch in f"{nombre[:12]} {p['title'][:16]}" if ch not in '[]:*?/\\')[:31] or "Hoja"
                base, k = nom, 2
                while nom in usados:
                    nom = f"{base[:28]}_{k}"
                    k += 1
                usados.add(nom)
                df = pd.DataFrame(p["rows"] + ([p["total"]] if p["total"] else []))
                if df.empty:
                    continue
                for c in p["cols"]:      # en Excel van TODAS las facturas/folios, no la lista corta
                    if c[2] == "docs" and c[1] + "_full" in df.columns:
                        df[c[1]] = df[c[1] + "_full"].where(df[c[1] + "_full"].notna(), df[c[1]])
                df = df.reindex(columns=[c[1] for c in p["cols"]])
                df.columns = [c[0] for c in p["cols"]]
                for c in p["cols"]:
                    if c[2] == "date":
                        df[c[0]] = pd.to_datetime(df[c[0]], errors="coerce").dt.strftime("%d/%m/%Y")
                df.to_excel(xw, sheet_name=nom, index=False)
                ws = xw.sheets[nom]
                ws.freeze_panes = "B2"
                ws.auto_filter.ref = ws.dimensions
                for i, col in enumerate(df.columns, 1):
                    ws.column_dimensions[ws.cell(1, i).column_letter].width = min(max(len(str(col)) + 3, 12), 34)
    buf.seek(0)
    return buf


# ============================================================
# 10. INTERFAZ
# ============================================================
def _sel_todos(prefix, keys):
    for k in keys:
        st.session_state[f"{prefix}{k}"] = True


def _preset(nombre):
    act = set(PRESETS[nombre])
    for k, _, _ in SECCIONES:
        st.session_state[f"sec_{k}"] = k in act


def _limpiar():
    for k, _, _ in SECCIONES:
        st.session_state[f"sec_{k}"] = False


def main():
    st.markdown("""<style>
div.stButton > button, div.stDownloadButton > button{background:#2B343B!important;color:#DCE5EA!important;border:1px solid rgba(255,255,255,.10)!important;
border-radius:6px!important;width:100%!important;min-height:40px!important;box-shadow:none!important;transform:none!important;
font-size:12px!important;font-weight:800!important;letter-spacing:1px!important;text-transform:uppercase!important;transition:background .15s,border-color .15s!important}
div.stButton > button:hover, div.stDownloadButton > button:hover{background:#34414A!important;border-color:#00A3A3!important;color:#fff!important;transform:none!important}
div.stButton > button:active, div.stDownloadButton > button:active{background:#00A3A3!important;color:#fff!important}
div.stDownloadButton > button{border-color:#00A3A3!important;color:#00D1D1!important}
div[data-testid="stVerticalBlockBorderWrapper"]{border:1px solid rgba(255,255,255,.08)!important;border-radius:10px!important;background:rgba(43,52,59,.28)!important}
div[data-testid="stCheckbox"]{background:#2B343B;border:1px solid rgba(255,255,255,.08);border-radius:6px;padding:8px 12px;margin-bottom:6px;transition:border-color .15s,background .15s}
div[data-testid="stCheckbox"]:hover{border-color:rgba(0,163,163,.7)}
div[data-testid="stCheckbox"]:has(input:checked){border-color:#00A3A3;background:rgba(0,163,163,.16)}
div[data-testid="stCheckbox"] label{width:100%;cursor:pointer}
</style>""", unsafe_allow_html=True)
    st.markdown("<div style='padding:6px 0 14px 0;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:18px;'>"
                "<span style='color:#FFFFFF;font-size:13px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;'>"
                "REPORTES // CONSULTAS · ARMA TU REPORTE Y IMPRÍMELO</span></div>", unsafe_allow_html=True)

    try:
        import pytz
        hoy = pd.Timestamp(datetime.now(pytz.timezone("America/Mexico_City")).date())
    except Exception:
        hoy = pd.Timestamp(datetime.now().date())

    with st.spinner("Cargando base de envíos..."):
        try:
            base = datos_base()
        except Exception as e:
            st.error(f"No se pudo cargar la matriz de envíos: {e}")
            return

    anios_disp = sorted({int(y) for y in base["FECHA DE ENVÍO"].dt.year.dropna().unique()} | {hoy.year}, reverse=True)
    mes_prev = hoy.month - 1 or 12
    anio_prev = hoy.year if hoy.month > 1 else hoy.year - 1

    # ---------- 1. FILTROS ----------
    st.markdown("##### 1 · FILTROS")
    c1, c2, c3, c4 = st.columns([1, 1.6, 1.2, 1.2])
    anios = c1.multiselect("AÑO(S)", anios_disp, default=[anio_prev if anio_prev in anios_disp else anios_disp[0]], key="q_anios")
    meses_sel = c2.multiselect("MES(ES) (vacío = todo el año)", MESES, default=[MESES[mes_prev - 1]], key="q_meses")
    modalidad = c3.selectbox("COBRO", ["TODAS", "COBRO REGRESO", "COBRO DESTINO"], key="q_mod")
    costo_sel = c4.selectbox("COSTO A CONSIDERAR", ["Guía + adicionales", "Solo guía"], key="q_costo")
    if not anios:
        st.warning("Elige al menos un año.")
        return
    incluir_adic = costo_sel == "Guía + adicionales"

    d1, d2, d3, d4 = st.columns([1.3, 1, 1, 1])
    cajas_modo_txt = d1.selectbox("PEDIDOS POR NÚMERO DE CAJAS", ["TODOS", "PEQUEÑOS (1 a N)", "GRANDES (más de N)", "RANGO PERSONALIZADO"], key="q_cajas")
    max_peq = d2.selectbox("PEQUEÑO = HASTA (CAJAS)", [2, 3, 4, 5, 6, 8, 10], index=2, key="q_maxpeq")
    caj_min = d3.number_input("CAJAS DESDE", min_value=0, value=1, step=1, key="q_cmin", disabled=cajas_modo_txt != "RANGO PERSONALIZADO")
    caj_max = d4.number_input("CAJAS HASTA (0 = sin límite)", min_value=0, value=0, step=1, key="q_cmax", disabled=cajas_modo_txt != "RANGO PERSONALIZADO")
    cajas_modo = {"PEQUEÑOS (1 a N)": "PEQUEÑOS", "GRANDES (más de N)": "GRANDES", "RANGO PERSONALIZADO": "RANGO"}.get(cajas_modo_txt, "TODOS")

    # Opciones dependientes del año elegido
    u = preparar_universo(base, incluir_adic, hoy, int(max_peq))
    uy = u[u["FECHA DE ENVÍO"].isna() | u["_ANIO"].isin(anios)]
    with st.expander("MÁS FILTROS: fletera, transporte, destino, cliente, concepto, entrega, semáforo, búsqueda", expanded=False):
        e1, e2, e3 = st.columns(3)
        fleteras = e1.multiselect("FLETERA (vacío = todas)", sorted(uy["_FLE"].unique()), key=f"q_fle_{'_'.join(map(str, anios))}")
        transportes = e2.multiselect("TRANSPORTE", sorted(uy["_TR"].unique()), key=f"q_tr_{'_'.join(map(str, anios))}")
        destinos = e3.multiselect("DESTINO", sorted(uy["_DE"].unique()), key=f"q_de_{'_'.join(map(str, anios))}")
        g1, g2, g3 = st.columns(3)
        clientes = g1.multiselect("CLIENTE", sorted(uy.loc[~uy["ES_EXTRA"], "_CLI"].unique()), key=f"q_cli_{'_'.join(map(str, anios))}")
        conceptos = g2.multiselect("CONCEPTO", sorted(uy["_CONC"].unique()), key=f"q_con_{'_'.join(map(str, anios))}")
        estatus = g3.multiselect("ESTATUS DE ENTREGA", ESTATUS, key="q_est")
        h1, h2, h3 = st.columns([1.3, 1, 1.2])
        clases = h1.multiselect("SEMÁFORO", CLASES, key="q_cla")
        pct_min = h2.number_input("% LOGÍSTICO MAYOR A (0 = sin filtro)", min_value=0.0, value=0.0, step=0.5, key="q_pmin")
        buscar = h3.text_input("BUSCAR FACTURA / CLIENTE", key="q_buscar")
        solo_fuera = st.checkbox("Solo pedidos fuera de target (en alerta, críticos, en pérdida o sin facturación)", key="q_fuera")

    f = dict(anios=[int(a) for a in anios], meses=[MESES.index(m) + 1 for m in meses_sel], modalidad=modalidad,
             incluir_adic=incluir_adic, cajas_modo=cajas_modo, max_peq=int(max_peq), caj_min=int(caj_min), caj_max=int(caj_max),
             fleteras=fleteras, transportes=transportes, destinos=destinos, clientes=clientes, conceptos=conceptos,
             estatus=estatus, clases=clases, pct_min=float(pct_min), buscar=buscar.strip(), solo_fuera=solo_fuera)
    d, ext, d_nocaj = aplicar_filtros(u, f)

    # ---------- 2. BLOQUES ----------
    st.markdown("##### 2 · ARMA TU REPORTE (marca los bloques que quieras)")
    for k, _, _ in SECCIONES:
        st.session_state.setdefault(f"sec_{k}", k in PRESETS["Ejecutivo"])
    with st.container(border=True):
        b1, b2, b3, b4, _sp = st.columns([1, 1, 1, 1, 3])
        b1.button("Ejecutivo", on_click=_preset, args=("Ejecutivo",), key="p1")
        b2.button("Costos", on_click=_preset, args=("Costos",), key="p2")
        b3.button("Todo", on_click=_preset, args=("Todo",), key="p3")
        b4.button("Limpiar", on_click=_limpiar, key="p4")
        cols_chk = st.columns(4)
        for i, (k, nombre, desc) in enumerate(SECCIONES):
            cols_chk[i % 4].checkbox(nombre, key=f"sec_{k}", help=desc)
    activas = [k for k, _, _ in SECCIONES if st.session_state.get(f"sec_{k}")]

    # ---------- 3. OPCIONES ----------
    o = dict(orden_met="Costo logístico ($)", orden_dir="MAYOR A MENOR", top=15, rank_orden="% logístico", rank_dir="MAYOR A MENOR",
             rank_top=50, cz_filas="Fletera", cz_cols="Mes", cz_met="% logístico", mu_sol=[], mu_detalle=False)
    with st.expander("3 · OPCIONES DE LOS BLOQUES (orden, top, pedido por pedido, cruce, muestras)", expanded=False):
        a1, a2, a3 = st.columns(3)
        o["orden_met"] = a1.selectbox("ORDENAR TABLAS Y GRÁFICAS POR", list(METRICAS), key="o_met")
        o["orden_dir"] = a2.selectbox("DIRECCIÓN", ["MAYOR A MENOR", "MENOR A MAYOR"], key="o_dir")
        o["top"] = a3.selectbox("TOP EN TABLAS AGRUPADAS", TOPS, index=2, key="o_top")
        if "rank" in activas:
            r1, r2, r3 = st.columns(3)
            o["rank_orden"] = r1.selectbox("PEDIDO POR PEDIDO · ORDENAR POR", list(ORDEN_RANK), key="o_ro")
            o["rank_dir"] = r2.selectbox("PEDIDO POR PEDIDO · DIRECCIÓN", ["MAYOR A MENOR", "MENOR A MAYOR"], key="o_rd")
            o["rank_top"] = r3.selectbox("PEDIDO POR PEDIDO · CUÁNTOS", [25, 50, 100, 200, 500, "TODOS"], index=1, key="o_rt")
        if "cruz" in activas:
            z1, z2, z3 = st.columns(3)
            o["cz_filas"] = z1.selectbox("CRUCE · FILAS", list(DIMS), index=0, key="o_zf")
            o["cz_cols"] = z2.selectbox("CRUCE · COLUMNAS", list(DIMS), index=list(DIMS).index("Mes"), key="o_zc")
            o["cz_met"] = z3.selectbox("CRUCE · MÉTRICA", list(CRUCE_MET), index=1, key="o_zm")
        if "mues" in activas:
            dm, _msg = datos_muestras()
            m1, m2 = st.columns([2, 1])
            sol_opts = sorted(dm["_SOL"].unique()) if dm is not None else []
            o["mu_sol"] = m1.multiselect("MUESTRAS · SOLICITANTE (vacío = todos)", sol_opts, key="o_msol")
            o["mu_detalle"] = m2.checkbox("MUESTRAS · incluir detalle por folio", key="o_mdet")

    ctx = dict(d=d, ext=ext, d_nocaj=d_nocaj, f=f, opts=o)
    resumen = texto_filtros(f)
    if not activas:
        st.info("Marca al menos un bloque para armar el reporte.")
        return
    if d.empty and ext.empty and "mues" not in activas:
        st.warning("No hay información con esos filtros. Prueba con otro mes, año o quita algún filtro.")
        return

    with st.spinner("Armando el reporte..."):
        secciones = construir(ctx, activas)

    # ---------- IMPRESIÓN ----------
    st.markdown("##### 3 · IMPRIME")
    firma = hashlib.md5(json.dumps([f, activas, o, st.session_state.get("q_orient", "AUTOMÁTICA")], sort_keys=True, default=str).encode()).hexdigest()
    titulo = (", ".join(m.title() for m in meses_sel) if meses_sel else "Año completo") + " " + "/".join(str(a) for a in f["anios"])
    nom_base = titulo.replace(" ", "_").replace("/", "-").replace(",", "")
    with st.container(border=True):
        p1, p2, p3 = st.columns([1.2, 1, 1])
        orient = p1.selectbox("ORIENTACIÓN DEL PDF", ["AUTOMÁTICA", "VERTICAL", "HORIZONTAL"], key="q_orient")
        p2.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        p3.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        gen_pdf = p2.button("Generar PDF", key="q_pdf")
        gen_xls = p3.button("Generar Excel", key="q_xls")
        if gen_pdf:
            with st.spinner("Armando el PDF..."):
                try:
                    pdf = generar_pdf(secciones, resumen, titulo, obtener_logo_bytes(), orient)
                    st.session_state["q_pdf_out"] = {"bytes": pdf.getvalue(), "firma": firma, "nombre": f"Reporte_Consultas_{nom_base}.pdf"}
                except Exception as e:
                    st.error(f"No se pudo generar el PDF: {e}")
        if gen_xls:
            with st.spinner("Armando el Excel..."):
                try:
                    st.session_state["q_xls_out"] = {"bytes": generar_excel(secciones, resumen).getvalue(), "firma": firma,
                                                     "nombre": f"Consultas_{nom_base}.xlsx"}
                except Exception as e:
                    st.error(f"No se pudo generar el Excel: {e}")
        for clave, etiqueta, mime, col, nombre in (
                ("q_pdf_out", "Descargar PDF", "application/pdf", p2, "PDF"),
                ("q_xls_out", "Descargar Excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", p3, "Excel")):
            out = st.session_state.get(clave)
            if out and out["firma"] == firma:
                col.download_button(etiqueta, data=out["bytes"], file_name=out["nombre"], mime=mime, key=f"dl_{clave}")
            elif out:
                col.caption(f"Cambiaste filtros o bloques: vuelve a generar el {nombre}.")

    st.markdown("---")
    render_pantalla(secciones, resumen, f)


if __name__ == "__main__":
    main()
