import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# ── CONFIGURACIÓN DE PÁGINA (Debe ser lo primero) ──
st.set_page_config(layout="wide", page_title="Nexion Expedientes")

# --- CONFIGURACIÓN DE CONEXIÓN (GITHUB) ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = "RH2026/nexion"
FILE_PATH_CON = "consignas.csv"
URL_CONSIGNAS = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH_CON}"

@st.cache_data(ttl=600)
def load_consignas():
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        df = pd.read_csv(URL_CONSIGNAS, storage_options=headers, low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error cargando consignas: {e}")
        return None

def render_expediente_chingon(df):
    df_clean = df.fillna('')
    data = df_clean.to_dict('records')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ 
                background-color: #384A52; 
                color: #e2e8f0; 
                font-family: 'Inter', sans-serif; 
                margin: 0; 
                padding: 0px 5px; /* Ajuste fino lateral */
            }}
            
            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); }}
            ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 10px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: rgba(56, 189, 248, 0.4); }}

            .row-expediente {{
                background-color: #263238;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                margin-bottom: 12px;
                padding: 18px 24px;
                transition: all 0.3s ease;
                width: 100%; /* Fuerza el ancho total */
                box-sizing: border-box;
            }}
            
            .row-expediente:hover {{
                border-color: #00FFAA;
                background-color: #2d3b42;
                transform: scale(1.001);
            }}
            
            .label-mini {{
                font-size: 8px;
                text-transform: uppercase;
                color: rgba(255,255,255,0.3);
                font-weight: 800;
                letter-spacing: 1.5px;
            }}
            
            .valor {{ font-size: 14px; font-weight: 700; color: #FFFFFF; }}
            .highlight {{ color: #00FFAA; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="w-full">
            {"".join([f'''
            <div class="row-expediente">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
                    
                    <div>
                        <div class="label-mini">Talon / Folio</div>
                        <div class="valor highlight text-xl leading-none">{str(item.get('TALON', ''))}</div>
                        <div class="text-[10px] text-blue-400 mt-1 opacity-70 italic">F. Doc: {str(item.get('F.DOC', ''))}</div>
                    </div>
                    
                    <div class="md:border-l md:border-white/5 md:pl-6">
                        <div class="label-mini">Destinatario</div>
                        <div class="valor truncate text-sm uppercase">{str(item.get('DESTINATARIO', ''))[:45]}</div>
                        <div class="text-[10px] text-white/50 italic">{str(item.get('ORIGEN', ''))} → {str(item.get('DESTINO', ''))}</div>
                    </div>

                    <div class="md:border-l md:border-white/5 md:pl-6">
                        <div class="label-mini">Resumen Financiero</div>
                        <div class="flex justify-between items-center">
                            <span class="label-mini">Bultos:</span> <span class="valor text-xs">{str(item.get('BULTOS', '0'))}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="label-mini">Total Cargo:</span> <span class="valor text-emerald-400 text-sm">${str(item.get('TOTAL', '0'))}</span>
                        </div>
                    </div>

                    <div class="text-right md:border-l md:border-white/5 md:pl-6">
                        <div class="label-mini">Estatus Entrega</div>
                        <div class="valor text-sm {"text-orange-400" if not item.get('F.ENTREGA') else "text-white"}">
                            {str(item.get('F.ENTREGA', 'PENDIENTE'))}
                        </div>
                        <div class="text-[10px] text-blue-400 font-bold uppercase tracking-tighter">
                            {str(item.get('QUIEN RECIBIO', ''))[:25]}
                        </div>
                    </div>
                </div>

                <div class="mt-4 pt-3 border-t border-white/5 flex flex-col md:flex-row justify-between gap-4">
                    <div class="flex-1">
                        <span class="label-mini text-blue-300">Domicilio Entrega:</span>
                        <span class="text-[11px] text-white/60 ml-2"> {str(item.get('DOMICILIO DEL DESTINATARIO', ''))}</span>
                    </div>
                    <div class="text-right">
                        <span class="label-mini">Notas:</span>
                        <span class="text-[11px] text-white/40 italic ml-2"> {str(item.get('OBSERVACION 1', '--'))}</span>
                    </div>
                </div>
            </div>
            ''' for item in data])}
        </div>
    </body>
    </html>
    """
    # Usamos height dinámico o uno alto para que el scroll de la página mande
    return components.html(html_content, height=1200, scrolling=True)

# --- EJECUCIÓN ---
df_consignas = load_consignas()

if df_consignas is not None:
    st.markdown("<h3 style='text-align:center; color:white; font-size:18px; letter-spacing:4px; font-weight:900;'>EXPEDIENTES LOGÍSTICOS</h3>", unsafe_allow_html=True)
    
    # El buscador ahora se verá igual de ancho que las tarjetas de abajo
    search = st.text_input("🔍 Buscar por Talón:", placeholder="Escribe el número de talón...", key="search_main")
    
    if search:
        df_consignas = df_consignas[df_consignas['TALON'].astype(str).str.contains(search, case=False)]
        
    render_expediente_chingon(df_consignas)
