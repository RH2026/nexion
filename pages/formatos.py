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
    f_desviacion = c2.text_input("No. DESVIACIÓN").upper()
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
    f_coment_hallazgo = st.text_area("COMENTARIOS (DESCRIPCIÓN BREVE DEL HALLAZGO)").upper()
    f_acciones = st.text_area("ACCIONES A REALIZAR SEGÚN SEA EL CASO").upper()
    f_dictamen = st.radio("DICTAMEN FINAL:", ["ACEPTADO ( )", "RECHAZADO ( )"], horizontal=True)

# --- MOTOR DE IMPRESIÓN (REPLICA EXACTA) ---
def generar_html_exacto():
    # Procesar filas
    filas_html = ""
    for _, r in df_edit.iterrows():
        f_val = r['FECHA'].strftime('%d-%b-%y') if r['FECHA'] else ""
        filas_html += f"""
        <tr style="height:22px;">
            <td style="border:1px solid black;">{f_val}</td>
            <td style="border:1px solid black;">{r['No de factura']}</td>
            <td style="border:1px solid black;">{r['No de parte']}</td>
            <td style="border:1px solid black;">{r['Orden fabricacion']}</td>
            <td style="border:1px solid black;">{r['Lote']}</td>
            <td style="border:1px solid black; text-align:center;">{r['Cantidad']}</td>
            <td style="border:1px solid black;">{r['Descripcion']}</td>
        </tr>"""
    
    # Relleno hasta 10 filas
    for _ in range(max(0, 10 - len(df_edit))):
        filas_html += "<tr style='height:22px;'><td style='border:1px solid black;' colspan='7'></td></tr>"

    html_template = f"""
    <html>
    <head>
        <style>
            @media print {{ @page {{ size: letter landscape; margin: 5mm; }} }}
            body {{ font-family: 'Arial Narrow', Arial; font-size: 10px; color: black; }}
            table {{ width: 100%; border-collapse: collapse; border: 1.5px solid black; table-layout: fixed; }}
            td, th {{ border: 1px solid black; padding: 2px; }}
            .header-gray {{ background-color: #D9D9D9; font-weight: bold; text-align: center; }}
            .input-blue {{ color: blue; font-weight: bold; font-style: italic; }}
            .title {{ font-size: 14px; font-weight: bold; text-align: center; height: 30px; }}
        </style>
    </head>
    <body>
        <table>
            <tr>
                <td colspan="2" style="width:20%; text-align:center;"><b>JYPESA</b></td>
                <td colspan="8" class="title">Formato de control de rehabilitación, reproceso y retrabajo de producto</td>
            </tr>
            <tr class="header-gray">
                <td>Clave:</td><td>Versión:</td><td colspan="2">Fecha de publicación:</td><td colspan="2">Fecha de próxima revisión:</td><td colspan="4">Sustituye a:</td>
            </tr>
            <tr style="text-align:center;">
                <td>F03-PNO-AC-21</td><td>3</td><td colspan="2">14-Ene-25</td><td colspan="2">14-Ene-28</td><td colspan="4">F03-PNO-AC-21 V02</td>
            </tr>
            <tr class="header-gray">
                <td style="width:12%;">Solicita Calidad:</td><td style="width:10%;">No de desviación:</td><td style="width:10%;">No de retrabajo:</td><td style="width:10%;">No de reclamo:</td><td style="width:8%;">No de cliente:</td><td style="width:12%;">Nombre comercial:</td><td style="width:10%;">Transporte:</td><td style="width:10%;">Guía:</td><td colspan="2">Costo:</td>
            </tr>
            <tr class="input-blue" style="text-align:center; height:25px;">
                <td>{f_solicita}</td><td>{f_desviacion}</td><td>{f_retrabajo}</td><td>{f_reclamo}</td><td>{f_cliente}</td><td>{f_nom_com}</td><td>{f_transp}</td><td>{f_guia}</td><td colspan="2">{f_costo}</td>
            </tr>
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray">
                <td style="width:10%;">Fecha</td><td style="width:12%;">No de factura</td><td style="width:12%;">No de parte</td><td style="width:12%;">Orden de fabricación</td><td style="width:8%;">Lote</td><td style="width:8%;">Cantidad</td><td>Descripción del producto</td>
            </tr>
            {filas_html}
        </table>

        <table style="margin-top:-1px;">
            <tr>
                <td class="header-gray" style="width:15%;">Orden de:</td>
                <td style="width:15%;">Retrabajo / Rehab / Reproc</td>
                <td class="header-gray" style="width:70%;">Comentarios (descripción breve del hallazgo)</td>
            </tr>
            <tr>
                <td colspan="2" style="height:40px;"></td>
                <td class="input-blue" valign="top">{f_coment_hallazgo}</td>
            </tr>
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray">
                <td style="width:50%;">Acciones a realizar según sea el caso</td>
                <td style="width:50%;">DICTAMEN FINAL: {f_dictamen}</td>
            </tr>
            <tr>
                <td class="input-blue" style="height:50px;" valign="top">{f_acciones}</td>
                <td style="text-align:center;"><b>ACEPTADO ( ) O RECHAZADO ( )</b></td>
            </tr>
        </table>

        <div style="display:flex; justify-content:space-around; margin-top:50px; text-align:center;">
            <div style="width:30%; border-top:1px solid black;"><b>Analista de incoming</b><br>Firma/fecha</div>
            <div style="width:30%; border-top:1px solid black;"><b>Supervisor de calidad</b><br>Firma/fecha</div>
            <div style="width:30%; border-top:1px solid black;"><b>Supervisor de producción</b><br>Firma/fecha</div>
        </div>
        
        <div style="margin-top:20px; display:flex; justify-content:space-between; font-size:9px;">
            <span>Formato: F02-PNO-SGC-02 Versión 01</span>
            <span>Página 1 de 1</span>
        </div>
    </body>
    </html>
    """
    return html_template

if st.button("IMPRIMIR FORMATO REPLICA", type="primary", use_container_width=True):
    formato = generar_html_exacto()
    components.html(f"<html><body>{formato}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)






























































































