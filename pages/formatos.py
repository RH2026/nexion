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

# --- CAPTURA DE DATOS (ESTILO ELITE) ---
st.title(":material/rebase_edit: Control de Rehabilitación y Reproceso")
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    f_solicita = c1.text_input("SOLICITA CALIDAD").upper()
    f_desviacion = c2.text_input("No. DE DESVIACIÓN").upper()
    f_retrabajo = c3.text_input("No. RETRABAJO").upper()
    f_reclamo = c4.text_input("No. DE RECLAMO").upper()
    f_cliente = c5.text_input("No. CLIENTE").upper()

    c6, c7, c8, c9 = st.columns([2, 1, 1, 1])
    f_nom_com = c6.text_input("NOMBRE COMERCIAL").upper()
    f_transp = c7.text_input("TRANSPORTE").upper()
    f_guia = c8.text_input("GUÍA").upper()
    f_costo = c9.text_input("COSTO").upper()

st.write("### :material/grid_view: Detalle de Productos")
df_edit = st.data_editor(st.session_state.df_calidad_oficial, num_rows="dynamic", use_container_width=True,
                         column_config={"FECHA": st.column_config.DateColumn("FECHA", format="DD/MM/YYYY")})

with st.container(border=True):
    cx1, cx2 = st.columns(2)
    f_tipo_orden = cx1.multiselect("TIPO DE ORDEN:", ["Retrabajo", "Rehabilitación", "Reproceso"])
    f_coment_hallazgo = cx2.text_area("COMENTARIOS (DESCRIPCIÓN BREVE DEL HALLAZGO)").upper()
    f_acciones = st.text_area("ACCIONES A REALIZAR SEGÚN SEA EL CASO").upper()
    
    st.write("Seguimiento Administrativo:")
    ca_v1, ca_v2, ca_v3 = st.columns(3)
    f_nota_credito = ca_v1.checkbox("Nota de crédito")
    f_producto_nc = ca_v2.checkbox("Producto")
    f_servicio_nc = ca_v3.checkbox("Servicio")

    ca1, ca2, ca3, ca4 = st.columns(4)
    f_mano_obra = ca1.text_input("GASTO: MANO DE OBRA").upper()
    f_hrs = ca2.text_input("HRS").upper()
    f_otros_gastos = ca3.text_input("OTROS").upper()
    f_cant_final = ca4.text_input("CANTIDAD").upper()
    f_dictamen = st.radio("DICTAMEN FINAL:", ["ACEPTADO", "RECHAZADO"], horizontal=True)

