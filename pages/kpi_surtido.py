import base64
from datetime import datetime, timedelta
import io
import time
import requests
import pandas as pd
import streamlit as st
import pytz
import plotly.express as px
import plotly.graph_objects as go

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | KPI de Surtido y Envíos",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="KPI SURTIDO", submodulo_actual="ANALITICA")

# ============================================================
# 3. FUNCIONES DE CARGA DE DATOS MAESTRA Y FUENTES AUXILIARES
# ============================================================
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

# ============================================================
# 4. INTERFAZ PRINCIPAL DEL KPI DASHBOARD
# ============================================================
def main():
    tz_gdl = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(tz_gdl)
    hoy_gdl = ahora.date()

    # Título y Reloj Sincronizado en GDL
    col_titulo, col_indicador = st.columns([4, 1.8], vertical_alignment="center")
    
    with col_titulo:
        st.markdown(
            """
            <div style="text-align:left; margin-top:15px; margin-bottom:10px;">
                <span style="color:#FFFFFF; font-weight:600; font-size:14px; letter-spacing:3px;">
                    DASHBOARD EJECUTIVO // KPI DE SURTIDO Y ENVÍOS
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_indicador:
        fecha_str = ahora.strftime("%d/%m/%Y")
        hora_str = ahora.strftime("%H:%M:%S")

        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-top: 15px; margin-bottom: 10px; padding: 6px 12px; background: #182229; border: 1px solid #34495E; border-radius: 6px;">
                <div style="width: 6px; height: 6px; background: #00FFAA; border-radius: 50%; box-shadow: 0 0 8px #00FFAA;"></div>
                <span style="color: #8B9BB4; font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">Sync GDL:</span>
                <span style="color: #E8EEF2; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">{fecha_str} &bull; <span style="color:#00FFAA;">{hora_str}</span></span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with st.spinner("🔄 Conectando con bases remotas y cruzando guías y métricas de surtido..."):
        df_raw = cargar_datos_envios()
        df_dashboard_global = cargar_datos_dashboard_global()
        
        df_t1_global = pd.DataFrame()
        try:
            df_t1_global = pd.read_excel("T1.xlsx")
            df_t1_global.columns = df_t1_global.columns.str.strip().str.upper()
        except Exception:
            pass

    if df_raw.empty:
        st.warning("No se encontraron registros en la base de datos de envíos.")
        return

    df_raw.columns = df_raw.columns.str.strip()

    # Normalización de estructura base
    df_envios = pd.DataFrame()
    df_envios['factura'] = df_raw.get('Factura', pd.Series(dtype=str)).fillna('').astype(str)
    df_envios['recomendacion'] = df_raw.get('RECOMENDACION', pd.Series(dtype=str)).fillna('SIN ASIGNAR').astype(str)
    df_envios['nombre_cliente'] = df_raw.get('Nombre_Cliente', df_raw.get('Nombre_Extran', pd.Series(dtype=str))).fillna('').astype(str)
    df_envios['destino'] = df_raw.get('DESTINO', pd.Series(dtype=str)).fillna('NACIONAL').astype(str)
    
    f_prog_input = df_raw.get('FECHA DE PROGRAMACION', pd.Series(dtype=str)).fillna('').astype(str).str.strip()
    dt_prog_temp = pd.to_datetime(f_prog_input, errors='coerce', dayfirst=True)
    df_envios['fecha_programacion'] = dt_prog_temp.dt.strftime('%d/%m/%Y').fillna(f_prog_input)
    df_envios['dt_prog_parsed'] = dt_prog_temp

    # ============================================================
    # 5. EXTRACCIÓN ROBUSTA DE GUÍAS Y FECHAS (CRUCE MULTI-FUENTE)
    # ============================================================
    lista_guias = []
    lista_fechas_envio = []
    f_env_raw_list = df_raw.get('FECHA DE ENVIO', pd.Series(dtype=str)).fillna('').astype(str).str.strip()

    for idx, row in df_raw.iterrows():
        fac = str(row.get('Factura', '')).strip()
        guia_encontrada = ""
        fecha_envio_encontrada = ""
        
        # 1. Buscar en df_raw (envios.csv)
        for col_g in ['NÚMERO DE GUÍA', 'NUMERO DE GUIA', 'GUIA', 'TALON', 'Nro Guia']:
            if col_g in df_raw.columns and pd.notna(row.get(col_g)):
                val_g = str(row.get(col_g)).strip()
                if val_g and val_g.lower() not in ['', 'nan', '0', '0.0', 'none']:
                    guia_encontrada = val_g
                    break
        
        # 2. Si no hay guía, buscar en Matriz_Excel_Dashboard.csv
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

        # 3. Si aún no hay guía, buscar en T1.xlsx
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
        fp = str(row['fecha_programacion']).strip()
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
            elif not tiene_fe and not tiene_g and ahora.replace(tzinfo=None) > limite:
                tarde = True

        if tiene_g and tiene_fe:
            estatus_calculado.append("SURTIDA / EN TIEMPO" if not tarde else "CON RETRASO")
        elif not tiene_g and not tiene_fe:
            estatus_calculado.append("PENDIENTE / SURTIENDO")
        else:
            estatus_calculado.append("ENVIADA PARCIAL")

    df_envios['estatus'] = estatus_calculado

    # ============================================================
    # 6. FILTROS TÁCTICOS AVANZADOS (CON FECHA DE PROGRAMACIÓN)
    # ============================================================
    st.markdown("<div style='font-size: 11px; font-weight: 800; color: #8B9BB4; letter-spacing: 1px; margin-bottom: 8px;'>FILTROS DE ANÁLISIS</div>", unsafe_allow_html=True)
    
    f1, f2, f3, f4, f5 = st.columns(5)
    
    with f1:
        # Por defecto muestra el día de hoy pero permite seleccionarlo/limpiarlo
        filtro_fprog = st.date_input("FECHA PROGRAMACIÓN", value=hoy_gdl, key="kpi_filtro_fprog")

    with f2:
        facturas_opts = ["TODAS"] + sorted(list(df_envios['factura'].loc[df_envios['factura'] != ''].unique()))
        filtro_factura = st.selectbox("FACTURA", facturas_opts, key="kpi_filtro_factura")

    with f3:
        paq_opts = ["TODAS"] + sorted(list(df_envios['recomendacion'].loc[df_envios['recomendacion'] != ''].unique()))
        filtro_paqueteria = st.selectbox("PAQUETERÍA", paq_opts, key="kpi_filtro_paq")

    with f4:
        estatus_opts = ["TODOS"] + sorted(list(df_envios['estatus'].unique()))
        filtro_estatus = st.selectbox("ESTATUS DE SURTIDO", estatus_opts, key="kpi_filtro_estatus")

    with f5:
        rango_dias = st.selectbox("VENTANA", ["Día Actual", "Últimos 7 días", "Histórico Completo"], index=0, key="kpi_filtro_ventana")

    # Aplicar filtros
    df_filtrado = df_envios.copy()
    
    if filtro_fprog is not None:
        df_filtrado = df_filtrado[df_filtrado['dt_prog_parsed'].dt.date == filtro_fprog]

    if filtro_factura != "TODAS":
        df_filtrado = df_filtrado[df_filtrado['factura'] == filtro_factura]
        
    if filtro_paqueteria != "TODAS":
        df_filtrado = df_filtrado[df_filtrado['recomendacion'] == filtro_paqueteria]
        
    if filtro_estatus != "TODOS":
        df_filtrado = df_filtrado[df_filtrado['estatus'] == filtro_estatus]
        
    if rango_dias == "Día Actual":
        df_filtrado = df_filtrado[df_filtrado['dt_prog_parsed'].dt.date == hoy_gdl]
    elif rango_dias == "Últimos 7 días":
        hace_7 = hoy_gdl - timedelta(days=7)
        df_filtrado = df_filtrado[(df_filtrado['dt_prog_parsed'].dt.date >= hace_7) | (df_filtrado['dt_prog_parsed'].isna())]

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 7. CÁLCULO DE KPIs EJECUTIVOS
    # ============================================================
    total_facturas = len(df_filtrado)
    hoy_str = ahora.strftime('%d/%m/%Y')
    
    enviadas_hoy = len(df_filtrado[df_filtrado['fecha_envio'] == hoy_str])
    surtidas_tiempo = len(df_filtrado[df_filtrado['estatus'] == "SURTIDA / EN TIEMPO"])
    con_retraso = len(df_filtrado[df_filtrado['estatus'] == "CON RETRASO"])
    pendientes = len(df_filtrado[df_filtrado['estatus'].str.contains("PENDIENTE", na=False)])
    
    porcentaje_exito = (surtidas_tiempo / total_facturas * 100) if total_facturas > 0 else 0

    # Render de Tarjetas KPI
    kpi_cols = st.columns(5)
    
    with kpi_cols[0]:
        st.markdown(f"""
            <div style="background: #182229; border: 1px solid #34495E; padding: 14px; border-radius: 8px; text-align: center;">
                <div style="color: #8B9BB4; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Facturas Totales</div>
                <div style="color: #E8EEF2; font-size: 22px; font-weight: 800; margin-top: 4px;">{total_facturas}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[1]:
        st.markdown(f"""
            <div style="background: #182229; border: 1px solid rgba(0,255,170,0.3); padding: 14px; border-radius: 8px; text-align: center;">
                <div style="color: #00FFAA; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Se Fueron Hoy</div>
                <div style="color: #00FFAA; font-size: 22px; font-weight: 800; margin-top: 4px;">{enviadas_hoy}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[2]:
        st.markdown(f"""
            <div style="background: #182229; border: 1px solid #34495E; padding: 14px; border-radius: 8px; text-align: center;">
                <div style="color: #8B9BB4; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Sí Surtidas</div>
                <div style="color: #FFD166; font-size: 22px; font-weight: 800; margin-top: 4px;">{surtidas_tiempo}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[3]:
        st.markdown(f"""
            <div style="background: #182229; border: 1px solid rgba(255,75,75,0.3); padding: 14px; border-radius: 8px; text-align: center;">
                <div style="color: #FF6B6B; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Con Retraso / Pend.</div>
                <div style="color: #FF6B6B; font-size: 22px; font-weight: 800; margin-top: 4px;">{con_retraso + pendientes}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[4]:
        st.markdown(f"""
            <div style="background: #182229; border: 1px solid #34495E; padding: 14px; border-radius: 8px; text-align: center;">
                <div style="color: #8B9BB4; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">Efectividad</div>
                <div style="color: #00FFAA; font-size: 22px; font-weight: 800; margin-top: 4px;">{porcentaje_exito:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 8. GRÁFICAS DE DONA INTERACTIVAS (PLOTLY)
    # ============================================================
    if not df_filtrado.empty:
        col_c1, col_c2 = st.columns(2)

        config_layout = {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#E8EEF2", "family": "Inter, sans-serif", "size": 11},
            "margin": {"t": 20, "b": 10, "l": 10, "r": 10},
            "legend": {"orientation": "h", "y": -0.15}
        }

        with col_c1:
            st.markdown("<div style='font-size: 11px; font-weight: 800; color: #8B9BB4; letter-spacing: 1px; margin-bottom: 5px;'>DISTRIBUCIÓN POR ESTATUS DE SURTIDO</div>", unsafe_allow_html=True)
            df_estatus_counts = df_filtrado['estatus'].value_counts().reset_index()
            df_estatus_counts.columns = ['Estatus', 'Cantidad']
            
            fig_donita1 = px.pie(
                df_estatus_counts, 
                names='Estatus', 
                values='Cantidad', 
                hole=0.6,
                color_discrete_sequence=['#00FFAA', '#FFD166', '#FF6B6B', '#3B82F6']
            )
            fig_donita1.update_traces(textposition='inside', textinfo='percent+value')
            fig_donita1.update_layout(**config_layout)
            st.plotly_chart(fig_donita1, use_container_width=True, config={'displayModeBar': False})

        with col_c2:
            st.markdown("<div style='font-size: 11px; font-weight: 800; color: #8B9BB4; letter-spacing: 1px; margin-bottom: 5px;'>VOLUMEN OPERATIVO POR PAQUETERÍA</div>", unsafe_allow_html=True)
            df_paq_counts = df_filtrado['recomendacion'].value_counts().reset_index()
            df_paq_counts.columns = ['Paquetería', 'Cantidad']
            
            fig_donita2 = px.pie(
                df_paq_counts, 
                names='Paquetería', 
                values='Cantidad', 
                hole=0.6,
                color_discrete_sequence=['#00A3A3', '#3B82F6', '#8B5CF6', '#EC4899', '#64748B']
            )
            fig_donita2.update_traces(textposition='inside', textinfo='percent+value')
            fig_donita2.update_layout(**config_layout)
            st.plotly_chart(fig_donita2, use_container_width=True, config={'displayModeBar': False})

    # ============================================================
    # 9. TABLA DE PEDIDOS CON ENCABEZADO STICKY
    # ============================================================
    st.markdown("<div style='font-size: 11px; font-weight: 800; color: #8B9BB4; letter-spacing: 1px; margin-top: 15px; margin-bottom: 8px;'>DETALLE DE PEDIDOS Y SURTIDO</div>", unsafe_allow_html=True)

    sorted_table_data = df_filtrado.sort_values(by='factura', ascending=False).to_dict('records')

    if not sorted_table_data:
        st.info("No hay registros para mostrar con los filtros seleccionados.")
        return

    html_table = '<div class="envios-premium-wrap"><div class="envios-premium-scroll"><table class="envios-premium-table"><thead><tr>'
    columnas = ["FACTURA", "PAQUETERÍA", "NO. GUÍA", "F. PROGRAMACIÓN", "CLIENTE", "DESTINO", "FECHA ENVÍO", "ESTATUS"]

    for col in columnas:
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

if __name__ == "__main__":
    main()
