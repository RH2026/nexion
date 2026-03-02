¡Entendido perfectamente, amor! Para que quede idéntico a la imagen oficial de calidad de JYPESA, necesitamos ajustar la estructura de las tablas, añadir las secciones de "Seguimiento a la desviación", los campos de "Gasto" y "Hrs", y sobre todo, habilitar la parte de los checkbox para Retrabajo/Rehabilitación/Reproceso.

Aquí tienes el código con el motor de impresión corregido al 100% para que sea una réplica exacta del formato de Excel:

Python
import streamlit as st
import pandas as pd
from datetime import date, datetime
import pytz 
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="NEXION - Calidad Oficial")

# --- ESTADO DE LA TABLA ---
if 'df_calidad_oficial' not in st.session_state:
    st.session_state.df_calidad_oficial = pd.DataFrame(
        [{"FECHA": None, "No de factura": "", "No de parte": "", "Orden fabricacion": "", "Lote": "", "Cantidad": "", "Descripcion": ""}] * 10
    )

# --- CAPTURA DE DATOS (INPUTS AMARILLOS) ---
st.title("Captura de Formato de Calidad")
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    f_solicita = c1.text_input("SOLICITA CALIDAD").upper()
    f_desviacion = c2.text_input("No. DE DESVIACIÓN").upper()
    f_retrabajo = c3.text_input("No. RETRABAJO").upper()
    f_reclamo = c4.text_input("No. RECLAMO").upper()
    f_cliente = c5.text_input("No. CLIENTE").upper()

    c6, c7, c8, c9 = st.columns([2, 1, 1, 1])
    f_nom_com = c6.text_input("NOMBRE COMERCIAL").upper()
    f_transp = c7.text_input("TRANSPORTE").upper()
    f_guia = c8.text_input("GUÍA").upper()
    f_costo = c9.text_input("COSTO").upper()

st.write("### Detalle de Productos")
df_edit = st.data_editor(st.session_state.df_calidad_oficial, num_rows="dynamic", use_container_width=True,
                         column_config={"FECHA": st.column_config.DateColumn("FECHA", format="DD/MM/YYYY")})

with st.container(border=True):
    cx1, cx2 = st.columns(2)
    f_tipo_orden = cx1.multiselect("TIPO DE ORDEN:", ["Retrabajo", "Rehabilitación", "Reproceso"])
    f_coment_hallazgo = cx2.text_area("COMENTARIOS (DESCRIPCIÓN BREVE DEL HALLAZGO)").upper()
    
    f_acciones = st.text_area("ACCIONES A REALIZAR SEGÚN SEA EL CASO").upper()
    
    ca1, ca2, ca3 = st.columns(3)
    f_mano_obra = ca1.text_input("GASTO: MANO DE OBRA").upper()
    f_hrs = ca2.text_input("HRS").upper()
    f_otros_gastos = ca3.text_input("OTROS / CANTIDAD").upper()
    
    f_dictamen = st.radio("DICTAMEN FINAL:", ["ACEPTADO", "RECHAZADO"], horizontal=True)

