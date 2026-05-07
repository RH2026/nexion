import streamlit as st
import pandas as pd
from github import Github
import io
import pytz
from datetime import datetime

# ── 1. CONFIGURACIÓN DE ACCESO Y RUTAS ──
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "pedidos.csv"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/pedidos.csv"
tz_gdl = pytz.timezone('America/Mexico_City')

# Opciones de estatus con emojis para identificación visual rápida
OPCIONES_ESTATUS = ["🆕 PENDIENTE", "🚚 EN RUTA", "✅ ENTREGADO", "❌ CANCELADO"]

st.markdown("### ⚡ Panel de Control: Matriz de Pedidos")

# ── 2. LÓGICA DE CARGA ULTRA RÁPIDA (SESSION STATE) ──
def get_data_nexion():
    if 'df_pedidos' not in st.session_state:
        try:
            # Lectura directa del RAW
            df = pd.read_csv(CSV_URL)
            columnas_requeridas = ["NO CLIENTE", "FACTURA", "NOMBRE DEL CLIENTE", "DESTINO", "FECHA DE ENVÍO"]
            
            # Asegurar que existan las columnas base
            for col in columnas_requeridas:
                if col not in df.columns: df[col] = "N/A"
            
            # Inyectar ESTATUS si no existe
            if "ESTATUS" not in df.columns:
                df["ESTATUS"] = OPCIONES_ESTATUS[0] # PENDIENTE por defecto
            
            # Guardamos en el estado de sesión para velocidad instantánea
            st.session_state.df_pedidos = df[columnas_requeridas + ["ESTATUS"]]
        except Exception as e:
            st.error(f"Error de conexión con el nodo: {e}")
            return pd.DataFrame()
    return st.session_state.df_pedidos

# ── 3. ACCIONES RÁPIDAS (BOTONES SUPERIORES) ──
col_acc1, col_acc2, col_spacer = st.columns([1, 1, 2])

with col_acc1:
    if st.button("🔄 REFRESCAR DATOS", use_container_width=True):
        if 'df_pedidos' in st.session_state:
            del st.session_state.df_pedidos
        st.rerun()

with col_acc2:
    # Botón para limpiar selección (opcional)
    if st.button("🧹 LIMPIAR CACHÉ", use_container_width=True):
        st.cache_data.clear()
        st.toast("Caché del sistema depurada")

# ── 4. EDITOR DE DATOS (UX OPTIMIZADA) ──
df_actual = get_data_nexion()

if not df_actual.empty:
    # El corazón del check rápido: SelectboxColumn
    edited_df = st.data_editor(
        df_actual,
        use_container_width=True,
        hide_index=True,
        key="editor_nexion_v3",
        column_config={
            "ESTATUS": st.column_config.SelectboxColumn(
                "ESTATUS",
                help="Clic para cambiar estado",
                options=OPCIONES_ESTATUS,
                width="medium",
                required=True,
            ),
            # Bloqueamos las demás columnas para que el cursor vaya directo al estatus
            "NO CLIENTE": st.column_config.TextColumn(disabled=True),
            "FACTURA": st.column_config.TextColumn(disabled=True),
            "NOMBRE DEL CLIENTE": st.column_config.TextColumn(disabled=True),
            "DESTINO": st.column_config.TextColumn(disabled=True),
            "FECHA DE ENVÍO": st.column_config.TextColumn(disabled=True),
        }
    )

    st.markdown("---")

    # ── 5. GUARDADO MASIVO A GITHUB ──
    if st.button("🚀 EJECUTAR UPLINK A GITHUB", type="primary", use_container_width=True):
        if not TOKEN:
            st.error("Error: GITHUB_TOKEN no configurado en secrets.")
        else:
            with st.status("Sincronizando con Nexion Core...", expanded=True) as status:
                try:
                    g = Github(TOKEN)
                    repo = g.get_repo(REPO_NAME)
                    
                    # Convertir a CSV sin index
                    csv_string = edited_df.to_csv(index=False)
                    
                    # Obtener el archivo actual para el SHA
                    contents = repo.get_contents(FILE_PATH)
                    
                    # Commit
                    hora_local = datetime.now(tz_gdl).strftime('%H:%M:%S')
                    repo.update_file(
                        path=FILE_PATH,
                        message=f"MATRIX_SYNC // {hora_local}",
                        content=csv_string,
                        sha=contents.sha
                    )
                    
                    # Actualizar memoria local para evitar recargas
                    st.session_state.df_pedidos = edited_df
                    status.update(label="Sincronización Exitosa", state="complete", expanded=False)
                    st.toast("Nodos actualizados correctamente", icon="✅")
                    
                except Exception as e:
                    status.update(label=f"Fallo en Uplink: {str(e)}", state="error")
else:
    st.info("Esperando conexión con el archivo pedidos.csv...")






















































































































































