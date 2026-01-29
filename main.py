import os
import asyncio
from nicegui import ui, app
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE RECURSOS ---
app.add_static_files('/static', 'static')

class SessionState:
    def __init__(self):
        self.dark_mode = True
        self.menu_main = "TRACKING"
        self.menu_sub = "GENERAL"
        self.splash_done = False

state = SessionState()

# --- ESTILOS ELITE (ZARA / DHL INSPIRED) ---
def apply_styles():
    # Paleta Premium: Onix Elegante y Platino Satinado
    bg = "#0A0A0B" if state.dark_mode else "#F5F5F7"
    text = "#FFFFFF" if state.dark_mode else "#1A1A1A"
    border = "#1F1F22" if state.dark_mode else "#D1D1D6"
    accent = "#F2CC0C"  # Toque sutil de amarillo DHL para detalles
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);')
    
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;400;700;900&display=swap');
            * {{ font-family: 'Inter', sans-serif; letter-spacing: -0.01em; }}
            
            .nexion-border {{ border-color: {border} !important; }}
            
            .nexion-btn {{ 
                text-transform: uppercase; letter-spacing: 3px; font-size: 9px; font-weight: 400;
                border: 0.5px solid {border} !important; transition: all 0.4s ease;
                color: {text} !important; border-radius: 0px !important;
            }}
            .nexion-btn:hover {{ 
                background-color: {text} !important; color: {bg} !important; 
                letter-spacing: 4px;
            }}
            
            .active-menu {{ 
                border-bottom: 1.5px solid {text} !important; 
                font-weight: 700 !important;
                opacity: 1 !important; 
            }}
            
            .sub-menu-btn {{ 
                font-size: 9px; opacity: 0.4; color: {text} !important; 
                letter-spacing: 2px; font-weight: 200;
            }}
            
            .input-premium {{
                background-color: transparent !important;
                border-bottom: 1px solid {border} !important;
                font-size: 14px !important;
                letter-spacing: 2px !important;
            }}
            
            .fade-in {{ animation: fadeIn 1.2s ease-out; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        </style>
    ''')

# --- NAVEGACIÓN ---
nav_map = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT"]
}

def navigate_main(selection):
    state.menu_main = selection
    state.menu_sub = nav_map[selection][0] if nav_map[selection] else "GENERAL"
    render_interface.refresh()

def navigate_sub(selection):
    state.menu_sub = selection
    render_interface.refresh()

def toggle_theme():
    state.dark_mode = not state.dark_mode
    render_interface.refresh()

# --- INTERFAZ ---
@ui.refreshable
def render_interface():
    apply_styles()
    
    with ui.column().classes('w-full items-center fade-in px-8'):
        # --- HEADER (LOGOS CARGADOS DESDE STATIC) ---
        with ui.row().classes('w-full items-center justify-between py-10 border-b nexion-border'):
            with ui.row().classes('items-center gap-6'):
                # Intento de cargar logos n1.png (dark) o n2.png (light)
                logo_src = '/static/n1.png' if state.dark_mode else '/static/n2.png'
                ui.image(logo_src).style('width: 140px; height: auto;').classes('opacity-90')
                
                with ui.column().classes('gap-0 border-l nexion-border pl-6'):
                    ui.label('CORE').classes('text-xs font-black tracking-[5px]')
                    ui.label('LOGISTICS OS').classes('text-[7px] tracking-[3px] opacity-40')

            with ui.row().classes('gap-8 items-center'):
                for m in nav_map.keys():
                    active = "active-menu" if state.menu_main == m else ""
                    ui.button(m, on_click=lambda x, m=m: navigate_main(m)).props('flat px-0').classes(f'nexion-btn border-none! {active}')
                
                ui.button('EN' if state.dark_mode else 'ES').props('flat dense').classes('text-[8px] opacity-30')
                ui.button('☾' if state.dark_mode else '☀', on_click=toggle_theme).props('flat').classes('opacity-50')

        # --- SUBNAV ---
        with ui.row().classes('w-full justify-start gap-10 py-6 mb-12'):
            for s in nav_map[state.menu_main]:
                active = "active-menu" if state.menu_sub == s else ""
                ui.button(s, on_click=lambda x, s=s: navigate_sub(s)).props('flat dense').classes(f'sub-menu-btn {active}')

        # --- CONTENT ---
        with ui.column().classes('w-full max-w-5xl'):
            if state.menu_main == "TRACKING":
                with ui.column().classes('w-full items-center mt-20'):
                    ui.label('S Y S T E M &nbsp; Q U E R Y').classes('text-[9px] opacity-30 mb-12 tracking-[10px]')
                    
                    search = ui.input(placeholder='REFERENCE NUMBER').classes('w-full max-w-md input-premium text-center').props('borderless')
                    
                    with ui.row().classes('mt-12 gap-4'):
                        ui.button('SEARCH', on_click=lambda: ui.notify(f"Querying: {search.value}")) \
                            .classes('nexion-btn px-12 py-3').style('background-color: var(--text); color: var(--bg); font-weight: 900;')
                        ui.button('SCAN QR').classes('nexion-btn px-12 py-3 opacity-50')

            elif state.menu_main == "SEGUIMIENTO":
                with ui.row().classes('w-full justify-between items-end mb-8'):
                    ui.label(state.menu_sub).classes('text-4xl font-thin tracking-tighter uppercase')
                    ui.label('DATA SOURCE: SAP S/4HANA').classes('text-[7px] opacity-30 tracking-[2px]')
                
                if state.menu_sub == "GANTT":
                    fig = go.Figure(go.Bar(x=["P-102", "P-105", "P-109"], y=[85, 40, 92], marker_color='#F2CC0C' if not state.dark_mode else '#FFFFFF'))
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                        font_family="Inter", font_color='gray', height=300,
                        margin=dict(l=0, r=0, t=20, b=0)
                    )
                    ui.plotly(fig).classes('w-full')
                else:
                    ui.separator().classes('opacity-10 mb-4')
                    ui.label("EN ESPERA DE PARÁMETROS DE FILTRADO...").classes('text-[10px] opacity-20 tracking-widest')

        # --- FOOTER ---
        with ui.footer().classes('bg-transparent p-8 items-center border-t nexion-border'):
            with ui.row().classes('w-full justify-between opacity-30 text-[8px] tracking-[3px]'):
                ui.label('GDL // MX // 2026')
                ui.label('NEXION LOGISTICS SYSTEMS PRO')
                ui.label('AUTHORIZED ACCESS ONLY')

# --- PÁGINA INICIAL ---
@ui.page('/')
async def main_page():
    if not state.splash_done:
        with ui.column().classes('fixed inset-0 items-center justify-center z-[100]') \
            .style('background-color: #0A0A0B') as splash:
            # Minimalist Loader
            ui.label('N').classes('text-white text-4xl font-black tracking-tighter animate-pulse')
            msg = ui.label('CORE INITIALIZATION').classes('text-[8px] tracking-[6px] text-white/40 mt-8 font-light')
            
            await asyncio.sleep(1.0)
            msg.set_text('SYNCING SAP MODULES')
            await asyncio.sleep(1.0)
            msg.set_text('READY')
            await asyncio.sleep(0.4)
            
            splash.delete()
            state.splash_done = True
            render_interface()
    else:
        render_interface()

if __name__ in {"__main__", "nicegui"}:
    port = int(os.environ.get("PORT", 8080))
    ui.run(host='0.0.0.0', port=port, title="NEXION", dark=True, reload=False, show=False)

























































































































































































































































































































































































































































































































