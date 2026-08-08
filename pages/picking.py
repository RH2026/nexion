import base64
from datetime import datetime
import io
import os
import re
import time
import pandas as pd
import qrcode
from io import BytesIO
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Selector de Ubicaciones PT",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos idénticos al tono de tu sistema NEXION
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}
div.stButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 32px !important;
    width: 100% !important;
}}
div.stButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<h3 style='color: #00D4FF; letter-spacing: 2px;'>📦 GENERADOR Y LOCALIZADOR DE PARTIDAS POR FACTURA (QR)</h3>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 11px; opacity: 0.8;'>Agrupa facturas con múltiples partidas en un solo QR y escanéalo para ver la ubicación exacta en almacén de cada producto.</p>", unsafe_allow_html=True)

# ── CREACIÓN AUTOMÁTICA DE CSVs SI NO EXISTEN (PARA PRUEBAS) ──────────────────
ARCHIVO_UBICACIONES = "ubicaciones.csv"

if not os.path.exists(ARCHIVO_UBICACIONES):
    df_inicial_ub = pd.DataFrame({
        "CODIGO_PT": ["PT-001", "PT-015", "PT-042", "PT-003", "PT-010"],
        "DESCRIPCION": ["Jabon Rosa 100g", "Crema Facial 250ml", "Shampoo Manzanilla", "Jabon Neutro", "Gel Corporal"],
        "PASILLO": ["Pasillo 1", "Pasillo 2", "Pasillo 1", "Pasillo 3", "Pasillo 2"],
        "ESTANTE": ["Estante A-04", "Estante B-12", "Estante A-09", "Estante C-01", "Estante B-05"]
    })
    df_inicial_ub.to_csv(ARCHIVO_UBICACIONES, index=False, encoding="utf-8-sig")

# Cargar la base de datos de ubicaciones de forma segura
@st.cache_data(ttl=10)
def cargar_ubicaciones():
    try:
        df = pd.read_csv(ARCHIVO_UBICACIONES, encoding="utf-8-sig")
        df.columns = df.columns.str.strip().str.upper()
        return df
    except Exception:
        return pd.DataFrame()

df_ubicaciones = cargar_ubicaciones()

# Simulador de listado maestro de partidas (Facturas con varias líneas)
if "df_partidas" not in st.session_state:
    st.session_state.df_partidas = pd.DataFrame({
        "FACTURA": ["203040", "203040", "203040", "205060", "205060"],
        "CLIENTE": ["CLIENTE A", "CLIENTE A", "CLIENTE A", "CLIENTE B", "CLIENTE B"],
        "CODIGO_PT": ["PT-001", "PT-015", "PT-042", "PT-003", "PT-010"],
        "DESCRIPCION": ["Jabon Rosa 100g", "Crema Facial 250ml", "Shampoo Manzanilla", "Jabon Neutro", "Gel Corporal"],
        "CANTIDAD": [5, 2, 3, 10, 4]
    })

tab1, tab2 = st.tabs(["1️⃣ GENERAR QR POR FACTURA", "2️⃣ ESCANEAR Y LOCALIZAR PARTIDAS"])

