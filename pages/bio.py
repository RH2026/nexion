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
        
        # --- LÓGICA DE ORDENAMIENTO POR FECHA ---
        if 'F.DOC' in df.columns:
            # Intentamos convertir a fecha (dayfirst=True por si viene en formato DD/MM/YYYY)
            df['F_TEMP'] = pd.to_datetime(df['F.DOC'], errors='coerce', dayfirst=True)
            # Ordenamos: las más recientes (NaT o vacías se van al final)
            df = df.sort_values(by='F_TEMP', ascending=False).drop(columns=['F_TEMP'])
            
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
                padding: 10px 15px;
            }}
            
            ::-webkit-scrollbar {{ 
                width: 10px; 
                height: 10px;
            }}
            ::-webkit-scrollbar-track {{ 
                background: rgba(0,0,0,0.2); 
                border-radius: 10px;
            }}
            ::-webkit-scrollbar-thumb {{ 
                background: rgba(56, 189, 248, 0.6); 
                border-radius: 10px;
                border: 2px solid #384A52;
            }}
            ::-webkit-scrollbar-thumb:hover {{ 
                background: rgba(0, 255, 170, 0.8); 
            }}

            .row-expediente {{
                background-color: #263238;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                margin-bottom: 12px;
                padding: 18px 24px;
                transition: all 0.3s ease;
                width: 100%;
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
                color: rgba(255,255,255,0.6); 
                font-weight: 800;
                letter-spacing: 1.5px;
            }}
            
            .valor {{ font-size: 14px; font-weight: 700; color: #FFFFFF; }}
            .highlight {{ color: #00FFAA; font-family: monospace; }}
            
            .text-muted-claro {{
                color: rgba(255,255,255,0.7); 
                font-style: italic;
            }}
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
                        <div class="text-[10px] text-blue-300 mt-1 opacity-90 italic">F. Doc: {str(item.get('F.DOC', ''))}</div>
                    </div>
                    
                    <div class="md:border-l md:border-white/10 md:pl-6">
                        <div class="label-mini">Destinatario / Origen-Dest</div>
                        <div class="valor truncate text-sm uppercase">{str(item.get('DESTINATARIO', ''))[:45]}</div>
                        <div class="text-[10px] text-muted-claro">{str(item.get('ORIGEN', ''))} → {str(item.get('DESTINO', ''))}</div>
                    </div>

                    <div class="md:border-l md:border-white/10 md:pl-6">
                        <div class="label-mini">Resumen Financiero</div>
                        <div class="flex justify-between items-center">
                            <span class="label-mini">Bultos:</span> <span class="valor text-xs">{str(item.get('BULTOS', '0'))}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="label-mini">Total Cargo:</span> <span class="valor text-emerald-400 text-sm">${str(item.get('TOTAL', '0'))}</span>
                        </div>
                    </div>

                    <div class="text-right md:border-l md:border-white/10 md:pl-6">
                        <div class="label-mini">Estatus Entrega</div>
                        <div class="valor text-sm {"text-orange-400" if not item.get('F.ENTREGA') else "text-white"}">
                            {str(item.get('F.ENTREGA', 'PENDIENTE'))}
                        </div>
                        <div class="text-[10px] text-blue-300 font-bold uppercase tracking-tighter">
                            {str(item.get('QUIEN RECIBIO', ''))[:25]}
                        </div>
                    </div>
                </div>

                <div class="mt-4 pt-3 border-t border-white/10 flex flex-col md:flex-row justify-between gap-4">
                    <div class="flex-1">
                        <span class="label-mini text-blue-200">Domicilio Entrega:</span>
                        <span class="text-[11px] text-white/80 ml-2"> {str(item.get('DOMICILIO DEL DESTINATARIO', ''))}</span>
                    </div>
                    <div class="text-right flex gap-4">
                        <div>
                            <span class="label-mini text-orange-200">Ref:</span>
                            <span class="text-[11px] text-white/80 italic ml-1">{str(item.get('REFERENCIA', '--'))}</span>
                        </div>
                        <div>
                            <span class="label-mini text-white/60">Notas:</span>
                            <span class="text-[11px] text-white/70 italic ml-1">{str(item.get('OBSERVACION 1', '--'))}</span>
                        </div>
                    </div>
                </div>
            </div>
            ''' for item in data])}
        </div>
    </body>
    </html>
    """
    return components.html(html_content, height=1200, scrolling=True)

# --- EJECUCIÓN PRINCIPAL ---
df_consignas = load_consignas()

if df_consignas is not None:
    st.markdown("<h3 style='text-align:center; color:white; font-size:18px; letter-spacing:4px; font-weight:900;'>EXPEDIENTES LOGÍSTICOS</h3>", unsafe_allow_html=True)
    render_expediente_chingon(df_consignas)

if df_consignas is not None:
    st.markdown("<h3 style='text-align:center; color:white; font-size:18px; letter-spacing:4px; font-weight:900;'>EXPEDIENTES LOGÍSTICOS</h3>", unsafe_allow_html=True)
    
    # Renderizado directo sin buscador amor
    render_expediente_chingon(df_consignas)
