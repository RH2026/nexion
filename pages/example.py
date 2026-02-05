import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NEXION | Industrial Logistics", page_icon="📦", layout="wide")

# DISEÑO INDUSTRIAL ULTRA-COMPACTO
st.markdown("""
    <style>
    .stApp { background-color: #1A202C; } /* Fondo oscuro profundo */
    
    /* Forzar color blanco en etiquetas y textos que no se veían */
    label, p, span, .stMarkdown, .stSelectbox, .stNumberInput label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    /* Tarjeta de Tarima Compacta */
    .tarima-card {
        background-color: #2D3748 !important;
        padding: 12px 18px;
        border-radius: 4px;
        border-left: 6px solid #63B3ED;
        margin-bottom: 10px;
        color: #FFFFFF !important;
    }
    
    .tarima-header {
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid #4A5568;
        padding-bottom: 5px;
        margin-bottom: 8px;
        font-weight: 800;
        font-size: 1rem;
    }

    /* Filas de productos más delgadas para menos scroll */
    .sku-row {
        display: flex;
        justify-content: space-between;
        padding: 4px 0;
        border-bottom: 1px solid #4A5568;
        font-size: 0.8rem;
    }

    .badge {
        padding: 2px 6px;
        border-radius: 2px;
        font-size: 9px;
        font-weight: bold;
    }
    .badge-base { background-color: #63B3ED; color: #1A202C; }
    .badge-cima { background-color: #CBD5E0; color: #1A202C; }

    /* Métricas en una sola línea */
    .metric-compact {
        background-color: #2D3748;
        border: 1px solid #4A5568;
        padding: 10px;
        text-align: center;
        border-radius: 4px;
    }
    
    /* Ajuste para que el botón de descarga se vea bien */
    .stDownloadButton button {
        background-color: #63B3ED !important;
        color: #1A202C !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- CLASE PDF PROFESIONAL ---
class NEXION_PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV', 0, 1, 'L')
        self.set_font('Helvetica', 'B', 9)
        self.cell(0, 5, 'NEXION - REPORTE DE CARGA', 0, 1, 'L')
        self.line(10, 28, 200, 28)
        self.ln(10)

def generar_pdf_bytes(pallets, info):
    pdf = NEXION_PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 7, f"ORDEN: {info['transfer']} | DESTINO: {info['destino']}", 0, 1)
    pdf.ln(5)
    for i, p in enumerate(pallets):
        pdf.set_fill_color(31, 59, 77); pdf.set_text_color(255)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 8, f"TARIMA {i+1} - {p['peso']:.1f} KG - {p['vol']:.3f} M3", 1, 1, 'L', True)
        pdf.set_text_color(0); pdf.set_font("Helvetica", 'B', 8)
        pdf.cell(30, 7, "ITEM", 1); pdf.cell(110, 7, "DESCRIPCION", 1); pdf.cell(20, 7, "CANT", 1); pdf.cell(30, 7, "PESO", 1, 1)
        pdf.set_font("Helvetica", '', 7)
        df_p = pd.DataFrame(p['cajas'])
        res = df_p.groupby('ItemCode').agg({'Descripción':'first', 'Peso':'sum', 'Densidad':'first'}).sort_values('Densidad', ascending=False)
        for code, row in res.iterrows():
            pdf.cell(30, 6, str(code), 1); pdf.cell(110, 6, str(row['Descripción'])[:65], 1); pdf.cell(20, 6, str(len(df_p[df_p['ItemCode']==code])), 1, 0, 'C'); pdf.cell(30, 6, f"{row['Peso']:.1f}", 1, 1)
        pdf.ln(5)
    return pdf.output()

# --- LÓGICA ---
if 'pallets' not in st.session_state: st.session_state.pallets = None

st.markdown("<h2 style='color: white; text-align: center; margin: 0;'>NEXION: INDUSTRIAL OPTIMIZER</h2>", unsafe_allow_html=True)

# Layout de configuración en una sola fila para ahorrar espacio
with st.container():
    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    largo = c_p1.number_input("Largo (m)", 1.2, step=0.1)
    ancho = c_p2.number_input("Ancho (m)", 1.0, step=0.1)
    alto = c_p3.number_input("Alto (m)", 1.7, step=0.1)
    eficiencia = c_p4.slider("Eficiencia", 0.5, 1.0, 0.85)
    vol_util = (largo * ancho * (alto - 0.15)) * eficiencia

with st.expander("📝 Datos de Envío", expanded=False):
    c_e1, c_e2 = st.columns(2)
    t_ref = c_e1.text_input("Referencia", "ORDEN-2026")
    destino_ref = c_e2.text_input("Destino", "ALMACEN CENTRAL")

archivo = st.file_uploader("Subir CSV", type="csv")

if archivo:
    df_csv = pd.read_csv(archivo)
    if st.button("🚀 EJECUTAR CÁLCULO"):
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
    res_cols = st.columns(3)
    res_cols[0].markdown(f'<div class="metric-compact"><b>TARIMAS</b><br><h3>{len(st.session_state.pallets)}</h3></div>', unsafe_allow_html=True)
    res_cols[1].markdown(f'<div class="metric-compact"><b>CAJAS</b><br><h3>{sum(len(p["cajas"]) for p in st.session_state.pallets)}</h3></div>', unsafe_allow_html=True)
    res_cols[2].markdown(f'<div class="metric-compact"><b>PESO TOTAL</b><br><h3>{sum(p["peso"] for p in st.session_state.pallets):,.0f} KG</h3></div>', unsafe_allow_html=True)

    st.write("###")
    
    # Vista en 2 columnas
    t_cols = st.columns(2)
    for i, p in enumerate(st.session_state.pallets):
        with t_cols[i % 2]:
            st.markdown(f"""
            <div class="tarima-card">
                <div class="tarima-header">
                    <span>TARIMA {i+1}</span>
                    <span style='color: #63B3ED;'>{p['peso']:.1f} KG</span>
                </div>
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
                    <span><b>{code}</b> <small>{row['Descripción'][:30]}...</small></span>
                    <span>{counts[code]} CJ {badge}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    pdf_out = generar_pdf_bytes(st.session_state.pallets, {'transfer': t_ref, 'destino': destino_ref})
    st.download_button(label="📥 DESCARGAR PACKING LIST", data=bytes(pdf_out), file_name=f"NEXION_PL_{t_ref}.pdf", mime="application/pdf")
