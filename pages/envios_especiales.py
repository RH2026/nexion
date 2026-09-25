import base64
from datetime import datetime, date
import io
import re
import time
import unicodedata
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
import reportlab.lib.units as units
from auth import exigir_autenticacion

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Logistics - Envíos Especiales",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO Y PERMISOS
# ============================================================
render_layout(modulo_actual="REPORTES", submodulo_actual="ENVÍOS ESPECIALES")


# ==========================================
# 3. FUNCIONES GLOBALES DE APOYO PARA ETIQUETAS PDF
# (idénticas al patrón de muestras.py — mismo layout de etiqueta)
# ==========================================
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
    w_rec, h_rec = 10.40 * units.cm, 8.08 * units.cm
    c = canvas.Canvas(output, pagesize=(w_rec, h_rec))
    x_offset, y_offset = 0.0 * units.cm, 0.0 * units.cm

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
        c.drawCentredString(x_offset + (w_rec / 2), y_offset + h_rec - 0.3 * units.cm, "JABONES Y PRODUCTOS ESPECIALIZADOS, SA DE CV")
        c.setFont("Helvetica", 6)
        info_contacto = "Privada del Gallo No. 1525 Col. La Aurora C.P. 44460 Guadalajara, JAL México Tel.. 0152 (33) 35402939"
        dibujar_texto_bloque_pro(c, info_contacto, x_offset + (w_rec / 2), y_offset + h_rec - 0.7 * units.cm, 10 * units.cm, "Helvetica", 6, 0.25 * units.cm, max_lineas=1)

        c.setLineWidth(0.3)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.line(x_offset + 0.5 * units.cm, y_offset + h_rec - 1.0 * units.cm, x_offset + w_rec - 0.5 * units.cm, y_offset + h_rec - 1.0 * units.cm)
        c.setStrokeColorRGB(0, 0, 0)

        y_termino_nombre = dibujar_texto_bloque_pro(c, nombre_final, x_offset + (w_rec / 2), y_offset + h_rec - 2.0 * units.cm, 10 * units.cm, "Helvetica-Bold", 26, 0.75 * units.cm, max_lineas=3)

        y_inicio_direccion = y_termino_nombre - 0.7 * units.cm
        if y_inicio_direccion > y_offset + 4.3 * units.cm:
            y_inicio_direccion = y_offset + 4.3 * units.cm
        if y_inicio_direccion < y_offset + 2.9 * units.cm:
            y_inicio_direccion = y_offset + 2.9 * units.cm
        dibujar_texto_bloque_pro(c, direccion_final, x_offset + (w_rec / 2), y_inicio_direccion, 10.0 * units.cm, "Helvetica-Bold", 14.5, 0.5 * units.cm, max_lineas=3)

        c.setLineWidth(0.6)
        y_linea_pie = y_offset + 1.4 * units.cm
        c.line(x_offset + 0.2 * units.cm, y_linea_pie, x_offset + w_rec - 0.2 * units.cm, y_linea_pie)

        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x_offset + 0.5 * units.cm, y_linea_pie - 0.4 * units.cm, "FOLIO")
        c.drawCentredString(x_offset + 5.2 * units.cm, y_linea_pie - 0.4 * units.cm, "CAJAS / BULTO")
        c.drawString(x_offset + 7.5 * units.cm, y_linea_pie - 0.4 * units.cm, "TRANSPORTE")

        c.setFont("Helvetica-Bold", 13)
        c.drawString(x_offset + 0.5 * units.cm, y_linea_pie - 1.0 * units.cm, str(factura_val))

        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x_offset + 5.2 * units.cm, y_linea_pie - 1.0 * units.cm, f"{i + 1} / {total_etqs}")

        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_offset + 7.5 * units.cm, y_linea_pie - 1.0 * units.cm, transporte_final[:18])
        c.showPage()

    c.save()
    return output.getvalue()


# ==========================================
# 4. FUNCIONES MAESTRAS DE SOPORTE
# ==========================================
def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = "".join(
        c for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    ).upper()
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    return " ".join(texto.split())


if "reset_key_cee" not in st.session_state:
    st.session_state.reset_key_cee = 0
if "folio_guardado_cee" not in st.session_state:
    st.session_state.folio_guardado_cee = False


