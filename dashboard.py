import streamlit as st
import pandas as pd
from datetime import datetime
import datetime
import os
import streamlit.components.v1 as components
import requests
from io import StringIO
import plotly.graph_objects as go
import time
from github import Github
import json

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")

# ── TEMA FIJO (MODO OSCURO FORZADO - ONIX AZULADO) ──────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"
if "menu_main" not in st.session_state:
    st.session_state.menu_main = "TRACKING"
if "menu_sub" not in st.session_state:
    st.session_state.menu_sub = "GENERAL"

# Variables de diseño (Ajuste a Negro Ónix Azulado)
vars_css = {
    "bg": "#0E1117",      # Fondo Onix Azulado
    "card": "#1A1F2B",    # Fondos de tarjetas e inputs (Sutilmente más claro)
    "text": "#E0E6ED",    # Texto principal (Gris Platino)
    "sub": "#8892B0",     # Texto secundario
    "border": "#2D333B",  # Bordes y líneas
    "logo": "n1.png"      # Logo
}

# ── CSS MAESTRO INTEGRAL (REPARACIÓN DEFINITIVA Y SIN ERRORES) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* 1. Limpieza de Interfaz */
header, footer, [data-testid="stHeader"] {{
    visibility: hidden;
    height: 0px;
}}

/* APP BASE */
html, body {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
}}

.stApp {{ 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['text']} !important; 
    font-family: 'Inter', sans-serif !important; 
}}

/* CONTENEDOR PRINCIPAL */
.block-container {{ 
    padding-top: 0.8rem !important; 
    padding-bottom: 5rem !important; 
    background-color: {vars_css['bg']} !important;
}}

/* 2. ANIMACIÓN DE ENTRADA (BLINDADA) */
@keyframes fadeInUp {{ 
    from {{ opacity: 0; transform: translateY(15px); }} 
    to {{ opacity: 1; transform: translateY(0); }} 
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

/* 3. TÍTULOS Y OPERATIONAL QUERY */
h3, .op-query-text {{ 
    font-size: 11px !important; 
    letter-spacing: 8px !important; 
    text-align: center !important; 
    margin-top: 8px !important; 
    margin-bottom: 18px !important; 
    color: {vars_css['sub']} !important; 
    display: block !important; 
    width: 100% !important; 
}}

/* 4. BOTONES SLIM */
div.stButton > button {{ 
    background-color: {vars_css['card']} !important; 
    color: {vars_css['text']} !important; 
    border: 1px solid {vars_css['border']} !important; 
    border-radius: 2px !important; 
    font-weight: 700 !important; 
    text-transform: uppercase; 
    font-size: 10px !important; 
    height: 28px !important; 
    min-height: 28px !important; 
    line-height: 28px !important; 
    transition: all 0.2s ease !important; 
    width: 100% !important; 
}}

div.stButton > button:hover {{ 
    background-color: #ffffff !important; 
    color: #000000 !important; 
    border-color: #ffffff !important; 
}}

/* 5. INPUTS */
.stTextInput input {{ 
    background-color: {vars_css['card']} !important; 
    color: {vars_css['text']} !important; 
    border: 1px solid {vars_css['border']} !important; 
    border-radius: 2px !important; 
    height: 45px !important; 
    text-align: center !important; 
    letter-spacing: 2px; 
}}

/* DATA EDITOR */
[data-testid="stDataEditor"] {{
    background-color: {vars_css['card']} !important;
    border: 1px solid {vars_css['border']} !important;
}}

[data-testid="stDataEditor"] * {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
}}

/* 6. FOOTER FIJO */
.footer {{ 
    position: fixed; 
    bottom: 0 !important; 
    left: 0 !important; 
    width: 100% !important; 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['sub']} !important; 
    text-align: center; 
    padding: 12px 0px !important; 
    font-size: 9px; 
    letter-spacing: 2px; 
    border-top: 1px solid {vars_css['border']} !important; 
    z-index: 999999 !important; 
    animation: none !important; 
    transform: none !important; 
}}

/* 7. GRÁFICOS / IFRAME (PLOTLY + FRAPPE) */
.stPlotlyChart {{
    visibility: visible !important;
    opacity: 1 !important;
    min-height: 300px !important;
}}

