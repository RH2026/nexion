import base64
from datetime import datetime
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
    "card": "#628290",
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
    
    def render_kpi(valor, total, titulo, color):
        porc = (valor / total * 100) if total > 0 else 0
        circunferencia = 238.76
        offset = circunferencia - (porc / 100 * circunferencia)
        
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-title">{titulo}</div>
                <div style="position: relative; width: 160px; height: 160px; display: flex; align-items: center; justify-content: center;">
                    <svg class="stat-circle" viewBox="0 0 100 100">
                        <circle class="stat-bg" cx="50" cy="50" r="38"></circle>
                        <circle class="stat-progress" cx="50" cy="50" r="38" 
                                style="stroke: {color}; 
                                       stroke-dasharray: {circunferencia}; 
                                       stroke-dashoffset: {offset};">
                        </circle>
                    </svg>
                    <div class="stat-value">{valor}</div>
                </div>
                <div class="stat-percent" style="color: {color};">{porc:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {vars_css['bg']} !important; }}
        .spacer-menu {{ margin-top: 30px; }}
        .metric-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 100%;
        }}
        .metric-title {{ color: #94a3b8; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; font-weight: 600; }}
        .stat-circle {{ transform: rotate(-90deg); width: 160px; height: 160px; overflow: visible; }}
        .stat-circle circle {{ fill: none; stroke-width: 15; }}
        .stat-bg {{ stroke: #2F3E45; }}
        .stat-progress {{ transition: stroke-dashoffset 0.8s ease-in-out; stroke-linecap: butt; }}
        .stat-value {{ position: absolute; color: white; font-size: 22px; font-weight: 800; top: 50%; left: 50%; transform: translate(-50%, -50%); }}
        .stat-percent {{ font-size: 16px; margin-top: 5px; font-weight: 700; }}
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
        # DEFINICIÓN DE LAS 5 PESTAÑAS (TABS) BIEN SEPARADAS
        # ==========================================================
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "KPIs", 
            "DISTRIBUCION DE CARGA", 
            "EFECTIVIDAD DE ENVIOS", 
            "RANKING DE FLETERAS",
            "COTIZADOR" 
        ])

        # ----------------------------------------------------------
        # TAB 1: KPIS (Donitas, Gráficos y el selector de Período integrado)
        # ----------------------------------------------------------
        with tab1:
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
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: render_kpi(total_p, total_p, "Pedidos", "#f6c23e")
            with c2: render_kpi(entregados, total_p, "Entregados", "#1cc88a")
            with c3: render_kpi(total_t, total_p, "Tránsito", "#4e73df")
            with c4: render_kpi(en_tiempo, total_p, "En Tiempo", "#36b9cc")
            with c5: render_kpi(retrasados, total_p, "Retraso", "#fb7185")
                    
            st.markdown("<br>", unsafe_allow_html=True)
        
            st.markdown(f"""
                <hr style="border: 0; height: 1px; background: {vars_css['border']}; margin: 40px 0; opacity: 0.3;">
                <div style="
                    color: {vars_css['sub']}; 
                    font-size: 14px; 
                    font-weight: 500; 
                    letter-spacing: 2px; 
                    margin-bottom: 20px; 
                    text-transform: uppercase;
                ">
                    Distribución de Carga actual
                </div>
            """, unsafe_allow_html=True)
            
            color_transito = "#36b9cc"
            color_retraso = "#fb7185"
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                df_t = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna() & (df_mes["PROMESA DE ENTREGA"] >= hoy_dt)].copy()
                df_t_count = df_t.groupby("FLETERA").size().reset_index(name="CANTIDAD")
                total_t_graf = df_t_count["CANTIDAD"].sum()
            
                st.markdown(f"""
                    <div style='background: linear-gradient(90deg, {color_transito}15 0%, transparent 100%); padding: 15px; border-radius: 4px; border-left: 4px solid {color_transito};'>
                        <p style='margin:0; color:{color_transito}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;'>🔵 En tránsito en tiempo</p>
                        <h2 style='margin:0; color:white; font-size:28px;'>{total_t_graf} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                    </div>
                """, unsafe_allow_html=True)
            
                import altair as alt
                if not df_t_count.empty:
                    h_t = len(df_t_count) * 35 + 50
                    chart_t = alt.Chart(df_t_count).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=18, color=color_transito).encode(
                        x=alt.X("CANTIDAD:Q", title=None, axis=None),
                        y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='#94a3b8', labelFontSize=11))
                    )
                    text_t = chart_t.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700).encode(text="CANTIDAD:Q")
                    st.altair_chart((chart_t + text_t).properties(height=h_t).configure_view(strokeOpacity=0), use_container_width=True)
                else:
                    st.markdown("<div style='padding:20px; color:#475569; font-size:12px;'>Sin carga en tránsito</div>", unsafe_allow_html=True)
            
            with col_graf2:
                df_r = df_mes[df_mes["FECHA DE ENTREGA REAL"].isna() & (df_mes["PROMESA DE ENTREGA"] < hoy_dt)].copy()
                df_r_count = df_r.groupby("FLETERA").size().reset_index(name="CANTIDAD")
                total_r_graf = df_r_count["CANTIDAD"].sum()
            
                st.markdown(f"""
                    <div style='background: linear-gradient(90deg, {color_retraso}15 0%, transparent 100%); padding: 15px; border-radius: 4px; border-left: 4px solid {color_retraso};'>
                        <p style='margin:0; color:{color_retraso}; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;'>🔴 En tránsito con Retraso</p>
                        <h2 style='margin:0; color:white; font-size:28px;'>{total_r_graf} <span style='font-size:14px; color:#94a3b8;'>pedidos</span></h2>
                    </div>
                """, unsafe_allow_html=True)
            
                if not df_r_count.empty:
                    h_r = len(df_r_count) * 35 + 50
                    chart_r = alt.Chart(df_r_count).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, size=18, color=color_retraso).encode(
                        x=alt.X("CANTIDAD:Q", title=None, axis=None),
                        y=alt.Y("FLETERA:N", title=None, sort='-x', axis=alt.Axis(labelColor='#94a3b8', labelFontSize=11))
                    )
                    text_r = chart_r.mark_text(align='left', baseline='middle', dx=8, color='white', fontWeight=700).encode(text="CANTIDAD:Q")
                    st.altair_chart((chart_r + text_r).properties(height=h_r).configure_view(strokeOpacity=0), use_container_width=True)
                else:
                    st.markdown("<div style='padding:20px; color:#00FFAA; font-size:12px; font-weight:bold;'>✓ Todo entregado a tiempo</div>", unsafe_allow_html=True)

        # ----------------------------------------------------------
        # TAB 2: PESTAÑA 2 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab2:
            st.write("") 
             
        # ----------------------------------------------------------
        # TAB 3: PESTAÑA 3 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("💡 **Espacio reservado para la Pestaña 3.** Aquí podrás agregar contenido adicional de manera totalmente independiente.")
            # AQUÍ PUEDES EMPEZAR A INSERTAR TU CONTENIDO PARA LA PESTAÑA 3

        # ----------------------------------------------------------
        # TAB 4: PESTAÑA 4 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab4:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("💡 **Espacio reservado para la Pestaña 4.** Espacio libre y bien delimitado para nuevos componentes.")
            # AQUÍ PUEDES EMPEZAR A INSERTAR TU CONTENIDO PARA LA PESTAÑA 4

        # ----------------------------------------------------------
        # TAB 5: PESTAÑA 5 (Espacio reservado para futuro contenido)
        # ----------------------------------------------------------
        with tab5:
            st.write("") 
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

