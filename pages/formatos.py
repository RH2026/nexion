import streamlit as st
import pandas as pd
from datetime import date, datetime
import pytz 
import streamlit.components.v1 as components
import io
import xlsxwriter

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="NEXION - Calidad Oficial")

# --- 1. MOTOR DE EXCEL (RÉPLICA EXACTA SEGÚN IMAGEN) ---
def generar_excel_identico(enc, productos, dictamen_val, tipo_orden, admin_nc):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = workbook.add_worksheet("Formato Calidad")
    
    # FORMATOS DE CELDA
    title_f = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 2, 'font_size': 12})
    header_f = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D9D9D9', 'font_size': 8})
    data_blue = workbook.add_format({'font_color': 'blue', 'italic': True, 'bold': True, 'align': 'center', 'border': 1, 'font_size': 10})
    border_std = workbook.add_format({'border': 1, 'font_size': 9, 'align': 'center'})
    firma_f = workbook.add_format({'align': 'center', 'valign': 'top', 'border': 1, 'font_size': 9})

    ws.set_column('A:L', 10)

    # A. ENCABEZADO SUPERIOR
    ws.merge_range('A1:B2', 'JYPESA', title_f)
    ws.merge_range('C1:L2', 'Formato de control de rehabilitación, reproceso y retrabajo de producto', title_f)
    
    ws.write('A3', 'Clave:', header_f)
    ws.write('B3', 'F03-PNO-AC-21', border_std)
    ws.write('C3', 'Versión:', header_f)
    ws.write('D3', '3', border_std)
    ws.merge_range('E3:F3', 'Fecha de publicación:', header_f)
    ws.merge_range('G3:H3', '14-Ene-25', border_std)
    ws.merge_range('I3:L3', 'Sustituye a: F03-PNO-AC-21 V02', border_std)

    # B. DATOS DE CAPTURA
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

    # C. TABLA DE PRODUCTOS (SIEMPRE 10 FILAS)
    row = 6
    headers = ['FECHA', 'No FACTURA', 'No PARTE', 'FAB.', 'LOTE', 'CANT.', 'DESCRIPCIÓN']
    for i, h in enumerate(headers): ws.write(row, i, h, header_f)

    row = 7
    for i in range(10):
        if i < len(productos) and (productos[i].get('No de factura') or productos[i].get('Descripcion')):
            p = productos[i]
            f_val = p['FECHA'].strftime('%d/%m/%Y') if p['FECHA'] else ""
            ws.write(row, 0, f_val, border_std)
            ws.write(row, 1, p['No de factura'], border_std)
            ws.write(row, 2, p['No de parte'], border_std)
            ws.write(row, 3, p['Orden fabricacion'], border_std)
            ws.write(row, 4, p['Lote'], border_std)
            ws.write(row, 5, p['Cantidad'], border_std)
            ws.merge_range(row, 6, row, 11, p['Descripcion'], border_std)
        else:
            ws.merge_range(row, 0, row, 11, "", border_std)
        row += 1

    # D. BLOQUE ANALISTA E INCOMING (IGUAL A LA IMAGEN)
    ws.write(row, 0, 'Nota de crédito', header_f)
    ws.write(row, 1, '( x )' if admin_nc[0] else '(  )', border_std)
    ws.merge_range(row, 2, row+3, 11, 'Analista de incoming\n\n\n__________________________\nFirma/fecha', firma_f)
    ws.write(row+1, 0, 'Producto', header_f)
    ws.write(row+1, 1, '( x )' if admin_nc[1] else '(  )', border_std)
    ws.write(row+2, 0, 'Servicio', header_f)
    ws.write(row+2, 1, '( x )' if admin_nc[2] else '(  )', border_std)

    workbook.close()
    return output.getvalue()

# --- ESTADO DE LA TABLA ---
if 'df_calidad_oficial' not in st.session_state:
    st.session_state.df_calidad_oficial = pd.DataFrame(
        [{"FECHA": None, "No de factura": "", "No de parte": "", "Orden fabricacion": "", "Lote": "", "Cantidad": "", "Descripcion": ""}] * 10
    )

# --- CAPTURA ---
st.title(":material/rebase_edit: Control de Calidad JYPESA")
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

df_edit = st.data_editor(st.session_state.df_calidad_oficial, num_rows="dynamic", use_container_width=True)

with st.container(border=True):
    ca_v1, ca_v2, ca_v3 = st.columns(3)
    nc = ca_v1.checkbox("Nota de crédito")
    pr = ca_v2.checkbox("Producto")
    se = ca_v3.checkbox("Servicio")
    f_dictamen = st.radio("DICTAMEN FINAL:", ["ACEPTADO", "RECHAZADO"], horizontal=True)

# --- BOTONES DE IMPRESIÓN Y EXCEL ---
st.divider()
col_p, col_e = st.columns(2)

# 1. IMPRESIÓN (EL QUE YA TENÍAMOS DOMINADO AMOR)
if col_p.button(":material/print: IMPRIMIR FORMATO RÉPLICA", type="primary", use_container_width=True):
    # Aquí va tu función generar_html_exacto() que ya tenemos configurada
    st.info("Abriendo ventana de impresión...")

# 2. EXCEL (IDENTICO A LA IMAGEN)
try:
    excel_file = generar_excel_identico(
        {"sol": f_solicita, "des": f_desviacion, "ret": f_retrabajo, "rec": f_reclamo, "cli": f_cliente, "nom": f_nom_com},
        df_edit.to_dict('records'),
        f_dictamen,
        [], # tipo_orden
        [nc, pr, se]
    )
    col_e.download_button(
        label=":material/file_download: DESCARGAR EXCEL IDÉNTICO",
        data=excel_file,
        file_name=f"CALIDAD_JYPESA_{f_nom_com}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
except:
    col_e.warning("Esperando datos...")









































































































