import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="NEXION | Core", layout="wide", initial_sidebar_state="collapsed")


# ── TEMA ACTUALIZADO (GRIS HUMO + TEXTO ALTO CONTRASTE) ────────
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

tema = st.session_state.tema

if tema == "oscuro":
    vars_css = {
        "bg": "#05070A", "card": "#0D1117",
        "text": "#F0F6FC", "sub": "#8B949E",
        "border": "#1B1F24", "hover": "#161B22",
        "btn_primary_bg": "#F0F6FC", "btn_primary_txt": "#05070A"
    }
else:
    vars_css = {
        "bg": "#E9ECF1", 
        "card": "#FFFFFF",
        "text": "#111111", # <--- NEGRO MÁS PROFUNDO PARA MÁXIMA LEGIBILIDAD
        "sub": "#2D3136",  # <--- SUBTEXTO MÁS OSCURO (GRAFITO)
        "border": "#C9D1D9", 
        "hover": "#EBEEF2",
        "btn_primary_bg": "#000000",
        "btn_primary_txt": "#FFFFFF"
    }

# ── ALIAS DE COMPATIBILIDAD
bg_color      = vars_css["bg"]
card_bg      = vars_css["card"]
text_main    = vars_css["text"]
text_sub     = vars_css["sub"]
border_color = vars_css["border"]
btn_hover    = vars_css["hover"]
btn_primary_bg  = vars_css["btn_primary_bg"]
btn_primary_txt = vars_css["btn_primary_txt"]


# ── CSS MAESTRO ──────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

:root {{
  --bg:{bg_color}; --card:{card_bg};
  --text:{text_main}; --sub:{text_sub};
  --border:{border_color}; --hover:{btn_hover};
  --btnp-bg:{btn_primary_bg};
  --btnp-txt:{btn_primary_txt};
}}

* {{
  transition: background-color .35s ease, color .35s ease, border-color .35s ease;
}}

header, footer, #MainMenu, div[data-testid="stDecoration"],
[data-testid="stStatusWidget"], .viewerBadge_container__1QSob {{
  display:none !important;
}}

.main .block-container {{ padding-bottom:0 !important; }}

.stApp {{
  background:var(--bg) !important;
  color:var(--text) !important;
  font-family:'Inter',sans-serif !important;
}}

/* BOTONES Y SELECTORES */
div.stButton>button,
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div {{
  background:var(--card) !important;
  color:var(--text) !important;
  border:1px solid var(--border) !important;
  border-radius:2px !important;
  font-size:11px !important;
  font-weight:700 !important; /* <--- UN POCO MÁS DE PESO PARA LEER MEJOR */
  letter-spacing:2px !important;
  text-transform:uppercase;
}}

div.stButton>button:hover {{
  background:var(--hover) !important;
  border-color:var(--text) !important;
}}

div.stButton>button[kind="primary"] {{
  background:var(--btnp-bg) !important;
  color:var(--btnp-txt) !important;
  border:none !important;
  font-weight:800 !important;
  height:48px !important;
}}

.stTextInput input {{
  background:var(--card) !important;
  color:var(--text) !important;
  border:1px solid var(--border) !important;
  border-radius:2px !important;
  height:48px !important;
}}

