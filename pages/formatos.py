import streamlit as st
import pandas as pd
from github import Github
import datetime

# --- CONFIGURACIÓN DE GITHUB ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "pages/muestras.csv"

def load_data_fresh():
    timestamp = datetime.datetime.now().timestamp()
    csv_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?v={timestamp}"
    try:
        df = pd.read_csv(csv_url)
        df['FOLIO'] = df['FOLIO'].astype(str)
        # Limpiamos espacios en blanco accidentales en los nombres de columnas
        df.columns = df.columns.str.strip()
        return df
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
        # Convertimos a CSV sin índice para evitar columnas fantasma
        csv_data = df_to_save.to_csv(index=False)
        repo.update_file(contents.path, mensaje_commit, csv_data, contents.sha)
        st.success(f"✅ Sincronizado: {mensaje_commit}")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error en GitHub: {e}")

# --- INTERFAZ ---
st.set_page_config(page_title="JYPESA - Ingeniería", layout="wide")

st.markdown("""
    <div style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px;">
        <h1 style="margin-bottom: 0; color: #1E3A8A;">JYPESA</h1>
        <h5 style="margin-top: 0; color: #555; letter-spacing: 2px;">AUTOMATIZACIÓN DE PROCESOS</h5>
    </div>
    <br>
    """, unsafe_allow_html=True)

# DATOS DEL REMITENTE
with st.expander("📍 DATOS DEL REMITENTE (FIJOS)", expanded=False):
    st.markdown("""
    **Remitente:** Jabones y productos Especializados  
    **Dirección:** C. Cernícalo 155, Col. La Aurora, CP 44460  
    **Ciudad:** Guadalajara, Jalisco  
    **Contacto:** Rigoberto Hernandez | **Tel:** 3319753122
    """)

# --- CONSULTA RÁPIDA ---
st.markdown("### 🔍 CONSULTA RÁPIDA DE ENVÍOS")
df_busqueda = load_data_fresh()
c_bus1, c_bus2 = st.columns([1, 3])
folio_query = c_bus1.text_input("Ingresa Folio a consultar")

if folio_query:
    res = df_busqueda[df_busqueda["FOLIO"] == str(folio_query)]
    if not res.empty:
        datos = res.iloc[0]
        with st.container(border=True):
            col_inf1, col_inf2, col_inf3, col_inf4, col_inf5 = st.columns(5)
            col_inf1.metric("FECHA ENVÍO", str(datos["FECHA"]))
            col_inf2.metric("DESTINATARIO", datos.get("DESTINATARIO /  NOMBRE DEL HOTEL", "N/A"))
            col_inf3.metric("TRANSPORTE", str(datos["TRANSPORTE"]) if pd.notna(datos["TRANSPORTE"]) and datos["TRANSPORTE"] != "" else "Pendiente")
            col_inf4.metric("GUÍA", str(datos["GUIA"]) if pd.notna(datos["GUIA"]) and datos["GUIA"] != "" else "Pendiente")
            col_inf5.metric("COSTO GUÍA", f"${datos['COSTO GUIA']}")
    else:
        st.warning("No se encontró información para ese folio.")

st.divider()

tab1, tab2 = st.tabs(["📋 Registro e Impresión", "⚙️ Actualización de Logística"])

