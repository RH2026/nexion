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

    # --- DEFINICIÓN DE TABS (SOLO RENDER DE ESTATUS Y EDICIÓN) ---
    tab1, tab2 = st.tabs(["Render de Estatus", "Edición y Actualización"])

    # --- TAB 1: RENDER DE ESTATUS ---
    with tab1:
        
        df_estatus = cargar_estatus_github()

        if not df_estatus.empty:
            df_estatus.columns = [str(c).upper().strip() for c in df_estatus.columns]

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

            df_render = df_estatus.copy()
            
            if filtro_estatus_tab2 != "TODOS":
                df_render = df_render[df_render["ESTATUS"] == filtro_estatus_tab2]
                
            if filtro_prov_tab2 != "TODOS" and col_prov_key:
                df_render = df_render[df_render[col_prov_key] == filtro_prov_tab2]

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

    # --- TAB 2: EDICIÓN Y ACTUALIZACIÓN ---
    with tab2:
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
