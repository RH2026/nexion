import streamlit as st
import pandas as pd
from datetime import date
from datetime import datetime
import pytz 
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Control de Calidad")

# --- LÓGICA DE ESTADO (SESSION STATE) ---
if 'df_productos_calidad' not in st.session_state:
    # CORRECCIÓN 1: FECHA como None y Cantidad como int para evitar el error de tipos
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

# --- INICIALIZACIÓN DE DATOS FIJOS Y DE SESIÓN ---
tz_gdl = pytz.timezone('America/Mexico_City')
now_gdl = datetime.now(tz_gdl)
folio_auto = now_gdl.strftime('%m%d%H%M')

# --- ESTILOS CSS PARA LA CAPTURA ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet" />
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
        .stTextInput label, .stDateInput label, .stNumberInput label {
            color: #94a3b8 !important; font-size: 0.8rem !important;
            text-transform: uppercase !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE RENDERIZADO HTML PARA IMPRESIÓN OFICIAL ---
def generar_formato_impresion(datos_encabezado, filas_productos, datos_dictamen):
    tabla_productos_html = ""
    # Filtrar solo filas que tengan algún dato para no imprimir basura
    filas_reales = [f for f in filas_productos if f['No de factura'] or f['Descripcion']]
    
    for i in range(10): # Siempre generamos 10 espacios en el papel
        if i < len(filas_reales):
            prod = filas_reales[i]
            f_str = prod['FECHA'].strftime('%d/%m/%Y') if prod['FECHA'] else ""
            tabla_productos_html += f"""
            <tr style="height: 25px;">
                <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{f_str}</td>
                <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['No de factura']}</td>
                <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['No de parte']}</td>
                <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['No de fabricacion']}</td>
                <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['Lote']}</td>
                <td style="border:1px solid black; padding: 0 4px; font-size:10px; text-align:center;">{prod['Cantidad']}</td>
                <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['Descripcion']}</td>
            </tr>"""
        else:
            tabla_productos_html += '<tr style="height: 25px;"><td style="border:1px solid black;" colspan="7"></td></tr>'

    return f"""
    <html>
    <head>
        <style>
            @media print {{ @page {{ size: landscape; margin: 10mm; }} header, footer {{ display: none !important; }} }}
            body {{ font-family: Arial, sans-serif; background: white; color: black; font-size: 11px; }}
            table {{ width: 100%; border-collapse: collapse; border: 2px solid black; margin-bottom: -1px; }}
            th, td {{ border: 1px solid black; padding: 4px; text-align: left; }}
            .fixed-data {{ font-weight: bold; background-color: #f2f2f2; width: 15%; }}
            .input-data {{ color: blue; font-weight: bold; font-style: italic; }}
            .signature-line {{ border-top: 2px solid black; margin-top: 40px; text-align: center; width: 80%; margin: 40px auto 0 auto; }}
        </style>
    </head>
    <body>
        <table>
            <tr>
                <td rowspan="2" style="width:10%; text-align:center;"><b>JYPESA</b></td>
                <td colspan="4" style="text-align:center; background-color:#eee;">
                    <h4 style="margin:0;">Formato de control de rehabilitación, reproceso y retrabajo de producto</h4>
                </td>
            </tr>
            <tr>
                <td class="fixed-data">Clave:</td><td>F03-PNO-AC-21</td>
                <td class="fixed-data">Versión:</td><td>3</td>
            </tr>
            <tr>
                <td class="fixed-data">Solicita Calidad:</td><td colspan="2" class="input-data">{datos_encabezado['Solicita_Calidad']}</td>
                <td class="fixed-data">No de desviación:</td><td class="input-data">{datos_encabezado['No_Desviacion']}</td>
            </tr>
            <tr>
                <td class="fixed-data">No de retrabajo:</td><td class="input-data">{datos_encabezado['No_Retrabajo']}</td>
                <td class="fixed-data">No de reclamo:</td><td colspan="2" class="input-data">{datos_encabezado['No_Reclamo']}</td>
            </tr>
            <tr>
                <td class="fixed-data">Fecha de publicación:</td><td>14-Ene-25</td>
                <td class="fixed-data">No de cliente:</td><td colspan="2" class="input-data">{datos_encabezado['No_Cliente']}</td>
            </tr>
            <tr>
                <td class="fixed-data">Nombre comercial:</td><td class="input-data">{datos_encabezado['Nombre_Comercial']}</td>
                <td class="fixed-data">Transporte:</td><td class="input-data">{datos_encabezado['Transporte']}</td>
                <td class="fixed-data">Guía:</td><td class="input-data">{datos_encabezado['Guia']}</td>
            </tr>
            <tr>
                <td class="fixed-data">Costo:</td><td colspan="4" class="input-data">{datos_encabezado['Costo']}</td>
            </tr>
        </table>
        <table>
            <tr style="background-color:#ddd; text-align:center; font-weight:bold; font-size:9px;">
                <td>FECHA</td><td>No FACTURA</td><td>No PARTE</td><td>No FABRICACIÓN</td><td>LOTE</td><td>CANT.</td><td>DESCRIPCIÓN</td>
            </tr>
            {tabla_productos_html}
        </table>
        <table>
            <tr><td class="fixed-data">Comentarios:</td><td colspan="3" class="input-data" style="height:50px;">{datos_dictamen['Comentarios']}</td></tr>
            <tr><td class="fixed-data">Acciones:</td><td class="input-data">{datos_dictamen['Acciones']}</td>
                <td class="fixed-data">DICTAMEN:</td><td class="input-data" style="text-align:center;">{datos_dictamen['Dictamen']}</td>
            </tr>
        </table>
        <div style="display: flex; justify-content: space-around; margin-top: 30px;">
            <div style="width:30%;"><div class="signature-line"></div><b>Analista Incoming</b></div>
            <div style="width:30%;"><div class="signature-line"></div><b>Supervisor Calidad</b></div>
            <div style="width:30%;"><div class="signature-line"></div><b>Supervisor Producción</b></div>
        </div>
    </body>
    </html>
    """

# --- CAPTURA DE DATOS ---
st.markdown('<div class="seccion-captura"><span class="material-symbols-rounded">engineering</span> CAPTURA DE DATOS - FORMULARIO AMARILLO</div>', unsafe_allow_html=True)

with st.container(border=True):
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    solicita_calidad = col_e1.text_input("SOLICITA CALIDAD", key="sol_cal_inp").upper()
    no_desviacion = col_e2.text_input("No. DE DESVIACIÓN", key="no_desv_inp").upper()
    no_retrabajo = col_e3.text_input("No. DE RETRABAJO", key="no_ret_inp").upper()
    no_reclamo = col_e4.text_input("No. DE RECLAMO", key="no_rec_inp").upper()

    col_e5, col_e6 = st.columns([1.5, 2.5])
    no_cliente = col_e5.text_input("No. DE CLIENTE", key="no_cli_inp").upper()
    comentarios_orden = col_e6.text_input("Comentarios de la orden", key="com_ord_inp").upper()

    col_e7, col_e8, col_e9, col_e10 = st.columns(4)
    nombre_comercial = col_e7.text_input("NOMBRE COMERCIAL", key="nom_com_inp").upper()
    transporte = col_e8.selectbox("TRANSPORTE", ["DHL", "FEDEX", "UPS", "JYPESA PROPIO", "OTRO"], key="transp_sel")
    guia = col_e9.text_input("GUÍA / TRACKING", key="guia_inp").upper()
    costo = col_e10.text_input("COSTO USD", key="costo_inp").upper()

st.divider()
st.markdown('<div class="seccion-captura"><span class="material-symbols-rounded">grid_view</span> CAPTURA DE PRODUCTOS (TABLA)</div>', unsafe_allow_html=True)

df_productos_edit = st.data_editor(
    st.session_state.df_productos_calidad,
    num_rows="dynamic",
    use_container_width=True,
    key=f"editor_calidad_{st.session_state.reset_counter_calidad}",
    column_config={
        "FECHA": st.column_config.DateColumn("FECHA", format="DD/MM/YYYY"),
        "No de factura": st.column_config.TextColumn("FACTURA"),
        "No de parte": st.column_config.TextColumn("No DE PARTE"),
        "No de fabricacion": st.column_config.TextColumn("No DE FABRICACIÓN"),
        "Lote": st.column_config.TextColumn("LOTE"),
        "Cantidad": st.column_config.NumberColumn("CANTIDAD", min_value=1),
        "Descripcion": st.column_config.TextColumn("DESCRIPCIÓN DEL PRODUCTO")
    }
)

st.divider()
st.markdown('<div class="seccion-captura"><span class="material-symbols-rounded">fact_check</span> DICTAMEN Y COMENTARIOS FINALES</div>', unsafe_allow_html=True)

with st.container(border=True):
    col_f1, col_f2 = st.columns([2, 1])
    acciones_realizar = col_f1.text_input("ACCIONES A REALIZAR", key="acc_real_inp").upper()
    comentarios_dictamen = col_f1.text_area("HALLAZGOS / COMENTARIOS", height=100, key="com_dict_inp").upper()
    dictamen_final = col_f2.radio("Dictamen FINAL", ["ACEPTADO", "RECHAZADO"], key="dictamen_radio")

st.divider()
enviar_col, imprimir_col = st.columns(2)

if imprimir_col.button(":material/print: GENERAR E IMPRIMIR REPORTE OFICIAL", use_container_width=True, type="primary"):
    # RECOPILACIÓN DE DATOS PARA LA FUNCIÓN
    encabezado = {
        "Solicita_Calidad": solicita_calidad, "No_Desviacion": no_desviacion,
        "No_Retrabajo": no_retrabajo, "No_Reclamo": no_reclamo,
        "No_Cliente": no_cliente, "Nombre_Comercial": nombre_comercial,
        "Transporte": transporte, "Guia": guia, "Costo": costo
    }
    dictamen = {
        "Comentarios": comentarios_dictamen, 
        "Acciones": acciones_realizar, 
        "Dictamen": dictamen_final
    }
    
    # GENERACIÓN E INYECCIÓN
    html_oficial = generar_formato_impresion(encabezado, df_productos_edit.to_dict('records'), dictamen)
    components.html(f"<html><body>{html_oficial}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)

if enviar_col.button(":material/delete_sweep: LIMPIAR TODO", use_container_width=True):
    st.session_state.df_productos_calidad = pd.DataFrame([{"FECHA": None, "No de factura": "", "No de parte": "", "No de fabricacion": "", "Lote": "", "Cantidad": 1, "Descripcion": ""}] * 10)
    st.session_state.reset_counter_calidad += 1
    st.rerun()


























































































