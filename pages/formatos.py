import streamlit as st
import pandas as pd
from datetime import date, datetime
import pytz 
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Calidad Oficial")

# --- 1. LÓGICA DE ESTADO (SESSION STATE) ---
if 'df_productos_calidad' not in st.session_state:
    # CORRECCIÓN VITAL: Inicializamos FECHA con None y Cantidad con 1 (entero)
    # Esto evita el error de "Type Compatibility" que bloqueaba tu app
    st.session_state.df_productos_calidad = pd.DataFrame(
        [{
            "FECHA": None, 
            "No de factura": "", 
            "No de parte": "", 
            "No de fabricacion": "", 
            "Lote": "", 
            "Cantidad": 1, 
            "Descripcion": ""
        }] * 10
    )

if 'reset_counter_calidad' not in st.session_state:
    st.session_state.reset_counter_calidad = 0

# --- 2. INICIALIZACIÓN DE DATOS Y ESTILOS ---
tz_gdl = pytz.timezone('America/Mexico_City')
now_gdl = datetime.now(tz_gdl)

st.markdown("""
    <style>
        .stApp { background-color: #1a2432; }
        .seccion-captura {
            display: flex; align-items: center; font-size: 1.1rem;
            color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;
            margin-bottom: 20px;
        }
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input {
            border-bottom: 2px solid #f6c23e !important;
            border-radius: 0px !important; color: white !important;
            font-weight: 600 !important; background-color: transparent !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCIÓN DE RENDERIZADO (RÉPLICA EXACTA DEL EXCEL) ---
def generar_formato_impresion(enc, filas, dictamen):
    # Generamos las 10 filas de la tabla de productos
    tabla_productos_html = ""
    for i in range(10):
        if i < len(filas) and (filas[i]['No de factura'] or filas[i]['Descripcion']):
            f = filas[i]
            f_fecha = f['FECHA'].strftime('%d-%b-%y') if f['FECHA'] else ""
            tabla_productos_html += f"""
            <tr style="height: 25px;">
                <td>{f_fecha}</td><td>{f['No de factura']}</td><td>{f['No de parte']}</td>
                <td>{f['No de fabricacion']}</td><td>{f['Lote']}</td>
                <td style="text-align:center;">{f['Cantidad']}</td><td>{f['Descripcion']}</td>
            </tr>"""
        else:
            tabla_productos_html += '<tr style="height: 25px;"><td colspan="7"></td></tr>'

    return f"""
    <html>
    <head>
        <style>
            @media print {{ @page {{ size: landscape; margin: 10mm; }} }}
            body {{ font-family: Arial; font-size: 10px; color: black; }}
            table {{ width: 100%; border-collapse: collapse; border: 2px solid black; margin-bottom: -1px; }}
            td, th {{ border: 1px solid black; padding: 4px; }}
            .header-gray {{ background: #D9D9D9; font-weight: bold; text-align: center; }}
            .input-val {{ color: blue; font-weight: bold; font-style: italic; }}
        </style>
    </head>
    <body>
        <table>
            <tr>
                <td rowspan="2" style="width:15%; text-align:center;"><b>JYPESA</b></td>
                <td colspan="4" style="text-align:center; background:#eee;"><b>Formato de control de rehabilitación, reproceso y retrabajo de producto</b></td>
            </tr>
            <tr class="header-gray">
                <td>Clave: F03-PNO-AC-21</td><td>Versión: 3</td>
                <td>Publicación: 14-Ene-25</td><td>Sustituye a: F03-PNO-AC-21 V02</td>
            </tr>
            <tr class="header-gray">
                <td>Solicita Calidad</td><td>No de desviación</td><td>No de retrabajo</td><td>No de reclamo</td><td>No de cliente</td>
            </tr>
            <tr class="input-val" style="text-align:center; height:25px;">
                <td>{enc['sol']}</td><td>{enc['des']}</td><td>{enc['ret']}</td><td>{enc['rec']}</td><td>{enc['cli']}</td>
            </tr>
            <tr class="header-gray">
                <td colspan="2">Nombre comercial</td><td>Transporte</td><td>Guía</td><td>Costo</td>
            </tr>
            <tr class="input-val" style="text-align:center; height:25px;">
                <td colspan="2">{enc['nom']}</td><td>{enc['tra']}</td><td>{enc['gui']}</td><td>{enc['cos']}</td>
            </tr>
        </table>
        <table style="margin-top:-1px;">
            <tr class="header-gray">
                <td style="width:10%;">Fecha</td><td style="width:12%;">Factura</td><td style="width:12%;">No Parte</td>
                <td style="width:12%;">Fabricación</td><td style="width:10%;">Lote</td><td style="width:10%;">Cantidad</td><td>Descripción</td>
            </tr>
            {tabla_productos_html}
        </table>
        <table>
            <tr><td class="header-gray" style="width:20%;">Comentarios (Hallazgo):</td><td class="input-val" style="height:50px;">{dictamen['com']}</td></tr>
            <tr><td class="header-gray">Acciones a realizar:</td><td class="input-val">{dictamen['acc']}</td></tr>
            <tr class="header-gray"><td>DICTAMEN FINAL:</td><td style="font-size:12px;">{dictamen['dic']}</td></tr>
        </table>
        <div style="display:flex; justify-content:space-around; margin-top:50px; text-align:center;">
            <div style="width:30%; border-top:1px solid black;"><b>Analista Incoming</b></div>
            <div style="width:30%; border-top:1px solid black;"><b>Supervisor Calidad</b></div>
            <div style="width:30%; border-top:1px solid black;"><b>Supervisor Producción</b></div>
        </div>
    </body>
    </html>
    """

# --- 4. CAPTURA DE DATOS (INTERFAZ) ---
st.markdown('<div class="seccion-captura">:material/engineering: CAPTURA DE DATOS OFICIAL</div>', unsafe_allow_html=True)

with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    solicita = c1.text_input("SOLICITA CALIDAD").upper()
    desviacion = c2.text_input("No. DE DESVIACIÓN").upper()
    retrabajo = c3.text_input("No. DE RETRABAJO").upper()
    reclamo = c4.text_input("No. DE RECLAMO").upper()

    c5, c6 = st.columns([1, 3])
    cliente = c5.text_input("No. DE CLIENTE").upper()
    com_breve = c6.text_input("COMENTARIOS BREVES DE LA ORDEN").upper()

    c7, c8, c9, c10 = st.columns(4)
    nom_com = c7.text_input("NOMBRE COMERCIAL").upper()
    transp = c8.selectbox("TRANSPORTE", ["FEDEX", "DHL", "UPS", "JYPESA", "OTRO"])
    guia = c9.text_input("GUÍA").upper()
    costo = c10.text_input("COSTO USD").upper()

st.divider()
df_edit = st.data_editor(
    st.session_state.df_productos_calidad,
    num_rows="dynamic", use_container_width=True,
    key=f"editor_calidad_{st.session_state.reset_counter_calidad}",
    column_config={"FECHA": st.column_config.DateColumn("FECHA", format="DD/MM/YYYY")}
)

st.divider()
with st.container(border=True):
    col_f1, col_f2 = st.columns([2, 1])
    acciones = col_f1.text_area("ACCIONES A REALIZAR").upper()
    hallazgo = col_f1.text_area("HALLAZGOS / COMENTARIOS").upper()
    dictamen_final = col_f2.radio("DICTAMEN FINAL", ["ACEPTADO ( )", "RECHAZADO ( )"])

# --- 5. BOTONES ---
c_b1, c_b2 = st.columns(2)
if c_b1.button(":material/print: IMPRIMIR FORMATO REPLICA", type="primary", use_container_width=True):
    enc = {"sol": solicita, "des": desviacion, "ret": retrabajo, "rec": reclamo, "cli": cliente, "nom": nom_com, "tra": transp, "gui": guia, "cos": costo}
    dic = {"com": hallazgo, "acc": acciones, "dic": dictamen_final}
    html = generar_formato_impresion(enc, df_edit.to_dict('records'), dic)
    components.html(f"<html><body>{html}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)

if c_b2.button(":material/delete_sweep: LIMPIAR TODO", use_container_width=True):
    st.session_state.df_productos_calidad = pd.DataFrame([{"FECHA": None, "No de factura": "", "No de parte": "", "No de fabricacion": "", "Lote": "", "Cantidad": 1, "Descripcion": ""}] * 10)
    st.session_state.reset_counter_calidad += 1
    st.rerun()





























































































