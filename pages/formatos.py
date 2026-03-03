import streamlit as st
import pandas as pd
from datetime import date, datetime
import pytz 
import streamlit.components.v1 as components
import io
import xlsxwriter

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Calidad Oficial")

# --- 1. MOTOR DE EXCEL (RÉPLICA EXACTA SEGÚN TU IMAGEN) ---
def generar_excel_identico(enc, productos, dictamen_val, admin_nc, hallazgo, acciones):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = workbook.add_worksheet("Formato Calidad")
    
    # Formatos
    title_f = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 2, 'font_size': 11})
    header_f = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D9D9D9', 'font_size': 8})
    data_blue = workbook.add_format({'font_color': 'blue', 'italic': True, 'bold': True, 'align': 'center', 'border': 1, 'font_size': 10})
    std_f = workbook.add_format({'border': 1, 'font_size': 9, 'align': 'center'})
    firma_f = workbook.add_format({'align': 'center', 'valign': 'top', 'border': 1, 'font_size': 9})

    ws.set_column('A:L', 11)

    # Encabezado (Réplica de imagen)
    ws.merge_range('A1:B2', 'JYPESA', title_f)
    ws.merge_range('C1:L2', 'Formato de control de rehabilitación, reproceso y retrabajo de producto', title_f)
    
    ws.write('A3', 'Clave:', header_f)
    ws.write('B3', 'F03-PNO-AC-21', std_f)
    ws.write('C3', 'Versión:', header_f)
    ws.write('D3', '3', std_f)
    ws.merge_range('E3:F3', 'Fecha de publicación:', header_f)
    ws.merge_range('G3:H3', '14-Ene-25', std_f)
    ws.merge_range('I3:L3', 'Sustituye a: F03-PNO-AC-21 V02', std_f)

    # Datos de Captura
    ws.write('A4', 'Solicita:', header_f)
    ws.write('B4', enc.get('sol', ''), data_blue)
    ws.write('C4', 'Desviación:', header_f)
    ws.write('D4', enc.get('des', ''), data_blue)
    ws.write('E4', 'Retrabajo:', header_f)
    ws.write('F4', enc.get('ret', ''), data_blue)
    ws.write('G4', 'Reclamo:', header_f)
    ws.write('H4', enc.get('rec', ''), data_blue)
    ws.write('I4', 'Cliente:', header_f)
    ws.write('J4', enc.get('cli', ''), data_blue)
    ws.merge_range('K4:L4', enc.get('nom', ''), data_blue)

    # Tabla Productos (10 filas fijas como en la imagen)
    row = 6
    h_list = ['FECHA', 'No FACTURA', 'No PARTE', 'FAB.', 'LOTE', 'CANT.', 'DESCRIPCIÓN']
    for i, h in enumerate(h_list): ws.write(row, i, h, header_f)

    row = 7
    for i in range(10):
        if i < len(productos):
            p = productos[i]
            f_val = ""
            if p.get('FECHA') and not pd.isnull(p['FECHA']):
                try: f_val = p['FECHA'].strftime('%d/%m/%Y')
                except: f_val = str(p['FECHA'])
            ws.write(row, 0, f_val, std_f)
            ws.write(row, 1, p.get('No de factura', ''), std_f)
            ws.write(row, 2, p.get('No de parte', ''), std_f)
            ws.write(row, 3, p.get('Orden fabricacion', ''), std_f)
            ws.write(row, 4, p.get('Lote', ''), std_f)
            ws.write(row, 5, p.get('Cantidad', ''), std_f)
            ws.merge_range(row, 6, row, 11, p.get('Descripcion', ''), std_f)
        else:
            ws.merge_range(row, 0, row, 11, "", std_f)
        row += 1

    # Bloques Administrativos (Réplica exacta parte baja)
    ws.write(row, 0, 'Nota de crédito', header_f)
    ws.write(row, 1, '( x )' if admin_nc[0] else '(   )', std_f)
    ws.merge_range(row, 2, row+3, 11, 'Analista de incoming\n\n\n__________________________\nFirma/fecha', firma_f)
    ws.write(row+1, 0, 'Producto', header_f)
    ws.write(row+1, 1, '( x )' if admin_nc[1] else '(   )', std_f)
    ws.write(row+2, 0, 'Servicio', header_f)
    ws.write(row+2, 1, '( x )' if admin_nc[2] else '(   )', std_f)
    
    workbook.close()
    return output.getvalue()

# --- 2. ESTADO DE LA TABLA ---
if 'df_calidad_oficial' not in st.session_state:
    st.session_state.df_calidad_oficial = pd.DataFrame(
        [{"FECHA": None, "No de factura": "", "No de parte": "", "Orden fabricacion": "", "Lote": "", "Cantidad": "", "Descripcion": ""}] * 10
    )

