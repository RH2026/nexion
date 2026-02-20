import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JYPESA Control", layout="centered")

if 'folio_auto' not in st.session_state:
    st.session_state.folio_auto = datetime.now().strftime("%Y%m%d%H%M%S")

# CSS para estilo en pantalla
st.markdown("""
    <style>
    .block-container { max-width: 1000px; padding-top: 2rem; }
    .header-tabla { background-color: #444; color: white; padding: 8px; text-align: center; font-weight: bold; border-radius: 5px 5px 0 0; margin-bottom: 10px; }
    .stCheckbox { margin-bottom: -15px; }
    .prod-label { font-size: 13px; font-weight: 500; padding-top: 5px; line-height: 1.2; }
    .especial-header { background-color: #222; color: white; padding: 5px; text-align: center; font-weight: bold; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- LISTADO DE PRODUCTOS ACTUALIZADO ---
amenidades_list = [
    "Kit Elements", "Kit Almond", "Kit Biogena", "Kit Cava", 
    "Kit Persa", "Kit Lavarino", "Kit Botánicos", 
    "Accesorios Ecologicos", "Accesorios Lavarino"
]

dispensadores_list = [
    "Dispensador Almond", "Dispensador Biogena", "Dispensador Cava", 
    "Dispensador Persa", "Dispensador Botánicos L", "Dispensador Dove", 
    "Dispensador Biogena 400ml", "Llave Magnetica", "Rack Dove", 
    "Rack JH Color Blanco de 2 pzas", "Rack JH Color Blanco de 1 pzas", 
    "Soporte dob INOX Cap lock", "Soporte Ind INOX Cap lock"
]

# --- FORMULARIO APP ---
st.markdown("<h1 style='color: #1E1E1E;'>JYPESA</h1>", unsafe_allow_html=True)
st.markdown("<p style='margin-top: -20px; font-weight: bold;'>ENVÍO DE MUESTRAS</p>", unsafe_allow_html=True)
st.title("📦 Orden de Envío")

c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 1])
with c1: f_folio = st.text_input("FOLIO (AUTO)", value=st.session_state.folio_auto, disabled=True)
with c2: f_paqueteria = st.selectbox("FORMA DE ENVÍO", ["Envio Pagado", "Envio por cobrar", "Entrega Personal"])
with c3: f_entrega = st.selectbox("TIPO DE ENTREGA", ["Domicilio", "Ocurre Oficina"])
with c4: f_fecha = st.date_input("FECHA", date.today())

st.markdown("---")

col_rem, col_dest = st.columns(2)
with col_rem:
    st.markdown('<div style="background:black;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:3px;">REMITENTE</div>', unsafe_allow_html=True)
    st.text_input("Nombre", "Jabones y Productos Especializados", disabled=True)
    st.text_input("Calle y Número", "C. Cernícalo 155", disabled=True)
    cr1, cr2 = st.columns(2)
    with cr1: st.text_input("Colonia/Del.", "La Aurora", disabled=True)
    with cr2: st.text_input("C.P.", "44460", disabled=True)
    cr3, cr4 = st.columns(2)
    with cr3: f_atencion_rem = st.text_input("Atención", "Rigoberto Hernandez", key="rem_atn")
    with cr4: f_tel_rem = st.text_input("Tel.", "3319753122", key="rem_tel")
    f_solicitante = st.text_input("Solicitante / Agente", "JYPESA", key="rem_sol")

with col_dest:
    st.markdown('<div style="background:#b30000;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:3px;">DESTINATARIO / NOMBRE DEL HOTEL</div>', unsafe_allow_html=True)
    f_hotel = st.text_input("Hotel", key="dest_hotel")
    f_calle = st.text_input("Calle, Número y Cruce", key="dest_calle")
    ci1, ci2 = st.columns(2)
    with ci1: f_colonia = st.text_input("Colonia", key="dest_col")
    with ci2: f_cp = st.text_input("Código Postal", key="dest_cp")
    ci3, ci4 = st.columns(2)
    with ci3: f_ciudad = st.text_input("Ciudad", key="dest_ciu")
    with ci4: f_estado = st.text_input("Estado", key="dest_est")
    ci5, ci6 = st.columns(2)
    with ci5: f_contacto = st.text_input("Contacto", key="dest_cont")
    with ci6: f_telefono = st.text_input("Teléfono", key="dest_tel")

st.markdown("---")
st.subheader("🛒 Selección de Catálogo")

seleccionados = []
col_prod1, col_prod2 = st.columns(2)

def render_cat(lista, columna, titulo, tipo):
    with columna:
        st.markdown(f'<div class="header-tabla">{titulo}</div>', unsafe_allow_html=True)
        h1, h2, h3 = st.columns([2.5, 1, 1.2])
        h1.caption("PRODUCTO")
        h2.caption("SEL.")
        h3.caption("CANT.")
        for p in lista:
            r1, r2, r3 = st.columns([2.5, 1, 1.2])
            r1.markdown(f"<div class='prod-label'>{p}</div>", unsafe_allow_html=True)
            sel = r2.checkbox("", key=f"ch_{tipo}_{p}", label_visibility="collapsed")
            cant = r3.number_input("", min_value=0, step=1, key=f"ca_{tipo}_{p}", label_visibility="collapsed", disabled=not sel)
            if sel and cant > 0:
                seleccionados.append({"desc": p, "um": "PZAS", "cant": cant, "cod": "-"})

render_cat(amenidades_list, col_prod1, "KITS Y ACCESORIOS", "kits")
render_cat(dispensadores_list, col_prod2, "DISPENSADORES Y RACKS", "disp")

st.markdown('<div class="especial-header">✨ PRODUCTOS ESPECIALES / CÓDIGOS</div>', unsafe_allow_html=True)
if 'rows_especiales' not in st.session_state: st.session_state.rows_especiales = 3

especiales_data = []
he1, he2, he3, he4 = st.columns([0.8, 0.8, 1, 2.4])
he1.caption("CANT.")
he2.caption("U.M.")
he3.caption("CÓDIGO")
he4.caption("DESCRIPCIÓN")

for i in range(st.session_state.rows_especiales):
    re1, re2, re3, re4 = st.columns([0.8, 0.8, 1, 2.4])
    esp_cant = re1.number_input("", min_value=0, key=f"e_can_{i}", label_visibility="collapsed")
    esp_um = re2.text_input("", placeholder="PZA", key=f"e_um_{i}", label_visibility="collapsed")
    esp_cod = re3.text_input("", placeholder="CÓD.", key=f"e_cod_{i}", label_visibility="collapsed")
    esp_desc = re4.text_input("", placeholder="Descripción...", key=f"e_des_{i}", label_visibility="collapsed")
    if esp_cant > 0 and esp_desc:
        especiales_data.append({"cant": esp_cant, "um": esp_um.upper(), "cod": esp_cod.upper(), "desc": esp_desc.upper()})

if st.button("➕ Más filas"):
    st.session_state.rows_especiales += 2
    st.rerun()

st.markdown("---")
f_comentarios = st.text_area("💬 COMENTARIOS ADICIONALES", height=70)

# --- LÓGICA DE IMPRESIÓN CORREGIDA ---
all_prods = seleccionados + especiales_data
filas_html = "".join([f"<tr><td style='padding: 8px; border: 1px solid black;'>{d['desc']}</td><td style='text-align:center; border: 1px solid black;'>{d['cod']}</td><td style='text-align:center; border: 1px solid black;'>{d['um']}</td><td style='text-align:center; border: 1px solid black;'>{d['cant']}</td></tr>" for d in all_prods])

html_impresion = f"""
<div id="printable-area" style="font-family:Arial; border:2px solid black; padding:15px; width:700px; min-height:950px; margin:auto; position:relative; box-sizing:border-box; background: white;">
    
    <style>
        @media print {{
            @page {{ size: letter; margin: 0; }}
            body {{ margin: 0; padding: 0; }}
            #printable-area {{ border: 2px solid black !important; width: 100% !important; height: 99vh !important; margin: 0 !important; padding: 20px !important; }}
        }}
    </style>

    <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px;">
        <h1 style="margin: 0; font-size: 28px; letter-spacing: 1px;">JYPESA</h1>
        <h2 style="margin: 0; font-size: 16px; text-decoration: underline;">ENVÍO DE MUESTRAS</h2>
        <div style="width: 50px;"></div>
    </div>

    <table style="width:100%; border-collapse:collapse; margin-bottom:5px; font-size: 11px;">
        <tr><td style="border:1px solid black;padding:4px"><b>FOLIO:</b> {f_folio}</td>
            <td style="border:1px solid black;padding:4px"><b>ENVÍO:</b> {f_paqueteria}</td>
            <td style="border:1px solid black;padding:4px"><b>ENTREGA:</b> {f_entrega}</td>
            <td style="border:1px solid black;padding:4px"><b>FECHA:</b> {f_fecha}</td></tr>
    </table>

    <div style="display:flex; gap:5px; margin-top:5px;">
        <div style="flex:1; border:1px solid black;">
            <div style="background:black; color:white; text-align:center; font-weight:bold; font-size:11px;">REMITENTE</div>
            <div style="padding:4px; font-size:10px;">
                <b>Jabones y Productos Especializados</b><br>C. Cernícalo 155, La Aurora C.P.: 44460<br>Guadalajara, Jalisco<br>ATN: {f_atencion_rem} | TEL: {f_tel_rem}<br>SOLICITÓ: {f_solicitante}
            </div>
        </div>
        <div style="flex:1; border:1px solid black;">
            <div style="background:#b30000; color:white; text-align:center; font-weight:bold; font-size:11px;">DESTINATARIO</div>
            <div style="padding:4px; font-size:10px;">
                <b>{f_hotel}</b><br>{f_calle}<br>Col: {f_colonia} C.P.: {f_cp}<br>{f_ciudad}, {f_estado}<br>ATN: {f_contacto} | TEL: {f_telefono}
            </div>
        </div>
    </div>

    <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:11px;">
        <thead>
            <tr style="background:#444; color:white;">
                <th style="padding: 8px; border: 1px solid black;">DESCRIPCIÓN DEL PRODUCTO</th>
                <th style="border: 1px solid black;">CÓDIGO</th>
                <th style="border: 1px solid black;">U.M.</th>
                <th style="border: 1px solid black;">CANT.</th>
            </tr>
        </thead>
        <tbody>
            {filas_html if filas_html else '<tr><td colspan="4" style="text-align:center; padding: 20px;">Sin productos seleccionados</td></tr>'}
        </tbody>
    </table>

    <div style="border:1px solid black; padding:8px; margin-top:10px; font-size:11px; min-height: 50px;">
        <b>COMENTARIOS ADICIONALES:</b><br>{f_comentarios}
    </div>
    
    <div style="position:absolute; bottom:30px; left:20px; right:20px;">
        <div style="text-align:center; font-size:11px; font-weight:bold; margin-bottom:25px; border-bottom: 1px solid black; display: inline-block; width: 100%; padding-bottom: 5px;">
            RECIBO DE CONFORMIDAD DEL CLIENTE
        </div>
        <div style="display:flex; justify-content:space-between; text-align:center; font-size:10px; margin-top: 10px;">
            <div style="width:30%;">__________________________<br>FECHA DE RECIBO</div>
            <div style="width:35%;">__________________________<br>NOMBRE Y FIRMA</div>
            <div style="width:30%;">__________________________<br>SELLO DE RECIBIDO</div>
        </div>
        <div style="margin-top:25px; border-top: 1px solid #444; padding-top:5px; text-align: right; font-size: 9px; color: #666;">
            SISTEMA DE CONTROL DE MUESTRAS - JYPESA 2026
        </div>
    </div>
</div>
"""

# --- BOTONES ---
st.markdown("<br>", unsafe_allow_html=True)
b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    if st.button("🚀 GUARDAR REGISTRO", type="primary", use_container_width=True):
        if not f_hotel: st.warning("⚠️ Ingresa el hotel.")
        else: st.success("✅ Registro Guardado."); time.sleep(1); st.rerun()
with b_col2:
    if st.button("🖨️ IMPRIMIR REPORTE", use_container_width=True):
        components.html(f"<html><body>{html_impresion}<script>window.print();</script></body></html>", height=0)
with b_col3:
    if st.button("🔄 NUEVO REGISTRO", use_container_width=True):
        st.session_state.folio_auto = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.rows_especiales = 3
        st.rerun()
