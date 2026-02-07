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
        repo.update_file(contents.path, mensaje_commit, df_to_save.to_csv(index=False), contents.sha)
        st.success(f"✅ Sincronizado: {mensaje_commit}")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error en GitHub: {e}")

# --- INTERFAZ ESTILO INGENIERÍA ---
st.set_page_config(page_title="JYPESA - Ingeniería", layout="wide")

st.markdown("""
    <div style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px;">
        <h1 style="margin-bottom: 0; color: #1E3A8A;">JYPESA</h1>
        <h5 style="margin-top: 0; color: #555; letter-spacing: 2px;">AUTOMATIZACIÓN DE PROCESOS</h5>
    </div>
    <br>
    """, unsafe_allow_html=True)

# DATOS FIJOS DEL REMITENTE
with st.expander("📍 DATOS DEL REMITENTE (FIJOS)", expanded=False):
    st.markdown("""
    **Remitente:** Jabones y productos Especializados  
    **Dirección:** C. Cernícalo 155, Col. La Aurora, CP 44460  
    **Ciudad:** Guadalajara, Jalisco  
    **Contacto:** Rigoberto Hernandez | **Tel:** 3319753122
    """)

# --- NUEVA SECCIÓN: BUSCADOR RÁPIDO POR FOLIO ---
st.markdown("### 🔍 CONSULTA RÁPIDA DE ENVÍOS")
df_busqueda = load_data_fresh()
c_bus1, c_bus2 = st.columns([1, 3])
folio_query = c_bus1.text_input("Ingresa Folio a consultar", placeholder="Ej. 3")

if folio_query:
    # Filtramos la información del folio
    res = df_busqueda[df_busqueda["FOLIO"].astype(str) == str(folio_query)]
    if not res.empty:
        datos = res.iloc[0] # Tomamos el primero para datos generales
        with st.container(border=True):
            col_inf1, col_inf2, col_inf3, col_inf4 = st.columns(4)
            col_inf1.metric("DESTINATARIO", datos["DESTINATARIO /  NOMBRE DEL HOTEL"])
            col_inf2.metric("TRANSPORTE", datos["TRANSPORTE"] if pd.notna(datos["TRANSPORTE"]) else "Pendiente")
            col_inf3.metric("GUÍA", datos["GUIA"] if pd.notna(datos["GUIA"]) else "Pendiente")
            col_inf4.metric("COSTO GUÍA", f"${datos['COSTO GUIA']}")
    else:
        st.warning("No se encontró información para ese folio.")

st.divider()

# --- TABS ORIGINALES ---
tab1, tab2 = st.tabs(["📋 Registro e Impresión", "⚙️ Actualización de Logística"])

