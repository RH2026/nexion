from datetime import datetime
import pandas as pd
import streamlit as st
from weasyprint import HTML

st.subheader("Generador de Orden de Embarque - PaqMex")

# 1. Cargar tu matriz de clientes (ajusta la ruta o método de carga según uses en NEXION)
# @st.cache_data
# def cargar_matriz():
#     return pd.read_excel("matriz_clientes.xlsx")
# df_clientes = cargar_matriz()

# Opciones manuales o de selección
# cliente_elegido = st.selectbox("Seleccionar Cliente Destino:", df_clientes["CLIENTE"].unique())
# datos_cliente = df_clientes[df_clientes["CLIENTE"] == cliente_elegido].iloc[0]

# Simulando la selección para el ejemplo:
num_factura = st.text_input("Número de Factura:", value="241106")
tipo_pago = st.radio(
    "Selecciona Tipo de Pago:", ["CRÉDITO", "POR COBRAR", "PAGADO"]
)

# Datos fijos del Remitente (Jypesa)
remitente = {
    "cliente": "JABONES Y PRODUCTOS ESPECIALIZADOS SA DE CV",
    "rfc": "JPE830408B35",
    "calle": "Privada del Gallo No. 1525",
    "colonia": "Col La Aurora",
    "municipio": "Guadalajara",
    "estado": "Jalisco",
    "contacto": "Rigoberto Hernandez",
    "telefono": "33 19 75 31 22",
}

# Datos del Destinatario (Jalados dinámicamente de tu matriz)
# (Aquí usamos campos de ejemplo que vendrían de tu DataFrame)
destinatario = {
    "cliente": "HAMPTON REYNOSA/ZONA INDUSTRIAL, MEXICO",
    "rfc": "DBM121023M10",
    "calle": "PLAZA PERIFERICO, CARR. LIBRE A MONTERREY-REYNOSA 1000",
    "colonia": "0",
    "municipio": "REYNOSA",
    "estado": "TAM",
    "contacto": "",
    "telefono": "899 970 0108",
}

# Lógica de Facturación: Si es Crédito se usan datos de Jypesa; si es Cobro Destino se usan fiscales de destinatario
if tipo_pago == "CRÉDITO":
    facturacion = remitente
    credito_mark = "X"
    por_cobrar_mark = ""
    pagado_mark = ""
else:
    facturacion = destinatario  # O sus datos fiscales específicos de la matriz
    credito_mark = ""
    por_cobrar_mark = "X" if tipo_pago == "POR COBRAR" else ""
    pagado_mark = "X" if tipo_pago == "PAGADO" else ""

# Fecha actual
fecha_actual = datetime.now().strftime("%d/%m/%Y")

