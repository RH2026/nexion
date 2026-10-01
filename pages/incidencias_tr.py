import base64
from datetime import datetime, timedelta
from io import StringIO, BytesIO
import io
import html as _html
import json
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
from auth import exigir_autenticacion
from components.layout import render_layout

exigir_autenticacion("Incidencias")


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Logistics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LAYOUT MAESTRO (estilos, sesión, permisos, header, buscador, menú y footer)
# ============================================================
render_layout(modulo_actual="SEGUIMIENTO", submodulo_actual="INCIDENCIAS")


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


# ================================================================================
# 5. INTERFAZ PRINCIPAL CON SISTEMA DE TABS
#    TAB 0 -> Render principal   TAB 1 -> Captura   TAB 2 -> Edición
# ================================================================================

def main():
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    # ── CONFIGURACIÓN DEL REPOSITORIO DE INCIDENCIAS ─────────────────────────────────────
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "incidencias.csv"
    MATRIZ_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/Matriz_Excel_Dashboard.csv"

    usuario_actual = str(st.session_state.get("usuario", st.session_state.get("usuario_activo", ""))).strip()
    nombre_usuario_actual = str(st.session_state.get("nombre_completo", "")).strip().upper()
    es_admin_session = st.session_state.get("es_admin", False)
    es_administrador = es_admin_session or (usuario_actual.upper() in ["RIGOBERTO", "RIGOBERTO HERNÁNDEZ"])

    COLUMNAS_INCIDENCIAS = [
        "FOLIO", "TIPO", "CREADOR", "RESPONSABLE", "PRIORIDAD", "VINCULO_BUSQUEDA",
        "CLIENTE_DESTINO", "PEDIDO_GUIA", "ID_SEGUIMIENTO", "ID_QUEJA",
        "DETALLE_INCIDENCIA", "ACCIONES", "ESTATUS"
    ]

    OPC_TIPO = ["Incidencia", "Tarea (Task)"]
    OPC_PRIORIDAD = ["Media", "Urgente", "Alta", "Baja"]
    OPC_ESTATUS = ["PENDIENTE", "EN PROCESO", "SOLUCIONADO", "RECHAZADO"]
    LISTA_COLABORADORES = [
        "RIGOBERTO HERNÁNDEZ", "RIGOBERTO DEL REAL", "ALEJANDRA GOMEZ",
        "CYNTHIA ORNELAS", "BRENDA PIZANO", "CARLOS FIALKO",
        "CLAUDIA JIMENEZ", "CARLOS VAZQUEZ", "SANDRA",
        "ALEJANDRA SANCHEZ", "MARTHA CASAS", "CRISTOBAL A", "URI EL CAPI"
    ]

    esc = lambda v: _html.escape(str(v))

    @st.cache_data(ttl=600)
    def cargar_matriz_global():
        try:
            r = requests.get(f"{MATRIZ_URL}?t={int(time.time())}")
            if r.status_code == 200:
                df = pd.read_csv(StringIO(r.text))
                df.columns = [c.strip().upper() for c in df.columns]
                return df
        except Exception:
            return None
        return None

    df_global = cargar_matriz_global()

    API_URL = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    RAMA = "main"

    def _gh_headers(extra=None):
        if not TOKEN:
            raise RuntimeError("No se encontró el GITHUB_TOKEN en los secrets.")
        h = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        if extra:
            h.update(extra)
        return h

    def _normalizar_inc(df):
        df = df.copy()
        df.columns = [str(c).strip().upper() for c in df.columns]
        for c in COLUMNAS_INCIDENCIAS:
            if c not in df.columns:
                df[c] = ""
        df = df[COLUMNAS_INCIDENCIAS]
        for c in COLUMNAS_INCIDENCIAS:
            df[c] = df[c].fillna("").astype(str).replace("nan", "")
        return df.reset_index(drop=True)

    def _leer_incidencias_fresco():
        """Lee incidencias.csv por la API de GitHub (SIN caché del CDN). Devuelve (df, sha).
        Si el archivo no existe devuelve (df vacío, None)."""
        params = {"ref": RAMA, "t": time.time_ns()}
        r = requests.get(API_URL, headers=_gh_headers(), params=params, timeout=20)
        if r.status_code == 404:
            return pd.DataFrame(columns=COLUMNAS_INCIDENCIAS), None
        r.raise_for_status()
        data = r.json()
        if data.get("content"):
            raw = base64.b64decode(data["content"])
        else:  # archivo grande: la API no manda el contenido en base64
            r2 = requests.get(API_URL, headers=_gh_headers({"Accept": "application/vnd.github.raw"}),
                              params=params, timeout=30)
            r2.raise_for_status()
            raw = r2.content
        df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig", dtype=str, keep_default_na=False)
        return _normalizar_inc(df), data.get("sha")

    def _put_incidencias(df, sha, mensaje):
        payload = {
            "message": mensaje,
            "content": base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode(),
            "branch": RAMA,
        }
        if sha:
            payload["sha"] = sha
        return requests.put(API_URL, headers=_gh_headers(), json=payload, timeout=30)

    def guardar_incidencia_github(nueva_data, es_nuevo, mensaje):
        """Guarda SOLO esta fila. Relee el archivo justo antes de escribir (nunca pisa lo de
        otros) y reintenta si hay conflicto de versión. Devuelve (ok, df_final, folio_usado)."""
        for intento in range(4):
            try:
                df, sha = _leer_incidencias_fresco()
            except Exception as e:
                st.error(f"No se pudo leer GitHub antes de guardar: {e}")
                return False, None, None

            datos = dict(nueva_data)
            existe = df["FOLIO"] == datos["FOLIO"]

            # Registro nuevo cuyo folio ya lo ocupó otra persona: se le asigna el siguiente libre
            if es_nuevo and existe.any():
                nums = df["FOLIO"].str.extract(r"REG-(\d+)")[0].dropna().astype(int)
                datos["FOLIO"] = f"REG-{(nums.max() if not nums.empty else 0) + 1:03d}"
                existe = df["FOLIO"] == datos["FOLIO"]

            fila = {c: str(datos.get(c, "")) for c in COLUMNAS_INCIDENCIAS}
            if existe.any():
                idx = df.index[existe][0]          # se edita en su lugar (conserva el orden)
                for c in COLUMNAS_INCIDENCIAS:
                    df.at[idx, c] = fila[c]
            else:
                df = pd.concat([df, pd.DataFrame([fila])], ignore_index=True)

            try:
                r = _put_incidencias(df, sha, mensaje)
            except Exception as e:
                st.error(f"No se pudo guardar en GitHub: {e}")
                return False, None, None

            if r.status_code in (200, 201):
                return True, df, datos["FOLIO"]
            if r.status_code in (409, 422) and intento < 3:
                time.sleep(0.6 * (intento + 1))   # alguien más guardó: releer y reintentar
                continue
            st.error(f"Error de GitHub: {r.status_code} - {r.text[:200]}")
            return False, None, None

        st.error("No se pudo guardar por conflictos repetidos. Intenta de nuevo.")
        return False, None, None

    def guardar_tabla_completa(df_nuevo, df_base):
        """Para el editor avanzado (reemplaza la tabla). Solo escribe si nadie más cambió el
        archivo desde que lo cargaste; si cambió, NO pisa nada. Devuelve (estado, df)."""
        try:
            fresco, sha = _leer_incidencias_fresco()
        except Exception as e:
            st.error(f"No se pudo leer GitHub antes de guardar: {e}")
            return "ERROR", None

        if not fresco.equals(_normalizar_inc(df_base)):
            return "CONFLICTO", fresco

        df_guardar = _normalizar_inc(df_nuevo)
        try:
            r = _put_incidencias(df_guardar, sha, f"Sincronización de registros {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        except Exception as e:
            st.error(f"No se pudo guardar en GitHub: {e}")
            return "ERROR", None

        if r.status_code in (200, 201):
            return "OK", df_guardar
        if r.status_code in (409, 422):
            try:
                fresco, _ = _leer_incidencias_fresco()
            except Exception:
                fresco = df_base
            return "CONFLICTO", fresco
        st.error(f"Error de GitHub: {r.status_code} - {r.text[:200]}")
        return "ERROR", None

    def cargar_datos_seguro():
        try:
            df, sha = _leer_incidencias_fresco()
            if sha is None:  # el archivo no existe todavía: se crea vacío
                df_nuevo = pd.DataFrame(columns=COLUMNAS_INCIDENCIAS)
                _put_incidencias(df_nuevo, None, "Crear incidencias.csv")
                return df_nuevo
            return df
        except Exception as e:
            st.error(f"Error al cargar el módulo: {e}")
        return pd.DataFrame(columns=COLUMNAS_INCIDENCIAS)

    # ── PDF DE UNA INCIDENCIA (mismo formato corporativo que recolecciones) ──────────────
    def generar_pdf_incidencia(fila):
        """Genera el PDF de UNA incidencia / tarea. Devuelve bytes o None."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.units import mm
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_RIGHT, TA_CENTER
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                                            TableStyle, Spacer, HRFlowable)
        except ImportError:
            st.error("Falta la librería `reportlab`. Agrégala a tu requirements.txt para generar PDFs.")
            return None

        f = {str(k).upper().strip(): v for k, v in dict(fila).items()}
        g = lambda k: str(f.get(k, "") if f.get(k, "") is not None else "").strip()

        def P(txt):
            return _html.escape(str(txt)).replace("\n", "<br/>")

        st_base = ParagraphStyle("base", fontName="Helvetica", fontSize=8.5, leading=11)
        st_cel = ParagraphStyle("cel", parent=st_base, fontSize=8.5, leading=10.5)
        st_der = ParagraphStyle("der", parent=st_base, alignment=TA_RIGHT, fontSize=9, leading=12)
        st_marca = ParagraphStyle("marca", parent=st_base, fontName="Helvetica-Bold", fontSize=15, leading=17)
        st_sub = ParagraphStyle("sub", parent=st_base, fontSize=6.5, leading=8)
        st_tit = ParagraphStyle("tit", parent=st_base, fontName="Helvetica-Bold", fontSize=11,
                                alignment=TA_CENTER, leading=14)

        W = letter[0] - 30 * mm
        folio = g("FOLIO")
        elementos = []

        encabezado = Table(
            [[[Paragraph("Jabones y Productos Especializados", st_marca),
               Paragraph("Distribución y Logística | 2026", st_sub)],
              Paragraph(f"<b>FOLIO:</b> {P(folio)}<br/><b>FECHA:</b> {datetime.now():%Y-%m-%d}", st_der)]],
            colWidths=[W * 0.65, W * 0.35],
        )
        encabezado.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elementos.append(encabezado)
        elementos.append(HRFlowable(width="100%", thickness=1.6, color=colors.black,
                                    spaceBefore=2, spaceAfter=12))
        elementos.append(Paragraph("REPORTE DE INCIDENCIA / TAREA", st_tit))
        elementos.append(Spacer(1, 10))

        datos = [
            ("TIPO", g("TIPO")), ("PRIORIDAD", g("PRIORIDAD").upper()),
            ("ESTATUS", g("ESTATUS").upper()), ("CREADOR", g("CREADOR") or "—"),
            ("RESPONSABLE", g("RESPONSABLE") or "—"), ("PEDIDO / GUÍA", g("PEDIDO_GUIA") or "—"),
            ("CLIENTE / DESTINO", g("CLIENTE_DESTINO") or "—"), ("ID SEGUIMIENTO", g("ID_SEGUIMIENTO") or "—"),
            ("ID DE QUEJA / REF", g("ID_QUEJA") or "—"), ("", ""),
        ]
        filas_datos = []
        for i in range(0, len(datos), 2):
            fila_d = []
            for etiqueta, valor in datos[i:i + 2]:
                fila_d.append(Paragraph(f"<b>{P(etiqueta)}:</b> {P(valor)}" if etiqueta else "", st_cel))
            filas_datos.append(fila_d)
        tabla_datos = Table(filas_datos, colWidths=[W / 2, W / 2])
        tabla_datos.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elementos.append(tabla_datos)
        elementos.append(Spacer(1, 12))

        def caja(titulo, texto, alto_extra=40):
            contenido = [Paragraph(f"<b>{titulo}</b>" + (f"<br/>{P(texto)}" if texto else ""), st_cel),
                         Spacer(1, alto_extra)]
            t = Table([[contenido]], colWidths=[W])
            t.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            return t

        elementos.append(caja("QUEJA / INCONFORMIDAD (DETALLE):", g("DETALLE_INCIDENCIA")))
        elementos.append(Spacer(1, 8))
        elementos.append(caja("ACCIONES / PASOS A SEGUIR:", g("ACCIONES")))

        def _pie(canvas_, doc):
            canvas_.saveState()
            canvas_.setFont("Helvetica", 7)
            canvas_.setFillColor(colors.grey)
            canvas_.drawString(15 * mm, 10 * mm, f"Generado: {datetime.now():%Y-%m-%d %H:%M}")
            canvas_.drawRightString(letter[0] - 15 * mm, 10 * mm, f"Página {doc.page}")
            canvas_.restoreState()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=15 * mm, rightMargin=15 * mm,
                                topMargin=14 * mm, bottomMargin=18 * mm, pageCompression=1,
                                title=f"Incidencia {folio}")
        doc.build(elementos, onFirstPage=_pie, onLaterPages=_pie)
        return buffer.getvalue()

    def _nombre_pdf(folio):
        return "Incidencia_" + re.sub(r"[^\w\-]", "_", str(folio)) + ".pdf"

    @st.cache_data(ttl=60, show_spinner=False)
    def _pdf_b64_cache(fila_json):
        pdf = generar_pdf_incidencia(json.loads(fila_json))
        return base64.b64encode(pdf).decode() if pdf else ""

    MAX_PDF_INLINE = 200

    # ── Datos frescos en cada recarga ────────────────────────────────────────────────────
    st.session_state.df_incidencias = cargar_datos_seguro()
    for c in COLUMNAS_INCIDENCIAS:
        if c not in st.session_state.df_incidencias.columns:
            st.session_state.df_incidencias[c] = ""
    df_master = st.session_state.df_incidencias.copy()

    _msg = st.session_state.pop("msg_incidencias", None)
    if _msg:
        (st.success if _msg[0] == "ok" else st.warning)(_msg[1])

    # ── ESTILOS GENERALES (botones + KPI), igual que recolecciones ───────────────────────
    st.markdown("""
        <style>
            input[type=number]::-webkit-inner-spin-button,
            input[type=number]::-webkit-outer-spin-button {
                -webkit-appearance: none; margin: 0;
            }
            div.stButton > button,
            div.stFormSubmitButton > button,
            div.stDownloadButton > button {
                background-color: #628290 !important;
                color: #FFFFFF !important;
                border: 1px solid #628290 !important;
                border-radius: 7px !important;
                transition: all 0.3s ease !important;
                width: 100% !important;
                box-shadow: none !important;
                font-weight: 700 !important;
                font-size: 10px !important;
                height: 32px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }
            div.stButton > button:hover,
            div.stButton > button:focus,
            div.stFormSubmitButton > button:hover,
            div.stFormSubmitButton > button:focus,
            div.stDownloadButton > button:hover,
            div.stDownloadButton > button:focus {
                background-color: #4E6772 !important;
                color: #FFFFFF !important;
                border-color: #4E6772 !important;
                box-shadow: none !important;
            }
            div.stButton > button:active,
            div.stFormSubmitButton > button:active,
            div.stDownloadButton > button:active {
                background-color: #3f555f !important;
                border-color: #3f555f !important;
                color: #FFFFFF !important;
            }
            .base-card-alerta {
                background-color: #2B343B;
                border: 1px solid #4B5D67;
                border-left: 5px solid #38bdf8;
                padding: 16px 20px;
                border-radius: 6px;
                width: 100%;
                font-family: 'Inter', sans-serif;
                color: white;
                box-sizing: border-box;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                margin-bottom: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    def _titulo(titulo, subtitulo):
        st.markdown(
            "<div style='margin-bottom:18px;'>"
            f"<div style='color:#FFFFFF;font-size:19px;font-weight:800;letter-spacing:.3px;'>{titulo}</div>"
            f"<div style='color:#8B9BB4;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>{subtitulo}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    def _kpi(col, titulo, valor, unidad, color):
        with col:
            st.markdown(f"""
                <div class='base-card-alerta' style='border-left-color: {color};'>
                    <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>{titulo}</div>
                    <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{valor} <span style='font-size: 10px; color: {color}; font-weight: 700; text-transform: uppercase;'>{unidad}</span></div>
                </div>
            """, unsafe_allow_html=True)

    # ── DEFINICIÓN DE TABS ───────────────────────────────────────────────────────────────
    tab0, tab1, tab2 = st.tabs(["Render Principal", "Captura", "Edición"])

    # ============================================================================
    # TAB 0: RENDER PRINCIPAL
    # ============================================================================
    with tab0:
        _titulo("RENDER DE INCIDENCIAS",
                "MONITOREO DE INCIDENCIAS Y TAREAS · GITHUB EN TIEMPO REAL · HAZ CLIC EN UN FOLIO PARA VER QUEJA / INCONFORMIDAD Y ACCIONES")

        df_ren = df_master[df_master["FOLIO"].str.strip() != ""].copy()

        if df_ren.empty:
            st.info("No hay registros guardados.")
        else:
            with st.container():
                f1, f2, f3, f4 = st.columns(4, vertical_alignment="bottom")
                with f1:
                    flt_estatus = st.selectbox("FILTRAR POR ESTATUS",
                                               ["TODOS"] + sorted(df_ren["ESTATUS"].replace("", "SIN ESTATUS").unique().tolist()),
                                               key="flt_inc_estatus")
                with f2:
                    flt_prioridad = st.selectbox("FILTRAR POR PRIORIDAD",
                                                 ["TODOS"] + sorted(df_ren["PRIORIDAD"].replace("", "SIN PRIORIDAD").unique().tolist()),
                                                 key="flt_inc_prioridad")
                with f3:
                    flt_tipo = st.selectbox("FILTRAR POR TIPO",
                                            ["TODOS"] + sorted(df_ren["TIPO"].replace("", "SIN TIPO").unique().tolist()),
                                            key="flt_inc_tipo")
                with f4:
                    flt_resp = st.selectbox("FILTRAR POR RESPONSABLE",
                                            ["TODOS"] + sorted(df_ren["RESPONSABLE"].replace("", "SIN ASIGNAR").unique().tolist()),
                                            key="flt_inc_resp")

            df_vista = df_ren.copy()
            if flt_estatus != "TODOS":
                df_vista = df_vista[df_vista["ESTATUS"].replace("", "SIN ESTATUS") == flt_estatus]
            if flt_prioridad != "TODOS":
                df_vista = df_vista[df_vista["PRIORIDAD"].replace("", "SIN PRIORIDAD") == flt_prioridad]
            if flt_tipo != "TODOS":
                df_vista = df_vista[df_vista["TIPO"].replace("", "SIN TIPO") == flt_tipo]
            if flt_resp != "TODOS":
                df_vista = df_vista[df_vista["RESPONSABLE"].replace("", "SIN ASIGNAR") == flt_resp]

            # Más nuevo primero
            df_vista = df_vista.iloc[::-1]

            est_up = df_ren["ESTATUS"].str.upper()
            k1, k2, k3, k4, k5 = st.columns(5)
            _kpi(k1, "TOTAL REGISTROS", len(df_ren), "FOLIOS", "#38bdf8")
            _kpi(k2, "PENDIENTES", int((est_up == "PENDIENTE").sum()), "ABIERTOS", "#FDE047")
            _kpi(k3, "EN PROCESO", int((est_up == "EN PROCESO").sum()), "EN CURSO", "#60a5fa")
            _kpi(k4, "SOLUCIONADOS", int((est_up == "SOLUCIONADO").sum()), "CERRADOS", "#00FFAA")
            _kpi(k5, "URGENTES", int((df_ren["PRIORIDAD"].str.upper() == "URGENTE").sum()), "PRIORIDAD", "#F97316")

            st.markdown("<p style='font-size:11px; font-weight:700; letter-spacing:8px; color:#FFFFFF; text-transform:uppercase; text-align:center; margin-bottom:20px;'>DETALLE OPERATIVO DE INCIDENCIAS</p>", unsafe_allow_html=True)

            if df_vista.empty:
                st.markdown("""
                    <div style="background: rgba(56, 189, 248, 0.05); border: 1px dashed #38bdf8; border-radius: 10px; padding: 25px; text-align: center; margin-top: 20px;">
                        <p style="color: #38bdf8; font-size: 16px; margin: 0;"><b>SIN REGISTROS BAJO ESTE FILTRO</b></p>
                        <p style="color: #94a3b8; font-size: 12px; margin-top: 5px;">No se encontraron elementos que coincidan con los criterios seleccionados.</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                try:
                    import reportlab  # noqa: F401
                    pdf_disponible = True
                except ImportError:
                    pdf_disponible = False
                    st.warning("Falta `reportlab` en requirements.txt para generar los PDF.")
                n_filas_pdf = 0

                color_prio = {"URGENTE": "#ff4b4b", "ALTA": "#f97316", "MEDIA": "#38bdf8", "BAJA": "#00FFAA"}
                color_est = {"PENDIENTE": "#FDE047", "EN PROCESO": "#60a5fa", "SOLUCIONADO": "#00FFAA", "RECHAZADO": "#FF4B4B"}

                filas_html = ""
                for item in df_vista.to_dict("records"):
                    folio_txt = str(item.get("FOLIO", "")).strip()
                    estatus_val = str(item.get("ESTATUS", "")).strip().upper() or "SIN ESTATUS"
                    prio_val = str(item.get("PRIORIDAD", "")).strip().upper() or "SIN PRIORIDAD"
                    tipo_val = str(item.get("TIPO", "")).strip() or "Incidencia"

                    c_e = color_est.get(estatus_val, "#38bdf8")
                    c_p = color_prio.get(prio_val, "#94a3b8")

                    detalle = str(item.get("DETALLE_INCIDENCIA", "")).strip()
                    acciones = str(item.get("ACCIONES", "")).strip()
                    id_seg = str(item.get("ID_SEGUIMIENTO", "")).strip()
                    id_queja = str(item.get("ID_QUEJA", "")).strip()
                    creador = str(item.get("CREADOR", "")).strip() or "N/A"
                    responsable = str(item.get("RESPONSABLE", "")).strip() or "N/A"

                    detalle_html = esc(detalle).replace("\n", "<br>") if detalle else "<span style='opacity:.5'>SIN CAPTURAR</span>"
                    acciones_html = esc(acciones).replace("\n", "<br>") if acciones else "<span style='opacity:.5'>SIN CAPTURAR</span>"

                    aviso = ""
                    if not detalle or not acciones:
                        aviso = "<span class='aviso' title='Falta capturar detalle o acciones'>⚠</span>"

                    btn_pdf_html = ""
                    if pdf_disponible and n_filas_pdf < MAX_PDF_INLINE:
                        b64_pdf = _pdf_b64_cache(json.dumps(item, default=str, sort_keys=True))
                        if b64_pdf:
                            btn_pdf_html = (f"<button class='btn-pdf' data-b64='{b64_pdf}' "
                                            f"data-name='{esc(_nombre_pdf(folio_txt))}' "
                                            f"onclick='descargarPdf(this)'>📄 DESCARGAR PDF</button>")
                            n_filas_pdf += 1
                    elif pdf_disponible:
                        btn_pdf_html = "<span class='chip'>PDF: FILTRA PARA HABILITARLO</span>"

                    chip_seg = f"<span class='chip'>SEGUIMIENTO {esc(id_seg)}</span>" if id_seg else ""
                    chip_queja = f"<span class='chip chip-queja'>QUEJA / REF {esc(id_queja)}</span>" if id_queja else "<span class='chip'>SIN REF</span>"

                    filas_html += f"""
                    <tr class="fila-main" onclick="toggleDet(this)">
                        <td style="font-family: monospace; font-weight: 800; color: #FFFFFF;"><span class="flecha">▸</span> {esc(folio_txt)} {aviso}</td>
                        <td style="text-transform: uppercase; font-weight: 700; color:#38bdf8;">{esc(tipo_val)}</td>
                        <td style="text-align:center;"><span class="badge" style="color:{c_p}; border-color:{c_p}; background:{c_p}1A;">{esc(prio_val)}</span></td>
                        <td style="text-transform: uppercase; font-weight: 700;">{esc(item.get('CLIENTE_DESTINO', '')) or 'N/A'}</td>
                        <td style="font-family: monospace; color: #FFD700;">{esc(item.get('PEDIDO_GUIA', '')) or 'N/A'}</td>
                        <td style="font-family: monospace;">{esc(id_seg) or 'N/A'}</td>
                        <td style="text-transform: uppercase;">{esc(responsable)}</td>
                        <td style="text-align:center;"><span class="badge" style="color:{c_e}; border-color:{c_e}; background:{c_e}1A;">{esc(estatus_val)}</span></td>
                    </tr>
                    <tr class="fila-det">
                        <td colspan="8">
                            <div class="det-box">
                                <div class="det-head">{btn_pdf_html}CREADOR: <b>{esc(creador)}</b> &nbsp; ASIGNADO A: <b>{esc(responsable)}</b> &nbsp; {chip_seg} {chip_queja}</div>
                                <div class="bloque">
                                    <div class="lbl">QUEJA / INCONFORMIDAD (DETALLE)</div>
                                    <div class="txt">{detalle_html}</div>
                                </div>
                                <div class="bloque acc">
                                    <div class="lbl">ACCIONES / PASOS A SEGUIR</div>
                                    <div class="txt">{acciones_html}</div>
                                </div>
                            </div>
                        </td>
                    </tr>
                    """

                TEMPLATE = """
                <div style="font-family: 'Inter', sans-serif; width: 100%;">
                    <style>
                        body { background: transparent; margin: 0; padding: 0; }
                        ::-webkit-scrollbar { width: 8px; height: 8px; }
                        ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.1); border-radius: 10px; }
                        ::-webkit-scrollbar-thumb { background: #3498db; border-radius: 10px; border: 2px solid #384A52; }
                        ::-webkit-scrollbar-thumb:hover { background: #2ecc71; box-shadow: 0 0 10px rgba(46, 204, 113, 0.5); }

                        .table-container { max-height: 580px; overflow-y: auto; border: 1px solid #4B5D67; border-radius: 8px; background-color: #2B343B; }
                        .matriz-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 12px; color: white; }
                        .matriz-table th {
                            position: sticky; top: 0; background-color: #1E252B; color: rgba(255,255,255,0.7);
                            font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
                            padding: 14px 16px; border-bottom: 2px solid #4B5D67; z-index: 10;
                        }
                        .matriz-table td { padding: 12px 16px; border-bottom: 1px solid rgba(75,93,103,0.4); vertical-align: middle; }
                        .matriz-table tbody tr { transition: background 0.2s ease; }
                        .matriz-table tbody tr:hover { background-color: rgba(56,189,248,0.08); }

                        .badge { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid; display: inline-block; letter-spacing: 0.5px; }

                        .fila-main { cursor: pointer; }
                        .fila-main .flecha { display: inline-block; color: #38bdf8; transition: transform 0.2s ease; margin-right: 4px; }
                        .fila-main.open .flecha { transform: rotate(90deg); }
                        .fila-main.open { background-color: rgba(56,189,248,0.12); }
                        .aviso { color: #FDE047; margin-left: 4px; cursor: help; }

                        .matriz-table tbody tr.fila-det { display: none; }
                        .matriz-table tbody tr.fila-det.open { display: table-row; }
                        .matriz-table tbody tr.fila-det:hover { background-color: transparent; }
                        .matriz-table tbody tr.fila-det > td { padding: 4px 16px 16px 16px; }

                        .det-box { background: #1E252B; border: 1px solid #4B5D67; border-left: 3px solid #38bdf8; border-radius: 6px; padding: 12px 16px; }
                        .det-head { font-size: 11px; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px; color: rgba(255,255,255,0.7); }
                        .btn-pdf {
                            float: right; background-color: #628290; color: #FFFFFF; border: 1px solid #628290; border-radius: 7px;
                            font-size: 10px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;
                            height: 28px; padding: 0 14px; cursor: pointer; transition: all 0.3s ease;
                        }
                        .btn-pdf:hover { background-color: #4E6772; border-color: #4E6772; }
                        .btn-pdf:active { background-color: #3f555f; border-color: #3f555f; }
                        .chip { font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; border: 1px solid #4B5D67; color: #94a3b8; letter-spacing: 0.5px; margin-right: 4px; }
                        .chip-queja { color: #F97316; border-color: #F97316; background: rgba(249,115,22,0.1); }

                        .bloque { border-top: 1px solid #4B5D67; padding: 10px 0 6px 0; }
                        .bloque .lbl { font-size: 9px; font-weight: 800; letter-spacing: 1px; color: rgba(255,255,255,0.6); margin-bottom: 6px; }
                        .bloque .txt { font-size: 12px; line-height: 1.55; color: #eee; text-transform: none; letter-spacing: 0; }
                        .bloque.acc .txt { color: #38bdf8; }
                    </style>

                    <div class="table-container">
                        <table class="matriz-table">
                            <thead>
                                <tr>
                                    <th>FOLIO</th>
                                    <th>TIPO</th>
                                    <th style="text-align:center;">PRIORIDAD</th>
                                    <th>CLIENTE / DESTINO</th>
                                    <th>PEDIDO / GUÍA</th>
                                    <th>ID SEGUIMIENTO</th>
                                    <th>RESPONSABLE</th>
                                    <th style="text-align:center;">ESTATUS</th>
                                </tr>
                            </thead>
                            <tbody>
                                %%FILAS%%
                            </tbody>
                        </table>
                    </div>

                    <script>
                        function descargarPdf(btn) {
                            try {
                                var bin = atob(btn.dataset.b64);
                                var bytes = new Uint8Array(bin.length);
                                for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
                                var url = URL.createObjectURL(new Blob([bytes], {type: 'application/pdf'}));
                                var a = document.createElement('a');
                                a.href = url;
                                a.download = btn.dataset.name || 'incidencia.pdf';
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                                setTimeout(function() { URL.revokeObjectURL(url); }, 2000);
                            } catch (e) {
                                alert('No se pudo descargar el PDF. Intenta de nuevo o usa otro navegador.');
                            }
                        }
                        function toggleDet(tr) {
                            tr.classList.toggle('open');
                            tr.nextElementSibling.classList.toggle('open');
                        }
                    </script>
                </div>
                """
                components.html(TEMPLATE.replace("%%FILAS%%", filas_html), height=620, scrolling=False)

    # ============================================================================
    # TAB 1: CAPTURA (nuevo registro)
    # ============================================================================
    with tab1:
        _titulo("CAPTURA DE INCIDENCIA / TAREA",
                "REGISTRAR UN NUEVO FOLIO · EL FOLIO SE ASIGNA AUTOMÁTICAMENTE")

        if not es_administrador:
            st.info("La captura de incidencias está disponible solo para administradores.")
        else:
            if not df_master.empty:
                nums = df_master["FOLIO"].str.extract(r"REG-(\d+)")[0].dropna().astype(int)
                sugerencia_folio = f"REG-{(nums.max() if not nums.empty else 0) + 1:03d}"
            else:
                sugerencia_folio = "REG-001"

            c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])
            with c1:
                t_tipo = st.selectbox("Tipo de Registro", OPC_TIPO, key="cap_tipo")
            with c2:
                n_pedido = st.text_input("📦 Vincular Pedido / Factura", placeholder="Escribe pedido...", key="cap_pedido").strip().upper()
            with c3:
                st.text_input("Folio ID (automático)", value=sugerencia_folio, disabled=True, key="cap_folio_vis")
            with c4:
                t_prior = st.selectbox("Prioridad", OPC_PRIORIDAD, key="cap_prior")

            info_matriz = {"cliente_destino": "", "pedido_guia": ""}
            if n_pedido and df_global is not None:
                res = df_global[df_global["NÚMERO DE PEDIDO"].astype(str).str.contains(n_pedido, na=False)]
                if not res.empty:
                    fila_m = res.iloc[0]
                    guia = fila_m.get("NÚMERO DE GUÍA", "N/A")
                    cliente = fila_m.get("NOMBRE DEL CLIENTE", "N/A")
                    destino = fila_m.get("DESTINO", "N/A")
                    info_matriz["cliente_destino"] = f"CLIENTE: {cliente} | DESTINO: {destino}"
                    info_matriz["pedido_guia"] = f"PEDIDO: {n_pedido} | GUIA: {guia}"
                    st.success("✅ Pedido localizado en la Matriz; se llenaron cliente y guía.")
                else:
                    st.warning("⚠️ Pedido no localizado en la Matriz. Puedes llenar los campos a mano.")

            # La llave incluye el pedido para que los campos se refresquen al localizarlo
            kp = re.sub(r"\W", "_", n_pedido) or "x"

            with st.form("form_captura_incidencia", clear_on_submit=False):
                f2_c1, f2_c2 = st.columns(2)
                with f2_c1:
                    t_cliente_destino = st.text_input("CLIENTE / DESTINO", value=info_matriz["cliente_destino"], key=f"cap_cd_{kp}")
                    t_pedido_guia = st.text_input("PEDIDO / GUÍA", value=info_matriz["pedido_guia"], key=f"cap_pg_{kp}")
                    resp_def = nombre_usuario_actual if nombre_usuario_actual in LISTA_COLABORADORES else LISTA_COLABORADORES[0]
                    t_responsable = st.selectbox("ASIGNAR A (RESPONSABLE SEGUIMIENTO)", LISTA_COLABORADORES,
                                                 index=LISTA_COLABORADORES.index(resp_def), key="cap_resp")
                with f2_c2:
                    t_id_seguimiento = st.text_input("ID SEGUIMIENTO", value=sugerencia_folio, key="cap_idseg")
                    t_id_queja = st.text_input("ID DE QUEJA / REF", value=sugerencia_folio, key="cap_idq")
                    t_estatus = st.selectbox("Estatus", OPC_ESTATUS, key="cap_estatus")

                t_detalle = st.text_area("QUEJA / INCONFORMIDAD (DETALLE)", key="cap_detalle")
                t_acciones = st.text_area("ACCIONES / PASOS A SEGUIR", key="cap_acciones")

                enviar_cap = st.form_submit_button(":material/save: GUARDAR REGISTRO")

            if enviar_cap:
                creador_final = nombre_usuario_actual if nombre_usuario_actual else usuario_actual.upper()
                nueva_data = {
                    "FOLIO": sugerencia_folio,
                    "TIPO": t_tipo,
                    "CREADOR": creador_final,
                    "RESPONSABLE": t_responsable,
                    "PRIORIDAD": t_prior,
                    "VINCULO_BUSQUEDA": n_pedido,
                    "CLIENTE_DESTINO": str(t_cliente_destino).upper(),
                    "PEDIDO_GUIA": str(t_pedido_guia).upper(),
                    "ID_SEGUIMIENTO": str(t_id_seguimiento).upper(),
                    "ID_QUEJA": str(t_id_queja).upper(),
                    "DETALLE_INCIDENCIA": t_detalle,
                    "ACCIONES": t_acciones,
                    "ESTATUS": t_estatus,
                }
                ok, df_final, folio_usado = guardar_incidencia_github(
                    nueva_data, True, f"Nueva incidencia {sugerencia_folio}",
                )
                if ok:
                    st.session_state.df_incidencias = df_final
                    for k_w in ("cap_pedido", "cap_detalle", "cap_acciones", "cap_idseg", "cap_idq"):
                        st.session_state.pop(k_w, None)
                    texto_ok = f"✅ ¡Registro {folio_usado} guardado y asignado con éxito!"
                    if folio_usado != sugerencia_folio:
                        texto_ok += f" (El folio {sugerencia_folio} ya lo había tomado otra persona; se guardó como {folio_usado}.)"
                    st.session_state.msg_incidencias = ("ok", texto_ok)
                    st.rerun()

    # ============================================================================
    # TAB 2: EDICIÓN
    # ============================================================================
    with tab2:
        _titulo("EDICIÓN Y ACTUALIZACIÓN",
                "MODIFICAR DATOS, DETALLE, ACCIONES Y ESTATUS DE FOLIOS EXISTENTES")

        if not es_administrador:
            st.info("La edición de incidencias está disponible solo para administradores.")
        elif df_master.empty:
            st.warning("No hay registros disponibles para editar.")
        else:
            folios_list = df_master["FOLIO"][df_master["FOLIO"].str.strip() != ""].tolist()[::-1]
            folio_edit = st.selectbox("Selecciona el Folio a Modificar / Actualizar", folios_list, key="edit_inc_folio_sel")

            if folio_edit:
                fila_a = df_master[df_master["FOLIO"] == folio_edit].iloc[0]
                k = re.sub(r"\W", "_", str(folio_edit))

                def _idx(lista, valor, default=0):
                    return lista.index(valor) if valor in lista else default

                opc_tipo_e = list(OPC_TIPO)
                if fila_a["TIPO"] and fila_a["TIPO"] not in opc_tipo_e:
                    opc_tipo_e.append(fila_a["TIPO"])
                opc_prio_e = list(OPC_PRIORIDAD)
                if fila_a["PRIORIDAD"] and fila_a["PRIORIDAD"] not in opc_prio_e:
                    opc_prio_e.append(fila_a["PRIORIDAD"])
                opc_est_e = list(OPC_ESTATUS)
                if fila_a["ESTATUS"] and fila_a["ESTATUS"] not in opc_est_e:
                    opc_est_e.append(fila_a["ESTATUS"])
                opc_resp_e = list(LISTA_COLABORADORES)
                if fila_a["RESPONSABLE"] and fila_a["RESPONSABLE"] not in opc_resp_e:
                    opc_resp_e.append(fila_a["RESPONSABLE"])

                with st.form(f"form_edicion_inc_{k}"):
                    st.markdown(f"**Editando Folio:** `{folio_edit}` · Creado por: **{fila_a['CREADOR'] or 'N/A'}**")

                    e1, e2, e3 = st.columns(3)
                    with e1:
                        e_tipo = st.selectbox("Tipo de Registro", opc_tipo_e, index=_idx(opc_tipo_e, fila_a["TIPO"]), key=f"e_tipo_{k}")
                    with e2:
                        e_prior = st.selectbox("Prioridad", opc_prio_e, index=_idx(opc_prio_e, fila_a["PRIORIDAD"]), key=f"e_prior_{k}")
                    with e3:
                        e_estatus = st.selectbox("Estatus", opc_est_e, index=_idx(opc_est_e, fila_a["ESTATUS"]), key=f"e_est_{k}")

                    ec1, ec2 = st.columns(2)
                    with ec1:
                        e_cd = st.text_input("CLIENTE / DESTINO", value=fila_a["CLIENTE_DESTINO"], key=f"e_cd_{k}")
                        e_pg = st.text_input("PEDIDO / GUÍA", value=fila_a["PEDIDO_GUIA"], key=f"e_pg_{k}")
                        e_resp = st.selectbox("ASIGNAR A (RESPONSABLE SEGUIMIENTO)", opc_resp_e,
                                              index=_idx(opc_resp_e, fila_a["RESPONSABLE"]), key=f"e_resp_{k}")
                    with ec2:
                        e_vinculo = st.text_input("PEDIDO / FACTURA VINCULADO", value=fila_a["VINCULO_BUSQUEDA"], key=f"e_vinc_{k}")
                        e_idseg = st.text_input("ID SEGUIMIENTO", value=fila_a["ID_SEGUIMIENTO"], key=f"e_idseg_{k}")
                        e_idq = st.text_input("ID DE QUEJA / REF", value=fila_a["ID_QUEJA"], key=f"e_idq_{k}")

                    e_detalle = st.text_area("QUEJA / INCONFORMIDAD (DETALLE)", value=fila_a["DETALLE_INCIDENCIA"], height=120, key=f"e_det_{k}")
                    e_acciones = st.text_area("ACCIONES / PASOS A SEGUIR", value=fila_a["ACCIONES"], height=120, key=f"e_acc_{k}")

                    btn_actualizar = st.form_submit_button(":material/sync: ACTUALIZAR REGISTRO")

                # PDF con lo que ya está guardado (si acabas de editar, guarda primero)
                pdf_edit = generar_pdf_incidencia(fila_a.to_dict())
                if pdf_edit:
                    st.download_button("📄 DESCARGAR PDF DEL FOLIO", data=pdf_edit,
                                       file_name=_nombre_pdf(folio_edit), mime="application/pdf",
                                       key=f"btn_pdf_edit_inc_{k}")

                if btn_actualizar:
                    nueva_data = {
                        "FOLIO": folio_edit,
                        "TIPO": e_tipo,
                        "CREADOR": fila_a["CREADOR"],   # el creador original no cambia
                        "RESPONSABLE": e_resp,
                        "PRIORIDAD": e_prior,
                        "VINCULO_BUSQUEDA": str(e_vinculo).strip().upper(),
                        "CLIENTE_DESTINO": str(e_cd).upper(),
                        "PEDIDO_GUIA": str(e_pg).upper(),
                        "ID_SEGUIMIENTO": str(e_idseg).upper(),
                        "ID_QUEJA": str(e_idq).upper(),
                        "DETALLE_INCIDENCIA": e_detalle,
                        "ACCIONES": e_acciones,
                        "ESTATUS": e_estatus,
                    }
                    cambios = [c for c in COLUMNAS_INCIDENCIAS if str(fila_a[c]).strip() != str(nueva_data[c]).strip()]
                    if not cambios:
                        st.info("No hay cambios que guardar en este folio.")
                    else:
                        ok, df_final, _ = guardar_incidencia_github(
                            nueva_data, False,
                            f"Actualización de incidencia {folio_edit}: {', '.join(cambios)}",
                        )
                        if ok:
                            st.session_state.df_incidencias = df_final
                            st.session_state.msg_incidencias = ("ok", f"✅ ¡Folio {folio_edit} actualizado correctamente en GitHub!")
                            st.rerun()

            # ── Editor avanzado (tabla completa) ─────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("⚙️ Editor avanzado de registros", expanded=False):
                df_editor = df_master.copy()
                for col in COLUMNAS_INCIDENCIAS:
                    if col not in df_editor.columns:
                        df_editor[col] = ""
                    df_editor[col] = df_editor[col].astype(str).replace("nan", "").fillna("")

                df_editado = st.data_editor(df_editor, hide_index=True, use_container_width=True,
                                            num_rows="dynamic", key="editor_avanzado_inc")

                cabeceras = "".join([f"<th>{c}</th>" for c in COLUMNAS_INCIDENCIAS if c != "VINCULO_BUSQUEDA"])
                cuerpo = ""
                for _, fila in df_editado.iterrows():
                    cuerpo += "<tr>" + "".join([f"<td>{esc(fila.get(c, ''))}</td>" for c in COLUMNAS_INCIDENCIAS if c != "VINCULO_BUSQUEDA"]) + "</tr>"

                html_print = f"""
                <div id="printableArea" style="font-family: sans-serif;">
                    <h2>JYPESA - Logística NEXION</h2>
                    <table border="1" style="width:100%; border-collapse: collapse;">
                        <thead><tr>{cabeceras}</tr></thead>
                        <tbody>{cuerpo}</tbody>
                    </table>
                </div>
                """

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(":material/sync: SINCRONIZAR", use_container_width=True, key="btn_sync_inc"):
                        estado, df_resultado = guardar_tabla_completa(df_editado, df_master)
                        if estado == "OK":
                            st.session_state.df_incidencias = df_resultado
                            st.session_state.msg_incidencias = ("ok", "✅ Registros sincronizados con éxito.")
                            st.rerun()
                        elif estado == "CONFLICTO":
                            st.session_state.df_incidencias = df_resultado
                            st.session_state.msg_incidencias = ("warn", "⚠️ Otra persona guardó cambios mientras editabas. Se recargó la versión más reciente; vuelve a hacer tus cambios para no pisar los de ella.")
                            st.rerun()
                with col2:
                    if st.button(":material/print: IMPRIMIR", use_container_width=True, key="btn_print_inc"):
                        components.html(f"{html_print}<script>window.print();</script>", height=0, width=0)
                with col3:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                        df_editado.to_excel(writer, index=False, sheet_name="Registros")
                    st.download_button("BAJAR EXCEL", data=buffer.getvalue(), file_name="registros_nexion.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True, key="btn_excel_inc")


if __name__ == "__main__":
    main()
