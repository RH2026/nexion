from datetime import datetime
import os
import pytz
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Salida de PT",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO
# ============================================================
render_layout(modulo_actual="FORMATOS", submodulo_actual="SALIDA DE PT")

# ============================================================
# 3. LÓGICA DE NEGOCIO Y DATOS
# ============================================================

# ── A. GENERACIÓN DE FOLIO CON HORA DE GUADALAJARA ──
if 'folio_nexion' not in st.session_state:
    tz_gdl = pytz.timezone('America/Mexico_City') 
    now_gdl = datetime.now(tz_gdl)
    st.session_state.folio_nexion = f"F-{now_gdl.strftime('%Y%m%d-%H%M')}"

# ── B. CARGA DE INVENTARIO ──────────────────────
@st.cache_data
def load_inventory():
    ruta = os.path.join(os.getcwd(), "inventario.csv")
    if not os.path.exists(ruta): 
        ruta = os.path.join(os.getcwd(), "..", "inventario.csv")
    try:
        df = pd.read_csv(ruta, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except: 
        return pd.DataFrame(columns=['CODIGO', 'DESCRIPCION'])

df_inv = load_inventory()

# ── C. INICIALIZACIÓN DE FILAS (CANTIDAD siempre como número) ──
if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame([
        {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0} 
    ] * 10)

# Aseguramos que CANTIDAD sea numérica para que el editor no se trabe
st.session_state.rows["CANTIDAD"] = pd.to_numeric(st.session_state.rows["CANTIDAD"], errors='coerce').fillna(0).astype(int)

# ── D. CUERPO DE ENTRADA (ESTRUCTURA CON ICONOS) ────────────────
with st.container(border=True):
    h1, h2, h3 = st.columns(3)
    f_val = h1.date_input(":material/calendar_month: FECHA", value=datetime.now(), key="f_in_pt")
    t_val = h2.selectbox(":material/schedule: TURNO", ["MATUTINO", "VESPERTINO", "NOCTURNO", "MIXTO"], key="t_in_pt")
    fol_val = h3.text_input(":material/fingerprint: FOLIO", value=st.session_state.folio_nexion, key="fol_in_pt")

# ── E. BÚSQUEDA AUXILIAR ──────────────────────────
with st.expander(":material/search: Buscar Codigo", expanded=False):
    busqueda = st.text_input("Escribe el nombre del producto o código:").strip().upper()
    if busqueda:
        resultados = df_inv[
            df_inv['CODIGO'].astype(str).str.contains(busqueda, na=False) | 
            df_inv['DESCRIPCION'].astype(str).str.upper().str.contains(busqueda, na=False)
        ]
        if not resultados.empty:
            st.dataframe(resultados, use_container_width=True, hide_index=True)
        else:
            st.warning("No se encontraron coincidencias en el inventario.")

# ── F. MOTOR DE BÚSQUEDA INTERNO (LOOKUP CORREGIDO) ──────────────────────────
def lookup_pt():
    # Obtenemos los cambios del estado del editor
    edits = st.session_state["editor_pt"].get("edited_rows", {})
    added = st.session_state["editor_pt"].get("added_rows", [])
    
    # 1. Filas nuevas
    for row in added:
        new_row = {"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}
        new_row.update(row)
        st.session_state.rows = pd.concat([st.session_state.rows, pd.DataFrame([new_row])], ignore_index=True)
    
    # 2. Ediciones (La clave: Actualizar solo lo necesario para no interrumpir el tipeo)
    for idx_str, info in edits.items():
        idx = int(idx_str)
        for col, val in info.items():
            st.session_state.rows.at[idx, col] = val
            
            # Solo buscamos descripción si lo que cambió fue el CÓDIGO
            if col == "CODIGO" and val:
                val_codigo = str(val).strip().upper()
                if not df_inv.empty:
                    match = df_inv[df_inv['CODIGO'].astype(str).str.strip().str.upper() == val_codigo]
                    if not match.empty:
                        st.session_state.rows.at[idx, "DESCRIPCION"] = match.iloc[0]['DESCRIPCION']
                        st.session_state.rows.at[idx, "CODIGO"] = val_codigo
                    else:
                        st.session_state.rows.at[idx, "DESCRIPCION"] = "⚠️ NO ENCONTRADO"

# ── G. EDITOR DE DATOS DINÁMICO ────────────────────────────────────
st.markdown("<p style='font-size:12px; font-weight:normal; color:#FFFFFF; letter-spacing:2px; margin-bottom:10px;'>EDICIÓN SOLICITUD DE MATERIALES</p>", unsafe_allow_html=True)

df_final_pt = st.data_editor(
    st.session_state.rows, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="editor_pt", 
    on_change=lookup_pt,
    column_config={
        "CODIGO": st.column_config.TextColumn("CÓDIGO", help="Escribe el código", validate=r"^[a-zA-Z0-9_-]+$"),
        "DESCRIPCION": st.column_config.TextColumn("DESCRIPCIÓN DEL PRODUCTO", width="large", disabled=True),
        "CANTIDAD": st.column_config.NumberColumn("CANT.", min_value=0, step=1, format="%d", width="small", required=True),
        "DISPONIBILIDAD": st.column_config.CheckboxColumn("✅ LISTO", default=False)
    }
)

# ── H. ESTILOS Y SECCIÓN FINAL ────────────────────────────────────
st.markdown("""
    <style>
    [data-testid="stDataEditor"] div[role="columnheader"] { background-color: #263238 !important; color: #00FFAA !important; font-weight: bold !important; }
    div[data-testid="stTextArea"] textarea { background-color: #465B66 !important; color: white !important; border-radius: 15px !important; border: 1px solid rgba(0,255,170,0.3) !important; }
    </style>
""", unsafe_allow_html=True)

coment_val = st.text_area("NOTAS DE LOGÍSTICA", placeholder="¿Instrucciones?", key="coment_in_pt")

# --- HTML PARA IMPRESIÓN PT ---
# Importante: Usamos df_final_pt que es el resultado directo del editor
filas_print = df_final_pt[df_final_pt["CODIGO"] != ""]

tabla_html = "".join([
    f"<tr><td style='border:1px solid black;padding:6px; font-size:10px;'>{r['CODIGO']}</td>"
    f"<td style='border:1px solid black;padding:6px; font-size:10px;'>{r['DESCRIPCION']}</td>"
    f"<td style='border:1px solid black;padding:6px;text-align:center; font-size:10px;'>{r['CANTIDAD']}</td></tr>" 
    for _, r in filas_print.iterrows()
])

form_pt_html = f"""
<html>
<head>
    <style>
        @page {{ 
            size: letter; 
            margin: 1cm; 
        }}
        @media print {{
            body {{ margin: 0; padding: 0; }}
            .print-container {{ min-height: 95vh; display: flex; flex-direction: column; }}
        }}
        body {{ 
            font-family: sans-serif; 
            color: black; 
            background: white; 
            margin: 0;
        }}
        .print-container {{
            display: flex;
            flex-direction: column;
            min-height: 95vh;
            width: 100%;
        }}
        .main-content {{
            flex-grow: 1;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 10px; 
        }}
        th {{ 
            background: #eee; 
            border: 1px solid black; 
            padding: 6px; 
            text-align: left; 
            font-size: 11px;
        }}
        .comments-section {{
            margin-top: 15px;
            font-size: 10px;
            border: 1px solid black;
            padding: 8px;
            min-height: 30px;
        }}
        .signature-section {{
            margin-top: 30px;
            display: flex;
            justify-content: space-between;
            text-align: center;
            font-size: 9px;
            padding-bottom: 10px;
        }}
        .sig-box {{
            width: 30%;
            border-top: 1px solid black;
            padding-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="print-container">
        <div class="main-content">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid black; padding-bottom:5px; margin-bottom:15px;">
                <div>
                    <h2 style="margin:0; font-size: 16px; letter-spacing:1px;">Jabones y Productos Especializados</h2>
                    <p style="margin:0; font-size:9px; letter-spacing:1px;">Distribución y Logística | 2026</p>
                </div>
                <div style="text-align:right; font-size:11px;">
                    <b>FOLIO:</b> {fol_val}<br>
                    <b>FECHA:</b> {f_val}
                </div>
            </div>

            <h3 style="text-align:center; font-size: 14px; letter-spacing:1px; margin: 10px 0;">ENTREGA DE MATERIALES PT</h3>
            <p style="font-size:11px;"><b>TURNO:</b> {t_val}</p>
            
            <table>
                <thead>
                    <tr><th>CÓDIGO</th><th>DESCRIPCIÓN</th><th>CANTIDAD</th></tr>
                </thead>
                <tbody>
                    {tabla_html}
                </tbody>
            </table>

            <div class="comments-section">
                <b>COMENTARIOS:</b> {coment_val}
            </div>
        </div>

        <div class="signature-section">
            <div class="sig-box">
                <b>ENTREGÓ</b><br>
                Analista de Inventario
            </div>
            <div class="sig-box">
                <b>AUTORIZACIÓN</b><br>
                Carlos Fialko / Dir. Operaciones
            </div>
            <div class="sig-box">
                <b>RECIBIÓ</b><br>
                Rigoberto Hernandez / Cord. Logística
            </div>
        </div>
    </div>
</body>
</html>
"""

st.markdown("<br>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    if st.button(":material/picture_as_pdf: IMPRIMIR SALIDA PT", type="primary", use_container_width=True):
        components.html(f"<html><body>{form_pt_html}<script>window.print();</script></body></html>", height=0)
with c2:
    if st.button(":material/refresh: BORRAR", use_container_width=True):
        if 'folio_nexion' in st.session_state: del st.session_state.folio_nexion
        st.session_state.rows = pd.DataFrame([{"CODIGO": "", "DESCRIPCION": "", "CANTIDAD": 0}] * 10)
        st.rerun()
