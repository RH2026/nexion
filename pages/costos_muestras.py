import io
import time
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from auth import exigir_autenticacion

from components.layout import render_layout
from muestras_common import (
    precios,
    obtener_datos_github,
    subir_a_github,
    generar_etiquetas_limpias,
    generar_html_impresion,
    es_usuario_logistica,
    bloque_acceso_restringido,
)

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Reportes - Costos de Muestras",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO Y PERMISOS
# ============================================================
render_layout(modulo_actual="REPORTES", submodulo_actual="COSTOS DE MUESTRAS")


def main():
    puede_ver, usuario_logeado = es_usuario_logistica()

    if not puede_ver:
        bloque_acceso_restringido(usuario_logeado)
        return

    df_actual, sha_actual = obtener_datos_github()

    if not df_actual.empty:
        for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL", "ESTATUS"]:
            if col not in df_actual.columns:
                if col == "ESTATUS":
                    df_actual[col] = "NO SURTIDO"
                else:
                    df_actual[col] = 0.0

    def subtitulo_pestana(texto):
        st.markdown(
            f"""
            <div style='padding: 6px 0 14px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 20px;'>
                <span style='color:#FFFFFF; font-size:13px; font-weight:800; letter-spacing:2.5px; text-transform:uppercase;'>
                    DASHBOARD EJECUTIVO // {texto}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def grafico_horizontal(serie, color, alto=420):
        """Gráfica de barras HORIZONTAL: las categorías (nombres) se leen
        de corrido en el eje vertical, sin rotar ni amontonarse abajo."""
        if serie is None or serie.empty:
            st.caption("Sin datos suficientes para graficar en este periodo.")
            return
        df_chart = serie.reset_index()
        df_chart.columns = ["categoria", "valor"]
        chart = (
            alt.Chart(df_chart)
            .mark_bar(color=color, cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X("valor:Q", title=None),
                y=alt.Y("categoria:N", sort="-x", title=None, axis=alt.Axis(labelLimit=280, labelFontSize=11)),
                tooltip=[alt.Tooltip("categoria:N", title=""), alt.Tooltip("valor:Q", title="Valor", format=",.0f")],
            )
            .properties(height=alto)
        )
        st.altair_chart(chart, use_container_width=True, theme="streamlit")

    def grafico_vertical(serie, color, alto=380):
        """Gráfica de barras VERTICAL con las etiquetas del eje X
        SIEMPRE horizontales (labelAngle=0), sin quedar 'paradas'."""
        if serie is None or serie.empty:
            st.caption("Sin datos suficientes para graficar.")
            return
        df_chart = serie.reset_index()
        df_chart.columns = ["categoria", "valor"]
        chart = (
            alt.Chart(df_chart)
            .mark_bar(color=color, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("categoria:N", title=None, sort=None, axis=alt.Axis(labelAngle=0, labelFontSize=11)),
                y=alt.Y("valor:Q", title=None),
                tooltip=[alt.Tooltip("categoria:N", title=""), alt.Tooltip("valor:Q", title="Valor", format=",.0f")],
            )
            .properties(height=alto)
        )
        st.altair_chart(chart, use_container_width=True, theme="streamlit")

    # ============================================================
    # ORDEN DE PESTAÑAS: 0) Indicadores  1) Historial y Reportes
    #                    2) Gestionar Folios  3) Edición
    # ============================================================
    t0, t1, t2, t3 = st.tabs(["Indicadores", "Historial y Reportes", "Gestionar Folios / Guías", "Edición"])

    # ============================================================
    # TAB 0 — INDICADORES (dashboard visual con filtro mensual)
    # ============================================================
    with t0:
        subtitulo_pestana("KPI DE SURTIDO Y ENVÍOS")
        if df_actual.empty:
            st.info("No hay registros todavía para generar indicadores.")
        else:
            df_ind = df_actual.copy()
            df_ind['FECHA'] = df_ind['FECHA'].astype(str).str.strip()
            df_ind['FECHA_DT'] = pd.to_datetime(df_ind['FECHA'], format='%Y-%m-%d', errors='coerce')
            df_ind['FECHA_DT'] = df_ind['FECHA_DT'].fillna(
                pd.to_datetime(df_ind['FECHA'], dayfirst=True, errors='coerce')
            )
            df_ind['MES_FILTRO'] = df_ind['FECHA_DT'].dt.strftime('%m - %Y').fillna("SIN FECHA")
            df_ind['COSTO_TOTAL'] = pd.to_numeric(df_ind.get('COSTO_TOTAL', 0), errors='coerce').fillna(0)
            df_ind['COSTO_GUIA'] = pd.to_numeric(df_ind.get('COSTO_GUIA', 0), errors='coerce').fillna(0)

            meses_ind = sorted([m for m in df_ind['MES_FILTRO'].unique() if m != "SIN FECHA"], reverse=True)
            if "SIN FECHA" in df_ind['MES_FILTRO'].values:
                meses_ind.append("SIN FECHA")

            col_fi1, col_fi2 = st.columns([1.5, 2.5])
            mes_ind_sel = col_fi1.selectbox(
                ":material/calendar_month: FILTRAR PERIODO",
                ["MOSTRAR TODO"] + meses_ind,
                key="mes_indicadores"
            )

            if mes_ind_sel != "MOSTRAR TODO":
                df_kpi = df_ind[df_ind['MES_FILTRO'] == mes_ind_sel].copy()
            else:
                df_kpi = df_ind.copy()

            # --------------------------------------------------
            # KPIs PRINCIPALES (cálculo, se muestran dentro de la
            # primera sub-pestaña "🧮 KPI's")
            # --------------------------------------------------
            total_folios = len(df_kpi)
            costo_prod_total = df_kpi['COSTO_TOTAL'].sum()
            costo_flete_total = df_kpi['COSTO_GUIA'].sum()
            costo_general = costo_prod_total + costo_flete_total
            costo_promedio = (costo_general / total_folios) if total_folios else 0
            despachados = (df_kpi['ESTATUS'].astype(str).str.upper() == "DESPACHADO").sum()
            pct_despachado = (despachados / total_folios * 100) if total_folios else 0

            def tarjeta_kpi(titulo, valor, color="#00D4FF"):
                return f"""
                <div style="background:#263238; border:1px solid rgba(255,255,255,0.05); border-top:3px solid {color}; border-radius:10px; padding:16px 12px; text-align:center; height:100%;">
                    <div style="color:rgba(255,255,255,0.5); font-size:9px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; margin-bottom:8px;">{titulo}</div>
                    <div style="color:{color}; font-size:20px; font-weight:900; font-family:monospace;">{valor}</div>
                </div>"""

            if total_folios:
                top_solicitante_nombre = (
                    df_kpi.groupby(df_kpi['SOLICITO'].astype(str).str.upper())['FOLIO'].count().idxmax()
                )
            else:
                top_solicitante_nombre = "SIN DATOS"

            # --------------------------------------------------
            # SUB-PESTAÑAS: KPI's + LAS 6 GRÁFICAS (evita el scroll infinito)
            # --------------------------------------------------
            sub_g0, sub_g1, sub_g2, sub_g3, sub_g4, sub_g5, sub_g6 = st.tabs([
                "KPI's",
                "Tendencia Mensual",
                "Envíos por Agente",
                "Costo por Agente",
                "Top Destinos",
                "Flete por Paquetería",
                "Productos Top",
            ])

            with sub_g0:
                st.write("")
                k1, k2, k3, k4, k5 = st.columns(5)
                k1.markdown(tarjeta_kpi("TOTAL DE ENVÍOS", f"{total_folios}"), unsafe_allow_html=True)
                k2.markdown(tarjeta_kpi("COSTO PRODUCTOS", f"${costo_prod_total:,.0f}", "#38bdf8"), unsafe_allow_html=True)
                k3.markdown(tarjeta_kpi("COSTO FLETES", f"${costo_flete_total:,.0f}", "#a855f7"), unsafe_allow_html=True)
                k4.markdown(tarjeta_kpi("INVERSIÓN TOTAL", f"${costo_general:,.0f}", "#00FFAA"), unsafe_allow_html=True)
                k5.markdown(tarjeta_kpi("% DESPACHADO", f"{pct_despachado:,.0f}%", "#FFD700"), unsafe_allow_html=True)

                st.write("")
                k6, k7 = st.columns(2)
                k6.markdown(tarjeta_kpi("COSTO PROMEDIO / ENVÍO", f"${costo_promedio:,.0f}", "#FFA500"), unsafe_allow_html=True)
                k7.markdown(tarjeta_kpi("AGENTE CON MÁS ENVÍOS", top_solicitante_nombre[:24], "#FF6B6B"), unsafe_allow_html=True)

            with sub_g1:
                st.markdown(
                    "<p style='color:#00FFAA; font-size:11px; font-weight:800; letter-spacing:1px; text-transform:uppercase; margin:8px 0;'>Costo Total por Mes (histórico completo)</p>",
                    unsafe_allow_html=True,
                )
                df_validas = df_ind.dropna(subset=['FECHA_DT']).copy()
                if not df_validas.empty:
                    df_validas['MES_PERIOD'] = df_validas['FECHA_DT'].dt.to_period('M')
                    df_validas['COSTO_INVERSION'] = df_validas['COSTO_TOTAL'] + df_validas['COSTO_GUIA']
                    trend = df_validas.groupby('MES_PERIOD')['COSTO_INVERSION'].sum().sort_index()
                    trend.index = trend.index.strftime('%m - %Y')
                    grafico_vertical(trend, "#508592", alto=420)
                else:
                    st.caption("Sin fechas válidas para graficar la tendencia.")

            with sub_g2:
                st.markdown(
                    "<p style='color:#38bdf8; font-size:11px; font-weight:800; letter-spacing:1px; text-transform:uppercase; margin:8px 0;'>Envíos por Solicitante / Agente (top 10 del periodo)</p>",
                    unsafe_allow_html=True,
                )
                por_solicitante = (
                    df_kpi.groupby(df_kpi['SOLICITO'].astype(str).str.upper())['FOLIO']
                    .count()
                    .sort_values(ascending=False)
                    .head(10)
                )
                grafico_horizontal(por_solicitante, "#A4B7C0", alto=420)

            with sub_g3:
                st.markdown(
                    "<p style='color:#a855f7; font-size:11px; font-weight:800; letter-spacing:1px; text-transform:uppercase; margin:8px 0;'>Costo por Solicitante / Agente (top 10 del periodo)</p>",
                    unsafe_allow_html=True,
                )
                costo_por_solicitante = (
                    df_kpi.assign(COSTO_INVERSION=df_kpi['COSTO_TOTAL'] + df_kpi['COSTO_GUIA'])
                    .groupby(df_kpi['SOLICITO'].astype(str).str.upper())['COSTO_INVERSION']
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                )
                grafico_horizontal(costo_por_solicitante, "#a855f7", alto=420)

            with sub_g4:
                st.markdown(
                    "<p style='color:#FFD700; font-size:11px; font-weight:800; letter-spacing:1px; text-transform:uppercase; margin:8px 0;'>Top Destinos / Hoteles (top 10 del periodo)</p>",
                    unsafe_allow_html=True,
                )
                top_destinos = (
                    df_kpi.groupby(df_kpi['NOMBRE DEL HOTEL'].astype(str).str.upper())['FOLIO']
                    .count()
                    .sort_values(ascending=False)
                    .head(10)
                )
                grafico_horizontal(top_destinos, "#508592", alto=420)

            with sub_g5:
                st.markdown(
                    "<p style='color:#FF6B6B; font-size:11px; font-weight:800; letter-spacing:1px; text-transform:uppercase; margin:8px 0;'>Costo de Flete por Paquetería (top 10 del periodo)</p>",
                    unsafe_allow_html=True,
                )
                col_paq = 'PAQUETERIA_NOMBRE' if 'PAQUETERIA_NOMBRE' in df_kpi.columns else 'PAQUETERIA'
                df_paq = df_kpi.copy()
                df_paq[col_paq] = df_paq[col_paq].replace('', 'SIN ASIGNAR').fillna('SIN ASIGNAR')
                costo_flete_paq = (
                    df_paq.groupby(df_paq[col_paq].astype(str).str.upper())['COSTO_GUIA']
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                )
                grafico_horizontal(costo_flete_paq, "#FF6B6B", alto=420)

            with sub_g6:
                st.markdown(
                    "<p style='color:#00D4FF; font-size:11px; font-weight:800; letter-spacing:1px; text-transform:uppercase; margin:8px 0;'>Productos Más Solicitados (piezas, periodo filtrado)</p>",
                    unsafe_allow_html=True,
                )
                cantidades_prod = {}
                for p in precios.keys():
                    if p in df_kpi.columns:
                        cantidades_prod[p] = pd.to_numeric(df_kpi[p], errors='coerce').fillna(0).sum()
                serie_prod = pd.Series(cantidades_prod, dtype="float64").sort_values(ascending=False).head(10)
                serie_prod = serie_prod[serie_prod > 0]
                serie_prod.index = [i[:35].upper() for i in serie_prod.index]
                grafico_horizontal(serie_prod, "#A4B7C0", alto=420)

    # ============================================================
    # TAB 1 — HISTORIAL Y REPORTES (costos y envíos por solicitante)
    # ============================================================
    with t1:
        subtitulo_pestana("HISTORIAL Y REPORTES DE COSTOS")
        if not df_actual.empty:
            st.write("")
            df_actual['FECHA'] = df_actual['FECHA'].astype(str).str.strip()
            df_actual['FECHA_DT'] = pd.to_datetime(df_actual['FECHA'], format='%Y-%m-%d', errors='coerce')
            df_actual['FECHA_DT'] = df_actual['FECHA_DT'].fillna(
                pd.to_datetime(df_actual['FECHA'], dayfirst=True, errors='coerce')
            )
            df_actual['MES_FILTRO'] = df_actual['FECHA_DT'].dt.strftime('%m - %Y').fillna("SIN FECHA")

            meses_lista = sorted([m for m in df_actual['MES_FILTRO'].unique() if m != "SIN FECHA"], reverse=True)
            if "SIN FECHA" in df_actual['MES_FILTRO'].values:
                meses_lista.append("SIN FECHA")

            col_f1, col_f2 = st.columns([1.5, 2.5])
            mes_sel = col_f1.selectbox(
                ":material/calendar_month: FILTRAR PERIODO",
                ["MOSTRAR TODO"] + meses_lista
            )

            if mes_sel != "MOSTRAR TODO":
                df_render = df_actual[df_actual['MES_FILTRO'] == mes_sel].copy()
            else:
                df_render = df_actual.copy()

            t_prod = df_render["COSTO_TOTAL"].sum()
            t_flete = df_render["COSTO_GUIA"].sum()
            filas_html = ""
            tarjetas_html = ""

            df_render = df_render.fillna(0)
            df_render = df_render.sort_values(by="FOLIO", ascending=False)

            for _, r in df_render.iterrows():
                detalle_p = ""
                for p in precios.keys():
                    cant = r.get(p, 0)
                    if cant > 0:
                        detalle_p += f"• {int(cant)} PZAS {str(p).upper()}<br>"

                estatus_bd = str(r.get('ESTATUS', 'NO SURTIDO')).upper()
                if estatus_bd == "DESPACHADO":
                    badge_html = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:2px 8px; border-radius:12px; font-size:9px; font-weight:800; letter-spacing:1px; margin-top:5px;'>✓ DESPACHADO</div>"
                else:
                    badge_html = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:2px 8px; border-radius:12px; font-size:9px; font-weight:800; letter-spacing:1px; margin-top:5px; box-shadow: 0 0 8px rgba(255,68,68,0.4);'>⚠️ NO SURTIDO</div>"

                filas_html += f"""
                <tr style="page-break-inside: avoid;">
                    <td style='border:1px solid black; padding:6px; text-align:center; font-size:10px; width:7%;'>{r['FOLIO']}</td>
                    <td style='border:1px solid black; padding:6px; font-size:10px; width:15%;'>
                        <b style='color:black;'>{str(r['SOLICITO']).upper()}</b><br>
                        <small style='font-size:8px; color:#444;'>{r['FECHA']}</small>
                    </td>
                    <td style='border:1px solid black; padding:6px; font-size:10px; width:25%;'>
                        <b>{str(r['NOMBRE DEL HOTEL']).upper()}</b><br>
                        <small style='font-size:8px; color:#333;'>{str(r['DESTINO']).upper()}</small>
                    </td>
                    <td style='border:1px solid black; padding:6px; font-size:9px; line-height:1.3; width:33%;'>
                        {detalle_p}
                    </td>
                    <td style='border:1px solid black; padding:6px; text-align:right; font-size:10px; width:10%; white-space:nowrap;'>
                        <b>${r['COSTO_TOTAL']:,.2f}</b>
                    </td>
                    <td style='border:1px solid black; padding:6px; text-align:right; font-size:10px; width:10%; white-space:nowrap;'>
                        ${r['COSTO_GUIA']:,.2f}
                    </td>
                </tr>"""

                tarjetas_html += f"""
                <div class="card-reporte" style="padding: 20px 30px; margin-bottom: 15px;">
                    <div class="col-folio" style="flex: 1;">
                        <div class="label-mini">FOLIO</div>
                        <div class="val-folio" style="margin-bottom: 5px;">#{r['FOLIO']}</div>
                        <div class="val-sub">{r['FECHA']}</div>
                        {badge_html}
                    </div>
                    <div class="col-info" style="flex: 2.5; padding: 0 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                        <div class="label-mini">SOLICITANTE / DESTINO</div>
                        <div class="val-main" style="margin-bottom: 4px;">{str(r['SOLICITO']).upper()}</div>
                        <div class="val-sub">{str(r['NOMBRE DEL HOTEL']).upper()}</div>
                        <div class="val-sub" style="opacity: 0.7;">{str(r['DESTINO']).upper()}</div>
                    </div>
                    <div class="col-detalle" style="flex: 2.5; padding: 0 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                        <div class="label-mini">DESGLOSE PRODUCTOS</div>
                        <div class="val-list" style="line-height: 1.6;">{detalle_p if detalle_p else 'SIN DETALLE'}</div>
                    </div>
                    <div class="col-costos" style="flex: 1.5; text-align: right; padding-left: 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                        <div class="label-mini">INVERSIÓN</div>
                        <div class="val-costo" style="font-size: 14px; margin-bottom: 5px;">Prod: ${r['COSTO_TOTAL']:,.2f}</div>
                        <div class="val-flete" style="font-size: 14px;">Flete: ${r['COSTO_GUIA']:,.2f}</div>
                    </div>
                </div>"""

            st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <p style='color:#00FFAA; font-weight:800; letter-spacing:2px; font-size:14px; margin:0;'>VISTA: {mes_sel}</p>
                    <p style='color:#FFFFFF; font-size:12px; opacity:0.6;'>Mostrando {len(df_render)} registros</p>
                </div>
            """, unsafe_allow_html=True)

            html_final = f"""
            <div style="font-family: 'Inter', sans-serif;">
                <style>
                    body {{ background: transparent; margin: 0; padding: 0; }}
                    .container-reporte {{ height: 500px; overflow-y: auto; padding-right: 10px; }}
                    .card-reporte {{ background: #263238; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; display: flex; min-width: 800px; justify-content: space-between; align-items: center; transition: 0.3s; }}
                    .card-reporte:hover {{ border-color: #38bdf8; background: #2d3b42; }}
                    .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px; }}
                    .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }}
                    .val-main {{ color: #FFFFFF; font-size: 12px; font-weight: 700; }}
                    .val-sub {{ color: rgba(255,255,255,0.5); font-size: 10px; }}
                    .val-list {{ color: #FFFFFF; font-size: 9px; line-height: 1.4; opacity: 0.8; }}
                    .val-costo {{ color: #38bdf8; font-size: 13px; font-weight: 700; font-family: monospace; }}
                    .val-flete {{ color: #a855f7; font-size: 13px; font-weight: 700; font-family: monospace; }}
                    ::-webkit-scrollbar {{ width: 8px; }}
                    ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                    ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                </style>
                <div class="container-reporte">{tarjetas_html}</div>
            </div>"""
            components.html(html_final, height=520, scrolling=False)

            st.markdown(f"""
                <div style="background:#263238; border-top: 4px solid #00FFAA; border-radius: 0 0 12px 12px; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                    <div style="color:rgba(255,255,255,0.6); font-size:12px;">PRODUCTOS: <span style="color:white; font-weight:bold;">${t_prod:,.2f}</span></div>
                    <div style="color:rgba(255,255,255,0.6); font-size:12px;">FLETES: <span style="color:white; font-weight:bold;">${t_flete:,.2f}</span></div>
                    <div style="color:#00FFAA; font-size:16px; font-weight:800; letter-spacing:1px;">TOTAL FILTRADO: ${(t_prod+t_flete):,.2f}</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <style>
            div[data-testid="stDownloadButton"] button {
                background-color: #628290 !important;
                color: #FFFFFF !important;
                border: 1px solid #628290 !important;
                width: 100% !important;
                border-radius: 4px !important;
                font-weight: 400 !important;
                box-shadow: none !important;
                outline: none !important;
            }
            div[data-testid="stDownloadButton"] button:hover {
                background-color: #4E6772 !important;
                border-color: #4E6772 !important;
                color: #FFFFFF !important;
            }
            div[data-testid="stDownloadButton"] button:focus,
            div[data-testid="stDownloadButton"] button:active {
                background-color: #263238 !important;
                color: #FFFFFF !important;
                border-color: #44555A !important;
                box-shadow: none !important;
                outline: none !important;
            }
            </style>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                form_pt_html = f"<html><head><style>@media print{{@page{{size:letter landscape;margin:1cm;}} body{{margin:0;padding:0;width:100% !important;font-family:sans-serif;}} .no-print{{display:none;}}}} table{{width:100% !important;border-collapse:collapse;margin-top:15px;table-layout:fixed;}} th{{background:#eee !important;border:1px solid black;padding:8px;font-size:11px;-webkit-print-color-adjust:exact;}} td{{border:1px solid black;padding:6px;font-size:10px;vertical-align:top;word-wrap:break-word;}}</style></head><body><div style='display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px solid black;padding-bottom:10px;'><div><h1 style='margin:0;font-size:18px;font-weight:900;'>Jabones y Productos Especializados</h1><p style='margin:0;font-size:10px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;'>distribucion y Logistica 2026</p></div><div style='text-align:right;'><h2 style='margin:0;font-size:16px;text-decoration:underline;'>Reporte de Envio de Muestras</h2><p style='margin:5px 0 0 0;font-size:12px;'><b>GENERADO: {date.today().strftime('%d/%m/%Y')}</b></p></div></div><table><thead><tr><th style='width:7%;'>FOLIO</th><th style='width:15%;'>SOLICITANTE</th><th style='width:25%;'>DESTINO / HOTEL</th><th style='width:33%;'>DETALLE DE PRODUCTOS</th><th style='width:10%;'>COSTO PROD.</th><th style='width:10%;'>FLETE</th></tr></thead><tbody>{filas_html}</tbody></table><div style='text-align:right;margin-top:20px;border-top:2px solid black;padding-top:10px;font-family:monospace;'><p style='margin:2px 0;'>TOTAL PRODUCTOS: <b>${t_prod:,.2f}</b></p><p style='margin:2px 0;'>TOTAL FLETES: <b>${t_flete:,.2f}</b></p><h3 style='margin:8px 0;font-size:20px;'>INVERSIÓN TOTAL: ${(t_prod+t_flete):,.2f}</h3></div></body></html>"
                if st.button(":material/print: IMPRIMIR REPORTE", type="primary", use_container_width=True, key="btn_imprimir_reporte_tab"):
                    components.html(f"{form_pt_html}<script>window.print();</script>", height=0)
            with c2:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_render.drop(columns=['FECHA_DT', 'MES_FILTRO']).to_excel(writer, index=False)
                st.download_button(f":material/download: EXCEL {mes_sel}", data=output.getvalue(), file_name=f"JYPESA_Muestras_{mes_sel}.xlsx", use_container_width=True, key="btn_download_excel_tab")
            with c3:
                if st.button(":material/update: ACTUALIZAR", use_container_width=True, key="btn_actualizar_tab"):
                    st.rerun()
        else:
            st.info("No hay registros todavía.")

    # ============================================================
    # TAB 2 — GESTIONAR FOLIOS EXISTENTES (guías, flete, reimpresión)
    # ============================================================
    with t2:
        subtitulo_pestana("GESTIÓN DE FOLIOS Y GUÍAS")
        contenedor_aviso = st.empty()
        if not df_actual.empty:
            st.markdown("""
            <style>
            div[data-testid="stButton"] button {
                background-color: #628290 !important;
                color: #FFFFFF !important;
                border: 1px solid #628290 !important;
                transition: all 0.3s ease-in-out !important;
            }
            div[data-testid="stButton"] button:hover {
                background-color: #4E6772 !important;
                color: #FFFFFF !important;
                border-color: #4E6772 !important;
            }
            </style>
            """, unsafe_allow_html=True)

            df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
            opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]

            fol_sel_texto = st.selectbox(
                "Seleccionar Folio para procesar (Logística):",
                opciones_folios,
                index=None,
                placeholder="Busca el folio que envió Ventas..."
            )

            datos_fol = None
            fol_edit = None

            if fol_sel_texto:
                fol_edit = int(fol_sel_texto.split(" - ")[0])
                datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]

                detalle_p_admin = ""
                for p in precios.keys():
                    cant_admin = datos_fol.get(p, 0)
                    if cant_admin > 0:
                        detalle_p_admin += f"• {int(cant_admin)} PZAS {str(p).upper()}<br>"

                estatus_admin = str(datos_fol.get('ESTATUS', 'NO SURTIDO')).upper()
                if estatus_admin == "DESPACHADO":
                    badge_admin = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:4px 10px; border-radius:12px; font-size:10px; font-weight:800; letter-spacing:1px; margin-top:8px;'>✓ DESPACHADO</div>"
                    borde_color = "#00FFAA"
                else:
                    badge_admin = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:4px 10px; border-radius:12px; font-size:10px; font-weight:800; letter-spacing:1px; margin-top:8px; box-shadow: 0 0 10px rgba(255,68,68,0.3);'>⚠️ NO SURTIDO</div>"
                    borde_color = "#FF4444"

                st.markdown(f"""
                <div style="background: #263238; border: 1px solid rgba(255,255,255,0.05); border-left: 6px solid {borde_color}; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; padding: 20px 30px; margin-top: 15px; margin-bottom: 5px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    <div style="flex: 1.2;">
                        <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:4px;">FOLIO A PROCESAR</div>
                        <div style="color: {borde_color}; font-family: monospace; font-size: 22px; font-weight: 900; line-height:1;">#{datos_fol['FOLIO']}</div>
                        <div style="color: rgba(255,255,255,0.5); font-size: 11px; margin-top: 4px;">{datos_fol['FECHA']}</div>
                        {badge_admin}
                    </div>
                    <div style="flex: 2.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.08);">
                        <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:4px;">DESTINO / HOTEL</div>
                        <div style="color: #FFFFFF; font-size: 14px; font-weight: 800; margin-bottom: 2px;">{str(datos_fol.get('NOMBRE DEL HOTEL','')).upper()}</div>
                        <div style="color: #38bdf8; font-size: 11px; font-weight: 700; margin-bottom: 4px;">Atn: {str(datos_fol.get('CONTACTO','')).upper()}</div>
                        <div style="color: rgba(255,255,255,0.5); font-size: 10px; line-height:1.4;">{str(datos_fol.get('DESTINO','')).upper()}</div>
                    </div>
                    <div style="flex: 2.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.08);">
                        <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:6px;">PRODUCTOS SOLICITADOS</div>
                        <div style="color: #FFFFFF; font-size: 10px; line-height: 1.6; opacity: 0.9;">{detalle_p_admin if detalle_p_admin else '<i>Sin detalle de productos</i>'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            st.markdown(
                "<p style='color: #00FFAA; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px;'>1. ASIGNAR DATOS DE ENVÍO</p>",
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                n_paq_nombre = st.selectbox(
                    "Nombre de Paquetería",
                    [
                        "AEREO",
                        "NO APLICA",
                        "TRES GUERRAS",
                        "ONE",
                        "POTOSINOS",
                        "CASTORES",
                        "FEDEX",
                        "PAQMEX",
                        "TINY PACK"
                    ],
                    index=None,
                    placeholder="Selecciona paquetería..."
                )

            with c2:
                n_tipo_pago = st.selectbox(
                    "Modalidad de Pago",
                    [
                        "NO APLICA",
                        "CREDITO",
                        "COBRO DESTINO"
                    ],
                    index=None,
                    placeholder="¿Cómo se paga?"
                )

            with c3:
                n_gui = st.text_input(
                    "Número de Guía"
                ).upper()

            c4, c5, c6 = st.columns([1, 1, 1])

            with c4:
                n_costo_guia = st.number_input(
                    "Costo de Flete ($)",
                    min_value=0.0
                )

            with c5:
                val_def_cajas = int(
                    datos_fol.get('CANTIDAD_TOTAL', 1)
                ) if datos_fol is not None else 1

                n_total_cajas = st.number_input(
                    "Cantidad Final de Cajas / Bultos",
                    min_value=1,
                    max_value=100,
                    value=max(val_def_cajas, 1),
                    step=1
                )

            st.info(
                "Verifica los datos antes de imprimir. "
                "La base de datos no se afecta hasta que guardes."
            )

            b1, b2, b3 = st.columns(3)

            with b1:
                btn_guardar = st.button(
                    ":material/update: GUARDAR Y ACTUALIZAR FOLIO",
                    use_container_width=True,
                    disabled=not fol_sel_texto
                )

            with b2:
                btn_imprimir = st.button(
                    ":material/print: IMPRIMIR FORMATO ACTUALIZADO",
                    use_container_width=True,
                    disabled=not fol_sel_texto
                )

            with b3:
                if fol_sel_texto and datos_fol is not None:
                    cant_etiquetas_sel = n_total_cajas

                    transporte_etq = (
                        n_paq_nombre
                        if n_paq_nombre
                        else datos_fol.get(
                            "PAQUETERIA_NOMBRE",
                            datos_fol.get(
                                "PAQUETERIA",
                                "TRES GUERRAS"
                            )
                        )
                    )

                    pdf_etq_bytes = generar_etiquetas_limpias(
                        reg_datos=datos_fol,
                        total_etqs=int(cant_etiquetas_sel),
                        factura_val=f"JYP-{int(datos_fol['FOLIO'])}",
                        transporte_val=transporte_etq
                    )

                    st.download_button(
                        label=":material/save: DESCARGAR ETIQUETA PDF",
                        data=pdf_etq_bytes,
                        file_name=f"Etiqueta_JYP-{int(datos_fol['FOLIO'])}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.button(
                        ":material/save: DESCARGAR ETIQUETA PDF",
                        use_container_width=True,
                        disabled=True
                    )

            if btn_guardar and datos_fol is not None:
                idx = df_actual.index[
                    df_actual['FOLIO'] == fol_edit
                ].tolist()[0]

                df_actual.at[idx, "PAQUETERIA_NOMBRE"] = n_paq_nombre
                df_actual.at[idx, "MODALIDAD_PAGO"] = n_tipo_pago
                df_actual.at[idx, "NUMERO_GUIA"] = n_gui
                df_actual.at[idx, "COSTO_GUIA"] = n_costo_guia
                df_actual.at[idx, "CANTIDAD_TOTAL"] = n_total_cajas
                df_actual.at[idx, "ESTATUS"] = "DESPACHADO"

                if subir_a_github(
                    df_actual,
                    sha_actual,
                    f"Logistica Folio {fol_edit}"
                ):
                    st.success(
                        f"FOLIO JYP-{fol_edit} GUARDADO"
                    )
                    time.sleep(1.5)
                    st.rerun()

            if btn_imprimir and datos_fol is not None:
                prods_re = []

                for p in precios.keys():
                    if p in datos_fol and datos_fol[p] > 0:
                        prods_re.append({
                            "desc": p,
                            "cant": int(datos_fol[p])
                        })

                paq_a_imprimir = (
                    n_paq_nombre
                    if n_paq_nombre
                    else datos_fol.get(
                        "PAQUETERIA_NOMBRE",
                        "S/P"
                    )
                )

                pago_a_imprimir = (
                    n_tipo_pago
                    if n_tipo_pago
                    else datos_fol.get(
                        "MODALIDAD_PAGO",
                        "PENDIENTE"
                    )
                )

                h_re = generar_html_impresion(
                    f"JYP-{int(datos_fol['FOLIO'])}",
                    datos_fol.get("PAQUETERIA", "ENVIO"),
                    datos_fol.get("TIPO_ENTREGA", "DOMICILIO"),
                    datos_fol["FECHA"],
                    "RIGOBERTO HERNANDEZ",
                    "3319753122",
                    datos_fol["SOLICITO"],
                    datos_fol["NOMBRE DEL HOTEL"],
                    "",
                    "",
                    "",
                    datos_fol["DESTINO"],
                    "",
                    datos_fol["CONTACTO"],
                    prods_re,
                    datos_fol.get(
                        "COMENTARIOS",
                        "RE-IMPRESIÓN DE LOGÍSTICA"
                    ),
                    paq_a_imprimir,
                    pago_a_imprimir,
                    total_cajas=n_total_cajas
                )

                components.html(
                    f"<html><body>{h_re}<script>window.print();</script></body></html>",
                    height=0
                )
        else:
            st.info("No hay registros todavía.")

    # ============================================================
    # TAB 3 — EDICIÓN TOTAL DE MATRIZ DE MUESTRAS
    # ============================================================
    with t3:
        subtitulo_pestana("EDICIÓN DE REGISTROS")
        st.markdown("### EDICIÓN TOTAL DE MATRIZ DE MUESTRAS")
        st.info("Modifica cualquier registro de la base de datos de manera directa. Los cambios se sincronizarán y actualizarán en GitHub al guardar.")

        if df_actual.empty:
            st.warning("No hay registros en la matriz de muestras para editar.")
        else:
            df_sorted_edit = df_actual.sort_values(by="FOLIO", ascending=False)

            opciones_edit = [
                f"Folio #{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']} ({r['FECHA']})"
                for _, r in df_sorted_edit.iterrows()
            ]

            folio_a_editar = st.selectbox(
                "Selecciona el Folio que deseas modificar o eliminar:",
                opciones_edit,
                index=None,
                placeholder="Escribe el folio o nombre del hotel...",
                key="select_folio_edicion_total"
            )

            if folio_a_editar:
                num_folio_sel = int(
                    folio_a_editar.split(" - ")[0].replace("Folio #", "")
                )

                idx_fila = df_actual.index[
                    df_actual["FOLIO"] == num_folio_sel
                ].tolist()[0]

                registro_sel = df_actual.loc[idx_fila]

                st.markdown("---")
                st.subheader(f"Editando: JYP-{num_folio_sel}")

                col_e1, col_e2, col_e3 = st.columns(3)

                with col_e1:
                    nuevo_hotel = st.text_input(
                        "Nombre del Hotel",
                        value=str(registro_sel.get("NOMBRE DEL HOTEL", "")),
                        key=f"hotel_{num_folio_sel}"
                    ).upper()

                    nuevo_solicito = st.text_input(
                        "Solicitante",
                        value=str(registro_sel.get("SOLICITO", "")),
                        key=f"solicito_{num_folio_sel}"
                    ).upper()

                    nuevo_estatus = st.selectbox(
                        "Estatus",
                        ["NO SURTIDO", "DESPACHADO"],
                        index=(
                            0
                            if str(registro_sel.get("ESTATUS", "NO SURTIDO")) == "NO SURTIDO"
                            else 1
                        ),
                        key=f"estatus_{num_folio_sel}"
                    )

                with col_e2:
                    nuevo_destino = st.text_area(
                        "Destino / Dirección",
                        value=str(registro_sel.get("DESTINO", "")),
                        key=f"destino_{num_folio_sel}"
                    ).upper()

                    nuevo_contacto = st.text_input(
                        "Contacto Receptor",
                        value=str(registro_sel.get("CONTACTO", "")),
                        key=f"contacto_{num_folio_sel}"
                    ).upper()

                with col_e3:
                    nueva_paqueteria = st.text_input(
                        "Paquetería",
                        value=str(
                            registro_sel.get(
                                "PAQUETERIA_NOMBRE",
                                registro_sel.get("PAQUETERIA", "")
                            )
                        ),
                        key=f"paqueteria_{num_folio_sel}"
                    ).upper()

                    nueva_guia = st.text_input(
                        "Número de Guía",
                        value=str(registro_sel.get("NUMERO_GUIA", "")),
                        key=f"guia_{num_folio_sel}"
                    ).upper()

                    nuevo_costo_guia = st.number_input(
                        "Costo Guía / Flete ($)",
                        min_value=0.0,
                        value=float(registro_sel.get("COSTO_GUIA", 0.0)),
                        key=f"costo_{num_folio_sel}"
                    )

                st.markdown("##### 📦 Modificar Cantidades de Productos")
                st.write("Ajusta las piezas de los productos incluidos en este folio:")

                nuevas_cantidades = {}
                cols_prods = st.columns(3)
                keys_precios = list(precios.keys())

                for i, prod in enumerate(keys_precios):
                    val_bruto = registro_sel.get(prod, 0)

                    try:
                        cant_actual = (
                            int(val_bruto)
                            if pd.notna(val_bruto) and str(val_bruto).strip() != ""
                            else 0
                        )
                    except (ValueError, TypeError):
                        cant_actual = 0

                    col_target = cols_prods[i % 3]

                    with col_target:
                        nuevas_cantidades[prod] = st.number_input(
                            f"{prod[:28]}",
                            min_value=0,
                            step=1,
                            value=cant_actual,
                            key=f"edit_{num_folio_sel}_{prod}"
                        )

                nuevo_comentario = st.text_area(
                    "Comentarios Adicionales",
                    value=str(registro_sel.get("COMENTARIOS", "")),
                    key=f"comentarios_{num_folio_sel}"
                ).upper()

                st.markdown("---")

                col_btn_1, col_btn_2 = st.columns([2, 1])

                with col_btn_1:
                    guardar_cambios = st.button(
                        "GUARDAR CAMBIOS EN ESTE FOLIO",
                        key=f"guardar_cambios_{num_folio_sel}",
                        use_container_width=True
                    )

                with col_btn_2:
                    eliminar_registro = st.button(
                        "ELIMINAR ESTE FOLIO",
                        key=f"eliminar_registro_{num_folio_sel}",
                        use_container_width=True
                    )

                if guardar_cambios:
                    total_cants = sum(nuevas_cantidades.values())

                    total_cost_p = sum(
                        qty * precios.get(p_key, 0)
                        for p_key, qty in nuevas_cantidades.items()
                    )

                    df_actual.at[idx_fila, "NOMBRE DEL HOTEL"] = nuevo_hotel
                    df_actual.at[idx_fila, "SOLICITO"] = nuevo_solicito
                    df_actual.at[idx_fila, "ESTATUS"] = nuevo_estatus
                    df_actual.at[idx_fila, "DESTINO"] = nuevo_destino
                    df_actual.at[idx_fila, "CONTACTO"] = nuevo_contacto
                    df_actual.at[idx_fila, "PAQUETERIA_NOMBRE"] = nueva_paqueteria
                    df_actual.at[idx_fila, "NUMERO_GUIA"] = nueva_guia
                    df_actual.at[idx_fila, "COSTO_GUIA"] = nuevo_costo_guia
                    df_actual.at[idx_fila, "CANTIDAD_TOTAL"] = total_cants
                    df_actual.at[idx_fila, "COSTO_TOTAL"] = round(total_cost_p, 2)
                    df_actual.at[idx_fila, "COMENTARIOS"] = nuevo_comentario

                    for p_key, qty in nuevas_cantidades.items():
                        df_actual.at[idx_fila, p_key] = qty

                    if subir_a_github(
                        df_actual,
                        sha_actual,
                        f"Edicion total Folio JYP-{num_folio_sel}"
                    ):
                        st.success(f"¡Folio JYP-{num_folio_sel} actualizado y sincronizado correctamente!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Error al sincronizar con GitHub. Verifica tus credenciales.")

                if eliminar_registro:
                    df_actual = df_actual.drop(idx_fila).reset_index(drop=True)

                    if subir_a_github(
                        df_actual,
                        sha_actual,
                        f"Eliminacion Folio JYP-{num_folio_sel}"
                    ):
                        st.success(f"¡El folio JYP-{num_folio_sel} ha sido eliminado permanentemente!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Error al eliminar el registro en GitHub.")


if __name__ == "__main__":
    main()
