from datetime import datetime
import io
import re
import time
import unicodedata
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas
import pandas as pd
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Logistics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── TEMA Y CSS MAESTROS ──────────────────────────────────────────
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
    "logo": "n1.png",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* --- ANIMACIONES DE ENTRADA --- */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(15px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

[data-testid="stVerticalBlock"] > div {{
    animation: fadeInUp 0.6s ease-out;
}}

/* --- OCULTAR ELEMENTOS DE STREAMLIT Y SIDEBAR --- */
header, footer, [data-testid="stHeader"] {{
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}}

[data-testid="collapsedControl"], 
[data-testid="stSidebar"], 
[data-testid="stToolbar"], 
.viewerBadge_container__1QSob, 
#MainMenu, 
button[kind="header"] {{
    visibility: hidden !important;
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

/* APP BASE */
html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}

.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 5rem !important;
    background-color: {vars_css['bg']} !important;
}}

/* BOTONES SLIM Y BOTONES DE DESCARGA */
div.stButton > button, div.stDownloadButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 32px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
    border-color: #00A3A3 !important;
}}

/*FOOTER FIJO */
.footer {{ 
    position: fixed; 
    bottom: 0 !important; 
    left: 0 !important; 
    width: 100% !important; 
    background-color: {vars_css['bg']} !important; 
    color: {vars_css['sub']} !important; 
    text-align: center; 
    padding: 12px 0px !important; 
    font-size: 9px; 
    letter-spacing: 2px; 
    border-top: 1px solid {vars_css['border']} !important; 
    z-index: 999999 !important; 
}}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. SISTEMA DE SEGURIDAD (VALIDACIÓN DE SESIÓN Y PERMISOS)
# ==========================================
if not st.session_state.get("autenticado", False):
    st.session_state.pagina_destino = "pages/etiquetas.py"
    st.switch_page("pages/log.py")