# --- MOTOR DE IMPRESIÓN (RÉPLICA EXACTA) ---
def generar_html_exacto():
    filas_html = ""
    for _, r in df_edit.iterrows():
        f_val = r['FECHA'].strftime('%d-%b-%y') if r['FECHA'] else ""
        filas_html += f"""
        <tr style="height:18px;">
            <td>{f_val}</td><td>{r['No de factura']}</td><td>{r['No de parte']}</td>
            <td>{r['Orden fabricacion']}</td><td>{r['Lote']}</td>
            <td style="text-align:center;">{r['Cantidad']}</td><td>{r['Descripcion']}</td>
        </tr>"""
    
    for _ in range(max(0, 10 - len(df_edit))):
        filas_html += "<tr style='height:18px;'><td colspan='7'></td></tr>"

    check_ret = "( x )" if "Retrabajo" in f_tipo_orden else "(   )"
    check_rehab = "( x )" if "Rehabilitación" in f_tipo_orden else "(   )"
    check_repro = "( x )" if "Reproceso" in f_tipo_orden else "(   )"
    c_nc = "( x )" if f_nota_credito else "(   )"
    c_pr = "( x )" if f_producto_nc else "(   )"
    c_se = "( x )" if f_servicio_nc else "(   )"
    dic_acep = "( x )" if f_dictamen == "ACEPTADO" else "(   )"
    dic_rech = "( x )" if f_dictamen == "RECHAZADO" else "(   )"

    html_template = f"""
    <html>
    <head>
        <style>
            @media print {{ @page {{ size: letter landscape; margin: 5mm; }} }}
            body {{ font-family: 'Arial Narrow', Arial; font-size: 8.2px; color: black; }}
            table {{ width: 100%; border-collapse: collapse; table-layout: fixed; border: 1.5px solid black; }}
            td {{ border: 1px solid black; padding: 2px; }}
            .header-gray {{ background-color: #D9D9D9; font-weight: bold; text-align: center; font-size: 7.8px; }}
            .input-blue {{ color: blue; font-weight: bold; font-style: italic; font-size: 9.5px; }}
            .title {{ font-size: 13px; font-weight: bold; text-align: center; height: 28px; }}
        </style>
    </head>
    <body>
        <table>
            <tr>
                <td colspan="2" style="width:18%; text-align:center;"><b>JYPESA</b></td>
                <td colspan="10" class="title">Formato de control de rehabilitación, reproceso y retrabajo de producto</td>
            </tr>
            <tr class="header-gray">
                <td>Clave:</td><td>Versión:</td><td colspan="3">Fecha de publicación:</td><td colspan="3">Fecha de próxima revisión:</td><td colspan="4">Sustituye a:</td>
            </tr>
            <tr style="text-align:center;">
                <td>F03-PNO-AC-21</td><td>3</td><td colspan="3">14-Ene-25</td><td colspan="3">14-Ene-28</td><td colspan="4">F03-PNO-AC-21 V02</td>
            </tr>
            <tr class="header-gray">
                <td>Solicita Calidad:</td><td>No de desviación:</td><td colspan="2">No de retrabajo:</td><td>No de reclamo:</td><td>No de cliente</td><td colspan="2">Nombre comercial</td><td>Transporte</td><td>Guía</td><td colspan="2">Costo</td>
            </tr>
            <tr class="input-blue" style="text-align:center; height:22px;">
                <td>{f_solicita}</td><td>{f_desviacion}</td><td colspan="2">{f_retrabajo}</td><td>{f_reclamo}</td><td>{f_cliente}</td><td colspan="2">{f_nom_com}</td><td>{f_transp}</td><td>{f_guia}</td><td colspan="2">{f_costo}</td>
            </tr>
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray">
                <td style="width:10%;">Fecha</td><td style="width:12%;">No de factura</td><td style="width:12%;">No de parte</td><td style="width:12%;">Orden de fabricación</td><td style="width:8%;">Lote</td><td style="width:8%;">Cantidad</td><td>Descripción del producto</td>
            </tr>
            {filas_html}
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray"><td style="width:25%;">Orden de:</td><td style="width:75%;">Comentarios (descripción breve del hallazgo)</td></tr>
            <tr><td>Retrabajo <span style="float:right;">{check_ret}</span></td><td rowspan="3" class="input-blue" valign="top">{f_coment_hallazgo}</td></tr>
            <tr><td>Rehabilitación <span style="float:right;">{check_rehab}</span></td></tr>
            <tr><td>Reproceso <span style="float:right;">{check_repro}</span></td></tr>
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray"><td>Acciones a realizar según sea el caso Retrabajo/Rehabilitación/Reproceso</td></tr>
            <tr><td class="input-blue" style="height:35px;" valign="top">{f_acciones}</td></tr>
        </table>

        <table style="margin-top:-1px;">
            <tr>
                <td style="width:18%;" class="header-gray">Nota de crédito</td><td style="width:7%; text-align:center;">{c_nc}</td>
                <td rowspan="4" style="width:75%; border:none;"></td> </tr>
            <tr><td class="header-gray">Producto</td><td style="text-align:center;">{c_pr}</td></tr>
            <tr><td class="header-gray">Servicio</td><td style="text-align:center;">{c_se}</td></tr>
            <tr style="height:15px;"><td></td><td></td></tr>
        </table>

        <table style="margin-top:-1px; border-top:none;">
            <tr>
                <td style="height:80px; text-align:center; vertical-align:top; padding-top:10px;">
                    <b>Analista de incoming</b><br><br><br><br>
                    ____________________________________________________________<br>
                    Firma/fecha
                </td>
            </tr>
        </table>

        <table style="margin-top:-1px;">
            <tr class="header-gray"><td colspan="3">Seguimiento a la desviación</td></tr>
            <tr style="height:20px;">
                <td>Analista de inventario MP:</td><td>Analista de inventario PT:</td><td>Programador de producción:</td>
            </tr>
            <tr class="header-gray"><td colspan="3">Dictamen de retrabajo/rehabilitación/reproceso finalizado: Aceptado {dic_acep} o rechazado {dic_rech}</td></tr>
        </table>

        <table style="margin-top:-1px;">
            <tr style="height:20px;">
                <td style="width:30%;">Gasto: mano de obra: <span class="input-blue">{f_mano_obra}</span></td>
                <td style="width:15%;">hrs: <span class="input-blue">{f_hrs}</span></td>
                <td style="width:25%;">Otros: <span class="input-blue">{f_otros_gastos}</span></td>
                <td>Cantidad: <span class="input-blue">{f_cant_final}</span></td>
            </tr>
            <tr><td colspan="4" style="height:30px;"><b>Comentarios:</b></td></tr>
        </table>

        <div style="display:flex; justify-content:space-around; margin-top:40px; text-align:center;">
            <div style="width:40%; border-top:1.5px solid black; padding-top:5px;"><b>Supervisor de calidad</b><br>Firma/fecha</div>
            <div style="width:40%; border-top:1.5px solid black; padding-top:5px;"><b>Supervisor de producción</b><br>Firma/fecha</div>
        </div>

        <div style="margin-top:15px; display:flex; justify-content:space-between; font-size:7.5px;">
            <span>Formato: F02-PNO-SGC-02 Versión 01</span><span>Página 1 de 1</span>
        </div>
    </body>
    </html>
    """
    return html_template