# --- MOTOR DE IMPRESIÓN (REPLICA EXACTA) ---
def generar_html_exacto():
    # Procesar filas de la tabla de productos
    filas_html = ""
    for _, r in df_edit.iterrows():
        f_val = r['FECHA'].strftime('%d-%b-%y') if r['FECHA'] else ""
        filas_html += f"""
        <tr style="height:20px;">
            <td>{f_val}</td>
            <td>{r['No de factura']}</td>
            <td>{r['No de parte']}</td>
            <td>{r['Orden fabricacion']}</td>
            <td>{r['Lote']}</td>
            <td style="text-align:center;">{r['Cantidad']}</td>
            <td>{r['Descripcion']}</td>
        </tr>"""
    
    # Relleno para asegurar las filas de la imagen
    for _ in range(max(0, 10 - len(df_edit))):
        filas_html += "<tr style='height:20px;'><td colspan='7'></td></tr>"

    # Lógica de checks para Tipo de Orden
    check_ret = "( x )" if "Retrabajo" in f_tipo_orden else "(   )"
    check_rehab = "( x )" if "Rehabilitación" in f_tipo_orden else "(   )"
    check_repro = "( x )" if "Reproceso" in f_tipo_orden else "(   )"
    
    # Lógica de dictamen
    dic_acep = "( x )" if f_dictamen == "ACEPTADO" else "(   )"
    dic_rech = "( x )" if f_dictamen == "RECHAZADO" else "(   )"

    html_template = f"""
    <html>
    <head>
        <style>
            @media print {{ @page {{ size: letter landscape; margin: 5mm; }} }}
            body {{ font-family: 'Arial Narrow', Arial; font-size: 9px; color: black; }}
            table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
            td {{ border: 1px solid black; padding: 2px; }}
            .header-gray {{ background-color: #D9D9D9; font-weight: bold; text-align: center; font-size: 8px; }}
            .input-blue {{ color: blue; font-weight: bold; font-style: italic; font-size: 10px; }}
            .title {{ font-size: 13px; font-weight: bold; text-align: center; }}
            .no-border {{ border: none; }}
        </style>
    </head>
    <body>
        <table>
            <tr>
                <td colspan="2" style="width:20%; text-align:center;"><b>JYPESA</b></td>
                <td colspan="9" class="title">Formato de control de rehabilitación, reproceso y retrabajo de producto</td>
            </tr>
            <tr class="header-gray">
                <td>Clave:</td><td>Versión:</td><td colspan="2">Fecha de publicación:</td><td colspan="2">Fecha de próxima revisión:</td><td colspan="5">Sustituye a:</td>
            </tr>
            <tr style="text-align:center;">
                <td>F03-PNO-AC-21</td><td>3</td><td colspan="2">14-Ene-25</td><td colspan="2">14-Ene-28</td><td colspan="5">F03-PNO-AC-21 V02</td>
            </tr>
            <tr class="header-gray">
                <td style="width:9%;">Solicita Calidad:</td>
                <td style="width:8%;">No de desviación:</td>
                <td colspan="2">No de retrabajo: / No de reclamo:</td>
                <td style="width:6%;">No de cliente</td>
                <td colspan="2">Nombre comercial</td>
                <td style="width:8%;">Transporte</td>
                <td style="width:8%;">Guía</td>
                <td colspan="2">Costo</td>
            </tr>
            <tr class="input-blue" style="text-align:center; height:22px;">
                <td>{f_solicita}</td>
                <td>{f_desviacion}</td>
                <td>{f_retrabajo}</td><td>{f_reclamo}</td>
                <td>{f_cliente}</td>
                <td colspan="2">{f_nom_com}</td>
                <td>{f_transp}</td>
                <td>{f_guia}</td>
                <td colspan="2">{f_costo}</td>
            </tr>
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray">
                <td style="width:10%;">Fecha</td><td style="width:12%;">No de factura</td><td style="width:12%;">No de parte</td><td style="width:12%;">Orden de fabricación</td><td style="width:8%;">Lote</td><td style="width:8%;">Cantidad</td><td>Descripción del producto</td>
            </tr>
            {filas_html}
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray">
                <td colspan="2" style="width:20%;">Orden de:</td>
                <td style="width:80%;">Comentarios (descripción breve del hallazgo)</td>
            </tr>
            <tr>
                <td style="width:15%;">Retrabajo</td><td style="width:5%; text-align:center;">{check_ret}</td>
                <td rowspan="3" class="input-blue" valign="top">{f_coment_hallazgo}</td>
            </tr>
            <tr><td>Rehabilitación</td><td style="text-align:center;">{check_rehab}</td></tr>
            <tr><td>Reproceso</td><td style="text-align:center;">{check_repro}</td></tr>
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray"><td>Acciones a realizar según sea el caso Retrabajo/Rehabilitación/Reproceso</td></tr>
            <tr><td class="input-val" style="height:45px;" valign="top">{f_acciones}</td></tr>
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray"><td colspan="3">Seguimiento a la desviación</td></tr>
            <tr style="height:20px;">
                <td><b>Analista de inventario MP:</b></td>
                <td><b>Analista de inventario PT:</b></td>
                <td><b>Programador de producción:</b></td>
            </tr>
            <tr class="header-gray">
                <td colspan="3">Dictamen de retrabajo/rehabilitación/reproceso finalizado: Aceptado {dic_acep} o rechazado {dic_rech}</td>
            </tr>
        </table>

        <table style="margin-top:-1px;">
            <tr style="height:20px;">
                <td style="width:33%;">Gasto: mano de obra: <span class="input-blue">{f_mano_obra}</span></td>
                <td style="width:15%;">hrs: <span class="input-blue">{f_hrs}</span></td>
                <td>Otros: <span class="input-blue">{f_otros_gastos}</span></td>
            </tr>
        </table>

        <div style="display:flex; justify-content:space-around; margin-top:40px; text-align:center;">
            <div style="width:30%;">
                <div style="border-top:1px solid black; width:80%; margin:auto;"></div>
                <b>Analista de incoming</b><br>Firma/fecha
            </div>
            <div style="width:30%;">
                <div style="border-top:1px solid black; width:80%; margin:auto;"></div>
                <b>Supervisor de calidad</b><br>Firma/fecha
            </div>
            <div style="width:30%;">
                <div style="border-top:1px solid black; width:80%; margin:auto;"></div>
                <b>Supervisor de producción</b><br>Firma/fecha
            </div>
        </div>

        <div style="margin-top:15px; display:flex; justify-content:space-between; font-size:8px;">
            <span>Formato: F02-PNO-SGC-02 Versión 01</span>
            <span>Página 1 de 1</span>
        </div>
    </body>
    </html>
    """
    return html_template

# BOTÓN DE IMPRESIÓN
if st.button("IMPRIMIR FORMATO REPLICA", type="primary", use_container_width=True):
    formato = generar_html_exacto()
    components.html(f"<html><body>{formato}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)































































































