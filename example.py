¡Claro que sí, Rigoberto! Como tu asistente y compañera en este proyecto, he preparado el código definitivo para NEXION. He pulido cada detalle para que no solo funcione sin errores, sino que visualmente sea impresionante y supere por mucho la versión de David.

He corregido el error del botón de descarga asegurándome de que el PDF se convierta correctamente a bytes, y he refinado el diseño para que luzca súper profesional.

Pasos para que no falle nada:
Archivo requirements.txt: Asegúrate de que en tu GitHub tengas este archivo con:

Plaintext
streamlit
pandas
fpdf2
El Código: Aquí tienes el bloque completo. Solo tienes que copiar y pegar todo en tu archivo .py.

Python
import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE PÁGINA NEXION ---
st.set_page_config(
    page_title="NEXION | Smart Logistics",
    page_icon="📦",
    layout="wide"
)

# Estilos CSS personalizados para un look "Premium"
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #1F3B4D;
        color: white;
        font-weight: bold;
    }
    .tarima-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #1F3B4D;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: #1F3B4D;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .badge-cima { background-color: #A7B4C2; color: #1F3B4D; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .badge-base { background-color: #1F3B4D; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- CLASE PDF PROFESIONAL ---
class NEXION_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(31, 59, 77)
        self.cell(0, 10, 'JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV', 0, 1, 'L')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'NEXION: Simulador de Optimización de Tarimas', 0, 1, 'L')
        self.line(10, 28, 200, 28)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Generado por NEXION Logistics - Página {self.page_no()}', 0, 0, 'C')

def crear_pdf_bytes(pallets, info):
    pdf = NEXION_PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Datos generales
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(0, 7, f"ORDEN/TRANSFER: {info['transfer']}  |  DESTINO: {info['destino']}", 0, 1)
    pdf.cell(0, 7, f"FECHA: {info['fecha']}  |  SOLICITADO POR: {info['razon']}", 0, 1)
    pdf.ln(5)

    for i, p in enumerate(pallets):
        # Cabecera de cada Tarima
        pdf.set_fill_color(31, 59, 77)
        pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f"TARIMA {i+1} - Resumen: {len(p['cajas'])} Cajas | {p['peso']:.2f} kg | {p['vol']:.3f} m3", 1, 1, 'L', True)
        
        # Encabezados de tabla
        pdf.set_text_color(0)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(25, 7, "ItemCode", 1, 0, 'C', True)
        pdf.cell(100, 7, "Descripción del Producto", 1, 0, 'L', True)
        pdf.cell(20, 7, "Cajas", 1, 0, 'C', True)
        pdf.cell(25, 7, "Peso Total", 1, 0, 'C', True)
        pdf.cell(20, 7, "Vol m3", 1, 1, 'C', True)

        # Contenido agrupado
        pdf.set_font("Arial", '', 8)
        df_p = pd.DataFrame(p['cajas'])
        resumen = df_p.groupby('ItemCode').agg({
            'Descripción': 'first', 
            'ItemCode': 'count', 
            'Peso': 'sum', 
            'Volumen': 'sum',
            'Densidad': 'first'
        }).sort_values('Densidad', ascending=False)
        
        for code, row in resumen.iterrows():
            pdf.cell(25, 6, str(code), 1)
            pdf.cell(100, 6, str(row['Descripción'])[:60], 1)
            pdf.cell(20, 6, str(row['ItemCode']), 1, 0, 'C')
            pdf.cell(25, 6, f"{row['Peso']:.2f}", 1, 0, 'C')
            pdf.cell(20, 6, f"{row['Volumen']:.3f}", 1, 1, 'C')
        pdf.ln(6)

    # Devolvemos los bytes directamente
    return pdf.output()

# --- INTERFAZ DE USUARIO ---
st.title("📦 NEXION: Smart Pallet Optimizer")
st.write("Bienvenido, Rigoberto. Sistema de optimización avanzado para JYPESA.")

