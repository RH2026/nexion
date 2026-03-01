import streamlit as st
import streamlit.components.v1 as components
from datetime import date, datetime

# --- CONFIGURACIÓN DE PÁGINA (WIDE) ---
st.set_page_config(layout="wide", page_title="NEXION - Proforma")

# --- CONFIGURACIÓN DE PRODUCTOS ---
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
                <p style="margin:0; font-size: 0.8em; color: #666;"><b>Tracking:</b> {info_envio['guia']}</p>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <div style="border: 1px solid #ccc; padding: 10px;">
                <b style="font-size: 0.9em; color: #666;">SHIPPER / REMITENTE</b>
                <p style="margin:5px 0; font-size: 0.85em;">
                    <b>{datos_rem['empresa']}</b><br>
                    {datos_rem['direccion']}<br>
                    {datos_rem['ciudad']}, {datos_rem['pais']}<br>
                    <b>ATN: {datos_rem['atencion']}</b><br>
                    TEL: {datos_rem['tel']}
                </p>
            </div>
            <div style="border: 1px solid #ccc; padding: 10px;">
                <b style="font-size: 0.9em; color: #666;">CONSIGNEE / DESTINATARIO</b>
                <p style="margin:5px 0; font-size: 0.85em;">
                    <b>{datos_dest['nombre']}</b><br>
                    {datos_dest['calle']}<br>
                    {datos_dest['ciudad']}, {datos_dest['estado']} CP: {datos_dest['cp']}<br>
                    {datos_dest['pais']}<br>
                    <b>TAX ID / RFC:</b> {datos_dest['tax_id']}<br>
                    TEL: {datos_dest['tel']}
                </p>
            </div>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.9em;">
            <thead><tr style="background: #f2f2f2;"><th style="border: 1px solid #ddd; padding: 8px;">Description</th><th style="border: 1px solid #ddd; padding: 8px;">HS Code</th><th style="border: 1px solid #ddd; padding: 8px;">Qty</th><th style="border: 1px solid #ddd; padding: 8px;">Unit USD</th><th style="border: 1px solid #ddd; padding: 8px;">Total USD</th></tr></thead>
            <tbody>{filas_html}</tbody>
            <tfoot><tr><td colspan="4" style="text-align:right; padding: 10px;"><b>TOTAL VALUE USD:</b></td><td style="border: 1px solid #ddd; padding: 10px; text-align:right; background: #eee;"><b>${subtotal:.2f}</b></td></tr></tfoot>
        </table>
        <div style="margin-top: 30px; font-size: 0.7em; color: #666; border-top: 1px solid #eee; padding-top: 10px;">
            <p>Declaration: The values declared are for customs purposes only. No commercial value.</p>
        </div>
    </div>
    """

# --- LÓGICA DE FOLIO AUTOMÁTICO ---
if 'folio_num' not in st.session_state:
    st.session_state.folio_num = int(datetime.now().strftime("%m%d%H%M"))

# --- INTERFAZ DE CAPTURA ---
st.title("📄 Generador de Proforma Internacional")

# SECCIÓN DE DATOS DE ENVÍO (CAPTURA DIRECTA)
c_env1, c_env2, c_env3 = st.columns([1, 1, 1])
f_folio = c_env1.text_input("FOLIO / INVOICE #", value=f"PRO-{st.session_state.folio_num}")
f_fecha = c_env2.date_input("FECHA DE ENVÍO", date.today())
f_guia = c_env3.text_input("NÚMERO DE GUÍA FEDEX", placeholder="0000 0000 0000")

st.write("")
col_izq, col_der = st.columns(2)

with col_izq:
    st.markdown('<div style="background:#4e73df;color:white;text-align:center;font-weight:bold;padding:8px;border-radius:4px 4px 0 0;">REMITENTE</div>', unsafe_allow_html=True)
    st.text_input("NOMBRE", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
    r1, r2 = st.columns([1.5, 1])
    rem_atn = r1.text_input("ATENCIÓN", "RIGOBERTO HERNANDEZ")
    rem_tel = r2.text_input("TELÉFONO", "3319753122")
    rem_sol = st.text_input("SOLICITANTE / AGENTE").upper()

with col_der:
    st.markdown('<div style="background:#f6c23e;color:black;text-align:center;font-weight:bold;padding:8px;border-radius:4px 4px 0 0;">DESTINATARIO / HOTEL</div>', unsafe_allow_html=True)
    dest_nom = st.text_input("HOTEL / NOMBRE").upper()
    dest_calle = st.text_input("CALLE Y NÚMERO").upper()
    dp1, dp2 = st.columns(2)
    dest_pais = dp1.text_input("PAÍS DESTINO").upper()
    dest_estado = dp2.text_input("ESTADO / PROVINCIA").upper()
    dp3, dp4 = st.columns(2)
    dest_ciudad = dp3.text_input("CIUDAD").upper()
    dest_tax = dp4.text_input("TAX ID / RFC / RUC").upper()
    dp5, dp6 = st.columns(2)
    dest_contacto = dp5.text_input("TEL. CONTACTO")
    dest_cp = dp6.text_input("C.P. / ZIP CODE")

st.divider()
st.markdown("### 📦 PRODUCTOS Y VALORES (CAPTURA DIRECTA)")
seleccion = st.multiselect("Busca productos:", list(productos_proforma.keys()))

items_capturados = []
if seleccion:
    for prod in seleccion:
        info = productos_proforma[prod]
        cp1, cp2, cp3 = st.columns([2, 1, 1])
        with cp1: st.write(f"**{prod}**")
        with cp2: cant = st.number_input(f"Cant.", min_value=1, value=1, key=f"q_{prod}")
        with cp3: precio = st.number_input(f"Precio (USD)", min_value=0.0, value=info[2], step=0.1, key=f"p_{prod}")
        items_capturados.append({"desc_es": prod, "desc_en": info[0], "hs": info[1], "cant": cant, "precio": precio})

st.write("")

# Botón de impresión independiente
if st.button("🖨️ GENERAR E IMPRIMIR FACTURA", use_container_width=True, type="primary"):
    if not dest_nom or not items_capturados:
        st.error("Vida, faltan datos del hotel o productos.")
    else:
        # Se envía 'rem_atn' a la función para que aparezca en la impresión
        rem_info = {
            "empresa": "JABONES Y PRODUCTOS ESPECIALIZADOS", 
            "direccion": "C. Cernícalo 155, La Aurora", 
            "ciudad": "Guadalajara, Jalisco, 44460", 
            "pais": "MEXICO", 
            "tel": rem_tel,
            "atencion": rem_atn
        }
        dest_info = {"nombre": dest_nom, "calle": dest_calle, "ciudad": dest_ciudad, "estado": dest_estado, "pais": dest_pais, "tel": dest_contacto, "tax_id": dest_tax, "cp": dest_cp}
        
        proforma_html = generar_proforma_html(rem_info, dest_info, items_capturados, {"folio": f_folio, "fecha": f_fecha, "guia": f_guia})
        
        st.session_state.folio_num += 1
        st.success("¡Documento generado con éxito!")
        components.html(f"<html><body>{proforma_html}<script>window.print();</script></body></html>", height=0)




















































































