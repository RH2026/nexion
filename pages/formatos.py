import streamlit as st
import pandas as pd
from github import Github
import io

# ── CONFIGURACIÓN DE ACCESO ──
TOKEN = st.secrets.get("GITHUB_TOKEN", None)
REPO_NAME = "RH2026/nexion"
FILE_PATH = "pedidos.csv"
# Usamos el link raw que me pasaste
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/pedidos.csv"

st.markdown("### 📦 Gestión de Pedidos - Nexion Core")

# 1. Función para cargar datos
@st.cache_data(ttl=60)  # Se actualiza cada minuto o al presionar "Actualizar"
def load_matrix():
    try:
        df = pd.read_csv(CSV_URL)
        # Filtramos solo las columnas que necesitas
        columnas_base = ["NO CLIENTE", "FACTURA", "NOMBRE DEL CLIENTE", "DESTINO", "FECHA DE ENVÍO"]
        
        # Si el archivo tiene más columnas, solo nos quedamos con las tuyas
        # Si falta alguna, la crea vacía para no romper el renderizado
        for col in columnas_base:
            if col not in df.columns:
                df[col] = ""
        
        # Inyectamos la columna de ESTATUS si no existe
        if "ESTATUS" not in df.columns:
            df["ESTATUS"] = "PENDIENTE"
            
        return df[columnas_base + ["ESTATUS"]]
    except Exception as e:
        st.error(f"Error al conectar con el nodo de datos: {e}")
        return pd.DataFrame()

# Botón de Actualizar (limpia caché y recarga)
if st.button("🔄 ACTUALIZAR MATRIZ"):
    st.cache_data.clear()
    st.rerun()

# 2. Renderizado Editable
df_pedidos = load_matrix()

if not df_pedidos.empty:
    # El data_editor permite que el usuario edite el campo ESTATUS o cualquier otro
    edited_df = st.data_editor(
        df_pedidos,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ESTATUS": st.column_config.SelectboxColumn(
                "ESTATUS",
                help="Estado actual del pedido",
                options=["PENDIENTE", "EN RUTA", "ENTREGADO", "CANCELADO"],
                required=True,
            )
        }
    )

    # 3. Botón de Guardar en GitHub
    if st.button("💾 GUARDAR CAMBIOS EN GITHUB", type="primary"):
        if TOKEN:
            try:
                g = Github(TOKEN)
                repo = g.get_repo(REPO_NAME)
                
                # Convertimos el DataFrame editado a CSV string
                csv_buffer = io.StringIO()
                edited_df.to_csv(csv_buffer, index=False)
                content_to_save = csv_buffer.getvalue()
                
                # Obtener el archivo actual para el SHA (necesario para update)
                contents = repo.get_contents(FILE_PATH)
                
                repo.update_file(
                    path=FILE_PATH,
                    message=f"UPDATE // Pedidos Status Sync ({pd.Timestamp.now().strftime('%H:%M')})",
                    content=content_to_save,
                    sha=contents.sha
                )
                
                st.success("Sincronización Global Exitosa.")
                st.balloons()
                st.cache_data.clear() # Limpiar para la próxima carga
            except Exception as e:
                st.error(f"Fallo en el Uplink: {e}")
        else:
            st.error("Token de seguridad no detectado.")
else:
    st.warning("No se encontraron datos en pedidos.csv o el archivo está vacío.")






















































































































































