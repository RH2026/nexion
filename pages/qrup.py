import streamlit as st

st.set_page_config(page_title="Prueba Láser", layout="centered")

st.markdown("### 🔍 TEST DE LECTOR LÁSER INDUSTRIAL")
st.markdown("Apunta con el láser a cualquier código (o escríbelo manualmente) y presiona **Enter**.")

# Inicializar historial de pruebas en memoria si no existe
if "historial_pruebas" not in st.session_state:
    st.session_state.historial_pruebas = []

# Función que se ejecuta automáticamente al presionar Enter con el láser o teclado
def procesar_lectura():
    texto_leido = st.session_state.get("input_test", "").strip()
    if texto_leido:
        # Agregamos la prueba al historial
        st.session_state.historial_pruebas.insert(0, texto_leido)
        # Limpiamos la caja de texto para dejarla lista para el siguiente disparo
        st.session_state["input_test"] = ""

# Input configurado con on_change para atrapar el Enter del láser de inmediato
st.text_input(
    "Dispara con el láser aquí:",
    placeholder="Esperando lectura del escáner...",
    key="input_test",
    on_change=procesar_lectura
)

# Botón por si acaso se quiere simular manual
if st.button("PROBAR MANUAL"):
    procesar_lectura()

st.markdown("---")
st.markdown(f"**Total leídos en esta prueba:** {len(st.session_state.historial_pruebas)}")

# Mostrar la lista de lo que la pistola va leyendo
if st.session_state.historial_pruebas:
    st.markdown("#### 📋 Últimas lecturas capturadas:")
    for i, item in enumerate(st.session_state.historial_pruebas[:10]):
        st.code(f"Lectura #{len(st.session_state.historial_pruebas) - i}: {item}")

if st.button("🗑️ Limpiar Historial"):
    st.session_state.historial_pruebas = []
    st.rerun()
