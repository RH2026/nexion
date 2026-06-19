import streamlit as st
import pandas as pd
import io
from github import Github
from datetime import timedelta

# Configuración de página
st.set_page_config(page_title="Nexion: Dashboard KPIs", layout="wide")

# --- CSS ELITE ACTUALIZADO ---
st.markdown("""
    <style>
    /* Estilo de Tarjetas KPI */
    .kpi-card { 
        background: #242c33; padding: 25px; border-radius: 15px; border: 1px solid #343e47; 
        text-align: center; margin-bottom: 20px; transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .kpi-card:hover { border-color: #5DADE2; transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.3); }
    .kpi-label { color: #A4B9C8; font-size: 10px; font-weight: 700; letter-spacing: 2px; margin-bottom: 8px; }
    .kpi-value { color: white; font-size: 24px; font-weight: 700; margin-bottom: 2px; } /* Tamaño reducido */
    .kpi-pct { font-size: 12px; font-weight: 700; margin-bottom: 10px; }
    .bar-bg { background-color: #0B1014; border-radius: 10px; height: 5px; width: 100%; }
    .bar-fill { height: 5px; border-radius: 10px; transition: 0.5s; }
    
    /* Efecto Hover en filas de detalle */
    .row-detalle {
        background: #263238; border: 1px solid rgba(255,255,255,0.05); border-left: 5px solid; 
        border-radius: 8px; padding: 15px 20px; margin-bottom: 8px; 
        display: flex; justify-content: space-between; align-items: center;
        transition: 0.3s ease;
    }
    .row-detalle:hover { background: #2d3b42; transform: translateX(5px); border-color: #5DADE2 !important; cursor: pointer; }
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

st.title("📊 Nexion: Dashboard de Control Logístico")

try:
    df = cargar_datos()
    df['MES_PROG'] = df['PROGRAMACION'].dt.to_period('M')
    meses = sorted(df['MES_PROG'].dropna().unique(), reverse=True)
    mes_sel = st.selectbox("Seleccionar Mes de Programación", options=[m.strftime('%Y-%m') for m in meses])
    df_vol = df[df['MES_PROG'] == pd.Period(mes_sel, freq='M')].copy()

    df_vol = df_vol[df_vol['FECHA DE ENVIO'].notna()].copy()
    df_vol['Estado_KPI'] = df_vol.apply(lambda x: "A TIEMPO" if (x['FECHA DE ENVIO'] - x['PROGRAMACION']) <= timedelta(days=1) else "FUERA DE TIEMPO", axis=1)

    # Métricas
    tot, ok, no = len(df_vol), len(df_vol[df_vol['Estado_KPI'] == "A TIEMPO"]), len(df_vol[df_vol['Estado_KPI'] != "A TIEMPO"])

    st.markdown(f"<h3 style='text-align:center; color:#5DADE2; margin-bottom:30px;'>DESEMPEÑO DESPACHOS 24H — {mes_sel}</h3>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    def render_card(val, tot, lab, col):
        porc = (val / tot * 100) if tot > 0 else 0
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{lab.upper()}</div><div class="kpi-value">{val}</div><div class="kpi-pct" style="color: {col};">{porc:.1f}%</div><div class="bar-bg"><div class="bar-fill" style="background-color: {col}; width: {porc}%;"></div></div></div>""", unsafe_allow_html=True)

    with c1: render_card(tot, tot, "Total Facturas", "#5a8dee")
    with c2: render_card(ok, tot, "A Tiempo", "#39da8a")
    with c3: render_card(no, tot, "Fuera de Meta", "#ff5b5c")

    st.markdown("<p style='color:#54AFE7; font-weight:bold; margin-top:20px;'>🔍 DETALLE DE OPERACIÓN EN TIEMPO REAL</p>", unsafe_allow_html=True)
    
    for _, row in df_vol.iterrows():
        borde_color = '#00FFAA' if row['Estado_KPI'] == 'A TIEMPO' else '#FF4B4B'
        st.markdown(f"""
            <div class="row-detalle" style="border-left-color: {borde_color};">
                <div style="flex: 1;"><div style="font-size:8px; color:rgba(255,255,255,0.4);">PEDIDO</div><div style="color: #00FFAA; font-weight: 800;">{row['FACTURA']}</div></div>
                <div style="flex: 1;"><div style="font-size:8px; color:rgba(255,255,255,0.4);">PROGRAMACIÓN</div><div style="font-size:11px;">{row['PROGRAMACION'].strftime('%d/%m/%Y')}</div></div>
                <div style="flex: 1;"><div style="font-size:8px; color:rgba(255,255,255,0.4);">SALIDA ALMACÉN</div><div style="font-size:11px;">{row['FECHA DE ENVIO'].strftime('%d/%m/%Y')}</div></div>
                <div style="text-align: right;"><div style="color: {borde_color}; font-weight: 800; font-size: 11px;">{row['Estado_KPI']}</div></div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error en Nexion: {e}")












