"""
JYPESA | Reportes - Reporte Mensual en PDF (para Dirección)

Genera un PDF ejecutivo del mes elegido con:
  1. Resumen del mes
  2. Efectividad de envíos (despachos en 24 h hábiles)
  3. Inteligencia de negocio
  4. Top 20 clientes de distribución
  5. Distribución de carga (solo COBRO REGRESO)
  6. Cobro regreso: costo por fletera (lo que paga JYPESA)
  7. Ranking de fleteras (efectividad de entregas, tiempos y costo promedio)
  8. Costos de muestras

Los cálculos replican los del dashboard, pero filtran por MES **y AÑO**.
Los gráficos se dibujan directo con reportlab (no necesita kaleido ni matplotlib).
"""
import html as _html
import io
import os
import time
from datetime import datetime
from io import BytesIO

import numpy as np
import pandas as pd
import requests
import streamlit as st

from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)

from components.layout import render_layout

# Datos de muestras (mismo módulo que usa la página de Costos de Muestras)
try:
    from muestras_common import obtener_datos_github, precios as PRECIOS_MUESTRAS
    MUESTRAS_OK, MUESTRAS_ERR = True, ""
except Exception as _e_muestras:  # el reporte se genera igual, sin esa sección
    obtener_datos_github, PRECIOS_MUESTRAS = None, {}
    MUESTRAS_OK, MUESTRAS_ERR = False, str(_e_muestras)


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Reportes - Reporte Mensual PDF",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="REPORTES", submodulo_actual="REPORTE MENSUAL PDF")


# ============================================================
# 3. CONSTANTES
# ============================================================
GITHUB_USER, GITHUB_REPO, BRANCH = "RH2026", "nexion", "main"
ARCHIVO_MATRIZ = "Matriz_Excel_Dashboard.csv"
ARCHIVO_LOGO = "n1.png"

MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO",
         "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

# Mismas listas que el dashboard
CARRIERS_PRINCIPALES_DC = ["TRES GUERRAS", "ONE", "TINY PACK", "PAQMEX", "PAQUETE", "SANCHEZ", "FLETES DE REGRESO", "FARMASES"]
FLETERAS_PRINCIPALES_RK = ["TRES GUERRAS", "ONE", "TINY PACK", "PAQMEX", "SANCHEZ", "FLETES DE REGRESO"]
TARGET_COSTO_LOG = 7.5   # % meta de costo logístico (igual que Análisis Mensual)
FERIADOS_24H = ['2026-01-01', '2026-02-02', '2026-03-16', '2026-05-01']   # <- agrega aquí los de otros años

# Paleta (impresión)
C_NAVY = colors.HexColor("#384A52")
C_SLATE = colors.HexColor("#2B343B")
C_TEAL = colors.HexColor("#00A3A3")
C_GOLD = colors.HexColor("#FFC000")
C_GREEN = colors.HexColor("#2E9E6B")
C_RED = colors.HexColor("#D64545")
C_BLUE = colors.HexColor("#3B82F6")
C_PURPLE = colors.HexColor("#7C5CBF")
C_ORANGE = colors.HexColor("#E8833A")
C_GRAY = colors.HexColor("#6B7A86")
C_LIGHT = colors.HexColor("#F3F6F8")
C_BORDER = colors.HexColor("#D5DDE2")
C_TEXT = colors.HexColor("#1F2D35")
HEX = {k: v.hexval().replace("0x", "#") for k, v in dict(
    teal=C_TEAL, green=C_GREEN, red=C_RED, blue=C_BLUE, gold=C_GOLD, purple=C_PURPLE,
    orange=C_ORANGE, gray=C_GRAY, slate=C_SLATE).items()}

PAGE_W, PAGE_H = letter
MARGIN = 36
CONTENT_W = PAGE_W - 2 * MARGIN   # 540


# ============================================================
# 4. UTILIDADES DE FORMATO Y FECHAS
# ============================================================
def esc(t):
    return _html.escape("" if t is None else str(t))


def trunc(t, n):
    t = "" if t is None else str(t)
    return t if len(t) <= n else t[: n - 1] + "."


def money(v, dec=0):
    try:
        return f"${float(v):,.{dec}f}"
    except Exception:
        return "-"


def num(v, dec=0):
    try:
        return f"{float(v):,.{dec}f}"
    except Exception:
        return "-"


def pct(v, dec=1):
    try:
        if v is None or pd.isna(v):
            return "-"
        return f"{float(v):.{dec}f}%"
    except Exception:
        return "-"


def parse_fecha_segura(serie):
    """Convierte fechas sin invertir día/mes (ISO -> año-mes-día; el resto -> día/mes/año)."""
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
    return pd.to_numeric(
        serie.astype(str).str.replace(r"[^\d\.\-]", "", regex=True).replace("", "0"),
        errors="coerce",
    ).fillna(0.0)


# ============================================================
# 5. CARGA Y PREPARACIÓN DE DATOS
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
        if os.path.exists(ARCHIVO_LOGO):
            with open(ARCHIVO_LOGO, "rb") as f:
                return f.read()
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{ARCHIVO_LOGO}"
        r = requests.get(url, headers=_headers_github(), timeout=20)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None


def preparar_base(df_raw):
    """Normaliza la matriz de envíos: fechas, textos y números."""
    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    for c in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL", "EMISION"]:
        df[c] = parse_fecha_segura(df[c]) if c in df.columns else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

    for c in ["FLETERA", "FORMA DE ENVIO", "TRANSPORTE", "DESTINO", "NOMBRE DEL CLIENTE",
              "INCIDENCIAS", "MES", "NÚMERO DE PEDIDO"]:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].fillna("").astype(str).str.strip()
        df.loc[df[c].str.lower() == "nan", c] = ""
    df["MES"] = df["MES"].str.upper()

    for c in ["COSTO DE LA GUÍA", "FACTURACION", "VALUACION", "COSTOS ADICIONALES", "CANTIDAD DE CAJAS"]:
        df[c] = limpiar_moneda(df[c]) if c in df.columns else 0.0
    df["CAJAS"] = pd.to_numeric(df["CAJAS"], errors="coerce").fillna(0) if "CAJAS" in df.columns else 0.0
    return df


def filtrar_mes(df, col, anio, mes):
    f = df[col]
    return df[(f.dt.year == anio) & (f.dt.month == mes)].copy()


# ============================================================
# 6. CÁLCULOS POR SECCIÓN (replican el dashboard)
# ============================================================
def calc_resumen(df_mes, hoy):
    total_p = len(df_mes)
    entregados = int(df_mes["FECHA DE ENTREGA REAL"].notna().sum())
    df_trans = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna()]
    en_tiempo = int((df_trans["PROMESA DE ENTREGA"] >= hoy).sum())
    retrasados = int((df_trans["PROMESA DE ENTREGA"] < hoy).sum())

    ret = df_trans[df_trans["PROMESA DE ENTREGA"] < hoy].copy()
    ret["FLETERA"] = ret["FLETERA"].replace("", "SIN ASIGNAR")
    ret_fletera = ret.groupby("FLETERA").size().sort_values(ascending=False)

    dest = df_mes[df_mes["DESTINO"] != ""]["DESTINO"].value_counts().head(8)
    return dict(total=total_p, entregados=entregados, en_transito=len(df_trans), en_tiempo=en_tiempo,
                retrasados=retrasados, pct_entregado=(entregados / total_p * 100) if total_p else 0.0,
                ret_fletera=ret_fletera, destinos=dest)


def _kpi_24h(ini, fin, feriados):
    if pd.isna(ini) and not pd.isna(fin):
        ini = fin
    if pd.isna(ini) or pd.isna(fin):
        return "Sin Datos", None
    try:
        if fin <= ini:
            return "A Tiempo", 0
        d = int(np.busday_count(ini.date(), fin.date(), weekmask='1111100', holidays=feriados))
        if d == 0:
            return "A Tiempo", d
        if d == 1 and fin.time() <= ini.time():
            return "A Tiempo", d
        return "Fuera de Tiempo", d
    except Exception:
        return "Sin Datos", None


def calc_despachos(df_mes):
    d = df_mes.copy()
    feriados = np.array(FERIADOS_24H, dtype='datetime64[D]')
    estados, dias = [], []
    for ini, fin in zip(d["EMISION"], d["FECHA DE ENVÍO"]):
        e, n = _kpi_24h(ini, fin, feriados)
        estados.append(e)
        dias.append(n)
    d["Estado_KPI"], d["DIAS_HABILES"] = estados, dias

    validos = d[d["Estado_KPI"] != "Sin Datos"]
    tot = len(validos)
    ok = int((validos["Estado_KPI"] == "A Tiempo").sum())
    no = tot - ok

    por_dia = pd.DataFrame()
    if not validos.empty:
        v = validos.assign(_ORDEN=validos["FECHA DE ENVÍO"].dt.normalize())
        por_dia = (v.groupby(["_ORDEN", "Estado_KPI"]).size().unstack(fill_value=0).sort_index())
        for c in ["A Tiempo", "Fuera de Tiempo"]:
            if c not in por_dia.columns:
                por_dia[c] = 0
    fuera = (validos[validos["Estado_KPI"] == "Fuera de Tiempo"]
             .sort_values("DIAS_HABILES", ascending=False).head(12))
    return dict(total=tot, ok=ok, no=no, pct_ok=(ok / tot * 100) if tot else 0.0,
                pct_no=(no / tot * 100) if tot else 0.0, por_dia=por_dia, fuera=fuera,
                sin_datos=len(d) - tot)


