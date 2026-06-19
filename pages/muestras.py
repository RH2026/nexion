import streamlit as st
import pandas as pd
import io
from github import Github
from datetime import timedelta
import streamlit.components.v1 as components

# Configuración de página
st.set_page_config(page_title="Nexion: Dashboard KPIs", layout="wide")

# --- CSS ELITE ---
st.markdown("""
    <style>
    .kpi-card { background: #242c33; padding: 15px; border-radius: 12px; border: 1px solid #343e47; text-align: center; margin-bottom: 20px; }
    .kpi-label { color: #A4B9C8; font-size: 9px; font-weight: 700; letter-spacing: 2px; margin-bottom: 5px; }
    .kpi-value { color: white; font-size: 18px; font-weight: 700; }
    .kpi-pct { font-size: 11px; font-weight: 700; margin-bottom: 8px; }
    .bar-bg { background-color: #0B1014; border-radius: 10px; height: 4px; width: 100%; }
    .bar-fill { height: 4px; border-radius: 10px; }
    .scroll-container { height: 550px; overflow-y: auto; padding-right: 10px; border: 1px solid #343e47; border-radius: 10px; background: #1a2228; }
    .card-detalle { background: #263238; border-left: 4px solid; border-radius: 8px; padding: 10px 15px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; transition: 0.3s; }
    .card-detalle:hover { border-color: #38bdf8 !important; background: #2d3b42; transform: translateX(3px); }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("RH2026/nexion")
    contents = repo.get_contents("pedidos.csv", ref="main")
    
    df = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
    for col in df.columns:
        df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None'], '').str.strip().str.upper()
    
    for col in ['PROGRAMACION', 'FECHA DE ENVIO']:
        df[col] = pd.to_datetime(df[col].str.replace(r'[^0-9/]', '', regex=True), dayfirst=True, errors='coerce', format='mixed')
    return df

st.title("📊 Nexion: Análisis de Despacho 24h")

try:
    df = cargar_datos()
    df['MES_PROG'] = df['PROGRAMACION'].dt.to_period('M')
    
    # --- FILTRO POR MES CON OPCIÓN "TODAS" ---
    meses_lista = sorted(df['MES_PROG'].dropna().unique(), reverse=True)
    mes_sel = st.selectbox("Seleccionar Periodo", options=["TODAS"] + [m.strftime('%Y-%m') for m in meses_lista])
    
    # Filtrado
    if mes_sel == "TODAS":
        df_vol = df[df['FECHA DE ENVIO'].notna()].copy()
    else:
        df_vol = df[(df['MES_PROG'] == pd.Period(mes_sel, freq='M')) & (df['FECHA DE ENVIO'].notna())].copy()

    # Validar si hay datos
    if df_vol.empty:
        st.info("No se encontraron datos registrados para el periodo seleccionado.")
    else:
        # Cálculo KPI (24h)
        df_vol['Estado_KPI'] = df_vol.apply(lambda x: "A TIEMPO" if (x['FECHA DE ENVIO'] - x['PROGRAMACION']) <= timedelta(days=1) else "FUERA DE TIEMPO", axis=1)
        
        tot, ok, no = len(df_vol), len(df_vol[df_vol['Estado_KPI'] == "A TIEMPO"]), len(df_vol[df_vol['Estado_KPI'] != "A TIEMPO"])

        # Tarjetas KPI
        c1, c2, c3 = st.columns(3)
        def render_card(val, total, lab, col):
            porc = (val / total * 100) if total > 0 else 0
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{lab.upper()}</div><div class="kpi-value">{val}</div><div class="kpi-pct" style="color: {col};">{porc:.1f}%</div><div class="bar-bg"><div class="bar-fill" style="background-color: {col}; width: {porc}%;"></div></div></div>""", unsafe_allow_html=True)

        with c1: render_card(tot, tot, "Total Facturas", "#5a8dee")
        with c2: render_card(ok, tot, "A Tiempo", "#39da8a")
        with c3: render_card(no, tot, "Fuera de Meta", "#ff5b5c")

        # Detalle
        st.markdown("<p style='font-size:11px; font-weight:bold; color:#54AFE7; letter-spacing:1px; margin-top:15px; margin-bottom:10px;'>🔍 DETALLE DE OPERACIÓN</p>", unsafe_allow_html=True)
        
        st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
        for _, row in df_vol.iterrows():
            borde_color = '#00FFAA' if row['Estado_KPI'] == 'A TIEMPO' else '#FF4B4B'
            st.markdown(f"""
                <div class="card-detalle" style="border-left-color: {borde_color};">
                    <div><div style="font-size:7px; opacity:0.5; color:white;">PEDIDO</div><div style="color:#00FFAA; font-weight:700; font-size:12px;">{row['FACTURA']}</div></div>
                    <div><div style="font-size:7px; opacity:0.5; color:white;">PROGRAMACIÓN</div><div style="color:white; font-size:10px;">{row['PROGRAMACION'].strftime('%d/%m/%Y')}</div></div>
                    <div><div style="font-size:7px; opacity:0.5; color:white;">SALIDA ALMACÉN</div><div style="color:white; font-size:10px;">{row['FECHA DE ENVIO'].strftime('%d/%m/%Y')}</div></div>
                    <div style="color:{borde_color}; font-weight:700; font-size:10px;">{row['Estado_KPI']}</div>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error en el motor Nexion: {e}")










