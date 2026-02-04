import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="NEXION | Smart Logistics", page_icon="📦", layout="wide")

st.markdown("""
    <style>
    .tarima-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-top: 8px solid #1F3B4D;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: #1F3B4D;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- CLASE PDF ---
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
        res = pd.DataFrame(p['cajas']).groupby('ItemCode').agg({'Descripción':'first', 'ItemCode':'count', 'Peso':'sum'})
        for code, row in res.iterrows():
            pdf.cell(30, 6, str(code), 1); pdf.cell(110, 6, str(row['Descripción'])[:60], 1); pdf.cell(20, 6, str(row['ItemCode']), 1); pdf.cell(30, 6, f"{row['Peso']:.1f}", 1, 1)
        pdf.ln(5)
    return pdf.output()

# --- INICIALIZAR MEMORIA (Session State) ---
if 'pallets' not in st.session_state:
    st.session_state.pallets = None
if 'total_cajas' not in st.session_state:
    st.session_state.total_cajas = 0

# --- INTERFAZ ---
st.title("📦 NEXION: Smart Pallet Optimizer")

with st.sidebar:
    st.header("Configuración")
    largo = st.number_input("Largo (m)", 1.2, step=0.1)
    ancho = st.number_input("Ancho (m)", 1.0, step=0.1)
    alto_max = st.number_input("Alto Máx (m)", 1.7, step=0.1)
    eficiencia = st.slider("Eficiencia", 0.5, 1.0, 0.85)
    vol_util = (largo * ancho * (alto_max - 0.15)) * eficiencia

t_ref = st.text_input("Referencia / Orden", "TS-100")
destino_ref = st.text_input("Destino", "Jalisco")
archivo = st.file_uploader("Carga tu MATRIZ.csv", type="csv")

if archivo:
    df = pd.read_csv(archivo)
    
    if st.button("🚀 CALCULAR OPTIMIZACIÓN"):
        # Lógica de cálculo
        prods = []
        for _, r in df.iterrows():
            for _ in range(int(r['Cantidad a enviar'])):
                prods.append({'ItemCode': r['ItemCode'], 'Descripción': r['Descripción'], 'Peso': r['Peso/caja (kg)'], 'Volumen': r['Volumen/caja (m3)'], 'Densidad': r['kg/dm3']})
        
        prods.sort(key=lambda x: x['Densidad'])
        pallets_list, c_boxes, c_vol, c_peso = [], [], 0, 0
        l, r = 0, len(prods) - 1

        while l <= r:
            box = prods[l]
            if c_vol + box['Volumen'] <= vol_util:
                c_boxes.append(box); c_vol += box['Volumen']; c_peso += box['Peso']; l += 1
                if l <= r:
                    box_p = prods[r]
                    if c_vol + box_p['Volumen'] <= vol_util:
                        cur_box_p = prods[r]
                        c_boxes.append(cur_box_p); c_vol += cur_box_p['Volumen']; c_peso += cur_box_p['Peso']; r -= 1
            else:
                pallets_list.append({'cajas': c_boxes, 'vol': c_vol, 'peso': c_peso})
                c_boxes, c_vol, c_peso = [], 0, 0
        if c_boxes: pallets_list.append({'cajas': c_boxes, 'vol': c_vol, 'peso': c_peso})
        
        # Guardar en memoria para que no desaparezca
        st.session_state.pallets = pallets_list
        st.session_state.total_cajas = len(prods)

# --- MOSTRAR RESULTADOS SI YA SE CALCULÓ ---
if st.session_state.pallets:
    st.write("---")
    m1, m2 = st.columns(2)
    m1.markdown(f'<div class="metric-container"><h3>{len(st.session_state.pallets)}</h3>Tarimas</div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-container"><h3>{st.session_state.total_cajas}</h3>Cajas Totales</div>', unsafe_allow_html=True)
    
    st.write("### Detalle Visual")
    cols = st.columns(2)
    for i, p in enumerate(st.session_state.pallets):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="tarima-card">
                <h4>TARIMA {i+1}</h4>
                <p>Cajas: {len(p["cajas"])} | Peso: {p["peso"]:.1f}kg | Vol: {p["vol"]:.3f}m3</p>
            </div>
            """, unsafe_allow_html=True)

    # Botón PDF fuera del bloque de cálculo para que no desaparezca
    pdf_out = generar_pdf_bytes(st.session_state.pallets, {'transfer': t_ref, 'destino': destino_ref})
    st.download_button(
        label="📥 DESCARGAR PACKING LIST PDF",
        data=bytes(pdf_out),
        file_name=f"PL_{t_ref}.pdf",
        mime="application/pdf"
    )
