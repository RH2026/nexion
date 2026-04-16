import os
import io
import re
import json
import time
import base64
import requests
import pandas as pd
import numpy as np
import streamlit as st
import pytz
from io import StringIO
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NEXION | Operaciones Locales", layout="wide", initial_sidebar_state="collapsed")

# --- VARIABLES DE ESTILO (ONIX & CYAN) ---
vars_css = {
    "bg": "#0B1114",
    "card": "#1A2226",
    "accent": "#00FFAA",
    "text": "#FFFFFF",
    "sub": "#8fa3b0",
    "border": "#333333"
}

# 2. CSS MAESTRO CONSOLIDADO
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    .main {{ background-color: {vars_css['bg']}; color: {vars_css['text']}; font-family: 'Inter', sans-serif; }}
    
    /* Títulos Ejecutivos */
    h3 {{ 
        color: {vars_css['text']} !important; 
        letter-spacing: 3px !important; 
        text-transform: uppercase; 
        font-size: 1rem !important;
        border-bottom: 1px solid {vars_css['border']};
        padding-bottom: 10px;
        margin-top: 25px !important;
    }}

    /* Botones Neón */
    div.stButton > button {{
        background-color: {vars_css['accent']} !important;
        color: {vars_css['bg']} !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        height: 3.5em !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }}
    div.stButton > button:hover {{
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(0, 255, 170, 0.4);
    }}

    /* Inputs y Selectores */
    .stTextInput>div>div>input, div[data-baseweb="select"] {{
        background-color: {vars_css['card']} !important;
        color: white !important;
        border: 1px solid {vars_css['border']} !important;
    }}

    /* Contenedor de Info */
    .info-box {{
        background-color: {vars_css['card']};
        padding: 15px;
        border-radius: 4px;
        border-left: 4px solid {vars_css['accent']};
        margin-bottom: 20px;
    }}

    /* Footer */
    .footer {{
        position: fixed;
        bottom: 0; left: 0; width: 100%;
        background-color: {vars_css['bg']};
        color: {vars_css['sub']};
        text-align: center;
        padding: 12px 0;
        font-size: 9px;
        letter-spacing: 2px;
        border-top: 1px solid {vars_css['border']};
    }}
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---
def registrar_acceso(usuario):
    archivo_log = "log_accesos.csv"
    zona_horaria = pytz.timezone('America/Mexico_City')
    ahora = datetime.now(zona_horaria).strftime("%Y-%m-%d %I:%M %p")
    nuevo_registro = pd.DataFrame([[usuario, ahora]], columns=["Usuario", "Fecha/Hora"])
    if not os.path.isfile(archivo_log):
        nuevo_registro.to_csv(archivo_log, index=False)
    else:
        nuevo_registro.to_csv(archivo_log, mode='a', header=False, index=False)

def descargar_matriz():
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "locales.csv"
    timestamp = int(time.time())
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?t={timestamp}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json", "Cache-Control": "no-cache"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        datos = response.json()
        content = base64.b64decode(datos['content']).decode('utf-8')
        df = pd.read_csv(StringIO(content))
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace(['nan', 'None', 'NaN', 'null'], '')
        return df, datos['sha']
    return None, None

def actualizar_github(df, sha, mensaje):
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "locales.csv"
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_content = df.to_csv(index=False)
    encoded = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    payload = {"message": mensaje, "content": encoded, "sha": sha}
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code == 200

# --- LÓGICA DE AUTENTICACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<br><br><h3 style='text-align: center; border:none;'>NEXION SECURE LOGIN</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            user_input = st.text_input("OPERATOR ID")
            pass_input = st.text_input("ACCESS KEY", type="password")
            if st.form_submit_button("VERIFY IDENTITY"):
                usuarios = st.secrets.get("usuarios", {})
                if user_input in usuarios and str(usuarios[user_input]) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = user_input
                    registrar_acceso(user_input)
                    st.rerun()
                else:
                    st.error("ACCESS DENIED")
    st.stop()

# --- INTERFAZ OPERATIVA (DIRECTA) ---
st.markdown(f"**OPERADOR:** {st.session_state.usuario_activo.upper()} | {datetime.now().strftime('%d/%m/%Y')}")

df, sha = descargar_matriz()

