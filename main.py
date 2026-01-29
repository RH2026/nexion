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
    # Colores maestros con contraste garantizado
    bg = "#0A0A0B" if state.dark_mode else "#F5F5F7"
    text = "#FFFFFF" if state.dark_mode else "#1A1A1A"
    border = "#1F1F22" if state.dark_mode else "#D1D1D6"
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.5s ease;')
    
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;400;700;900&display=swap');
            * {{ font-family: 'Inter', sans-serif; color: inherit; }}
            
            :root {{
                --nexion-text: {text};
                --nexion-bg: {bg};
                --nexion-border: {border};
            }}

            .nexion-border {{ border-color: var(--nexion-border) !important; }}
            
            /* Dropdown Menu Style */
            .q-menu {{ 
                background-color: var(--nexion-bg) !important; 
                border: 1px solid var(--nexion-border) !important;
                box-shadow: none !important;
                border-radius: 0px !important;
            }}
            .q-item {{ color: var(--nexion-text) !important; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; }}
            .q-item:hover {{ background-color: var(--nexion-text) !important; color: var(--nexion-bg) !important; }}

            .nexion-btn {{ 
                text-transform: uppercase; letter-spacing: 3px; font-size: 9px; font-weight: 700;
                color: var(--nexion-text) !important;
            }}
            
            .input-premium {{ color: var(--nexion-text) !important; border-bottom: 1px solid var(--nexion-border); }}
        </style>
    ''')

# Mapa de navegación
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

# --- CONTENIDO DINÁMICO ---
@ui.refreshable
def main_content():
    with ui.column().classes('w-full items-center px-8 mt-20 fade-in'):
        # Título de Sección
        ui.label(state.menu_main).classes('text-[10px] tracking-[10px] opacity-30 mb-2')
        ui.label(state.menu_sub).classes('text-5xl font-black tracking-tighter uppercase mb-20')

        if state.menu_main == "TRACKING":
            with ui.column().classes('w-full max-w-md items-center'):
                search = ui.input(placeholder='REFERENCE NUMBER').classes('w-full text-center input-premium').props('borderless dark')
                ui.button('EXECUTE SEARCH', on_click=lambda: ui.notify(f"Query: {search.value}")) \
                    .classes('nexion-btn w-full py-4 mt-10').style('background-color: var(--nexion-text); color: var(--nexion-bg);')

# --- PÁGINA PRINCIPAL ---
@ui.page('/')
async def index():
    apply_styles()
    
    # 1. Splash
    if not state.splash_done:
        with ui.column().classes('fixed inset-0 items-center justify-center z-[100] bg-[#0A0A0B]') as splash:
            ui.label('N').classes('text-white text-7xl font-black tracking-tighter animate-pulse')
            await asyncio.sleep(1.5)
            splash.delete()
            state.splash_done = True

    # 2. Header con Menús Desplegables
    with ui.header().classes('bg-transparent border-b nexion-border p-6').style('backdrop-filter: blur(15px)'):
        with ui.row().classes('w-full items-center justify-between'):
            # Logo
            with ui.row().classes('items-center gap-6'):
                logo_src = f'/static/n{"1" if state.dark_mode else "2"}.png'
                ui.image(logo_src).style('width: 130px;').on('error', lambda: ui.label('NEXION').classes('text-2xl font-black'))

            # Menú de Navegación (Dropdowns)
            with ui.row().classes('gap-4'):
                for main_item, subs in nav_map.items():
                    with ui.button(main_item).props('flat dense').classes('nexion-btn'):
                        # Si tiene submenús, creamos el desplegable
                        if subs:
                            with ui.menu().props('auto-close'):
                                for s in subs:
                                    ui.menu_item(s, on_click=lambda x, m=main_item, s=s: navigate(m, s))
                        else:
                            # Si no tiene subs (como Tracking), el botón navega directo
                            ui.on('click', lambda x, m=main_item: navigate(m))
                
                # Cambio de tema
                ui.button('☾' if state.dark_mode else '☀', 
                          on_click=lambda: [setattr(state, 'dark_mode', not state.dark_mode), ui.run_javascript('window.location.reload()')]) \
                    .props('flat').classes('opacity-40 ml-4')

    # 3. Footer
    with ui.footer().classes('bg-transparent p-6 border-t nexion-border'):
        ui.label('NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026').classes('text-[8px] tracking-[4px] opacity-20 w-full text-center')

    # 4. Body
    main_content()

# --- RUN ---
if __name__ in {"__main__", "nicegui"}:
    port = int(os.environ.get("PORT", 8080))
    ui.run(host='0.0.0.0', port=port, title="NEXION", dark=True, reload=False, show=False)





























































































































































































































































































































































































































































































































