import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Logística Dashboard Pro", layout="wide")

def render_logistica_flow_mid(data):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{ 
                font-family: 'Inter', sans-serif; 
                background-color: #384A52; 
                color: #e2e8f0; 
                margin: 0;
            }}
            .glass-card {{
                /* Fondo mucho más oscuro para mayor contraste */
                background: rgba(15, 23, 42, 0.9);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                transition: transform 0.2s ease, border-color 0.2s ease;
            }}
            .glass-card:hover {{
                transform: translateY(-3px);
                border-color: rgba(56, 189, 248, 0.5);
                background: rgba(15, 23, 42, 0.95);
            }}
            @keyframes pulse-border {{
                0% {{ border-color: rgba(245, 158, 11, 0.3); }}
                50% {{ border-color: rgba(245, 158, 11, 0.8); }}
                100% {{ border-color: rgba(245, 158, 11, 0.3); }}
            }}
            .status-pending {{ 
                border-left: 5px solid #f59e0b; 
                animation: pulse-border 2s infinite;
            }}
            .status-delivered {{ border-left: 5px solid #10b981; }}
        </style>
    </head>
    <body class="p-4">
        <div class="max-w-full mx-auto">
            <header class="flex justify-between items-center mb-6 px-2">
                <h1 class="text-2xl font-black tracking-tighter text-white uppercase italic">
                    Logística <span class="text-blue-400 underline decoration-blue-400/20">Flow</span>
                </h1>
                <div class="bg-black/30 px-4 py-2 rounded-xl border border-white/10">
                    <p class="text-[9px] text-white/50 font-bold uppercase tracking-widest leading-none">Status</p>
                    <p class="text-xs font-bold text-emerald-400 leading-none mt-1 uppercase tracking-tighter">Live Monitor</p>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {"".join([f'''
                <div class="glass-card rounded-2xl p-4 flex flex-col justify-between {"status-delivered" if item['estatus'] == "ENTREGADA" else "status-pending"}">
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <span class="text-[9px] font-bold text-white/70 bg-black/50 px-2 py-0.5 rounded uppercase tracking-wider">
                                {item['semana']}
                            </span>
                            <div class="h-2 w-2 rounded-full {"bg-emerald-400 shadow-[0_0_10px_#10b981]" if item['estatus'] == "ENTREGADA" else "bg-orange-500 shadow-[0_0_10px_#f59e0b]"}"></div>
                        </div>
                        
                        <h3 class="text-xl font-black text-white leading-none mb-1 tracking-tight italic">{item['oc']}</h3>
                        <p class="text-[10px] text-white/60 font-medium mb-4 truncate italic">{item['entrega_texto']}</p>
                        
                        <div class="space-y-2.5 bg-black/50 rounded-xl p-3 border border-white/5 shadow-inner">
                            <div class="flex items-center justify-between">
                                <span class="text-[9px] text-white uppercase font-extrabold tracking-widest opacity-90">Volumen</span>
                                <span class="text-sm font-bold text-white">{item['cantidad']}</span>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-[9px] text-white uppercase font-extrabold tracking-widest opacity-90">Cita</span>
                                <span class="text-[11px] font-mono font-bold {"text-orange-400" if item['cita'] == "PENDIENTE" else "text-blue-300"}">
                                    {item['cita']}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <div class="w-full bg-black/40 rounded-full h-1 relative overflow-hidden">
                            <div class="{"bg-emerald-400" if item['estatus'] == "ENTREGADA" else "bg-orange-500"} h-full rounded-full transition-all duration-700" 
                                 style="width: {'100%' if item['estatus'] == "ENTREGADA" else '30%'}"></div>
                        </div>
                        <div class="flex justify-between mt-1.5 px-0.5">
                            <span class="text-[8px] font-bold text-white/30 uppercase tracking-tighter italic">{item['estatus']}</span>
                            <span class="text-[8px] font-bold text-white/50">{"100%" if item['estatus'] == "ENTREGADA" else "30%"}</span>
                        </div>
                    </div>
                </div>
                ''' for item in data])}
            </div>
        </div>
    </body>
    </html>
    """
    return components.html(html_content, height=850, scrolling=True)

# Dataset
data_corregida = [
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 8", "entrega_texto": "9 de marzo", "cita": "10/03/2026", "estatus": "ENTREGADA"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 13", "entrega_texto": "23 de marzo", "cita": "24/03/2026", "estatus": "ENTREGADA"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEM 15", "entrega_texto": "6 de abril", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 9197", "cantidad": "520", "semana": "SEM 17", "entrega_texto": "20 de abril", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo (1)", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo (2)", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 19", "entrega_texto": "4 de mayo (3)", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 21", "entrega_texto": "18 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 23", "entrega_texto": "1 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 25", "entrega_texto": "15 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEM 26", "entrega_texto": "22 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "160", "semana": "SEM 27", "entrega_texto": "29 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
]

render_logistica_flow_mid(data_corregida)
























































































