import base64
import calendar
from datetime import date, datetime, timedelta
import io
from io import BytesIO, StringIO
import json
import math
import os
import random
import re
import time
import unicodedata
import zipfile

import altair as alt
from fpdf import FPDF
from github import Github
import google.generativeai as genai
import numpy as np
import pandas as pd

# CAMBIO 1: Pillow con alias para no chocar con ReportLab
from PIL import Image as PILImage, ImageDraw, ImageFont

import plotly.express as px
import plotly.graph_objects as go
from pypdf import PdfReader, PdfWriter
import pytz
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

# CAMBIO 2: Importamos platypus completo para usar platypus.Image sin perder ningún elemento
import reportlab.platypus as platypus
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image


import requests
import streamlit as st
import streamlit.components.v1 as components


from components.layout import render_layout


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Formato de Recolecciones 3G",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="FORMATOS", submodulo_actual="RECOLECCION 3G")
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


# Inicialización segura de estados de menú
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "FORMATOS"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "RECOLECCIONES 3G"
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
        /* 2. Estilo corporativo para los botones personalizados */
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
    
    # --- FUNCIONES DE GITHUB PARA EL CONTROL DE ESTATUS Y EDICIÓN ---
    GITHUB_REPO = "RH2026/nexion"
    GITHUB_FILE = "recolecciones_estatus.csv"
    BRANCH = "main"

    def cargar_estatus_github():
        try:
            url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{GITHUB_FILE}"
            token = st.secrets["GITHUB_TOKEN"]
            headers = {"Authorization": f"token {token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
                df.columns = df.columns.astype(str).str.strip()
                
                # Definir esquema base estricto y limpiar nulos a prueba de errores
                columnas_requeridas = {
                    "Folio": str,
                    "Fecha_Recoleccion": str,
                    "Cliente": str,
                    "Proveedor": str,
                    "Peso_Total": float,
                    "Estatus": str,
                    "Observaciones": str,
                    "Solicitante": str,
                    "Numero de Guia": str,
                    "Costo de la Guia": float
                }
                
                for col, tipo in columnas_requeridas.items():
                    if col not in df.columns:
                        df[col] = "" if tipo == str else 0.0
                    else:
                        if tipo == float:
                            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                        else:
                            df[col] = df[col].astype(str).replace("nan", "")
                            
                return df
            else:
                return pd.DataFrame(columns=["Folio", "Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total", "Estatus", "Observaciones", "Solicitante", "Numero de Guia", "Costo de la Guia"])
        except Exception:
            return pd.DataFrame(columns=["Folio", "Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total", "Estatus", "Observaciones", "Solicitante", "Numero de Guia", "Costo de la Guia"])

    def guardar_estatus_github(df_nuevo, mensaje="Actualizar estatus de recolecciones"):
        try:
            token = st.secrets["GITHUB_TOKEN"]
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            
            response_get = requests.get(url, headers=headers)
            sha = response_get.json().get("sha") if response_get.status_code == 200 else None

            csv_buffer = df_nuevo.to_csv(index=False, encoding="utf-8-sig")
            content_encoded = base64.b64encode(csv_buffer.encode("utf-8")).decode("utf-8")

            payload = {
                "message": mensaje,
                "content": content_encoded,
                "branch": BRANCH
            }
            if sha:
                payload["sha"] = sha

            response_put = requests.put(url, headers=headers, json=payload)
            if response_put.status_code in [200, 201]:
                return True
            else:
                st.error(f"Error al guardar en GitHub: {response_put.status_code} - {response_put.text}")
                return False
        except Exception as e:
            st.error(f"No se pudo guardar en GitHub: {e}")
            return False

    # --- DEFINICIÓN DE TABS ---
    tab1, tab2, tab3 = st.tabs(["Formato Solicitud", "Render de Estatus", "Edición y Actualización"])
    # --- TAB 1: EL FORMATO ORIGINAL DE TRESGUERRAS ---
    with tab1:
        
        @st.cache_data(ttl=300)
        def obtener_logo_tresguerras():
            try:
                repo = "RH2026/nexion"
                filename = "logo_3G.png"
                branch = "main"
                url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filename}"
                token = st.secrets["GITHUB_TOKEN"]
                headers = {"Authorization": f"token {token}"}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    return BytesIO(response.content)
                return None
            except Exception:
                return None

        @st.cache_data(ttl=60)
        def cargar_matriz_facturacion_completa():
            try:
                repo = "RH2026/nexion"
                filename = "clientes.csv"
                branch = "main"
                url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filename}"
                token = st.secrets["GITHUB_TOKEN"]
                headers = {"Authorization": f"token {token}"}
                
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
                    df.columns = [str(c).upper().strip() for c in df.columns]
                    return df
                else:
                    st.error(f"Error al descargar {filename} de GitHub (Código {response.status_code}).")
                    return pd.DataFrame()
            except Exception as e:
                st.error(f"No se pudo cargar la matriz de facturación: {e}")
                return pd.DataFrame()

        df_facturacion = cargar_matriz_facturacion_completa()
        registro = pd.Series()    

        if not df_facturacion.empty:
            df_facturacion.columns = [str(c).upper().strip() for c in df_facturacion.columns]
            
            col_cliente_num = "CLIENTE" if "CLIENTE" in df_facturacion.columns else None
            col_nombre_hotel = "NOMBRE_EXTRAN" if "NOMBRE_EXTRAN" in df_facturacion.columns else None

            if col_cliente_num:
                df_facturacion[col_cliente_num] = df_facturacion[col_cliente_num].astype(str)

            # --- CONTROLES DE BÚSQUEDA (EXCLUSIVO NÚMERO DE CLIENTE EN 4 COLUMNAS) ---
            top_col1, top_col2, top_col3, top_col4 = st.columns(4)
            
            with top_col1:
                fecha_recoleccion_deseada = st.date_input("📅 Fecha Recolección", value=datetime.now(), key="tg_fecha_rec")
            fecha_rec_str = fecha_recoleccion_deseada.strftime("%d/%m/%Y")

            with top_col2:
                if col_cliente_num:
                    clientes_disponibles = sorted(df_facturacion[col_cliente_num].dropna().unique().tolist())
                    cliente_elegido = st.selectbox("Selecciona No. Cliente", clientes_disponibles, key="tg_sel_cte")
                    
                    if cliente_elegido:
                        match_cte = df_facturacion[df_facturacion[col_cliente_num] == str(cliente_elegido)]
                        if not match_cte.empty:
                            registro = match_cte.iloc[0]
                else:
                    st.warning("No se encontró la columna CLIENTE en la matriz.")

            with top_col3:
                num_factura = st.text_input("✍️ Folio / Referencia", value="S/F", key="tg_txt_fact_nuevo")

            with top_col4:
                tipo_pago_tg = st.selectbox("💳 Condición de Pago", ["POR COBRAR (DESTINO)", "PAGADO (ORIGEN)", "CRÉDITO"], key="tg_tipo_pago")

            # Mapeo seguro de datos desde el registro seleccionado
            def_extran = str(registro.get(col_nombre_hotel, "")) if not registro.empty and col_nombre_hotel and pd.notna(registro.get(col_nombre_hotel, "")) else ""
            def_dom = str(registro.get("DOMICILIO", registro.get("CALLE", ""))) if not registro.empty and pd.notna(registro.get("DOMICILIO", registro.get("CALLE", ""))) else ""
            def_col = str(registro.get("COLONIA", "")) if not registro.empty and pd.notna(registro.get("COLONIA", "")) else ""
            def_cui = str(registro.get("CUIDAD", registro.get("CIUDAD", ""))) if not registro.empty and pd.notna(registro.get("CUIDAD", registro.get("CIUDAD", ""))) else ""
            def_cp = str(registro.get("CP", "")) if not registro.empty and pd.notna(registro.get("CP", "")) else ""
            def_est = str(registro.get("ESTADO", "")) if not registro.empty and pd.notna(registro.get("ESTADO", "")) else ""

            tel_val = ""
            if not registro.empty:
                for col_p in ["TELEFONO", "TEL", "TELÉFONO"]:
                    if col_p in registro and pd.notna(registro[col_p]):
                        tel_val = str(registro[col_p]).strip()
                        break

            st.markdown("---")

            def titulo_seccion(texto, color_fondo="#b71c1c"):
                st.markdown(f"""
                    <div style="background-color: {color_fondo}; padding: 8px; border-radius: 4px; text-align: center; color: white; font-weight: bold; font-size: 15px; margin-bottom: 10px;">
                        {texto}
                    </div>
                """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                titulo_seccion("REMITENTE - RECOLECCIÓN (PROVEEDOR)", color_fondo="#e65100")
                rem_cliente = st.text_input("Comercializadora / Proveedor", value=def_extran, key=f"rem_cli_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                rem_calle = st.text_input("Calle y Número (Remitente)", value=def_dom, key=f"rem_call_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                rc1, rc2 = st.columns(2)
                with rc1:
                    rem_colonia = st.text_input("Colonia (Remitente)", value=def_col, key=f"rem_col_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                with rc2:
                    rem_cp = st.text_input("CP (Remitente)", value=def_cp, key=f"rem_cp_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                rc3, rc4 = st.columns(2)
                with rc3:
                    rem_cui = st.text_input("Ciudad / Municipio", value=def_cui, key=f"rem_cui_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                with rc4:
                    rem_estado = st.text_input("Estado", value=def_est, key=f"rem_est_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                rc5, rc6 = st.columns(2)
                with rc5:
                    rem_contacto = st.text_input("Persona que entrega", value="", key=f"rem_cont_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                with rc6:
                    rem_tel = st.text_input("Teléfono Remitente", value=tel_val, key=f"rem_tel_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")

            with col2:
                titulo_seccion("DESTINATARIO - ENTREGA (JYPESA)", color_fondo="#4B6B94")
                dest_cliente = st.text_input("Cliente Destino", value="Jabones y productos Especializados", key=f"dest_cli_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                dest_calle = st.text_input("Calle Destino", value="C. Cernícalo 155", key=f"dest_call_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                dc1, dc2 = st.columns(2)
                with dc1:
                    dest_colonia = st.text_input("Colonia Destino", value="La Aurora", key=f"dest_col_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                with dc2:
                    dest_cp = st.text_input("CP Destino", value="44460", key=f"dest_cp_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                dc3, dc4 = st.columns(2)
                with dc3:
                    dest_cui = st.text_input("Ciudad Destino", value="Guadalajara", key=f"dest_cui_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                with dc4:
                    dest_estado = st.text_input("Estado Destino", value="Jalisco", key=f"dest_est_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                dc5, dc6 = st.columns(2)
                with dc5:
                    dest_contacto = st.text_input("Persona que recibe", value="Jazmin Castillo", key=f"dest_cont_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
                with dc6:
                    dest_tel = st.text_input("Teléfono Destino", value="33 3540 2939 Ext.123", key=f"dest_tel_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")

            titulo_seccion("FACTURAR A (DATOS FISCALES JYPESA)", color_fondo="#37474f")
            fac_cliente = st.text_input("Facturar a Nombre de", value="JABONES Y PRODUCTOS ESPECIALIZADOS SA DE CV", key=f"fac_cli_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            fac_domicilio = st.text_input("Domicilio Fiscal", value="Privada del Gallo No. 1525, Col. La Aurora C.P. 44460 Guadalajara, JAL México", key=f"fac_dom_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            fac_rfc = st.text_input("RFC Facturación", value="JPE830408B35", key=f"fac_rfc_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")

            # --- SECCIÓN DINÁMICA DE EMBARQUE ---
            st.markdown("---")
            titulo_seccion("📦 DETALLE DE EMBARQUE Y LÍNEAS DE CARGA", color_fondo="#e65100")

            if "lineas_embarque" not in st.session_state:
                st.session_state.lineas_embarque = [
                    {"cantidad": 1, "tipo": "TARIMA", "descripcion": "AMENIDADES", "largo": 1.20, "ancho": 1.20, "alto": 2.00, "peso": 800.0}
                ]

            for idx, linea in enumerate(st.session_state.lineas_embarque):
                st.markdown(f"**Renglón {idx + 1}**")
                lc1, lc2, lc3, lc4, lc5, lc6, lc7 = st.columns([1, 2, 2, 1, 1, 1, 1])
                with lc1:
                    linea["cantidad"] = st.number_input("Cant.", min_value=1, value=linea["cantidad"], key=f"cant_{idx}")
                with lc2:
                    linea["tipo"] = st.selectbox("Tipo Bulto", ["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"], index=["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"].index(linea["tipo"]) if linea["tipo"] in ["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"] else 0, key=f"tipo_{idx}")
                with lc3:
                    linea["descripcion"] = st.text_input("Descripción", value=linea["descripcion"], key=f"desc_{idx}")
                with lc4:
                    linea["largo"] = st.number_input("Largo (m)", value=float(linea["largo"]), key=f"larg_{idx}")
                with lc5:
                    linea["ancho"] = st.number_input("Ancho (m)", value=float(linea.get("ancho", 1.20)), key=f"anch_{idx}")
                with lc6:
                    linea["alto"] = st.number_input("Alto (m)", value=float(linea["alto"]), key=f"alt_{idx}")
                with lc7:
                    linea["peso"] = st.number_input("Peso (KG)", value=float(linea["peso"]), key=f"pes_{idx}")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("➕ Agregar otra línea de carga", key="btn_add_line"):
                    st.session_state.lineas_embarque.append({"cantidad": 1, "tipo": "CAJA", "descripcion": "MERCANCIA", "largo": 0.50, "ancho": 0.50, "alto": 0.50, "peso": 50.0})
                    st.rerun()
            with col_btn2:
                if len(st.session_state.lineas_embarque) > 1 and st.button("🗑️ Eliminar última línea", key="btn_del_line"):
                    st.session_state.lineas_embarque.pop()
                    st.rerun()

            total_peso_calc = sum(l["peso"] * l["cantidad"] for l in st.session_state.lineas_embarque)
            st.info(f"⚖️ **Peso Total Calculado:** {total_peso_calc:,.2f} KG")

            def generar_pdf_tresguerras_oficial():
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
                story = []
                
                fecha_actual = datetime.now().strftime("%d/%m/%Y")
                
                th_style = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=colors.white, alignment=1)
                cell_bold = ParagraphStyle("CB", fontName="Helvetica-Bold", fontSize=6, leading=7.5)
                cell_normal = ParagraphStyle("CN", fontName="Helvetica", fontSize=6, leading=7.5)
                cell_center = ParagraphStyle("CC", fontName="Helvetica", fontSize=6, leading=7.5, alignment=1)

                logo_io = obtener_logo_tresguerras()
                logo_elem = Image(logo_io, width=85, height=22) if logo_io else Paragraph("<b>TRESGUERRAS</b>", cell_center)
                
                header_table = Table([
                    [
                        logo_elem, 
                        Paragraph("<b>AUTOTRANSPORTES DE CARGA TRESGUERRAS<br/>SOLICITUD DE SERVICIO</b>", ParagraphStyle("HT", alignment=1, fontSize=8.5, fontName="Helvetica-Bold")), 
                        Paragraph(f"<b>FECHA SOLICITUD:</b> {fecha_actual}<br/><b>FOLIO:</b> {num_factura}", ParagraphStyle("H2", fontSize=6, alignment=1))
                    ],
                    ["", Paragraph("PAQUETERIA", ParagraphStyle("PAQ", alignment=1, fontSize=5.5, fontName="Helvetica-Bold")), ""]
                ], colWidths=[105, 382, 115])
                header_table.setStyle(TableStyle([
                    ("SPAN", (0,0), (0,1)),
                    ("SPAN", (2,0), (2,1)),
                    ("GRID", (0,0), (-1,-1), 1, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("ALIGN", (0,0), (0,0), "CENTER"),
                    ("BACKGROUND", (1,0), (1,0), colors.HexColor("#e0e0e0")),
                    ("BACKGROUND", (2,0), (2,0), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (1,1), (1,1), colors.HexColor("#f5f5f5")),
                ]))
                story.append(header_table)
                story.append(Spacer(1, 2))

                fechas_table = Table([
                    [Paragraph("<b>FECHA DE RECOLECCION:</b>", cell_bold), Paragraph(fecha_rec_str, cell_center), Paragraph("<b>FECHA SOLICITUD</b>", cell_bold), Paragraph(fecha_actual, cell_center)],
                    [Paragraph("<b>FECHA DE RECEPCION:</b>", cell_bold), "", Paragraph("<b>FOLIO</b>", cell_bold), ""]
                ], colWidths=[110, 150, 105, 237])
                fechas_table.setStyle(TableStyle([
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("BACKGROUND", (1,0), (1,0), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (3,0), (3,0), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (1,1), (1,1), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (3,1), (3,1), colors.HexColor("#fff59d")),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))
                story.append(fechas_table)
                story.append(Spacer(1, 2))

                rem_data = [
                    [Paragraph("REMITENTE - RECOLECCION", th_style), ""],
                    [Paragraph("CLIENTE:", cell_bold), Paragraph(rem_cliente, cell_bold)],
                    [Paragraph("CALLE Y NUMERO:", cell_bold), Paragraph(rem_calle, cell_normal)],
                    [Paragraph("COLONIA / CP:", cell_bold), Paragraph(f"{rem_colonia} - C.P. {rem_cp}", cell_normal)],
                    [Paragraph("CIUDAD / ESTADO:", cell_bold), Paragraph(f"{rem_cui}, {rem_estado}", cell_normal)],
                    [Paragraph("CONTACTO / TEL:", cell_bold), Paragraph(f"{rem_contacto} - {rem_tel}", cell_normal)],
                ]
                t_rem = Table(rem_data, colWidths=[90, 211])
                t_rem.setStyle(TableStyle([
                    ("SPAN", (0,0), (1,0)),
                    ("BACKGROUND", (0,0), (1,0), colors.HexColor("#e65100")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))

                dest_data = [
                    [Paragraph("DESTINATARIO - ENTREGA", th_style), ""],
                    [Paragraph("CLIENTE:", cell_bold), Paragraph(dest_cliente, cell_bold)],
                    [Paragraph("CALLE Y NUMERO:", cell_bold), Paragraph(dest_calle, cell_normal)],
                    [Paragraph("COLONIA / CP:", cell_bold), Paragraph(f"{dest_colonia} - C.P. {dest_cp}", cell_normal)],
                    [Paragraph("CIUDAD / ESTADO:", cell_bold), Paragraph(f"{dest_cui}, {dest_estado}", cell_normal)],
                    [Paragraph("CONTACTO / TEL:", cell_bold), Paragraph(f"{dest_contacto} - {dest_tel}", cell_normal)],
                ]
                t_dest = Table(dest_data, colWidths=[90, 211])
                t_dest.setStyle(TableStyle([
                    ("SPAN", (0,0), (1,0)),
                    ("BACKGROUND", (0,0), (1,0), colors.black),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))

                t_top = Table([[t_rem, t_dest]], colWidths=[301, 301])
                story.append(t_top)
                story.append(Spacer(1, 2))

                fac_data = [
                    [Paragraph("<b>FACTURAR A:</b>", th_style), "", ""],
                    [Paragraph(fac_cliente, cell_center), "", ""],
                    [Paragraph("<b>DOMICILIO:</b>", cell_bold), Paragraph("Cel. 33 19 75 31 22", cell_center), ""],
                    [Paragraph(f"Privada del Gallo No. 1525, Col. La Aurora C.P. 44460 Guadalajara, JAL México<br/>Tel.. 0152 (33) 35402939<br/>E-mail: rhernandez@jypesa.com", ParagraphStyle("FD", alignment=1, fontSize=6, fontName="Helvetica", leading=7.5)), "", ""],
                    [Paragraph("<b>RFC:</b>", cell_bold), Paragraph(f"RFC {fac_rfc}", cell_center), ""]
                ]
                t_fac = Table(fac_data, colWidths=[75, 427, 100])
                t_fac.setStyle(TableStyle([
                    ("SPAN", (0,0), (2,0)),
                    ("SPAN", (0,1), (2,1)),
                    ("SPAN", (1,2), (2,2)),
                    ("SPAN", (0,3), (2,3)),
                    ("SPAN", (1,4), (2,4)),
                    ("BACKGROUND", (0,0), (2,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (0,1), (2,1), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (0,2), (0,2), colors.HexColor("#b71c1c")),
                    ("TEXTCOLOR", (0,2), (0,2), colors.white),
                    ("BACKGROUND", (1,2), (2,2), colors.HexColor("#ffffff")),
                    ("BACKGROUND", (0,3), (2,3), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (0,4), (2,4), colors.HexColor("#b71c1c")),
                    ("TEXTCOLOR", (0,4), (2,4), colors.white),
                    ("BACKGROUND", (1,4), (2,4), colors.HexColor("#fff59d")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))
                story.append(t_fac)
                story.append(Spacer(1, 2))

                emb_headers = ["Cantidad", "TIPO DE BULTOS", "DESCRIPCION", "DIAMETRO", "ALTO", "CUBICAJE (m3)", "PESO (KG)"]
                emb_data = [
                    [Paragraph("<b>INFORMACION DE EMBARQUE</b>", th_style), "", "", Paragraph("<b>DIMENSIONES (mts)</b>", th_style), "", Paragraph("<b>VOLUMEN</b>", th_style), Paragraph("<b>PESO POR BULTO</b>", th_style)],
                    [Paragraph(h, th_style) for h in emb_headers]
                ]

                for l in st.session_state.lineas_embarque:
                    ancho_val = l.get('ancho', 1.20)
                    dim_str = f"{l['largo']} x {ancho_val} x {l['alto']}"
                    emb_data.append([
                        str(l["cantidad"]), 
                        str(l["tipo"]), 
                        str(l["descripcion"]), 
                        str(dim_str), 
                        "", 
                        "0", 
                        str(l["peso"])
                    ])

                filas_actuales = len(st.session_state.lineas_embarque)
                for _ in range(max(0, 6 - filas_actuales)):
                    emb_data.append(["", "", "", "", "", "0", ""])
                    
                emb_data.append(["", "", "", "", "", "0", f"{total_peso_calc:,.1f}"])

                t_emb = Table(emb_data, colWidths=[45, 65, 182, 95, 65, 80, 70])
                t_emb.setStyle(TableStyle([
                    ("SPAN", (0,0), (2,0)),
                    ("SPAN", (3,0), (4,0)),
                    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#b71c1c")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("ALIGN", (0,0), (-1,-1), "CENTER"),
                    ("TOPPADDING", (0,0), (-1,-1), 1.5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                ]))
                story.append(t_emb)
                story.append(Spacer(1, 2))

                th_red = ParagraphStyle("THR", fontName="Helvetica-Bold", fontSize=6, leading=7, textColor=colors.white, alignment=1)
                th_green = ParagraphStyle("THG", fontName="Helvetica-Bold", fontSize=6, leading=7, textColor=colors.white, alignment=1)

                mid_table_data = [
                    [
                        Paragraph("<b>MERCANCIA ASEGURADA</b>", th_red), 
                        Paragraph("<b>REQUIERE ACUSE DE RECIBO</b>", th_red), 
                        Paragraph("<b>DESCRIPCION DEL ACUSE:</b>", th_red)
                    ],
                    [
                        Table([
                            [Paragraph("SI", cell_center), "", Paragraph("VALOR DECLARADO", cell_bold)],
                            [Paragraph("NO", cell_center), Paragraph("X", cell_center), Paragraph("POR CUENTA Y RIESGO", cell_bold)]
                        ], colWidths=[30, 30, 85], style=[
                            ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#fff59d")),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                        ]),
                        Table([
                            [Paragraph("SI", cell_center), Paragraph("X", cell_center), Paragraph("N<br/>O", cell_center)],
                            ["", "", ""]
                        ], colWidths=[30, 30, 25], style=[
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                        ]),
                        ""
                    ],
                    [
                        Paragraph("<b>TIPO DE PAGO MARCAR CON UNA X</b>", th_green), 
                        Paragraph("<b>MARCAR CON UNA X (EAD / OCURRE)</b>", th_green), 
                        Paragraph("<b>DOCUMENTOS QUE ANEXA</b>", th_red)
                    ],
                    [
                        Table([
                            [Paragraph("pagado (origen)", cell_center), Paragraph("por cobrar (destino)", cell_center), Paragraph("Credito", cell_center)],
                            ["", "", Paragraph("X", cell_center)]
                        ], colWidths=[48, 52, 45], style=[
                            ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                        ]),
                        Table([
                            [Paragraph("Recolección", cell_center), Paragraph("Recepción", cell_center), Paragraph("Entrega Domicilio", cell_center)],
                            [Paragraph("X", cell_center), "", Paragraph("X", cell_center)]
                        ], colWidths=[48, 45, 62], style=[
                            ("BACKGROUND", (0,1), (0,1), colors.HexColor("#fff59d")),
                            ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                        ]),
                        Table([
                            [Paragraph("factura", cell_center), Paragraph("orden de compra", cell_center), Paragraph("pedimento", cell_center), Paragraph("otro", cell_center)]
                        ], colWidths=[70, 70, 70, 62], style=[
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 4),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                        ])
                    ]
                ]

                t_mid = Table(mid_table_data, colWidths=[145, 155, 302])
                t_mid.setStyle(TableStyle([
                    ("SPAN", (2,1), (2,1)),
                    ("BACKGROUND", (0,0), (0,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (1,0), (1,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (2,0), (2,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                    ("BACKGROUND", (0,2), (0,2), colors.HexColor("#2e7d32")),
                    ("BACKGROUND", (1,2), (1,2), colors.HexColor("#2e7d32")),
                    ("BACKGROUND", (2,2), (2,2), colors.HexColor("#b71c1c")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("TOPPADDING", (0,0), (-1,-1), 1),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                ]))
                story.append(t_mid)
                story.append(Spacer(1, 2))

                t_final_block = Table([
                    [Paragraph("<b>DATOS DE QUIEN SOLICITA EL SERVICIO</b>", th_style), Paragraph("<b>OBSERVACIONES</b>", th_style)],
                    [
                        Table([
                            [Paragraph("<b>NOMBRE:</b>", cell_bold), Paragraph("RIGOBERTO HERNANDEZ", cell_center)],
                            [Paragraph("<b>EMPRESA:</b>", cell_bold), Paragraph("JYPESA", cell_center)],
                            [Paragraph("<b>E-MAIL:</b>", cell_bold), Paragraph("rhernandez@jypesa.com", cell_center)],
                            [Paragraph("<b>TELEFONO:</b>", cell_bold), Paragraph("Cel. 33 19 75 31 22", cell_center)]
                        ], colWidths=[70, 230], style=[
                            ("BACKGROUND", (1,0), (1,-1), colors.HexColor("#fff59d")),
                            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                            ("TOPPADDING", (0,0), (-1,-1), 1.5),
                            ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                        ]),
                        Paragraph("<b>LLAMAR AL REMITENTE UNA HORA ANTES DE LA RECOLECCIÓN,</b> SI NO QUIEREN ENTREGAR LLAMAR AL TELÉFONO<br/>Cel. 33 19 75 31 22 Rigoberto Hernandez", cell_normal)
                    ]
                ], colWidths=[300, 302])
                t_final_block.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (0,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (1,0), (1,0), colors.HexColor("#b71c1c")),
                    ("BACKGROUND", (1,1), (1,1), colors.HexColor("#fff59d")),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("TOPPADDING", (0,0), (-1,-1), 2),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ]))
                story.append(t_final_block)

                doc.build(story)
                buffer.seek(0)
                return buffer

            st.markdown("---")
            col_gen1, col_gen2 = st.columns(2)
            with col_gen1:
                if st.button("Generar Orden de Recolección (Tresguerras Oficial)", use_container_width=True, key="btn_gen_pdf_tg"):
                    pdf_buf = generar_pdf_tresguerras_oficial()
                    st.success("¡Formato de Tresguerras generado correctamente!")
                    st.download_button(
                        label="📥 Descargar PDF Tresguerras Oficial",
                        data=pdf_buf,
                        file_name=f"Tresguerras_Oficial_{num_factura}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_pdf_tg_btn"
                    )
            with col_gen2:
                if st.button("Registrar Folio en Estatus GitHub", use_container_width=True, key="btn_guardar_gh_tab1"):
                    df_estatus_actual = cargar_estatus_github()
                    nuevo_registro = pd.DataFrame([{
                        "Folio": str(num_factura),
                        "Fecha_Recoleccion": fecha_rec_str,
                        "Cliente": str(dest_cliente),
                        "Proveedor": str(rem_cliente),
                        "Peso_Total": float(total_peso_calc),
                        "Estatus": "PENDIENTE DE RECOLECCION",
                        "Observaciones": "Creado desde solicitud Tresguerras",
                        "Solicitante": "RIGOBERTO HERNANDEZ",
                        "Numero de Guia": "",
                        "Costo de la Guia": 0.0
                    }])
                    if not df_estatus_actual.empty and str(num_factura) in df_estatus_actual["Folio"].values:
                        df_estatus_actual.loc[df_estatus_actual["Folio"] == str(num_factura), ["Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total"]] = [fecha_rec_str, str(dest_cliente), str(rem_cliente), float(total_peso_calc)]
                        df_final = df_estatus_actual
                    else:
                        df_final = pd.concat([df_estatus_actual, nuevo_registro], ignore_index=True)
                    
                    if guardar_estatus_github(df_final, f"Registro de folio {num_factura}"):
                        st.success(f"¡Folio {num_factura} guardado/actualizado exitosamente en GitHub!")
        else:
            st.warning("No se encontraron datos en la matriz de facturación.")

    # --- TAB 2: RENDER DE ESTATUS ---
    with tab2:
        
        df_estatus = cargar_estatus_github()

        if not df_estatus.empty:
            df_estatus.columns = [str(c).upper().strip() for c in df_estatus.columns]

            # 1. FILTROS DE CABECERA PARA EL TABLERO
            with st.container():
                f_col1, f_col2 = st.columns([2, 2], vertical_alignment="bottom")
                
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

            # 2. PROCESAMIENTO Y APLICACIÓN DE FILTROS
            df_render = df_estatus.copy()
            
            if filtro_estatus_tab2 != "TODOS":
                df_render = df_render[df_render["ESTATUS"] == filtro_estatus_tab2]
                
            if filtro_prov_tab2 != "TODOS" and col_prov_key:
                df_render = df_render[df_render[col_prov_key] == filtro_prov_tab2]

            # 3. TARJETAS DE MÉTRICAS SUPERIORES (KPIs)
            total_envios = len(df_estatus)
            filtrados_n = len(df_render)
            
            pendientes_n = len(df_estatus[df_estatus["ESTATUS"].str.upper().str.contains("PENDIENTE|PROCESO", na=False)]) if "ESTATUS" in df_estatus.columns else 0
            entregados_n = len(df_estatus[df_estatus["ESTATUS"].str.upper().str.contains("ENTREGADO", na=False)]) if "ESTATUS" in df_estatus.columns else 0
            
            if "PESO_TOTAL" in df_estatus.columns:
                peso_total_val = pd.to_numeric(df_estatus["PESO_TOTAL"], errors="coerce").sum()
            else:
                peso_total_val = 0.0
                
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)

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
                    <div class='base-card-alerta' style='border-left-color: #F97316;'>
                        <div style='color: rgba(255,255,255,0.5); font-size: 9px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>PESO ACUMULADO</div>
                        <div style='color: white; font-size: 22px; font-weight: 800; line-height: 1.2; margin-top: 4px;'>{peso_total_val:,.1f} <span style='font-size: 10px; color: #F97316; font-weight: 700; text-transform: uppercase;'>KG</span></div>
                    </div>
                """, unsafe_allow_html=True)

            # 4. PANEL DE VISUALIZACIÓN ESTILO WAR ROOM PARA EL RENDER
            st.markdown(f"<p style='font-size:11px; font-weight:700; letter-spacing:8px; color:#FFFFFF; text-transform:uppercase; text-align:center; margin-bottom:20px;'>DETALLE OPERATIVO DE GITHUB</p>", unsafe_allow_html=True)

            if not df_render.empty:
                data_render = df_render.to_dict('records')
                
                html_render_cards = f"""
                <div style="font-family: 'Inter', sans-serif; padding-right: 10px;">
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

                        .card-excepcion {{
                            background: #263238;
                            border: 1px solid rgba(56, 189, 248, 0.15);
                            border-left: 6px solid #38bdf8;
                            border-radius: 12px;
                            margin-bottom: 12px;
                            padding: 18px 25px;
                            display: flex;
                            flex-wrap: wrap;
                            gap: 15px;
                            justify-content: space-between;
                            align-items: center;
                            transition: all 0.3s ease;
                            width: 100%;
                            box-sizing: border-box;
                        }}
                        .card-excepcion:hover {{ 
                            border-color: #38bdf8; 
                            background: #2d3b42;
                            transform: translateX(5px);
                        }}
                        .badge-estatus {{
                            background: rgba(56, 189, 248, 0.1);
                            color: #38bdf8;
                            padding: 8px 14px;
                            border-radius: 8px;
                            font-weight: 800;
                            font-family: monospace;
                            font-size: 13px;
                            text-align: center;
                            border: 1px solid rgba(56, 189, 248, 0.3);
                        }}
                        .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }}
                        .factura-destacada {{ color: #FFFFFF; font-size: 18px; font-weight: 800; letter-spacing: 1px; font-family: monospace; }}
                        .info-main {{ color: #FFFFFF; font-size: 13px; font-weight: 700; }}
                        .info-sub {{ color: #94a3b8; font-size: 11px; }}
                    </style>
                    {"".join([f'''
                    <div class="card-excepcion">
                        <div style="flex: 1.5; min-width: 180px;">
                            <div class="label-mini">Folio / Factura</div>
                            <div class="factura-destacada">{item.get('FOLIO', 'N/A')}</div>
                            <div class="info-sub" style="margin-top:4px;">Fecha: {item.get('FECHA_RECOLECCION', 'N/A')}</div>
                        </div>

                        <div style="flex: 2; min-width: 220px; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                            <div class="label-mini">Cliente / Destino</div>
                            <div class="info-main">{str(item.get('CLIENTE', 'N/A'))[:40]}</div>
                            <div class="info-sub" style="color: #FFFFFF !important;">Proveedor: {str(item.get('PROVEEDOR', 'N/A'))[:35]}</div>
                        </div>

                        <div style="flex: 1; min-width: 120px; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                            <div class="label-mini">Peso Total</div>
                            <div class="info-main" style="color: #00FFAA;">{float(item.get('PESO_TOTAL', 0.0)):,.2f} KG</div>
                            <div class="info-sub">Observación registrada</div>
                        </div>

                        <div style="flex: 1.2; min-width: 160px; text-align: right;">
                            <div class="label-mini" style="text-align:center;">Estatus Actual</div>
                            <div class="badge-estatus">{item.get('ESTATUS', 'PENDIENTE')}</div>
                        </div>
                    </div>
                    ''' for item in data_render])}
                </div>
                """
                
                components.html(html_render_cards, height=600, scrolling=True)
            else:
                st.markdown(f"""
                    <div style="background: rgba(56, 189, 248, 0.05); border: 1px dashed #38bdf8; border-radius: 10px; padding: 25px; text-align: center; margin-top: 20px;">
                        <p style="color: #38bdf8; font-size: 16px; margin: 0;"><b>SIN REGISTROS BAJO ESTE FILTRO</b></p>
                        <p style="color: #94a3b8; font-size: 12px; margin-top: 5px;">No se encontraron elementos que coincidan con los criterios seleccionados en el render.</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aún no hay registros de estatus guardados en GitHub para renderizar en este apartado.")

    # --- TAB 3: EDICIÓN Y ACTUALIZACIÓN ---
    with tab3:
        st.markdown("")
        df_estatus_edit = cargar_estatus_github()

        if not df_estatus_edit.empty:
            folios_list = df_estatus_edit["Folio"].astype(str).unique().tolist()
            folio_a_editar = st.selectbox("Selecciona el Folio a Modificar / Actualizar", folios_list, key="edit_folio_sel")

            if folio_a_editar:
                fila_actual = df_estatus_edit[df_estatus_edit["Folio"].astype(str) == str(folio_a_editar)].iloc[0]
                
                with st.form("form_edicion_estatus"):
                    st.markdown(f"**Editando Folio:** `{folio_a_editar}`")
                    
                    nuevo_estatus = st.selectbox(
                        "Estatus de la Recolección", 
                        ["PENDIENTE DE RECOLECCION", "EN RUTA", "ENTREGADO", "CANCELADO", "INCIDENCIA"],
                        index=["PENDIENTE DE RECOLECCION", "EN RUTA", "ENTREGADO", "CANCELADO", "INCIDENCIA"].index(fila_actual.get("Estatus", "PENDIENTE DE RECOLECCION")) if fila_actual.get("Estatus", "PENDIENTE DE RECOLECCION") in ["PENDIENTE DE RECOLECCION", "EN RUTA", "ENTREGADO", "CANCELADO", "INCIDENCIA"] else 0
                    )
                    
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        nuevo_solicitante = st.text_input("Solicitante", value=str(fila_actual.get("Solicitante", "")))
                        nuevo_num_guia = st.text_input("Número de Guía", value=str(fila_actual.get("Numero de Guia", "")))
                    with col_e2:
                        nuevo_costo_guia = st.number_input("Costo de la Guía", value=float(fila_actual.get("Costo de la Guia", 0.0)))
                        nuevo_peso = st.number_input("Peso Total (KG)", value=float(fila_actual.get("Peso_Total", 0.0)))

                    nuevo_cliente = st.text_input("Cliente Destino", value=str(fila_actual.get("Cliente", "")))
                    nuevo_proveedor = st.text_input("Proveedor Remitente", value=str(fila_actual.get("Proveedor", "")))
                    nueva_obs = st.text_area("Observaciones / Notas de Entrega", value=str(fila_actual.get("Observaciones", "")))

                    btn_guardar_cambios = st.form_submit_button("💾 GUARDAR CAMBIOS")

                    if btn_guardar_cambios:
                        idx_match = df_estatus_edit[df_estatus_edit["Folio"].astype(str) == str(folio_a_editar)].index
                        df_estatus_edit.loc[idx_match, "Estatus"] = nuevo_estatus
                        df_estatus_edit.loc[idx_match, "Observaciones"] = nueva_obs
                        df_estatus_edit.loc[idx_match, "Cliente"] = nuevo_cliente
                        df_estatus_edit.loc[idx_match, "Proveedor"] = nuevo_proveedor
                        df_estatus_edit.loc[idx_match, "Peso_Total"] = float(nuevo_peso)
                        df_estatus_edit.loc[idx_match, "Solicitante"] = nuevo_solicitante
                        df_estatus_edit.loc[idx_match, "Numero de Guia"] = str(nuevo_num_guia).strip()
                        df_estatus_edit.loc[idx_match, "Costo de la Guia"] = float(nuevo_costo_guia)
                    
                        if guardar_estatus_github(df_estatus_edit, f"Actualización de estatus y datos para folio {folio_a_editar}"):
                            st.success(f"¡Cambios guardados correctamente en GitHub para el folio {folio_a_editar}!")
                            st.rerun()
        else:
            st.warning("No hay registros disponibles para editar en GitHub.")

if __name__ == "__main__":
    main()

