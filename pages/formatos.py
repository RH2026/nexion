import streamlit as st
import pandas as pd
from github import Github
import datetime
from io import StringIO

# --- CONFIGURACIÓN DE GITHUB ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "pages/muestras.csv"  # Ruta según tu URL raw

def load_data():
    try:
        # Cargamos directamente desde el raw para lectura rápida
        csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
        return pd.read_csv(csv_url)
    except:
        # Si falla o no existe, devolvemos un DataFrame vacío con las columnas
        return pd.DataFrame(columns=[
            "FOLIO", "FECHA", "DESTINATARIO", "CIUDAD", "ESTADO", "CONTACTO", 
            "TELEFONO", "FORMA_ENVIO", "TRANSPORTE", "GUIA", "COSTO_GUIA", 
            "PRODUCTOS", "EXTRAS"
        ])

def save_to_github(df_to_save):
    if not TOKEN:
        st.error("No se encontró el TOKEN de GitHub en secrets.")
        return
    
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    try:
        contents = repo.get_contents(FILE_PATH)
        # Convertir DF a CSV string
        csv_content = df_to_save.to_csv(index=False)
        repo.update_file(contents.path, f"Actualización Folio {datetime.datetime.now()}", csv_content, contents.sha)
        st.success("✅ Datos sincronizados con GitHub (muestras.csv)")
    except Exception as e:
        st.error(f"Error al conectar con GitHub: {e}")

# --- INTERFAZ ---
st.set_page_config(page_title="JYPESA - Muestras", layout="wide")

# Cabezal de Remitente
st.markdown("### 🏢 DATOS DEL REMITENTE")
with st.container(border=True):
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.write("**Jabones y productos Especializados**\n\nC. Cernícalo 155, La Aurora")
    col_r2.write("**Ubicación:** Guadalajara, Jalisco\n\n**CP:** 44460")
    col_r3.write("**Contacto:** Rigoberto Hernandez\n\n**Tel:** 3319753122")

tab1, tab2 = st.tabs(["🆕 Registro de Muestras", "🔍 Buscar y Actualizar Logística"])

# --- TAB 1: REGISTRO ---
with tab1:
    with st.form("registro_nuevo"):
        st.subheader("Datos del Destino")
        c1, c2, c3 = st.columns(3)
        folio = c1.text_input("FOLIO")
        fecha = c2.date_input("FECHA", datetime.date.today())
        hotel = c3.text_input("DESTINATARIO / NOMBRE DEL HOTEL")
        
        c4, c5, c6, c7 = st.columns(4)
        ciudad = c4.text_input("CIUDAD")
        estado = c5.text_input("ESTADO")
        contacto = c6.text_input("CONTACTO")
        telefono = c7.text_input("TELEFONO")
        
        c8, c9 = st.columns(2)
        f_envio = c8.selectbox("FORMA DE ENVIO", ["PAQUETERIA", "ENTREGA LOCAL", "RECOLECCION EN PLANTA"])
        
        st.divider()
        st.subheader("Selección de Productos")
        
        prods_data = {
            "Accesorios Ecologicos": 47.85, "Dispensador Almond": 218.33, "Dispensador Biogena": 216.00,
            "Dispensador Cava": 230.58, "Dispensador Persa": 275.00, "Dispensador Botánicos L": 274.17,
            "Dispensador Dove": 125.00, "Dispensador Biogena 400ml": 184.87, "Kit Elements": 29.34,
            "Kit Almond": 33.83, "Kit Biogena": 48.95, "Kit Cava": 34.59, "Kit Persa": 58.02,
            "Kit Lavarino": 36.30, "Kit Botánicos": 29.34, "Llave Macnetica": 180.00, "Rack Dove": 0.00,
            "Rack JH Blanco 2 pzas": 62.00, "Rack JH Blanco 1 pza": 50.00, "Soporte dob INOX": 679.00, "Soporte Ind INOX": 608.00
        }
        
        seleccion = []
        cols = st.columns(3)
        for i, (p, precio) in enumerate(prods_data.items()):
            if cols[i % 3].checkbox(f"{p} (${precio})"):
                seleccion.append(f"{p} (${precio})")
        
        st.divider()
        st.subheader("Otros Productos (Manual)")
        cx1, cx2, cx3, cx4 = st.columns([1,1,1,3])
        cant = cx1.text_input("CANTIDAD")
        um = cx2.text_input("UM")
        cod = cx3.text_input("CODIGO")
        desc = cx4.text_input("DESCRIPCION")
        
        btn_guardar = st.form_submit_button("💾 GUARDAR E IMPRIMIR")
        
        if btn_guardar:
            df_actual = load_data()
            nuevo = pd.DataFrame([{
                "FOLIO": folio, "FECHA": str(fecha), "DESTINATARIO": hotel, "CIUDAD": ciudad,
                "ESTADO": estado, "CONTACTO": contacto, "TELEFONO": telefono,
                "FORMA_ENVIO": f_envio, "TRANSPORTE": "", "GUIA": "", "COSTO_GUIA": 0,
                "PRODUCTOS": " | ".join(seleccion), "EXTRAS": f"{cant} {um} {cod} {desc}"
            }])
            df_final = pd.concat([df_actual, nuevo], ignore_index=True)
            save_to_github(df_final)

# --- TAB 2: ACTUALIZAR ---
with tab2:
    st.subheader("Actualizar Datos de Envío")
    df_log = load_data()
    folio_buscado = st.selectbox("Selecciona el Folio para llenar Guía/Transporte", df_log["FOLIO"].unique())
    
    if folio_buscado:
        fila = df_log[df_log["FOLIO"] == folio_buscado].iloc[0]
        st.write(f"**Destino:** {fila['DESTINATARIO']} en {fila['CIUDAD']}")
        
        with st.form("update_log"):
            u1, u2, u3 = st.columns(3)
            transp_val = u1.text_input("TRANSPORTE", value=fila["TRANSPORTE"])
            guia_val = u2.text_input("GUIA", value=fila["GUIA"])
            costo_val = u3.number_input("COSTO GUIA", value=float(fila["COSTO_GUIA"]))
            
            if st.form_submit_button("🔄 ACTUALIZAR LOGÍSTICA"):
                df_log.loc[df_log["FOLIO"] == folio_buscado, ["TRANSPORTE", "GUIA", "COSTO_GUIA"]] = [transp_val, guia_val, costo_val]
                save_to_github(df_log)


















































