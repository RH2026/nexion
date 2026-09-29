import html as html_lib
import re
import time
from datetime import date, datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from auth import exigir_autenticacion

from components.layout import render_layout
from muestras_common import (
    precios,
    obtener_datos_github,
    subir_a_github,
    generar_etiquetas_limpias,
    generar_html_impresion,
)

# ============================================================
# 0. CONSTANTES Y FUNCIONES DE APOYO
# ============================================================
# Usuarios que pueden autorizar envíos de muestras (en minúsculas)
AUTORIZADORES = ["rigoberto", "arodriguez"]


def obtener_usuario_actual():
    """Regresa el usuario logueado en minúsculas.
    log.py lo guarda en st.session_state.usuario_activo."""
    return str(st.session_state.get("usuario_activo", "")).strip().lower()


def limpiar_telefono(texto):
    """Deja solo los dígitos del teléfono."""
    return re.sub(r"\D", "", texto or "")


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Formatos - Envio de Muestras",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Si no hay sesión iniciada, manda al login
exigir_autenticacion("muestras")

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO Y PERMISOS
# ============================================================
render_layout(modulo_actual="FORMATOS", submodulo_actual="ENVIO DE MUESTRAS")

# ============================================================
# 3. ESTADO DE SESIÓN
# ============================================================
if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0
if "folio_guardado" not in st.session_state:
    st.session_state.folio_guardado = False
if "seleccionados_muestras" not in st.session_state:
    st.session_state.seleccionados_muestras = []


# ==========================================
# 4. INTERFAZ PRINCIPAL (CAPTURA DE MUESTRAS)
# ==========================================
# ============================================================
# 0.1 APOYO PARA TARJETAS (PENDIENTES Y CONSULTA)
# ============================================================
CSS_TARJETAS = """
.jp-card { background:#263238; border:1px solid rgba(255,255,255,0.06); border-left:5px solid var(--acento,#FF4444);
           border-radius:12px; padding:14px 18px; margin-bottom:10px; display:flex; flex-wrap:wrap; gap:14px 18px;
           align-items:flex-start; font-family:'Inter',sans-serif; transition:all .25s ease; }
.jp-card:hover { background:#2d3b42; border-color:rgba(56,189,248,0.6); border-left-color:var(--acento,#FF4444); }
.jp-col { flex:1 1 180px; min-width:160px; }
.jp-col-prod { flex:2 1 260px; }
.jp-col-guia { flex:1 1 170px; text-align:right; }
.jp-lbl { font-size:8px; color:rgba(255,255,255,0.4); font-weight:800; letter-spacing:1px; text-transform:uppercase; margin-bottom:3px; }
.jp-folio { color:var(--acento,#00FFAA); font-family:monospace; font-size:20px; font-weight:900; line-height:1.1; }
.jp-fecha { color:rgba(255,255,255,0.5); font-size:10px; margin:2px 0 6px 0; }
.jp-hotel { color:#FFF; font-size:13px; font-weight:800; line-height:1.25; }
.jp-line { color:rgba(255,255,255,0.6); font-size:10px; margin-top:3px; line-height:1.35; }
.jp-line b { color:#FFD700; font-weight:700; }
.jp-tel { color:#38bdf8; font-weight:700; }
.jp-chips { display:flex; flex-wrap:wrap; gap:5px; }
.jp-chip { background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.1); color:#FFF; border-radius:8px;
           padding:3px 8px; font-size:9.5px; font-weight:600; }
.jp-chip b { color:#00FFAA; margin-right:3px; }
.jp-badge { display:inline-block; border-radius:10px; padding:2px 8px; font-size:8px; font-weight:800; letter-spacing:1px;
            margin:0 4px 4px 0; border:1px solid; }
.jp-ok   { color:#00FFAA; border-color:#00FFAA; background:rgba(0,255,170,0.10); }
.jp-bad  { color:#FF4444; border-color:#FF4444; background:rgba(255,68,68,0.10); }
.jp-wait { color:#f97316; border-color:#f97316; background:rgba(249,115,22,0.12); }
.jp-info { color:#38bdf8; border-color:#38bdf8; background:rgba(56,189,248,0.10); }
.jp-mute { color:rgba(255,255,255,0.45); border-color:rgba(255,255,255,0.2); background:rgba(255,255,255,0.04); }
.jp-guia { color:#38bdf8; font-family:monospace; font-size:14px; font-weight:800; line-height:1.2; }
.jp-guia2 { color:#FFF; font-family:monospace; font-size:12px; font-weight:700; margin-top:4px; }
.jp-pend { color:#f97316 !important; font-style:italic; font-size:10px; font-weight:400; }
.jp-tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin:6px 0 14px 0; }
.jp-tile { background:#263238; border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:10px 14px; }
.jp-tile .n { font-size:24px; font-weight:900; font-family:monospace; line-height:1.1; }
.jp-tile .t { font-size:8px; letter-spacing:1px; font-weight:800; color:rgba(255,255,255,0.45); text-transform:uppercase; }
.jp-banner { background:rgba(249,115,22,0.10); border:1px solid #f97316; color:#f97316; border-radius:10px;
             padding:8px 14px; font-size:11px; font-weight:800; letter-spacing:1px; margin-bottom:10px; }
"""


