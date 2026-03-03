import streamlit as st
import pandas as pd
from datetime import date, datetime
import pytz 
import streamlit.components.v1 as components
import io
import xlsxwriter

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Calidad Oficial")

# --- 1. MOTOR DE EXCEL (RÉPLICA EXACTA DEL PDF) ---
def generar_excel_identico(enc, productos, dictamen_val, admin_nc, hallazgo, acciones):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = workbook.add_worksheet("Formato Calidad")
    
    # FORMATOS
    title_f = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 2, 'font_size': 11})
    header_f = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D9D9D9', 'font_size': 8})
    data_blue = workbook.add_format({'font_color': 'blue', 'italic': True, 'bold': True, 'align': 'center', 'border': 1, 'font_size': 9})
    std_f = workbook.add_format({'border': 1, 'font_size': 8, 'align': 'center'})
    firma_f = workbook.add_format({'align': 'center', 'valign': 'top', 'border': 1, 'font_size': 8})

    ws.set_column('A:L', 9)

    # A. ENCABEZADO SUPERIOR
    ws.merge_range('A1:B2', 'JYPESA', title_f)
    ws.merge_range('C1:L2', 'Formato de control de rehabilitación, reproceso y retrabajo de producto', title_f)
    
    ws.write('A3', 'Clave:', header_f)
    ws.write('B3', 'F03-PNO-AC-21', std_f)
    ws.write('C3', 'Versión:', header_f)
    ws.write('D3', '3', std_f)
    ws.merge_range('E3:F3', 'Fecha de publicación:', header_f)
    ws.merge_range('G3:H3', '14-Ene-25', std_f)
    ws.merge_range('I3:L3', 'Sustituye a: F03-PNO-AC-21 V02', std_f)

    # B. DATOS CAPTURA
    ws.write('A4', 'Solicita:', header_f)
    ws.write('B4', enc['sol'], data_blue)
    ws.write('C4', 'Desviación:', header_f)
    ws.write('D4', enc['des'], data_blue)
    ws.write('E4', 'Retrabajo:', header_f)
    ws.write('F4', enc['ret'], data_blue)
    ws.write('G4', 'Reclamo:', header_f)
    ws.write('H4', enc['rec'], data_blue)
    ws.write('I4', 'Cliente:', header_f)
    ws.write('J4', enc['cli'], data_blue)
    ws.merge_range('K4:L4', enc['nom'], data_blue)

    # C. TABLA PRODUCTOS
    row = 6
    h_list = ['FECHA', 'No FACTURA', 'No PARTE', 'FAB.', 'LOTE', 'CANT.', 'DESCRIPCIÓN']
    for i, h in enumerate(h_list): ws.write(row, i, h, header_f)

    row = 7
    for i in range(10):
        if i < len(productos):
            p = productos[i]
            f_v = p['FECHA'].strftime('%d/%m/%Y') if p.get('FECHA') and not pd.isnull(p['FECHA']) else ""
            ws.write(row, 0, f_v, std_f)
            ws.write(row, 1, p.get('No de factura', ''), std_f)
            ws.write(row, 2, p.get('No de parte', ''), std_f)
            ws.write(row, 3, p.get('Orden fabricacion', ''), std_f)
            ws.write(row, 4, p.get('Lote', ''), std_f)
            ws.write(row, 5, p.get('Cantidad', ''), std_f)
            ws.merge_range(row, 6, row, 11, p.get('Descripcion', ''), std_f)
        else:
            ws.merge_range(row, 0, row, 11, "", std_f)
        row += 1

    # D. BLOQUE ANALISTA E INCOMING (REPLICA PDF)
    ws.merge_range(row, 0, row, 1, 'Nota de crédito', header_f)
    ws.write(row, 2, '( x )' if admin_nc[0] else '(   )', std_f)
    ws.merge_range(row, 3, row+3, 11, 'Analista de incoming\n\n\n__________________________\nFirma/fecha', firma_f)
    ws.merge_range(row+1, 0, row+1, 1, 'Producto', header_f)
    ws.write(row+1, 2, '( x )' if admin_nc[1] else '(   )', std_f)
    ws.merge_range(row+2, 0, row+2, 1, 'Servicio', header_f)
    ws.write(row+2, 2, '( x )' if admin_nc[2] else '(   )', std_f)
    ws.write(row+3, 0, '', std_f); ws.write(row+3, 1, '', std_f); ws.write(row+3, 2, '', std_f)

    workbook.close()
    return output.getvalue()

# --- 2. ESTADO ---
if 'df_calidad_oficial' not in st.session_state:
    st.session_state.df_calidad_oficial = pd.DataFrame([{"FECHA": None, "No de factura": "", "No de parte": "", "Orden fabricacion": "", "Lote": "", "Cantidad": "", "Descripcion": ""}] * 10)

