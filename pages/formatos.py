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

    # --- HISTORIAL, REPORTE Y EXCEL ---
    with st.expander("📊 VER REGISTROS Y REPORTES", expanded=False):
        tab1, tab2 = st.tabs(["📄 Tabla General", "📈 Reporte de Gastos"])
        
        with tab1:
            st.dataframe(df_actual, use_container_width=True)
        
        with tab2:
            st.subheader("Resumen de Gastos por Solicitante")
            
            # Aseguramos que el costo de guía sea numérico
            df_actual["COSTO_GUIA"] = pd.to_numeric(df_actual["COSTO_GUIA"]).fillna(0)
            
            # Agrupamos por Solicitante
            reporte = df_actual.groupby("SOLICITO").agg({
                "FOLIO": "count",
                "COSTO": "sum",
                "COSTO_GUIA": "sum"
            }).rename(columns={"FOLIO": "Total Muestras", "COSTO": "Costo Productos", "COSTO_GUIA": "Gasto Envío"})
            
            reporte["Total Inversión"] = reporte["Costo Productos"] + reporte["Gasto Envío"]
            
            # Formato de dinero para la tabla
            st.table(reporte.style.format("${:,.2f}", subset=["Costo Productos", "Gasto Envío", "Total Inversión"]))
            
            st.divider()
            st.subheader("Detalle de Productos (Sin Ceros)")
            
            # Buscador por Folio para "Imprimir" reporte individual
            folio_sel = st.selectbox("Selecciona un Folio para ver detalle de impresión:", df_actual["FOLIO"].unique())
            
            if folio_sel:
                datos_f = df_actual[df_actual["FOLIO"] == folio_sel].iloc[0]
                
                # Diseño tipo Reporte
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:20px; border-radius:10px; background-color: #f9f9f9;">
                    <h2 style='text-align: center;'>REPORTE DE SALIDA - FOLIO {folio_sel}</h2>
                    <p><b>Hotel:</b> {datos_f['NOMBRE DEL HOTEL']} | <b>Solicitó:</b> {datos_f['SOLICITO']}</p>
                    <p><b>Fecha:</b> {datos_f['FECHA']} | <b>Destino:</b> {datos_f['DESTINO']}</p>
                    <hr>
                    <h4>Productos Enviados:</h4>
                    <ul>
                """, unsafe_allow_html=True)
                
                # Solo mostrar productos con cantidad > 0
                for p in precios.keys():
                    cant = datos_f.get(p, 0)
                    if cant > 0:
                        st.write(f"✅ {cant} pza(s) - {p}")
                
                st.markdown(f"""
                    </ul>
                    <hr>
                    <p><b>Costo Productos:</b> ${datos_f['COSTO']:,.2f}</p>
                    <p><b>Paquetería:</b> {datos_f['PAQUETERIA_NOMBRE']} | <b>Guía:</b> {datos_f['NUMERO_GUIA']}</p>
                    <p><b>Costo Envío:</b> ${datos_f['COSTO_GUIA']:,.2f}</p>
                    <h3 style='color: #2e7d32;'>Gasto Total: ${float(datos_f['COSTO']) + float(datos_f['COSTO_GUIA']):,.2f}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.info("💡 Para imprimir este reporte, presiona **Ctrl + P** en tu teclado.")

        st.write("---")
        # Botón de descarga de siempre
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_actual.to_excel(writer, index=False)
        st.download_button("📥 DESCARGAR MATRIZ COMPLETA (EXCEL)", output.getvalue(), f"Matriz_{date.today()}.xlsx", use_container_width=True)



































































