import streamlit as st
import pandas as pd
import requests
import base64
from io import BytesIO
from datetime import date, datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JYPESA Nexión Control", layout="wide")

# --- VARIABLES DE GITHUB ---
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_PATH = "muestras.csv"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

# Diccionario de precios SINCRONIZADO con tu nueva matriz
precios = {
    "SPF": 0.0,
    "Accesorios Ecologicos": 47.85,
    "Accesorios Lavarino": 47.85,
    "Dispensador Almond": 218.33,
    "Dispensador Biogena": 216.00,
    "Dispensador Cava": 230.58,
    "Dispensador Persea": 275.00,  # Corregido con 'e' según tu matriz
    "Dispensador Botánicos": 274.17,
    "Dispensador Dove": 125.00,
    "Kit Elements": 29.34,
    "Kit Almond": 33.83,
    "Kit Biogena": 48.95,
    "Kit Cava": 34.59,
    "Kit Persa": 58.02,
    "Kit Lavarino": 36.30,
    "Kit Botánicos": 29.34,
    "Llave Magnetica": 180.00,
    "Rack Dove": 0.00,
    "Rack JH  Color Blanco de 2 pzas": 62.00, # Doble espacio para match exacto
    "Rack JH  Color Blanco de 1 pzas": 50.00, # Doble espacio para match exacto
    "Soporte dob INOX Cap lock": 679.00,
    "Soporte Ind INOX Cap lock": 608.00
}

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
def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, tel_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, productos, comentarios):
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
    <div id="printable-area" style="font-family:Arial; border:2px solid black; padding:15px; width:700px; min-height:950px; margin:auto; position:relative; box-sizing:border-box; background: white; color: black;">
        <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px;">
            <h1 style="margin: 0; font-size: 28px; letter-spacing: 1px;">JYPESA</h1>
            <h2 style="margin: 0; font-size: 16px; text-decoration: underline;">ORDEN DE ENVÍO MUESTRAS</h2>
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
                <th style="padding: 8px; border: 1px solid black;">DESCRIPCIÓN DEL PRODUCTO</th>
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
if not df_actual.empty:
    for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL"]:
        if col not in df_actual.columns: df_actual[col] = 0.0

nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1

# --- INTERFAZ ---
st.markdown("<h2 style='color: #1E1E1E; margin-bottom:0;'>JYPESA</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:12px; color: gray; margin-top:0;'>AUTOMATIZACIÓN DE PROCESOS</p>", unsafe_allow_html=True)

# --- CAPTURA NUEVA ---
with st.container():
    c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])
    f_folio = c1.text_input("FOLIO", value=str(nuevo_folio), disabled=True)
    f_paq_sel = c2.selectbox("FORMA DE ENVÍO", ["Envio Pagado", "Envio por cobrar", "Entrega Personal"])
    f_ent_sel = c3.selectbox("TIPO DE ENTREGA", ["Domicilio", "Ocurre Oficina"])
    f_fecha_sel = c4.date_input("FECHA", date.today())

st.divider()

col_rem, col_dest = st.columns(2)
with col_rem:
    st.markdown('<div style="background:black;color:white;text-align:center;font-weight:bold;padding:5px;">REMITENTE</div>', unsafe_allow_html=True)
    st.text_input("Nombre", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)
    c_rem1, c_rem2 = st.columns([2, 1])
    f_atn_rem = c_rem1.text_input("Atención", "RIGOBERTO HERNANDEZ")
    f_tel_rem = c_rem2.text_input("Teléfono", "3319753122")
    f_soli = st.text_input("Solicitante / Agente", placeholder="NOMBRE DE QUIEN SOLICITA LAS MUESTRAS")

with col_dest:
    st.markdown('<div style="background:#b30000;color:white;text-align:center;font-weight:bold;padding:5px;">DESTINATARIO / HOTEL</div>', unsafe_allow_html=True)
    f_h = st.text_input("Hotel / Nombre")
    f_ca = st.text_input("Calle y Número")
    cd1, cd2 = st.columns(2)
    f_co = cd1.text_input("Colonia")
    f_cp = cd2.text_input("C.P.")
    cd3, cd4 = st.columns(2)
    f_ci = cd3.text_input("Ciudad")
    f_es = cd4.text_input("Estado")
    f_con = st.text_input("Contacto Receptor")

st.divider()

# --- PRODUCTOS ---
st.subheader("🛒 Selección de Productos")
seleccionados = st.multiselect("Busca y selecciona productos:", list(precios.keys()))
prods_actuales = []
cants_dict = {p: 0 for p in precios.keys()}
total_cantidad = 0
total_costo_prods = 0