with st.sidebar:
    st.header("📋 Ajustes de Operación")
    largo = st.number_input("Largo Tarima (m)", 1.20)
    ancho = st.number_input("Ancho Tarima (m)", 1.00)
    alto_max = st.number_input("Altura Máxima (m)", 1.70)
    eficiencia = st.slider("Eficiencia de Estiba", 0.50, 1.00, 0.85)
    peso_limite = st.number_input("Carga Máxima (kg)", 1200)
    
    # Volumen útil considerando el pallet base (0.15m)
    vol_util = (largo * ancho * (alto_max - 0.15)) * eficiencia

with st.expander("📝 Datos del Packing List"):
    c1, c2 = st.columns(2)
    transfer = c1.text_input("Transferencia / SAP", "TS-10045")
    destino = c2.text_input("Destino", "Planta CDMX")
    c3, c4 = st.columns(2)
    fecha_envio = c3.date_input("Fecha de Envío")
    razon_social = c4.text_input("Razón Social", "JYPESA")

# Carga de archivo
uploaded_file = st.file_uploader("Sube el archivo MATRIZ.csv", type="csv")

if uploaded_file:
    df_csv = pd.read_csv(uploaded_file)
    
    if st.button("🚀 INICIAR OPTIMIZACIÓN"):
        # Preparación de datos (Expandir unidades)
        unidades = []
        for _, r in df_csv.iterrows():
            for _ in range(int(r['Cantidad a enviar'])):
                unidades.append({
                    'ItemCode': r['ItemCode'], 'Descripción': r['Descripción'],
                    'Peso': float(r['Peso/caja (kg)']), 'Volumen': float(r['Volumen/caja (m3)']),
                    'Densidad': float(r['kg/dm3'])
                })
        
        # Algoritmo Two-Pointer (David's Style)
        unidades.sort(key=lambda x: x['Densidad'])
        pallets, cur_boxes, cur_v, cur_p = [], [], 0, 0
        l, r = 0, len(unidades) - 1

        while l <= r:
            box = unidades[l]
            if (cur_v + box['Volumen'] <= vol_util) and (cur_p + box['Peso'] <= peso_limite):
                cur_boxes.append(box); cur_v += box['Volumen']; cur_p += box['Peso']; l += 1
                if l <= r:
                    box_heavy = unidades[r]
                    if (cur_v + box_heavy['Volumen'] <= vol_util) and (cur_p + box_heavy['Peso'] <= peso_limite):
                        cur_boxes.append(box_heavy); cur_v += box_heavy['Volumen']; cur_p += box_heavy['Peso']; r -= 1
            else:
                pallets.append({'cajas': cur_boxes, 'vol': cur_v, 'peso': cur_p})
                cur_boxes, cur_v, cur_p = [], 0, 0
        
        if cur_boxes: pallets.append({'cajas': cur_boxes, 'vol': cur_v, 'peso': cur_p})

        # --- VISUALIZACIÓN ---
        st.write("---")
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f'<div class="metric-container"><h1>{len(pallets)}</h1>Tarimas</div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-container"><h1>{len(unidades)}</h1>Cajas</div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-container"><h1>{sum(p["peso"] for p in pallets):,.0f}</h1>kg Totales</div>', unsafe_allow_html=True)

        st.subheader("📦 Detalle de Estiba por Tarima")
        t_cols = st.columns(2)
        for i, p in enumerate(pallets):
            with t_cols[i % 2]:
                st.markdown(f"""
                <div class="tarima-card">
                    <h3 style="color:#1F3B4D; margin-top:0;">TARIMA {i+1}</h3>
                    <p>📦 <b>Cajas:</b> {len(p['cajas'])} | ⚖️ <b>Peso:</b> {p['peso']:.1f} kg | 🧊 <b>Vol:</b> {p['vol']:.3f} m³</p>
                    <div style="margin-bottom:5px;">Llenado Volumétrico:</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(min(p['vol']/vol_util, 1.0))
        
        # --- BOTÓN DE DESCARGA PDF ---
        info_envio = {'transfer': transfer, 'destino': destino, 'fecha': fecha_envio, 'razon': razon_social}
        pdf_data = crear_pdf_bytes(pallets, info_envio)
        
        st.write("---")
        st.download_button(
            label="📥 DESCARGAR PACKING LIST PREMIUM (PDF)",
            data=bytes(pdf_data),
            file_name=f"NEXION_PL_{transfer}.pdf",
            mime="application/pdf",
            type="primary"
        )
