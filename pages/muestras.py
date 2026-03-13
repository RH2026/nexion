import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Logística Dashboard Pro", layout="wide")

def render_logistica_flow_balanced(data):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #0b0f1a; color: #e2e8f0; }}
            .glass-card {{
                background: rgba(23, 32, 53, 0.85);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                transition: transform 0.3s ease, border-color 0.3s ease;
            }}
            .glass-card:hover {{
                transform: translateY(-5px);
                border-color: rgba(255, 255, 255, 0.2);
            }}
            @keyframes pulse-border {{
                0% {{ border-color: rgba(245, 158, 11, 0.3); box-shadow: 0 0 0px rgba(245, 158, 11, 0); }}
                50% {{ border-color: rgba(245, 158, 11, 0.6); box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); }}
                100% {{ border-color: rgba(245, 158, 11, 0.3); box-shadow: 0 0 0px rgba(245, 158, 11, 0); }}
            }}
            .status-pending {{ 
                border-left: 5px solid #f59e0b; 
                animation: pulse-border 2.5s infinite;
            }}
            .status-delivered {{ border-left: 5px solid #10b981; }}
        </style>
    </head>
    <body class="p-6">
        <div class="max-w-full mx-auto">
            <header class="flex justify-between items-end mb-10">
                <div>
                    <h1 class="text-4xl font-black tracking-tighter text-white uppercase italic">
                        Logística <span class="text-blue-500">Flow</span>
                    </h1>
                    <p class="text-slate-500 text-sm font-medium uppercase tracking-widest">Panel de Control Operativo</p>
                </div>
                <div class="bg-blue-500/10 px-6 py-3 rounded-2xl border border-blue-500/20">
                    <p class="text-[10px] text-blue-400 uppercase font-bold tracking-widest">Total Órdenes</p>
                    <p class="text-3xl font-black text-white leading-none">{len(data)}</p>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {"".join([f'''
                <div class="glass-card rounded-3xl p-5 flex flex-col justify-between {"status-delivered" if item['estatus'] == "ENTREGADA" else "status-pending"}">
                    <div>
                        <div class="flex justify-between items-center mb-4">
                            <span class="bg-white/5 text-slate-400 text-[10px] px-3 py-1 rounded-full font-bold uppercase tracking-wider">
                                {item['semana']}
                            </span>
                            <div class="flex items-center gap-2">
                                <span class="text-[9px] font-black uppercase {"text-emerald-400" if item['estatus'] == "ENTREGADA" else "text-orange-400"}">
                                    {item['estatus']}
                                </span>
                                <div class="h-3 w-3 rounded-full {"bg-emerald-500 shadow-[0_0_12px_#10b981]" if item['estatus'] == "ENTREGADA" else "bg-orange-500 shadow-[0_0_12px_#f59e0b]"}"></div>
                            </div>
                        </div>
                        
                        <h3 class="text-2xl font-black text-white leading-tight mb-1">{item['oc']}</h3>
                        <p class="text-xs text-slate-400 font-semibold mb-6 italic opacity-80">{item['entrega_texto']}</p>
                        
                        <div class="space-y-4 bg-black/20 rounded-2xl p-4 border border-white/5">
                            <div class="flex items-center justify-between">
                                <span class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Volumen</span>
                                <span class="text-lg font-bold text-slate-200">{item['cantidad']} <small class="text-[10px] text-slate-500">unid</small></span>
                            </div>
                            <div class="h-[1px] bg-white/5"></div>
                            <div class="flex items-center justify-between">
                                <span class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Cita Logística</span>
                                <span class="text-sm font-mono font-bold {"text-orange-400" if item['cita'] == "PENDIENTE" else "text-blue-400"}">
                                    {item['cita']}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-6">
                        <div class="w-full bg-slate-800 rounded-full h-2 relative overflow-hidden">
                            <div class="{"bg-emerald-500" if item['estatus'] == "ENTREGADA" else "bg-orange-500"} h-full rounded-full transition-all duration-1000" 
                                 style="width: {'100%' if item['estatus'] == "ENTREGADA" else '35%'}"></div>
                        </div>
                        <div class="flex justify-between mt-2">
                            <span class="text-[9px] font-bold text-slate-600 uppercase tracking-tighter">Status Progress</span>
                            <span class="text-[9px] font-bold text-slate-400">{"100%" if item['estatus'] == "ENTREGADA" else "35%"}</span>
                        </div>
                    </div>
                </div>
                ''' for item in data])}
            </div>
        </div>
    </body>
    </html>
    """
    return components.html(html_content, height=1000, scrolling=True)

# Dataset
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

render_logistica_flow_balanced(data_corregida)
























































































