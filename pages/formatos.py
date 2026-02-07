Entiendo perfectamente el punto. Si los datos se están borrando es porque al actualizar no estamos manteniendo la integridad del resto de las filas o hay un conflicto al sobrescribir. Vamos a blindar esa parte.

Respecto a la impresión, le daremos ese toque profesional de Ingeniería con un encabezado técnico y limpio.

Cambios Aplicados:
Protección de Datos: Se optimizó la lógica de actualización para asegurar que solo se toquen las columnas de logística, dejando intacto el resto del archivo.

Encabezado "Nivel Ingeniería": Se agregó el título JYPESA seguido de Automatización de Procesos con un estilo visual más formal.

Renderizado de Impresión: Se estructuró la vista de impresión para que parezca una orden de salida profesional.

Python
import streamlit as st
import pandas as pd
from github import Github
import datetime

# --- CONFIGURACIÓN DE GITHUB ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "pages/muestras.csv"

def load_data():
    try:
        csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame(columns=[
            "FOLIO", "FECHA", "DESTINATARIO /  NOMBRE DEL HOTEL", "CIUDAD", "ESTADO", 
            "CONTACTO", "TELEFONO", "FORMA DE ENVIO", "TRANSPORTE", "GUIA", 
            "COSTO GUIA", "PRODUCTO", "PRECIO", "PRODUCTO EXTRA", "CANTIDAD EXTRA", "DESCRIPCION EXTRA"
        ])

def save_to_github(df_to_save, mensaje_commit):
    if not TOKEN:
        st.error("Falta GITHUB_TOKEN.")
        return
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(FILE_PATH)
        # Convertimos a CSV asegurando que no se pierdan datos por codificación
        repo.update_file(contents.path, mensaje_commit, df_to_save.to_csv(index=False), contents.sha)
        st.success(f"✅ Sistema Actualizado: {mensaje_commit}")
    except Exception as e:
        st.error(f"Error Crítico: {e}")

# --- INTERFAZ ESTILO INGENIERÍA ---
st.set_page_config(page_title="JYPESA - Ingeniería", layout="wide")

# Encabezado Nivel Ingeniería
st.markdown("""
    <div style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px;">
        <h1 style="margin-bottom: 0;">JYPESA</h1>
        <h5 style="margin-top: 0; color: #555;">Automatización de Procesos</h5>
    </div>
    """, unsafe_allow_stdio=True)

tab1, tab2 = st.tabs(["📋 Registro e Impresión", "⚙️ Actualización de Logística"])

