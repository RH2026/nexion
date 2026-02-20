import streamlit as st
import pandas as pd
import requests
import base64
from io import BytesIO
from datetime import date, datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
# Cambiado a "wide" para ocupar toda la pantalla
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

# --- CARGA DE DATOS ---
df_actual, sha_actual = obtener_datos_github()
for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA"]:
    if col not in df_actual.columns and not df_actual.empty:
        df_actual[col] = ""

nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .titulo-label { font-size: 24px; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    .section-header { background: #444; color: white; padding: 5px; text-align: center; font-weight: bold; margin-bottom: 10px; border-radius: 3px; }
    /* Ajuste para que los botones de acción se vean mejor */
    .stButton > button { height: 3em; }
    </style>
""", unsafe_allow_html=True)

# --- ENCABEZADO ---
st.markdown("<h1 style='color: #1E1E1E; margin-bottom:0;'>JYPESA</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-weight: bold; color: gray;'>CAPTURA DE MUESTRAS NEXIÓN</p>", unsafe_allow_html=True)

# --- DATOS GENERALES ---
c1, c2, c3, c4 = st.columns([1, 1.2, 1.2, 1])
f_folio = c1.text_input("FOLIO", value=str(nuevo_folio), disabled=True)
f_paqueteria = c2.selectbox("FORMA DE ENVÍO", ["Envio Pagado", "Envio por cobrar", "Entrega Personal"])
f_entrega = c3.selectbox("TIPO DE ENTREGA", ["Domicilio", "Ocurre Oficina"])
f_fecha = c4.date_input("FECHA", date.today())

st.markdown("---")

# --- BLOQUE REMITENTE Y DESTINATARIO ---
col_rem, col_dest = st.columns(2)
with col_rem:
    st.markdown('<div style="background:black;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:3px;">REMITENTE</div>', unsafe_allow_html=True)
    st.text_input("Nombre", "Jabones y Productos Especializados", disabled=True)
    st.text_input("Calle y Número", "C. Cernícalo 155", disabled=True)
    cr1, cr2 = st.columns(2)
    cr1.text_input("Colonia", "La Aurora", disabled=True)
    cr2.text_input("C.P.", "44460", disabled=True)
    f_atencion_rem = st.text_input("Atención", "Rigoberto Hernandez")
    f_solicitante = st.text_input("Solicitante / Agente", "JYPESA")

with col_dest:
    st.markdown('<div style="background:#b30000;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:3px;">DESTINATARIO / HOTEL</div>', unsafe_allow_html=True)
    f_hotel = st.text_input("Hotel / Nombre", key="hotel_dest")
    f_calle = st.text_input("Calle y Número", key="calle_dest")
    cd1, cd2 = st.columns(2)
    f_colonia = cd1.text_input("Colonia", key="col_dest")
    f_cp = cd2.text_input("Código Postal", key="cp_dest")
    cd3, cd4 = st.columns(2)
    f_ciudad = cd3.text_input("Ciudad", key="ciu_dest")
    f_estado = cd4.text_input("Estado", key="est_dest")
    f_contacto = st.text_input("Contacto Receptor", key="cont_dest")

st.markdown("---")

# --- SELECCIÓN DE PRODUCTOS ---
st.subheader("🛒 Selección de Productos")
seleccionados = st.multiselect("Busca y selecciona los productos:", list(precios.keys()))

productos_para_imprimir = []
cantidades_input = {}

if seleccionados:
    st.info("Escribe las cantidades:")
    cols_q = st.columns(4) # Un poco más ancho para aprovechar el wide
    for i, p in enumerate(seleccionados):
        with cols_q[i % 4]:
            cant = st.number_input(f"{p}", min_value=0, step=1, key=f"q_{p}")
            cantidades_input[p] = cant
            if cant > 0:
                productos_para_imprimir.append({"desc": p, "cant": cant, "cod": "-", "um": "PZAS"})

f_comentarios = st.text_area("💬 COMENTARIOS ADICIONALES", height=70)

# --- BOTONES DE ACCIÓN PRINCIPAL (Guardar e Imprimir juntos) ---
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns(2)

# Generación del HTML de impresión para el botón
filas_html = "".join([f"<tr><td style='padding: 8px; border: 1px solid black;'>{d['desc']}</td><td style='text-align:center; border: 1px solid black;'>{d['cod']}</td><td style='text-align:center; border: 1px solid black;'>{d['um']}</td><td style='text-align:center; border: 1px solid black;'>{d['cant']}</td></tr>" for d in productos_para_imprimir])

html_impresion = f"""
<div id="printable-area" style="font-family:Arial; border:2px solid black; padding:15px; width:700px; min-height:950px; margin:auto; position:relative; box-sizing:border-box; background: white; color: black;">
    <style>
        @media print {{
            @page {{ size: letter; margin: 0; }}
            body {{ margin: 0; padding: 0; }}
            #printable-area {{ border: 2px solid black !important; width: 100% !important; height: 99vh !important; margin: 0 !important; padding: 20px !important; }}
        }}
    </style>
    <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px;">
        <h1 style="margin: 0; font-size: 28px; letter-spacing: 1px;">JYPESA</h1>
        <h2 style="margin: 0; font-size: 16px; text-decoration: underline;">ORDEN DE ENVÍO MUESTRAS</h2>
    </div>
    <table style="width:100%; border-collapse:collapse; margin-bottom:5px; font-size: 11px;">
        <tr><td style="border:1px solid black;padding:4px"><b>FOLIO:</b> {nuevo_folio}</td>
            <td style="border:1px solid black;padding:4px"><b>ENVÍO:</b> {f_paqueteria}</td>
            <td style="border:1px solid black;padding:4px"><b>ENTREGA:</b> {f_entrega}</td>
            <td style="border:1px solid black;padding:4px"><b>FECHA:</b> {f_fecha}</td></tr>
    </table>
    <div style="display:flex; gap:5px; margin-top:5px;">
        <div style="flex:1; border:1px solid black;">
            <div style="background:black; color:white; text-align:center; font-weight:bold; font-size:11px;">REMITENTE</div>
            <div style="padding:4px; font-size:10px;">
                <b>Jabones y Productos Especializados</b><br>C. Cernícalo 155, La Aurora C.P.: 44460<br>ATN: {f_atencion_rem}<br>SOLICITÓ: {f_solicitante}
            </div>
        </div>
        <div style="flex:1; border:1px solid black;">
            <div style="background:#b30000; color:white; text-align:center; font-weight:bold; font-size:11px;">DESTINATARIO</div>
            <div style="padding:4px; font-size:10px;">
                <b>{f_hotel}</b><br>{f_calle}<br>Col: {f_colonia} C.P.: {f_cp}<br>{f_ciudad}, {f_estado}<br>ATN: {f_contacto}
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
        {filas_html if filas_html else '<tr><td colspan="4" style="text-align:center; padding: 20px;">Sin productos seleccionados</td></tr>'}
    </table>
    <div style="border:1px solid black; padding:8px; margin-top:10px; font-size:11px; min-height: 50px;">
        <b>COMENTARIOS:</b><br>{f_comentarios}
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

# Botón de Guardar
if col_btn1.button("🚀 GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
    if not f_hotel:
        st.error("⚠️ Ingresa el nombre del hotel.")
    elif not productos_para_imprimir:
        st.error("⚠️ Selecciona al menos un producto con cantidad mayor a 0.")
    else:
        registro_completo = {
            "FOLIO": nuevo_folio, 
            "FECHA": f_fecha.strftime("%Y-%m-%d"),
            "NOMBRE DEL HOTEL": f_hotel, 
            "DESTINO": f"{f_ciudad}, {f_estado}",
            "CONTACTO": f_contacto, 
            "SOLICITO": f_solicitante, 
            "PAQUETERIA": f_paqueteria,
            "PAQUETERIA_NOMBRE": "", 
            "NUMERO_GUIA": "", 
            "COSTO_GUIA": 0
        }
        total_piezas = sum(cantidades_input.values())
        total_costo = sum(cantidades_input[p] * precios[p] for p in cantidades_input)
        registro_completo["CANTIDAD"] = total_piezas
        registro_completo["COSTO"] = total_costo
        for producto in precios.keys():
            registro_completo[producto] = cantidades_input.get(producto, 0)
        df_final = pd.concat([df_actual, pd.DataFrame([registro_completo])], ignore_index=True)
        if subir_a_github(df_final, sha_actual, f"Folio {nuevo_folio}"):
            st.success(f"✅ ¡Folio {nuevo_folio} guardado correctamente!")
            time.sleep(1.5)
            st.rerun()

# Botón de Imprimir (A la mano del usuario)
if col_btn2.button("🖨️ IMPRIMIR ORDEN (FOLIO ACTUAL)", use_container_width=True):
    components.html(f"<html><body>{html_impresion}<script>window.print();</script></body></html>", height=0)

# --- SECCIÓN DE EDICIÓN Y REPORTES (Abajo para administración) ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("### 🛠 PANEL DE ADMINISTRACIÓN")
tab1, tab2 = st.tabs(["📝 Editar Guías de Envío", "📊 Historial de Muestras"])

with tab1:
    if not df_actual.empty:
        st.write("Selecciona un folio para agregar datos de paquetería:")
        folio_a_editar = st.selectbox("Seleccionar Folio para actualizar:", df_actual["FOLIO"].unique())
        col_g1, col_g2, col_g3 = st.columns(3)
        nombre_paq = col_g1.text_input("Paquetería")
        n_guia = col_g2.text_input("Número de Guía")
        c_guia = col_g3.number_input("Costo Guía ($)", min_value=0.0)
        if st.button("✅ ACTUALIZAR DATOS DE GUÍA"):
            idx = df_actual.index[df_actual['FOLIO'] == folio_a_editar].tolist()[0]
            df_actual.at[idx, "PAQUETERIA_NOMBRE"] = nombre_paq
            df_actual.at[idx, "NUMERO_GUIA"] = n_guia
            df_actual.at[idx, "COSTO_GUIA"] = c_guia
            if subir_a_github(df_actual, sha_actual, f"Guía Folio {folio_a_editar}"):
                st.success("¡Datos actualizados correctamente!"); st.rerun()

with tab2:
    if not df_actual.empty:
        st.dataframe(df_actual, use_container_width=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_actual.to_excel(writer, index=False)
        st.download_button("📥 DESCARGAR MATRIZ COMPLETA (EXCEL)", data=output.getvalue(), file_name="Matriz_Nexión.xlsx", use_container_width=True)
