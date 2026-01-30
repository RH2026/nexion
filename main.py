import os
from nicegui import ui, app

# ── NAV CONFIG ───────────────────────────────────────
NAV = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA PT"],
}

# ── GLOBAL STYLES (ZARA / DHL ELITE) ──────────────────
ui.add_head_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;900&display=swap');
* { font-family: 'Inter', sans-serif; -webkit-font-smoothing: antialiased; }
body { transition: background .6s ease, color .6s ease; overflow-x: hidden; }

/* Estética Zara: Tipografía aireada */
.nav-item {
    font-size: 10px; letter-spacing: 5px; text-transform: uppercase;
    opacity: .3; cursor: pointer; transition: all .4s;
}
.nav-item.active { opacity: 1; font-weight: 400; border-bottom: 1px solid currentColor; }

.sub-nav-item {
    font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
    opacity: .3; cursor: pointer; transition: all .4s;
    padding: 4px 12px;
}
.sub-nav-item.active { opacity: 1; font-weight: 700; }

.zara-input {
    border-bottom: 1px solid currentColor !important;
    letter-spacing: 6px; font-size: 14px; text-transform: uppercase;
    text-align: center; color: inherit;
}

.zara-btn {
    border: 1px solid currentColor !important;
    letter-spacing: 10px; font-size: 9px; padding: 18px 50px;
    background: transparent !important; color: inherit;
    border-radius: 0px !important; transition: .4s;
}
.zara-btn:hover { background: currentColor !important; color: var(--bg) !important; }

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade { animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); }
</style>
""", shared=True)

# ── CONTENT RENDERER ──────────────────────────────────
@ui.refreshable
def render_content():
    # Recuperamos el estado de la sesión del usuario
    s = app.storage.user.get('state', {'main': 'TRACKING', 'sub': 'GENERAL'})
    main = s['main']
    sub = s['sub']
    
    with ui.column().classes("w-full items-center mt-32 animate-fade"):
        # Títulos con Kerning Extremo
        ui.label(main).style("font-size:10px; letter-spacing:15px; opacity:.2")
        ui.label(sub).style("font-size:58px; font-weight:100; letter-spacing:25px; margin:40px 0; text-transform:uppercase; text-align:center")

        if main == "TRACKING":
            with ui.column().classes("w-full max-w-lg items-center gap-14"):
                ui.input(placeholder="REFERENCE NUMBER").classes("w-full zara-input").props('borderless')
                ui.button("E X E C U T E", on_click=lambda: ui.notify("INITIALIZING QUERY...")).classes("zara-btn")
        
        elif main == "SEGUIMIENTO" and sub == "GANTT":
            ui.label("MODULO GANTT INTERACTIVO").style("opacity:.3; letter-spacing:8px")
            # Aquí podrías meter un gráfico de Plotly más adelante
            ui.icon('analytics', size='100px').style('opacity:0.1; margin-top:20px')
            
        else:
            ui.label(f"WAITING FOR {main} DATA...").style("opacity:.2; letter-spacing:6px; font-size:11px")

# ── PAGE DEFINITION ───────────────────────────────────
@ui.page("/")
def index():
    # Inicializar almacenamiento persistente por sesión
    if 'state' not in app.storage.user:
        app.storage.user['state'] = {'dark': True, 'main': 'TRACKING', 'sub': 'GENERAL'}
    
    s = app.storage.user['state']

    def update_theme():
        s['dark'] = not s['dark']
        bg = "#0A0A0B" if s['dark'] else "#F5F5F7"
        text = "#FFFFFF" if s['dark'] else "#121212"
        ui.query("body").style(f"background:{bg}; color:{text}; --bg:{bg}")

    def navigate(m, sub_val=None):
        s['main'] = m
        # Si no se pasa sub_val, agarra el primero de la lista de NAV o "GENERAL"
        s['sub'] = sub_val if sub_val else (NAV[m][0] if NAV[m] else "GENERAL")
        update_theme() # Mantenemos consistencia del tema
        header.refresh()
        render_content.refresh()

    update_theme()

    # HEADER (Estático en su raíz, dinámico en su contenido)
    @ui.refreshable
    def header():
        with ui.header().classes("bg-transparent p-10 items-center justify-between").style("backdrop-filter: blur(20px)"):
            ui.label("NEXION").style("letter-spacing:10px; font-weight:900")
            
            with ui.row().classes("gap-10 items-center"):
                for m in NAV:
                    active = "active" if s['main'] == m else ""
                    ui.label(m).classes(f"nav-item {active}").on("click", lambda _, m=m: navigate(m))
                
                ui.label("☾/☀").classes("nav-item").on("click", lambda: (update_theme(), header.refresh()))

            # SUBNAV (Solo aparece si el menú principal tiene opciones)
            if NAV[s['main']]:
                with ui.row().classes("w-full justify-center gap-8 mt-12 border-t border-white/5 pt-6"):
                    for sub_item in NAV[s['main']]:
                        sub_active = "active" if s['sub'] == sub_item else ""
                        ui.label(sub_item).classes(f"sub-nav-item {sub_active}").on("click", lambda _, si=sub_item: navigate(s['main'], si))
    
    header()
    render_content()

    # FOOTER EDITORIAL
    with ui.footer().classes("bg-transparent p-12 text-center"):
        ui.label("N E X I O N // L O G I S T I C S // O S // 2 0 2 6").style("font-size:8px; letter-spacing:12px; opacity:.1")

# ── RUN ───────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=False,
        show=False,
        title="NEXION CORE",
        storage_secret="XENOCODE_PRO_SECRET" # Importante para guardar tu sesión
    )







































































































































































































































































































































































































































































































































