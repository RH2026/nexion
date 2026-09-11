from datetime import datetime, date
import os
import pytz
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Alertas y Excepciones",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="SEGUIMIENTO", submodulo_actual="ALERTAS")

# ============================================================
# 3. LÓGICA DE NEGOCIO Y DATOS (ALERTAS)
# ============================================================

# Variables de estilo y zona horaria
vars_css = {"sub": "#A4B9C8"}
tz_gdl = pytz.timezone('America/Mexico_City')
hoy_gdl = datetime.now(tz_gdl)

# Variable de control para simular si es de atención 3G o general (ajustar según tu sesión)
es_atencion3g = st.session_state.get("es_atencion3g", False)

# Carga de base de datos de seguimiento (asegura que el archivo CSV exista o se ajuste a tu entorno)
@st.cache_data
def load_seguimiento():
    ruta = os.path.join(os.getcwd(), "seguimiento.csv")
    if not os.path.exists(ruta):
        ruta = os.path.join(os.getcwd(), "..", "seguimiento.csv")
    try:
        return pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig')
    except:
        return pd.DataFrame()

df_seguimiento = load_seguimiento()

# 1. FILTROS DE CABECERA
with st.container():
    st.write("")
    f_col1, f_col2, f_col3 = st.columns([1, 1.5, 1.5], vertical_alignment="bottom")
    
    with f_col2:
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        mes_sel = st.selectbox("MES OPERATIVO", meses, index=hoy_gdl.month - 1)
        mes_num = meses.index(mes_sel) + 1
    
    with f_col1:
        inicio_m = date(hoy_gdl.year, mes_num, 1)
        
        if mes_num == 12:
            fin_m = date(hoy_gdl.year, 12, 31)
        else:
            fin_m = date(hoy_gdl.year, mes_num + 1, 1) - pd.Timedelta(days=1)
        
        # Aseguramos que fin_m sea objeto date puro de forma segura
        if isinstance(fin_m, datetime):
            fin_m_final = fin_m.date()
        elif hasattr(fin_m, 'date') and callable(fin_m.date):
            fin_m_final = fin_m.date()
        else:
            fin_m_final = fin_m
        
        rango_fechas = st.date_input(
            "RANGO DE ANÁLISIS",
            value=(inicio_m, min(hoy_gdl.date(), fin_m_final)),
            format="DD/MM/YYYY"
        )
    
    with f_col3:
        opciones_raw = sorted(df_seguimiento["FLETERA"].unique()) if not df_seguimiento.empty and "FLETERA" in df_seguimiento.columns else []
        
        if es_atencion3g:
            opciones_f = ["TRES GUERRAS"]
            indice_defecto = 0
            habilitado = False
        else:
            opciones_f = ["TODOS"] + opciones_raw
            indice_defecto = 0
            habilitado = True
        
        filtro_global_fletera = st.selectbox(
            "FILTRAR PAQUETERÍA", 
            options=opciones_f, 
            index=indice_defecto,
            disabled=not habilitado
        )

# ── 2. PROCESAMIENTO DE DATOS KPI ──
df_kpi = df_seguimiento.copy() if not df_seguimiento.empty else pd.DataFrame(columns=["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL", "FLETERA"])
df_kpi.columns = [str(c).upper() for c in df_kpi.columns]

for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
    if col in df_kpi.columns:
        df_kpi[col] = pd.to_datetime(df_kpi[col], dayfirst=True, errors='coerce')

# A. Filtrado por rango de fechas
if not df_kpi.empty and "FECHA DE ENVÍO" in df_kpi.columns:
    df_kpi = df_kpi.dropna(subset=["FECHA DE ENVÍO"])
    if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
        df_kpi = df_kpi[(df_kpi["FECHA DE ENVÍO"].dt.date >= rango_fechas[0]) & 
                        (df_kpi["FECHA DE ENVÍO"].dt.date <= rango_fechas[1])]