# ── PESTAÑA 1: GENERAR QR CON TODAS LAS PARTIDAS DE LA FACTURA ───────────────
with tab1:
    st.markdown("###### Generar Código QR Agrupado")
    
    facturas_unicas = st.session_state.df_partidas["FACTURA"].unique().tolist()
    factura_seleccionada = st.selectbox("Selecciona o ingresa el Folio de Factura:", facturas_unicas, key="sel_factura_gen")
    
    if st.button("🚀 GENERAR QR DE FACTURA CON SUS PARTIDAS"):
        df_fact = st.session_state.df_partidas[st.session_state.df_partidas["FACTURA"] == factura_seleccionada]
        
        partidas_str = []
        for _, row in df_fact.iterrows():
            partidas_str.append(f"{row['CODIGO_PT']}:{row['CANTIDAD']}")
        
        contenido_qr = f"FACTURA:{factura_seleccionada}|PARTIDAS:" + ";".join(partidas_str)
        
        st.session_state["ultimo_contenido_qr"] = contenido_qr
        st.session_state["factura_activa_qr"] = factura_seleccionada
        
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(contenido_qr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        st.session_state["qr_imagen_bytes"] = buffered.getvalue()

    if "qr_imagen_bytes" in st.session_state and st.session_state.get("factura_activa_qr") == factura_seleccionada:
        st.success(f"¡QR generado con éxito para la factura {factura_seleccionada}!")
        st.image(st.session_state["qr_imagen_bytes"], width=250)
        
        st.markdown("**Partidas empaquetadas en este QR:**")
        df_mostrar = st.session_state.df_partidas[st.session_state.df_partidas["FACTURA"] == factura_seleccionada]
        st.dataframe(df_mostrar[["CODIGO_PT", "DESCRIPCION", "CANTIDAD"]], use_container_width=True)

        st.download_button(
            label="📥 DESCARGAR IMAGEN QR",
            data=st.session_state["qr_imagen_bytes"],
            file_name=f"QR_Factura_{factura_seleccionada}.png",
            mime="image/png"
        )

# ── PESTAÑA 2: ESCANEAR Y BUSCAR UBICACIONES ─────────────────────────────────
with tab2:
    st.markdown("###### Escáner / Validador de Ubicaciones en Almacén")
    st.markdown("Si quieres probar el ejemplo rápido, haz clic abajo para cargar el texto del QR de la factura 203040.")
    
    if st.button("📋 CARGAR TEXTO DE PRUEBA (FACTURA 203040)"):
        st.session_state["input_scan_qr_val"] = "FACTURA:203040|PARTIDAS:PT-001:5;PT-015:2;PT-042:3"
        st.rerun()

    qr_leido_input = st.text_input("Contenido del QR escaneado (o pégalo aquí):", value=st.session_state.get("input_scan_qr_val", ""), placeholder="Ej: FACTURA:203040|PARTIDAS:PT-001:5;PT-015:2", key="input_scan_qr")
    
    if st.button("📍 CONSULTAR UBICACIONES DE SURTIDO", type="primary"):
        if qr_leido_input:
            try:
                match_fac = re.search(r"FACTURA:([^|]+)", qr_leido_input)
                match_part = re.search(r"PARTIDAS:(.+)", qr_leido_input)
                
                if match_fac and match_part:
                    factura_id = match_fac.group(1)
                    items_crudos = match_part.group(1).split(";")
                    
                    st.markdown(f"<div style='background:rgba(0,212,255,0.1); border-left:4px solid #00D4FF; padding:10px; border-radius:4px; margin-bottom:15px;'><b>FACTURA DETECTADA: #{factura_id}</b></div>", unsafe_allow_html=True)
                    
                    datos_surtido = []
                    for item in items_crudos:
                        if ":" in item:
                            sku, cantidad = item.split(":")
                            
                            desc_row = st.session_state.df_partidas[st.session_state.df_partidas["CODIGO_PT"] == sku]
                            descripcion = desc_row["DESCRIPCION"].values[0] if not desc_row.empty else "Producto General"
                            
                            ub_row = df_ubicaciones[df_ubicaciones["CODIGO_PT"] == sku]
                            if not ub_row.empty:
                                pasillo = ub_row["PASILLO"].values[0]
                                estante = ub_row["ESTANTE"].values[0]
                            else:
                                pasillo = "Sin Asignar"
                                estante = "Por Definir"
                                
                            datos_surtido.append({
                                "SKU": sku,
                                "Descripción": descripcion,
                                "Cantidad": cantidad,
                                "Pasillo": pasillo,
                                "Estante": estante
                            })
                    
                    for row in datos_surtido:
                        st.markdown(
                            f"""
                            <div style="background: #2B343B; border: 1px solid #4B5D67; border-left: 5px solid #00FFAA; padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="color: #00FFAA; font-size: 11px; font-weight: 800;">📦 {row['SKU']} - {row['Descripción']}</span><br>
                                    <span style="font-size: 10px; color: rgba(255,255,255,0.7);">Cantidad a recolectar: <b>{row['Cantidad']} piezas</b></span>
                                </div>
                                <div style="text-align: right; background: rgba(0,255,170,0.1); padding: 6px 12px; border-radius: 4px; border: 1px solid rgba(0,255,170,0.3);">
                                    <span style="font-size: 9px; color: #00FFAA; display: block; font-weight: 800;">UBICACIÓN EN ALMACÉN</span>
                                    <span style="font-size: 13px; color: white; font-weight: 700;">{row['Pasillo']} | {row['Estante']}</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.error("El formato del QR escaneado no es válido para este módulo.")
            except Exception as e:
                st.error(f"Error al procesar el código: {str(e)}")
        else:
            st.warning("Por favor ingresa o escanea el contenido del código QR.")
