import streamlit as st
import pandas as pd
from datetime import date
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JYPESA Control", layout="wide")

# CSS para compactar y dar estilo
st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] { gap: 1rem; }
    .stCheckbox { margin-bottom: -15px; }
    .header-tabla { background-color: #444; color: white; padding: 5px; text-align: center; font-weight: bold; font-size: 14px; border-radius: 5px 5px 0 0; }
    </style>
""", unsafe_allow_html=True)

# --- LISTADO DE PRODUCTOS ORGANIZADO ---
amenidades_kits = [
    "Kit Elements", "Kit Almond", "Kit Biogena", "Kit Cava", "Kit Persa", 
    "Kit Lavarino", "Kit Botánicos", "Accesorios Ecologicos", "Accesorios Lavarino"
]

dispensadores_racks = [
    "Dispensador Almond", "Dispensador Biogena", "Dispensador Cava", "Dispensador Persa", 
    "Dispensador Botánicos L", "Dispensador Dove", "Dispensador Biogena 400ml",
    "Llave Magnetica", "Rack Dove", "Rack JH Color Blanco de 2 pzas", 
    "Rack JH Color Blanco de 1 pzas", "Soporte dob INOX Cap lock", "Soporte Ind INOX Cap lock"
]

# --- DATOS GENERALES ---
c1, c2, c3 = st.columns([1, 2, 1])
with c1: f_folio = st.text_input("FOLIO")
with c2: f_paqueteria = st.text_input("PAQUETERIA / FORMA DE ENVIO")
with c3: f_fecha = st.date_input("FECHA", date.today())

col_izq, col_der = st.columns(2)
with col_izq:
    st.markdown('<div style="background:#b30000;color:white;text-align:center;font-weight:bold;padding:5px">DESTINATARIO</div>', unsafe_allow_html=True)
    f_hotel = st.text_input("Nombre del Hotel")
    f_calle = st.text_input("Calle y Número")
    c_i1, c_i2 = st.columns(2)
    with c_i1: f_contacto = st.text_input("Contacto")
    with c_i2: f_telefono = st.text_input("Teléfono")

with col_der:
    st.markdown('<div style="background:black;color:white;text-align:center;font-weight:bold;padding:5px">REMITENTE</div>', unsafe_allow_html=True)
    st.text_input("Nombre", "Jabones y productos Especializados", disabled=True)
    st.text_input("Dirección", "C. Cernícalo 155, La Aurora", disabled=True)
    f_solicitante = st.text_input("Solicitante", "JYPESA")

st.markdown("---")

# --- SECCIÓN DE PRODUCTOS EN DOS COLUMNAS ---
st.markdown("### 📦 SELECCIÓN DE ARTÍCULOS")

seleccionados = {}

col_prod1, col_prod2 = st.columns(2)

def generar_fila_producto(lista):
    # Encabezado de la mini-tabla
    h1, h2, h3 = st.columns([2.5, 1, 1])
    h1.markdown("**PRODUCTO**")
    h2.markdown("**SEL.**")
    h3.markdown("**CANT.**")
    
    for p in lista:
        r1, r2, r3 = st.columns([2.5, 1, 1])
        with r1: st.markdown(f"<div style='font-size:12px; padding-top:5px;'>{p}</div>", unsafe_allow_html=True)
        with r2: sel = st.checkbox("", key=f"sel_{p}", label_visibility="collapsed")
        with r3: cant = st.number_input("", min_value=0, step=1, key=f"can_{p}", label_visibility="collapsed", disabled=not sel)
        if sel and cant > 0:
            seleccionados[p] = cant

with col_prod1:
    st.markdown('<div class="header-tabla">AMENIDADES Y KITS</div>', unsafe_allow_html=True)
    generar_fila_producto(amenidades_kits)

with col_prod2:
    st.markdown('<div class="header-tabla">DISPENSADORES Y SOPORTES</div>', unsafe_allow_html=True)
    generar_fila_producto(dispensadores_racks)

st.markdown("---")
f_comentarios = st.text_area("COMENTARIOS / NOTAS ESPECIALES", height=70)

# --- HTML PARA IMPRESIÓN ---
filas_html = "".join([f"<tr><td>{p}</td><td>PZAS</td><td>{c}</td></tr>" for p, c in seleccionados.items()])
html_impresion = f"""
<div style="font-family:Arial; border:2px solid black; padding:15px; width:750px; margin:auto;">
    <table style="width:100%; border-collapse:collapse;">
        <tr><td style="border:1px solid black;padding:5px"><b>FOLIO:</b> {f_folio}</td>
            <td style="border:1px solid black;padding:5px"><b>ENVÍO:</b> {f_paqueteria}</td>
            <td style="border:1px solid black;padding:5px"><b>FECHA:</b> {f_fecha}</td></tr>
    </table>
    <div style="display:flex; margin-top:10px; gap:5px;">
        <div style="flex:1; border:1px solid black;">
            <div style="background:#b30000; color:white; text-align:center; font-weight:bold; font-size:12px;">DESTINATARIO</div>
            <div style="padding:5px; font-size:11px;"><b>{f_hotel}</b><br>{f_calle}<br>ATN: {f_contacto} | TEL: {f_telefono}</div>
        </div>
        <div style="flex:1; border:1px solid black;">
            <div style="background:black; color:white; text-align:center; font-weight:bold; font-size:12px;">REMITENTE</div>
            <div style="padding:5px; font-size:11px;">Jabones y productos Especializados<br>C. Cernícalo 155, La Aurora<br>SOLICITÓ: {f_solicitante}</div>
        </div>
    </div>
    <table style="width:100%; border-collapse:collapse; margin-top:10px; text-align:center; font-size:12px;">
        <tr style="background:#444; color:white;"><th>PRODUCTO</th><th>U.M.</th><th>CANTIDAD</th></tr>
        {filas_html}
    </table>
    <div style="border:1px solid black; margin-top:10px; padding:5px; font-size:11px;"><b>COMENTARIOS:</b> {f_comentarios}</div>
    <div style="margin-top:30px; text-align:center; font-size:10px;">RECIBO DE CONFORMIDAD DEL CLIENTE<br><br>____________________________________<br>NOMBRE Y FIRMA</div>
</div>
"""

# --- BOTONES DE ACCIÓN ---
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("🚀 GUARDAR REGISTRO", type="primary", use_container_width=True):
        st.success("¡Registro guardado exitosamente!")
        time.sleep(1.5); st.rerun()
with b2:
    if st.button("🖨️ IMPRIMIR REPORTE", use_container_width=True):
        components.html(f"<html><body>{html_impresion}<script>window.print();</script></body></html>", height=0)
with b3:
    if st.button("🔄 NUEVO REGISTRO", use_container_width=True):
        st.rerun()

with b3:
    if st.button("🔄 NUEVO REGISTRO", use_container_width=True):
        st.rerun()
