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
    # Colores Zara: Blanco puro o Negro absoluto
    bg = "#0A0A0B" if state.dark_mode else "#FFFFFF"
    text = "#FFFFFF" if state.dark_mode else "#000000"
    border = "#1A1A1D" if state.dark_mode else "#EEEEEE"
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.5s ease;')
    
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;300;400&display=swap');
            
            * {{ font-family: 'Inter', sans-serif; -webkit-font-smoothing: antialiased; }}
            
            :root {{
                --n-text: {text};
                --n-bg: {bg};
            }}

            /* ELIMINAR ESTILO DE BOTÓN: Ahora son solo texto */
            .zara-nav {{
                font-size: 11px !important;
                letter-spacing: 3px !important;
                text-transform: uppercase;
                font-weight: 300 !important;
                color: var(--n-text) !important;
                cursor: pointer;
                transition: opacity 0.3s;
                padding: 5px 10px;
            }}
            .zara-nav:hover {{ opacity: 0.5; }}

            /* Dropdown minimalista (solo texto) */
            .q-menu {{ 
                background-color: var(--n-bg) !important; 
                border: 0.5px solid var(--n-text) !important;
                box-shadow: none !important;
                border-radius: 0px !important;
            }}
            .q-item {{ 
                font-size: 10px !important; 
                letter-spacing: 2px !important; 
                color: var(--n-text) !important;
                padding: 15px 20px !important;
            }}

            /* Input tipo Zara (solo una línea abajo) */
            .zara-input {{
                border-bottom: 1px solid var(--n-text) !important;
                font-size: 12px !important;
                letter-spacing: 5px !important;
                text-transform: uppercase;
            }}
            
            /* Botón de ejecución: Texto plano con borde sutil */
            .zara-execute {{
                border: 1px solid var(--n-text) !important;
                font-size: 10px !important;
                letter-spacing: 8px !important;
                padding: 15px 40px !important;
                background: transparent !important;
                color: var(--n-text) !important;
                border-radius: 0px !important;
                text-transform: uppercase;
            }}
            .zara-execute:hover {{
                background: var(--n-text) !important;
                color: var(--n-bg) !important;
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
    with ui.column().classes('w-full items-center px-8 mt-40'):
        # Títulos con kerning extremo
        ui.label(state.menu_main).style('letter-spacing: 15px; font-size: 10px; opacity: 0.4;')
        ui.label(state.menu_sub).style('letter-spacing: 25px; font-size: 60px; font-weight: 100; margin-bottom: 80px;')

        if state.menu_main == "TRACKING":
            with ui.column().classes('w-full max-w-lg items-center gap-16'):
                ui.input(placeholder='REFERENCE NUMBER').classes('w-full zara-input text-center').props('borderless')
                ui.button('E X E C U T E', on_click=lambda: ui.notify('SEARCHING...')) \
                    .classes('zara-execute w-full')

@ui.page('/')
async def index():
    apply_styles()
    
    # Header Limpio (Como tu imagen de Zara)
    with ui.header().classes('bg-transparent p-10 items-center justify-between').style('backdrop-filter: blur(10px)'):
        # Logo a la izquierda
        logo_src = f'/static/n{"1" if state.dark_mode else "2"}.png'
        ui.image(logo_src).style('width: 100px; opacity: 0.8;')

        # Menú a la derecha (Solo texto, sin cajas)
        with ui.row().classes('gap-8 items-center'):
            for main_item, subs in nav_map.items():
                with ui.label(main_item).classes('zara-nav'):
                    if subs:
                        with ui.menu().props('auto-close'):
                            for s in subs:
                                ui.menu_item(s, on_click=lambda x, m=main_item, s=s: navigate(m, s))
                    else:
                        ui.on('click', lambda x, m=main_item: navigate(m))
            
            # Switch de tema sutil
            ui.label('☾' if state.dark_mode else '☀').classes('zara-nav opacity-30').on('click', lambda: [setattr(state, 'dark_mode', not state.dark_mode), ui.run_javascript('window.location.reload()')])

    # Cuerpo
    main_content()

if __name__ in {"__main__", "nicegui"}:
    ui.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), title="NEXION", reload=False, show=False)
































































































































































































































































































































































































































































































