div[data-testid="stSelectbox"] label p {{
  font-size:10px !important;
  color:var(--text) !important; /* <--- USAMOS EL TEXTO PRINCIPAL PARA LOS LABELS */
  font-weight: 800 !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
}}
</style>
""", unsafe_allow_html=True)

# ── SPLASH ───────────────────────────────────────────
if "splash_completado" not in st.session_state:
    st.session_state.splash_completado = False

if not st.session_state.splash_completado:
    p = st.empty()
    with p.container():
        for m in ["ESTABLISHING SECURE ACCESS","PARSING LOGISTICS DATA","SYSTEM READY"]:
            st.markdown(f"""
            <div style="height:80vh;display:flex;flex-direction:column;justify-content:center;align-items:center;">
              <div style="width:40px;height:40px;border:1px solid var(--border);
              border-top:1px solid var(--text);border-radius:50%;animation:spin 1s linear infinite;"></div>
              <p style="margin-top:40px;font-family:monospace;font-size:10px;letter-spacing:5px;color:var(--text);">{m}</p>
            </div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
            """, unsafe_allow_html=True)
            time.sleep(.9)
    st.session_state.splash_completado = True
    st.rerun()

# ── HEADER ───────────────────────────────────────────
c1,c2,c3 = st.columns([1.5,4,.5])
with c1:
    st.markdown("<h2 style='letter-spacing:4px;font-weight:300;margin:0;'>NEXION</h2>"
                "<p style='font-size:9px;margin-top:-5px;letter-spacing:1px;color:var(--sub);'>CORE INTELLIGENCE</p>",
                unsafe_allow_html=True)

# ── 5. HEADER Y NAVEGACIÓN PRINCIPAL ───────────────────────
c1, c2, c3 = st.columns([1.5, 4, .5])
with c1:
    st.markdown(f"<h2 style='letter-spacing:4px;font-weight:300;margin:0;color:{text_main};'>NEXION</h2>"
                f"<p style='font-size:9px;margin-top:-5px;letter-spacing:1px;color:{text_sub};'>CORE INTELLIGENCE</p>",
                unsafe_allow_html=True)

with c2:
    if "pagina" not in st.session_state: 
        st.session_state.pagina = "RASTREO"
    
    # Menú Principal
    cols = st.columns(4)
    for i, b in enumerate(["RASTREO", "INTELIGENCIA", "REPORTES", "FORMATOS"]):
        with cols[i]:
            # Resaltamos el botón si la página está activa
            if st.button(b, use_container_width=True, key=f"main_nav_{b}"):
                st.session_state.pagina = b
                st.rerun()

with c3:
    if st.button("☀️" if tema == "oscuro" else "🌙", key="theme_toggle"):
        st.session_state.tema = "claro" if tema == "oscuro" else "oscuro"
        st.rerun()

st.markdown(f"<hr style='border-top:1px solid {border_color};margin:10px 0 20px;'>", unsafe_allow_html=True)

# ── 6. LÓGICA DE SUBMENÚS (ESCALABLE) ──────────────────────
# Aquí definimos qué submenús tiene cada sección
submenus = {
    "FORMATOS": ["SELECCIONE...", "SALIDA PT", "ENTRADA MP", "INVENTARIOS"],
    "REPORTES": ["SELECCIONE...", "KPI SEMANAL", "REPORTE MENSUAL"]
}

# Si la página actual tiene submenús, los mostramos
if st.session_state.pagina in submenus:
    st.markdown("<div style='margin-bottom: -10px;'></div>", unsafe_allow_html=True)
    _, col_sub, _ = st.columns([1, 1.5, 1])
    
    with col_sub:
        st.markdown(f"<p style='text-align: center; color: {text_sub}; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px;'>Submenú {st.session_state.pagina}</p>", unsafe_allow_html=True)
        
        # Selectbox que actúa como disparador de páginas
        seleccion = st.selectbox(
            "",
            options=submenus[st.session_state.pagina],
            label_visibility="collapsed",
            key=f"sub_{st.session_state.pagina}"
        )

        # Lógica de redirección específica
        if seleccion == "SALIDA PT":
            st.toast("Redirigiendo a Formatos...", icon="📄")
            time.sleep(0.5)
            st.switch_page("formatos.py") # Asegúrate de que formatos.py esté en la raíz o en /pages

if st.session_state.pagina == "FORMATOS":
    st.markdown("<div style='margin-top: 15vh;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align: center;'>
            <p style='color: {text_sub}; font-size: 12px; letter-spacing: 4px; text-transform: uppercase;'>
                Módulo de Formatos Operativos
            </p>
            <p style='color: {text_main}; font-size: 10px; opacity: 0.6;'>
                Seleccione el documento requerido en el menú superior para continuar.
            </p>
        </div>
    """, unsafe_allow_html=True)


# 5. DATOS
@st.cache_data
def cargar_datos():
    df = pd.DataFrame()  # <-- GARANTÍA DE EXISTENCIA

    try:
        df = pd.read_csv("Matriz_Excel_Dashboard.csv", encoding="utf-8")
        df.columns = df.columns.str.strip().str.upper()

        if "NO CLIENTE" in df.columns:
            df["NO CLIENTE"] = df["NO CLIENTE"].astype(str).str.strip()

        # Normalizar fechas SOLO si existen
        for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA", "FECHA DE ENTREGA REAL"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

        hoy = pd.Timestamp.today().normalize()

        # Columna siempre creada
        df["ESTATUS_CALCULADO"] = "EN TRANSITO"

        if "FECHA DE ENTREGA REAL" in df.columns:
            df.loc[df["FECHA DE ENTREGA REAL"].notna(), "ESTATUS_CALCULADO"] = "ENTREGADO"

        if "PROMESA DE ENTREGA" in df.columns:
            df.loc[
                df["FECHA DE ENTREGA REAL"].isna()
                & df["PROMESA DE ENTREGA"].notna()
                & (df["PROMESA DE ENTREGA"] < hoy),
                "ESTATUS_CALCULADO"
            ] = "RETRASADO"

        return df

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return df

