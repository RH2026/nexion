import os
from nicegui import ui, app
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE ESTILOS (Tailwind + CSS) ---
def aplicar_estilos(tema_oscuro: bool):
    bg = "#0E1117" if tema_oscuro else "#E3E7ED"
    text = "#F0F6FC" if tema_oscuro else "#111111"
    border = "#1B1F24" if tema_oscuro else "#C9D1D9"
    card = "#111827" if tema_oscuro else "#FFFFFF"
    
    ui.query('body').style(f'background-color: {bg}; color: {text}; transition: all 0.5s ease;')
    # Inyectamos CSS para componentes que requieren personalización profunda
    ui.add_head_html(f'''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
            * {{ font-family: 'Inter', sans-serif; }}
            .nexion-border {{ border: 1px solid {border} !important; }}
            .nexion-btn {{ 
                text-transform: uppercase; letter-spacing: 1px; font-size: 10px; font-weight: 700;
                border: 1px solid {border} !important; transition: 0.3s;
            }}
            .nexion-btn:hover {{ background-color: {text} !important; color: {bg} !important; }}
            .active-menu {{ border-bottom: 2px solid {text} !important; opacity: 1 !important; }}
            .sub-menu-btn {{ font-size: 10px; opacity: 0.6; }}
        </style>
    ''')

class NexionCore:
    def __init__(self):
        self.dark_mode = True
        self.menu_main = "TRACKING"
        self.menu_sub = "GENERAL"
        self.splash_complete = False
        
        # Estructura de navegación
        self.nav_structure = {
            "TRACKING": [],
            "SEGUIMIENTO": ["TRK", "GANTT"],
            "REPORTES": ["APQ", "OPS", "OTD"],
            "FORMATOS": ["SALIDA DE PT"]
        }

    async def splash_screen(self):
        """Splash screen con animaciones de carga"""
        with ui.column().classes('fixed-center items-center z-50 w-full h-full justify-center shadow-2xl') \
            .style('background-color: #0E1117') as splash:
            ui.spinner(size='60px', color='white', thickness=2).classes('mb-10')
            msg = ui.label('ESTABLISHING SECURE ACCESS').classes('text-[10px] tracking-[5px] text-white font-mono')
            
            steps = ["PARSING LOGISTICS DATA", "SYSTEM READY"]
            for step in steps:
                await ui.run_javascript(f'await new Promise(r => setTimeout(r, 800))')
                msg.set_text(step)
            
            await ui.run_javascript(f'await new Promise(r => setTimeout(r, 500))')
            splash.delete()
            self.build_interface()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        ui.run_javascript('window.location.reload()') # Recarga suave para aplicar variables de CSS

    def navigate_main(self, menu):
        self.menu_main = menu
        self.menu_sub = self.nav_structure[menu][0] if self.nav_structure[menu] else "GENERAL"
        self.render_content()

    def navigate_sub(self, sub):
        self.menu_sub = sub
        self.render_content()

    def build_interface(self):
        aplicar_estilos(self.dark_mode)
        
        # --- HEADER PRINCIPAL ---
        with ui.header().classes('bg-transparent border-b nexion-border p-4 items-center justify-between').style('backdrop-filter: blur(10px)'):
            with ui.column().classes('gap-0'):
                ui.label('NEXION').classes('text-2xl font-black tracking-tighter')
                ui.label('CORE INTELLIGENCE').classes('text-[8px] tracking-[2px] opacity-60 -mt-2')

            # Menú Horizontal Superior
            with ui.row().classes('gap-6'):
                for m in self.nav_structure.keys():
                    is_active = "active-menu" if self.menu_main == m else ""
                    ui.button(m, on_click=lambda x, m=m: self.navigate_main(m)) \
                        .props('flat px-2').classes(f'nexion-btn {is_active}')

            ui.button('☾' if self.dark_mode else '☀', on_click=self.toggle_theme).props('flat')

        # --- ÁREA DE SUBMENÚS ---
        self.sub_container = ui.row().classes('w-full justify-center p-2 gap-4 opacity-80')
        
        # --- CONTENIDO DINÁMICO ---
        self.content_area = ui.column().classes('w-full items-center mt-10 p-6')
        self.render_content()

        # --- FOOTER ---
        with ui.footer().classes('bg-transparent nexion-border text-center p-2'):
            ui.label('NEXION // LOGISTICS OS // GUADALAJARA, JAL. // © 2026') \
                .classes('text-[9px] tracking-[4px] opacity-40 w-full')

    def render_content(self):
        # Limpiar áreas dinámicas
        self.sub_container.clear()
        self.content_area.clear()

        # Renderizar Submenús si existen
        with self.sub_container:
            for s in self.nav_structure[self.menu_main]:
                is_active = "active-menu" if self.menu_sub == s else ""
                ui.button(f"» {s}", on_click=lambda x, s=s: self.navigate_sub(s)) \
                    .props('flat dense').classes(f'sub-menu-btn {is_active}')

        # Renderizar Contenido según Selección
        with self.content_area:
            if self.menu_main == "TRACKING":
                ui.label('OPERATIONAL QUERY').classes('text-[11px] tracking-[8px] opacity-60 mb-8')
                with ui.column().classes('w-full max-w-md items-center gap-4'):
                    ref = ui.input(placeholder='INGRESE GUÍA O REFERENCIA...') \
                        .classes('w-full text-center nexion-border').props('dark square outlined')
                    ui.button('EXECUTE SYSTEM SEARCH', on_click=lambda: ui.notify(f"Searching: {ref.value}")) \
                        .classes('nexion-btn w-full py-4 bg-white text-black' if self.dark_mode else 'nexion-btn w-full py-4 bg-black text-white')

            elif self.menu_main == "SEGUIMIENTO":
                ui.label(f"MÓDULO SEGUIMIENTO > {self.menu_sub}").classes('text-xl font-thin tracking-[4px]')
                if self.menu_sub == "GANTT":
                    # Ejemplo de integración con Plotly (como tenías antes)
                    fig = go.Figure(go.Bar(x=[1, 2, 3], y=[4, 5, 6], marker_color='#8B949E'))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='gray')
                    ui.plotly(fig).classes('w-full h-96')
                else:
                    ui.label("Cargando base de datos TRK...").classes('italic opacity-50')

            elif self.menu_main == "REPORTES":
                ui.label(f"PANEL DE CONTROL {self.menu_sub}").classes('text-xl tracking-widest')
                ui.separator().classes('w-1/4 opacity-20')
                ui.label("No hay datos pendientes en este periodo.").classes('text-xs opacity-50')

# --- INICIALIZACIÓN ---
nexion = NexionCore()

@ui.page('/')
async def index():
    if not nexion.splash_complete:
        await nexion.splash_screen()
        nexion.splash_complete = True
    else:
        nexion.build_interface()

# Configuración para Railway (Puerto dinámico)
port = int(os.environ.get("PORT", 8080))
ui.run(host='0.0.0.0', port=port, title="NEXION | Core", dark=True, reload=False)























































































































































































































































































































































































































































































