def limpiar_numero_texto(valor):
    """Convierte guías / teléfonos a texto limpio.
    Quita el '.0' que agrega pandas y expande notación científica (8.75112E+11 -> 875112000000).
    OJO: si el dato ya se guardó como 8.75112E+11, los dígitos perdidos no se pueden recuperar."""
    if valor is None:
        return ""
    s = str(valor).strip()
    if s.lower() in ("", "nan", "none", "0", "0.0"):
        return ""
    if re.fullmatch(r"\d+\.0+", s):
        return s.split(".")[0]
    if re.fullmatch(r"\d+(\.\d+)?[eE]\+?\d+", s):
        try:
            from decimal import Decimal
            return str(int(Decimal(s)))
        except Exception:
            return s
    return s


def _e(valor):
    """Escapa texto para meterlo seguro en HTML."""
    return html_lib.escape(str(valor if valor is not None else ""))


def _tel_visible(valor):
    """Teléfono sin '.0' ni espacios (pandas puede leerlo como número)."""
    return limpiar_numero_texto(valor)


def _chips_productos(item):
    """Regresa (html_chips, total_piezas) con los productos del folio."""
    chips, total = "", 0
    for p_key in precios.keys():
        cant = pd.to_numeric(item.get(p_key, 0), errors="coerce")
        if pd.notna(cant) and cant > 0:
            total += int(cant)
            nombre = str(p_key).upper()
            corto = nombre if len(nombre) <= 34 else nombre[:33] + "…"
            chips += f'<span class="jp-chip" title="{_e(nombre)}"><b>{int(cant)}</b>{_e(corto)}</span>'
    return (chips or '<span class="jp-line"><i>Sin detalle</i></span>'), total


def _contacto_visible(item):
    nombre = str(item.get("CONTACTO_NOMBRE", "") or "").strip()
    tel = _tel_visible(item.get("CONTACTO_TELEFONO", ""))
    if nombre or tel:
        return nombre, tel
    return str(item.get("CONTACTO", "") or "").strip(), ""


def _estado_aut(item):
    v = str(item.get("AUTORIZACION", "") or "").strip().upper()
    return v if v in ("AUTORIZADO", "PENDIENTE") else ""


