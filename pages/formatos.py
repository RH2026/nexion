import streamlit as st
import pandas as pd
from datetime import date
from datetime import datetime
import pytz # Necesario para la hora exacta en MX

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="NEXION - Control de Calidad")

# --- LÓGICA DE ESTADO (SESSION STATE) ---
# Usamos session state para que los datos no se borren si la página se recarga
if 'df_productos_calidad' not in st.session_state:
    st.session_state.df_productos_calidad = pd.DataFrame(
        [{"FECHA": "", "No de factura": "", "No de parte": "", "No de fabricacion": "", "Lote": "", "Cantidad": "", "Descripcion": ""}] * 10
    )

# --- INICIALIZACIÓN DE DATOS FIJOS Y DE SESIÓN ---
# Configurar zona horaria de Guadalajara
tz_gdl = pytz.timezone('America/Mexico_City')
now_gdl = datetime.now(tz_gdl)

# Folio automático (puedes cambiar esta lógica según tu necesidad)
folio_auto = now_gdl.strftime('%m%d%H%M')

# --- ESTILOS CSS PARA LA CAPTURA ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet" />
    <style>
        .stApp { background-color: #1a2432; }
        
        /* Títulos de sección con icono Material Design */
        .seccion-captura {
            display: flex;
            align-items: center;
            font-size: 1.1rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
        }

        /* Estilo para inputs de captura manual (marcados en amarillo en la imagen) */
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input {
            border-bottom: 2px solid #f6c23e !important; /* Tu amarillo de NEXION */
            border-radius: 0px !important;
            color: white !important;
            font-weight: 600 !important;
            background-color: transparent !important;
        }

        .stTextInput>div>div>input:focus {
            border-bottom: 2px solid #f6c23e !important;
            box-shadow: none !important;
        }
        
        /* Estilo para los label de Streamlit */
        .stTextInput label, .stDateInput label, .stNumberInput label {
            color: #94a3b8 !important;
            font-size: 0.8rem !important;
            text-transform: uppercase !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE RENDERIZADO HTML PARA IMPRESIÓN OFICIAL ---
def generar_formato_impresion(datos_encabezado, filas_productos, datos_dictamen):
    
    # Renderizar filas de productos (máximo 10)
    tabla_productos_html = ""
    for i, prod in enumerate(filas_productos):
        # Aseguramos que solo renderice 10 filas
        if i >= 10: break
        
        tabla_productos_html += f"""
        <tr style="height: 25px;">
            <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['FECHA']}</td>
            <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['No de factura']}</td>
            <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['No de parte']}</td>
            <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['No de fabricacion']}</td>
            <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['Lote']}</td>
            <td style="border:1px solid black; padding: 0 4px; font-size:10px; text-align:center;">{prod['Cantidad']}</td>
            <td style="border:1px solid black; padding: 0 4px; font-size:10px;">{prod['Descripcion']}</td>
        </tr>
        """
        
    # Calcular y rellenar espacios vacíos si hay menos de 10 productos
    num_filas = len(filas_productos)
    for _ in range(max(0, 10 - num_filas)):
        tabla_productos_html += f'<tr style="height: 25px;"><td style="border:1px solid black;" colspan="7"></td></tr>'

    # Estructura HTML final con CSS para impresión
    return f"""
    <html>
    <head>
        <style>
            @media print {{
                @page {{ size: landscape; margin: 10mm; }}
                body {{ margin: 0; padding: 0; }}
                header, footer {{ display: none !important; }}
            }}
            body {{ font-family: Arial, sans-serif; background: white; color: black; font-size: 11px; }}
            .oficial-box {{ padding: 0; width: 100%; border-collapse: collapse; }}
            table {{ width: 100%; border-collapse: collapse; border: 2px solid black; }}
            th, td {{ border: 1px solid black; padding: 2px; text-align: left; vertical-align: middle; }}
            .fixed-data {{ font-weight: bold; background-color: #f2f2f2; }}
            .input-data {{ color: blue; font-weight: bold; font-style: italic; }}
            .signature-line {{ border-top: 2px solid black; margin-top: 50px; text-align: center; width: 80%; margin-left: auto; margin-right: auto; }}
        </style>
    </head>
    <body>
        <div class="oficial-box">
            
            <table style="border-bottom: 2px solid black;">
                <tr>
                    <td rowspan="2" style="width:15%; text-align:center;">
                        <img src="https://static.wixstatic.com/media/078a3c_f84236a2353a470bb9387d853b050f2f~mv2.png" alt="JYPESA LOGO" width="80">
                    </td>
                    <td colspan="4" style="text-align:center; background-color:#eee;">
                        <h4 style="margin:0; letter-spacing:1px; font-size:14px;">Formato de control de rehabilitación, reproceso y retrabajo de producto</h4>
                    </td>
                </tr>
                <tr>
                    <td class="fixed-data">Clave:</td>
                    <td>F03-PNO-AC-21</td>
                    <td class="fixed-data">Versión:</td>
                    <td>3</td>
                </tr>
                <tr>
                    <td class="fixed-data">Solicita Calidad:</td>
                    <td colspan="2" class="input-data">{datos_encabezado['Solicita_Calidad']}</td>
                    <td class="fixed-data">No de desviación:</td>
                    <td class="input-data">{datos_encabezado['No_Desviacion']}</td>
                </tr>
                <tr>
                    <td class="fixed-data">No de retrabajo:</td>
                    <td class="input-data">{datos_encabezado['No_Retrabajo']}</td>
                    <td class="fixed-data">No de reclamo:</td>
                    <td colspan="2" class="input-data">{datos_encabezado['No_Reclamo']}</td>
                </tr>
                <tr>
                    <td class="fixed-data">Fecha de publicación:</td>
                    <td>14-Ene-25</td>
                    <td class="fixed-data">No de cliente:</td>
                    <td colspan="2" class="input-data">{datos_encabezado['No_Cliente']}</td>
                </tr>
                <tr>
                    <td class="fixed-data">Nombre comercial:</td>
                    <td class="input-data">{datos_encabezado['Nombre_Comercial']}</td>
                    <td class="fixed-data">Transporte:</td>
                    <td class="input-data">{datos_encabezado['Transporte']}</td>
                    <td class="fixed-data">Guía:</td>
                    <td class="input-data">{datos_encabezado['Guia']}</td>
                </tr>
                <tr>
                    <td class="fixed-data">Sustituye a:</td>
                    <td colspan="2">F03-PNO-AC-21 V02</td>
                    <td class="fixed-data">Costo:</td>
                    <td colspan="2" class="input-data">{datos_encabezado['Costo']}</td>
                </tr>
            </table>

            <table style="margin-top: -2px; border-bottom: 2px solid black;">
                <thead>
                    <tr style="font-size:10px; background-color:#ddd; height:20px;">
                        <th style="border:1px solid black; width:10%; text-align:center;">FECHA</th>
                        <th style="border:1px solid black; width:15%; text-align:center;">No de factura</th>
                        <th style="border:1px solid black; width:15%; text-align:center;">No de parte</th>
                        <th style="border:1px solid black; width:15%; text-align:center;">No de fabricación</th>
                        <th style="border:1px solid black; width:10%; text-align:center;">Lote</th>
                        <th style="border:1px solid black; width:10%; text-align:center;">Cantidad</th>
                        <th style="border:1px solid black; width:25%; text-align:center;">Descripción del producto</th>
                    </tr>
                </thead>
                <tbody style="font-size:10px;">
                    {tabla_productos_html}
                </tbody>
            </table>

            <table style="margin-top:-2px; border-bottom: 2px solid black;">
                <tr>
                    <td class="fixed-data" style="width:20%;">Comentarios:</td>
                    <td colspan="3" class="input-data" style="height: 60px;">{datos_dictamen['Comentarios']}</td>
                </tr>
                <tr>
                    <td class="fixed-data">Acciones a realizar:</td>
                    <td class="input-data">{datos_dictamen['Acciones']}</td>
                    <td class="fixed-data">DICTAMEN:</td>
                    <td class="input-data" style="text-align:center; font-size:12px;">{datos_dictamen['Dictamen']}</td>
                </tr>
            </table>

            <div style="margin-top: 50px; display: flex; justify-content: space-between; font-size: 12px;">
                <div style="width: 30%; text-align:center;">
                    <div class="signature-line"></div>
                    <b>Analista de Incoming</b><br>
                    <span style="font-size:10px;">Firma/fecha</span>
                </div>
                <div style="width: 30%; text-align:center;">
                    <div class="signature-line"></div>
                    <b>Supervisor de calidad</b><br>
                    <span style="font-size:10px;">Firma/fecha</span>
                </div>
                <div style="width: 30%; text-align:center;">
                    <div class="signature-line"></div>
                    <b>Supervisor de producción</b><br>
                    <span style="font-size:10px;">Firma/fecha</span>
                </div>
            </div>

            <div style="margin-top: 80px; display: flex; justify-content: space-between; font-size: 10px; border-top: 1px solid #ccc; padding-top: 5px;">
                <div>Formato: F02-PNO-SGC-02 Versión 01</div>
                <div>Página 1 de 1</div>
            </div>
        </div>
    </body>
    </html>
    """

# --- CAPTURA DE DATOS (INTERFAZ ELITE) ---
st.markdown('<div class="seccion-captura"><span class="material-symbols-rounded">engineering</span> CAPTURA DE DATOS - FORMULARIO AMARILLO</div>', unsafe_allow_html=True)

# 1. ENCABEZADO (INPUTS AMARILLOS DE TU IMAGEN)
with st.container(border=True):
    # Fila 1 (4 columnas para un layout limpio)
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    # Solicita Calidad - marcado como imput manual
    solicita_calidad = col_e1.text_input("SOLICITA CALIDAD", placeholder="Nombre o Depto.", key="sol_cal_inp")
    # No de desviación - marcado como imput manual
    no_desviacion = col_e2.text_input("No. DE DESVIACIÓN", placeholder="NEX-00000", key="no_desv_inp")
    # No de retrabajo - marcado como imput manual
    no_retrabajo = col_e3.text_input("No. DE RETRABAJO", key="no_ret_inp")
    # No de reclamo - marcado como imput manual
    no_reclamo = col_e4.text_input("No. DE RECLAMO", key="no_rec_inp")

    # Fila 2
    col_e5, col_e6 = st.columns([1.5, 2.5]) # Layout asimétrico para el No_Cliente
    # No de cliente - marcado como imput manual
    no_cliente = col_e5.text_input("No. DE CLIENTE", key="no_cli_inp")
    # Comentarios de la orden - marcado como imput manual
    comentarios_orden = col_e6.text_input("Comentarios (descripción breve de la orden)", placeholder="Comentario para la orden", key="com_ord_inp")

    # Fila 3 - Datos de transporte y costo
    col_e7, col_e8, col_e9, col_e10 = st.columns(4)
    # Nombre comercial - marcado como imput manual
    nombre_comercial = col_e7.text_input("NOMBRE COMERCIAL", key="nom_com_inp")
    # Transporte - marcado como imput manual
    transporte = col_e8.selectbox("TRANSPORTE", ["DHL", "FEDEX", "UPS", "JYPESA PROPIO", "OTRO"], key="transp_sel")
    # Guía - marcado como imput manual
    guia = col_e9.text_input("GUÍA AÉREA / TRACKING", key="guia_inp")
    # Costo - marcado como imput manual
    costo = col_e10.text_input("COSTO USD", key="costo_inp")

# 2. SELECCIÓN DE PRODUCTOS (GRID)
st.divider()
st.markdown('<div class="seccion-captura"><span class="material-symbols-rounded">grid_view</span> CAPTURA DE PRODUCTOS (TABLA)</div>', unsafe_allow_html=True)

# Editor de datos nativo para la tabla de productos
df_productos_edit = st.data_editor(
    st.session_state.df_productos_calidad,
    num_rows="dynamic",
    use_container_width=True,
    key="calidad_productos_editor",
    column_config={
        "FECHA": st.column_config.DateColumn("FECHA", format="DD/MM/YYYY"),
        "No de factura": st.column_config.TextColumn("FACTURA"),
        "No de parte": st.column_config.TextColumn("No DE PARTE"),
        "No de fabricacion": st.column_config.TextColumn("No DE FABRICACIÓN"),
        "Lote": st.column_config.TextColumn("LOTE"),
        "Cantidad": st.column_config.NumberColumn("CANTIDAD", min_value=1),
        "Descripcion": st.column_config.TextColumn("DESCRIPCIÓN DEL PRODUCTO")
    }
)

# 3. DICTAMEN (SECCIÓN AMARILLA AL FINAL)
st.divider()
st.markdown('<div class="seccion-captura"><span class="material-symbols-rounded">fact_check</span> DICTAMEN Y COMENTARIOS FINALES</div>', unsafe_allow_html=True)

with st.container(border=True):
    col_f1, col_f2 = st.columns([2, 1])
    
    # Comentarios - marcado como imput manual
    comentarios_dictamen = col_f1.text_area("COMENTARIOS FINALES DEL ANALISTA", height=100, key="com_dict_inp")
    
    # Dictamen FINAL con los checks de la imagen original
    dictamen_final = col_f2.radio(
        "Dictamen FINAL Acéptado / Rechazado",
        ["Aceptado", "Rechazado"],
        key="dictamen_radio"
    )

# --- BOTONES DE IMPRESIÓN Y ACCIÓN ---
st.divider()
enviar_col, imprimir_col = st.columns(2)

# Botón de impresión (principal, use type="primary")
if imprimir_col.button(":material/print: GENERAR E IMPRIMIR REPORTE OFICIAL", use_container_width=True, type="primary"):
    
    # 1. Validar que la tabla de productos no esté vacía
    filas_validas = df_productos_edit[df_productos_edit["CODIGO"] != ""]
    if filas_validas.empty:
        st.error("Vida, no has capturado ningún producto en la tabla.")
    else:
        # 2. Recopilar todos los datos
        rem_info = {
            "folio_reporte": f"INT-{folio_auto}", # Usamos el folio automático de NEXION
            "fecha_reporte": f_fecha_sel.strftime('%d/%m/%Y'),
            "hora_reporte": f_hora_sel,
            "paqueteria_impresion": f_paq_sel # Para usar en el HTML si es necesario
        }
        dest_info = {"nombre": f_h_sel, "calle": f_ca_sel, "colonia": f_co_sel, "cp": f_cp_sel, "ciudad": f_ci_sel, "estado": f_es_sel, "contacto": f_con_sel}
        
        # 3. Generar el HTML para impresión
        contrarecibo_html = generar_contrarecibo_html(rem_info, dest_info, filas_validas.to_dict('records'))
        
        st.success("¡Documento generado con estilo Elite!")
        
        # 4. Inyectar el HTML con el script de impresión
        components.html(f"<html><body>{contrarecibo_html}<script>window.onload = function() {{ window.print(); }}</script></body></html>", height=0)

if enviar_col.button(":material/delete_sweep: LIMPIAR TODO", use_container_width=True):
    # Lógica de borrado progresivo de tu sistema
    st.session_state.rows_contrarecibo = pd.DataFrame([{"FECHA": now_gdl.strftime('%d/%m/%Y'), "CODIGO": "", "PAQUETERIA": "", "CANTIDAD": ""}] * 10)
    st.session_state.reset_counter += 1
    st.rerun()

























































































