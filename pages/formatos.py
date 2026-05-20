import streamlit as st
import pandas as pd
from datetime import datetime
import time
import base64

# Configuración de página (optimizada para móvil)
st.set_page_config(page_title="Nexion Wallet", page_icon="💳", layout="centered")

# --- ESTILOS CSS (Silicon Valley Dark Mode) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
    }
    .saldo-card {
        background-color: #1E2127;
        border-left: 4px solid #00FFAA;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .saldo-titulo {
        color: #8892B0;
        font-size: 14px;
        margin-bottom: 5px;
    }
    .saldo-monto {
        color: #E6F1FF;
        font-size: 24px;
        font-weight: bold;
    }
    /* Estilo para mensaje de acceso denegado */
    .access-denied {
        text-align: center;
        color: #FF4B4B;
        margin-top: 50px;
        padding: 20px;
        border: 1px solid #FF4B4B;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE VARIABLES EN MEMORIA ---
if 'saldos' not in st.session_state:
    st.session_state.saldos = {"Bolsillo": 1500.00, "Banco": 12400.00, "Caja de Ahorro": 5000.00}
if 'movimientos' not in st.session_state:
    st.session_state.movimientos = []
if 'splash_completado' not in st.session_state:
    st.session_state.splash_completado = False
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# ==============================================================================
# ── FLUJO DE CONTROL MAESTRO ──
# ==============================================================================

# 1. SPLASH SCREEN (Animación de carga)
if not st.session_state.splash_completado:
    p = st.empty()
    mensajes = [
        "ESTABLISHING SECURE ACCESS...",
        "LOADING FINANCIAL DATA...",
        "SYNCHRONIZING NEXION WALLET...",
        "SYSTEM READY..."
    ]
    
    for m in mensajes:
        with p.container():
            st.markdown(f"""
            <div style="height:70vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
                <div style="width:80px;height:80px;border:2px solid rgba(255,255,255,0.05); border-top:2px solid #00FFAA; border-radius:50%;animation:spin 1s linear infinite; box-shadow: 0 0 15px rgba(0,255,170,0.3);"></div>
                <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:white;text-transform:uppercase;">{m}</p>
            </div>
            <style>
                @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
            </style>
            """, unsafe_allow_html=True)
            time.sleep(0.7)
            
    p.empty()
    st.session_state.splash_completado = True
    st.rerun()

# 2. PANTALLA DE LOGIN DE NEXION
elif not st.session_state.autenticado:
    # Intenta cargar el logo, si no existe, muestra el texto de Xenocode
    try:
        with open("n2.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{encoded}" width="180">'
    except FileNotFoundError:
        logo_html = '<h1 style="color: #00FFAA; font-family: monospace; margin: 0;">NEXION</h1>'

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; margin-bottom: 30px;">
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.form("login_form", clear_on_submit=False):
        user_input = st.text_input("USUARIO", placeholder="Introduce tu usuario")
        pass_input = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")
        
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        submit_button = st.form_submit_button("VERIFY IDENTITY", use_container_width=True)
        
        if submit_button:
            # ¡AQUÍ USAMOS TUS SECRETS!
            lista_usuarios = st.secrets.get("usuarios", {})
            
            nombres_reales = {
                "Rigoberto": "Rigoberto Hernández",
                "AGomez": "Ale Gomez",
                "JMoreno": "Jesus Moreno",
                "Cynthia": "Cynthia",
                "Brenda": "Brenda",
                "Fialko": "Fialko",
                "Atencion3G": "Sandra Yaneli",
                "Claudia": "Claudia",
                "Ruth": "Ruth Buenrostro",
                "Carlos": "Carlos Vazquez"
            }
            generos = {
                "Rigoberto": "M", "AGomez": "F", "JMoreno": "M", "Cynthia": "F", 
                "Brenda": "F", "Fialko": "M", "Yaneli": "F", "Claudia": "F", 
                "Arturo": "M", "Ruth": "F", "Carlos": "M"
            }
            
            if user_input in lista_usuarios and str(lista_usuarios[user_input]) == pass_input:
                st.session_state.autenticado = True
                st.session_state.usuario_activo = user_input
                
                nombre_completo = nombres_reales.get(user_input, user_input)
                gen = generos.get(user_input, "M")
                saludo = "BIENVENIDA" if gen == "F" else "BIENVENIDO"
                
                st.success(f"¡{saludo}!, {nombre_completo.upper()}") 
                time.sleep(1) 
                st.rerun()
            else:
                st.error("ERROR: ACCESS DENIED. INVALID CREDENTIALS.")

# 3. INTERFAZ DE WALLET (EXCLUSIVO PARA RIGOBERTO)
else:
    # ── VALIDACIÓN DE USUARIO ÉLITE ──
    if st.session_state.usuario_activo.upper() != "RIGOBERTO":
        st.markdown("""
            <div class="access-denied">
                <h2>⚠️ ACCESO DENEGADO</h2>
                <p>Este módulo es exclusivo de la dirección general.</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("⬅️ Volver", use_container_width=True):
             st.session_state.autenticado = False
             st.rerun()
             
    else:
        # --- EL CÓDIGO DE LA WALLET SÓLO SE EJECUTA SI ERES TÚ ---
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("<h3 style='color: #00FFAA;'>Mi Cartera (Xenocode)</h3>", unsafe_allow_html=True)
        with col2:
            if st.button("🔒 Salir"):
                st.session_state.autenticado = False
                st.session_state.splash_completado = False
                st.rerun()

        # VISOR DE SALDOS
        st.write("### Cuentas Activas")
        for cuenta, monto in st.session_state.saldos.items():
            st.markdown(f"""
                <div class="saldo-card">
                    <div class="saldo-titulo">{cuenta}</div>
                    <div class="saldo-monto">${monto:,.2f} MXN</div>
                </div>
            """, unsafe_allow_html=True)

        st.write("---")

        # CAPTURA RÁPIDA
        st.write("### Registrar Movimiento")
        with st.form("registro_rapido", clear_on_submit=True):
            monto = st.number_input("Cantidad ($)", min_value=0.01, format="%.2f", step=100.0)
            concepto = st.text_input("¿En qué fue? (Ej. Gasolina, Comida)")
            cuenta_sel = st.selectbox("¿De qué cuenta?", ["Bolsillo", "Banco", "Caja de Ahorro"])
            
            col_gasto, col_ingreso = st.columns(2)
            with col_gasto:
                btn_gasto = st.form_submit_button("📉 Gasto (-)", use_container_width=True)
            with col_ingreso:
                btn_ingreso = st.form_submit_button("📈 Ingreso (+)", use_container_width=True)
                
            if btn_gasto and monto and concepto:
                st.session_state.saldos[cuenta_sel] -= monto
                st.session_state.movimientos.append({"Fecha": datetime.now().strftime("%d/%m %H:%M"), "Tipo": "Gasto", "Concepto": concepto, "Monto": f"-${monto:,.2f}", "Cuenta": cuenta_sel})
                st.rerun()
                
            if btn_ingreso and monto and concepto:
                st.session_state.saldos[cuenta_sel] += monto
                st.session_state.movimientos.append({"Fecha": datetime.now().strftime("%d/%m %H:%M"), "Tipo": "Ingreso", "Concepto": concepto, "Monto": f"+${monto:,.2f}", "Cuenta": cuenta_sel})
                st.rerun()

        # HISTORIAL RECIENTE
        if st.session_state.movimientos:
            st.write("### Últimos Movimientos")
            df = pd.DataFrame(st.session_state.movimientos[::-1])
            st.dataframe(df, use_container_width=True, hide_index=True)






















































































































