def _tarjeta_html(item, mostrar_guia=True):
    """Tarjeta de un folio (se usa en pendientes y en consulta)."""
    est = str(item.get("ESTATUS", "") or "NO SURTIDO").strip().upper()
    aut = _estado_aut(item)

    if aut == "PENDIENTE":
        acento = "#f97316"
    elif est == "DESPACHADO":
        acento = "#00FFAA"
    else:
        acento = "#FF4444"

    badge_est = ('<span class="jp-badge jp-ok">✓ DESPACHADO</span>' if est == "DESPACHADO"
                 else '<span class="jp-badge jp-bad">⚠ NO SURTIDO</span>')
    if aut == "AUTORIZADO":
        quien = str(item.get("AUTORIZADO_POR", "") or "").strip().upper()
        badge_aut = f'<span class="jp-badge jp-info">✓ AUTORIZADO{(" · " + _e(quien)) if quien else ""}</span>'
    elif aut == "PENDIENTE":
        badge_aut = '<span class="jp-badge jp-wait">⏳ PENDIENTE DE AUTORIZAR</span>'
    else:
        badge_aut = '<span class="jp-badge jp-mute">AUT. N/D</span>'

    chips, total = _chips_productos(item)
    c_nom, c_tel = _contacto_visible(item)
    contacto = ""
    if c_nom or c_tel:
        contacto = f'<div class="jp-line"><b>RECIBE:</b> {_e(c_nom)}' + (f' · <span class="jp-tel">{_e(c_tel)}</span>' if c_tel else "") + "</div>"
    destino = str(item.get("DESTINO", "") or "").strip()
    destino_html = f'<div class="jp-line"><b>DESTINO:</b> {_e(destino[:90])}{"…" if len(destino) > 90 else ""}</div>' if destino else ""

    guia_html = ""
    if mostrar_guia:
        paq = item.get("PAQUETERÍA", "") or item.get("PAQUETERIA_NOMBRE", "") or ""
        guia = item.get("NÚMERO DE GUÍA", "") or item.get("NUMERO_GUIA", "") or ""
        paq = "" if str(paq) in ("0", "0.0", "nan") else str(paq)
        guia = limpiar_numero_texto(guia)
        guia_html = f"""
        <div class="jp-col jp-col-guia">
            <div class="jp-lbl">Envío</div>
            <div class="jp-guia {'jp-pend' if not paq else ''}">{_e(paq) if paq else 'PAQUETERÍA PENDIENTE'}</div>
            <div class="jp-guia2 {'jp-pend' if not guia else ''}">{_e(guia) if guia else 'GUÍA PENDIENTE'}</div>
        </div>"""

    return f"""
    <div class="jp-card" style="--acento:{acento};">
        <div class="jp-col" style="flex:0 1 150px;">
            <div class="jp-lbl">Folio / Fecha</div>
            <div class="jp-folio">#{_e(item.get('FOLIO', ''))}</div>
            <div class="jp-fecha">{_e(str(item.get('FECHA', ''))[:10])}</div>
            {badge_est}{badge_aut}
        </div>
        <div class="jp-col">
            <div class="jp-lbl">Hotel / Solicitante</div>
            <div class="jp-hotel">{_e(str(item.get('NOMBRE DEL HOTEL', ''))[:60])}</div>
            <div class="jp-line"><b>SOLICITÓ:</b> {_e(str(item.get('SOLICITO', ''))[:40])}</div>
            {contacto}{destino_html}
        </div>
        <div class="jp-col jp-col-prod">
            <div class="jp-lbl">Productos · {total} pzas</div>
            <div class="jp-chips">{chips}</div>
        </div>{guia_html}
    </div>"""


