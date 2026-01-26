import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

# ── 1. CONFIGURACIÓN DE PÁGINA ─────────────────────────
st.set_page_config(
    page_title="NEXION | Formatos",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── 2. TEMA DINÁMICO ──────────────────────────────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema
vars_css = {
    "bg": "#05070A" if tema == "oscuro" else "#E9ECF1",
    "card": "#0D1117" if tema == "oscuro" else "#FFFFFF",
    "text": "#F0F6FC" if tema == "oscuro" else "#111111",
    "sub": "#8B949E" if tema == "oscuro" else "#2D3136",
    "border": "#1B1F24" if tema == "oscuro" else "#C9D1D9"
}

# ── 3. CSS MAESTRO ────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"] {{
    display: none !important;
}}

.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 0rem !important;
}}

.stApp {{
    background: {vars_css["bg"]} !important;
    color: {vars_css["text"]} !important;
    font-family: 'Inter', sans-serif !important;
}}

.print-btn {{
    width: 100%;
    height: 48px;
    background-color: transparent;
    color: {vars_css["text"]};
    border: 1px solid {vars_css["border"]};
    border-radius: 4px;
    cursor: pointer;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-top: 20px;
}}

@media print {{
    .no-print, button, .stButton {{
        display: none !important;
    }}
    .stApp {{
        background-color: white !important;
        color: black !important;
    }}
    .block-container {{
        padding: 0 !important;
    }}
    hr {{ border-top: 1px solid #000 !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ── 4. HEADER ─────────────────────────────────────────
c1, c2, c3 = st.columns([1.5, 4, .5])
with c1:
    logo = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo, width=140)
        st.markdown(
            f"<p style='font-size:9px;color:{vars_css['sub']};letter-spacing:1px;'>Core Intelligence</p>",
            unsafe_allow_html=True
        )
    except:
        st.markdown("<h2>NEXION</h2>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        with cols[i]:
            if st.button(b, use_container_width=True):
                if b != "FORMATOS":
                    st.switch_page("dashboard.py")

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {vars_css['border']};'>", unsafe_allow_html=True)

# ── 5. INVENTARIO ─────────────────────────────────────
@st.cache_data
def get_inventory():
    for r in ["inventario.csv", "../inventario.csv"]:
        try:
            df = pd.read_csv(r, sep=None, engine="python")
            df.columns = df.columns.str.strip().str.upper()
            return df
        except:
            pass
    return pd.DataFrame(columns=["CODIGO", "DESCRIPCION"])

df_inv = get_inventory()

# ── 6. FORMATO PRINCIPAL ───────────────────────────────
st.markdown(
    f"<p style='text-align:center;color:{vars_css['sub']};letter-spacing:3px;font-size:11px;'>ENTREGA DE MATERIALES PT</p>",
    unsafe_allow_html=True
)

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    c1.date_input("FECHA", value=datetime.now(), key="f_pt_val")
    c2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_pt_val")
    c3.text_input("FOLIO", value="F-2026-001", key="fol_pt_val")

# ── 7. DATAFRAME EN SESSION ───────────────────────────
if "df_final" not in st.session_state:
    st.session_state.df_final = pd.DataFrame(columns=["CODIGO", "DESCRIPCION", "CANTIDAD"])

# ── 7.1. INICIALIZAR NUEVOS INPUTS DE FORMA SEGURA ─────
if "new_codigo" not in st.session_state:
    st.session_state.new_codigo = ""

if "new_cant" not in st.session_state:
    st.session_state.new_cant = 1

# ── 8. FORMULARIO NUEVA FILA ──────────────────────────
with st.expander("➕ Nuevo Registro de Actividad", expanded=True):
    new_codigo = st.text_input("Código / Parte", key="new_codigo")  # no value=
    cantidad = st.number_input("Cantidad", min_value=1, step=1, key="new_cant")  # quitar value=
    if st.button("Añadir y Sincronizar"):
        if new_codigo.strip() != "":
            cod_upper = new_codigo.strip().upper()
            desc = ""
            match = df_inv[df_inv["CODIGO"].astype(str).str.strip().str.upper() == cod_upper]
            if not match.empty:
                desc = match.iloc[0]["DESCRIPCION"]

            new_row = {"CODIGO": cod_upper, "DESCRIPCION": desc, "CANTIDAD": cantidad}
            st.session_state.df_final = pd.concat([st.session_state.df_final, pd.DataFrame([new_row])], ignore_index=True)
            # limpiar input de forma segura
            st.session_state.new_codigo = ""
            st.session_state.new_cant = 1
            st.experimental_rerun()
# ── 9. DATA EDITOR ────────────────────────────────────
edited_df = st.data_editor(
    st.session_state.df_final,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    column_config={
        "CODIGO": st.column_config.TextColumn("CÓDIGO / PARTE"),
        "DESCRIPCION": st.column_config.TextColumn("DESCRIPCIÓN"),
        "CANTIDAD": st.column_config.NumberColumn("CANTIDAD")
    },
    key="editor_nexion"
)

# ── 10. FIRMAS ────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
linea = f"border-top:1px solid {vars_css['sub']};width:80%;margin:auto;"

for col, titulo, nombre in [
    (f1, "ENTREGÓ", "Analista de Inventario"),
    (f2, "AUTORIZÓ", "Carlos Fialko / Dir. Operaciones"),
    (f3, "RECIBIÓ", "Jesus Moreno / Aux. Logística")
]:
    with col:
        st.markdown(
            f"<hr style='{linea}'><p style='text-align:center;font-size:10px;'>{titulo}<br><b>{nombre}</b></p>",
            unsafe_allow_html=True
        )

# ── 11. BOTÓN IMPRIMIR / GENERAR PDF ──────────────────
components.html(
    """
    <button class="print-btn" onclick="window.print()">
        🖨️ GENERAR PDF / IMPRIMIR
    </button>
    """,
    height=90,
)





















