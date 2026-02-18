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

    # --- HISTORIAL Y REPORTES ---
    with st.expander("📊 VER REGISTROS Y REPORTES", expanded=False):
        
        # 1. VISTA EN PANTALLA (Tabla limpia estilo Excel)
        st.markdown("<h3 style='text-align: center;'>REPORTE GENERAL</h3>", unsafe_allow_html=True)
        
        df_display = df_actual.copy()
        # Aseguramos que los costos sean numéricos para la vista y sumas
        df_display["COSTO"] = pd.to_numeric(df_display["COSTO"]).fillna(0)
        df_display["COSTO_GUIA"] = pd.to_numeric(df_display["COSTO_GUIA"]).fillna(0)
        
        # Mostramos la tabla en pantalla
        st.dataframe(df_display, use_container_width=True)
        
        # Totales rápidos en pantalla
        t_prod = df_display["COSTO"].sum()
        t_flete = df_display["COSTO_GUIA"].sum()
        st.markdown(f"**TOTAL PRODUCTO:** ${t_prod:,.2f} | **TOTAL FLETE:** ${t_flete:,.2f}")

        st.divider()

        # 2. GENERACIÓN DE HTML PARA IMPRESIÓN (Tu código de ejemplo adaptado)
        # Filtramos solo lo que tiene cantidad > 0 para el reporte impreso
        filas_html = ""
        for _, r in df_display.iterrows():
            # Aquí sacamos el detalle de productos sin ceros para el cuerpo del reporte
            detalle_productos = ""
            for p in precios.keys():
                cant = r.get(p, 0)
                if cant > 0:
                    detalle_productos += f"• {cant} pza(s) {p}<br>"
            
            filas_html += f"""
            <tr>
                <td style='border:1px solid black;padding:8px;'>{r['FOLIO']}</td>
                <td style='border:1px solid black;padding:8px;'>{r['NOMBRE DEL HOTEL']}<br><small>{r['DESTINO']}</small></td>
                <td style='border:1px solid black;padding:8px;'>{detalle_productos}</td>
                <td style='border:1px solid black;padding:8px;text-align:right;'>${r['COSTO']:,.2f}</td>
                <td style='border:1px solid black;padding:8px;text-align:right;'>${r['COSTO_GUIA']:,.2f}</td>
            </tr>
            """

        form_pt_html = f"""
        <html>
        <head>
            <style>
                @page {{ size: auto; margin: 0mm; }}
                @media print {{
                    body {{ margin: 0; padding: 15mm; }}
                    .no-print {{ display: none !important; }}
                }}
                body {{ font-family: sans-serif; color: black; background: white; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px; }}
                th {{ background: #eee; border: 1px solid black; padding: 8px; text-align: left; }}
                .signature-section {{ margin-top: 50px; display: flex; justify-content: space-between; text-align: center; font-size: 10px; }}
                .sig-box {{ width: 30%; border-top: 1px solid black; padding-top: 5px; }}
            </style>
        </head>
        <body>
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:10px; margin-bottom:20px;">
                <div>
                    <h2 style="margin:0; letter-spacing:2px;">JYPESA</h2>
                    <p style="margin:0; font-size:10px; letter-spacing:1px;">AUTOMATIZACIÓN DE PROCESOS</p>
                </div>
                <div style="text-align:right; font-size:12px;">
                    <b>REPORTE GENERAL DE MUESTRAS</b><br>
                    <b>FECHA:</b> {date.today()}
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>FOLIO</th>
                        <th>DESTINO / HOTEL</th>
                        <th>DETALLE PRODUCTOS</th>
                        <th>COSTO</th>
                        <th>FLETE</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
            </table>
            <div style="text-align:right; margin-top:10px; font-size:12px;">
                <b>TOTAL PRODUCTOS: ${t_prod:,.2f}</b><br>
                <b>TOTAL FLETES: ${t_flete:,.2f}</b>
            </div>
            <div class="signature-section">
                <div class="sig-box"><b>ENTREGÓ</b><br>Analista de Inventario</div>
                <div class="sig-box"><b>AUTORIZACIÓN</b><br>Dir. Operaciones</div>
                <div class="sig-box"><b>RECIBIÓ</b><br>Logística / Solicitante</div>
            </div>
        </body>
        </html>
        """

        # 3. BOTONES DE ACCIÓN
        c1, c2 = st.columns(2)
        with c1:
            # Botón de impresión usando components.html como en tu ejemplo
            if st.button("🖨️ IMPRIMIR REPORTE PT", type="primary", use_container_width=True):
                import streamlit.components.v1 as components
                components.html(f"<html><body>{form_pt_html}<script>window.print();</script></body></html>", height=0)
        
        with c2:
            # Botón de Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_actual.to_excel(writer, index=False)
            st.download_button("📥 DESCARGAR EXCEL", output.getvalue(), f"Matriz_Muestras_{date.today()}.xlsx", use_container_width=True)







































































