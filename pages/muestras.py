import streamlit as st
import pandas as pd
import requests
import base64
import time
from io import BytesIO
from datetime import date
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA WIDE ---
st.set_page_config(layout="wide")

# --- VARIABLES DE GITHUB ---
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_PATH = "CEE.csv"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

# --- FUNCIONES GITHUB ---
def obtener_datos_github():
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = r.json()
            df = pd.read_csv(BytesIO(base64.b64decode(content['content'])))
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

# --- FUNCIÓN PARA GENERAR EL HTML DE IMPRESIÓN ---
def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, tel_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, cajas, comentarios, paq_nombre, tipo_pago):
    filas_prod = f"""
    <tr>
        <td style='padding: 8px; border: 1px solid black;'>ENVIO DE CAJAS ESPECIALES</td>
        <td style='text-align:center; border: 1px solid black;'>-</td>
        <td style='text-align:center; border: 1px solid black;'>CAJAS</td>
        <td style='text-align:center; border: 1px solid black;'>{cajas}</td>
    </tr>"""

    html = f"""
    <div id="printable-area" style="font-family:Arial; border:2px solid black; padding:15px; width:700px; min-height:950px; margin:auto; position:relative; box-sizing:border-box; background: white; color: black;">
        <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px;">
            <h1 style="margin: 0; font-size: 28px; letter-spacing: 1px;">JYPESA</h1>
            <div style="text-align:right">
                <h2 style="margin: 0; font-size: 16px; text-decoration: underline;">ORDEN DE ENVÍO COSTOS ESPECIALES</h2>
                <p style="margin:0; font-size:12px;"><b>{paq_nombre} - {tipo_pago}</b></p>
            </div>
        </div>
        <table style="width:100%; border-collapse:collapse; margin-bottom:5px; font-size: 11px;">
            <tr><td style="border:1px solid black;padding:4px"><b>FOLIO:</b> {folio}</td>
                <td style="border:1px solid black;padding:4px"><b>ENVÍO:</b> {str(paq).upper()}</td>
                <td style="border:1px solid black;padding:4px"><b>ENTREGA:</b> {str(entrega).upper()}</td>
                <td style="border:1px solid black;padding:4px"><b>FECHA:</b> {fecha}</td></tr>
        </table>
        <div style="display:flex; gap:5px; margin-top:5px;">
            <div style="flex:1; border:1px solid black;">
                <div style="background:black; color:white; text-align:center; font-weight:bold; font-size:11px;">REMITENTE</div>
                <div style="padding:4px; font-size:10px;">
                    <b>JABONES Y PRODUCTOS ESPECIALIZADOS</b><br>C. Cernícalo 155, La Aurora C.P.: 44460<br>ATN: {str(atn_rem).upper()}<br>TEL: {tel_rem}<br>SOLICITÓ: {str(solicitante).upper()}
                </div>
            </div>
            <div style="flex:1; border:1px solid black;">
                <div style="background:#b30000; color:white; text-align:center; font-weight:bold; font-size:11px;">DESTINATARIO</div>
                <div style="padding:4px; font-size:10px;">
                    <b>{str(hotel).upper()}</b><br>{str(calle).upper()}<br>Col: {str(col).upper()} C.P.: {cp}<br>{str(ciudad).upper()}, {str(estado).upper()}<br>ATN: {str(contacto).upper()}
                </div>
            </div>
        </div>
        <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:11px;">
            <tr style="background:#444; color:white;">
                <th style="padding: 8px; border: 1px solid black;">DESCRIPCIÓN</th>
                <th style="border: 1px solid black;">CÓDIGO</th>
                <th style="border: 1px solid black;">U.M.</th>
                <th style="border: 1px solid black;">CANT.</th>
            </tr>
            {filas_prod}
        </table>
        <div style="border:1px solid black; padding:8px; margin-top:10px; font-size:11px; min-height: 50px;">
            <b>COMENTARIOS:</b><br>{str(comentarios).upper()}
        </div>
        <div style="position:absolute; bottom:30px; left:20px; right:20px;">
            <div style="text-align:center; font-size:11px; font-weight:bold; margin-bottom:25px; border-bottom: 1px solid black; width: 100%; padding-bottom: 5px;">RECIBO DE CONFORMIDAD DEL CLIENTE</div>
            <div style="display:flex; justify-content:space-between; text-align:center; font-size:10px;">
                <div style="width:30%;">__________________________<br>FECHA RECIBO</div>
                <div style="width:35%;">__________________________<br>NOMBRE Y FIRMA</div>
                <div style="width:30%;">__________________________<br>SELLO DE RECIBIDO</div>
            </div>
        </div>
    </div>
    """
    return html

# --- CARGA DE DATOS ---
df_actual, sha_actual = obtener_datos_github()
nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1

