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

# Diccionario de precios (Se mantiene intacto)
precios = {
    "SPF": 0.0,"Accesorios Ecologicos": 47.85, "Accesorios Lavarino": 47.85, "Dispensador Almond ": 218.33,
    "Dispensador Biogena": 216.00, "Dispensador Cava": 230.58, "Dispensador Persa": 275.00,
    "Dispensador Botánicos L": 274.17, "Dispensador Dove": 125.00, "Dispensador Biogena 400ml": 184.87,
    "Kit Elements ": 29.34, "Kit Almond ": 33.83, "Kit Biogena": 48.95, "Kit Cava": 34.59,
    "Kit Persa": 58.02, "Kit Lavarino": 36.30, "Kit Botánicos": 29.34, "Llave Magnetica": 180.00,
    "Rack Dove": 0.00, "Rack JH  Color Blanco de 2 pzas": 62.00, "Rack JH  Color Blanco de 1 pzas": 50.00,
    "Soporte dob  INOX Cap lock": 679.00, "Soporte Ind  INOX Cap lock": 608.00
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
def generar_html_impresion(folio, paq, entrega, fecha, atn_rem, solicitante, hotel, calle, col, cp, ciudad, estado, contacto, productos, comentarios):
    filas_prod = ""
    for p in productos:
        filas_prod += f"""
        <tr>
            <td style='padding: 8px; border: 1px solid black;'>{p['desc']}</td>
            <td style='text-align:center; border: 1px solid black;'>-</td>
            <td style='text-align:center; border: 1px solid black;'>PZAS</td>
            <td style='text-align:center; border: 1px solid black;'>{p['cant']}</td>
        </tr>"""

    html = f"""
    <div id="printable-area" style="font-family:Arial; border:2px solid black; padding:15px; width:700px; min-height:950px; margin:auto; position:relative; box-sizing:border-box; background: white; color: black;">
        <style>
            @media print {{ @page {{ size: letter; margin: 0; }} body {{ margin: 0; padding: 0; }} #printable-area {{ border: 2px solid black !important; width: 100% !important; height: 99vh !important; margin: 0 !important; padding: 20px !important; }} }}
        </style>
        <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px;">
            <h1 style="margin: 0; font-size: 28px; letter-spacing: 1px;">JYPESA</h1>
            <h2 style="margin: 0; font-size: 16px; text-decoration: underline;">ORDEN DE ENVÍO MUESTRAS</h2>
        </div>
        <table style="width:100%; border-collapse:collapse; margin-bottom:5px; font-size: 11px;">
            <tr><td style="border:1px solid black;padding:4px"><b>FOLIO:</b> {folio}</td>
                <td style="border:1px solid black;padding:4px"><b>ENVÍO:</b> {paq}</td>
                <td style="border:1px solid black;padding:4px"><b>ENTREGA:</b> {entrega}</td>
                <td style="border:1px solid black;padding:4px"><b>FECHA:</b> {fecha}</td></tr>
        </table>
        <div style="display:flex; gap:5px; margin-top:5px;">
            <div style="flex:1; border:1px solid black;">
                <div style="background:black; color:white; text-align:center; font-weight:bold; font-size:11px;">REMITENTE</div>
                <div style="padding:4px; font-size:10px;">
                    <b>Jabones y Productos Especializados</b><br>C. Cernícalo 155, La Aurora C.P.: 44460<br>ATN: {atn_rem}<br>SOLICITÓ: {solicitante}
                </div>
            </div>
            <div style="flex:1; border:1px solid black;">
                <div style="background:#b30000; color:white; text-align:center; font-weight:bold; font-size:11px;">DESTINATARIO</div>
                <div style="padding:4px; font-size:10px;">
                    <b>{hotel}</b><br>{calle}<br>Col: {col} C.P.: {cp}<br>{ciudad}, {estado}<br>ATN: {contacto}
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
            <b>COMENTARIOS:</b><br>{comentarios}
        </div>
        <div style="position:absolute; bottom:30px; left:20px; right:20px;">
            <div style="text-align:center; font-size:11px; font-weight:bold; margin-bottom:25px; border-bottom: 1px solid black; width: 100%; padding-bottom: 5px;">RECIBO DE CONFORMIDAD</div>
            <div style="display:flex; justify-content:space-between; text-align:center; font-size:10px;">
                <div style="width:30%;">__________________________<br>FECHA RECIBO</div>
                <div style="width:35%;">__________________________<br>NOMBRE Y FIRMA</div>
                <div style="width:30%;">__________________________<br>SELLO</div>
            </div>
        </div>
    </div>
    """
    return html

# --- CARGA DE DATOS ---
df_actual, sha_actual = obtener_datos_github()
for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA"]:
    if col not in df_actual.columns and not df_actual.empty:
        df_actual[col] = ""

nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1

# --- INTERFAZ ---
st.markdown("<h1 style='color: #1E1E1E; margin-bottom:0;'>JYPESA</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-weight: bold; color: gray;'>CAPTURA DE MUESTRAS NEXIÓN</p>", unsafe_allow_html=True)

# --- CAPTURA NUEVA ---
c1, c2, c3, c4 = st.columns([1, 1.2, 1.2, 1])
f_folio = c1.text_input("FOLIO", value=str(nuevo_folio), disabled=True)
f_paq_sel = c2.selectbox("FORMA DE ENVÍO", ["Envio Pagado", "Envio por cobrar", "Entrega Personal"])
f_ent_sel = c3.selectbox("TIPO DE ENTREGA", ["Domicilio", "Ocurre Oficina"])
f_fecha_sel = c4.date_input("FECHA", date.today())

st.markdown("---")
col_rem, col_dest = st.columns(2)
with col_rem:
    st.markdown('<div style="background:black;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:3px;">REMITENTE</div>', unsafe_allow_html=True)
    st.text_input("Nombre", "Jabones y Productos Especializados", disabled=True)
    f_atn_rem = st.text_input("Atención", "Rigoberto Hernandez")
    f_soli = st.text_input("Solicitante / Agente", "JYPESA")

with col_dest:
    st.markdown('<div style="background:#b30000;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:3px;">DESTINATARIO / HOTEL</div>', unsafe_allow_html=True)
    f_h = st.text_input("Hotel / Nombre")
    f_ca = st.text_input("Calle y Número")
    cd1, cd2 = st.columns(2)
    f_co = cd1.text_input("Colonia")
    f_cp = cd2.text_input("C.P.")
    cd3, cd4 = st.columns(2)
    f_ci = cd3.text_input("Ciudad")
    f_es = cd4.text_input("Estado")
    f_con = st.text_input("Contacto Receptor")

st.markdown("---")
st.subheader("🛒 Selección de Productos")
seleccionados = st.multiselect("Busca y selecciona:", list(precios.keys()))
prods_actuales = []
cants_dict = {}
if seleccionados:
    cols_q = st.columns(4)
    for i, p in enumerate(seleccionados):
        with cols_q[i % 4]:
            q = st.number_input(f"{p}", min_value=0, step=1, key=f"q_{p}")
            cants_dict[p] = q
            if q > 0: prods_actuales.append({"desc": p, "cant": q})

f_coment = st.text_area("💬 COMENTARIOS", height=70)

col_b1, col_b2 = st.columns(2)
if col_b1.button("🚀 GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
    if not f_h: st.error("Falta el hotel")
    elif not prods_actuales: st.error("Faltan productos")
    else:
        # CONCATENACIÓN DE DIRECCIÓN COMPLETA PARA EL EXCEL
        direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}"
        
        reg = {
            "FOLIO": nuevo_folio, 
            "FECHA": f_fecha_sel.strftime("%Y-%m-%d"), 
            "NOMBRE DEL HOTEL": f_h, 
            "DESTINO": direccion_completa, # Dirección concatenada
            "CONTACTO": f_con, 
            "SOLICITO": f_soli, 
            "PAQUETERIA": f_paq_sel,
            "PAQUETERIA_NOMBRE": "",
            "NUMERO_GUIA": "",
            "COSTO_GUIA": 0
        }
        for p in precios.keys(): reg[p] = cants_dict.get(p, 0)
        df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)
        if subir_a_github(df_f, sha_actual, f"Folio {nuevo_folio}"):
            st.success("¡Guardado correctamente en la matriz!"); time.sleep(1.5); st.rerun()