def verificar_permiso_pagina(modulo, submodulo=None):
    permisos = st.session_state.get("permisos", {})
    if st.session_state.get("usuario_activo", "").upper() == "RIGOBERTO":
        return True
        
    if not permisos.get(modulo.upper(), False) and not (submodulo and permisos.get(submodulo.upper(), False)):
        st.markdown(
            f"""
            <div style="
                background: {vars_css['card']}; 
                border: 1px solid {vars_css['border']}; 
                border-left: 5px solid #FFD700; 
                padding: 20px 25px; 
                border-radius: 8px; 
                width: 100%; 
                font-family: 'Inter', sans-serif; 
                color: white; 
                box-sizing: border-box; 
                margin-bottom: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <div style="width: 10px; height: 10px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 8px #FFD700;"></div>
                    <span style="color: #FFD700; font-size: 13px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">
                        ACCESS RESTRICTED // MÓDULO NO AUTORIZADO
                    </span>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 600; padding-left: 20px;">
                    No tienes permisos para acceder al módulo de <b style="color: white; text-transform: uppercase;">ETIQUETAS</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_regresar_m, _ = st.columns([1.5, 4])
        with col_regresar_m:
            if st.button("REGRESAR AL INICIO", key="btn_regresar_modulo", use_container_width=True):
                st.switch_page("pages/indicadores.py")
        st.stop()

# Blindaje correcto para ETIQUETAS (dentro de CENTRO DE DATOS)
verificar_permiso_pagina("CENTRO DE DATOS", "ETIQUETAS")


# ==========================================
# 3. FUNCIONES DE CONEXIÓN Y ETIQUETAS
# ==========================================
@st.cache_data(ttl=60)
def cargar_csv_github():
    try:
        repo = "RH2026/nexion"
        filename = "facturacion_moreno.csv"
        branch = "main"
        
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filename}"
        token = st.secrets["GITHUB_TOKEN"]
        headers = {"Authorization": f"token {token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
            df.columns = df.columns.astype(str).str.strip()
            return df
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def limpiar_parentesis(texto):
    return re.sub(r'\(.*?\)', '', str(texto)).strip()

def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
    texto = str(texto).upper()
    lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
    
    tamano_actual = tamano_max
    while len(lineas) > max_lineas and tamano_actual > 7:
        tamano_actual -= 0.5
        lineas = simpleSplit(texto, fuente, tamano_actual, ancho_max)
    
    c.setFont(fuente, tamano_actual)
    y_actual = y_inicio
    for line in lineas[:max_lineas]: 
        c.drawCentredString(x_centro, y_actual, line)
        y_actual -= interlineado
    return y_actual 

def generar_etiquetas_nexion(df_datos):
    output = io.BytesIO()
    w_rec, h_rec = 10.5 * cm, 7.5 * cm
    c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
    
    margen_h = 0.8 * cm
    w_util = w_rec - (2 * margen_h)
    x_centro = w_rec / 2

    if df_datos.empty:
        c.save()
        return output.getvalue()

    for index, row in df_datos.iterrows():
        try:
            cantidad_real = int(row['Quantity'])
            iteraciones = cantidad_real
        except: 
            continue 

        nombre_crudo = row.get('Nombre_Extran', row.get('Nombre_Ext', row.get('Nombre_Cliente', row.get('NOMBRE_CLIENTE', 'SIN NOMBRE'))))
        nombre_final = limpiar_parentesis(nombre_crudo)
        direccion_final = row.get('DIRECCION', row.get('Domicilio', row.get('DOMICILIO', 'DIRECCIÓN NO DISPONIBLE')))
        transporte_final = str(row.get('RECOMENDACION', row.get('Transporte', 'TRES GUERRAS')))
        factura_val = str(row.get('Factura', row.get('FOLIO', 'S/F')))

        for i in range(iteraciones):
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(0, 0, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)

            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_centro, h_rec - 0.3*cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            c.setFont("Helvetica", 5.5)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(c, info_contacto, x_centro, h_rec - 0.7*cm, w_util, "Helvetica", 5.5, 0.25*cm, max_lineas=1)
            
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(margen_h, h_rec - 0.95*cm, w_rec - margen_h, h_rec - 0.95*cm)
            c.setStrokeColorRGB(0, 0, 0)

            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_centro, h_rec - 1.8*cm, w_util, "Helvetica-Bold", 22, 0.65*cm, max_lineas=3)
            
            y_inicio_direccion = y_termino_nombre - 0.5*cm
            if y_inicio_direccion > 4.3*cm: y_inicio_direccion = 4.3*cm
            if y_inicio_direccion < 2.9*cm: y_inicio_direccion = 2.9*cm
            dibujar_texto_bloque_pro(c, direccion_final, x_centro, y_inicio_direccion, w_util, "Helvetica-Bold", 12.0, 0.45*cm, max_lineas=3)

            c.setLineWidth(0.6)
            y_linea_pie = 1.4*cm
            c.line(margen_h, y_linea_pie, w_rec - margen_h, y_linea_pie)
            
            x_col1 = margen_h + 0.1*cm         
            x_col2 = 5.25 * cm                 
            x_col3 = w_rec - margen_h - 2.8*cm 

            c.setFont("Helvetica-Bold", 8)
            c.drawString(x_col1, y_linea_pie - 0.4*cm, "FACTURA")
            c.drawCentredString(x_col2, y_linea_pie - 0.4*cm, "CAJAS")
            c.drawString(x_col3, y_linea_pie - 0.4*cm, "TRANSPORTE")
            
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_col1, y_linea_pie - 1.0*cm, factura_val)
            c.drawCentredString(x_col2, y_linea_pie - 1.0*cm, f"{i + 1} / {cantidad_real}")
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(x_col3, y_linea_pie - 1.0*cm, transporte_final[:16])
            
            c.showPage()

    c.save()
    return output.getvalue()


# ==========================================
# 4. HEADER Y MENÚ DE NAVEGACIÓN
# ==========================================
header_zone = st.container()
with header_zone:
    c1, c2, _, c4 = st.columns([1.5, 4.5, 0.2, 0.8], vertical_alignment="center")

    with c1:
        try:
            st.image(vars_css["logo"], width=160)
        except:
            st.write("**NEXION**")

    with c2:
        st.markdown(
            f"""
            <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
                <p style='font-size: 13px; letter-spacing: 5px; color: {vars_css['sub']}; margin: 0; font-weight: 500; text-transform: uppercase; text-align: center;'>
                    CENTRO DE DATOS <span style='color: #82D4E6; opacity: 0.8; margin: 0 15px;'>/</span> <span style='color: #FFD700; font-weight: 500;'>ETIQUETAS</span>
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with c4:
        if st.button("⬅ INICIO", use_container_width=True):
            st.switch_page("pages/indicadores.py")


# ==========================================
# 5. INTERFAZ PRINCIPAL (PESTAÑAS DE ETIQUETAS)
# ==========================================
def main():    
    tab1, tab2, tab3 = st.tabs([
        "CARGAR POR EXCEL (Lote)", 
        "BASE DE DATOS GITHUB", 
        "CAPTURA MANUAL"
    ])
    
    with tab1:
        st.subheader("Cargar Archivo Excel de Pedidos")
        archivo = st.file_uploader("Sube tu archivo .xlsx", type=["xlsx"], key="creador_etiquetas_excel")
        
        if archivo:
            try:
                df_excel = pd.read_excel(archivo, sheet_name=0)
                st.subheader("Vista previa de datos")
                st.dataframe(df_excel[['Quantity', 'DIRECCION', 'Factura']].head(5), use_container_width=True)

                if st.button("Generar Etiquetas desde Excel", use_container_width=True, key="btn_gen_excel"):
                    with st.spinner("Generando documento..."):
                        pdf_data = generar_etiquetas_nexion(df_excel)
                        if pdf_data:
                            st.success("¡Documento generado con éxito!")
                            st.download_button(
                                label="Descargar PDF de Etiquetas",
                                data=pdf_data,
                                file_name="etiquetas_nexion_excel.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="dl_excel"
                            )
            except Exception as e:
                st.error(f"Error al leer los pedidos: {e}")
    
    with tab2:
        st.subheader("Base de Datos - facturacion_moreno.csv")
        df_facturacion = cargar_csv_github()
        
        if not df_facturacion.empty:
            df_facturacion["Factura"] = df_facturacion["Factura"].astype(str)
            facturas_disponibles = df_facturacion["Factura"].unique()

            c_col1, c_col2 = st.columns(2)
            with c_col1:
                modo_busqueda = st.selectbox(
                    "🔍 Método de Selección", 
                    ["Seleccionar de la lista", "Escribir folio manual"],
                    key="modo_busq_etq_github"
                )

            num_factura_seleccionada = None
            with c_col2:
                if modo_busqueda == "Seleccionar de la lista":
                    num_factura_seleccionada = st.selectbox("📦 Selecciona Factura / Folio", facturas_disponibles, key="sel_factura_etq_github")
                else:
                    num_factura_seleccionada = st.text_input("✍️ Ingresa Folio Manual", key="txt_folio_manual_etq_github")

            if num_factura_seleccionada:
                df_encontrado = df_facturacion[df_facturacion["Factura"] == str(num_factura_seleccionada).strip()]
                
                if not df_encontrado.empty:
                    row_data = df_encontrado.iloc[0].copy()
                    
                    st.markdown("---")
                    st.info(f"📋 **Cliente encontrado:** {row_data.get('Nombre_Extran', row_data.get('Nombre_Cliente', 'SIN NOMBRE'))}")
                    
                    col_c, col_t = st.columns(2)
                    with col_c:
                        cajas_manual = st.number_input("📦 Cantidad de Cajas / Bultos", min_value=1, value=1, step=1, key="num_cajas_manual_db")
                    with col_t:
                        transporte_manual = st.text_input("🚛 Transporte / Paquetería", value=str(row_data.get('RECOMENDACION', row_data.get('Transporte', 'TRES GUERRAS'))), key="txt_transporte_manual_db")
                    
                    row_data['Quantity'] = cajas_manual
                    row_data['RECOMENDACION'] = transporte_manual
                    
                    df_procesar_individual = pd.DataFrame([row_data])

                    if st.button("Generar Etiqueta Individual", use_container_width=True, key="btn_gen_moreno"):
                        with st.spinner("Generando etiqueta..."):
                            pdf_data_moreno = generar_etiquetas_nexion(df_procesar_individual)
                            if pdf_data_moreno:
                                st.success("¡Etiqueta generada con éxito!")
                                st.download_button(
                                    label="Descargar PDF de Etiqueta",
                                    data=pdf_data_moreno,
                                    file_name=f"etiqueta_factura_{num_factura_seleccionada}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key="dl_moreno"
                                )
                else:
                    st.warning("El folio ingresado no se encontró en la base de datos de GitHub.")
        else:
            st.warning("No se pudieron cargar los datos de GitHub. Verifica tu token o conexión.")
    
    with tab3:
        st.markdown("""
            <div style="background-color: #263243; padding: 10px 15px; border-radius: 5px; color: #ffffff; font-size: 14px; margin-bottom: 20px;">
                Ingresa los datos del envío manualmente (sin necesidad de archivos).
            </div>
        """, unsafe_allow_html=True)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            manual_factura = st.text_input("NÚMERO DE FACTURA / FOLIO", value="235050", key="man_factura")
            manual_nombre = st.text_input("NOMBRE DEL CLIENTE / HOTEL", value="HOTEL EJEMPLO", key="man_nombre")
            manual_cajas = st.number_input("CANTIDAD DE CAJAS / BULTOS", min_value=1, value=1, step=1, key="man_cajas")

        with col_m2:
            manual_direccion = st.text_area("DIRECCIÓN COMPLETA DE DESTINO", value="Av. Principal #123, Col. Centro, C.P. 44100, Guadalajara, Jal.", height=107, key="man_direccion")
            manual_transporte = st.text_input("TRANSPORTE / PAQUETERÍA", value="TRES GUERRAS", key="man_transporte")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generar Etiqueta Manual", use_container_width=True, key="btn_gen_manual_libre"):
            if not manual_factura or not manual_nombre or not manual_direccion:
                st.error("Por favor completa los campos obligatorios (Factura, Nombre y Dirección).")
            else:
                dict_manual = {
                    'Factura': str(manual_factura),
                    'Nombre_Cliente': str(manual_nombre),
                    'DIRECCION': str(manual_direccion),
                    'Quantity': int(manual_cajas),
                    'RECOMENDACION': str(manual_transporte)
                }
                df_manual_pro = pd.DataFrame([dict_manual])

                with st.spinner("Generando etiqueta manual..."):
                    pdf_data_manual = generar_etiquetas_nexion(df_manual_pro)
                    if pdf_data_manual:
                        st.success("¡Etiqueta manual generada con éxito!")
                        st.download_button(
                            label="Descargar PDF de Etiqueta Manual",
                            data=pdf_data_manual,
                            file_name=f"etiqueta_manual_{manual_factura}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="dl_manual_libre"
                        )

if __name__ == "__main__":
    main()

# ── FOOTER FIJO ────────────────────────
st.markdown(
    f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