df = cargar_datos()

# 6. FUNCIÓN DE TABLA DINÁMICA (CLAVE)
def tabla_estilizada(df):
    return (
        df.style
        .set_properties(**{
            "background-color": card_bg,
            "color": text_sub,
            "border": f"1px solid {border_color}",
            "font-size": "11px"
        })
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", card_bg),
                    ("color", text_main),
                    ("border", f"1px solid {border_color}"),
                    ("font-size", "11px"),
                    ("text-transform", "uppercase"),
                    ("letter-spacing", "2px")
                ]
            }
        ])
        .hide(axis="index")
    )

# 7. RENDERIZADO RASTREO (CAJA DE BÚSQUEDA DHL)
if st.session_state.pagina == "RASTREO":
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    
    # --- CAJA DE BÚSQUEDA CENTRALIZADA ---
    _, col_search, _ = st.columns([1, 1.8, 1])
    with col_search:
        st.markdown(f"<p style='text-align: center; color: {text_sub}; font-size: 11px; letter-spacing: 3px; text-transform: uppercase;'>Operational Query</p>", unsafe_allow_html=True)
        busqueda = st.text_input("", placeholder="REFERENCIA O NÚMERO DE GUÍA...", label_visibility="collapsed")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        btn_search = st.button("EXECUTE SYSTEM SEARCH", type="primary", use_container_width=True)

    st.markdown("<div style='margin-bottom: 60px;'></div>", unsafe_allow_html=True)


# 7. RENDER
if st.session_state.get("pagina", "RASTREO") == "RASTREO":

    f1, f2, f3, f4 = st.columns(4)
    df_visual = df.copy().reset_index(drop=True)

    # FILTROS
    with f1:
        f_cli = st.selectbox(
            "Client ID",
            ["ALL"] + sorted(df_visual["NO CLIENTE"].dropna().unique())
        )
    with f2:
        f_car = st.selectbox(
            "Carrier",
            ["ALL"] + sorted(df_visual["FLETERA"].dropna().unique())
        )
    with f3:
        f_des = st.selectbox(
            "Destination",
            ["ALL"] + sorted(df_visual["DESTINO"].dropna().unique())
        )
    with f4:
        f_est = st.selectbox(
            "Status",
            ["ALL"] + sorted(df_visual["ESTATUS_CALCULADO"].dropna().unique())
        )

    if f_cli != "ALL":
        df_visual = df_visual[df_visual["NO CLIENTE"] == f_cli]
    if f_car != "ALL":
        df_visual = df_visual[df_visual["FLETERA"] == f_car]
    if f_des != "ALL":
        df_visual = df_visual[df_visual["DESTINO"] == f_des]
    if f_est != "ALL":
        df_visual = df_visual[df_visual["ESTATUS_CALCULADO"] == f_est]

    # COLUMNAS A MOSTRAR
    COLUMNAS_VISTA = [
        "NO CLIENTE",
        "NÚMERO DE PEDIDO",
        "NOMBRE DEL CLIENTE",
        "DESTINO",
        "FECHA DE ENVÍO",
        "PROMESA DE ENTREGA",
        "FLETERA",
        "NÚMERO DE GUÍA",
        "ESTATUS_CALCULADO"
    ]

    df_visual = df_visual.reset_index(drop=True)

    # FORMATO FECHAS (SOLO FECHA, SIN HORA)
    for col in ["FECHA DE ENVÍO", "PROMESA DE ENTREGA"]:
        df_visual[col] = (
            pd.to_datetime(df_visual[col], errors="coerce")
            .dt.strftime("%d/%m/%Y")
        )

    components.html(
    f"""
    <div style="
        width:100%;
        height:600px;
        display:flex;
        flex-direction:column;
    ">
        <div style="flex:0 0 auto;">
            {tabla_estilizada(df_visual[COLUMNAS_VISTA]).to_html()}
        </div>

        <!-- ESPACIADOR INVISIBLE -->
        <div style="flex:1 1 auto;"></div>
    </div>
    """,
    height=600,
    scrolling=True
)
    


























































































































































































































































































































































































