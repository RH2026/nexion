import streamlit as st
import pandas as pd
from datetime import date
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
# Volvemos a un ancho más cómodo pero controlado
st.set_page_config(page_title="JYPESA Control", layout="centered")

# CSS Ajustado: Un poco más ancho (1000px) y mejor espaciado
st.markdown("""
    <style>
    .block-container { max-width: 1000px; padding-top: 2rem; }
    .header-tabla { background-color: #444; color: white; padding: 8px; text-align: center; font-weight: bold; border-radius: 5px 5px 0 0; margin-bottom: 10px; }
    .stCheckbox { margin-bottom: -15px; }
    /* Estilo para los nombres de productos para que no se corten */
    .prod-label { font-size: 13px; font-weight: 500; padding-top: 5px; line-height: 1.2; }
    </style>
""", unsafe_allow_html=True)

# --- LISTADO DE PRODUCTOS ---
amenidades_kits = [
    "Kit Elements", "Kit Almond", "Kit Biogena", "Kit Cava", "Kit Persa", 
    "Kit Lavarino", "Kit Botánicos", "Accesorios Ecologicos", "Accesorios Lavarino"
]

dispensadores_racks = [
    "Dispensador Almond", "Dispensador Biogena", "Dispensador Cava", "Dispensador Persa", 
    "Dispensador Botánicos L", "Dispensador Dove", "Dispensador Biogena 400ml",
    "Llave Magnetica", "Rack Dove", "Rack JH Blanco 2 pzas", 
    "Rack JH Blanco 1 pzas", "Soporte dob INOX", "Soporte Ind INOX"
]

# --- FORMULARIO ---
st.title("📦 Orden de Envío")

# Fila superior
c1, c2, c3 = st.columns([1, 1.5, 1])
with c1: f_folio = st.text_input("FOLIO", key="main_folio")
with c2: f_paqueteria = st.text_input("PAQUETERÍA / FORMA DE ENVÍO", key="main_paq")
with c3: f_fecha = st.date_input("FECHA", date.today(), key="main_date")

st.markdown("---")

col_izq, col_der = st.columns(2)
with col_izq:
    st.markdown('<div style="background:#b30000;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:3px;">DESTINATARIO</div>', unsafe_allow_html=True)
    f_hotel = st.text_input("Hotel", key="dest_hotel")
    f_calle = st.text_input("Calle y Número", key="dest_calle")
    ci1, ci2 = st.columns(2)
    with ci1: f_contacto = st.text_input("Contacto", key="dest_cont")
    with ci2: f_telefono = st.text_input("Teléfono", key="dest_tel")

with col_der:
    st.markdown('<div style="background:black;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:3px;">REMITENTE</div>', unsafe_allow_html=True)
    st.text_input("Nombre", "Jabones y productos Especializados", disabled=True, key="rem_nom")
    st.text_input("Dirección", "C. Cernícalo 155, La Aurora", disabled=True, key="rem_dir")
    f_solicitante = st.text_input("Solicitante", "JYPESA", key="rem_sol")

st.markdown("---")
st.subheader("🛒 Selección de Artículos")

seleccionados = {}
col_prod1, col_prod2 = st.columns(2)

def render_seccion(lista, columna, titulo):
    with columna:
        st.markdown(f'<div class="header-tabla">{titulo}</div>', unsafe_allow_html=True)
        # Encabezado de columnas
        h1, h2, h3 = st.columns([2.5, 1, 1.2])
        h1.caption("PRODUCTO")
        h2.caption("SEL.")
        h3.caption("CANT.")
        
        for p in lista:
            r1, r2, r3 = st.columns([2.5, 1, 1.2])
            r1.markdown(f"<div class='prod-label'>{p}</div>", unsafe_allow_html=True)
            sel = r2.checkbox("", key=f"ch_{p}", label_visibility="collapsed")
            cant = r3.number_input("", min_value=0, step=1, key=f"ca_{p}", label_visibility="collapsed", disabled=not sel)
            if sel and cant > 0:
                seleccionados[p] = cant

render_seccion(amenidades_kits, col_prod1, "AMENIDADES Y KITS")
render_seccion(dispensadores_racks, col_prod2, "DISPENSADORES Y RACKS")

st.markdown("---")
f_comentarios = st.text_area("💬 COMENTARIOS / NOTAS", height=80, key="txt_coment")

# --- LÓGICA DE IMPRESIÓN ---
filas_html = "".join([f"<tr><td>{p}</td><td>PZAS</td><td style='text-align:center'>{c}</td></tr>" for p, c in seleccionados.items()])
html_impresion = f"""
<div style="font-family:Arial; border:1px solid black; padding:20px; width:750px; margin:auto;">
    <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:5px;">
        <span><b>FOLIO:</b> {f_folio}</span>
        <span><b>ENVÍO:</b> {f_paqueteria}</span>
        <span><b>FECHA:</b> {f_fecha}</span>
    </div>
    <div style="display:flex; margin-top:10px; gap:10px;">
        <div style="flex:1; border:1px solid black;">
            <div style="background:#b30000; color:white; text-align:center; font-weight:bold; font-size:12px;">DESTINATARIO</div>
            <div style="padding:10px; font-size:12px;"><b>{f_hotel}</b><br>{f_calle}<br>ATN: {f_contacto}<br>TEL: {f_telefono}</div>
        </div>
        <div style="flex:1; border:1px solid black;">
            <div style="background:black; color:white; text-align:center; font-weight:bold; font-size:12px;">REMITENTE</div>
            <div style="padding:10px; font-size:12px;">Jabones y productos Especializados<br>C. Cernícalo 155, La Aurora<br>SOLICITÓ: {f_solicitante}</div>
        </div>
    </div>
    <table style="width:100%; border-collapse:collapse; margin-top:15px; font-size:12px;" border="1">
        <tr style="background:#444; color:white;"><th>PRODUCTO</th><th>U.M.</th><th>CANTIDAD</th></tr>
        {filas_html if filas_html else '<tr><td colspan="3" style="text-align:center">No se seleccionaron productos</td></tr>'}
    </table>
    <p style="font-size:12px; border:1px solid black; padding:5px; margin-top:10px;"><b>NOTAS:</b> {f_comentarios}</p>
    <div style="margin-top:50px; text-align:center; font-size:11px;">
        <div style="display:flex; justify-content:space-around;">
            <div>__________________________<br>FECHA</div>
            <div>__________________________<br>NOMBRE Y FIRMA</div>
            <div>__________________________<br>SELLO</div>
        </div>
    </div>
</div>
"""

# --- BOTONES DE ACCIÓN ---
st.markdown("<br>", unsafe_allow_html=True)
b_col1, b_col2, b_col3 = st.columns(3)

with b_col1:
    if st.button("🚀 GUARDAR REGISTRO", type="primary", use_container_width=True, key="btn_save"):
        if not f_hotel:
            st.warning("⚠️ Por favor ingresa el nombre del hotel.")
        else:
            st.success("✅ Registro guardado en sistema.")
            time.sleep(1.2)
            st.rerun()

with b_col2:
    if st.button("🖨️ IMPRIMIR REPORTE", use_container_width=True, key="btn_print"):
        components.html(f"<html><body>{html_impresion}<script>window.print();</script></body></html>", height=0)

with b_col3:
    if st.button("🔄 NUEVO REGISTRO", use_container_width=True, key="btn_new"):
        st.rerun()