def calc_bi(df_mes):
    d = df_mes
    fact, guias = d["FACTURACION"].sum(), d["COSTO DE LA GUÍA"].sum()
    adic, cajas = d["COSTOS ADICIONALES"].sum(), d["CANTIDAD DE CAJAS"].sum()
    por_f = pd.DataFrame()
    dd = d[d["FLETERA"] != ""]
    if not dd.empty:
        por_f = dd.groupby("FLETERA").agg(
            pedidos=("FLETERA", "size"), facturacion=("FACTURACION", "sum"),
            guias=("COSTO DE LA GUÍA", "sum"), adic=("COSTOS ADICIONALES", "sum"),
            cajas=("CANTIDAD DE CAJAS", "sum")).reset_index()
        por_f["operativo"] = por_f["guias"] + por_f["adic"]
        por_f["pct_log"] = np.where(por_f["facturacion"] > 0, por_f["guias"] / por_f["facturacion"] * 100, 0.0)
        por_f["costo_caja"] = np.where(por_f["cajas"] > 0, por_f["operativo"] / por_f["cajas"], np.nan)
        por_f = por_f.sort_values("facturacion", ascending=False)
    return dict(fact=fact, guias=guias, adic=adic, cajas=cajas,
                costo_log=(guias / fact * 100) if fact else 0.0,
                costo_caja=(guias / cajas) if cajas else 0.0, por_fletera=por_f)


def calc_top_clientes(df_mes, n=20):
    d = df_mes[df_mes["NOMBRE DEL CLIENTE"] != ""]
    total_fact = df_mes["FACTURACION"].sum()
    top = pd.DataFrame()
    if not d.empty:
        top = d.groupby("NOMBRE DEL CLIENTE").agg(
            pedidos=("NOMBRE DEL CLIENTE", "size"), cajas=("CANTIDAD DE CAJAS", "sum"),
            facturacion=("FACTURACION", "sum"), guias=("COSTO DE LA GUÍA", "sum")).reset_index()
        top = top.sort_values("facturacion", ascending=False).head(n)
        top["share"] = np.where(total_fact > 0, top["facturacion"] / total_fact * 100, 0.0)
    forma = df_mes[df_mes["FORMA DE ENVIO"] != ""]["FORMA DE ENVIO"].value_counts()
    return dict(top=top, forma=forma, total_fact=total_fact,
                share_top=(top["facturacion"].sum() / total_fact * 100) if (total_fact and not top.empty) else 0.0)


def calc_carga_regreso(df_all, anio, mes):
    """Distribución de carga, solo COBRO REGRESO (misma lógica que la pestaña del dashboard)."""
    d = df_all.copy()
    fletera_base = d["FLETERA"].str.upper().str.strip()
    sin_asignar = (d["TRANSPORTE"].str.upper().str.strip() == "COBRO REGRESO") | (fletera_base == "COBRO REGRESO")
    d = d[~sin_asignar]
    texto_carrier = d["TRANSPORTE"].str.upper() + " | " + d["FLETERA"].str.upper()
    d = d[texto_carrier.apply(lambda x: any(p in x for p in CARRIERS_PRINCIPALES_DC))]

    # Periodo: el dashboard usa la columna MES (texto); aquí además se valida el año con la fecha de envío
    f_env = d["FECHA DE ENVÍO"]
    ok_anio = f_env.isna() | (f_env.dt.year == anio)
    d = d[(d["MES"] == MESES[mes - 1]) & ok_anio & (d["TRANSPORTE"] != "")].copy()
    d = d[d["FORMA DE ENVIO"].str.contains("REGRESO", case=False, na=False)
          | d["TRANSPORTE"].str.contains("COBRO REGRESO", case=False, na=False)]
    if d.empty:
        return dict(vacio=True)

    total = d["CAJAS"].sum()
    part = d.groupby("TRANSPORTE", as_index=False)["CAJAS"].sum()
    part["PCT"] = (part["CAJAS"] / total * 100) if total else 0.0
    part = part.sort_values("CAJAS", ascending=False)
    rutas = (d.groupby(["TRANSPORTE", "DESTINO", "FORMA DE ENVIO"], as_index=False)["CAJAS"].sum())
    orden = part.set_index("TRANSPORTE")["CAJAS"]
    rutas["_O"] = rutas["TRANSPORTE"].map(orden)
    rutas = rutas.sort_values(["_O", "TRANSPORTE", "CAJAS"], ascending=[False, True, False]).drop(columns="_O")
    return dict(vacio=False, registros=len(d), total=total, part=part, rutas=rutas,
                lider=part.iloc[0], destinos=d["DESTINO"].replace("", pd.NA).nunique())


def calc_costos_regreso(df_all, anio, mes):
    """Costos de COBRO REGRESO (lo que paga JYPESA), por fletera.
    Misma lógica que la página 'Análisis Mensual': FORMA DE ENVIO contiene REGRESO,
    flete = guía + costos adicionales, costo logístico = flete / facturación.
    Periodo: igual que la sección 05 (columna MES + validación de año)."""
    d = df_all.copy()
    f_env = d["FECHA DE ENVÍO"]
    ok_anio = f_env.isna() | (f_env.dt.year == anio)
    d = d[(d["MES"] == MESES[mes - 1]) & ok_anio]
    d = d[d["FORMA DE ENVIO"].str.contains("REGRESO", case=False, na=False)].copy()
    if d.empty:
        return dict(vacio=True)

    d["FLETERA"] = d["FLETERA"].replace("", "SIN ASIGNAR")
    d["_FLETE"] = d["COSTO DE LA GUÍA"] + d["COSTOS ADICIONALES"]
    d["_EVAL"] = d["PROMESA DE ENTREGA"].notna() & d["FECHA DE ENTREGA REAL"].notna()
    d["_OK"] = d["_EVAL"] & (d["FECHA DE ENTREGA REAL"] <= d["PROMESA DE ENTREGA"])
    d["_INC"] = d["VALUACION"] > 0

    flete, fact, cajas = d["_FLETE"].sum(), d["FACTURACION"].sum(), d["CAJAS"].sum()
    val, n_eval, n_ok = d["VALUACION"].sum(), int(d["_EVAL"].sum()), int(d["_OK"].sum())

    # Desglose por concepto (informativo; usa solo el costo de guía, como el dashboard)
    muestras = consignas = fnacional = 0.0
    col_c = next((c for c in d.columns if "CONCEPTO" in str(c).upper()), None)
    if col_c:
        conc = d[col_c].fillna("").astype(str).str.strip().str.upper()
        g = d["COSTO DE LA GUÍA"]
        muestras = g[conc.str.contains("MUESTRA|RECOLECCI", regex=True)].sum()
        consignas = g[conc.str.contains("CONSIGNA", regex=True)].sum()
        fnacional = g[conc.str.contains("NACIONAL", regex=True)].sum()

    res = d.groupby("FLETERA").agg(
        envios=("FLETERA", "size"), cajas=("CAJAS", "sum"), flete=("_FLETE", "sum"),
        fact=("FACTURACION", "sum"), val=("VALUACION", "sum"),
        n_eval=("_EVAL", "sum"), n_ok=("_OK", "sum")).reset_index()
    res["pct_gasto"] = (res["flete"] / flete * 100) if flete else 0.0
    res["costo_caja"] = res["flete"] / res["cajas"].replace(0, np.nan)
    res["pct_log"] = res["flete"] / res["fact"].replace(0, np.nan) * 100
    res["efic"] = res["n_ok"] / res["n_eval"].replace(0, np.nan) * 100
    res = res.sort_values("flete", ascending=False).reset_index(drop=True)

    return dict(vacio=False, registros=len(d), flete=flete, fact=fact, cajas=cajas, val=val,
                costo_log=(flete / fact * 100) if fact else 0.0,
                costo_caja=(flete / cajas) if cajas else 0.0,
                efic=(n_ok / n_eval * 100) if n_eval else None,
                pct_inc=(d["_INC"].sum() / len(d) * 100),
                muestras=muestras, consignas=consignas, fnacional=fnacional, res=res)


def _resumen_por_fletera(df_in):
    filas = []
    for fletera, g in df_in.groupby("FLETERA"):
        entregados = int(g["_ENTREGADO"].sum())
        a_tiempo = int(g["_A_TIEMPO"].sum())
        dias_ok = g.loc[g["_ENTREGADO"] & (g["_DIAS"] >= 0), "_DIAS"]
        cajas = g["CANTIDAD DE CAJAS"].sum()
        costo = g["_COSTO"].sum()
        filas.append({
            "FLETERA": fletera, "ENVIOS": len(g), "ENTREGADOS": entregados, "A_TIEMPO": a_tiempo,
            "RETRASO": max(entregados - a_tiempo, 0),
            "PCT_A_TIEMPO": (a_tiempo / entregados * 100) if entregados else None,
            "INCIDENCIAS_PCT": (g["_INCIDENCIA"].sum() / len(g) * 100) if len(g) else 0.0,
            "DIAS_PROM": dias_ok.mean() if not dias_ok.empty else None,
            "COSTO_PROM_ENVIO": g["_COSTO"].mean() if len(g) else 0.0,
            "COSTO_PROM_CAJA": (costo / cajas) if cajas else None,
        })
    return pd.DataFrame(filas)


