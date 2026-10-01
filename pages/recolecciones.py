import base64
from datetime import datetime
from io import BytesIO
import io
import html as _html
import json
import re
import time

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from components.layout import render_layout


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Recolecciones Pendientes",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="SEGUIMIENTO", submodulo_actual="RECOLECCIONES")


#----registra usuario------
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
    except Exception as e:
        return None


# Inicialización segura de estados de menú
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "SEGUIMIENTO"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "RECOLECCIONES"
if "busqueda_activa" not in st.session_state:
    st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
    st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
    st.session_state.search_key_version = 1
if "tipo_resultado" not in st.session_state:
    st.session_state.tipo_resultado = "OPERACION"


# ==========================================
# 5. INTERFAZ PRINCIPAL CON SISTEMA DE TABS
# ==========================================
def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True
    
    st.markdown("""
        <style>        
            /* --- ESTILOS GENERALES Y HOVER PARA BOTONES (INCLUIDO EL FORMULARIO) --- */
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
    
            /* --- TARJETAS DE KPI ESTILO WAR ROOM --- */
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
    
    # --------------------------------------------------------
    # CONFIGURACIÓN DE ARCHIVOS EN GITHUB
    #   - recolecciones_estatus.csv  -> 1 fila por folio (datos del formato + motivo + queja)
    #   - recolecciones_detalle.csv  -> 1 fila por producto/código de cada folio
    # --------------------------------------------------------
    GITHUB_REPO = "RH2026/nexion"
    BRANCH = "main"

    ARCHIVO_ESTATUS = "recolecciones_estatus.csv"
    ARCHIVO_DETALLE = "recolecciones_detalle.csv"

    COLUMNAS_ESTATUS = ["Folio", "Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total",
                        "Estatus", "Observaciones", "Solicitante", "Numero de Guia", "Costo de la Guia",
                        "Motivo", "ID_Queja", "Motivo_Devolucion"]
    COLUMNAS_NUM = ["Peso_Total", "Costo de la Guia"]

    COLUMNAS_DETALLE = ["Folio", "Codigo", "Descripcion", "Cant_Solicitada", "Cant_Recibida"]
    COLUMNAS_NUM_DET = ["Cant_Solicitada", "Cant_Recibida"]
    COLUMNAS_PROD_EDIT = ["Codigo", "Descripcion", "Cant_Solicitada", "Cant_Recibida"]

    OPC_MOTIVO = ["SIN DEFINIR", "QUEJA", "DEVOLUCIÓN", "REPOSICIÓN", "MUESTRA", "OTRO"]

    esc = lambda v: _html.escape(str(v))

    def _fmt_cant(v):
        try:
            return f"{float(v):g}"
        except Exception:
            return "0"

    def _api_url(archivo):
        return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{archivo}"

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

    def _leer_github_fresco(archivo, columnas, columnas_num):
        """Lee un CSV por la API de GitHub (SIN caché del CDN). Devuelve (df, sha)."""
        url = _api_url(archivo)
        params = {"ref": BRANCH, "t": time.time_ns()}
        r = requests.get(url, headers=_gh_headers(), params=params, timeout=20)
        if r.status_code == 404:
            return _normalizar(pd.DataFrame(columns=columnas), columnas, columnas_num), None
        r.raise_for_status()
        data = r.json()
        if data.get("content"):
            raw = base64.b64decode(data["content"])
        else:  # archivos grandes: la API no manda el contenido en base64
            r2 = requests.get(url, headers=_gh_headers({"Accept": "application/vnd.github.raw"}),
                              params=params, timeout=30)
            r2.raise_for_status()
            raw = r2.content
        # dtype=str: evita que "Numero de Guia" o "Folio" se conviertan en 1234.0
        df = pd.read_csv(BytesIO(raw), encoding="utf-8-sig", dtype=str, keep_default_na=False)
        return _normalizar(df, columnas, columnas_num), data.get("sha")

    def cargar_estatus_github():
        try:
            df, _ = _leer_github_fresco(ARCHIVO_ESTATUS, COLUMNAS_ESTATUS, COLUMNAS_NUM)
            return df
        except Exception as e:
            st.error(f"No se pudo leer el archivo de estatus desde GitHub: {e}")
            return _normalizar(pd.DataFrame(columns=COLUMNAS_ESTATUS), COLUMNAS_ESTATUS, COLUMNAS_NUM)

    def cargar_detalle_github():
        try:
            df, _ = _leer_github_fresco(ARCHIVO_DETALLE, COLUMNAS_DETALLE, COLUMNAS_NUM_DET)
            return df
        except Exception as e:
            st.error(f"No se pudo leer el detalle de productos desde GitHub: {e}")
            return _normalizar(pd.DataFrame(columns=COLUMNAS_DETALLE), COLUMNAS_DETALLE, COLUMNAS_NUM_DET)

    def _modificar_csv_github(archivo, columnas, columnas_num, mutador, mensaje):
        """Relee el archivo justo antes de escribir (nunca pisa ediciones previas),
        aplica `mutador(df)` -> df (o None si hubo error) y sube el resultado.
        Si hay conflicto de versión, reintenta."""
        url = _api_url(archivo)
        for intento in range(4):
            try:
                df, sha = _leer_github_fresco(archivo, columnas, columnas_num)
            except Exception as e:
                st.error(f"No se pudo leer GitHub antes de guardar: {e}")
                return False

            df = mutador(df)
            if df is None:
                return False

            payload = {
                "message": mensaje,
                "content": base64.b64encode(df.to_csv(index=False).encode("utf-8-sig")).decode("utf-8"),
                "branch": BRANCH,
            }
            if sha:
                payload["sha"] = sha

            try:
                r = requests.put(url, headers=_gh_headers(), json=payload, timeout=30)
            except Exception as e:
                st.error(f"No se pudo guardar en GitHub: {e}")
                return False

            if r.status_code in (200, 201):
                return True
            if r.status_code in (409, 422) and intento < 3:
                time.sleep(0.6 * (intento + 1))  # alguien más guardó: releer y reintentar
                continue
            st.error(f"Error al guardar en GitHub: {r.status_code} - {r.text}")
            return False

        st.error("No se pudo guardar por conflictos repetidos. Intenta de nuevo.")
        return False

    def actualizar_folio_github(folio, cambios, mensaje):
        """Actualiza SOLO la fila del folio (y solo los campos cambiados)."""
        def _mut(df):
            mask = df["Folio"].astype(str) == str(folio)
            if not mask.any():
                st.error(f"El folio {folio} ya no existe en el archivo.")
                return None
            for col, val in cambios.items():
                df.loc[mask, col] = val
            return df
        return _modificar_csv_github(ARCHIVO_ESTATUS, COLUMNAS_ESTATUS, COLUMNAS_NUM, _mut, mensaje)

    def reemplazar_detalle_github(folio, productos, mensaje):
        """Reemplaza TODAS las filas de productos de ese folio por `productos`."""
        def _mut(df):
            df = df[df["Folio"].astype(str) != str(folio)]
            if not productos.empty:
                nuevo = productos.copy()
                nuevo.insert(0, "Folio", str(folio))
                df = pd.concat([df, nuevo[COLUMNAS_DETALLE]], ignore_index=True)
            return _normalizar(df.reset_index(drop=True), COLUMNAS_DETALLE, COLUMNAS_NUM_DET)
        return _modificar_csv_github(ARCHIVO_DETALLE, COLUMNAS_DETALLE, COLUMNAS_NUM_DET, _mut, mensaje)

    # --- Utilidades para la captura de productos ---
    def _limpiar_productos(df):
        """Deja solo filas con código, con tipos consistentes (para guardar y comparar)."""
        if df is None or len(df) == 0:
            return pd.DataFrame(columns=COLUMNAS_PROD_EDIT)
        df = df.copy()
        for col in COLUMNAS_PROD_EDIT:
            if col not in df.columns:
                df[col] = ""
        df = df[COLUMNAS_PROD_EDIT]
        df["Codigo"] = df["Codigo"].fillna("").astype(str).str.strip()
        df["Descripcion"] = df["Descripcion"].fillna("").astype(str).str.strip()
        for col in COLUMNAS_NUM_DET:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        df = df[df["Codigo"] != ""]
        return df.reset_index(drop=True)

    def _parsear_pegado(texto):
        """Convierte líneas 'CODIGO, CANTIDAD, DESCRIPCION(opcional)' en filas de productos."""
        filas = []
        for linea in str(texto or "").splitlines():
            linea = linea.strip()
            if not linea:
                continue
            partes = [p.strip() for p in re.split(r"[,\t;]", linea)]
            codigo = partes[0]
            if not codigo:
                continue
            if len(partes) > 1 and partes[1] != "":
                cant = pd.to_numeric(partes[1], errors="coerce")
                cant = 0.0 if pd.isna(cant) else float(cant)
            else:
                cant = 1.0
            desc = partes[2] if len(partes) > 2 else ""
            filas.append({"Codigo": codigo, "Descripcion": desc,
                          "Cant_Solicitada": cant, "Cant_Recibida": 0.0})
        return pd.DataFrame(filas, columns=COLUMNAS_PROD_EDIT)

    def generar_pdf_recoleccion(fila, productos):
        """Genera el PDF (formato corporativo) de UNA recolección. Devuelve bytes o None."""
        try:
            from reportlab.lib.pagesizes import letter
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

        def P(txt):  # texto seguro para Paragraph (escapa y respeta saltos de línea)
            return _html.escape(str(txt)).replace("\n", "<br/>")

        st_base = ParagraphStyle("base", fontName="Helvetica", fontSize=8.5, leading=11)
        st_cel = ParagraphStyle("cel", parent=st_base, fontSize=8.5, leading=10.5)
        st_der = ParagraphStyle("der", parent=st_base, alignment=TA_RIGHT, fontSize=9, leading=12)
        st_marca = ParagraphStyle("marca", parent=st_base, fontName="Helvetica-Bold", fontSize=15, leading=17)
        st_sub = ParagraphStyle("sub", parent=st_base, fontSize=6.5, leading=8)
        st_tit = ParagraphStyle("tit", parent=st_base, fontName="Helvetica-Bold", fontSize=11,
                                alignment=TA_CENTER, leading=14)
        st_der_cel = ParagraphStyle("dercel", parent=st_cel, alignment=TA_RIGHT)

        W = letter[0] - 30 * mm
        folio = g("FOLIO")
        fecha = g("FECHA_RECOLECCION") or datetime.now().strftime("%Y-%m-%d")

        elementos = []

        # --- Encabezado (igual al de tus otros formatos) ---
        encabezado = Table(
            [[[Paragraph("Jabones y Productos Especializados", st_marca),
               Paragraph("Distribución y Logística | 2026", st_sub)],
              Paragraph(f"<b>FOLIO:</b> {P(folio)}<br/><b>FECHA:</b> {P(fecha)}", st_der)]],
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
        elementos.append(Paragraph("REPORTE DE RECOLECCIÓN", st_tit))
        elementos.append(Spacer(1, 10))

        # --- Datos generales ---
        try:
            peso_txt = f"{float(f.get('PESO_TOTAL', 0) or 0):,.2f} KG"
        except Exception:
            peso_txt = g("PESO_TOTAL")
        try:
            costo_txt = f"$ {float(f.get('COSTO DE LA GUIA', 0) or 0):,.2f}"
        except Exception:
            costo_txt = g("COSTO DE LA GUIA")

        datos = [
            ("CLIENTE", g("CLIENTE")), ("PROVEEDOR", g("PROVEEDOR")),
            ("NO. GUÍA", g("NUMERO DE GUIA")), ("ESTATUS", g("ESTATUS").upper()),
            ("SOLICITANTE", g("SOLICITANTE")), ("PESO TOTAL", peso_txt),
            ("COSTO GUÍA", costo_txt), ("MOTIVO", g("MOTIVO") or "—"),
            ("ID DE QUEJA", g("ID_QUEJA") or "SIN QUEJA"), ("", ""),
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

        # --- Tabla de productos ---
        filas_prod = [[Paragraph("<b>CÓDIGO</b>", st_cel), Paragraph("<b>DESCRIPCIÓN</b>", st_cel),
                       Paragraph("<b>SOLICITADO</b>", st_der_cel), Paragraph("<b>RECIBIDO</b>", st_der_cel)]]
        tot_sol, tot_rec = 0.0, 0.0
        n_prod = 0
        for prod in productos or []:
            pr = {str(k).upper().strip(): v for k, v in dict(prod).items()}
            try:
                sol = float(pr.get("CANT_SOLICITADA", 0) or 0)
            except Exception:
                sol = 0.0
            try:
                rec = float(pr.get("CANT_RECIBIDA", 0) or 0)
            except Exception:
                rec = 0.0
            tot_sol += sol
            tot_rec += rec
            n_prod += 1
            filas_prod.append([Paragraph(P(pr.get("CODIGO", "")), st_cel),
                               Paragraph(P(pr.get("DESCRIPCION", "")), st_cel),
                               Paragraph(_fmt_cant(sol), st_der_cel),
                               Paragraph(_fmt_cant(rec), st_der_cel)])
        estilos_prod = [
            ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        if n_prod == 0:
            filas_prod.append([Paragraph("Sin productos capturados", st_cel), "", "", ""])
            estilos_prod.append(("SPAN", (0, 1), (-1, 1)))
        else:
            filas_prod.append(["", Paragraph("<b>TOTAL</b>", st_der_cel),
                               Paragraph(f"<b>{_fmt_cant(tot_sol)}</b>", st_der_cel),
                               Paragraph(f"<b>{_fmt_cant(tot_rec)}</b>", st_der_cel)])
        tabla_prod = Table(filas_prod, colWidths=[W * 0.20, W * 0.50, W * 0.15, W * 0.15], repeatRows=1)
        tabla_prod.setStyle(TableStyle(estilos_prod))
        elementos.append(tabla_prod)
        elementos.append(Spacer(1, 10))

        # --- Cuadros de texto: motivo de la devolución y comentarios ---
        def caja(titulo, texto, alto_extra=22):
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

        elementos.append(caja("MOTIVO DE LA DEVOLUCIÓN:", g("MOTIVO_DEVOLUCION")))
        elementos.append(Spacer(1, 8))
        elementos.append(caja("COMENTARIOS:", g("OBSERVACIONES"), alto_extra=14))

        def _pie(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(colors.grey)
            canvas.drawString(15 * mm, 10 * mm, f"Generado: {datetime.now():%Y-%m-%d %H:%M}")
            canvas.drawRightString(letter[0] - 15 * mm, 10 * mm, f"Página {doc.page}")
            canvas.restoreState()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=15 * mm, rightMargin=15 * mm,
                                topMargin=14 * mm, bottomMargin=18 * mm,
                                title=f"Recolección {folio}")
        doc.build(elementos, onFirstPage=_pie, onLaterPages=_pie)
        return buffer.getvalue()

    def _nombre_pdf(folio):
        return "Recoleccion_" + re.sub(r"[^\w\-]", "_", str(folio)) + ".pdf"

    col_espacio, col_regresar = st.columns([5, 1])
    with col_regresar:
        # Verificas que la variable de sesión exista y que el usuario sea Rigoberto
        if st.session_state.get("usuario") == "Rigoberto":
            if st.button("⬅️ Formatos", use_container_width=True, key="btn_ir_forrecolecciones"):
                st.switch_page("pages/recoleccion_3g.py")
    
    # --- DEFINICIÓN DE TABS (SOLO RENDER DE ESTATUS Y EDICIÓN) ---
    tab1, tab2 = st.tabs(["Render de Estatus", "Edición y Actualización"])
   
    
    # --- TAB 1: RENDER DE ESTATUS ---
    with tab1:

        st.markdown(
            "<div style='margin-bottom:18px;'>"
            "<div style='color:#FFFFFF;font-size:19px;font-weight:800;letter-spacing:.3px;'>RENDER DE ESTATUS</div>"
            "<div style='color:#8B9BB4;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>MONITOREO DE RECOLECCIONES · GITHUB EN TIEMPO REAL · HAZ CLIC EN UN FOLIO PARA VER MOTIVO Y PRODUCTOS</div>"
            "</div>",
            unsafe_allow_html=True
        )

        df_estatus = cargar_estatus_github()
        df_detalle = cargar_detalle_github()

        if not df_estatus.empty:
            df_estatus.columns = [str(c).upper().strip() for c in df_estatus.columns]
            df_detalle.columns = [str(c).upper().strip() for c in df_detalle.columns]

            # Productos agrupados por folio (para el detalle desplegable)
            detalle_por_folio = {}
            if not df_detalle.empty:
                for f, g in df_detalle.groupby(df_detalle["FOLIO"].astype(str)):
                    detalle_por_folio[f] = g.to_dict("records")

            with st.container():
                f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 2], vertical_alignment="bottom")
                
                with f_col1:
                    opciones_estatus = ["TODOS"] + sorted(df_estatus["ESTATUS"].dropna().unique().tolist()) if "ESTATUS" in df_estatus.columns else ["TODOS"]
                    filtro_estatus_tab2 = st.selectbox("FILTRAR POR ESTATUS", options=opciones_estatus, key="sel_estatus_tab2")
                
                with f_col2:
                    col_prov_key = "PROVEEDOR" if "PROVEEDOR" in df_estatus.columns else ("FLETERA" if "FLETERA" in df_estatus.columns else None)
                    if col_prov_key:
                        opciones_prov = ["TODOS"] + sorted(df_estatus[col_prov_key].dropna().unique().tolist())
                        filtro_prov_tab2 = st.selectbox("FILTRAR POR PROVEEDOR", options=opciones_prov, key="sel_prov_tab2")
                    else:
                        filtro_prov_tab2 = "TODOS"

                with f_col3:
                    motivos_existentes = sorted([m for m in df_estatus["MOTIVO"].str.strip().unique().tolist() if m])
                    opciones_motivo = ["TODOS"] + motivos_existentes + ["SIN CAPTURAR"]
                    filtro_motivo = st.selectbox("FILTRAR POR MOTIVO", options=opciones_motivo, key="sel_motivo_tab1")

                with f_col4:
                    filtro_queja = st.selectbox("QUEJA", options=["TODOS", "CON QUEJA", "SIN QUEJA"], key="sel_queja_tab1")

            df_render = df_estatus.copy()
            
            if filtro_estatus_tab2 != "TODOS":
                df_render = df_render[df_render["ESTATUS"] == filtro_estatus_tab2]
                
            if filtro_prov_tab2 != "TODOS" and col_prov_key:
                df_render = df_render[df_render[col_prov_key] == filtro_prov_tab2]

            if filtro_motivo == "SIN CAPTURAR":
                df_render = df_render[df_render["MOTIVO"].str.strip() == ""]
            elif filtro_motivo != "TODOS":
                df_render = df_render[df_render["MOTIVO"].str.strip() == filtro_motivo]

            if filtro_queja == "CON QUEJA":
                df_render = df_render[df_render["ID_QUEJA"].str.strip() != ""]
            elif filtro_queja == "SIN QUEJA":
                df_render = df_render[df_render["ID_QUEJA"].str.strip() == ""]

            total_envios = len(df_estatus)
            filtrados_n = len(df_render)
            
            pendientes_n = len(df_estatus[df_estatus["ESTATUS"].str.upper().str.contains("PENDIENTE|PROCESO", na=False)]) if "ESTATUS" in df_estatus.columns else 0
            entregados_n = len(df_estatus[df_estatus["ESTATUS"].str.upper().str.contains("ENTREGADO", na=False)]) if "ESTATUS" in df_estatus.columns else 0
            con_queja_n = int((df_estatus["ID_QUEJA"].str.strip() != "").sum())
            
            if "PESO_TOTAL" in df_estatus.columns:
                peso_total_val = pd.to_numeric(df_estatus["PESO_TOTAL"], errors="coerce").sum()
            else:
                peso_total_val = 0.0
                
            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

            with kpi1:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #38bdf8;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>TOTAL REGISTROS</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{total_envios} <span style='font-size: 10px; color: #38bdf8; font-weight: 700; text-transform: uppercase;'>FOLIOS</span></div>
                    </div>
                """, unsafe_allow_html=True)

            with kpi2:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #FDE047;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>PENDIENTES</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{pendientes_n} <span style='font-size: 10px; color: #FDE047; font-weight: 700; text-transform: uppercase;'>ACTIVOS</span></div>
                    </div>
                """, unsafe_allow_html=True)

            with kpi3:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #00FFAA;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>ENTREGADOS</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{entregados_n} <span style='font-size: 10px; color: #00FFAA; font-weight: 700; text-transform: uppercase;'>COMPLETOS</span></div>
                    </div>
                """, unsafe_allow_html=True)

            with kpi4:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #A78BFA;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>RECOLECCIONES POR QUEJA</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{con_queja_n} <span style='font-size: 10px; color: #A78BFA; font-weight: 700; text-transform: uppercase;'>CON ID</span></div>
                    </div>
                """, unsafe_allow_html=True)

            with kpi5:
                st.markdown(f"""
                    <div class='base-card-alerta' style='border-left-color: #F97316;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>PESO ACUMULADO</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{peso_total_val:,.1f} <span style='font-size: 10px; color: #F97316; font-weight: 700; text-transform: uppercase;'>KG</span></div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown(f"<p style='font-size:11px; font-weight:700; letter-spacing:8px; color:#FFFFFF; text-transform:uppercase; text-align:center; margin-bottom:20px;'>DETALLE OPERATIVO DE GITHUB</p>", unsafe_allow_html=True)

            if not df_render.empty:
                data_render = df_render.to_dict('records')
                
                # --- CONSTRUCCIÓN DE LA TABLA ESTILO MATRIZ CON ENCABEZADO STICKY ---
                filas_html = ""
                for item in data_render:
                    estatus_val = str(item.get('ESTATUS', 'PENDIENTE')).upper()
                    
                    # Colores de badge según estatus
                    if "ENTREGADO" in estatus_val:
                        badge_color = "#00FFAA"
                        badge_bg = "rgba(0, 255, 170, 0.1)"
                    elif "PENDIENTE" in estatus_val or "PROCESO" in estatus_val:
                        badge_color = "#FDE047"
                        badge_bg = "rgba(253, 224, 71, 0.1)"
                    elif "CANCELADO" in estatus_val or "INCIDENCIA" in estatus_val:
                        badge_color = "#FF4B4B"
                        badge_bg = "rgba(255, 75, 75, 0.1)"
                    else:
                        badge_color = "#38bdf8"
                        badge_bg = "rgba(56, 189, 248, 0.1)"

                    # --- Datos del detalle desplegable ---
                    folio_txt = str(item.get('FOLIO', 'N/A'))
                    motivo_raw = str(item.get('MOTIVO', '')).strip()
                    id_queja = str(item.get('ID_QUEJA', '')).strip()
                    productos = detalle_por_folio.get(folio_txt, [])

                    motivo_html = esc(motivo_raw) if motivo_raw else "<span style='opacity:.5'>SIN CAPTURAR</span>"

                    if id_queja:
                        chip_queja = f"<span class='chip chip-queja'>QUEJA {esc(id_queja)}</span>"
                    elif motivo_raw.upper() == "QUEJA":
                        chip_queja = "<span class='chip chip-warn'>⚠ QUEJA SIN ID</span>"
                    else:
                        chip_queja = "<span class='chip'>SIN QUEJA</span>"

                    falta_captura = (not motivo_raw) or (not productos)
                    aviso = "<span class='aviso' title='Falta capturar motivo o productos'>⚠</span>" if falta_captura else ""

                    filas_prod = ""
                    for p in productos:
                        sol = float(p.get('CANT_SOLICITADA', 0) or 0)
                        rec = float(p.get('CANT_RECIBIDA', 0) or 0)
                        if rec >= sol and rec > 0:
                            color_rec = "#00FFAA"
                        elif rec > 0:
                            color_rec = "#FDE047"
                        else:
                            color_rec = "rgba(255,255,255,0.4)"
                        filas_prod += (
                            f"<tr><td class='mono'>{esc(p.get('CODIGO', ''))}</td>"
                            f"<td>{esc(p.get('DESCRIPCION', ''))}</td>"
                            f"<td class='r'>{_fmt_cant(sol)}</td>"
                            f"<td class='r' style='color:{color_rec}; font-weight:700;'>{_fmt_cant(rec)}</td></tr>"
                        )
                    if not filas_prod:
                        filas_prod = "<tr><td colspan='4' style='opacity:.5; text-align:center;'>Sin productos capturados</td></tr>"

                    motivo_dev = str(item.get('MOTIVO_DEVOLUCION', '')).strip()
                    motivo_dev_html = (esc(motivo_dev).replace("\n", "<br>") if motivo_dev
                                       else "<span style='opacity:.5'>SIN CAPTURAR</span>")
                    fila_dev = (f"<tr class='fila-texto'><td colspan='4'>"
                                f"<span class='lbl'>MOTIVO DE LA DEVOLUCIÓN:</span> {motivo_dev_html}</td></tr>")

                    filas_html += f"""
                    <tr class="fila-main" onclick="toggleDet(this)">
                        <td style="font-family: monospace; font-weight: 800; color: #FFFFFF;"><span class="flecha">▸</span> {esc(folio_txt)} {aviso}</td>
                        <td>{esc(item.get('FECHA_RECOLECCION', 'N/A'))}</td>
                        <td style="font-family: monospace; color: #38bdf8; font-weight: 700;">{esc(item.get('NUMERO DE GUIA', 'N/A'))}</td>
                        <td style="text-transform: uppercase; font-weight: 700;">{esc(item.get('CLIENTE', 'N/A'))}</td>
                        <td style="text-transform: uppercase;">{esc(item.get('PROVEEDOR', 'N/A'))}</td>
                        <td style="color: #00FFAA; font-weight: 700; text-align: right;">{float(item.get('PESO_TOTAL', 0.0)):,.2f} KG</td>
                        <td style="text-align: right; font-family: monospace; color: #FFD700;">$ {float(item.get('COSTO DE LA GUIA', 0.0)):,.2f}</td>
                        <td style="text-align: center;">
                            <span style="background-color: {badge_bg}; color: {badge_color}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid {badge_color}; display: inline-block; letter-spacing: 0.5px;">
                                {esc(estatus_val)}
                            </span>
                        </td>
                    </tr>
                    <tr class="fila-det">
                        <td colspan="8">
                            <div class="det-box">
                                <div class="det-head">MOTIVO: <b>{motivo_html}</b> &nbsp; {chip_queja} &nbsp; <span style="opacity:.6;">{len(productos)} CÓDIGO(S)</span></div>
                                <table class="sub-table">
                                    <thead>
                                        <tr>
                                            <th>CÓDIGO</th>
                                            <th>DESCRIPCIÓN</th>
                                            <th class="r">SOLICITADO</th>
                                            <th class="r">RECIBIDO</th>
                                        </tr>
                                    </thead>
                                    <tbody>{filas_prod}{fila_dev}</tbody>
                                </table>
                            </div>
                        </td>
                    </tr>
                    """

                html_tabla_matriz = f"""
                <div style="font-family: 'Inter', sans-serif; width: 100%;">
                    <style>
                        body {{ background: transparent; margin: 0; padding: 0; }}
                        
                        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ 
                            background: #3498db; 
                            border-radius: 10px; 
                            border: 2px solid #384A52; 
                        }}
                        ::-webkit-scrollbar-thumb:hover {{ 
                            background: #2ecc71; 
                            box-shadow: 0 0 10px rgba(46, 204, 113, 0.5); 
                        }}

                        .table-container {{
                            max-height: 580px;
                            overflow-y: auto;
                            border: 1px solid #4B5D67;
                            border-radius: 8px;
                            background-color: #2B343B;
                        }}

                        .matriz-table {{
                            width: 100%;
                            border-collapse: collapse;
                            text-align: left;
                            font-size: 12px;
                            color: white;
                        }}

                        .matriz-table th {{
                            position: sticky;
                            top: 0;
                            background-color: #1E252B;
                            color: rgba(255, 255, 255, 0.7);
                            font-size: 10px;
                            font-weight: 800;
                            letter-spacing: 1px;
                            text-transform: uppercase;
                            padding: 14px 16px;
                            border-bottom: 2px solid #4B5D67;
                            z-index: 10;
                        }}

                        .matriz-table td {{
                            padding: 12px 16px;
                            border-bottom: 1px solid rgba(75, 93, 103, 0.4);
                            vertical-align: middle;
                        }}

                        .matriz-table tbody tr {{
                            transition: background 0.2s ease;
                        }}

                        .matriz-table tbody tr:hover {{
                            background-color: rgba(56, 189, 248, 0.08);
                        }}

                        /* --- FILA PRINCIPAL CLICKEABLE + DETALLE DESPLEGABLE --- */
                        .fila-main {{ cursor: pointer; }}
                        .fila-main .flecha {{
                            display: inline-block;
                            color: #38bdf8;
                            transition: transform 0.2s ease;
                            margin-right: 4px;
                        }}
                        .fila-main.open .flecha {{ transform: rotate(90deg); }}
                        .fila-main.open {{ background-color: rgba(56, 189, 248, 0.12); }}
                        .aviso {{ color: #FDE047; margin-left: 4px; cursor: help; }}

                        .matriz-table tbody tr.fila-det {{ display: none; }}
                        .matriz-table tbody tr.fila-det.open {{ display: table-row; }}
                        .matriz-table tbody tr.fila-det:hover {{ background-color: transparent; }}
                        .matriz-table tbody tr.fila-det > td {{ padding: 4px 16px 16px 16px; }}

                        .det-box {{
                            background: #1E252B;
                            border: 1px solid #4B5D67;
                            border-left: 3px solid #38bdf8;
                            border-radius: 6px;
                            padding: 12px 16px;
                        }}
                        .det-head {{
                            font-size: 11px;
                            letter-spacing: 1px;
                            text-transform: uppercase;
                            margin-bottom: 10px;
                            color: rgba(255, 255, 255, 0.7);
                        }}
                        .chip {{
                            font-size: 10px;
                            font-weight: 800;
                            padding: 3px 8px;
                            border-radius: 6px;
                            border: 1px solid #4B5D67;
                            color: #94a3b8;
                            letter-spacing: 0.5px;
                        }}
                        .chip-queja {{ color: #F97316; border-color: #F97316; background: rgba(249, 115, 22, 0.1); }}
                        .chip-warn {{ color: #FDE047; border-color: #FDE047; background: rgba(253, 224, 71, 0.1); }}

                        .matriz-table .sub-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
                        .matriz-table .sub-table th {{
                            position: static;
                            background: transparent;
                            padding: 6px 10px;
                            font-size: 9px;
                            border-bottom: 1px solid #4B5D67;
                        }}
                        .matriz-table .sub-table td {{
                            padding: 6px 10px;
                            border-bottom: 1px solid rgba(75, 93, 103, 0.3);
                        }}
                        .matriz-table .sub-table .mono {{ font-family: monospace; color: #38bdf8; font-weight: 700; }}
                        .matriz-table .sub-table .r, .matriz-table .sub-table th.r {{ text-align: right; }}
                        .matriz-table .sub-table .fila-texto td {{ border-top: 1px solid #4B5D67; border-bottom: none; padding-top: 10px; line-height: 1.5; }}
                        .matriz-table .sub-table .lbl {{ font-size: 9px; font-weight: 800; letter-spacing: 1px; color: rgba(255, 255, 255, 0.6); margin-right: 6px; }}
                    </style>

                    <div class="table-container">
                        <table class="matriz-table">
                            <thead>
                                <tr>
                                    <th>FACTURA / FOLIO</th>
                                    <th>RECOLECCIÓN</th>
                                    <th>NO. GUÍA</th>
                                    <th>CLIENTE</th>
                                    <th>PROVEEDOR</th>
                                    <th style="text-align: right;">PESO TOTAL</th>
                                    <th style="text-align: right;">COSTO GUÍA</th>
                                    <th style="text-align: center;">ESTATUS</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filas_html}
                            </tbody>
                        </table>
                    </div>

                    <script>
                        function toggleDet(tr) {{
                            tr.classList.toggle('open');
                            tr.nextElementSibling.classList.toggle('open');
                        }}
                    </script>
                </div>
                """
                
                components.html(html_tabla_matriz, height=620, scrolling=False)

                # --- REPORTE PDF POR FOLIO ---
                col_pdf1, col_pdf2 = st.columns([3, 1], vertical_alignment="bottom")
                with col_pdf1:
                    folios_pdf = df_render["FOLIO"].astype(str).unique().tolist()
                    folio_pdf = st.selectbox("FOLIO PARA REPORTE PDF", folios_pdf, key="sel_folio_pdf")
                with col_pdf2:
                    fila_pdf = df_render[df_render["FOLIO"].astype(str) == str(folio_pdf)].iloc[0].to_dict()
                    pdf_bytes = generar_pdf_recoleccion(fila_pdf, detalle_por_folio.get(str(folio_pdf), []))
                    if pdf_bytes:
                        st.download_button("📄 DESCARGAR PDF", data=pdf_bytes,
                                           file_name=_nombre_pdf(folio_pdf), mime="application/pdf",
                                           key="btn_pdf_tab1", use_container_width=True)
            else:
                st.markdown(f"""
                    <div style="background: rgba(56, 189, 248, 0.05); border: 1px dashed #38bdf8; border-radius: 10px; padding: 25px; text-align: center; margin-top: 20px;">
                        <p style="color: #38bdf8; font-size: 16px; margin: 0;"><b>SIN REGISTROS BAJO ESTE FILTRO</b></p>
                        <p style="color: #94a3b8; font-size: 12px; margin-top: 5px;">No se encontraron elementos que coincidan con los criterios seleccionados en el render.</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aún no hay registros de estatus guardados en GitHub para renderizar en este apartado.")

    # --- TAB 2: EDICIÓN Y ACTUALIZACIÓN ---
    with tab2:

        if st.session_state.get("mensaje_guardado"):
            st.success(st.session_state.mensaje_guardado)
            del st.session_state.mensaje_guardado

        st.markdown(
            "<div style='margin-bottom:18px;'>"
            "<div style='color:#FFFFFF;font-size:19px;font-weight:800;letter-spacing:.3px;'>EDICIÓN Y ACTUALIZACIÓN</div>"
            "<div style='color:#8B9BB4;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;'>MODIFICAR ESTATUS, MOTIVO Y PRODUCTOS DE FOLIOS</div>"
            "</div>",
            unsafe_allow_html=True
        )

        df_estatus_edit = cargar_estatus_github()

        if not df_estatus_edit.empty:
            folios_list = df_estatus_edit["Folio"].astype(str).unique().tolist()
            folio_a_editar = st.selectbox("Selecciona el Folio a Modificar / Actualizar", folios_list, key="edit_folio_sel")

            if folio_a_editar:
                fila_actual = df_estatus_edit[df_estatus_edit["Folio"].astype(str) == str(folio_a_editar)].iloc[0]

                # Productos actuales de este folio
                df_det_all = cargar_detalle_github()
                det_folio = df_det_all[df_det_all["Folio"].astype(str) == str(folio_a_editar)]
                prod_orig = _limpiar_productos(det_folio[COLUMNAS_PROD_EDIT])

                # Cada folio tiene sus propias llaves de widget => no se arrastra nada de otro registro
                k = re.sub(r"\W", "_", str(folio_a_editar))
                claves = {n: f"edit_{n}_{k}" for n in ["estatus", "solicitante", "guia", "costo", "peso",
                                                       "cliente", "proveedor", "obs",
                                                       "motivo", "queja", "prod", "pegar", "motdev"]}
                OPC_ESTATUS = ["PENDIENTE", "EN RUTA", "ENTREGADO", "CANCELADO", "INCIDENCIA"]
                estatus_actual = str(fila_actual.get("Estatus", "PENDIENTE")).strip().upper()

                motivo_actual = str(fila_actual.get("Motivo", "")).strip()
                opciones_motivo_edit = list(OPC_MOTIVO)
                if motivo_actual and motivo_actual not in opciones_motivo_edit:
                    opciones_motivo_edit.append(motivo_actual)  # respeta valores previos fuera de catálogo
                idx_motivo = opciones_motivo_edit.index(motivo_actual) if motivo_actual in opciones_motivo_edit else 0

                with st.form(f"form_edicion_estatus_{k}"):
                    st.markdown(f"**Editando Folio:** `{folio_a_editar}`")

                    nuevo_estatus = st.selectbox(
                        "Estatus de la Recolección", OPC_ESTATUS,
                        index=OPC_ESTATUS.index(estatus_actual) if estatus_actual in OPC_ESTATUS else 0,
                        key=claves["estatus"],
                    )

                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        nuevo_solicitante = st.text_input("Solicitante", value=str(fila_actual.get("Solicitante", "")), key=claves["solicitante"])
                        nuevo_num_guia = st.text_input("Número de Guía", value=str(fila_actual.get("Numero de Guia", "")), key=claves["guia"])
                    with col_e2:
                        nuevo_costo_guia = st.number_input("Costo de la Guía", value=float(fila_actual.get("Costo de la Guia", 0.0)), key=claves["costo"])
                        nuevo_peso = st.number_input("Peso Total (KG)", value=float(fila_actual.get("Peso_Total", 0.0)), key=claves["peso"])

                    nuevo_cliente = st.text_input("Cliente Destino", value=str(fila_actual.get("Cliente", "")), key=claves["cliente"])
                    nuevo_proveedor = st.text_input("Proveedor Remitente", value=str(fila_actual.get("Proveedor", "")), key=claves["proveedor"])
                    nueva_obs = st.text_area("Observaciones / Notas de Entrega", value=str(fila_actual.get("Observaciones", "")), key=claves["obs"])

                    # --- MOTIVO DE LA RECOLECCIÓN ---
                    st.markdown("---")
                    st.markdown("**Motivo de la recolección**")
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        nuevo_motivo = st.selectbox("Motivo", opciones_motivo_edit, index=idx_motivo, key=claves["motivo"])
                    with col_m2:
                        nuevo_id_queja = st.text_input(
                            "ID de queja (déjalo vacío si no aplica)",
                            value=str(fila_actual.get("ID_Queja", "")),
                            key=claves["queja"],
                        )

                    # --- PRODUCTOS DE LA RECOLECCIÓN ---
                    st.markdown("**Productos de esta recolección**")
                    prod_editado = st.data_editor(
                        prod_orig,
                        num_rows="dynamic",
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Codigo": st.column_config.TextColumn("Código", required=False),
                            "Descripcion": st.column_config.TextColumn("Descripción"),
                            "Cant_Solicitada": st.column_config.NumberColumn("Solicitado", min_value=0, step=1, format="%g"),
                            "Cant_Recibida": st.column_config.NumberColumn("Recibido", min_value=0, step=1, format="%g"),
                        },
                        key=claves["prod"],
                    )

                    texto_pegado = st.text_area(
                        "Pegar códigos rápido (opcional): una línea por producto → CÓDIGO, CANTIDAD, DESCRIPCIÓN (opcional)",
                        height=90,
                        key=claves["pegar"],
                        placeholder="ABC-123, 5, Jabón líquido 1L\nXYZ-999, 2",
                    )

                    nuevo_motivo_dev = st.text_area(
                        "Motivo de la devolución (texto libre, va al final de los códigos)",
                        value=str(fila_actual.get("Motivo_Devolucion", "")),
                        height=90,
                        key=claves["motdev"],
                    )

                    btn_guardar_cambios = st.form_submit_button("💾 GUARDAR CAMBIOS")

                # PDF del folio con lo que ya está guardado (si acabas de editar, guarda primero)
                pdf_edit = generar_pdf_recoleccion(fila_actual.to_dict(), prod_orig.to_dict("records"))
                if pdf_edit:
                    st.download_button("📄 DESCARGAR PDF DEL FOLIO", data=pdf_edit,
                                       file_name=_nombre_pdf(folio_a_editar), mime="application/pdf",
                                       key=f"btn_pdf_edit_{k}")

                if btn_guardar_cambios:
                    motivo_guardar = "" if nuevo_motivo == "SIN DEFINIR" else nuevo_motivo

                    # Productos: lo editado en la tabla + lo pegado en el cuadro de texto
                    prod_nuevo = _limpiar_productos(
                        pd.concat([_limpiar_productos(prod_editado), _parsear_pegado(texto_pegado)],
                                  ignore_index=True)
                    )
                    cambio_prod = prod_nuevo.to_dict("records") != prod_orig.to_dict("records")

                    # Solo se envían los campos que realmente cambiaron, de ESTA fila
                    candidatos = {
                        "Estatus": nuevo_estatus,
                        "Observaciones": nueva_obs,
                        "Cliente": nuevo_cliente,
                        "Proveedor": nuevo_proveedor,
                        "Solicitante": nuevo_solicitante,
                        "Numero de Guia": str(nuevo_num_guia).strip(),
                        "Peso_Total": float(nuevo_peso),
                        "Costo de la Guia": float(nuevo_costo_guia),
                        "Motivo": motivo_guardar,
                        "ID_Queja": str(nuevo_id_queja).strip(),
                        "Motivo_Devolucion": str(nuevo_motivo_dev).strip(),
                    }
                    cambios = {}
                    for col, val in candidatos.items():
                        orig = fila_actual.get(col, "")
                        if col in COLUMNAS_NUM:
                            if abs(float(orig) - float(val)) > 1e-9:
                                cambios[col] = val
                        elif str(orig).strip() != str(val).strip():
                            cambios[col] = val

                    if not cambios and not cambio_prod:
                        st.info("No hay cambios que guardar en este folio.")
                    else:
                        ok = True
                        # 1) Primero el detalle de productos; 2) después el encabezado.
                        #    Así, si algo falla a la mitad, no queda un folio con motivo pero sin productos.
                        if cambio_prod:
                            ok = reemplazar_detalle_github(
                                folio_a_editar, prod_nuevo,
                                f"Actualización de productos del folio {folio_a_editar} ({len(prod_nuevo)} códigos)",
                            )
                        if ok and cambios:
                            ok = actualizar_folio_github(
                                folio_a_editar, cambios,
                                f"Actualización de folio {folio_a_editar}: {', '.join(cambios)}",
                            )
                            if not ok and cambio_prod:
                                st.warning("Los productos sí se guardaron, pero los datos del folio no. Vuelve a intentar.")

                        if ok:
                            for c in claves.values():      # borra cualquier rastro del formulario
                                st.session_state.pop(c, None)
                            msg = f"¡Folio {folio_a_editar} actualizado correctamente en GitHub!"
                            if motivo_guardar == "QUEJA" and not str(nuevo_id_queja).strip():
                                msg += " ⚠ El motivo es QUEJA pero falta el ID de queja."
                            st.session_state.mensaje_guardado = msg
                            st.rerun()
        else:
            st.warning("No hay registros disponibles para editar en GitHub.")

if __name__ == "__main__":
    main()
