import time
from datetime import date

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
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Formatos - Envio de Muestras",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
def main():
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

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
        f_atn_rem = c_rem1.text_input(":material/person: Atención", "RIGOBERTO HERNANDEZ")
        f_tel_rem = c_rem2.text_input(":material/call: Teléfono", "3319753122")
        f_soli = st.text_input(
            ":material/badge: Solicitante / Agente",
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

        f_con = st.text_input(
            ":material/contact_phone: Contacto Receptor",
            placeholder="NOMBRE Y TELÉFONO DE QUIEN RECIBE",
            key=f"con_{st.session_state.reset_key}"
        ).upper()

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
    st.write("")

    col_b1, col_b2, col_b3 = st.columns([1, 1, 0.5])

    if col_b1.button(":material/save: GUARDAR REGISTRO NUEVO", use_container_width=True, type="primary"):
        if not f_h:
            st.error("Falta el hotel")
        elif not f_soli:
            st.error("Falta el nombre de quien solicita (Solicitante / Agente)")
        elif not f_con:
            st.error("Falta el nombre y teléfono de quien recibe")
        elif not prods_actuales:
            st.error("Selecciona al menos un producto")
        else:
            direccion_completa = f"{f_ca}, Col. {f_co}, CP {f_cp}, {f_ci}, {f_es}".upper()

            reg = {
                "FOLIO": nuevo_num,
                "ESTATUS": "NO SURTIDO",
                "FECHA": f_fecha_sel.strftime("%Y-%m-%d"),
                "NOMBRE DEL HOTEL": f_h.upper(),
                "DESTINO": direccion_completa,
                "CONTACTO": f_con.upper(),
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
        if not df_actual.empty:
            busqueda = st.text_input("Escribe el nombre del Hotel, Solicitante o Folio para filtrar:").upper()

            df_vista = df_actual.copy()
            df_vista = df_vista.fillna('')

            if busqueda:
                df_vista = df_vista[df_vista.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

            df_render = df_vista.sort_values(by="FOLIO", ascending=False)
            data_busqueda = df_render.to_dict('records')

            alto_busqueda = min(len(data_busqueda) * 130 + 20, 550)

            tarjetas_busqueda_html = ""
            for item in data_busqueda:
                detalle_p_busqueda = ""
                for p_key in precios.keys():
                    cant_p = pd.to_numeric(item.get(p_key, 0), errors='coerce')
                    if pd.notna(cant_p) and cant_p > 0:
                        detalle_p_busqueda += f"• {int(cant_p)} PZAS {str(p_key).upper()}<br>"

                estatus_val = str(item.get('ESTATUS', 'NO SURTIDO')).upper()
                if estatus_val == 'DESPACHADO':
                    badge_status = "<div style='display:inline-block; background:rgba(0,255,170,0.1); border:1px solid #00FFAA; color:#00FFAA; padding:2px 6px; border-radius:10px; font-size:8px; font-weight:800; letter-spacing:1px;'>✓ DESPACHADO</div>"
                else:
                    badge_status = "<div style='display:inline-block; background:rgba(255,68,68,0.1); border:1px solid #FF4444; color:#FF4444; padding:2px 6px; border-radius:10px; font-size:8px; font-weight:800; letter-spacing:1px; box-shadow: 0 0 8px rgba(255,68,68,0.4);'>⚠️ NO SURTIDO</div>"

                paq_text = item.get('PAQUETERÍA', '') or item.get('PAQUETERIA_NOMBRE', '')
                guia_text = item.get('NÚMERO DE GUÍA', '') or item.get('NUMERO_GUIA', '')

                tarjetas_busqueda_html += f"""
                <div class="card-busqueda" style="padding: 15px; margin-bottom: 10px; background: #263238; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1.1;">
                        <div class="label-mini">Folio / Fecha</div>
                        <div class="val-folio">#{str(item['FOLIO'])}</div>
                        <div style="color: rgba(255,255,255,0.5); font-size: 10px; margin-bottom: 5px;">{str(item['FECHA'])[:10]}</div>
                        {badge_status}
                    </div>
                    <div style="flex: 2.0; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                        <div class="label-mini">Hotel / Destino</div>
                        <div class="val-hotel">{str(item.get('NOMBRE DEL HOTEL', ''))[:30]}</div>
                        <div class="val-soli">SOLICITÓ: {str(item.get('SOLICITO', ''))[:30]}</div>
                    </div>
                    <div style="flex: 2.5; padding: 0 10px; border-left: 1px solid rgba(255,255,255,0.05);">
                        <div class="label-mini">Productos Solicitados</div>
                        <div style="color: #FFFFFF; font-size: 9px; line-height: 1.4; opacity: 0.9;">{detalle_p_busqueda if detalle_p_busqueda else '<i>Sin detalle</i>'}</div>
                    </div>
                    <div style="flex: 1.6; text-align: right; border-left: 1px solid rgba(255,255,255,0.05); padding-left: 10px;">
                        <div class="val-guia {'pendiente' if not paq_text else ''}">
                            { paq_text if paq_text else 'PAQUETERÍA PENDIENTE' }
                        </div>
                        <div class="val-sub-guia {'pendiente' if not guia_text else ''}">
                            { guia_text if guia_text else 'GUÍA PENDIENTE' }
                        </div>
                    </div>
                </div>
                """

            html_busqueda = f"""
            <div style="font-family: 'Inter', sans-serif; padding-right: 10px; height: {alto_busqueda}px; overflow-y: auto;">
                <style>
                    body {{ background: transparent; margin: 0; padding: 0; }}
                    ::-webkit-scrollbar {{ width: 8px; }}
                    ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                    ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; min-height: 50px; }}
                    ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}

                    .card-busqueda {{
                        transition: all 0.3s ease;
                    }}
                    .card-busqueda:hover {{ border-color: #38bdf8; background: #2d3b42; transform: translateX(5px); }}
                    .label-mini {{ font-size: 8px; color: rgba(255,255,255,0.4); font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }}
                    .val-folio {{ color: #00FFAA; font-family: monospace; font-size: 16px; font-weight: 800; }}
                    .val-hotel {{ color: #FFFFFF; font-size: 13px; font-weight: 700; margin-top: 2px; }}
                    .val-soli {{ color: #FFD700; font-size: 10px; font-weight: 600; margin-top: 2px; opacity: 0.8; }}
                    .val-guia {{ color: #38bdf8; font-family: monospace; font-size: 14px; font-weight: 800; line-height: 1.2; }}
                    .val-sub-guia {{ color: #FFFFFF; font-family: monospace; font-size: 12px; font-weight: 700; margin-top: 4px; }}
                    .pendiente {{ color: #f97316 !important; font-style: italic; opacity: 0.8; font-size: 10px; font-weight: 400; }}
                </style>
                {tarjetas_busqueda_html}
            </div>
            """
            components.html(html_busqueda, height=alto_busqueda, scrolling=False)
        else:
            st.info("No hay registros todavía.")


if __name__ == "__main__":
    main()
