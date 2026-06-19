import streamlit as st
import pandas as pd
import io
from github import Github
from datetime import timedelta

st.set_page_config(page_title="Nexion: KPI Despacho", layout="wide")

# CSS para que todo el texto sea blanco y el fondo sea Elite
st.markdown("""
    <style>
    .kpi-card { background: #242c33; padding: 20px; border-radius: 12px; border: 1px solid #343e47; text-align: center; }
    .kpi-label { color: #A4B9C8; font-size: 10px; font-weight: 700; margin-bottom: 5px; }
    .kpi-value { color: white; font-size: 22px; font-weight: 700; }
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
    
    # Filtro: Mes + Exclusión de los que no tienen FECHA DE ENVIO
    df_vol = df[(df['MES_PROG'] == pd.Period(mes_sel, freq='M')) & (df['FECHA DE ENVIO'].notna())].copy()

    # Cálculo KPI (Tolerancia 24h)
    df_vol['Estado_KPI'] = df_vol.apply(lambda x: "A TIEMPO" if (x['FECHA DE ENVIO'] - x['PROGRAMACION']) <= timedelta(days=1) else "FUERA DE TIEMPO", axis=1)

    tot, ok, no = len(df_vol), len(df_vol[df_vol['Estado_KPI'] == "A TIEMPO"]), len(df_vol[df_vol['Estado_KPI'] != "A TIEMPO"])

    # Tarjetas KPI
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-label">TOTAL FACTURAS</div><div class="kpi-value">{tot}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-label">A TIEMPO</div><div class="kpi-value" style="color:#39da8a;">{ok}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-label">FUERA DE META</div><div class="kpi-value" style="color:#ff5b5c;">{no}</div></div>', unsafe_allow_html=True)

    # Detalle con Dataframe Nativo (sin scrolls extraños y con fuentes blancas)
    st.markdown("<h4 style='color:#5DADE2; margin-top:20px;'>🔍 DETALLE DE OPERACIÓN</h4>", unsafe_allow_html=True)
    
    # Preparamos dataframe para visualización limpia
    df_disp = df_vol[['FACTURA', 'PROGRAMACION', 'FECHA DE ENVIO', 'Estado_KPI']].copy()
    df_disp['PROGRAMACION'] = df_disp['PROGRAMACION'].dt.strftime('%d/%m/%Y')
    df_disp['FECHA DE ENVIO'] = df_disp['FECHA DE ENVIO'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        df_disp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "FACTURA": st.column_config.TextColumn("PEDIDO"),
            "Estado_KPI": st.column_config.TextColumn("ESTADO"),
        }
    )

except Exception as e:
    st.error(f"Error en el motor Nexion: {e}")











