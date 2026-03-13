import streamlit as st
import streamlit.components.v1 as components

# Configuración de la página
st.set_page_config(page_title="Logistics Dashboard Premium", layout="wide")

def render_chingon_calendar(data):
    # Definimos el template HTML con Tailwind CSS para el look "Chingón"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }}
            .glass {{
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                transition: all 0.3s ease;
            }}
            .glass:hover {{
                border-color: #38bdf8;
                transform: translateY(-2px);
                box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.2);
            }}
            .timeline-dot {{
                width: 12px; height: 12px;
                background: #38bdf8;
                box-shadow: 0 0 10px #38bdf8;
            }}
        </style>
    </head>
    <body class="p-8">
        <div class="max-w-6xl mx-auto">
            <header class="mb-10 text-center">
                <h1 class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
                    Calendario de Suministros 2026
                </h1>
                <p class="text-slate-400 mt-2">Seguimiento de Órdenes de Compra y Entregas</p>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {"".join([f'''
                <div class="glass p-6 rounded-2xl relative overflow-hidden">
                    <div class="absolute top-0 right-0 p-3">
                        <span class="text-[10px] font-bold uppercase tracking-widest text-blue-400 bg-blue-400/10 px-2 py-1 rounded">
                            {item['semana']}
                        </span>
                    </div>
                    
                    <div class="flex flex-col h-full">
                        <div class="mb-4">
                            <p class="text-slate-500 text-xs font-semibold uppercase tracking-wider">Orden de Compra</p>
                            <h2 class="text-xl font-bold text-white tracking-tight">{item['oc']}</h2>
                        </div>

                        <div class="flex items-center gap-4 mb-6">
                            <div class="bg-emerald-500/20 p-3 rounded-xl">
                                <svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                                </svg>
                            </div>
                            <div>
                                <p class="text-slate-500 text-xs">Cantidad</p>
                                <p class="text-lg font-mono font-bold text-slate-200">{item['cantidad']} <span class="text-xs font-normal text-slate-400">cajas</span></p>
                            </div>
                        </div>

                        <div class="mt-auto border-t border-slate-700/50 pt-4">
                            <div class="flex justify-between items-end">
                                <div>
                                    <p class="text-slate-500 text-[10px] uppercase font-bold">Fecha Entrega Estimada</p>
                                    <p class="text-sm text-slate-300 italic">"{item['entrega_texto']}"</p>
                                </div>
                                <div class="text-right">
                                    <p class="text-blue-400 text-[10px] uppercase font-bold">Fecha de Cita</p>
                                    <p class="text-lg font-bold text-white">{item['cita'] if item['cita'] else '-- / --'}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                ''' for item in data])}
            </div>
        </div>
    </body>
    </html>
    """
    return components.html(html_content, height=800, scrolling=True)

# Data extraída de tu imagen
data_logistica = [
    {"oc": "C09421-L01", "cantidad": "---", "semana": "N/A", "entrega_texto": "Pendiente", "cita": ""},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 8", "entrega_texto": "9 de marzo", "cita": "10/03/2026"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 13", "entrega_texto": "23 de marzo", "cita": "24/03/2026"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 15", "entrega_texto": "6 de abril", "cita": ""},
    {"oc": "OC 9197", "cantidad": "520", "semana": "SEMANA 17", "entrega_texto": "20 de abril", "cita": ""},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 19", "entrega_texto": "4 de mayo", "cita": ""},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 21", "entrega_texto": "18 de mayo", "cita": ""},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 23", "entrega_texto": "1 de junio", "cita": ""},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 25", "entrega_texto": "15 de junio", "cita": ""},
    {"oc": "OC 10663", "cantidad": "160", "semana": "SEMANA 27", "entrega_texto": "29 de junio", "cita": ""},
]

# Título de Streamlit (opcional, ya que el HTML tiene el suyo)
st.markdown("### Visualización de Logística Avanzada")

# Ejecutamos el render
render_chingon_calendar(data_logistica)
























































