if seleccionados:
    cols_q = st.columns(4)
    for i, p in enumerate(seleccionados):
        with cols_q[i % 4]:
            q = st.number_input(f"{p}", min_value=0, step=1, key=f"q_{p}")
            cants_dict[p] = q
            if q > 0:
                prods_actuales.append({"desc": p, "cant": q})
                total_cantidad += q
                total_costo_prods += (q * precios[p])

f_coment = st.text_area("💬 COMENTARIOS", height=70)

# --- BOTONES PRINCIPALES ---
col_b1, col_b2 = st.columns(2)
if col_b1.button("🚀 GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
    if not f_h: st.error("Falta el hotel")
    elif not prods_actuales: st.error("Selecciona al menos un producto")
    else:
        direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()
        reg = {
            "FOLIO": nuevo_folio, "FECHA": f_fecha_sel.strftime("%Y-%m-%d"), 
            "NOMBRE DEL HOTEL": f_h.upper(), "DESTINO": direccion_completa,
            "CONTACTO": f_con.upper(), "SOLICITO": f_soli.upper() if f_soli else "JYPESA", "PAQUETERIA": f_paq_sel.upper(),
            "PAQUETERIA_NOMBRE": "", "NUMERO_GUIA": "", "COSTO_GUIA": 0.0,
            "CANTIDAD_TOTAL": total_cantidad,
            "COSTO_TOTAL": round(total_costo_prods, 2)
        }
        for p, cant in cants_dict.items(): reg[p] = cant
        df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
        if subir_a_github(df_f, sha_actual, f"Folio {nuevo_folio}"):
            st.success(f"¡Guardado! Costo: ${total_costo_prods}"); time.sleep(1); st.rerun()

if col_b2.button("🖨️ IMPRIMIR ESTE FOLIO", use_container_width=True):
    if not prods_actuales: st.warning("No hay productos")
    else:
        h_print = generar_html_impresion(nuevo_folio, f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem, f_soli if f_soli else "JYPESA", f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, prods_actuales, f_coment)
        components.html(f"<html><body>{h_print}<script>window.print();</script></body></html>", height=0)

# --- NUEVA OPCIÓN DE BÚSQUEDA RÁPIDA (JUSTO DESPUÉS DE GUARDAR/IMPRIMIR) ---
st.write("")
with st.expander("🔍 BÚSQUEDA RÁPIDA DE GUÍAS (CONSULTA DE FOLIOS)", expanded=False):
    if not df_actual.empty:
        busqueda = st.text_input("Escribe el nombre del Hotel o Folio para filtrar:")
        # Columnas solicitadas: Folio, Fecha, Hotel, Guía (y agregué Paquetería para contexto)
        df_vista = df_actual[["FOLIO", "FECHA", "NOMBRE DEL HOTEL", "PAQUETERIA_NOMBRE", "NUMERO_GUIA"]].copy()
        df_vista.columns = ["FOLIO", "FECHA ENVÍO", "HOTEL", "PAQUETERÍA", "NÚMERO DE GUÍA"]
        
        if busqueda:
            df_vista = df_vista[df_vista.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        
        st.dataframe(df_vista.sort_values(by="FOLIO", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros todavía.")

# --- PANEL DE ADMIN ---
st.divider()
st.markdown("### 🛠 PANEL DE ADMINISTRACIÓN")
t1, t2 = st.tabs(["📝 Gestionar Folios Existentes", "📊 Historial y Reportes"])

with t1:
    if not df_actual.empty:
        df_sorted = df_actual.sort_values(by="FOLIO", ascending=False)
        opciones_folios = [f"{int(r['FOLIO'])} - {r['NOMBRE DEL HOTEL']}" for _, r in df_sorted.iterrows()]
        
        fol_sel_texto = st.selectbox("Seleccionar Folio para Editar:", opciones_folios)
        fol_edit = int(fol_sel_texto.split(" - ")[0])
        
        datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]
        c_adm1, c_adm2 = st.columns(2)
        with c_adm1:
            st.markdown(f'<div style="background:#4e73df;color:white;padding:10px;border-radius:5px;">Actualizar envío - Folio {fol_edit}</div>', unsafe_allow_html=True)
            n_paq = st.text_input("Empresa de Paquetería", value=str(datos_fol["PAQUETERIA_NOMBRE"]))
            n_gui = st.text_input("Número de Guía", value=str(datos_fol["NUMERO_GUIA"]))
            c_gui = st.number_input("Costo de Guía ($)", value=float(datos_fol["COSTO_GUIA"]))
            if st.button("✅ ACTUALIZAR DATOS DE ENVÍO", use_container_width=True):
                idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                df_actual.at[idx, "PAQUETERIA_NOMBRE"] = n_paq.upper()
                df_actual.at[idx, "NUMERO_GUIA"] = n_gui.upper()
                df_actual.at[idx, "COSTO_GUIA"] = c_gui
                if subir_a_github(df_actual, sha_actual, f"Guía {fol_edit}"):
                    st.success("¡Datos actualizados!"); time.sleep(1); st.rerun()
        with c_adm2:
            st.markdown('<div style="background:#f6c23e;color:black;padding:10px;border-radius:5px;">Re-impresión de Documento</div>', unsafe_allow_html=True)
            st.write("")
            if st.button("🖨️ RE-GENERAR FORMATO E IMPRIMIR", use_container_width=True):
                prods_re = []
                for p in precios.keys():
                    if p in datos_fol and datos_fol[p] > 0: prods_re.append({"desc": p, "cant": int(datos_fol[p])})
                h_re = generar_html_impresion(fol_edit, datos_fol["PAQUETERIA"], "Domicilio", datos_fol["FECHA"], "RIGOBERTO HERNANDEZ", "3319753122", datos_fol["SOLICITO"], datos_fol["NOMBRE DEL HOTEL"], "-", "-", "-", datos_fol["DESTINO"], "", datos_fol["CONTACTO"], prods_re, "RE-IMPRESIÓN")
                components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)

with t2:
    if not df_actual.empty:
        st.dataframe(df_actual, use_container_width=True)
        t_prod = df_actual["COSTO_TOTAL"].sum()
        t_flete = df_actual["COSTO_GUIA"].sum()
        filas_html = ""
        for _, r in df_actual.iterrows():
            detalle_p = ""
            for p in precios.keys():
                cant = r.get(p, 0)
                if cant > 0: detalle_p += f"• {int(cant)} PZAS {str(p).upper()}<br>"
            filas_html += f"<tr><td style='border:1px solid black;padding:8px;'>{r['FOLIO']}</td><td style='border:1px solid black;padding:8px;'><b>{str(r['SOLICITO']).upper()}</b><br><small>{r['FECHA']}</small></td><td style='border:1px solid black;padding:8px;'>{str(r['NOMBRE DEL HOTEL']).upper()}<br><small>{str(r['DESTINO']).upper()}</small></td><td style='border:1px solid black;padding:8px;font-size:10px;'>{detalle_p}</td><td style='border:1px solid black;padding:8px;text-align:right;'>${r['COSTO_TOTAL']:,.2f}</td><td style='border:1px solid black;padding:8px;text-align:right;'>${r['COSTO_GUIA']:,.2f}</td></tr>"

        form_pt_html = f"""
        <html><head><style>@media print{{body{{padding:15mm;}} .no-print{{display:none;}}}} body{{font-family:sans-serif;}} table{{width:100%;border-collapse:collapse;margin-top:15px;font-size:11px;}} th{{background:#eee;border:1px solid black;padding:8px;}}</style></head>
        <body>
            <div style="display:flex;justify-content:space-between;border-bottom:2px solid black;padding-bottom:10px;">
                <div><h2>JYPESA</h2><p style="margin:0;font-size:10px;">AUTOMATIZACIÓN DE PROCESOS</p></div>
                <div style="text-align:right;"><b>REPORTE DE SALIDA PT</b><br>GENERADO: {date.today()}</div>
            </div>
            <table><thead><tr><th>FOLIO</th><th>SOLICITANTE</th><th>DESTINO</th><th>DETALLE</th><th>COSTO PROD.</th><th>FLETE</th></tr></thead>
            <tbody>{filas_html}</tbody></table>
            <div style="text-align:right;margin-top:20px;border-top:1px solid black;">
                <p>TOTAL PRODUCTOS: ${t_prod:,.2f}</p><p>TOTAL FLETES: ${t_flete:,.2f}</p><h3>INVERSIÓN TOTAL: ${(t_prod+t_flete):,.2f}</h3>
            </div>
        </body></html>"""

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🖨️ IMPRIMIR REPORTE PT", type="primary", use_container_width=True):
                components.html(f"<html><body>{form_pt_html}<script>window.print();</script></body></html>", height=0)
        with c2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_actual.to_excel(writer, index=False)
            st.download_button("📥 DESCARGAR EXCEL", data=output.getvalue(), file_name=f"Matriz_{date.today()}.xlsx", use_container_width=True)
        with c3:
            if st.button("🔄 ACTUALIZAR DATOS", use_container_width=True): st.rerun()
