import base64
from datetime import datetime, timedelta
import io
import re
import time
import unicodedata
import requests
import pandas as pd
import streamlit as st
import pytz

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Logistics - Envíos Nacionales",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO Y PERMISOS
# ============================================================
render_layout(modulo_actual="ENTREGAS", submodulo_actual="NACIONAL")

def verificar_permiso_modulo(modulo, submodulo=None):
    permisos = st.session_state.get("permisos", {})
    if st.session_state.get("usuario_activo", "").upper() == "RIGOBERTO":
        return True
        
    if not permisos.get(modulo.upper(), False) or (submodulo and not permisos.get(submodulo.upper(), False)):
        st.markdown(
            f"""
            <div style="
                background: #2B343B; 
                border: 1px solid #4B5D67; 
                border-left: 5px solid #FFD700; 
                padding: 20px 25px; 
                border-radius: 8px; 
                width: 100%; 
                font-family: 'Inter', sans-serif; 
                color: white; 
                box-sizing: border-box; 
                margin-top: 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                    <div style="width: 10px; height: 10px; background: #FFD700; border-radius: 50%; box-shadow: 0 0 8px #FFD700;"></div>
                    <span style="color: #FFD700; font-size: 13px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">
                        ACCESS RESTRICTED // MÓDULO NO AUTORIZADO
                    </span>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 600; padding-left: 20px;">
                    No tienes permisos para acceder a esta sección.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

verificar_permiso_modulo("ENTREGAS", "NACIONAL")


# ============================================================
# 3. FUNCIONES MAESTRAS DE SOPORTE Y DATOS
# ============================================================
@st.cache_data(ttl=60)
def cargar_datos_dashboard():
    t = int(time.time())
    url = f"https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/Matriz_Excel_Dashboard.csv?v={t}"
    try:
        df = pd.read_csv(url, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return None


# ============================================================
# 4. INTERFAZ PRINCIPAL Y RENDER DE ENVÍOS (CON FILTROS Y DESCARGA SIN GUÍA)
# ============================================================
def render_envios_flow_responsive(data):
    sorted_data = sorted(data, key=lambda x: str(x['factura']), reverse=True)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #384A52; color: #e2e8f0; margin: 0; padding: 5px; width: 100%; }}
            ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
            ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
            ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; }}
            ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
            .list-row {{ background-color: #263238; border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.2s ease; margin-bottom: 6px; border-radius: 8px; overflow: hidden; width: 100%; }}
            .list-row:hover {{ background-color: #2c3b42; border-color: rgba(56, 189, 248, 0.3); }}
            .label-mini {{ font-size: 8px; text-transform: uppercase; font-weight: 800; color: #BFBFBF; letter-spacing: 0.5px; margin-bottom: 2px; }}
            
            .table-scroll-container {{
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }}

            .grid-envios {{
                display: grid;
                grid-template-columns: 70px 160px 140px 140px minmax(140px, 1fr) 160px 140px 140px;
                gap: 10px;
                align-items: center;
                min-width: 860px;
                padding: 10px 14px;
            }}
        </style>
    </head>
    <body>
        <div class="w-full space-y-1">
            {"".join([f'''
            <div class="list-row flex items-stretch">
                <div class="w-2 shrink-0 {("bg-emerald-500" if item['estatus'] in ["EN TIEMPO", "ENVIADA EN TIEMPO", "ENVIADA EN ESPERA DE GUÍA"] or (item['estatus'] == "ENVIADA") else ("bg-red-500" if "RETRASO" in item['estatus'] else "bg-amber-500"))} shadow-[2px_0_10px_rgba(0,0,0,0.3)]"></div>
                
                <div class="table-scroll-container">
                    <div class="grid-envios flex-1">
                        
                        <!-- FACTURA -->
                        <div>
                            <div class="label-mini">Factura</div>
                            <div class="text-xs font-black text-white italic tracking-tighter">{item['factura']}</div>
                        </div>

                        <!-- RECOLECCIÓN -->
                        <div>
                            <div class="label-mini">Recolección</div>
                            <div class="text-[10px] text-sky-400 font-bold uppercase truncate">{item['recomendacion']}</div>
                        </div>

                        <!-- NO GUÍA -->
                        <div>
                            <div class="label-mini">No. Guía</div>
                            <div class="text-[10px] font-mono font-bold text-amber-300 truncate">{item['numero_guia'] if item['numero_guia'] else 'PENDIENTE'}</div>
                        </div>
                        
                        <!-- FECHA PROGRAMACIÓN -->
                        <div>
                            <div class="label-mini">F. Programación</div>
                            <div class="text-[10px] font-bold text-slate-300 truncate">{item['fecha_programacion'] if item['fecha_programacion'] else 'N/A'}</div>
                        </div>
                        
                        <!-- CLIENTE -->
                        <div class="min-w-0">
                            <div class="label-mini">Cliente</div>
                            <div class="text-[11px] font-semibold text-sky-200 truncate">
                                {(item['nombre_extran'] if str(item['nombre_extran']).strip() else item['nombre_cliente'])}
                            </div>
                        </div>

                        <!-- DESTINO -->
                        <div class="border-l border-white/5 pl-2">
                            <div class="label-mini">Destino</div>
                            <div class="text-[10px] font-bold text-white truncate">{item['destino']}</div>
                        </div>

                        <!-- FECHA DE ENVÍO -->
                        <div class="border-l border-white/5 pl-2">
                            <div class="label-mini">Fecha Envío</div>
                            <div class="text-[10px] font-bold text-sky-400">{item['fecha_envio'] if item['fecha_envio'] and item['fecha_envio'] != 'nan' else 'SIN ENVIAR'}</div>
                        </div>

                        <!-- ESTATUS -->
                        <div class="border-l border-white/5 pl-2">
                            <div class="label-mini">Estatus</div>
                            <div class="text-[9px] font-black uppercase {("text-emerald-400" if item['estatus'] in ["EN TIEMPO", "ENVIADA EN TIEMPO", "ENVIADA EN ESPERA DE GUÍA"] or (item['estatus'] == "ENVIADA") else ("text-red-400" if "RETRASO" in item['estatus'] else "text-amber-400"))} tracking-tighter">
                                {item['estatus']}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
            ''' for item in sorted_data])}
        </div>
    </body>
    </html>
    """
    return components.html(html_content, height=800, scrolling=True)


def main():    
    if "animacion_cargada" not in st.session_state:
        time.sleep(0.08)
        st.session_state.animacion_cargada = True
    
    usuario_actual = st.session_state.get("usuario_activo", "").upper()
    es_admin = usuario_actual == "RIGOBERTO"

    if es_admin:
        with st.expander("🔐 Panel de Seguridad / Modo Edición Admin", expanded=False):
            st.markdown(
                """
                <div style='background: rgba(0, 255, 170, 0.08); border: 1px solid #00FFAA; border-left: 5px solid #00FFAA; padding: 12px 18px; border-radius: 6px; margin-bottom: 15px; font-family: "Inter", sans-serif; color: white;'>
                    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 2px;'>
                        <div style='width: 7px; height: 7px; background: #00FFAA; border-radius: 50%; box-shadow: 0 0 8px #00FFAA;'></div>
                        <span style='font-size: 10px; font-weight: 800; color: #00FFAA; letter-spacing: 1.5px; text-transform: uppercase;'>ACCESS GRANTED // NIVEL 5 (ROOT)</span>
                    </div>
                    <div style='font-size: 11px; color: rgba(255,255,255,0.85); font-weight: 600; margin-left: 15px;'>
                        Administrador Reconocido. Credenciales de seguridad validadas en el sistema central.
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            modo_edicion = st.checkbox(
                "Activar Modo Edición de Envíos en Pantalla",
                value=False,
                key="check_modo_edicion_envios_session",
            )
    else:
        modo_edicion = False

    # ── TÍTULO Y BOTÓN DE ACTUALIZACIÓN ────────────────────────
    col_titulo, col_btn_refrescar = st.columns([4, 1.2], vertical_alignment="center")
    with col_titulo:
        st.markdown("""
            <div style='text-align:left; margin-top:15px; margin-bottom:10px;'>
                <span style='color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;'>
                    PANEL DE CONTROL DE ENVÍOS
                </span>
            </div>
        """, unsafe_allow_html=True)
    with col_btn_refrescar:
        if st.button("ACTUALIZAR DATOS", key="btn_refrescar_datos_envios", use_container_width=True):
            st.cache_data.clear()
            st.session_state["editor_version"] = st.session_state.get("editor_version", 1) + 1
            st.session_state.pop("df_envios_cache_v", None)
            st.rerun()

    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "envios.csv"
    
    current_t = int(time.time() * 1000)
    CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}?_t={current_t}"

    def get_github_data():
        headers = {
            "Authorization": f"token {TOKEN}" if TOKEN else "",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        headers = {k: v for k, v in headers.items() if v}
        
        response = requests.get(CSV_URL, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
        else:
            st.error(f"Hubo un error al cargar los datos: {response.status_code}")
            return pd.DataFrame()

    def guardar_cambios_github(df_nuevo):
        headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
        api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
        
        r_get = requests.get(api_url, headers=headers)
        if r_get.status_code != 200:
            st.error("No se pudo obtener el identificador actual del archivo en GitHub.")
            return False
        sha_actual = r_get.json().get("sha")
        
        csv_buffer = io.StringIO()
        df_nuevo.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        content_encoded = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        
        payload = {
            "message": "Actualización automática de envíos desde panel admin seguro de Rigoberto",
            "content": content_encoded,
            "sha": sha_actual
        }
        
        r_put = requests.put(api_url, json=payload, headers=headers)
        if r_put.status_code in [200, 201]:
            st.success("¡Envíos guardados en GitHub con éxito, mi amor! 🚀")
            st.cache_data.clear()
            st.session_state["editor_version"] = st.session_state.get("editor_version", 1) + 1
            return True
        else:
            st.error(f"Error al guardar en GitHub: {r_put.json().get('message', 'Desconocido')}")
            return False

    df_raw = get_github_data()

    df_dashboard_global = cargar_datos_dashboard()
    df_t1_global = pd.DataFrame()
    try:
        df_t1_global = pd.read_excel("T1.xlsx")
        df_t1_global.columns = df_t1_global.columns.str.strip().str.upper()
    except Exception:
        pass

    if not df_raw.empty:
        df_raw.columns = df_raw.columns.str.strip()

        if modo_edicion:
            st.markdown(
                f"""
                <div style='background: rgba(234, 179, 8, 0.08); border: 1px solid #eab308; border-left: 5px solid #eab308; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; font-family: "Inter", sans-serif; color: white;'>
                    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 4px;'>
                        <div style='width: 8px; height: 8px; background: #eab308; border-radius: 50%; box-shadow: 0 0 8px #eab308;'></div>
                        <span style='font-size: 11px; font-weight: 800; color: #eab308; letter-spacing: 1.5px; text-transform: uppercase;'>NEXION SECURITY // MODO EDICIÓN ACTIVO</span>
                    </div>
                    <div style='font-size: 12px; color: rgba(255,255,255,0.8); font-weight: 500; margin-left: 18px;'>
                        Modifica los registros en la matriz inferior y ejecuta la sincronización para actualizar la base remota de forma segura.
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            editor_key = f"editor_envios_admin_session_{st.session_state.get('editor_version', 1)}"

            df_editado = st.data_editor(
                df_raw,
                use_container_width=True,
                num_rows="dynamic",
                key=editor_key,
            )

            if st.button(
                ":material/save: Guardar Cambios en GitHub", key="btn_guardar_github_envios_session"
            ):
                if guardar_cambios_github(df_editado):
                    st.rerun()
            st.markdown("---")

        df_envios = pd.DataFrame()
        df_envios['factura'] = df_raw.get('Factura', pd.Series(dtype=str)).fillna('').astype(str)
        df_envios['recomendacion'] = df_raw.get('RECOMENDACION', pd.Series(dtype=str)).fillna('').astype(str)
        df_envios['nombre_cliente'] = df_raw.get('Nombre_Cliente', pd.Series(dtype=str)).fillna('').astype(str)
        df_envios['nombre_extran'] = df_raw.get('Nombre_Extran', pd.Series(dtype=str)).fillna('').astype(str)
        
        def limpiar_destino_largo(val):
            v_str = str(val).strip()
            if not v_str or v_str.lower() in ['nan', '0', 'none']:
                return "NACIONAL"
            if len(v_str) > 25:
                partes = [p.strip() for p in v_str.split(',')]
                if len(partes) >= 2:
                    return f"{partes[-2]} / {partes[-1]}" if len(partes[-2]) < 15 else partes[-1]
                return v_str[:25] + "..."
            return v_str

        df_envios['destino'] = df_raw.get('DESTINO', pd.Series(dtype=str)).apply(limpiar_destino_largo)
        
        f_prog_input = df_raw.get('FECHA DE PROGRAMACION', pd.Series(dtype=str)).fillna('').astype(str).str.strip()
        dt_prog_temp = pd.to_datetime(f_prog_input, errors='coerce', dayfirst=True)
        df_envios['fecha_programacion'] = dt_prog_temp.dt.strftime('%d/%m/%Y').fillna(f_prog_input)

        lista_guias = []
        lista_fechas_envio = []
        
        f_env_raw_list = df_raw.get('FECHA DE ENVIO', pd.Series(dtype=str)).fillna('').astype(str).str.strip()

        for idx, row in df_raw.iterrows():
            fac = str(row.get('Factura', '')).strip()
            guia_encontrada = ""
            fecha_envio_encontrada = ""
            
            for col_g in ['NÚMERO DE GUÍA', 'NUMERO DE GUIA', 'GUIA', 'TALON']:
                if col_g in df_raw.columns and pd.notna(row.get(col_g)):
                    val_g = str(row.get(col_g)).strip()
                    if val_g and val_g not in ['', 'nan', '0', '0.0']:
                        guia_encontrada = val_g
                        break
            
            if not guia_encontrada and df_dashboard_global is not None and not df_dashboard_global.empty:
                for col_ped in ['NÚMERO DE PEDIDO', 'PEDIDO', 'FACTURA']:
                    if col_ped in df_dashboard_global.columns:
                        match_dash = df_dashboard_global[df_dashboard_global[col_ped].astype(str).str.strip() == fac]
                        if not match_dash.empty:
                            for cg_dash in ['NÚMERO DE GUÍA', 'NUMERO DE GUIA', 'GUIA']:
                                if cg_dash in match_dash.columns:
                                    vg = str(match_dash.iloc[0][cg_dash]).strip()
                                    if vg and vg not in ['', 'nan', '0', '0.0']:
                                        guia_encontrada = vg
                                        break
                        if guia_encontrada:
                            break

            encontrado_en_t1 = False
            if not df_t1_global.empty:
                for col_t1_ped in ['OBSERVACION 1', 'PEDIDO', 'FACTURA']:
                    if col_t1_ped in df_t1_global.columns:
                        match_t1 = df_t1_global[df_t1_global[col_t1_ped].astype(str).str.strip() == fac]
                        if not match_t1.empty:
                            for cg_t1 in ['TALON', 'GUIA', 'NÚMERO DE GUÍA']:
                                if cg_t1 in match_t1.columns:
                                    vg = str(match_t1.iloc[0][cg_t1]).strip()
                                    if vg and vg not in ['', 'nan', '0', '0.0']:
                                        guia_encontrada = vg
                                        encontrado_en_t1 = True
                                        break
                            
                            if encontrado_en_t1:
                                for col_fdoc in ['F.DOC', 'FECHA', 'FECHA DOC']:
                                    if col_fdoc in match_t1.columns:
                                        fdoc_val = str(match_t1.iloc[0][col_fdoc]).strip()
                                        if fdoc_val and fdoc_val not in ['', 'nan', '0', '0.0']:
                                            dt_parsed_fdoc = pd.to_datetime(fdoc_val, errors='coerce', dayfirst=True)
                                            fecha_envio_encontrada = dt_parsed_fdoc.strftime('%d/%m/%Y') if pd.notnull(dt_parsed_fdoc) else fdoc_val
                                            break
                                break
                        if guia_encontrada:
                            break

            if encontrado_en_t1 and fecha_envio_encontrada:
                final_fecha_envio = fecha_envio_encontrada
            else:
                orig_fe = str(f_env_raw_list.iloc[idx]).strip()
                final_fecha_envio = orig_fe

            lista_guias.append(guia_encontrada)
            lista_fechas_envio.append(final_fecha_envio)

        df_envios['numero_guia'] = lista_guias
        df_envios['fecha_envio_raw'] = lista_fechas_envio

        dt_envio_temp = pd.to_datetime(df_envios['fecha_envio_raw'], errors='coerce', dayfirst=True)
        df_envios['fecha_envio'] = dt_envio_temp.dt.strftime('%d/%m/%Y').fillna(df_envios['fecha_envio_raw'])
        
        df_envios['dt_prog_parsed'] = dt_prog_temp
        df_envios['dt_envio_parsed'] = dt_envio_temp

        tz_gdl = pytz.timezone("America/Mexico_City")
        ahora_gdl = datetime.now(tz_gdl).replace(tzinfo=None)
        hoy_gdl = ahora_gdl.date()
        
        valores_nulos_fecha = ['', 'nan', '0', '0.0', '-', 'nat', 'none']
        
        estatus_calculado = []
        for f_prog, f_env, guia_val in zip(f_prog_input, lista_fechas_envio, lista_guias):
            fp_str = str(f_prog).strip()
            fe_str = str(f_env).strip()
            g_str = str(guia_val).strip()
            
            tiene_g = g_str and g_str.lower() not in valores_nulos_fecha
            tiene_fe = fe_str.lower() not in valores_nulos_fecha
            
            if tiene_g and not tiene_fe and fp_str and fp_str.lower() not in valores_nulos_fecha:
                fe_str = fp_str
                tiene_fe = True

            dt_prog = pd.to_datetime(fp_str, dayfirst=True, errors='coerce')
            dt_env = pd.to_datetime(fe_str, dayfirst=True, errors='coerce')
            
            tarde = False
            if pd.notna(dt_prog):
                limite_24h = dt_prog + timedelta(hours=24)
                fecha_prog_date = dt_prog.date()
                
                if tiene_fe and pd.notna(dt_env) and dt_env > limite_24h:
                    tarde = True
                elif not tiene_fe and not tiene_g and ahora_gdl > limite_24h:
                    tarde = True
            else:
                fecha_prog_date = None

            if tiene_g and tiene_fe:
                estatus_calculado.append("ENVIADA CON RETRASO" if tarde else "ENVIADA EN TIEMPO")
            elif not tiene_g and tiene_fe:
                estatus_calculado.append("ENVIADA")
            elif tiene_g and not tiene_fe:
                estatus_calculado.append("ENVIADA CON RETRASO" if tarde else "ENVIADA EN TIEMPO")
            else:
                if fecha_prog_date is not None and fecha_prog_date > hoy_gdl:
                    estatus_calculado.append("SURTIENDO")
                else:
                    estatus_calculado.append("RETRASO" if tarde else "SURTIENDO")
                    
        df_envios['estatus'] = estatus_calculado
        df_envios = df_envios.replace(r'(?i)^nan$', '', regex=True)
        df_envios = df_envios.sort_values(by='factura', ascending=True, ignore_index=True)

        # ── BÚNKER DE FILTROS TÁCTICOS ──
        f1, f2, f3, f4, f5 = st.columns(5)

        with f1:
            filtro_fprog = st.date_input("FECHA PROGRAMACIÓN", value=None, key="calendario_fprog_envios")

        with f2:
            filtro_fenvio = st.date_input("FECHA DE ENVÍO", value=None, key="calendario_fenv_envios")

        with f3:
            facturas_opts = ["TODAS"] + sorted(list(df_envios['factura'].loc[df_envios['factura'] != ''].unique()))
            filtro_factura = st.selectbox("FACTURA", facturas_opts, key="filtro_factura_envios")

        with f4:
            paq_opts = ["TODAS"] + sorted(list(df_envios['recomendacion'].loc[df_envios['recomendacion'] != ''].unique()))
            filtro_paqueteria = st.selectbox("PAQUETERÍA", paq_opts, key="filtro_paqueteria_envios")

        with f5:
            estatus_opts = ["TODOS"] + sorted(list(df_envios['estatus'].loc[df_envios['estatus'] != ''].unique()))
            filtro_estatus = st.selectbox("ESTATUS", estatus_opts, key="filtro_estatus_envios")

        df_filtrado = df_envios.copy()

        if filtro_fprog is not None:
            df_filtrado = df_filtrado[df_filtrado['dt_prog_parsed'].dt.date == filtro_fprog]

        if filtro_fenvio is not None:
            df_filtrado = df_filtrado[df_filtrado['dt_envio_parsed'].dt.date == filtro_fenvio]

        if filtro_factura != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['factura'] == filtro_factura]

        if filtro_paqueteria != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['recomendacion'] == filtro_paqueteria]

        if filtro_estatus != "TODOS":
            df_filtrado = df_filtrado[df_filtrado['estatus'] == filtro_estatus]

        # ── BLOQUE EXCLUSIVO PARA RIGOBERTO: FILTRO Y DESCARGA SIN GUÍA ──
        if es_admin:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            col_switch_sin_guia, col_btn_descarga = st.columns([2.5, 1.5], vertical_alignment="center")
            
            with col_switch_sin_guia:
                solo_sin_guia = st.toggle("🔍 Filtrar únicamente registros pendientes sin número de guía", value=False, key="toggle_solo_sin_guia_admin")
            
            if solo_sin_guia:
                mask_sin_guia = df_filtrado['numero_guia'].astype(str).str.strip().isin(['', 'nan', '0', '0.0', 'PENDIENTE'])
                df_filtrado = df_filtrado[mask_sin_guia]

            with col_btn_descarga:
                df_excel_export = df_filtrado.drop(columns=['dt_prog_parsed', 'dt_envio_parsed'], errors='ignore')
                
                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
                    df_excel_export.to_excel(writer, index=False, sheet_name='Envios_Seguimiento')
                excel_data = output_buffer.getvalue()

                st.download_button(
                    label="📥 Descargar Reporte en Excel",
                    data=excel_data,
                    file_name=f"seguimiento_envios_sin_guia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="btn_download_excel_sin_guia"
                )

        data_completa = df_filtrado.to_dict('records')
    else:
        data_completa = []

    render_envios_flow_responsive(data_completa)
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

# ── FOOTER FIJO ────────────────────────
st.markdown(
    f"""
    <div class="footer">
        NEXION // SUPPLY CHAIN INTELLIGENCE // GDL HUB // © 2026 <br>
        <span style="opacity:0.5; font-size:8px; letter-spacing:4px;">ENGINEERED BY</span>
        <span style="color:{vars_css['text']}; font-weight:500; letter-spacing:3px;">RIGOBERTO HERNANDEZ</span>
    </div>
""",
    unsafe_allow_html=True,
)
