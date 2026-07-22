import base64
from datetime import datetime
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import requests
import streamlit as st

st.subheader("Generador de Orden de Embarque - Facturación Moreno")


# 1. Función para leer tu matriz CSV directamente desde GitHub
@st.cache_data(ttl=60)
def cargar_csv_github():
  try:
    repo = "RH2026/nexion"
    filename = "facturacion_moreno.csv"
    branch = "main"

    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filename}"
    token = st.secrets["GITHUB_TOKEN"]
    headers = {"Authorization": f"token {token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
      df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
      return df
    else:
      st.error(f"Error al descargar de GitHub (Código {response.status_code}).")
      return pd.DataFrame()
  except Exception as e:
    st.error(f"No se pudo cargar el archivo CSV desde GitHub: {e}")
    return pd.DataFrame()


df_facturacion = cargar_csv_github()

if not df_facturacion.empty:
  df_facturacion["Factura"] = df_facturacion["Factura"].astype(str)

  facturas_disponibles = df_facturacion["Factura"].unique()
  num_factura = st.selectbox(
      "Selecciona o busca el número de Factura:", facturas_disponibles
  )

  registro = df_facturacion[df_facturacion["Factura"] == str(num_factura)].iloc[
      0
  ]

  tipo_pago = st.radio(
      "Selecciona Tipo de Pago:", ["CRÉDITO", "POR COBRAR", "PAGADO"]
  )

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

  # Destinatario (Datos de Entrega) usando Nombre_Cliente y TELEFONO
  destinatario = {
      "cliente": str(registro.get("Nombre_Cliente", "")),
      "rfc": str(registro.get("RFC", "")),
      "calle": str(registro.get("Domicilio", "")),
      "colonia": str(registro.get("Colonia", "")),
      "municipio": f"{registro.get('Cuidad', '')} - CP: {registro.get('CP', '')}",
      "estado": str(registro.get("Estado", "")),
      "contacto": str(registro.get("Nombre_Cliente", "")),
      "telefono": str(registro.get("TELEFONO", "No registrado")),
  }

  # Lógica de Facturación
  if tipo_pago == "CRÉDITO":
    facturacion = remitente
    credito_mark = "X"
    por_cobrar_mark = ""
    pagado_mark = ""
  else:
    # Si es Cobro Destino, usamos la columna Nombre_Extran para la Razón Social / datos fiscales
    fiscal_crudo = str(registro.get("FISCAL", ""))
    fiscal_limpio = (
        fiscal_crudo.replace("_x000D_", " ")
        .replace("\r", " ")
        .replace("\n", " ")
    )
    razon_social_extran = str(registro.get("Nombre_Extran", ""))
    rfc_fiscal = str(registro.get("RFC", ""))

    facturacion = {
        "cliente": razon_social_extran,  # Razón Social exacta desde Nombre_Extran
        "rfc": rfc_fiscal,
        "calle": fiscal_limpio,  # Domicilio fiscal limpio
        "colonia": "",
        "municipio": "",
        "estado": "",
        "email": "sbomailer@jypesa.com",
    }
    credito_mark = ""
    por_cobrar_mark = "X" if tipo_pago == "POR COBRAR" else ""
    pagado_mark = "X" if tipo_pago == "PAGADO" else ""

  fecha_actual = datetime.now().strftime("%d/%m/%Y")


  # --- FUNCIÓN DE GENERACIÓN PDF (ReportLab) ---
  def generar_pdf_reportlab():
    buffer = BytesIO()
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
        alignment=2,
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
        alignment=1,
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

    # Encabezado
    header_data = [
        [
            Paragraph("PAQMEX S.A. DE C.V.", title_style),
            Paragraph("PaqMex", logo_style),
        ],
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

    # Fecha y Factura
    meta_data = [
        [
            "",
            Paragraph(
                "<b>FECHA:</b>", ParagraphStyle("R", alignment=2, fontSize=9)
            ),
            Paragraph(
                f"<b>{fecha_actual}</b>",
                ParagraphStyle("C", alignment=1, fontSize=9),
            ),
        ],
        [
            "",
            Paragraph(
                "<b>FACTURA:</b>", ParagraphStyle("R", alignment=2, fontSize=9)
            ),
            Paragraph(
                f"<b>{num_factura}</b>",
                ParagraphStyle("C", alignment=1, fontSize=9),
            ),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[350, 100, 104])
    t_meta.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (2, 0), (2, 0), 1, colors.black),
            ("LINEBELOW", (2, 1), (2, 1), 1, colors.black),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )
    story.append(t_meta)
    story.append(Spacer(1, 6))

    # Remitente y Destinatario
    rem_data = [
        [Paragraph("REMITENTE", th_style), ""],
        [
            Paragraph("CLIENTE:", cell_bold),
            Paragraph(remitente["cliente"], cell_bold),
        ],
        [Paragraph("RFC:", cell_bold), Paragraph(remitente["rfc"], cell_normal)],
        [
            Paragraph("CALLE:", cell_bold),
            Paragraph(remitente["calle"], cell_normal),
        ],
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
        [
            Paragraph("RFC:", cell_bold),
            Paragraph(destinatario["rfc"], cell_normal),
        ],
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
                f"{destinatario['municipio']} &nbsp;&nbsp; {destinatario['estado']}",
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

    # Facturación (Con Nombre_Extran)
    fac_data = [
        [Paragraph("FACTURACION", th_style), ""],
        [
            Paragraph("CLIENTE:", cell_bold),
            Paragraph(facturacion["cliente"], cell_bold),
        ],
        [
            Paragraph("DATOS / RFC:", cell_bold),
            Paragraph(
                f"{facturacion.get('calle', '')}<br/><b>RFC: {facturacion['rfc']}</b>",
                cell_normal,
            ),
        ],
        [
            Paragraph("EMAIL:", cell_bold),
            Paragraph(
                facturacion.get("email", "sbomailer@jypesa.com"), cell_normal
            ),
        ],
    ]
    t_fac = Table(fac_data, colWidths=[70, 202])
    t_fac.setStyle(
        TableStyle([
            ("SPAN", (0, 0), (1, 0)),
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#6c8ebf")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    serv_data = [
        [Paragraph("SERVICIOS", th_style), "", "", ""],
        [
            Paragraph("PAGADO:", cell_bold),
            pagado_mark,
            Paragraph("SEGURO:", cell_bold),
            "SI: X   NO:",
        ],
        [
            Paragraph("POR COBRAR:", cell_bold),
            por_cobrar_mark,
            Paragraph("VALOR DECLARADO:", cell_bold),
            "",
        ],
        [Paragraph("CREDITO:", cell_bold), credito_mark, "", ""],
        [
            Paragraph("OCURRE:", cell_bold),
            "",
            Paragraph("CITA :", cell_bold),
            "SI [ &nbsp; ] NO",
        ],
        [
            Paragraph("A DOMICILIO:", cell_bold),
            "X",
            Paragraph("CONTACTO:<br/>TELEFONO:", cell_bold),
            "",
        ],
        [Paragraph("MANIOBRAS:", cell_bold), "", "", ""],
    ]
    t_serv = Table(serv_data, colWidths=[70, 45, 85, 72])
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
            ("ALIGN", (1, 1), (1, 3), "CENTER"),
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

    # Contenido
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
    for i in range(1, 5):
      cont_data.append([str(i), "", "", "", "", "", ""])

    t_cont = Table(cont_data, colWidths=[25, 60, 80, 164, 155, 50, 64])
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

    # Carta Porte
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

    # Firmas
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

  if st.button("Generar PDF con datos de CSV"):
    pdf_buffer = generar_pdf_reportlab()
    st.success(
        f"¡Orden de embarque para la factura {num_factura} generada con"
        " éxito!"
    )
    st.download_button(
        label="📥 Descargar PDF de Orden de Embarque",
        data=pdf_buffer,
        file_name=f"Orden_Embarque_{num_factura}.pdf",
        mime="application/pdf",
    )
else:
  st.warning("No se encontraron datos en el CSV de GitHub.")













































































































































