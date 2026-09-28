import base64
from datetime import datetime, timedelta
import io
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
from auth import exigir_autenticacion
import math
import plotly.express as px

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Logistics - Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── TEMA Y CSS MAESTROS ──────────────────────────────────────────
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
    "logo": "n1.png",
}

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO Y PERMISOS
# ============================================================
render_layout(modulo_actual="DASHBOARD")

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


@st.cache_data(ttl=60)
def cargar_datos_dashboard_global():
    t = int(time.time())
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
    try:
        df = pd.read_csv(url, encoding="utf-8-sig")
        df.columns = df.columns.str.strip().str.upper()
        return df
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def cargar_datos_envios():
    token = st.secrets.get("GITHUB_TOKEN", None)
    headers = {"Authorization": f"token {token}"} if token else {}
    t = int(time.time() * 1000)
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/envios.csv?_t={t}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = df.columns.str.strip()
            return df
        return pd.DataFrame()
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

# ==========================================
# 5. INTERFAZ PRINCIPAL CON SISTEMA DE TABS
# ==========================================
def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True
    
    def cargar_datos():
        t = int(time.time())
        url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
        try:
            df = pd.read_csv(url, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            return None         

    # --------------------------------------------------------
    # TARJETA PLANA ESTILO "KPI SURTIDO" (borde + número grande)
    # --------------------------------------------------------
    def render_flat_card(titulo, valor, color, border_alpha=None):
        border_style = f"rgba({border_alpha}, 0.3)" if border_alpha else vars_css['border']
        st.markdown(f"""
            <div style="background: #182229; border: 1px solid {border_style}; padding: 14px; border-radius: 8px; text-align: center;">
                <div style="color: {color if border_alpha else '#8B9BB4'}; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">{titulo}</div>
                <div style="color: {color}; font-size: 22px; font-weight: 800; margin-top: 4px;">{valor}</div>
            </div>
        """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # SUBTÍTULO ESTÁNDAR PARA CADA PESTAÑA
    # --------------------------------------------------------
    def render_subtitulo(texto):
        st.markdown(
            f"""
            <div style="text-align:left; margin-top:15px; margin-bottom:15px;">
                <span style="color:#FFFFFF; font-weight:600; font-size:14px; letter-spacing:3px;">
                    {texto}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {vars_css['bg']} !important; }}
        .spacer-menu {{ margin-top: 30px; }}
        .donut-section-title {{ font-size: 11px; font-weight: 800; color: #8B9BB4; letter-spacing: 1px; margin-bottom: 5px; }}
        .donut-section-title-s {{ font-size: 13px; font-weight: 500; color: #E8EEF2; letter-spacing: 1px; margin-bottom: 6px; }}
    </style>
    """, unsafe_allow_html=True)

    df_raw = cargar_datos()
    
    if df_raw is not None:
        import pytz
        from datetime import datetime
        tz_gdl = pytz.timezone('America/Mexico_City')
        hoy_gdl = datetime.now(tz_gdl).date()
        hoy_dt = pd.Timestamp(hoy_gdl)
        meses = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO","JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]
                
        # ==========================================================
        # DEFINICIÓN DE LAS 6 PESTAÑAS (TABS) BIEN SEPARADAS
        # ==========================================================
        tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "KPI'S SURTIDO",
            "KPI'S DE ENVÍOS",
            "DISTRIBUCION DE CARGA",
            "EFECTIVIDAD DE ENVIOS",
            "RANKING DE FLETERAS",
            "COTIZADOR"
        ])

        # ----------------------------------------------------------
        # TAB 0: KPI'S SURTIDO (guías, cruce con T1.xlsx y matriz global)
        # ----------------------------------------------------------
        with tab0:
            tz_gdl_surtido = pytz.timezone("America/Mexico_City")
            ahora_surtido = datetime.now(tz_gdl_surtido)
            hoy_gdl_surtido = ahora_surtido.date()
            # Día base por defecto: AYER. Lo de hoy apenas se está surtiendo/programando,
            # así que para ver el cierre real (qué sí tiene guía y qué no) usamos ayer.
            ayer_gdl_surtido = hoy_gdl_surtido - timedelta(days=1)

            col_titulo_s, col_indicador_s = st.columns([4, 1.8], vertical_alignment="center")

            with col_titulo_s:
                render_subtitulo("DASHBOARD EJECUTIVO // KPI DE SURTIDO Y ENVÍOS")

            with col_indicador_s:
                fecha_str_s = ahora_surtido.strftime("%d/%m/%Y")
                hora_str_s = ahora_surtido.strftime("%H:%M:%S")
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-top: 15px; margin-bottom: 10px; padding: 6px 12px; background: #182229; border: 1px solid #34495E; border-radius: 6px;">
                        <div style="width: 6px; height: 6px; background: #00FFAA; border-radius: 50%; box-shadow: 0 0 8px #00FFAA;"></div>
                        <span style="color: #8B9BB4; font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">Sync GDL:</span>
                        <span style="color: #E8EEF2; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">{fecha_str_s} &bull; <span style="color:#00FFAA;">{hora_str_s}</span></span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with st.spinner("🔄 Conectando con bases remotas y cruzando guías y métricas de surtido..."):
                df_raw_surtido = cargar_datos_envios()
                df_dashboard_global = cargar_datos_dashboard_global()

                df_t1_global = pd.DataFrame()
                try:
                    df_t1_global = pd.read_excel("T1.xlsx")
                    df_t1_global.columns = df_t1_global.columns.str.strip().str.upper()
                except Exception:
                    pass

            if df_raw_surtido.empty:
                st.warning("No se encontraron registros en la base de datos de envíos.")
            else:
                with st.spinner("🔗 Ejecutando cruce inteligente de guías, facturas y programación contra las bases remotas..."):
                    df_raw_surtido.columns = df_raw_surtido.columns.str.strip()

                    # Normalización de estructura base
                    df_envios = pd.DataFrame()
                    df_envios['factura'] = df_raw_surtido.get('Factura', pd.Series(dtype=str)).fillna('').astype(str)
                    df_envios['recomendacion'] = df_raw_surtido.get('RECOMENDACION', pd.Series(dtype=str)).fillna('SIN ASIGNAR').astype(str)
                    extran_s = df_raw_surtido.get('Nombre_Extran', pd.Series(dtype=str)).fillna('').astype(str)
                    cliente_s = df_raw_surtido.get('Nombre_Cliente', pd.Series(dtype=str)).fillna('').astype(str)
                    df_envios['nombre_cliente'] = extran_s.where(extran_s.str.strip() != '', cliente_s)
                    df_envios['destino'] = df_raw_surtido.get('DESTINO', pd.Series(dtype=str)).fillna('NACIONAL').astype(str)

                    f_prog_input = df_raw_surtido.get('FECHA DE PROGRAMACION', pd.Series(dtype=str)).fillna('').astype(str).str.strip()
                    dt_prog_temp = pd.to_datetime(f_prog_input, errors='coerce', dayfirst=True)
                    df_envios['fecha_programacion'] = dt_prog_temp.dt.strftime('%d/%m/%Y').fillna(f_prog_input)
                    df_envios['dt_prog_parsed'] = dt_prog_temp

                    # --------------------------------------------------
                    # EXTRACCIÓN ROBUSTA DE GUÍAS Y FECHAS (CRUCE MULTI-FUENTE)
                    # --------------------------------------------------
                    lista_guias = []
                    lista_fechas_envio = []
                    f_env_raw_list = df_raw_surtido.get('FECHA DE ENVIO', pd.Series(dtype=str)).fillna('').astype(str).str.strip()

                    for idx, row in df_raw_surtido.iterrows():
                        fac = str(row.get('Factura', '')).strip()
                        guia_encontrada = ""
                        fecha_envio_encontrada = ""

                        for col_g in ['NÚMERO DE GUÍA', 'NUMERO DE GUIA', 'GUIA', 'TALON', 'Nro Guia']:
                            if col_g in df_raw_surtido.columns and pd.notna(row.get(col_g)):
                                val_g = str(row.get(col_g)).strip()
                                if val_g and val_g.lower() not in ['', 'nan', '0', '0.0', 'none']:
                                    guia_encontrada = val_g
                                    break

                        if not guia_encontrada and not df_dashboard_global.empty:
                            for col_ped in ['NÚMERO DE PEDIDO', 'PEDIDO', 'FACTURA']:
                                if col_ped in df_dashboard_global.columns:
                                    match_dash = df_dashboard_global[df_dashboard_global[col_ped].astype(str).str.strip() == fac]
                                    if not match_dash.empty:
                                        for cg_dash in ['NÚMERO DE GUÍA', 'NUMERO DE GUIA', 'GUIA', 'TALON']:
                                            if cg_dash in match_dash.columns:
                                                vg = str(match_dash.iloc[0][cg_dash]).strip()
                                                if vg and vg.lower() not in ['', 'nan', '0', '0.0', 'none']:
                                                    guia_encontrada = vg
                                                    break
                                    if guia_encontrada:
                                        break

                        encontrado_en_t1 = False
                        if not guia_encontrada and not df_t1_global.empty:
                            for col_t1_ped in ['OBSERVACION 1', 'PEDIDO', 'FACTURA']:
                                if col_t1_ped in df_t1_global.columns:
                                    match_t1 = df_t1_global[df_t1_global[col_t1_ped].astype(str).str.strip() == fac]
                                    if not match_t1.empty:
                                        for cg_t1 in ['TALON', 'GUIA', 'NÚMERO DE GUÍA']:
                                            if cg_t1 in match_t1.columns:
                                                vg = str(match_t1.iloc[0][cg_t1]).strip()
                                                if vg and vg.lower() not in ['', 'nan', '0', '0.0', 'none']:
                                                    guia_encontrada = vg
                                                    encontrado_en_t1 = True
                                                    break
                                        if encontrado_en_t1:
                                            for col_fdoc in ['F.DOC', 'FECHA', 'FECHA DOC']:
                                                if col_fdoc in match_t1.columns:
                                                    fdoc_val = str(match_t1.iloc[0][col_fdoc]).strip()
                                                    if fdoc_val and fdoc_val.lower() not in ['', 'nan', '0', '0.0', 'none']:
                                                        dt_parsed_fdoc = pd.to_datetime(fdoc_val, errors='coerce', dayfirst=True)
                                                        fecha_envio_encontrada = dt_parsed_fdoc.strftime('%d/%m/%Y') if pd.notnull(dt_parsed_fdoc) else fdoc_val
                                                        break
                                            break

                        if not guia_encontrada:
                            guia_encontrada = "PENDIENTE"

                        if encontrado_en_t1 and fecha_envio_encontrada:
                            final_fecha_envio = fecha_envio_encontrada
                        else:
                            final_fecha_envio = str(f_env_raw_list.loc[idx]).strip() if idx in f_env_raw_list.index else ''

                        lista_guias.append(guia_encontrada)
                        lista_fechas_envio.append(final_fecha_envio)

                    df_envios['numero_guia'] = lista_guias
                    df_envios['fecha_envio_raw'] = lista_fechas_envio

                    dt_envio_temp = pd.to_datetime(df_envios['fecha_envio_raw'], errors='coerce', dayfirst=True)
                    df_envios['fecha_envio'] = dt_envio_temp.dt.strftime('%d/%m/%Y').fillna(df_envios['fecha_envio_raw'])
                    df_envios['dt_envio_parsed'] = dt_envio_temp

                    # Cálculo automático de estatus operativo
                    estatus_calculado = []
                    valores_nulos = ['', 'nan', '0', '0.0', '-', 'nat', 'none', 'pendiente']

                    for idx, row in df_envios.iterrows():
                        fe = str(row['fecha_envio']).strip()
                        guia = str(row['numero_guia']).strip()

                        tiene_g = guia and guia.lower() not in valores_nulos
                        tiene_fe = fe and fe.lower() not in valores_nulos

                        dt_p = row['dt_prog_parsed']
                        dt_e = row['dt_envio_parsed']

                        tarde = False
                        if pd.notna(dt_p):
                            limite = dt_p + timedelta(hours=24)
                            if tiene_fe and pd.notna(dt_e) and dt_e > limite:
                                tarde = True
                            elif not tiene_fe and not tiene_g and ahora_surtido.replace(tzinfo=None) > limite:
                                tarde = True

                        if tiene_g and tiene_fe:
                            estatus_calculado.append("SURTIDA / EN TIEMPO" if not tarde else "CON RETRASO")
                        elif not tiene_g and not tiene_fe:
                            estatus_calculado.append("PENDIENTE / SURTIENDO")
                        elif tiene_fe and not tiene_g:
                            estatus_calculado.append("ENVIADA")
                        else:
                            estatus_calculado.append("ENVIADA PARCIAL")

                    df_envios['estatus'] = estatus_calculado


                # --------------------------------------------------
                # FILTROS TÁCTICOS AVANZADOS
                # --------------------------------------------------
                st.markdown("<div style='font-size: 11px; font-weight: 800; color: #8B9BB4; letter-spacing: 1px; margin-bottom: 8px;'>FILTROS DE ANÁLISIS</div>", unsafe_allow_html=True)

                fs1, fs2, fs3, fs4, fs5 = st.columns(5)

                with fs1:
                    filtro_fprog = st.date_input("FECHA PROGRAMACIÓN", value=ayer_gdl_surtido, key="kpi_filtro_fprog")

                with fs2:
                    facturas_opts = ["TODAS"] + sorted(list(df_envios['factura'].loc[df_envios['factura'] != ''].unique()))
                    filtro_factura = st.selectbox("FACTURA", facturas_opts, key="kpi_filtro_factura")

                with fs3:
                    paq_opts = ["TODAS"] + sorted(list(df_envios['recomendacion'].loc[df_envios['recomendacion'] != ''].unique()))
                    filtro_paqueteria = st.selectbox("PAQUETERÍA", paq_opts, key="kpi_filtro_paq")

                with fs4:
                    estatus_opts = ["TODOS"] + sorted(list(df_envios['estatus'].unique()))
                    filtro_estatus = st.selectbox("ESTATUS DE SURTIDO", estatus_opts, key="kpi_filtro_estatus")

                with fs5:
                    rango_dias = st.selectbox("VENTANA", ["Día Anterior", "Últimos 7 días", "Histórico Completo"], index=0, key="kpi_filtro_ventana")

                df_filtrado = df_envios.copy()

                if filtro_fprog is not None:
                    df_filtrado = df_filtrado[df_filtrado['dt_prog_parsed'].dt.date == filtro_fprog]

                if filtro_factura != "TODAS":
                    df_filtrado = df_filtrado[df_filtrado['factura'] == filtro_factura]

                if filtro_paqueteria != "TODAS":
                    df_filtrado = df_filtrado[df_filtrado['recomendacion'] == filtro_paqueteria]

                if filtro_estatus != "TODOS":
                    df_filtrado = df_filtrado[df_filtrado['estatus'] == filtro_estatus]

                if rango_dias == "Día Anterior":
                    df_filtrado = df_filtrado[df_filtrado['dt_prog_parsed'].dt.date == ayer_gdl_surtido]
                elif rango_dias == "Últimos 7 días":
                    hace_7 = ayer_gdl_surtido - timedelta(days=7)
                    df_filtrado = df_filtrado[(df_filtrado['dt_prog_parsed'].dt.date >= hace_7) | (df_filtrado['dt_prog_parsed'].isna())]

                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

                # --------------------------------------------------
                # KPIs EJECUTIVOS
                # --------------------------------------------------
                total_facturas = len(df_filtrado)
                hoy_str_s = ahora_surtido.strftime('%d/%m/%Y')

                # ENVIADAS / SURTIDAS: si la factura ya tiene fecha de envío registrada,
                # entonces ya se surtió y ya se envió (es el mismo hecho, no dos cosas
                # distintas), sin importar si aún no tiene número de guía asignado.
                enviadas = len(df_filtrado[df_filtrado['fecha_envio'].astype(str).str.strip().str.lower().apply(lambda v: v not in valores_nulos)])
                surtidas_tiempo = enviadas
                con_retraso = len(df_filtrado[df_filtrado['estatus'] == "CON RETRASO"])
                pendientes = len(df_filtrado[df_filtrado['estatus'].str.contains("PENDIENTE", na=False)])

                # EFECTIVIDAD: del total de facturas, cuántas se enviaron/surtieron
                # (tienen fecha de envío). Enviadas + Surtidas es el mismo número,
                # combinado se divide entre el total para sacar el porcentaje.
                porcentaje_exito = (enviadas / total_facturas * 100) if total_facturas > 0 else 0

                kpi_cols_s = st.columns(5)
                with kpi_cols_s[0]:
                    render_flat_card("Facturas Totales", total_facturas, "#E8EEF2")
                with kpi_cols_s[1]:
                    render_flat_card("Enviadas", enviadas, "#00FFAA", border_alpha="0,255,170")
                with kpi_cols_s[2]:
                    render_flat_card("Sí Surtidas", surtidas_tiempo, "#FFD166")
                with kpi_cols_s[3]:
                    render_flat_card("Con Retraso / Pend.", con_retraso + pendientes, "#FF6B6B", border_alpha="255,75,75")
                with kpi_cols_s[4]:
                    render_flat_card("Efectividad", f"{porcentaje_exito:.1f}%", "#00FFAA")

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                # --------------------------------------------------
                # DONAS INTERACTIVAS
                # --------------------------------------------------
                if not df_filtrado.empty:
                    col_c1, col_c2, col_c3 = st.columns(3)

                    config_layout_s = {
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)",
                        "font": {"color": "#E8EEF2", "family": "Inter, sans-serif", "size": 10},
                        "margin": {"t": 20, "b": 10, "l": 10, "r": 10},
                        "legend": {"orientation": "h", "y": -0.18},
                        "height": 340
                    }

                    with col_c1:
                        st.markdown("<div class='donut-section-title-s'>DISTRIBUCIÓN POR ESTATUS DE SURTIDO</div>", unsafe_allow_html=True)
                        df_estatus_counts = df_filtrado['estatus'].value_counts().reset_index()
                        df_estatus_counts.columns = ['Estatus', 'Cantidad']

                        fig_donita_s1 = px.pie(
                            df_estatus_counts,
                            names='Estatus',
                            values='Cantidad',
                            hole=0.6,
                            color_discrete_sequence=['#00FFAA', '#FFD166', '#FF6B6B', '#3B82F6']
                        )
                        fig_donita_s1.update_traces(textposition='inside', textinfo='percent+value', texttemplate='<b>%{percent} (%{value})</b>', textfont=dict(color='#1F2937', size=11, family='Inter, sans-serif'), insidetextfont=dict(color='#1F2937', size=11))
                        fig_donita_s1.update_layout(**config_layout_s)
                        st.plotly_chart(fig_donita_s1, use_container_width=True, config={'displayModeBar': False})

                    with col_c2:
                        st.markdown("<div class='donut-section-title-s'>VOLUMEN OPERATIVO POR PAQUETERÍA</div>", unsafe_allow_html=True)
                        df_paq_counts = df_filtrado['recomendacion'].value_counts().reset_index()
                        df_paq_counts.columns = ['Paquetería', 'Cantidad']

                        fig_donita_s2 = px.pie(
                            df_paq_counts,
                            names='Paquetería',
                            values='Cantidad',
                            hole=0.6,
                            color_discrete_sequence=['#00A3A3', '#3B82F6', '#8B5CF6', '#EC4899', '#64748B']
                        )
                        fig_donita_s2.update_traces(textposition='inside', textinfo='percent+value', texttemplate='<b>%{percent} (%{value})</b>', textfont=dict(color='#FFFFFF', size=11, family='Inter, sans-serif'), insidetextfont=dict(color='#FFFFFF', size=11))
                        fig_donita_s2.update_layout(**config_layout_s)
                        st.plotly_chart(fig_donita_s2, use_container_width=True, config={'displayModeBar': False})

                    with col_c3:
                        st.markdown("<div class='donut-section-title-s'>DISTRIBUCIÓN POR DESTINO</div>", unsafe_allow_html=True)
                        df_destino_counts = df_filtrado['destino'].value_counts().reset_index()
                        df_destino_counts.columns = ['Destino', 'Cantidad']

                        fig_donita_s3 = px.pie(
                            df_destino_counts,
                            names='Destino',
                            values='Cantidad',
                            hole=0.6,
                            color_discrete_sequence=['#FFA07A', '#38bdf8', '#A855F7', '#FFD700', '#00FFAA', '#FF6B6B']
                        )
                        fig_donita_s3.update_traces(textposition='inside', textinfo='percent+value', texttemplate='<b>%{percent} (%{value})</b>', textfont=dict(color='#FFFFFF', size=11, family='Inter, sans-serif'), insidetextfont=dict(color='#FFFFFF', size=11))
                        fig_donita_s3.update_layout(**config_layout_s)
                        st.plotly_chart(fig_donita_s3, use_container_width=True, config={'displayModeBar': False})

                # --------------------------------------------------
                # TABLA DE PEDIDOS CON ENCABEZADO STICKY
                # --------------------------------------------------
                st.markdown("<div style='font-size: 11px; font-weight: 800; color: #8B9BB4; letter-spacing: 1px; margin-top: 15px; margin-bottom: 8px;'>DETALLE DE PEDIDOS Y SURTIDO</div>", unsafe_allow_html=True)

                sorted_table_data = df_filtrado.sort_values(by='factura', ascending=False).to_dict('records')

                if not sorted_table_data:
                    st.info("No hay registros para mostrar con los filtros seleccionados.")
                else:
                    html_table = '<div class="envios-premium-wrap"><div class="envios-premium-scroll"><table class="envios-premium-table"><thead><tr>'
                    columnas_s = ["FACTURA", "PAQUETERÍA", "NO. GUÍA", "F. PROGRAMACIÓN", "CLIENTE", "DESTINO", "FECHA ENVÍO", "ESTATUS"]

                    for col in columnas_s:
                        html_table += f"<th>{col}</th>"
                    html_table += "</tr></thead><tbody>"

                    for item in sorted_table_data:
                        est = str(item.get("estatus", "")).strip().upper()
                        if "TIEMPO" in est or est == "ENVIADA":
                            s_class = "envios-premium-income"
                        elif "RETRASO" in est:
                            s_class = "envios-premium-expense"
                        else:
                            s_class = "envios-premium-fixed"

                        html_table += "<tr>"
                        html_table += f"<td>{item.get('factura', '')}</td>"
                        html_table += f"<td>{item.get('recomendacion', '')}</td>"
                        html_table += f"<td style='color:#FFD166; font-family:monospace; font-weight:800;'>{item.get('numero_guia', '')}</td>"
                        html_table += f"<td>{item.get('fecha_programacion', '')}</td>"
                        html_table += f"<td style='max-width:250px; overflow:hidden; text-overflow:ellipsis;'>{item.get('nombre_cliente', '')}</td>"
                        html_table += f"<td>{item.get('destino', '')}</td>"
                        html_table += f"<td>{item.get('fecha_envio', '')}</td>"
                        html_table += f"<td><span class='envios-premium-badge {s_class}'><span class='envios-premium-dot'></span>{est}</span></td>"
                        html_table += "</tr>"

                    html_table += "</tbody></table></div></div>"

                    st.markdown(
                        f"""
                        <style>
                        .envios-premium-wrap{{ width:100%; background:#202B33; border:1px solid #34495E; border-radius:8px; overflow:hidden; box-shadow:0 8px 24px rgba(0,0,0,.18); margin-top:5px; }}
                        .envios-premium-scroll{{ width:100%; max-height:480px; overflow:auto; scrollbar-width:thin; scrollbar-color:#40525D #182229; }}
                        .envios-premium-table{{ width:100%; min-width:1100px; border-collapse:separate; border-spacing:0; font-family:Inter,Arial,sans-serif; font-size:11px; color:#E8EEF2; }}
                        .envios-premium-table th{{ background:#182229!important; color:#8B9BB4!important; text-align:left; font-size:9px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; padding:12px 13px; border-bottom:1px solid #34495E; position:sticky; top:0; z-index:51; white-space:nowrap; }}
                        .envios-premium-table td{{ padding:11px 13px; border-bottom:1px solid rgba(52,73,94,.55); white-space:nowrap; vertical-align:middle; }}
                        .envios-premium-table tbody tr{{ background:#202B33!important; }}
                        .envios-premium-table tbody tr:nth-child(even){{ background:#1E2930!important; }}
                        .envios-premium-table tbody tr:hover{{ background:#263740!important; box-shadow:inset 3px 0 0 #00FFAA; }}
                        .envios-premium-badge{{ display:inline-flex; align-items:center; gap:6px; padding:4px 8px; border-radius:4px; font-size:9px; font-weight:800; letter-spacing:.6px; border:1px solid #465762; }}
                        .envios-premium-income{{ color:#00FFAA!important; background:rgba(0,255,170,.08)!important; border-color:rgba(0,255,170,.28)!important; }}
                        .envios-premium-expense{{ color:#FF6B6B!important; background:rgba(255,75,75,.08)!important; border-color:rgba(255,75,75,.28)!important; }}
                        .envios-premium-fixed{{ color:#FFD166!important; background:rgba(255,209,102,.08)!important; border-color:rgba(255,209,102,.25)!important; }}
                        .envios-premium-dot{{ width:5px; height:5px; border-radius:50%; display:inline-block; background:currentColor; box-shadow:0 0 6px currentColor; }}
                        </style>
                        {html_table}
                        """,
                        unsafe_allow_html=True
                    )

        # ----------------------------------------------------------
        # TAB 1: KPI'S DE ENVÍOS (Tarjetas planas + Donas grandes con leyenda)
        # ----------------------------------------------------------
        with tab1:
            render_subtitulo("KPI'S DE ENVÍOS // PEDIDOS, ENTREGAS Y EFECTIVIDAD DEL MES")
            st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)
            sub_env1, sub_env2, sub_env3 = st.tabs([
                "RESUMEN DEL MES",
                "INTELIGENCIA DE NEGOCIO",
                "TOP CLIENTES Y DISTRIBUCIÓN",
            ])

            with sub_env1:
                # --- FILTRO DE PERÍODO INTEGRADO DENTRO DE LA TAB 1 ---
                mes_sel = st.selectbox("PERÍODO", meses, index=hoy_gdl.month - 1, key="select_mes_tab1")
            
                with st.spinner("🔄 Cargando y sincronizando información de envíos del período..."):
                    df_raw_tab1 = cargar_datos()

                    if df_raw_tab1 is not None:
                        df_raw_tab1["FECHA DE ENVÍO DT"] = pd.to_datetime(df_raw_tab1["FECHA DE ENVÍO"], dayfirst=True, errors='coerce')
                        num_mes_sel = meses.index(mes_sel) + 1

                        df_filtrado_mes = df_raw_tab1[df_raw_tab1["FECHA DE ENVÍO DT"].dt.month == num_mes_sel].copy()
                        df_filtrado_mes = df_filtrado_mes.sort_values(by="FECHA DE ENVÍO DT", ascending=False)

                    df = df_raw_tab1.copy()
                    for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
                        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

                    df_mes = df[df["FECHA DE ENVÍO"].dt.month == (meses.index(mes_sel) + 1)].copy()

                if df_raw_tab1 is not None:
                    st.markdown(f"""<div style="text-align:left; margin-top:5px; margin-bottom:5px;">
                        <span style="color:#FFC000; font-weight:400; font-size:12px; letter-spacing:3px;">
                            MOSTRANDO {len(df_filtrado_mes)} REGISTROS CORRESPONDIENTES A {mes_sel}
                        </span>
                    </div>""", unsafe_allow_html=True)

                total_p = len(df_mes)
                entregados = len(df_mes[df_mes["FECHA DE ENTREGA REAL"].notna()])
                df_trans = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna()]
                en_tiempo = len(df_trans[df_trans["PROMESA DE ENTREGA"] >= hoy_dt])
                retrasados = len(df_trans[df_trans["PROMESA DE ENTREGA"] < hoy_dt])
                total_t = len(df_trans)  

                # --- TARJETAS PLANAS (mismo estilo que KPI Surtido) ---
                kpi_cols = st.columns(5)
                with kpi_cols[0]:
                    render_flat_card("Pedidos", total_p, "#E8EEF2")
                with kpi_cols[1]:
                    render_flat_card("Entregados", entregados, "#00FFAA", border_alpha="0,255,170")
                with kpi_cols[2]:
                    render_flat_card("En Tránsito", total_t, "#3B82F6")
                with kpi_cols[3]:
                    render_flat_card("En Tiempo", en_tiempo, "#FFD166")
                with kpi_cols[4]:
                    render_flat_card("Con Retraso", retrasados, "#FF6B6B", border_alpha="255,75,75")

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
                st.markdown(f"""
                    <hr style="border: 0; height: 1px; background: {vars_css['border']}; margin: 30px 0; opacity: 0.3;">
                """, unsafe_allow_html=True)

                # --------------------------------------------------------
                # DONAS GRANDES CON LEYENDA (mismo lenguaje visual que KPI Surtido)
                # --------------------------------------------------------
                config_layout = {
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "#E8EEF2", "family": "Inter, sans-serif", "size": 11},
                    "margin": {"t": 20, "b": 10, "l": 10, "r": 10},
                    "legend": {"orientation": "h", "y": -0.18},
                    "height": 380,
                }

                col_d1, col_d2, col_d3 = st.columns(3)

                with col_d1:
                    st.markdown("<div class='donut-section-title-s'>DISTRIBUCIÓN DE PEDIDOS DEL MES</div>", unsafe_allow_html=True)
                    df_status_counts = pd.DataFrame({
                        "Estatus": ["ENTREGADOS", "EN TRÁNSITO EN TIEMPO", "EN TRÁNSITO CON RETRASO"],
                        "Cantidad": [entregados, en_tiempo, retrasados],
                    })
                    df_status_counts = df_status_counts[df_status_counts["Cantidad"] > 0]

                    if not df_status_counts.empty:
                        fig_donita1 = px.pie(
                            df_status_counts,
                            names="Estatus",
                            values="Cantidad",
                            hole=0.6,
                            color="Estatus",
                            color_discrete_map={
                                "ENTREGADOS": "#00FFAA",
                                "EN TRÁNSITO EN TIEMPO": "#FFD166",
                                "EN TRÁNSITO CON RETRASO": "#FF6B6B",
                            },
                        )
                        fig_donita1.update_traces(textposition='inside', textinfo='percent+value', texttemplate='<b>%{percent} (%{value})</b>', textfont=dict(color='#FFFFFF', size=11, family='Inter, sans-serif'), insidetextfont=dict(color='#FFFFFF', size=11))
                        fig_donita1.update_layout(**config_layout)
                        st.plotly_chart(fig_donita1, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin pedidos en este período</div>", unsafe_allow_html=True)

                with col_d2:
                    st.markdown("<div class='donut-section-title-s'>PORCENTAJE DE PEDIDOS CON RETRASO POR FLETERA</div>", unsafe_allow_html=True)
                    df_retraso = df_trans[df_trans["PROMESA DE ENTREGA"] < hoy_dt]
                    df_retraso_fletera = df_retraso.groupby("FLETERA").size().reset_index(name="Cantidad")
                    df_retraso_fletera.columns = ["Fletera", "Cantidad"]

                    if not df_retraso_fletera.empty:
                        fig_donita2 = px.pie(
                            df_retraso_fletera,
                            names="Fletera",
                            values="Cantidad",
                            hole=0.6,
                            color_discrete_sequence=['#FF6B6B', '#F97316', '#EC4899', '#8B5CF6', '#64748B'],
                        )
                        fig_donita2.update_traces(textposition='inside', textinfo='percent+value', texttemplate='<b>%{percent} (%{value})</b>', textfont=dict(color='#FFFFFF', size=11, family='Inter, sans-serif'), insidetextfont=dict(color='#FFFFFF', size=11))
                        fig_donita2.update_layout(**config_layout)
                        st.plotly_chart(fig_donita2, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#00FFAA; font-size:12px; font-weight:bold;'>✓ Sin pedidos con retraso en este período</div>", unsafe_allow_html=True)

                with col_d3:
                    st.markdown("<div class='donut-section-title-s'>DISTRIBUCIÓN DE PEDIDOS POR DESTINO</div>", unsafe_allow_html=True)
                    df_destino_mes = df_mes[df_mes["DESTINO"].astype(str).str.strip() != ""]["DESTINO"].value_counts().reset_index()
                    df_destino_mes.columns = ["Destino", "Cantidad"]
                    df_destino_mes = df_destino_mes.head(8).sort_values("Cantidad", ascending=False)

                    if not df_destino_mes.empty:
                        fig_donita3 = px.bar(
                            df_destino_mes,
                            x="Destino",
                            y="Cantidad",
                            text_auto=True,
                            color_discrete_sequence=["#FFD166"],
                        )
                        fig_donita3.update_traces(textfont=dict(color="#E8EEF2", size=11), textposition="outside")
                        fig_donita3.update_layout(**config_layout, xaxis_title=None, yaxis_title=None)
                        st.plotly_chart(fig_donita3, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin pedidos en este período</div>", unsafe_allow_html=True)

            with sub_env2:
                # ==========================================================
                # INTELIGENCIA DE NEGOCIO — CONSULTA DETALLADA DEL PERÍODO
                # ==========================================================
                st.markdown(
                    """<div style="text-align:left; margin-top:15px; margin-bottom:15px;">
                        <span style="color:#FFC000; font-weight:600; font-size:12px; letter-spacing:3px;">
                            INTELIGENCIA DE NEGOCIO // CONSULTA DETALLADA DEL PERÍODO
                        </span>
                    </div>""",
                    unsafe_allow_html=True
                )

                def _limpiar_moneda_bi(serie):
                    return pd.to_numeric(
                        serie.astype(str).str.replace(r"[^\d\.\-]", "", regex=True).replace("", "0"),
                        errors="coerce"
                    ).fillna(0.0)

                df_bi = df_mes.copy()
                for col_num in ["COSTO DE LA GUÍA", "FACTURACION", "VALUACION", "COSTOS ADICIONALES", "CANTIDAD DE CAJAS"]:
                    df_bi[col_num] = _limpiar_moneda_bi(df_bi[col_num]) if col_num in df_bi.columns else 0.0
                for col_txt in ["FLETERA", "FORMA DE ENVIO", "TRANSPORTE", "DESTINO", "NOMBRE DEL CLIENTE",
                                 "INCIDENCIAS", "COMENTARIOS", "TRIGGER", "CONCEPTO", "EMISION",
                                 "NÚMERO DE PEDIDO", "NÚMERO DE GUÍA", "NO CLIENTE", "DOMICILIO", "CAJAS"]:
                    if col_txt not in df_bi.columns:
                        df_bi[col_txt] = ""
                    df_bi[col_txt] = df_bi[col_txt].fillna("")

                # --- FILTROS RÁPIDOS DE NEGOCIO ---
                bf1, bf2, bf3, bf4 = st.columns([1.3, 1.3, 1.1, 2])
                with bf1:
                    op_fletera_bi = sorted([x for x in df_bi["FLETERA"].unique().tolist() if str(x).strip() != ""])
                    filtro_fletera_bi = st.multiselect("FLETERA", op_fletera_bi, default=[], key="bi_filtro_fletera")
                with bf2:
                    op_envio_bi = sorted([x for x in df_bi["FORMA DE ENVIO"].unique().tolist() if str(x).strip() != ""])
                    filtro_envio_bi = st.multiselect("FORMA DE ENVÍO", op_envio_bi, default=[], key="bi_filtro_envio")
                with bf3:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    solo_incidencias_bi = st.checkbox("SOLO CON INCIDENCIAS", value=False, key="bi_solo_incidencias")
                with bf4:
                    busq_bi = st.text_input("BUSCAR CLIENTE / PEDIDO / GUÍA", value="", key="bi_busqueda", placeholder="Escribe para filtrar...")

                df_bi_f = df_bi.copy()
                if filtro_fletera_bi:
                    df_bi_f = df_bi_f[df_bi_f["FLETERA"].isin(filtro_fletera_bi)]
                if filtro_envio_bi:
                    df_bi_f = df_bi_f[df_bi_f["FORMA DE ENVIO"].isin(filtro_envio_bi)]
                if solo_incidencias_bi:
                    df_bi_f = df_bi_f[~df_bi_f["INCIDENCIAS"].astype(str).str.strip().str.upper().isin(["", "OK"])]
                if busq_bi:
                    _b = busq_bi.upper()
                    _mask_bi = (
                        df_bi_f["NOMBRE DEL CLIENTE"].astype(str).str.upper().str.contains(_b, na=False)
                        | df_bi_f["NÚMERO DE PEDIDO"].astype(str).str.upper().str.contains(_b, na=False)
                        | df_bi_f["NÚMERO DE GUÍA"].astype(str).str.upper().str.contains(_b, na=False)
                    )
                    df_bi_f = df_bi_f[_mask_bi]

                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

                # --- KPIs FINANCIEROS Y OPERATIVOS ---
                total_facturacion_bi = df_bi_f["FACTURACION"].sum()
                total_costo_guias_bi = df_bi_f["COSTO DE LA GUÍA"].sum()
                total_costos_adic_bi = df_bi_f["COSTOS ADICIONALES"].sum()
                total_cajas_bi = df_bi_f["CANTIDAD DE CAJAS"].sum()
                costo_logistico_bi = (total_costo_guias_bi / total_facturacion_bi * 100) if total_facturacion_bi else 0.0
                costo_promedio_caja_bi = (total_costo_guias_bi / total_cajas_bi) if total_cajas_bi else 0.0

                bi_kpi_cols = st.columns(6)
                with bi_kpi_cols[0]:
                    render_flat_card("Facturación", f"${total_facturacion_bi:,.0f}", "#00FFAA", border_alpha="0,255,170")
                with bi_kpi_cols[1]:
                    render_flat_card("Costo Guías", f"${total_costo_guias_bi:,.0f}", "#38bdf8")
                with bi_kpi_cols[2]:
                    render_flat_card("Costos Adic.", f"${total_costos_adic_bi:,.0f}", "#FFD166")
                with bi_kpi_cols[3]:
                    render_flat_card("Costo Logístico", f"{costo_logistico_bi:.1f}%", "#8B5CF6")
                with bi_kpi_cols[4]:
                    render_flat_card("Cajas Enviadas", f"{total_cajas_bi:,.0f}", "#E8EEF2")
                with bi_kpi_cols[5]:
                    render_flat_card("Costo Prom./Caja", f"${costo_promedio_caja_bi:,.2f}", "#FF6B6B", border_alpha="255,75,75")


                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                # --- GRÁFICOS DE NEGOCIO (agrupados por tema para que se entiendan de un vistazo) ---
                config_layout_bi = {
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "#E8EEF2", "family": "Inter, sans-serif", "size": 14},
                    "margin": {"t": 20, "b": 10, "l": 10, "r": 10},
                    "height": 340,
                }

                def _seccion_bi(emoji_sec, texto_sec, color_sec):
                    st.markdown(
                        f"""<div style="font-size:12px; font-weight:800; color:{color_sec}; letter-spacing:1.5px;
                        text-transform:uppercase; border-left:3px solid {color_sec}; padding-left:9px;
                        margin:22px 0 12px 0;">{emoji_sec} {texto_sec}</div>""",
                        unsafe_allow_html=True
                    )

                # === GRUPO 1: COMPARATIVO POR FLETERA (ingreso vs. costo, lado a lado) ===
                _seccion_bi("", "GRUPO 1 · COMPARATIVO POR FLETERA — INGRESO VS. COSTO", "#38bdf8")
                bg1, bg2 = st.columns(2)

                with bg1:
                    st.markdown("<div class='donut-section-title-s'>FACTURACIÓN GENERADA POR FLETERA</div>", unsafe_allow_html=True)
                    df_fact_fletera = df_bi_f.groupby("FLETERA", as_index=False)["FACTURACION"].sum()
                    df_fact_fletera = df_fact_fletera[df_fact_fletera["FLETERA"] != ""].sort_values("FACTURACION", ascending=False).head(8)
                    if not df_fact_fletera.empty:
                        fig_bi1 = px.bar(df_fact_fletera, x="FLETERA", y="FACTURACION", text_auto=".2s", color_discrete_sequence=["#7FA0B0"])
                        fig_bi1.update_traces(textfont=dict(color="#E8EEF2"))
                        fig_bi1.update_layout(**config_layout_bi, xaxis_title=None, yaxis_title=None)
                        st.plotly_chart(fig_bi1, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos para graficar</div>", unsafe_allow_html=True)

                with bg2:
                    st.markdown("<div class='donut-section-title-s'>COSTO OPERATIVO POR FLETERA (GUÍA + ADICIONALES)</div>", unsafe_allow_html=True)
                    df_bi_f["_costo_total_envio_bi"] = df_bi_f["COSTO DE LA GUÍA"] + df_bi_f["COSTOS ADICIONALES"]
                    df_costo_fletera_bi = df_bi_f.groupby("FLETERA", as_index=False)["_costo_total_envio_bi"].sum()
                    df_costo_fletera_bi = df_costo_fletera_bi[df_costo_fletera_bi["FLETERA"] != ""].sort_values("_costo_total_envio_bi", ascending=False).head(8)
                    if not df_costo_fletera_bi.empty:
                        fig_bi2 = px.bar(df_costo_fletera_bi, x="FLETERA", y="_costo_total_envio_bi", text_auto=".2s", color_discrete_sequence=["#B98B78"])
                        fig_bi2.update_traces(textfont=dict(color="#E8EEF2"))
                        fig_bi2.update_layout(**config_layout_bi, xaxis_title=None, yaxis_title="COSTO ($)")
                        st.plotly_chart(fig_bi2, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos para graficar</div>", unsafe_allow_html=True)


            with sub_env3:
                # === GRUPO 2: CLIENTES Y CANAL DE ENVÍO ===
                st.markdown(
                    """<div style="text-align:left; margin-top:15px; margin-bottom:15px;">
                        <span style="color:#FFC000; font-weight:600; font-size:12px; letter-spacing:3px;">
                            CLIENTES // CANAL DE ENVÍO
                        </span>
                    </div>""",
                    unsafe_allow_html=True
                )
                bg3, bg4 = st.columns(2)

                with bg3:
                    st.markdown("<div class='donut-section-title-s'>TOP 10 CLIENTES POR FACTURACIÓN</div>", unsafe_allow_html=True)
                    df_top_clientes_bi = df_bi_f.groupby("NOMBRE DEL CLIENTE", as_index=False)["FACTURACION"].sum()
                    df_top_clientes_bi = df_top_clientes_bi[df_top_clientes_bi["NOMBRE DEL CLIENTE"] != ""].sort_values("FACTURACION", ascending=False).head(10)
                    if not df_top_clientes_bi.empty:
                        fig_bi3 = px.bar(df_top_clientes_bi, x="FACTURACION", y="NOMBRE DEL CLIENTE", orientation="h", text_auto=".2s", color_discrete_sequence=["#00FFAA"])
                        fig_bi3.update_traces(textfont=dict(color="#1F2937"))
                        fig_bi3.update_layout(**config_layout_bi, xaxis_title=None, yaxis_title=None, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_bi3, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos para graficar</div>", unsafe_allow_html=True)

                with bg4:
                    st.markdown("<div class='donut-section-title-s'>DISTRIBUCIÓN POR FORMA DE ENVÍO</div>", unsafe_allow_html=True)
                    df_envio_counts = df_bi_f[df_bi_f["FORMA DE ENVIO"] != ""]["FORMA DE ENVIO"].value_counts().reset_index()
                    df_envio_counts.columns = ["Forma", "Cantidad"]
                    if not df_envio_counts.empty:
                        fig_bi4 = px.pie(df_envio_counts, names="Forma", values="Cantidad", hole=0.6,
                                          color_discrete_sequence=['#00FFAA', '#38bdf8', '#FFD166', '#A855F7', '#FF6B6B'])
                        fig_bi4.update_traces(textposition='inside', textinfo='percent+value', texttemplate='<b>%{percent}</b>',
                                              textfont=dict(color='#1F2937', size=11, family='Inter, sans-serif'),
                                              insidetextfont=dict(color='#1F2937', size=11))
                        fig_bi4.update_layout(**config_layout_bi, legend={"orientation": "h", "y": -0.18})
                        st.plotly_chart(fig_bi4, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos para graficar</div>", unsafe_allow_html=True)

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                # --- PREPARAR VISTA LEGIBLE PARA TABLAS DE CONSULTA (fechas como texto) ---
                df_bi_display = df_bi_f.copy()
                for col_fecha_bi in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
                    if col_fecha_bi in df_bi_display.columns:
                        df_bi_display[col_fecha_bi] = df_bi_display[col_fecha_bi].dt.strftime('%d/%m/%Y')
                        df_bi_display[col_fecha_bi] = df_bi_display[col_fecha_bi].fillna("")

                # --- TABLAS DE CONSULTA CON EL MISMO FORMATO STICKY QUE KPI SURTIDO ---
                def _escapar_bi(valor):
                    return str(valor).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                def _tabla_sticky_bi(df_tabla, columnas_tabla, max_altura=340):
                    html = f'<div class="bi-sticky-wrap"><div class="bi-sticky-scroll" style="max-height:{max_altura}px;"><table class="bi-sticky-table"><thead><tr>'
                    for col in columnas_tabla:
                        html += f"<th>{_escapar_bi(col)}</th>"
                    html += "</tr></thead><tbody>"
                    for _, fila in df_tabla.iterrows():
                        html += "<tr>"
                        for col in columnas_tabla:
                            html += f"<td>{_escapar_bi(fila.get(col, ''))}</td>"
                        html += "</tr>"
                    html += "</tbody></table></div></div>"
                    return html

                st.markdown(
                    """
                    <style>
                    .bi-sticky-wrap{ width:100%; background:#202B33; border:1px solid #34495E; border-radius:8px; overflow:hidden; box-shadow:0 8px 24px rgba(0,0,0,.18); margin-top:5px; }
                    .bi-sticky-scroll{ width:100%; overflow:auto; scrollbar-width:thin; scrollbar-color:#40525D #182229; }
                    .bi-sticky-table{ width:100%; min-width:900px; border-collapse:separate; border-spacing:0; font-family:Inter,Arial,sans-serif; font-size:11px; color:#FFFFFF; }
                    .bi-sticky-table th{ background:#182229!important; color:#8B9BB4!important; text-align:left; font-size:9px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; padding:12px 13px; border-bottom:1px solid #34495E; position:sticky; top:0; z-index:51; white-space:nowrap; }
                    .bi-sticky-table td{ padding:11px 13px; border-bottom:1px solid rgba(52,73,94,.55); white-space:nowrap; color:#FFFFFF!important; vertical-align:middle; }
                    .bi-sticky-table tbody tr{ background:#202B33!important; }
                    .bi-sticky-table tbody tr:nth-child(even){ background:#1E2930!important; }
                    .bi-sticky-table tbody tr:hover{ background:#263740!important; box-shadow:inset 3px 0 0 #38bdf8; }
                    </style>
                    """,
                    unsafe_allow_html=True
                )


                # --- TABLA DE CONSULTA GENERAL (TODAS LAS COLUMNAS) ---
                st.markdown(f"<div class='donut-section-title-s'>\U0001F50E DETALLE COMPLETO DE REGISTROS ({len(df_bi_display)})</div>", unsafe_allow_html=True)

                cols_detalle_bi = [c for c in [
                    "NO CLIENTE", "NÚMERO DE PEDIDO", "NOMBRE DEL CLIENTE", "DESTINO",
                    "FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL",
                    "FLETERA", "NÚMERO DE GUÍA", "TRANSPORTE", "FORMA DE ENVIO",
                    "CANTIDAD DE CAJAS", "CAJAS", "COSTO DE LA GUÍA", "COSTOS ADICIONALES",
                    "FACTURACION", "VALUACION", "EMISION", "MES", "TRIGGER", "CONCEPTO",
                    "COMENTARIOS"
                ] if c in df_bi_display.columns]
                st.markdown(_tabla_sticky_bi(df_bi_display, cols_detalle_bi, max_altura=460), unsafe_allow_html=True)

                csv_export_bi = df_bi_display[cols_detalle_bi].to_csv(index=False).encode("utf-8-sig")
                st.download_button("📥 DESCARGAR ESTA VISTA (CSV)", data=csv_export_bi,
                                    file_name=f"detalle_envios_{mes_sel}.csv", mime="text/csv", key="bi_download_csv")



        # ----------------------------------------------------------
        # TAB 2: PESTAÑA 2 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab2:
            render_subtitulo("DISTRIBUCIÓN DE CARGA // VOLUMEN Y OCUPACIÓN POR FLETERA")
            st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)

            import html as html_lib
            import plotly.graph_objects as go

            # --- DATOS BASE (misma fuente que el resto del dashboard) ---
            df_carga_raw = df_raw.copy()
            for col_txt_dc in ["TRANSPORTE", "DESTINO", "FORMA DE ENVIO", "MES"]:
                if col_txt_dc not in df_carga_raw.columns:
                    df_carga_raw[col_txt_dc] = ""
                df_carga_raw[col_txt_dc] = df_carga_raw[col_txt_dc].fillna("").astype(str).str.strip()
            df_carga_raw["MES"] = df_carga_raw["MES"].str.upper()
            df_carga_raw["CAJAS"] = pd.to_numeric(df_carga_raw["CAJAS"], errors="coerce").fillna(0) if "CAJAS" in df_carga_raw.columns else 0

            # --- "COBRO REGRESO" a secas (sin nombre de paquetería) = aún sin fletera: no se considera ---
            # (lo que diga "TINY PACK COBRO REGRESO", "TRES GUERRAS COBRO REGRESO", etc. SÍ se considera)
            _fletera_base_dc = df_carga_raw["FLETERA"].fillna("").astype(str).str.upper().str.strip() if "FLETERA" in df_carga_raw.columns else pd.Series("", index=df_carga_raw.index)
            _sin_asignar_dc = (df_carga_raw["TRANSPORTE"].str.upper().str.strip() == "COBRO REGRESO") | (_fletera_base_dc == "COBRO REGRESO")
            df_carga_raw = df_carga_raw[~_sin_asignar_dc]

            # --- SOLO LAS 7 PAQUETERÍAS MÁS IMPORTANTES ---
            CARRIERS_PRINCIPALES_DC = ["TRES GUERRAS", "ONE", "TINY PACK", "PAQMEX", "PAQUETE", "SANCHEZ", "FLETES DE REGRESO", "FARMASES"]
            _fletera_dc = df_carga_raw["FLETERA"].fillna("").astype(str).str.upper() if "FLETERA" in df_carga_raw.columns else pd.Series("", index=df_carga_raw.index)
            _texto_carrier_dc = df_carga_raw["TRANSPORTE"].str.upper() + " | " + _fletera_dc
            df_carga_raw = df_carga_raw[
                _texto_carrier_dc.apply(lambda nom_x: any(p in nom_x for p in CARRIERS_PRINCIPALES_DC))
            ]

            # --- FILTROS: PERÍODO + FLUJO ---
            dcf1, dcf2 = st.columns([1.3, 3])
            with dcf1:
                mes_sel_carga = st.selectbox("PERÍODO", meses, index=hoy_gdl.month - 1, key="select_mes_carga")
            with dcf2:
                tipo_mov_carga = st.radio(
                    "FLUJO", ["TODOS", "COBRO DESTINO", "COBRO REGRESO"],
                    index=2, horizontal=True, key="tipo_mov_carga"
                )

            df_carga = df_carga_raw[(df_carga_raw["MES"] == mes_sel_carga) & (df_carga_raw["TRANSPORTE"] != "")].copy()
            if tipo_mov_carga == "COBRO DESTINO":
                df_carga = df_carga[df_carga["FORMA DE ENVIO"].str.contains("DESTINO", case=False, na=False)
                                    | df_carga["TRANSPORTE"].str.contains("COBRO DESTINO", case=False, na=False)]
            elif tipo_mov_carga == "COBRO REGRESO":
                df_carga = df_carga[df_carga["FORMA DE ENVIO"].str.contains("REGRESO", case=False, na=False)
                                    | df_carga["TRANSPORTE"].str.contains("COBRO REGRESO", case=False, na=False)]

            if df_carga.empty:
                st.warning(f"No se encontraron registros para '{tipo_mov_carga}' en {mes_sel_carga}.")
            else:
                total_cajas_carga = df_carga["CAJAS"].sum()
                df_part_carga = df_carga.groupby("TRANSPORTE", as_index=False)["CAJAS"].sum()
                df_part_carga["PORCENTAJE"] = (df_part_carga["CAJAS"] / total_cajas_carga * 100) if total_cajas_carga else 0.0
                df_part_carga = df_part_carga.sort_values("CAJAS", ascending=True)

                lider_carga = df_part_carga.iloc[-1]
                st.markdown(f"""<div style="text-align:left; margin-top:5px; margin-bottom:5px;">
                    <span style="color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;">
                        MOSTRANDO {len(df_carga)} REGISTROS CORRESPONDIENTES A {mes_sel_carga}
                    </span>
                </div>""", unsafe_allow_html=True)

                # --- TARJETAS ---
                dc_cols = st.columns(3)
                with dc_cols[0]:
                    render_flat_card("Volumen Total (Cajas)", f"{int(total_cajas_carga):,}", "#E8EEF2")
                with dc_cols[1]:
                    render_flat_card("Carrier Dominante", f"{lider_carga['TRANSPORTE']} · {lider_carga['PORCENTAJE']:.0f}%", "#00FFAA", border_alpha="0,255,170")
                with dc_cols[2]:
                    render_flat_card("Destinos Distintos", df_carga["DESTINO"].replace("", pd.NA).nunique(), "#7FA0B0")

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                config_layout_dc = {
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "#E8EEF2", "family": "Inter, sans-serif", "size": 12},
                    "margin": {"t": 20, "b": 10, "l": 10, "r": 60},
                    "height": max(340, len(df_part_carga) * 38),
                }

                st.markdown("<div class='donut-section-title-s'>PARTICIPACIÓN DE CARGA POR CARRIER (CAJAS Y %)</div>", unsafe_allow_html=True)
                fig_dc1 = go.Figure(go.Bar(
                    x=df_part_carga["CAJAS"], y=df_part_carga["TRANSPORTE"], orientation="h",
                    marker=dict(color="#7FA0B0"),
                    text=[f"{int(c):,} · {p:.1f}%" for c, p in zip(df_part_carga["CAJAS"], df_part_carga["PORCENTAJE"])],
                    textposition="outside", textfont=dict(color="#E8EEF2"), cliponaxis=False,
                ))
                fig_dc1.update_layout(**config_layout_dc, xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                      yaxis=dict(showgrid=False, automargin=True), showlegend=False,
                                      hoverlabel=dict(bgcolor="#182229", font_size=12))
                st.plotly_chart(fig_dc1, use_container_width=True, config={'displayModeBar': False},
                                key=f"bar_part_{mes_sel_carga}_{tipo_mov_carga}")

                # --- EXPLORADOR DE RUTAS Y DESTINOS ---
                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                st.markdown("<div class='donut-section-title-s'>EXPLORADOR DE RUTAS Y DESTINOS</div>", unsafe_allow_html=True)

                lista_carriers_dc = ["TODOS"] + sorted(df_carga["TRANSPORTE"].unique())
                col_sel_dc, _ = st.columns([3, 1])
                with col_sel_dc:
                    carrier_sel_dc = st.selectbox("CARRIER", lista_carriers_dc, key=f"select_carrier_{mes_sel_carga}_{tipo_mov_carga}",
                                                  label_visibility="collapsed")

                df_dest_f_dc = df_carga if carrier_sel_dc == "TODOS" else df_carga[df_carga["TRANSPORTE"] == carrier_sel_dc]
                df_dest_sum_dc = (df_dest_f_dc.groupby(["TRANSPORTE", "DESTINO", "FORMA DE ENVIO"], as_index=False)["CAJAS"].sum()
                                  .sort_values(["TRANSPORTE", "CAJAS"], ascending=[True, False]))
                total_sel_dc = df_dest_sum_dc["CAJAS"].sum()

                st.markdown(f"<p style='color:#FFC000; font-size:12px; font-weight:600; letter-spacing:2px; margin:10px 0 15px 0;'>UNIDADES EN SELECCIÓN ACTUAL: {int(total_sel_dc):,}</p>", unsafe_allow_html=True)

                # Un solo encabezado por carrier, con sus rutas debajo
                bloques_dc = []
                for carrier_dc, g_dc in df_dest_sum_dc.groupby("TRANSPORTE", sort=False):
                    filas_dc = "".join(
                        f'''<div class="route-row"><div><span class="dest-name">{html_lib.escape(str(r["DESTINO"]))}</span>
                        <span class="method-tag">{html_lib.escape(str(r["FORMA DE ENVIO"]))}</span></div>
                        <div class="unit-badge">{int(r["CAJAS"]):,} u.</div></div>'''
                        for _, r in g_dc.iterrows()
                    )
                    bloques_dc.append(f'''<div class="carrier-group"><div class="carrier-header">
                        <span class="carrier-name">{html_lib.escape(str(carrier_dc))}</span>
                        <span class="carrier-total">{int(g_dc["CAJAS"].sum()):,} u.</span></div>{filas_dc}</div>''')

                html_rutas_dc = f"""
                <div style="font-family: 'Inter', sans-serif; padding-right: 10px;">
                    <style>
                        body {{ background: transparent; margin: 0; padding: 0; }}
                        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ background: #4B5D67; border-radius: 10px; }}
                        .carrier-group {{ background: #182229; border: 1px solid #4B5D67; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }}
                        .carrier-header {{ background: rgba(127,160,176,0.12); padding: 10px 15px; border-bottom: 1px solid #4B5D67; display: flex; justify-content: space-between; align-items: center; }}
                        .carrier-name {{ color: #7FA0B0; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }}
                        .carrier-total {{ color: #8B9BB4; font-size: 10px; font-weight: 800; letter-spacing: 1px; }}
                        .route-row {{ display: flex; justify-content: space-between; padding: 10px 15px; align-items: center; border-bottom: 1px solid rgba(75,93,103,0.4); }}
                        .route-row:last-child {{ border-bottom: none; }}
                        .dest-name {{ color: #E8EEF2; font-size: 12px; font-weight: 600; }}
                        .method-tag {{ background: rgba(185,139,120,0.15); color: #B98B78; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: 700; margin-left: 8px; }}
                        .unit-badge {{ background: rgba(0,255,170,0.12); color: #00FFAA; padding: 4px 10px; border-radius: 6px; font-family: monospace; font-weight: 800; font-size: 13px; border: 1px solid rgba(0,255,170,0.25); }}
                    </style>
                    {"".join(bloques_dc)}
                </div>
                """
                components.html(html_rutas_dc, height=500, scrolling=True)
                _, col_dl_dc = st.columns([3, 1])
                with col_dl_dc:
                    st.markdown("""
                        <style>
                            .st-key-dl_carga_rutas button,
                            .st-key-dl_carga_rutas [data-testid="stDownloadButton"] button,
                            .st-key-dl_carga_rutas [data-testid="stBaseButton-secondary"] {
                                background-color: #628290 !important;
                                color: #ffffff !important;
                                border: 1px solid #628290 !important;
                                border-radius: 7px !important;
                                font-weight: 700 !important;
                                text-transform: uppercase !important;
                                font-size: 10px !important;
                                height: 32px !important;
                                width: 100% !important;
                                transition: all 0.3s ease !important;
                            }
                            .st-key-dl_carga_rutas button:hover,
                            .st-key-dl_carga_rutas [data-testid="stBaseButton-secondary"]:hover {
                                background-color: #4E6772 !important;
                                border-color: #4E6772 !important;
                                color: #ffffff !important;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    st.download_button("DESCARGAR CSV", data=df_dest_sum_dc.to_csv(index=False).encode("utf-8"),
                                       file_name=f"carga_{carrier_sel_dc}_{mes_sel_carga}.csv", mime="text/csv",
                                       use_container_width=True, key="dl_carga_rutas")
             
        # ----------------------------------------------------------
        # TAB 3: PESTAÑA 3 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab3:
            render_subtitulo("EFECTIVIDAD DE ENVÍOS // DESPACHOS EN 24 HORAS HÁBILES")
            st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)

            import io as io_lib
            import html as html_lib
            import numpy as np
            import plotly.graph_objects as go

            # --- DATOS BASE ---
            df_desp_raw = df_raw.copy()
            for col_f_ds in ["EMISION", "FECHA DE ENVÍO"]:
                if col_f_ds in df_desp_raw.columns:
                    df_desp_raw[col_f_ds] = pd.to_datetime(df_desp_raw[col_f_ds], dayfirst=True, errors="coerce")
                else:
                    df_desp_raw[col_f_ds] = pd.NaT
            if "NÚMERO DE PEDIDO" not in df_desp_raw.columns:
                df_desp_raw["NÚMERO DE PEDIDO"] = ""
            df_desp_raw["NÚMERO DE PEDIDO"] = df_desp_raw["NÚMERO DE PEDIDO"].fillna("").astype(str).str.strip()

            # --- FILTROS: PERÍODO + ESTATUS + BÚSQUEDA ---
            dsf1, dsf2, dsf3 = st.columns([1.3, 1.6, 2.4])
            with dsf1:
                mes_sel_desp = st.selectbox("PERÍODO", meses, index=hoy_gdl.month - 1, key="select_mes_desp")
            with dsf2:
                buscar_desp = st.text_input("BUSCAR PEDIDO", placeholder="Escribe para filtrar...", key="buscar_pedido_desp")
            with dsf3:
                filtro_estado_desp = st.radio("ESTATUS", ["TODOS", "A TIEMPO", "FUERA DE TIEMPO"],
                                              index=0, horizontal=True, key="filtro_estado_desp")

            df_desp = df_desp_raw[df_desp_raw["FECHA DE ENVÍO"].dt.month == (meses.index(mes_sel_desp) + 1)].copy()

            # --- REGLA DE 24H HÁBILES (feriados y fines de semana no cuentan) ---
            lista_feriados_ds = ['2026-01-01', '2026-02-02', '2026-03-16', '2026-05-01']
            feriados_np_ds = np.array(lista_feriados_ds, dtype='datetime64[D]')

            def _calcular_kpi_24h_ds(row):
                ini = row['EMISION']
                fin = row['FECHA DE ENVÍO']
                if pd.isna(ini) and not pd.isna(fin):
                    ini = fin
                if pd.isna(ini) or pd.isna(fin):
                    return pd.Series(["Sin Datos", None])
                try:
                    if fin <= ini:
                        return pd.Series(["A Tiempo", 0])
                    d = int(np.busday_count(ini.date(), fin.date(), weekmask='1111100', holidays=feriados_np_ds))
                    if d == 0:
                        return pd.Series(["A Tiempo", d])
                    if d == 1 and fin.time() <= ini.time():
                        return pd.Series(["A Tiempo", d])
                    return pd.Series(["Fuera de Tiempo", d])
                except Exception:
                    return pd.Series(["Sin Datos", None])

            if not df_desp.empty:
                df_desp[["Estado_KPI", "DIAS_HABILES"]] = df_desp.apply(_calcular_kpi_24h_ds, axis=1)
            else:
                df_desp["Estado_KPI"] = pd.Series(dtype=str)
                df_desp["DIAS_HABILES"] = pd.Series(dtype=float)

            validos_ds = df_desp[df_desp["Estado_KPI"] != "Sin Datos"]
            tot_ds = len(validos_ds)
            ok_ds = int((validos_ds["Estado_KPI"] == "A Tiempo").sum())
            no_ds = tot_ds - ok_ds
            pct_ok_ds = (ok_ds / tot_ds * 100) if tot_ds else 0.0
            pct_no_ds = (no_ds / tot_ds * 100) if tot_ds else 0.0

            st.markdown(f"""<div style="text-align:left; margin-top:5px; margin-bottom:5px;">
                <span style="color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;">
                    MOSTRANDO {len(df_desp)} REGISTROS CORRESPONDIENTES A {mes_sel_desp}
                </span>
            </div>""", unsafe_allow_html=True)

            # --- TARJETAS ---
            ds_cols = st.columns(3)
            with ds_cols[0]:
                render_flat_card("Total Facturas", tot_ds, "#E8EEF2")
            with ds_cols[1]:
                render_flat_card("A Tiempo", f"{ok_ds} · {pct_ok_ds:.1f}%", "#00FFAA", border_alpha="0,255,170")
            with ds_cols[2]:
                render_flat_card("Fuera de Meta", f"{no_ds} · {pct_no_ds:.1f}%", "#FF6B6B", border_alpha="255,75,75")

            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

            # --- GRÁFICO: DESPACHOS POR DÍA ---
            st.markdown("<div class='donut-section-title-s'>DESPACHOS POR DÍA: A TIEMPO VS. FUERA DE TIEMPO</div>", unsafe_allow_html=True)
            if not validos_ds.empty:
                df_dia_ds = validos_ds.assign(DIA=validos_ds["FECHA DE ENVÍO"].dt.strftime("%d/%m"),
                                              _ORDEN=validos_ds["FECHA DE ENVÍO"].dt.normalize())
                df_dia_ds = df_dia_ds.groupby(["_ORDEN", "DIA", "Estado_KPI"]).size().reset_index(name="Facturas")
                df_dia_ds = df_dia_ds.sort_values("_ORDEN")
                fig_ds = px.bar(df_dia_ds, x="DIA", y="Facturas", color="Estado_KPI", barmode="stack",
                                category_orders={"DIA": df_dia_ds["DIA"].drop_duplicates().tolist()},
                                color_discrete_map={"A Tiempo": "#00FFAA", "Fuera de Tiempo": "#FF6B6B"})
                fig_ds.update_xaxes(type="category", tickmode="linear", tickangle=-45)
                fig_ds.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                     font={"color": "#E8EEF2", "family": "Inter, sans-serif", "size": 12},
                                     margin={"t": 20, "b": 10, "l": 10, "r": 10}, height=320,
                                     xaxis_title=None, yaxis_title=None,
                                     legend={"orientation": "h", "y": -0.2, "title": None})
                st.plotly_chart(fig_ds, use_container_width=True, config={'displayModeBar': False}, key=f"desp_dia_{mes_sel_desp}")
            else:
                st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos para graficar</div>", unsafe_allow_html=True)

            # --- DETALLE DE OPERACIÓN ---
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            st.markdown("<div class='donut-section-title-s'>DETALLE DE OPERACIÓN EN TIEMPO REAL</div>", unsafe_allow_html=True)

            df_lista_ds = df_desp.copy()
            if filtro_estado_desp == "A TIEMPO":
                df_lista_ds = df_lista_ds[df_lista_ds["Estado_KPI"] == "A Tiempo"]
            elif filtro_estado_desp == "FUERA DE TIEMPO":
                df_lista_ds = df_lista_ds[df_lista_ds["Estado_KPI"] == "Fuera de Tiempo"]
            if buscar_desp.strip():
                df_lista_ds = df_lista_ds[df_lista_ds["NÚMERO DE PEDIDO"].str.contains(buscar_desp.strip(), case=False, na=False)]

            # Fuera de tiempo: primero los de mayor retraso; resto: más recientes primero
            if filtro_estado_desp == "FUERA DE TIEMPO":
                df_lista_ds = df_lista_ds.sort_values("DIAS_HABILES", ascending=False)
            else:
                df_lista_ds = df_lista_ds.sort_values("EMISION", ascending=False, na_position="last")

            if df_lista_ds.empty:
                st.info("No hay registros para los filtros seleccionados.")
            else:
                data_detalle_ds = df_lista_ds.to_dict("records")
                alto_detalle_ds = min(len(data_detalle_ds) * 72 + 20, 550)

                def _fmt_fecha_ds(v):
                    return v.strftime("%d/%m/%Y %H:%M") if pd.notna(v) else "S/D"

                def _tarjeta_ds(item):
                    est = str(item["Estado_KPI"])
                    if est == "A Tiempo":
                        color, clase = "#00FFAA", "st-ok"
                    elif est == "Fuera de Tiempo":
                        color, clase = "#FF6B6B", "st-fuera"
                    else:
                        color, clase = "#94a3b8", "st-otro"
                    dias = item["DIAS_HABILES"]
                    dias_txt = f"{int(dias)} DÍAS HÁB." if pd.notna(dias) else "—"
                    return f"""
                    <div class="card-detalle" style="border-left-color: {color};">
                        <div style="flex: 1;"><div class="label-mini">Pedido</div>
                            <div class="val-pedido">{html_lib.escape(str(item['NÚMERO DE PEDIDO']))}</div></div>
                        <div class="col-sep" style="flex: 1.5;"><div class="label-mini">Emisión</div>
                            <div class="val-fecha">{_fmt_fecha_ds(item['EMISION'])}</div></div>
                        <div class="col-sep" style="flex: 1.5;"><div class="label-mini">Salida de Almacén</div>
                            <div class="val-fecha">{_fmt_fecha_ds(item['FECHA DE ENVÍO'])}</div></div>
                        <div class="col-sep" style="flex: 0.8;"><div class="label-mini">Diferencia</div>
                            <div class="val-fecha">{dias_txt}</div></div>
                        <div style="flex: 1; text-align: right;"><span class="badge-kpi {clase}">{est.upper()}</span></div>
                    </div>"""

                html_detalle_ds = f"""
                <div style="font-family: 'Inter', sans-serif; padding-right: 10px;">
                    <style>
                        body {{ background: transparent; margin: 0; padding: 0; }}
                        ::-webkit-scrollbar {{ width: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ background: #4B5D67; border-radius: 10px; }}
                        .card-detalle {{ background: #182229; border: 1px solid #4B5D67; border-left: 5px solid #94a3b8; border-radius: 8px;
                                         padding: 12px 20px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }}
                        .col-sep {{ padding: 0 10px; border-left: 1px solid rgba(75,93,103,0.5); }}
                        .label-mini {{ font-size: 8px; color: #8B9BB4; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }}
                        .val-pedido {{ color: #00FFAA; font-family: monospace; font-size: 15px; font-weight: 800; }}
                        .val-fecha {{ color: #E8EEF2; font-size: 11px; font-weight: 400; }}
                        .badge-kpi {{ padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; display: inline-block; min-width: 100px; text-align: center; }}
                        .st-ok {{ background: rgba(0,255,170,0.1); color: #00FFAA; border: 1px solid rgba(0,255,170,0.25); }}
                        .st-fuera {{ background: rgba(255,107,107,0.1); color: #FF6B6B; border: 1px solid rgba(255,107,107,0.25); }}
                        .st-otro {{ background: rgba(255,255,255,0.05); color: #94a3b8; border: 1px solid rgba(255,255,255,0.1); }}
                    </style>
                    {"".join(_tarjeta_ds(item) for item in data_detalle_ds)}
                </div>
                """
                components.html(html_detalle_ds, height=alto_detalle_ds, scrolling=True)

                # --- DESCARGA EXCEL (al final de la lista, estilo layout.py) ---
                df_excel_ds = pd.DataFrame({
                    "NÚMERO DE PEDIDO": df_lista_ds["NÚMERO DE PEDIDO"],
                    "EMISION": df_lista_ds["EMISION"].dt.strftime("%d/%m/%Y %H:%M").fillna("S/D"),
                    "FECHA DE ENVÍO": df_lista_ds["FECHA DE ENVÍO"].dt.strftime("%d/%m/%Y %H:%M").fillna("S/D"),
                    "ESTATUS": df_lista_ds["Estado_KPI"],
                    "DÍAS HÁBILES": df_lista_ds["DIAS_HABILES"],
                })
                buffer_ds = io_lib.BytesIO()
                try:
                    with pd.ExcelWriter(buffer_ds, engine="xlsxwriter") as writer_ds:
                        df_excel_ds.to_excel(writer_ds, index=False, sheet_name="Detalle_Operacion")
                except ImportError:
                    buffer_ds = io_lib.BytesIO()
                    with pd.ExcelWriter(buffer_ds, engine="openpyxl") as writer_ds:
                        df_excel_ds.to_excel(writer_ds, index=False, sheet_name="Detalle_Operacion")
                buffer_ds.seek(0)

                st.markdown("""
                    <style>
                        .st-key-dl_desp_excel button,
                        .st-key-dl_desp_excel [data-testid="stDownloadButton"] button,
                        .st-key-dl_desp_excel [data-testid="stBaseButton-secondary"] {
                            background-color: #628290 !important;
                            color: #ffffff !important;
                            border: 1px solid #628290 !important;
                            border-radius: 7px !important;
                            font-weight: 700 !important;
                            text-transform: uppercase !important;
                            font-size: 10px !important;
                            height: 32px !important;
                            width: 100% !important;
                            transition: all 0.3s ease !important;
                        }
                        .st-key-dl_desp_excel button:hover,
                        .st-key-dl_desp_excel [data-testid="stBaseButton-secondary"]:hover {
                            background-color: #4E6772 !important;
                            border-color: #4E6772 !important;
                            color: #ffffff !important;
                        }
                    </style>
                """, unsafe_allow_html=True)
                _, col_dl_ds = st.columns([3, 1])
                with col_dl_ds:
                    st.download_button(
                        label="DESCARGAR EXCEL",
                        data=buffer_ds,
                        file_name=f"Detalle_Operacion_{mes_sel_desp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="dl_desp_excel",
                    )

        # ----------------------------------------------------------
        # TAB 4: PESTAÑA 4 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab4:
            render_subtitulo("RANKING DE FLETERAS // DESEMPEÑO Y PUNTUALIDAD")
            st.markdown('<div class="spacer-menu"></div>', unsafe_allow_html=True)

            # --- PREPARACIÓN DE DATOS BASE (todo el ranking parte de aquí) ---
            df_rank_raw = df_raw.copy()
            for col_fecha_rk in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
                if col_fecha_rk in df_rank_raw.columns:
                    df_rank_raw[col_fecha_rk] = pd.to_datetime(df_rank_raw[col_fecha_rk], dayfirst=True, errors='coerce')
                else:
                    df_rank_raw[col_fecha_rk] = pd.NaT

            if "FLETERA" not in df_rank_raw.columns:
                df_rank_raw["FLETERA"] = ""
            df_rank_raw["FLETERA"] = df_rank_raw["FLETERA"].fillna("")

            if "INCIDENCIAS" not in df_rank_raw.columns:
                df_rank_raw["INCIDENCIAS"] = ""
            df_rank_raw["INCIDENCIAS"] = df_rank_raw["INCIDENCIAS"].fillna("")

            def _limpiar_moneda_rk(serie):
                return pd.to_numeric(
                    serie.astype(str).str.replace(r"[^\d\.\-]", "", regex=True).replace("", "0"),
                    errors="coerce"
                ).fillna(0.0)

            for col_num_rk in ["COSTO DE LA GUÍA", "COSTOS ADICIONALES", "CANTIDAD DE CAJAS"]:
                df_rank_raw[col_num_rk] = _limpiar_moneda_rk(df_rank_raw[col_num_rk]) if col_num_rk in df_rank_raw.columns else 0.0

            # --- FLETERAS PRINCIPALES: TODA la pestaña evalúa solo estas, sin importar el filtro ---
            FLETERAS_PRINCIPALES_RK = ["TRES GUERRAS", "ONE", "TINY PACK", "PAQMEX", "SANCHEZ", "FLETES DE REGRESO"]
            df_rank_raw = df_rank_raw[
                df_rank_raw["FLETERA"].astype(str).str.upper().str.strip().apply(
                    lambda nom_x: any(p in nom_x for p in FLETERAS_PRINCIPALES_RK)
                )
            ]

            # --- FILTRO COMPARTIDO POR LAS 3 SUB-TABS ---
            rkf1, rkf2 = st.columns([1.3, 3])
            with rkf1:
                mes_sel_rank = st.selectbox("PERÍODO", meses, index=hoy_gdl.month - 1, key="select_mes_rank")
            with rkf2:
                op_fletera_rank = sorted([x for x in df_rank_raw["FLETERA"].unique().tolist() if str(x).strip() != ""])
                filtro_fletera_rank = st.multiselect("FLETERA", op_fletera_rank, default=[], key="rank_filtro_fletera")

            num_mes_rank = meses.index(mes_sel_rank) + 1
            df_rank_periodo = df_rank_raw[df_rank_raw["FECHA DE ENVÍO"].dt.month == num_mes_rank].copy()
            df_rank_periodo = df_rank_periodo[df_rank_periodo["FLETERA"].astype(str).str.strip() != ""]

            # --- MÉTRICAS BASE POR REGISTRO (se calculan antes de aplicar el filtro de fletera) ---
            df_rank_periodo["_ENTREGADO"] = df_rank_periodo["FECHA DE ENTREGA REAL"].notna()
            df_rank_periodo["_A_TIEMPO"] = df_rank_periodo["_ENTREGADO"] & (df_rank_periodo["FECHA DE ENTREGA REAL"] <= df_rank_periodo["PROMESA DE ENTREGA"])
            df_rank_periodo["_INCIDENCIA"] = ~df_rank_periodo["INCIDENCIAS"].astype(str).str.strip().str.upper().isin(["", "OK"])
            df_rank_periodo["_DIAS_TRANSITO"] = (df_rank_periodo["FECHA DE ENTREGA REAL"] - df_rank_periodo["FECHA DE ENVÍO"]).dt.days
            df_rank_periodo["_COSTO_TOTAL"] = df_rank_periodo["COSTO DE LA GUÍA"] + df_rank_periodo["COSTOS ADICIONALES"]

            df_rank = df_rank_periodo.copy()
            if filtro_fletera_rank:
                df_rank = df_rank[df_rank["FLETERA"].isin(filtro_fletera_rank)]

            st.markdown(f"""<div style="text-align:left; margin-top:5px; margin-bottom:5px;">
                <span style="color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;">
                    MOSTRANDO {len(df_rank)} REGISTROS CORRESPONDIENTES A {mes_sel_rank}
                </span>
            </div>""", unsafe_allow_html=True)

            # --- RESUMEN AGREGADO POR FLETERA (alimenta las 3 sub-tabs) ---
            def _resumen_por_fletera_rk(df_in):
                filas_x = []
                for fletera_x, g_x in df_in.groupby("FLETERA"):
                    entregados_x = int(g_x["_ENTREGADO"].sum())
                    a_tiempo_x = int(g_x["_A_TIEMPO"].sum())
                    pct_a_tiempo_x = (a_tiempo_x / entregados_x * 100) if entregados_x else None
                    incidencias_pct_x = (g_x["_INCIDENCIA"].sum() / len(g_x) * 100) if len(g_x) else 0.0
                    dias_validos_x = g_x.loc[g_x["_ENTREGADO"] & (g_x["_DIAS_TRANSITO"] >= 0), "_DIAS_TRANSITO"]
                    dias_prom_x = dias_validos_x.mean() if not dias_validos_x.empty else None
                    cajas_sum_x = g_x["CANTIDAD DE CAJAS"].sum()
                    costo_sum_x = g_x["_COSTO_TOTAL"].sum()
                    costo_prom_envio_x = g_x["_COSTO_TOTAL"].mean() if len(g_x) else 0.0
                    costo_prom_caja_x = (costo_sum_x / cajas_sum_x) if cajas_sum_x else None
                    filas_x.append({
                        "FLETERA": fletera_x,
                        "ENVIOS": len(g_x),
                        "ENTREGADOS": entregados_x,
                        "A_TIEMPO": a_tiempo_x,
                        "RETRASO": max(entregados_x - a_tiempo_x, 0),
                        "PCT_A_TIEMPO": pct_a_tiempo_x,
                        "INCIDENCIAS_PCT": incidencias_pct_x,
                        "DIAS_TRANSITO_PROM": dias_prom_x,
                        "COSTO_PROM_ENVIO": costo_prom_envio_x,
                        "COSTO_PROM_CAJA": costo_prom_caja_x,
                    })
                return pd.DataFrame(filas_x)

            df_resumen_rk = _resumen_por_fletera_rk(df_rank)

            # --- RESUMEN FIJO SIN FILTRO DE FLETERA (base ya restringida a las fleteras principales) ---
            df_resumen_principales_rk = _resumen_por_fletera_rk(df_rank_periodo)

            config_layout_rk = {
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#E8EEF2", "family": "Inter, sans-serif", "size": 12},
                "margin": {"t": 20, "b": 10, "l": 10, "r": 10},
                "height": 360,
            }

            def _titulo_sub_rk(texto_sub):
                st.markdown(f"""<div style="text-align:left; margin-top:5px; margin-bottom:15px;">
                    <span style="color:#FFC000; font-weight:600; font-size:12px; letter-spacing:3px;">
                        {texto_sub}
                    </span>
                </div>""", unsafe_allow_html=True)

            sub_rank1, sub_rank2, sub_rank3 = st.tabs([
                "EFECTIVIDAD DE ENTREGAS",
                "TIEMPOS DE TRÁNSITO",
                "COSTO PROMEDIO POR PAQUETERÍA",
            ])

            # ==========================================================
            # SUB-TAB 1: EFECTIVIDAD DE ENTREGAS
            # ==========================================================
            with sub_rank1:
                _titulo_sub_rk("EFECTIVIDAD DE ENTREGAS // % DE CUMPLIMIENTO DE PROMESA")

                total_entregados_rk = int(df_rank["_ENTREGADO"].sum())
                total_a_tiempo_rk = int(df_rank["_A_TIEMPO"].sum())
                efectividad_global_rk = (total_a_tiempo_rk / total_entregados_rk * 100) if total_entregados_rk else 0.0

                df_con_entregas_rk = df_resumen_rk[df_resumen_rk["ENTREGADOS"] > 0]
                if not df_con_entregas_rk.empty:
                    fila_top_rk = df_con_entregas_rk.loc[df_con_entregas_rk["PCT_A_TIEMPO"].idxmax()]
                    fletera_top_rk = f"{fila_top_rk['FLETERA']}"
                    fletera_top_val_rk = f"{fila_top_rk['PCT_A_TIEMPO']:.0f}%"
                else:
                    fletera_top_rk, fletera_top_val_rk = "—", "—"

                if not df_resumen_rk.empty:
                    fila_inc_rk = df_resumen_rk.loc[df_resumen_rk["INCIDENCIAS_PCT"].idxmax()]
                    fletera_inc_rk = f"{fila_inc_rk['FLETERA']}"
                    fletera_inc_val_rk = f"{fila_inc_rk['INCIDENCIAS_PCT']:.0f}%"
                else:
                    fletera_inc_rk, fletera_inc_val_rk = "—", "—"

                rk1_cols = st.columns(4)
                with rk1_cols[0]:
                    render_flat_card("Efectividad Global", f"{efectividad_global_rk:.0f}%", "#8FBF9F", border_alpha="143,191,159")
                with rk1_cols[1]:
                    render_flat_card("Pedidos Entregados", total_entregados_rk, "#E8EEF2")
                with rk1_cols[2]:
                    render_flat_card(f"Más Puntual: {fletera_top_rk}", fletera_top_val_rk, "#FFD166")
                with rk1_cols[3]:
                    render_flat_card(f"Más Incidencias: {fletera_inc_rk}", fletera_inc_val_rk, "#B98B78", border_alpha="185,139,120")

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                rkc1, rkc2 = st.columns(2)
                with rkc1:
                    st.markdown("<div class='donut-section-title-s'>RANKING DE EFECTIVIDAD — FLETERAS PRINCIPALES (%)</div>", unsafe_allow_html=True)
                    df_con_entregas_principales_rk = df_resumen_principales_rk[df_resumen_principales_rk["ENTREGADOS"] > 0]
                    if not df_con_entregas_principales_rk.empty:
                        df_plot_rk1 = df_con_entregas_principales_rk.sort_values("PCT_A_TIEMPO", ascending=True)
                        fig_rk1 = px.bar(df_plot_rk1, x="PCT_A_TIEMPO", y="FLETERA", orientation="h",
                                          color_discrete_sequence=["#8FBF9F"])
                        fig_rk1.update_traces(text=df_plot_rk1["PCT_A_TIEMPO"].round(0).astype(int).astype(str) + "%",
                                              textposition="outside", textfont=dict(color="#E8EEF2"))
                        fig_rk1.update_layout(**config_layout_rk, xaxis_title="% A TIEMPO", yaxis_title=None)
                        st.plotly_chart(fig_rk1, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin entregas registradas en este período</div>", unsafe_allow_html=True)

                with rkc2:
                    st.markdown("<div class='donut-section-title-s'>COMPOSICIÓN — FLETERAS PRINCIPALES: A TIEMPO VS. CON RETRASO</div>", unsafe_allow_html=True)
                    if not df_con_entregas_principales_rk.empty:
                        df_largo_rk = pd.concat([
                            df_con_entregas_principales_rk[["FLETERA", "A_TIEMPO"]].rename(columns={"A_TIEMPO": "Cantidad"}).assign(Estatus="A TIEMPO"),
                            df_con_entregas_principales_rk[["FLETERA", "RETRASO"]].rename(columns={"RETRASO": "Cantidad"}).assign(Estatus="CON RETRASO"),
                        ])
                        fig_rk2 = px.bar(df_largo_rk, x="FLETERA", y="Cantidad", color="Estatus", barmode="stack",
                                          color_discrete_map={"A TIEMPO": "#8FBF9F", "CON RETRASO": "#B98B78"})
                        fig_rk2.update_layout(**config_layout_rk, xaxis_title=None, yaxis_title=None,
                                              legend={"orientation": "h", "y": -0.18})
                        st.plotly_chart(fig_rk2, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin entregas registradas en este período</div>", unsafe_allow_html=True)

            # ==========================================================
            # SUB-TAB 2: TIEMPOS DE TRÁNSITO
            # ==========================================================
            with sub_rank2:
                _titulo_sub_rk("TIEMPOS DE TRÁNSITO // DÍAS DE ENVÍO A ENTREGA")

                df_dias_validos_rk = df_rank[df_rank["_ENTREGADO"] & (df_rank["_DIAS_TRANSITO"] >= 0)]
                tiempo_prom_gral_rk = df_dias_validos_rk["_DIAS_TRANSITO"].mean() if not df_dias_validos_rk.empty else 0.0

                df_con_tiempo_rk = df_resumen_rk[df_resumen_rk["DIAS_TRANSITO_PROM"].notna()]
                if not df_con_tiempo_rk.empty:
                    fila_rapida_rk = df_con_tiempo_rk.loc[df_con_tiempo_rk["DIAS_TRANSITO_PROM"].idxmin()]
                    fila_lenta_rk = df_con_tiempo_rk.loc[df_con_tiempo_rk["DIAS_TRANSITO_PROM"].idxmax()]
                    rapida_nom_rk, rapida_val_rk = fila_rapida_rk["FLETERA"], f"{fila_rapida_rk['DIAS_TRANSITO_PROM']:.1f} días"
                    lenta_nom_rk, lenta_val_rk = fila_lenta_rk["FLETERA"], f"{fila_lenta_rk['DIAS_TRANSITO_PROM']:.1f} días"
                else:
                    rapida_nom_rk, rapida_val_rk = "—", "—"
                    lenta_nom_rk, lenta_val_rk = "—", "—"

                rk2_cols = st.columns(4)
                with rk2_cols[0]:
                    render_flat_card("Tiempo Promedio General", f"{tiempo_prom_gral_rk:.1f} días", "#7FA0B0")
                with rk2_cols[1]:
                    render_flat_card("Envíos Analizados", len(df_dias_validos_rk), "#E8EEF2")
                with rk2_cols[2]:
                    render_flat_card(f"Más Rápida: {rapida_nom_rk}", rapida_val_rk, "#8FBF9F", border_alpha="143,191,159")
                with rk2_cols[3]:
                    render_flat_card(f"Más Lenta: {lenta_nom_rk}", lenta_val_rk, "#B98B78", border_alpha="185,139,120")

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                rkc3, rkc4 = st.columns(2)
                with rkc3:
                    st.markdown("<div class='donut-section-title-s'>RANKING DE TIEMPO PROMEDIO DE TRÁNSITO (DÍAS)</div>", unsafe_allow_html=True)
                    if not df_con_tiempo_rk.empty:
                        df_plot_rk3 = df_con_tiempo_rk.sort_values("DIAS_TRANSITO_PROM", ascending=False)
                        fig_rk3 = px.bar(df_plot_rk3, x="DIAS_TRANSITO_PROM", y="FLETERA", orientation="h",
                                          color_discrete_sequence=["#7FA0B0"])
                        fig_rk3.update_traces(text=df_plot_rk3["DIAS_TRANSITO_PROM"].round(1).astype(str) + " días",
                                              textposition="outside", textfont=dict(color="#E8EEF2"))
                        fig_rk3.update_layout(**config_layout_rk, xaxis_title="DÍAS PROMEDIO", yaxis_title=None)
                        st.plotly_chart(fig_rk3, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin entregas registradas en este período</div>", unsafe_allow_html=True)

                with rkc4:
                    st.markdown("<div class='donut-section-title-s'>CONSISTENCIA DE TIEMPOS POR FLETERA</div>", unsafe_allow_html=True)
                    if not df_dias_validos_rk.empty:
                        fig_rk4 = px.box(df_dias_validos_rk, x="FLETERA", y="_DIAS_TRANSITO",
                                          color_discrete_sequence=["#7FA0B0"])
                        fig_rk4.update_layout(**config_layout_rk, xaxis_title=None, yaxis_title="DÍAS DE TRÁNSITO")
                        st.plotly_chart(fig_rk4, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos suficientes para graficar</div>", unsafe_allow_html=True)

            # ==========================================================
            # SUB-TAB 3: COSTO PROMEDIO POR PAQUETERÍA
            # ==========================================================
            with sub_rank3:
                _titulo_sub_rk("COSTO PROMEDIO POR PAQUETERÍA // GUÍA + ADICIONALES")

                costo_prom_envio_gral_rk = df_rank["_COSTO_TOTAL"].mean() if len(df_rank) else 0.0
                cajas_totales_rk = df_rank["CANTIDAD DE CAJAS"].sum()
                costo_prom_caja_gral_rk = (df_rank["_COSTO_TOTAL"].sum() / cajas_totales_rk) if cajas_totales_rk else 0.0

                df_con_costo_rk = df_resumen_rk[df_resumen_rk["ENVIOS"] > 0]
                if not df_con_costo_rk.empty:
                    fila_barata_rk = df_con_costo_rk.loc[df_con_costo_rk["COSTO_PROM_ENVIO"].idxmin()]
                    fila_cara_rk = df_con_costo_rk.loc[df_con_costo_rk["COSTO_PROM_ENVIO"].idxmax()]
                    barata_nom_rk, barata_val_rk = fila_barata_rk["FLETERA"], f"${fila_barata_rk['COSTO_PROM_ENVIO']:,.0f}"
                    cara_nom_rk, cara_val_rk = fila_cara_rk["FLETERA"], f"${fila_cara_rk['COSTO_PROM_ENVIO']:,.0f}"
                else:
                    barata_nom_rk, barata_val_rk = "—", "—"
                    cara_nom_rk, cara_val_rk = "—", "—"

                rk3_cols = st.columns(4)
                with rk3_cols[0]:
                    render_flat_card("Costo Prom. por Envío", f"${costo_prom_envio_gral_rk:,.0f}", "#B98B78", border_alpha="185,139,120")
                with rk3_cols[1]:
                    render_flat_card("Costo Prom. por Caja", f"${costo_prom_caja_gral_rk:,.2f}", "#C9A46C")
                with rk3_cols[2]:
                    render_flat_card(f"Más Económica: {barata_nom_rk}", barata_val_rk, "#8FBF9F", border_alpha="143,191,159")
                with rk3_cols[3]:
                    render_flat_card(f"Más Cara: {cara_nom_rk}", cara_val_rk, "#FF6B6B", border_alpha="255,75,75")

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                rkc5, rkc6 = st.columns(2)
                with rkc5:
                    st.markdown("<div class='donut-section-title-s'>RANKING DE COSTO PROMEDIO POR ENVÍO</div>", unsafe_allow_html=True)
                    if not df_con_costo_rk.empty:
                        df_plot_rk5 = df_con_costo_rk.sort_values("COSTO_PROM_ENVIO", ascending=False)
                        fig_rk5 = px.bar(df_plot_rk5, x="COSTO_PROM_ENVIO", y="FLETERA", orientation="h",
                                          color_discrete_sequence=["#B98B78"])
                        fig_rk5.update_traces(text="$" + df_plot_rk5["COSTO_PROM_ENVIO"].round(0).astype(int).astype(str),
                                              textposition="outside", textfont=dict(color="#E8EEF2"))
                        fig_rk5.update_layout(**config_layout_rk, xaxis_title="COSTO PROMEDIO ($)", yaxis_title=None)
                        st.plotly_chart(fig_rk5, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos para graficar</div>", unsafe_allow_html=True)

                with rkc6:
                    st.markdown("<div class='donut-section-title-s'>RANKING DE COSTO PROMEDIO POR CAJA</div>", unsafe_allow_html=True)
                    df_con_costo_caja_rk = df_con_costo_rk[df_con_costo_rk["COSTO_PROM_CAJA"].notna()]
                    if not df_con_costo_caja_rk.empty:
                        df_plot_rk6 = df_con_costo_caja_rk.sort_values("COSTO_PROM_CAJA", ascending=False)
                        fig_rk6 = px.bar(df_plot_rk6, x="COSTO_PROM_CAJA", y="FLETERA", orientation="h",
                                          color_discrete_sequence=["#C9A46C"])
                        fig_rk6.update_traces(text="$" + df_plot_rk6["COSTO_PROM_CAJA"].round(2).astype(str),
                                              textposition="outside", textfont=dict(color="#E8EEF2"))
                        fig_rk6.update_layout(**config_layout_rk, xaxis_title="COSTO PROMEDIO ($)", yaxis_title=None)
                        st.plotly_chart(fig_rk6, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos de cajas para graficar</div>", unsafe_allow_html=True)

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                st.markdown("<div class='donut-section-title-s'>MAPA DE VALOR: COSTO PROMEDIO VS. EFECTIVIDAD POR FLETERA</div>", unsafe_allow_html=True)
                df_mapa_valor_rk = df_resumen_rk[df_resumen_rk["PCT_A_TIEMPO"].notna() & (df_resumen_rk["ENVIOS"] > 0)]
                if not df_mapa_valor_rk.empty:
                    fig_rk7 = px.scatter(df_mapa_valor_rk, x="COSTO_PROM_ENVIO", y="PCT_A_TIEMPO", text="FLETERA",
                                          size="ENVIOS", color_discrete_sequence=["#7FA0B0"])
                    fig_rk7.update_traces(textposition="top center", textfont=dict(color="#E8EEF2", size=10), marker=dict(line=dict(width=0)))
                    fig_rk7.update_layout(**{**config_layout_rk, "height": 380},
                                          xaxis_title="COSTO PROMEDIO POR ENVÍO ($)", yaxis_title="% ENTREGAS A TIEMPO")
                    st.plotly_chart(fig_rk7, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin datos suficientes para graficar</div>", unsafe_allow_html=True)

        # ----------------------------------------------------------
        # TAB 5: PESTAÑA 5 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab5:
            render_subtitulo("COTIZADOR // CALCULADORA DE TARIFAS Y RUTAS")
            # =========================================================-
            # 1. PROCESAMIENTO DE DATOS
            # =========================================================
            df['FECHA DE ENVÍO'] = pd.to_datetime(df['FECHA DE ENVÍO'], errors='coerce')
            df['FECHA DE ENTREGA REAL'] = pd.to_datetime(df['FECHA DE ENTREGA REAL'], errors='coerce')
            df['DIAS_REALES'] = (df['FECHA DE ENTREGA REAL'] - df['FECHA DE ENVÍO']).dt.days
            
            # =========================================================
            # 2. SECCIÓN DEL CALCULADOR INTELIGENTE
            # =========================================================            
            usuario_actual = st.session_state.get('usuario_activo', 'Cielo')
            
            c1, c2, c3 = st.columns([1, 1, 0.8])
            
            with c1:
                st.text_input("ORIGEN", value="GUADALAJARA (GDL)", disabled=True, key="orig_fix")
            
            with c2:
                busqueda_manual = st.text_input(
                    "BUSCAR POR DESTINO, CP O DOMICILIO", 
                    placeholder="Ej: 63734, Litibu, Cancún...",
                    key="busqueda_manual_v6"
                )
            
            with c3:
                num_cajas = st.number_input("CANTIDAD DE CAJAS", min_value=1, value=1, step=1)
            
            # --- LÓGICA DE VISUALIZACIÓN POR DEFECTO ---
            if not busqueda_manual:
                df_validos = df[df['DIAS_REALES'].notna()]
                rutas_dos_dias = df_validos[df_validos['DIAS_REALES'] == 2]
                if not rutas_dos_dias.empty:
                    busqueda_activa = rutas_dos_dias['DESTINO'].iloc[0]
                    texto_mostrar = f"{busqueda_activa}"
                elif not df_validos.empty:
                    busqueda_activa = df_validos.groupby('DESTINO')['DIAS_REALES'].mean().idxmin()
                    texto_mostrar = f"{busqueda_activa} (Ruta sugerida)"
                else:
                    busqueda_activa = ""
                    texto_mostrar = "CONSULTA DE RUTA"
            else:
                busqueda_activa = busqueda_manual
                texto_mostrar = busqueda_manual.upper()
            
            # --- FILTRADO ---            
            busqueda_aux = str(busqueda_activa).lower() if pd.notna(busqueda_activa) else ""
            mask = (
                df['DESTINO'].astype(str).str.lower().str.contains(busqueda_aux, na=False) |
                df['DOMICILIO'].astype(str).str.lower().str.contains(busqueda_aux, na=False)
            )
            
            historial = df[mask & (df['DIAS_REALES'].notna())].copy()
            
            # --- ASIGNACIÓN DE VARIABLES (CON RESPALDO SI ESTÁ VACÍO) ---
            if not historial.empty:
                fletera_recomendada = historial['FLETERA'].value_counts().idxmax()
                promedio_dias = historial['DIAS_REALES'].mean()
                total_viajes = len(historial)
                dias_redondeados = math.ceil(promedio_dias)
                texto_domicilio = str(historial['DOMICILIO'].iloc[0]).upper()
            else:
                fletera_recomendada = "SIN REGISTRO"
                total_viajes = 0
                dias_redondeados = "N/D"
                texto_domicilio = ""
    
            # --- MOTOR LÓGICO DE PRECIOS NEXION ELITE ---
            regiones_65 = [
                "HERMOSILLO", "HERMOSILLO, SON", "GUAYMAS", "GUAYMAS, SON", 
                "DURANGO", "DURANGO, DUR", "SALTILLO", "SALTILLO, COA", 
                "TEPIC", "TEPIC, NAY", "MAZATLAN", "MAZATLAN, SIN", 
                "CANANEA", "CANANEA, SON", "TORREON", "TORREON, COA", 
                "CULIACAN", "CULIACAN, SIN", "CIUDAD OBREGON", "CIUDAD OBREGON, SON", 
                "LOS MOCHIS", "LOS MOCHIS, SIN", "OBREGON", "OBREGON, SON", 
                "CABORCA", "CABORCA, SON", "NOGALES", "NOGALES, SON", 
                "NAVOJOA", "NAVOJOA, SON", "MONTERREY", "MONTERREY, NL",
                "APODACA", "APODACA, NL", "PIEDRAS NEGRAS", "PIEDRAS NEGRAS, COA",
                "NUEVO VALLARTA", "NUEVO VALLARTA, NAY", "RINCON DE GUAYABITOS", "RINCON DE GUAYABITOS, NAY",
                "CAJEME, CIUDAD OBREGON, SON", "TORREON COAHUILA, COA",
                "QUERETARO", "QRO", "QUE", "GUANAJUATO", "GTO", "LEON", "CELAYA", 
                "AGUASCALIENTES", "AGS", "SAN LUIS POTOSI", "SLP", "HIDALGO", "HID", 
                "PUEBLA", "PUE", "JALISCO", "JAL", "ESTADO DE MEXICO", "EDOMEX",
                "TLAXCALA", "TLA", "MORELOS", "MOR", "CDMX", "CMX", "DF", "DF2",
                "MEXICO, DF", "MEXICO, DF2", "CIUDAD DE MEXICO", "MÉXICO, DF2", ", CMX",
                "CIUDAD DE MÉXICO, DF2", "DELEGACION CUAUHTEMOC, CMX", "ALCALDIA CUAUHTEMOC, CMX",
                "ALCALDIA CUAJIMALPA DE MORELOS, CMX", "CUAJIMALPA DE MORELOS, DF2",
                "MATEHUALA, SLP", "IXTAPAN DE LA SAL, MEX", "QUERETARO, QUE", "ATITALAQUIA, HID",
                "MORELIA, MCH", "SILAO, GTO", "TOLUCA, MEX", "SALAMANCA, GTO", "SANTIAGO DE QUERETARO, QUE",
                "JURIQUILLA, QUE", "PACHUCA, HID", "CALVILLO, AGS", "PUEBLA, PUE", "AMEALCO DE BONFIL, QUE",
                "TULA DE ALLENDE, HID", "ACAMBARO, GTO", "CUAUTLANCINGO, PUE", "NUEVA ITALIA, MCH", 
                "JACONA, MCH", "CORONANGO, PUE", "IRAPUATO, GTO", "GUANAJUATO, GTO", 
                "SAN MIGUEL DE ALLENDE, GTO", "ZAMORA, MCH", "CUERNAVACA, MOR", "TOLUCA, DF2", 
                "IXTAPALUCA, MEX", "IZTACALCO, CMX", "TETLATLAHUACA, TLA", "NAUCALPAN DE JUAREZ, MEX", 
                "NICOLAS ROMERO, MEX", "SAN ANDRES, PUE", "TLANEPANTLA, MEX", "TEPOTZOTLAN, MEX", 
                "VALLE DE BRAVO, MEX", "PATZCUARO, MCH", "ALVARO OBREGON, CMX", "TLALPAN, DF2", 
                "SAN ANDRES CHOLULA, PUE", "TOLUCA DE LERDO, MEX", "CEDRAL, SLP", "TEQUISQUIAPAN, QUE", 
                "TLALNEPANTLA DE BAZ, CMX", "MÉXICO, DF2", "BERNAL, QUE", "SILAO DE LA VICTORIA, GTO", 
                "SAN JUAN DEL RIO, QUE", "CUAHUTEMOC, CMX", "METEPEC, MEX", "PACHUCA de SOTO, HID", 
                "MUNICIPIO ALVARO OBREGON, MCH", "TLANEPANTLA, CMX", "ATLIXCO, PUE", "MIGUEL HIDALGO, CMX", 
                "SANTA CRUZ TECÁMAC, MEX", "EL MARQUES, QUE", "MARINA NACIONAL, CMX", "MEXICO, DF2", 
                "CUAJIMALPA DE MORELOS, CMX", "URUAPAN, MCH", "CIUDAD DE MEXICO, DF2", "BENITO JUAREZ, CMX", 
                "YAUHQUEMEHCAN, TLA", "NAUCALPAN DE JUAREZ, CMX", "GUADALAJARA, JAL", "ZAPOTLAN EL GRANDE, JAL",
                "ARANDAS, JAL", "SAN JUAN DE LOS LAGOS, JAL", "JOCOTEPEC, JAL", "CD GUZMAN, JAL"
            ]
            
            if any(x in texto_domicilio for x in ["VERACRUZ", " VER ", " VER.", ", VER"]):
                es_region_65 = False
            else:
                es_region_65 = any(region in texto_domicilio for region in regiones_65)
            
            if 1 <= num_cajas <= 4:
                precio_unitario = 450 / num_cajas
                total_sin_iva = 450
                leyenda_region = "Tarifa Plana Nacional (1-4 cajas)"
            else:
                if es_region_65:
                    precio_unitario = 65
                    leyenda_region = "Zona con Tarifa Preferencial"
                else:
                    precio_unitario = 95
                    leyenda_region = "Zona Norte / Sur / Costa"
                total_sin_iva = num_cajas * precio_unitario
            
            total_con_iva = total_sin_iva * 1.16 if not historial.empty else 0.0
    
            # --- RENDER PRINCIPAL (TARJETAS DE MÉTRICAS - SIEMPRE SE MUESTRA) ---
            st.markdown(f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; width: 100%; margin-bottom: 25px; font-family: 'Inter', sans-serif;"><div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #38bdf8; border-radius: 12px; padding: 22px 25px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between;"><div><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;"><span style="font-size: 10px; color: #38bdf8; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;">TIEMPO ESTIMADO DE RUTA</span><span style="font-size: 12px; color: #ffffff; font-weight: 800; background: rgba(56, 189, 248, 0.2); padding: 5px 12px; border-radius: 6px; border: 1.5px solid #38bdf8; letter-spacing: 0.5px;">{fletera_recomendada}</span></div><div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.2); padding: 14px 18px; border-radius: 8px; margin-bottom: 15px; border: 1px solid rgba(255,255,255,0.04);"><div style="text-align: left;"><div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px;">ORIGEN</div><div style="font-size: 14px; color: white; font-weight: 800; margin-top: 2px;">GDL</div></div><div style="text-align: center; flex-grow: 1; padding: 0 15px;"><div style="font-size: 8px; color: #38bdf8; font-weight: 800; letter-spacing: 2px; margin-bottom: 3px;">EN TRÁNSITO</div><div style="height: 2px; background: linear-gradient(90deg, #38bdf8, #a855f7); width: 100%;"></div></div><div style="text-align: right;"><div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px;">DESTINO</div><div style="font-size: 14px; color: #00FFAA; font-weight: 800; margin-top: 2px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{texto_mostrar[:18]}</div></div></div></div><div style="display: flex; align-items: baseline; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 5px;"><div style="display: flex; align-items: baseline; gap: 8px;"><span style="font-size: 2rem; font-weight: 900; color: white; line-height: 1;">{dias_redondeados}</span><span style="font-size: 11px; color: #38bdf8; font-weight: 800; letter-spacing: 1px;">DÍAS HÁBILES</span></div><span style="font-size: 10px; color: rgba(255,255,255,0.5); font-style: italic;">Basado en {total_viajes} entregas</span></div></div><div style="background: {vars_css['card']}; border: 1px solid {vars_css['border']}; border-left: 5px solid #FFD700; border-radius: 12px; padding: 22px 25px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between;"><div><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;"><span style="font-size: 10px; color: #FFD700; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;">INVERSIÓN LOGÍSTICA</span><span style="font-size: 11px; color: rgba(255,255,255,0.8); font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">*INCLUYE 16% IVA</span></div><div style="display: flex; align-items: baseline; gap: 6px; margin-bottom: 12px;"><span style="font-size: 2rem; font-weight: 900; color: #FFD700; line-height: 1;">${total_con_iva:,.2f}</span><span style="font-size: 11px; color: rgba(255,255,255,0.6); font-weight: 700;">MXN</span></div></div><div style="background: rgba(0,0,0,0.25); border-radius: 8px; padding: 12px 15px; border: 1px solid rgba(255,255,255,0.04);"><div style="display: flex; justify-content: space-between; font-size: 13px; color: white; margin-bottom: 6px; align-items: baseline;"><span>CANTIDAD DE CAJAS: <b style="color: #38bdf8; font-size: 15px;">{num_cajas}</b></span><span style="font-size: 11px;">UNITARIO: <b style="color: #00FFAA;">${precio_unitario:,.2f}</b></span></div><div style="font-size: 10px; color: #FFD700; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 6px;">✓ {leyenda_region}</div></div></div></div>""", unsafe_allow_html=True)
            # --- SECCIÓN DE HISTORIAL Y SCROLL CHINGÓN ---
            st.markdown(f'<p style="color:{"#FFFFFF" if not historial.empty else "rgba(255,255,255,0.5)"}; font-weight:800; letter-spacing:2px; font-size:14px; margin-bottom:15px; border-left: 4px solid {"#00FFAA" if not historial.empty else "#FFD700"}; padding-left: 10px;">{"HISTORIAL DE ENVÍOS ENCONTRADOS" if not historial.empty else "SIN HISTORIAL DE ENVÍOS PREVIOS"}</p>', unsafe_allow_html=True)
            
               
            if not historial.empty:
                # Preparación de datos
                historial_sorted = historial[['NÚMERO DE PEDIDO','NOMBRE DEL CLIENTE','DOMICILIO','FECHA DE ENVÍO','FLETERA']].sort_values(by='FECHA DE ENVÍO', ascending=False).copy()
                historial_sorted['FECHA_STR'] = historial_sorted['FECHA DE ENVÍO'].dt.strftime('%d/%m/%Y')
                data_hist = historial_sorted.fillna('').to_dict('records')
    
                # Renderizado con Scroll Chidote (Components HTML)
                html_historial = f"""
                <div style="padding: 5px; font-family: 'Inter', sans-serif;">
                    <style>
                        .card-historial {{ background-color: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 14px 20px; margin-bottom: 10px; transition: all 0.3s ease; display: flex; justify-content: space-between; align-items: center; width: 100%; box-sizing: border-box; }}
                        .card-historial:hover {{ border-color: #38bdf8; background-color: #2d3b42; transform: translateX(4px); }}
                        .label-mini {{ font-size: 8px; text-transform: uppercase; color: rgba(255,255,255,0.5); font-weight: 800; letter-spacing: 1px; }}
                        .valor-id {{ font-size: 15px; font-weight: 800; color: #00FFAA; font-family: monospace; }}
                        .valor-text {{ font-size: 12px; font-weight: 600; color: #FFFFFF; }}
                        .sub-text {{ font-size: 10px; color: rgba(255,255,255,0.6); font-style: italic; }}
                        
                        /* Scrollbar chingón */
                        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); }}
                        ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                    </style>
                    {"".join([f'''
                    <div class="card-historial">
                        <div style="flex: 1;"><div class="label-mini">Pedido</div><div class="valor-id">{str(item.get('NÚMERO DE PEDIDO', ''))}</div></div>
                        <div style="flex: 2; padding: 0 15px;"><div class="label-mini">Cliente / Domicilio</div><div class="valor-text">{str(item.get('NOMBRE DEL CLIENTE', ''))[:35]}</div><div class="sub-text">{str(item.get('DOMICILIO', ''))[:50]}</div></div>
                        <div style="flex: 1; text-align: right;"><div class="label-mini">Fletera / Fecha</div><div style="color: #38bdf8; font-size: 12px; font-weight: 700;">{str(item.get('FLETERA', ''))}</div><div class="valor-text" style="font-size: 11px; opacity: 0.8;">{item.get('FECHA_STR', '')}</div></div>
                    </div>''' for item in data_hist])}
                </div>"""
                components.html(html_historial, height=450, scrolling=True)
            else:
                st.markdown(
                    f"""
                    <div style="background-color: #212529; border: 1px solid #ff4d4d; border-radius: 6px; padding: 14px 18px; font-family: 'Inter', sans-serif; box-sizing: border-box; width: 100%;">
                        <div style="font-size: 10px; color: #ff4d4d; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px;">AVISO DEL SISTEMA: SIN COINCIDENCIAS</div>
                        <div style="font-size: 13px; color: #d1d5db; font-weight: 500; margin-bottom: 6px;">Lo siento <b style="color: #ffffff;">{st.session_state.get("nombre_completo", usuario_actual)}</b>, no se encontró historial de envíos para: <b style="color: #ff4d4d;">{busqueda_manual}</b></div>
                        <div style="font-size: 9px; color: #ffffff; font-weight: 300; letter-spacing: 1px; text-transform: uppercase; margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 6px;">[ ACCIÓN: VERIFICA LOS DATOS O VALIDA COBERTURA DIRECTA EN LOGÍSTICA // 33 19 75 31 22 ]</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

if __name__ == "__main__":
    main()
