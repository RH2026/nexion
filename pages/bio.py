import streamlit as st
import pandas as pd
from datetime import date
import streamlit.components.v1 as components
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Envíos", layout="wide")

# --- ESTILOS CSS PARA EL FORMULARIO EN STREAMLIT ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; }
    .header-style { 
        background-color: #b30000; 
        color: white; 
        padding: 10px; 
        border-radius: 5px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATOS INICIALES ---
productos_amenidades = [
    "ELEMENTS", "ALMON OLIVE", "BIOGENA", "CAVA", 
    "LAVANDA BOTANICUS", "LAVARIVO", "BOTANICUS", 
    "PERSEA", "RAINFOREST", "DOVE", "ECOLOGICOS"
]

# --- INTERFAZ DE USUARIO ---
st.markdown("<h1 class='header-style'>ORDEN DE ENVÍO Y PRODUCTOS</h1>", unsafe_allow_html=True)

with st.form("formulario_envio"):
    # Fila Superior: Folio, Paquetería y Fecha
    c_f1, c_f2, c_f3 = st.columns([1, 2, 1])
    with c_f1: nuevo_folio = st.text_input("FOLIO")
    with c_f2: f_paqueteria = st.text_input("PAQUETERÍA")
    with c_f3: f_fecha = st.date_input("FECHA", date.today())

    # Bloques de Destinatario y Remitente
    col_dest, col_rem = st.columns(2)
    
    with col_dest:
        st.error("🔴 **DESTINATARIO / NOMBRE DEL HOTEL**")
        f_hotel = st.text_input("Nombre del Hotel / Cliente")
        f_calle = st.text_input("Calle, Número y Cruce de Calles")
        c_d1, c_d2 = st.columns(2)
        with c_d1: f_colonia = st.text_input("Colonia")
        with c_d2: f_cp = st.text_input("Código Postal")
        c_d3, c_d4 = st.columns(2)
        with c_d3: f_ciudad = st.text_input("Ciudad")
        with c_d4: f_estado = st.text_input("Estado")
        f_contacto = st.text_input("Atención a (Contacto)")

    with col_rem:
        st.info("⚪ **REMITENTE**")
        st.text_input("Nombre", value="Jabones y productos Especializados", disabled=True)
        st.text_input("Dirección", value="C. Cernícalo 155", disabled=True)
        st.text_input("Colonia/Delegación", value="La Aurora, CP 44460", disabled=True)
        st.text_input("Ciudad/Estado", value="Guadalajara, Jalisco", disabled=True)
        f_solicito = st.text_input("Solicitante (JYPESA)", value="JYPESA")

    st.markdown("---")
    st.subheader("🛒 SELECCIÓN DE PRODUCTOS")
    
    # Tabla de productos (seleccionamos cuales y cantidades)
    seleccionados = st.multiselect("Selecciona los productos a incluir", productos_amenidades)
    cantidades = {}
    
    if seleccionados:
        cols_prod = st.columns(len(seleccionados))
        for i, producto in enumerate(seleccionados):
            with cols_prod[i]:
                cantidades[producto] = st.number_input(f"Cant. {producto}", min_value=0, step=1)

    f_comentarios = st.text_area("COMENTARIOS")

    # Botón para procesar
    btn_guardar = st.form_submit_button("🚀 GUARDAR Y PREPARAR")

# --- LÓGICA DE GUARDADO E IMPRESIÓN ---
if btn_guardar:
    if not f_hotel or not seleccionados:
        st.error("Por favor llena el nombre del hotel y selecciona al menos un producto.")
    else:
        # 1. Crear DataFrame para Excel
        datos_fila = {
            "FOLIO": nuevo_folio, "FECHA": f_fecha, "HOTEL": f_hotel, 
            "PAQUETERIA": f_paqueteria, "CONTACTO": f_contacto
        }
        for p, c in cantidades.items(): datos_fila[p] = c
        df_registro = pd.DataFrame([datos_fila])

        # 2. Generar HTML para Impresión (parecido a tu imagen)
        tabla_html = "".join([f"<tr><td>{p}</td><td>{c}</td><td>PZAS</td><td>Producto de línea</td></tr>" for p, c in cantidades.items()])
        
        form_pt_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 12px; }}
                .header-red {{ background-color: #b30000; color: white; padding: 5px; font-weight: bold; }}
                .sub-header {{ background-color: #444; color: white; padding: 3px; font-size: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ border: 1px solid black; padding: 5px; text-align: left; }}
                .box {{ border: 1px solid black; padding: 10px; height: 150px; }}
            </style>
        </head>
        <body>
            <div style="display: flex; justify-content: space-between;">
                <div>FOLIO: {nuevo_folio}</div>
                <div>PAQUETERIA: {f_paqueteria}</div>
                <div>FECHA: {f_fecha}</div>
            </div>
            <div style="display: flex; margin-top: 20px;">
                <div style="width: 50%; border-right: 1px solid black; padding-right: 10px;">
                    <div class="header-red">DESTINATARIO</div>
                    <div style="background-color: #fff3cd; padding: 5px;">
                        <b>{f_hotel}</b><br>{f_calle}<br>
                        {f_colonia}, {f_cp}<br>{f_ciudad}, {f_estado}<br>
                        CONTACTO: {f_contacto}
                    </div>
                </div>
                <div style="width: 50%; padding-left: 10px;">
                    <div class="sub-header">REMITENTE</div>
                    Jabones y productos Especializados<br>C. Cernícalo 155, La Aurora<br>CP 44460, Guadalajara, Jal.
                </div>
            </div>
            <table>
                <tr style="background-color: #444; color: white;">
                    <th>PRODUCTO</th><th>CANTIDAD</th><th>UM</th><th>DESCRIPCIÓN</th>
                </tr>
                {tabla_html}
            </table>
            <div style="margin-top: 20px;"><b>COMENTARIOS:</b><br>{f_comentarios}</div>
            <div style="margin-top: 50px; text-align: center;">
                __________________________________<br>RECIBO DE CONFORMIDAD DEL CLIENTE
            </div>
        </body>
        </html>
        """

        # --- BOTONES DE ACCIÓN (3 COLUMNAS) ---
        st.success("¡Datos preparados con éxito!")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            if st.button("🖨️ IMPRIMIR AHORA"):
                components.html(f"<html><body>{form_pt_html}<script>window.print();</script></body></html>", height=0)
        
        with c2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_registro.to_excel(writer, index=False)
            st.download_button("📥 DESCARGAR EXCEL", output.getvalue(), f"Envio_{nuevo_folio}.xlsx")
            
        with c3:
            if st.button("🔄 NUEVO REGISTRO"):
                st.rerun()
