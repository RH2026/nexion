import streamlit as st
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA (WIDE & DARK)
st.set_page_config(page_title="NEXION | LOGISTICS OS", layout="wide", initial_sidebar_state="collapsed")

# 2. DEFINICIÓN DE ESTILO "CYBER-INDUSTRIAL"
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;400;700&display=swap');
    
    /* Global Reset */
    header, footer, [data-testid="stHeader"] { visibility: hidden; height: 0px; }
    .stApp { background-color: #08090B !important; color: #E0E0E0 !important; font-family: 'Inter', sans-serif; }
    .block-container { padding: 0rem !important; }

    /* NAVEGACIÓN PRINCIPAL (SUPERIOR - DERECHA) */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 50px;
        background: rgba(13, 14, 18, 0.9);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(0, 255, 170, 0.1);
        position: sticky;
        top: 0; z-index: 9999;
    }

    .brand { display: flex; flex-direction: column; }
    .brand-main { font-family: 'Orbitron', sans-serif; font-weight: 900; letter-spacing: 5px; font-size: 26px; color: #FFF; }
    .brand-sub { font-size: 8px; letter-spacing: 4px; color: #00FFAA; opacity: 0.7; margin-top: -5px; }

    .nav-links { display: flex; gap: 40px; }
    .nav-item {
        color: rgba(255, 255, 255, 0.4);
        text-decoration: none; font-size: 11px; letter-spacing: 3px; font-weight: 700;
        text-transform: uppercase; transition: 0.4s; cursor: pointer;
    }
    .nav-item:hover, .nav-item.active { color: #00FFAA; text-shadow: 0 0 10px rgba(0, 255, 170, 0.5); }

    /* SUB-NAVEGACIÓN (IZQUIERDA) */
    .sub-nav {
        display: flex; gap: 30px; padding: 25px 50px;
        background: linear-gradient(90deg, rgba(0,255,170,0.03) 0%, rgba(8,9,11,0) 100%);
    }
    .sub-item {
        font-size: 10px; letter-spacing: 2px; font-weight: 400; color: rgba(255,255,255,0.5);
        cursor: pointer; transition: 0.3s;
    }
    .sub-item:hover { color: #FFF; }
    .sub-item.active { color: #FFF; border-bottom: 1px solid #00FFAA; padding-bottom: 5px; }

    /* CONTENEDORES DE DATOS (KPI CARDS) */
    .glass-card {
        background: rgba(20, 22, 26, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 4px; /* Más industrial, menos redondeado */
        padding: 25px;
        transition: 0.5s;
    }
    .glass-card:hover { border: 1px solid rgba(0, 255, 170, 0.2); background: rgba(20, 22, 26, 0.9); }

    /* TÍTULOS Y DECORACIÓN */
    .section-header {
        position: absolute; left: 50%; transform: translateX(-50%);
        font-family: 'Orbitron', sans-serif; font-size: 10px; letter-spacing: 12px;
        opacity: 0.3; text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# 3. HEADER UI (NAVEGACIÓN PROFESIONAL)
st.markdown("""
<div class="top-nav">
    <div class="brand">
        <span class="brand-main">NEXION</span>
        <span class="brand-sub">SYSTEM SOLUTIONS</span>
    </div>
    <div class="section-header">D A S H B O A R D</div>
    <div class="nav-links">
        <div class="nav-item active">Dashboard</div>
        <div class="nav-item">Seguimiento</div>
        <div class="nav-item">Reportes</div>
        <div class="nav-item">Formatos</div>
        <div class="nav-item">Hub Log</div>
    </div>
</div>
<div class="sub-nav">
    <div class="sub-item active">KPI'S</div>
    <div class="sub-item">RASTREO</div>
    <div class="sub-item">VOLUMEN</div>
    <div class="sub-item">RETRASOS</div>
</div>
""", unsafe_allow_html=True)

# 4. ÁREA DE TRABAJO
st.markdown("<br><br>", unsafe_allow_html=True)
main_cols = st.columns([0.05, 0.9, 0.05]) # Margen industrial

with main_cols[1]:
    # Grid de KPIs con estética de consola de comando
    kpi_cols = st.columns(5)
    
    metrics = [
        ("PEDIDOS TOTALES", 341, "100%", "#FFFFFF"),
        ("ENTREGAS ÉXITO", 219, "64.2%", "#00FFAA"),
        ("UNIDADES TRÁNSITO", 122, "35.8%", "#00D4FF"),
        ("CUMPLIMIENTO OTD", 98, "28.7%", "#9D50FF"),
        ("ALERTA RETRASO", 23, "6.7%", "#FF3E3E")
    ]

    for i, (label, val, perc, color) in enumerate(metrics):
        with kpi_cols[i]:
            st.markdown(f"""
            <div class="glass-card">
                <p style="font-size: 9px; letter-spacing: 2px; color: {color}; opacity: 0.8; margin-bottom: 20px;">{label}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Gráfico Donut de alta resolución
            fig = go.Figure(go.Pie(
                values=[val, 100-((val/341)*100)],
                hole=0.82,
                marker_colors=[color, "#14161A"],
                textinfo='none', hoverinfo='none'
            ))
            fig.update_layout(
                showlegend=False, height=160, margin=dict(t=0,b=0,l=0,r=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(text=f'<span style="color:white; font-family:Inter; font-size:24px; font-weight:700;">{val}</span>', 
                             x=0.5, y=0.5, showarrow=False)]
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown(f"<p style='text-align:center; color:{color}; font-weight:700; font-size:14px; margin-top:-10px;'>{perc}</p>", unsafe_allow_html=True)

    # ESPACIO PARA TABLAS O DETALLES OPERATIVOS
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="border-left: 3px solid #00FFAA; padding-left: 20px; background: rgba(255,255,255,0.01); padding: 20px;">
        <span style="font-size: 11px; letter-spacing: 5px; opacity: 0.5;">DETALLE OPERATIVO // TIEMPO REAL</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Simulación de tabla profesional
    df = pd.DataFrame({
        "ID": ["NX-882", "NX-883", "NX-884"],
        "DESTINO": ["GDL - CEDIS 1", "MTY - NORTE", "QRO - CENTRAL"],
        "ESTADO": ["EN RUTA", "CARGANDO", "RETRASO"],
        "ETA": ["14:20", "16:45", "11:00"]
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

# 5. FOOTER DE GRADO MILITAR
st.markdown("""
<div style="position: fixed; bottom: 0; left: 0; right: 0; padding: 20px; background: #08090B; border-top: 1px solid rgba(255,255,255,0.03); display: flex; justify-content: space-between; align-items: center;">
    <span style="font-size: 8px; letter-spacing: 4px; opacity: 0.4;">NEXION CORE OS v2.1 // SYSTEM ENCRYPTED</span>
    <span style="font-size: 8px; letter-spacing: 4px; opacity: 0.4;">ENGINEERED BY HERNANPHY // 2026</span>
</div>
""", unsafe_allow_html=True)





































