import streamlit as st
import pandas as pd
import io
import streamlit.components.v1 as components
from github import Github
from datetime import timedelta, datetime

# --- CONFIGURACIÓN VISUAL Y RENDERING ---
st.set_page_config(page_title="Nexion: Dashboard KPIs", layout="wide")

# Estilos CSS compartidos (Onyx Blue & Elite)
st.markdown("""
    <style>
    .main { background-color: #0B1114; color: #FFFFFF; }
    .card-detalle { background: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-left: 5px solid #94a3b8; border-radius: 10px; padding: 12px 20px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .val-pedido { color: #00FFAA; font-family: monospace; font-size: 15px; font-weight: 800; }
    .badge-kpi { padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 800; }
    .st-entregado { background: rgba(0, 255, 170, 0.1); color: #00FFAA; border: 1px solid rgba(0, 255, 170, 0.2); }
    .st-fuera { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid rgba(255, 75, 75, 0.2); }
    </style>
    """, unsafe_allow_html=True)

# 1. CARGA ROBUSTA (Motor de tu módulo funcional)
@st.cache_data
def cargar_datos():
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("RH2026/nexion")
    contents = repo.get_contents("pedidos.csv", ref="main")
    
    df = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
    for col in df.columns:
        df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None'], '').str.strip().str.upper()
    
    for col in ['PROGRAMACION', 'FECHA DE ENVIO']:
        df[col] = pd.to_datetime(df[col].str.replace(r'[^0-9/]', '', regex=True), 
                                 dayfirst=True, errors='coerce', format='mixed')
    return df

st.title("📊 Nexion: Análisis de Despachos 24h")

try:
    df = cargar_datos()
    
    # --- FILTRO POR MES (PROGRAMACIÓN) ---
    df['MES_PROG'] = df['PROGRAMACION'].dt.to_period('M')
    meses = sorted(df['MES_PROG'].dropna().unique(), reverse=True)
    mes_sel = st.selectbox("Seleccionar Mes de Programación", options=[m.strftime('%Y-%m') for m in meses])
    df_vol = df[df['MES_PROG'] == pd.Period(mes_sel, freq='M')].copy()

    # --- LÓGICA DE KPI 24 HORAS ---
    df_vol = df_vol[df_vol['FECHA DE ENVIO'].notna()].copy()
    df_vol['DIFERENCIA'] = df_vol['FECHA DE ENVIO'] - df_vol['PROGRAMACION']
    df_vol['Estado_KPI'] = df_vol['DIFERENCIA'].apply(lambda x: "A TIEMPO" if x <= timedelta(days=1) else "FUERA DE TIEMPO")

    # --- MÉTRICAS DE TARJETA ---
    tot_v = len(df_vol)
    ok_v = len(df_vol[df_vol['Estado_KPI'] == "A TIEMPO"])
    no_v = tot_v - ok_v
    
    # Renderizado estilo Elite
    c_v1, c_v2, c_v3 = st.columns(3)
    def render_modern_bar(val, total, label, color):
        porc = (val / total * 100) if total > 0 else 0
        st.markdown(f"""
            <div style="background: rgba(26, 37, 47, 0.6); padding: 20px; border-radius: 15px; border: 1px solid #243441; text-align: center;">
                <p style="color: #A4B9C8; font-size: 10px; font-weight: bold;">{label.upper()}</p>
                <h2 style="color: white; margin: 0; font-size: 24px;">{val}</h2>
                <p style="color: {color}; font-weight: bold;">{porc:.1f}%</p>
            </div>
        """, unsafe_allow_html=True)
        
    render_modern_bar(tot_v, tot_v, "Total Pedidos", "#5a8dee")
    render_modern_bar(ok_v, tot_v, "A Tiempo (<=24h)", "#39da8a")
    render_modern_bar(no_v, tot_v, "Fuera de Meta", "#ff5b5c")

    # --- DETALLE DE OPERACIÓN (Estilo Tarjetas) ---
    st.markdown("<p style='color:#54AFE7; font-weight:bold; margin-top:30px;'>🔍 DETALLE EN TIEMPO REAL</p>", unsafe_allow_html=True)
    
    for _, row in df_vol.iterrows():
        estilo_badge = "st-entregado" if row['Estado_KPI'] == "A TIEMPO" else "st-fuera"
        st.markdown(f"""
            <div class="card-detalle" style="border-left-color: {'#00FFAA' if row['Estado_KPI']=='A TIEMPO' else '#FF4B4B'};">
                <div style="flex: 1;"><div style="font-size:8px; color:rgba(255,255,255,0.4);">PEDIDO</div><div class="val-pedido">{row['FACTURA']}</div></div>
                <div style="flex: 1;"><div style="font-size:8px; color:rgba(255,255,255,0.4);">PROGRAMACIÓN</div><div style="font-size:11px;">{row['PROGRAMACION'].strftime('%d/%m/%Y')}</div></div>
                <div style="flex: 1;"><div style="font-size:8px; color:rgba(255,255,255,0.4);">SALIDA ALMACÉN</div><div style="font-size:11px;">{row['FECHA DE ENVIO'].strftime('%d/%m/%Y')}</div></div>
                <div style="text-align: right;"><div class="badge-kpi {estilo_badge}">{row['Estado_KPI']}</div></div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error en el motor Nexion: {e}")













