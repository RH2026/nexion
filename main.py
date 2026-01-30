import os
from nicegui import ui

# ── STATE ─────────────────────────────────────────────
class State:
    def __init__(self):
        self.dark = True
        self.menu = "TRACKING"

state = State()

# ── GLOBAL STYLES (SHARED, UNA SOLA VEZ) ──────────────
ui.add_head_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400&display=swap');

* {
    font-family: 'Inter', sans-serif;
    -webkit-font-smoothing: antialiased;
}

body {
    transition: background .3s ease, color .3s ease;
}

.header, .footer {
    position: fixed;
    width: 100%;
    left: 0;
    z-index: 10;
}

.header { top: 0; }
.footer { bottom: 0; }

.nav {
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    opacity: .6;
    cursor: pointer;
}
.nav:hover { opacity: 1; }

.center {
    min-height: 100vh;
    padding-top: 140px;
    padding-bottom: 120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: fade .35s ease;
}

@keyframes fade {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}

.search {
    width: 360px;
    padding: 18px;
    border: 2px solid #FFCC00;
    background: transparent;
    letter-spacing: 4px;
    text-transform: uppercase;
    font-size: 14px;
}

.btn {
    margin-top: 32px;
    padding: 16px 42px;
    border: 1px solid currentColor;
    background: transparent;
    font-size: 10px;
    letter-spacing: 6px;
    cursor: pointer;
}
.btn:hover {
    background: currentColor;
    color: var(--bg);
}

.footer {
    text-align: center;
    font-size: 9px;
    letter-spacing: 4px;
    opacity: .4;
    padding: 16px;
}
</style>
""", shared=True)

# ── THEME ─────────────────────────────────────────────
def apply_theme():
    bg = "#0A0A0B" if state.dark else "#FFFFFF"
    text = "#FFFFFF" if state.dark else "#000000"
    ui.query("body").style(f"background:{bg};color:{text};--bg:{bg}")

# ── MAIN CONTENT ──────────────────────────────────────
@ui.refreshable
def content():
    with ui.column().classes("center"):
        ui.label("VERSION NUEVA").style(
            "font-size:10px;letter-spacing:10px;opacity:.4"
        )
        ui.label(state.menu).style(
            "font-size:56px;font-weight:200;letter-spacing:22px;margin:40px 0"
        )
        ui.input(placeholder="REFERENCE NUMBER").classes("search text-center")
        ui.button("EXECUTE", on_click=lambda: ui.notify("SEARCHING")).classes("btn")

# ── PAGE ──────────────────────────────────────────────
@ui.page("/")
def index():
    apply_theme()

    with ui.header().classes("header p-8 flex justify-between"):
        ui.label("NEXION").style("letter-spacing:6px")
        ui.label("☾ / ☀").classes("nav").on(
            "click",
            lambda: (
                setattr(state, "dark", not state.dark),
                apply_theme()
            )
        )

    content()

    with ui.footer().classes("footer"):
        ui.label("NEXION // LOGISTICS OS")

# ── RUN ───────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=False,
        show=False,
    )





































































































































































































































































































































































































































































































































