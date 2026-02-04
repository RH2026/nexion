import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NEXION | Smart Logistics", page_icon="📦", layout="wide")

# CSS Avanzado para forzar visibilidad y mejorar el diseño
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    /* Estilo para las tarjetas de las tarimas */
    .tarima-card {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 12px;
        border-top: 10px solid #1F3B4D;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
        color: #1F2933 !important; /* Texto oscuro forzado */
    }
    .tarima-card h3, .tarima-card h4 {
        color: #1F3B4D !important;
        margin-bottom: 15px;
        font-weight: bold;
    }
    /* Estilo para las filas de productos */
    .sku-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #edf2f7;
        color: #2d3748 !important;
    }
    /* Etiquetas de Cima y Base */
    .badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: bold;
        margin-left: 10px;
        text-transform: uppercase;
    }
    .badge-base { background-color: #1F3B4D; color: white; }
    .badge-cima { background-color: #CBD5E0; color: #1F3B4D; }
    
    .metric-container {
        background-color: #1F3B4D;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CLASE PDF (Se mantiene igual porque ya funcionaba bien) ---
class NEXION_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV', 0, 1, 'L')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'NEXION - REPORTE DE OPTIMIZACIÓN', 0, 1, 'L')
        self.line(10, 28, 200, 28)
        self.ln(10)

def generar_pdf_bytes(pallets, info):
    pdf = NEXION_PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, f"ORDEN: {info['transfer']} | DESTINO: {info['destino']}", 0, 1)
    pdf.ln(5)
    for i, p in enumerate(pallets):
        pdf.set_fill_color(31, 59, 77); pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f"TARIMA {i+1} - Peso: {p['peso']:.1f}kg - Vol: {p['vol']:.3f}m3", 1, 1, 'L', True)
        pdf.set_text_color(0); pdf.set_font("Arial", 'B', 8)
        pdf.cell(30, 7, "ItemCode", 1); pdf.cell(110, 7, "Descripcion", 1); pdf.cell(20, 7, "Cant.", 1); pdf.cell(30, 7, "Peso", 1, 1)
        pdf.set_font("Arial", '', 7)
        res = pd.DataFrame(p['cajas']).groupby('ItemCode').agg({'Descripción':'first', 'ItemCode':'count', 'Peso':'sum', 'Densidad':'first'}).sort_values('Densidad', ascending=False)
        for code, row in res.iterrows():
            pdf.cell(30, 6, str(code), 1); pdf.cell(110, 6, str(row['Descripción'])[:60], 1); pdf.cell(20, 6, str(row['ItemCode']), 1); pdf.cell(30, 6, f"{row['Peso']:.1f}", 1, 1)
        pdf.ln(5)
    return pdf.output()

# --- MEMORIA DE SESIÓN ---
if 'pallets' not in st.session_state:
    st.session_state.pallets = None

# --- INTERFAZ ---
st.title("📦 NEXION: Smart Pallet Optimizer")

with st.sidebar:
    st.header("Configuración de Carga")
    largo = st.number_input("Largo (m)", 1.2, step=0.1)
    ancho = st.number_input("Ancho (m)", 1.0, step=0.1)
    alto_max = st.number_input("Alto Máx (m)", 1.7, step=0.1)
    eficiencia = st.slider("Eficiencia de Estiba", 0.5, 1.0, 0.85)
    vol_util = (largo * ancho * (alto_max - 0.15)) * eficiencia

t_ref = st.text_input("Referencia Transferencia", "TS-100")
destino_ref = st.text_input("Destino", "Jalisco")
archivo = st.file_uploader("Cargar MATRIZ.csv", type="csv")

if archivo:
    df = pd.read_csv(archivo)
    if st.button("🚀 PROCESAR Y OPTIMIZAR"):
        unidades = []
        for _, r in df.iterrows():
            for _ in range(int(r['Cantidad a enviar'])):
                unidades.append({'ItemCode': r['ItemCode'], 'Descripción': r['Descripción'], 'Peso': r['Peso/caja (kg)'], 'Volumen': r['Volumen/caja (m3)'], 'Densidad': r['kg/dm3']})
        
        unidades.sort(key=lambda x: x['Densidad'])
        pallets_list, c_boxes, c_vol, c_peso = [], [], 0, 0
        l, r = 0, len(unidades) - 1

        while l <= r:
            box = unidades[l]
            if c_vol + box['Volumen'] <= vol_util:
                c_boxes.append(box); c_vol += box['Volumen']; c_peso += box['Peso']; l += 1
                if l <= r:
                    box_heavy = unidades[r]
                    if c_vol + box_heavy['Volumen'] <= vol_util:
                        c_boxes.append(box_heavy); c_vol += box_heavy['Volumen']; c_peso += box_heavy['Peso']; r -= 1
            else:
                pallets_list.append({'cajas': c_boxes, 'vol': c_vol, 'peso': c_peso})
                c_boxes, c_vol, c_peso = [], 0, 0
        if c_boxes: pallets_list.append({'cajas': c_boxes, 'vol': c_vol, 'peso': c_peso})
        st.session_state.pallets = pallets_list

# --- RENDERIZADO VISUAL ---
if st.session_state.pallets:
    st.write("---")
    m1, m2 = st.columns(2)
    m1.markdown(f'<div class="metric-container"><h2>{len(st.session_state.pallets)}</h2>Tarimas Optimizadas</div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><h2>{sum(len(p["cajas"]) for p in st.session_state.pallets)}</h2>Cajas Totales</div>', unsafe_allow_html=True)

    st.write("### Detalle de Estiba (Base a Cima)")
    t_cols = st.columns(2)
    for i, p in enumerate(st.session_state.pallets):
        with t_cols[i % 2]:
            st.markdown(f"""
            <div class="tarima-card">
                <h3>TARIMA {i+1}</h3>
                <p><b>Peso:</b> {p['peso']:.1f} kg | <b>Volumen:</b> {p['vol']:.3f} m³</p>
                <hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;">
            """, unsafe_allow_html=True)
            
            # Agrupar y ordenar para mostrar Base y Cima
            df_p = pd.DataFrame(p['cajas'])
            resumen = df_p.groupby('ItemCode').agg({'Descripción':'first', 'ItemCode':'count', 'Densidad':'first'}).sort_values('Densidad', ascending=False).reset_index()
            
            for idx_row, row in resumen.iterrows():
                # Lógica de etiquetas
                badge = ""
                if idx_row == 0: 
                    badge = '<span class="badge badge-base">BASE</span>'
                elif idx_row == len(resumen) - 1:
                    badge = '<span class="badge badge-cima">CIMA</span>'
                
                st.markdown(f"""
                <div class="sku-row">
                    <span><b>{row['ItemCode']}</b> - {row['Descripción'][:40]}...</span>
                    <span><b>{row['ItemCode_y']} pz</b> {badge}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

    # Botón PDF
    pdf_out = generar_pdf_bytes(st.session_state.pallets, {'transfer': t_ref, 'destino': destino_ref})
    st.download_button(label="📥 DESCARGAR PACKING LIST PDF", data=bytes(pdf_out), file_name=f"PL_{t_ref}.pdf", mime="application/pdf")
