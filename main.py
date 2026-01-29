import os
import asyncio
from nicegui import ui, app
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE ESTADO ---
# Usamos un diccionario simple para manejar el estado de la sesión
class SessionState:
    def __init__(self):
        self.dark_mode = True
        self.menu_main = "TRACKING"
        self.menu_sub = "GENERAL"
        self.splash_done = False

state = SessionState()

# --- ESTILOS DINÁMICOS ---
def apply_styles():
    # Colores basados en tu diseño original
    bg = "#0E1117" if state.dark_mode else "#E3E7ED"
    text = "#F0F6FC" if state.dark_mode else "#111111"
    border = "#1B1F24" if state.dark_mode else "#C9D1D9"
    card = "#111827" if state.dark_mode else "#FFFFFF"
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: background 0.5s, color 0.5s;')
    
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
            * {{ font-family: 'Inter', sans-serif; }}
            .nexion-border {{ border: 1px solid {border} !important; }}
            .nexion-btn {{ 
                text-transform: uppercase; letter-spacing: 2px; font-size: 10px; font-weight: 700;
                border: 1px solid {border} !important; transition: 0.3s;
                color: {text} !important;
            }}
            .nexion-btn:hover {{ background-color: {text} !important; color: {bg} !important; }}
            .active-menu {{ border-bottom: 2px solid {text} !important; opacity: 1 !important; font-weight: 800; }}
            .sub-menu-btn {{ font-size: 10px; opacity: 0.6; color: {text} !important; }}
            .fade-in {{ animation: fadeIn 0.8s ease-in; }}
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        </style>
    ''')

# --- LÓGICA DE NAVEGACIÓN ---
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

# --- COMPONENTES DE INTERFAZ ---
@ui.refreshable
def render_interface():
    apply_styles()
    
    with ui.column().classes('w-full items-center fade-in'):
        # --- HEADER ---
        with ui.row().classes('w-full items-center justify-between border-b nexion-border p-4 mb-2'):
            with ui.column().classes('gap-0'):
                ui.label('NEXION').classes('text-2xl font-black tracking-tighter')
                ui.label('CORE INTELLIGENCE').classes('text-[8px] tracking-[2px] opacity-60 -mt-2')

            with ui.row().classes('gap-4'):
                for m in nav_map.keys():
                    active_class = "active-menu" if state.menu_main == m else ""
                    ui.button(m, on_click=lambda x, m=m: navigate_main(m)).props('flat').classes(f'nexion-btn {active_class}')

            ui.button('☾' if state.dark_mode else '☀', on_click=toggle_theme).props('flat').classes('text-lg')

        # --- SUBNAV ---
        with ui.row().classes('w-full justify-center gap-6 p-2 mb-10'):
            for s in nav_map[state.menu_main]:
                active_class = "active-menu" if state.menu_sub == s else ""
                ui.button(f"» {s}", on_click=lambda x, s=s: navigate_sub(s)).props('flat dense').classes(f'sub-menu-btn {active_class}')

        # --- CONTENT AREA ---
        with ui.column().classes('w-full max-w-4xl items-center'):
            if state.menu_main == "TRACKING":
                ui.label('OPERATIONAL QUERY').classes('text-[11px] tracking-[8px] opacity-50 mb-6 mt-20')
                search = ui.input(placeholder='INGRESE GUÍA O REFERENCIA...').classes('w-80 text-center nexion-border').props('dark square outlined')
                ui.button('EXECUTE SYSTEM SEARCH', on_click=lambda: ui.notify(f"Buscando: {search.value}")) \
                    .classes('nexion-btn w-80 py-4 mt-4').style('background-color: var(--text); color: var(--bg);')

            elif state.menu_main == "SEGUIMIENTO":
                ui.label(f"MÓDULO SEGUIMIENTO > {state.menu_sub}").classes('text-lg font-light tracking-[5px] mb-4')
                if state.menu_sub == "GANTT":
                    fig = go.Figure(go.Bar(x=["A", "B", "C"], y=[10, 20, 15]))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#8B949E', margin=dict(l=0, r=0, t=0, b=0))
                    ui.plotly(fig).classes('w-full h-64')
                else:
                    ui.label("DATOS DE TRK CARGADOS CORRECTAMENTE").classes('text-xs opacity-40 italic')

            else:
                ui.label(f"SECCIÓN {state.menu_main} - {state.menu_sub}").classes('opacity-30')

        # --- FOOTER ---
        ui.label('NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026') \
            .classes('fixed-bottom w-full text-center p-4 text-[9px] tracking-[4px] opacity-40 border-t nexion-border')

# --- PÁGINA DE ENTRADA CON SPLASH ---
@ui.page('/')
async def main_page():
    if not state.splash_done:
        # Contenedor del Splash
        with ui.column().classes('fixed inset-0 items-center justify-center z-[100] shadow-2xl') \
            .style('background-color: #0E1117') as splash:
            ui.spinner(size='60px', color='white', thickness=2).classes('mb-10')
            msg = ui.label('ESTABLISHING SECURE ACCESS').classes('text-[10px] tracking-[5px] text-white font-mono')
            
            # Usamos asyncio.sleep para evitar el TimeoutError de JS
            await asyncio.sleep(1.2)
            msg.set_text('PARSING LOGISTICS DATA')
            await asyncio.sleep(1.2)
            msg.set_text('SYSTEM READY')
            await asyncio.sleep(0.5)
            
            splash.delete()
            state.splash_done = True
            render_interface()
    else:
        render_interface()

# --- LANZAMIENTO (Optimizado para Railway) ---
if __name__ in {"__main__", "nicegui"}:
    # Obtenemos el puerto de Railway o usamos 8080 por defecto
    port = int(os.environ.get("PORT", 8080))
    ui.run(
        host='0.0.0.0', 
        port=port, 
        title="NEXION | Core", 
        dark=True, 
        reload=False, 
        show=False
    )
























































































































































































































































































































































































































































































































