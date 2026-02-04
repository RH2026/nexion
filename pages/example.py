import streamlit as st
import pandas as pd
from fpdf import FPDF  # fpdf2 usa el mismo nombre de importación
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NEXION | JYPESA Logistics", layout="wide")

# Estilos visuales mejorados
st.markdown("""
    <style>
    .tarima-card {
        background-color: #ffffff;
        border-top: 5px solid #1F3B4D;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #1F3B4D;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN GENERAR PDF (Actualizada para fpdf2) ---
def generar_pdf(pallets, header_data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Encabezado estilo JYPESA
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV", 0, 1, 'L')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, "NEXION - SISTEMA DE OPTIMIZACIÓN DE CARGA", 0, 1, 'L')
    pdf.line(10, 28, 200, 28)
    pdf.ln(10)

    # Datos del envío
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 7, f"Transferencia: {header_data['transfer']}", 0, 0)
    pdf.cell(0, 7, f"Destino: {header_data['destino']}", 0, 1)
    pdf.ln(5)

    for i, p_boxes in enumerate(pallets):
        # Título de Tarima
        pdf.set_fill_color(31, 59, 77)
        pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 10)
        p_peso = sum(b['Peso'] for b in p_boxes)
        p_vol = sum(b['Volumen'] for b in p_boxes)
        pdf.cell(0, 8, f"TARIMA {i+1} - ({len(p_boxes)} cajas, {p_peso:.2f} kg, {p_vol:.3f} m3)", 1, 1, 'L', True)
        
        # Tabla de contenido
        pdf.set_text_color(0)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(30, 7, "ItemCode", 1, 0, 'C')
        pdf.cell(100, 7, "Descripcion", 1, 0, 'C')
        pdf.cell(20, 7, "Cant.", 1, 0, 'C')
        pdf.cell(20, 7, "Peso", 1, 0, 'C')
        pdf.cell(20, 7, "Vol", 1, 1, 'C')

        pdf.set_font("Arial", '', 7)
        df_p = pd.DataFrame(p_boxes)
        resumen = df_p.groupby('ItemCode').agg({
            'Descripción': 'first',
            'ItemCode': 'count',
            'Peso': 'sum',
            'Volumen': 'sum'
        })
        
        for code, row in resumen.iterrows():
            pdf.cell(30, 6, str(code), 1)
            pdf.cell(100, 6, str(row['Descripción'])[:60], 1)
            pdf.cell(20, 6, str(row['ItemCode']), 1, 0, 'C')
            pdf.cell(20, 6, f"{row['Peso']:.1f}", 1, 0, 'C')
            pdf.cell(20, 6, f"{row['Volumen']:.3f}", 1, 1, 'C')
        pdf.ln(4)

    return pdf.output()

# --- LÓGICA DE INTERFAZ ---
st.title("📦 NEXION v2.0")
st.subheader("Simulador de Estiba y Optimización de Tarimas")

with st.sidebar:
    st.header("Configuración")
    largo = st.number_input("Largo Tarima (m)", 1.2, step=0.1)
    ancho = st.number_input("Ancho Tarima (m)", 1.0, step=0.1)
    alto_max = st.number_input("Alto Máx (m)", 1.7, step=0.1)
    eficiencia = st.slider("Eficiencia de espacio", 0.5, 1.0, 0.85)
    vol_util = (largo * ancho * (alto_max - 0.15)) * eficiencia

col1, col2 = st.columns(2)
transfer = col1.text_input("Referencia / Transferencia")
destino = col2.text_input("Destino")

uploaded_file = st.file_uploader("Sube el archivo MATRIZ.csv", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if st.button("CALCULAR TARIMAS"):
        # Lógica de empaquetado (Dos punteros)
        prods = []
        for _, r in df.iterrows():
            for _ in range(int(r['Cantidad a enviar'])):
                prods.append({
                    'ItemCode': r['ItemCode'], 'Descripción': r['Descripción'], 
                    'Peso': r['Peso/caja (kg)'], 'Volumen': r['Volumen/caja (m3)'], 
                    'Densidad': r['kg/dm3']
                })
        
        prods.sort(key=lambda x: x['Densidad'])
        pallets, cur_boxes, cur_vol = [], [], 0
        l, r = 0, len(prods)-1

        while l <= r:
            box = prods[l] # Intentar ligero
            if cur_vol + box['Volumen'] <= vol_util:
                cur_boxes.append(box)
                cur_vol += box['Volumen']
                l += 1
                if l <= r: # Intentar pesado
                    box_p = prods[r]
                    if cur_vol + box_p['Volumen'] <= vol_util:
                        cur_boxes.append(box_p)
                        cur_vol += box_p['Volumen']
                        r -= 1
            else:
                pallets.append(cur_boxes)
                cur_boxes, cur_vol = [], 0

        if cur_boxes: pallets.append(cur_boxes)

        # Dashboard Visual
        st.write("---")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-box"><h3>{len(pallets)}</h3>Tarimas</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-box"><h3>{len(prods)}</h3>Cajas</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-box"><h3>{vol_util:.2f}</h3>m3 Útiles</div>', unsafe_allow_html=True)

        st.ln = st.write("")
        
        # Grid de Tarimas
        cols = st.columns(2)
        for i, p in enumerate(pallets):
            with cols[i % 2]:
                st.markdown(f"""
                <div class="tarima-card">
                    <h4>TARIMA {i+1}</h4>
                    <p>Cajas: {len(p)} | Vol: {sum(b['Volumen'] for b in p):.3f} m3</p>
                </div>
                """, unsafe_allow_html=True)

        # Botón de Descarga
        pdf_out = generar_pdf(pallets, {'transfer': transfer, 'destino': destino})
        st.download_button("📥 DESCARGAR PACKING LIST PDF", data=pdf_out, file_name="Packing_List.pdf", mime="application/pdf")