if col_b2.button("🖨️ IMPRIMIR ESTE FOLIO", use_container_width=True):
    h_print = generar_html_impresion(nuevo_folio, f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_soli, f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con, prods_actuales, f_coment)
    components.html(f"<html><body>{h_print}<script>window.print();</script></body></html>", height=0)

# --- PANEL DE ADMIN ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("### 🛠 PANEL DE ADMINISTRACIÓN")
t1, t2 = st.tabs(["📝 Gestionar Folios Existentes", "📊 Historial y Reportes"])

with t1:
    if not df_actual.empty:
        fol_edit = st.selectbox("Seleccionar Folio:", sorted(df_actual["FOLIO"].unique(), reverse=True))
        datos_fol = df_actual[df_actual["FOLIO"] == fol_edit].iloc[0]
        
        c_edit1, c_edit2 = st.columns(2)
        with c_edit1:
            st.info(f"Actualizar envío - Folio {fol_edit}")
            n_paq = st.text_input("Empresa de Paquetería", value=datos_fol["PAQUETERIA_NOMBRE"])
            n_gui = st.text_input("Número de Guía", value=datos_fol["NUMERO_GUIA"])
            c_gui = st.number_input("Costo de Guía ($)", value=float(datos_fol["COSTO_GUIA"]))
            
            if st.button("✅ ACTUALIZAR DATOS DE ENVÍO"):
                idx = df_actual.index[df_actual['FOLIO'] == fol_edit].tolist()[0]
                df_actual.at[idx, "PAQUETERIA_NOMBRE"] = n_paq
                df_actual.at[idx, "NUMERO_GUIA"] = n_gui
                df_actual.at[idx, "COSTO_GUIA"] = c_gui
                if subir_a_github(df_actual, sha_actual, f"Guía Folio {fol_edit}"):
                    st.success("¡Datos actualizados!"); st.rerun()

        with c_edit2:
            st.warning("Re-impresión de Documento")
            if st.button("🖨️ RE-GENERAR FORMATO E IMPRIMIR"):
                prods_re = []
                for p in precios.keys():
                    if datos_fol.get(p, 0) > 0:
                        prods_re.append({"desc": p, "cant": int(datos_fol[p])})
                
                h_re = generar_html_impresion(fol_edit, datos_fol["PAQUETERIA"], "Domicilio", datos_fol["FECHA"], 
                                             "Rigoberto Hernandez", datos_fol["SOLICITO"], datos_fol["NOMBRE DEL HOTEL"],
                                             "-", "-", "-", datos_fol["DESTINO"], "", datos_fol["CONTACTO"], prods_re, "RE-IMPRESIÓN")
                components.html(f"<html><body>{h_re}<script>window.print();</script></body></html>", height=0)

with t2:
    if not df_actual.empty:
        st.write("### Matriz Completa de Muestras")
        st.dataframe(df_actual, use_container_width=True)
        
        # BOTÓN DE DESCARGA EXCEL
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_actual.to_excel(writer, index=False, sheet_name='Matriz_Nexión')
        
        st.download_button(
            label="📥 DESCARGAR MATRIZ COMPLETA (EXCEL)",
            data=output.getvalue(),
            file_name=f"Matriz_Nexión_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
