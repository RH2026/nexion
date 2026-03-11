import streamlit as st
from datetime import date
import streamlit.components.v1 as components

# --- DISEÑO CHINGÓN PARA IMPRESIÓN (Moderno y Ejecutivo) ---
def generar_carta_pro_html(datos_rem, datos_carta):
    return f"""
    <div style="font-family: 'Segoe UI', Helvetica, Arial, sans-serif; padding: 60px; color: #1a1a1a; max-width: 800px; margin: auto; background: white; line-height: 1.6;">
        <div style="border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: baseline;">
            <span style="font-size: 1.2em; font-weight: bold; letter-spacing: 2px; color: #333;">JABONES Y PRODUCTOS ESPECIALIZADOS</span>
            <span style="font-size: 0.9em; color: #666;">{datos_carta['fecha_texto']}</span>
        </div>

        <div style="margin-bottom: 40px;">
            <p style="margin: 0; font-size: 0.9em; color: #666; text-transform: uppercase; letter-spacing: 1px;">Atención a:</p>
            <p style="margin: 0; font-weight: bold; font-size: 1.1em;">{datos_carta['paqueteria']}</p>
            <p style="margin: 0; font-weight: bold; color: #444;">Departamento de Servicio al Cliente / Reclamos</p>
        </div>

        <div style="margin-bottom: 30px;">
            <h2 style="font-size: 1.2em; border-left: 4px solid #003399; padding-left: 15px; text-transform: uppercase;">
                Asunto: {datos_carta['asunto']} - Guía {datos_carta['guia']}
            </h2>
        </div>

        <div style="text-align: justify; font-size: 1.05em; color: #222;">
            <p>Estimados,</p>
            <div style="white-space: pre-wrap;">{datos_carta['cuerpo_texto']}</div>
        </div>

        <div style="margin-top: 60px; border-top: 1px solid #eee; padding-top: 20px;">
            <p style="margin-bottom: 40px;">Atentamente,</p>
            
            <p style="margin: 0; font-weight: bold; font-size: 1.1em; color: #003399;">{datos_rem['atencion']}</p>
            <p style="margin: 0; font-size: 0.9em; font-weight: bold;">Gerencia de Distribución y Logística</p>
            <p style="margin: 0; font-size: 0.85em; color: #555;">JYPESA | Jabones y Productos Especializados, S.A. de C.V.</p>
            
            <div style="margin-top: 15px; font-size: 0.85em; color: #666;">
                <span>📞 {datos_rem['tel']}</span> | 
                <span style="color: #003399;">✉ {datos_rem['email']}</span>
            </div>
        </div>
    </div>
    """

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Nexion Reclamos", page_icon="✉️")
st.title("✉️ Generador de Reclamos Ejecutivo")

# Sidebar para configuración rápida
with st.sidebar:
    st.header("⚙️ Configuración")
    paqueteria_sel = st.selectbox("Paquetería:", ["ONE PAQUETERIA", "FEDEX", "ESTAFETA", "DHL", "PAQUETEXPRESS", "TRESGUERRAS"])
    tipo_incidencia = st.selectbox("Tipo de Incidencia:", ["Faltante", "Extravío", "Siniestro / Daño Total", "Daño Parcial"])
    f_fecha = st.date_input("Fecha", date.today())

col1, col2 = st.columns(2)
with col1:
    f_guia = st.text_input("Número de Guía", "JALGDL ")
    f_cajas = st.number_input("Cajas afectadas", min_value=1, value=1)

with col2:
    f_codigos = st.text_input("Códigos de producto", placeholder="4052-L20, 4052-L18...")
    f_monto = st.text_input("Monto total a reclamar (Solo número)", "0.00")

st.divider()

# --- LÓGICA DINÁMICA DE TEXTO ---
dict_asuntos = {
    "Faltante": "Reclamo formal por faltante de mercancía",
    "Extravío": "Reporte de extravío de envío y solicitud de indemnización",
    "Siniestro / Daño Total": "Notificación de siniestro (Mercancía dañada en su totalidad)",
    "Daño Parcial": "Reclamo por daño parcial en el contenido del envío"
}

# Redacción automática basada en la selección
if tipo_incidencia == "Faltante":
    detalle = f"notifico formalmente el faltante de {f_cajas} cajas (Códigos: {f_codigos}). El cliente reporta que el bulto llegó con sellos alterados o incompleto, según consta en las anotaciones de la carta porte."
elif tipo_incidencia == "Extravío":
    detalle = f"hago de su conocimiento el extravío total de {f_cajas} bultos relacionados a la guía mencionada. Tras agotar los tiempos de búsqueda, procedemos con el cobro de la mercancía."
elif tipo_incidencia == "Siniestro / Daño Total":
    detalle = f"notifico el siniestro de {f_cajas} cajas. La mercancía presenta daños estructurales severos que impiden su uso o comercialización, por lo que se declara como pérdida total."
else: # Daño Parcial
    detalle = f"notifico daños parciales en {f_cajas} cajas. Aunque el bulto fue entregado, el contenido interno presenta roturas/daños que afectan el valor de la mercancía (Códigos: {f_codigos})."

texto_base = (
    f"Por medio de la presente, {detalle}\n\n"
    f"Adjuntamos a este reclamo la evidencia fotográfica correspondiente y la factura del envío para su validación.\n\n"
    f"Costo de la mercancía a reclamar es de: {f_monto} + IVA, se anexa factura para corroborar precio.\n\n"
    f"Sin más por el momento quedo atento para cualquier aclaración."
)

st.subheader("📝 Edición Final del Cuerpo")
cuerpo_final = st.text_area("Puedes ajustar los detalles aquí:", value=texto_base, height=280)

if st.button(":material/print: GENERAR E IMPRIMIR DOCUMENTO", use_container_width=True, type="primary"):
    
    rem_info = {
        "atencion": "Rigoberto Hernandez",
        "tel": "(52) 33 3540 2939 Ext. 157",
        "email": "rhernandez@jypesa.com"
    }
    
    # Fecha elegante
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_formato = f"{f_fecha.day} de {meses[f_fecha.month - 1]} del {f_fecha.year}"
    
    carta_info = {
        "paqueteria": paqueteria_sel,
        "asunto": dict_asuntos[tipo_incidencia],
        "guia": f_guia,
        "fecha_texto": fecha_formato,
        "cuerpo_texto": cuerpo_final
    }

    html_pro = generar_carta_pro_html(rem_info, carta_info)
    
    st.info("Preparando impresión...")
    components.html(f"<html><body>{html_pro}<script>window.print();</script></body></html>", height=0)

















































