# --- TAB 1: REGISTRO (IDÉNTICO) ---
with tab1:
    with st.form("registro_ingenieria"):
        c1, c2, c3 = st.columns(3)
        folio = c1.text_input("FOLIO")
        fecha = c2.date_input("FECHA", datetime.date.today())
        hotel = c3.text_input("DESTINATARIO /  NOMBRE DEL HOTEL")
        
        c4, c5, c6, c7 = st.columns(4)
        ciudad = c4.text_input("CIUDAD")
        estado = c5.text_input("ESTADO")
        contacto = c6.text_input("CONTACTO")
        telefono = c7.text_input("TELEFONO")
        
        f_envio = st.selectbox("FORMA DE ENVIO", ["PAQUETERIA", "ENTREGA LOCAL", "RECOLECCION EN PLANTA"])
        
        st.markdown("---")
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
        
        st.markdown("---")
        st.subheader("Producto No Listado (Extra)")
        ce1, ce2, ce3, ce4 = st.columns([1,1,2,2])
        cant_ex = ce1.text_input("CANTIDAD EXTRA")
        um_ex = ce2.text_input("UM")
        prod_ex = ce3.text_input("PRODUCTO EXTRA")
        desc_ex = ce4.text_input("DESCRIPCION EXTRA")
        
        col_b1, col_b2 = st.columns(2)
        btn_guardar = col_b1.form_submit_button("💾 GUARDAR REGISTRO")
        btn_imprimir = col_b2.form_submit_button("🖨️ RENDERIZAR FORMATO IMPRESIÓN")

    if btn_guardar:
        df_actual = load_data_fresh()
        nuevas_filas = []
        for item in seleccionados:
            nuevas_filas.append({
                "FOLIO": folio, "FECHA": str(fecha), "DESTINATARIO /  NOMBRE DEL HOTEL": hotel,
                "CIUDAD": ciudad, "ESTADO": estado, "CONTACTO": contacto, "TELEFONO": telefono,
                "FORMA DE ENVIO": f_envio, "TRANSPORTE": "", "GUIA": "", "COSTO GUIA": 0,
                "PRODUCTO": item["p"], "PRECIO": item["pre"], "PRODUCTO EXTRA": "", "CANTIDAD EXTRA": "", "DESCRIPCION EXTRA": ""
            })
        if prod_ex:
            nuevas_filas.append({
                "FOLIO": folio, "FECHA": str(fecha), "DESTINATARIO /  NOMBRE DEL HOTEL": hotel,
                "CIUDAD": ciudad, "ESTADO": estado, "CONTACTO": contacto, "TELEFONO": telefono,
                "FORMA DE ENVIO": f_envio, "TRANSPORTE": "", "GUIA": "", "COSTO GUIA": 0,
                "PRODUCTO": "EXTRA", "PRECIO": 0, "PRODUCTO EXTRA": prod_ex, "CANTIDAD EXTRA": f"{cant_ex} {um_ex}", "DESCRIPCION EXTRA": desc_ex
            })
        if nuevas_filas:
            df_final = pd.concat([df_actual, pd.DataFrame(nuevas_filas)], ignore_index=True)
            save_to_github(df_final, f"Registro Folio {folio}")
            st.rerun()

    if btn_imprimir:
        st.markdown(f"""
            <div style="background-color: white; padding: 30px; border: 2px solid #1E3A8A; color: black; font-family: 'Courier New', Courier, monospace;">
                <div style="text-align: center; border-bottom: 2px solid black; padding-bottom: 10px;">
                    <h1 style="margin:0;">JYPESA</h1>
                    <p style="margin:0; font-weight: bold;">Automatización de Procesos</p>
                </div>
                <br>
                <div style="font-size: 14px;">
                    <p><b>FOLIO:</b> {folio} &nbsp;&nbsp; <b>FECHA:</b> {fecha}</p>
                    <hr>
                    <p><b>REMITENTE:</b> Jabones y productos Especializados | C. Cernícalo 155, La Aurora, GDL.</p>
                    <p><b>DESTINATARIO:</b> {hotel}</p>
                    <p><b>DESTINO:</b> {ciudad}, {estado} | <b>ENVÍO:</b> {f_envio}</p>
                    <p><b>ATENCIÓN:</b> {contacto} | <b>TEL:</b> {telefono}</p>
                    <hr>
                    <h4 style="text-align:center;">DETALLE DE PRODUCTOS (SIN COSTO)</h4>
                    <ul>
                        {"".join([f"<li>{item['p']}</li>" for item in seleccionados])}
                        {f"<li>{cant_ex} {um_ex} - {prod_ex} ({desc_ex})</li>" if prod_ex else ""}
                    </ul>
                </div>
                <br><br>
                <div style="text-align: center; font-size: 10px; color: #555; border-top: 1px dashed black;">
                    PARA USO INTERNO - CONTROL DE MUESTRAS JYPESA
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- TAB 2: ACTUALIZACIÓN (IDÉNTICO) ---
with tab2:
    c_ref1, c_ref2 = st.columns([1,4])
    if c_ref1.button("🔄 ACTUALIZAR LISTA"):
        st.cache_data.clear()
        st.rerun()
    
    st.subheader("⚙️ Control Logístico Posterior")
    df_repo = load_data_fresh()
    
    if not df_repo.empty:
        df_repo['FOLIO'] = df_repo['FOLIO'].astype(str)
        folios_lista = sorted(df_repo["FOLIO"].unique().tolist(), reverse=True)
        folio_update = st.selectbox("Seleccione Folio para completar Transporte/Guía", folios_lista)
        
        if folio_update:
            idx_folio = df_repo[df_repo["FOLIO"] == folio_update].index
            datos_act = df_repo.loc[idx_folio[0]]
            
            st.info(f"📍 Editando: {datos_act['DESTINATARIO /  NOMBRE DEL HOTEL']} ({datos_act['CIUDAD']})")
            
            with st.form("form_update_log"):
                u1, u2, u3 = st.columns(3)
                t_val = u1.text_input("TRANSPORTE", value=str(datos_act.get("TRANSPORTE", "")))
                g_val = u2.text_input("GUIA", value=str(datos_act.get("GUIA", "")))
                c_val = u3.number_input("COSTO GUIA", value=float(datos_act.get("COSTO GUIA", 0.0)))
                
                if st.form_submit_button("🔒 GUARDAR CAMBIOS"):
                    df_repo.loc[idx_folio, ["TRANSPORTE", "GUIA", "COSTO GUIA"]] = [t_val, g_val, c_val]
                    save_to_github(df_repo, f"Update Logistica Folio {folio_update}")
                    st.rerun()
























































