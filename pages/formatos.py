import streamlit as st
import pandas as pd
import requests
import base64
from datetime import date
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Nexión - Muestras", layout="wide")

GITHUB_USER = "RH2026"
GITHUB_REPO = "nexion"
GITHUB_PATH = "muestras.csv"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

# Diccionario de precios con los nombres EXACTOS
precios = {
    "Accesorios Ecologicos": 47.85, "Accesorios Lavarino": 47.85, "Dispensador Almond ": 218.33,
    "Dispensador Biogena": 216.00, "Dispensador Cava": 230.58, "Dispensador Persa": 275.00,
    "Dispensador Botánicos L": 274.17, "Dispensador Dove": 125.00, "Dispensador Biogena 400ml": 184.87,
    "Kit Elements ": 29.34, "Kit Almond ": 33.83, "Kit Biogena": 48.95, "Kit Cava": 34.59,
    "Kit Persa": 58.02, "Kit Lavarino": 36.30, "Kit Botánicos": 29.34, "Llave Magnetica": 180.00,
    "Rack Dove": 0.00, "Rack JH  Color Blanco de 2 pzas": 62.00, "Rack JH  Color Blanco de 1 pzas": 50.00,
    "Soporte dob  INOX Cap lock": 679.00, "Soporte Ind  INOX Cap lock": 608.00
}

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

# --- LÓGICA DE DATOS ---
df_actual, sha_actual = obtener_datos_github()

# Asegurar que las columnas de guía existan en el DF si no vienen en el CSV
for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA"]:
    if col not in df_actual.columns and not df_actual.empty:
        df_actual[col] = ""

nuevo_folio = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1) if not df_actual.empty else 1

# --- INTERFAZ DE CAPTURA NUEVA ---
st.title("📦 Captura de Muestras Nexión")

col1, col2, col3 = st.columns(3)
f_folio = col1.text_input("FOLIO", value=str(nuevo_folio), disabled=True)
f_fecha = col1.date_input("FECHA", value=date.today())
f_hotel = col2.text_input("NOMBRE DEL HOTEL", key="hotel")
f_destino = col2.text_input("DESTINO", key="destino")
f_contacto = col3.text_input("CONTACTO", key="contacto")
f_solicito = col3.text_input("SOLICITÓ", key="solicito")
f_paqueteria = st.selectbox("FORMA DE ENVÍO", ["PAQUETERIA", "ENTREGA DIRECTA", "OTRO"], key="envio")

st.divider()
st.subheader("Selección de Productos")
seleccionados = st.multiselect("Busca y selecciona los productos:", list(precios.keys()), key="multiselect_prod")

cantidades_input = {}
if seleccionados:
    st.info("Escribe las cantidades:")
    cols_q = st.columns(3)
    for i, p in enumerate(seleccionados):
        with cols_q[i % 3]:
            cantidades_input[p] = st.number_input(f"Cantidad: {p}", min_value=1, step=1, key=f"q_{p}")

if st.button("🚀 GUARDAR REGISTRO NUEVO", use_container_width=True):
    if not f_hotel:
        st.error("Ingresa el nombre del hotel.")
    elif not seleccionados:
        st.error("Selecciona al menos un producto.")
    else:
        registro_completo = {
            "FOLIO": nuevo_folio, "FECHA": f_fecha.strftime("%Y-%m-%d"),
            "NOMBRE DEL HOTEL": f_hotel, "DESTINO": f_destino,
            "CONTACTO": f_contacto, "SOLICITO": f_solicito, "PAQUETERIA": f_paqueteria,
            "PAQUETERIA_NOMBRE": "", "NUMERO_GUIA": "", "COSTO_GUIA": 0
        }
        total_piezas = sum(cantidades_input.values())
        total_costo = sum(cantidades_input[p] * precios[p] for p in cantidades_input)
        registro_completo["CANTIDAD"] = total_piezas
        registro_completo["COSTO"] = total_costo
        for producto in precios.keys():
            registro_completo[producto] = cantidades_input.get(producto, 0)
        
        df_final = pd.concat([df_actual, pd.DataFrame([registro_completo])], ignore_index=True)
        if subir_a_github(df_final, sha_actual, f"Folio {nuevo_folio}"):
            st.success(f"¡Folio {nuevo_folio} guardado!"); st.balloons(); st.rerun()