# B. Filtrado por fletera
if filtro_global_fletera != "TODOS" and "FLETERA" in df_kpi.columns:
    df_kpi = df_kpi[df_kpi["FLETERA"] == filtro_global_fletera]
    
# C. Identificación de "En Tránsito" y Cálculo de Atrasos
if not df_kpi.empty and 'FECHA DE ENTREGA REAL' in df_kpi.columns:
    df_kpi['ESTATUS_CALCULADO'] = df_kpi['FECHA DE ENTREGA REAL'].apply(lambda x: 'ENTREGADO' if pd.notna(x) else 'EN TRANSITO')
    df_sin_entregar = df_kpi[df_kpi['ESTATUS_CALCULADO'] == 'EN TRANSITO'].copy()
else:
    df_sin_entregar = pd.DataFrame()

if not df_sin_entregar.empty and "PROMESA DE ENTREGA" in df_sin_entregar.columns:
    df_sin_entregar["DIAS_ATRASO"] = (pd.Timestamp(hoy_gdl.date()) - df_sin_entregar["PROMESA DE ENTREGA"]).dt.days
    df_sin_entregar["DIAS_ATRASO"] = df_sin_entregar["DIAS_ATRASO"].apply(lambda x: x if (pd.notna(x) and x > 0) else 0)
    df_sin_entregar["DIAS_TRANS"] = (pd.Timestamp(hoy_gdl.date()) - df_sin_entregar["FECHA DE ENVÍO"]).dt.days
else:
    if not df_sin_entregar.empty:
        df_sin_entregar["DIAS_ATRASO"] = 0
        df_sin_entregar["DIAS_TRANS"] = 0

# D. Lógica para el PRÓXIMO MES
proximo_mes_num = mes_num + 1 if mes_num < 12 else 1
anio_proximo = hoy_gdl.year if mes_num < 12 else hoy_gdl.year + 1
nombre_prox_mes = meses[proximo_mes_num - 1]

df_full = df_seguimiento.copy() if not df_seguimiento.empty else pd.DataFrame()
if not df_full.empty:
    df_full.columns = [str(c).upper() for c in df_full.columns]
    if "PROMESA DE ENTREGA" in df_full.columns:
        fechas_promesa = pd.to_datetime(df_full["PROMESA DE ENTREGA"], dayfirst=True, errors='coerce')
        conteo_proximo = len(df_full[(fechas_promesa.dt.month == proximo_mes_num) & (fechas_promesa.dt.year == anio_proximo)])
    else:
        conteo_proximo = 0
else:
    conteo_proximo = 0

# E. Métricas Finales
total_p = len(df_kpi)
pend_p = len(df_sin_entregar)
entregados_v = len(df_kpi[df_kpi['ESTATUS_CALCULADO'] == 'ENTREGADO']) if not df_kpi.empty and 'ESTATUS_CALCULADO' in df_kpi.columns else 0
eficiencia = (entregados_v / total_p * 100) if total_p > 0 else 0

# Estilo para tarjetas de alerta
st.markdown("""
    <style>
    .base-card-alerta {
        background-color: #1A252F;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #38bdf8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    </style>
""", unsafe_allow_html=True)

# ── 4. SEMÁFORO DE ALERTAS ──
st.markdown(f"<div style='margin-top:40px; margin-bottom:15px; text-align:center;'><span style='color:{vars_css['sub']}; font-size:10px; font-weight:800; letter-spacing:4px; opacity:0.6; text-transform:uppercase;'>S E M Á F O R O &nbsp; D E &nbsp; A L E R T A S</span></div>", unsafe_allow_html=True)

a1_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] == 1]) if not df_sin_entregar.empty and "DIAS_ATRASO" in df_sin_entregar.columns else 0
a2_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"].between(2,4)]) if not df_sin_entregar.empty and "DIAS_ATRASO" in df_sin_entregar.columns else 0
a5_v = len(df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] >= 5]) if not df_sin_entregar.empty and "DIAS_ATRASO" in df_sin_entregar.columns else 0

