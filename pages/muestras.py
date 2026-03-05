import streamlit as st
import pandas as pd
import requests
import base64
import time
from io import BytesIO
from datetime import date
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE GITHUB ---
GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_PATH = "CEE.csv"  # Tu nueva matriz
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

# --- FUNCIONES GITHUB ---
def obtener_datos_github():
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = r.json()
            df = pd.read_csv(BytesIO(base64.b64decode(content['content'])))
            return df, content['sha']
    except:
        pass
    return pd.DataFrame(), None

def subir_a_github(df, sha, msg):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    csv_string = df.to_csv(index=False)
    payload = {"message": msg, "content": base64.b64encode(csv_string.encode()).decode(), "sha": sha}
    return requests.put(url, json=payload, headers=headers).status_code == 200

# --- FUNCIÓN PARA GENERAR EL HTML DE IMPRESIÓN ---
def generar_html_impresion(folio, fecha, hotel, destino, contacto, solicito, paqueteria, paq_nombre, guia, costo, cajas):
    html = f"""
    <div id="printable-area" style="font-family:Arial; border:2px solid black; padding:15px; width:700px; margin:auto; background: white; color: black;">
        <div style="display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px; border-bottom: 2px solid black; padding-bottom:10px;">
            <h1 style="margin: 0; font-size: 28px;">JYPESA</h1>
            <div style="text-align:right">
                <h2 style="margin: 0; font-size: 16px;">REPORTE DE COSTO ENVÍO ESPECIAL</h2>
                <p style="margin:0; font-size:12px;"><b>FOLIO: {folio}</b></p>
            </div>
        </div>
        
        <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size: 12px;">
            <tr>
                <td style="border:1px solid black;padding:8px; width:50%;"><b>FECHA:</b> {fecha}</td>
                <td style="border:1px solid black;padding:8px; width:50%;"><b>SOLICITÓ:</b> {solicito}</td>
            </tr>
            <tr>
                <td style="border:1px solid black;padding:8px;"><b>HOTEL:</b> {hotel}</td>
                <td style="border:1px solid black;padding:8px;"><b>DESTINO:</b> {destino}</td>
            </tr>
            <tr>
                <td style="border:1px solid black;padding:8px;"><b>CONTACTO:</b> {contacto}</td>
                <td style="border:1px solid black;padding:8px;"><b>MODALIDAD:</b> {paqueteria}</td>
            </tr>
        </table>

        <table style="width:100%; border-collapse:collapse; margin-top:20px; font-size: 12px; text-align:center;">
            <tr style="background:#eee;">
                <th style="border:1px solid black;padding:8px;">PAQUETERÍA</th>
                <th style="border:1px solid black;padding:8px;">NÚMERO DE GUÍA</th>
                <th style="border:1px solid black;padding:8px;">CAJAS</th>
                <th style="border:1px solid black;padding:8px;">COSTO ENVÍO</th>
            </tr>
            <tr>
                <td style="border:1px solid black;padding:8px;">{paq_nombre}</td>
                <td style="border:1px solid black;padding:8px;">{guia}</td>
                <td style="border:1px solid black;padding:8px;">{cajas}</td>
                <td style="border:1px solid black;padding:8px;">${costo:,.2f}</td>
            </tr>
        </table>
        
        <div style="margin-top:40px; text-align:center; font-size:10px;">
            <p>__________________________<br>FIRMA RESPONSABLE</p>
        </div>
    </div>
    """
    return html

# --- CARGA DE DATOS ---
df_actual, sha_actual = obtener_datos_github()
nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1

st.title("📦 Costos de Envíos Especiales (CEE)")

# --- INTERFAZ DE CAPTURA ---
with st.form("form_cee"):
    c1, c2, c3 = st.columns([0.5, 1, 1])
    f_folio = c1.text_input("FOLIO", value=str(nuevo_folio), disabled=True)
    f_fecha = c2.date_input("FECHA", date.today())
    f_solicito = c3.text_input("QUIEN SOLICITÓ", placeholder="Nombre del agente").upper()

    f_hotel = st.text_input("NOMBRE DEL HOTEL").upper()
    f_destino = st.text_input("DESTINO (DIRECCIÓN / CIUDAD)").upper()
    
    col1, col2 = st.columns(2)
    f_contacto = col1.text_input("CONTACTO / TELÉFONO").upper()
    f_paq_tipo = col2.selectbox("MODALIDAD", ["ENVIO PAGADO", "ENVIO POR COBRAR", "ENTREGA PERSONAL"])

    st.divider()
    
    cx1, cx2, cx3, cx4 = st.columns(4)
    f_paq_nombre = cx1.selectbox("PAQUETERÍA", ["TRES GUERRAS", "ONE", "POTOSINOS", "CASTORES", "FEDEX", "PAQMEX", "TINY PACK"])
    f_guia = cx2.text_input("NÚMERO DE GUÍA").upper()
    f_cajas = cx3.number_input("CANTIDAD CAJAS", min_value=1, step=1)
    f_costo = cx4.number_input("COSTO GUÍA ($)", min_value=0.0, step=10.0)

    btn_guardar = st.form_submit_button("💾 GUARDAR Y REGISTRAR COSTO", use_container_width=True)

if btn_guardar:
    if not f_hotel or not f_solicito:
        st.error("Por favor llena el Hotel y quien solicita.")
    else:
        nuevo_reg = {
            "FOLIO": nuevo_folio,
            "FECHA": f_fecha.strftime("%Y-%m-%d"),
            "NOMBRE DEL HOTEL": f_hotel,
            "DESTINO": f_destino,
            "CONTACTO": f_contacto,
            "SOLICITO": f_solicito,
            "PAQUETERIA": f_paq_tipo,
            "PAQUETERIA_NOMBRE": f_paq_nombre,
            "NUMERO_GUIA": f_guia,
            "COSTO_GUIA": f_costo,
            "CAJAS": f_cajas
        }
        
        df_final = pd.concat([df_actual, pd.DataFrame([nuevo_reg])], ignore_index=True)
        if subir_a_github(df_final, sha_actual, f"Folio CEE {nuevo_folio}"):
            st.success(f"Registro guardado correctamente. Folio: {nuevo_folio}")
            
            # Generar impresión automática
            h_print = generar_html_impresion(nuevo_folio, f_fecha, f_hotel, f_destino, f_contacto, f_solicito, f_paq_tipo, f_paq_nombre, f_guia, f_costo, f_cajas)
            components.html(f"<html><body>{h_print}<script>window.print();</script></body></html>", height=0)
            time.sleep(2)
            st.rerun()

# --- TABLA DE CONSULTA ---
st.divider()
st.subheader("📋 Historial de Envíos Especiales")
if not df_actual.empty:
    st.dataframe(df_actual.sort_values(by="FOLIO", ascending=False), use_container_width=True, hide_index=True)
    
    # Exportar a Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_actual.to_excel(writer, index=False)
    st.download_button("📥 Descargar Reporte Completo (Excel)", data=output.getvalue(), file_name=f"Reporte_CEE_{date.today()}.xlsx")
else:
    st.info("Aún no hay datos en CEE.csv")























































