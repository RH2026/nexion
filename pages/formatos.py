import streamlit as st
import pandas as pd
from github import Github
import io
import pytz
import time
from datetime import datetime

# ── 1. CONFIGURACIÓN DE ACCESO Y RUTAS ──
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "pedidos.csv"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/pedidos.csv"
tz_gdl = pytz.timezone('America/Mexico_City')

# ── 2. OPCIONES DE LOS SELECTORES (DROP-DOWNS) ──
OPCIONES_ESTATUS = ["🆕 PENDIENTE", "🚚 EN RUTA", "✅ ENTREGADO", "❌ CANCELADO"]
OPCIONES_PAQUETERIA = ["FEDEX", "TRES GUERRAS", "CASTORES", "ONE", "PAQMEX", "TAMAZULA", "TIBSA", "KORA", "SANCHEZ", "TINY", "POTOSINOS"]
OPCIONES_SURTIDOR = ["SANDRA", "YAZMIN", "KEVIN", "FELIX"]

st.set_page_config(page_title="Nexion Core - Matrix", layout="wide")
st.markdown("### ⚡ Panel de Control: Matriz de Pedidos")

# ── 3. LÓGICA DE CARGA ULTRA RÁPIDA (SESSION STATE) ──
def get_data_nexion():
    if 'df_pedidos' not in st.session_state:
        try:
            df = pd.read_csv(CSV_URL)
            # Columnas fijas de lectura
            columnas_lectura = ["NO CLIENTE", "FACTURA", "NOMBRE DEL CLIENTE", "DESTINO", "FECHA DE ENVÍO"]
            # Columnas nuevas que queremos agregar si no existen
            columnas_nuevas = ["ESTATUS", "SURTIDOR", "PAQUETERIA", "INCIDENCIA"]
            
            for col in columnas_lectura:
                if col not in df.columns: df[col] = "N/A"
            
            # Inicializar las columnas editables si son nuevas en el CSV
            for col in columnas_nuevas:
                if col not in df.columns:
                    df[col] = "" # O un valor por defecto
            
            st.session_state.df_pedidos = df[columnas_lectura + columnas_nuevas]
        except Exception as e:
            st.error(f"Error de conexión con el nodo: {e}")
            return pd.DataFrame()
    return st.session_state.df_pedidos

# ── 4. ACCIONES DE REFRESCO ──
if st.button("🔄 RECARGAR MATRIZ", use_container_width=False):
    if 'df_pedidos' in st.session_state:
        del st.session_state.df_pedidos
    st.cache_data.clear()
    st.rerun()

# ── 5. EDITOR DE DATOS (LA MATRIZ EDITABLE) ──
df_actual = get_data_nexion()

if not df_actual.empty:
    edited_df = st.data_editor(
        df_actual,
        use_container_width=True,
        hide_index=True,
        key="editor_nexion_v4",
        column_config={
            # SELECTORES RÁPIDOS
            "ESTATUS": st.column_config.SelectboxColumn("ESTATUS", options=OPCIONES_ESTATUS, width="medium"),
            "SURTIDOR": st.column_config.SelectboxColumn("SURTIDOR", options=OPCIONES_SURTIDOR, width="small"),
            "PAQUETERIA": st.column_config.SelectboxColumn("PAQUETERIA", options=OPCIONES_PAQUETERIA, width="medium"),
            
            # COLUMNA DE TEXTO LIBRE
            "INCIDENCIA": st.column_config.TextColumn("INCIDENCIA", help="Escribe aquí cualquier observación", width="large"),
            
            # COLUMNAS BLOQUEADAS (LECTURA)
            "NO CLIENTE": st.column_config.TextColumn(disabled=True),
            "FACTURA": st.column_config.TextColumn(disabled=True),
            "NOMBRE DEL CLIENTE": st.column_config.TextColumn(disabled=True),
            "DESTINO": st.column_config.TextColumn(disabled=True),
            "FECHA DE ENVÍO": st.column_config.TextColumn(disabled=True),
        }
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 6. BOTONES DE GUARDADO Y DESCARGA ──
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
                        csv_string = edited_df.to_csv(index=False)
                        contents = repo.get_contents(FILE_PATH)
                        
                        hora_local = datetime.now(tz_gdl).strftime('%H:%M:%S')
                        repo.update_file(
                            path=FILE_PATH,
                            message=f"MATRIX_UPDATE // {hora_local}",
                            content=csv_string,
                            sha=contents.sha
                        )
                        
                        st.session_state.df_pedidos = edited_df
                        status.update(label="Sincronización Exitosa", state="complete", expanded=False)
                        st.toast("Datos actualizados en GitHub", icon="✅")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        status.update(label=f"Fallo en Uplink: {str(e)}", state="error")

    with col_download:
        csv_data = edited_df.to_csv(index=False).encode('utf-8-sig')
        fecha_str = datetime.now(tz_gdl).strftime('%d_%m_%Y')
        st.download_button(
            label="📥 DESCARGAR LOCAL",
            data=csv_data,
            file_name=f"nexion_pedidos_{fecha_str}.csv",
            mime="text/csv",
            use_container_width=True
        )






















































































































































