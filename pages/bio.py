import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE CONEXIÓN (GITHUB) ---
# Asegúrate de tener tu TOKEN en los Secrets de Streamlit como: GITHUB_TOKEN
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] if "GITHUB_TOKEN" in st.secrets else "TU_TOKEN_AQUÍ"
URL_CONSIGNAS = "https://raw.githubusercontent.com/RH2026/nexion/refs/heads/main/consignas.csv"

@st.cache_data
def load_consignas():
    try:
        # Usamos el token para archivos privados si es necesario
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        df = pd.read_csv(URL_CONSIGNAS, storage_options=headers, low_memory=False)
        return df
    except Exception as e:
        st.error(f"Error cargando consignas: {e}")
        return None

def render_expediente_chingon(df):
    # Convertimos el DF a lista de diccionarios para el HTML
    data = df.to_dict('records')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
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
                transform: translateY(-2px);
            }}
            .label-mini {{
                font-size: 9px;
                text-transform: uppercase;
                color: rgba(255,255,255,0.4);
                font-weight: 800;
                letter-spacing: 1px;
            }}
            .valor {{ font-size: 13px; font-weight: 600; color: #FFFFFF; }}
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
                        <div class="valor highlight text-lg">{item.get('TALON', 'N/A')}</div>
                        <div class="label-mini mt-2 text-blue-400">F. Doc: {item.get('F.DOC', '--')}</div>
                    </div>
                    
                    <div>
                        <div class="label-mini">Destinatario</div>
                        <div class="valor truncate text-xs">{item.get('DESTINATARIO', 'N/A')}</div>
                        <div class="text-[10px] text-white/50 italic">{item.get('DESTINO', '--')}</div>
                    </div>

                    <div class="border-x border-white/5 px-4">
                        <div class="label-mini">Financiero</div>
                        <div class="flex justify-between">
                            <span class="label-mini">Sub:</span> <span class="valor text-[11px]">${item.get('SUBTOTAL', 0)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="label-mini">Total:</span> <span class="valor text-emerald-400">${item.get('TOTAL', 0)}</span>
                        </div>
                    </div>

                    <div class="text-right">
                        <div class="label-mini">Estatus Entrega</div>
                        <div class="valor text-[11px]">{item.get('F.ENTREGA', 'PENDIENTE')}</div>
                        <div class="text-[9px] text-orange-400 font-bold uppercase">{item.get('QUIEN RECIBIO', '')[:20]}</div>
                    </div>
                </div>

                <div class="mt-3 pt-3 border-t border-white/5 flex flex-wrap gap-4">
                    <div class="flex-1 min-w-[200px]">
                        <span class="label-mini">Domicilio:</span>
                        <span class="text-[10px] text-white/60"> {item.get('DOMICILIO DEL DESTINATARIO', 'No registrado')}</span>
                    </div>
                    <div class="w-full md:w-auto">
                        <span class="label-mini">Obs:</span>
                        <span class="text-[10px] text-white/60 italic"> {item.get('OBSERVACION 1', '--')}</span>
                    </div>
                </div>
            </div>
            ''' for item in data])}
        </div>
    </body>
    </html>
    """
    return components.html(html_content, height=800, scrolling=True)

# --- EJECUCIÓN ---
df_consignas = load_consignas()

if df_consignas is not None:
    st.markdown("<h3 style='text-align:center; color:white; font-size:16px;'>EXPEDIENTES LOGÍSTICOS</h3>", unsafe_allow_html=True)
    render_expediente_chingon(df_consignas)
