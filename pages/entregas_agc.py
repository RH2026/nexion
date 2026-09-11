import base64
from datetime import datetime, timedelta
import io
import time
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
import streamlit.components.v1 as components
import streamlit as st

from components.layout import render_layout

# ============================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="JYPESA | Logistics - Entregas AGC",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. LLAMADA AL LAYOUT MAESTRO Y PERMISOS
# ============================================================
render_layout(modulo_actual="ENTREGAS", submodulo_actual="AGC")

# Verificación de seguridad específica del módulo
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

verificar_permiso_modulo("ENTREGAS", "AGC")


# ============================================================
# 3. INTERFAZ PRINCIPAL (ENTREGAS AGC)
# ============================================================
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
                "Activar Modo Edición de Citas en Pantalla",
                value=False,
                key="check_modo_edicion_session",
            )
    else:
        modo_edicion = False

    if 'tipo_vista_agc' not in st.session_state:
        st.session_state.tipo_vista_agc = 'ENTREGAS'

    if 'fecha_calendario_ref' not in st.session_state:
        st.session_state.fecha_calendario_ref = datetime.now()

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        btn_type_1 = "primary" if st.session_state.tipo_vista_agc == 'ENTREGAS' else "secondary"
        if st.button("VISTA DE ENTREGAS", use_container_width=True, type=btn_type_1):
            st.session_state.tipo_vista_agc = 'ENTREGAS'
            st.rerun()

    with col_btn2:
        btn_type_2 = "primary" if st.session_state.tipo_vista_agc == 'CALENDARIO' else "secondary"
        if st.button("VISTA CALENDARIO GLOBAL", use_container_width=True, type=btn_type_2):
            st.session_state.tipo_vista_agc = 'CALENDARIO'
            st.rerun()

    titulo_dinamico = "PANEL DE ENTREGAS PENDIENTES (AGC)" if st.session_state.tipo_vista_agc == 'ENTREGAS' else "CALENDARIO DE ENTREGAS GLOBAL"

    st.markdown(f"""
        <div style='text-align:center; margin-top:25px; margin-bottom:20px;'>
            <span style='color:#FFFFFF; font-weight:400; font-size:12px; letter-spacing:3px;'>
                {titulo_dinamico}
            </span>
        </div>
    """, unsafe_allow_html=True)

    def render_logistica_flow_responsive(data):
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
            <style>
                body {{ 
                    font-family: 'Inter', sans-serif; 
                    background-color: #384A52; 
                    color: #e2e8f0; 
                    margin: 0;
                    padding: 5px;
                    width: 100%;
                }}
                ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
                ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.1); border-radius: 10px; }}
                ::-webkit-scrollbar-thumb {{ background: #3498db; border-radius: 10px; border: 2px solid #384A52; }}
                ::-webkit-scrollbar-thumb:hover {{ background: #2ecc71; }}
                .list-row {{
                    background-color: #263238;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    transition: all 0.2s ease;
                    margin-bottom: 8px;
                    border-radius: 10px;
                    overflow: hidden;
                    width: 100%;
                }}
                .list-row:hover {{
                    background-color: #2c3b42;
                    border-color: rgba(56, 189, 248, 0.3);
                }}
                .label-mini {{
                    font-size: 9px;
                    text-transform: uppercase;
                    font-weight: 800;
                    color: #BFBFBF;
                    letter-spacing: 0.5px;
                }}
            </style>
        </head>
        <body>
            <div class="w-full space-y-2">
                {"".join([f'''
                <div class="list-row flex items-stretch">
                    <div class="w-2 shrink-0 {"bg-emerald-500" if item['estatus'] == "ENTREGADA" else "bg-amber-500"} shadow-[2px_0_10px_rgba(0,0,0,0.3)]"></div>
                    <div class="flex flex-col md:flex-row flex-1 p-3 items-start md:items-center justify-between gap-4">
                        
                        <div class="w-full md:w-44 shrink-0">
                            <div class="label-mini">{item['semana']}</div>
                            <div class="text-sm font-black text-white italic tracking-tighter leading-none min-h-[20px]">
                                {item['oc']}
                            </div>
                            <div class="text-[12px] text-sky-400 font-bold mt-1">
                                ITEM: {item['item_no']}
                            </div>
                        </div>
                        
                        <div class="w-full md:flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                            <div>
                                <div class="label-mini">Fecha Compromiso</div>
                                <div class="text-xs text-slate-300 italic truncate min-h-[16px]">
                                    {item['entrega_texto']}
                                </div>
                            </div>
                            <div>
                                <div class="label-mini">Producto</div>
                                <div class="text-xs font-semibold text-sky-200 truncate min-h-[16px]">
                                    {item['producto']}
                                </div>
                            </div>
                        </div>

                        <div class="w-full md:w-[420px] shrink-0 flex gap-4 py-2 md:py-0 border-y md:border-y-0 md:border-x border-white/5 md:px-8">
                            <div class="w-3/5 shrink-0">
                                <div class="label-mini">Cita</div>
                                <div class="text-sm font-mono font-bold min-h-[20px] truncate {"text-slate-500" if "PENDIENTE" in str(item['cita']).upper() else "text-amber-300"}">
                                    {item['cita']}
                                </div>
                            </div>
                            <div class="w-2/5 shrink-0">
                                <div class="label-mini">Tarimas</div>
                                <div class="text-sm font-bold text-white min-h-[20px] truncate">
                                    {item['tarimas_num']} Tarimas
                                </div>
                            </div>
                        </div>

                        <div class="w-full md:w-40 flex justify-between md:block text-right shrink-0">
                            <div class="label-mini md:mb-1">Tipo / Estatus</div>
                            <div class="text-[10px] font-bold text-emerald-300 uppercase">{item['tipo']}</div>
                            <div class="text-[11px] font-black uppercase {"text-emerald-400" if item['estatus'] == "ENTREGADA" else "text-orange-400"} tracking-tighter min-h-[16px]">
                                {item['estatus']}
                            </div>
                        </div>

                    </div>
                </div>
                ''' for item in data])}
            </div>
        </body>
        </html>
        """
        return components.html(html_content, height=800, scrolling=True)

    def generar_pdf_citas_mes(data_completa, mes_num, anio=2026):
        meses_nombres = {
            1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
            7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
        }
        nombre_mes = meses_nombres.get(mes_num, "MES")

        citas_filtradas = []
        for item in data_completa:
            if item.get('estatus') == 'ENTREGADA':
                continue
            try:
                fecha_str = str(item['cita']).split(" - ")[0].strip()
                dt = datetime.strptime(fecha_str, "%d/%m/%m" if len(fecha_str.split('/')[2])==2 else "%d/%m/%Y")
                if dt.month == mes_num and dt.year == anio:
                    citas_filtradas.append(item)
            except:
                pass

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        pdf.setFillColorRGB(0.21, 0.28, 0.32)
        pdf.rect(0, height - 80, width, 80, fill=1, stroke=0)
        
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, height - 35, "JYPESA | REPORTE DE CITAS AGC PENDIENTES")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, height - 55, f"PERIODO: {nombre_mes} {anio} — NEXION SUPPLY CHAIN INTELLIGENCE")

        y = height - 120
        pdf.setFillColorRGB(0.1, 0.1, 0.1)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(40, y, "FECHA / CITA")
        pdf.drawString(160, y, "OC / PEDIDO")
        pdf.drawString(250, y, "UNIDAD")
        pdf.drawString(330, y, "TARIMAS")
        pdf.drawString(400, y, "PRODUCTO")
        
        y -= 8
        pdf.setStrokeColorRGB(0.7, 0.7, 0.7)
        pdf.line(40, y, width - 40, y)
        y -= 20

        pdf.setFont("Helvetica", 8)
        for item in citas_filtradas:
            if y < 50:
                pdf.showPage()
                y = height - 50
            
            pdf.drawString(40, y, str(item.get('cita', ''))[:30])
            pdf.drawString(160, y, str(item.get('oc', ''))[:15])
            pdf.drawString(250, y, str(item.get('tipo', ''))[:12])
            pdf.drawString(330, y, str(item.get('tarimas_num', '0'))[:8] + " Tarimas")
            pdf.drawString(400, y, str(item.get('producto', ''))[:25])
            y -= 18

        if not citas_filtradas:
            pdf.setFont("Helvetica-Oblique", 10)
            pdf.drawString(40, y, "No hay citas pendientes registradas para este mes.")

        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()

    def render_calendario_semanal_por_horas(data_completa, fecha_ref):
        lunes = fecha_ref - timedelta(days=fecha_ref.weekday())
        dias_semana = [lunes + timedelta(days=i) for i in range(7)]

        eventos_map = {}
        horas_detectadas = set()

        for item in data_completa:
            if item.get('estatus') == 'ENTREGADA':
                continue
            try:
                cita_raw = str(item['cita'])
                partes = [p.strip() for p in cita_raw.split("-")]
                if len(partes) >= 2:
                    fecha_str = partes[0]
                    hora_str = partes[1].upper()
                    
                    dt_cita = None
                    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d/%m/%m"):
                        try:
                            dt_cita = datetime.strptime(fecha_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not dt_cita:
                        continue

                    f_key = dt_cita.strftime("%Y-%m-%d")
                    
                    h_clean = hora_str.replace("A. M.", "AM").replace("P. M.", "PM").strip()
                    if len(h_clean) > 8:
                        h_clean = h_clean[:8]

                    horas_detectadas.add(h_clean)

                    if f_key not in eventos_map:
                        eventos_map[f_key] = {}
                    if h_clean not in eventos_map[f_key]:
                        eventos_map[f_key][h_clean] = []
                    
                    oc_txt = str(item.get('oc', ''))
                    producto_txt = str(item.get('producto', ''))
                    
                    tarima_val = str(item.get('tarimas_num', '0'))
                    if not tarima_val or tarima_val in ['0', 'nan', '0.0']:
                        try:
                            cant_raw = str(item.get('cantidad', ''))
                            if "TARIMAS" in cant_raw:
                                tarima_val = cant_raw.split("TARIMAS")[0].split("/")[-1].strip()
                        except:
                            tarima_val = "0"
                    
                    detalle_html = f"<div class='mb-1 font-bold text-amber-300'>{oc_txt} | {tarima_val} Tarimas</div><div class='text-xs text-slate-200 font-semibold'>{producto_txt}</div>"
                    eventos_map[f_key][h_clean].append(detalle_html)
            except Exception:
                pass

        horas_fijas = sorted(list(horas_detectadas)) if horas_detectadas else ["08:00", "11:00", "15:00"]
        
        nombres_dias_es = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
        columnas_html = "<th class='p-3 text-left text-xs font-black uppercase text-slate-400 border-b border-white/10 bg-[#212c31] sticky left-0 z-10'>Hora</th>"
        for i, d in enumerate(dias_semana):
            label_d = f"{d.strftime('%d')}-{nombres_dias_es[i]}"
            columnas_html += f"<th class='p-3 text-center text-xs font-black uppercase text-slate-300 border-b border-white/10 bg-[#212c31]'>{label_d}</th>"

        filas_html = ""
        for h in horas_fijas:
            filas_html += f"<tr><td class='p-3 font-mono font-bold text-xs text-sky-400 border-b border-white/5 bg-[#263238] sticky left-0'>{h}</td>"
            for d in dias_semana:
                f_key = d.strftime("%Y-%m-%d")
                contenido_celda = "—"
                if f_key in eventos_map and h in eventos_map[f_key]:
                    items_hora = eventos_map[f_key][h]
                    contenido_celda = "<hr style='border-color:rgba(255,255,255,0.1); margin:4px 0;'>".join(items_hora)
                
                filas_html += f"<td class='p-3 text-center text-xs border-b border-white/5 bg-[#1a2327] align-top'>{contenido_celda}</td>"
            filas_html += "</tr>"
        
        html_calendario = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Inter', sans-serif; background-color: #384A52; color: #e2e8f0; margin:0; padding:0; width: 100%; }}
                ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
                ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 4px; }}
            </style>
        </head>
        <body class="p-0">
            <div class="w-full bg-[#1e272c] rounded-xl border border-white/10 shadow-2xl overflow-hidden">
                <div class="bg-[#263238] px-6 py-4 border-b border-white/10 flex justify-between items-center">
                    <h2 class="text-xl font-black text-white tracking-widest italic">SEMANA ACTIVA <span style="color: #34D399;" class="font-light">({dias_semana[0].strftime('%d/%m/%Y')} al {dias_semana[-1].strftime('%d/%m/%Y')})</span></h2>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full border-collapse">
                        <thead>
                            <tr>{columnas_html}</tr>
                        </thead>
                        <tbody>
                            {filas_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        return components.html(html_calendario, height=550, scrolling=True)

    TOKEN = st.secrets.get("GITHUB_TOKEN", None)
    REPO_NAME = "RH2026/nexion"
    FILE_PATH = "agc.csv"
    CSV_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH}"

    def get_github_data():
        headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
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
            "message": "Actualización automática de citas desde panel admin seguro de Rigoberto",
            "content": content_encoded,
            "sha": sha_actual
        }
        
        r_put = requests.put(api_url, json=payload, headers=headers)
        if r_put.status_code in [200, 201]:
            st.success("¡Citas y cambios guardados en GitHub con éxito, mi amor! 🚀")
            st.cache_data.clear()
            return True
        else:
            st.error(f"Error al guardar en GitHub: {r_put.json().get('message', 'Desconocido')}")
            return False

    df_raw = get_github_data()

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

            df_editado = st.data_editor(
                df_raw,
                use_container_width=True,
                num_rows="dynamic",
                key="editor_agc_admin_session",
            )

            if st.button(
                "Guardar Cambios en GitHub", key="btn_guardar_github_session"
            ):
                if guardar_cambios_github(df_editado):
                    st.rerun()
            st.markdown("---")

        num_rows = len(df_raw)
        df_entregas = pd.DataFrame(index=range(num_rows))
        
        df_entregas['oc'] = df_raw.get('PO Customer', pd.Series(['']*num_rows)).fillna('').astype(str).values
        df_entregas['item_no'] = df_raw.get('Item No.', pd.Series(['']*num_rows)).fillna('').astype(str).values
        df_entregas['producto'] = df_raw.get('PRODUCTO', pd.Series(['']*num_rows)).fillna('').astype(str).values
        
        cajas = df_raw.get('Cajas a Entregar', pd.Series(['0']*num_rows)).fillna('').astype(str).str.lower().str.replace('nan', '0').str.strip()
        tarimas = df_raw.get('Tarimas', pd.Series(['0']*num_rows)).fillna('').astype(str).str.lower().str.replace('nan', '0').str.strip()
        cajas = cajas.replace({'': '0', '0.0': '0'})
        tarimas = tarimas.replace({'': '0', '0.0': '0'})
        
        tarimas_limpias = []
        for t_val in tarimas:
            try:
                val = float(t_val)
                if val.is_integer():
                    tarimas_limpias.append(str(int(val)))
                else:
                    tarimas_limpias.append(str(val))
            except ValueError:
                tarimas_limpias.append(t_val)
        
        df_entregas['tarimas_num'] = tarimas_limpias
        df_entregas['cantidad'] = cajas.values + " CJS / " + pd.Series(tarimas_limpias).values + " TARIMAS"
        df_entregas['semana'] = "OV: " + df_raw.get('OV Jypesa', pd.Series(['']*num_rows)).fillna('').astype(str).values
        df_entregas['entrega_texto'] = df_raw.get('FECHA HORACIO', pd.Series(['']*num_rows)).fillna('').astype(str).values
        
        cita_series = df_raw.get('CITA', pd.Series(['']*num_rows)).fillna('').astype(str).str.strip().values
        hora_series = df_raw.get('HORA', pd.Series(['']*num_rows)).fillna('').astype(str).str.strip().values
        
        valores_nulos = ['', 'nan', '0', '0.0', '-', 'nat']
        citas_combinadas = []
        for c, h in zip(cita_series, hora_series):
            es_cita_vacia = str(c).lower() in valores_nulos
            es_hora_vacia = str(h).lower() in valores_nulos
            
            if es_cita_vacia and es_hora_vacia:
                citas_combinadas.append("PENDIENTE DE CITA")
            elif not es_cita_vacia and es_hora_vacia:
                citas_combinadas.append(f"{c} - POR ASIGNAR")
            elif es_cita_vacia and not es_hora_vacia:
                citas_combinadas.append(f"PENDIENTE - {h}")
            else:
                citas_combinadas.append(f"{c} - {h}")
                
        df_entregas['cita'] = citas_combinadas

        estatus_raw = df_raw.get('ESTATUS', pd.Series(['PENDIENTE']*num_rows)).fillna('PENDIENTE').astype(str).str.upper().str.strip()
        df_entregas['estatus'] = estatus_raw.replace('NAN', 'PENDIENTE').values
        
        col_unidad_encontrada = ''
        for col in df_raw.columns:
            col_upper = col.upper().strip()
            if 'UNIDAD' in col_upper or col_upper == 'TIPO':
                col_unidad_encontrada = col
                break
        
        if col_unidad_encontrada:
            tipo_raw = df_raw.get(col_unidad_encontrada, pd.Series(['']*num_rows)).fillna('').astype(str).str.upper().str.strip()
        else:
            tipo_raw = pd.Series(['CAMION']*num_rows)
            
        df_entregas['tipo'] = tipo_raw.str.replace('Ó', 'O').values
        df_entregas = df_entregas.replace(r'(?i)^nan$', '', regex=True)

        def parse_fecha_cita(val):
            val_str = str(val).upper().strip()
            if "PENDIENTE" in val_str or not val_str or val_str in ['NAN', '0', '-']:
                return datetime(9999, 12, 31)
            try:
                fecha_parte = val_str.split(" - ")[0].strip()
                formato = "%d/%m/%Y" if len(fecha_parte.split('/')[-1]) == 4 else "%d/%m/%m"
                return datetime.strptime(fecha_parte, formato)
            except:
                return datetime(9999, 12, 31)

        df_entregas['_temp_dt'] = df_entregas['cita'].apply(parse_fecha_cita)
        df_entregas = df_entregas.sort_values(by='_temp_dt', ascending=True).drop(columns=['_temp_dt']).reset_index(drop=True)
        
        data_completa = df_entregas.to_dict('records')
        data_pendientes = [item for item in data_completa if item['estatus'] != 'ENTREGADA']
    else:
        data_completa = []
        data_pendientes = []

    if st.session_state.tipo_vista_agc == 'ENTREGAS':
        render_logistica_flow_responsive(data_pendientes)
    elif st.session_state.tipo_vista_agc == 'CALENDARIO':
        col_nav1, col_nav2, col_btn_pdf = st.columns([1, 1, 4])
        
        with col_nav1:
            if st.button("◀ SEMANA ANTERIOR", use_container_width=True):
                st.session_state.fecha_calendario_ref -= timedelta(days=7)
                st.rerun()
        with col_nav2:
            if st.button("SEMANA SIGUIENTE ▶", use_container_width=True):
                st.session_state.fecha_calendario_ref += timedelta(days=7)
                st.rerun()

        with col_btn_pdf:
            pdf_bytes = generar_pdf_citas_mes(data_completa, st.session_state.fecha_calendario_ref.month)
            nombre_mes_actual = st.session_state.fecha_calendario_ref.strftime("%B").lower()
            nombre_archivo_pdf = f"citas_pendientes_agc_{nombre_mes_actual}_2026.pdf"
            
            st.download_button(
                label="DESCARGAR PDF DE CITAS DEL MES",
                data=pdf_bytes,
                file_name=nombre_archivo_pdf,
                mime="application/pdf",
                use_container_width=True
            )
            
        render_calendario_semanal_por_horas(data_completa, st.session_state.fecha_calendario_ref)


if __name__ == "__main__":
    main()
