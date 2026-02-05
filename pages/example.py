import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NEXION | Industrial Logistics", page_icon="📦", layout="wide")

# DISEÑO INDUSTRIAL ÉLITE (Forzado de colores para evitar invisibilidad)
st.markdown("""
    <style>
    /* Fondo general estilo concreto/oficina técnica */
    .stApp {
        background-color: #E2E8F0;
    }
    
    /* Tarjeta de Tarima Estilo Industrial */
    .tarima-card {
        background-color: #FFFFFF !important;
        padding: 24px;
        border-radius: 4px;
        border-left: 10px solid #1A202C;
        border-right: 1px solid #CBD5E0;
        border-bottom: 1px solid #CBD5E0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-bottom: 30px;
        color: #1A202C !important; /* Negro industrial para el texto */
    }
    
    .tarima-header {
        font-size: 22px;
        font-weight: 800;
        color: #1A202C !important;
        border-bottom: 2px solid #E2E8F0;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
    }

    /* Filas de productos */
    .sku-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #EDF2F7;
        color: #2D3748 !important;
    }

    /* Badges de Carga */
    .badge {
        padding: 5px 12px;
        border-radius: 2px;
        font-size: 10px;
        font-weight: 900;
        letter-spacing: 1px;
    }
    .badge-base { background-color: #1A202C; color: #FFFFFF; }
    .badge-cima { background-color: #EDF2F7; color: #1A202C; border: 1px solid #CBD5E0; }

    /* Métricas superiores */
    .metric-container {
        background-color: #1A202C;
        color: #FFFFFF;
        padding: 20px;
        border-radius: 4px;
        text-align: center;
        border-bottom: 5px solid #4A5568;
    }
    
    /* Forzar visibilidad en inputs */
    label, p, span { color: #1A202C !important; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# --- CLASE PDF PROFESIONAL ---
class NEXION_PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(26, 32, 44)
        self.cell(0, 10, 'JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV', 0, 1, 'L')
        self.set_font('Helvetica', 'B', 9)
        self.cell(0, 5, 'SISTEMA NEXION - LOGISTICA DE ALTA PRECISION', 0, 1, 'L')
        self.line(10, 28, 200, 28)
        self.ln(10)

def generar_pdf_bytes(pallets, info):
    pdf = NEXION_PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 7, f"REFERENCIA: {info['transfer']} | DESTINO: {info['destino']}", 0, 1)
    pdf.ln(5)
    for i, p in enumerate(pallets):
        pdf.set_fill_color(26, 32, 44); pdf.set_text_color(255)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 8, f"TARIMA {i+1} - {p['peso']:.1f} KG - {p['vol']:.3f} M3", 1, 1, 'L', True)
        pdf.set_text_color(0); pdf.set_font("Helvetica", 'B', 8)
        pdf.cell(30, 7, "ITEM CODE", 1); pdf.cell(110, 7, "DESCRIPCION", 1); pdf.cell(20, 7, "CANT.", 1); pdf.cell(30, 7, "PESO SUB", 1, 1)
        pdf.set_font("Helvetica", '', 7)
        df_p = pd.DataFrame(p['cajas'])
        resumen = df_p.groupby('ItemCode').agg({'Descripción':'first', 'Peso':'sum', 'Densidad':'first'}).sort_values('Densidad', ascending=False)
        for code, row in resumen.iterrows():
            pdf.cell(30, 6, str(code), 1); pdf.cell(110, 6, str(row['Descripción'])[:65], 1); pdf.cell(20, 6, str(len(df_p[df_p['ItemCode']==code])), 1, 0, 'C'); pdf.cell(30, 6, f"{row['Peso']:.1f}", 1, 1)
        pdf.ln(5)
    return pdf.output()

# --- APP LOGIC ---
if 'pallets' not in st.session_state: st.session_state.pallets = None

st.markdown("<h1 style='color: #1A202C; text-align: center;'>NEXION: INDUSTRIAL PALLETIZER</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("🏢 Planta de Carga")
    largo = st.number_input("Largo (m)", 1.2, step=0.1)
    ancho = st.number_input("Ancho (m)", 1.0, step=0.1)
    alto = st.number_input("Alto Máx (m)", 1.7, step=0.1)
    eficiencia = st.slider("Eficiencia", 0.5, 1.0, 0.85)
    vol_util = (largo * ancho * (alto - 0.15)) * eficiencia

c1, c2 = st.columns(2)
t_ref = c1.text_input("Referencia", "ORDEN-2026")
destino_ref = c2.text_input("Destino", "ALMACEN CENTRAL")
archivo = st.file_uploader("Cargar MATRIZ.csv", type="csv")

if archivo:
    df_csv = pd.read_csv(archivo)
    if st.button("🚀 EJECUTAR OPTIMIZACIÓN ÉLITE"):
        unidades = []
        for _, r in df_csv.iterrows():
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
                    box_p = unidades[r]
                    if c_vol + box_p['Volumen'] <= vol_util:
                        c_boxes.append(box_p); c_vol += box_p['Volumen']; c_peso += box_p['Peso']; r -= 1
            else:
                pallets_list.append({'cajas': c_boxes, 'vol': c_vol, 'peso': c_peso})
                c_boxes, c_vol, c_peso = [], 0, 0
        if c_boxes: pallets_list.append({'cajas': c_boxes, 'vol': c_vol, 'peso': c_peso})
        st.session_state.pallets = pallets_list

# --- RESULTADOS ---
if st.session_state.pallets:
    st.write("---")
    res1, res2, res3 = st.columns(3)
    res1.markdown(f'<div class="metric-container"><h1>{len(st.session_state.pallets)}</h1>TARIMAS</div>', unsafe_allow_html=True)
    res2.markdown(f'<div class="metric-container"><h1>{sum(len(p["cajas"]) for p in st.session_state.pallets)}</h1>CAJAS</div>', unsafe_allow_html=True)
    res3.markdown(f'<div class="metric-container"><h1>{sum(p["peso"] for p in st.session_state.pallets):,.0f}</h1>KG TOTAL</div>', unsafe_allow_html=True)

    st.markdown("<h3 style='color: #1A202C; margin-top: 30px;'>ESTRUCTURA DE CARGA POR PALLET</h3>", unsafe_allow_html=True)
    
    t_cols = st.columns(2)
    for i, p in enumerate(st.session_state.pallets):
        with t_cols[i % 2]:
            st.markdown(f"""
            <div class="tarima-card">
                <div class="tarima-header">
                    <span>TARIMA {i+1}</span>
                    <span style='font-size: 14px;'>{p['peso']:.1f} KG</span>
                </div>
                <p style='margin-bottom: 20px;'>Capacidad utilizada: <b>{p['vol']:.3f} / {vol_util:.3f} m³</b></p>
            """, unsafe_allow_html=True)
            
            df_p = pd.DataFrame(p['cajas'])
            resumen = df_p.groupby('ItemCode').agg({'Descripción': 'first', 'Densidad': 'first'}).sort_values('Densidad', ascending=False)
            counts = df_p['ItemCode'].value_counts()
            
            for idx_num, (code, row) in enumerate(resumen.iterrows()):
                badge = ""
                if idx_num == 0: badge = '<span class="badge badge-base">BASE</span>'
                elif idx_num == len(resumen) - 1: badge = '<span class="badge badge-cima">CIMA</span>'
                
                st.markdown(f"""
                <div class="sku-row">
                    <span><b>{code}</b> <br> <small>{row['Descripción'][:45]}...</small></span>
                    <span style='text-align: right;'><b>{counts[code]} CJ</b> {badge}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

    pdf_out = generar_pdf_bytes(st.session_state.pallets, {'transfer': t_ref, 'destino': destino_ref})
    st.download_button(label="📥 GENERAR Y DESCARGAR PACKING LIST ÉLITE", data=bytes(pdf_out), file_name=f"NEXION_PL_{t_ref}.pdf", mime="application/pdf")
