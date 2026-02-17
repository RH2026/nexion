import os
import io
import zipfile
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
import unicodedata
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

# --- 0. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(layout="wide")
vars_css = {'sub': '#54AFE7', 'border': '#333'}

st.markdown(f"""
    <style>
    .op-query-text {{ color: #54AFE7; font-weight: bold; letter-spacing: 1px; font-size: 14px; }}
    .stButton>button {{ width: 100%; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 1. CARGA DE MATRIZ DESDE GITHUB ---
@st.cache_data
def obtener_matriz_github():
    url = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/matriz_historial.csv"
    try:
        # Cargamos y limpiamos nombres de columnas de la matriz
        m = pd.read_csv(url)
        m.columns = [str(c).upper().strip() for c in m.columns]
        return m
    except Exception as e:
        st.error(f"Error al conectar con la matriz de GitHub: {e}")
        return pd.DataFrame()

def normalizar_cadena(texto):
    if pd.isna(texto): return ""
    # Elimina acentos y convierte a mayúsculas para un match perfecto
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper().strip()

# --- 2. FUNCIONES MAESTRAS ---
def generar_sellos_fisicos(lista_textos, x, y):
    output = PdfWriter()
    for texto in lista_textos:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 11)
        can.drawString(x, y, f"{str(texto).upper()}")
        can.save()
        packet.seek(0)
        output.add_page(PdfReader(packet).pages[0])
    out_io = io.BytesIO()
    output.write(out_io)
    return out_io.getvalue()

def marcar_pdf_digital(pdf_file, texto_sello, x, y):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 11)
    can.drawString(x, y, f"{str(texto_sello).upper()}")
    can.save()
    packet.seek(0)
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(pdf_file)
    output = PdfWriter()
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)
    for i in range(1, len(existing_pdf.pages)):
        output.add_page(existing_pdf.pages[i])
    out_io = io.BytesIO()
    output.write(out_io)
    return out_io.getvalue()

# --- BLOQUE 1: PREPARACIÓN S&T ---
st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>S&T PREPARATION MODULE</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Subir archivo ERP", type=["xlsx", "csv"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        df.columns = [str(c).strip().replace('\n', '').replace('\t', '') for c in df.columns]
        col_folio = next((c for c in df.columns if 'factura' in c.lower() or 'docnum' in c.lower()), df.columns[0])
        
        st.toast(f"ARCHIVO DETECTADO: {len(df)} FILAS", icon="🔍")

        col_left, col_right = st.columns([1, 2], gap="large")
        with col_left:
            st.markdown(f"<p class='op-query-text'>FILTROS DE RANGO</p>", unsafe_allow_html=True)
            serie_folios = pd.to_numeric(df[col_folio], errors='coerce').dropna()
            f_min, f_max = (int(serie_folios.min()), int(serie_folios.max())) if not serie_folios.empty else (0,0)
            inicio = st.number_input("Folio Inicial", value=f_min)
            final = st.number_input("Folio Final", value=f_max)
            df[col_folio] = pd.to_numeric(df[col_folio], errors='coerce')
            df_rango = df[(df[col_folio] >= inicio) & (df[col_folio] <= final)].copy()

        with col_right:
            st.markdown(f"<p class='op-query-text'>SELECCIÓN DE FOLIOS</p>", unsafe_allow_html=True)
            if not df_rango.empty:
                info_folios = df_rango.drop_duplicates(subset=[col_folio])[[col_folio]]
                selector_df = info_folios.copy()
                selector_df.insert(0, "Incluir", True)
                edited_df = st.data_editor(selector_df, hide_index=True, height=300, use_container_width=True, key="ed_st_v3")
            else:
                st.warning("Sin datos en el rango.")

        if not df_rango.empty and not edited_df.empty:
            folios_finales = edited_df[edited_df["Incluir"] == True][col_folio].tolist()
            c1, c2, c3 = st.columns([1,1,2])
            
            with c1:
                render_btn = st.button("RENDERIZAR TABLA")
            
            if render_btn or "df_final_st" in st.session_state:
                if render_btn:
                    st.session_state.df_final_st = df_rango[df_rango[col_folio].isin(folios_finales)]
                
                df_st = st.session_state.df_final_st
                st.dataframe(df_st, use_container_width=True)
                
                with c3:
                    if st.button("🚀 SMART ROUTING (MATCH DESTINO GITHUB)", type="primary"):
                        # --- PROCESO DE CRUCE CON COLUMNA 'DESTINO' ---
                        df_analisis = df_st.drop_duplicates(subset=[col_folio]).copy()
                        matriz_db = obtener_matriz_github()
                        
                        # Identificamos columna DIRECCION en el ERP subido
                        col_dir_erp = next((c for c in df_analisis.columns if 'DIRECCION' in c.upper()), None)
                        
                        # Identificamos columnas en la MATRIZ de GitHub
                        col_dest_matriz = 'DESTINO' if 'DESTINO' in matriz_db.columns else matriz_db.columns[0]
                        col_flet_matriz = 'TRANSPORTE' if 'TRANSPORTE' in matriz_db.columns else 'FLETERA'

                        def motor_smart(row):
                            if not col_dir_erp: return "ERROR: SIN COL DIRECCION"
                            
                            direc_cliente = normalizar_cadena(row[col_dir_erp])
                            
                            # 1. Prioridad Local (Hardcoded por eficiencia)
                            if any(loc in direc_cliente for loc in ["GDL", "GUADALAJARA", "ZAPOPAN", "TLAQUEPAQUE", "TONALA"]):
                                return "LOCAL"
                            
                            # 2. Match contra columna DESTINO del CSV de GitHub
                            for _, fila in matriz_db.iterrows():
                                keyword_destino = normalizar_cadena(fila[col_dest_matriz])
                                # Si la palabra del destino histórico aparece en la dirección actual...
                                if keyword_destino and (keyword_destino in direc_cliente):
                                    return fila.get(col_flet_matriz, "ASIGNADO")
                            
                            return "REVISIÓN MANUAL"

                        df_analisis['RECOMENDACION'] = df_analisis.apply(motor_smart, axis=1)
                        df_analisis['COSTO'] = 0.0
                        df_analisis['FECHA_HORA'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        st.session_state.df_analisis = df_analisis
                        st.success("Motor Smart Routing finalizado con éxito.")
                        st.rerun()

    except Exception as e:
        st.error(f"Error S&T: {e}")

# --- BLOQUE 2: SMART ROUTING ---
if "df_analisis" in st.session_state:
    st.markdown("---")
    st.markdown(f"<p style='letter-spacing:3px; color:{vars_css['sub']}; font-size:10px; font-weight:700;'>LOGISTICS INTELLIGENCE HUB | XENOCODE CORE</p>", unsafe_allow_html=True)
    
    p = st.session_state.df_analisis
    modo_edicion = st.toggle("EDITAR VALORES MANUALMENTE")
    
    p_editado = st.data_editor(
        p, use_container_width=True, hide_index=True,
        column_config={
            "RECOMENDACION": st.column_config.TextColumn("FLETERA RECOMENDADA", disabled=not modo_edicion),
            "COSTO": st.column_config.NumberColumn("TARIFA", format="$%.2f", disabled=not modo_edicion),
        },
        key="editor_final_v3"
    )

    # SISTEMA DE SELLADO
    with st.expander("AJUSTES DE IMPRESIÓN Y SELLADO", expanded=True):
        cx, cy = st.columns(2)
        ax = cx.slider("Posición X", 0, 612, 510)
        ay = cy.slider("Posición Y", 0, 792, 760)
        
        if st.button("GENERAR SELLOS PARA PAPEL"):
            pdf_sellos = generar_sellos_fisicos(p_editado['RECOMENDACION'].tolist(), ax, ay)
            st.download_button("Descargar PDF de Sellos", pdf_sellos, "Sellos.pdf")
            
        st.markdown("---")
        pdf_files = st.file_uploader("Subir Facturas para Sellado Digital", type="pdf", accept_multiple_files=True)
        if pdf_files and st.button("ESTAMPAR DIGITALMENTE"):
            col_id = p_editado.columns[0]
            mapa_sellos = pd.Series(p_editado.RECOMENDACION.values, index=p_editado[col_id].astype(str)).to_dict()
            zip_io = io.BytesIO()
            with zipfile.ZipFile(zip_io, "a") as zf:
                for pdf in pdf_files:
                    f_id = next((k for k in mapa_sellos.keys() if k in pdf.name.upper()), None)
                    if f_id:
                        zf.writestr(f"SELLADO_{pdf.name}", marcar_pdf_digital(pdf, mapa_sellos[f_id], ax, ay))
            st.download_button("DESCARGAR ZIP SELLADO", zip_io.getvalue(), "Facturas_Digitales.zip")































































































