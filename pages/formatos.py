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
        st.error("Falta GITHUB_TOKEN en los secrets.")
        return
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(contents.path, mensaje_commit, df_to_save.to_csv(index=False), contents.sha)
        st.success(f"✅ GitHub actualizado: {mensaje_commit}")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- INTERFAZ ---
st.set_page_config(page_title="Gestión de Muestras", layout="wide")

tab1, tab2 = st.tabs(["🆕 Nueva Solicitud", "🚚 Actualizar Transporte/Guía"])

# --- TAB 1: REGISTRO E IMPRESIÓN ---
with tab1:
    with st.form("form_registro"):
        st.subheader("Datos de Envío")
        c1, c2, c3 = st.columns(3)
        folio = c1.text_input("FOLIO")
        fecha = c2.date_input("FECHA", datetime.date.today())
        hotel = c3.text_input("DESTINATARIO /  NOMBRE DEL HOTEL")
        
        c4, c5, c6, c7 = st.columns(4)
        ciudad = c4.text_input("CIUDAD")
        estado = c5.text_input("ESTADO")
        contacto = c6.text_input("CONTACTO")
        telefono = c7.text_input("TELEFONO")
        
        f_envio = st.selectbox("FORMA DE ENVIO", ["PAQUETERIA", "LOCAL", "RECOLECCION"])
        
        st.divider()
        st.subheader("Selección de Productos")
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
            if cols[i % 3].checkbox(f"{p} (${pre})"):
                seleccionados.append({"p": p, "pre": pre})
        
        st.write("**Producto Extra:**")
        ce1, ce2, ce3 = st.columns([1,2,2])
        c_ex = ce1.text_input("CANT")
        p_ex = ce2.text_input("PRODUCTO EXTRA")
        d_ex = ce3.text_input("DESCRIPCION EXTRA")
        
        col_b1, col_b2 = st.columns(2)
        btn_guardar = col_b1.form_submit_button("💾 GUARDAR REGISTRO")
        btn_imprimir = col_b2.form_submit_button("🖨️ GENERAR VISTA DE IMPRESIÓN")

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
        save_to_github(df_final, f"Nuevo Folio {folio}")

    if btn_imprimir:
        st.markdown("---")
        st.markdown("### 📄 FORMATO DE SALIDA (MUESTRAS)")
        st.write("**REMITENTE:** Jabones y productos Especializados | C. Cernícalo 155, La Aurora, GDL.")
        st.write(f"**FOLIO:** {folio} | **FECHA:** {fecha}")
        st.write(f"**DESTINO:** {hotel} - {ciudad}, {estado}")
        st.write(f"**ATN:** {contacto} | **TEL:** {telefono}")
        st.write("**PRODUCTOS SOLICITADOS:**")
        for item in seleccionados:
            st.write(f"- {item['p']}")
        if p_ex:
            st.write(f"- {c_ex} {p_ex} ({d_ex})")
        st.info("Para imprimir: Ctrl + P")

# --- TAB 2: ACTUALIZACIÓN ---
with tab2:
    st.subheader("Actualizar Logística de Envío")
    df_repo = load_data()
    folio_update = st.selectbox("Seleccione Folio para completar datos", df_repo["FOLIO"].unique())
    
    if folio_update:
        # Mostrar datos actuales para confirmar
        data_folio = df_repo[df_repo["FOLIO"] == folio_update]
        st.write(f"Actualizando destino: **{data_folio.iloc[0]['DESTINATARIO /  NOMBRE DEL HOTEL']}**")
        
        with st.form("form_actualizar"):
            c_u1, c_u2, c_u3 = st.columns(3)
            nuevo_t = c_u1.text_input("TRANSPORTE", value=data_folio.iloc[0]["TRANSPORTE"])
            nueva_g = c_u2.text_input("GUIA", value=data_folio.iloc[0]["GUIA"])
            nuevo_c = c_u3.number_input("COSTO GUIA", value=float(data_folio.iloc[0]["COSTO GUIA"]))
            
            if st.form_submit_button("🔄 ACTUALIZAR TODAS LAS FILAS"):
                # Actualizar todas las filas que tengan ese FOLIO
                df_repo.loc[df_repo["FOLIO"] == folio_update, ["TRANSPORTE", "GUIA", "COSTO GUIA"]] = [nuevo_t, nueva_g, nuevo_c]
                save_to_github(df_repo, f"Update Logistica Folio {folio_update}")




















