c_a1, c_a2, c_a3 = st.columns(3)

# Alerta LEVE (Amarillo Neón)
c_a1.markdown(f"""
    <div class='base-card-alerta' style='border-left-color: #FDE047;'>
        <div style='color: rgba(255,255,255,0.4); font-size: 12px; font-weight: 800; letter-spacing: 1px;'>BAJO RIESGO (1D)</div>
        <div style='color: white; font-size: 28px; font-weight: 800; line-height: 1;'>{a1_v} <span style='font-size: 10px; color: #FDE047; opacity: 0.7;'>PEDIDOS</span></div>
    </div>
""", unsafe_allow_html=True)

# Alerta MODERADO (Naranja Eléctrico)
c_a2.markdown(f"""
    <div class='base-card-alerta' style='border-left-color: #F97316;'>
        <div style='color: rgba(255,255,255,0.4); font-size: 12px; font-weight: 800; letter-spacing: 1px;'>DEMORA (2-4D)</div>
        <div style='color: white; font-size: 28px; font-weight: 800; line-height: 1;'>{a2_v} <span style='font-size: 10px; color: #F97316; opacity: 0.7;'>PEDIDOS</span></div>
    </div>
""", unsafe_allow_html=True)

# Alerta CRÍTICO (Rojo Intenso)
c_a3.markdown(f"""
    <div class='base-card-alerta' style='border-left-color: #FF4B4B;'>
        <div style='color: rgba(255,255,255,0.4); font-size: 12px; font-weight: 800; letter-spacing: 1px;'>CRÍTICO (+5D)</div>
        <div style='color: white; font-size: 28px; font-weight: 800; line-height: 1;'>{a5_v} <span style='font-size: 10px; color: #FF4B4B; opacity: 0.7;'>PEDIDOS</span></div>
    </div>
""", unsafe_allow_html=True)

# --- 5. PANEL DE EXCEPCIONES (DISEÑO WAR ROOM) ---
st.divider()
df_criticos = df_sin_entregar[df_sin_entregar["DIAS_ATRASO"] > 0].copy() if not df_sin_entregar.empty and "DIAS_ATRASO" in df_sin_entregar.columns else pd.DataFrame()
df_viz = pd.DataFrame()

