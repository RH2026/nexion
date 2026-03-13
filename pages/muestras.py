import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Logística Compact Pro", layout="wide")

def render_logistica_flow_compact(data):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #0b0f1a; color: #e2e8f0; }}
            .glass-card {{
                background: rgba(23, 32, 53, 0.8);
                backdrop-filter: blur(8px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                transition: all 0.3s ease;
            }}
            @keyframes pulse-border {{
                0% {{ border-color: rgba(245, 158, 11, 0.2); }}
                50% {{ border-color: rgba(245, 158, 11, 0.6); }}
                100% {{ border-color: rgba(245, 158, 11, 0.2); }}
            }}
            .status-pending {{ 
                border-left: 3px solid #f59e0b; 
                animation: pulse-border 2s infinite;
            }}
            .status-delivered {{ border-left: 3px solid #10b981; }}
        </style>
    </head>
    <body class="p-4 md:p-8">
        <div class="max-w-full mx-auto">
            <header class="flex justify-between items-center mb-8">
                <div>
                    <h1 class="text-3xl font-extrabold tracking-tighter text-white">
                        LOGÍSTICA <span class="text-orange-500">COMPACT</span>
                    </h1>
                </div>
                <div class="bg-slate-800/50 px-4 py-2 rounded-xl border border-white/5">
                    <p class="text-[10px] text-slate-500 uppercase font-bold tracking-widest text-center">Registros Totales</p>
                    <p class="text-xl font-black text-white text-center italic leading-none">{len(data)}</p>
                </div>
            </header>

            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
                {"".join([f'''
                <div class="glass-card rounded-2xl p-3 flex flex-col justify-between {"status-delivered" if item['estatus'] == "ENTREGADA" else "status-pending"}">
                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-[8px] font-bold text-slate-500 uppercase">{item['semana']}</span>
                            <div class="h-2 w-2 rounded-full {"bg-emerald-500 shadow-[0_0_8px_#10b981]" if item['estatus'] == "ENTREGADA" else "bg-orange-500 shadow-[0_0_8px_#f59e0b]"}"></div>
                        </div>
                        
                        <h3 class="text-lg font-black text-white leading-none mb-1">{item['oc']}</h3>
                        <p class="text-[9px] text-slate-500 font-medium mb-3 truncate">{item['entrega_texto']}</p>
                        
                        <div class="space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-[8px] text-slate-500 uppercase tracking-tighter">Cajas</span>
                                <span class="text-xs font-bold text-slate-200">{item['cantidad']}</span>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-[8px] text-slate-500 uppercase tracking-tighter">Cita</span>
                                <span class="text-[10px] font-mono {"text-orange-400 font-bold" if item['cita'] == "PENDIENTE" else "text-blue-400 font-bold"}">
                                    {item['cita']}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <div class="w-full bg-slate-800 rounded-full h-1 relative">
                            <div class="{"bg-emerald-500" if item['estatus'] == "ENTREGADA" else "bg-orange-500"} h-1 rounded-full" 
                                 style="width: {'100%' if item['estatus'] == "ENTREGADA" else '25%'}"></div>
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

# Tu dataset actualizado
data_corregida = [
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 8", "entrega_texto": "9 de marzo", "cita": "10/03/2026", "estatus": "ENTREGADA"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 13", "entrega_texto": "23 de marzo", "cita": "24/03/2026", "estatus": "ENTREGADA"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 15", "entrega_texto": "6 de abril", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 9197", "cantidad": "520", "semana": "SEM 17", "entrega_texto": "20 de abril", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 21", "entrega_texto": "18 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 23", "entrega_texto": "1 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 25", "entrega_texto": "15 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 26", "entrega_texto": "22 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "160", "semana": "SEM 27", "entrega_texto": "29 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
]

render_logistica_flow_compact(data_corregida)
























































































