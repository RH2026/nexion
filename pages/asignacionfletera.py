import base64
import io
import re
import time
import unicodedata
import zipfile
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit as st


# ==========================================
# 1. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================


@st.cache_data(ttl=60)
def obtener_matriz_github():
  """Carga la matriz de destinos y fleteras desde GitHub evitando caché obsoleta."""
  url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv?nocache={int(time.time())}"
  try:
    m = pd.read_csv(url)
    m.columns = [str(c).upper().strip() for c in m.columns]
    return m
  except Exception as e:
    st.error(f"Error fatal al conectar con GitHub: {e}")
    return pd.DataFrame()


def guardar_facturacion_moreno(df):
  """Guarda automáticamente el archivo de facturación en el repositorio."""
  try:
    token = st.secrets["GITHUB_TOKEN"]
    repo = "RH2026/nexion"
    filename = "facturacion_moreno.csv"
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"

    csv_content = df.to_csv(index=False).encode("utf-8-sig")
    content_base64 = base64.b64encode(csv_content).decode("utf-8")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    import requests

    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None

    payload = {
        "message": f"Auto-update Facturación: {time.strftime('%Y-%m-%d %H:%M')}",
        "content": content_base64,
        "branch": "main",
    }
    if sha:
      payload["sha"] = sha

    requests.put(url, headers=headers, json=payload)
    return True
  except Exception:
    return False


def limpiar_texto(texto):
  """Normaliza textos para eliminar acentos y caracteres especiales."""
  if pd.isna(texto):
    return ""
  texto = "".join(
      c
      for c in unicodedata.normalize("NFD", str(texto))
      if unicodedata.category(c) != "Mn"
  ).upper()
  texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
  return " ".join(texto.split())


# ==========================================
# 2. FUNCIONES DE GENERACIÓN QR Y PDF
# ==========================================


def generar_qr_imagen(texto_qr):
  """Genera un código QR en memoria y devuelve un buffer de imagen."""
  qr = qrcode.QRCode(version=1, box_size=3, border=1)
  qr.add_data(texto_qr)
  qr.make(fit=True)
  img = qr.make_image(fill_color="black", back_color="white")

  buffer = io.BytesIO()
  img.save(buffer, format="PNG")
  buffer.seek(0)
  return buffer


def generar_sellos_fisicos_con_qr(lista_datos, x, y):
  """Genera el PDF con los sellos físicos (Fletera + QR de Factura/Fecha)."""
  output = PdfWriter()
  for fletera, factura, fecha in lista_datos:
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # 1. Dibujar la Fletera (Lado derecho superior)
    can.setFont("Helvetica-Bold", 11)
    can.drawString(x, y, f"{str(fletera).upper()}")

    # 2. Dibujar el QR compacto abajo del texto de la fletera
    datos_qr = f"FAC: {factura} | FECHA: {fecha}"
    qr_buffer = generar_qr_imagen(datos_qr)
    can.drawImage(
        ImageReader(qr_buffer), x, y - 50, width=40, height=40, mask="auto"
    )

    can.save()
    packet.seek(0)
    output.add_page(PdfReader(packet).pages[0])

  out_io = io.BytesIO()
  output.write(out_io)
  return out_io.getvalue()


def marcar_pdf_digital_con_qr(pdf_file, fletera, factura, fecha, x, y):
  """Superpone el sello con Fletera y QR en un PDF digital existente."""
  packet = io.BytesIO()
  can = canvas.Canvas(packet, pagesize=letter)

  can.setFont("Helvetica-Bold", 11)
  can.drawString(x, y, f"{str(fletera).upper()}")

  datos_qr = f"FAC: {factura} | FECHA: {fecha}"
  qr_buffer = generar_qr_imagen(datos_qr)
  can.drawImage(
      ImageReader(qr_buffer), x, y - 50, width=40, height=40, mask="auto"
  )

  can.save()
  packet.seek(0)

  new_pdf = PdfReader(packet)
  existing_pdf = PdfReader(pdf_file)
  output = PdfWriter()

  page = existing_pdf.pages[0]
  page.merge_page(new_pdf.pages[0])
  output.add_page(page)

  for i in range(1, len(existing_pdf.pages)):
    output.add_page(existing_pdf.pages[i])

  out_io = io.BytesIO()
  output.write(out_io)
  return out_io.getvalue()


# ==========================================
# 3. INTERFAZ PRINCIPAL (STREAMLIT)
# ==========================================


