import base64
from datetime import datetime
from io import BytesIO
import io
import json
import re
import time

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image

from components.layout import render_layout


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Formato de Recolecciones 3G",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="FORMATOS", submodulo_actual="RECOLECCION 3G")


#----registra usuario------
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

def registrar_acceso_github(usuario, modulo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/auditoria_accesos.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if r.status_code == 200:
        file_data = r.json()
        sha = file_data.get("sha", "")
        content_decoded = base64.b64decode(file_data.get("content", "")).decode("utf-8")
        df_aud = pd.read_csv(io.StringIO(content_decoded))
    else:
        df_aud = pd.DataFrame(columns=["FECHA_HORA", "USUARIO", "MODULO"])
        sha = ""

    nuevo_registro = pd.DataFrame([{"FECHA_HORA": fecha_hora, "USUARIO": usuario, "MODULO": modulo}])
    df_aud = pd.concat([df_aud, nuevo_registro], ignore_index=True)
    
    csv_string = df_aud.to_csv(index=False)
    payload = {
        "message": f"Registro de acceso de {usuario} al módulo {modulo}",
        "content": base64.b64encode(csv_string.encode()).decode()
    }
    if sha:
        payload["sha"] = sha
        
    requests.put(url, json=payload, headers=headers)


# ==========================================
# 3. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================
def cargar_estatus_github():
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/recolecciones_estatus.csv"
        token = st.secrets["GITHUB_TOKEN"]
        headers = {"Authorization": f"token {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
            df.columns = df.columns.astype(str).str.strip()
            return df
        else:
            return pd.DataFrame(columns=["Folio", "Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total", "Estatus", "Observaciones", "Solicitante", "Numero de Guia", "Costo de la Guia"])
    except Exception:
        return pd.DataFrame(columns=["Folio", "Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total", "Estatus", "Observaciones", "Solicitante", "Numero de Guia", "Costo de la Guia"])

def guardar_estatus_github(df_nuevo, mensaje="Actualizar estatus de recolecciones"):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/recolecciones_estatus.csv"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        response_get = requests.get(url, headers=headers)
        sha = response_get.json().get("sha") if response_get.status_code == 200 else None

        csv_buffer = df_nuevo.to_csv(index=False, encoding="utf-8-sig")
        content_encoded = base64.b64encode(csv_buffer.encode("utf-8")).decode("utf-8")

        payload = {
            "message": mensaje,
            "content": content_encoded,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        response_put = requests.put(url, headers=headers, json=payload)
        return response_put.status_code in [200, 201]
    except Exception:
        return False


# ==========================================
# 4. INTERFAZ PRINCIPAL
# ==========================================
def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True
    
    st.markdown("""
    <style>
        div.stButton > button,
        div.stButton > button:link,
        div.stButton > button:visited {
            background-color: #2B343B !important; 
            color: #FFFFFF !important;             
            border: 1px solid #2B343B !important; 
            border-radius: 5px !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            box-shadow: none !important;
        }
        
        div.stButton > button:hover,
        div.stButton > button:focus {
            background-color: #00A3A3 !important; 
            color: #FFFFFF !important;             
            border-color: #00A3A3 !important;
            box-shadow: none !important;
        }
        
        div.stButton > button:active {
            background-color: #00A3A3 !important;
            border-color: #00A3A3 !important;
            color: #FFFFFF !important;
        }
    </style>
""", unsafe_allow_html=True)

    @st.cache_data(ttl=300)
    def obtener_logo_tresguerras():
        try:
            url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/logo_3G.png"
            token = st.secrets["GITHUB_TOKEN"]
            headers = {"Authorization": f"token {token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return BytesIO(response.content)
            return None
        except Exception:
            return None

    @st.cache_data(ttl=60)
    def cargar_matriz_facturacion_completa():
        try:
            url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/clientes.csv"
            token = st.secrets["GITHUB_TOKEN"]
            headers = {"Authorization": f"token {token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig")
                df.columns = [str(c).upper().strip() for c in df.columns]
                return df
            else:
                return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    df_facturacion = cargar_matriz_facturacion_completa()
    registro = pd.Series()    

    if not df_facturacion.empty:
        df_facturacion.columns = [str(c).upper().strip() for c in df_facturacion.columns]
        
        col_cliente_num = "CLIENTE" if "CLIENTE" in df_facturacion.columns else None
        col_nombre_hotel = "NOMBRE_EXTRAN" if "NOMBRE_EXTRAN" in df_facturacion.columns else None

        if col_cliente_num:
            df_facturacion[col_cliente_num] = df_facturacion[col_cliente_num].astype(str)

        top_col1, top_col2, top_col3, top_col4 = st.columns(4)
        
        with top_col1:
            fecha_recoleccion_deseada = st.date_input("📅 Fecha Recolección", value=datetime.now(), key="tg_fecha_rec")
        fecha_rec_str = fecha_recoleccion_deseada.strftime("%d/%m/%Y")

        with top_col2:
            if col_cliente_num:
                clientes_disponibles = sorted(df_facturacion[col_cliente_num].dropna().unique().tolist())
                cliente_elegido = st.selectbox("Selecciona No. Cliente", clientes_disponibles, key="tg_sel_cte")
                
                if cliente_elegido:
                    match_cte = df_facturacion[df_facturacion[col_cliente_num] == str(cliente_elegido)]
                    if not match_cte.empty:
                        registro = match_cte.iloc[0]

        with top_col3:
            num_factura = st.text_input("✍️ Folio / Referencia", value="S/F", key="tg_txt_fact_nuevo")

        with top_col4:
            tipo_pago_tg = st.selectbox("💳 Condición de Pago", ["POR COBRAR (DESTINO)", "PAGADO (ORIGEN)", "CRÉDITO"], key="tg_tipo_pago")

        def_extran = str(registro.get(col_nombre_hotel, "")) if not registro.empty and col_nombre_hotel and pd.notna(registro.get(col_nombre_hotel, "")) else ""
        def_dom = str(registro.get("DOMICILIO", registro.get("CALLE", ""))) if not registro.empty and pd.notna(registro.get("DOMICILIO", registro.get("CALLE", ""))) else ""
        def_col = str(registro.get("COLONIA", "")) if not registro.empty and pd.notna(registro.get("COLONIA", "")) else ""
        def_cui = str(registro.get("CUIDAD", registro.get("CIUDAD", ""))) if not registro.empty and pd.notna(registro.get("CUIDAD", registro.get("CIUDAD", ""))) else ""
        def_cp = str(registro.get("CP", "")) if not registro.empty and pd.notna(registro.get("CP", "")) else ""
        def_est = str(registro.get("ESTADO", "")) if not registro.empty and pd.notna(registro.get("ESTADO", "")) else ""

        tel_val = ""
        if not registro.empty:
            for col_p in ["TELEFONO", "TEL", "TELÉFONO"]:
                if col_p in registro and pd.notna(registro[col_p]):
                    tel_val = str(registro[col_p]).strip()
                    break

        st.markdown("---")

        def titulo_seccion(texto, color_fondo="#b71c1c"):
            st.markdown(f"""
                <div style="background-color: {color_fondo}; padding: 8px; border-radius: 4px; text-align: center; color: white; font-weight: bold; font-size: 15px; margin-bottom: 10px;">
                    {texto}
                </div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            titulo_seccion("REMITENTE - RECOLECCIÓN (PROVEEDOR)", color_fondo="#e65100")
            rem_cliente = st.text_input("Comercializadora / Proveedor", value=def_extran, key=f"rem_cli_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            rem_calle = st.text_input("Calle y Número (Remitente)", value=def_dom, key=f"rem_call_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            rc1, rc2 = st.columns(2)
            with rc1:
                rem_colonia = st.text_input("Colonia (Remitente)", value=def_col, key=f"rem_col_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            with rc2:
                rem_cp = st.text_input("CP (Remitente)", value=def_cp, key=f"rem_cp_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            rc3, rc4 = st.columns(2)
            with rc3:
                rem_cui = st.text_input("Ciudad / Municipio", value=def_cui, key=f"rem_cui_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            with rc4:
                rem_estado = st.text_input("Estado", value=def_est, key=f"rem_est_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            rc5, rc6 = st.columns(2)
            with rc5:
                rem_contacto = st.text_input("Persona que entrega", value="", key=f"rem_cont_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            with rc6:
                rem_tel = st.text_input("Teléfono Remitente", value=tel_val, key=f"rem_tel_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")

        with col2:
            titulo_seccion("DESTINATARIO - ENTREGA (JYPESA)", color_fondo="#4B6B94")
            dest_cliente = st.text_input("Cliente Destino", value="Jabones y productos Especializados", key=f"dest_cli_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            dest_calle = st.text_input("Calle Destino", value="C. Cernícalo 155", key=f"dest_call_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            dc1, dc2 = st.columns(2)
            with dc1:
                dest_colonia = st.text_input("Colonia Destino", value="La Aurora", key=f"dest_col_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            with dc2:
                dest_cp = st.text_input("CP Destino", value="44460", key=f"dest_cp_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            dc3, dc4 = st.columns(2)
            with dc3:
                dest_cui = st.text_input("Ciudad Destino", value="Guadalajara", key=f"dest_cui_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            with dc4:
                dest_estado = st.text_input("Estado Destino", value="Jalisco", key=f"dest_est_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            dc5, dc6 = st.columns(2)
            with dc5:
                dest_contacto = st.text_input("Persona que recibe", value="Jazmin Castillo", key=f"dest_cont_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
            with dc6:
                dest_tel = st.text_input("Teléfono Destino", value="33 3540 2939 Ext.123", key=f"dest_tel_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")

        titulo_seccion("FACTURAR A (DATOS FISCALES JYPESA)", color_fondo="#37474f")
        fac_cliente = st.text_input("Facturar a Nombre de", value="JABONES Y PRODUCTOS ESPECIALIZADOS SA DE CV", key=f"fac_cli_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
        fac_domicilio = st.text_input("Domicilio Fiscal", value="Privada del Gallo No. 1525, Col. La Aurora C.P. 44460 Guadalajara, JAL México", key=f"fac_dom_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")
        fac_rfc = st.text_input("RFC Facturación", value="JPE830408B35", key=f"fac_rfc_{cliente_elegido if 'cliente_elegido' in locals() else 'gen'}")

        st.markdown("---")
        titulo_seccion("📦 DETALLE DE EMBARQUE Y LÍNEAS DE CARGA", color_fondo="#e65100")

        if "lineas_embarque" not in st.session_state:
            st.session_state.lineas_embarque = [
                {"cantidad": 1, "tipo": "TARIMA", "descripcion": "AMENIDADES", "largo": 1.20, "ancho": 1.20, "alto": 2.00, "peso": 800.0}
            ]

        for idx, linea in enumerate(st.session_state.lineas_embarque):
            st.markdown(f"**Renglón {idx + 1}**")
            lc1, lc2, lc3, lc4, lc5, lc6, lc7 = st.columns([1, 2, 2, 1, 1, 1, 1])
            with lc1:
                linea["cantidad"] = st.number_input("Cant.", min_value=1, value=linea["cantidad"], key=f"cant_{idx}")
            with lc2:
                linea["tipo"] = st.selectbox("Tipo Bulto", ["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"], index=["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"].index(linea["tipo"]) if linea["tipo"] in ["TARIMA", "CAJA", "ATADO", "TAMBO", "SACO", "OTRO"] else 0, key=f"tipo_{idx}")
            with lc3:
                linea["descripcion"] = st.text_input("Descripción", value=linea["descripcion"], key=f"desc_{idx}")
            with lc4:
                linea["largo"] = st.number_input("Largo (m)", value=float(linea["largo"]), key=f"larg_{idx}")
            with lc5:
                linea["ancho"] = st.number_input("Ancho (m)", value=float(linea.get("ancho", 1.20)), key=f"anch_{idx}")
            with lc6:
                linea["alto"] = st.number_input("Alto (m)", value=float(linea["alto"]), key=f"alt_{idx}")
            with lc7:
                linea["peso"] = st.number_input("Peso (KG)", value=float(linea["peso"]), key=f"pes_{idx}")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("➕ Agregar otra línea de carga", key="btn_add_line"):
                st.session_state.lineas_embarque.append({"cantidad": 1, "tipo": "CAJA", "descripcion": "MERCANCIA", "largo": 0.50, "ancho": 0.50, "alto": 0.50, "peso": 50.0})
                st.rerun()
        with col_btn2:
            if len(st.session_state.lineas_embarque) > 1 and st.button("🗑️ Eliminar última línea", key="btn_del_line"):
                st.session_state.lineas_embarque.pop()
                st.rerun()

        total_peso_calc = sum(l["peso"] * l["cantidad"] for l in st.session_state.lineas_embarque)
        st.info(f"⚖️ **Peso Total Calculado:** {total_peso_calc:,.2f} KG")

        def generar_pdf_tresguerras_oficial():
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
            story = []
            
            fecha_actual = datetime.now().strftime("%d/%m/%Y")
            
            th_style = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=colors.white, alignment=1)
            cell_bold = ParagraphStyle("CB", fontName="Helvetica-Bold", fontSize=6, leading=7.5)
            cell_normal = ParagraphStyle("CN", fontName="Helvetica", fontSize=6, leading=7.5)
            cell_center = ParagraphStyle("CC", fontName="Helvetica", fontSize=6, leading=7.5, alignment=1)

            logo_io = obtener_logo_tresguerras()
            logo_elem = Image(logo_io, width=85, height=22) if logo_io else Paragraph("<b>TRESGUERRAS</b>", cell_center)
            
            header_table = Table([
                [
                    logo_elem, 
                    Paragraph("<b>AUTOTRANSPORTES DE CARGA TRESGUERRAS<br/>SOLICITUD DE SERVICIO</b>", ParagraphStyle("HT", alignment=1, fontSize=8.5, fontName="Helvetica-Bold")), 
                    Paragraph(f"<b>FECHA SOLICITUD:</b> {fecha_actual}<br/><b>FOLIO:</b> {num_factura}", ParagraphStyle("H2", fontSize=6, alignment=1))
                ],
                ["", Paragraph("PAQUETERIA", ParagraphStyle("PAQ", alignment=1, fontSize=5.5, fontName="Helvetica-Bold")), ""]
            ], colWidths=[105, 382, 115])
            header_table.setStyle(TableStyle([
                ("SPAN", (0,0), (0,1)),
                ("SPAN", (2,0), (2,1)),
                ("GRID", (0,0), (-1,-1), 1, colors.black),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ALIGN", (0,0), (0,0), "CENTER"),
                ("BACKGROUND", (1,0), (1,0), colors.HexColor("#e0e0e0")),
                ("BACKGROUND", (2,0), (2,0), colors.HexColor("#fff59d")),
                ("BACKGROUND", (1,1), (1,1), colors.HexColor("#f5f5f5")),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 2))

            fechas_table = Table([
                [Paragraph("<b>FECHA DE RECOLECCION:</b>", cell_bold), Paragraph(fecha_rec_str, cell_center), Paragraph("<b>FECHA SOLICITUD</b>", cell_bold), Paragraph(fecha_actual, cell_center)],
                [Paragraph("<b>FECHA DE RECEPCION:</b>", cell_bold), "", Paragraph("<b>FOLIO</b>", cell_bold), ""]
            ], colWidths=[110, 150, 105, 237])
            fechas_table.setStyle(TableStyle([
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("BACKGROUND", (1,0), (1,0), colors.HexColor("#fff59d")),
                ("BACKGROUND", (3,0), (3,0), colors.HexColor("#fff59d")),
                ("BACKGROUND", (1,1), (1,1), colors.HexColor("#fff59d")),
                ("BACKGROUND", (3,1), (3,1), colors.HexColor("#fff59d")),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0), (-1,-1), 1.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
            ]))
            story.append(fechas_table)
            story.append(Spacer(1, 2))

            rem_data = [
                [Paragraph("REMITENTE - RECOLECCION", th_style), ""],
                [Paragraph("CLIENTE:", cell_bold), Paragraph(rem_cliente, cell_bold)],
                [Paragraph("CALLE Y NUMERO:", cell_bold), Paragraph(rem_calle, cell_normal)],
                [Paragraph("COLONIA / CP:", cell_bold), Paragraph(f"{rem_colonia} - C.P. {rem_cp}", cell_normal)],
                [Paragraph("CIUDAD / ESTADO:", cell_bold), Paragraph(f"{rem_cui}, {rem_estado}", cell_normal)],
                [Paragraph("CONTACTO / TEL:", cell_bold), Paragraph(f"{rem_contacto} - {rem_tel}", cell_normal)],
            ]
            t_rem = Table(rem_data, colWidths=[90, 211])
            t_rem.setStyle(TableStyle([
                ("SPAN", (0,0), (1,0)),
                ("BACKGROUND", (0,0), (1,0), colors.HexColor("#e65100")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0), (-1,-1), 1.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
            ]))

            dest_data = [
                [Paragraph("DESTINATARIO - ENTREGA", th_style), ""],
                [Paragraph("CLIENTE:", cell_bold), Paragraph(dest_cliente, cell_bold)],
                [Paragraph("CALLE Y NUMERO:", cell_bold), Paragraph(dest_calle, cell_normal)],
                [Paragraph("COLONIA / CP:", cell_bold), Paragraph(f"{dest_colonia} - C.P. {dest_cp}", cell_normal)],
                [Paragraph("CIUDAD / ESTADO:", cell_bold), Paragraph(f"{dest_cui}, {dest_estado}", cell_normal)],
                [Paragraph("CONTACTO / TEL:", cell_bold), Paragraph(f"{dest_contacto} - {dest_tel}", cell_normal)],
            ]
            t_dest = Table(dest_data, colWidths=[90, 211])
            t_dest.setStyle(TableStyle([
                ("SPAN", (0,0), (1,0)),
                ("BACKGROUND", (0,0), (1,0), colors.black),
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0), (-1,-1), 1.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
            ]))

            t_top = Table([[t_rem, t_dest]], colWidths=[301, 301])
            story.append(t_top)
            story.append(Spacer(1, 2))

            fac_data = [
                [Paragraph("<b>FACTURAR A:</b>", th_style), "", ""],
                [Paragraph(fac_cliente, cell_center), "", ""],
                [Paragraph("<b>DOMICILIO:</b>", cell_bold), Paragraph("Cel. 33 19 75 31 22", cell_center), ""],
                [Paragraph(f"Privada del Gallo No. 1525, Col. La Aurora C.P. 44460 Guadalajara, JAL México<br/>Tel.. 0152 (33) 35402939<br/>E-mail: rhernandez@jypesa.com", ParagraphStyle("FD", alignment=1, fontSize=6, fontName="Helvetica", leading=7.5)), "", ""],
                [Paragraph("<b>RFC:</b>", cell_bold), Paragraph(f"RFC {fac_rfc}", cell_center), ""]
            ]
            t_fac = Table(fac_data, colWidths=[75, 427, 100])
            t_fac.setStyle(TableStyle([
                ("SPAN", (0,0), (2,0)),
                ("SPAN", (0,1), (2,1)),
                ("SPAN", (1,2), (2,2)),
                ("SPAN", (0,3), (2,3)),
                ("SPAN", (1,4), (2,4)),
                ("BACKGROUND", (0,0), (2,0), colors.HexColor("#b71c1c")),
                ("BACKGROUND", (0,1), (2,1), colors.HexColor("#fff59d")),
                ("BACKGROUND", (0,2), (0,2), colors.HexColor("#b71c1c")),
                ("TEXTCOLOR", (0,2), (0,2), colors.white),
                ("BACKGROUND", (1,2), (2,2), colors.HexColor("#ffffff")),
                ("BACKGROUND", (0,3), (2,3), colors.HexColor("#fff59d")),
                ("BACKGROUND", (0,4), (2,4), colors.HexColor("#b71c1c")),
                ("TEXTCOLOR", (0,4), (2,4), colors.white),
                ("BACKGROUND", (1,4), (2,4), colors.HexColor("#fff59d")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING", (0,0), (-1,-1), 1.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
            ]))
            story.append(t_fac)
            story.append(Spacer(1, 2))

            emb_headers = ["Cantidad", "TIPO DE BULTOS", "DESCRIPCION", "DIAMETRO", "ALTO", "CUBICAJE (m3)", "PESO (KG)"]
            emb_data = [
                [Paragraph("<b>INFORMACION DE EMBARQUE</b>", th_style), "", "", Paragraph("<b>DIMENSIONES (mts)</b>", th_style), "", Paragraph("<b>VOLUMEN</b>", th_style), Paragraph("<b>PESO POR BULTO</b>", th_style)],
                [Paragraph(h, th_style) for h in emb_headers]
            ]

            for l in st.session_state.lineas_embarque:
                ancho_val = l.get('ancho', 1.20)
                dim_str = f"{l['largo']} x {ancho_val} x {l['alto']}"
                emb_data.append([
                    str(l["cantidad"]), 
                    str(l["tipo"]), 
                    str(l["descripcion"]), 
                    str(dim_str), 
                    "", 
                    "0", 
                    str(l["peso"])
                ])

            filas_actuales = len(st.session_state.lineas_embarque)
            for _ in range(max(0, 6 - filas_actuales)):
                emb_data.append(["", "", "", "", "", "0", ""])
                
            emb_data.append(["", "", "", "", "", "0", f"{total_peso_calc:,.1f}"])

            t_emb = Table(emb_data, colWidths=[45, 65, 182, 95, 65, 80, 70])
            t_emb.setStyle(TableStyle([
                ("SPAN", (0,0), (2,0)),
                ("SPAN", (3,0), (4,0)),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#b71c1c")),
                ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#b71c1c")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("TOPPADDING", (0,0), (-1,-1), 1.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
            ]))
            story.append(t_emb)
            story.append(Spacer(1, 2))

            th_red = ParagraphStyle("THR", fontName="Helvetica-Bold", fontSize=6, leading=7, textColor=colors.white, alignment=1)
            th_green = ParagraphStyle("THG", fontName="Helvetica-Bold", fontSize=6, leading=7, textColor=colors.white, alignment=1)

            mid_table_data = [
                [
                    Paragraph("<b>MERCANCIA ASEGURADA</b>", th_red), 
                    Paragraph("<b>REQUIERE ACUSE DE RECIBO</b>", th_red), 
                    Paragraph("<b>DESCRIPCION DEL ACUSE:</b>", th_red)
                ],
                [
                    Table([
                        [Paragraph("SI", cell_center), "", Paragraph("VALOR DECLARADO", cell_bold)],
                        [Paragraph("NO", cell_center), Paragraph("X", cell_center), Paragraph("POR CUENTA Y RIESGO", cell_bold)]
                    ], colWidths=[30, 30, 85], style=[
                        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#fff59d")),
                        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                        ("TOPPADDING", (0,0), (-1,-1), 1),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                    ]),
                    Table([
                        [Paragraph("SI", cell_center), Paragraph("X", cell_center), Paragraph("N<br/>O", cell_center)],
                        ["", "", ""]
                    ], colWidths=[30, 30, 25], style=[
                        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                        ("TOPPADDING", (0,0), (-1,-1), 1),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                    ]),
                    ""
                ],
                [
                    Paragraph("<b>TIPO DE PAGO MARCAR CON UNA X</b>", th_green), 
                    Paragraph("<b>MARCAR CON UNA X (EAD / OCURRE)</b>", th_green), 
                    Paragraph("<b>DOCUMENTOS QUE ANEXA</b>", th_red)
                ],
                [
                    Table([
                        [Paragraph("pagado (origen)", cell_center), Paragraph("por cobrar (destino)", cell_center), Paragraph("Credito", cell_center)],
                        ["", "", Paragraph("X", cell_center)]
                    ], colWidths=[48, 52, 45], style=[
                        ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                        ("TOPPADDING", (0,0), (-1,-1), 1),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                    ]),
                    Table([
                        [Paragraph("Recolección", cell_center), Paragraph("Recepción", cell_center), Paragraph("Entrega Domicilio", cell_center)],
                        [Paragraph("X", cell_center), "", Paragraph("X", cell_center)]
                    ], colWidths=[48, 45, 62], style=[
                        ("BACKGROUND", (0,1), (0,1), colors.HexColor("#fff59d")),
                        ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                        ("TOPPADDING", (0,0), (-1,-1), 1),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                    ]),
                    Table([
                        [Paragraph("factura", cell_center), Paragraph("orden de compra", cell_center), Paragraph("pedimento", cell_center), Paragraph("otro", cell_center)]
                    ], colWidths=[70, 70, 70, 62], style=[
                        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                        ("TOPPADDING", (0,0), (-1,-1), 4),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                    ])
                ]
            ]

            t_mid = Table(mid_table_data, colWidths=[145, 155, 302])
            t_mid.setStyle(TableStyle([
                ("SPAN", (2,1), (2,1)),
                ("BACKGROUND", (0,0), (0,0), colors.HexColor("#b71c1c")),
                ("BACKGROUND", (1,0), (1,0), colors.HexColor("#b71c1c")),
                ("BACKGROUND", (2,0), (2,0), colors.HexColor("#b71c1c")),
                ("BACKGROUND", (2,1), (2,1), colors.HexColor("#fff59d")),
                ("BACKGROUND", (0,2), (0,2), colors.HexColor("#2e7d32")),
                ("BACKGROUND", (1,2), (1,2), colors.HexColor("#2e7d32")),
                ("BACKGROUND", (2,2), (2,2), colors.HexColor("#b71c1c")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("TOPPADDING", (0,0), (-1,-1), 1),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1),
            ]))
            story.append(t_mid)
            story.append(Spacer(1, 2))

            t_final_block = Table([
                [Paragraph("<b>DATOS DE QUIEN SOLICITA EL SERVICIO</b>", th_style), Paragraph("<b>OBSERVACIONES</b>", th_style)],
                [
                    Table([
                        [Paragraph("<b>NOMBRE:</b>", cell_bold), Paragraph("RIGOBERTO HERNANDEZ", cell_center)],
                        [Paragraph("<b>EMPRESA:</b>", cell_bold), Paragraph("JYPESA", cell_center)],
                        [Paragraph("<b>E-MAIL:</b>", cell_bold), Paragraph("rhernandez@jypesa.com", cell_center)],
                        [Paragraph("<b>TELEFONO:</b>", cell_bold), Paragraph("Cel. 33 19 75 31 22", cell_center)]
                    ], colWidths=[70, 230], style=[
                        ("BACKGROUND", (1,0), (1,-1), colors.HexColor("#fff59d")),
                        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                        ("TOPPADDING", (0,0), (-1,-1), 1.5),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
                    ]),
                    Paragraph("<b>LLAMAR AL REMITENTE UNA HORA ANTES DE LA RECOLECCIÓN,</b> SI NO QUIEREN ENTREGAR LLAMAR AL TELÉFONO<br/>Cel. 33 19 75 31 22 Rigoberto Hernandez", cell_normal)
                ]
            ], colWidths=[300, 302])
            t_final_block.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (0,0), colors.HexColor("#b71c1c")),
                ("BACKGROUND", (1,0), (1,0), colors.HexColor("#b71c1c")),
                ("BACKGROUND", (1,1), (1,1), colors.HexColor("#fff59d")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("TOPPADDING", (0,0), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ]))
            story.append(t_final_block)

            doc.build(story)
            buffer.seek(0)
            return buffer

        st.markdown("---")
        col_gen1, col_gen2 = st.columns(2)
        with col_gen1:
            if st.button("Generar Orden de Recolección (Tresguerras Oficial)", use_container_width=True, key="btn_gen_pdf_tg"):
                pdf_buf = generar_pdf_tresguerras_oficial()
                st.success("¡Formato de Tresguerras generado correctamente!")
                st.download_button(
                    label="📥 Descargar PDF Tresguerras Oficial",
                    data=pdf_buf,
                    file_name=f"Tresguerras_Oficial_{num_factura}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_pdf_tg_btn"
                )
        with col_gen2:
            if st.button("Registrar Folio en Estatus GitHub", use_container_width=True, key="btn_guardar_gh_tab1"):
                df_estatus_actual = cargar_estatus_github()
                nuevo_registro = pd.DataFrame([{
                    "Folio": str(num_factura),
                    "Fecha_Recoleccion": fecha_rec_str,
                    "Cliente": str(dest_cliente),
                    "Proveedor": str(rem_cliente),
                    "Peso_Total": float(total_peso_calc),
                    "Estatus": "PENDIENTE DE RECOLECCION",
                    "Observaciones": "Creado desde solicitud Tresguerras",
                    "Solicitante": "RIGOBERTO HERNANDEZ",
                    "Numero de Guia": "",
                    "Costo de la Guia": 0.0
                }])
                if not df_estatus_actual.empty and str(num_factura) in df_estatus_actual["Folio"].values:
                    df_estatus_actual.loc[df_estatus_actual["Folio"] == str(num_factura), ["Fecha_Recoleccion", "Cliente", "Proveedor", "Peso_Total"]] = [fecha_rec_str, str(dest_cliente), str(rem_cliente), float(total_peso_calc)]
                    df_final = df_estatus_actual
                else:
                    df_final = pd.concat([df_estatus_actual, nuevo_registro], ignore_index=True)
                
                if guardar_estatus_github(df_final, f"Registro de folio {num_factura}"):
                    st.success(f"¡Folio {num_factura} guardado/actualizado exitosamente en GitHub!")
    else:
        st.warning("No se encontraron datos en la matriz de facturación.")

if __name__ == "__main__":
    main()
