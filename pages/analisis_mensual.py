from datetime import datetime, timedelta
import os
import pytz
import unicodedata
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Análisis Mensual",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="REPORTES", submodulo_actual="ANALISIS MENSUAL")

# ============================================================
# 3. LÓGICA DE NEGOCIO Y DATOS
# ============================================================

# --- 1. MOTOR DE DATOS NIVEL ELITE (JERARQUÍA Y FLECHAS EN DELTAS) ---
st.markdown("""
<style>
.main { background-color: #070B0E; }

/* Tarjetas con diseño esmeralda y moderno */
.metric-card {
    background: linear-gradient(135deg, rgba(20, 35, 45, 0.8) 0%, rgba(12, 22, 30, 0.95) 100%);
    padding: 20px 22px;
    border-radius: 16px;
    border: 1px solid rgba(0, 255, 170, 0.3);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 170, 0.1);
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}
.metric-card:hover {
    border-color: #00FFAA;
    box-shadow: 0 10px 30px rgba(0, 255, 170, 0.25);
    transform: translateY(-3px);
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 5px;
    height: 100%;
    background: linear-gradient(180deg, #00FFAA 0%, #00B4D8 100%);
    box-shadow: 0 0 10px #00FFAA;
}
/* Etiqueta superior compacta */
.metric-label {
    color: #8398AB;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 6px;
}
/* Valor principal con tipografía contundente */
.metric-value {
    color: #FFFFFF;
    font-size: 1.8rem;
    font-weight: 900;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
    text-shadow: 0 2px 5px rgba(0,0,0,0.4);
}
/* Deltas grandes con indicadores de dirección claros */
.metric-delta {
    font-size: 0.9rem;
    font-weight: 800;
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    letter-spacing: 0.3px;
}
.delta-pos { color: #00FFAA; background: rgba(0, 255, 170, 0.15); border: 1px solid rgba(0, 255, 170, 0.35); }
.delta-neg { color: #FF5252; background: rgba(255, 82, 82, 0.15); border: 1px solid rgba(255, 82, 82, 0.35); }

h1 { color: #FFFFFF; font-family: 'Arial Black'; border-bottom: 2px solid #00FFAA; padding-bottom: 10px; }
h3 { color: #00FFAA; margin-top: 30px; font-family: 'Arial'; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px rgba(0,255,170,0.2); }
.analysis-box {
    background: linear-gradient(135deg, rgba(20, 35, 45, 0.9) 0%, rgba(12, 22, 30, 0.95) 100%);
    padding: 25px;
    border-radius: 16px;
    border: 1px solid rgba(0, 255, 170, 0.3);
    color: #C1D0DF;
    line-height: 1.8;
    font-size: 0.95rem;
    box-shadow: 0 8px 25px rgba(0,0,0,0.5);
}
.highlight { color: #00FFAA; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if 'ver_grafico' not in st.session_state:
    st.session_state.ver_grafico = False

def limpiar_columnas(txt):
    if not isinstance(txt, str): return txt
    texto = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    return texto.strip().upper()

def limpiar_dinero(col):
    return pd.to_numeric(
        col.astype(str)
        .str.replace('$', '', regex=False)
        .str.replace(',', '', regex=False)
        .str.strip(),
        errors='coerce'
    ).fillna(0)

# 2. CARGA Y PROCESAMIENTO A PRUEBA DE ERRORES
try:
    df_actual = pd.read_csv('Matriz_Excel_Dashboard.csv')
    df_2025 = pd.read_csv('Historial2025.csv')

    df_actual.columns = [limpiar_columnas(c) for c in df_actual.columns]
    df_2025.columns = [limpiar_columnas(c) for c in df_2025.columns]

    columnas_dinero = ['COSTO DE LA GUIA', 'FACTURACION', 'VALUACION', 'COSTOS ADICIONALES', 'CAJAS']
    for col in columnas_dinero:
        if col in df_actual.columns: 
            df_actual[col] = limpiar_dinero(df_actual[col])

    for col in ['COSTO DE LA GUIA', 'CAJAS']:
        if col in df_2025.columns: 
            df_2025[col] = limpiar_dinero(df_2025[col])

    for f_col in ['FECHA DE ENVIO', 'PROMESA DE ENTREGA', 'FECHA DE ENTREGA REAL']:
        if f_col in df_actual.columns:
            df_actual[f_col] = pd.to_datetime(df_actual[f_col], errors='coerce')

    df_actual['MES'] = df_actual['MES'].fillna("SIN MES").astype(str).str.strip().str.upper()
    df_2025['MES'] = df_2025['MES'].fillna("SIN MES").astype(str).str.strip().str.upper()

    if 'FORMA DE ENVIO' in df_actual.columns:
        df_gastos = df_actual[df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False)].copy()
    else:
        df_gastos = df_actual.copy()
        
    df_gastos['COSTOS ADICIONALES'] = limpiar_dinero(df_gastos.get('COSTOS ADICIONALES', 0))
    df_gastos['COSTO DE FLETE'] = df_gastos['COSTO DE LA GUIA'] + df_gastos['COSTOS ADICIONALES']
    
    # 3. INTERFAZ
    meses_nombres = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    mes_actual_txt = meses_nombres.get(datetime.now().month, "ENERO")
    opciones_mes = ["TODOS"] + sorted(df_gastos['MES'].unique().tolist())
    indice_def = opciones_mes.index(mes_actual_txt) if mes_actual_txt in opciones_mes else 0

    c_f1, c_f2 = st.columns(2)
    with c_f1: mes_sel = st.selectbox(":material/calendar_month: FILTRAR POR MES:", opciones_mes, index=indice_def)
    with c_f2: flet_sel = st.selectbox(":material/local_shipping: FILTRAR POR FLETERA:", ["TODAS"] + sorted(df_gastos['FLETERA'].unique().tolist()) if 'FLETERA' in df_gastos.columns else ["TODAS"])

    df_filtered = df_gastos.copy()
    if mes_sel != "TODOS": df_filtered = df_filtered[df_filtered['MES'] == mes_sel]
    if flet_sel != "TODAS" and 'FLETERA' in df_filtered.columns: df_filtered = df_filtered[df_filtered['FLETERA'] == flet_sel]

    # 4. CÁLCULOS PRINCIPALES
    mask_evaluable = df_filtered['PROMESA DE ENTREGA'].notna() & df_filtered['FECHA DE ENTREGA REAL'].notna()
    df_eval = df_filtered[mask_evaluable]
    pct_eficiencia = ( (df_eval['FECHA DE ENTREGA REAL'] <= df_eval['PROMESA DE ENTREGA']).sum() / len(df_eval) * 100 ) if len(df_eval) > 0 else 0

    total_flete_2026 = df_filtered['COSTO DE FLETE'].sum() if 'COSTO DE FLETE' in df_filtered.columns else 0
    total_fact_2026 = df_filtered['FACTURACION'].sum() if 'FACTURACION' in df_filtered.columns else 0
    total_cajas_2026 = df_filtered['CAJAS'].sum() if 'CAJAS' in df_filtered.columns else 0
    total_valuacion_2026 = df_filtered['VALUACION'].sum() if 'VALUACION' in df_filtered.columns else 0

    meses_activos = df_filtered['MES'].unique()
    df_2025_filtrado = df_2025[df_2025['MES'].isin(meses_activos)]
    total_flete_2025 = df_2025_filtrado['COSTO DE LA GUIA'].sum() if 'COSTO DE LA GUIA' in df_2025_filtrado.columns else 0
    total_cajas_2025 = df_2025_filtrado['CAJAS'].sum() if 'CAJAS' in df_2025_filtrado.columns else 0
    
    costo_caja_2026 = (total_flete_2026 / total_cajas_2026) if total_cajas_2026 > 0 else 0
    costo_caja_2025 = (total_flete_2025 / total_cajas_2025) if total_cajas_2025 > 0 else 0
    var_costo_caja = ((costo_caja_2026 - costo_caja_2025) / costo_caja_2025 * 100) if costo_caja_2025 > 0 else 0
    var_volumen = ((total_cajas_2026 - total_cajas_2025) / total_cajas_2025 * 100) if total_cajas_2025 > 0 else 0
    var_flete_total = ((total_flete_2026 - total_flete_2025) / total_flete_2025 * 100) if total_flete_2025 > 0 else 0
    costo_log_real = (total_flete_2026/total_fact_2026*100) if total_fact_2026 > 0 else 0
    diferencia_target = costo_log_real - 7.5
    num_inc = (df_filtered['VALUACION'] > 0).sum() if 'VALUACION' in df_filtered.columns else 0
    pct_inc = (num_inc/len(df_filtered)*100) if len(df_filtered)>0 else 0
    inc_vi_monto = (total_flete_2026 + total_valuacion_2026) - total_flete_2025
    
    total_valuacion_2025 = df_2025_filtrado['VALUACION'].sum() if 'VALUACION' in df_2025_filtrado.columns else 0
    num_inc_2025 = (df_2025_filtrado['VALUACION'] > 0).sum() if 'VALUACION' in df_2025_filtrado.columns else 0
    pct_inc_2025 = (num_inc_2025 / len(df_2025_filtrado) * 100) if len(df_2025_filtrado) > 0 else 0
    
    var_val_monto = total_valuacion_2026 - total_valuacion_2025
    var_pct_inc = pct_inc - pct_inc_2025
    var_inc_vi_pct = (inc_vi_monto / total_flete_2025 * 100) if total_flete_2025 > 0 else 0

    # --- CÁLCULO DE LOS 3 CONCEPTOS NUEVOS (SOLO COBRO REGRESO) ---
    total_muestras = 0.0
    total_consignas = 0.0
    total_fnacional = 0.0
    
    col_concepto = next((c for c in df_filtered.columns if 'CONCEPTO' in c), None)
    
    if col_concepto:
        conceptos_limpios = df_filtered[col_concepto].fillna('SIN CONCEPTO').astype(str).str.strip().str.upper()
        total_muestras = df_filtered.loc[conceptos_limpios.str.contains('MUESTRA|RECOLECCI', regex=True), 'COSTO DE LA GUIA'].sum()
        total_consignas = df_filtered.loc[conceptos_limpios.str.contains('CONSIGNA', regex=True), 'COSTO DE LA GUIA'].sum()
        total_fnacional = df_filtered.loc[conceptos_limpios.str.contains('NACIONAL', regex=True), 'COSTO DE LA GUIA'].sum()
    else:
        st.warning("⚠️ Amor, Nexion no está detectando la columna CONCEPTO en el archivo CSV.")

    # --- LÓGICA DE HIERRO INTELIGENTE: COMPARATIVA MES ANTERIOR ---
    meses_map_inv = {k: v for v, k in meses_nombres.items()}
    
    total_fact_actual = total_fact_2026
    total_fact_mes_anterior = 0
    var_fact_mensual = 0
    pct_eficiencia_ant = 0
    var_eficiencia_mensual = 0
    mes_anterior_nombre = None
    
    if mes_sel != "TODOS":
        num_mes_actual = meses_map_inv.get(mes_sel, 3) 
        if num_mes_actual == 1:
            mes_anterior_nombre = "DICIEMBRE"
            if 'FORMA DE ENVIO' in df_2025.columns:
                df_ant_raw = df_2025[(df_2025['MES'] == mes_anterior_nombre) & (df_2025['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False))]
            else:
                df_ant_raw = df_2025[df_2025['MES'] == mes_anterior_nombre]
            total_fact_mes_anterior = df_ant_raw['FACTURACION'].sum() if 'FACTURACION' in df_ant_raw.columns else 0
        else:
            mes_anterior_nombre = meses_nombres.get(num_mes_actual - 1)
            if 'FORMA DE ENVIO' in df_actual.columns:
                df_ant_raw = df_actual[(df_actual['MES'] == mes_anterior_nombre) & (df_actual['FORMA DE ENVIO'].str.contains('REGRESO', na=False, case=False))]
            else:
                df_ant_raw = df_actual[df_actual['MES'] == mes_anterior_nombre]
            total_fact_mes_anterior = df_ant_raw['FACTURACION'].sum() if 'FACTURACION' in df_ant_raw.columns else 0

        if total_fact_mes_anterior > 0:
            var_fact_mensual = ((total_fact_actual - total_fact_mes_anterior) / total_fact_mes_anterior) * 100

        if not df_ant_raw.empty:
            mask_ant = df_ant_raw['PROMESA DE ENTREGA'].notna() & df_ant_raw['FECHA DE ENTREGA REAL'].notna()
            df_eval_ant = df_ant_raw[mask_ant]
            if not df_eval_ant.empty:
                cumplidos_ant = (df_eval_ant['FECHA DE ENTREGA REAL'] <= df_eval_ant['PROMESA DE ENTREGA']).sum()
                pct_eficiencia_ant = (cumplidos_ant / len(df_eval_ant)) * 100
                var_eficiencia_mensual = pct_eficiencia - pct_eficiencia_ant

    # --- BOTONES DE VISTA ---
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("VER MÉTRICAS Y TARJETAS", use_container_width=True):
            st.session_state.ver_grafico = False
    with c_btn2:
        if st.button("VER GRÁFICO COMPARATIVO", use_container_width=True):
            st.session_state.ver_grafico = True

    # --- 5. VISTA DE TARJETAS (CON FLECHAS ARRIBA/ABAJO) ---
    if not st.session_state.ver_grafico:
        st.markdown("### RESUMEN DE RENDIMIENTO")
        
        txt_mes_ant = f"vs {mes_anterior_nombre}" if mes_anterior_nombre else "Promedio"
        
        def render_card(label, value, raw_val, text_template, is_positive=True):
            # Asignación automática de flecha arriba (▲) o abajo (▼) según el signo o valor numérico
            arrow = "▲" if raw_val >= 0 else "▼"
            delta_text = f"{arrow} {text_template}"
            delta_class = "delta-pos" if is_positive else "delta-neg"
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-delta {delta_class}">{delta_text}</div>
                </div>
            """, unsafe_allow_html=True)

        k1, k2, k3 = st.columns(3)
        with k1: render_card("COSTO DE FLETE", f"${total_flete_2026:,.2f}", var_flete_total, f"{abs(var_flete_total):.1f}% vs 2025", var_flete_total <= 0)
        with k2: render_card("FACTURACIÓN", f"${total_fact_actual:,.2f}", var_fact_mensual, f"{abs(var_fact_mensual):.1f}% {txt_mes_ant}", var_fact_mensual >= 0)
        with k3: render_card("CAJAS ENVIADAS", f"{total_cajas_2026:,.0f}", var_volumen, f"{abs(var_volumen):.1f}% Vol.", var_volumen >= 0)
        
        k4, k5, k6 = st.columns(3)
        with k4: render_card("COSTO LOGÍSTICO", f"{costo_log_real:.2f}%", diferencia_target, f"{abs(diferencia_target):.2f}% vs Target 7.5%", diferencia_target <= 0)
        with k5: render_card("COSTO POR CAJA", f"${costo_caja_2026:,.2f}", var_costo_caja, f"{abs(var_costo_caja):.1f}% vs 2025", var_costo_caja <= 0)
        with k6: render_card("% EFICIENCIA ENTREGA", f"{pct_eficiencia:.1f}%", var_eficiencia_mensual, f"{abs(var_eficiencia_mensual):.1f}% {txt_mes_ant}", var_eficiencia_mensual >= 0)
        
        k7, k8, k9 = st.columns(3)
        with k7: render_card("VALUACIÓN INCIDENCIAS", f"${total_valuacion_2026:,.2f}", var_val_monto, f"${abs(var_val_monto):,.2f}", var_val_monto <= 0)
        with k8: render_card("% DE INCIDENCIAS", f"{pct_inc:.1f}%", var_pct_inc, f"{abs(var_pct_inc):.1f}%", var_pct_inc <= 0)
        with k9: render_card("INCREMENTO + VI", f"${inc_vi_monto:,.2f}", inc_vi_monto, f"{abs(var_inc_vi_pct):.1f}%", inc_vi_monto <= 0)

        # --- NUEVAS TARJETAS DE CONCEPTOS ---
        st.markdown("### DESGLOSE DE CONCEPTOS (INFORMATIVO)")
        k10, k11, k12 = st.columns(3)
        with k10: render_card("MUESTRAS / REC.", f"${total_muestras:,.2f}", 1, "Informativo", True)
        with k11: render_card("CONSIGNAS", f"${total_consignas:,.2f}", 1, "Informativo", True)
        with k12: render_card("F NACIONAL", f"${total_fnacional:,.2f}", 1, "Informativo", True)

        # --- 6. ANÁLISIS DINÁMICO PROFUNDO ---
        st.markdown("### DIAGNÓSTICO ESTRATÉGICO DE OPERACIÓN")
        
        if costo_log_real <= 7.5:
            status_target = "🟢 DENTRO DEL TARGET"
            desc_costo = "La gestión financiera es <span class='highlight'>óptima</span>, manteniendo la rentabilidad bajo los parámetros establecidos."
        else:
            status_target = "🔴 FUERA DE TARGET"
            desc_costo = f"Se detecta una desviación del <span class='highlight'>{diferencia_target:.2f}%</span>. Es prioritario revisar la negociación con fleteras o la consolidación de carga."

        if pct_eficiencia >= 95: status_entrega = "Excelencia Logística"
        elif pct_eficiencia >= 85: status_entrega = "Operación Estable"
        else: status_entrega = "Alerta de Servicio"

        alerta_incidencias = f"<br>⚠️ <b style='color:#FF4B4B;'>ALERTA:</b> El nivel de incidencias ({pct_inc:.1f}%) está impactando la valuación en <span class='highlight'>${total_valuacion_2026:,.2f}</span>." if pct_inc > 5 else ""
        tendencia_caja = "una <span class='highlight'>mejora</span>" if var_costo_caja <= 0 else "un <span class='highlight'>incremento</span>"

        html_analisis = f'''
        <div class="analysis-box">
            <div style="display: flex; justify-content: space-between;">
                <b>ESTADO FINANCIERO:</b> <span>{status_target}</span>
            </div>
            <hr style="border: 0.5px solid rgba(0, 255, 170, 0.2); margin: 10px 0;">
            <b>RESUMEN EJECUTIVO:</b><br>
            • {desc_costo}<br>
            • La logística de entregas se califica como <span class="highlight">{status_entrega}</span> con un cumplimiento del {pct_eficiencia:.1f}%.<br>
            • El costo operativo por unidad presenta {tendencia_caja} del {abs(var_costo_caja):.1f}% vs el año anterior.{alerta_incidencias}
            <br><br>
            <i style="font-size: 0.85rem; color: #8FA4B5;">* Datos calculados dinámicamente basados en el cierre de fletes y promesas de entrega.</i>
        </div>'''
        
        st.markdown(html_analisis, unsafe_allow_html=True)
        st.write("")

        # --- REPORTE DE IMPRESIÓN REPOTENCIADO ---
        def generar_reporte_grafico():
            estatus_rep = "DENTRO DE PARÁMETROS" if costo_log_real <= 7.5 else "FUERA DE PARÁMETROS"
            pct_cumplimiento_target = max(0, min(100, (7.5 / costo_log_real) * 100)) if costo_log_real > 0 else 0
            c_flete_rep = "red" if var_flete_total > 0 else "green"
            c_caja_rep = "red" if var_costo_caja > 0 else "green"
            ahora_gdl = datetime.utcnow() - timedelta(hours=6)
            fecha_hoy = ahora_gdl.strftime('%d/%m/%Y')
            hora_hoy = ahora_gdl.strftime('%H:%M')

            return f"""
            <div id="printable-report" style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #000; background: #fff; max-width: 900px; margin: auto;">
                <table style="width: 100%; border-bottom: 4px solid #000; margin-bottom: 20px;">
                    <tr>
                        <td style="width: 50%;">
                            <h1 style="margin: 0; font-size: 14px; font-weight: 900; color: #000; text-transform: uppercase;">Jabones y Productos Especializados</h1>
                            <p style="margin: 0; font-size: 11px; font-weight: bold; text-transform: uppercase; color: #666;">Distribución y Logística | 2026</p>
                        </td>
                        <td style="width: 50%; text-align: right; font-size: 11px; line-height: 1.6;">
                            <b>REPORTE ID:</b> LOG-{mes_sel[:3].upper()}-2026<br>
                            <b>FECHA:</b> {fecha_hoy} | <b>HORA:</b> {hora_hoy} (ZMG)<br>
                            <span style="border: 2px solid #000; padding: 4px 10px; font-weight: bold; display: inline-block; margin-top: 8px;">
                                {estatus_rep}
                            </span>
                        </td>
                    </tr>
                </table>

                <h2 style="text-align: center; text-transform: uppercase; font-size: 18px; text-decoration: underline;">Análisis Operativo Mensual: {mes_sel}</h2>
                
                <div style="margin-bottom: 30px;">
                    <p style="font-size: 12px; font-weight: bold;">RENDIMIENTO VS META (TARGET 7.5%):</p>
                    <div style="width: 100%; border: 2px solid #000; height: 35px; position: relative; background: #f0f0f0;">
                        <div style="width: {pct_cumplimiento_target}%; background: #444; height: 100%;"></div>
                        <div style="position: absolute; top: 8px; left: 10px; color: #fff; font-weight: bold;">ACTUAL: {costo_log_real:.2f}%</div>
                        <div style="position: absolute; top: 8px; right: 10px; color: #000; font-weight: bold;">OBJETIVO: 7.50%</div>
                    </div>
                </div>

                <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                    <div style="flex: 1; border: 1px solid #000; padding: 10px;">
                        <p style="margin: 0 0 10px 0; font-size: 10px; font-weight: bold; text-align: center; background: #000; color: #fff;">ESTRUCTURA DE COSTOS</p>
                        <table style="width: 100%; font-size: 11px; border-collapse: collapse;">
                            <tr><td>Gasto Flete 2026:</td><td style="text-align: right; color:{c_flete_rep}"><b>${total_flete_2026:,.2f}</b></td></tr>
                            <tr><td>Gasto Flete 2025:</td><td style="text-align: right;">${total_flete_2025:,.2f}</td></tr>
                            <tr><td>Variación Gasto:</td><td style="text-align: right;"><b>{var_flete_total:+.1f}%</b></td></tr>
                        </table>
                    </div>
                    <div style="flex: 1; border: 1px solid #000; padding: 10px;">
                        <p style="margin: 0 0 10px 0; font-size: 10px; font-weight: bold; text-align: center; background: #000; color: #fff;">EFICIENCIA UNITARIA</p>
                        <div style="text-align: center; padding-top: 5px;">
                            <span style="font-size: 26px; font-weight: bold;">${costo_caja_2026:.2f}</span><br>
                            <span style="font-size: 10px;">Costo por Caja Actual</span><br>
                            <span style="font-size: 11px; color:{c_caja_rep}; font-weight:bold;">Var: {var_costo_caja:+.1f}% vs 2025</span>
                        </div>
                    </div>
                </div>

                <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 20px;">
                    <tr style="background: #000; color: #fff; border: 1px solid #000;">
                        <th style="padding: 10px; text-align: left;">MÉTRICA DE OPERACIÓN DETALLADA</th>
                        <th style="padding: 10px; text-align: center;">VALOR ACTUAL</th>
                    </tr>
                    <tr><td style="border: 1px solid #000; padding: 8px;">Facturación Bruta Totales</td><td style="border: 1px solid #000; padding: 8px; text-align: center; font-weight:bold;">${total_fact_2026:,.2f}</td></tr>
                    <tr><td style="border: 1px solid #000; padding: 8px;">Cajas Enviadas (Volumen)</td><td style="border: 1px solid #000; padding: 8px; text-align: center;">{int(total_cajas_2026):,.0f} Uds.</td></tr>
                    <tr><td style="border: 1px solid #000; padding: 8px;">Variación Volumen vs 2025</td><td style="border: 1px solid #000; padding: 8px; text-align: center;">{var_volumen:+.1f}%</td></tr>
                    <tr><td style="border: 1px solid #000; padding: 8px;">Costo Logístico sobre Ventas</td><td style="border: 1px solid #000; padding: 8px; text-align: center; font-weight:bold;">{costo_log_real:.2f}%</td></tr>
                    <tr style="background: #f9f9f9;"><td style="border: 1px solid #000; padding: 8px;"><b>Eficiencia On-Time (Entregas en Tiempo)</b></td><td style="border: 1px solid #000; padding: 8px; text-align: center; font-weight:bold;">{pct_eficiencia:.1f}%</td></tr>
                    <tr><td style="border: 1px solid #000; padding: 8px;">Valuación de Incidencias</td><td style="border: 1px solid #000; padding: 8px; text-align: center;">${total_valuacion_2026:,.2f}</td></tr>
                    <tr><td style="border: 1px solid #000; padding: 8px;">Porcentaje de Incidencias sobre Pedidos</td><td style="border: 1px solid #000; padding: 8px; text-align: center;">{pct_inc:.1f}%</td></tr>
                    <tr><td style="border: 1px solid #000; padding: 8px;">Impacto Económico Neto (Incremento + VI)</td><td style="border: 1px solid #000; padding: 8px; text-align: center; font-weight:bold;">${inc_vi_monto:,.2f}</td></tr>
                </table>

                <h3 style="font-size: 11px; font-weight: bold; margin-top: 10px; background: #000; color: #fff; padding: 5px; text-align: center;">DESGLOSE POR CONCEPTO INFORMATIVO</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 30px;">
                    <tr>
                        <td style="border: 1px solid #000; padding: 6px; background: #f9f9f9;"><b>Muestras / Recolecciones</b></td>
                        <td style="border: 1px solid #000; padding: 6px; text-align: center;">${total_muestras:,.2f}</td>
                        <td style="border: 1px solid #000; padding: 6px; background: #f9f9f9;"><b>Consignas</b></td>
                        <td style="border: 1px solid #000; padding: 6px; text-align: center;">${total_consignas:,.2f}</td>
                        <td style="border: 1px solid #000; padding: 6px; background: #f9f9f9;"><b>F Nacional</b></td>
                        <td style="border: 1px solid #000; padding: 6px; text-align: center;">${total_fnacional:,.2f}</td>
                    </tr>
                </table>

                <div style="margin-top: 40px; display: flex; justify-content: space-between; text-align: center; font-size: 11px;">
                    <div style="width: 40%; border-top: 2px solid #000; padding-top: 10px;">
                        <b>Rigoberto Hernández</b><br>Coordinador de Logística Nacional
                    </div>
                    <div style="width: 40%; border-top: 2px solid #000; padding-top: 10px;">
                        <b>Carlos Fialko</b><br>Director General
                    </div>
                </div>
            </div>
            """

        def generar_memoria_tecnica():
            gasto_base_2025 = total_flete_2026 - inc_vi_monto
            ahora_gdl = datetime.utcnow() - timedelta(hours=6)
            fecha_hoy = ahora_gdl.strftime('%d/%m/%Y')
            hora_hoy = ahora_gdl.strftime('%H:%M')
            
            txt_volumen = "el alza" if var_volumen >= 0 else "la reducción"
            txt_gasto = "el incremento" if var_flete_total >= 0 else "la disminución"
            
            if var_costo_caja < 0:
                txt_tarifa = "una <span style='color: #2e7d32; font-weight: bold;'>reducción (optimización)</span> en la tarifa unitaria por caja"
            elif var_costo_caja > 0:
                txt_tarifa = "un <span style='color: #d32f2f; font-weight: bold;'>incremento</span> en la tarifa unitaria por caja"
            else:
                txt_tarifa = "una <b>estabilidad absoluta</b> en la tarifa unitaria por caja"

            if total_valuacion_2026 <= 0:
                txt_inc = f"Al no existir incidencias acumuladas (${total_valuacion_2026:,.2f}), el impacto financiero es estrictamente operativo."
            else:
                txt_inc = f"Es importante notar que existen incidencias acumuladas por ${total_valuacion_2026:,.2f} que impactan el balance financiero del periodo."

            return f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 10px; color: #333; max-width: 800px; margin: auto; background-color: #fff;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #000; padding-bottom: 5px; margin-bottom: 15px;">
                    <div style="text-align: left;">
                        <h1 style="margin: 0; font-size: 18px; text-transform: uppercase;">Jabones y Productos Especializados</h1>
                        <p style="margin: 2px 0; font-size: 10px; color: #666; font-weight: bold; text-transform: uppercase;">Memoria Técnica de Cálculo y Variaciones</p>
                    </div>
                    <div style="text-align: right; font-size: 10px; color: #444; line-height: 1.6;">
                        <b>REPORTE ID:</b> TEC-{mes_sel[:3].upper()}-2026<br>
                        <b>FECHA:</b> {fecha_hoy} | <b>HORA:</b> {hora_hoy} (ZMG)
                    </div>
                </div>
                <p style="font-size: 11px; line-height: 1.4; color: #555; margin-bottom: 15px;">
                    Este documento detalla la trazabilidad algorítmica de los KPIs presentados en el periodo <b>{mes_sel} 2026</b>.
                </p>
                
                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">1. COSTO LOGÍSTICO (KPI DE RENTABILIDAD)</h3>
                    <div style="background: #f0f0f0; padding: 8px; text-align: center; font-family: 'Courier New'; font-weight: bold; font-size: 13px;">
                        ( ∑ Flete Actual / ∑ Facturación Actual ) x 100
                    </div>
                    <p style="font-size: 10px; margin-top: 5px;"><b>Resultado:</b> (${total_flete_2026:,.2f} / ${total_fact_2026:,.2f}) x 100 = <b>{costo_log_real:.2f}%</b></p>
                </div>
                
                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">2. EFICIENCIA DE ENTREGA (OTD)</h3>
                    <div style="background: #f0f0f0; padding: 8px; text-align: center; font-family: 'Courier New'; font-weight: bold; font-size: 13px;">
                        ( Envíos On-Time / Total Envíos Evaluables ) x 100
                    </div>
                    <p style="font-size: 10px; margin-top: 5px;"><b>Resultado:</b> Cumplimiento del <b>{pct_eficiencia:.1f}%</b> basado en registros evaluables.</p>
                </div>
                
                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">3. COSTO POR CAJA (EFICIENCIA UNITARIA)</h3>
                    <div style="background: #f0f0f0; padding: 8px; text-align: center; font-family: 'Courier New'; font-weight: bold; font-size: 13px;">
                        Gasto de Flete Total / Cantidad de Cajas Enviadas
                    </div>
                    <p style="font-size: 10px; margin-top: 5px;"><b>Resultado:</b> ${total_flete_2026:,.2f} / {total_cajas_2026:,.0f} cajas = <b>${costo_caja_2026:,.2f} / caja</b></p>
                </div>
                
                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">4. INCREMENTO LOGÍSTICO + VALUACIÓN INCIDENCIAS (VI)</h3>
                    <div style="background: #f0f0f0; padding: 8px; text-align: center; font-family: 'Courier New'; font-weight: bold; font-size: 13px;">
                        (Gasto_2026 - Gasto_2025) + Valuación_Incidencias
                    </div>
                    <p style="font-size: 10px; margin-top: 5px;"><b>Desglose:</b> (${total_flete_2026:,.2f} - ${gasto_base_2025:,.2f}) + ${total_valuacion_2026:,.2f} = <b>${inc_vi_monto:,.2f}</b></p>
                </div>
                
                <div style="margin-top: 10px; padding: 10px; border: 2px solid #2276AA; background: #f0f7ff;">
                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">5. ANÁLISIS DE DELTAS (COMPARATIVA ANUAL)</h3>
                    <table style="width: 100%; font-size: 9px; border-collapse: collapse; text-align: left; margin-top: 5px;">
                        <tr style="border-bottom: 1px solid #2276AA; background: #e3f2fd;">
                            <th style="padding: 4px;">INDICADOR</th>
                            <th>PREVIO (2025)</th>
                            <th>ACTUAL (2026)</th>
                            <th>VARIACIÓN (DELTA)</th>
                        </tr>
                        <tr>
                            <td style="padding: 4px;"><b>Gasto de Flete</b></td>
                            <td>${gasto_base_2025:,.2f}</td>
                            <td>${total_flete_2026:,.2f}</td>
                            <td style="color: #d32f2f; font-weight: bold;">{var_flete_total:+.1f}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px;"><b>Volumen Cajas</b></td>
                            <td>{total_cajas_2025:,.0f}</td>
                            <td>{total_cajas_2026:,.0f}</td>
                            <td style="color: #2e7d32; font-weight: bold;">{var_volumen:+.1f}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px;"><b>Costo x Caja</b></td>
                            <td>${costo_caja_2025:,.2f}</td>
                            <td>${costo_caja_2026:,.2f}</td>
                            <td style="color: #d32f2f; font-weight: bold;">{var_costo_caja:+.1f}%</td>
                        </tr>
                    </table>
                </div>

                <div style="margin-top: 10px; padding: 10px; border: 1px solid #eee; background: #fdfdfd;">
                    <h3 style="margin: 0 0 5px 0; color: #2276AA; font-size: 12px;">6. DESGLOSE DE CONCEPTOS ESPECIALES</h3>
                    <p style="font-size: 10px; margin-top: 5px;">
                        Muestras/Recolecciones: <b>${total_muestras:,.2f}</b> | Consignas: <b>${total_consignas:,.2f}</b> | F Nacional: <b>${total_fnacional:,.2f}</b><br>
                        <i style="color: #777;">* Valores meramente informativos para la modalidad Cobro Regreso. No aplican en la comparativa anual (Deltas).</i>
                    </p>
                </div>
                
                <div style="margin-top: 15px; padding: 10px; background: #fffde7; border-left: 5px solid #fbc02d; font-size: 9px; line-height: 1.3;">
                    <b>INTERPRETACIÓN TÉCNICA:</b> La relación entre {txt_volumen} de volumen ({var_volumen:+.1f}%) y {txt_gasto} del gasto ({var_flete_total:+.1f}%) confirma {txt_tarifa}. {txt_inc}
                </div>
                
                <div style="margin-top: 30px; display: flex; justify-content: space-around; text-align: center; font-size: 10px;">
                    <div style="width: 200px; border-top: 1px solid #000; padding-top: 5px;">
                        <b>Rigoberto Hernández</b><br>Coordinación de Logística
                    </div>
                </div>
            </div>
            """

        col_print1, col_print2 = st.columns(2)
        with col_print1:
            if st.button(":material/print: GENERAR REPORTE GRÁFICO", type="primary", use_container_width=True):
                st.session_state.reporte_a_imprimir = generar_reporte_grafico()
        with col_print2:
            if st.button(":material/calculate: IMPRIMIR CÁLCULO APLICADO", use_container_width=True):
                st.session_state.reporte_a_imprimir = generar_memoria_tecnica()

        if st.session_state.get('reporte_a_imprimir') is not None:
            html_template = f"""
                <script>
                    var win = window.open('', '_blank', 'height=800,width=800');
                    win.document.write('<html><body>' + `{st.session_state.reporte_a_imprimir}` + '</body></html>');
                    win.document.close();
                    win.onload = function() {{ 
                        win.print(); 
                    }};
                </script>
            """
            components.html(html_template, height=0)
            st.session_state.reporte_a_imprimir = None

    # --- 8. VISTA DE GRÁFICO (COMPARATIVO) ---
    else:
        st.markdown("###  COMPARATIVA ANUAL DE GASTOS (2025 vs 2026)")
        
        df_g_2026 = df_gastos.groupby('MES')['COSTO DE FLETE'].sum().reset_index()
        df_g_2025 = df_2025.groupby('MES')['COSTO DE LA GUIA'].sum().reset_index()

        meses_orden = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
                       "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        df_g_2026['MES'] = pd.Categorical(df_g_2026['MES'], categories=meses_orden, ordered=True)
        df_g_2025['MES'] = pd.Categorical(df_g_2025['MES'], categories=meses_orden, ordered=True)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_g_2025.sort_values('MES')['MES'], 
            y=df_g_2025.sort_values('MES')['COSTO DE LA GUIA'], 
            name='Gasto 2025', 
            marker_color='#36b9cc', 
            text=[f'${x:,.0f}' for x in df_g_2025.sort_values('MES')['COSTO DE LA GUIA']],
            textposition='outside',
            textfont=dict(color='#A4B9C8') 
        ))

        fig.add_trace(go.Bar(
            x=df_g_2026.sort_values('MES')['MES'], 
            y=df_g_2026.sort_values('MES')['COSTO DE FLETE'], 
            name='Gasto 2026 (Actual)', 
            marker_color='#00FFAA', 
            text=[f'${x:,.0f}' for x in df_g_2026.sort_values('MES')['COSTO DE FLETE']],
            textposition='outside',
            textfont=dict(color='#FFFFFF')
        ))

        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='group',
            xaxis_title="MESES DE OPERACIÓN",
            yaxis_title="MONTO TOTAL ($)",
            font=dict(color="#A4B9C8"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=80) 
        )

        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Las etiquetas doradas muestran el gasto acumulado actual de JYPESA para comparación directa.")

except Exception as e:
    st.error(f"¡Atención, amor! Detalle en el código: {e}")
