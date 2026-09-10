from datetime import datetime
import os
import streamlit as st
import streamlit.components.v1 as components

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Cotizaciones",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="FORMATOS", submodulo_actual="COTIZACIONES")

# ============================================================
# 3. LÓGICA DE NEGOCIO Y DATOS (COTIZACIONES)
# ============================================================

jypesa_azul = "#003A70" 
jypesa_amarillo = "#FFC72C"

with st.container(border=True):
    st.markdown("<p style='color: #A4B9C8; font-size: 11px; font-weight: bold; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 10px;'>DATOS GENERALES</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        cliente = st.text_input("CLIENTE / EMPRESA", placeholder="Ej. Comercializadora ABC")
    with c2:
        origen = st.text_input("ORIGEN", placeholder="Ej. Guadalajara, Jal.")
    with c3:
        destino = st.text_input("DESTINO", placeholder="Ej. Monterrey, N.L.")
    
    st.write("") 
    
    st.markdown("<p style='color: #A4B9C8; font-size: 11px; font-weight: bold; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 10px;'>DETALLES DEL SERVICIO</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        transporte = st.text_input("FLETERA / TRANSPORTE")
        unidad = st.selectbox("TIPO DE UNIDAD", ["CAMIONETA 3.5", "RABÓN", "TORTON", "TRAILER 48'", "TRAILER 53'", "CONSOLIDADO"])
    with col2:
        cant_pallets = st.number_input("CANTIDAD DE PALLETS", min_value=0, step=1)
        cant_cajas = st.number_input("CANTIDAD DE CAJAS", min_value=0, step=1)
    with col3:
        costo = st.number_input("COSTO DE LA COTIZACIÓN ($)", min_value=0.0, format="%.2f")
        tiempo_transito = st.text_input("TIEMPO DE TRÁNSITO", placeholder="Ej. 2 a 3 días hábiles")
    
    observaciones = st.text_area("OBSERVACIONES (Opcional)", placeholder="Condiciones especiales, maniobras, seguro, etc.")

st.write("") 

# --- LÓGICA DE IMPRESIÓN COMPACTA Y SIN ENCABEZADOS ---
def generar_cotizacion_html():
    ahora = datetime.now()
    ms = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_texto = f"{ahora.day} de {ms[ahora.month - 1]} del {ahora.year}"
    
    cliente_txt = cliente if cliente else "A QUIEN CORRESPONDA"
    
    obs_html = f"""
    <div style="margin-top: 15px; padding: 12px; background-color: #f9f9f9; border-left: 4px solid {jypesa_amarillo}; border-radius: 4px;">
        <p style="margin: 0; font-size: 0.85em; font-weight: bold; color: #333;">OBSERVACIONES / CONDICIONES:</p>
        <p style="margin: 4px 0 0 0; font-size: 0.85em; color: #444; white-space: pre-wrap;">{observaciones}</p>
    </div>
    """ if observaciones else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @media print {{
                @page {{ margin: 0; size: letter; }}
                body {{ margin: 1.5cm; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; background: white;">
        <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 15px 30px; color: #1a1a1a; max-width: 700px; margin: auto; line-height: 1.35; border: 1px solid #eee;">
            
            <div style="border-bottom: 3px solid {jypesa_azul}; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: baseline;">
                <div style="display: flex; flex-direction: column;">
                    <span style="font-size: 1.1em; font-weight: 800; letter-spacing: 1px; color: #000000; text-transform: uppercase;">Jabones y Productos Especializados</span>
                    <span style="font-size: 0.85em; font-weight: 600; color: #666; letter-spacing: 0.5px;">Distribución y Logística | 2026</span>
                </div>
                <span style="font-size: 0.85em; color: #444; font-weight: 700;">{fecha_texto}</span>
            </div>

            <div style="margin-bottom: 20px;">
                <p style="margin: 0; font-size: 0.75em; color: #666; text-transform: uppercase;">Cotización preparada para:</p>
                <p style="margin: 0; font-weight: bold; font-size: 1.1em; color: #000; text-transform: uppercase;">{cliente_txt}</p>
            </div>

            <div style="margin-bottom: 15px; background-color: #fefdf5; padding: 10px 15px; border-radius: 4px; border-left: 5px solid {jypesa_amarillo};">
                <h2 style="font-size: 1em; text-transform: uppercase; color: #000; margin:0; font-weight: 800; letter-spacing: 0.5px;">
                    PROPUESTA DE SERVICIO LOGÍSTICO
                </h2>
            </div>

            <div style="margin-bottom: 20px; font-size: 0.95em; color: #222;">
                <p style="margin-bottom: 15px;">Por medio de la presente, ponemos a su consideración la siguiente propuesta económica para el servicio de transporte, de acuerdo con los requerimientos solicitados:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em;">
                    <tr style="background-color: {jypesa_azul}; color: white;">
                        <th style="padding: 8px; text-align: left; border: 1px solid {jypesa_azul};" colspan="2">DETALLES DEL SERVICIO</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; width: 35%; font-weight: 700; color: #444; background-color: #fafafa;">Ruta:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>{origen if origen else 'N/A'}</b> ➔ <b>{destino if destino else 'N/A'}</b></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; font-weight: 700; color: #444; background-color: #fafafa;">Transporte / Unidad:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{transporte} - {unidad}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; font-weight: 700; color: #444; background-color: #fafafa;">Volumen de Carga:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{cant_pallets} Pallets / {cant_cajas} Cajas</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; font-weight: 700; color: #444; background-color: #fafafa;">Tiempo estimado:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{tiempo_transito if tiempo_transito else 'Sujeto a disponibilidad y ruta'}</td>
                    </tr>
                </table>

                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr style="background-color: #f4f4f4;">
                        <td style="padding: 12px; font-weight: bold; font-size: 1.05em; color: #000; border: 1px solid #ddd; text-align: right; width: 65%;">INVERSIÓN TOTAL (Antes de IVA):</td>
                        <td style="padding: 12px; text-align: right; font-weight: 800; font-size: 1.15em; color: {jypesa_azul}; border: 1px solid #ddd;">${costo:,.2f}</td>
                    </tr>
                </table>

                {obs_html}
            </div>

            <div style="margin-top: 25px; margin-bottom: 10px; border-top: 2px solid #eee; padding-top: 15px;">
                <p style="margin-bottom: 20px; font-size: 0.9em; color: #333;">Quedo a sus órdenes para cualquier duda o comentario sobre esta propuesta.</p>
                <p style="margin: 0; font-weight: 800; font-size: 1.1em; color: {jypesa_azul};">Rigoberto Hernández</p>
                <p style="margin: 0; font-size: 0.9em; font-weight: 700; color: #333;">Coordinador de Distribución y Logística</p>
                <p style="margin: 0; font-size: 0.8em; color: #555;">JYPESA | S.A. de C.V.</p>
                
                <div style="margin-top: 10px; font-size: 0.85em; color: #444; background-color: #f9f9f9; padding: 8px; border-radius: 4px; display: inline-block; border: 1px solid #eee;">
                    <span style="color: {jypesa_azul}; font-weight: bold;">📱 33 19 75 31 22</span> <span style="margin: 0 8px; color: #ccc;">|</span> 
                    <span>📞 (52) 33 3540 2939 Ext. 157</span> <span style="margin: 0 8px; color: #ccc;">|</span> 
                    <span style="color: {jypesa_azul}; text-decoration: none;">✉ rhernandez@jypesa.com</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

if st.button(":material/print: IMPRIMIR COTIZACIÓN TÉCNICA", type="primary", use_container_width=True):
    cot_html = generar_cotizacion_html()
    components.html(f"{cot_html}<script>window.print();</script>", height=0)