def calc_ranking(df_all, anio, mes):
    d = df_all[df_all["FLETERA"].str.upper().apply(lambda x: any(p in x for p in FLETERAS_PRINCIPALES_RK))]
    d = filtrar_mes(d, "FECHA DE ENVÍO", anio, mes)
    d = d[d["FLETERA"] != ""].copy()
    if d.empty:
        return dict(vacio=True)
    d["_ENTREGADO"] = d["FECHA DE ENTREGA REAL"].notna()
    d["_A_TIEMPO"] = d["_ENTREGADO"] & (d["FECHA DE ENTREGA REAL"] <= d["PROMESA DE ENTREGA"])
    d["_INCIDENCIA"] = ~d["INCIDENCIAS"].astype(str).str.strip().str.upper().isin(["", "OK"])
    d["_DIAS"] = (d["FECHA DE ENTREGA REAL"] - d["FECHA DE ENVÍO"]).dt.days
    d["_COSTO"] = d["COSTO DE LA GUÍA"] + d["COSTOS ADICIONALES"]
    res = _resumen_por_fletera(d)

    entregados, a_tiempo = int(d["_ENTREGADO"].sum()), int(d["_A_TIEMPO"].sum())
    dias_ok = d[d["_ENTREGADO"] & (d["_DIAS"] >= 0)]["_DIAS"]
    cajas = d["CANTIDAD DE CAJAS"].sum()
    out = dict(vacio=False, df=d, res=res, registros=len(d), entregados=entregados,
               efectividad=(a_tiempo / entregados * 100) if entregados else 0.0,
               dias_prom=dias_ok.mean() if not dias_ok.empty else 0.0, dias_n=len(dias_ok),
               costo_envio=d["_COSTO"].mean() if len(d) else 0.0,
               costo_caja=(d["_COSTO"].sum() / cajas) if cajas else 0.0)

    def _ext(df_, col, fn):
        s = df_[df_[col].notna()]
        return s.loc[getattr(s[col], fn)()] if not s.empty else None
    out["top_puntual"] = _ext(res[res["ENTREGADOS"] > 0], "PCT_A_TIEMPO", "idxmax") if (res["ENTREGADOS"] > 0).any() else None
    out["top_incid"] = res.loc[res["INCIDENCIAS_PCT"].idxmax()] if not res.empty else None
    out["rapida"], out["lenta"] = _ext(res, "DIAS_PROM", "idxmin"), _ext(res, "DIAS_PROM", "idxmax")
    out["barata"], out["cara"] = _ext(res, "COSTO_PROM_ENVIO", "idxmin"), _ext(res, "COSTO_PROM_ENVIO", "idxmax")
    return out


# --- Muestras -------------------------------------------------
def preparar_muestras(df):
    d = df.copy()
    for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL", "ESTATUS",
                "SOLICITO", "NOMBRE DEL HOTEL", "FOLIO", "FECHA"]:
        if col not in d.columns:
            d[col] = "NO SURTIDO" if col == "ESTATUS" else (0.0 if col in ("COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL") else "")
    d["FECHA_DT"] = parse_fecha_segura(d["FECHA"].astype(str).str.strip())
    d["COSTO_TOTAL"] = pd.to_numeric(d["COSTO_TOTAL"], errors="coerce").fillna(0)
    d["COSTO_GUIA"] = pd.to_numeric(d["COSTO_GUIA"], errors="coerce").fillna(0)
    d["INVERSION"] = d["COSTO_TOTAL"] + d["COSTO_GUIA"]
    return d


def calc_muestras(d_all, anio, mes, precios):
    d = d_all[(d_all["FECHA_DT"].dt.year == anio) & (d_all["FECHA_DT"].dt.month == mes)].copy()
    total = len(d)
    prod, flete = d["COSTO_TOTAL"].sum(), d["COSTO_GUIA"].sum()
    inv = prod + flete
    despachados = int((d["ESTATUS"].astype(str).str.upper() == "DESPACHADO").sum())
    sol = d["SOLICITO"].astype(str).str.upper()

    por_sol = pd.DataFrame()
    if total:
        por_sol = d.assign(SOL=sol).groupby("SOL").agg(
            envios=("FOLIO", "size"), prod=("COSTO_TOTAL", "sum"), flete=("COSTO_GUIA", "sum"),
            inversion=("INVERSION", "sum")).reset_index().sort_values("inversion", ascending=False).head(10)

    # Tendencia: 12 meses que terminan en el mes elegido
    fin = pd.Period(year=anio, month=mes, freq="M")
    meses_rango = [fin - i for i in range(11, -1, -1)]
    v = d_all.dropna(subset=["FECHA_DT"]).copy()
    v["P"] = v["FECHA_DT"].dt.to_period("M")
    serie = v.groupby("P")["INVERSION"].sum()
    tendencia = [(f"{p.month:02d}/{str(p.year)[2:]}", float(serie.get(p, 0.0))) for p in meses_rango]

    top_dest = d.assign(H=d["NOMBRE DEL HOTEL"].astype(str).str.upper()).groupby("H")["FOLIO"].size().sort_values(ascending=False).head(10)
    col_paq = "PAQUETERIA_NOMBRE" if "PAQUETERIA_NOMBRE" in d.columns else "PAQUETERIA"
    paq = d.assign(P=d[col_paq].replace("", "SIN ASIGNAR").replace(0.0, "SIN ASIGNAR").fillna("SIN ASIGNAR").astype(str).str.upper())
    flete_paq = paq.groupby("P")["COSTO_GUIA"].sum().sort_values(ascending=False).head(10)

    cant = {}
    for p in (precios or {}).keys():
        if p in d.columns:
            cant[p] = pd.to_numeric(d[p], errors="coerce").fillna(0).sum()
    prod_top = pd.Series(cant, dtype="float64").sort_values(ascending=False).head(10)
    prod_top = prod_top[prod_top > 0]

    return dict(total=total, prod=prod, flete=flete, inv=inv, prom=(inv / total) if total else 0.0,
                pct_desp=(despachados / total * 100) if total else 0.0,
                top_agente=(sol.value_counts().idxmax() if total else "SIN DATOS"),
                por_sol=por_sol, tendencia=tendencia, top_dest=top_dest, flete_paq=flete_paq, prod_top=prod_top)


# ============================================================
# 7. COMPONENTES VISUALES PARA EL PDF
# ============================================================
def _estilos():
    base = dict(fontName="Helvetica", textColor=C_TEXT)
    return {
        "body": ParagraphStyle("body", fontSize=9, leading=12.5, **base),
        "bullet": ParagraphStyle("bullet", fontSize=9, leading=12.5, leftIndent=12, bulletIndent=0, spaceAfter=3, **base),
        "small": ParagraphStyle("small", fontSize=7.5, leading=10, textColor=C_GRAY, fontName="Helvetica"),
        "sec_t": ParagraphStyle("sec_t", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.white),
        "sec_s": ParagraphStyle("sec_s", fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#B7C4CC")),
        "sub": ParagraphStyle("sub", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=C_SLATE, spaceBefore=6, spaceAfter=4),
        "kpi_l": ParagraphStyle("kpi_l", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=C_GRAY),
        "kpi_v": ParagraphStyle("kpi_v", fontName="Helvetica-Bold", fontSize=15, leading=18),
        "kpi_v_s": ParagraphStyle("kpi_v_s", fontName="Helvetica-Bold", fontSize=10.5, leading=13),
        "th": ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=7, leading=8.5, textColor=colors.white),
        "nota": ParagraphStyle("nota", fontName="Helvetica-Oblique", fontSize=7.5, leading=10, textColor=C_GRAY),
    }


ST = _estilos()