if not df_criticos.empty:
    st.markdown(f"""<p style='font-size:11px; font-weight:700; letter-spacing:8px; color:#FFFFFF; text-transform:uppercase; text-align:center; margin-bottom:20px;'>PANEL DE EXCEPCIONES CRÍTICAS</p>""", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: 
        lista_fleteras = ["TODOS"] + sorted(df_criticos["FLETERA"].unique()) if "FLETERA" in df_criticos.columns else ["TODOS"]
        sel_f = st.selectbox("TRANSPORTISTA:", options=lista_fleteras, key="f_critico_v2")
    with c2: 
        sel_g = st.selectbox("GRAVEDAD ATRASO:", ["TODOS", "CRÍTICO (+5 DÍAS)", "MODERADO (2-4 DÍAS)", "LEVE (1 DÍA)"], key="g_critico_v2")
    
    df_viz = df_criticos.copy()
    if sel_f != "TODOS" and "FLETERA" in df_viz.columns: df_viz = df_viz[df_viz["FLETERA"] == sel_f]
    if sel_g == "CRÍTICO (+5 DÍAS)": df_viz = df_viz[df_viz["DIAS_ATRASO"] >= 5]
    elif sel_g == "MODERADO (2-4 DÍAS)": df_viz = df_viz[df_viz["DIAS_ATRASO"].between(2, 4)]
    elif sel_g == "LEVE (1 DÍA)": df_viz = df_viz[df_viz["DIAS_ATRASO"] == 1]

    if not df_viz.empty:
        df_viz = df_viz.sort_values("DIAS_ATRASO", ascending=False)
        data_excepciones = df_viz.to_dict('records')
        
        html_excepciones = f"""
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
                    border: 1px solid rgba(255, 75, 75, 0.15);
                    border-left: 6px solid #FF4B4B;
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
                    border-color: #FF4B4B; 
                    background: #2d3b42;
                    transform: translateX(5px);
                }}
                .badge-retraso {{
                    background: rgba(255, 75, 75, 0.1);
                    color: #FF4B4B;
                    padding: 10px 18px;
                    border-radius: 10px;
                    font-weight: 800;
                    font-family: monospace;
                    font-size: 22px;
                    text-align: center;
                    min-width: 90px;
                    border: 1px solid rgba(255, 75, 75, 0.3);
                }}
                .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }}
                .factura-destacada {{ color: #FFFFFF; font-size: 19px; font-weight: 800; letter-spacing: 1px; font-family: monospace; }}
                .info-main {{ color: #FFFFFF; font-size: 14px; font-weight: 700; }}
                .info-sub {{ color: #FFFFFF; font-size: 11px; font-style: italic; }}
                .moderado {{ border-left-color: #FFA500; border-color: rgba(255, 165, 0, 0.2); }}
                .badge-moderado {{ color: #FFA500; background: rgba(255, 165, 0, 0.1); border-color: rgba(255, 165, 0, 0.3); }}
                @media (max-width: 600px) {{
                    .card-excepcion {{ padding: 15px; }}
                    .section-box {{ border-left: none !important; padding-left: 0 !important; min-width: 100% !important; }}
                    .badge-retraso {{ width: 100%; }}
                }}
            </style>
            {"".join([f'''
            <div class="card-excepcion {'moderado' if item['DIAS_ATRASO'] < 5 else ''}">
                <div class="section-box" style="flex: 1.5; min-width: 200px;">
                    <div class="label-mini">No. Factura / Pedido</div>
                    <div class="factura-destacada">{item.get('NÚMERO DE PEDIDO', 'N/A')}</div>
                    <div class="info-sub" style="margin-top:5px;">Cliente: {str(item.get('NOMBRE DEL CLIENTE', ''))[:35]}</div>
                </div>
                
                <div class="section-box" style="flex: 1.5; min-width: 180px; padding: 0 15px; border-left: 1px solid rgba(255,255,255,0.05);">
                    <div class="label-mini">Transporte / Estatus</div>
                    <div class="info-main" style="color:#38bdf8;">{item.get('FLETERA', 'N/A')}</div>
                    <div class="info-sub" style="color: #FFFFFF !important;">Guía: {item.get('NÚMERO DE GUÍA') if item.get('NÚMERO DE GUÍA') else 'SIN ASIGNAR'}</div>
                </div>
                
                <div class="section-box" style="flex: 1.2; min-width: 150px; text-align: left; padding: 0 15px; border-left: 1px solid rgba(255,255,255,0.05);">
                    <div class="label-mini">Días en Ruta</div>
                    <div class="info-main" style="margin-bottom: 5px;">{item.get('DIAS_TRANS', 0)} d.</div>
                    <div class="label-mini" style="font-size: 7px; color: #FFA500;">P. Entrega</div>
                    <div class="info-sub" style="font-size: 10px; font-style: normal;">{item.get('PROMESA DE ENTREGA').strftime('%d/%m/%Y') if hasattr(item.get('PROMESA DE ENTREGA'), 'strftime') else item.get('PROMESA DE ENTREGA', '')}</div>
                </div>
                
                <div style="flex: 0.5; min-width: 100px;">
                    <div class="label-mini" style="text-align:center;">Retraso</div>
                    <div class="badge-retraso {'badge-moderado' if item['DIAS_ATRASO'] < 5 else ''}">+{item['DIAS_ATRASO']}</div>
                </div>
            </div>
            ''' for item in data_excepciones])}
        </div>
        """
        components.html(html_excepciones, height=700, scrolling=True)
    else:
        st.markdown(f"""
            <div style="background-color: rgba(56, 189, 248, 0.1); border: 1px dashed #38bdf8; border-radius: 10px; padding: 20px; text-align: center;">
                <p style="color: #38bdf8; font-size: 18px; margin: 0;"><b>BÚSQUEDA SIN RESULTADOS</b></p>
                <p style="color: #94a3b8; font-size: 12px; margin-top: 5px; letter-spacing: 1px;">
                    No detectamos pedidos activos bajo los criterios seleccionados. Verifica tus filtros de Transportista o Gravedad.
                </p>
            </div>
        """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, rgba(0,255,170,0.1) 0%, rgba(0,0,0,0) 100%); border-left: 5px solid #00FFAA; border-radius: 5px; padding: 25px; margin: 20px 0;">
            <h3 style="color: #00FFAA; margin: 0; font-size: 20px; letter-spacing: 2px;">✓ STATUS: OPERACIÓN LIMPIA</h3>
            <p style="color: #FFFFFF; font-size: 14px; margin-top: 8px; opacity: 0.8;">
                <b>SISTEMA NEXION:</b> No se detectaron anomalías ni entregas fuera de tiempo en el rango analizado. Todo fluye conforme a lo planeado.
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- 6. BOTÓN DE DESCARGA: EXCEPCIONES Y RETRASOS ---
st.divider()

if 'df_viz' in locals() and not df_viz.empty:
    import io

    df_reporte = df_viz.copy()
    columnas_excel = ["NÚMERO DE PEDIDO", "NOMBRE DEL CLIENTE", "FLETERA", "NÚMERO DE GUÍA", "DIAS_TRANS", "DIAS_ATRASO", "FECHA DE ENVÍO", "PROMESA DE ENTREGA"]
    columnas_existentes = [c for c in columnas_excel if c in df_reporte.columns]
    
    for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA"]:
        if col in df_reporte.columns:
            df_reporte[col] = pd.to_datetime(df_reporte[col], errors='coerce').dt.strftime('%d/%m/%Y')

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_reporte[columnas_existentes].to_excel(writer, index=False, sheet_name='Retrasos_Criticos')
        
    buffer.seek(0)

    st.markdown(f"""<p style='font-size:11px; font-weight:700; letter-spacing:3px; color:#38bdf8; text-transform:uppercase; text-align:center; margin-bottom:10px;'>REPORTE DE EXCEPCIONES DETECTADAS</p>""", unsafe_allow_html=True)
    
    st.download_button(
        label="DESCARGAR DETALLE DE RETRASOS (EXCEL)",
        data=buffer,
        file_name=f"Reporte_Retrasos_Nexion_{mes_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="btn_descarga_excel_retrasos"
    )
    
    st.markdown(f"<p style='color:#94a3b8; font-size:10px; text-align:center;'>Se exportarán {len(df_viz)} registros con anomalías en la entrega.</p>", unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 30px; text-align: center; margin-top: 20px;">
            <h4 style="color: #FFFFFF; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 0;">ARCHIVO DE EXPORTACIÓN NO DISPONIBLE</h4>
            <p style="color: #64748b; font-size: 12px; margin-top: 10px; line-height: 1.6;">
                <b>SISTEMA NEXION:</b> No se han generado excepciones críticas en el filtro actual.<br>
                El reporte de descarga se habilitará automáticamente cuando se detecten anomalías.
            </p>
            <div style="display: inline-block; margin-top: 15px; padding: 4px 12px; background: rgba(0, 255, 170, 0.1); border-radius: 20px;">
                <span style="color: #00FFAA; font-size: 10px; font-weight: 800; letter-spacing: 1px;">✓ OPERACIÓN SIN INCIDENCIAS</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