# ==========================================
# 5. INTERFAZ PRINCIPAL (ENVÍOS ESPECIALES)
# ==========================================
def main():
    if "animacion_cargada_cee" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada_cee = True

    GITHUB_USER = "RH2026"
    GITHUB_REPO = "nexion"
    GITHUB_PATH = "CEE.csv"
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

    def obtener_datos_github():
        try:
            url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = r.json()
                df = pd.read_csv(io.BytesIO(base64.b64decode(content['content'])))
                return df, content['sha']
        except Exception:
            pass
        return pd.DataFrame(), None

    def subir_a_github(df, sha, msg):
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        csv_string = df.to_csv(index=False)
        payload = {"message": msg, "content": base64.b64encode(csv_string.encode()).decode(), "sha": sha}
        return requests.put(url, json=payload, headers=headers).status_code == 200

    def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, tel_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, cajas, unidad, comentarios, paq_nombre, tipo_pago, total_cajas=None):
        if total_cajas is None:
            total_cajas = cajas

        filas_prod = f"""
        <tr>
            <td style='padding: 8px; border: 1px solid black;'>ENVÍO DE MERCANCÍA ESPECIAL</td>
            <td style='text-align:center; border: 1px solid black;'>-</td>
            <td style='text-align:center; border: 1px solid black;'>{str(unidad).upper()}</td>
            <td style='text-align:center; border: 1px solid black;'>{cajas}</td>
        </tr>"""

        html = f"""
        <style>
            @media print {{
                @page {{ size: letter; margin: 1cm; }}
                body {{ margin: 0; padding: 0; }}
            }}
        </style>

        <div id="printable-area" style="font-family:Arial; width:100%; box-sizing:border-box; background: white; color: black; display: flex; flex-direction: column; min-height: 95vh;">

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
                    <td style="border:1px solid black; padding:6px;"><b>TOTAL CAJAS:</b> <span style="font-size: 13px; font-weight: 900; color: #000;">{total_cajas}</span></td>
                    <td style="border:1px solid black; padding:6px;"><b>FECHA:</b> {fecha}</td>
                </tr>
            </table>

            <div style="display:flex; gap:10px; margin-bottom:15px;">
                <div style="flex:1; border:1px solid black;">
                    <div style="background:#ffffff; color:black; text-align:center; font-weight:bold; font-size:12px; padding:4px;">REMITENTE</div>
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
                        <th style="padding: 8px; border: 1px solid black;">DESCRIPCIÓN</th>
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

    # --- CARGA DE DATOS ---
    df_actual, sha_actual = obtener_datos_github()

    if not df_actual.empty:
        for col in ["PAQUETERIA_NOMBRE", "MODALIDAD_PAGO", "NUMERO_GUIA", "COSTO_GUIA", "ESTATUS"]:
            if col not in df_actual.columns:
                df_actual[col] = "NO SURTIDO" if col == "ESTATUS" else ""
        nuevo_num = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1)
    else:
        nuevo_num = 1

    # --- CAPTURA NUEVA ---
    st.write("")
    with st.container():
        c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])
        f_folio = c1.text_input(":material/confirmation_number: FOLIO", value=f"CEE-{nuevo_num}", disabled=True)
        f_paq_sel = c2.selectbox(":material/local_shipping: FORMA DE ENVÍO", ["Credito", "Envio por cobrar", "Entrega Personal"])
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
        f_soli = st.text_input(
            ":material/badge: Solicitante / Agente",
            placeholder="NOMBRE DE QUIEN SOLICITA",
            key=f"soli_cee_{st.session_state.reset_key_cee}"
        ).upper()

    with col_dest:
        st.markdown('<div style="background:#f6c23e;color:black;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">DESTINATARIO</div>', unsafe_allow_html=True)
        st.write("")
        f_h = st.text_input(":material/hotel: Hotel / Proveedor", key=f"h_cee_{st.session_state.reset_key_cee}").upper()
        f_ca = st.text_input(":material/location_on: Calle y Número", key=f"ca_cee_{st.session_state.reset_key_cee}").upper()
        cd1, cd2 = st.columns(2)
        f_co = cd1.text_input(":material/map: Colonia", key=f"co_cee_{st.session_state.reset_key_cee}").upper()
        f_cp = cd2.text_input(":material/mailbox: C.P.", key=f"cp_cee_{st.session_state.reset_key_cee}")
        cd3, cd4 = st.columns(2)
        f_ci = cd3.text_input(":material/location_city: Ciudad", key=f"ci_cee_{st.session_state.reset_key_cee}").upper()
        f_es = cd4.text_input(":material/public: Estado", key=f"es_cee_{st.session_state.reset_key_cee}").upper()
        f_con = st.text_input(
            ":material/contact_phone: Contacto Receptor",
            placeholder="QUIEN RECIBE",
            key=f"con_cee_{st.session_state.reset_key_cee}"
        ).upper()

    st.divider()
    st.subheader(":material/inventory_2: Detalles del Envío")
    cd_1, cd_2 = st.columns(2)
    f_cajas = cd_1.number_input("CANTIDAD", min_value=1, step=1, key=f"cajas_cee_{st.session_state.reset_key_cee}")
    f_unidad = cd_2.selectbox("UNIDAD DE MEDIDA", ["CAJA", "PALLET", "BULTO", "SACO", "BIDON", "ATADO", "OTRO"], key=f"unidad_cee_{st.session_state.reset_key_cee}")

    f_coment = st.text_area("💬 COMENTARIOS", height=90, key=f"coment_cee_{st.session_state.reset_key_cee}").upper()

    st.write("")
    col_b1, col_b2, col_b3 = st.columns([1, 1, 0.5])

    if col_b1.button(":material/save: GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
        if not f_h:
            st.error("Falta el hotel")
        elif not f_soli:
            st.error("Falta el nombre de quien solicita (Solicitante / Agente)")
        elif not f_con:
            st.error("Falta el nombre y teléfono de quien recibe")
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
                "TIPO_ENTREGA": f_ent_sel.upper(),
                "PAQUETERIA_NOMBRE": "",
                "MODALIDAD_PAGO": "",
                "NUMERO_GUIA": "",
                "COSTO_GUIA": 0.0,
                "CAJAS": f_cajas,
                "UNIDAD": f_unidad,
                "COMENTARIOS": f_coment,
            }
            df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
            if subir_a_github(df_f, sha_actual, f"Folio CEE-{nuevo_num}"):
                st.session_state.folio_actual_cee = nuevo_num
                st.session_state.folio_guardado_cee = True
                st.success(f"¡Guardado correctamente! Folio: CEE-{nuevo_num}")
                time.sleep(1)
                st.rerun()

    if not st.session_state.folio_guardado_cee:
        st.markdown("""
            <div style="background-color: rgba(255, 165, 0, 0.1); border-left: 5px solid #FFA500; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                <span style="color: white; font-size: 14px;">
                    <b style="color: #FFA500;">BLOQUEO DE SEGURIDAD:</b>
                    Debes guardar el registro antes de poder imprimir.
                </span>
            </div>
        """, unsafe_allow_html=True)

    if col_b2.button(":material/picture_as_pdf: GUARDAR PDF", use_container_width=True, disabled=not st.session_state.folio_guardado_cee):
        folio_final = st.session_state.get("folio_actual_cee", nuevo_num - 1)
        folio_simple = f"CEE-{folio_final}"
        h_print = generar_html_impresion(
            folio_simple, f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem,
            f_soli, f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, f_cajas, f_unidad,
            f_coment, "", ""
        )
        js_code = f"""
            <html><head><title>{folio_simple}_{f_h}</title></head>
            <body>{h_print}<script>setTimeout(function(){{ window.print(); }}, 500);</script></body></html>
        """
        components.html(js_code, height=0)

    if col_b3.button(":material/delete_sweep: BORRAR", use_container_width=True):
        st.session_state.folio_guardado_cee = False
        if "folio_actual_cee" in st.session_state:
            del st.session_state.folio_actual_cee
        st.session_state.reset_key_cee += 1
        st.rerun()

    st.write("")
    st.write("")

    # ==========================================
    # CONSULTA RÁPIDA (tarjetas tipo scroll)
    # ==========================================
    with st.expander("🔍 CONSULTA DE FOLIOS Y GUIAS", expanded=True):
        if not df_actual.empty:
            busqueda = st.text_input("Escribe el nombre del Hotel, Solicitante o Folio para filtrar:").upper()
            df_vista = df_actual.copy().fillna('')
            if busqueda:
                df_vista = df_vista[df_vista.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

            df_render = df_vista.sort_values(by="FOLIO", ascending=False)
            data_busqueda = df_render.to_dict('records')
            alto_busqueda = min(len(data_busqueda) * 120 + 20, 550)

            tarjetas_busqueda_html = ""
            for item in data_busqueda:
                estatus_val = str(item.get('ESTATUS', 'NO SURTIDO')).upper()
                if estatus_val == 'DESPACHADO':
                    badge_status = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:2px 6px; border-radius:10px; font-size:8px; font-weight:800; letter-spacing:1px;'>✓ DESPACHADO</div>"
                else:
                    badge_status = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:2px 6px; border-radius:10px; font-size:8px; font-weight:800; letter-spacing:1px; box-shadow: 0 0 8px rgba(255,68,68,0.4);'>⚠️ NO SURTIDO</div>"

                paq_text = item.get('PAQUETERIA_NOMBRE', '')
                guia_text = item.get('NUMERO_GUIA', '')

                tarjetas_busqueda_html += f"""
                <div class="card-busqueda" style="padding: 15px; margin-bottom: 10px; background: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1.1;">
                        <div class="label-mini">Folio / Fecha</div>
                        <div class="val-folio">CEE-{str(item['FOLIO'])}</div>
                        <div style="color: rgba(255,255,255,0.5); font-size: 10px; margin-bottom: 5px;">{str(item['FECHA'])[:10]}</div>
                        {badge_status}
                    </div>
                    <div style="flex: 2.0; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                        <div class="label-mini">Hotel / Destino</div>
                        <div class="val-hotel">{str(item.get('NOMBRE DEL HOTEL', ''))[:30]}</div>
                        <div class="val-soli">SOLICITÓ: {str(item.get('SOLICITO', ''))[:30]}</div>
                    </div>
                    <div style="flex: 2.0; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                        <div class="label-mini">Envío</div>
                        <div style="color: #FFFFFF; font-size: 10px; line-height: 1.4; opacity: 0.9;">{item.get('CAJAS', '')} {str(item.get('UNIDAD', '')).upper()}</div>
                    </div>
                    <div style="flex: 1.6; text-align: right; border-left: 1px solid rgba(255,255,255,0.05); padding-left: 10px;">
                        <div class="val-guia {'pendiente' if not paq_text else ''}">{ paq_text if paq_text else 'PAQUETERÍA PENDIENTE' }</div>
                        <div class="val-sub-guia {'pendiente' if not guia_text else ''}">{ guia_text if guia_text else 'GUÍA PENDIENTE' }</div>
                    </div>
                </div>
                """

            html_busqueda = f"""
            <div style="font-family: 'Inter', sans-serif; padding-right: 10px; height: {alto_busqueda}px; overflow-y: auto;">
                <style>
                    body {{ background: transparent; margin: 0; padding: 0; }}
                    ::-webkit-scrollbar {{ width: 8px; }}
                    ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                    ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; min-height: 50px; }}
                    .card-busqueda {{ transition: all 0.3s ease; }}
                    .card-busqueda:hover {{ border-color: #38bdf8; background: #2d3b42; transform: translateX(5px); }}
                    .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }}
                    .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }}
                    .val-hotel {{ color: #FFFFFF; font-size: 13px; font-weight: 700; margin-top: 2px; }}
                    .val-soli {{ color: #FFD700; font-size: 10px; font-weight: 600; margin-top: 2px; opacity: 0.8; }}
                    .val-guia {{ color: #38bdf8; font-family: monospace; font-size: 14px; font-weight: 800; line-height: 1.2; }}
                    .val-sub-guia {{ color: #FFFFFF; font-family: monospace; font-size: 12px; font-weight: 700; margin-top: 4px; }}
                    .pendiente {{ color: #f97316 !important; font-style: italic; opacity: 0.8; font-size: 10px; font-weight: 400; }}
                </style>
                {tarjetas_busqueda_html}
            </div>
            """
            components.html(html_busqueda, height=alto_busqueda, scrolling=False)
        else:
            st.info("No hay registros todavía.")

    st.divider()
    st.write("")

    usuario_logeado = st.session_state.get('usuario_activo', 'Invitado')
    permisos_usuario = st.session_state.get('permisos', {})

    es_admin_general = (
        usuario_logeado.upper() == "RIGOBERTO"
        or permisos_usuario.get("ACCESS CONTROL", False)
        or permisos_usuario.get("PANEL COSTOS ESPECIALES", False)
        or "LOGISTICA" in usuario_logeado.upper()
    )

    if es_admin_general or usuario_logeado in ["Rigoberto", "JMoreno"]:
        st.markdown("""
            <div style='background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.2); border-left: 4px solid #00D4FF; padding: 10px 15px; border-radius: 6px; margin: 20px 0 15px 0;'>
                <span style='color: #00D4FF; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;'>
                    🛠 PANEL DE ADMINISTRACIÓN — USO EXCLUSIVO DE LOGÍSTICA
                </span>
            </div>
        """, unsafe_allow_html=True)

        t1, t2, t3 = st.tabs(["Gestionar Folios Existentes", "Historial y Reportes", "Edicion"])

        # ============================================================
        # T1: GESTIONAR FOLIOS (asignar paquetería/guía + re-impresión + etiquetado)
        # ============================================================
        with t1:
            if not df_actual.empty:
                df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
                opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]
                fol_sel_texto = st.selectbox(
                    "Seleccionar Folio para procesar (Logística):",
                    opciones_folios, index=None, placeholder="Busca el folio que envió Ventas..."
                )

                datos_fol = None
                fol_edit = None
                if fol_sel_texto:
                    fol_edit = int(fol_sel_texto.split(" - ")[0])
                    datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]

                    estatus_admin = str(datos_fol.get('ESTATUS', 'NO SURTIDO')).upper()
                    if estatus_admin == "DESPACHADO":
                        badge_admin = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:4px 10px; border-radius:12px; font-size:10px; font-weight:800; letter-spacing:1px; margin-top:8px;'>✓ DESPACHADO</div>"
                        borde_color = "#00FFAA"
                    else:
                        badge_admin = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:4px 10px; border-radius:12px; font-size:10px; font-weight:800; letter-spacing:1px; margin-top:8px; box-shadow: 0 0 10px rgba(255,68,68,0.3);'>⚠️ NO SURTIDO</div>"
                        borde_color = "#FF4444"

                    st.markdown(f"""
                    <div style="background: #263238; border: 1px solid rgba(255,255,255,0.05); border-left: 6px solid {borde_color}; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; padding: 20px 30px; margin-top: 15px; margin-bottom: 5px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                        <div style="flex: 1.2;">
                            <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:4px;">FOLIO A PROCESAR</div>
                            <div style="color: {borde_color}; font-family: monospace; font-size: 22px; font-weight: 900; line-height:1;">CEE-{datos_fol['FOLIO']}</div>
                            <div style="color: rgba(255,255,255,0.5); font-size: 11px; margin-top: 4px;">{datos_fol['FECHA']}</div>
                            {badge_admin}
                        </div>
                        <div style="flex: 2.5; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:4px;">DESTINO / HOTEL</div>
                            <div style="color: #FFFFFF; font-size: 14px; font-weight: 800; margin-bottom: 2px;">{str(datos_fol.get('NOMBRE DEL HOTEL','')).upper()}</div>
                            <div style="color: #38bdf8; font-size: 11px; font-weight: 700; margin-bottom: 4px;">Atn: {str(datos_fol.get('CONTACTO','')).upper()}</div>
                            <div style="color: rgba(255,255,255,0.5); font-size: 10px; line-height:1.4;">{str(datos_fol.get('DESTINO','')).upper()}</div>
                        </div>
                        <div style="flex: 2.0; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div style="font-size: 9px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; margin-bottom:6px;">ENVÍO</div>
                            <div style="color: #FFFFFF; font-size: 13px; line-height: 1.6; opacity: 0.9;">{datos_fol.get('CAJAS', '')} {str(datos_fol.get('UNIDAD', '')).upper()}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()
                st.markdown(
                    "<p style='color: #00FFAA; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px;'>1. ASIGNAR DATOS DE ENVÍO</p>",
                    unsafe_allow_html=True,
                )

                c1, c2, c3 = st.columns(3)
                with c1:
                    n_paq_nombre = st.selectbox(
                        "Nombre de Paquetería",
                        ["AEREO", "NO APLICA", "TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES", "FEDEX", "PAQMEX", "TINY PACK"],
                        index=None, placeholder="Selecciona paquetería..."
                    )
                with c2:
                    n_tipo_pago = st.selectbox(
                        "Modalidad de Pago", ["NO APLICA", "CREDITO", "COBRO DESTINO"],
                        index=None, placeholder="¿Cómo se paga?"
                    )
                with c3:
                    n_gui = st.text_input("Número de Guía").upper()

                c4, c5, c6 = st.columns(3)
                with c4:
                    n_costo_guia = st.number_input("Costo de Flete ($)", min_value=0.0)
                with c5:
                    val_def_cajas = int(datos_fol.get('CAJAS', 1)) if datos_fol is not None else 1
                    n_total_cajas = st.number_input("Cantidad Final de Cajas / Bultos", min_value=1, max_value=200, value=max(val_def_cajas, 1), step=1)
                with c6:
                    val_def_unidad = str(datos_fol.get('UNIDAD', 'CAJA')).upper() if datos_fol is not None else "CAJA"
                    opciones_unidad = ["CAJA", "PALLET", "BULTO", "SACO", "BIDON", "ATADO", "OTRO"]
                    n_unidad = st.selectbox("Unidad de Medida", opciones_unidad, index=opciones_unidad.index(val_def_unidad) if val_def_unidad in opciones_unidad else 0)

                st.info("Verifica los datos antes de imprimir. La base de datos no se afecta hasta que guardes.")

                b1, b2, b3 = st.columns(3)
                with b1:
                    btn_guardar = st.button(":material/update: GUARDAR Y ACTUALIZAR FOLIO", use_container_width=True, disabled=not fol_sel_texto)
                with b2:
                    btn_imprimir = st.button(":material/print: IMPRIMIR FORMATO ACTUALIZADO", use_container_width=True, disabled=not fol_sel_texto)
                with b3:
                    if fol_sel_texto and datos_fol is not None:
                        transporte_etq = n_paq_nombre if n_paq_nombre else datos_fol.get("PAQUETERIA_NOMBRE", datos_fol.get("PAQUETERIA", "TRES GUERRAS"))
                        pdf_etq_bytes = generar_etiquetas_limpias(
                            reg_datos=datos_fol, total_etqs=int(n_total_cajas),
                            factura_val=f"CEE-{int(datos_fol['FOLIO'])}", transporte_val=transporte_etq
                        )
                        st.download_button(
                            label=":material/save: DESCARGAR ETIQUETA PDF", data=pdf_etq_bytes,
                            file_name=f"Etiqueta_CEE-{int(datos_fol['FOLIO'])}.pdf", mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.button(":material/save: DESCARGAR ETIQUETA PDF", use_container_width=True, disabled=True)

                if btn_guardar and datos_fol is not None:
                    idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                    df_actual.at[idx, "PAQUETERIA_NOMBRE"] = n_paq_nombre
                    df_actual.at[idx, "MODALIDAD_PAGO"] = n_tipo_pago
                    df_actual.at[idx, "NUMERO_GUIA"] = n_gui
                    df_actual.at[idx, "COSTO_GUIA"] = n_costo_guia
                    df_actual.at[idx, "CAJAS"] = n_total_cajas
                    df_actual.at[idx, "UNIDAD"] = n_unidad
                    df_actual.at[idx, "ESTATUS"] = "DESPACHADO"
                    if subir_a_github(df_actual, sha_actual, f"Logistica Folio CEE-{fol_edit}"):
                        st.success(f"FOLIO CEE-{fol_edit} GUARDADO")
                        time.sleep(1.5)
                        st.rerun()

                if btn_imprimir and datos_fol is not None:
                    paq_a_imprimir = n_paq_nombre if n_paq_nombre else datos_fol.get("PAQUETERIA_NOMBRE", "S/P")
                    pago_a_imprimir = n_tipo_pago if n_tipo_pago else datos_fol.get("MODALIDAD_PAGO", "PENDIENTE")
                    h_re = generar_html_impresion(
                        f"CEE-{int(datos_fol['FOLIO'])}",
                        datos_fol.get("PAQUETERIA", "ENVIO"),
                        datos_fol.get("TIPO_ENTREGA", "DOMICILIO"),
                        datos_fol["FECHA"], "RIGOBERTO HERNANDEZ", "3319753122",
                        datos_fol["SOLICITO"], datos_fol["NOMBRE DEL HOTEL"],
                        "", "", "", datos_fol["DESTINO"], "", datos_fol["CONTACTO"],
                        n_total_cajas, n_unidad,
                        datos_fol.get("COMENTARIOS", "RE-IMPRESIÓN DE LOGÍSTICA"),
                        paq_a_imprimir, pago_a_imprimir, total_cajas=n_total_cajas
                    )
                    components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)
            else:
                st.info("No hay registros todavía.")

        # ============================================================
        # T2: HISTORIAL Y REPORTES (tarjetas scroll + reporte imprimible + excel)
        # ============================================================
        with t2:
            if not df_actual.empty:
                st.write("")
                df_actual['FECHA'] = df_actual['FECHA'].astype(str).str.strip()
                df_actual['FECHA_DT'] = pd.to_datetime(df_actual['FECHA'], format='%Y-%m-%d', errors='coerce')
                df_actual['FECHA_DT'] = df_actual['FECHA_DT'].fillna(pd.to_datetime(df_actual['FECHA'], dayfirst=True, errors='coerce'))
                df_actual['MES_FILTRO'] = df_actual['FECHA_DT'].dt.strftime('%m - %Y').fillna("SIN FECHA")

                meses_lista = sorted([m for m in df_actual['MES_FILTRO'].unique() if m != "SIN FECHA"], reverse=True)
                if "SIN FECHA" in df_actual['MES_FILTRO'].values:
                    meses_lista.append("SIN FECHA")

                col_f1, col_f2 = st.columns([1.5, 2.5])
                mes_sel = col_f1.selectbox(":material/calendar_month: FILTRAR PERIODO", ["MOSTRAR TODO"] + meses_lista)

                df_render = df_actual[df_actual['MES_FILTRO'] == mes_sel].copy() if mes_sel != "MOSTRAR TODO" else df_actual.copy()
                df_render = df_render.fillna(0).sort_values(by="FOLIO", ascending=False)

                t_flete = pd.to_numeric(df_render["COSTO_GUIA"], errors="coerce").fillna(0).sum()
                filas_html = ""
                tarjetas_html = ""

                for _, r in df_render.iterrows():
                    estatus_bd = str(r.get('ESTATUS', 'NO SURTIDO')).upper()
                    if estatus_bd == "DESPACHADO":
                        badge_html = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:2px 8px; border-radius:12px; font-size:9px; font-weight:800; letter-spacing:1px; margin-top:5px;'>✓ DESPACHADO</div>"
                    else:
                        badge_html = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:2px 8px; border-radius:12px; font-size:9px; font-weight:800; letter-spacing:1px; margin-top:5px; box-shadow: 0 0 8px rgba(255,68,68,0.4);'>⚠️ NO SURTIDO</div>"

                    detalle_envio = f"{int(pd.to_numeric(r.get('CAJAS', 0), errors='coerce') or 0)} {str(r.get('UNIDAD', '')).upper()}"

                    filas_html += f"""
                    <tr style="page-break-inside: avoid;">
                        <td style='border:1px solid black; padding:6px; text-align:center; font-size:10px; width:8%;'>CEE-{r['FOLIO']}</td>
                        <td style='border:1px solid black; padding:6px; font-size:10px; width:18%;'><b style='color:black;'>{str(r['SOLICITO']).upper()}</b><br><small style='font-size:8px; color:#444;'>{r['FECHA']}</small></td>
                        <td style='border:1px solid black; padding:6px; font-size:10px; width:30%;'><b>{str(r['NOMBRE DEL HOTEL']).upper()}</b><br><small style='font-size:8px; color:#333;'>{str(r['DESTINO']).upper()}</small></td>
                        <td style='border:1px solid black; padding:6px; font-size:10px; width:20%;'>{detalle_envio}</td>
                        <td style='border:1px solid black; padding:6px; text-align:right; font-size:10px; width:14%; white-space:nowrap;'>${float(r['COSTO_GUIA']):,.2f}</td>
                    </tr>"""

                    tarjetas_html += f"""
                    <div class="card-reporte" style="padding: 20px 30px; margin-bottom: 15px;">
                        <div class="col-folio" style="flex: 1;">
                            <div class="label-mini">FOLIO</div>
                            <div class="val-folio" style="margin-bottom: 5px;">CEE-{r['FOLIO']}</div>
                            <div class="val-sub">{r['FECHA']}</div>
                            {badge_html}
                        </div>
                        <div class="col-info" style="flex: 2.5; padding: 0 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div class="label-mini">SOLICITANTE / DESTINO</div>
                            <div class="val-main" style="margin-bottom: 4px;">{str(r['SOLICITO']).upper()}</div>
                            <div class="val-sub">{str(r['NOMBRE DEL HOTEL']).upper()}</div>
                            <div class="val-sub" style="opacity: 0.7;">{str(r['DESTINO']).upper()}</div>
                        </div>
                        <div class="col-detalle" style="flex: 2.0; padding: 0 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div class="label-mini">ENVÍO</div>
                            <div class="val-list">{detalle_envio}</div>
                        </div>
                        <div class="col-costos" style="flex: 1.5; text-align: right; padding-left: 25px; border-left: 1px solid rgba(255,255,255,0.08);">
                            <div class="label-mini">FLETE</div>
                            <div class="val-flete" style="font-size: 14px;">${float(r['COSTO_GUIA']):,.2f}</div>
                        </div>
                    </div>"""

                st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <p style='color:#00FFAA; font-weight:800; letter-spacing:2px; font-size:14px; margin:0;'>VISTA: {mes_sel}</p>
                        <p style='color:#FFFFFF; font-size:12px; opacity:0.6;'>Mostrando {len(df_render)} registros</p>
                    </div>
                """, unsafe_allow_html=True)

                html_final = f"""
                <div style="font-family: 'Inter', sans-serif;">
                    <style>
                        body {{ background: transparent; margin: 0; padding: 0; }}
                        .container-reporte {{ height: 500px; overflow-y: auto; padding-right: 10px; }}
                        .card-reporte {{ background: #263238; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; display: flex; min-width: 800px; justify-content: space-between; align-items: center; transition: 0.3s; }}
                        .card-reporte:hover {{ border-color: #38bdf8; background: #2d3b42; }}
                        .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px; }}
                        .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }}
                        .val-main {{ color: #FFFFFF; font-size: 12px; font-weight: 700; }}
                        .val-sub {{ color: rgba(255,255,255,0.5); font-size: 10px; }}
                        .val-list {{ color: #FFFFFF; font-size: 12px; line-height: 1.4; opacity: 0.9; }}
                        .val-flete {{ color: #a855f7; font-size: 13px; font-weight: 700; font-family: monospace; }}
                        ::-webkit-scrollbar {{ width: 8px; }}
                        ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                        ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; }}
                    </style>
                    <div class="container-reporte">{tarjetas_html}</div>
                </div>"""
                components.html(html_final, height=520, scrolling=False)

                st.markdown(f"""
                    <div style="background:#263238; border-top: 4px solid #00FFAA; border-radius: 0 0 12px 12px; padding: 15px 25px; display: flex; justify-content: flex-end; align-items: center; margin-bottom: 25px;">
                        <div style="color:#00FFAA; font-size:16px; font-weight:800; letter-spacing:1px;">TOTAL FLETES FILTRADO: ${t_flete:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                with c1:
                    form_pt_html = f"<html><head><style>@media print{{@page{{size:letter landscape;margin:1cm;}} body{{margin:0;padding:0;width:100% !important;font-family:sans-serif;}} .no-print{{display:none;}}}} table{{width:100% !important;border-collapse:collapse;margin-top:15px;table-layout:fixed;}} th{{background:#eee !important;border:1px solid black;padding:8px;font-size:11px;-webkit-print-color-adjust:exact;}} td{{border:1px solid black;padding:6px;font-size:10px;vertical-align:top;word-wrap:break-word;}}</style></head><body><div style='display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px solid black;padding-bottom:10px;'><div><h1 style='margin:0;font-size:18px;font-weight:900;'>Jabones y Productos Especializados</h1><p style='margin:0;font-size:10px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;'>distribucion y Logistica 2026</p></div><div style='text-align:right;'><h2 style='margin:0;font-size:16px;text-decoration:underline;'>Reporte de Envíos Especiales</h2><p style='margin:5px 0 0 0;font-size:12px;'><b>GENERADO: {date.today().strftime('%d/%m/%Y')}</b></p></div></div><table><thead><tr><th style='width:8%;'>FOLIO</th><th style='width:18%;'>SOLICITANTE</th><th style='width:30%;'>DESTINO / HOTEL</th><th style='width:20%;'>ENVÍO</th><th style='width:14%;'>FLETE</th></tr></thead><tbody>{filas_html}</tbody></table><div style='text-align:right;margin-top:20px;border-top:2px solid black;padding-top:10px;font-family:monospace;'><h3 style='margin:8px 0;font-size:20px;'>TOTAL FLETES: ${t_flete:,.2f}</h3></div></body></html>"
                    if st.button(":material/print: IMPRIMIR REPORTE", type="primary", use_container_width=True, key="btn_imprimir_reporte_cee"):
                        components.html(f"{form_pt_html}<script>window.print();</script>", height=0)
                with c2:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_render.drop(columns=['FECHA_DT', 'MES_FILTRO']).to_excel(writer, index=False)
                    st.download_button(f":material/download: EXCEL {mes_sel}", data=output.getvalue(), file_name=f"JYPESA_CEE_{mes_sel}.xlsx", use_container_width=True, key="btn_download_excel_cee")
                with c3:
                    if st.button(":material/update: ACTUALIZAR", use_container_width=True, key="btn_actualizar_cee"):
                        st.rerun()
            else:
                st.info("No hay registros todavía.")

        # ============================================================
        # T3: EDICIÓN TOTAL (editar campos + eliminar)
        # ============================================================
        with t3:
            st.markdown("### EDICIÓN TOTAL DE MATRIZ DE ENVÍOS ESPECIALES")
            st.info("Modifica cualquier registro de la base de datos de manera directa. Los cambios se sincronizarán y actualizarán en GitHub al guardar.")

            if df_actual.empty:
                st.warning("No hay registros en la matriz de envíos especiales para editar.")
            else:
                df_sorted_edit = df_actual.sort_values(by="FOLIO", ascending=False)
                opciones_edit = [f"Folio #{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']} ({r['FECHA']})" for _, r in df_sorted_edit.iterrows()]

                folio_a_editar = st.selectbox(
                    "Selecciona el Folio que deseas modificar o eliminar:",
                    opciones_edit, index=None, placeholder="Escribe el folio o nombre del hotel...",
                    key="select_folio_edicion_cee"
                )

                if folio_a_editar:
                    num_folio_sel = int(folio_a_editar.split(" - ")[0].replace("Folio #", ""))
                    idx_fila = df_actual.index[df_actual["FOLIO"] == num_folio_sel].tolist()[0]
                    registro_sel = df_actual.loc[idx_fila]

                    st.markdown("---")
                    st.subheader(f"Editando: CEE-{num_folio_sel}")

                    col_e1, col_e2, col_e3 = st.columns(3)
                    with col_e1:
                        nuevo_hotel = st.text_input("Nombre del Hotel", value=str(registro_sel.get("NOMBRE DEL HOTEL", "")), key=f"hotel_cee_{num_folio_sel}").upper()
                        nuevo_solicito = st.text_input("Solicitante", value=str(registro_sel.get("SOLICITO", "")), key=f"solicito_cee_{num_folio_sel}").upper()
                        nuevo_estatus = st.selectbox(
                            "Estatus", ["NO SURTIDO", "DESPACHADO"],
                            index=0 if str(registro_sel.get("ESTATUS", "NO SURTIDO")) == "NO SURTIDO" else 1,
                            key=f"estatus_cee_{num_folio_sel}"
                        )
                    with col_e2:
                        nuevo_destino = st.text_area("Destino / Dirección", value=str(registro_sel.get("DESTINO", "")), key=f"destino_cee_{num_folio_sel}").upper()
                        nuevo_contacto = st.text_input("Contacto Receptor", value=str(registro_sel.get("CONTACTO", "")), key=f"contacto_cee_{num_folio_sel}").upper()
                    with col_e3:
                        nueva_paqueteria = st.text_input("Paquetería", value=str(registro_sel.get("PAQUETERIA_NOMBRE", registro_sel.get("PAQUETERIA", ""))), key=f"paqueteria_cee_{num_folio_sel}").upper()
                        nueva_guia = st.text_input("Número de Guía", value=str(registro_sel.get("NUMERO_GUIA", "")), key=f"guia_cee_{num_folio_sel}").upper()
                        nuevo_costo_guia = st.number_input("Costo Guía / Flete ($)", min_value=0.0, value=float(registro_sel.get("COSTO_GUIA", 0.0) or 0.0), key=f"costo_cee_{num_folio_sel}")

                    st.markdown("##### 📦 Detalle del Envío")
                    col_e4, col_e5 = st.columns(2)
                    with col_e4:
                        nuevas_cajas = st.number_input("Cantidad (Cajas/Bultos)", min_value=1, step=1, value=int(pd.to_numeric(registro_sel.get("CAJAS", 1), errors="coerce") or 1), key=f"cajas_edit_cee_{num_folio_sel}")
                    with col_e5:
                        opciones_unidad_edit = ["CAJA", "PALLET", "BULTO", "SACO", "BIDON", "ATADO", "OTRO"]
                        unidad_actual = str(registro_sel.get("UNIDAD", "CAJA")).upper()
                        nueva_unidad = st.selectbox("Unidad de Medida", opciones_unidad_edit, index=opciones_unidad_edit.index(unidad_actual) if unidad_actual in opciones_unidad_edit else 0, key=f"unidad_edit_cee_{num_folio_sel}")

                    nuevo_comentario = st.text_area("Comentarios Adicionales", value=str(registro_sel.get("COMENTARIOS", "")), key=f"comentarios_cee_{num_folio_sel}").upper()

                    st.markdown("---")
                    col_btn_1, col_btn_2 = st.columns([2, 1])
                    with col_btn_1:
                        guardar_cambios = st.button("GUARDAR CAMBIOS EN ESTE FOLIO", key=f"guardar_cambios_cee_{num_folio_sel}", use_container_width=True)
                    with col_btn_2:
                        eliminar_registro = st.button("ELIMINAR ESTE FOLIO", key=f"eliminar_registro_cee_{num_folio_sel}", use_container_width=True)

                    if guardar_cambios:
                        df_actual.at[idx_fila, "NOMBRE DEL HOTEL"] = nuevo_hotel
                        df_actual.at[idx_fila, "SOLICITO"] = nuevo_solicito
                        df_actual.at[idx_fila, "ESTATUS"] = nuevo_estatus
                        df_actual.at[idx_fila, "DESTINO"] = nuevo_destino
                        df_actual.at[idx_fila, "CONTACTO"] = nuevo_contacto
                        df_actual.at[idx_fila, "PAQUETERIA_NOMBRE"] = nueva_paqueteria
                        df_actual.at[idx_fila, "NUMERO_GUIA"] = nueva_guia
                        df_actual.at[idx_fila, "COSTO_GUIA"] = nuevo_costo_guia
                        df_actual.at[idx_fila, "CAJAS"] = nuevas_cajas
                        df_actual.at[idx_fila, "UNIDAD"] = nueva_unidad
                        df_actual.at[idx_fila, "COMENTARIOS"] = nuevo_comentario

                        if subir_a_github(df_actual, sha_actual, f"Edicion total Folio CEE-{num_folio_sel}"):
                            st.success(f"¡Folio CEE-{num_folio_sel} actualizado y sincronizado correctamente!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error al sincronizar con GitHub. Verifica tus credenciales.")

                    if eliminar_registro:
                        df_actual = df_actual.drop(idx_fila).reset_index(drop=True)
                        if subir_a_github(df_actual, sha_actual, f"Eliminacion Folio CEE-{num_folio_sel}"):
                            st.success(f"¡El folio CEE-{num_folio_sel} ha sido eliminado permanentemente!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error al eliminar el registro en GitHub.")
    else:
        vars_css = {"card": "#263238", "border": "rgba(255,255,255,0.05)", "text": "#FFFFFF"}
        html_restringido = f"""<div style="background-color:{vars_css['card']}; border:1px solid {vars_css['border']}; border-left:8px solid #F7C300; padding:18px 40px; border-radius:10px; margin:15px 0; box-shadow:0 6px 20px rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:space-between;"><div style="display:flex; align-items:center; gap:25px;"><span style="font-size:28px;">🔐</span><div style="text-align:left;"><span style="color:#F7C300; font-weight:900; font-size:14px; letter-spacing:3px; text-transform:uppercase; display:block; margin-bottom:4px;">ÁREA RESTRINGIDA</span><span style="color:{vars_css['text']}; font-size:14px; font-weight:500; opacity:0.9;">El perfil de operador <b>{usuario_logeado}</b> no cuenta con privilegios de nivel <b>Logística</b>.</span></div></div><div style="padding:6px 16px; border:1px solid rgba(247,195,0,0.5); background:rgba(247,195,0,0.1); border-radius:6px; font-size:11px; color:#F7C300; font-weight:900; letter-spacing:1px;">ID ACCESO: {st.session_state.get('usuario_activo', 'ERR')}</div></div>"""
        st.markdown(html_restringido, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
