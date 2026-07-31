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

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="JYPESA | Logistics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. SISTEMA DE SEGURIDAD PRO (BANNER ESTILO CIBER-SEGURIDAD)
if not st.session_state.get("autenticado", False):
  st.markdown(
      """
        <style>
        @keyframes pulseGlow {
            0% { border-color: rgba(255, 75, 75, 0.4); box-shadow: 0 0 10px rgba(255, 75, 75, 0.1); }
            50% { border-color: rgba(255, 75, 75, 0.9); box-shadow: 0 0 25px rgba(255, 75, 75, 0.3); }
            100% { border-color: rgba(255, 75, 75, 0.4); box-shadow: 0 0 10px rgba(255, 75, 75, 0.1); }
        }
        .security-alert-box {
            background: rgba(30, 39, 46, 0.95);
            border: 1px solid rgba(255, 75, 75, 0.6);
            border-left: 6px solid #ff4b4b;
            border-radius: 12px;
            padding: 25px 30px;
            margin-top: 10vh;
            text-align: center;
            animation: pulseGlow 2s infinite ease-in-out;
            font-family: 'Inter', sans-serif;
        }
        .security-title {
            color: #ff4b4b;
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .security-desc {
            color: #ffffff;
            font-size: 12px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            opacity: 0.8;
            margin-bottom: 0px;
        }
        </style>
        <div class="security-alert-box">
            <div class="security-title">⚡ ACCESS DENIED // SECURITY PROTOCOL ACTIVE</div>
            <div class="security-desc">Credenciales de sesión no detectadas. Redirigiendo al núcleo de autenticación.</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("<br>", unsafe_allow_html=True)
  col_btn1, col_btn2, col_btn3 = st.columns([2, 1.5, 2])
  with col_btn2:
    if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
      st.switch_page("log.py")
  st.stop()

# ── TEMA Y CSS MAESTROS ──────────────────────────────────────────
vars_css = {
    "bg": "#384A52",
    "card": "#2B343B",
    "text": "#FFFFFF",
    "sub": "#FFFFFF",
    "border": "#4B5D67",
    "logo": "n1.png",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* --- OCULTAR ELEMENTOS DE STREAMLIT Y GITHUB --- */
header, footer, [data-testid="stHeader"] {{
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}}

[data-testid="collapsedControl"], [data-testid="stSidebar"], [data-testid="stToolbar"], .viewerBadge_container__1QSob, #MainMenu {{
    visibility: hidden !important;
    display: none !important;
}}

/* APP BASE */
html, body, .stApp {{
    background-color: {vars_css['bg']} !important;
    color: {vars_css['text']} !important;
    font-family: 'Inter', sans-serif !important;
}}

.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 5rem !important;
    background-color: {vars_css['bg']} !important;
}}

/* BOTONES SLIM */
div.stButton > button {{
    background-color: {vars_css['card']} !important;
    color: {vars_css['text']} !important;
    border: 1px solid {vars_css['border']} !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 10px !important;
    height: 34px !important;
    width: 100% !important;
}}

div.stButton > button:hover {{
    background-color: #00A3A3 !important;
    color: #ffffff !important;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 3. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ==========================================
@st.cache_data(ttl=60)
def obtener_matriz_github():
  url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv?nocache={int(time.time())}"
  try:
    m = pd.read_csv(url)
    m.columns = [str(c).upper().strip() for c in m.columns]
    return m
  except Exception as e:
    st.error(f"Error fatal al conectar con GitHub: {e}")
    return pd.DataFrame()


def limpiar_texto(texto):
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
# 4. FUNCIONES DE GENERACIÓN QR Y PDF
# ==========================================
def generar_qr_imagen(texto_qr):
  qr = qrcode.QRCode(version=1, box_size=3, border=1)
  qr.add_data(texto_qr)
  qr.make(fit=True)
  img = qr.make_image(fill_color="black", back_color="white")
  buffer = io.BytesIO()
  img.save(buffer, format="PNG")
  buffer.seek(0)
  return buffer


def generar_sellos_fisicos_con_qr(lista_datos, x, y):
  output = PdfWriter()
  for fletera, factura, fecha in lista_datos:
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 11)
    can.drawString(x, y, f"{str(fletera).upper()}")
    datos_qr = f"FAC: {factura} | FECHA: {fecha}"
    qr_buffer = generar_qr_imagen(datos_qr)
    can.drawImage(
        ImageReader(qr_buffer),
        x + 150,
        y - 35,
        width=45,
        height=45,
        mask="auto",
    )
    can.save()
    packet.seek(0)
    output.add_page(PdfReader(packet).pages[0])
  out_io = io.BytesIO()
  output.write(out_io)
  return out_io.getvalue()


def marcar_pdf_digital_con_qr(pdf_file, fletera, factura, fecha, x, y):
  packet = io.BytesIO()
  can = canvas.Canvas(packet, pagesize=letter)
  can.setFont("Helvetica-Bold", 11)
  can.drawString(x, y, f"{str(fletera).upper()}")
  datos_qr = f"FAC: {factura} | FECHA: {fecha}"
  qr_buffer = generar_qr_imagen(texto_qr=datos_qr)
  can.drawImage(
      ImageReader(qr_buffer), x + 150, y - 35, width=45, height=45, mask="auto"
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


# Inicialización segura de estados de menú si no existen
if "menu_main" not in st.session_state:
  st.session_state.menu_main = "CENTRO DE DATOS"
if "menu_sub" not in st.session_state:
  st.session_state.menu_sub = "ASIGNAR FLETERA"
if "busqueda_activa" not in st.session_state:
  st.session_state.busqueda_activa = False
if "resultado_busqueda" not in st.session_state:
  st.session_state.resultado_busqueda = None
if "search_key_version" not in st.session_state:
  st.session_state.search_key_version = 1

# ==========================================
# 5. HEADER CON 4 COLUMNAS (BÚSQUEDA OPTIMIZADA)
# ==========================================
header_zone = st.container()
with header_zone:
  c1, c2, c3, c4 = st.columns([1.5, 3.5, 0.9, 0.9], vertical_alignment="center")

  with c1:
    try:
      st.image(vars_css["logo"], width=160)
    except Exception:
      st.write("**NEXION**")

  with c2:
    texto_principal = st.session_state.menu_main
    azul_nexion = "#82D4E6"
    oro_brillante = "#FFD700"

    if texto_principal == "DASHBOARD":
      texto_principal = (
          f"NEXION <span style='color: {azul_nexion}; font-weight: 500; margin:"
          " 0 10px; font-size: 16px;'>|</span> SMART LOGISTICS"
      )

    if st.session_state.menu_sub != "GENERAL":
      ruta = (
          f"{texto_principal} "
          f"<span style='color: {azul_nexion}; opacity: 0.8; margin: 0"
          " 15px;'>/</span> "
          f"<span style='color: {oro_brillante}; font-weight: 500;"
          " text-shadow: 0 0 8px rgba(255, 215, 0, 0.6);'>"
          f"{st.session_state.menu_sub}</span>"
      )
    else:
      ruta = texto_principal

    st.markdown(
        f"""
        <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
            <p style='font-size: 13px; letter-spacing: 5px; color: {vars_css['sub']}; margin: 0; font-weight: 500; text-transform: uppercase; text-align: center;'>
                {ruta}
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

  with c3:
    es_atencion3g = (
        st.session_state.get("usuario_activo", "").upper() == "ATENCION3G"
    )
    key_actual = f"main_search_v{st.session_state.search_key_version}"

    query = st.text_input(
        "Buscar",
        (
            "🔍 BUSCADOR DESACTIVADO"
            if es_atencion3g
            else "🔍 Buscar guía/pedido..."
        ),
        label_visibility="collapsed",
        key=key_actual,
        disabled=es_atencion3g,
    )

    if query:
      url_raw = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv"
      try:
        df_matriz_fresco = pd.read_csv(url_raw)
      except Exception:
        df_matriz_fresco = None

      res_ops = pd.DataFrame()
      if df_matriz_fresco is not None:
        cols_m = [c.upper() for c in df_matriz_fresco.columns]
        if "NÚMERO DE GUÍA" in cols_m:
          res_ops = df_matriz_fresco[
              (
                  df_matriz_fresco["NÚMERO DE GUÍA"]
                  .astype(str)
                  .str.contains(query, case=False, na=False)
              )
              | (
                  df_matriz_fresco["NÚMERO DE PEDIDO"]
                  .astype(str)
                  .str.contains(query, case=False, na=False)
              )
              | (
                  df_matriz_fresco["NO CLIENTE"]
                  .astype(str)
                  .str.contains(query, case=False, na=False)
              )
              | (
                  df_matriz_fresco["NOMBRE DEL CLIENTE"]
                  .astype(str)
                  .str.contains(query, case=False, na=False)
              )
          ]

      res_inv = pd.DataFrame()
      try:
        df_inv_temp = pd.read_csv("inventario.csv")
        res_inv = df_inv_temp[
            (
                df_inv_temp["CODIGO"]
                .astype(str)
                .str.contains(query, case=False, na=False)
            )
            | (
                df_inv_temp["DESCRIPCION"]
                .astype(str)
                .str.contains(query, case=False, na=False)
            )
        ]
      except Exception:
        pass

      if not res_ops.empty:
        st.session_state.busqueda_activa = True
        st.session_state.tipo_resultado = "OPERACION"
        st.session_state.resultado_busqueda = res_ops
      elif not res_inv.empty:
        st.session_state.busqueda_activa = True
        st.session_state.tipo_resultado = "INVENTARIO"
        st.session_state.resultado_busqueda = res_inv
      else:
        st.session_state.busqueda_activa = False
        st.toast("No se encontró ningún registro", icon="🔍")

  with c4:
    with st.popover("☰ Menú", use_container_width=True):
      usuario = st.session_state.get("usuario_activo", "GUEST")
      es_admin = usuario.upper() == "RIGOBERTO"
      es_ventas = usuario.upper() == "VENTAS"
      es_atencion3g = usuario.upper() == "ATENCION3G"

      nombre_display = st.session_state.get(
          "nombre_completo", "OPERADOR DESCONOCIDO"
      )

      st.markdown(
          f"""
            <div style='background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin-bottom: 15px; border-left: 3px solid #00D4FF;'>
                <p style='color:#00D4FF; font-size:9px; font-weight:500; margin:0; letter-spacing:1px;'>USUARIO ACTIVO</p>
                <p style='color:{vars_css['text']}; font-size:14px; font-weight:500; margin:0;'>{nombre_display.upper()}</p>
            </div>
        """,
          unsafe_allow_html=True,
      )

      st.markdown(
          "<p style='color:#f0f0f0; font-size:10px; font-weight:400;"
          " text-align:center; margin:10px 0; letter-spacing:1px;'>MENÚ"
          " PRINCIPAL</p>",
          unsafe_allow_html=True,
      )

      if not es_ventas and not es_atencion3g:
        if st.button("DASHBOARD", use_container_width=True, key="pop_trk"):
          st.session_state.menu_main = "DASHBOARD"
          st.session_state.menu_sub = "GENERAL"
          st.session_state.busqueda_activa = False
          st.rerun()

      if not es_ventas:
        with st.expander(
            "SEGUIMIENTO",
            expanded=(st.session_state.menu_main == "SEGUIMIENTO"),
        ):
          usuario_actual = str(
              st.session_state.get(
                  "usuario", st.session_state.get("usuario_activo", "")
              )
          ).strip()
          if es_admin:
            opciones_seg = ["ALERTAS", "GANTT", "QUEJAS"]
          elif usuario_actual == "Cynthia":
            opciones_seg = ["ALERTAS", "QUEJAS"]
          else:
            opciones_seg = ["ALERTAS"]

          for s in opciones_seg:
            label = f"» {s}" if st.session_state.menu_sub == s else s
            if st.button(label, use_container_width=True, key=f"pop_sub_{s}"):
              st.session_state.menu_main = "SEGUIMIENTO"
              st.session_state.menu_sub = s
              st.session_state.busqueda_activa = False
              st.rerun()

      if not es_atencion3g:
        with st.expander(
            "REPORTES", expanded=(st.session_state.menu_main == "REPORTES")
        ):
          usuario_actual = str(
              st.session_state.get(
                  "usuario", st.session_state.get("usuario_activo", "")
              )
          ).strip()
          if es_admin or usuario_actual == "Carlos":
            opciones_rep = [
                "COSTOS CEDIS",
                "ANALISIS MENSUAL",
                "DETALLE COSTOS",
                "ENVIOS ESPECIALES",
                "ENVIO DE MUESTRAS",
            ]
          else:
            opciones_rep = ["ENVIO DE MUESTRAS"]

          for s in opciones_rep:
            label = f"» {s}" if st.session_state.menu_sub == s else s
            if st.button(label, use_container_width=True, key=f"pop_rep_{s}"):
              st.session_state.menu_main = "REPORTES"
              st.session_state.menu_sub = s
              st.session_state.busqueda_activa = False
              st.rerun()

      if not es_ventas and not es_atencion3g:
        with st.expander(
            "FORMATOS", expanded=(st.session_state.menu_main == "FORMATOS")
        ):
          opciones_for = [
              "SALIDA DE PT",
              "CHECK LIST AGC",
              "QR AGC",
              "PREGUIA PAQMEX",
              "RECOLECCION 3G",
              "RECOLECCION ONE",
              "CARTA RECLAMO",
              "COTIZACIONES",
          ]
          for s in opciones_for:
            label = f"» {s}" if st.session_state.menu_sub == s else s
            if st.button(label, use_container_width=True, key=f"pop_for_{s}"):
              st.session_state.menu_main = "FORMATOS"
              st.session_state.menu_sub = s
              st.session_state.busqueda_activa = False
              st.rerun()

      if not es_ventas and not es_atencion3g:
        with st.expander(
            "CENTRO DE DATOS",
            expanded=(st.session_state.menu_main == "CENTRO DE DATOS"),
        ):
          for s in ["ASIGNAR FLETERA", "CARGAR DATOS", "ETIQUETAS", "HERRAMIENTAS"]:
            label = f"» {s}" if st.session_state.menu_sub == s else s
            if st.button(label, use_container_width=True, key=f"pop_hub_{s}"):
              st.session_state.menu_main = "CENTRO DE DATOS"
              st.session_state.menu_sub = s
              st.session_state.busqueda_activa = False
              st.rerun()

      if st.session_state.get("usuario_activo") == "Rigoberto":
        with st.expander(
            "FINANZAS", expanded=(st.session_state.menu_main == "FINANZAS")
        ):
          opciones_fin = ["WALLET", "CAJA CHICA", "GASTOS"]
          for s in opciones_fin:
            label = f"» {s}" if st.session_state.menu_sub == s else s
            if st.button(label, use_container_width=True, key=f"pop_fin_{s}"):
              st.session_state.menu_main = "FINANZAS"
              st.session_state.menu_sub = s
              st.session_state.busqueda_activa = False
              st.rerun()

      usuario_actual = st.session_state.get("usuario_activo", "").upper()
      if usuario_actual in ["RIGOBERTO", "JMORENO", "CARLOS"]:
        with st.expander(
            "ENFOQUE", expanded=(st.session_state.get("menu_main") == "ENFOQUE")
        ):
          for s in ["MORENO", "VAZQUEZ", "MIGUEL"]:
            label = f"» {s}" if st.session_state.get("menu_sub") == s else s
            if st.button(label, use_container_width=True, key=f"pop_enf_{s}"):
              st.session_state.menu_main = "ENFOQUE"
              st.session_state.menu_sub = s
              st.rerun()

      st.markdown(
          "<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True
      )
      if st.button("TERMINAR SESIÓN", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
          del st.session_state[key]
        st.rerun()

st.markdown("---")


# ==========================================
# 6. INTERFAZ PRINCIPAL (MÓDULO DE ASIGNACIÓN)
# ==========================================
def main():
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
  # LOGISTICS INTELLIGENCE & SISTEMA DE SELLADO
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
