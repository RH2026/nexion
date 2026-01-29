import os
import asyncio
from nicegui import ui, app
import plotly.graph_objects as go

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
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.6s ease;')
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
            .fade-in {{ animation: fadeIn 0.8s ease-out; }}
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        </style>
    ''')

nav_map = {"TRACKING": [], "SEGUIMIENTO": ["TRK", "GANTT"], "REPORTES": ["APQ", "OPS", "OTD"], "FORMATOS": ["SALIDA DE PT"]}

def navigate_main(selection):
    state.menu_main = selection
    state.menu_sub = nav_map[selection][0] if nav_map[selection] else "GENERAL"
    render_interface.refresh()

def toggle_theme():
    state.dark_mode = not state.dark_mode
    render_interface.refresh()

@ui.refreshable
def render_interface():
    apply_styles()
    
    # --- 1. HEADER (Nivel Superior - Directo al render) ---
    with ui.header().classes('bg-transparent border-b nexion-border p-6 items-center justify-between').style('backdrop-filter: blur(10px)'):
        with ui.row().classes('items-center gap-6'):
            logo_src = f'/static/n{"1" if state.dark_mode else "2"}.png'
            ui.image(logo_src).style('width: 130px;')
        
        with ui.row().classes('gap-6'):
            for m in nav_map.keys():
                active = "active-menu" if state.menu_main == m else ""
                ui.button(m, on_click=lambda x, m=m: navigate_main(m)).props('flat px-0').classes(f'nexion-btn border-none! {active}')
            ui.button('☾' if state.dark_mode else '☀', on_click=toggle_theme).props('flat').classes('opacity-50')

    # --- 2. CONTENEDOR PRINCIPAL (Cuerpo de la página) ---
    with ui.column().classes('w-full items-center px-8 mt-4 fade-in'):
        # Subnavegación
        with ui.row().classes('w-full justify-start gap-8 py-4 mb-10'):
            for s in nav_map[state.menu_main]:
                active = "active-menu" if state.menu_sub == s else ""
                ui.button(s, on_click=lambda x, s=s: (setattr(state, 'menu_sub', s), render_interface.refresh())).props('flat dense').classes(f'text-[9px] opacity-40 {active}')

        # Área de Contenido
        with ui.column().classes('w-full max-w-5xl items-center mt-10'):
            if state.menu_main == "TRACKING":
                ui.label('SYSTEM QUERY').classes('text-[9px] tracking-[10px] opacity-30 mb-10')
                ui.input(placeholder='REFERENCE NUMBER').classes('w-full max-w-md text-center border-b nexion-border').props('borderless dark')
                ui.button('SEARCH').classes('nexion-btn px-12 py-3 mt-8').style('background-color: var(--text); color: var(--bg);')
            
            elif state.menu_main == "SEGUIMIENTO":
                ui.label(f"MÓDULO {state.menu_sub}").classes('text-4xl font-thin tracking-tighter uppercase')

    # --- 3. FOOTER (Nivel Superior - Directo al render) ---
    with ui.footer().classes('bg-transparent p-6 border-t nexion-border'):
        ui.label('NEXION // LOGISTICS OS // 2026').classes('text-[8px] tracking-[4px] opacity-30 w-full text-center')

@ui.page('/')
async def main_page():
    if not state.splash_done:
        with ui.column().classes('fixed inset-0 items-center justify-center z-[100] bg-[#0A0A0B]') as splash:
            ui.label('N').classes('text-white text-5xl font-black animate-pulse')
            await asyncio.sleep(2.0)
            splash.delete()
            state.splash_done = True
            render_interface()
    else:
        render_interface()

if __name__ in {"__main__", "nicegui"}:
    ui.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), title="NEXION", dark=True, reload=False, show=False)


























































































































































































































































































































































































































































































































