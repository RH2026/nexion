import base64
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from components.layout import render_layout

# 1. Configuración de la página
st.set_page_config(
    page_title="JYPESA | Check List AGC",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Llamada al layout (Valida permisos automáticamente y pinta el header, menú y buscador)
render_layout(modulo_actual="FORMATOS", submodulo_actual="CHECK LIST AGC")

# ── 3. LÓGICA EXCLUSIVA DE TU MÓDULO ──
jypesa_azul = "#003A70"
jypesa_amarillo = "#FFC72C"
    
with st.container():
    st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        orden_carga = st.text_input("ORDEN DE CARGA / GUÍA", placeholder="Ej. OC-98765")
    with c2:
        inspector = st.text_input("INSPECTOR / AUDITOR", value="Carlos Vazquez")
    with c3:
        transporte = st.text_input("TRANSPORTE", placeholder="Ej. Tres Guerras - MTY")
        
    st.markdown('</div>', unsafe_allow_html=True)
    
st.write("") 

def generar_checklist_html():
    ahora = datetime.now()
    ms = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_texto = f"{ahora.day} de {ms[ahora.month - 1]} del {ahora.year}"
    
    logo_base64 = ""
    try:
        with open("jypesa.png", "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    except:
        pass
    
    img_tag = f'<img src="data:image/png;base64,{logo_base64}" style="width: 100px; height: auto;">' if logo_base64 else ''
    
    filas_html = ""
    for i in range(1, 31):
        filas_html += f"""
        <tr>
            <td style="border: 1px solid #bbb; padding: 4px; text-align: center; font-weight: bold; background-color: #f9f9f9;">{i}</td>
            <td style="border: 1px solid #bbb; padding: 4px; text-align: center;"></td>
            <td style="border: 1px solid #bbb; padding: 4px; text-align: center;"></td>
            <td style="border: 1px solid #bbb; padding: 4px; text-align: center;"></td>
            <td style="border: 1px solid #bbb; padding: 4px; text-align: center;"></td>
            <td style="border: 1px solid #bbb; padding: 4px; text-align: center;"></td>
            <td style="border: 1px solid #bbb; padding: 4px; text-align: center;"></td>
        </tr>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @media print {{
                @page {{ margin: 0; size: letter portrait; }}
                body {{ margin: 1cm; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; background: white;">
        <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 10px 20px; color: #1a1a1a; max-width: 800px; margin: auto; line-height: 1.3;">
            
            <div style="border-bottom: 3px solid {jypesa_azul}; padding-bottom: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    {img_tag}
                    <div style="display: flex; flex-direction: column;">
                        <span style="font-size: 1.1em; font-weight: 800; color: #000000; text-transform: uppercase;">Jabones y Productos Especializados</span>
                        <span style="font-size: 0.8em; font-weight: 600; color: #666;">Distribución y Logística | Control de Calidad</span>
                    </div>
                </div>
                <span style="font-size: 0.85em; color: #444; font-weight: 700;">{fecha_texto}</span>
            </div>

            <div style="margin-bottom: 8px; background-color: #fefdf5; padding: 8px 12px; border-radius: 4px; border-left: 5px solid {jypesa_amarillo}; display: flex; justify-content: space-between; align-items: center;">
                <h2 style="font-size: 0.65em; text-transform: uppercase; color: #000; margin:0; font-weight: 800;">
                    CHECKLIST DE INSPECCIÓN DE TARIMAS CONFORME ESPECIFICACIÓN DE AGC
                </h2>
                <div style="font-size: 0.8em; color: #333; text-align: right;">
                    <strong>Orden/Guía:</strong> {orden_carga if orden_carga else '___'}<br>
                    <strong>Transporte:</strong> {transporte if transporte else '___'}
                </div>
            </div>

            <div style="background: #fff3cd; border: 1px solid #ffeeba; padding: 6px 10px; margin-bottom: 12px; text-align: center; font-size: 0.8em; font-weight: bold; color: #856404; border-radius: 4px;">
                Marque con una “✅” para indicar que cumple la especificación y marque con una “❌” para indicar que no cumple.
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 0.75em; margin-bottom: 15px;">
                <thead>
                    <tr style="background-color: {jypesa_azul}; color: white; text-align: center;">
                        <th style="padding: 6px; border: 1px solid {jypesa_azul}; width: 6%;">Tarima</th>
                        <th style="padding: 6px; border: 1px solid {jypesa_azul}; width: 15%;">Emplayo</th>
                        <th style="padding: 6px; border: 1px solid {jypesa_azul}; width: 15%;">Esquineros</th>
                        <th style="padding: 6px; border: 1px solid {jypesa_azul}; width: 16%;">Tacón sin Logos</th>
                        <th style="padding: 6px; border: 1px solid {jypesa_azul}; width: 16%;">Estiba Alineada</th>
                        <th style="padding: 6px; border: 1px solid {jypesa_azul}; width: 16%;">Estado de Cajas</th>
                        <th style="padding: 6px; border: 1px solid {jypesa_azul}; width: 16%;">QR Correcto</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
            </table>

            <div style="margin-top: 20px; display: flex; justify-content: space-around; text-align: center; font-size: 0.85em; color: #333;">
                <div>
                    <div style="border-bottom: 1px solid #000; width: 200px; height: 40px; margin: auto;"></div>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">{inspector if inspector else 'Firma del Inspector'}</p>
                    <p style="margin: 0; color: #666; font-size: 0.9em;">Auditor de Carga</p>
                </div>
                <div>
                    <div style="border-bottom: 1px solid #000; width: 200px; height: 40px; margin: auto;"></div>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">Vo. Bo. Almacén / Logística</p>
                    <p style="margin: 0; color: #666; font-size: 0.9em;">JYPESA</p>
                </div>
            </div>

        </div>
    </body>
    </html>
    """

if st.button(":material/print: IMPRIMIR CHECKLIST", type="primary", use_container_width=True):
    checklist_html = generar_checklist_html()
    components.html(f"{checklist_html}<script>window.print();</script>", height=0)