# --- INTERFAZ ---
with st.container():
    cp1, cp2 = st.columns(2)
    f_paq_nombre = cp1.selectbox(":material/local_shipping: NOMBRE DE PAQUETERÍA", ["TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES", "FEDEX", "PAQMEX", "TINY PACK"])
    f_tipo_pago = cp2.selectbox(":material/payments: MODALIDAD DE PAGO", ["CREDITO", "COBRO DESTINO"])
    st.write("") 
    c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])
    f_folio = c1.text_input(":material/confirmation_number: FOLIO", value=str(nuevo_folio), disabled=True)
    f_paq_sel = c2.selectbox(":material/local_shipping: FORMA DE ENVÍO", ["Envio Pagado", "Envio por cobrar", "Entrega Personal"])
    f_ent_sel = c3.selectbox(":material/home_pin: TIPO DE ENTREGA", ["Domicilio", "Ocurre Oficina"])
    f_fecha_sel = c4.date_input(":material/calendar_today: FECHA", date.today())

st.divider()

col_rem, col_dest = st.columns(2)
with col_rem:
    # Color cambiado a un Azul oscuro para combinar con NEXION
    st.markdown('<div style="background:#FFFFFF;color:white;text-align:center;font-weight:bold;padding:10px;border-radius:4px;letter-spacing:1px;">REMITENTE</div>', unsafe_allow_html=True)
    st.write("")
    st.text_input(":material/corporate_fare: Nombre", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
    c_rem1, c_rem2 = st.columns([2, 1])
    f_atn_rem = c_rem1.text_input(":material/person: Atención", "RIGOBERTO HERNANDEZ")
    f_tel_rem = c_rem2.text_input(":material/call: Teléfono", "3319753122")
    f_soli = st.text_input(":material/badge: Solicitante / Agente", placeholder="NOMBRE DE QUIEN SOLICITA").upper()

with col_dest:
    # Amarillo mantenido como en tu imagen
    st.markdown('<div style="background:#ffcc4d;color:black;text-align:center;font-weight:bold;padding:10px;border-radius:4px;letter-spacing:1px;">DESTINATARIO / HOTEL</div>', unsafe_allow_html=True)
    st.write("")
    f_h = st.text_input(":material/hotel: Hotel / Nombre").upper()
    f_ca = st.text_input(":material/location_on: Calle y Número").upper()
    cd1, cd2 = st.columns(2)
    f_co = cd1.text_input(":material/map: Colonia").upper()
    f_cp = cd2.text_input(":material/mailbox: C.P.")
    cd3, cd4 = st.columns(2)
    f_ci = cd3.text_input(":material/location_city: Ciudad").upper()
    f_es = cd4.text_input(":material/public: Estado").upper()
    f_con = st.text_input(":material/contact_phone: Contacto Receptor", placeholder="QUIEN RECIBE").upper()

st.divider()
st.subheader(":material/inventory_2: Detalles del Envío")
f_cajas = st.number_input("CANTIDAD DE CAJAS ENVIADAS", min_value=1, step=1)
f_costo_guia = st.number_input("COSTO DE GUÍA ($)", min_value=0.0, step=10.0)
f_coment = st.text_area("💬 COMENTARIOS", height=70).upper()

col_b1, col_b2, col_b3 = st.columns([1, 1, 0.5]) 
if col_b1.button(":material/save: GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
    if not f_h: st.error("Falta el hotel")
    else:
        direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()
        reg = {
            "FOLIO": nuevo_folio, "FECHA": f_fecha_sel.strftime("%Y-%m-%d"), 
            "NOMBRE DEL HOTEL": f_h.upper(), "DESTINO": direccion_completa,
            "CONTACTO": f_con.upper(), "SOLICITO": f_soli.upper() if f_soli else "JYPESA", 
            "PAQUETERIA": f_paq_sel.upper(), "PAQUETERIA_NOMBRE": f_paq_nombre, 
            "NUMERO_GUIA": "", "COSTO_GUIA": f_costo_guia, "CAJAS": f_cajas
        }
        df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
        if subir_a_github(df_f, sha_actual, f"Folio CEE {nuevo_folio}"):
            st.success(f"¡Guardado!"); time.sleep(1); st.rerun()

if col_b2.button(":material/print: IMPRIMIR ESTE FOLIO", use_container_width=True):
    h_print = generar_html_impresion(nuevo_folio, f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem, f_soli if f_soli else "JYPESA", f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, f_cajas, f_coment, f_paq_nombre, f_tipo_pago)
    components.html(f"<html><body>{h_print}<script>window.print();</script></body></html>", height=0)

if col_b3.button(":material/delete_sweep: BORRAR", use_container_width=True):
    st.rerun()

# --- PANEL DE ADMIN ---
st.divider()
st.markdown("### 🛠 PANEL DE ADMINISTRACIÓN")
t1, t2 = st.tabs(["Gestionar Folios", "Historial y Reportes"])

with t1:
    if not df_actual.empty:
        df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
        opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]
        fol_sel_texto = st.selectbox("Seleccionar Folio para Editar:", opciones_folios, index=None)
        fol_edit = ""; datos_fol = None
        if fol_sel_texto:
            fol_edit = int(fol_sel_texto.split(" - ")[0]); datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]

        c_adm1, c_adm2 = st.columns(2)
        with c_adm1:
            st.markdown(f'<div style="background:#5c7aff;color:white;padding:10px;border-radius:5px;">Actualizar Folio {fol_edit}</div>', unsafe_allow_html=True)
            n_gui = st.text_input("Número de Guía", value=str(datos_fol["NUMERO_GUIA"]) if datos_fol is not None else "").upper()
            c_gui = st.number_input("Costo Guía", value=float(datos_fol["COSTO_GUIA"]) if datos_fol is not None else 0.0)
            if st.button(":material/update: ACTUALIZAR", use_container_width=True):
                if datos_fol is not None:
                    idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                    df_actual.at[idx, "NUMERO_GUIA"] = n_gui; df_actual.at[idx, "COSTO_GUIA"] = c_gui
                    if subir_a_github(df_actual, sha_actual, f"Edit {fol_edit}"):
                        st.success("¡Listo!"); time.sleep(1); st.rerun()

        with c_adm2:
            st.markdown('<div style="background:#f6c23e;color:black;padding:10px;border-radius:5px;">Re-impresión</div>', unsafe_allow_html=True)
            if st.button(":material/print: RE-IMPRIMIR", use_container_width=True):
                if datos_fol is not None:
                    h_re = generar_html_impresion(fol_edit, datos_fol["PAQUETERIA"], "Domicilio", datos_fol["FECHA"], "RIGOBERTO HERNANDEZ", "3319753122", datos_fol["SOLICITO"], datos_fol["NOMBRE DEL HOTEL"], "-", "-", "-", datos_fol["DESTINO"], "", datos_fol["CONTACTO"], datos_fol["CAJAS"], "RE-IMPRESIÓN", datos_fol["PAQUETERIA_NOMBRE"], "S/P")
                    components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)