# --- 3. INTERFAZ DE CAPTURA ---
st.title(":material/rebase_edit: Control de Calidad JYPESA")
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    f_sol = c1.text_input("SOLICITA CALIDAD").upper()
    f_des = c2.text_input("No. DE DESVIACIÓN").upper()
    f_ret = c3.text_input("No. RETRABAJO").upper()
    f_rec = c4.text_input("No. DE RECLAMO").upper()
    f_cli = c5.text_input("No. CLIENTE").upper()

    c6, c7, c8, c9 = st.columns([2, 1, 1, 1])
    f_nom = c6.text_input("NOMBRE COMERCIAL").upper()
    f_tra = c7.text_input("TRANSPORTE").upper()
    f_gui = c8.text_input("GUÍA").upper()
    f_cos = c9.text_input("COSTO").upper()

df_edit = st.data_editor(st.session_state.df_calidad_oficial, num_rows="dynamic", use_container_width=True)

with st.container(border=True):
    hallazgo = st.text_area("COMENTARIOS (HALLAZGO)").upper()
    acciones = st.text_area("ACCIONES A REALIZAR").upper()
    ca_v1, ca_v2, ca_v3 = st.columns(3)
    nc = ca_v1.checkbox("Nota de crédito")
    pr = ca_v2.checkbox("Producto")
    se = ca_v3.checkbox("Servicio")
    f_dic = st.radio("DICTAMEN FINAL:", ["ACEPTADO", "RECHAZADO"], horizontal=True)

# --- 4. IMPRESIÓN (LA QUE YA DOMINÁBAMOS) ---
def generar_html_exacto():
    filas_html = ""
    for _, r in df_edit.iterrows():
        f_val = ""
        if r['FECHA'] and not pd.isnull(r['FECHA']):
            try: f_val = r['FECHA'].strftime('%d-%b-%y')
            except: f_val = str(r['FECHA'])
        filas_html += f"""<tr style="height:18px;"><td>{f_val}</td><td>{r['No de factura']}</td><td>{r['No de parte']}</td><td>{r['Orden fabricacion']}</td><td>{r['Lote']}</td><td style="text-align:center;">{r['Cantidad']}</td><td>{r['Descripcion']}</td></tr>"""
    for _ in range(max(0, 10 - len(df_edit))): filas_html += "<tr style='height:18px;'><td colspan='7'></td></tr>"
    
    return f"""<html><head><style>
        @media print {{ @page {{ size: letter landscape; margin: 5mm; }} }}
        body {{ font-family: 'Arial Narrow', Arial; font-size: 8.2px; color: black; }}
        table {{ width: 100%; border-collapse: collapse; border: 1.5px solid black; }}
        td {{ border: 1px solid black; padding: 2px; }}
        .header-gray {{ background-color: #D9D9D9; font-weight: bold; text-align: center; }}
        .input-blue {{ color: blue; font-weight: bold; font-style: italic; font-size: 9.5px; }}
        .title {{ font-size: 13px; font-weight: bold; text-align: center; height: 28px; }}
    </style></head><body>
        <table><tr><td colspan="2" style="text-align:center;"><b>JYPESA</b></td><td colspan="10" class="title">Formato de control de rehabilitación, reproceso y retrabajo de producto</td></tr>
        <tr class="header-gray"><td>Clave: F03-PNO-AC-21</td><td>Versión: 3</td><td colspan="3">Publicación: 14-Ene-25</td><td colspan="4">Sustituye a: F03-PNO-AC-21 V02</td></tr>
        <tr class="input-blue" style="text-align:center;"><td>{f_sol}</td><td>{f_des}</td><td colspan="2">{f_ret}</td><td>{f_rec}</td><td>{f_cli}</td><td colspan="2">{f_nom}</td><td>{f_tra}</td><td>{f_gui}</td><td colspan="2">{f_cos}</td></tr></table>
        <table style="margin-top:-1px;">{filas_html}</table>
        <table style="margin-top:-1px;"><tr><td style="width:18%;" class="header-gray">Nota crédito ({"x" if nc else " "})</td><td rowspan="4" style="text-align:center;"><b>Analista de incoming</b><br><br>__________________________<br>Firma/fecha</td></tr></table>
    </body></html>"""

# --- 5. BOTONES DE ACCIÓN (BLINDADOS) ---
st.divider()
c_print, c_excel = st.columns(2)

if c_print.button(":material/print: IMPRIMIR FORMATO", type="primary", use_container_width=True):
    formato = generar_html_exacto()
    components.html(f"<html><body>{formato}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)

# Generación de Excel silenciosa para que no salgan letreros amarillos
excel_data = generar_excel_identico(
    {"sol": f_sol, "des": f_des, "ret": f_ret, "rec": f_rec, "cli": f_cli, "nom": f_nom},
    df_edit.to_dict('records'),
    f_dic,
    [nc, pr, se],
    hallazgo,
    acciones
)

c_excel.download_button(
    label=":material/file_download: DESCARGAR EXCEL IDÉNTICO",
    data=excel_data,
    file_name=f"CALIDAD_JYPESA_{f_nom}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)










































































































