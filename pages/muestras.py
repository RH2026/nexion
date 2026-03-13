import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Logistics Dashboard Pro", layout="wide")

def render_chingon_calendar(data):
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
            .card-entregada {{ border-color: #10b981 !important; box-shadow: 0 0 15px -5px rgba(16, 185, 129, 0.3); }}
            .card-pendiente {{ border-color: rgba(255, 255, 255, 0.1); }}
            .glass:hover {{ transform: translateY(-4px); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); }}
        </style>
    </head>
    <body class="p-8">
        <div class="max-w-7xl mx-auto">
            <header class="mb-12 flex justify-between items-end">
                <div>
                    <h1 class="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 italic">
                        LOGÍSTICA FLOW 2026
                    </h1>
                    <p class="text-slate-400 font-light">Control de suministros y estatus de almacén</p>
                </div>
                <div class="text-right">
                    <span class="text-xs text-slate-500 uppercase tracking-widest">Última actualización</span>
                    <p class="text-sm font-mono text-emerald-400">13/MAR/2026</p>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {"".join([f'''
                <div class="glass p-5 rounded-3xl relative {"card-entregada" if item['estatus'] == "ENTREGADA" else "card-pendiente"}">
                    <div class="absolute top-4 right-4">
                        <span class="text-[9px] font-bold px-2 py-1 rounded-full {"bg-emerald-500/20 text-emerald-400" if item['estatus'] == "ENTREGADA" else "bg-blue-500/10 text-blue-400"}">
                            {item['estatus'] if item['estatus'] else 'EN PROCESO'}
                        </span>
                    </div>

                    <div class="flex flex-col gap-4">
                        <div>
                            <span class="text-slate-500 text-[10px] font-bold tracking-widest uppercase">{item['semana']}</span>
                            <h2 class="text-2xl font-black text-white">{item['oc']}</h2>
                        </div>

                        <div class="flex items-center gap-3">
                            <div class="{"text-emerald-400" if item['estatus'] == "ENTREGADA" else "text-blue-400"}">
                                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                                </svg>
                            </div>
                            <div>
                                <p class="text-slate-500 text-[10px] uppercase">Volumen</p>
                                <p class="text-lg font-bold">{item['cantidad']} <span class="text-xs font-normal opacity-50">Cajas</span></p>
                            </div>
                        </div>

                        <div class="bg-slate-800/50 rounded-2xl p-3 border border-white/5">
                            <div class="flex justify-between items-center">
                                <div>
                                    <p class="text-slate-500 text-[9px] uppercase">Cita Programada</p>
                                    <p class="text-sm font-semibold text-slate-200">{item['cita'] if item['cita'] else 'Sin fecha'}</p>
                                </div>
                                <div class="text-right">
                                    <p class="text-slate-500 text-[9px] uppercase">Semana de</p>
                                    <p class="text-sm font-medium text-slate-400 italic text-[11px]">{item['entrega_texto']}</p>
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
    return components.html(html_content, height=900, scrolling=True)

# Data actualizada con la columna ESTATUS
data_logistica = [
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 8", "entrega_texto": "9 de marzo", "cita": "10/03/2026", "estatus": "ENTREGADA"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 13", "entrega_texto": "23 de marzo", "cita": "24/03/2026", "estatus": ""},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 15", "entrega_texto": "6 de abril", "cita": "", "estatus": ""},
    {"oc": "OC 9197", "cantidad": "520", "semana": "SEMANA 17", "entrega_texto": "20 de abril", "cita": "", "estatus": ""},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 19", "entrega_texto": "4 de mayo", "cita": "", "estatus": ""},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 21", "entrega_texto": "18 de mayo", "cita": "", "estatus": ""},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 23", "entrega_texto": "1 de junio", "cita": "", "estatus": ""},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 25", "entrega_texto": "15 de junio", "cita": "", "estatus": ""},
    {"oc": "OC 10663", "cantidad": "160", "semana": "SEMANA 27", "entrega_texto": "29 de junio", "cita": "", "estatus": ""},
]

render_chingon_calendar(data_logistica)
























































