def seccion(num_, titulo, subtitulo=""):
    cont = [Paragraph(f"{num_:02d}&nbsp;&nbsp;{esc(titulo)}", ST["sec_t"])]
    if subtitulo:
        cont.append(Paragraph(esc(subtitulo), ST["sec_s"]))
    t = Table([[cont]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_SLATE),
        ("LINEBEFORE", (0, 0), (0, 0), 5, C_TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return [t, Spacer(1, 10)]


def subtitulo(texto):
    return Paragraph(esc(texto).upper(), ST["sub"])


def kpi_row(items, ncols=4, gap=8):
    """items: [(etiqueta, valor, color_hex)]"""
    cw = (CONTENT_W - gap * (ncols - 1)) / ncols
    out = []
    for i in range(0, len(items), ncols):
        chunk = items[i:i + ncols]
        row, widths, style = [], [], []
        for j, (lab, val, col) in enumerate(chunk):
            c = j * 2
            v_style = ST["kpi_v"] if len(str(val)) <= 13 else ST["kpi_v_s"]
            row.append([Paragraph(esc(lab).upper(), ST["kpi_l"]),
                        Spacer(1, 3),
                        Paragraph(f'<font color="{col}">{esc(val)}</font>', v_style)])
            widths.append(cw)
            style += [("BACKGROUND", (c, 0), (c, 0), C_LIGHT),
                      ("LINEABOVE", (c, 0), (c, 0), 3, colors.HexColor(col)),
                      ("BOX", (c, 0), (c, 0), 0.5, C_BORDER)]
            if j < len(chunk) - 1:
                row.append("")
                widths.append(gap)
        t = Table([row], colWidths=widths, hAlign="LEFT")
        t.setStyle(TableStyle(style + [("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                       ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        out += [t, Spacer(1, 8)]
    return out


def tabla(headers, rows, widths, aligns=None, font=7.5, total_row=None):
    aligns = aligns or ["L"] * len(headers)
    amap = {"L": 0, "C": 1, "R": 2}

    def cell(txt, a, bold=False, color=C_TEXT):
        return Paragraph(esc(txt), ParagraphStyle("c", fontName="Helvetica-Bold" if bold else "Helvetica",
                                                  fontSize=font, leading=font + 2, alignment=amap[a], textColor=color))
    data = [[Paragraph(esc(h), ParagraphStyle("h", parent=ST["th"], alignment=amap[a])) for h, a in zip(headers, aligns)]]
    for r in rows:
        data.append([cell(c, a) for c, a in zip(r, aligns)])
    if total_row:
        data.append([cell(c, a, bold=True) for c, a in zip(total_row, aligns)])
    t = Table(data, colWidths=widths, repeatRows=1)
    st_ = [("BACKGROUND", (0, 0), (-1, 0), C_SLATE),
           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("LINEBELOW", (0, 0), (-1, -1), 0.3, C_BORDER),
           ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
           ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
           ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    for i in range(2, len(data), 2):
        st_.append(("BACKGROUND", (0, i), (-1, i), C_LIGHT))
    if total_row:
        st_ += [("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), colors.HexColor("#E3EAEE")),
                ("LINEABOVE", (0, len(data) - 1), (-1, len(data) - 1), 0.8, C_SLATE)]
    t.setStyle(TableStyle(st_))
    return t


def sin_datos(texto="Sin información para el periodo seleccionado."):
    t = Table([[Paragraph(esc(texto), ST["nota"])]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C_LIGHT), ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                           ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    return t


def lado_a_lado(izq, der, t_izq, t_der, w=(262, 262), gap=16):
    t = Table([[Paragraph(esc(t_izq).upper(), ST["sub"]), "", Paragraph(esc(t_der).upper(), ST["sub"])],
               [izq, "", der]], colWidths=[w[0], gap, w[1]], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


# --- Gráficos (dibujados con reportlab) ----------------------
def _s(d, x, y, txt, size=7, bold=False, anchor="start", fill=C_TEXT):
    d.add(String(x, y, txt, fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size,
                 textAnchor=anchor, fillColor=fill))


def chart_barras_h(items, width=CONTENT_W, color=C_TEAL, fmt=num, label_w=150, bar_h=12, gap=5, colors_list=None):
    items = [(str(k), float(v)) for k, v in items]
    if not items:
        return sin_datos()
    n = len(items)
    h = n * (bar_h + gap) + gap
    d = Drawing(width, h)
    vmax = max(v for _, v in items) or 1.0
    area = width - label_w - 62
    y = h - gap - bar_h
    for i, (lab, v) in enumerate(items):
        _s(d, label_w - 6, y + bar_h / 2 - 2.5, trunc(lab, int(label_w / 4.1)), 7, anchor="end")
        w = max(area * v / vmax, 0.8) if v > 0 else 0
        d.add(Rect(label_w, y, w, bar_h, fillColor=(colors_list[i] if colors_list else color), strokeColor=None))
        _s(d, label_w + w + 4, y + bar_h / 2 - 2.5, fmt(v), 7, bold=True)
        y -= bar_h + gap
    return d


def chart_barras_v(cats, vals, width=CONTENT_W, height=150, color=C_TEAL, fmt=num, rotar=False):
    n = len(cats)
    if n == 0 or not any(vals):
        return sin_datos()
    d = Drawing(width, height)
    left, bottom, top = 8, 22, 14
    area_w, area_h = width - left - 6, height - bottom - top
    vmax = max(vals) or 1.0
    slot = area_w / n
    bw = min(slot * 0.62, 34)
    d.add(Line(left, bottom, left + area_w, bottom, strokeColor=C_BORDER, strokeWidth=0.8))
    mostrar_val = n <= 16
    paso = 1 if n <= 16 else int(np.ceil(n / 16))
    for i, (c, v) in enumerate(zip(cats, vals)):
        x = left + i * slot + (slot - bw) / 2
        hh = area_h * v / vmax
        d.add(Rect(x, bottom, bw, hh, fillColor=color, strokeColor=None))
        if mostrar_val and v > 0:
            _s(d, x + bw / 2, bottom + hh + 3, fmt(v), 6.5, bold=True, anchor="middle")
        if i % paso == 0:
            _s(d, x + bw / 2, bottom - 10, str(c), 6.5, anchor="middle", fill=C_GRAY)
    return d


def chart_apiladas_v(cats, series, width=CONTENT_W, height=165):
    """series: [(nombre, valores, color)]"""
    n = len(cats)
    if n == 0:
        return sin_datos()
    d = Drawing(width, height)
    left, bottom, top = 8, 22, 26
    area_w, area_h = width - left - 6, height - bottom - top
    totales = [sum(s[1][i] for s in series) for i in range(n)]
    vmax = max(totales) or 1.0
    slot = area_w / n
    bw = min(slot * 0.7, 26)
    d.add(Line(left, bottom, left + area_w, bottom, strokeColor=C_BORDER, strokeWidth=0.8))
    paso = 1 if n <= 22 else int(np.ceil(n / 22))
    for i in range(n):
        x = left + i * slot + (slot - bw) / 2
        y0 = bottom
        for _, vals, col in series:
            hh = area_h * vals[i] / vmax
            if hh > 0:
                d.add(Rect(x, y0, bw, hh, fillColor=col, strokeColor=colors.white, strokeWidth=0.4))
            y0 += hh
        if totales[i] > 0 and n <= 22:
            _s(d, x + bw / 2, y0 + 2.5, str(int(totales[i])), 6.2, bold=True, anchor="middle")
        if i % paso == 0:
            _s(d, x + bw / 2, bottom - 9, trunc(cats[i], max(int(slot / 3.4), 4)), 6, anchor="middle", fill=C_GRAY)
    lx = left
    for nombre, _, col in series:
        d.add(Rect(lx, height - 12, 8, 8, fillColor=col, strokeColor=None))
        _s(d, lx + 12, height - 11, nombre, 7)
        lx += 90
    return d


def chart_donut(items, width=262, height=130):
    """items: [(etiqueta, valor, color)]"""
    items = [(l, float(v), c) for l, v, c in items if v and v > 0]
    if not items:
        return sin_datos("Sin datos para graficar.")
    d = Drawing(width, height)
    size = min(height - 10, 110)
    pie = Pie()
    pie.x, pie.y, pie.width, pie.height = 4, (height - size) / 2, size, size
    pie.data = [v for _, v, _ in items]
    pie.labels = None
    pie.sideLabels = 0
    pie.startAngle = 90
    pie.direction = "clockwise"
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 1.2
    for i, (_, _, c) in enumerate(items):
        pie.slices[i].fillColor = c
    d.add(pie)
    d.add(Circle(4 + size / 2, height / 2, size * 0.30, fillColor=colors.white, strokeColor=None))
    total = sum(v for _, v, _ in items)
    _s(d, 4 + size / 2, height / 2 - 4, num(total), 11, bold=True, anchor="middle")
    ly = height / 2 + len(items) * 8.5 - 6
    lx = size + 18
    for lab, v, c in items:
        d.add(Rect(lx, ly - 1, 8, 8, fillColor=c, strokeColor=None))
        _s(d, lx + 12, ly, f"{trunc(lab, 22)}", 7)
        _s(d, lx + 12, ly - 8.5, f"{num(v)}  ({v / total * 100:.0f}%)", 7, bold=True, fill=C_GRAY)
        ly -= 19
    return d


def chart_scatter(puntos, width=CONTENT_W, height=200, xtitle="", ytitle=""):
    """puntos: [(etiqueta, x, y, tamaño)]  (y en porcentaje 0-100)"""
    if not puntos:
        return sin_datos("Sin datos suficientes para el mapa de valor.")
    d = Drawing(width, height)
    L, B, T, R = 48, 30, 22, 24
    aw, ah = width - L - R, height - B - T
    xs, ys = [p[1] for p in puntos], [p[2] for p in puntos]
    xmin, xmax = min(xs), max(xs)
    padx = (xmax - xmin) * 0.18 or max(abs(xmax) * 0.1, 1.0)
    xmin, xmax = max(xmin - padx, 0), xmax + padx
    # Eje Y ajustado a los datos (múltiplos de 10) para que los puntos no se amontonen
    ymin = max(np.floor((min(ys) - 8) / 10) * 10, 0)
    ymax = min(np.ceil((max(ys) + 8) / 10) * 10, 100)
    if ymax - ymin < 20:
        ymax = min(ymin + 20, 100)
        ymin = max(ymax - 20, 0)
    smax = max(p[3] for p in puntos) or 1
    pasos = 4
    for k in range(pasos + 1):
        yv = ymin + (ymax - ymin) * k / pasos
        yy = B + ah * k / pasos
        d.add(Line(L, yy, L + aw, yy, strokeColor=C_BORDER, strokeWidth=0.4))
        _s(d, L - 5, yy - 2.5, f"{yv:.0f}%", 6.5, anchor="end", fill=C_GRAY)
    for k in range(5):
        xv = xmin + (xmax - xmin) * k / 4
        xx = L + aw * k / 4
        d.add(Line(xx, B, xx, B - 3, strokeColor=C_GRAY, strokeWidth=0.5))
        _s(d, xx, B - 11, money(xv), 6.5, anchor="middle", fill=C_GRAY)
    d.add(Line(L, B, L + aw, B, strokeColor=C_GRAY, strokeWidth=0.8))
    d.add(Line(L, B, L, B + ah, strokeColor=C_GRAY, strokeWidth=0.8))
    _s(d, L + aw / 2, 4, xtitle, 7, bold=True, anchor="middle", fill=C_GRAY)
    _s(d, L, height - 10, ytitle, 6.5, bold=True, fill=C_GRAY)

    ocupados = []   # rectángulos (x0, y0, x1, y1) de etiquetas ya colocadas
    for lab, x, y, sz in sorted(puntos, key=lambda p: -p[3]):
        px_ = L + aw * (x - xmin) / (xmax - xmin)
        py_ = B + ah * (min(max(y, ymin), ymax) - ymin) / (ymax - ymin)
        r = 4 + 7 * (sz / smax) ** 0.5
        d.add(Circle(px_, py_, r, fillColor=colors.Color(0, 0.64, 0.64, alpha=0.75), strokeColor=colors.white, strokeWidth=0.8))
        txt = trunc(lab, 18)
        w_txt = 4.1 * len(txt)
        for dy in (0, 10, -10, 20, -20, 30, -30):
            x0, y0 = px_ + r + 3, py_ - 3 + dy
            if x0 + w_txt > width:           # si no cabe a la derecha, va a la izquierda
                x0 = px_ - r - 3 - w_txt
            caja = (x0, y0 - 1, x0 + w_txt, y0 + 8)
            if not any(caja[0] < o[2] and caja[2] > o[0] and caja[1] < o[3] and caja[3] > o[1] for o in ocupados):
                break
        ocupados.append(caja)
        _s(d, caja[0], caja[1] + 1, txt, 7, bold=True)
    return d


# ============================================================
# 8. DOCUMENTO: PLANTILLAS, ENCABEZADO Y PIE
# ============================================================
class _NumberedCanvas(rl_canvas.Canvas):
    titulo_pie = ""

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
            self.line(MARGIN, 34, PAGE_W - MARGIN, 34)
            self.setFont("Helvetica", 7)
            self.setFillColor(C_GRAY)
            self.drawString(MARGIN, 23, f"JYPESA | Logística  -  {self.titulo_pie}  -  Generado e impreso con Nexion Smart Logistic")
            self.drawRightString(PAGE_W - MARGIN, 23, f"Página {self._pageNumber} de {n}")
            super().showPage()
        super().save()


def _hacer_paginas(titulo_mes, subtitulo_portada, logo_bytes):
    BANNER_H = 175

    def portada(c, doc):
        c.saveState()
        c.setFillColor(C_NAVY)
        c.rect(0, PAGE_H - BANNER_H, PAGE_W, BANNER_H, stroke=0, fill=1)
        c.setFillColor(C_TEAL)
        c.rect(0, PAGE_H - BANNER_H, PAGE_W, 5, stroke=0, fill=1)
        c.setFillColor(C_GOLD)
        c.rect(MARGIN, PAGE_H - 70, 38, 3, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#9FB3BF"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN, PAGE_H - 58, "JYPESA  |  LOGÍSTICA Y DISTRIBUCIÓN")
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 30)
        c.drawString(MARGIN, PAGE_H - 108, "REPORTE MENSUAL")
        c.setFont("Helvetica-Bold", 30)
        c.setFillColor(C_GOLD)
        c.drawString(MARGIN, PAGE_H - 142, titulo_mes)
        c.setFillColor(colors.HexColor("#9FB3BF"))
        c.setFont("Helvetica", 8.5)
        c.drawString(MARGIN, PAGE_H - 162, subtitulo_portada)
        if logo_bytes:
            try:
                
                c.drawImage(ImageReader(BytesIO(logo_bytes)), PAGE_W - MARGIN - 110, PAGE_H - 88, width=102, height=48,
                            preserveAspectRatio=True, mask='auto', anchor='c')
            except Exception:
                pass
        c.restoreState()

    def normal(c, doc):
        c.saveState()
        c.setFillColor(C_NAVY)
        c.rect(0, PAGE_H - 30, PAGE_W, 30, stroke=0, fill=1)
        c.setFillColor(C_TEAL)
        c.rect(0, PAGE_H - 30, PAGE_W, 2.5, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(MARGIN, PAGE_H - 19, "REPORTE MENSUAL DE LOGÍSTICA")
        c.setFillColor(C_GOLD)
        c.drawRightString(PAGE_W - MARGIN, PAGE_H - 19, titulo_mes)
        c.restoreState()

    f_portada = Frame(MARGIN, 44, CONTENT_W, PAGE_H - BANNER_H - 44 - 16, id="fp", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f_normal = Frame(MARGIN, 44, CONTENT_W, PAGE_H - 44 - 48, id="fn", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    return [PageTemplate(id="portada", frames=[f_portada], onPage=portada),
            PageTemplate(id="normal", frames=[f_normal], onPage=normal)]


# ============================================================
# 9. ARMADO DEL REPORTE
# ============================================================
def generar_reporte_pdf(df_base, df_muestras, anio, mes, hoy, precios=None, logo_bytes=None, muestras_msg=""):
    """Devuelve BytesIO con el PDF.  df_base: salida de preparar_base().  df_muestras: salida de preparar_muestras() o None."""
    titulo_mes = f"{MESES[mes - 1]} {anio}"
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    df_mes = filtrar_mes(df_base, "FECHA DE ENVÍO", anio, mes)
    R = calc_resumen(df_mes, hoy)
    D = calc_despachos(df_mes)
    B = calc_bi(df_mes)
    T = calc_top_clientes(df_mes, 20)
    C = calc_carga_regreso(df_base, anio, mes)
    G = calc_costos_regreso(df_base, anio, mes)
    K = calc_ranking(df_base, anio, mes)
    M = calc_muestras(df_muestras, anio, mes, precios) if df_muestras is not None else None

    story = [NextPageTemplate("normal")]

    # ---------------- PORTADA / RESUMEN EJECUTIVO ----------------
    story += [Spacer(1, 6), Paragraph("RESUMEN EJECUTIVO", ParagraphStyle("re", fontName="Helvetica-Bold", fontSize=11, textColor=C_SLATE, spaceAfter=8))]
    efect = None if K.get("vacio") else K["efectividad"]
    story += kpi_row([
        ("Pedidos del mes", num(R["total"]), HEX["slate"]),
        ("Entregados", f"{num(R['entregados'])} ({R['pct_entregado']:.0f}%)", HEX["green"]),
        ("Facturación", money(B["fact"]), HEX["teal"]),
        ("Costo logístico", pct(B["costo_log"]), HEX["purple"]),
        ("Despacho en 24 h háb.", pct(D["pct_ok"]) if D["total"] else "-", HEX["blue"]),
        ("Entregas a tiempo", pct(efect, 0) if efect is not None else "-", HEX["green"]),
        ("Tránsito promedio", f"{K['dias_prom']:.1f} días" if not K.get("vacio") else "-", HEX["orange"]),
        ("Inversión en muestras", money(M["inv"]) if M else "N/D", HEX["gold"]),
    ], ncols=4)

    hallazgos = []
    if R["total"]:
        hallazgos.append(f"Se enviaron <b>{num(R['total'])}</b> pedidos en {titulo_mes.title()}: <b>{num(R['entregados'])}</b> ya fueron entregados "
                         f"({R['pct_entregado']:.0f}%) y <b>{num(R['en_transito'])}</b> siguen en tránsito, de los cuales <b>{num(R['retrasados'])}</b> "
                         f"presentan retraso frente a su promesa de entrega.")
    else:
        hallazgos.append(f"No se encontraron pedidos con fecha de envío en {titulo_mes.title()}.")
    if D["total"]:
        hallazgos.append(f"<b>{D['pct_ok']:.1f}%</b> de las facturas salió de almacén dentro de las 24 horas hábiles ({num(D['ok'])} de {num(D['total'])}); "
                         f"<b>{num(D['no'])}</b> quedaron fuera de meta.")
    if not K.get("vacio") and K["entregados"]:
        txt = f"La efectividad global de entregas fue <b>{K['efectividad']:.0f}%</b> con un tránsito promedio de <b>{K['dias_prom']:.1f} días</b>."
        if K["top_puntual"] is not None:
            txt += f" La más puntual fue <b>{esc(K['top_puntual']['FLETERA'])}</b> ({K['top_puntual']['PCT_A_TIEMPO']:.0f}%)"
        if K["top_incid"] is not None and K["top_incid"]["INCIDENCIAS_PCT"] > 0:
            txt += f" y la que más incidencias registró, <b>{esc(K['top_incid']['FLETERA'])}</b> ({K['top_incid']['INCIDENCIAS_PCT']:.0f}% de sus envíos)."
        else:
            txt += "."
        hallazgos.append(txt)
    if B["fact"]:
        hallazgos.append(f"El costo de guías equivale a <b>{B['costo_log']:.1f}%</b> de la facturación ({money(B['guias'])} sobre {money(B['fact'])}); "
                         f"costo promedio por caja <b>{money(B['costo_caja'], 2)}</b>.")
    if not K.get("vacio") and K["barata"] is not None and K["cara"] is not None and K["barata"]["FLETERA"] != K["cara"]["FLETERA"]:
        hallazgos.append(f"Costo promedio por envío: la más económica fue <b>{esc(K['barata']['FLETERA'])}</b> ({money(K['barata']['COSTO_PROM_ENVIO'])}) "
                         f"y la más cara <b>{esc(K['cara']['FLETERA'])}</b> ({money(K['cara']['COSTO_PROM_ENVIO'])}).")
    if not C.get("vacio"):
        hallazgos.append(f"En cobro regreso se movieron <b>{num(C['total'])}</b> cajas; carrier dominante: <b>{esc(C['lider']['TRANSPORTE'])}</b> ({C['lider']['PCT']:.0f}%).")
    if not G.get("vacio"):
        mayor = G["res"].iloc[0]
        dentro = G["costo_log"] <= TARGET_COSTO_LOG
        hallazgos.append(f"Fletes de cobro regreso: se pagaron <b>{money(G['flete'])}</b> ({money(G['costo_caja'], 2)} por caja), equivalente a "
                         f"<b>{G['costo_log']:.2f}%</b> de la facturación de esa modalidad ({'dentro' if dentro else 'fuera'} del target de {TARGET_COSTO_LOG}%). "
                         f"El mayor gasto fue con <b>{esc(mayor['FLETERA'])}</b> ({mayor['pct_gasto']:.0f}% del total).")
    if M and M["total"]:
        hallazgos.append(f"Muestras: <b>{num(M['total'])}</b> envíos con una inversión de <b>{money(M['inv'])}</b> "
                         f"(productos {money(M['prod'])} + fletes {money(M['flete'])}); {M['pct_desp']:.0f}% despachado.")
    story.append(Paragraph("HALLAZGOS CLAVE", ParagraphStyle("hk", fontName="Helvetica-Bold", fontSize=11, textColor=C_SLATE, spaceBefore=4, spaceAfter=6)))
    for h in hallazgos:
        story.append(Paragraph(h, ST["bullet"], bulletText="•"))

    story += [Spacer(1, 8), Paragraph("CONTENIDO", ParagraphStyle("ct", fontName="Helvetica-Bold", fontSize=9, textColor=C_GRAY, spaceAfter=3)),
              Paragraph("01 Resumen del mes · 02 Efectividad de envíos · 03 Inteligencia de negocio · 04 Top 20 clientes · "
                        "05 Distribución de carga (cobro regreso) · 06 Cobro regreso: costo por fletera · 07 Ranking de fleteras · 08 Costos de muestras", ST["small"])]

    # ---------------- 01 RESUMEN DEL MES ----------------
    story += [PageBreak()] + seccion(1, "RESUMEN DEL MES", f"Pedidos, entregas y retrasos con fecha de envío en {titulo_mes.title()}")
    story += kpi_row([
        ("Pedidos", num(R["total"]), HEX["slate"]),
        ("Entregados", num(R["entregados"]), HEX["green"]),
        ("En tránsito", num(R["en_transito"]), HEX["blue"]),
        ("En tiempo", num(R["en_tiempo"]), HEX["gold"]),
        ("Con retraso", num(R["retrasados"]), HEX["red"]),
    ], ncols=5)
    if R["total"]:
        don = chart_donut([("Entregados", R["entregados"], C_GREEN), ("Tránsito en tiempo", R["en_tiempo"], C_GOLD),
                           ("Tránsito con retraso", R["retrasados"], C_RED)])
        rf = R["ret_fletera"]
        der = chart_barras_h(list(rf.items()), width=262, label_w=100, color=C_RED, colors_list=None) if len(rf) else sin_datos("Sin pedidos con retraso en este periodo.")
        story.append(lado_a_lado(don, der, "Distribución de pedidos del mes", "Pedidos con retraso por fletera"))
        story.append(Spacer(1, 10))
        story.append(KeepTogether([subtitulo("Pedidos por destino (top 8)"),
                                   chart_barras_h(list(R["destinos"].items()), color=C_GOLD, label_w=170)]))
        story += [Spacer(1, 6), Paragraph("Nota: 'En tiempo' y 'Con retraso' se evalúan sobre pedidos aún en tránsito, comparando la promesa de entrega contra la fecha de generación "
                                          f"de este reporte ({hoy.strftime('%d/%m/%Y')}).", ST["nota"])]
    else:
        story.append(sin_datos())

    # ---------------- 02 EFECTIVIDAD DE ENVÍOS ----------------
    story += [PageBreak()] + seccion(2, "EFECTIVIDAD DE ENVÍOS", "Despachos de almacén dentro de 24 horas hábiles (fines de semana y feriados no cuentan)")
    if D["total"]:
        story += kpi_row([("Total facturas evaluadas", num(D["total"]), HEX["slate"]),
                          ("A tiempo", f"{num(D['ok'])}  ·  {D['pct_ok']:.1f}%", HEX["green"]),
                          ("Fuera de meta", f"{num(D['no'])}  ·  {D['pct_no']:.1f}%", HEX["red"])], ncols=3)
        pd_ = D["por_dia"]
        cats = [i.strftime("%d/%m") for i in pd_.index]
        story.append(KeepTogether([subtitulo("Despachos por día de salida"),
                                   chart_apiladas_v(cats, [("A tiempo", pd_["A Tiempo"].astype(int).tolist(), C_GREEN),
                                                           ("Fuera de tiempo", pd_["Fuera de Tiempo"].astype(int).tolist(), C_RED)])]))
        story.append(Spacer(1, 8))
        if not D["fuera"].empty:
            rows = [[str(r["NÚMERO DE PEDIDO"]),
                     r["EMISION"].strftime("%d/%m/%Y %H:%M") if pd.notna(r["EMISION"]) else "S/D",
                     r["FECHA DE ENVÍO"].strftime("%d/%m/%Y %H:%M") if pd.notna(r["FECHA DE ENVÍO"]) else "S/D",
                     f"{int(r['DIAS_HABILES'])}"] for _, r in D["fuera"].iterrows()]
            story.append(KeepTogether([subtitulo("Pedidos con mayor retraso en despacho (top 12)"),
                                       tabla(["PEDIDO", "EMISIÓN", "SALIDA DE ALMACÉN", "DÍAS HÁBILES"], rows, [150, 130, 150, 110], ["L", "C", "C", "C"])]))
        else:
            story.append(Paragraph("Todos los despachos del periodo salieron dentro de la meta.", ST["body"]))
        if D["sin_datos"]:
            story += [Spacer(1, 4), Paragraph(f"{num(D['sin_datos'])} registro(s) sin fecha de emisión/salida no se incluyeron en el cálculo.", ST["nota"])]
    else:
        story.append(sin_datos())

    # ---------------- 03 INTELIGENCIA DE NEGOCIO ----------------
    story += [PageBreak()] + seccion(3, "INTELIGENCIA DE NEGOCIO", "Facturación, costos logísticos y comparativo por fletera")
    story += kpi_row([("Facturación", money(B["fact"]), HEX["green"]), ("Costo guías", money(B["guias"]), HEX["blue"]),
                      ("Costos adicionales", money(B["adic"]), HEX["gold"])], ncols=3)
    story += kpi_row([("Costo logístico (guías / fact.)", pct(B["costo_log"]), HEX["purple"]),
                      ("Cajas enviadas", num(B["cajas"]), HEX["slate"]),
                      ("Costo promedio por caja", money(B["costo_caja"], 2), HEX["red"])], ncols=3)
    pf = B["por_fletera"]
    if not pf.empty:
        top_f = pf.head(8)
        izq = chart_barras_h([(r.FLETERA, r.facturacion) for r in top_f.itertuples()], width=262, label_w=92, color=C_GREEN, fmt=money)
        top_o = pf.sort_values("operativo", ascending=False).head(8)
        der = chart_barras_h([(r.FLETERA, r.operativo) for r in top_o.itertuples()], width=262, label_w=92, color=C_ORANGE, fmt=money)
        story.append(lado_a_lado(izq, der, "Facturación generada por fletera", "Costo operativo por fletera (guía + adic.)"))
        story.append(Spacer(1, 10))
        rows = [[r.FLETERA, num(r.pedidos), money(r.facturacion), money(r.guias), money(r.adic), pct(r.pct_log),
                 num(r.cajas), money(r.costo_caja, 2) if pd.notna(r.costo_caja) else "-"] for r in pf.head(12).itertuples()]
        story.append(KeepTogether([subtitulo("Detalle por fletera"),
                                   tabla(["FLETERA", "PEDIDOS", "FACTURACIÓN", "COSTO GUÍAS", "COSTOS ADIC.", "% LOGÍSTICO", "CAJAS", "COSTO/CAJA"], rows,
                                         [95, 50, 80, 70, 65, 62, 50, 68], ["L", "R", "R", "R", "R", "R", "R", "R"])]))
        story += [Spacer(1, 4), Paragraph("Costo/caja = (guía + adicionales) / cajas. Costo logístico = costo de guías / facturación.", ST["nota"])]
    else:
        story.append(sin_datos())

    # ---------------- 04 TOP 20 CLIENTES ----------------
    story += [PageBreak()] + seccion(4, "TOP 20 CLIENTES DE DISTRIBUCIÓN", "Clientes con mayor facturación del periodo y forma de envío")
    top = T["top"]
    if not top.empty:
        story += kpi_row([("Facturación total del periodo", money(T["total_fact"]), HEX["green"]),
                          ("Concentración del Top 20", pct(T["share_top"]), HEX["purple"]),
                          ("Clientes distintos", num(df_mes[df_mes['NOMBRE DEL CLIENTE'] != '']['NOMBRE DEL CLIENTE'].nunique()), HEX["slate"])], ncols=3)
        rows = [[str(i + 1), trunc(r["NOMBRE DEL CLIENTE"], 46), num(r["pedidos"]), num(r["cajas"]),
                 money(r["facturacion"]), money(r["guias"]), pct(r["share"])] for i, (_, r) in enumerate(top.iterrows())]
        story.append(tabla(["#", "CLIENTE", "PEDIDOS", "CAJAS", "FACTURACIÓN", "COSTO GUÍA", "% DEL TOTAL"], rows,
                           [22, 208, 50, 45, 78, 70, 67], ["C", "L", "R", "R", "R", "R", "R"],
                           total_row=["", "TOP 20", num(top["pedidos"].sum()), num(top["cajas"].sum()), money(top["facturacion"].sum()),
                                      money(top["guias"].sum()), pct(T["share_top"])]))
        if not T["forma"].empty:
            colores = [C_TEAL, C_BLUE, C_GOLD, C_PURPLE, C_RED, C_ORANGE, C_GREEN, C_GRAY]
            story += [Spacer(1, 10), KeepTogether([subtitulo("Distribución por forma de envío (pedidos)"),
                                                   chart_donut([(k, v, colores[i % len(colores)]) for i, (k, v) in enumerate(T["forma"].head(7).items())], width=CONTENT_W, height=120)])]
    else:
        story.append(sin_datos())

    # ---------------- 05 DISTRIBUCIÓN DE CARGA (COBRO REGRESO) ----------------
    story += [PageBreak()] + seccion(5, "DISTRIBUCIÓN DE CARGA  ·  COBRO REGRESO", "Volumen de cajas por carrier y destino (solo flujo de cobro regreso)")
    if not C.get("vacio"):
        story += kpi_row([("Volumen total (cajas)", num(C["total"]), HEX["slate"]),
                          ("Carrier dominante", f"{C['lider']['TRANSPORTE']} · {C['lider']['PCT']:.0f}%", HEX["green"]),
                          ("Destinos distintos", num(C["destinos"]), HEX["teal"])], ncols=3)
        story.append(KeepTogether([subtitulo("Cajas por carrier"),
                                   chart_barras_h([(r.TRANSPORTE, r.CAJAS) for r in C["part"].itertuples()], label_w=170, color=C_TEAL,
                                                  fmt=lambda v: f"{num(v)}")]))
        story.append(Spacer(1, 8))
        rutas = C["rutas"]
        MAXF = 20
        rows = [[r["TRANSPORTE"], r["DESTINO"], r["FORMA DE ENVIO"], num(r["CAJAS"])] for _, r in rutas.head(MAXF).iterrows()]
        story.append(subtitulo("Detalle de rutas (carrier / destino)"))
        story.append(tabla(["CARRIER", "DESTINO", "FORMA DE ENVÍO", "CAJAS"], rows, [190, 140, 130, 80], ["L", "L", "L", "R"],
                           total_row=["TOTAL", "", "", num(C["total"])]))
        if len(rutas) > MAXF:
            story += [Spacer(1, 3), Paragraph(f"Se muestran las {MAXF} rutas principales de {len(rutas)}. El total incluye todas.", ST["nota"])]
    else:
        story.append(sin_datos(f"No se encontraron registros de COBRO REGRESO en {titulo_mes.title()}."))

    # ---------------- 06 COBRO REGRESO: COSTO POR FLETERA ----------------
    story += [PageBreak()] + seccion(6, "COBRO REGRESO  ·  COSTO POR FLETERA",
                                     "Lo que paga JYPESA por fletes de regreso: gasto, costo por caja y servicio por fletera")
    if not G.get("vacio"):
        col_log = HEX["green"] if G["costo_log"] <= TARGET_COSTO_LOG else HEX["red"]
        story += kpi_row([
            ("Costo de flete (guía + adic.)", money(G["flete"], 2), HEX["slate"]),
            ("Cajas enviadas", num(G["cajas"]), HEX["teal"]),
            ("Costo por caja", money(G["costo_caja"], 2), HEX["orange"]),
            (f"Costo logístico (target {TARGET_COSTO_LOG}%)", f"{G['costo_log']:.2f}%", col_log),
        ], ncols=4)
        story += kpi_row([
            ("Facturación cobro regreso", money(G["fact"], 2), HEX["green"]),
            ("Eficiencia de entrega", pct(G["efic"]) if G["efic"] is not None else "-", HEX["blue"]),
            ("Valuación de incidencias", money(G["val"], 2), HEX["red"]),
            ("% de incidencias", pct(G["pct_inc"]), HEX["gold"]),
        ], ncols=4)
        story.append(subtitulo("Desglose por concepto (informativo)"))
        story += kpi_row([("Muestras / recolecciones", money(G["muestras"], 2), HEX["purple"]),
                          ("Consignas", money(G["consignas"], 2), HEX["purple"]),
                          ("F nacional", money(G["fnacional"], 2), HEX["purple"])], ncols=3)

        res = G["res"]
        izq = chart_barras_h([(r.FLETERA, r.flete) for r in res.itertuples()], width=262, label_w=92, color=C_ORANGE, fmt=money)
        cc = res[res["costo_caja"].notna()].sort_values("costo_caja", ascending=True)
        der = (chart_barras_h([(r.FLETERA, r.costo_caja) for r in cc.itertuples()], width=262, label_w=92, color=C_GOLD,
                              fmt=lambda v: money(v, 2)) if not cc.empty else sin_datos("Sin cajas registradas."))
        story.append(lado_a_lado(izq, der, "Gasto de flete por fletera", "Costo promedio por caja"))
        story.append(Spacer(1, 10))

        rows = [[trunc(r.FLETERA, 24), num(r.envios), num(r.cajas), money(r.flete, 2), pct(r.pct_gasto, 0),
                 money(r.costo_caja, 2) if pd.notna(r.costo_caja) else "-", pct(r.pct_log, 2) if pd.notna(r.pct_log) else "-",
                 pct(r.efic, 0) if pd.notna(r.efic) else "-", money(r.val, 2)] for r in res.itertuples()]
        story.append(KeepTogether([subtitulo("Detalle por fletera (cobro regreso)"),
                                   tabla(["FLETERA", "ENVÍOS", "CAJAS", "COSTO FLETE", "% GASTO", "COSTO/CAJA", "% LOGÍSTICO", "% A TIEMPO", "VALUACIÓN INC."],
                                         rows, [100, 40, 42, 70, 48, 58, 52, 56, 74],
                                         ["L", "R", "R", "R", "R", "R", "R", "R", "R"],
                                         total_row=["TOTAL", num(G["registros"]), num(G["cajas"]), money(G["flete"], 2), "100%",
                                                    money(G["costo_caja"], 2), pct(G["costo_log"], 2),
                                                    pct(G["efic"], 0) if G["efic"] is not None else "-", money(G["val"], 2)])]))
        story += [Spacer(1, 4), Paragraph(
            f"Solo incluye envíos con forma de envío COBRO REGRESO. Costo de flete = guía + costos adicionales. Costo logístico = costo de flete / facturación de esta modalidad "
            f"(target {TARGET_COSTO_LOG}%); a diferencia de la sección 03, aquí se incluyen los adicionales y no se mezclan otras modalidades. "
            "% a tiempo = entregas con fecha real menor o igual a la promesa, sobre envíos con ambas fechas. "
            "El desglose por concepto usa solo el costo de guía y es informativo.", ST["nota"])]
    else:
        story.append(sin_datos(f"No se encontraron envíos de COBRO REGRESO en {titulo_mes.title()}."))

    # ---------------- 07 RANKING DE FLETERAS ----------------
    story += [PageBreak()] + seccion(7, "RANKING DE FLETERAS", "Efectividad de entregas, tiempos de tránsito y costo promedio (fleteras principales)")
    if not K.get("vacio"):
        res = K["res"]
        # Tabla resumen
        story.append(subtitulo("Resumen comparativo"))
        orden = res.sort_values("PCT_A_TIEMPO", ascending=False, na_position="last")
        rows = [[r.FLETERA, num(r.ENVIOS), num(r.ENTREGADOS), pct(r.PCT_A_TIEMPO, 0), pct(r.INCIDENCIAS_PCT, 0),
                 f"{r.DIAS_PROM:.1f}" if pd.notna(r.DIAS_PROM) else "-", money(r.COSTO_PROM_ENVIO),
                 money(r.COSTO_PROM_CAJA, 2) if pd.notna(r.COSTO_PROM_CAJA) else "-"] for r in orden.itertuples()]
        story.append(tabla(["FLETERA", "ENVÍOS", "ENTREGADOS", "% A TIEMPO", "% INCIDENCIAS", "DÍAS PROM.", "COSTO/ENVÍO", "COSTO/CAJA"], rows,
                           [96, 48, 62, 58, 66, 56, 74, 80], ["L", "R", "R", "R", "R", "R", "R", "R"]))
        story.append(Spacer(1, 12))

        # 6.1 Efectividad de entregas
        story.append(CondPageBreak(300))
        story.append(subtitulo("Efectividad de entregas  //  cumplimiento de promesa"))
        tp, ti = K["top_puntual"], K["top_incid"]
        story += kpi_row([("Efectividad global", f"{K['efectividad']:.0f}%", HEX["green"]),
                          ("Pedidos entregados", num(K["entregados"]), HEX["slate"]),
                          (f"Más puntual: {tp['FLETERA']}" if tp is not None else "Más puntual", pct(tp["PCT_A_TIEMPO"], 0) if tp is not None else "-", HEX["gold"]),
                          (f"Más incidencias: {ti['FLETERA']}" if ti is not None else "Más incidencias", pct(ti["INCIDENCIAS_PCT"], 0) if ti is not None else "-", HEX["orange"])], ncols=4)
        con_ent = res[res["ENTREGADOS"] > 0]
        if not con_ent.empty:
            a = con_ent.sort_values("PCT_A_TIEMPO", ascending=False)
            izq = chart_barras_h([(r.FLETERA, r.PCT_A_TIEMPO) for r in a.itertuples()], width=262, label_w=92, color=C_GREEN, fmt=lambda v: f"{v:.0f}%")
            der = chart_apiladas_v([r.FLETERA for r in a.itertuples()],
                                   [("A tiempo", a["A_TIEMPO"].astype(int).tolist(), C_GREEN), ("Con retraso", a["RETRASO"].astype(int).tolist(), C_ORANGE)],
                                   width=262, height=max(120, 28 + len(a) * 14))
            story.append(lado_a_lado(izq, der, "Ranking de efectividad (%)", "Entregas a tiempo vs. con retraso"))
        story.append(Spacer(1, 12))

        # 6.2 Tiempos
        story.append(CondPageBreak(260))
        story.append(subtitulo("Tiempos de tránsito  //  días de envío a entrega"))
        ra, le = K["rapida"], K["lenta"]
        story += kpi_row([("Tiempo promedio general", f"{K['dias_prom']:.1f} días", HEX["teal"]),
                          ("Envíos analizados", num(K["dias_n"]), HEX["slate"]),
                          (f"Más rápida: {ra['FLETERA']}" if ra is not None else "Más rápida", f"{ra['DIAS_PROM']:.1f} días" if ra is not None else "-", HEX["green"]),
                          (f"Más lenta: {le['FLETERA']}" if le is not None else "Más lenta", f"{le['DIAS_PROM']:.1f} días" if le is not None else "-", HEX["red"])], ncols=4)
        con_t = res[res["DIAS_PROM"].notna()].sort_values("DIAS_PROM", ascending=True)
        if not con_t.empty:
            story.append(KeepTogether([subtitulo("Días promedio de tránsito por fletera"),
                                       chart_barras_h([(r.FLETERA, r.DIAS_PROM) for r in con_t.itertuples()], label_w=130, color=C_BLUE, fmt=lambda v: f"{v:.1f} d")]))
        story.append(Spacer(1, 12))

        # 6.3 Costos
        story.append(CondPageBreak(330))
        story.append(subtitulo("Costo promedio por paquetería  //  guía + adicionales"))
        ba, ca = K["barata"], K["cara"]
        story += kpi_row([("Costo prom. por envío", money(K["costo_envio"]), HEX["orange"]),
                          ("Costo prom. por caja", money(K["costo_caja"], 2), HEX["gold"]),
                          (f"Más económica: {ba['FLETERA']}" if ba is not None else "Más económica", money(ba["COSTO_PROM_ENVIO"]) if ba is not None else "-", HEX["green"]),
                          (f"Más cara: {ca['FLETERA']}" if ca is not None else "Más cara", money(ca["COSTO_PROM_ENVIO"]) if ca is not None else "-", HEX["red"])], ncols=4)
        costo = res[res["ENVIOS"] > 0].sort_values("COSTO_PROM_ENVIO", ascending=True)
        caja = res[res["COSTO_PROM_CAJA"].notna()].sort_values("COSTO_PROM_CAJA", ascending=True)
        izq = chart_barras_h([(r.FLETERA, r.COSTO_PROM_ENVIO) for r in costo.itertuples()], width=262, label_w=92, color=C_ORANGE, fmt=money)
        der = chart_barras_h([(r.FLETERA, r.COSTO_PROM_CAJA) for r in caja.itertuples()], width=262, label_w=92, color=C_GOLD, fmt=lambda v: money(v, 2)) if not caja.empty else sin_datos("Sin cajas registradas.")
        story.append(lado_a_lado(izq, der, "Costo promedio por envío", "Costo promedio por caja"))
        story.append(Spacer(1, 10))
        mapa = res[res["PCT_A_TIEMPO"].notna() & (res["ENVIOS"] > 0)]
        story.append(KeepTogether([subtitulo("Mapa de valor: costo promedio vs. efectividad por fletera"),
                                   chart_scatter([(r.FLETERA, r.COSTO_PROM_ENVIO, r.PCT_A_TIEMPO, r.ENVIOS) for r in mapa.itertuples()],
                                                 xtitle="COSTO PROMEDIO POR ENVÍO ($)", ytitle="% ENTREGAS A TIEMPO"),
                                   Paragraph("Más arriba = más puntual; más a la izquierda = más económica. El tamaño del círculo es el volumen de envíos.", ST["nota"])]))
    else:
        story.append(sin_datos())

    # ---------------- 08 COSTOS DE MUESTRAS ----------------
    story += [PageBreak()] + seccion(8, "COSTOS DE MUESTRAS", "Inversión en producto y fletes de muestras del periodo")
    if M is None:
        story.append(sin_datos(muestras_msg or "No fue posible cargar la información de muestras."))
    elif not M["total"]:
        story.append(sin_datos(f"No hay envíos de muestras registrados en {titulo_mes.title()}."))
    else:
        story += kpi_row([("Total de envíos", num(M["total"]), HEX["slate"]), ("Costo productos", money(M["prod"]), HEX["blue"]),
                          ("Costo fletes", money(M["flete"]), HEX["purple"]), ("Inversión total", money(M["inv"]), HEX["green"])], ncols=4)
        story += kpi_row([("Costo promedio por envío", money(M["prom"]), HEX["orange"]), ("% despachado", pct(M["pct_desp"], 0), HEX["gold"]),
                          ("Agente con más envíos", trunc(M["top_agente"], 26), HEX["red"])], ncols=3)
        story.append(KeepTogether([subtitulo("Inversión por mes (últimos 12 meses)"),
                                   chart_barras_v([c for c, _ in M["tendencia"]], [v for _, v in M["tendencia"]], height=140, color=C_TEAL, fmt=lambda v: money(v))]))
        story.append(Spacer(1, 8))
        if not M["por_sol"].empty:
            rows = [[trunc(r.SOL, 34), num(r.envios), money(r.prod), money(r.flete), money(r.inversion)] for r in M["por_sol"].itertuples()]
            story.append(KeepTogether([subtitulo("Solicitantes / agentes (top 10 por inversión)"),
                                       tabla(["SOLICITANTE", "ENVÍOS", "PRODUCTOS", "FLETE", "INVERSIÓN"], rows, [200, 55, 95, 90, 100], ["L", "R", "R", "R", "R"])]))
        story.append(CondPageBreak(250))
        story.append(Spacer(1, 8))
        izq = chart_barras_h(list(M["top_dest"].items()), width=262, label_w=120, color=C_BLUE) if len(M["top_dest"]) else sin_datos("Sin datos.")
        der = chart_barras_h(list(M["flete_paq"].items()), width=262, label_w=100, color=C_PURPLE, fmt=money) if len(M["flete_paq"]) else sin_datos("Sin datos.")
        story.append(lado_a_lado(izq, der, "Top destinos / hoteles (envíos)", "Costo de flete por paquetería"))
        story.append(Spacer(1, 8))
        if len(M["prod_top"]):
            story.append(KeepTogether([subtitulo("Productos más solicitados (piezas)"),
                                       chart_barras_h([(str(k)[:40].upper(), v) for k, v in M["prod_top"].items()], label_w=210, color=C_GOLD)]))

    # ---------------- CONSTRUCCIÓN ----------------
    buf = BytesIO()
    doc = BaseDocTemplate(buf, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=48, bottomMargin=44,
                          title=f"Reporte Mensual de Logística - {titulo_mes}", author="JYPESA Logística")
    doc.addPageTemplates(_hacer_paginas(titulo_mes, f"Generado el {ahora}  ·  Fuente: Matriz de envíos y registro de muestras", logo_bytes))

    class _Canvas(_NumberedCanvas):
        titulo_pie = f"Reporte mensual {titulo_mes.title()}"
    doc.build(story, canvasmaker=_Canvas)
    buf.seek(0)
    return buf


# ============================================================
# 10. INTERFAZ MÍNIMA (solo elegir mes y generar)
# ============================================================
def main():
    st.markdown("""
<style>
    div.stButton > button, div.stButton > button:link, div.stButton > button:visited {
        background-color: #2B343B !important; color: #FFFFFF !important; border: 1px solid #2B343B !important;
        border-radius: 5px !important; transition: all 0.3s ease !important; width: 100% !important; box-shadow: none !important;
    }
    div.stButton > button:hover, div.stButton > button:focus, div.stButton > button:active {
        background-color: #00A3A3 !important; color: #FFFFFF !important; border-color: #00A3A3 !important; box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

    st.markdown(
        "<div style='padding: 6px 0 14px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 20px;'>"
        "<span style='color:#FFFFFF; font-size:13px; font-weight:800; letter-spacing:2.5px; text-transform:uppercase;'>"
        "REPORTES // REPORTE MENSUAL EN PDF PARA DIRECCIÓN</span></div>", unsafe_allow_html=True)

    try:
        import pytz
        hoy = pd.Timestamp(datetime.now(pytz.timezone("America/Mexico_City")).date())
    except Exception:
        hoy = pd.Timestamp(datetime.now().date())

    with st.spinner("Cargando base de envíos..."):
        try:
            df_raw = cargar_matriz()
        except Exception as e:
            st.error(f"No se pudo cargar la matriz de envíos: {e}")
            return
    df_base = preparar_base(df_raw)

    anios = sorted({int(y) for y in df_base["FECHA DE ENVÍO"].dt.year.dropna().unique()} | {hoy.year}, reverse=True)
    mes_prev = hoy.month - 1 or 12
    anio_prev = hoy.year if hoy.month > 1 else hoy.year - 1

    c1, c2, c3 = st.columns([1.3, 1, 1.6], vertical_alignment="bottom")
    mes_sel = c1.selectbox("MES", MESES, index=mes_prev - 1)
    anio_sel = c2.selectbox("AÑO", anios, index=anios.index(anio_prev) if anio_prev in anios else 0)
    generar = c3.button("GENERAR REPORTE PDF", use_container_width=True)

    st.caption("Incluye: resumen del mes, efectividad de envíos, inteligencia de negocio, top 20 clientes, distribución de carga (cobro regreso), "
               "costo por fletera en cobro regreso, ranking de fleteras (efectividad, tiempos y costo promedio) y costos de muestras.")

    if generar:
        mes_num = MESES.index(mes_sel) + 1
        with st.spinner("Armando el reporte..."):
            df_muestras, msg_muestras = None, ""
            if MUESTRAS_OK:
                try:
                    df_m, _sha = obtener_datos_github()
                    if df_m is not None and not df_m.empty:
                        df_muestras = preparar_muestras(df_m)
                    else:
                        msg_muestras = "No hay registros de muestras cargados."
                except Exception as e:
                    msg_muestras = f"No se pudo leer el registro de muestras: {e}"
            else:
                msg_muestras = f"No se pudo importar muestras_common: {MUESTRAS_ERR}"
            try:
                pdf = generar_reporte_pdf(df_base, df_muestras, int(anio_sel), mes_num, hoy,
                                          precios=PRECIOS_MUESTRAS, logo_bytes=obtener_logo_bytes(), muestras_msg=msg_muestras)
                st.session_state["rep_mensual_pdf"] = {"bytes": pdf.getvalue(), "nombre": f"Reporte_Mensual_Logistica_{mes_sel}_{anio_sel}.pdf"}
                if msg_muestras:
                    st.warning(f"Reporte generado, pero la sección de muestras quedó sin datos: {msg_muestras}")
                else:
                    st.success("¡Reporte generado!")
            except Exception as e:
                st.error(f"No se pudo generar el reporte: {e}")

    rep = st.session_state.get("rep_mensual_pdf")
    if rep:
        st.download_button("DESCARGAR REPORTE PDF", data=rep["bytes"], file_name=rep["nombre"], mime="application/pdf",
                           use_container_width=True, key="rep_mensual_dl")


if __name__ == "__main__":
    main()
