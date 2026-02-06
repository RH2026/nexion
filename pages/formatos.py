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

def save_to_github(df_to_save):
    if not TOKEN:
        st.error("Falta GITHUB_TOKEN en los secrets.")
        return
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(contents.path, f"Registro Folio {datetime.datetime.now()}", df_to_save.to_csv(index=False), contents.sha)
        st.success("✅ ¡Información guardada en GitHub!")
    except Exception as e:
        st.error(f"Error: {e}")

# --- INTERFAZ ---
st.title("📋 Formato de Muestras JYPESA")

# Datos fijos del remitente (Visual)
st.info("**Remitente:** Jabones y productos Especializados | C. Cernícalo 155, La Aurora, CP 44460 | Rigoberto Hernandez")

with st.form("main_form"):
    # Fila 1: Datos Básicos
    c1, c2, c3 = st.columns(3)
    folio = c1.text_input("FOLIO")
    fecha = c2.date_input("FECHA", datetime.date.today())
    hotel = c3.text_input("DESTINATARIO /  NOMBRE DEL HOTEL")
    
    # Fila 2: Ubicación y Contacto
    c4, c5, c6, c7 = st.columns(4)
    ciudad = c4.text_input("CIUDAD")
    estado = c5.text_input("ESTADO")
    contacto = c6.text_input("CONTACTO")
    telefono = c7.text_input("TELEFONO")
    
    # Fila 3: Envío (Logística inicial vacía)
    c8, c9, c10 = st.columns(3)
    f_envio = c8.selectbox("FORMA DE ENVIO", ["PAQUETERIA", "ENTREGA LOCAL", "RECOLECCION"])
    transporte = c9.text_input("TRANSPORTE")
    guia = c10.text_input("GUIA")
    
    c11 = st.columns(1)[0]
    costo_guia = c11.number_input("COSTO GUIA", min_value=0.0, step=0.1)

    st.divider()
    
    # PRODUCTOS DE LISTA
    st.subheader("Selección de Productos")
    productos_precios = {
        "Accesorios Ecologicos": 47.85, "Dispensador Almond": 218.33, "Dispensador Biogena": 216.00,
        "Dispensador Cava": 230.58, "Dispensador Persa": 275.00, "Dispensador Botánicos L": 274.17,
        "Dispensador Dove": 125.00, "Dispensador Biogena 400ml": 184.87, "Kit Elements": 29.34,
        "Kit Almond": 33.83, "Kit Biogena": 48.95, "Kit Cava": 34.59, "Kit Persa": 58.02,
        "Kit Lavarino": 36.30, "Kit Botánicos": 29.34, "Llave Macnetica": 180.00, "Rack Dove": 0.00,
        "Rack JH Blanco 2 pzas": 62.00, "Rack JH Blanco 1 pza": 50.00, "Soporte dob INOX": 679.00, "Soporte Ind INOX": 608.00
    }
    
    seleccionados = []
    cols = st.columns(3)
    for i, (prod, precio) in enumerate(productos_precios.items()):
        if cols[i % 3].checkbox(f"{prod} (${precio})"):
            seleccionados.append({"prod": prod, "prec": precio})

    st.divider()
    
    # PRODUCTO EXTRA
    st.subheader("Producto No Listado (Extra)")
    ce1, ce2, ce3, ce4 = st.columns([1,1,2,2])
    cant_ex = ce1.text_input("CANTIDAD EXTRA")
    um_ex = ce2.text_input("UM") # Se puede concatenar a descripción si no hay columna UM
    prod_ex = ce3.text_input("PRODUCTO EXTRA")
    desc_ex = ce4.text_input("DESCRIPCION EXTRA")

    # BOTONES
    col_btn1, col_btn2 = st.columns(2)
    btn_guardar = col_btn1.form_submit_button("💾 GUARDAR")
    btn_imprimir = col_btn2.form_submit_button("🖨️ IMPRIMIR (VISTA PREVIA)")

    if btn_guardar:
        df_base = load_data()
        nuevas_filas = []
        
        # Si hay productos de lista, crear una fila por cada uno
        if seleccionados:
            for item in seleccionados:
                nuevas_filas.append({
                    "FOLIO": folio, "FECHA": str(fecha), "DESTINATARIO /  NOMBRE DEL HOTEL": hotel,
                    "CIUDAD": ciudad, "ESTADO": estado, "CONTACTO": contacto, "TELEFONO": telefono,
                    "FORMA DE ENVIO": f_envio, "TRANSPORTE": transporte, "GUIA": guia, "COSTO GUIA": costo_guia,
                    "PRODUCTO": item["prod"], "PRECIO": item["prec"],
                    "PRODUCTO EXTRA": "", "CANTIDAD EXTRA": "", "DESCRIPCION EXTRA": ""
                })
        
        # Si hay producto extra, añadir una fila (o incluirlo en la primera si prefieres)
        if prod_ex:
            nuevas_filas.append({
                "FOLIO": folio, "FECHA": str(fecha), "DESTINATARIO /  NOMBRE DEL HOTEL": hotel,
                "CIUDAD": ciudad, "ESTADO": estado, "CONTACTO": contacto, "TELEFONO": telefono,
                "FORMA DE ENVIO": f_envio, "TRANSPORTE": transporte, "GUIA": guia, "COSTO GUIA": costo_guia,
                "PRODUCTO": "EXTRA", "PRECIO": 0,
                "PRODUCTO EXTRA": prod_ex, "CANTIDAD EXTRA": cant_ex, "DESCRIPCION EXTRA": desc_ex
            })
            
        if nuevas_filas:
            df_nuevo = pd.DataFrame(nuevas_filas)
            df_final = pd.concat([df_base, df_nuevo], ignore_index=True)
            save_to_github(df_final)
        else:
            st.warning("Selecciona al menos un producto.")

if btn_imprimir:
    st.write("### Vista Previa de Impresión")
    st.write(f"**Folio:** {folio} | **Hotel:** {hotel}")
    st.write(f"**Productos:** {', '.join([x['prod'] for x in seleccionados])}")
    st.info("💡 Para imprimir: Presiona Ctrl+P en tu navegador.")



















































