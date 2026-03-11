import streamlit as st
from datetime import date, datetime
import streamlit.components.v1 as components

# --- FUNCIÓN GENERADORA DEL HTML (Basada en tu imagen de JYPEA) ---
def generar_carta_reclamo_html(datos_rem, datos_guia, detalles_reclamo):
    return f"""
    <div style="font-family: 'Arial', sans-serif; padding: 50px; color: #000; max-width: 750px; margin: auto; background: white; line-height: 1.5;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="letter-spacing: 5px; font-weight: 300; margin-bottom: 0;">JYPE S A</h2>
            <p style="font-size: 0.7em; color: #888; margin-top: 0;">HOSPITALITY</p>
        </div>

        <div style="text-align: right; font-weight: bold; margin-bottom: 30px;">
            Guadalajara, Jalisco a {datos_guia['fecha_emision']}
        </div>

        <div style="margin-bottom: 25px;">
            <p style="margin: 0; font-weight: bold;">ONE PAQUETERIA</p>
            <p style="margin: 0; font-weight: bold;">A quien corresponda:</p>
        </div>

        <div style="text-align: justify;">
            <p>Por medio de la presente, manifiesto mi inconformidad respecto al cobro realizado por el envío de 
            <b>{detalles_reclamo['cantidad_pallets']} pallets</b> recientemente embarcados, guía <b>{datos_guia['num_guia']}</b>.</p>

            <p>El valor convenido por tarima es de hasta <b>${detalles_reclamo['precio_acordado']:.2f} pesos</b>; sin embargo, en esta ocasión 
            se facturó un importe superior a <b>${detalles_reclamo['precio_facturado']:.2f} pesos</b>, bajo el argumento de que las tarimas 
            excedían el tamaño acordado.</p>

            <p>Después de revisar las especificaciones del embarque, no se identifica un excedente que justifique dicho incremento. 
            Por lo anterior, solicito atentamente se revise nuevamente el cálculo aplicado y se me proporcione el sustento técnico 
            correspondiente, ya que el cargo realizado no parece estar alineado con las condiciones previamente establecidas.</p>

            <p>Agradezco de antemano su pronta revisión y quedo atento a su respuesta para la aclaración correspondiente.</p>
        </div>

        <div style="margin-top: 40px;">
            <p>Sin más por el momento quedo atento para cualquier aclaración.</p>
            <p style="font-weight: bold; margin-bottom: 40px;">Atentamente</p>
            
            <p style="margin: 0; font-weight: bold;">{datos_rem['atencion']}</p>
            <p style="margin: 0; font-style: italic; font-size: 0.9em;">Distribución y Logística</p>
            <p style="margin: 0; font-size: 0.9em;">Tel: {datos_rem['tel']}</p>
            <p style="margin: 0; font-size: 0.9em; color: #003399;">{datos_rem['email']}</p>
            
            <div style="margin-top: 20px;">
                <p style="margin: 0; font-size: 0.9em;">En representación de:</p>
                <p style="margin: 0; font-weight: bold;">Jabones y Productos Especializados, S.A. de C.V.</p>
            </div>
        </div>
    </div>
    """

# --- INTERFAZ EN STREAMLIT ---
st.title("✉️ Generador de Carta de Reclamo")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Datos del Envío")
    f_guia = st.text_input("Número de Guía (Ej: JALGDL 239548)", "JALGDL ")
    f_fecha = st.date_input("Fecha de la Carta", date.today())
    f_pallets = st.number_input("Cantidad de Pallets", min_value=1, value=3)

with col2:
    st.markdown("### 💰 Detalles del Cobro")
    f_precio_base = st.number_input("Precio Acordado ($)", value=2000.0)
    f_precio_real = st.number_input("Precio Facturado ($)", value=4000.0)
    f_email = st.text_input("Email de contacto", "rhernandez@jypesa.com")

st.divider()

# Botón de acción
if st.button(":material/print: GENERAR CARTA DE RECLAMO", use_container_width=True, type="primary"):
    
    rem_info = {
        "atencion": "Rigoberto Hernandez",
        "tel": "(52) 33 3540 2939 Ext. 157",
        "email": f_email
    }
    
    guia_info = {
        "num_guia": f_guia,
        "fecha_emision": f_fecha.strftime("%d de %B del %Y")
    }
    
    reclamo_info = {
        "cantidad_pallets": f_pallets,
        "precio_acordado": f_precio_base,
        "precio_facturado": f_precio_real
    }

    carta_html = generar_carta_reclamo_html(rem_info, guia_info, reclamo_info)
    
    st.success("¡Carta generada! Preparando impresión...")
    components.html(f"<html><body>{carta_html}<script>window.print();</script></body></html>", height=800, scrolling=True)














































































