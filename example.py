import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NEXION | Smart Logistics", page_icon="📦", layout="wide")

# Diseño visual avanzado con CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
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
    .stProgress > div > div > div > div { background-color: #1F3B4D; }
    </style>
""", unsafe_allow_html=True)

# --- CLASE PDF PROFESIONAL ---
class NEXION_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(31, 59, 77)
        self.cell(0, 10, 'JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV', 0, 1, 'L')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'NEXION: Reporte de Optimización de Carga', 0, 1, 'L')
        self.line(10, 28, 200, 28)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'NEXION Logistics System - Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_final(pallets, info):
    pdf = NEXION_PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, f"ORDEN: {info['transfer']} | DESTINO: {info['destino']}", 0, 1)
    pdf.cell(0, 7, f"FECHA: {info['fecha']} | CLIENTE: {info['razon']}", 0, 1)
    pdf.ln(5)

    for i, p in enumerate(pallets):
        pdf.set_fill_color(31, 59, 77); pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f"TARIMA {i+1} - Peso: {p['peso']:.2f} kg | Vol: {p['vol']:.3f} m3", 1, 1, 'L', True)
        
        pdf.set_text_color(0); pdf.set_fill_color(245, 245, 245)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(30, 7, "ItemCode", 1, 0, 'C', True)
        pdf.cell(100, 7, "Descripción", 1, 0, 'L', True)
        pdf.cell(20, 7, "Cajas", 1, 0, 'C', True)
        pdf.cell(20, 7, "Peso Sub.", 1, 0, 'C', True)
        pdf.cell(20, 7, "Vol m3", 1, 1, 'C', True)

        pdf.set_font("Arial", '', 8)
        df_p = pd.DataFrame(p['cajas'])
        resumen = df_p.groupby('ItemCode').agg({'Descripción':'first', 'ItemCode':'count', 'Peso':'sum', 'Volumen':'sum'})
        
        for code, row in resumen.iterrows():
            pdf.cell(30, 6, str(code), 1)
            pdf.cell(100, 6, str(row['Descripción'])[:60], 1)
            pdf.cell(20, 6, str(row['ItemCode']), 1, 0, 'C')
            pdf.cell(20, 6, f"{row['Peso']:.1f}", 1, 0, 'C')
            pdf.cell(20, 6, f"{row['Volumen']:.3f}", 1, 1, 'C')
        pdf.ln(6)
    
    # Retornar los bytes del PDF
    return pdf.output()

# --- INTERFAZ ---
st.title("📦 NEXION: Smart Pallet Optimizer")

with st.sidebar:
    st.header("⚙️ Configuración Logística")
    largo = st.number_input("Largo (m)", 1.20)
    ancho = st.number_input("Ancho (m)", 1.00)
    alto_max = st.number_input("Alto Máx (m)", 1.70)
    eficiencia = st.slider("Factor Eficiencia", 0.50, 1.00, 0.85)
    peso_limite = st.number_input("Carga Máx (kg)", 1200)
    vol_util = (largo * ancho * (alto_max - 0.15)) * eficiencia

with st.expander("📝 Información del Reporte", expanded=True):
    c1, c2 = st.columns(2)
    transfer = c1.text_input("Transferencia", "TS-102030")
    destino = c2.text_input("Destino", "Planta Jalisco")
    c3, c4 = st.columns(2)
    fecha_envio = c3.date_input("Fecha de Salida")
    razon = c4.text_input("Razón Social", "JYPESA")

archivo = st.file_uploader("Cargar MATRIZ.csv", type="csv")

if archivo:
    df = pd.read_csv(archivo)
    if st.button("🚀 CALCULAR OPTIMIZACIÓN"):
        # Preparación de datos
        unidades = []
        for _, r in df.iterrows():
            for _ in range(int(r['Cantidad a enviar'])):
                unidades.append({'ItemCode': r['ItemCode'], 'Descripción': r['Descripción'], 
                               'Peso': float(r['Peso/caja (kg)']), 'Volumen': float(r['Volumen/caja (m3)']), 
                               'Densidad': float(r['kg/dm3'])})
        
        # Algoritmo Two-Pointer
        unidades.sort(key=lambda x: x['Densidad'])
        pallets, c_boxes, c_vol, c_peso = [], [], 0, 0
        l, r = 0, len(unidades) - 1

        while l <= r:
            box = unidades[l]
            if c_vol + box['Volumen'] <= vol_util and c_peso + box['Peso'] <= peso_limite:
                c_boxes.append(box); c_vol += box['Volumen']; c_peso += box['Peso']; l += 1
                if l <= r:
                    box_p = unidades[r]
                    if c_vol + box_p['Volumen'] <= vol_util and c_peso + box_p['Peso'] <= peso_limite:
                        c_boxes.append(box_p); c_vol += box_p['Volumen']; c_peso += box_p['Peso']; r -= 1
            else:
                pallets.append({'cajas': c_boxes, 'vol': c_vol, 'peso': c_peso})
                c_boxes, c_vol, c_peso = [], 0, 0
        if c_boxes: pallets.append({'cajas': c_boxes, 'vol': c_vol, 'peso': c_peso})

        # Resumen Ejecutivo
        st.write("---")
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-container"><h2>{len(pallets)}</h2>Tarimas</div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-container"><h2>{len(unidades)}</h2>Cajas</div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-container"><h2>{sum(p["peso"] for p in pallets):,.0f}</h2>kg Totales</div>', unsafe_allow_html=True)

        # Visualización de Estiba
        st.subheader("📋 Detalle de Carga")
        grid = st.columns(2)
        for i, p in enumerate(pallets):
            with grid[i % 2]:
                st.markdown(f"""
                <div class="tarima-card">
                    <h4 style="margin:0; color:#1F3B4D">TARIMA {i+1}</h4>
                    <p><b>{len(p['cajas'])}</b> cajas | <b>{p['peso']:.1f}</b> kg</p>
                    <small>Espacio utilizado:</small>
                </div>
                """, unsafe_allow_html=True)
                st.progress(min(p['vol']/vol_util, 1.0))

        # --- BOTÓN DE DESCARGA PDF (CORREGIDO) ---
        info_envio = {'transfer': transfer, 'destino': destino, 'fecha': fecha_envio, 'razon': razon}
        pdf_bytes = generar_pdf_final(pallets, info_envio)
        
        st.write("---")
        st.download_button(
            label="📥 DESCARGAR PACKING LIST PROFESIONAL",
            data=bytes(pdf_bytes), # La conversión a bytes soluciona el error
            file_name=f"NEXION_PL_{transfer}.pdf",
            mime="application/pdf",
            type="primary"
        )
