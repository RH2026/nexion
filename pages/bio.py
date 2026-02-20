import streamlit as st
import pandas as pd
from datetime import date
import streamlit.components.v1 as components
from io import BytesIO
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Control de Envíos JYPESA", layout="wide")

# Estilos visuales para parecerse a la imagen
st.markdown("""
    <style>
    .report-text { font-family: 'Arial'; font-size: 12px; }
    .stCheckbox { margin-bottom: -15px; }
    .destinatario-header { background-color: #b30000; color: white; padding: 5px; font-weight: bold; text-align: center; }
    .remitente-header { background-color: #000000; color: white; padding: 5px; font-weight: bold; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- LISTA DE PRODUCTOS ---
lista_productos = [
    "ELEMENTS", "ALMON OLIVE", "BIOGENA", "CAVA", "LAVANDA BOTANICUS", 
    "LAVARIVO", "BOTANICUS", "PERSEA", "RAINFOREST", "DOVE", "ECOLOGICOS"
]

# --- FORMULARIO DE ENTRADA ---
with st.container():
    # Encabezado Superior
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1: f_folio = st.text_input("FOLIO")
    with c2: f_paqueteria = st.text_input("PAQUETERIA / FORMA DE ENVIO")
    with c3: f_fecha = st.date_input("FECHA", date.today())

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown('<div class="destinatario-header">DESTINATARIO / NOMBRE DEL HOTEL</div>', unsafe_allow_html=True)
        f_hotel = st.text_input("Nombre del Hotel", label_visibility="collapsed")
        f_calle = st.text_input("CALLE, NUMERO Y CRUCE DE CALLES")
        c_i1, c_i2 = st.columns(2)
        with c_i1: f_colonia = st.text_input("COLONIA")
        with c_i2: f_cp = st.text_input("CODIGO POSTAL")
        c_i3, c_i4 = st.columns(2)
        with c_i3: f_ciudad = st.text_input("CIUDAD")
        with c_i4: f_estado = st.text_input("ESTADO")
        c_i5, c_i6 = st.columns(2)
        with c_i5: f_contacto = st.text_input("CONTACTO")
        with c_i6: f_telefono = st.text_input("TELEFONO")

    with col_der:
        st.markdown('<div class="remitente-header">REMITENTE</div>', unsafe_allow_html=True)
        st.text_input("Nombre", value="Jabones y productos Especializados", disabled=True)
        st.text_input("CALLE Y NUMERO", value="C. Cernícalo 155", disabled=True)
        c_d1, c_d2 = st.columns(2)
        with c_d1: st.text_input("COLONIA", value="La Aurora", disabled=True)
        with c_d2: st.text_input("CP", value="44460", disabled=True)
        c_d3, c_d4 = st.columns(2)
        with c_d3: st.text_input("CIUDAD", value="Guadalajara", disabled=True)
        with c_d4: st.text_input("ESTADO", value="Jalisco", disabled=True)
        f_solicitante = st.text_input("SOLICITANTE / NOMBRE DE AGENTE", value="JYPESA")

    st.markdown("---")
    
    # --- SECCIÓN DE PRODUCTOS (AMENIDADES) ---
    st.subheader("AMENIDADES")
    seleccionados = {}
    
    # Encabezados de la tabla de selección
    h1, h2, h3 = st.columns([2, 1, 1])
    h1.write("**PRODUCTO**")
    h2.write("**SELECCIONAR**")
    h3.write("**CANTIDAD**")

    for prod in lista_productos:
        p1, p2, p3 = st.columns([2, 1, 1])
        p1.write(prod)
        es_seleccionado = p2.checkbox("Incluir", key=f"check_{prod}", label_visibility="collapsed")
        cant = p3.number_input("Cant", min_value=0, step=1, key=f"cant_{prod}", label_visibility="collapsed")
        if es_seleccionado:
            seleccionados[prod] = cant

    f_comentarios = st.text_area("COMENTARIOS", height=100)

# --- GENERACIÓN DEL HTML PARA IMPRESIÓN ---
filas_tabla = "".join([
    f"<tr><td>{p}</td><td>PZAS</td><td></td><td>{c}</td></tr>" 
    for p, c in seleccionados.items()
])

html_impresion = f"""
<div id="print-area" style="font-family: Arial; border: 1px solid black; padding: 10px; width: 800px;">
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="border: 1px solid black; padding: 5px;">FOLIO: {f_folio}</td>
            <td style="border: 1px solid black; padding: 5px;">PAQUETERIA: {f_paqueteria}</td>
            <td style="border: 1px solid black; padding: 5px;">FECHA: {f_fecha}</td>
        </tr>
    </table>
    <div style="display: flex; margin-top: 10px;">
        <div style="width: 50%; border: 1px solid black;">
            <div style="background: #b30000; color: white; text-align: center; font-weight: bold;">DESTINATARIO</div>
            <div style="padding: 5px; background: #fff8e1;">
                <b>{f_hotel}</b><br>{f_calle}<br>Col: {f_colonia} CP: {f_cp}<br>{f_ciudad}, {f_estado}<br>ATN: {f_contacto} | TEL: {f_telefono}
            </div>
        </div>
        <div style="width: 50%; border: 1px solid black;">
            <div style="background: black; color: white; text-align: center; font-weight: bold;">REMITENTE</div>
            <div style="padding: 5px;">
                Jabones y productos Especializados<br>C. Cernícalo 155, La Aurora<br>Guadalajara, Jalisco CP 44460<br>SOLICITÓ: {f_solicitante}
            </div>
        </div>
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; text-align: center;">
        <tr style="background: #444; color: white;">
            <th>PRODUCTO</th><th>UM</th><th>CODIGO</th><th>CANTIDAD</th>
        </tr>
        {filas_tabla}
    </table>
    <div style="border: 1px solid black; margin-top: 10px; padding: 5px;">
        <b>COMENTARIOS:</b> {f_comentarios}
    </div>
    <div style="margin-top: 30px; text-align: center;">
        <p>RECIBO DE CONFORMIDAD DEL CLIENTE</p>
        <br>____________________________________<br>NOMBRE Y FIRMA
    </div>
</div>
"""

# --- BOTONES DE ACCIÓN ---
st.markdown("---")
c_bot1, c_bot2, c_bot3, c_bot4 = st.columns(4)

with c_bot1:
    if st.button("🚀 GUARDAR REGISTRO", type="primary", use_container_width=True):
        if not f_hotel:
            st.error("¡Falta el nombre del hotel!")
        else:
            st.success(f"Folio {f_folio} guardado.")
            time.sleep(1)
            st.rerun()

with c_bot2:
    if st.button("🖨️ IMPRIMIR", use_container_width=True):
        components.html(f"""
            <html>
                <body>
                    {html_impresion}
                    <script>
                        setTimeout(function() {{ window.print(); }}, 500);
                    </script>
                </body>
            </html>
        """, height=0)

with c_bot3:
    # Generar Excel en memoria
    output = BytesIO()
    df_excel = pd.DataFrame([{"FOLIO": f_folio, "HOTEL": f_hotel, "PRODUCTOS": str(seleccionados)}])
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_excel.to_excel(writer, index=False)
    st.download_button("📥 DESCARGAR EXCEL", output.getvalue(), f"Envio_{f_folio}.xlsx", use_container_width=True)

with c_bot4:
    if st.button("🔄 NUEVO REGISTRO", use_container_width=True):
        st.rerun()
        with c3:
            if st.button("🔄 NUEVO REGISTRO"):
                st.rerun()
