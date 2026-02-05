import streamlit as st
from fpdf import FPDF
import datetime

# --- CONFIGURACIÓN DE PRECIOS (TU DATA) ---
precios_muestras = {
    "Elements": 29.34, "Almond Olive": 33.83, "Biogena": 48.95, 
    "Cava": 34.59, "Persa": 58.02, "Lavarino": 36.30, 
    "Botánicos": 274.17, "Ecologicos": 47.85
}

# --- CLASE PARA EL PDF PROFESIONAL ---
class ReportePDF(FPDF):
    def header(self):
        # Encabezado Industrial
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'REPORTE DE COSTOS DE MUESTRAS', 0, 1, 'C')
        self.set_draw_color(255, 221, 0) # El amarillo #FFDD00 que te gusta
        self.line(10, 22, 200, 22)
        self.ln(10)

    def footer(self):
        # Pie de página solicitado
        self.set_y(-25)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, 'JYPESA', 0, 1, 'C')
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, 'Automatización de Procesos', 0, 0, 'C')

# --- INTERFAZ EN STREAMLIT ---
st.set_page_config(page_title="NEXION - JYPESA", layout="wide")

st.title("📦 Generador de Muestras Elite")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        destinatario = st.text_input("Destinatario / Hotel", "Tania Vega")
        flete = st.number_input("Costo de Flete (Manual $)", min_value=0.0, value=0.0)
    with col2:
        fecha = st.date_input("Fecha de Envío", datetime.date.today())
        # Selección múltiple de productos
        productos_sel = st.multiselect("Selecciona los productos enviados", list(precios_muestras.keys()))

# --- TABLA DE CANTIDADES ---
totales_productos = {}
if productos_sel:
    st.subheader("Cantidades")
    cols = st.columns(len(productos_sel))
    for i, p in enumerate(productos_sel):
        cant = cols[i].number_input(f"Cant. {p}", min_value=1, step=1)
        totales_productos[p] = cant * precios_muestras[p]

    costo_muestras = sum(totales_productos.values())
    total_general = costo_muestras + flete

    st.divider()
    st.metric("TOTAL A REPORTE", f"${total_general:,.2f}")

    # --- BOTÓN PARA GENERAR E IMPRIMIR ---
    if st.button("Generar PDF para Imprimir"):
        pdf = ReportePDF()
        pdf.add_page()
        
        # Datos de envío
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, f"Destinatario: {destinatario}", 0, 1)
        pdf.cell(0, 10, f"Fecha: {fecha}", 0, 1)
        pdf.ln(5)

        # Tabla de costos
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 10, "Producto", 1, 0, 'C', True)
        pdf.cell(40, 10, "Costo Unit.", 1, 0, 'C', True)
        pdf.cell(70, 10, "Subtotal", 1, 1, 'C', True)

        pdf.set_font('Arial', '', 10)
        for prod in productos_sel:
            pdf.cell(80, 10, prod, 1)
            pdf.cell(40, 10, f"${precios_muestras[prod]:.2f}", 1, 0, 'R')
            pdf.cell(70, 10, f"${totales_productos[prod]:.2f}", 1, 1, 'R')

        # Totales
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(120, 10, "SUBTOTAL MUESTRAS:", 0, 0, 'R')
        pdf.cell(70, 10, f"${costo_muestras:.2f}", 1, 1, 'R')
        pdf.cell(120, 10, "FLETE:", 0, 0, 'R')
        pdf.cell(70, 10, f"${flete:.2f}", 1, 1, 'R')
        pdf.set_fill_color(255, 221, 0)
        pdf.cell(120, 10, "TOTAL GENERAL:", 0, 0, 'R')
        pdf.cell(70, 10, f"${total_general:.2f}", 1, 1, 'R', True)

        # Guardar y descargar
        pdf_output = pdf.output(dest_='S').encode('latin-1')
        st.download_button(
            label="⬇️ Descargar Reporte PDF",
            data=pdf_output,
            file_name=f"Reporte_{destinatario}_{fecha}.pdf",
            mime="application/pdf"
        )






























































