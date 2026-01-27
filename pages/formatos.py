# ── 3. CSS MAESTRO (UNIFICACIÓN DE COLORES E INPUTS) ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

:root {{
  --bg: {v["bg"]}; 
  --card: {v["card"]};
  --text: {v["text"]}; 
  --sub: {v["sub"]};
  --border: {v["border"]}; 
  --btnp-bg: {v["text"]}; 
  --btnp-txt: {v["bg"]};
}}

/* OCULTAR ELEMENTOS NATIVOS */
header, footer, #MainMenu, [data-testid="stHeader"], [data-testid="stDecoration"] {{ 
    display:none !important; 
}}

.block-container {{ padding-top: 1.5rem !important; }}

.stApp {{ 
    background: var(--bg) !important; 
    color: var(--text) !important; 
    font-family: 'Inter', sans-serif !important; 
}}

/* VISIBILIDAD DE LABELS */
[data-testid="stWidgetLabel"] p {{
    color: var(--text) !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
}}

/* UNIFICACIÓN DE TODOS LOS INPUTS (FECHA, SELECT, TEXTO) */
/* Esto asegura que se vean parejos en tema claro */
div[data-testid="stdate_input"] > div > div,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] > div > div,
.stTextInput input, .stSelectbox div[role="button"] {{
    background-color: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    height: 42px !important;
}}

/* BOTONES CON HOVER INVERTIDO */
div.stButton>button {{
    background: var(--card) !important; 
    color: var(--text) !important;
    border: 1px solid var(--border) !important; 
    border-radius: 2px !important;
    font-size: 11px !important; 
    font-weight: 700 !important; 
    letter-spacing: 2px !important; 
    text-transform: uppercase;
    width: 100%;
    transition: all .3s ease;
}}

div.stButton>button:hover {{
    background: var(--text) !important;
    color: var(--bg) !important;
    border-color: var(--text) !important;
}}

/* BOTÓN PRIMARIO */
div.stButton>button[kind="primary"] {{
    background: var(--btnp-bg) !important;
    color: var(--btnp-txt) !important;
    border: none !important;
    font-weight: 800 !important;
    height: 48px !important;
}}
</style>
""", unsafe_allow_html=True)
# ── 4. HEADER Y NAVEGACIÓN (Título Visual Actualizado) ───
c1, c2, c3 = st.columns([2, 3.5, .5], vertical_alignment="top")
with c1:
    logo = "n1.png" if tema == "oscuro" else "n2.png"
    try:
        st.image(logo, width=140)
        # Actualización de subtítulo visual
        st.markdown(f"<div style='margin-top:-15px;'><p style='font-size:9px; color:{v['sub']}; letter-spacing:1px; text-transform:uppercase;'>Automatización de Procesos</p></div>", unsafe_allow_html=True)
    except: 
        st.markdown(f"<h2 style='color:{v['text']}; margin:0;'>NEXION</h2>", unsafe_allow_html=True)

with c2:
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        if cols[i].button(b, key=f"nav_{b}", use_container_width=True):
            if b != "FORMATOS": st.switch_page("dashboard.py")
            else: st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="t_btn"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"; st.rerun()

st.markdown(f"<hr style='border-top:1px solid {v['border']}; margin:5px 0 15px;'>", unsafe_allow_html=True)

# ── 5. CARGA DE INVENTARIO (RAÍZ) ──────────────────────
@st.cache_data
def load_inventory():
    ruta = os.path.join(os.getcwd(), "inventario.csv")
    if not os.path.exists(ruta): ruta = os.path.join(os.getcwd(), "..", "inventario.csv")
    try:
        df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip().upper() for c in df.columns] # CODIGO, DESCRIPCION
        return df
    except: return pd.DataFrame(columns=['CODIGO', 'DESCRIPCION'])

df_inv = load_inventory()

# ── 6. CUERPO DE ENTRADA (WEB) ────────────────────────
with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    f_val = h1.date_input("FECHA", value=datetime.now(), key="f_in")
    t_val = h2.selectbox("TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_in")
    fol_val = h3.text_input("FOLIO", value="F-2026-001", key="fol_in")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}] * 10)

def lookup():
    edits = st.session_state["editor_pt"].get("edited_rows", {})
    for idx_str, info in edits.items():
        idx = int(idx_str)
        if "CODIGO" in info:
            val = str(info["CODIGO"]).strip().upper()
            if not df_inv.empty:
                match = df_inv[df_inv['CODIGO'].astype(str).str.strip().str.upper() == val]
                if not match.empty:
                    st.session_state.rows.at[idx, "DESCRIPCION"] = match.iloc[0]['DESCRIPCION']
                    st.session_state.rows.at[idx, "CODIGO"] = val

df_final = st.data_editor(st.session_state.rows, num_rows="dynamic", use_container_width=True, key="editor_pt", on_change=lookup)

# ── 7. RENDERIZADO PRO (HTML PARA IMPRESIÓN) ───────────
filas_print = df_final[df_final["CODIGO"] != ""]
tabla_html = "".join([f"<tr><td style='border:1px solid black;padding:8px;'>{r['CODIGO']}</td><td style='border:1px solid black;padding:8px;'>{r['DESCRIPCION']}</td><td style='border:1px solid black;padding:8px;text-align:center;'>{r['CANTIDAD']}</td></tr>" for _, r in filas_print.iterrows()])

form_html = f"""
<div style="font-family:sans-serif; padding:20px; color:black; background:white;">
    <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:10px;">
        <div>
            <h2 style="margin:0; letter-spacing:2px;">NEXION LOGISTICS</h2>
            <p style="margin:0; font-size:10px; letter-spacing:1px;">AUTOMATIZACIÓN DE PROCESOS</p>
        </div>
        <div style="text-align:right; font-size:12px;">
            <p style="margin:0;"><b>FOLIO:</b> {fol_val}</p>
            <p style="margin:0;"><b>FECHA:</b> {f_val}</p>
            <p style="margin:0;"><b>TURNO:</b> {t_val}</p>
        </div>
    </div>
    <h3 style="text-align:center; letter-spacing:5px; margin-top:30px; text-decoration:underline;">ENTREGA DE MATERIALES PT</h3>
    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
        <thead><tr style="background:#f2f2f2;">
            <th style="border:1px solid black;padding:10px;">CÓDIGO</th>
            <th style="border:1px solid black;padding:10px;">DESCRIPCIÓN</th>
            <th style="border:1px solid black;padding:10px;text-align:center;">CANTIDAD</th>
        </tr></thead>
        <tbody>{tabla_html}</tbody>
    </table>
    <div style="margin-top:80px; display:flex; justify-content:space-around; text-align:center; font-size:10px;">
        <div style="width:30%; border-top:1px solid black;">ENTREGÓ<br><b>Analista de Inventario</b></div>
        <div style="width:30%; border-top:1px solid black;">AUTORIZACIÓN<br><b>Carlos Fialko / Dir. Operaciones</b></div>
        <div style="width:30%; border-top:1px solid black;">RECIBIÓ<br><b>Jesus Moreno / Aux. Logística</b></div>
    </div>
</div>
"""

# ── 8. BOTÓN DE ACCIÓN FINAL ───────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🖨️ GENERAR FORMATO PROFESIONAL (PDF)", type="primary", use_container_width=True):
    components.html(f"{form_html}<script>window.onload = function() {{ window.print(); }}</script>", height=0)
    st.toast("Renderizando Automatización de Procesos...", icon="⚙️")
















































