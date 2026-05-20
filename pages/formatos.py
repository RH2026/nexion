import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import base64

# 1. CONFIGURACIÓN WIDE (PC y Móvil)
st.set_page_config(page_title="Nexion Wallet Pro", page_icon="📈", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (Ajustados para Wide) ---
st.markdown("""
    <style>
    /* Fondo menos fúnebre */
    .stApp { background-color: #1E2329; }
    
    /* Ocultar rastro de Streamlit/GitHub */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Campos de entrada ultra oscuros */
    div[data-baseweb="input"] > div {
        background-color: #0D1117 !important;
        border: 1px solid #2D333B !important;
        color: white !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #0D1117 !important;
        border: 1px solid #2D333B !important;
        color: white !important;
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background-color: #2D333B;
        padding: 20px;
        border-radius: 12px;
        border-top: 3px solid #00FFAA;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE DATOS ---
if 'saldos' not in st.session_state:
    st.session_state.saldos = {"Bolsillo": 2500.00, "Banco": 45000.00, "Caja de Ahorro": 15000.00}
if 'movimientos' not in st.session_state:
    # Datos de ejemplo para que los gráficos luzcan al inicio
    st.session_state.movimientos = [
        {"Fecha": "18/05 10:00", "Tipo": "Ingreso", "Concepto": "Nomina", "Monto": 5000.0, "Cuenta": "Banco"},
        {"Fecha": "19/05 14:00", "Tipo": "Gasto", "Concepto": "Comida", "Monto": -350.0, "Cuenta": "Bolsillo"}
    ]
if 'splash_completado' not in st.session_state:
    st.session_state.splash_completado = False
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# ==============================================================================
# ── FLUJO DE CONTROL ──
# ==============================================================================

# 1. SPLASH SCREEN
if not st.session_state.splash_completado:
    p = st.empty()
    for m in ["ESTABLISHING SECURE ACCESS...", "LOADING BIOMETRICS...", "SYNCHRONIZING CHARTS...", "SYSTEM READY..."]:
        with p.container():
            st.markdown(f"""
            <div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:80px;height:80px;border:2px solid rgba(255,255,255,0.05); border-top:2px solid #00FFAA; border-radius:50%;animation:spin 1s linear infinite;"></div>
                <p style="margin-top:40px;font-family:monospace;letter-spacing:5px;color:white;">{m}</p>
            </div>
            <style> @keyframes spin {{ to {{ transform: rotate(360deg); }} }} </style>
            """, unsafe_allow_html=True)
            time.sleep(0.6)
    p.empty()
    st.session_state.splash_completado = True
    st.rerun()

# 2. LOGIN (Usando tus Secrets)
elif not st.session_state.autenticado:
    _, col_login, _ = st.columns([1, 1, 1]) # Centrado en PC
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try:
            with open("n2.png", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                st.markdown(f'<div style="text-align:center"><img src="data:image/png;base64,{encoded}" width="180"></div>', unsafe_allow_html=True)
        except: st.markdown("<h1 style='text-align:center; color:#00FFAA;'>NEXION</h1>", unsafe_allow_html=True)

        with st.form("login_form"):
            user_input = st.text_input("USUARIO")
            pass_input = st.text_input("CONTRASEÑA", type="password")
            if st.form_submit_button("VERIFY IDENTITY", use_container_width=True):
                usuarios = st.secrets.get("usuarios", {"Rigoberto": "1234"}) # Mockup para testing
                if user_input in usuarios and str(usuarios[user_input]) == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_activo = user_input
                    st.rerun()
                else: st.error("ACCESS DENIED")

# 3. DASHBOARD WALLET (WIDE)
else:
    # Verificación exclusiva para Rigoberto
    if st.session_state.usuario_activo.upper() != "RIGOBERTO":
        st.error("ACCESO RESTRINGIDO")
        st.stop()

    # HEADER
    head1, head2 = st.columns([5, 1])
    with head1:
        st.markdown(f"<h1 style='color:#00FFAA; margin-bottom:0;'>Nexion Wallet Pro</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#8892B0;'>Terminal de {st.session_state.usuario_activo}</p>", unsafe_allow_html=True)
    with head2:
        if st.button("🔒 Cerrar"):
            st.session_state.autenticado = False
            st.rerun()

    st.write("---")

    # --- FILA 1: MÉTRICAS GENERALES ---
    m1, m2, m3, m4 = st.columns(4)
    total_general = sum(st.session_state.saldos.values())
    total_ingresos = sum([m['Monto'] for m in st.session_state.movimientos if m['Tipo'] == "Ingreso"])
    total_egresos = sum([abs(m['Monto']) for m in st.session_state.movimientos if m['Tipo'] == "Gasto"])

    m1.markdown(f"<div class='metric-card'><small>SALDO TOTAL</small><h2>${total_general:,.2f}</h2></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card' style='border-top-color:#00FFAA'><small>INGRESOS</small><h2>${total_ingresos:,.2f}</h2></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='metric-card' style='border-top-color:#FF4B4B'><small>EGRESOS</small><h2>${total_egresos:,.2f}</h2></div>", unsafe_allow_html=True)
    m4.markdown(f"<div class='metric-card' style='border-top-color:#8892B0'><small>MOVIMIENTOS</small><h2>{len(st.session_state.movimientos)}</h2></div>", unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)

    # --- FILA 2: GRÁFICOS ---
    g1, g2 = st.columns([1, 1.5])

    with g1:
        st.write("### Distribución de Fondos")
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(st.session_state.saldos.keys()),
            values=list(st.session_state.saldos.values()),
            hole=.6,
            marker_colors=['#00FFAA', '#1E2127', '#8892B0']
        )])
        fig_pie.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              font_color="white", margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        st.write("### Flujo de Efectivo")
        if st.session_state.movimientos:
            df_graph = pd.DataFrame(st.session_state.movimientos)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(name='Ingreso', x=df_graph['Fecha'], y=[m if m > 0 else 0 for m in df_graph['Monto']], marker_color='#00FFAA'))
            fig_bar.add_trace(go.Bar(name='Gasto', x=df_graph['Fecha'], y=[abs(m) if m < 0 else 0 for m in df_graph['Monto']], marker_color='#FF4B4B'))
            fig_bar.update_layout(barmode='stack', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                 font_color="white", height=300, margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig_bar, use_container_width=True)

    st.write("---")

    # --- FILA 3: ACCIONES Y TABLA ---
    c_form, c_table = st.columns([1, 2])

    with c_form:
        st.write("### Nueva Operación")
        with st.form("wallet_op", clear_on_submit=True):
            val_monto = st.number_input("Monto ($)", min_value=0.0, step=100.0)
            val_concepto = st.text_input("Descripción")
            val_cuenta = st.selectbox("Cuenta", list(st.session_state.saldos.keys()))
            
            f1, f2 = st.columns(2)
            if f1.form_submit_button("📉 GASTO", use_container_width=True):
                if val_monto > 0 and val_concepto:
                    st.session_state.saldos[val_cuenta] -= val_monto
                    st.session_state.movimientos.append({"Fecha": datetime.now().strftime("%d/%m %H:%M"), "Tipo": "Gasto", "Concepto": val_concepto, "Monto": -val_monto, "Cuenta": val_cuenta})
                    st.rerun()
            if f2.form_submit_button("📈 INGRESO", use_container_width=True):
                if val_monto > 0 and val_concepto:
                    st.session_state.saldos[val_cuenta] += val_monto
                    st.session_state.movimientos.append({"Fecha": datetime.now().strftime("%d/%m %H:%M"), "Tipo": "Ingreso", "Concepto": val_concepto, "Monto": val_monto, "Cuenta": val_cuenta})
                    st.rerun()

    with c_table:
        st.write("### Historial de Movimientos")
        if st.session_state.movimientos:
            df_final = pd.DataFrame(st.session_state.movimientos[::-1])
            # Aplicar formato de color a los montos
            def color_monto(val):
                color = '#00FFAA' if val > 0 else '#FF4B4B'
                return f'color: {color}'
            
            st.dataframe(df_final.style.applymap(color_monto, subset=['Monto']), 
                         use_container_width=True, hide_index=True)






















































































































































