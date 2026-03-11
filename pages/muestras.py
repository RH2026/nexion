import streamlit as st
from datetime import date
import streamlit.components.v1 as components

# --- FUNCIÓN GENERADORA DEL HTML (Diseño Limpio para Impresión) ---
def generar_carta_final_html(datos_rem, datos_carta):
    return f"""
    <div style="font-family: 'Arial', sans-serif; padding: 50px; color: #000; max-width: 750px; margin: auto; background: white; line-height: 1.5;">
        <div style="text-align: right; font-weight: bold; margin-bottom: 30px;">
            Guadalajara, Jalisco a {datos_carta['fecha_texto']}
        </div>

        <div style="margin-bottom: 25px;">
            <p style="margin: 0; font-weight: bold; text-transform: uppercase;">{datos_carta['paqueteria']}</p>
            <p style="margin: 0; font-weight: bold;">A quien corresponda:</p>
        </div>

        <div style="text-align: justify; white-space: pre-wrap;">
{datos_carta['cuerpo_texto']}
        </div>

        <div style="margin-top: 40px;">
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
st.title("✉️ Generador de Cartas de Reclamo")

col1, col2 = st.columns(2)

with col1:
    # Selector de Paqueterías
    paqueteria_sel = st.selectbox("Selecciona la Paquetería:", 
                                  ["ONE PAQUETERIA", "FEDEX", "ESTAFETA", "DHL", "PAQUETEXPRESS", "TRESGUERRAS"])
    f_fecha = st.date_input("Fecha del documento", date.today())
    f_cajas = st.number_input("Cantidad de cajas afectadas", min_value=1, value=1)

with col2:
    f_codigos = st.text_input("Códigos de producto", placeholder="Ej: 4052-L20 - 2 Cajas, 4052-L18 - 3 cajas")
    f_monto = st.text_input("Monto (Solo el número)", placeholder="Ej: 3,410")
    f_guia = st.text_input("Número de Guía", "JALGDL ")

st.divider()

# --- CONSTRUCCIÓN DEL TEXTO POR DEFAULT ---
texto_defecto = (
    f"Por medio de la presente, notifico formalmente el reclamo y cobro total correspondiente a "
    f"{f_cajas} cajas con el código {f_codigos}, estas cajas están reportadas como faltantes por parte del cliente, "
    f"están las anotaciones en carta porte y factura, anexo evidencias y factura para que corroboren el precio.\n\n"
    f"Costo de la mercancía a reclamar es de: {f_monto} + IVA, se anexa factura para corroborar precio.\n\n"
    f"Sin más por el momento quedo atento para cualquier aclaración."
)

st.subheader("📝 Cuerpo de la Carta (Editable)")
cuerpo_final = st.text_area("Puedes ajustar el texto aquí:", value=texto_defecto, height=250)

if st.button(":material/print: GENERAR E IMPRIMIR", use_container_width=True, type="primary"):
    
    # Datos fijos de Rigoberto
    rem_info = {
        "atencion": "Rigoberto Hernandez",
        "tel": "(52) 33 3540 2939 Ext. 157",
        "email": "rhernandez@jypesa.com"
    }
    
    # Formato de fecha
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_formato = f"{f_fecha.day} de {meses[f_fecha.month - 1]} del {f_fecha.year}"
    
    carta_info = {
        "paqueteria": paqueteria_sel,
        "fecha_texto": fecha_formato,
        "cuerpo_texto": cuerpo_final
    }

    html_final = generar_carta_final_html(rem_info, carta_info)
    
    # Se genera el componente oculto que dispara la impresión
    st.success(f"Generando documento para {paqueteria_sel}...")
    components.html(f"<html><body>{html_final}<script>window.print();</script></body></html>", height=0)
















































































