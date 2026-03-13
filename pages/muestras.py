import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Logística Dashboard Balanced", layout="wide")

def render_logistica_flow_mid(data):
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
                backdrop-filter: blur(8px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                transition: transform 0.2s ease;
            }}
            .glass-card:hover {{
                transform: translateY(-3px);
                border-color: rgba(56, 189, 248, 0.3);
            }}
            @keyframes pulse-border {{
                0% {{ border-color: rgba(245, 158, 11, 0.2); }}
                50% {{ border-color: rgba(245, 158, 11, 0.5); }}
                100% {{ border-color: rgba(245, 158, 11, 0.2); }}
            }}
            .status-pending {{ 
                border-left: 4px solid #f59e0b; 
                animation: pulse-border 2s infinite;
            }}
            .status-delivered {{ border-left: 4px solid #10b981; }}
        </style>
    </head>
    <body class="p-4">
        <div class="max-w-full mx-auto">
            <header class="flex justify-between items-center mb-6 px-2">
                <h1 class="text-2xl font-black tracking-tighter text-white uppercase italic">
                    Logística <span class="text-blue-500 underline decoration-blue-500/20">Pro</span>
                </h1>
                <div class="flex gap-4">
                    <div class="text-right">
                        <p class="text-[9px] text-slate-500 font-bold uppercase tracking-widest leading-none">Status</p>
                        <p class="text-xs font-bold text-emerald-400 leading-none mt-1 uppercase">Live Data</p>
                    </div>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {"".join([f'''
                <div class="glass-card rounded-2xl p-4 flex flex-col justify-between {"status-delivered" if item['estatus'] == "ENTREGADA" else "status-pending"}">
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <span class="text-[9px] font-bold text-slate-400 bg-white/5 px-2 py-0.5 rounded uppercase tracking-wider">
                                {item['semana']}
                            </span>
                            <div class="h-2 w-2 rounded-full {"bg-emerald-500 shadow-[0_0_8px_#10b981]" if item['estatus'] == "ENTREGADA" else "bg-orange-500 shadow-[0_0_8px_#f59e0b]"}"></div>
                        </div>
                        
                        <h3 class="text-xl font-black text-white leading-none mb-1 tracking-tight">{item['oc']}</h3>
                        <p class="text-[10px] text-slate-500 font-medium mb-4 truncate italic">{item['entrega_texto']}</p>
                        
                        <div class="space-y-2.5 bg-black/30 rounded-xl p-3 border border-white/5">
                            <div class="flex items-center justify-between">
                                <span class="text-[9px] text-slate-500 uppercase font-bold tracking-tight">Volumen</span>
                                <span class="text-sm font-bold text-slate-200">{item['cantidad']}</span>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-[9px] text-slate-500 uppercase font-bold tracking-tight">Cita</span>
                                <span class="text-[11px] font-mono font-bold {"text-orange-400" if item['cita'] == "PENDIENTE" else "text-blue-400"}">
                                    {item['cita']}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <div class="w-full bg-slate-800 rounded-full h-1 relative overflow-hidden">
                            <div class="{"bg-emerald-500" if item['estatus'] == "ENTREGADA" else "bg-orange-500"} h-full rounded-full" 
                                 style="width: {'100%' if item['estatus'] == "ENTREGADA" else '30%'}"></div>
                        </div>
                        <div class="flex justify-between mt-1.5 px-0.5">
                            <span class="text-[8px] font-bold text-slate-600 uppercase tracking-tighter">{item['estatus']}</span>
                            <span class="text-[8px] font-bold text-slate-500">{"100%" if item['estatus'] == "ENTREGADA" else "30%"}</span>
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
























































