# --- SECCIÓN DE EDICIÓN (DESPUÉS) ---
st.divider()
if not df_actual.empty:
    with st.expander("📝 AGREGAR DATOS DE ENVÍO / GUÍA (POST-CAPTURA)", expanded=False):
        st.write("Selecciona un folio existente para agregar los datos de la paquetería:")
        folio_a_editar = st.selectbox("Seleccionar Folio:", df_actual["FOLIO"].unique())
        
        col_g1, col_g2, col_g3 = st.columns(3)
        nombre_paq = col_g1.text_input("Nombre Paquetería (Ej. FedEx, DHL)")
        n_guia = col_g2.text_input("Número de Guía")
        c_guia = col_g3.number_input("Costo de la Guía", min_value=0.0, step=0.1)
        
        if st.button("✅ ACTUALIZAR DATOS DE ENVÍO"):
            # Localizar el índice del folio y actualizar solo esas columnas
            idx = df_actual.index[df_actual['FOLIO'] == folio_a_editar].tolist()[0]
            df_actual.at[idx, "PAQUETERIA_NOMBRE"] = nombre_paq
            df_actual.at[idx, "NUMERO_GUIA"] = n_guia
            df_actual.at[idx, "COSTO_GUIA"] = c_guia
            
            with st.spinner("Actualizando guía en GitHub..."):
                if subir_a_github(df_actual, sha_actual, f"Actualización Guía Folio {folio_a_editar}"):
                    st.success(f"¡Guía actualizada para el folio {folio_a_editar}!"); st.rerun()

    # --- HISTORIAL Y REPORTES ESTILO EXCEL ---
    with st.expander("📊 VER REGISTROS Y REPORTES", expanded=False):
        
        # Contenedor que vamos a imprimir
        reporte_completo_html = ""
        
        # 1. Preparación de Datos
        df_vista = df_actual.copy()
        df_vista["COSTO"] = pd.to_numeric(df_vista["COSTO"]).fillna(0)
        df_vista["COSTO_GUIA"] = pd.to_numeric(df_vista["COSTO_GUIA"]).fillna(0)
        
        total_prod = df_vista["COSTO"].sum()
        total_flete = df_vista["COSTO_GUIA"].sum()

        # 2. Construcción de Filas del Reporte General
        filas_general = ""
        for _, row in df_vista.iterrows():
            filas_general += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 5px;">{row['DESTINO']}</td>
                <td style="border: 1px solid #ddd; padding: 5px;">{row['CONTACTO']}</td>
                <td style="border: 1px solid #ddd; padding: 5px;">{row['SOLICITO']}</td>
                <td style="border: 1px solid #ddd; padding: 5px;">{row['PAQUETERIA']}</td>
                <td style="border: 1px solid #ddd; padding: 5px; text-align: center;">{row['CANTIDAD']}</td>
                <td style="border: 1px solid #ddd; padding: 5px; text-align: right;">${row['COSTO']:,.2f}</td>
                <td style="border: 1px solid #ddd; padding: 5px;">{row['PAQUETERIA_NOMBRE']}</td>
                <td style="border: 1px solid #ddd; padding: 5px;">{row['NUMERO_GUIA']}</td>
                <td style="border: 1px solid #ddd; padding: 5px; text-align: right;">${row['COSTO_GUIA']:,.2f}</td>
            </tr>
            """

        # 3. Construcción de Filas del Acumulado por Agente
        resumen_agente = df_vista.groupby("SOLICITO").agg({"COSTO_GUIA": "sum", "COSTO": "sum"}).reset_index()
        filas_agente = ""
        for _, row in resumen_agente.iterrows():
            total_agente = row['COSTO_GUIA'] + row['COSTO']
            filas_agente += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{row['SOLICITO']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">$ {row['COSTO_GUIA']:,.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">$ {row['COSTO']:,.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;"><b>$ {total_agente:,.2f}</b></td>
            </tr>
            """

        # 4. El Reporte Final (Diseño igual a tu imagen)
        reporte_final_html = f"""
        <div id="printableArea" style="font-family: Arial, sans-serif; color: black; background-color: white; padding: 20px;">
            <h4 style="text-align: center; margin-bottom: 20px;">REPORTE GENERAL</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <thead>
                    <tr style="background-color: #f9f9f9;">
                        <th style="border: 1px solid #000; padding: 5px;">DESTINO</th>
                        <th style="border: 1px solid #000; padding: 5px;">CONTACTO</th>
                        <th style="border: 1px solid #000; padding: 5px;">SOLICITO</th>
                        <th style="border: 1px solid #000; padding: 5px;">PAQUETERIA</th>
                        <th style="border: 1px solid #000; padding: 5px;">CANT</th>
                        <th style="border: 1px solid #000; padding: 5px;">COSTO</th>
                        <th style="border: 1px solid #000; padding: 5px;">PAQ. NOMBRE</th>
                        <th style="border: 1px solid #000; padding: 5px;">GUIA</th>
                        <th style="border: 1px solid #000; padding: 5px;">FLETE</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_general}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="5" style="text-align: right; padding: 10px;"><b>TOTALES:</b></td>
                        <td style="text-align: right; border-top: 2px solid #000;"><b>$ {total_prod:,.2f}</b></td>
                        <td colspan="2"></td>
                        <td style="text-align: right; border-top: 2px solid #000;"><b>$ {total_flete:,.2f}</b></td>
                    </tr>
                </tfoot>
            </table>

            <div style="margin-top: 50px;">
                <h4 style="text-align: center; border-bottom: 1px solid #000; padding-bottom: 5px;">ACUMULADO POR AGENTE</h4>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px;">
                    <tr style="text-align: left;">
                        <th style="padding: 8px;">SOLICITANTE</th>
                        <th style="padding: 8px; text-align: right;">FLETE</th>
                        <th style="padding: 8px; text-align: right;">PRODUCTO</th>
                        <th style="padding: 8px; text-align: right;">TOTAL</th>
                    </tr>
                    {filas_agente}
                </table>
            </div>
        </div>
        """

        # Mostrar el reporte en la app
        st.markdown(reporte_final_html, unsafe_allow_html=True)

        # Botones de Acción
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🖨️ IMPRIMIR REPORTE", use_container_width=True):
                st.components.v1.html(f"""
                    <script>
                        var printContents = document.getElementById('printableArea').innerHTML;
                        var originalContents = document.body.innerHTML;
                        document.body.innerHTML = '<html><head><title>Reporte Nexión</title></head><body>' + printContents + '</body></html>';
                        window.print();
                        window.location.reload();
                    </script>
                """, height=0)

        with col_btn2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_actual.to_excel(writer, index=False)
            st.download_button("📥 DESCARGAR EXCEL", output.getvalue(), f"Matriz_{date.today()}.xlsx", use_container_width=True)






































































