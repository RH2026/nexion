import base64
from datetime import datetime, date
import io
import re
import time
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
import reportlab.lib.units as units

# ==========================================
# VALIDACIÓN DE PERMISO DE SECCIÓN
# ==========================================
from layout import verificar_permiso_pagina, vars_css
verificar_permiso_pagina("REPORTES", "ENVIO DE MUESTRAS")

cm = units.cm

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="REPORTES", submodulo_actual="MUESTRAS")

# ==========================================
# LÓGICA Y COMPONENTES DEL MÓDULO DE MUESTRAS
# ==========================================
def main():
    GITHUB_USER = "RH2026"
    GITHUB_REPO = "nexion"
    GITHUB_PATH = "muestras.csv"
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 
    
    precios = {
        "Envio Muestras Especiales": 0.0,
        "Kit Accesorios Ecologicos": 47.85,
        "kit Accesorios Lavarino": 47.85,
        "kit Dispensador Almond 250": 218.33,
        "kit Dispensador Biogena 250": 216.00,
        "kit Dispensador Cava 250": 230.58,
        "kit Dispensador Persea 250": 275.00,
        "kit Dispensador Botánicos 250": 274.17,
        "kit Dispensador Dove 250": 125.00,
        "kit Dispensador Rainforest 250": 216.00,
        "Kit Elements": 29.34,
        "Kit Almond": 33.83,
        "Kit Biogena": 48.95,
        "Kit Cava": 34.59,
        "Kit Persa": 58.02,
        "Kit Lavarino": 36.30,
        "Kit Botánicos": 29.34,
        "Kit Rainforest": 30.34,
        "JHJY-0050 Llave magnetica para soporte JH": 180.00,
        "JHJY-0033 Rack JH  Color Blanco de 2 pzas": 65.00,
        "JHJY-0034 Rack JH  Color Blanco de 1 pzas": 50.00,
        "JHJY-0045 Soporte de acero inoxidable Jypesa INOX Cap lock individual": 679.00,
        "JHJY-0046 Soporte de acero inoxidable Jypesa INOX Cap lock doble": 679.00,
        "JHJY-0047 Soporte de acero inoxidable Jypesa INOX Cap lock triple": 679.00,
        "JHJY-0037 Llave para rack de acero Jypesa": 25.50,
        "JHJY-0026 Rack JH Individual color Negro": 40.28,
        "JHJY-0027 Rack JH Doble color Negro": 40.28,
        "JHJY-0065 KIT Bracket+Key+3M Super Glue/Screw black ANTI-THEFT Emperor Semi circular 12 Piezas/Caja": 418.2,
        "JHJY-0064 KIT Bracket+Key+3M Super Glue/Screw black ANTI-THEFT Easy snap 12 Piezas/Caja": 418.2,
        "4029-A90 NOCEAN Cepillo Dental eco amigable nOcean caja con 144 piezas": 4.1,
        "4029-A91 NOCEAN Peine de bambu eco amigable nOcean caja con 200 piezas": 8.74,
        "4029-A92 NOCEAN Kit de afeitar eco amigable nOcean caja con 200 piezas": 16.60,
        "4029-A93 NOCEAN Kit de vanidad eco amigable nOcean caja con 500 piezas": 3.8,
        "4029-A95 NOCEAN Kit de costura eco amigable nOcean caja con 500 piezas": 2.4,
        "4029-A96 NOCEAN Limpia calzado eco amigable nOcean caja con 500 piezas": 4.4,
        "4029-A97 NOCEAN Toallita desmaquillante comprimida eco amigable nOcean caja con 300 piezas": 5.2,
        "4029-A98 NOCEAN Esponja de celulosa comprimida eco amigable nOcean caja con 500 piezas": 3.95,
        "4052-L17 CAVA Shampoo Cava Nocean 40 ml. Caja con 150 piezas": 5.99,
        "4052-L18 CAVA Acondicionador Cava Nocean 40 ml. Caja con 150 piezas": 5.99,
        "4052-L19 CAVA Gel de baño Cava Nocean 40 ml. Caja con 150 piezas": 5.99,
        "4052-L20 CAVA Crema Humectante Cava Nocean 40 ml. Caja con 150 piezas": 6.44,
        "4018-A23 Limpia calzado Lavarino Cosso. Cajilla Nva. Imagen Caja con 225 piezas": 3.23,
        "4018-A24 Gorra de baño Lavarino Cosso. Cajilla Nva. Imagen Caja con 225 piezas": 2.26,
        "4018-A25 KIT dental Lavarino Cosso. Cajilla Nva. Imagen Caja con 144 piezas": 11.60,
        "4018-A26 KIT de vanidad Lavarino Cosso. Cajilla Nva. Imagen Caja con 150 piezas": 2.95,
        "4018-A27 KIT de afeitar Lavarino Cosso. Cajilla Nva. Imagen Caja con 116 piezas": 7.230,
        "4018-A28 KIT de costura Lavarino Cosso. Cajilla Nva. Imagen Caja con 225 piezas": 1.90,
        "4018-A29 Peine Lavarino Cosso. Manga Nva. Imagen 400 Piezas": 2.44,
        "68829526 Rack Dove Dove Mlac Bracket Metalized Bottle 1 Pieza": 193.90
    }
    
    def limpiar_parentesis(texto):
        return re.sub(r'\(.*?\)', '', str(texto)).strip()
    
    def dibujar_texto_bloque_pro(c, texto, x_centro, y_inicio, ancho_max, fuente, tamano_max, interlineado, max_lineas=3):
        texto = str(texto).upper()
        lineas = simpleSplit(texto, fuente, tamano_max, ancho_max)
        
        tamano_actual = tamano_max
        while len(lineas) > max_lineas and tamano_actual > 8:
            tamano_actual -= 0.5
            lineas = simpleSplit(texto, fuente, tamano_actual, ancho_max)
        
        c.setFont(fuente, tamano_actual)
        y_actual = y_inicio
        for line in lineas[:max_lineas]: 
            c.drawCentredString(x_centro, y_actual, line)
            y_actual -= interlineado
        return y_actual 
    
    def generar_etiquetas_limpias(reg_datos, total_etqs, factura_val, transporte_val):
        output = io.BytesIO()
        w_rec, h_rec = 10.40 * cm, 8.08 * cm
        c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
        x_offset, y_offset = 0.0 * cm, 0.0 * cm
        
        nombre_crudo = reg_datos.get('NOMBRE DEL HOTEL', 'SIN NOMBRE')
        nombre_final = limpiar_parentesis(nombre_crudo)
        direccion_final = reg_datos.get('DESTINO', 'DIRECCIÓN NO DISPONIBLE')
        transporte_final = str(transporte_val if transporte_val else 'TRES GUERRAS')
    
        for i in range(total_etqs):
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x_offset, y_offset, w_rec, h_rec)
            c.setDash([])
            c.setStrokeColorRGB(0, 0, 0)
    
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_offset + (w_rec/2), y_offset + h_rec - 0.3*cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
            c.setFont("Helvetica", 6)
            info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
            dibujar_texto_bloque_pro(c, info_contacto, x_offset + (w_rec/2), y_offset + h_rec - 0.7*cm, 10*cm, "Helvetica", 6, 0.25*cm, max_lineas=1)
            
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.line(x_offset + 0.5*cm, y_offset + h_rec - 1.0*cm, x_offset + w_rec - 0.5*cm, y_offset + h_rec - 1.0*cm)
            c.setStrokeColorRGB(0, 0, 0)
    
            y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_offset + (w_rec/2), y_offset + h_rec - 2.0*cm, 10*cm, "Helvetica-Bold", 26, 0.75*cm, max_lineas=3)
    
            y_inicio_direccion = y_termino_nombre - 0.7*cm
            if y_inicio_direccion > y_offset + 4.3*cm: y_inicio_direccion = y_offset + 4.3*cm
            if y_inicio_direccion < y_offset + 2.9*cm: y_inicio_direccion = y_offset + 2.9*cm
            dibujar_texto_bloque_pro(c, direccion_final, x_offset + (w_rec/2), y_inicio_direccion, 10.0 * cm, "Helvetica-Bold", 14.5, 0.5*cm, max_lineas=3)
    
            c.setLineWidth(0.6)
            y_linea_pie = y_offset + 1.4*cm
            c.line(x_offset + 0.2*cm, y_linea_pie, x_offset + w_rec - 0.2*cm, y_linea_pie)
            
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 0.4*cm, "FACTURA")
            c.drawCentredString(x_offset + 5.2*cm, y_linea_pie - 0.4*cm, "CAJAS / BULTO")
            c.drawString(x_offset + 7.5*cm, y_linea_pie - 0.4*cm, "TRANSPORTE")
    
            c.setFont("Helvetica-Bold", 13)
            c.drawString(x_offset + 0.5*cm, y_linea_pie - 1.0*cm, str(factura_val))
            c.drawCentredString(x_offset + 5.2*cm, y_linea_pie - 1.0*cm, f"{i + 1} / {total_etqs}")
            c.drawString(x_offset + 7.5*cm, y_linea_pie - 1.0*cm, transporte_final[:18])
            c.showPage()
    
        c.save()
        return output.getvalue()

    def obtener_datos_github():
        try:
            url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = r.json()
                df = pd.read_csv(io.BytesIO(base64.b64decode(content['content'])))
                return df, content['sha']
        except:
            pass
        return pd.DataFrame(), None
    
    def subir_a_github(df, sha, msg):
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        csv_string = df.to_csv(index=False)
        payload = {"message": msg, "content": base64.b64encode(csv_string.encode()).decode(), "sha": sha}
        return requests.put(url, json=payload, headers=headers).status_code == 200                        

    def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, tel_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, productos, comentarios, paq_nombre, tipo_pago, total_cajas=1):
        filas_prod = ""
        for p in productos:
            filas_prod += f"""
            <tr>
                <td style='padding: 8px; border: 1px solid black;'>{str(p['desc']).upper()}</td>
                <td style='text-align:center; border: 1px solid black;'>-</td>
                <td style='text-align:center; border: 1px solid black;'>PZAS</td>
                <td style='text-align:center; border: 1px solid black;'>{p['cant']}</td>
            </tr>"""
        
        html = f"""
        <style>
            @media print {{
                @page {{ size: letter; margin: 1cm; }}
                body {{ margin: 0; padding: 0; }}
            }}
        </style>
        <div style="font-family:Arial; width:100%; box-sizing:border-box; background: white; color: black; display: flex; flex-direction: column; min-height: 95vh;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                <div style="text-align: left;">
                    <h1 style="margin: 0; font-size: 18px; font-weight: 900; color: #000;">Jabones y Productos Especializados</h1>
                    <p style="margin: 0; font-size: 11px; font-weight: bold; text-transform: uppercase; color: #444;">Distribución y Logística | 2026</p>
                </div>
                <div style="text-align: right;">
                    <h2 style="margin: 0; font-size: 16px; text-decoration: underline; font-weight: 900;">ORDEN DE EMBARQUE</h2>
                    <p style="margin: 5px 0 0 0; font-size: 13px;"><b>{paq_nombre} - {tipo_pago}</b></p>
                </div>
            </div>
            <table style="width:100%; border-collapse:collapse; margin-bottom:15px; font-size: 12px;">
                <tr>
                    <td style="border:1px solid black; padding:6px;"><b>FOLIO:</b> {folio}</td>
                    <td style="border:1px solid black; padding:6px;"><b>ENVÍO:</b> {str(paq).upper()}</td>
                    <td style="border:1px solid black; padding:6px;"><b>ENTREGA:</b> {str(entrega).upper()}</td>
                    <td style="border:1px solid black; padding:6px;"><b>TOTAL CAJAS:</b> <span style="font-size: 13px; font-weight: 900; color: #000;">{total_cajas} </span></td>
                    <td style="border:1px solid black; padding:6px;"><b>FECHA:</b> {fecha}</td>
                </tr>
            </table>
            <div style="display:flex; gap:10px; margin-bottom:15px;">
                <div style="flex:1; border:1px solid black;">
                    <div style="background:withe; color:black; text-align:center; font-weight:bold; font-size:12px; padding:4px;">REMITENTE</div>
                    <div style="padding:8px; font-size:11px; line-height:1.4;">
                        <b>JABONES Y PRODUCTOS ESPECIALIZADOS</b><br>
                        C. Cernícalo 155, La Aurora C.P.: 44460<br>
                        ATN: {str(atn_rem).upper()}<br>
                        TEL: {tel_rem}<br>
                        SOLICITÓ: {str(solicitante).upper()}
                    </div>
                </div>
                <div style="flex:1; border:1px solid black;">
                    <div style="background:#ffffff; color:black; text-align:center; font-weight:bold; font-size:12px; padding:4px;">DESTINATARIO</div>
                    <div style="padding:8px; font-size:11px; line-height:1.4;">
                        <b>{str(hotel).upper()}</b><br>
                        {f"{str(calle).upper()}<br>" if calle and calle != "-" else ""}
                        {f"Col: {str(col).upper()} " if col and col != "-" else ""}
                        {f"C.P.: {cp}" if cp and cp != "-" else ""}
                        {"<br>" if (col and col != "-") or (cp and cp != "-") else ""}
                        {str(ciudad).upper()}{f", {str(estado).upper()}" if estado and estado != "-" else ""}<br>
                        ATN: {str(contacto).upper()}
                    </div>
                </div>
            </div>
            <div style="flex-grow: 1;">
                <table style="width:100%; border-collapse:collapse; margin-top:5px; font-size:12px;">
                    <tr style="background:#ffffff; color:black;">
                        <th style="padding: 8px; border: 1px solid black;">DESCRIPCIÓN DEL PRODUCTO</th>
                        <th style="border: 1px solid black; width: 100px;">CÓDIGO</th>
                        <th style="border: 1px solid black; width: 80px;">U.M.</th>
                        <th style="border: 1px solid black; width: 80px;">CANT.</th>
                    </tr>
                    {filas_prod}
                </table>
                <div style="border:1px solid black; padding:10px; margin-top:15px; font-size:12px; min-height: 80px;">
                    <b>COMENTARIOS:</b><br>{str(comentarios).upper()}
                </div>
            </div>
            <div style="margin-top: 40px; padding-bottom: 20px;">
                <div style="text-align:center; font-size:12px; font-weight:bold; margin-bottom:40px; border-bottom: 2px solid black; padding-bottom: 8px;">
                    RECIBO DE CONFORMIDAD DEL CLIENTE
                </div>
                <div style="display:flex; justify-content:space-between; text-align:center; font-size:11px;">
                    <div style="width:30%;">__________________________<br><b>FECHA RECIBO</b></div>
                    <div style="width:35%;">__________________________<br><b>NOMBRE Y FIRMA</b></div>
                    <div style="width:30%;">__________________________<br><b>SELLO DE RECIBIDO</b></div>
                </div>
            </div>
        </div>
        """
        return html
    
    df_actual, sha_actual = obtener_datos_github()
    
    if not df_actual.empty:
        for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL", "ESTATUS"]:
            if col not in df_actual.columns: 
                df_actual[col] = "NO SURTIDO" if col == "ESTATUS" else 0.0
        nuevo_num = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1)
    else:
        nuevo_num = 1
    
    st.write("")
    with st.container():
        f_paq_nombre = ""
        f_tipo_pago = ""
        
        c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])
        f_folio = c1.text_input(":material/confirmation_number: FOLIO", value=f"JYP-{nuevo_num}", disabled=True)
        f_paq_sel = c2.selectbox(":material/local_shipping: FORMA DE ENVÍO", ["Envio Pagado", "Envio por cobrar", "Entrega Personal"])
        f_ent_sel = c3.selectbox(":material/home_pin: TIPO DE ENTREGA", ["Domicilio", "Ocurre Oficina"])
        f_fecha_sel = c4.date_input(":material/calendar_today: FECHA", date.today())
    
    st.divider()
    
    col_rem, col_dest = st.columns(2)
    with col_rem:
        st.markdown('<div style="background:#4e73df;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">REMITENTE</div>', unsafe_allow_html=True)
        st.write("")
        st.text_input(":material/corporate_fare: Nombre", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
        c_rem1, c_rem2 = st.columns([2, 1])
        f_atn_rem = c_rem1.text_input(":material/person: Atención", "RIGOBERTO HERNANDEZ")
        f_tel_rem = c_rem2.text_input(":material/call: Teléfono", "3319753122")
        f_soli = st.text_input(":material/badge: Solicitante / Agente", placeholder="NOMBRE DE QUIEN SOLICITA LAS MUESTRAS", key=f"soli_{st.session_state.get('reset_key', 0)}").upper()
    
    with col_dest:
        st.markdown('<div style="background:#f6c23e;color:black;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">DESTINATARIO / HOTEL</div>', unsafe_allow_html=True)
        st.write("")
        f_h = st.text_input(":material/hotel: Hotel / Nombre", key=f"h_{st.session_state.get('reset_key', 0)}").upper()
        f_ca = st.text_input(":material/location_on: Calle y Número", key=f"ca_{st.session_state.get('reset_key', 0)}").upper()
        cd1, cd2 = st.columns(2)
        f_co = cd1.text_input(":material/map: Colonia", key=f"co_{st.session_state.get('reset_key', 0)}").upper()
        f_cp = cd2.text_input(":material/mailbox: C.P.", key=f"cp_{st.session_state.get('reset_key', 0)}")
        cd3, cd4 = st.columns(2)
        f_ci = cd3.text_input(":material/location_city: Ciudad", key=f"ci_{st.session_state.get('reset_key', 0)}").upper()
        f_es = cd4.text_input(":material/public: Estado", key=f"es_{st.session_state.get('reset_key', 0)}").upper()
        f_con = st.text_input(":material/contact_phone: Contacto Receptor", placeholder="NOMBRE Y TELÉFONO DE QUIEN RECIBE", key=f"con_{st.session_state.get('reset_key', 0)}").upper()
    
    st.divider()
    
    st.markdown("""
        <style>
        .stMultiSelect div[data-baseweb="select"] { height: auto !important; min-height: 45px !important; }
        .stMultiSelect div[data-baseweb="valueContainer"] { flex-wrap: wrap !important; display: flex !important; gap: 5px !important; padding: 5px 0 !important; }
        .stMultiSelect div[data-baseweb="tag"] { background-color: #384A52 !important; border-radius: 5px; color: white !important; }
        div[data-testid="stNumberInput"] { width: 100% !important; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='display: flex; align-items: center; gap: 10px; margin: 15px 0 10px 0;'><div style='background: #00D4FF; width: 4px; height: 16px; border-radius: 2px;'></div><span style='color: white; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;'>SELECCION DE PRODUCTOS</span></div>", unsafe_allow_html=True)
    
    if "seleccionados_muestras" not in st.session_state:
        st.session_state.seleccionados_muestras = []
    
    def eliminar_producto(prod_a_borrar):
        st.session_state.seleccionados_muestras = [p for p in st.session_state.seleccionados_muestras if p != prod_a_borrar]
    
    seleccionados = st.multiselect(
        ":material/search: Busca y selecciona productos:", 
        list(precios.keys()),
        key=f"prod_select_{st.session_state.get('reset_key', 0)}",
        default=st.session_state.get('seleccionados_muestras', []),
        placeholder="SELECCIONAR PRODUCTOS"
    )
    st.session_state.seleccionados_muestras = seleccionados
    
    prods_actuales = []
    total_cantidad = 0
    total_costo_prods = 0
    
    if seleccionados:
        st.info(f"Has seleccionado {len(seleccionados)} productos. Indica las cantidades abajo:")
        num_filas = (len(seleccionados) + 2) // 3 
        altura_dinamica = min(max(num_filas * 95, 120), 500) 
        
        with st.container(height=altura_dinamica, border=True):
            col_bloque_1, col_bloque_2, col_bloque_3 = st.columns(3)
            for i, p in enumerate(seleccionados):
                target_col = col_bloque_1 if i % 3 == 0 else (col_bloque_2 if i % 3 == 1 else col_bloque_3)
                with target_col:
                    c1, c2, c3 = st.columns([1.5, 1.8, 0.5])
                    with c1:
                        st.markdown(f"<div style='padding-top:10px; font-size:10px; line-height:1.1;'><b>{p.upper()}</b></div>", unsafe_allow_html=True)
                    with c2:
                        q = st.number_input("Cant", min_value=0, step=1, key=f"q_{p}", label_visibility="collapsed")
                    with c3:
                        st.button(":material/delete:", key=f"btn_del_{p}", type="tertiary", on_click=eliminar_producto, args=(p,))
                if q > 0:
                    prods_actuales.append({"desc": p, "cant": q})
                    total_cantidad += q
                    total_costo_prods += (q * (precios.get(p, 0)))
                st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    
    st.markdown("---")
    f_coment = st.text_area("💬 COMENTARIOS ADICIONALES", height=100, placeholder="SI EL PRODUCTO NO ESTA EN LA LISTA SELECCIONABLE, INGRESALOS AQUI O CUALQUIER COMENTARIO ADICIONAL").upper()
    
    st.write("")
    col_b1, col_b2, col_b3 = st.columns([1, 1, 0.5]) 

    if col_b1.button(":material/save: GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
        if not f_h: 
            st.error("Falta el hotel")
        elif not f_soli:
            st.error("Falta el nombre de quien solicita (Solicitante / Agente)")
        elif not f_con: 
            st.error("Falta el nombre y teléfono de quien recibe")
        elif not prods_actuales: 
            st.error("Selecciona al menos un producto")
        else:
            direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()
            reg = {
                "FOLIO": nuevo_num, 
                "ESTATUS": "NO SURTIDO",
                "FECHA": f_fecha_sel.strftime("%Y-%m-%d"), 
                "NOMBRE DEL HOTEL": f_h.upper(), 
                "DESTINO": direccion_completa,
                "CONTACTO": f_con.upper(), 
                "SOLICITO": f_soli.upper(),
                "PAQUETERIA": f_paq_sel.upper(),
                "PAQUETERIA_NOMBRE": f_paq_nombre,
                "NUMERO_GUIA": "", 
                "COSTO_GUIA": 0.0,
                "CANTIDAD_TOTAL": total_cantidad,
                "COSTO_TOTAL": round(total_costo_prods, 2),
                "COMENTARIOS": f_coment
            }
            for p in precios.keys(): reg[p] = 0
            for item in prods_actuales: reg[item["desc"]] = item["cant"]
            
            df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
            if subir_a_github(df_f, sha_actual, f"Folio JYP-{nuevo_num}"):
                st.session_state.folio_actual = nuevo_num
                st.session_state.folio_guardado = True 
                st.success(f"¡Guardado correctamente! Folio: JYP-{nuevo_num}")
                time.sleep(1)
                st.rerun()

    if not st.session_state.get("folio_guardado", False):
        st.markdown('<div style="background-color: rgba(255, 165, 0, 0.1); border-left: 5px solid #FFA500; padding: 10px; margin-bottom: 10px; border-radius: 5px;"><span style="color: white; font-size: 14px;"><b style="color: #FFA500;">BLOQUEO DE SEGURIDAD:</b> Debes guardar el registro antes de poder imprimir.</span></div>', unsafe_allow_html=True)

    if col_b2.button(":material/picture_as_pdf: GUARDAR PDF", use_container_width=True, disabled=not st.session_state.get("folio_guardado", False)):
        folio_final = st.session_state.get("folio_actual", nuevo_num - 1)
        folio_simple = f"JYP-{folio_final}" 
        h_print = generar_html_impresion(folio_simple, f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem, f_soli, f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, prods_actuales, f_coment, f_paq_nombre, f_tipo_pago)
        js_code = f"<html><head><title>{folio_simple}_{f_h}</title></head><body>{h_print}<script>setTimeout(function(){{ window.print(); }}, 500);</script></body></html>"
        components.html(js_code, height=0)

    if col_b3.button(":material/delete_sweep: BORRAR", use_container_width=True):
        st.session_state.folio_guardado = False
        if "folio_actual" in st.session_state: del st.session_state.folio_actual
        st.session_state.seleccionados_muestras = []
        st.session_state.reset_key = st.session_state.get('reset_key', 0) + 1
        st.rerun()

    st.write("")
    with st.container():
        with st.expander("🔍 CONSULTA DE FOLIOS Y GUIAS", expanded=True):
            if not df_actual.empty:
                busqueda = st.text_input("Escribe el nombre del Hotel, Solicitante o Folio para filtrar:").upper()
                df_vista = df_actual.copy().fillna('') 
                if busqueda:
                    df_vista = df_vista[df_vista.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
                
                df_render = df_vista.sort_values(by="FOLIO", ascending=False)
                data_busqueda = df_render.to_dict('records')
                alto_busqueda = min(len(data_busqueda) * 130 + 20, 550) 
                
                tarjetas_busqueda_html = ""
                for item in data_busqueda:
                    detalle_p_busqueda = ""
                    for p_key in precios.keys():
                        cant_p = pd.to_numeric(item.get(p_key, 0), errors='coerce')
                        if pd.notna(cant_p) and cant_p > 0:
                            detalle_p_busqueda += f"• {int(cant_p)} PZAS {str(p_key).upper()}<br>"
                    
                    estatus_val = str(item.get('ESTATUS', 'NO SURTIDO')).upper()
                    badge_status = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:2px 6px; border-radius:10px; font-size:8px; font-weight:800; letter-spacing:1px;'>✓ DESPACHADO</div>" if estatus_val == 'DESPACHADO' else "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:2px 6px; border-radius:10px; font-size:8px; font-weight:800; letter-spacing:1px;'>⚠️ NO SURTIDO</div>"
                    
                    paq_text = item.get('PAQUETERÍA', '') or item.get('PAQUETERIA_NOMBRE', '')
                    guia_text = item.get('NÚMERO DE GUÍA', '') or item.get('NUMERO_GUIA', '')
                    
                    tarjetas_busqueda_html += f"""
                    <div class="card-busqueda" style="padding: 15px; margin-bottom: 10px; background: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1.1;"><div class="label-mini">Folio / Fecha</div><div class="val-folio">#{str(item['FOLIO'])}</div><div style="color: rgba(255,255,255,0.5); font-size: 10px; margin-bottom: 5px;">{str(item['FECHA'])[:10]}</div>{badge_status}</div>
                        <div style="flex: 2.0; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);"><div class="label-mini">Hotel / Destino</div><div class="val-hotel">{str(item.get('NOMBRE DEL HOTEL', ''))[:30]}</div><div class="val-soli">SOLICITÓ: {str(item.get('SOLICITO', ''))[:30]}</div></div>
                        <div style="flex: 2.5; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);"><div class="label-mini">Productos Solicitados</div><div style="color: #FFFFFF; font-size: 9px; line-height: 1.4; opacity: 0.9;">{detalle_p_busqueda if detalle_p_busqueda else '<i>Sin detalle</i>'}</div></div>
                        <div style="flex: 1.6; text-align: right; border-left: 1px solid rgba(255,255,255,0.05); padding-left: 10px;"><div class="val-guia {'pendiente' if not paq_text else ''}">{paq_text if paq_text else 'PAQUETERÍA PENDIENTE'}</div><div class="val-sub-guia {'pendiente' if not guia_text else ''}">{guia_text if guia_text else 'GUÍA PENDIENTE'}</div></div>
                    </div>
                    """

                html_busqueda = f"""<div style="font-family: 'Inter', sans-serif; padding-right: 10px; height: {alto_busqueda}px; overflow-y: auto;"><style>.card-busqueda {{ transition: all 0.3s ease; }} .card-busqueda:hover {{ border-color: #38bdf8; background: #2d3b42; transform: translateX(5px); }} .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }} .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }} .val-hotel {{ color: #FFFFFF; font-size: 13px; font-weight: 700; margin-top: 2px; }} .val-soli {{ color: #FFD700; font-size: 10px; font-weight: 600; margin-top: 2px; opacity: 0.8; }} .val-guia {{ color: #38bdf8; font-family: monospace; font-size: 14px; font-weight: 800; line-height: 1.2; }} .val-sub-guia {{ color: #FFFFFF; font-family: monospace; font-size: 12px; font-weight: 700; margin-top: 4px; }} .pendiente {{ color: #f97316 !important; font-style: italic; opacity: 0.8; font-size: 10px; font-weight: 400; }}</style>{tarjetas_busqueda_html}</div>"""
                components.html(html_busqueda, height=alto_busqueda, scrolling=False)
            else:
                st.info("No hay registros todavía.")
            
    st.divider()
    
    usuario_logeado = st.session_state.get('usuario_activo', 'Invitado')
    permisos_usuario = st.session_state.get('permisos', {})
    es_admin_general = (usuario_logeado.upper() == "RIGOBERTO" or permisos_usuario.get("ACCESS CONTROL", False) or permisos_usuario.get("PANEL MUESTRAS", False) or "LOGISTICA" in usuario_logeado.upper())
    
    if es_admin_general or usuario_logeado in ["Rigoberto", "JMoreno"]:
        st.markdown(
            '<div style="background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.2); border-left: 4px solid #00D4FF; padding: 10px 15px; border-radius: 6px; margin: 20px 0 15px 0;">'
            '<span style="color: #00D4FF; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">'
            '🛠 PANEL DE ADMINISTRACIÓN — USO EXCLUSIVO DE LOGÍSTICA</span></div>', 
            unsafe_allow_html=True
        )
        t1, t2, t3 = st.tabs(["Gestionar Folios Existentes", "Historial y Reportes", "Edicion"])
        
        with t1:
            if not df_actual.empty:
                df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
                opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]
                fol_sel_texto = st.selectbox("Seleccionar Folio para procesar (Logística):", opciones_folios, index=None, placeholder="Busca el folio que envió Ventas...")
                
                datos_fol = None
                fol_edit = None
                if fol_sel_texto:
                    fol_edit = int(fol_sel_texto.split(" - ")[0])
                    datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]
                    detalle_p_admin = ""
                    for p in precios.keys():
                        if datos_fol.get(p, 0) > 0: detalle_p_admin += f"• {int(datos_fol[p])} PZAS {str(p).upper()}<br>"
                    
                    borde_color = "#00FFAA" if str(datos_fol.get('ESTATUS', 'NO SURTIDO')).upper() == "DESPACHADO" else "#FF4444"
                    badge_admin = f"<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid {borde_color}; color:{borde_color}; padding:4px 10px; border-radius:12px; font-size:10px; font-weight:800; margin-top:8px;'>{ '✓ DESPACHADO' if borde_color == '#00FFAA' else '⚠️ NO SURTIDO' }</div>"

                    st.markdown(f'<div style="background: #263238; border: 1px solid rgba(255,255,255,0.05); border-left: 6px solid {borde_color}; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; padding: 20px 30px; margin-top: 15px; margin-bottom: 5px;"><div style="flex: 1.2;"><div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:4px;">FOLIO</div><div style="color: {borde_color}; font-family: monospace; font-size: 22px; font-weight: 900;">#{datos_fol["FOLIO"]}</div>{badge_admin}</div><div style="flex: 2.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.08);"><div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px;">HOTEL</div><div style="color: #FFFFFF; font-size: 14px; font-weight: 800;">{str(datos_fol.get("NOMBRE DEL HOTEL","")).upper()}</div><div style="color: #38bdf8; font-size: 11px; font-weight: 700;">Atn: {str(datos_fol.get("CONTACTO","")).upper()}</div></div><div style="flex: 2.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.08);"><div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:6px;">PRODUCTOS</div><div style="color: #FFFFFF; font-size: 10px; line-height: 1.6;">{detalle_p_admin}</div></div></div>', unsafe_allow_html=True)

                st.divider() 
                c_adm1, c_adm2 = st.columns(2)
                with c_adm1:
                    n_paq_nombre = st.selectbox("Nombre de Paquetería", ["AEREO", "NO APLICA","TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES", "FEDEX", "PAQMEX", "TINY PACK"], index=None, placeholder="Selecciona paquetería...")
                    n_tipo_pago = st.selectbox("Modalidad de Pago", ["NO APLICA","CREDITO", "COBRO DESTINO"], index=None, placeholder="¿Cómo se paga?")
                    n_gui = st.text_input("Número de Guía").upper()
                    n_costo_guia = st.number_input("Costo de Flete ($)", min_value=0.0)
                    n_total_cajas = st.number_input("Cantidad Final de Cajas / Bultos", min_value=1, max_value=100, value=max(int(datos_fol.get('CANTIDAD_TOTAL', 1)) if datos_fol is not None else 1, 1), step=1)
                    
                    if st.button(":material/update: GUARDAR Y ACTUALIZAR FOLIO", use_container_width=True, disabled=not fol_sel_texto) and datos_fol is not None:
                        idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                        df_actual.at[idx, "PAQUETERIA_NOMBRE"] = n_paq_nombre
                        df_actual.at[idx, "MODALIDAD_PAGO"] = n_tipo_pago
                        df_actual.at[idx, "NUMERO_GUIA"] = n_gui
                        df_actual.at[idx, "COSTO_GUIA"] = n_costo_guia
                        df_actual.at[idx, "CANTIDAD_TOTAL"] = n_total_cajas 
                        df_actual.at[idx, "ESTATUS"] = "DESPACHADO" 
                        if subir_a_github(df_actual, sha_actual, f"Logistica Folio {fol_edit}"):
                            st.success(f"FOLIO JYP-{fol_edit} GUARDADO")
                            time.sleep(1.5)
                            st.rerun()
                
                with c_adm2:
                    if st.button(":material/print: IMPRIMIR FORMATO ACTUALIZADO", use_container_width=True, disabled=not fol_sel_texto) and datos_fol is not None:
                        prods_re = [{"desc": p, "cant": int(datos_fol[p])} for p in precios.keys() if p in datos_fol and datos_fol[p] > 0]
                        h_re = generar_html_impresion(f"JYP-{int(datos_fol['FOLIO'])}", datos_fol.get("PAQUETERIA", "ENVIO"), datos_fol.get("TIPO_ENTREGA", "DOMICILIO"), datos_fol["FECHA"], "RIGOBERTO HERNANDEZ", "3319753122", datos_fol["SOLICITO"], datos_fol["NOMBRE DEL HOTEL"], "", "", "", datos_fol["DESTINO"], "", datos_fol["CONTACTO"], prods_re, datos_fol.get("COMENTARIOS", ""), n_paq_nombre or "S/P", n_tipo_pago or "PENDIENTE", total_cajas=n_total_cajas)
                        components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)
                    
                    if fol_sel_texto and datos_fol is not None:
                        pdf_etq_bytes = generar_etiquetas_limpias(datos_fol, int(n_total_cajas), f"JYP-{int(datos_fol['FOLIO'])}", n_paq_nombre or datos_fol.get("PAQUETERIA", "TRES GUERRAS"))
                        st.download_button(label=":material/save: DESCARGAR ETIQUETA PDF", data=pdf_etq_bytes, file_name=f"Etiqueta_JYP-{int(datos_fol['FOLIO'])}.pdf", mime="application/pdf", use_container_width=True)
        
        with t2:
            if not df_actual.empty:
                df_actual['FECHA'] = df_actual['FECHA'].astype(str).str.strip()
                df_actual['FECHA_DT'] = pd.to_datetime(df_actual['FECHA'], format='%Y-%m-%d', errors='coerce').fillna(pd.to_datetime(df_actual['FECHA'], dayfirst=True, errors='coerce'))
                df_actual['MES_FILTRO'] = df_actual['FECHA_DT'].dt.strftime('%m - %Y').fillna("SIN FECHA")
                meses_lista = sorted([m for m in df_actual['MES_FILTRO'].unique() if m != "SIN FECHA"], reverse=True)
                if "SIN FECHA" in df_actual['MES_FILTRO'].values: meses_lista.append("SIN FECHA")
                
                mes_sel = st.selectbox(":material/calendar_month: FILTRAR PERIODO", ["MOSTRAR TODO"] + meses_lista)
                df_render = df_actual[df_actual['MES_FILTRO'] == mes_sel].copy() if mes_sel != "MOSTRAR TODO" else df_actual.copy()
                
                t_prod, t_flete = df_render["COSTO_TOTAL"].sum(), df_render["COSTO_GUIA"].sum()
                tarjetas_html = ""
                for _, r in df_render.fillna(0).sort_values(by="FOLIO", ascending=False).iterrows():
                    detalle_p = "".join([f"• {int(r[p])} PZAS {str(p).upper()}<br>" for p in precios.keys() if r.get(p, 0) > 0])
                    badge_html = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:2px 8px; border-radius:12px; font-size:9px;'>✓ DESPACHADO</div>" if str(r.get('ESTATUS', '')) == "DESPACHADO" else "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:2px 8px; border-radius:12px; font-size:9px;'>⚠️ NO SURTIDO</div>"
                    tarjetas_html += f'<div style="padding: 15px; margin-bottom: 10px; background: #263238; border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; display: flex; justify-content: space-between; align-items: center;"><div style="flex:1;"><b>#{r["FOLIO"]}</b><br>{r["FECHA"]}<br>{badge_html}</div><div style="flex:2.5; padding:0 15px;"><b>{str(r["SOLICITO"]).upper()}</b><br>{str(r["NOMBRE DEL HOTEL"]).upper()}</div><div style="flex:2.5; font-size:9px;">{detalle_p}</div><div style="flex:1.5; text-align:right;">Prod: ${r["COSTO_TOTAL"]:,.2f}<br>Flete: ${r["COSTO_GUIA"]:,.2f}</div></div>'
                
                components.html(f'<div style="height:400px; overflow-y:auto; font-family:sans-serif; color:white;">{tarjetas_html}</div>', height=420)
        
        with t3:
            if not df_actual.empty:
                opciones_edit = [f"Folio #{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']} ({r['FECHA']})" for _, r in df_actual.sort_values(by="FOLIO", ascending=False).iterrows()]
                folio_a_editar = st.selectbox("Selecciona el Folio que deseas modificar o eliminar:", opciones_edit, index=None, placeholder="Escribe el folio...")
                if folio_a_editar:
                    num_folio_sel = int(folio_a_editar.split(" - ")[0].replace("Folio #", ""))
                    idx_fila = df_actual.index[df_actual['FOLIO'] == num_folio_sel].tolist()[0]
                    registro_sel = df_actual.loc[idx_fila]
                    
                    with st.form(key=f"form_edicion_{num_folio_sel}"):
                        nuevo_hotel = st.text_input("Nombre del Hotel", value=str(registro_sel.get("NOMBRE DEL HOTEL", ""))).upper()
                        nuevo_solicito = st.text_input("Solicitante", value=str(registro_sel.get("SOLICITO", ""))).upper()
                        nuevo_estatus = st.selectbox("Estatus", ["NO SURTIDO", "DESPACHADO"], index=0 if str(registro_sel.get("ESTATUS", "")) == "NO SURTIDO" else 1)
                        
                        if st.form_submit_button("GUARDAR CAMBIOS EN ESTE FOLIO", use_container_width=True):
                            df_actual.at[idx_fila, "NOMBRE DEL HOTEL"] = nuevo_hotel
                            df_actual.at[idx_fila, "SOLICITO"] = nuevo_solicito
                            df_actual.at[idx_fila, "ESTATUS"] = nuevo_estatus
                            if subir_a_github(df_actual, sha_actual, f"Edicion Folio JYP-{num_folio_sel}"):
                                st.success("¡Actualizado con éxito!")
                                time.sleep(1)
                                st.rerun()

if __name__ == "__main__":
    main()
