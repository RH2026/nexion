import os
import asyncio
from nicegui import ui, app

# --- RECURSOS ESTÁTICOS ---
app.add_static_files('/static', 'static')

class SessionState:
    def __init__(self):
        self.dark_mode = True
        self.menu_main = "TRACKING"
        self.menu_sub = "GENERAL"
        self.splash_done = False

state = SessionState()

def apply_styles():
    # Definición de variables maestras para evitar colores perdidos
    bg = "#0A0A0B" if state.dark_mode else "#F5F5F7"
    text = "#FFFFFF" if state.dark_mode else "#1A1A1A"
    border = "#1F1F22" if state.dark_mode else "#D1D1D6"
    accent = "#FFFFFF" if state.dark_mode else "#000000"
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.5s ease;')
    
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;400;700;900&display=swap');
            * {{ font-family: 'Inter', sans-serif; }}
            
            /* Variables para uso en clases */
            :root {{
                --nexion-text: {text};
                --nexion-bg: {bg};
                --nexion-border: {border};
            }}

            .nexion-border {{ border-color: var(--nexion-border) !important; }}
            
            .nexion-btn {{ 
                text-transform: uppercase; letter-spacing: 3px; font-size: 9px;
                border: 0.5px solid var(--nexion-border) !important; 
                color: var(--nexion-text) !important;
                border-radius: 0px !important;
            }}
            .nexion-btn:hover {{ background-color: var(--nexion-text) !important; color: var(--nexion-bg) !important; }}
            
            /* Submenú estilo Píldora Minimalista */
            .pill-nav {{
                font-size: 10px; letter-spacing: 2px; font-weight: 400;
                color: var(--nexion-text) !important;
                opacity: 0.4; transition: all 0.3s ease;
                border-radius: 20px !important;
                padding: 4px 16px !important;
            }}
            .pill-active {{
                opacity: 1 !important;
                background-color: var(--nexion-text) !important;
                color: var(--nexion-bg) !important;
                font-weight: 800 !important;
            }}

            .active-main {{ border-bottom: 2px solid var(--nexion-text) !important; font-weight: 700 !important; }}
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

# --- CONTENIDO CENTRAL ---
@ui.refreshable
def main_content():
    with ui.column().classes('w-full items-center px-8'):
        
        # DISEÑO DE SUBMENÚ TIPO PÍLDORA (Elegante y Moderno)
        if nav_map[state.menu_main]:
            with ui.row().classes('justify-center gap-2 py-6 mb-10'):
                for s in nav_map[state.menu_main]:
                    is_active = "pill-active" if state.menu_sub == s else ""
                    ui.button(s, on_click=lambda x, s=s: navigate(state.menu_main, s)) \
                        .props('flat dense no-caps').classes(f'pill-nav {is_active}')

        # Escenario Dinámico
        with ui.column().classes('w-full max-w-5xl items-center mt-10'):
            # El color del texto aquí usa var(--nexion-text) implícitamente por apply_styles
            if state.menu_main == "TRACKING":
                ui.label('SYSTEM QUERY').classes('text-[9px] tracking-[10px] opacity-30 mb-10')
                ui.input(placeholder='REFERENCE NUMBER').classes('w-full max-w-md text-center nexion-border').props('borderless dark')
                ui.button('SEARCH').classes('nexion-btn px-12 py-3 mt-8').style('background-color: var(--nexion-text); color: var(--nexion-bg);')
            else:
                ui.label(f"{state.menu_main}").classes('text-[10px] tracking-[5px] opacity-30 mb-2')
                ui.label(state.menu_sub).classes('text-5xl font-black tracking-tighter uppercase')

# --- ESTRUCTURA RAÍZ ---
@ui.page('/')
async def index():
    apply_styles()
    
    if not state.splash_done:
        with ui.column().classes('fixed inset-0 items-center justify-center z-[100] bg-[#0A0A0B]') as splash:
            ui.label('N').classes('text-white text-6xl font-black animate-pulse tracking-tighter')
            await asyncio.sleep(1.5)
            splash.delete()
            state.splash_done = True

    # Header
    with ui.header().classes('bg-transparent border-b nexion-border p-6').style('backdrop-filter: blur(15px)'):
        with ui.row().classes('w-full items-center justify-between'):
            with ui.row().classes('items-center gap-6'):
                logo_src = f'/static/n{"1" if state.dark_mode else "2"}.png'
                ui.image(logo_src).style('width: 130px;').on('error', lambda: ui.label('NEXION').classes('text-2xl font-black'))
            
            with ui.row().classes('gap-6'):
                for m in nav_map.keys():
                    is_active = "active-main" if state.menu_main == m else ""
                    ui.button(m, on_click=lambda x, m=m: navigate(m)).props('flat px-0').classes(f'nexion-btn border-none! {is_active}')
                
                ui.button('☾' if state.dark_mode else '☀', on_click=lambda: [setattr(state, 'dark_mode', not state.dark_mode), ui.run_javascript('window.location.reload()')]) \
                    .props('flat').classes('opacity-40')

    # Footer
    with ui.footer().classes('bg-transparent p-6 border-t nexion-border'):
        ui.label('NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026') \
            .classes('text-[8px] tracking-[4px] opacity-20 w-full text-center')

    # Body
    with ui.column().classes('w-full mt-10'):
        main_content()

if __name__ in {"__main__", "nicegui"}:
    port = int(os.environ.get("PORT", 8080))
    ui.run(host='0.0.0.0', port=port, title="NEXION", dark=True, reload=False, show=False)




























































































































































































































































































































































































































































































































