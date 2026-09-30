import base64
from datetime import datetime, timedelta
from io import StringIO
import io
import re
import time
import unicodedata
import zipfile
import calendar
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import pandas as pd
from pypdf import PdfReader, PdfWriter
import qrcode
import streamlit.components.v1 as components
import streamlit as st
import pytz
from auth import exigir_autenticacion
from components.layout import render_layout

exigir_autenticacion("Incidencias")


# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Logistics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LAYOUT MAESTRO (estilos, sesión, permisos, header, buscador, menú y footer)
# ============================================================
render_layout(modulo_actual="SEGUIMIENTO", submodulo_actual="INCIDENCIAS")


def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    ).upper()
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    return " ".join(texto.split())



# ================================================================================
# 5. INTERFAZ PRINCIPAL 
# ================================================================================

def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True

    # ── CONFIGURACIÓN DEL REPOSITORIO DE INCIDENCIAS ─────────────────────────────────────
    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "incidencias.csv"
    CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"
    MATRIZ_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/Matriz_Excel_Dashboard.csv"
    
    usuario_actual = str(st.session_state.get("usuario", st.session_state.get("usuario_activo", ""))).strip()
    nombre_usuario_actual = str(st.session_state.get("nombre_completo", "")).strip().upper()
    es_admin_session = st.session_state.get("es_admin", False)
    es_administrador = es_admin_session or (usuario_actual.upper() in ["RIGOBERTO", "RIGOBERTO HERNÁNDEZ"])
    
    # Se agregó la columna CREADOR y se mantiene RESPONSABLE
    COLUMNAS_INCIDENCIAS = [
        "FOLIO", "TIPO", "CREADOR", "RESPONSABLE", "PRIORIDAD", "VINCULO_BUSQUEDA", 
        "CLIENTE_DESTINO", "PEDIDO_GUIA", "ID_SEGUIMIENTO", "ID_QUEJA", 
        "DETALLE_INCIDENCIA", "ACCIONES", "ESTATUS"
    ]
    
    @st.cache_data(ttl=600)
    def cargar_matriz_global():
        try:
            r = requests.get(f"{MATRIZ_URL}?t={int(time.time())}")
            if r.status_code == 200:
                df = pd.read_csv(StringIO(r.text))
                df.columns = [c.strip().upper() for c in df.columns]
                return df
        except:
            return None
        return None
    
    df_global = cargar_matriz_global()
    
    API_URL = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    RAMA = "main"

    def _gh_headers(extra=None):
        if not TOKEN:
            raise RuntimeError("No se encontró el GITHUB_TOKEN en los secrets.")
        h = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        if extra:
            h.update(extra)
        return h

    def _normalizar_inc(df):
        df = df.copy()
        df.columns = [str(c).strip().upper() for c in df.columns]
        for c in COLUMNAS_INCIDENCIAS:
            if c not in df.columns:
                df[c] = ""
        df = df[COLUMNAS_INCIDENCIAS]
        for c in COLUMNAS_INCIDENCIAS:
            df[c] = df[c].fillna("").astype(str).replace("nan", "")
        return df.reset_index(drop=True)

    def _leer_incidencias_fresco():
        """Lee incidencias.csv por la API de GitHub (SIN caché del CDN). Devuelve (df, sha).
        Si el archivo no existe devuelve (df vacío, None)."""
        params = {"ref": RAMA, "t": time.time_ns()}
        r = requests.get(API_URL, headers=_gh_headers(), params=params, timeout=20)
        if r.status_code == 404:
            return pd.DataFrame(columns=COLUMNAS_INCIDENCIAS), None
        r.raise_for_status()
        data = r.json()
        if data.get("content"):
            raw = base64.b64decode(data["content"])
        else:  # archivo grande: la API no manda el contenido en base64
            r2 = requests.get(API_URL, headers=_gh_headers({"Accept": "application/vnd.github.raw"}),
                              params=params, timeout=30)
            r2.raise_for_status()
            raw = r2.content
        df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig", dtype=str, keep_default_na=False)
        return _normalizar_inc(df), data.get("sha")

    def _put_incidencias(df, sha, mensaje):
        payload = {
            "message": mensaje,
            "content": base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode(),
            "branch": RAMA,
        }
        if sha:
            payload["sha"] = sha
        return requests.put(API_URL, headers=_gh_headers(), json=payload, timeout=30)

    def guardar_incidencia_github(nueva_data, es_nuevo, mensaje):
        """Guarda SOLO esta fila. Relee el archivo justo antes de escribir (nunca pisa lo de
        otros) y reintenta si hay conflicto de versión. Devuelve (ok, df_final, folio_usado)."""
        for intento in range(4):
            try:
                df, sha = _leer_incidencias_fresco()
            except Exception as e:
                st.error(f"No se pudo leer GitHub antes de guardar: {e}")
                return False, None, None

            datos = dict(nueva_data)
            existe = df["FOLIO"] == datos["FOLIO"]

            # Registro nuevo cuyo folio ya lo ocupó otra persona: se le asigna el siguiente libre
            if es_nuevo and existe.any():
                nums = df["FOLIO"].str.extract(r"REG-(\d+)")[0].dropna().astype(int)
                datos["FOLIO"] = f"REG-{(nums.max() if not nums.empty else 0) + 1:03d}"
                existe = df["FOLIO"] == datos["FOLIO"]

            fila = {c: str(datos.get(c, "")) for c in COLUMNAS_INCIDENCIAS}
            if existe.any():
                idx = df.index[existe][0]          # se edita en su lugar (conserva el orden)
                for c in COLUMNAS_INCIDENCIAS:
                    df.at[idx, c] = fila[c]
            else:
                df = pd.concat([df, pd.DataFrame([fila])], ignore_index=True)

            try:
                r = _put_incidencias(df, sha, mensaje)
            except Exception as e:
                st.error(f"No se pudo guardar en GitHub: {e}")
                return False, None, None

            if r.status_code in (200, 201):
                return True, df, datos["FOLIO"]
            if r.status_code in (409, 422) and intento < 3:
                time.sleep(0.6 * (intento + 1))   # alguien más guardó: releer y reintentar
                continue
            st.error(f"Error de GitHub: {r.status_code} - {r.text[:200]}")
            return False, None, None

        st.error("No se pudo guardar por conflictos repetidos. Intenta de nuevo.")
        return False, None, None

    def guardar_tabla_completa(df_nuevo, df_base):
        """Para el editor avanzado (reemplaza la tabla). Solo escribe si nadie más cambió el
        archivo desde que lo cargaste; si cambió, NO pisa nada. Devuelve (estado, df)."""
        try:
            fresco, sha = _leer_incidencias_fresco()
        except Exception as e:
            st.error(f"No se pudo leer GitHub antes de guardar: {e}")
            return "ERROR", None

        if not fresco.equals(_normalizar_inc(df_base)):
            return "CONFLICTO", fresco

        df_guardar = _normalizar_inc(df_nuevo)
        try:
            r = _put_incidencias(df_guardar, sha, f"Sincronización de registros {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        except Exception as e:
            st.error(f"No se pudo guardar en GitHub: {e}")
            return "ERROR", None

        if r.status_code in (200, 201):
            return "OK", df_guardar
        if r.status_code in (409, 422):
            try:
                fresco, _ = _leer_incidencias_fresco()
            except Exception:
                fresco = df_base
            return "CONFLICTO", fresco
        st.error(f"Error de GitHub: {r.status_code} - {r.text[:200]}")
        return "ERROR", None

    def cargar_datos_seguro():
        try:
            df, sha = _leer_incidencias_fresco()
            if sha is None:  # el archivo no existe todavía: se crea vacío
                df_nuevo = pd.DataFrame(columns=COLUMNAS_INCIDENCIAS)
                _put_incidencias(df_nuevo, None, "Crear incidencias.csv")
                return df_nuevo
            return df
        except Exception as e:
            st.error(f"Error al cargar el módulo: {e}")
        return pd.DataFrame(columns=COLUMNAS_INCIDENCIAS)

    # Siempre datos frescos en cada recarga (así ves lo que capturan los demás)
    st.session_state.df_incidencias = cargar_datos_seguro()

    for c in COLUMNAS_INCIDENCIAS:
        if c not in st.session_state.df_incidencias.columns:
            st.session_state.df_incidencias[c] = ""

    df_master = st.session_state.df_incidencias.copy()

    _msg = st.session_state.pop("msg_incidencias", None)
    if _msg:
        (st.success if _msg[0] == "ok" else st.warning)(_msg[1])
    
    st.markdown("""
        <style>
        input[type=number]::-webkit-inner-spin-button, 
        input[type=number]::-webkit-outer-spin-button { 
            -webkit-appearance: none; margin: 0; 
        }
        .search-container-pro {
            border-left: 4px solid #f43f5e;
            padding-left: 15px;
            margin-bottom: 20px;
            background: rgba(244, 63, 94, 0.05);
            padding-top: 10px;
            padding-bottom: 1px;
            border-radius: 0 10px 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ── 1. PANEL DE CAPTURA INTELIGENTE (EXCLUSIVO PARA ADMIN) ───────────────────────────
    if es_administrador:
        with st.expander("➕ Registrar o Editar Incidencia / Tarea", expanded=False):
            
            c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])
            
            with c1:
                tipo_opciones = ["Incidencia", "Tarea (Task)"]
                t_tipo = st.selectbox("Tipo de Registro", tipo_opciones)
            
            with c2:
                n_pedido = st.text_input("📦 Vincular Pedido / Factura", placeholder="Escribe pedido...").strip().upper()
            
            if not st.session_state.df_incidencias.empty and "FOLIO" in st.session_state.df_incidencias.columns:
                folios_numeros = st.session_state.df_incidencias['FOLIO'].str.extract(r'REG-(\d+)')[0].dropna().astype(int)
                if not folios_numeros.empty:
                    ultimo_folio = folios_numeros.max()
                    sugerencia_folio = f"REG-{ultimo_folio + 1:03d}"
                else:
                    sugerencia_folio = "REG-001"
            else:
                sugerencia_folio = "REG-001"
                
            with c3:
                t_folio_input = st.text_input("Folio ID", value=sugerencia_folio).strip().upper()
                
            incidencia_existente = None
            mask = None
            if t_folio_input and not st.session_state.df_incidencias.empty:
                mask = st.session_state.df_incidencias['FOLIO'] == t_folio_input
                if mask.any():
                    incidencia_existente = st.session_state.df_incidencias[mask].iloc[0]
                    st.info(f"Modo Edición: Folio {t_folio_input}")
                    
            with c4:
                prioridades = ["Media", "Urgente", "Alta", "Baja"]
                idx_prio = prioridades.index(incidencia_existente['PRIORIDAD']) if incidencia_existente is not None and incidencia_existente['PRIORIDAD'] in prioridades else 0
                t_prior = st.selectbox("Prioridad", prioridades, index=idx_prio)
    
            info_matriz = {"cliente_destino": "", "pedido_guia": ""}
            if n_pedido and df_global is not None:
                res = df_global[df_global["NÚMERO DE PEDIDO"].astype(str).str.contains(n_pedido, na=False)]
                if not res.empty:
                    fila_m = res.iloc[0]
                    guia = fila_m.get('NÚMERO DE GUÍA', 'N/A')
                    cliente = fila_m.get('NOMBRE DEL CLIENTE', 'N/A')
                    destino = fila_m.get('DESTINO', 'N/A')
                    info_matriz["cliente_destino"] = f"CLIENTE: {cliente} | DESTINO: {destino}"
                    info_matriz["pedido_guia"] = f"PEDIDO: {n_pedido} | GUIA: {guia}"
                else:
                    st.warning("⚠️ Pedido no localizado en la Matriz. Puedes llenar los campos a mano.")
    
            with st.form("form_incidencias", clear_on_submit=False):
                f2_c1, f2_c2 = st.columns([1, 1])
                
                # Lista de colaboradores del sistema para asignar tareas/incidencias
                lista_colaboradores = [
                    "RIGOBERTO HERNÁNDEZ", "RIGOBERTO DEL REAL", "ALEJANDRA GOMEZ", 
                    "CYNTHIA ORNELAS", "BRENDA PIZANO", "CARLOS FIALKO", 
                    "CLAUDIA JIMENEZ", "CARLOS VAZQUEZ", "SANDRA", 
                    "ALEJANDRA SANCHEZ", "MARTHA CASAS", "CRISTOBAL A", "URI EL CAPI"
                ]
                
                with f2_c1:
                    val_cd = info_matriz["cliente_destino"] if info_matriz["cliente_destino"] else (incidencia_existente['CLIENTE_DESTINO'] if incidencia_existente is not None else "")
                    t_cliente_destino = st.text_input("CLIENTE / DESTINO", value=val_cd)
                    
                    val_pg = info_matriz["pedido_guia"] if info_matriz["pedido_guia"] else (incidencia_existente['PEDIDO_GUIA'] if incidencia_existente is not None else "")
                    t_pedido_guia = st.text_input("PEDIDO / GUÍA", value=val_pg)
                    
                    # Selector para asignar responsable del seguimiento
                    resp_actual = incidencia_existente['RESPONSABLE'] if incidencia_existente is not None else (nombre_usuario_actual if nombre_usuario_actual else "RIGOBERTO HERNÁNDEZ")
                    idx_resp = lista_colaboradores.index(resp_actual) if resp_actual in lista_colaboradores else 0
                    t_responsable = st.selectbox("ASIGNAR A (RESPONSABLE SEGUIMIENTO)", lista_colaboradores, index=idx_resp)
                    
                with f2_c2:
                    val_id_seg_default = incidencia_existente['ID_SEGUIMIENTO'] if incidencia_existente is not None else t_folio_input
                    t_id_seguimiento = st.text_input("ID SEGUIMIENTO", value=val_id_seg_default if val_id_seg_default else "")
                    
                    val_id_queja_default = incidencia_existente['ID_QUEJA'] if incidencia_existente is not None else t_folio_input
                    t_id_queja = st.text_input("ID DE QUEJA / REF", value=val_id_queja_default if val_id_queja_default else "")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                
                val_det = incidencia_existente['DETALLE_INCIDENCIA'] if incidencia_existente is not None else ""
                t_detalle = st.text_area("DETALLE / DESCRIPCIÓN DE LA TAREA O INCIDENCIA", value=val_det, key=f"area_detalle_{t_folio_input}")
                
                val_acc = incidencia_existente['ACCIONES'] if incidencia_existente is not None else ""
                t_acciones = st.text_area("ACCIONES / PASOS A SEGUIR", value=val_acc, key=f"area_acciones_{t_folio_input}")
                
                estatus_opciones = ["PENDIENTE", "EN PROCESO", "SOLUCIONADO", "RECHAZADO"]
                idx_estatus = estatus_opciones.index(incidencia_existente['ESTATUS']) if incidencia_existente is not None and incidencia_existente['ESTATUS'] in estatus_opciones else 0
                t_estatus = st.selectbox("Estatus", estatus_opciones, index=idx_estatus)
    
                st.markdown("<br>", unsafe_allow_html=True)
                texto_boton = ":material/sync: ACTUALIZAR REGISTRO" if incidencia_existente is not None else ":material/save: GUARDAR REGISTRO"
                enviar = st.form_submit_button(texto_boton, use_container_width=True)
                
                if enviar:
                    folio_final = t_folio_input if t_folio_input else sugerencia_folio
                    valor_busqueda = n_pedido if n_pedido else (incidencia_existente.get('VINCULO_BUSQUEDA', '') if incidencia_existente is not None else "")
                    busqueda_final = str(valor_busqueda).upper() if valor_busqueda is not None else ""
                    
                    # Si es edición mantiene el creador original, si es nuevo toma el nombre actual del usuario logueado
                    creador_final = incidencia_existente.get('CREADOR', '') if incidencia_existente is not None and str(incidencia_existente.get('CREADOR', '')).strip() != "" else (nombre_usuario_actual if nombre_usuario_actual else usuario_actual.upper())

                    nueva_data = {
                        "FOLIO": folio_final,
                        "TIPO": t_tipo,
                        "CREADOR": creador_final,
                        "RESPONSABLE": t_responsable,
                        "PRIORIDAD": t_prior,
                        "VINCULO_BUSQUEDA": busqueda_final, 
                        "CLIENTE_DESTINO": str(t_cliente_destino).upper(),
                        "PEDIDO_GUIA": str(t_pedido_guia).upper(),
                        "ID_SEGUIMIENTO": str(t_id_seguimiento).upper(),
                        "ID_QUEJA": str(t_id_queja).upper(),
                        "DETALLE_INCIDENCIA": t_detalle,
                        "ACCIONES": t_acciones,
                        "ESTATUS": t_estatus
                    }
                    
                    es_nuevo = incidencia_existente is None
                    ok, df_final, folio_usado = guardar_incidencia_github(
                        nueva_data, es_nuevo,
                        f"{'Nueva incidencia' if es_nuevo else 'Actualización de incidencia'} {folio_final}",
                    )
                    if ok:
                        st.session_state.df_incidencias = df_final
                        for k_txt in (f"area_detalle_{t_folio_input}", f"area_acciones_{t_folio_input}"):
                            st.session_state.pop(k_txt, None)   # borra rastro del formulario
                        texto_ok = "✅ ¡Guardado y asignado con éxito!"
                        if folio_usado != folio_final:
                            texto_ok += f" (El folio {folio_final} ya lo había tomado otra persona; se guardó como {folio_usado}.)"
                        st.session_state.msg_incidencias = ("ok", texto_ok)
                        st.rerun()
    
    # ── 2. MONITOR DE REGISTROS (GRID PROFESIONAL - ORDENADOS DE MÁS NUEVO A MÁS VIEJO) ──
    st.markdown("""
        <style>
        .card-hover {
            border: 1px solid #3d474d;
            border-left: 5px solid;
            transition: transform 0.2s, background-color 0.2s, border-color 0.3s !important;
        }
        .card-hover:hover {
            transform: scale(1.01);
            background-color: #313a40 !important;
            border: 1px solid #38bdf8 !important;
            border-left: 5px solid #38bdf8 !important;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)
    
    prioridad_colores = {"Urgente": "#ff4b4b", "Alta": "#f97316", "Media": "#38bdf8", "Baja": "#00FFAA"}
    estatus_colores = {"PENDIENTE": "#fbbf24", "EN PROCESO": "#60a5fa", "SOLUCIONADO": "#22c55e", "RECHAZADO": "#ef4444"}
    
    if df_master.empty:
        st.info("No hay registros guardados.")
    else:
        df_master_ordenado = df_master.iloc[::-1]

        for _, row in df_master_ordenado.iterrows():
            if not str(row.get("FOLIO", "")).strip(): continue
            
            color_p = prioridad_colores.get(row.get("PRIORIDAD", "Baja"), "#94a3b8")
            f_est = row.get('ESTATUS', 'PENDIENTE')
            color_e = estatus_colores.get(f_est, "#64748b")
            t_reg = row.get('TIPO', 'Incidencia')
            
            badge_tipo = f"<span style='background: #38bdf822; color: #38bdf8; padding: 1px 5px; border-radius: 3px; font-weight: bold; font-size: 0.65em; margin-right: 4px;'>{t_reg.upper()}</span>"
            
            st.markdown(f"""<div class="card-hover" style="border-left-color: {color_p}; padding: 12px; margin-bottom: 10px; background: #262e33; border-radius: 5px;"><div style="display: grid; grid-template-columns: 0.9fr 1.5fr 1.2fr 2fr 1.2fr; gap: 10px; align-items: center;"><div><div style="font-size: 0.65em; color: #888;">FOLIO / TIPO</div><div style="color: {color_p}; font-weight: bold; font-size: 1em;">{row.get('FOLIO', 'REG-???')}</div>{badge_tipo}<span style="background: {color_e}33; color: {color_e}; padding: 1px 4px; border-radius: 3px; font-weight: bold; font-size: 0.7em;">{f_est}</span></div><div><div style="font-size: 0.65em; color: #888;">CLIENTE / PEDIDO</div><div style="color: #fff; font-size: 0.9em; font-weight: bold;">{row.get('CLIENTE_DESTINO', 'N/A')}</div><div style="font-size: 0.8em; color: #bbb;">📦 {row.get('PEDIDO_GUIA', 'N/A')}</div></div><div><div style="font-size: 0.65em; color: #888;">ID SEGUIMIENTO / REF</div><div style="font-size: 0.85em; color: #eee;">{row.get('ID_SEGUIMIENTO', 'N/A')}</div><div style="font-size: 0.85em; color: #eee;">{row.get('ID_QUEJA', 'N/A')}</div></div><div><div style="font-size: 0.65em; color: #888;">DETALLE / ACCIONES</div><div style="font-size: 0.85em; color: #eee;">{row.get('DETALLE_INCIDENCIA', 'Sin detalle...')}</div><div style="font-size: 0.8em; color: #38bdf8;"><i>{row.get('ACCIONES', '')}</i></div></div><div style="text-align: right;"><div style="font-size: 0.65em; color: #888;">CREADOR / ASIGNADO A</div><div style="color: #fff; font-size: 0.8em; font-weight: bold;">🎯 {row.get('RESPONSABLE', 'N/A')}</div><div style="font-size: 0.7em; color: #38bdf8;">✍️ {row.get('CREADOR', row.get('USUARIO', 'N/A'))}</div></div></div></div>""", unsafe_allow_html=True)  
    
    # ── 3. EDITOR DE AVANZADO (EXCLUSIVO PARA ADMIN) ────────────────────────────────────
    if es_administrador:
        with st.expander("⚙️ Editor avanzado de registros", expanded=False):
            df_editor = df_master.copy()
            
            for col in COLUMNAS_INCIDENCIAS:
                if col not in df_editor.columns: df_editor[col] = ""
                df_editor[col] = df_editor[col].astype(str).replace("nan", "").fillna("")
                
            df_editado = st.data_editor(df_editor, hide_index=True, use_container_width=True, num_rows="dynamic")
            
            cabeceras = "".join([f"<th>{c}</th>" for c in COLUMNAS_INCIDENCIAS if c != 'VINCULO_BUSQUEDA'])
            cuerpo = ""
            for _, fila in df_editado.iterrows():
                cuerpo += "<tr>" + "".join([f"<td>{str(fila.get(c, ''))}</td>" for c in COLUMNAS_INCIDENCIAS if c != 'VINCULO_BUSQUEDA']) + "</tr>"
    
            html_print = f"""
            <div id="printableArea" style="font-family: sans-serif;">
                <h2>JYPESA - Logística NEXION</h2>
                <table border="1" style="width:100%; border-collapse: collapse;">
                    <thead><tr>{cabeceras}</tr></thead>
                    <tbody>{cuerpo}</tbody>
                </table>
            </div>
            """
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(":material/sync: SINCRONIZAR", use_container_width=True):
                    estado, df_resultado = guardar_tabla_completa(df_editado, df_master)
                    if estado == "OK":
                        st.session_state.df_incidencias = df_resultado
                        st.session_state.msg_incidencias = ("ok", "✅ Registros sincronizados con éxito en GitHub.")
                        st.rerun()
                    elif estado == "CONFLICTO":
                        st.session_state.df_incidencias = df_resultado
                        st.session_state.msg_incidencias = ("warn", "⚠️ Otra persona guardó cambios mientras editabas. Se recargó la versión más reciente; vuelve a hacer tus cambios para no pisar los de ella.")
                        st.rerun()
            with col2:
                import streamlit.components.v1 as components
                if st.button(":material/print: IMPRIMIR", use_container_width=True):
                    components.html(f"{html_print}<script>window.print();</script>", height=0, width=0)
            with col3:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_editado.to_excel(writer, index=False, sheet_name='Registros')
                st.download_button("BAJAR EXCEL", data=buffer.getvalue(), file_name="registros_nexion.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)  


if __name__ == "__main__":
    main()
