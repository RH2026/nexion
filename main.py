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

:root { --text: #FFFFFF; --bg: #0A0A0B; --border: #1F1F22; }

.nav-item {
    font-size: 10px; letter-spacing: 5px; text-transform: uppercase;
    opacity: .3; cursor: pointer; transition: all .4s;
}
.nav-item.active { opacity: 1; font-weight: 400; border-bottom: 1px solid var(--text); }

.sub-nav-item {
    font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
    opacity: .3; cursor: pointer; transition: all .4s;
}
.sub-nav-item.active { opacity: 1; font-weight: 700; }

.zara-input {
    border-bottom: 1px solid var(--text) !important;
    letter-spacing: 6px; font-size: 14px; text-transform: uppercase;
    text-align: center; color: inherit;
}

.zara-btn {
    border: 1px solid var(--text) !important;
    letter-spacing: 10px; font-size: 9px; padding: 18px 50px;
    background: transparent !important; color: inherit;
    border-radius: 0px !important; transition: .4s;
}
.zara-btn:hover { background: var(--text) !important; color: var(--bg) !important; }
</style>
""", shared=True)

# ── LÓGICA DE NAVEGACIÓN ──────────────────────────────
def navigate(s, m, sub_val=None):
    s['main'] = m
    s['sub'] = sub_val if sub_val else (NAV[m][0] if NAV[m] else "GENERAL")
    header_content.refresh()
    main_content.refresh()

# ── COMPONENTES REFRESCABLES (CONTENIDO INTERNO) ──────
@ui.refreshable
def header_content():
    s = app.storage.user.get('state', {'main': 'TRACKING', 'sub': 'GENERAL', 'dark': True})
    with ui.row().classes("w-full items-center justify-between"):
        ui.label("NEXION").style("letter-spacing:10px; font-weight:900")
        
        with ui.row().classes("gap-10 items-center"):
            for m in NAV:
                active = "active" if s['main'] == m else ""
                ui.label(m).classes(f"nav-item {active}").on("click", lambda _, m=m: navigate(s, m))
            
            ui.label("☾/☀").classes("nav-item").on("click", lambda: [s.update({'dark': not s['dark']}), ui.run_javascript('window.location.reload()')])

    if NAV[s['main']]:
        with ui.row().classes("w-full justify-center gap-8 mt-12 border-t border-white/5 pt-6"):
            for sub_item in NAV[s['main']]:
                sub_active = "active" if s['sub'] == sub_item else ""
                ui.label(sub_item).classes(f"sub-nav-item {sub_active}").on("click", lambda _, si=sub_item: navigate(s, s['main'], si))

@ui.refreshable
def main_content():
    s = app.storage.user.get('state', {'main': 'TRACKING', 'sub': 'GENERAL'})
    with ui.column().classes("w-full items-center mt-32"):
        ui.label(s['main']).style("font-size:10px; letter-spacing:15px; opacity:.2")
        ui.label(s['sub']).style("font-size:58px; font-weight:100; letter-spacing:25px; margin:40px 0; text-transform:uppercase; text-align:center")

        if s['main'] == "TRACKING":
            with ui.column().classes("w-full max-w-lg items-center gap-14"):
                ui.input(placeholder="REFERENCE NUMBER").classes("w-full zara-input").props('borderless')
                ui.button("E X E C U T E", on_click=lambda: ui.notify("SEARCHING...")).classes("zara-btn")

# ── PÁGINA MAESTRA ────────────────────────────────────
@ui.page("/")
def index():
    if 'state' not in app.storage.user:
        app.storage.user['state'] = {'dark': True, 'main': 'TRACKING', 'sub': 'GENERAL'}
    
    s = app.storage.user['state']
    
    # Aplicar tema inicial
    bg = "#0A0A0B" if s['dark'] else "#F5F5F7"
    text = "#FFFFFF" if s['dark'] else "#121212"
    ui.query("body").style(f"background:{bg}; color:{text}; --bg:{bg}; --text:{text}")

    # HEADER ESTÁTICO (NiceGUI es feliz así)
    with ui.header().classes("bg-transparent p-10").style("backdrop-filter: blur(20px)"):
        header_content()
    
    # CUERPO REFRESCABLE
    main_content()

    # FOOTER ESTÁTICO
    with ui.footer().classes("bg-transparent p-12 text-center"):
        ui.label("N E X I O N // G D L // © 2 0 2 6").style("font-size:8px; letter-spacing:12px; opacity:.1")

# ── RUN ───────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=False,
        show=False,
        storage_secret="XENOCODE_ULTRA_SECRET"
    )








































































































































































































































































































































































































































































































































