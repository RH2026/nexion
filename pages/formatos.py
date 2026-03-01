import streamlit as st
import streamlit.components.v1 as components
from datetime import date

# --- CONFIGURACIÓN DE PRODUCTOS BILINGÜES ---
productos_proforma = {
    "Accesorios Ecologicos": ("Ecological Accessories", "3401.11", 2.50),
    "Dispensador Almond": ("Almond Dispenser", "3924.90", 11.50),
    "Kit Biogena": ("Biogena Amenities Kit", "3401.11", 3.20),
    "Jabón de Tocador 40g": ("Toilet Soap 40g", "3401.11", 0.45),
    "Shampoo Botánicos 30ml": ("Botanical Shampoo 30ml", "3305.10", 0.60),
    "Soporte Inoxidable": ("Stainless Steel Holder", "7324.90", 35.00)
}

def generar_proforma_html(datos_rem, datos_dest, items, info_envio):
    filas_html = ""
    subtotal = 0
    for item in items:
        total_item = item['cant'] * item['precio']
        subtotal += total_item
        filas_html += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{item['desc_es']}<br><i style="font-size:0.8em; color:#555;">{item['desc_en']}</i></td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align:center;">{item['hs']}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align:center;">{item['cant']}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">${item['precio']:.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">${total_item:.2f}</td>
        </tr>"""

    return f"""
    <div style="font-family: 'Helvetica', Arial, sans-serif; padding: 40px; color: #333; max-width: 800px; margin: auto; background: white;">
        <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 10px;">
            <div>
                <h1 style="margin:0; color:#003399;">PROFORMA INVOICE</h1>
                <p style="margin:0;">FACTURA PROFORMA</p>
            </div>
            <div style="text-align: right;">
                <p style="margin:0;"><b>Date / Fecha:</b> {info_envio['fecha']}</p>
                <p style="margin:0;"><b>Invoice #:</b> {info_envio['folio']}</p>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <div style="border: 1px solid #ccc; padding: 10px;">
                <b style="font-size: 0.9em; color: #666;">SHIPPER / REMITENTE</b>
                <p style="margin:5px 0; font-size: 0.9em;"><b>{datos_rem['empresa']}</b><br>{datos_rem['direccion']}<br>{datos_rem['ciudad']}, {datos_rem['pais']}<br>TEL: {datos_rem['tel']}</p>
            </div>
            <div style="border: 1px solid #ccc; padding: 10px;">
                <b style="font-size: 0.9em; color: #666;">CONSIGNEE / DESTINATARIO</b>
                <p style="margin:5px 0; font-size: 0.9em;"><b>{datos_dest['nombre']}</b><br>{datos_dest['calle']}<br>{datos_dest['ciudad']}, {datos_dest['pais']}<br>TEL: {datos_dest['tel']}</p>
            </div>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.9em;">
            <thead>
                <tr style="background: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Description / Descripción</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">HS Code</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Qty</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Unit USD</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Total USD</th>
                </tr>
            </thead>
            <tbody>{filas_html}</tbody>
            <tfoot>
                <tr>
                    <td colspan="4" style="text-align:right; padding: 10px;"><b>TOTAL VALUE USD:</b></td>
                    <td style="border: 1px solid #ddd; padding: 10px; text-align:right; background: #eee;"><b>${subtotal:.2f}</b></td>
                </tr>
            </tfoot>
        </table>
        <div style="margin-top: 30px; font-size: 0.75em; border: 1px solid #eee; padding: 10px; background: #fafafa;">
            <p style="margin:0;"><b>Declaration:</b> These commodities, technology or software were exported in accordance with the export administration regulations. Diversion contrary to law is prohibited. The values declared are for customs purposes only.</p>
        </div>
    </div>
    """

# --- INTERFAZ DE CAPTURA CON TU ESTILO ---
st.title("📄 Generador de Proforma Internacional")

with st.form("proforma_form"):
    # Fila superior de configuración
    c1, c2, c3 = st.columns([1, 1, 1])
    f_folio = c1.text_input("FOLIO / INVOICE #", "PRO-2026-001")
    f_fecha = c2.date_input("FECHA DE ENVÍO", date.today())
    f_currency = c3.selectbox("MONEDA", ["USD (Dólares)", "MXN (Pesos)"])

    st.write("")

    # --- SECCIÓN REMITENTE (Azul) ---
    st.markdown('<div style="background:#4e73df;color:white;text-align:center;font-weight:bold;padding:8px;border-radius:4px 4px 0 0;">REMITENTE</div>', unsafe_allow_html=True)
    with st.container():
        st.text_input("NOMBRE", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
        r1, r2 = st.columns([2, 1])
        rem_atn = r1.text_input("ATENCIÓN", "RIGOBERTO HERNANDEZ")
        rem_tel = r2.text_input("TELÉFONO", "3319753122")
        rem_sol = st.text_input("SOLICITANTE / AGENTE", placeholder="NOMBRE DE QUIEN SOLICITA").upper()

    st.write("")

    # --- SECCIÓN DESTINATARIO (Amarillo) ---
    st.markdown('<div style="background:#f6c23e;color:black;text-align:center;font-weight:bold;padding:8px;border-radius:4px 4px 0 0;">DESTINATARIO / HOTEL</div>', unsafe_allow_html=True)
    with st.container():
        dest_nom = st.text_input("HOTEL / NOMBRE").upper()
        dest_calle = st.text_input("CALLE Y NÚMERO").upper()
        d1, d2 = st.columns(2)
        dest_col = d1.text_input("COLONIA").upper()
        dest_cp = d2.text_input("C.P.")
        d3, d4 = st.columns(2)
        dest_ciudad = d3.text_input("CIUDAD").upper()
        dest_estado = d4.text_input("ESTADO").upper()
        dest_contacto = st.text_input("CONTACTO RECEPTOR", placeholder="NOMBRE Y TELÉFONO DE QUIEN RECIBE").upper()

    st.divider()

    # --- PRODUCTOS ---
    st.markdown("### 📦 PRODUCTOS")
    seleccion = st.multiselect("Selecciona los productos:", list(productos_proforma.keys()))
    
    items_capturados = []
    if seleccion:
        cols = st.columns(4)
        for i, prod in enumerate(seleccion):
            with cols[i % 4]:
                cant = st.number_input(f"{prod}", min_value=1, step=1, key=f"q_{prod}")
                info = productos_proforma[prod]
                items_capturados.append({
                    "desc_es": prod, "desc_en": info[0], "hs": info[1],
                    "cant": cant, "precio": info[2]
                })

    st.write("")
    enviar = st.form_submit_button("🖨️ GENERAR PROFORMA E IMPRIMIR", use_container_width=True, type="primary")

if enviar:
    if not dest_nom or not items_capturados:
        st.error("Amor, faltan datos del hotel o no has seleccionado productos.")
    else:
        rem_info = {"empresa": "JABONES Y PRODUCTOS ESPECIALIZADOS", "direccion": "C. Cernícalo 155, La Aurora", "ciudad": "Guadalajara, Jalisco, 44460", "pais": "MEXICO", "tel": rem_tel}
        dest_info = {"nombre": dest_nom, "calle": dest_calle, "ciudad": f"{dest_ciudad}, {dest_estado} CP {dest_cp}", "pais": "USA", "tel": dest_contacto}
        
        proforma_html = generar_proforma_html(rem_info, dest_info, items_capturados, {"folio": f_folio, "fecha": f_fecha})
        
        st.success("¡Documento listo!")
        components.html(f"<html><body>{proforma_html}<script>window.print();</script></body></html>", height=0)










































































