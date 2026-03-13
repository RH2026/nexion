import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Logística Master Premium", layout="wide")

def render_logistica_flow(data):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #0b0f1a; color: #e2e8f0; }}
            .glass-card {{
                background: rgba(23, 32, 53, 0.8);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                transition: all 0.4s ease;
            }}
            /* Efecto de pulsación para lo pendiente */
            @keyframes pulse-border {{
                0% {{ border-color: rgba(245, 158, 11, 0.2); }}
                50% {{ border-color: rgba(245, 158, 11, 0.6); }}
                100% {{ border-color: rgba(245, 158, 11, 0.2); }}
            }}
            .status-pending {{ 
                border-left: 4px solid #f59e0b; 
                animation: pulse-border 2s infinite;
            }}
            .status-delivered {{ border-left: 4px solid #10b981; }}
            .glow-orange {{ text-shadow: 0 0 10px rgba(245, 158, 11, 0.5); }}
        </style>
    </head>
    <body class="p-6 md:p-12">
        <div class="max-w-full mx-auto">
            <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-4">
                <div>
                    <h1 class="text-5xl font-extrabold tracking-tighter text-white">
                        PANEL DE <span class="text-orange-500 underline decoration-orange-500/30">PENDIENTES</span>
                    </h1>
                    <p class="text-slate-400 mt-2 text-lg">Revisión de flujo y citas por confirmar</p>
                </div>
                <div class="bg-orange-500/10 border border-orange-500/20 rounded-2xl p-4">
                    <p class="text-orange-400 text-xs font-bold uppercase tracking-widest text-center">Atención Requerida</p>
                    <p class="text-2xl font-black text-white text-center italic">ACTUALIZANDO DATOS</p>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-6">
                {"".join([f'''
                <div class="glass-card rounded-3xl p-6 flex flex-col justify-between {"status-delivered" if item['estatus'] == "ENTREGADA" else "status-pending"}">
                    <div>
                        <div class="flex justify-between items-start mb-4">
                            <span class="bg-white/5 text-slate-400 text-[10px] px-2 py-1 rounded-md font-mono">{item['semana']}</span>
                            <span class="text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-tighter 
                                {"bg-emerald-500/20 text-emerald-400" if item['estatus'] == "ENTREGADA" else "bg-orange-500/20 text-orange-400"}">
                                {item['estatus']}
                            </span>
                        </div>
                        
                        <h3 class="text-3xl font-black text-white mb-1 tracking-tight">{item['oc']}</h3>
                        <p class="text-slate-500 text-xs font-semibold mb-6 italic">{item['entrega_texto']}</p>
                        
                        <div class="space-y-4">
                            <div class="flex items-center justify-between">
                                <span class="text-slate-400 text-xs uppercase tracking-widest">Volumen</span>
                                <span class="text-xl font-bold text-slate-200">{item['cantidad']} <small class="text-[10px] opacity-40 uppercase">cajas</small></span>
                            </div>
                            <div class="h-[1px] bg-gradient-to-r from-transparent via-slate-700 to-transparent"></div>
                            <div class="flex items-center justify-between">
                                <span class="text-slate-400 text-xs uppercase tracking-widest font-bold">Fecha Cita:</span>
                                <span class="text-md font-mono {"text-orange-400 glow-orange" if item['cita'] == "PENDIENTE" else "text-blue-400"}">
                                    {item['cita']}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-8 flex items-center gap-2">
                        <div class="w-full bg-slate-800 rounded-full h-1.5">
                            <div class="{"bg-emerald-500" if item['estatus'] == "ENTREGADA" else "bg-orange-500"} h-1.5 rounded-full" 
                                 style="width: {'100%' if item['estatus'] == "ENTREGADA" else '25%'}"></div>
                        </div>
                        <span class="text-[10px] font-bold text-slate-600">{"100%" if item['estatus'] == "ENTREGADA" else "25%"}</span>
                    </div>
                </div>
                ''' for item in data])}
            </div>
        </div>
    </body>
    </html>
    """
    return components.html(html_content, height=1000, scrolling=True)

# Dataset corregido: de la Semana 15 en adelante todo es PENDIENTE
data_corregida = [
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 8", "entrega_texto": "semana del 9 de marzo", "cita": "10/03/2026", "estatus": "ENTREGADA"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 13", "entrega_texto": "semana del 23 de marzo", "cita": "24/03/2026", "estatus": "ENTREGADA"},
    {"oc": "OC 9197", "cantidad": "1,120", "semana": "SEMANA 15", "entrega_texto": "semana del 6 de abril", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 9197", "cantidad": "520", "semana": "SEMANA 17", "entrega_texto": "semana del 20 de abril", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 19", "entrega_texto": "semana del 4 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 19", "entrega_texto": "semana del 4 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 19", "entrega_texto": "semana del 4 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 21", "entrega_texto": "semana del 18 de mayo", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 23", "entrega_texto": "semana del 1 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 25", "entrega_texto": "semana del 15 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "1,120", "semana": "SEMANA 26", "entrega_texto": "semana del 22 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
    {"oc": "OC 10663", "cantidad": "160", "semana": "SEMANA 27", "entrega_texto": "semana del 29 de junio", "cita": "PENDIENTE", "estatus": "PENDIENTE"},
]

render_logistica_flow(data_corregida)
























































































