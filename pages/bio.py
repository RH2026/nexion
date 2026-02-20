¡Entiendo perfectamente, amor! Esa lista estaba ocupando demasiado espacio y se veía muy pesada. Para que se vea "chingón", vamos a usar tablas de HTML dentro de Streamlit. Esto nos permite tener casillas de verificación y campos de entrada en una cuadrícula compacta y elegante, igualito a tu formato de Excel.

Aquí tienes el código con un diseño mucho más profesional, compacto y visualmente limpio:

Python
import streamlit as st
import pandas as pd
from datetime import date
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JYPESA Control", layout="wide")

# CSS para que la tabla de entrada se vea impecable
st.markdown("""
    <style>
    .tabla-productos { width: 100%; border-collapse: collapse; font-family: sans-serif; }
    .tabla-productos th { background-color: #444; color: white; padding: 8px; text-align: left; }
    .tabla-productos td { border: 1px solid #ddd; padding: 4px; }
    /* Compactar inputs de Streamlit */
    div[data-testid="stHorizontalBlock"] { gap: 0rem; }
    .stNumberInput input { padding: 2px !important; }
    </style>
""", unsafe_allow_html=True)

# --- LISTA DE PRODUCTOS ---
productos = [
    "ELEMENTS", "ALMON OLIVE", "BIOGENA", "CAVA", "LAVANDA BOTANICUS", 
    "LAVARIVO", "BOTANICUS", "PERSEA", "RAINFOREST", "DOVE", "ECOLOGICOS"
]

# --- ENCABEZADO Y DATOS ---
c1, c2, c3 = st.columns([1, 2, 1])
with c1: f_folio = st.text_input("FOLIO")
with c2: f_paqueteria = st.text_input("PAQUETERIA / FORMA DE ENVIO")
with c3: f_fecha = st.date_input("FECHA", date.today())

col_izq, col_der = st.columns(2)
with col_izq:
    st.markdown('<div style="background:#b30000;color:white;text-align:center;font-weight:bold;padding:5px">DESTINATARIO</div>', unsafe_allow_html=True)
    f_hotel = st.text_input("Hotel")
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

# --- DISEÑO COMPACTO DE PRODUCTOS (CHINGÓN) ---
st.markdown("### 📦 SELECCIÓN DE PRODUCTOS (AMENIDADES)")

# Creamos encabezados manuales para que parezca una tabla real
h1, h2, h3 = st.columns([3, 1, 1])
h1.markdown("**PRODUCTO**")
h2.markdown("**¿INCLUIR?**")
h3.markdown("**CANTIDAD**")

seleccionados = {}

# Iteramos de forma compacta
for p in productos:
    row1, row2, row3 = st.columns([3, 1, 1])
    with row1:
        st.markdown(f"<div style='padding-top:5px'>{p}</div>", unsafe_allow_html=True)
    with row2:
        check = st.checkbox("Seleccionar", key=f"ch_{p}", label_visibility="collapsed")
    with row3:
        cant = st.number_input("Cant", min_value=0, step=1, key=f"ct_{p}", label_visibility="collapsed", disabled=not check)
    
    if check and cant > 0:
        seleccionados[p] = cant

f_comentarios = st.text_area("COMENTARIOS", height=70)

# --- LÓGICA DE IMPRESIÓN ---
filas_html = "".join([f"<tr><td>{p}</td><td>PZAS</td><td></td><td>{c}</td></tr>" for p, c in seleccionados.items()])
html_impresion = f"""
    <div style="font-family:Arial; border:2px solid black; padding:20px; width:750px;">
        <h2 style="text-align:center; margin-top:0;">ORDEN DE ENVÍO</h2>
        <table style="width:100%; border-collapse:collapse; margin-bottom:10px;">
            <tr><td style="border:1px solid black;padding:5px"><b>FOLIO:</b> {f_folio}</td>
                <td style="border:1px solid black;padding:5px"><b>ENVÍO:</b> {f_paqueteria}</td>
                <td style="border:1px solid black;padding:5px"><b>FECHA:</b> {f_fecha}</td></tr>
        </table>
        <div style="display:flex; gap:10px;">
            <div style="flex:1; border:1px solid black;">
                <div style="background:#b30000; color:white; padding:3px; text-align:center;">DESTINATARIO</div>
                <div style="padding:5px; font-size:13px;"><b>{f_hotel}</b><br>{f_calle}<br>ATN: {f_contacto}<br>TEL: {f_telefono}</div>
            </div>
            <div style="flex:1; border:1px solid black;">
                <div style="background:black; color:white; padding:3px; text-align:center;">REMITENTE</div>
                <div style="padding:5px; font-size:13px;">Jabones y productos Especializados<br>C. Cernícalo 155, La Aurora<br>SOLICITÓ: {f_solicitante}</div>
            </div>
        </div>
        <table style="width:100%; border-collapse:collapse; margin-top:15px; text-align:center;">
            <tr style="background:#444; color:white;"><th>PRODUCTO</th><th>UM</th><th>CÓDIGO</th><th>CANTIDAD</th></tr>
            {filas_html}
        </table>
        <div style="border:1px solid black; margin-top:10px; padding:10px; height:60px;"><b>COMENTARIOS:</b> {f_comentarios}</div>
        <div style="margin-top:40px; text-align:center; font-size:12px;">RECIBO DE CONFORMIDAD DEL CLIENTE<br><br>____________________________________<br>NOMBRE Y FIRMA</div>
    </div>
"""

# --- BOTONES DE ACCIÓN ---
st.markdown("---")
b1, b2, b3 = st.columns(3)

with b1:
    if st.button("🚀 GUARDAR REGISTRO", type="primary", use_container_width=True):
        st.success("Guardado en sistema")
        time.sleep(1)
        st.rerun()

with b2:
    if st.button("🖨️ IMPRIMIR REPORTE", use_container_width=True):
        components.html(f"<html><body>{html_impresion}<script>window.print();</script></body></html>", height=0)

with b3:
    if st.button("🔄 NUEVO REGISTRO", use_container_width=True):
        st.rerun()
