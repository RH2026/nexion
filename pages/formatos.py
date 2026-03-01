import streamlit as st
import streamlit.components.v1 as components
from datetime import date

# --- CONFIGURACIÓN DE PRODUCTOS BILINGÜES ---
# Diccionario: "Nombre en Español": ("English Name", "Harmonized Code (HS)", "Precio Unitario USD")
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

    html = f"""
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
                <p style="margin:5px 0; font-size: 0.9em;">
                    <b>{datos_rem['empresa']}</b><br>
                    {datos_rem['direccion']}<br>
                    {datos_rem['ciudad']}, {datos_rem['pais']}<br>
                    TEL: {datos_rem['tel']}
                </p>
            </div>
            <div style="border: 1px solid #ccc; padding: 10px;">
                <b style="font-size: 0.9em; color: #666;">CONSIGNEE / DESTINATARIO</b>
                <p style="margin:5px 0; font-size: 0.9em;">
                    <b>{datos_dest['nombre']}</b><br>
                    {datos_dest['calle']}<br>
                    {datos_dest['ciudad']}, {datos_dest['pais']}<br>
                    TEL: {datos_dest['tel']}
                </p>
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
            <tbody>
                {filas_html}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="4" style="text-align:right; padding: 10px;"><b>TOTAL VALUE USD:</b></td>
                    <td style="border: 1px solid #ddd; padding: 10px; text-align:right; background: #eee;"><b>${subtotal:.2f}</b></td>
                </tr>
            </tfoot>
        </table>

        <div style="margin-top: 30px; font-size: 0.75em; border: 1px solid #eee; padding: 10px; background: #fafafa;">
            <p style="margin:0;"><b>Declaration:</b> These commodities, technology or software were exported in accordance with the export administration regulations. Diversion contrary to law is prohibited. The values declared are for customs purposes only.</p>
            <p style="margin:5px 0 0 0;"><b>Declaración:</b> Estas mercancías se exportan de acuerdo con las regulaciones de administración. Los valores declarados son únicamente para fines aduanales.</p>
        </div>

        <div style="margin-top: 40px; display: flex; justify-content: space-between;">
            <div style="width: 200px; border-top: 1px solid #000; text-align:center; font-size: 0.8em;">
                Signature / Firma Remitente
            </div>
            <div style="text-align: right; font-size: 0.8em; color: #999;">
                Generated by NEXION Logistics OS
            </div>
        </div>
    </div>
    """
    return html

# --- INTERFAZ DE CAPTURA ---
st.title("📄 Generador de Proforma Internacional")

with st.expander("🏢 DATOS DEL REMITENTE", expanded=False):
    rem_empresa = st.text_input("Empresa", "JABONES Y PRODUCTOS ESPECIALIZADOS")
    rem_dir = st.text_input("Dirección", "C. Cernícalo 155, La Aurora")
    rem_cty = st.text_input("Ciudad/Estado/CP", "Guadalajara, Jalisco, 44460")
    rem_tel = st.text_input("Teléfono Rem", "3319753122")

with st.form("proforma_form"):
    c1, c2, c3 = st.columns([1, 1, 1])
    f_folio = c1.text_input("Folio / Invoice #", "PRO-2026-001")
    f_fecha = c2.date_input("Fecha de Envío", date.today())
    f_currency = c3.selectbox("Moneda", ["USD (Dólares)", "MXN (Pesos)"])

    st.markdown("### 🏨 DATOS DEL DESTINATARIO")
    d1, d2 = st.columns(2)
    dest_nom = d1.text_input("Nombre / Hotel")
    dest_calle = d2.text_input("Calle y Número")
    d3, d4, d5 = st.columns(3)
    dest_ciudad = d3.text_input("Ciudad/Estado")
    dest_cp = d4.text_input("Zip Code / CP")
    dest_pais = d5.text_input("Country / País", "USA")
    dest_tel = st.text_input("Teléfono Contacto")

    st.markdown("### 📦 PRODUCTOS")
    seleccion = st.multiselect("Selecciona los productos para exportar:", list(productos_proforma.keys()))
    
    items_capturados = []
    if seleccion:
        cols = st.columns(2)
        for i, prod in enumerate(seleccion):
            with cols[i % 2]:
                cant = st.number_input(f"Cantidad: {prod}", min_value=1, step=1, key=f"q_{prod}")
                info = productos_proforma[prod]
                items_capturados.append({
                    "desc_es": prod,
                    "desc_en": info[0],
                    "hs": info[1],
                    "cant": cant,
                    "precio": info[2]
                })

    enviar = st.form_submit_button("🖨️ GENERAR Y PREVISUALIZAR")

if enviar:
    if not dest_nom or not items_capturados:
        st.error("Amor, faltan datos del hotel o no has seleccionado productos.")
    else:
        rem = {"empresa": rem_empresa, "direccion": rem_dir, "ciudad": rem_cty, "pais": "MEXICO", "tel": rem_tel}
        dest = {"nombre": dest_nom, "calle": dest_calle, "ciudad": f"{dest_ciudad} {dest_cp}", "pais": dest_pais, "tel": dest_tel}
        envio = {"folio": f_folio, "fecha": f_fecha}
        
        proforma_html = generar_proforma_html(rem, dest, items_capturados, envio)
        
        st.success("¡Proforma generada con éxito!")
        # Mostramos una previsualización
        st.markdown("---")
        components.html(f"""
            <html>
                <body style="background: #f0f2f6;">
                    {proforma_html}
                    <script>
                        // Al cargar, abre el diálogo de impresión automáticamente
                        window.print();
                    </script>
                </body>
            </html>
        """, height=800, scrolling=True)










































































