import streamlit as st
import pandas as pd
import io
import numpy as np
from github import Github
from datetime import timedelta
import streamlit.components.v1 as components

# Configuración inicial
st.set_page_config(page_title="Nexion: KPI Despacho", layout="wide")

# CSS "Elite" con el efecto Hover que pediste
st.markdown("""
    <style>
    .main { background-color: #0B1114; }
    .kpi-card { background: #242c33; padding: 25px; border-radius: 15px; border: 1px solid #343e47; text-align: center; margin-bottom: 20px; transition: 0.3s; }
    .kpi-card:hover { border-color: #5DADE2; transform: translateY(-5px); }
    .kpi-label { color: #A4B9C8; font-size: 10px; font-weight: 700; letter-spacing: 2px; margin-bottom: 8px; }
    .kpi-value { color: white; font-size: 24px; font-weight: 700; }
    .kpi-pct { font-size: 12px; font-weight: 700; margin-bottom: 10px; }
    .bar-bg { background-color: #0B1014; border-radius: 10px; height: 5px; width: 100%; }
    .bar-fill { height: 5px; border-radius: 10px; }
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
    meses = sorted(df['MES_PROG'].dropna().unique(), reverse=True)
    mes_sel = st.selectbox("Seleccionar Mes de Programación", options=[m.strftime('%Y-%m') for m in meses])
    
    # Lógica: Filtrado de mes y exclusión de registros sin fecha de envío
    df_vol = df[(df['MES_PROG'] == pd.Period(mes_sel, freq='M')) & (df['FECHA DE ENVIO'].notna())].copy()

    # Cálculo KPI (24h de tolerancia)
    df_vol['Estado_KPI'] = df_vol.apply(lambda x: "A TIEMPO" if (x['FECHA DE ENVIO'] - x['PROGRAMACION']) <= timedelta(days=1) else "FUERA DE TIEMPO", axis=1)

    # Métricas
    tot = len(df_vol)
    ok = len(df_vol[df_vol['Estado_KPI'] == "A TIEMPO"])
    no = tot - ok

    # Tarjetas KPI (Estilo Elite)
    c1, c2, c3 = st.columns(3)
    def render_card(val, total, lab, col):
        porc = (val / total * 100) if total > 0 else 0
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{lab.upper()}</div><div class="kpi-value">{val}</div><div class="kpi-pct" style="color: {col};">{porc:.1f}%</div><div class="bar-bg"><div class="bar-fill" style="background-color: {col}; width: {porc}%;"></div></div></div>""", unsafe_allow_html=True)

    with c1: render_card(tot, tot, "Total Facturas", "#5a8dee")
    with c2: render_card(ok, tot, "A Tiempo", "#39da8a")
    with c3: render_card(no, tot, "Fuera de Meta", "#ff5b5c")

    # Renderizado con Scroll (Igual que tu código de referencia)
    df_vol['EMIS_STR'] = df_vol['PROGRAMACION'].dt.strftime('%d/%m/%Y').fillna("S/D")
    df_vol['ENVIO_STR'] = df_vol['FECHA DE ENVIO'].dt.strftime('%d/%m/%Y').fillna("S/D")
    
    alto_detalle = min(len(df_vol) * 90 + 20, 550)
    
    html_detalle = f"""
    <style>
        .card-detalle {{ background: #263238; border-left: 5px solid; border-radius: 10px; padding: 12px 20px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; transition: 0.3s; }}
        .card-detalle:hover {{ border-color: #38bdf8 !important; background: #2d3b42; transform: translateX(5px); }}
        .val-pedido {{ color: #00FFAA; font-weight: 800; }}
        .badge-kpi {{ font-weight: 800; font-size: 11px; }}
    </style>
    {"".join([f'''
    <div class="card-detalle" style="border-left-color: {'#00FFAA' if row['Estado_KPI']=='A TIEMPO' else '#FF4B4B'};">
        <div><div style="font-size:8px; opacity:0.5;">PEDIDO</div><div class="val-pedido">{row['FACTURA']}</div></div>
        <div><div style="font-size:8px; opacity:0.5;">PROGRAMACIÓN</div><div>{row['EMIS_STR']}</div></div>
        <div><div style="font-size:8px; opacity:0.5;">SALIDA ALMACÉN</div><div>{row['ENVIO_STR']}</div></div>
        <div class="badge-kpi" style="color: {'#00FFAA' if row['Estado_KPI']=='A TIEMPO' else '#FF4B4B'};">{row['Estado_KPI']}</div>
    </div>''' for _, row in df_vol.iterrows()])}
    """
    components.html(html_detalle, height=alto_detalle, scrolling=True)

except Exception as e:
    st.error(f"Error en Nexion: {e}")