iframe {{
    background-color: {vars_css['bg']} !important;
    border: 1px solid {vars_css['border']} !important;
}}
</style>
""", unsafe_allow_html=True)

# ── 4. SPLASH SCREEN ──────────────────────────────────────
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS", "PARSING LOGISTICS DATA", "SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:40px;height:40px;border:1px solid {vars_css['border']}; border-top:1px solid {vars_css['text']};border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:{vars_css['text']};">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.7)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER Y NAVEGACIÓN (LÍNEA 1) ──────────────────────────
header_zone = st.container()
with header_zone:
    c1, c2 = st.columns([1.5, 5.4], vertical_alignment="center")
    with c1:
        try:
            st.image(vars_css["logo"], width=120)
            st.markdown(f"<p style='font-size:8px; letter-spacing:2px; color:{vars_css['sub']}; margin-top:-22px; margin-left:2px;'>CORE INTELLIGENCE</p>", unsafe_allow_html=True)
        except:
            st.markdown(f"<h3 style='letter-spacing:4px; font-weight:800; margin:0; color:{vars_css['text']};'>NEXION</h3>", unsafe_allow_html=True)
    with c2:
        cols_main = st.columns(4)
        main_menus = ["TRACKING", "SEGUIMIENTO", "REPORTES", "FORMATOS"]
        for i, m in enumerate(main_menus):
            with cols_main[i]:
                seleccionado = st.session_state.menu_main == m
                btn_label = f"● {m}" if seleccionado else m
                if st.button(btn_label, use_container_width=True, key=f"main_{m}"):
                    st.session_state.menu_main = m
                    st.session_state.menu_sub = "GENERAL"
                    st.rerun()

# ── SUBMENÚS (LÍNEA 2 COMPLETA) ────────────────────────────
sub_map = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT", "QUEJAS"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT", "PAGOS"]
}

current_subs = sub_map.get(st.session_state.menu_main, [])
if current_subs:
    sub_zone = st.container()
    with sub_zone:
        cols_sub = st.columns(len(current_subs) + 4)
        for i, s in enumerate(current_subs):
            with cols_sub[i]:
                sub_activo = st.session_state.menu_sub == s
                sub_label = f"» {s}" if sub_activo else s
                if st.button(sub_label, use_container_width=True, key=f"sub_{s}"):
                    st.session_state.menu_sub = s
                    st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']}; margin:5px 0 15px; opacity:0.3;'>", unsafe_allow_html=True)

# ── CONTENEDOR DE CONTENIDO ──────────────────────────────────
main_container = st.container()
with main_container:
    # 1. TRACKING
    if st.session_state.menu_main == "TRACKING":
        st.markdown("<div style='margin-top: 5vh;'></div>", unsafe_allow_html=True)
        _, col_search, _ = st.columns([1, 1.6, 1])
        with col_search:
            st.markdown(f"<p class='op-query-text'>O P E R A T I O N A L &nbsp; Q U E R Y</p>", unsafe_allow_html=True)
            busqueda = st.text_input("REF", placeholder="INGRESE GUÍA O REFERENCIA...", label_visibility="collapsed")
            if st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True):
                st.toast(f"Buscando: {busqueda}")

    # 2. SEGUIMIENTO
    elif st.session_state.menu_main == "SEGUIMIENTO":
        if st.session_state.menu_sub == "TRK":
            st.subheader("SEGUIMIENTO > TRK")
            st.info("Espacio para contenido de Tracking Operativo")
        elif st.session_state.menu_sub == "GANTT":
            st.subheader("SEGUIMIENTO > GANTT")
            st.info("Espacio para contenido de Gantt")
            
                    
        elif st.session_state.menu_sub == "QUEJAS":
            st.subheader("SEGUIMIENTO > QUEJAS")
            st.info("Gestión de incidencias")

    # 3. REPORTES
    elif st.session_state.menu_main == "REPORTES":
        st.subheader(f"MÓDULO DE INTELIGENCIA > {st.session_state.menu_sub}")

    # 4. FORMATOS
    elif st.session_state.menu_main == "FORMATOS":
        if st.session_state.menu_sub == "SALIDA DE PT":
            st.subheader("FORMATOS > SALIDA DE PRODUCTO TERMINADO")
            # Aquí iría el contenido de Salida de PT
            
        elif st.session_state.menu_sub == "PAGOS":
            st.subheader("FORMATOS > CONTROL DE PAGOS")
            # Aquí iría el contenido de Pagos
            
        else:
            # ── AQUÍ INTEGRAMOS LA ANIMACIÓN DE BIENVENIDA ────────────────
            st.subheader("CENTRO DE DOCUMENTACIÓN")            
            
            st.components.v1.html(
                """
                <div id="matrix-container" style="width: 100%;">
                    <canvas id="matrix-canvas"></canvas>
                    <div class="overlay-text">NEXION CORE: ESPERANDO SELECCIÓN</div>
                </div>
            
                <style>
                    #matrix-container {
                        height: 450px; background: #0E1117; border-radius: 10px;
                        position: relative; border: 1px solid #1e2530; overflow: hidden;
                        width: 100%;
                    }
                    #matrix-canvas { display: block; width: 100%; }
                    
                    .overlay-text {
                        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                        color: #5d6d7e; 
                        font-family: 'Segoe UI', Tahoma, sans-serif;
                        font-weight: bold; letter-spacing: 10px; pointer-events: none;
                        font-size: 0.9rem; text-transform: uppercase;
                        text-align: center; width: 100%;
                        animation: pulse-text 4s infinite ease-in-out;
                        z-index: 10;
                    }
            
                    @keyframes pulse-text {
                        0%, 100% { opacity: 0.3; }
                        50% { opacity: 0.7; color: #3b82f6; }
                    }
                </style>
            
                <script>
                    const canvas = document.getElementById('matrix-canvas');
                    const ctx = canvas.getContext('2d');
                    const container = document.getElementById('matrix-container');
            
                    // FUNCIÓN CLAVE: Ajustar al ancho real del cliente (toda la pantalla)
                    function resize() {
                        canvas.width = container.clientWidth; 
                        canvas.height = 450;
                    }
                    resize();
            
                    const alphabet = "01XENOCODENEXION0101";
                    const fontSize = 14;
                    
                    // Calcular columnas basadas en el ancho TOTAL
                    let columns = Math.floor(canvas.width / fontSize);
                    const drops = [];
            
                    function initDrops() {
                        columns = Math.floor(canvas.width / fontSize);
                        for (let x = 0; x < columns; x++) {
                            drops[x] = {
                                currentX: x * fontSize,
                                baseX: x * fontSize,
                                y: Math.random() * -canvas.height,
                                speed: Math.random() * 1.5 + 1
                            };
                        }
                    }
                    initDrops();
            
                    let mouseX = -2000, mouseY = -2000;
                    container.addEventListener('mousemove', (e) => {
                        const rect = container.getBoundingClientRect();
                        mouseX = e.clientX - rect.left;
                        mouseY = e.clientY - rect.top;
                    });
            
                    // Escuchar si cambias el tamaño de la ventana
                    window.addEventListener('resize', () => {
                        resize();
                        initDrops();
                    });
            
                    function draw() {
                        ctx.fillStyle = '#0E1117';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        ctx.font = fontSize + 'px monospace';
            
                        drops.forEach(drop => {
                            const text = alphabet.charAt(Math.floor(Math.random() * alphabet.length));
                            const dx = drop.currentX - mouseX;
                            const dy = drop.y - mouseY;
                            const distance = Math.sqrt(dx*dx + dy*dy);
                            const forceArea = 140; 
            
                            if (distance < forceArea) {
                                const force = (forceArea - distance) / forceArea;
                                const direction = dx > 0 ? 1 : -1;
                                drop.currentX += direction * force * 20;
                                ctx.fillStyle = '#3b82f6'; 
                                ctx.shadowBlur = 12;
                                ctx.shadowColor = '#3b82f6';
                            } else {
                                drop.currentX += (drop.baseX - drop.currentX) * 0.1;
                                ctx.fillStyle = 'rgba(45, 55, 72, 0.15)'; 
                                ctx.shadowBlur = 0;
                            }
            
                            ctx.fillText(text, drop.currentX, drop.y);
                            drop.y += drop.speed;
            
                            if (drop.y > canvas.height) {
                                drop.y = -20;
                                drop.currentX = drop.baseX;
                            }
                        });
                    }
                    setInterval(draw, 30);
                </script>
                """, height=470
            )

# ── FOOTER FIJO ────────────────────────
st.markdown(f"""
<div class="footer">
    NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026
</div>
""", unsafe_allow_html=True)





























































































































































































































































































































































































































































































































































































