# ── ESTILOS CSS PARA REPLICAR TU IMAGEN ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* Reset y Fondo */
header, footer, [data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
.stApp {{ background-color: #1B1E23 !important; color: #FFFAFA !important; font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 2rem !important; }}

/* CONTENEDOR DE HEADER (LOGO + TITULO + MENU) */
.nav-container {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 0 20px;
    border-bottom: 1px solid #41485233;
    padding-bottom: 10px;
    position: relative;
}}

/* LOGO IZQUIERDA */
.logo-box {{
    text-align: left;
    line-height: 1.2;
}}
.logo-main {{ font-weight: 800; letter-spacing: 4px; font-size: 22px; color: #FFFAFA; }}
.logo-sub {{ font-size: 8px; letter-spacing: 3px; color: #FFFFFF; opacity: 0.6; display: block; }}

/* TITULO CENTRAL */
.center-title {{
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: 20px;
    font-size: 10px;
    letter-spacing: 8px;
    font-weight: 600;
    opacity: 0.8;
}}

/* MENU DERECHA (TABS NIVEL 1) */
div[data-testid="stTabNav"] > div[role="tablist"] {{
    justify-content: flex-end !important;
    border-bottom: none !important;
    gap: 10px;
}}

/* SUBSECCIONES (TABS NIVEL 2 - FORZAR IZQUIERDA) */
div[data-testid="stVerticalBlock"] div[data-testid="stTabNav"] > div[role="tablist"] {{
    justify-content: flex-start !important;
    margin-top: 30px !important;
}}

/* ESTILO DE PESTAÑAS (Mismo que tu imagen) */
button[data-baseweb="tab"] {{
    background-color: transparent !important;
    border: none !important;
    color: #FFFFFF !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    opacity: 0.4;
    padding: 10px 15px !important;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    opacity: 1 !important;
    border-bottom: 2px solid #00FFAA !important;
}}

div[data-baseweb="tab-highlight"] {{ background-color: #00FFAA !important; }}

/* FOOTER */
.footer-nexion {{ 
    position: fixed; bottom: 0; left: 0; width: 100%; 
    background-color: #1B1E23; color: #FFFFFF; 
    text-align: center; padding: 15px 0; font-size: 8px; letter-spacing: 3px;
    border-top: 1px solid #414852; opacity: 0.7;
}}
</style>
""", unsafe_allow_html=True)

# ── ESTRUCTURA VISUAL ──

# Header con Logo y Título Central
st.markdown('''
<div class="nav-container">
    <div class="logo-box">
        <span class="logo-main">NEXION</span>
        <span class="logo-sub">SYSTEM SOLUTIONS</span>
    </div>
    <div class="center-title">D A S H B O A R D</div>
    <div style="width: 300px;"></div> </div>
''', unsafe_allow_html=True)

# Menú Principal (Nivel 1 - Derecha por CSS)
tabs_n1 = st.tabs(["DASHBOARD", "SEGUIMIENTO", "REPORTES", "FORMATOS", "HUB LOG"])

with tabs_n1[0]:
    # Subsecciones (Nivel 2 - Izquierda por CSS)
    sub_tabs = st.tabs(["KPI'S", "RASTREO", "VOLUMEN", "RETRASOS"])
    
    with sub_tabs[0]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Aquí es donde pondríamos tus 5 Donut Charts para que se vea igual a la imagen
        st.info("Listo para insertar los Donuts de Pedidos, Entregados, etc.")

with tabs_n1[1]:
    st.write("Seguimiento Content")

# Footer
st.markdown('<div class="footer-nexion">NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026 // ENGINEERED BY HERNANPHY</div>', unsafe_allow_html=True)
































