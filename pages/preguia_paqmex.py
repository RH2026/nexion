import base64
from datetime import datetime
from io import BytesIO
import requests
import streamlit as st
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Preguia PaqMex",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="FORMATOS", submodulo_actual="PREGUIA PAQMEX")

# ============================================================
# 3. LÓGICA DE NEGOCIO Y DATOS (GITHUB)
# ============================================================

@st.cache_data(ttl=10)
def cargar_csv_github():
    try:
        repo = "RH2026/nexion"
        filename = "facturacion.csv"
        branch = "main"
        
        token = st.secrets["GITHUB_TOKEN"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        url = f"https://api.github.com/repos/{repo}/contents/{filename}?ref={branch}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            file_info = response.json()
            download_url = file_info.get("download_url")
            if download_url:
                resp_download = requests.get(download_url, headers={"Authorization": f"token {token}"})
                if resp_download.status_code == 200:
                    df = pd.read_csv(BytesIO(resp_download.content), encoding="utf-8-sig")
                    df.columns = df.columns.astype(str).str.strip()
                    return df
            
            st.error("⚠️ No se pudo obtener la URL de descarga directa del archivo grande.")
            return pd.DataFrame()
        else:
            st.error(f"⚠️ Error en la API de GitHub (Código {response.status_code}).")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Excepción capturada al cargar CSV: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def obtener_logo_github():
    try:
        repo = "RH2026/nexion"
        filename = "paqmex.jpg"
        branch = "main"
        
        token = st.secrets["GITHUB_TOKEN"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        url = f"https://api.github.com/repos/{repo}/contents/{filename}?ref={branch}"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_info = response.json()
            content_bytes = base64.b64decode(file_info["content"])
            return BytesIO(content_bytes)
        return None
    except Exception:
        return None


df_facturacion = cargar_csv_github()

if not df_facturacion.empty:
    df_facturacion["Factura"] = df_facturacion["Factura"].astype(str)
    facturas_disponibles = df_facturacion["Factura"].unique()

    # --- SECCIÓN SUPERIOR DE CONFIGURACIÓN Y SELECCIÓN EN 3 COLUMNAS ---
    c_col1, c_col2, c_col3 = st.columns(3)

    with c_col1:
        modo_busqueda = st.selectbox(
            "🔍 Método de Selección", 
            ["Seleccionar de la lista", "Escribir folio manual"]
        )

    with c_col2:
        if modo_busqueda == "Seleccionar de la lista":
            num_factura = st.selectbox(
                "📦 Selecciona Factura / Folio", facturas_disponibles
            )
            if not df_facturacion.empty and num_factura in facturas_disponibles:
                registro = df_facturacion[
                    df_facturacion["Factura"] == str(num_factura)
                ].iloc[0]
            else:
                registro = pd.Series()
        else:
            num_factura = st.text_input("✍️ Ingresa Folio Manual")
            if (
                num_factura
                and not df_facturacion.empty
                and str(num_factura) in df_facturacion["Factura"].values
            ):
                registro = df_facturacion[
                    df_facturacion["Factura"] == str(num_factura)
                ].iloc[0]
            else:
                registro = pd.Series()

    with c_col3:
        tipo_pago = st.selectbox(
            "💳 Tipo de Pago", 
            ["CRÉDITO", "POR COBRAR", "PAGADO"]
        )

    # Extracción inteligente de valores con respaldo vacío si es manual
    def_extran = (
        str(registro.get("Nombre_Extran", ""))
        if not registro.empty and pd.notna(registro.get("Nombre_Extran", ""))
        else ""
    )
    def_rfc = (
        str(registro.get("RFC", ""))
        if not registro.empty and pd.notna(registro.get("RFC", ""))
        else ""
    )
    def_dom = (
        str(registro.get("Domicilio", ""))
        if not registro.empty and pd.notna(registro.get("Domicilio", ""))
        else ""
    )
    def_col = (
        str(registro.get("Colonia", ""))
        if not registro.empty and pd.notna(registro.get("Colonia", ""))
        else ""
    )
    def_cui = (
        str(registro.get("Cuidad", ""))
        if not registro.empty and pd.notna(registro.get("Cuidad", ""))
        else ""
    )
    def_cp = (
        str(registro.get("CP", ""))
        if not registro.empty and pd.notna(registro.get("CP", ""))
        else ""
    )
    def_est = (
        str(registro.get("Estado", ""))
        if not registro.empty and pd.notna(registro.get("Estado", ""))
        else ""
    )
    def_cli = (
        str(registro.get("Nombre_Cliente", ""))
        if not registro.empty and pd.notna(registro.get("Nombre_Cliente", ""))
        else ""
    )
    def_fiscal = (
        str(registro.get("FISCAL", ""))
        if not registro.empty and pd.notna(registro.get("FISCAL", ""))
        else ""
    )

    # Buscar teléfono probando variaciones
    tel_val = ""
    if not registro.empty:
        for col_posible in ["TELEFONO", "Telefono", "telefono", "TEL", "Teléfono"]:
            if col_posible in registro and pd.notna(registro[col_posible]):
                tel_val = str(registro[col_posible]).strip()
                break
    if not tel_val or tel_val.lower() == "nan":
        tel_val = ""

    st.markdown("---")
            
    # --- ESTILOS DE TÍTULOS TIPO BARRA ---
    def titulo_seccion(texto, color_fondo="#4169E1"):
        st.markdown(
            f"""
            <div style="
                background-color: {color_fondo}; 
                padding: 10px; 
                border-radius: 5px; 
                text-align: center; 
                color: white; 
                font-weight: bold; 
                font-size: 16px;
                margin-bottom: 15px;">
                {texto}
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- SECCIÓN VISUAL PARA COMPROBAR Y EDITAR DATOS ---
    col1, col2 = st.columns(2)

    with col1:
        titulo_seccion("REMITENTE", color_fondo="#4e73df")
        rem_cliente = st.text_input(
            "Cliente Remitente",
            value="JABONES Y PRODUCTOS ESPECIALIZADOS SA DE CV",
        )
        rem_rfc = st.text_input("RFC Remitente", value="JPE830408B35")
        rem_calle = st.text_input("Calle Remitente", value="Privada del Gallo No. 1525")
        
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            rem_colonia = st.text_input("Colonia Remitente", value="Col La Aurora")
        with r_col2:
            rem_cp = st.text_input("CP Remitente", value="44430")
        
        r_col3, r_col4 = st.columns(2)
        with r_col3:
            rem_mun = st.text_input("Municipio Remitente", value="Guadalajara")
        with r_col4:
            rem_estado = st.text_input("Estado Remitente", value="Jalisco")
        
        r_col5, r_col6 = st.columns(2)
        with r_col5:
            rem_contacto = st.text_input("Contacto Remitente", value="Rigoberto Hernandez")
        with r_col6:
            rem_tel = st.text_input("Teléfono Remitente", value="33 19 75 31 22")

    with col2:
        titulo_seccion("DESTINATARIO / ENTREGA", color_fondo="#4B6B94")
        dest_cliente = st.text_input(
            "Cliente Destino (Comercial)", value=def_extran
        )
        dest_rfc = st.text_input("RFC Destino", value=def_rfc)
        dest_calle = st.text_input("Calle Destino", value=def_dom)
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            dest_colonia = st.text_input("Colonia Destino", value=def_col)
        with d_col2:
            dest_cp = st.text_input("CP Destino", value=def_cp)
        
        d_col3, d_col4 = st.columns(2)
        with d_col3:
            dest_cui = st.text_input("Ciudad Destino", value=def_cui)
        with d_col4:
            dest_estado = st.text_input("Estado Destino", value=def_est)
        
        dest_tel = st.text_input("Teléfono Destino", value=tel_val)

    # Diccionarios base para remitente y destinatario
    remitente = {
        "cliente": rem_cliente,
        "rfc": rem_rfc,
        "calle": rem_calle,
        "colonia": rem_colonia,
        "municipio": rem_mun,
        "estado": rem_estado,
        "contacto": rem_contacto,
        "telefono": rem_tel,
    }

    destinatario = {
        "cliente": dest_cliente,
        "rfc": dest_rfc,
        "calle": dest_calle,
        "colonia": dest_colonia,
        "municipio": f"{dest_cui} - CP: {dest_cp}",
        "estado": dest_estado,
        "telefono": dest_tel if dest_tel else "No registrado",
    }

    # Dirección completa concatenada de Jypesa para Crédito o Pagado
    direccion_jypesa_completa = f"{rem_calle}, {rem_colonia}, {rem_mun}, {rem_estado} - CP: {rem_cp}"

    # Encabezado de Facturación Dinámico según Tipo de Pago
    titulo_seccion("FACTURACIÓN", color_fondo="#4B6B94")
    
    val_cli_fac = remitente["cliente"] if tipo_pago in ["CRÉDITO", "PAGADO"] else def_cli
    val_rfc_fac = remitente["rfc"] if tipo_pago in ["CRÉDITO", "PAGADO"] else def_rfc
    val_calle_fac = direccion_jypesa_completa if tipo_pago in ["CRÉDITO", "PAGADO"] else def_fiscal

    fac_cliente = st.text_input("Cliente de Facturación", value=val_cli_fac)
    fac_rfc = st.text_input("RFC Facturación", value=val_rfc_fac)
    fac_calle = st.text_area(
        "Domicilio Fiscal / Datos Fiscales (FISCAL)",
        value=str(val_calle_fac).replace("_x000D_", " ").replace("\r", " ").replace("\n", " "),
    )

    # Definición de marcas y diccionario final de facturación para el PDF
    if tipo_pago == "CRÉDITO":
        facturacion = {
            "cliente": fac_cliente,
            "rfc": fac_rfc,
            "calle": fac_calle,
            "colonia": "",
            "municipio": "",
            "estado": "",
            "email": "rhernandez@jypesa.com",
        }
        credito_mark = "X"
        por_cobrar_mark = ""
        pagado_mark = ""
    elif tipo_pago == "POR COBRAR":
        facturacion = {
            "cliente": fac_cliente,
            "rfc": fac_rfc,
            "calle": fac_calle,
            "colonia": "",
            "municipio": "",
            "estado": "",
            "email": "",
        }
        credito_mark = ""
        por_cobrar_mark = "X"
        pagado_mark = ""
    else:  # PAGADO
        facturacion = {
            "cliente": fac_cliente,
            "rfc": fac_rfc,
            "calle": fac_calle,
            "colonia": "",
            "municipio": "",
            "estado": "",
            "email": "rhernandez@jypesa.com",
        }
        credito_mark = ""
        por_cobrar_mark = ""
        pagado_mark = "X"


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

        fecha_actual = datetime.now().strftime("%d/%m/%Y")

        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
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

        logo_io = obtener_logo_github()
        if logo_io:
            logo_element = Image(logo_io, width=130, height=45)
        else:
            logo_element = Paragraph(
                "<b>PaqMex</b><br/><font size=6>SOLUCIONES EN LOGÍSTICA</font>",
                ParagraphStyle(
                    "FallbackLogo",
                    parent=styles["Normal"],
                    fontName="Helvetica-BoldOblique",
                    fontSize=16,
                    textColor=colors.HexColor("#003366"),
                    alignment=2,
                ),
            )

        header_data = [
            [Paragraph("PAQMEX S.A. DE C.V.", title_style), logo_element]
        ]
        t_header = Table(header_data, colWidths=[280, 274])
        t_header.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        story.append(t_header)
        story.append(Spacer(1, 10))
        story.append(Paragraph("ORDEN DE EMBARQUE", subtitle_style))
        story.append(Spacer(1, 8))

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
                Paragraph("TELEFONO:", cell_bold),
                Paragraph(destinatario["telefono"], cell_normal),
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

    st.markdown("---")    
    
    st.markdown(
        """
        <style>
        div.stButton > button, div.stDownloadButton > button {
            width: 100%;
            border-radius: 6px;
            font-weight: bold;
            padding: 0.6rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if st.button(":material/print: Generar PDF con datos de Orden de Embarque", use_container_width=True):
        pdf_buffer = generar_pdf_reportlab()
        st.success(
            f"¡Orden de embarque para la factura {num_factura} generada con éxito!"
        )
        st.download_button(
            label=":material/download: Descargar PDF de Orden de Embarque",
            data=pdf_buffer,
            file_name=f"Orden_Embarque_{num_factura}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
else:
    st.warning("No se encontraron datos en el CSV de GitHub.")
