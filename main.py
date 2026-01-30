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
    # Paleta Premium: Onix profundo y Platino satinado
    bg = "#0A0A0B" if state.dark_mode else "#F2F2F7"
    text = "#FFFFFF" if state.dark_mode else "#121212"
    border = "#1A1A1D" if state.dark_mode else "#D1D1D6"
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.8s ease;')
    
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;200;400;900&display=swap');
            
            * {{ 
                font-family: 'Inter', sans-serif; 
                color: inherit; 
                -webkit-font-smoothing: antialiased; 
            }}
            
            :root {{
                --n-text: {text};
                --n-bg: {bg};
                --n-border: {border};
            }}

            /* Minimalismo Zara: Bordes rectos y espaciado agresivo */
            .nexion-border {{ border-color: var(--n-border) !important; }}
            
            /* Menú Dropdown Estilo Boutique */
            .q-menu {{ 
                background-color: var(--n-bg) !important; 
                border: 0.5px solid var(--n-border) !important;
                box-shadow: 0px 20px 40px rgba(0,0,0,0.4) !important;
                border-radius: 0px !important;
            }}
            .q-item {{ 
                font-size: 8px !important; 
                letter-spacing: 5px !important; 
                text-transform: uppercase;
                font-weight: 200 !important;
                padding: 15px 30px !important;
            }}
            .q-item:hover {{ background-color: var(--n-text) !important; color: var(--n-bg) !important; }}

            /* Navegación "Luxury Tech" */
            .nexion-btn {{ 
                text-transform: uppercase; 
                letter-spacing: 5px !important; 
                font-size: 8px !important; 
                font-weight: 200 !important;
                color: var(--n-text) !important;
                opacity: 0.5;
                transition: opacity 0.4s ease;
            }}
            .nexion-btn:hover {{ opacity: 1; }}
            
            /* Títulos Principales: Espaciado Extremo (Zara Look) */
            .ultra-spacing {{
                letter-spacing: 20px !important;
                text-transform: uppercase;
                font-weight: 100 !important;
                line-height: 1.2;
            }}

            .input-premium {{ 
                color: var(--n-text) !important; 
                border-bottom: 0.5px solid var(--n-border) !important;
                letter-spacing: 6px !important;
                font-size: 11px !important;
                text-transform: uppercase;
                text-align: center !important;
            }}
            
            /* Botón EXECUTE (Estilo Etiqueta DHL/FedEx) */
            .btn-execute {{
                background-color: var(--n-text) !important;
                color: var(--n-bg) !important;
                border-radius: 0px !important;
                letter-spacing: 8px !important;
                font-size: 9px !important;
                font-weight: 900 !important;
                padding: 1.5rem 4rem !important;
            }}
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
    with ui.column().classes('w-full items-center px-8 mt-40 animate-fade-in'):
        ui.label(state.menu_main).classes('text-[8px] ultra-spacing opacity-30 mb-6')
        ui.label(state.menu_sub).classes('text-6xl ultra-spacing mb-32')

        if state.menu_main == "TRACKING":
            with ui.column().classes('w-full max-lg items-center gap-16'):
                search = ui.input(placeholder='REFERENCE NUMBER').classes('w-full input-premium').props('borderless dark')
                ui.button('E X E C U T E', on_click=lambda: ui.notify(f"Querying: {search.value}")) \
                    .classes('btn-execute w-full')

@ui.page('/')
async def index():
    apply_styles()
    
    if not state.splash_done:
        with ui.column().classes('fixed inset-0 items-center justify-center z-[100] bg-[#0A0A0B]') as splash:
            ui.label('N').classes('text-white text-9xl font-thin tracking-[50px] animate-pulse ml-[50px]')
            await asyncio.sleep(1.8)
            splash.delete()
            state.splash_done = True

    with ui.header().classes('bg-transparent border-b nexion-border p-8').style('backdrop-filter: blur(25px)'):
        with ui.row().classes('w-full items-center justify-between'):
            with ui.row().classes('items-center gap-10'):
                logo_src = f'/static/n{"1" if state.dark_mode else "2"}.png'
                ui.image(logo_src).style('width: 100px; opacity: 0.9;')

            with ui.row().classes('gap-12'):
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
                    .props('flat').classes('opacity-20 ml-8')

    with ui.footer().classes('bg-transparent p-12 border-t nexion-border'):
        ui.label('N E X I O N // G D L // L O G I S T I C S // 2 0 2 6').classes('text-[7px] tracking-[10px] opacity-10 w-full text-center')

    main_content()

if __name__ in {"__main__", "nicegui"}:
    port = int(os.environ.get("PORT", 8080))
    ui.run(host='0.0.0.0', port=port, title="NEXION", dark=True, reload=False, show=False)
































































































































































































































































































































































































































































































