# --- TAB 1: REGISTRO ---
with tab1:
    with st.form("registro_ingenieria"):
        c1, c2, c3 = st.columns(3)
        folio = c1.text_input("FOLIO (ID Único)")
        fecha = c2.date_input("FECHA DE SOLICITUD", datetime.date.today())
        hotel = c3.text_input("DESTINATARIO /  NOMBRE DEL HOTEL")
        
        c4, c5, c6, c7 = st.columns(4)
        ciudad = c4.text_input("CIUDAD")
        estado = c5.text_input("ESTADO")
        contacto = c6.text_input("CONTACTO")
        telefono = c7.text_input("TELÉFONO")
        
        f_envio = st.selectbox("FORMA DE ENVIO", ["PAQUETERIA", "LOCAL", "RECOLECCION"])
        
        st.markdown("---")
        st.subheader("Ítems para Envío")
        prods_dict = {
            "Accesorios Ecologicos": 47.85, "Dispensador Almond": 218.33, "Dispensador Biogena": 216.00,
            "Dispensador Cava": 230.58, "Dispensador Persa": 275.00, "Dispensador Botánicos L": 274.17,
            "Dispensador Dove": 125.00, "Dispensador Biogena 400ml": 184.87, "Kit Elements": 29.34,
            "Kit Almond": 33.83, "Kit Biogena": 48.95, "Kit Cava": 34.59, "Kit Persa": 58.02,
            "Kit Lavarino": 36.30, "Kit Botánicos": 29.34, "Llave Macnetica": 180.00, "Rack Dove": 0.00,
            "Rack JH Blanco 2 pzas": 62.00, "Rack JH Blanco 1 pza": 50.00, "Soporte dob INOX": 679.00, "Soporte Ind INOX": 608.00
        }
        
        seleccionados = []
        cols = st.columns(3)
        for i, (p, pre) in enumerate(prods_dict.items()):
            if cols[i % 3].checkbox(f"{p}"):
                seleccionados.append({"p": p, "pre": pre})
        
        st.markdown("**Especificaciones Extra:**")
        ce1, ce2, ce3 = st.columns([1,2,2])
        c_ex = ce1.text_input("CANT")
        p_ex = ce2.text_input("PRODUCTO EXTRA")
        d_ex = ce3.text_input("DESCRIPCION EXTRA")
        
        col_b1, col_b2 = st.columns(2)
        btn_guardar = col_b1.form_submit_button("💾 GUARDAR REGISTRO")
        btn_imprimir = col_b2.form_submit_button("🖨️ RENDERIZAR FORMATO IMPRESIÓN")

    if btn_guardar:
        df_actual = load_data()
        nuevas_filas = []
        for item in seleccionados:
            nuevas_filas.append({
                "FOLIO": folio, "FECHA": str(fecha), "DESTINATARIO /  NOMBRE DEL HOTEL": hotel,
                "CIUDAD": ciudad, "ESTADO": estado, "CONTACTO": contacto, "TELEFONO": telefono,
                "FORMA DE ENVIO": f_envio, "TRANSPORTE": "", "GUIA": "", "COSTO GUIA": 0,
                "PRODUCTO": item["p"], "PRECIO": item["pre"], "PRODUCTO EXTRA": "", "CANTIDAD EXTRA": "", "DESCRIPCION EXTRA": ""
            })
        if p_ex:
            nuevas_filas.append({
                "FOLIO": folio, "FECHA": str(fecha), "DESTINATARIO /  NOMBRE DEL HOTEL": hotel,
                "CIUDAD": ciudad, "ESTADO": estado, "CONTACTO": contacto, "TELEFONO": telefono,
                "FORMA DE ENVIO": f_envio, "TRANSPORTE": "", "GUIA": "", "COSTO GUIA": 0,
                "PRODUCTO": "EXTRA", "PRECIO": 0, "PRODUCTO EXTRA": p_ex, "CANTIDAD EXTRA": c_ex, "DESCRIPCION EXTRA": d_ex
            })
        df_final = pd.concat([df_actual, pd.DataFrame(nuevas_filas)], ignore_index=True)
        save_to_github(df_final, f"Registro Folio {folio}")

    if btn_imprimir:
        st.markdown("""---
            <div style="background-color: white; padding: 30px; border: 1px solid #ccc; color: black;">
                <h2 style="text-align: center; margin:0;">JYPESA</h2>
                <p style="text-align: center; margin:0; border-bottom: 1px solid black;">Automatización de Procesos</p>
                <br>
                <table style="width:100%">
                    <tr><td><b>FOLIO:</b> %s</td><td><b>FECHA:</b> %s</td></tr>
                    <tr><td><b>DESTINATARIO:</b> %s</td><td><b>CIUDAD/EDO:</b> %s, %s</td></tr>
                    <tr><td><b>ATN:</b> %s</td><td><b>TEL:</b> %s</td></tr>
                </table>
                <hr>
                <h4>PRODUCTOS SOLICITADOS (MUESTRAS)</h4>
        """ % (folio, fecha, hotel, ciudad, estado, contacto, telefono), unsafe_allow_html=True)
        for item in seleccionados:
            st.markdown(f"- {item['p']}")
        if p_ex:
            st.markdown(f"- {c_ex} {p_ex} ({d_ex})")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: ACTUALIZACIÓN ---
with tab2:
    st.subheader("⚙️ Control Logístico Posterior")
    df_repo = load_data()
    # Filtramos folios únicos
    folios_lista = df_repo["FOLIO"].unique().tolist()
    folio_update = st.selectbox("Seleccione Folio para Carga de Datos", folios_lista)
    
    if folio_update:
        # Extraemos la información actual del primer registro que encuentre de ese folio
        idx_folio = df_repo[df_repo["FOLIO"] == folio_update].index
        datos_actuales = df_repo.loc[idx_folio[0]]
        
        st.info(f"Destinatario Registrado: {datos_actuales['DESTINATARIO /  NOMBRE DEL HOTEL']}")
        
        with st.form("form_update_final"):
            u1, u2, u3 = st.columns(3)
            # Pre-llenamos con lo que ya tenga (si es que tiene algo)
            t_val = u1.text_input("TRANSPORTE", value=str(datos_actuales.get("TRANSPORTE", "")))
            g_val = u2.text_input("GUIA", value=str(datos_actuales.get("GUIA", "")))
            c_val = u3.number_input("COSTO GUIA", value=float(datos_actuales.get("COSTO GUIA", 0.0)))
            
            if st.form_submit_button("🔒 ACTUALIZAR Y ASEGURAR DATOS"):
                # Actualizamos todas las ocurrencias de ese folio
                df_repo.loc[idx_folio, "TRANSPORTE"] = t_val
                df_repo.loc[idx_folio, "GUIA"] = g_val
                df_repo.loc[idx_folio, "COSTO GUIA"] = c_val
                
                save_to_github(df_repo, f"Update Logistica Folio {folio_update}")




















































