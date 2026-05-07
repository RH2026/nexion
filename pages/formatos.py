import streamlit as st
import pandas as pd
from github import Github
import io
import pytz
import time
from datetime import datetime

# ── 1. CONFIGURACIÓN DE ACCESO Y RUTAS ──
# Asegúrate de tener GITHUB_TOKEN en tu archivo .streamlit/secrets.toml
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "pedidos.csv"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/pedidos.csv"
tz_gdl = pytz.timezone('America/Mexico_City')

# Opciones de estatus con emojis para que el operador identifique todo de un vistazo
OPCIONES_ESTATUS = ["🆕 PENDIENTE", "🚚 EN RUTA", "✅ ENTREGADO", "❌ CANCELADO"]

st.set_page_config(page_title="Nexion Core - Matrix", layout="wide")

st.markdown("### ⚡ Panel de Control: Matriz de Pedidos")

# ── 2. LÓGICA DE CARGA ULTRA RÁPIDA (SESSION STATE) ──
def get_data_nexion():
    # Usamos el estado de sesión para que la edición sea fluida y sin lag
    if 'df_pedidos' not in st.session_state:
        try:
            # Lectura directa del RAW de GitHub
            df = pd.read_csv(CSV_URL)
            columnas_requeridas = ["NO CLIENTE", "FACTURA", "NOMBRE DEL CLIENTE", "DESTINO", "FECHA DE ENVÍO"]
            
            # Verificación de columnas para evitar errores de carga
            for col in columnas_requeridas:
                if col not in df.columns: 
                    df[col] = "N/A"
            
            # Si no existe la columna ESTATUS, la creamos
            if "ESTATUS" not in df.columns:
                df["ESTATUS"] = OPCIONES_ESTATUS[0]
            
            st.session_state.df_pedidos = df[columnas_requeridas + ["ESTATUS"]]
        except Exception as e:
            st.error(f"Error de conexión con el nodo: {e}")
            return pd.DataFrame()
    return st.session_state.df_pedidos

# ── 3. ACCIONES DE REFRESCO ──
col_acc1, col_acc2 = st.columns([1, 5])
with col_acc1:
    if st.button("🔄 RECARGAR MATRIZ", use_container_width=True):
        if 'df_pedidos' in st.session_state:
            del st.session_state.df_pedidos
        st.cache_data.clear()
        st.rerun()

# ── 4. EDITOR DE DATOS (LA MATRIZ EDITABLE) ──
df_actual = get_data_nexion()

if not df_actual.empty:
    # Configuramos el editor para que solo el ESTATUS sea editable (Check Rápido)
    edited_df = st.data_editor(
        df_actual,
        use_container_width=True,
        hide_index=True,
        key="editor_nexion_v3",
        column_config={
            "ESTATUS": st.column_config.SelectboxColumn(
                "ESTATUS",
                help="Selecciona el estado con un clic",
                options=OPCIONES_ESTATUS,
                width="medium",
                required=True,
            ),
            # Bloqueamos el resto de columnas para evitar ediciones accidentales
            "NO CLIENTE": st.column_config.TextColumn(disabled=True),
            "FACTURA": st.column_config.TextColumn(disabled=True),
            "NOMBRE DEL CLIENTE": st.column_config.TextColumn(disabled=True),
            "DESTINO": st.column_config.TextColumn(disabled=True),
            "FECHA DE ENVÍO": st.column_config.TextColumn(disabled=True),
        }
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 5. BOTONES DE GUARDADO Y DESCARGA ──
    col_save, col_download = st.columns([2, 1])

    with col_save:
        if st.button("🚀 EJECUTAR UPLINK A GITHUB", type="primary", use_container_width=True):
            if not TOKEN:
                st.error("Error: Token de seguridad no encontrado.")
            else:
                with st.status("Sincronizando con Nexion Core...", expanded=True) as status:
                    try:
                        g = Github(TOKEN)
                        repo = g.get_repo(REPO_NAME)
                        
                        # Convertir los datos editados a CSV
                        csv_string = edited_df.to_csv(index=False)
                        
                        # Obtener el archivo para el SHA (evita conflictos de versión)
                        contents = repo.get_contents(FILE_PATH)
                        
                        hora_local = datetime.now(tz_gdl).strftime('%H:%M:%S')
                        repo.update_file(
                            path=FILE_PATH,
                            message=f"MATRIX_SYNC // {hora_local}",
                            content=csv_string,
                            sha=contents.sha
                        )
                        
                        # Actualizamos la memoria local para que los cambios persistan
                        st.session_state.df_pedidos = edited_df
                        status.update(label="Sincronización Exitosa", state="complete", expanded=False)
                        st.toast("Nodos actualizados en la nube", icon="✅")
                        time.sleep(1)
                        st.rerun()
                        
                    except Exception as e:
                        status.update(label=f"Fallo en Uplink: {str(e)}", state="error")

    with col_download:
        # Generar CSV preparado para Excel (con encoding correcto)
        csv_data = edited_df.to_csv(index=False).encode('utf-8-sig')
        fecha_str = datetime.now(tz_gdl).strftime('%d_%m_%Y')
        
        st.download_button(
            label="📥 DESCARGAR LOCAL",
            data=csv_data,
            file_name=f"nexion_pedidos_{fecha_str}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.info("No hay datos disponibles para mostrar en este momento.")






















































































































































