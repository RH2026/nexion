import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from fpdf import FPDF

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="NEXION | Logística Avanzada", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .tarima-card {
        background-color: #ffffff;
        border-left: 5px solid #1F3B4D;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(pallets, header_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "JYPESA - PACKING LIST (NEXION)", 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Referencia: {header_data['transfer']} | Destino: {header_data['destino']}", 0, 1, 'C')
    pdf.ln(5)

    for i, p_boxes in enumerate(pallets):
        pdf.set_fill_color(31, 59, 77)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, f"TARIMA {i+1}", 1, 1, 'L', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(30, 7, "ItemCode", 1)
        pdf.cell(100, 7, "Descripcion", 1)
        pdf.cell(20, 7, "Cajas", 1)
        pdf.cell(20, 7, "Peso(kg)", 1)
        pdf.cell(20, 7, "Vol(m3)", 1, 1)

        pdf.set_font("Arial", '', 8)
        df_p = pd.DataFrame(p_boxes)
        resumen = df_p.groupby('ItemCode').agg({'Descripción': 'first', 'ItemCode': 'count', 'Peso': 'sum', 'Volumen': 'sum'})
        
        for code, row in resumen.iterrows():
            pdf.cell(30, 6, str(code), 1)
            pdf.cell(100, 6, str(row['Descripción'])[:55], 1)
            pdf.cell(20, 6, str(row['ItemCode']), 1)
            pdf.cell(20, 6, f"{row['Peso']:.2f}", 1)
            pdf.cell(20, 6, f"{row['Volumen']:.3f}", 1, 1)
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title("📦 NEXION: Smart Pallet Simulator")
st.write("Optimizando la carga de JYPESA con inteligencia de datos.")

with st.sidebar:
    st.header("⚙️ Configuración")
    largo = st.number_input("Largo Tarima (m)", 1.2, step=0.1)
    ancho = st.number_input("Ancho Tarima (m)", 1.0, step=0.1)
    alto_max = st.number_input("Alto Máx (m)", 1.7, step=0.1)
    peso_limite = st.number_input("Peso Límite Tarima (kg)", 1500, step=100)
    eficiencia = st.slider("Factor Eficiencia", 0.5, 1.0, 0.85)
    
    vol_util = (largo * ancho * (alto_max - 0.15)) * eficiencia

# Datos de envío
with st.expander("📝 Datos del Envío", expanded=True):
    c1, c2 = st.columns(2)
    transfer = c1.text_input("Transferencia / Orden", "TS-2024-001")
    destino = c2.text_input("Destino", "Guadalajara, Jalisco")

uploaded_file = st.file_uploader("Cargar MATRIZ.csv", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if st.button("🚀 CALCULAR OPTIMIZACIÓN", type="primary"):
        # Algoritmo de Dos Punteros
        prods = []
        for _, r in df.iterrows():
            for _ in range(int(r['Cantidad a enviar'])):
                prods.append({'ItemCode': r['ItemCode'], 'Descripción': r['Descripción'], 
                             'Peso': r['Peso/caja (kg)'], 'Volumen': r['Volumen/caja (m3)'], 'Densidad': r['kg/dm3']})
        
        prods.sort(key=lambda x: x['Densidad'])
        pallets, cur_boxes, cur_vol, cur_peso = [], [], 0, 0
        l, r = 0, len(prods)-1

        while l <= r:
            for idx in [l, r] if l != r else [l]:
                box = prods[idx]
                if cur_vol + box['Volumen'] <= vol_util and cur_peso + box['Peso'] <= peso_limite:
                    cur_boxes.append(box)
                    cur_vol += box['Volumen']
                    cur_peso += box['Peso']
                    if idx == l: l += 1
                    else: r -= 1
                else:
                    if cur_boxes: pallets.append(cur_boxes)
                    cur_boxes, cur_vol, cur_peso = [box], box['Volumen'], box['Peso']
                    if idx == l: l += 1
                    else: r -= 1
        if cur_boxes: pallets.append(cur_boxes)

        # Resumen General
        st.write("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Tarimas", len(pallets))
        m2.metric("Total Cajas", len(prods))
        m3.metric("Eficiencia Promedio", f"{eficiencia*100}%")

        # Render Tarimas
        col_view1, col_view2 = st.columns(2)
        for i, p in enumerate(pallets):
            view = col_view1 if i % 2 == 0 else col_view2
            with view:
                p_peso = sum(b['Peso'] for b in p)
                p_vol = sum(b['Volumen'] for b in p)
                
                st.markdown(f"""
                <div class="tarima-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-size:18px; font-weight:bold; color:#1F3B4D;">TARIMA {i+1}</span>
                        <span class="status-badge" style="background:#e3f2fd; color:#1565c0;">{len(p)} CAJAS</span>
                    </div>
                """, unsafe_allow_html=True)
                
                st.write(f"**Peso:** {p_peso:.2f} / {peso_limite} kg")
                st.progress(min(p_peso/peso_limite, 1.0))
                st.write(f"**Volumen:** {p_vol:.3f} / {vol_util:.3f} m³")
                st.progress(min(p_vol/vol_util, 1.0))
                st.markdown("</div>", unsafe_allow_html=True)

        # Botón PDF
        header_data = {'transfer': transfer, 'destino': destino}
        pdf_bytes = generar_pdf(pallets, header_data)
        st.download_button("📥 Descargar Packing List Profesional (PDF)", data=pdf_bytes, 
                           file_name=f"PL_{transfer}.pdf", mime="application/pdf")