def main():
  st.set_page_config(
      page_title="Nexion - Módulo de Sellado",
      page_icon="📦",
      layout="wide",
  )

  vars_css = {"sub": "#555555"}

  st.markdown(
      f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px;"
      " font-weight:700;'>S&T PREPARATION MODULE</p>",
      unsafe_allow_html=True,
  )

  uploaded_file = st.file_uploader(
      "Subir archivo ERP", type=["xlsx", "csv"], label_visibility="collapsed"
  )

  if uploaded_file is not None:
    try:
      df = (
          pd.read_csv(uploaded_file, sep=None, engine="python")
          if uploaded_file.name.endswith(".csv")
          else pd.read_excel(uploaded_file)
      )

      df.columns = [str(c).strip().replace("\n", "") for c in df.columns]
      col_folio = next(
          (
              c
              for c in df.columns
              if "factura" in c.lower()
              or "docnum" in c.lower()
              or "folio" in c.lower()
          ),
          df.columns[0],
      )
      df[col_folio] = pd.to_numeric(df[col_folio], errors="coerce")

      col_left, col_right = st.columns([1, 2], gap="large")

      with col_left:
        st.markdown(
            "<p class='op-query-text'>FILTROS</p>", unsafe_allow_html=True
        )
        folios_manuales = st.text_input(
            "Folios específicos (separados por coma):",
            placeholder="Ej: 1001, 1002, 1005",
        )

        serie = df[col_folio].dropna()
        inicio = st.number_input(
            "Desde:", value=int(serie.min()) if not serie.empty else 0
        )
        final = st.number_input(
            "Hasta:", value=int(serie.max()) if not serie.empty else 0
        )

        if folios_manuales:
          lista_manual = [
              int(x.strip())
              for x in folios_manuales.split(",")
              if x.strip().isdigit()
          ]
          df_rango = df[df[col_folio].isin(lista_manual)].copy()
        else:
          df_rango = df[
              (df[col_folio] >= inicio) & (df[col_folio] <= final)
          ].copy()

      with col_right:
        st.markdown(
            "<p class='op-query-text'>SELECCIÓN</p>", unsafe_allow_html=True
        )
        if not df_rango.empty:
          info = df_rango.drop_duplicates(subset=[col_folio])[[col_folio]]
          info.insert(0, "Incluir", True)
          edited_df = st.data_editor(
              info, hide_index=True, use_container_width=True, key="ed_v4"
          )
        else:
          st.warning("Rango vacío")
          edited_df = pd.DataFrame()

      if not df_rango.empty and not edited_df.empty:
        folios_ok = edited_df[edited_df["Incluir"] == True][
            col_folio
        ].tolist()

        st.markdown("---")
        if st.button(
            ":material/play_circle: RENDERIZAR TABLA", use_container_width=True
        ):
          st.session_state.df_final_st = df_rango[
              df_rango[col_folio].isin(folios_ok)
          ]

        if "df_final_st" in st.session_state:
          df_st = st.session_state.df_final_st
          st.dataframe(df_st, use_container_width=True)

          towrite = io.BytesIO()
          df_st.to_excel(towrite, index=False, engine="openpyxl")
          st.download_button(
              label=":material/download: DESCARGAR S&T",
              data=towrite.getvalue(),
              file_name="ST_DATA.xlsx",
              use_container_width=True,
          )

          if st.button(
              ":material/join_inner: SMART ROUTING (MOTOR DE ASIGNACIÓN)",
              type="primary",
              use_container_width=True,
          ):
            try:
              df_log = df_st.drop_duplicates(subset=[col_folio]).copy()
              matriz_db = obtener_matriz_github()

              col_dir_erp = next(
                  (c for c in df_log.columns if "DIRECCION" in c.upper()), None
              )
              col_dest_matriz = (
                  "DESTINO"
                  if "DESTINO" in matriz_db.columns
                  else matriz_db.columns[0]
              )
              col_flet_matriz = (
                  "TRANSPORTE"
                  if "TRANSPORTE" in matriz_db.columns
                  else "FLETERA"
              )
              col_tarifa_matriz = (
                  "PRECIO POR CAJA"
                  if "PRECIO POR CAJA" in matriz_db.columns
                  else "COSTO"
              )

              def motor_v4(row):
                if not col_dir_erp:
                  return "ERROR: COL DIRECCION", 0.0
                dir_limpia = limpiar_texto(row[col_dir_erp])
                if any(
                    loc in dir_limpia
                    for loc in [
                        "GDL",
                        "GUADALAJARA",
                        "ZAPOPAN",
                        "TLAQUEPAQUE",
                        "TONALA",
                        "TLAJOMULCO",
                    ]
                ):
                  return "LOCAL", 0.0
                for _, fila in matriz_db.iterrows():
                  dest_key = limpiar_texto(fila[col_dest_matriz])
                  if dest_key and (dest_key in dir_limpia):
                    flet = fila.get(col_flet_matriz, "ASIGNADO")
                    costo_val = pd.to_numeric(
                        fila.get(col_tarifa_matriz, 0.0), errors="coerce"
                    )
                    return flet, costo_val
                return "REVISIÓN MANUAL", 0.0

              res = df_log.apply(motor_v4, axis=1)
              df_log["RECOMENDACION"] = [r[0] for r in res]
              df_log["COSTO"] = [r[1] for r in res]

              df_log = df_log.rename(columns={col_folio: "Factura"})
              cols_deseadas = [
                  "Factura",
                  "RECOMENDACION",
                  "Transporte",
                  "DIRECCION",
                  "COSTO",
                  "Nombre_Cliente",
                  "Nombre_Extran",
                  "Quantity",
                  "DESTINO",
              ]
              cols_finales = [c for c in cols_deseadas if c in df_log.columns]

              st.session_state.df_analisis = df_log[cols_finales]
              st.success("¡Motor sincronizado con datos recientes!")
              st.rerun()

            except Exception as e:
              st.error(f"Error en el motor de asignación: {e}")

    except Exception as e:
      st.error(f"Error procesando el archivo ERP: {e}")

  # ==========================================
  # BLOQUE 2: LOGISTICS INTELLIGENCE & SELLADO
  # ==========================================
  if "df_analisis" in st.session_state:
    st.markdown("---")
    st.markdown(
        f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px;"
        " font-weight:700;'>LOGISTICS INTELLIGENCE HUB</p>",
        unsafe_allow_html=True,
    )

    p = st.session_state.df_analisis.copy()
    p.columns = [str(c) for c in p.columns]

    if p.columns.duplicated().any():
      cols = []
      for i, col in enumerate(p.columns):
        cols.append(f"{col}_{i}" if col in cols else col)
      p.columns = cols

    p = p.loc[:, ~p.columns.isna()]
    modo_edicion = st.toggle("HABILITAR EDICIÓN MANUAL")

    p_editado = st.data_editor(
        p,
        use_container_width=True,
        hide_index=True,
        column_config={
            "RECOMENDACION": st.column_config.TextColumn(
                "FLETERA", disabled=not modo_edicion
            ),
            "COSTO": st.column_config.NumberColumn(
                "TARIFA", format="$%.2f", disabled=not modo_edicion
            ),
        },
        key="editor_final_github",
    )

    if st.button(
        ":material/save_as: FIJAR CAMBIOS",
        use_container_width=True,
        type="primary",
    ):
      st.session_state.df_analisis = p_editado
      st.toast("Cambios guardados", icon="✅")

    output_xlsx = io.BytesIO()
    p_editado.to_excel(output_xlsx, index=False, engine="openpyxl")
    st.download_button(
        label=":material/download: DESCARGAR ANÁLISIS",
        data=output_xlsx.getvalue(),
        file_name="Analisis_Final.xlsx",
        use_container_width=True,
        type="primary",
    )

    with st.expander("SISTEMA DE SELLADO", expanded=False):
      cx, cy = st.columns(2)
      ax = cx.slider("X", 0, 612, 399)
      ay = cy.slider("Y", 0, 792, 760)

      col_fecha_erp = next(
          (
              c
              for c in p_editado.columns
              if "FECHA" in c.upper() or "DATE" in c.upper()
          ),
          None,
      )
      fecha_default = time.strftime("%Y-%m-%d")

      lista_datos_sellado = []
      for _, row in p_editado.iterrows():
        flet = row.get("RECOMENDACION", "SIN ASIGNAR")
        fac = row.get("Factura", "S/N")
        fec = (
            str(row.get(col_fecha_erp, fecha_default))
            if col_fecha_erp
            else fecha_default
        )
        lista_datos_sellado.append((flet, fac, fec))

      st.markdown("###### :material/print: Opciones de Impresión Física con QR")
      s1, s2 = st.columns(2)

      with s1:
        st.download_button(
            label=":material/print: GENERAR SELLOS NORMAL + QR",
            data=generar_sellos_fisicos_con_qr(lista_datos_sellado, ax, ay),
            file_name="Sellos_Normales_QR.pdf",
            use_container_width=True,
            type="primary",
        )

      with s2:
        lista_inversa = lista_datos_sellado[::-1]
        st.download_button(
            label=":material/swap_vert: GENERAR SELLOS INVERSO + QR",
            data=generar_sellos_fisicos_con_qr(lista_inversa, ax, ay),
            file_name="Sellos_Inversos_QR.pdf",
            use_container_width=True,
            type="primary",
        )

      st.markdown("---")
      st.markdown("###### :material/devices: Opciones de Sellado Digital con QR")
      pdfs = st.file_uploader(
          ":material/picture_as_pdf: Subir Facturas (PDF)",
          type="pdf",
          accept_multiple_files=True,
          key="pdf_uploader_qr",
      )

      if pdfs:
        if st.button("EJECUTAR SELLADO DIGITAL CON QR", use_container_width=True):
          mapa_datos = {
              str(row["Factura"]): (
                  row["RECOMENDACION"],
                  str(row.get(col_fecha_erp, fecha_default))
                  if col_fecha_erp
                  else fecha_default,
              )
              for _, row in p_editado.iterrows()
          }

          z_io = io.BytesIO()
          with zipfile.ZipFile(z_io, "a") as zf:
            for pdf in pdfs:
              f_id = next(
                  (k for k in mapa_datos.keys() if k in pdf.name.upper()), None
              )
              if f_id:
                flet_val, fec_val = mapa_datos[f_id]
                pdf_marcado = marcar_pdf_digital_con_qr(
                    pdf, flet_val, f_id, fec_val, ax, ay
                )
                zf.writestr(f"SELLADO_QR_{pdf.name}", pdf_marcado)

          st.download_button(
              label=":material/folder_zip: DESCARGAR ZIP CON QR",
              data=z_io.getvalue(),
              file_name="Sellado_QR.zip",
              use_container_width=True,
              type="primary",
          )


if __name__ == "__main__":
  main()
