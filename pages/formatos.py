import streamlit as st
import pandas as pd
from github import Github
import datetime

# --- CONFIGURACIÓN DE GITHUB ---
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "pages/muestras.csv"

# Función para forzar la lectura fresca de GitHub
def load_data_fresh():
    # Añadimos un parámetro aleatorio a la URL para saltar el caché de GitHub
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
        # Limpiar caché de la app para que reconozca el nuevo folio inmediatamente
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

tab1, tab2 = st.tabs(["📋 Registro e Impresión", "⚙️ Actualización de Logística"])

# --- TAB 1: REGISTRO (Mismo código anterior) ---
with tab1:
    # ... (Tu código de formulario se mantiene igual para no mover el estilo)
    with st.form("registro_ingenieria"):
        c1, c2, c3 = st.columns(3)
        folio = c1.text_input("FOLIO (ID Único)")
        fecha = c2.date_input("FECHA DE SOLICITUD", datetime.date.today())
        hotel = c3.text_input("DESTINATARIO /  NOMBRE DEL HOTEL")
        # [Resto de los inputs...]
        # (Asegúrate de mantener aquí la lógica de seleccionados y p_ex)
        
        # Simulando el final del form para el botón:
        btn_guardar = st.form_submit_button("💾 GUARDAR REGISTRO")
        
    if btn_guardar:
        df_actual = load_data_fresh()
        # Lógica de creación de filas...
        # save_to_github(df_final, f"Registro Folio {folio}")

# --- TAB 2: ACTUALIZACIÓN (CON REFRESCO FORZADO) ---
with tab2:
    col_ref, col_tit = st.columns([1, 4])
    if col_ref.button("🔄 REFRESCAR LISTA"):
        st.cache_data.clear()
        st.rerun()
    
    col_tit.subheader("⚙️ Control Logístico Posterior")
    
    # Cargamos datos frescos
    df_repo = load_data_fresh()
    
    if not df_repo.empty:
        # Limpiamos valores nulos en FOLIO para evitar errores en el selectbox
        df_repo['FOLIO'] = df_repo['FOLIO'].astype(str)
        folios_lista = sorted(df_repo["FOLIO"].unique().tolist(), reverse=True)
        
        folio_update = st.selectbox("Seleccione Folio para Carga de Datos", folios_lista, help="Si no aparece el folio reciente, presione REFRESCAR LISTA")
        
        if folio_update:
            idx_folio = df_repo[df_repo["FOLIO"] == folio_update].index
            datos_actuales = df_repo.loc[idx_folio[0]]
            
            st.info(f"📍 Destino: {datos_actuales['DESTINATARIO /  NOMBRE DEL HOTEL']}")
            
            with st.form("form_update_log"):
                u1, u2, u3 = st.columns(3)
                t_val = u1.text_input("TRANSPORTE", value=str(datos_actuales.get("TRANSPORTE", "")))
                g_val = u2.text_input("GUIA", value=str(datos_actuales.get("GUIA", "")))
                c_val = u3.number_input("COSTO GUIA", value=float(datos_actuales.get("COSTO GUIA", 0.0)))
                
                if st.form_submit_button("🔒 GUARDAR CAMBIOS LOGÍSTICOS"):
                    df_repo.loc[idx_folio, "TRANSPORTE"] = t_val
                    df_repo.loc[idx_folio, "GUIA"] = g_val
                    df_repo.loc[idx_folio, "COSTO GUIA"] = c_val
                    save_to_github(df_repo, f"Update Logistica Folio {folio_update}")
                    st.rerun() # Para recargar la vista con los nuevos datos























































