import streamlit as st
from datetime import date
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA WIDE ---
st.set_page_config(layout="wide", page_title="Nexion Reclamos", page_icon="✉️")

# --- DISEÑO DE IMPRESIÓN PROFESIONAL ---
def generar_carta_pro_html(datos_rem, datos_carta):
    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 60px; color: #1a1a1a; max-width: 750px; margin: auto; background: white; line-height: 1.6;">
        <div style="border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: baseline;">
            <span style="font-size: 1.2em; font-weight: bold; letter-spacing: 2px; color: #333;">JABONES Y PRODUCTOS ESPECIALIZADOS</span>
            <span style="font-size: 0.9em; color: #666;">{datos_carta['fecha_texto']}</span>
        </div>
        <div style="margin-bottom: 40px;">
            <p style="margin: 0; font-size: 0.8em; color: #666; text-transform: uppercase;">Atención a:</p>
            <p style="margin: 0; font-weight: bold; font-size: 1.1em;">{datos_carta['paqueteria']}</p>
            <p style="margin: 0; font-weight: bold; color: #444;">Departamento de Reclamos / Operaciones</p>
        </div>
        <div style="margin-bottom: 30px;">
            <h2 style="font-size: 1.1em; border-left: 4px solid #003399; padding-left: 15px; text-transform: uppercase; color: #000;">
                ASUNTO: {datos_carta['asunto']}
            </h2>
        </div>
        <div style="text-align: justify; font-size: 1.05em; color: #222; white-space: pre-wrap;">{datos_carta['cuerpo_texto']}</div>
        <div style="margin-top: 60px; border-top: 1px solid #eee; padding-top: 20px;">
            <p style="margin-bottom: 40px;">Atentamente,</p>
            <p style="margin: 0; font-weight: bold; font-size: 1.1em; color: #003399;">{datos_rem['atencion']}</p>
            <p style="margin: 0; font-size: 0.9em; font-weight: bold;">Gerencia de Distribución y Logística</p>
            <p style="margin: 0; font-size: 0.85em; color: #555;">JYPESA | S.A. de C.V.</p>
            <div style="margin-top: 10px; font-size: 0.85em; color: #666;">
                <span>📞 {datos_rem['tel']}</span> | <span>✉ {datos_rem['email']}</span>
            </div>
        </div>
    </div>
    """

st.title("✉️ Generador de Reclamos")

# --- INTERFAZ COMPACTA EN MODO WIDE ---
# Fila 1: Datos principales de la fletera y tipo
c1, c2, c3, c4 = st.columns([1.5, 1.2, 1, 1])
with c1:
    paqueteria_sel = st.selectbox(":material/local_shipping: FLETERA", 
                                  ["ONE PAQUETERIA", "FEDEX", "ESTAFETA", "DHL", "PAQUETEXPRESS", "TRESGUERRAS"])
with c2:
    tipo_incidencia = st.selectbox(":material/report_problem: INCIDENCIA", 
                                   ["Faltante", "Extravío", "Siniestro / Daño Total", "Daño Parcial"])
with c3:
    f_fecha = st.date_input(":material/calendar_today: FECHA CARTA", date.today())
with c4:
    f_guia = st.text_input(":material/tag: GUÍA", "JALGDL ")

# Fila 2: Detalles de la mercancía (Inputs pequeños)
c5, c6, c7 = st.columns([0.8, 2, 1])
with c5:
    f_cajas = st.number_input("CANT. CAJAS", min_value=1, value=1)
with c6:
    f_codigos = st.text_input("CÓDIGOS AFECTADOS", placeholder="Ej: 4052-L20, 4052-L18")
with c7:
    f_monto = st.text_input("MONTO RECLAMO", placeholder="Ej: 3,410")

st.divider()

# --- LÓGICA DE TEXTO DINÁMICO ---
dict_asuntos = {
    "Faltante": "Reclamo por Faltante de Mercancía",
    "Extravío": "Reporte de Extravío de Envío",
    "Siniestro / Daño Total": "Notificación de Siniestro (Daño Total)",
    "Daño Parcial": "Reclamo por Daño Parcial"
}

if tipo_incidencia == "Faltante":
    detalle = f"notifico formalmente el faltante de {f_cajas} cajas con el código {f_codigos}, reportadas como faltantes por parte del cliente. Se cuenta con anotaciones en carta porte y factura."
elif tipo_incidencia == "Extravío":
    detalle = f"hago de su conocimiento el extravío de {f_cajas} cajas con el código {f_codigos} relacionadas a la guía {f_guia}. Procedemos con la solicitud de indemnización."
elif tipo_incidencia == "Siniestro / Daño Total":
    detalle = f"notifico el siniestro de {f_cajas} cajas (Código {f_codigos}). La mercancía llegó con daños severos que impiden su uso, declarándose pérdida total."
else:
    detalle = f"notifico daños parciales en {f_cajas} cajas con el código {f_codigos}. El contenido presenta afectaciones que impactan su valor comercial."

texto_defecto = (
    f"Por medio de la presente, {detalle} anexo evidencias y factura para que corroboren el precio.\n\n"
    f"Costo de la mercancía a reclamar es de: {f_monto} + IVA, se anexa factura para corroborar precio.\n\n"
    f"Sin más por el momento quedo atento para cualquier aclaración."
)

# SECCIÓN DE EDICIÓN Y BOTÓN (Aprovechando el ancho)
ce1, ce2 = st.columns([3, 1])
with ce1:
    cuerpo_final = st.text_area(":material/edit: CUERPO DE LA CARTA", value=texto_defecto, height=220)

with ce2:
    st.write("###") # Espaciador
    st.info("Revisa que el monto y los códigos sean correctos antes de imprimir.")
    if st.button(":material/print: IMPRIMIR RECLAMO", use_container_width=True, type="primary"):
        rem_info = {
            "atencion": "Rigoberto Hernandez",
            "tel": "(52) 33 3540 2939 Ext. 157",
            "email": "rhernandez@jypesa.com"
        }
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        fecha_formato = f"{f_fecha.day} de {meses[f_fecha.month - 1]} del {f_fecha.year}"
        
        carta_info = {
            "paqueteria": paqueteria_sel,
            "asunto": dict_asuntos[tipo_incidencia],
            "guia": f_guia,
            "fecha_texto": fecha_formato,
            "cuerpo_texto": cuerpo_final
        }
        html_final = generar_carta_pro_html(rem_info, carta_info)
        components.html(f"<html><body>{html_final}<script>window.print();</script></body></html>", height=0)



















































































