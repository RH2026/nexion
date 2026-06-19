import streamlit as st
import pandas as pd
import io
from github import Github
from datetime import timedelta
import streamlit.components.v1 as components

# Configuración de página
st.set_page_config(page_title="Nexion: Dashboard KPIs", layout="wide")

# --- CSS ELITE - FUENTES AJUSTADAS ---
st.markdown("""
    <style>
    .kpi-card { background: #242c33; padding: 15px; border-radius: 12px; border: 1px solid #343e47; text-align: center; margin-bottom: 20px; transition: 0.3s; }
    .kpi-card:hover { border-color: #5DADE2; transform: translateY(-3px); }
    .kpi-label { color: #A4B9C8; font-size: 9px; font-weight: 700; letter-spacing: 2px; margin-bottom: 5px; }
    .kpi-value { color: white; font-size: 18px; font-weight: 700; }
    .kpi-pct { font-size: 11px; font-weight: 700; margin-bottom: 8px; }
    .bar-bg { background-color: #0B1014; border-radius: 10px; height: 4px; width: 100%; }
    .bar-fill { height: 4px; border-radius: 10px; }
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
    
    # Filtro: Mes seleccionado + Exclusión de los que no tienen FECHA DE ENVIO
    df_vol = df[(df['MES_PROG'] == pd.Period(mes_sel, freq='M')) & (df['FECHA DE ENVIO'].notna())].copy()

    # Cálculo KPI (24h de tolerancia)
    df_vol['Estado_KPI'] = df_vol.apply(lambda x: "A TIEMPO" if (x['FECHA DE ENVIO'] - x['PROGRAMACION']) <= timedelta(days=1) else "FUERA DE TIEMPO", axis=1)

    tot, ok, no = len(df_vol), len(df_vol[df_vol['Estado_KPI'] == "A TIEMPO"]), len(df_vol[df_vol['Estado_KPI'] != "A TIEMPO"])

    st.markdown(f"<h3 style='text-align:center; color:#5DADE2; margin-bottom:20px; font-size:18px;'>DESEMPEÑO DESPACHOS 24H — {mes_sel}</h3>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    def render_card(val, total, lab, col):
        porc = (val / total * 100) if total > 0 else 0
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{lab.upper()}</div><div class="kpi-value">{val}</div><div class="kpi-pct" style="color: {col};">{porc:.1f}%</div><div class="bar-bg"><div class="bar-fill" style="background-color: {col}; width: {porc}%;"></div></div></div>""", unsafe_allow_html=True)

    with c1: render_card(tot, tot, "Total Facturas", "#5a8dee")
    with c2: render_card(ok, tot, "A Tiempo", "#39da8a")
    with c3: render_card(no, tot, "Fuera de Meta", "#ff5b5c")

    # Detalle con Scroll Verde ajustado
    st.markdown("<p style='font-size:11px; font-weight:bold; color:#54AFE7; letter-spacing:1px; margin-top:15px; margin-bottom:10px;'>🔍 DETALLE DE OPERACIÓN</p>", unsafe_allow_html=True)
    
    df_vol['EMIS_STR'] = df_vol['PROGRAMACION'].dt.strftime('%d/%m/%Y').fillna("S/D")
    df_vol['ENVIO_STR'] = df_vol['FECHA DE ENVIO'].dt.strftime('%d/%m/%Y').fillna("S/D")
    
    alto_detalle = min(len(df_vol) * 70 + 20, 500)
    
    html_detalle = f"""
    <div style="font-family: 'Inter', sans-serif;">
        <style>
            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-thumb {{ background: #2ecc71; border-radius: 10px; }}
            .card-detalle {{ background: #263238; border-left: 4px solid; border-radius: 8px; padding: 10px 15px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; transition: 0.3s; }}
            .card-detalle:hover {{ border-color: #38bdf8 !important; background: #2d3b42; transform: translateX(3px); }}
        </style>
        {"".join([f'''
        <div class="card-detalle" style="border-left-color: {'#00FFAA' if row['Estado_KPI']=='A TIEMPO' else '#FF4B4B'};">
            <div><div style="font-size:7px; opacity:0.5; color:white;">PEDIDO</div><div style="color:#00FFAA; font-weight:700; font-size:12px;">{row['FACTURA']}</div></div>
            <div><div style="font-size:7px; opacity:0.5; color:white;">PROGRAMACIÓN</div><div style="color:white; font-size:10px;">{row['EMIS_STR']}</div></div>
            <div><div style="font-size:7px; opacity:0.5; color:white;">SALIDA ALMACÉN</div><div style="color:white; font-size:10px;">{row['ENVIO_STR']}</div></div>
            <div style="color:{'#00FFAA' if row['Estado_KPI']=='A TIEMPO' else '#FF4B4B'}; font-weight:700; font-size:10px;">{row['Estado_KPI']}</div>
        </div>''' for _, row in df_vol.iterrows()])}
    </div>
    """
    components.html(html_detalle, height=alto_detalle, scrolling=True)

except Exception as e:
    st.error(f"Error en Nexion: {e}")