# HTML y CSS con el formato idéntico
html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ size: letter; margin: 10mm; background-color: #ffffff; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: Helvetica, Arial, sans-serif; font-size: 8pt; color: #000000; margin: 0; padding: 0; }}
    .header-table {{ width: 100%; margin-bottom: 5px; }}
    .title-text {{ font-size: 16pt; font-weight: bold; letter-spacing: 0.5px; }}
    .subtitle-text {{ font-size: 12pt; font-weight: bold; text-align: center; margin: 5px 0 10px 0; }}
    .meta-table {{ width: 100%; margin-bottom: 8px; }}
    .meta-table td {{ font-size: 9pt; font-weight: bold; padding: 2px 0; }}
    .sec-table {{ width: 100%; border-collapse: collapse; margin-bottom: 6px; }}
    .sec-table th {{ background-color: #6c8ebf; color: #ffffff; font-size: 8.5pt; font-weight: bold; text-align: center; padding: 3px; border: 1px solid #333; }}
    .sec-table td {{ border: 1px solid #333; padding: 2.5px 4px; vertical-align: middle; font-size: 7.5pt; }}
    .label {{ font-weight: bold; width: 18%; }}
    .val {{ font-weight: normal; }}
    .two-col {{ width: 100%; margin-bottom: 0px; }}
    .two-col td {{ width: 50%; vertical-align: top; padding: 0 3px; }}
    .two-col td:first-child {{ padding-left: 0; }}
    .two-col td:last-child {{ padding-right: 0; }}
    .center {{ text-align: center; }}
    .bold {{ font-weight: bold; }}
    .signature-table {{ width: 100%; margin-top: 30px; }}
    .signature-table td {{ text-align: center; font-size: 7.5pt; font-weight: bold; padding-top: 25px; }}
    .sig-line {{ border-top: 1px solid #000; width: 80%; margin: 0 auto; padding-top: 3px; }}
</style>
</head>
<body>

<table class="header-table">
    <tr>
        <td style="width: 55%; vertical-align: middle;"><div class="title-text">PAQMEX S.A. DE C.V.</div></td>
        <td style="width: 45%; text-align: right; vertical-align: middle;">
            <div style="font-size: 20pt; font-weight: bold; color: #003366; font-style: italic;">PaqMex</div>
            <div style="font-size: 6pt; color: #003366; font-weight: bold;">SOLUCIONES EN LOGÍSTICA</div>
        </td>
    </tr>
</table>

<div class="subtitle-text">ORDEN DE EMBARQUE</div>

<table class="meta-table">
    <tr>
        <td style="width: 70%;"></td>
        <td style="width: 12%; text-align: right;">FECHA:</td>
        <td style="width: 18%; border-bottom: 1px solid #000; text-align: center;">{fecha_actual}</td>
    </tr>
    <tr>
        <td></td>
        <td style="text-align: right;">FACTURA:</td>
        <td style="border-bottom: 1px solid #000; text-align: center;">{num_factura}</td>
    </tr>
</table>

<!-- REMITENTE & DESTINATARIO -->
<table class="two-col">
    <tr>
        <td>
            <table class="sec-table">
                <tr><th colspan="2">REMITENTE</th></tr>
                <tr><td class="label">CLIENTE:</td><td class="val bold">{remitente['cliente']}</td></tr>
                <tr><td class="label">RFC:</td><td class="val">{remitente['rfc']}</td></tr>
                <tr><td class="label">CALLE:</td><td class="val">{remitente['calle']}</td></tr>
                <tr><td class="label">COLONIA:</td><td class="val">{remitente['colonia']}</td></tr>
                <tr><td class="label">MUNICIPIO:</td><td class="val">{remitente['municipio']} <span style="margin-left: 20px;">ESTADO:</span> <span style="margin-left: 10px;">{remitente['estado']}</span></td></tr>
                <tr><td class="label">CONTACTO:<br>TELEFONO:</td><td class="val">{remitente['contacto']}<br>{remitente['telefono']}</td></tr>
            </table>
        </td>
        <td>
            <table class="sec-table">
                <tr><th colspan="2">DESTINATARIO</th></tr>
                <tr><td class="label">CLIENTE:</td><td class="val bold">{destinatario['cliente']}</td></tr>
                <tr><td class="label">RFC:</td><td class="val">{destinatario['rfc']}</td></tr>
                <tr><td class="label">CALLE:</td><td class="val">{destinatario['calle']}</td></tr>
                <tr><td class="label">COLONIA:</td><td class="val">{destinatario['colonia']}</td></tr>
                <tr><td class="label">MUNICIPIO:</td><td class="val">{destinatario['municipio']} <span style="margin-left: 20px;">{destinatario['estado']}</span></td></tr>
                <tr><td class="label">CONTACTO:<br>TELEFONO:</td><td class="val">{destinatario['contacto']}<br>{destinatario['telefono']}</td></tr>
            </table>
        </td>
    </tr>
</table>

<!-- FACTURACION & SERVICIOS -->
<table class="two-col">
    <tr>
        <td>
            <table class="sec-table">
                <tr><th colspan="2">FACTURACION</th></tr>
                <tr><td class="label">CLIENTE:</td><td class="val bold">{facturacion['cliente']}</td></tr>
                <tr>
                    <td colspan="2" style="text-align: center; height: 52px; vertical-align: middle;">
                        Privada del Gallo No. 1525<br>
                        Col. La Aurora C.P. 44460<br>
                        Guadalajara, JAL México<br>
                        Tel.. 0152 (33) 35402939<br>
                        E-mail: sbomailer@jypesa.com. Tel. 33 3540 2939 Ext 157
                    </td>
                </tr>
                <tr><td class="label">RFC:</td><td class="val bold">{facturacion['rfc']}</td></tr>
                <tr><td class="label">EMAIL:</td><td class="val">sbomailer@jypesa.com</td></tr>
            </table>
        </td>
        <td>
            <table class="sec-table">
                <tr><th colspan="4">SERVICIOS</th></tr>
                <tr>
                    <td class="label" style="width: 30%;">PAGADO:</td>
                    <td class="center bold">{pagado_mark}</td>
                    <td class="label" style="width: 30%;">SEGURO:</td>
                    <td style="width: 20%;">SI: X &nbsp; NO:</td>
                </tr>
                <tr>
                    <td class="label">POR COBRAR:</td>
                    <td class="center bold">{por_cobrar_mark}</td>
                    <td colspan="2" class="label">VALOR DECLARADO:</td>
                </tr>
                <tr>
                    <td class="label">CREDITO:</td>
                    <td class="center bold" style="font-size: 11pt;">{credito_mark}</td>
                    <td colspan="2"></td>
                </tr>
                <tr>
                    <td class="label">OCURRE:</td>
                    <td></td>
                    <td colspan="2" rowspan="2">
                        CITA : <span style="margin-left: 15px;">SI</span> <span style="border:1px solid #000; padding:0 8px; margin-left:5px;">&nbsp;</span> <span style="margin-left: 10px;">NO</span><br><br>
                        CONTACTO:<br>TELEFONO:
                    </td>
                </tr>
                <tr>
                    <td class="label">A DOMICILIO:</td>
                    <td class="center bold" style="font-size: 11pt;">X</td>
                </tr>
                <tr>
                    <td colspan="4" class="label">MANIOBRAS:</td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!-- CONTENIDO -->
<table class="sec-table" style="margin-top: 4px;">
    <tr><th colspan="7">CONTENIDO</th></tr>
    <tr>
        <td class="center bold" style="width: 5%;">#</td>
        <td class="center bold" style="width: 15%;">CANTIDAD</td>
        <td class="center bold" style="width: 20%;">EMPAQUE</td>
        <td class="center bold" style="width: 30%;">CONTENIDO</td>
        <td class="center bold" style="width: 18%;">DIMENSIONES (ALTO/LARGO/ANCHO)</td>
        <td class="center bold" style="width: 6%;">KG REAL</td>
        <td class="center bold" style="width: 6%;">KG VOLUMEN</td>
    </tr>
    {"".join([f'<tr><td class="center">{i}</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>' for i in range(1, 5)])}
</table>

<!-- CARTA PORTE -->
<table class="sec-table" style="margin-top: 4px;">
    <tr><th colspan="3">CARTA PORTE</th></tr>
    <tr>
        <td class="center bold" style="width: 10%;">#</td>
        <td class="center bold" style="width: 45%;">CODIGO PRODUCTO CARTA PORTE SAT</td>
        <td class="center bold" style="width: 45%;">CODIGO UNIDAD PESO CARTA PORTE SAT</td>
    </tr>
    {"".join([f'<tr><td class="center">{i}</td><td>&nbsp;</td><td>&nbsp;</td></tr>' for i in range(1, 5)])}
</table>

<!-- FIRMAS -->
<table class="signature-table">
    <tr>
        <td style="width: 33%;"><div class="sig-line">FIRMA Y NOMBRE DEL CLIENTE :</div></td>
        <td style="width: 34%;"><div class="sig-line">FIRMA Y NOMBRE DE QUIEN RECIBE :</div></td>
        <td style="width: 33%;"><div class="sig-line">NUMERO DE UNIDAD</div></td>
    </tr>
</table>

</body>
</html>
"""

if st.button("Generar PDF de Orden de Embarque"):
  HTML(string=html_content).write_pdf("orden_embarque.pdf")
  st.success("¡Orden de embarque generada con éxito!")
  with open("orden_embarque.pdf", "rb") as f:
    st.download_button(
        "Descargar PDF", f, file_name=f"Orden_Embarque_{num_factura}.pdf"
    )
















































































































































