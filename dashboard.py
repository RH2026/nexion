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

                # ENVIADAS: cuenta todo lo que ya tenga fecha de envío registrada,
                # sin importar si aún no tiene número de guía asignado.
                enviadas = len(df_filtrado[df_filtrado['fecha_envio'].astype(str).str.strip().str.lower().apply(lambda v: v not in valores_nulos)])
                surtidas_tiempo = len(df_filtrado[df_filtrado['estatus'] == "SURTIDA / EN TIEMPO"])
                con_retraso = len(df_filtrado[df_filtrado['estatus'] == "CON RETRASO"])
                pendientes = len(df_filtrado[df_filtrado['estatus'].str.contains("PENDIENTE", na=False)])

                # EFECTIVIDAD: sólo cuenta como efectivo lo que se envió/surtió el
                # MISMO día que estaba programado. Si la fecha de envío quedó
                # registrada al día siguiente (o después), ya no entra en la efectividad.
                mask_mismo_dia_s = (
                    df_filtrado['dt_prog_parsed'].notna()
                    & df_filtrado['dt_envio_parsed'].notna()
                    & (df_filtrado['dt_prog_parsed'].dt.date == df_filtrado['dt_envio_parsed'].dt.date)
                )
                efectivas_mismo_dia = int(mask_mismo_dia_s.sum())
                porcentaje_exito = (efectivas_mismo_dia / total_facturas * 100) if total_facturas > 0 else 0

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
                    col_c1, col_c2 = st.columns(2)

                    config_layout_s = {
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)",
                        "font": {"color": "#E8EEF2", "family": "Inter, sans-serif", "size": 11},
                        "margin": {"t": 20, "b": 10, "l": 10, "r": 10},
                        "legend": {"orientation": "h", "y": -0.15}
                    }

                    with col_c1:
                        st.markdown("<div class='donut-section-title'>DISTRIBUCIÓN POR ESTATUS DE SURTIDO</div>", unsafe_allow_html=True)
                        df_estatus_counts = df_filtrado['estatus'].value_counts().reset_index()
                        df_estatus_counts.columns = ['Estatus', 'Cantidad']

                        fig_donita_s1 = px.pie(
                            df_estatus_counts,
                            names='Estatus',
                            values='Cantidad',
                            hole=0.6,
                            color_discrete_sequence=['#00FFAA', '#FFD166', '#FF6B6B', '#3B82F6']
                        )
                        fig_donita_s1.update_traces(textposition='inside', textinfo='percent+value')
                        fig_donita_s1.update_layout(**config_layout_s)
                        st.plotly_chart(fig_donita_s1, use_container_width=True, config={'displayModeBar': False})

                    with col_c2:
                        st.markdown("<div class='donut-section-title'>VOLUMEN OPERATIVO POR PAQUETERÍA</div>", unsafe_allow_html=True)
                        df_paq_counts = df_filtrado['recomendacion'].value_counts().reset_index()
                        df_paq_counts.columns = ['Paquetería', 'Cantidad']

                        fig_donita_s2 = px.pie(
                            df_paq_counts,
                            names='Paquetería',
                            values='Cantidad',
                            hole=0.6,
                            color_discrete_sequence=['#00A3A3', '#3B82F6', '#8B5CF6', '#EC4899', '#64748B']
                        )
                        fig_donita_s2.update_traces(textposition='inside', textinfo='percent+value')
                        fig_donita_s2.update_layout(**config_layout_s)
                        st.plotly_chart(fig_donita_s2, use_container_width=True, config={'displayModeBar': False})

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
                        if "TIEMPO" in est:
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
            
            # --- FILTRO DE PERÍODO INTEGRADO DENTRO DE LA TAB 1 ---
            mes_sel = st.selectbox("PERÍODO", meses, index=hoy_gdl.month - 1, key="select_mes_tab1")
            
            df_raw_tab1 = cargar_datos()

            if df_raw_tab1 is not None:
                df_raw_tab1["FECHA DE ENVÍO DT"] = pd.to_datetime(df_raw_tab1["FECHA DE ENVÍO"], dayfirst=True, errors='coerce')
                num_mes_sel = meses.index(mes_sel) + 1
                
                df_filtrado_mes = df_raw_tab1[df_raw_tab1["FECHA DE ENVÍO DT"].dt.month == num_mes_sel].copy()
                df_filtrado_mes = df_filtrado_mes.sort_values(by="FECHA DE ENVÍO DT", ascending=False)
                
                st.markdown(f"<p style='color:#00FFAA; font-size:11px; font-style:italic; margin-top:5px;'>Mostrando {len(df_filtrado_mes)} registros correspondientes a {mes_sel}</p>", unsafe_allow_html=True)
            
            df = df_raw_tab1.copy()
            for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        
            df_mes = df[df["FECHA DE ENVÍO"].dt.month == (meses.index(mes_sel) + 1)].copy()
        
            total_p = len(df_mes)
            entregados = len(df_mes[df_mes["FECHA DE ENTREGA REAL"].notna()])
            df_trans = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna()]
            en_tiempo = len(df_trans[df_trans["PROMESA DE ENTREGA"] >= hoy_dt])
            retrasados = len(df_trans[df_trans["PROMESA DE ENTREGA"] < hoy_dt])
            total_t = len(df_trans)  

            st.markdown("<br>", unsafe_allow_html=True)

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
                "legend": {"orientation": "h", "y": -0.15},
            }

            col_d1, col_d2 = st.columns(2)

            with col_d1:
                st.markdown("<div class='donut-section-title'>DISTRIBUCIÓN DE PEDIDOS DEL MES</div>", unsafe_allow_html=True)
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
                    fig_donita1.update_traces(textposition='inside', textinfo='percent+value')
                    fig_donita1.update_layout(**config_layout)
                    st.plotly_chart(fig_donita1, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin pedidos en este período</div>", unsafe_allow_html=True)

            with col_d2:
                st.markdown("<div class='donut-section-title'>PORCENTAJE DE PEDIDOS CON RETRASO POR FLETERA</div>", unsafe_allow_html=True)
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
                    fig_donita2.update_traces(textposition='inside', textinfo='percent+value')
                    fig_donita2.update_layout(**config_layout)
                    st.plotly_chart(fig_donita2, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown("<div style='padding:20px; color:#00FFAA; font-size:12px; font-weight:bold;'>✓ Sin pedidos con retraso en este período</div>", unsafe_allow_html=True)

        # ----------------------------------------------------------
        # TAB 2: PESTAÑA 2 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab2:
            render_subtitulo("DISTRIBUCIÓN DE CARGA // VOLUMEN Y OCUPACIÓN POR FLETERA")
             
        # ----------------------------------------------------------
        # TAB 3: PESTAÑA 3 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab3:
            render_subtitulo("EFECTIVIDAD DE ENVÍOS // CUMPLIMIENTO DE PROMESA DE ENTREGA")
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("💡 **Espacio reservado para la Pestaña 3.** Aquí podrás agregar contenido adicional de manera totalmente independiente.")
            # AQUÍ PUEDES EMPEZAR A INSERTAR TU CONTENIDO PARA LA PESTAÑA 3

        # ----------------------------------------------------------
        # TAB 4: PESTAÑA 4 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab4:
            render_subtitulo("RANKING DE FLETERAS // DESEMPEÑO Y PUNTUALIDAD")
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("💡 **Espacio reservado para la Pestaña 4.** Espacio libre y bien delimitado para nuevos componentes.")
            # AQUÍ PUEDES EMPEZAR A INSERTAR TU CONTENIDO PARA LA PESTAÑA 4

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
