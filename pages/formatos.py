import streamlit as st

# Configuración de página con la estética que te gusta
st.set_page_config(page_title="NEXION - Icon Lab", layout="wide")

# Estilo CSS para el fondo oscuro (Onyx/Azulado) y manejo de iconos
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0B1114;
    }
    .icon-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        border: 1px solid #1E262C;
        border-radius: 15px;
        background: #11181D;
        transition: 0.3s;
    }
    .icon-container:hover {
        border-color: #00FFAA;
    }
    .icon-svg {
        width: 80px;
        height: 80px;
        fill: white;
    }
    h3 {
        color: #00FFAA !important;
        font-family: 'Courier New', monospace;
        margin-top: 15px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Diccionario de Iconos SVG
icons = {
    "DASHBOARD": '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M13,3V9H21V3H13M13,21H21V11H13V21M3,21H11V15H3V21M3,13H11V3H3V13Z" /></svg>',
    "LOGÍSTICA": '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M20,18H4V4H20M20,2H4C2.89,2 2,2.89 2,4V18C2,19.1 2.9,20 4,20H9V22H15V20H20C21.1,20 22,19.1 22,18V4C22,2.89 21.1,2 20,2M12,17L7,12H10V8H14V12H17L12,17Z" /></svg>',
    "CARGA DATA": '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M11,9H13V15H16L12,19L8,15H11V9M5,20V18H19V20H5M19,9H15V3H9V9H5L12,16L19,9Z" /></svg>',
    "REPORTES": '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M8,12V14H16V12H8M8,16V18H13V16H8Z" /></svg>'
}

st.title("🧪 Panel de Pruebas de Módulos")
st.write("Prueba cómo se ven estos iconos SVG con tu paleta de colores actual.")

# Crear columnas para los módulos
cols = st.columns(4)

for i, (name, svg_code) in enumerate(icons.items()):
    with cols[i]:
        st.markdown(
            f"""
            <div class="icon-container">
                {svg_code}
                <h3>{name}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

# Espaciador
st.markdown("---")
st.info("💡 Consejo: Estos iconos son 100% escalables. Puedes cambiar el tamaño en el CSS `.icon-svg`.")

















































