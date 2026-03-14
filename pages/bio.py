import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE CONEXIÓN (GITHUB) ---
# Extraemos el token de forma segura
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "TU_TOKEN_AQUÍ")
REPO_NAME = "RH2026/nexion"
FILE_PATH_CON = "consignas.csv"
URL_CONSIGNAS = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{FILE_PATH_CON}"

@st.cache_data(ttl=600)
def load_consignas():
    try:
        # Usamos el token para archivos si es necesario
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        df = pd.read_csv(URL_CONSIGNAS, storage_options=headers, low_memory=False)
        # Limpiamos nombres de columnas
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error cargando consignas: {e}")
        return None

def render_expediente_chingon(df):
    # Llenamos vacíos para evitar errores de tipo None
    df_clean = df.fillna('')
    data = df_clean.to_dict('records')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ background-color: #384A52; color: #e2e8f0; font-family: 'Inter', sans-serif; margin: 0; padding: 10px; }}
            
            /* SCROLLBAR MINIMALISTA */
            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); }}
            ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 10px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: rgba(56, 189, 248, 0.4); }}

            .row-expediente {{
                background-color: #263238;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                margin-bottom: 10px;
                padding: 15px;
                transition: all 0.3s ease;
            }}
            .row-expediente:hover {{
                border-color: #00FFAA;
                transform: translateX(4px);
            }}
            .label-mini {{
                font-size: 8px;
                text-transform: uppercase;
                color: rgba(255,255,255,0.3);
                font-weight: 800;
                letter-spacing: 1.2px;
            }}
            .valor {{ font-size: 13px; font-weight: 700; color: #FFFFFF; }}
            .highlight {{ color: #00FFAA; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="max-w-6xl mx-auto">
            {"".join([f'''
            <div class="row-expediente">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <div class="label-mini">Talon / Folio</div>
                        <div class="valor highlight text-lg">{str(item.get('TALON', ''))}</div>
                        <div class="label-mini mt-1 text-blue-400">F. Doc: {str(item.get('F.DOC', ''))}</div>
                    </div>
                    
                    <div>
                        <div class="label-mini">Destinatario</div>
                        <div class="valor truncate text-xs">{str(item.get('DESTINATARIO', ''))[:30]}</div>
                        <div class="text-[10px] text-white/50 italic">{str(item.get('ORIGEN', ''))} → {str(item.get('DESTINO', ''))}</div>
                    </div>

                    <div class="border-x border-white/5 px-4">
                        <div class="label-mini">Financiero</div>
                        <div class="flex justify-between">
                            <span class="label-mini">Bultos:</span> <span class="valor text-[11px]">{str(item.get('BULTOS', '0'))}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="label-mini">Total:</span> <span class="valor text-emerald-400">${str(item.get('TOTAL', '0'))}</span>
                        </div>
                    </div>

                    <div class="text-right">
                        <div class="label-mini">Estatus Entrega</div>
                        <div class="valor text-[11px] {"text-orange-400" if not item.get('F.ENTREGA') else "text-white"}">
                            {str(item.get('F.ENTREGA', 'PENDIENTE'))}
                        </div>
                        <div class="text-[9px] text-blue-400 font-bold uppercase">
                            {str(item.get('QUIEN RECIBIO', ''))[:20]}
                        </div>
                    </div>
                </div>

                <div class="mt-3 pt-3 border-t border-white/5 flex flex-wrap gap-4">
                    <div class="flex-1 min-w-[200px]">
                        <span class="label-mini">Domicilio:</span>
                        <span class="text-[10px] text-white/50"> {str(item.get('DOMICILIO DEL DESTINATARIO', ''))}</span>
                    </div>
                    <div class="w-full md:w-auto">
                        <span class="label-mini">Obs:</span>
                        <span class="text-[10px] text-white/40 italic"> {str(item.get('OBSERVACION 1', '--'))}</span>
                    </div>
                </div>
            </div>
            ''' for item in data])}
        </div>
    </body>
    </html>
    """
    return components.html(html_content, height=850, scrolling=True)

# --- EJECUCIÓN ---
df_consignas = load_consignas()

if df_consignas is not None:
    st.markdown("<h3 style='text-align:center; color:white; font-size:16px; letter-spacing:2px;'>EXPEDIENTES LOGÍSTICOS</h3>", unsafe_allow_html=True)
    
    # Buscador por Talón
    search = st.text_input("🔍 Buscar por Talón:", placeholder="Escribe el número de talón...")
    if search:
        df_consignas = df_consignas[df_consignas['TALON'].astype(str).str.contains(search, case=False)]
        
    render_expediente_chingon(df_consignas)
