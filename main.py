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
    bg = "#0A0A0B" if state.dark_mode else "#F5F5F7"
    text = "#FFFFFF" if state.dark_mode else "#1A1A1A"
    border = "#1F1F22" if state.dark_mode else "#D1D1D6"
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.5s ease;')
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;400;700;900&display=swap');
            * {{ font-family: 'Inter', sans-serif; }}
            .nexion-border {{ border-color: {border} !important; }}
            .nexion-btn {{ 
                text-transform: uppercase; letter-spacing: 3px; font-size: 9px;
                border: 0.5px solid {border} !important; color: {text} !important;
                border-radius: 0px !important;
            }}
            .nexion-btn:hover {{ background-color: {text} !important; color: {bg} !important; }}
            .active-menu {{ border-bottom: 2px solid {text} !important; font-weight: 700 !important; opacity: 1 !important; }}
        </style>
    ''')

nav_map = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT"]
}

# --- NAVEGACIÓN SEGURA ---
def navigate(main, sub=None):
    state.menu_main = main
    state.menu_sub = sub if sub else (nav_map[main][0] if nav_map[main] else "GENERAL")
    main_content.refresh()
    # No refrescamos el header para evitar el error 500, la UI se mantiene estable

# --- CONTENIDO CENTRAL (SÍ ES REFRESHABLE) ---
@ui.refreshable
def main_content():
    with ui.column().classes('w-full items-center px-8'):
        # Sub-navegación sutil
        if nav_map[state.menu_main]:
            with ui.row().classes('w-full justify-start gap-8 py-4 mb-10 border-b nexion-border'):
                for s in nav_map[state.menu_main]:
                    is_active = "active-menu" if state.menu_sub == s else ""
                    ui.button(s, on_click=lambda x, s=s: navigate(state.menu_main, s)) \
                        .props('flat dense').classes(f'text-[9px] opacity-40 {is_active}')

        # Pantallas Dinámicas
        with ui.column().classes('w-full max-w-5xl items-center mt-10'):
            if state.menu_main == "TRACKING":
                ui.label('SYSTEM QUERY').classes('text-[9px] tracking-[10px] opacity-30 mb-10')
                ui.input(placeholder='REFERENCE NUMBER').classes('w-full max-w-md text-center border-b nexion-border').props('borderless dark')
                ui.button('SEARCH').classes('nexion-btn px-12 py-3 mt-8').style('background-color: var(--text); color: var(--bg);')
            else:
                ui.label(f"{state.menu_main} > {state.menu_sub}").classes('text-4xl font-thin tracking-tighter uppercase opacity-80')

# --- ESTRUCTURA RAÍZ (ESTÁTICA PARA EVITAR ERROR 500) ---
@ui.page('/')
async def index():
    apply_styles()
    
    # 1. Splash Screen
    if not state.splash_done:
        with ui.column().classes('fixed inset-0 items-center justify-center z-[100] bg-[#0A0A0B]') as splash:
            ui.label('N').classes('text-white text-6xl font-black animate-pulse tracking-tighter')
            await asyncio.sleep(1.5)
            splash.delete()
            state.splash_done = True

    # 2. Header Fijo (Hijo directo de la página)
    with ui.header().classes('bg-transparent border-b nexion-border p-6').style('backdrop-filter: blur(10px)'):
        with ui.row().classes('w-full items-center justify-between'):
            with ui.row().classes('items-center gap-6'):
                logo_src = f'/static/n{"1" if state.dark_mode else "2"}.png'
                ui.image(logo_src).style('width: 130px;').on('error', lambda: ui.label('NEXION').classes('text-2xl font-black'))
            
            with ui.row().classes('gap-6'):
                for m in nav_map.keys():
                    # Aquí no usamos active-menu por refresco, sino por navegación simple
                    ui.button(m, on_click=lambda x, m=m: navigate(m)).props('flat px-0').classes('nexion-btn border-none!')
                
                ui.button('☾' if state.dark_mode else '☀', on_click=lambda: [setattr(state, 'dark_mode', not state.dark_mode), ui.run_javascript('window.location.reload()')]) \
                    .props('flat').classes('opacity-40')

    # 3. Footer Fijo (Hijo directo de la página)
    with ui.footer().classes('bg-transparent p-6 border-t nexion-border'):
        ui.label('NEXION // LOGISTICS OS // 2026').classes('text-[8px] tracking-[4px] opacity-20 w-full text-center')

    # 4. Cuerpo de la App
    with ui.column().classes('w-full mt-10'):
        main_content()

# --- ARRANQUE ---
if __name__ in {"__main__", "nicegui"}:
    port = int(os.environ.get("PORT", 8080))
    ui.run(host='0.0.0.0', port=port, title="NEXION", dark=True, reload=False, show=False)




























































































































































































































































































































































































































































































