# --- 3. CAPTURA ---
st.title(":material/rebase_edit: Control de Calidad JYPESA")
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    f_sol = c1.text_input("SOLICITA CALIDAD").upper()
    f_des = c2.text_input("No. DE DESVIACIÓN").upper()
    f_ret = c3.text_input("No. RETRABAJO").upper()
    f_rec = c4.text_input("No. DE RECLAMO").upper()
    f_cli = c5.text_input("No. CLIENTE").upper()
    f_nom = st.text_input("NOMBRE COMERCIAL").upper()

df_edit = st.data_editor(st.session_state.df_calidad_oficial, num_rows="dynamic", use_container_width=True)

with st.container(border=True):
    hallazgo = st.text_area("COMENTARIOS (HALLAZGO)").upper()
    acciones = st.text_area("ACCIONES A REALIZAR").upper()
    c_nc, c_pr, c_se = st.columns(3)
    nc = c_nc.checkbox("Nota de crédito")
    pr = c_pr.checkbox("Producto")
    se = c_se.checkbox("Servicio")
    f_dic = st.radio("DICTAMEN:", ["ACEPTADO", "RECHAZADO"], horizontal=True)

# --- 4. IMPRESIÓN HTML (IGUAL AL PDF) ---
def generar_html_exacto():
    filas_html = ""
    for _, r in df_edit.iterrows():
        f_v = r['FECHA'].strftime('%d-%b-%y') if r.get('FECHA') and not pd.isnull(r['FECHA']) else ""
        filas_html += f"<tr><td>{f_v}</td><td>{r['No de factura']}</td><td>{r['No de parte']}</td><td>{r['Orden fabricacion']}</td><td>{r['Lote']}</td><td>{r['Cantidad']}</td><td>{r['Descripcion']}</td></tr>"
    for _ in range(max(0, 10 - len(df_edit))): filas_html += "<tr><td colspan='7' style='height:20px;'></td></tr>"

    return f"""<html><head><style>
        @media print {{ @page {{ size: letter landscape; margin: 5mm; }} }}
        body {{ font-family: Arial; font-size: 8px; color: black; }}
        table {{ width: 100%; border-collapse: collapse; border: 1.5px solid black; }}
        td {{ border: 1px solid black; padding: 3px; }}
        .gray {{ background: #D9D9D9; font-weight: bold; text-align: center; }}
        .blue {{ color: blue; font-weight: bold; font-style: italic; }}
    </style></head><body>
        <table><tr><td colspan="2">JYPESA</td><td colspan="5" style="text-align:center; font-size:12px;"><b>Formato de control de rehabilitación, reproceso y retrabajo de producto</b></td></tr>
        <tr class="gray"><td>Clave: F03-PNO-AC-21</td><td>Versión: 3</td><td>Publicación: 14-Ene-25</td><td colspan="4">Sustituye a: F03-PNO-AC-21 V02</td></tr>
        <tr class="blue" style="text-align:center;"><td>{f_sol}</td><td>{f_des}</td><td>{f_ret}</td><td>{f_rec}</td><td>{f_cli}</td><td colspan="2">{f_nom}</td></tr>
        <tr class="gray"><td>FECHA</td><td>FACTURA</td><td>No PARTE</td><td>FABRICACIÓN</td><td>LOTE</td><td>CANT.</td><td>DESCRIPCIÓN</td></tr>{filas_html}
        <tr><td class="gray">Nota Crédito ({"x" if nc else " "})</td><td colspan="6" rowspan="3" style="text-align:center;"><b>Analista de incoming</b><br><br>__________________________<br>Firma/fecha</td></tr>
        <tr><td class="gray">Producto ({"x" if pr else " "})</td></tr><tr><td class="gray">Servicio ({"x" if se else " "})</td></tr>
        </table>
    </body></html>"""

# --- 5. BOTONES (SEPARADOS E INDEPENDIENTES) ---
st.divider()
col1, col2 = st.columns(2)

if col1.button(":material/print: IMPRIMIR PDF", type="primary", use_container_width=True):
    components.html(f"<html><body>{generar_html_exacto()}<script>window.onload=function(){{window.print();}}</script></body></html>", height=0)

try:
    ex_file = generar_excel_identico({"sol":f_sol,"des":f_des,"ret":f_ret,"rec":f_rec,"cli":f_cli,"nom":f_nom,"hallazgo":hallazgo,"acc":acciones}, df_edit.to_dict('records'), f_dic, [nc, pr, se])
    col2.download_button(label=":material/file_download: DESCARGAR EXCEL", data=ex_file, file_name=f"CALIDAD_{f_nom}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
except Exception as e:
    col2.warning("Capturando datos...")











































































































