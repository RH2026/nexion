from datetime import datetime
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st

st.subheader("Generador de Orden de Embarque - PaqMex")

# 1. Captura de datos o carga desde tu matriz
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

# Datos del Destinatario (Jalados de tu matriz)
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

# Lógica de Facturación
if tipo_pago == "CRÉDITO":
  facturacion = remitente
  credito_mark = "X"
  por_cobrar_mark = ""
  pagado_mark = ""
else:
  facturacion = destinatario
  credito_mark = ""
  por_cobrar_mark = "X" if tipo_pago == "POR COBRAR" else ""
  pagado_mark = "X" if tipo_pago == "PAGADO" else ""

fecha_actual = datetime.now().strftime("%d/%m/%Y")


def generar_pdf_reportlab():
  buffer = BytesIO()
  # Márgenes estrechos de 10mm (aprox 28 puntos)
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=28,
      leftMargin=28,
      topMargin=28,
      bottomMargin=28,
  )
  story = []
  styles = getSampleStyleSheet()

  # Estilos personalizados
  title_style = ParagraphStyle(
      "TitleStyle",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=16,
      leading=18,
  )
  logo_style = ParagraphStyle(
      "LogoStyle",
      parent=styles["Normal"],
      fontName="Helvetica-BoldOblique",
      fontSize=20,
      leading=22,
      textColor=colors.HexColor("#003366"),
      alignment=2,  # Derecha
  )
  logo_sub = ParagraphStyle(
      "LogoSub",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=6,
      leading=7,
      textColor=colors.HexColor("#003366"),
      alignment=2,
  )
  subtitle_style = ParagraphStyle(
      "SubTitleStyle",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=12,
      leading=14,
      alignment=1,  # Centro
  )
  th_style = ParagraphStyle(
      "THStyle",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=8.5,
      leading=10,
      textColor=colors.white,
      alignment=1,
  )
  cell_bold = ParagraphStyle(
      "CellBold",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=7.5,
      leading=9,
  )
  cell_normal = ParagraphStyle(
      "CellNormal",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=7.5,
      leading=9,
  )
  cell_center = ParagraphStyle(
      "CellCenter",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=10,
      leading=12,
      alignment=1,
  )

  # 1. Encabezado principal
  header_data = [
      [Paragraph("PAQMEX S.A. DE C.V.", title_style), Paragraph("PaqMex", logo_style)],
      ["", Paragraph("SOLUCIONES EN LOGÍSTICA", logo_sub)],
  ]
  t_header = Table(header_data, colWidths=[280, 274])
  t_header.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
          ("TOPPADDING", (0, 0), (-1, -1), 0),
      ])
  )
  story.append(t_header)
  story.append(Spacer(1, 10))

  story.append(Paragraph("ORDEN DE EMBARQUE", subtitle_style))
  story.append(Spacer(1, 8))

  # 2. Fecha y Factura
  meta_data = [
      [
          "",
          Paragraph("<b>FECHA:</b>", ParagraphStyle("R", alignment=2, fontSize=9)),
          Paragraph(f"<b>{fecha_actual}</b>", ParagraphStyle("C", alignment=1, fontSize=9)),
      ],
      [
          "",
          Paragraph("<b>FACTURA:</b>", ParagraphStyle("R", alignment=2, fontSize=9)),
          Paragraph(f"<b>{num_factura}</b>", ParagraphStyle("C", alignment=1, fontSize=9)),
      ],
  ]
  t_meta = Table(meta_data, colWidths=[350, 100, 104])
  t_meta.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          (
              "LINEBELOW",
              (2, 0),
              (2, 0),
              1,
              colors.black,
          ),  # Línea bajo fecha
          (
              "LINEBELOW",
              (2, 1),
              (2, 1),
              1,
              colors.black,
          ),  # Línea bajo factura
          ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
      ])
  )
  story.append(t_meta)
  story.append(Spacer(1, 6))

  # 3. Remitente y Destinatario (Dos columnas)
  rem_data = [
      [Paragraph("REMITENTE", th_style), ""],
      [
          Paragraph("CLIENTE:", cell_bold),
          Paragraph(remitente["cliente"], cell_bold),
      ],
      [Paragraph("RFC:", cell_bold), Paragraph(remitente["rfc"], cell_normal)],
      [Paragraph("CALLE:", cell_bold), Paragraph(remitente["calle"], cell_normal)],
      [
          Paragraph("COLONIA:", cell_bold),
          Paragraph(remitente["colonia"], cell_normal),
      ],
      [
          Paragraph("MUNICIPIO:", cell_bold),
          Paragraph(
              f"{remitente['municipio']} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>ESTADO:</b> {remitente['estado']}",
              cell_normal,
          ),
      ],
      [
          Paragraph("CONTACTO:<br/>TELEFONO:", cell_bold),
          Paragraph(
              f"{remitente['contacto']}<br/>{remitente['telefono']}",
              cell_normal,
          ),
      ],
  ]
  t_rem = Table(rem_data, colWidths=[70, 202])
  t_rem.setStyle(
      TableStyle([
          ("SPAN", (0, 0), (1, 0)),
          ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#6c8ebf")),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
      ])
  )

  dest_data = [
      [Paragraph("DESTINATARIO", th_style), ""],
      [
          Paragraph("CLIENTE:", cell_bold),
          Paragraph(destinatario["cliente"], cell_bold),
      ],
      [Paragraph("RFC:", cell_bold), Paragraph(destinatario["rfc"], cell_normal)],
      [
          Paragraph("CALLE:", cell_bold),
          Paragraph(destinatario["calle"], cell_normal),
      ],
      [
          Paragraph("COLONIA:", cell_bold),
          Paragraph(destinatario["colonia"], cell_normal),
      ],
      [
          Paragraph("MUNICIPIO:", cell_bold),
          Paragraph(
              f"{destinatario['municipio']} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {destinatario['estado']}",
              cell_normal,
          ),
      ],
      [
          Paragraph("CONTACTO:<br/>TELEFONO:", cell_bold),
          Paragraph(
              f"{destinatario['contacto']}<br/>{destinatario['telefono']}",
              cell_normal,
          ),
      ],
  ]
  t_dest = Table(dest_data, colWidths=[70, 202])
  t_dest.setStyle(
      TableStyle([
          ("SPAN", (0, 0), (1, 0)),
          ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#6c8ebf")),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
      ])
  )

  t_top_blocks = Table([[t_rem, t_dest]], colWidths=[274, 274])
  t_top_blocks.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 0),
          ("RIGHTPADDING", (0, 0), (-1, -1), 0),
      ])
  )
  story.append(t_top_blocks)
  story.append(Spacer(1, 6))

  # 4. Facturación y Servicios
  fac_data = [
      [Paragraph("FACTURACION", th_style), ""],
      [
          Paragraph("CLIENTE:", cell_bold),
          Paragraph(facturacion["cliente"], cell_bold),
      ],
      [
          Paragraph(
              "RFC:<br/><br/><br/><br/>EMAIL:", cell_bold
          ),  # Espacio simulado igual al formato
          Paragraph(
              "Privada del Gallo No. 1525<br/>Col. La Aurora C.P. 44460<br/>Guadalajara, JAL México<br/>Tel.. 0152 (33) 35402939<br/>E-mail: sbomailer@jypesa.com",
              ParagraphStyle(
                  "CF",
                  parent=cell_normal,
                  alignment=1,
                  fontSize=7,
                  leading=8.5,
              ),
          ),
      ],
      [
          Paragraph("RFC:", cell_bold),
          Paragraph(f"<b>{facturacion['rfc']}</b>", cell_bold),
      ],
      [
          Paragraph("EMAIL:", cell_bold),
          Paragraph("sbomailer@jypesa.com", cell_normal),
      ],
  ]
  t_fac = Table(fac_data, colWidths=[70, 202])
  t_fac.setStyle(
      TableStyle([
          ("SPAN", (0, 0), (1, 0)),
          ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#6c8ebf")),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 2.5),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
      ])
  )

  serv_data = [
      [Paragraph("SERVICIOS", th_style), "", "", ""],
      [Paragraph("PAGADO:", cell_bold), pagado_mark, Paragraph("SEGURO:", cell_bold), "SI: X   NO:"],
      [Paragraph("POR COBRAR:", cell_bold), por_cobrar_mark, Paragraph("VALOR DECLARADO:", cell_bold), ""],
      [Paragraph("CREDITO:", cell_bold), credito_mark, "", ""],
      [Paragraph("OCURRE:", cell_bold), "", Paragraph("CITA :", cell_bold), "SI [ &nbsp; ] NO"],
      [Paragraph("A DOMICILIO:", cell_bold), "X", Paragraph("CONTACTO:<br/>TELEFONO:", cell_bold), ""],
      [Paragraph("MANIOBRAS:", cell_bold), "", "", ""],
  ]
  t_serv = Table(
      serv_data, colWidths=[70, 45, 85, 72]
  )  # Ancho total 274
  t_serv.setStyle(
      TableStyle([
          ("SPAN", (0, 0), (3, 0)),
          ("BACKGROUND", (0, 0), (3, 0), colors.HexColor("#6c8ebf")),
          ("SPAN", (2, 2), (3, 2)),
          ("SPAN", (2, 3), (3, 3)),
          ("SPAN", (2, 4), (3, 4)),
          ("SPAN", (0, 6), (3, 6)),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          (
              "ALIGN",
              (1, 1),
              (1, 3),
              "CENTER",
          ),  # Centrar X en casillas de pago
          ("ALIGN", (1, 5), (1, 5), "CENTER"),
          ("TOPPADDING", (0, 0), (-1, -1), 3.2),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
      ])
  )

  t_mid_blocks = Table([[t_fac, t_serv]], colWidths=[274, 274])
  t_mid_blocks.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 0),
          ("RIGHTPADDING", (0, 0), (-1, -1), 0),
      ])
  )
  story.append(t_mid_blocks)
  story.append(Spacer(1, 6))

  # 5. CONTENIDO
  cont_data = [[Paragraph("CONTENIDO", th_style), "", "", "", "", "", ""]]
  cont_headers = [
      "#",
      "CANTIDAD",
      "EMPAQUE",
      "CONTENIDO",
      "DIMENSIONES (ALTO/LARGO/ANCHO)",
      "KG REAL",
      "KG VOLUMEN",
  ]
  cont_data.append([Paragraph(h, th_style) for h in cont_headers])
  # Ajustar color de encabezados de columnas de contenido a un gris/azul claro o mantener oscuro
  for i in range(1, 5):
    cont_data.append(
        [
            str(i),
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    )

  t_cont = Table(
      cont_data, colWidths=[25, 60, 80, 164, 155, 50, 64]
  )  # Total 548
  t_cont.setStyle(
      TableStyle([
          ("SPAN", (0, 0), (6, 0)),
          ("BACKGROUND", (0, 0), (6, 0), colors.HexColor("#6c8ebf")),
          ("BACKGROUND", (0, 1), (6, 1), colors.HexColor("#6c8ebf")),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("TOPPADDING", (0, 0), (-1, -1), 3),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
      ])
  )
  story.append(t_cont)
  story.append(Spacer(1, 6))

  # 6. CARTA PORTE
  cp_data = [[Paragraph("CARTA PORTE", th_style), "", ""]]
  cp_headers = [
      "#",
      "CODIGO PRODUCTO CARTA PORTE SAT",
      "CODIGO UNIDAD PESO CARTA PORTE SAT",
  ]
  cp_data.append([Paragraph(h, th_style) for h in cp_headers])
  for i in range(1, 5):
    cp_data.append([str(i), "", ""])

  t_cp = Table(cp_data, colWidths=[25, 261, 262])
  t_cp.setStyle(
      TableStyle([
          ("SPAN", (0, 0), (2, 0)),
          ("BACKGROUND", (0, 0), (2, 0), colors.HexColor("#6c8ebf")),
          ("BACKGROUND", (0, 1), (2, 1), colors.HexColor("#6c8ebf")),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("TOPPADDING", (0, 0), (-1, -1), 3),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
      ])
  )
  story.append(t_cp)
  story.append(Spacer(1, 30))

  # 7. Firmas
  sig_style = ParagraphStyle(
      "Sig",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=7.5,
      leading=9,
      alignment=1,
  )
  sig_data = [
      [
          Paragraph(
              "________________________________________<br/>FIRMA Y NOMBRE DEL CLIENTE :",
              sig_style,
          ),
          Paragraph(
              "________________________________________<br/>FIRMA Y NOMBRE DE QUIEN RECIBE :",
              sig_style,
          ),
          Paragraph(
              "________________________________________<br/>NUMERO DE UNIDAD",
              sig_style,
          ),
      ]
  ]
  t_sig = Table(sig_data, colWidths=[183, 183, 182])
  t_sig.setStyle(
      TableStyle([
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
      ])
  )
  story.append(t_sig)

  doc.build(story)
  buffer.seek(0)
  return buffer


if st.button("Generar PDF de Orden de Embarque"):
  pdf_buffer = generar_pdf_reportlab()
  st.success("¡Orden de embarque generada con éxito con ReportLab!")
  st.download_button(
      label="📥 Descargar PDF",
      data=pdf_buffer,
      file_name=f"Orden_Embarque_{num_factura}.pdf",
      mime="application/pdf",
  )














































































































































