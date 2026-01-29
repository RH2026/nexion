import os
import asyncio
from nicegui import ui, app

# --- RECURSOS ---
app.add_static_files('/static', 'static')

class SessionState:
    def __init__(self):
        self.dark_mode = True
        self.menu_main = "TRACKING"
        self.menu_sub = "GENERAL"
        self.splash_done = False

state = SessionState()

def apply_styles():
    bg = "#0A0A0B" if state.dark_mode else "#F5F5F7"
    text = "#FFFFFF" if state.dark_mode else "#1A1A1A"
    border = "#1F1F22" if state.dark_mode else "#D1D1D6"
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.5s ease;')
    
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;200;400;900&display=swap');
            
            * {{ 
                font-family: 'Inter', sans-serif; 
                color: inherit; 
                -webkit-font-smoothing: antialiased;
            }}
            
            :root {{
                --nexion-text: {text};
                --nexion-bg: {bg};
                --nexion-border: {border};
            }}

            .nexion-border {{ border-color: var(--nexion-border) !important; }}
            
            /* Estilo Ultra-Minimalista para Dropdowns */
            .q-menu {{ 
                background-color: var(--nexion-bg) !important; 
                border: 1px solid var(--nexion-border) !important;
                box-shadow: 0px 10px 30px rgba(0,0,0,0.5) !important;
                border-radius: 0px !important;
                padding: 10px 0px !important;
            }}
            .q-item {{ 
                color: var(--nexion-text) !important; 
                font-size: 8px !important; 
                letter-spacing: 5px !important; 
                text-transform: uppercase;
                font-weight: 200 !important;
                padding: 12px 25px !important;
            }}
            .q-item:hover {{ 
                background-color: var(--nexion-text) !important; 
                color: var(--nexion-bg) !important; 
            }}

            /* Botones del Menú Principal */
            .nexion-btn {{ 
                text-transform: uppercase; 
                letter-spacing: 6px !important; 
                font-size: 8px !important; 
                font-weight: 200 !important;
                color: var(--nexion-text) !important;
                transition: all 0.4s ease;
            }}
            .nexion-btn:hover {{ opacity: 0.5; }}
            
            /* Títulos Principales Estilo 'E N E R A L' */
            .ultra-spacing {{
                letter-spacing: 25px !important;
                text-transform: uppercase;
                font-weight: 100 !important;
            }}

            .input-premium {{ 
                color: var(--nexion-text) !important; 
                border-bottom: 0.5px solid var(--nexion-border) !important;
                letter-spacing: 4px !important;
                font-size: 12px !important;
                text-transform: uppercase;
            }}
            
            .fade-in {{ animation: fadeIn 1.5s ease; }}
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        </style>
    ''')

nav_map = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT"]
}

def navigate(main, sub=None):
    state.menu_main = main
    state.menu_sub = sub if sub else (nav_map[main][0] if nav_map[main] else "GENERAL")
    main_content.refresh()

@ui.refreshable
def main_content():
    with ui.column().classes('w-full items-center px-8 mt-32 fade-in'):
        # Título de Sección con Espaciado Extremo
        ui.label(state.menu_main).classes('text-[9px] ultra-spacing opacity-20 mb-4')
        ui.label(state.menu_sub).classes('text-6xl ultra-spacing mb-24')

        if state.menu_main == "TRACKING":
            with ui.column().classes('w-full max-w-lg items-center'):
                search = ui.input(placeholder='REFERENCE').classes('w-full text-center input-premium').props('borderless dark')
                ui.button('E X E C U T E', on_click=lambda: ui.notify(f"Query: {search.value}")) \
                    .classes('nexion-btn w-full py-6 mt-16').style('background-color: var(--nexion-text); color: var(--nexion-bg); font-weight: 900 !important;')

@ui.page('/')
async def index():
    apply_styles()
    
    if not state.splash_done:
        with ui.column().classes('fixed inset-0 items-center justify-center z-[100] bg-[#0A0A0B]') as splash:
            ui.label('N').classes('text-white text-8xl font-thin tracking-[40px] animate-pulse ml-[40px]')
            await asyncio.sleep(1.8)
            splash.delete()
            state.splash_done = True

    # Header
    with ui.header().classes('bg-transparent border-b nexion-border p-8').style('backdrop-filter: blur(20px)'):
        with ui.row().classes('w-full items-center justify-between'):
            # Logo
            with ui.row().classes('items-center gap-8'):
                logo_src = f'/static/n{"1" if state.dark_mode else "2"}.png'
                ui.image(logo_src).style('width: 110px; opacity: 0.8;')

            # Menú Dropdowns Estilo Ultra-Minimalista
            with ui.row().classes('gap-10'):
                for main_item, subs in nav_map.items():
                    with ui.button(main_item).props('flat dense').classes('nexion-btn'):
                        if subs:
                            with ui.menu().props('auto-close'):
                                for s in subs:
                                    ui.menu_item(s, on_click=lambda x, m=main_item, s=s: navigate(m, s))
                        else:
                            ui.on('click', lambda x, m=main_item: navigate(m))
                
                ui.button('☾' if state.dark_mode else '☀', 
                          on_click=lambda: [setattr(state, 'dark_mode', not state.dark_mode), ui.run_javascript('window.location.reload()')]) \
                    .props('flat').classes('opacity-20 ml-6')

    # Footer
    with ui.footer().classes('bg-transparent p-10 border-t nexion-border'):
        ui.label('N E X I O N // L O G I S T I C S // 2 0 2 6').classes('text-[7px] tracking-[8px] opacity-10 w-full text-center')

    main_content()

if __name__ in {"__main__", "nicegui"}:
    port = int(os.environ.get("PORT", 8080))
    ui.run(host='0.0.0.0', port=port, title="NEXION", dark=True, reload=False, show=False)





























































































































































































































































































































































































































































































































