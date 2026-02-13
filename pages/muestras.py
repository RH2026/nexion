import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. CONFIGURACIÓN MAESTRA
st.set_page_config(page_title="NEXION | CORE", layout="wide", initial_sidebar_state="collapsed")

# 2. VARIABLES DE DISEÑO (NEÓN & DARK)
accent = "#00FFAA"
bg_dark = "#1B1E23"
card_bg = "#262C34"

# 3. CSS PROFESIONAL (HARDCODED)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    /* Reset total */
    header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
    .stApp {{ background-color: {bg_dark} !important; font-family: 'Inter', sans-serif; }}
    .block-container {{ padding: 0rem !important; }}

    /* BARRA DE NAVEGACIÓN SUPERIOR (CUSTOM) */
    .nav-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 40px;
        background: rgba(27, 30, 35, 0.95);
        border-bottom: 1px solid rgba(255,255,255,0.05);
        position: sticky;
        top: 0;
        z-index: 9999;
    }}

    .logo-section {{ line-height: 1; }}
    .logo-main {{ font-weight: 900; letter-spacing: 4px; font-size: 24px; color: white; }}
    .logo-sub {{ font-size: 9px; letter-spacing: 3px; color: {accent}; opacity: 0.8; display: block; }}

    .center-title {{ 
        font-size: 11px; letter-spacing: 10px; font-weight: 400; 
        color: white; opacity: 0.5; text-transform: uppercase;
    }}

    /* EL CONTENEDOR DE TABS DE STREAMLIT (NIVEL 1) */
    div[data-testid="stTabNav"] {{
        background: transparent !important;
        justify-content: flex-end !important;
        margin-right: 20px;
    }}

    button[data-baseweb="tab"] {{
        font-size: 11px !important;
        letter-spacing: 2px !important;
        font-weight: 700 !important;
        color: rgba(255,255,255,0.4) !important;
        border: none !important;
        padding: 10px 20px !important;
    }}

    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {accent} !important;
        background: rgba(0, 255, 170, 0.05) !important;
        border-bottom: 2px solid {accent} !important;
    }}

    /* SUBMENÚS (NIVEL 2 - IZQUIERDA FORZADA) */
    .sub-nav-container {{
        padding: 0 40px;
        margin-top: 20px;
    }}

    div[data-testid="stVerticalBlock"] div[data-testid="stTabNav"] {{
        justify-content: flex-start !important;
    }}

    /* TARJETAS DE KPIS */
    .kpi-card {{
        background: {card_bg};
        border-radius: 10px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.03);
        text-align: center;
    }}
</style>
""", unsafe_allow_html=True)

# 4. HEADER UI (ESTÁTICO)
st.markdown(f'''
<div class="nav-bar">
    <div class="logo-section">
        <span class="logo-main">NEXION</span>
        <span class="logo-sub">SYSTEM SOLUTIONS</span>
    </div>
    <div class="center-title">D A S H B O A R D</div>
    <div style="width: 200px;"></div> </div>
''', unsafe_allow_html=True)

# 5. ESTRUCTURA DE MENÚS
# Menú Principal a la Derecha (Controlado por CSS superior)
menu_principal = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])

with menu_principal[0]:
    st.markdown('<div class="sub-nav-container">', unsafe_allow_html=True)
    # Submenú a la Izquierda
    submenu = st.tabs(["KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"])
    
    with submenu[0]: # VISTA DE KPIS (LOS 5 DONUTS)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Grid para los Donuts
        cols = st.columns(5)
        
        metrics = [
            ("PEDIDOS", 341, "100.0%", "#FFFFFF"),
            ("ENTREGADOS", 219, "64.2%", "#00FFAA"),
            ("TRÁNSITO", 122, "35.8%", "#00D4FF"),
            ("EN TIEMPO", 98, "28.7%", "#BB86FC"),
            ("RETRASO", 23, "6.7%", "#FF4B4B")
        ]

        for i, (label, value, perc, color) in enumerate(metrics):
            with cols[i]:
                fig = go.Figure(go.Pie(
                    values=[value, 100], # Simplificado para visual
                    hole=.75,
                    marker_colors=[color, "#2D343D"],
                    textinfo='none',
                    hoverinfo='none'
                ))
                fig.update_layout(
                    showlegend=False,
                    margin=dict(t=0, b=0, l=0, r=0),
                    height=150,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    annotations=[dict(text=str(value), x=0.5, y=0.5, font_size=20, font_color="white", font_family="Inter", showarrow=False)]
                )
                st.markdown(f"<p style='text-align:center; font-size:10px; letter-spacing:2px; opacity:0.6;'>{label}</p>", unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown(f"<p style='text-align:center; font-size:12px; font-weight:bold; color:{color};'>{perc}</p>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 6. FOOTER PROFESIONAL
st.markdown(f"""
<div style="position: fixed; bottom: 0; width: 100%; background: {bg_dark}; padding: 15px; border-top: 1px solid rgba(255,255,255,0.05); text-align: center;">
    <span style="font-size: 8px; letter-spacing: 3px; color: white; opacity: 0.4;">
        NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 // ENGINEERED BY HERNANPHY
    </span>
</div>
""", unsafe_allow_html=True)


