# --- TAB 1: REGISTRO ---
with tab1:
    with st.form("registro_ingenieria"):
        c1, c2, c3 = st.columns(3)
        folio_reg = c1.text_input("FOLIO")
        fecha_reg = c2.date_input("FECHA", datetime.date.today())
        hotel_reg = c3.text_input("DESTINATARIO /  NOMBRE DEL HOTEL")
        
        c4, c5, c6, c7 = st.columns(4)
        ciudad_reg = c4.text_input("CIUDAD")
        estado_reg = c5.text_input("ESTADO")
        contacto_reg = c6.text_input("CONTACTO")
        telefono_reg = c7.text_input("TELEFONO")
        
        f_envio_reg = st.selectbox("FORMA DE ENVIO", ["PAQUETERIA", "ENTREGA LOCAL", "RECOLECCION EN PLANTA"])
        
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
        
        ce1, ce2, ce3, ce4 = st.columns([1,1,2,2])
        cant_ex = ce1.text_input("CANTIDAD EXTRA")
        um_ex = ce2.text_input("UM")
        prod_ex = ce3.text_input("PRODUCTO EXTRA")
        desc_ex = ce4.text_input("DESCRIPCION EXTRA")
        
        btn_guardar = st.form_submit_button("💾 GUARDAR REGISTRO")
        btn_imprimir = st.form_submit_button("🖨️ RENDERIZAR FORMATO IMPRESIÓN")

    if btn_guardar:
        # Volvemos a leer para no perder lo que otros hayan guardado mientras llenábamos el form
        df_fresh = load_data_fresh()
        nuevas_filas = []
        for item in seleccionados:
            nuevas_filas.append({
                "FOLIO": str(folio_reg), "FECHA": str(fecha_reg), "DESTINATARIO /  NOMBRE DEL HOTEL": hotel_reg,
                "CIUDAD": ciudad_reg, "ESTADO": estado_reg, "CONTACTO": contacto_reg, "TELEFONO": telefono_reg,
                "FORMA DE ENVIO": f_envio_reg, "TRANSPORTE": "", "GUIA": "", "COSTO GUIA": 0,
                "PRODUCTO": item["p"], "PRECIO": item["pre"], "PRODUCTO EXTRA": "", "CANTIDAD EXTRA": "", "DESCRIPCION EXTRA": ""
            })
        if prod_ex:
            nuevas_filas.append({
                "FOLIO": str(folio_reg), "FECHA": str(fecha_reg), "DESTINATARIO /  NOMBRE DEL HOTEL": hotel_reg,
                "CIUDAD": ciudad_reg, "ESTADO": estado_reg, "CONTACTO": contacto_reg, "TELEFONO": telefono_reg,
                "FORMA DE ENVIO": f_envio_reg, "TRANSPORTE": "", "GUIA": "", "COSTO GUIA": 0,
                "PRODUCTO": "EXTRA", "PRECIO": 0, "PRODUCTO EXTRA": prod_ex, "CANTIDAD EXTRA": f"{cant_ex} {um_ex}", "DESCRIPCION EXTRA": desc_ex
            })
        if nuevas_filas:
            df_final = pd.concat([df_fresh, pd.DataFrame(nuevas_filas)], ignore_index=True)
            save_to_github(df_final, f"Registro Folio {folio_reg}")
            st.rerun()

# --- TAB 2: ACTUALIZACIÓN (REPARADO) ---
with tab2:
    if st.button("🔄 ACTUALIZAR LISTA"):
        st.cache_data.clear()
        st.rerun()
    
    st.subheader("⚙️ Control Logístico Posterior")
    df_update = load_data_fresh()
    
    if not df_update.empty:
        folios_lista = sorted(df_update["FOLIO"].unique().tolist(), reverse=True)
        folio_sel = st.selectbox("Seleccione Folio para completar Transporte/Guía", folios_lista)
        
        if folio_sel:
            # Seleccionamos todas las filas del folio
            mask = df_update["FOLIO"] == str(folio_sel)
            datos_act = df_update[mask].iloc[0]
            
            st.info(f"📍 Editando Logística para: {datos_act.get('DESTINATARIO /  NOMBRE DEL HOTEL', 'N/A')}")
            
            with st.form("form_update_log"):
                u1, u2, u3 = st.columns(3)
                t_val = u1.text_input("TRANSPORTE", value=str(datos_act["TRANSPORTE"]) if pd.notna(datos_act["TRANSPORTE"]) else "")
                g_val = u2.text_input("GUIA", value=str(datos_act["GUIA"]) if pd.notna(datos_act["GUIA"]) else "")
                c_val = u3.number_input("COSTO GUIA", value=float(datos_act["COSTO GUIA"]) if pd.notna(datos_act["COSTO GUIA"]) else 0.0)
                
                if st.form_submit_button("🔒 GUARDAR CAMBIOS"):
                    # Volvemos a cargar los datos ANTES de guardar para asegurar que el DataFrame está completo
                    df_final_save = load_data_fresh()
                    df_final_save.loc[df_final_save["FOLIO"] == str(folio_sel), ["TRANSPORTE", "GUIA", "COSTO GUIA"]] = [t_val, g_val, c_val]
                    
                    save_to_github(df_final_save, f"Update Logistica Folio {folio_sel}")
                    st.rerun()


























