with t2:
    if not df_actual.empty:
        st.dataframe(df_actual, use_container_width=True)
        t_flete = df_actual["COSTO_GUIA"].sum()
        filas_html = ""
        for _, r in df_actual.iterrows():
            filas_html += f"<tr><td style='border:1px solid black;padding:8px;'>{r['FOLIO']}</td><td style='border:1px solid black;padding:8px;'><b>{str(r['SOLICITO']).upper()}</b><br><small>{r['FECHA']}</small></td><td style='border:1px solid black;padding:8px;'>{str(r['NOMBRE DEL HOTEL']).upper()}<br><small>{str(r['DESTINO']).upper()}</small></td><td style='border:1px solid black;padding:8px;'>ENVIO ESPECIAL: {int(r['CAJAS'])} CAJAS</td><td style='border:1px solid black;padding:8px;text-align:right;'>${r['COSTO_GUIA']:,.2f}</td></tr>"

        form_pt_html = f"""
        <html><head><style>body{{font-family:sans-serif;}} table{{width:100%;border-collapse:collapse;margin-top:15px;font-size:11px;}} th{{background:#eee;border:1px solid black;padding:8px;}}</style></head>
        <body>
            <div style="display:flex;justify-content:space-between;border-bottom:2px solid black;padding-bottom:10px;">
                <div><h2>JYPESA</h2><p style="margin:0;font-size:10px;">REPORTE DE COSTOS ESPECIALES</p></div>
                <div style="text-align:right;">GENERADO: {date.today()}</div>
            </div>
            <table><thead><tr><th>FOLIO</th><th>SOLICITANTE</th><th>DESTINO</th><th>DETALLE</th><th>FLETE</th></tr></thead>
            <tbody>{filas_html}</tbody></table>
            <div style="text-align:right;margin-top:20px;border-top:1px solid black;">
                <h3>TOTAL INVERSIÓN FLETES: ${t_flete:,.2f}</h3>
            </div>
        </body></html>"""

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(":material/print: IMPRIMIR REPORTE GENERAL", type="primary", use_container_width=True):
                components.html(f"<html><body>{form_pt_html}<script>window.print();</script></body></html>", height=0)
        with c2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_actual.to_excel(writer, index=False)
            st.download_button(":material/download: DESCARGAR EXCEL", data=output.getvalue(), file_name=f"Matriz_CEE_{date.today()}.xlsx", use_container_width=True)
        with c3:
            if st.button(":material/update: REFRESCAR DATOS", use_container_width=True): st.rerun()




























