def main():
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    usuario_actual = obtener_usuario_actual()
    puede_autorizar = usuario_actual in AUTORIZADORES

    df_actual, sha_actual = obtener_datos_github()

    if not df_actual.empty:
        for col in ["PAQUETERIA_NOMBRE", "NUMERO_GUIA", "COSTO_GUIA", "CANTIDAD_TOTAL", "COSTO_TOTAL", "ESTATUS"]:
            if col not in df_actual.columns:
                if col == "ESTATUS":
                    df_actual[col] = "NO SURTIDO"
                else:
                    df_actual[col] = 0.0

        nuevo_num = int(pd.to_numeric(df_actual["FOLIO"]).max() + 1)
    else:
        nuevo_num = 1

    # --- CAPTURA NUEVA ---
    st.write("")
    with st.container():
        f_paq_nombre = ""
        f_tipo_pago = ""

        c1, c2, c3, c4 = st.columns([0.8, 1.2, 1.2, 1])

        f_folio = c1.text_input(":material/confirmation_number: FOLIO", value=f"JYP-{nuevo_num}", disabled=True)
        f_paq_sel = c2.selectbox(
            ":material/local_shipping: FORMA DE ENVÍO",
            ["Envio Pagado", "Envio por cobrar", "Entrega Personal"]
        )
        f_ent_sel = c3.selectbox(
            ":material/home_pin: TIPO DE ENTREGA",
            ["Domicilio", "Ocurre Oficina"]
        )
        f_fecha_sel = c4.date_input(":material/calendar_today: FECHA", date.today())

    st.divider()

    col_rem, col_dest = st.columns(2)
    with col_rem:
        st.markdown(
            '<div style="background:#4e73df;color:white;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">REMITENTE</div>',
            unsafe_allow_html=True
        )
        st.write("")
        st.text_input(":material/corporate_fare: Nombre", "JABONES Y PRODUCTOS ESPECIALIZADOS", disabled=True)

        c_rem1, c_rem2 = st.columns([2, 1])
        f_atn_rem = c_rem1.text_input(":material/person: Atención (Nombre) *", "RIGOBERTO HERNANDEZ")
        f_tel_rem = c_rem2.text_input(":material/call: Teléfono (10 dígitos) *", "3319753122")
        f_soli = st.text_input(
            ":material/badge: Solicitante / Agente *",
            placeholder="NOMBRE DE QUIEN SOLICITA LAS MUESTRAS",
            key=f"soli_{st.session_state.reset_key}"
        ).upper()

    with col_dest:
        st.markdown(
            '<div style="background:#f6c23e;color:black;text-align:center;font-weight:bold;padding:5px;border-radius:4px;">DESTINATARIO / HOTEL</div>',
            unsafe_allow_html=True
        )
        st.write("")
        f_h = st.text_input(":material/hotel: Hotel / Nombre", key=f"h_{st.session_state.reset_key}").upper()
        f_ca = st.text_input(":material/location_on: Calle y Número", key=f"ca_{st.session_state.reset_key}").upper()

        cd1, cd2 = st.columns(2)
        f_co = cd1.text_input(":material/map: Colonia", key=f"co_{st.session_state.reset_key}").upper()
        f_cp = cd2.text_input(":material/mailbox: C.P.", key=f"cp_{st.session_state.reset_key}")

        cd3, cd4 = st.columns(2)
        f_ci = cd3.text_input(":material/location_city: Ciudad", key=f"ci_{st.session_state.reset_key}").upper()
        f_es = cd4.text_input(":material/public: Estado", key=f"es_{st.session_state.reset_key}").upper()

        cc1, cc2 = st.columns([2, 1])
        f_con_nom = cc1.text_input(
            ":material/person: Contacto Receptor - Nombre *",
            placeholder="NOMBRE DE QUIEN RECIBE",
            key=f"con_nom_{st.session_state.reset_key}"
        ).upper()
        f_con_tel = cc2.text_input(
            ":material/call: Contacto Receptor - Teléfono *",
            placeholder="10 DÍGITOS",
            key=f"con_tel_{st.session_state.reset_key}"
        )
        # Texto combinado (para el PDF y compatibilidad con la columna CONTACTO existente)
        f_con = f"{f_con_nom.strip()} TEL: {limpiar_telefono(f_con_tel)}"

    st.divider()

    st.markdown("""
        <style>
        .stMultiSelect div[data-baseweb="select"] {
            height: auto !important;
            min-height: 45px !important;
        }
        .stMultiSelect div[data-baseweb="valueContainer"] {
            flex-wrap: wrap !important;
            display: flex !important;
            gap: 5px !important;
            padding: 5px 0 !important;
        }
        .stMultiSelect div[data-baseweb="tag"] {
            background-color: #384A52 !important;
            border-radius: 5px;
            color: white !important;
        }
        div[data-testid="stNumberInput"] {
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <div style='display: flex; align-items: center; gap: 10px; margin: 15px 0 10px 0;'>
            <div style='background: #00D4FF; width: 4px; height: 16px; border-radius: 2px;'></div>
            <span style='color: white; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;'>
                SELECCION DE PRODUCTOS
            </span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "seleccionados_muestras" not in st.session_state:
        st.session_state.seleccionados_muestras = []

    def eliminar_producto(prod_a_borrar):
        st.session_state.seleccionados_muestras = [p for p in st.session_state.seleccionados_muestras if p != prod_a_borrar]

    seleccionados = st.multiselect(
        ":material/search: Busca y selecciona productos:",
        list(precios.keys()),
        key=f"prod_select_{st.session_state.reset_key}",
        default=st.session_state.get('seleccionados_muestras', []),
        placeholder="SELECCIONAR PRODUCTOS"
    )

    st.session_state.seleccionados_muestras = seleccionados

    prods_actuales = []
    total_cantidad = 0
    total_costo_prods = 0

    if seleccionados:
        st.info(f"Has seleccionado {len(seleccionados)} productos. Indica las cantidades abajo:")

        num_filas = (len(seleccionados) + 2) // 3
        altura_dinamica = min(max(num_filas * 95, 120), 500)

        with st.container(height=altura_dinamica, border=True):
            col_bloque_1, col_bloque_2, col_bloque_3 = st.columns(3)

            for i, p in enumerate(seleccionados):
                if i % 3 == 0:
                    target_col = col_bloque_1
                elif i % 3 == 1:
                    target_col = col_bloque_2
                else:
                    target_col = col_bloque_3

                with target_col:
                    c1, c2, c3 = st.columns([1.5, 1.8, 0.5])

                    with c1:
                        st.markdown(f"<div style='padding-top:10px; font-size:10px; line-height:1.1;'><b>{p.upper()}</b></div>", unsafe_allow_html=True)

                    with c2:
                        q = st.number_input("Cant", min_value=0, step=1, key=f"q_{p}", label_visibility="collapsed")

                    with c3:
                        st.button(":material/delete:", key=f"btn_del_{p}", type="tertiary", on_click=eliminar_producto, args=(p,))

                    if q > 0:
                        prods_actuales.append({"desc": p, "cant": q})
                        total_cantidad += q
                        total_costo_prods += (q * (precios.get(p, 0)))

                    st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)

    st.markdown("---")
    f_coment = st.text_area(
        "💬 COMENTARIOS ADICIONALES",
        height=100,
        placeholder="SI EL PRODUCTO NO ESTA EN LA LISTA SELECCIONABLE, INGRESALOS AQUI O CUALQUIER COMENTARIO ADICIONAL"
    ).upper()

    st.write("")
    f_autoriza = False
    if puede_autorizar:
        f_autoriza = st.checkbox(
            "✅ AUTORIZAR ESTE ENVÍO",
            key=f"auto_{st.session_state.reset_key}",
            help="Solo visible para usuarios autorizadores."
        )
    else:
        st.info("Este registro se guardará como PENDIENTE DE AUTORIZACIÓN. No podrá despacharse hasta que lo autorice Rigoberto o Arodriguez.")

    st.write("")

    col_b1, col_b2, col_b3 = st.columns([1, 1, 0.5])

    if col_b1.button(":material/save: GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
        errores = []
        if not f_h.strip():
            errores.append("Falta el hotel")
        if not f_soli.strip():
            errores.append("Falta el nombre de quien solicita (Solicitante / Agente)")
        if len(f_atn_rem.strip()) < 3:
            errores.append("Remitente: falta el nombre en Atención")
        if len(limpiar_telefono(f_tel_rem)) != 10:
            errores.append("Remitente: el teléfono debe tener 10 dígitos")
        if len(f_con_nom.strip()) < 3:
            errores.append("Destinatario: falta el nombre de quien recibe")
        if len(limpiar_telefono(f_con_tel)) != 10:
            errores.append("Destinatario: el teléfono de quien recibe debe tener 10 dígitos")
        if not prods_actuales:
            errores.append("Selecciona al menos un producto")

        if errores:
            for e in errores:
                st.error(e)
        else:
            autorizado = bool(puede_autorizar and f_autoriza)
            direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()

            reg = {
                "FOLIO": nuevo_num,
                "ESTATUS": "NO SURTIDO",
                "FECHA": f_fecha_sel.strftime("%Y-%m-%d"),
                "NOMBRE DEL HOTEL": f_h.upper(),
                "DESTINO": direccion_completa,
                "CONTACTO": f_con.upper(),
                "CONTACTO_NOMBRE": f_con_nom.strip(),
                "CONTACTO_TELEFONO": limpiar_telefono(f_con_tel),
                "AUTORIZACION": "AUTORIZADO" if autorizado else "PENDIENTE",
                "AUTORIZADO_POR": usuario_actual if autorizado else "",
                "FECHA_AUTORIZACION": datetime.now().strftime("%Y-%m-%d %H:%M") if autorizado else "",
                "SOLICITO": f_soli.upper(),
                "PAQUETERIA": f_paq_sel.upper(),
                "PAQUETERIA_NOMBRE": f_paq_nombre,
                "NUMERO_GUIA": "",
                "COSTO_GUIA": 0.0,
                "CANTIDAD_TOTAL": total_cantidad,
                "COSTO_TOTAL": round(total_costo_prods, 2),
                "COMENTARIOS": f_coment
            }

            for p in precios.keys():
                reg[p] = 0
            for item in prods_actuales:
                reg[item["desc"]] = item["cant"]

            df_f = pd.concat([df_actual, pd.DataFrame([reg])], ignore_index=True)

            if subir_a_github(df_f, sha_actual, f"Folio JYP-{nuevo_num}"):
                st.session_state.folio_actual = nuevo_num
                st.session_state.folio_guardado = True

                st.success(f"¡Guardado correctamente! Folio: JYP-{nuevo_num}")
                time.sleep(1)
                st.rerun()

    if not st.session_state.folio_guardado:
        st.markdown("""
            <div style="background-color: rgba(255, 165, 0, 0.1); border-left: 5px solid #FFA500; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                <span style="color: white; font-size: 14px;">
                    <b style="color: #FFA500;">BLOQUEO DE SEGURIDAD:</b>
                    Debes guardar el registro antes de poder imprimir.
                </span>
            </div>
        """, unsafe_allow_html=True)

    if col_b2.button(":material/picture_as_pdf: GUARDAR PDF", use_container_width=True, disabled=not st.session_state.folio_guardado):
        folio_final = st.session_state.get("folio_actual", nuevo_num - 1)
        folio_simple = f"JYP-{folio_final}"

        h_print = generar_html_impresion(
            folio_simple,
            f_paq_sel, f_ent_sel, f_fecha_sel, f_atn_rem, f_tel_rem,
            f_soli, f_h, f_ca, f_co, f_cp, f_ci, f_es, f_con,
            prods_actuales, f_coment, f_paq_nombre, f_tipo_pago
        )

        js_code = f"""
            <html>
                <head><title>{folio_simple}_{f_h}</title></head>
                <body>
                    {h_print}
                    <script>setTimeout(function(){{ window.print(); }}, 500);</script>
                </body>
            </html>
        """
        components.html(js_code, height=0)

    if col_b3.button(":material/delete_sweep: BORRAR", use_container_width=True):
        st.session_state.folio_guardado = False
        if "folio_actual" in st.session_state:
            del st.session_state.folio_actual
        st.session_state.seleccionados_muestras = []
        st.session_state.reset_key += 1
        st.rerun()

    st.write("")
    st.write("")
    st.write("")

    with st.expander("🔍 CONSULTA DE FOLIOS Y GUIAS", expanded=True):
        st.markdown(f"<style>{CSS_TARJETAS}</style>", unsafe_allow_html=True)

        if df_actual.empty:
            st.info("No hay registros todavía.")
        else:
            # ---------- Series de apoyo (estatus y autorización) ----------
            def _serie(df, col, defecto=""):
                if col in df.columns:
                    return df[col].fillna("").astype(str).str.strip().str.upper().replace("", defecto)
                return pd.Series(defecto, index=df.index)

            est_all = _serie(df_actual, "ESTATUS", "NO SURTIDO")
            aut_all = _serie(df_actual, "AUTORIZACION", "")

            # ---------- PENDIENTES DE AUTORIZACIÓN (solo autorizadores) ----------
            if puede_autorizar:
                pend = df_actual[aut_all == "PENDIENTE"].copy()
                if pend.empty:
                    st.success("✓ No hay envíos pendientes de autorización.")
                else:
                    st.markdown(
                        f'<div class="jp-banner">⏳ {len(pend)} ENVÍO(S) ESPERAN TU AUTORIZACIÓN</div>',
                        unsafe_allow_html=True,
                    )
                    pend["_f"] = pd.to_numeric(pend["FOLIO"], errors="coerce")
                    for _, r in pend.sort_values("_f", ascending=False).iterrows():
                        with st.container(border=True):
                            c_info, c_btn = st.columns([5, 1.3], vertical_alignment="center")
                            c_info.markdown(_tarjeta_html(r.fillna("").to_dict(), mostrar_guia=False), unsafe_allow_html=True)
                            if c_btn.button("✅ AUTORIZAR", key=f"aut_{r['FOLIO']}", type="primary", use_container_width=True):
                                with st.spinner("Autorizando..."):
                                    df_nuevo, sha_nuevo = obtener_datos_github()
                                    for col in ["AUTORIZACION", "AUTORIZADO_POR", "FECHA_AUTORIZACION"]:
                                        if col not in df_nuevo.columns:
                                            df_nuevo[col] = ""
                                        df_nuevo[col] = df_nuevo[col].astype(object)
                                    mask = pd.to_numeric(df_nuevo["FOLIO"], errors="coerce") == pd.to_numeric(r["FOLIO"])
                                    df_nuevo.loc[mask, "AUTORIZACION"] = "AUTORIZADO"
                                    df_nuevo.loc[mask, "AUTORIZADO_POR"] = usuario_actual
                                    df_nuevo.loc[mask, "FECHA_AUTORIZACION"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                    ok = subir_a_github(df_nuevo, sha_nuevo, f"Autoriza folio JYP-{r['FOLIO']}")
                                if ok:
                                    st.success(f"Folio JYP-{r['FOLIO']} autorizado")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("No se pudo guardar la autorización. Intenta de nuevo.")
                st.divider()

            # ---------- RESUMEN ----------
            n_total = len(df_actual)
            n_pend = int((aut_all == "PENDIENTE").sum())
            n_nosurt = int((est_all != "DESPACHADO").sum())
            n_desp = int((est_all == "DESPACHADO").sum())
            st.markdown(
                f"""
                <div class="jp-tiles">
                    <div class="jp-tile"><div class="n" style="color:#FFFFFF;">{n_total}</div><div class="t">Folios totales</div></div>
                    <div class="jp-tile"><div class="n" style="color:#f97316;">{n_pend}</div><div class="t">Por autorizar</div></div>
                    <div class="jp-tile"><div class="n" style="color:#FF4444;">{n_nosurt}</div><div class="t">No surtidos</div></div>
                    <div class="jp-tile"><div class="n" style="color:#00FFAA;">{n_desp}</div><div class="t">Despachados</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ---------- FILTROS ----------
            f1, f2, f3 = st.columns([2.4, 1, 1])
            busqueda = f1.text_input(
                "Buscar", placeholder="Hotel, solicitante, folio, guía...", label_visibility="collapsed"
            ).strip().upper()
            filtro_est = f2.selectbox("Estatus", ["TODOS", "NO SURTIDO", "DESPACHADO"], label_visibility="collapsed")
            filtro_aut = f3.selectbox("Autorización", ["TODAS", "PENDIENTE", "AUTORIZADO"], label_visibility="collapsed")

            df_vista = df_actual.copy().fillna("")
            if busqueda:
                hay = df_vista.astype(str).apply(
                    lambda col: col.str.contains(busqueda, case=False, regex=False)
                ).any(axis=1)
                df_vista = df_vista[hay]
            if filtro_est != "TODOS":
                df_vista = df_vista[est_all.loc[df_vista.index] == filtro_est]
            if filtro_aut != "TODAS":
                df_vista = df_vista[aut_all.loc[df_vista.index] == filtro_aut]

            df_vista = df_vista.assign(_f=pd.to_numeric(df_vista["FOLIO"], errors="coerce")).sort_values("_f", ascending=False)

            # ---------- RESULTADOS ----------
            MAX_TARJETAS = 60
            total_res = len(df_vista)
            if total_res == 0:
                st.info("Ningún folio coincide con los filtros.")
            else:
                st.caption(
                    f"Mostrando {min(total_res, MAX_TARJETAS)} de {total_res} folio(s)"
                    + (" · afina la búsqueda para ver los demás" if total_res > MAX_TARJETAS else "")
                )
                data_busqueda = df_vista.head(MAX_TARJETAS).to_dict("records")
                tarjetas = "".join(_tarjeta_html(item) for item in data_busqueda)
                alto = int(min(len(data_busqueda) * 150 + 20, 640))
                html_busqueda = f"""
                <style>
                    body {{ background: transparent; margin: 0; padding: 0; }}
                    ::-webkit-scrollbar {{ width: 8px; }}
                    ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); border-radius: 10px; }}
                    ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; min-height: 50px; }}
                    ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                    {CSS_TARJETAS}
                </style>
                <div style="padding-right:8px;">{tarjetas}</div>
                """
                components.html(html_busqueda, height=alto, scrolling=True)


if __name__ == "__main__":
    main()
