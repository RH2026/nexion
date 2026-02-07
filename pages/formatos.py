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
        # Forzamos a que el folio sea string y quitamos nulos para evitar errores de índice
        df['FOLIO'] = df['FOLIO'].astype(str)
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
        # index=False es vital para que no se cree una columna de números extra
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

# --- CONSULTA RÁPIDA ---
st.markdown("### 🔍 CONSULTA RÁPIDA")
df_master = load_data_fresh()
c_q1, c_q2 = st.columns([1, 3])
folio_q = c_q1.text_input("Ingresa Folio")

if folio_q:
    res = df_master[df_master["FOLIO"] == str(folio_q)]
    if not res.empty:
        d = res.iloc[0]
        st.info(f"**Fecha:** {d['FECHA']} | **Hotel:** {d['DESTINATARIO /  NOMBRE DEL HOTEL']} | **Guía:** {d['GUIA']} | **Costo:** ${d['COSTO GUIA']}")
    else:
        st.warning("No encontrado.")

tab1, tab2 = st.tabs(["📋 Registro e Impresión", "⚙️ Actualización de Logística"])

# --- TAB 1: REGISTRO ---
with tab1:
    with st.form("form_registro"):
        c1, c2, c3 = st.columns(3)
        f_val = c1.text_input("FOLIO")
        fe_val = c2.date_input("FECHA", datetime.date.today())
        h_val = c3.text_input("DESTINATARIO /  NOMBRE DEL HOTEL")
        
        c4, c5, c6, c7 = st.columns(4)
        ciu, edo, con, tel = c4.text_input("CIUDAD"), c5.text_input("ESTADO"), c6.text_input("CONTACTO"), c7.text_input("TELEFONO")
        env = st.selectbox("FORMA DE ENVIO", ["PAQUETERIA", "LOCAL", "RECOLECCION"])
        
        prods_dict = {"Accesorios Ecologicos": 47.85, "Dispensador Almond": 218.33, "Dispensador Biogena": 216.00, "Dispensador Cava": 230.58, "Dispensador Persa": 275.00, "Dispensador Botánicos L": 274.17, "Dispensador Dove": 125.00, "Dispensador Biogena 400ml": 184.87, "Kit Elements": 29.34, "Kit Almond": 33.83, "Kit Biogena": 48.95, "Kit Cava": 34.59, "Kit Persa": 58.02, "Kit Lavarino": 36.30, "Kit Botánicos": 29.34, "Llave Macnetica": 180.00, "Rack Dove": 0.00, "Rack JH Blanco 2 pzas": 62.00, "Rack JH Blanco 1 pza": 50.00, "Soporte dob INOX": 679.00, "Soporte Ind INOX": 608.00}
        
        seleccionados = []
        cols = st.columns(3)
        for i, (p, pre) in enumerate(prods_dict.items()):
            if cols[i % 3].checkbox(p): seleccionados.append({"p": p, "pre": pre})
        
        ce1, ce2, ce3, ce4 = st.columns([1,1,2,2])
        c_ex, u_ex, p_ex, d_ex = ce1.text_input("CANT EXTRA"), ce2.text_input("UM"), ce3.text_input("PRODUCTO EXTRA"), ce4.text_input("DESCRIPCION EXTRA")
        
        if st.form_submit_button("💾 GUARDAR REGISTRO"):
            # MÉTODO SEGURO: Convertimos el DF actual a lista de diccionarios
            df_fresh = load_data_fresh()
            data_list = df_fresh.to_dict('records')
            
            # Agregamos los nuevos registros a la lista
            for item in seleccionados:
                data_list.append({"FOLIO": str(f_val), "FECHA": str(fe_val), "DESTINATARIO /  NOMBRE DEL HOTEL": h_val, "CIUDAD": ciu, "ESTADO": edo, "CONTACTO": con, "TELEFONO": tel, "FORMA DE ENVIO": env, "TRANSPORTE": "", "GUIA": "", "COSTO GUIA": 0, "PRODUCTO": item["p"], "PRECIO": item["pre"], "PRODUCTO EXTRA": "", "CANTIDAD EXTRA": "", "DESCRIPCION EXTRA": ""})
            
            if p_ex:
                data_list.append({"FOLIO": str(f_val), "FECHA": str(fe_val), "DESTINATARIO /  NOMBRE DEL HOTEL": h_val, "CIUDAD": ciu, "ESTADO": edo, "CONTACTO": con, "TELEFONO": tel, "FORMA DE ENVIO": env, "TRANSPORTE": "", "GUIA": "", "COSTO GUIA": 0, "PRODUCTO": "EXTRA", "PRECIO": 0, "PRODUCTO EXTRA": p_ex, "CANTIDAD EXTRA": f"{c_ex} {u_ex}", "DESCRIPCION EXTRA": d_ex})
            
            # Convertimos de vuelta a DataFrame y guardamos
            df_final = pd.DataFrame(data_list)
            save_to_github(df_final, f"Registro {f_val}")
            st.rerun()

# --- TAB 2: ACTUALIZACIÓN ---
with tab2:
    if st.button("🔄 RECARGAR LISTA"): st.rerun()
    df_up = load_data_fresh()
    if not df_up.empty:
        f_list = sorted(df_up["FOLIO"].unique().tolist(), reverse=True)
        f_sel = st.selectbox("Folio a actualizar logística", f_list)
        if f_sel:
            # Buscamos la primera fila de ese folio para ver qué tiene
            row_data = df_up[df_up["FOLIO"] == str(f_sel)].iloc[0]
            with st.form("up_log"):
                u1, u2, u3 = st.columns(3)
                nt = u1.text_input("TRANSPORTE", value=str(row_data.get("TRANSPORTE", "")))
                ng = u2.text_input("GUIA", value=str(row_data.get("GUIA", "")))
                nc = u3.number_input("COSTO GUIA", value=float(row_data.get("COSTO GUIA", 0.0)))
                
                if st.form_submit_button("🔒 ACTUALIZAR"):
                    # Actualizamos directamente sobre el DF cargado
                    df_up.loc[df_up["FOLIO"] == str(f_sel), ["TRANSPORTE", "GUIA", "COSTO GUIA"]] = [nt, ng, nc]
                    save_to_github(df_up, f"Logistica {f_sel}")
                    st.rerun()



























































