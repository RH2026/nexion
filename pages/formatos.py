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

# ── 2. OPCIONES DE LOS SELECTORES (AGREGAMOS OPCIÓN VACÍA AL INICIO) ──
OPCIONES_ESTATUS = ["🆕 PENDIENTE", "🚚 EN RUTA", "✅ ENTREGADO", "❌ CANCELADO"]
# Agregamos "" al inicio para que el "None" desaparezca y quede en blanco
OPCIONES_PAQUETERIA = ["", "FEDEX", "TRES GUERRAS", "CASTORES", "ONE", "PAQMEX", "TAMAZULA", "TIBSA", "KORA", "SANCHEZ", "TINY", "POTOSINOS"]
OPCIONES_SURTIDOR = ["", "SANDRA", "YAZMIN", "KEVIN", "FELIX"]

st.set_page_config(page_title="Nexion Core - Matrix", layout="wide")
st.markdown("### ⚡ Panel de Control: Matriz de Pedidos")

# ── 3. LÓGICA DE CARGA ULTRA LIMPIA ──
def get_data_nexion():
    if 'df_pedidos' not in st.session_state:
        try:
            # Forzamos a pandas a ignorar los NA y tratarlos como strings vacíos
            df = pd.read_csv(CSV_URL, keep_default_na=False).fillna("")
            
            columnas_lectura = ["NO CLIENTE", "FACTURA", "NOMBRE DEL CLIENTE", "DESTINO", "FECHA DE ENVÍO"]
            columnas_nuevas = ["ESTATUS", "SURTIDOR", "PAQUETERIA", "INCIDENCIA"]
            
            # Asegurar que todas las columnas existan y estén limpias
            all_cols = columnas_lectura + columnas_nuevas
            for col in all_cols:
                if col not in df.columns:
                    df[col] = ""
                else:
                    # Reemplazo total de cualquier rastro de "None" o "nan" por vacío real
                    df[col] = df[col].astype(str).replace(['None', 'nan', 'NaN', 'None ', 'nan ', 'N/A'], '')
                    df[col] = df[col].str.strip()

            # Validación final para que el Editor no se pierda
            if not df.empty:
                # Si el estatus no es válido, poner el primero por defecto
                df.loc[~df['ESTATUS'].isin(OPCIONES_ESTATUS), 'ESTATUS'] = OPCIONES_ESTATUS[0]
                # Para los demás, si no están en la lista, asegurar que sean un string vacío ""
                df.loc[~df['SURTIDOR'].isin(OPCIONES_SURTIDOR), 'SURTIDOR'] = ""
                df.loc[~df['PAQUETERIA'].isin(OPCIONES_PAQUETERIA), 'PAQUETERIA'] = ""
            
            st.session_state.df_pedidos = df[all_cols]
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            return pd.DataFrame()
    return st.session_state.df_pedidos

# ── 4. BOTÓN RECARGAR ──
if st.button("🔄 RECARGAR MATRIZ"):
    if 'df_pedidos' in st.session_state:
        del st.session_state.df_pedidos
    st.cache_data.clear()
    st.rerun()

# ── 5. EDITOR DE DATOS (CONFIGURADO PARA BLANCOS) ──
df_actual = get_data_nexion()

if not df_actual.empty:
    edited_df = st.data_editor(
        df_actual,
        use_container_width=True,
        hide_index=True,
        key="editor_nexion_final_v6",
        column_config={
            "ESTATUS": st.column_config.SelectboxColumn("ESTATUS", options=OPCIONES_ESTATUS, width="medium"),
            "SURTIDOR": st.column_config.SelectboxColumn("SURTIDOR", options=OPCIONES_SURTIDOR, width="small"),
            "PAQUETERIA": st.column_config.SelectboxColumn("PAQUETERIA", options=OPCIONES_PAQUETERIA, width="medium"),
            "INCIDENCIA": st.column_config.TextColumn("INCIDENCIA", width="large"),
            "NO CLIENTE": st.column_config.TextColumn(disabled=True),
            "FACTURA": st.column_config.TextColumn(disabled=True),
            "NOMBRE DEL CLIENTE": st.column_config.TextColumn(disabled=True),
            "DESTINO": st.column_config.TextColumn(disabled=True),
            "FECHA DE ENVÍO": st.column_config.TextColumn(disabled=True),
        }
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 6. GUARDADO Y DESCARGA ──
    col_save, col_download = st.columns([2, 1])

    with col_save:
        if st.button("🚀 EJECUTAR UPLINK A GITHUB", type="primary", use_container_width=True):
            if TOKEN:
                with st.status("Sincronizando...", expanded=True) as status:
                    try:
                        g = Github(TOKEN)
                        repo = g.get_repo(REPO_NAME)
                        csv_string = edited_df.to_csv(index=False)
                        contents = repo.get_contents(FILE_PATH)
                        
                        hora_local = datetime.now(tz_gdl).strftime('%H:%M:%S')
                        repo.update_file(path=FILE_PATH, message=f"PRO_SYNC // {hora_local}", content=csv_string, sha=contents.sha)
                        
                        st.session_state.df_pedidos = edited_df
                        status.update(label="Sincronización Exitosa", state="complete", expanded=False)
                        st.toast("GitHub Actualizado correctamente", icon="✅")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        status.update(label=f"Error: {e}", state="error")

    with col_download:
        csv_data = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 DESCARGAR LOCAL", data=csv_data, file_name="pedidos_nexion.csv", mime="text/csv", use_container_width=True)
else:
    st.info("Sin datos para mostrar.")






















































































































































