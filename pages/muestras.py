import streamlit as st
from datetime import date
import streamlit.components.v1 as components

# --- FUNCIÓN GENERADORA DEL HTML ---
def generar_carta_dinamica_html(datos_rem, datos_carta):
    return f"""
    <div style="font-family: 'Arial', sans-serif; padding: 50px; color: #000; max-width: 750px; margin: auto; background: white; line-height: 1.5;">
        <div style="text-align: right; font-weight: bold; margin-bottom: 30px;">
            Guadalajara, Jalisco a {datos_carta['fecha_texto']}
        </div>

        <div style="margin-bottom: 25px;">
            <p style="margin: 0; font-weight: bold;">ONE PAQUETERIA</p>
            <p style="margin: 0; font-weight: bold;">A quien corresponda:</p>
        </div>

        <div style="text-align: justify; white-space: pre-wrap;">
{datos_carta['cuerpo_texto']}
        </div>

        <div style="margin-top: 40px;">
            <p>Sin más por el momento quedo atento para cualquier aclaración.</p>
            <p style="font-weight: bold; margin-bottom: 40px;">Atentamente</p>
            
            <p style="margin: 0; font-weight: bold;">{datos_rem['atencion']}</p>
            <p style="margin: 0; font-style: italic; font-size: 0.9em;">Distribución y Logística</p>
            <p style="margin: 0; font-size: 0.9em;">Tel: {datos_rem['tel']}</p>
            <p style="margin: 0; font-size: 0.9em; color: #003399; text-decoration: underline;">{datos_rem['email']}</p>
            
            <div style="margin-top: 20px;">
                <p style="margin: 0; font-size: 0.9em;">En representación de:</p>
                <p style="margin: 0; font-weight: bold;">Jabones y Productos Especializados, S.A. de C.V.</p>
            </div>
        </div>
    </div>
    """

# --- INTERFAZ EN STREAMLIT ---
st.title("✉️ Plantilla Maestra de Reclamos")

col1, col2 = st.columns(2)

with col1:
    tipo_reclamo = st.selectbox("Tipo de Incidencia:", ["Faltante de Mercancía", "Extravío de Paquete", "Siniestro / Daño"])
    f_fecha = st.date_input("Fecha del documento", date.today())
    f_cajas = st.number_input("Cantidad de cajas afectadas", min_value=1, value=1)

with col2:
    f_codigos = st.text_input("Códigos de producto", placeholder="Ej: 4052-L20, 4052-L18")
    f_monto = st.text_input("Costo a reclamar", placeholder="Ej: 3,410 MXN + IVA")
    f_guia = st.text_input("Número de Guía", "JALGDL ")

st.divider()

# --- LÓGICA DE TEXTO DINÁMICO ---
# Creamos un borrador automático basado en la selección
if tipo_reclamo == "Faltante de Mercancía":
    texto_base = f"Por medio de la presente, notifico formalmente el reclamo y cobro total correspondiente a {f_cajas} cajas con el código {f_codigos}, estas cajas están reportadas como faltantes por parte del cliente, están las anotaciones en carta porte y factura, anexo evidencias y factura para que corroboren el precio.\n\nCosto de la mercancía a reclamar es de: {f_monto}, se anexa factura para corroborar precio."
elif tipo_reclamo == "Extravío de Paquete":
    texto_base = f"Por medio de la presente, hago de su conocimiento el extravío de {f_cajas} cajas (Código: {f_codigos}) correspondientes a la guía {f_guia}. Solicito el reembolso total del valor declarado.\n\nCosto total de la pérdida: {f_monto}, según factura anexa."
else: # Siniestro / Daño
    texto_base = f"Por medio de la presente, notifico formalmente el siniestro ocurrido a {f_cajas} cajas con código {f_codigos}. La mercancía llegó dañada y no es apta para su uso, lo cual fue asentado en la guía {f_guia}.\n\nEl costo de los daños asciende a: {f_monto}."

# ÁREA DE EDICIÓN FINAL
st.subheader("📝 Editar cuerpo de la carta")
cuerpo_final = st.text_area("Puedes modificar el texto aquí antes de imprimir:", value=texto_base, height=200)

if st.button(":material/print: GENERAR E IMPRIMIR", use_container_width=True, type="primary"):
    
    # Datos de Rigoberto (Fijos según tu imagen)
    rem_info = {
        "atencion": "Rigoberto Hernandez",
        "tel": "(52) 33 3540 2939 Ext. 157",
        "email": "rhernandez@jypesa.com"
    }
    
    # Meses para el formato de fecha en español
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_formato = f"{f_fecha.day} de {meses[f_fecha.month - 1]} del {f_fecha.year}"
    
    carta_info = {
        "fecha_texto": fecha_formato,
        "cuerpo_texto": cuerpo_final
    }

    html_final = generar_carta_dinamica_html(rem_info, carta_info)
    components.html(f"<html><body>{html_final}<script>window.print();</script></body></html>", height=800, scrolling=True)















































































