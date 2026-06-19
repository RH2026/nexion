import streamlit as st
import pandas as pd
import io
import numpy as np
from github import Github
from datetime import timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Nexion: Dashboard KPIs", layout="wide")

# Mantenemos tus variables de estilo originales
vars_css = {"sub": "#54AFE7"}

@st.cache_data
def cargar_datos():
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("RH2026/nexion")
    contents = repo.get_contents("pedidos.csv", ref="main")
    
    df = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')), keep_default_na=False)
    for col in df.columns:
        df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None'], '').str.strip().str.upper()
    
    # Procesar fechas para cálculo
    for col in ['PROGRAMACION', 'FECHA DE ENVIO']:
        df[col] = pd.to_datetime(df[col].str.replace(r'[^0-9/]', '', regex=True), dayfirst=True, errors='coerce', format='mixed')
    return df

st.title("📊 Nexion: Dashboard de Control Logístico")

try:
    df = cargar_datos()
    df['MES_PROG'] = df['PROGRAMACION'].dt.to_period('M')
    meses = sorted(df['MES_PROG'].dropna().unique(), reverse=True)
    mes_sel = st.selectbox("Seleccionar Mes de Programación", options=[m.strftime('%Y-%m') for m in meses])
    
    # --- 2. LÓGICA DE KPI 24 HORAS ---
    # Filtro: Mes seleccionado + Exclusión de los que no tienen FECHA DE ENVIO
    df_vol = df[(df['MES_PROG'] == pd.Period(mes_sel, freq='M')) & (df['FECHA DE ENVIO'].notna())].copy()
    
    df_vol['Estado_KPI'] = df_vol.apply(lambda x: "A TIEMPO" if (x['FECHA DE ENVIO'] - x['PROGRAMACION']) <= timedelta(days=1) else "FUERA DE TIEMPO", axis=1)

    # Métricas
    tot_v = len(df_vol)
    ok_v = len(df_vol[df_vol['Estado_KPI'] == "A TIEMPO"])
    no_v = tot_v - ok_v

    # --- 3. INTERFAZ VISUAL (Estilo exacto de tu referencia) ---
    st.markdown(f'<div style="text-align:center;margin-bottom:30px;"><p style="color:{vars_css["sub"]};font-size:11px;letter-spacing:3px;font-weight:700;text-transform:uppercase;">Desempeño Despachos 24h — {mes_sel}</p></div>', unsafe_allow_html=True)
    
    c_v1, c_v2, c_v3 = st.columns(3)
    def render_modern_bar(valor, total, label, color):
        porcentaje = (valor / total * 100) if total > 0 else 0
        st.markdown(f"""
            <div style="background: rgba(26, 37, 47, 0.6); padding: 20px; border-radius: 15px; border: 1px solid #243441; text-align: center;">
                <p style="color: #A4B9C8; font-size: 10px; margin-bottom: 5px; font-weight: bold;">{label.upper()}</p>
                <h2 style="color: white; margin: 0; font-size: 24px;">{valor}</h2>
                <p style="color: {color}; font-size: 16px; margin-top: 5px; font-weight: bold;">{porcentaje:.1f}%</p>
                <div style="background-color: #0B1014; border-radius: 10px; height: 8px; width: 100%; margin-top: 10px;">
                    <div style="background-color: {color}; height: 8px; width: {porcentaje}%; border-radius: 10px; box-shadow: 0 0 10px {color}88;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with c_v1: render_modern_bar(tot_v, tot_v, "Total Facturas", "#5a8dee")
    with c_v2: render_modern_bar(ok_v, tot_v, "A Tiempo", "#39da8a")
    with c_v3: render_modern_bar(no_v, tot_v, "Fuera de Meta", "#ff5b5c")

    # --- 4. DETALLE CON SCROLL VERDE (Referencia exacta) ---
    st.markdown("<p style='font-size:12px; font-weight:bold; color:#54AFE7; letter-spacing:2px; margin-top:20px; margin-bottom:15px;'>🔍 DETALLE DE OPERACIÓN EN TIEMPO REAL</p>", unsafe_allow_html=True)
    
    df_vol['EMIS_STR'] = df_vol['PROGRAMACION'].dt.strftime('%d/%m/%Y').fillna("S/D")
    df_vol['ENVIO_STR'] = df_vol['FECHA DE ENVIO'].dt.strftime('%d/%m/%Y').fillna("S/D")
    
    alto_detalle = min(len(df_vol) * 90 + 20, 550)
    
    html_detalle = f"""
    <div style="font-family: 'Inter', sans-serif;">
        <style>
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.05); border-radius: 10px; }}
            ::-webkit-scrollbar-thumb {{ background: #2ecc71; border-radius: 10px; border: 2px solid #384A52; }}
            .card-detalle {{ background: #263238; border: 1px solid rgba(255,255,255,0.05); border-left: 5px solid; border-radius: 10px; padding: 12px 20px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; transition: 0.3s; }}
            .card-detalle:hover {{ border-color: #38bdf8 !important; background: #2d3b42; transform: translateX(5px); }}
        </style>
        {"".join([f'''
        <div class="card-detalle" style="border-left-color: {'#00FFAA' if row['Estado_KPI']=='A TIEMPO' else '#FF4B4B'};">
            <div><div style="font-size:8px; opacity:0.5; color:white;">PEDIDO</div><div style="color:#00FFAA; font-weight:800;">{row['FACTURA']}</div></div>
            <div><div style="font-size:8px; opacity:0.5; color:white;">PROGRAMACIÓN</div><div style="color:white;">{row['EMIS_STR']}</div></div>
            <div><div style="font-size:8px; opacity:0.5; color:white;">SALIDA ALMACÉN</div><div style="color:white;">{row['ENVIO_STR']}</div></div>
            <div style="color:{'#00FFAA' if row['Estado_KPI']=='A TIEMPO' else '#FF4B4B'}; font-weight:800;">{row['Estado_KPI']}</div>
        </div>''' for _, row in df_vol.iterrows()])}
    </div>
    """
    import streamlit.components.v1 as components
    components.html(html_detalle, height=alto_detalle, scrolling=True)

except Exception as e:
    st.error(f"Error en Nexion: {e}")