if st.button(":material/print: IMPRIMIR FORMATO REPLICA IDENTICO", type="primary", use_container_width=True):
    formato = generar_html_exacto()
    components.html(f"<html><body>{formato}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)

def generar_excel_identico(encabezado, productos, dictamen):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Formato Calidad")
    
    # --- CONFIGURACIÓN DE FORMATOS ---
    header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D9D9D9', 'font_size': 9})
    title_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 12})
    input_fmt = workbook.add_format({'font_color': 'blue', 'italic': True, 'bold': True, 'align': 'center', 'border': 1, 'font_size': 10})
    normal_fmt = workbook.add_format({'border': 1, 'align': 'left', 'font_size': 9})
    border_fmt = workbook.add_format({'border': 1})

    # Ajuste de columnas para que se vea igual al Excel original
    worksheet.set_column('A:K', 12)

    # --- ENCABEZADO (FILAS 1-5) ---
    worksheet.merge_range('A1:B2', 'JYPESA', title_fmt)
    worksheet.merge_range('C1:L2', 'Formato de control de rehabilitación, reproceso y retrabajo de producto', title_fmt)
    
    worksheet.write('A3', 'Clave:', header_fmt)
    worksheet.write('B3', 'F03-PNO-AC-21', border_fmt)
    worksheet.write('C3', 'Versión:', header_fmt)
    worksheet.write('D3', '3', border_fmt)
    worksheet.merge_range('E3:F3', 'Fecha de publicación:', header_fmt)
    worksheet.merge_range('G3:H3', '14-Ene-25', border_fmt)
    worksheet.merge_range('I3:L3', 'Sustituye a: F03-PNO-AC-21 V02', border_fmt)

    # --- FILA DE INPUTS AMARILLOS (MAPEADO A TU IMAGEN) ---
    worksheet.write('A4', 'Solicita Calidad:', header_fmt)
    worksheet.write('B4', encabezado['sol'], input_fmt)
    worksheet.write('C4', 'No Desviación:', header_fmt)
    worksheet.write('D4', encabezado['des'], input_fmt)
    worksheet.write('E4', 'No Retrabajo:', header_fmt)
    worksheet.write('F4', encabezado['ret'], input_fmt)
    worksheet.write('G4', 'No Cliente:', header_fmt)
    worksheet.write('H4', encabezado['cli'], input_fmt)
    worksheet.merge_range('I4:J4', 'Nombre Comercial:', header_fmt)
    worksheet.merge_range('K4:L4', encabezado['nom'], input_fmt)

    # --- TABLA DE PRODUCTOS ---
    worksheet.merge_range('A6:L6', 'DETALLE DE PRODUCTOS', header_fmt)
    cols = ['FECHA', 'No FACTURA', 'No PARTE', 'FABRICACIÓN', 'LOTE', 'CANTIDAD', 'DESCRIPCIÓN']
    for i, col in enumerate(cols):
        worksheet.write(6, i, col, header_fmt)

    row = 7
    for p in productos:
        if p['No de factura'] or p['Descripcion']:
            f_fecha = p['FECHA'].strftime('%d/%m/%Y') if p['FECHA'] else ""
            worksheet.write(row, 0, f_fecha, normal_fmt)
            worksheet.write(row, 1, p['No de factura'], normal_fmt)
            worksheet.write(row, 2, p['No de parte'], normal_fmt)
            worksheet.write(row, 3, p['Orden fabricacion'], normal_fmt)
            worksheet.write(row, 4, p['Lote'], normal_fmt)
            worksheet.write(row, 5, p['Cantidad'], normal_fmt)
            worksheet.merge_range(row, 6, row, 11, p['Descripcion'], normal_fmt)
            row += 1

    # --- SECCIÓN FINAL: DICTAMEN Y FIRMAS ---
    worksheet.merge_range(row + 1, 0, row + 2, 1, 'DICTAMEN:', header_fmt)
    worksheet.merge_range(row + 1, 2, row + 2, 11, dictamen['dic'], input_fmt)

    workbook.close()
    return output.getvalue()

# --- BOTÓN EN TU INTERFAZ ---
st.divider()
excel_data = generar_excel_identico(
    {"sol": solicita, "des": desviacion, "ret": retrabajo, "cli": cliente, "nom": nom_com},
    df_edit.to_dict('records'),
    {"dic": dictamen_final}
)

st.download_button(
    label=":material/download: DESCARGAR REPLICA EXCEL",
    data=excel_data,
    file_name=f"Calidad_{nom_com}_{datetime.now().strftime('%d%m%Y')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)


































































































