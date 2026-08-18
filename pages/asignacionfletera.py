from datetime import datetime
import io
import re
import time
import unicodedata
import requests
import pandas as pd
import streamlit as st
import pytz
from auth import exigir_autenticacion

exigir_autenticacion("asignacionfletera")

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Almacén Historial",
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

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(15px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

header, footer, [data-testid="stHeader"] {{
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}}

[data-testid="collapsedControl"], 
[data-testid="stSidebar"], 
[data-testid="stToolbar"], 
.viewerBadge_container__1QSob, 
#MainMenu, 
button[kind="header"] {{
    visibility: hidden !important;
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}

.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 5rem !important;
    background-color: {vars_css['bg']} !important;
}}

div.stButton > button, div.stDownloadButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 32px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

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
}}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. SEGURIDAD Y PERMISOS
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/asignacionfletera.py"
    st.switch_page("pages/log.py")

# ==========================================
# 3. RENDER DE HISTORIAL PARA ALMACÉN (CON ESTATUS Y CAMPOS ESPECÍFICOS)
# ==========================================
def render_historial_almacen(data):
    if not data:
        st.markdown("""
            <div style="background-color: #212529; border: 1px solid #ff4d4d; border-radius: 6px; padding: 14px 18px; font-family: 'Inter', sans-serif; box-sizing: border-box; width: 100%;">
                <div style="font-size: 10px; color: #ff4d4d; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px;">AVISO DEL SISTEMA: SIN REGISTROS</div>
                <div style="font-size: 13px; color: #d1d5db; font-weight: 500;">No se encontraron facturas en la matriz de facturación para los filtros seleccionados.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    st.markdown('<p style="color:#FFFFFF; font-weight:800; letter-spacing:2px; font-size:12px; margin-bottom:12px;">HISTORIAL DE ALMACÉN // CONTROL DE FACTURAS</p>', unsafe_allow_html=True)

    for idx, item in enumerate(data):
        estatus_val = str(item.get('estatus', 'ENVIADA')).upper()
        
        # Estilos y colores según el estatus solicitado
        if estatus_val == "ENVIADA":
            color_borde = "#10b981"
            color_texto_estatus = "#34d399"
        elif estatus_val == "CANCELADA":
            color_borde = "#ef4444"
            color_texto_estatus = "#f87171"
        elif estatus_val == "DETENIDA":
            color_borde = "#f59e0b"
            color_texto_estatus = "#fbbf24"
        elif estatus_val == "DUPLICADA":
            color_borde = "#a855f7"
            color_texto_estatus = "#c084fc"
        else:
            color_borde = "#38bdf8"
            color_texto_estatus = "#7dd3fc"

        with st.container():
            # Encabezado de la tarjeta con Factura y Estatus
            st.markdown(f"""
            <div style="background-color: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-left: 5px solid {color_borde}; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 10px 15px; font-family: 'Inter', sans-serif; display: flex; justify-content: space-between; align-items: center; width: 100%; box-sizing: border-box;">
                <div>
                    <span style="font-size: 8px; text-transform: uppercase; color: #BFBFBF; font-weight: 800;">Factura / Folio: </span>
                    <b style="font-size: 13px; color: white; font-style: italic;">{item['factura']}</b>
                </div>
                <div>
                    <span style="font-size: 8px; text-transform: uppercase; color: #BFBFBF; font-weight: 800;">Estatus Almacén: </span>
                    <b style="font-size: 11px; color: {color_texto_estatus}; text-transform: uppercase;">{estatus_val}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Columnas con los campos requeridos: Factura, Nombre_Extran, Ciudad, EstadoCP y controles
            col1, col2, col3, col4, col5 = st.columns([1, 2.5, 2.5, 2, 1])
            
            with col1:
                chk = st.checkbox("Check", value=False, key=f"chk_alm_{idx}")
            with col2:
                st.markdown(f"<div style='font-size:11px; color:#7dd3fc; padding-top:6px;'><b>Cliente Extran:</b> {item['nombre_extran'] if item['nombre_extran'] else 'N/A'}</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div style='font-size:11px; color:#e2e8f0; padding-top:6px;'><b>Ciudad:</b> {item['ciudad']}</div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div style='font-size:11px; color:#fde047; padding-top:6px;'><b>Estado / CP:</b> {item['estado_cp']}</div>", unsafe_allow_html=True)
            with col5:
                if st.button("💾", key=f"btn_alm_{idx}", use_container_width=True):
                    if chk:
                        st.success(f"¡Marcado #{item['factura']}!")
                    else:
                        st.info(f"Guardado #{item['factura']}")
            
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

def main():
    col_titulo, col_btn_refrescar = st.columns([4, 1.2], vertical_alignment="center")
    with col_titulo:
        st.markdown("""
            <div style='text-align:left; margin-top:15px; margin-bottom:10px;'>
                <span style='color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;'>
                    HISTORIAL DE ALMACÉN // FACTURACIÓN
                </span>
            </div>
        """, unsafe_allow_html=True)
    with col_btn_refrescar:
        if st.button("ACTUALIZAR DATOS", key="btn_refrescar_almacen", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "facturacion.csv"
    
    current_t = int(time.time() * 1000)
    CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?_t={current_t}"

    @st.cache_data(ttl=60)
    def get_facturacion_data(url, token):
        headers = {"Authorization": f"token {token}"} if token else {}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text), encoding="utf-8-sig")
        return pd.DataFrame()

    df_raw = get_facturacion_data(CSV_URL, TOKEN)

    if not df_raw.empty:
        df_raw.columns = df_raw.columns.str.strip()

        # Mapeo de columnas normalizadas
        df_proc = pd.DataFrame()
        df_proc['factura'] = df_raw.get('Factura', df_raw.get('FACTURA', pd.Series(dtype=str))).fillna('').astype(str)
        df_proc['nombre_extran'] = df_raw.get('Nombre_Extran', df_raw.get('NOMBRE_EXTRAN', pd.Series(dtype=str))).fillna('').astype(str)
        
        # Buscamos campos de ciudad y estado/cp flexibles por si varían en el CSV
        df_proc['ciudad'] = df_raw.get('Ciudad', df_raw.get('CIUDAD', df_raw.get('DESTINO', pd.Series(dtype=str)))).fillna('').astype(str)
        df_proc['estado_cp'] = df_raw.get('EstadoCP', df_raw.get('ESTADOCP', df_raw.get('CP', pd.Series(dtype=str)))).fillna('').astype(str)
        
        # Estatus por defecto (puedes ajustarlo si tu CSV ya trae una columna de estatus)
        df_proc['estatus'] = df_raw.get('Estatus', df_raw.get('ESTATUS', pd.Series(['ENVIADA'] * len(df_raw)))).fillna('ENVIADA').astype(str)

        # ── ELIMINAR DUPLICADOS DE PARTIDAS: Quedarse solo con la PRIMERA LÍNEA de cada folio ──
        df_proc = df_proc.drop_duplicates(subset=['factura'], keep='first')
        df_proc = df_proc[df_proc['factura'] != ''].sort_values(by='factura', ascending=True, ignore_index=True)

        # Filtros tácticos de búsqueda para almacén
        f1, f2 = st.columns(2)
        with f1:
            facturas_opts = ["TODAS"] + sorted(list(df_proc['factura'].unique()))
            filtro_factura = st.selectbox("FILTRAR POR FACTURA", facturas_opts, key="filtro_factura_almacen")
        with f2:
            estatus_opts = ["TODOS", "ENVIADA", "CANCELADA", "DETENIDA", "DUPLICADA"]
            filtro_estatus = st.selectbox("FILTRAR POR ESTATUS", estatus_opts, key="filtro_estatus_almacen")

        df_filtrado = df_proc.copy()
        if filtro_factura != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['factura'] == filtro_factura]
        if filtro_estatus != "TODOS":
            df_filtrado = df_filtrado[df_filtrado['estatus'].str.upper() == filtro_estatus]

        data_completa = df_filtrado.to_dict('records')
    else:
        data_completa = []

    render_historial_almacen(data_completa)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# ── FOOTER FIJO ────────────────────────
st.markdown(
    f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