if df is not None:
    # SECCIÓN 1: CARGA
    st.markdown("<h3>1. SALIDA DE ALMACEN (CARGA)</h3>", unsafe_allow_html=True)
    disponibles = df[~df['TRIGGER'].isin(['EN RUTA', 'ENTREGADO'])]
    
    if not disponibles.empty:
        pedidos_sel = st.multiselect("SELECCIONAR FOLIOS:", options=disponibles['NÚMERO DE PEDIDO'].unique())
        if pedidos_sel:
            ref_k = str(pedidos_sel[0])
            f1 = st.camera_input("FOTO 1: PRODUCTO", key=f"c1_{ref_k}")
            if f1:
                f2 = st.camera_input("FOTO 2: UNIDAD", key=f"c2_{ref_k}")
                if f2:
                    f3 = st.camera_input("FOTO 3: ESTIBA", key=f"c3_{ref_k}")
                    if f3:
                        if st.button("CONFIRMAR SALIDA DE UNIDAD"):
                            with st.spinner("SINCRONIZANDO..."):
                                ahora_c = datetime.now().strftime('%Y-%m-%d %H:%M')
                                for p in pedidos_sel:
                                    idx = df[df['NÚMERO DE PEDIDO'] == str(p)].index
                                    df.loc[idx, 'TRIGGER'] = 'EN RUTA'
                                    df.loc[idx, 'FECHA DE ENVÍO'] = ahora_c
                                if actualizar_github(df, sha, f"Carga: {pedidos_sel}"):
                                    st.success("REGISTRO EXITOSO")
                                    time.sleep(1)
                                    st.rerun()
    else:
        st.info("NO HAY PENDIENTES EN ALMACEN")

    st.markdown("<br>", unsafe_allow_html=True)

    # SECCIÓN 2: ENTREGA
    st.markdown("<h3>2. ENTREGA EN DESTINO</h3>", unsafe_allow_html=True)
    en_ruta = df[df['TRIGGER'] == 'EN RUTA']
    
    if not en_ruta.empty:
        opciones = en_ruta.apply(lambda x: f"{x['NÚMERO DE PEDIDO']} | {x['NOMBRE DEL CLIENTE']}", axis=1)
        sel = st.selectbox("PEDIDO A ENTREGAR:", opciones)
        id_p = sel.split(" | ")[0].strip()
        dat = en_ruta[en_ruta['NÚMERO DE PEDIDO'] == id_p].iloc[0]
        
        st.markdown(f"""
            <div class="info-box">
                <p style="margin:0; font-size: 0.7rem; color: {vars_css['accent']}; font-weight: bold;">DESTINO:</p>
                <p style="margin:0; font-size: 1rem; font-weight: bold;">{dat['DESTINO']}</p>
                <p style="margin:10px 0 0 0; font-size: 0.7rem; color: {vars_css['accent']}; font-weight: bold;">DOMICILIO:</p>
                <p style="margin:0; font-size: 0.85rem;">{dat['DOMICILIO']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        f_ent = st.camera_input("EVIDENCIA FINAL", key=f"ce_{id_p}")
        obs = st.text_input("OBSERVACIONES:", key=f"obs_{id_p}")

        if st.button("FINALIZAR ENTREGA"):
            if f_ent:
                with st.spinner("GUARDANDO..."):
                    ahora_e = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    idx_f = df[(df['NÚMERO DE PEDIDO'] == id_p) & (df['TRIGGER'] == 'EN RUTA')].index
                    if not idx_f.empty:
                        df.loc[idx_f[0], 'FECHA DE ENTREGA REAL'] = ahora_e
                        df.loc[idx_f[0], 'TRIGGER'] = 'ENTREGADO'
                        df.loc[idx_f[0], 'INCIDENCIAS'] = obs
                        if actualizar_github(df, sha, f"Entrega: {id_p}"):
                            st.success("ENTREGA CONFIRMADA")
                            time.sleep(1)
                            st.rerun()
            else:
                st.error("EVIDENCIA FOTOGRAFICA REQUERIDA")
    else:
        st.info("NO HAY PEDIDOS EN RUTA")
else:
    st.error("ERROR DE CONEXIÓN CON REPOSITORIO")




# ── FOOTER FIJO (BRANDING XENOCODE) ────────────────────────
st.markdown(f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""", unsafe_allow_html=True)
