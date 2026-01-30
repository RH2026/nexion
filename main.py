import os
from nicegui import ui

# ── STATE ─────────────────────────────────────────────
class State:
    def __init__(self):
        self.dark = True
        self.menu_main = "TRACKING"
        self.menu_sub = "GENERAL"

state = State()

# ── NAV CONFIG ───────────────────────────────────────
NAV = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA PT"],
}

# ── GLOBAL STYLES ─────────────────────────────────────
ui.add_head_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400&display=swap');

* { font-family: 'Inter', sans-serif; }

body { transition: background .3s ease, color .3s ease; }

.header, .footer {
    position: fixed;
    width: 100%;
    left: 0;
    z-index: 10;
    background: transparent;
}

.header { top: 0; }
.footer { bottom: 0; }

.nav {
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    opacity: .5;
    cursor: pointer;
}
.nav.active { opacity: 1; font-weight: 400; }
.nav:hover { opacity: 1; }

.subnav {
    font-size: 10px;
    letter-spacing: 4px;
    opacity: .4;
    cursor: pointer;
}
.subnav.active { opacity: 1; }

.center {
    min-height: 100vh;
    padding-top: 180px;
    padding-bottom: 120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: fade .35s ease;
}

@keyframes fade {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

.search {
    width: 280px;
    padding: 12px;
    border: 2px solid #FFCC00;
    background: transparent;
    letter-spacing: 2px;
    font-size: 12px;
    text-align: center;
}

.btn {
    margin-top: 24px;
    padding: 12px 32px;
    border: 1px solid currentColor;
    background: transparent;
    font-size: 10px;
    letter-spacing: 5px;
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

# ── CONTENT ───────────────────────────────────────────
@ui.refreshable
def content():
    with ui.column().classes("center"):
        ui.label(state.menu_main).style(
            "font-size:10px;letter-spacing:10px;opacity:.4"
        )
        ui.label(state.menu_sub).style(
            "font-size:42px;font-weight:200;letter-spacing:18px;margin:40px 0"
        )

        if state.menu_main == "TRACKING":
            ui.input(placeholder="REFERENCE NUMBER").classes("search")
            ui.button("EXECUTE", on_click=lambda: ui.notify("SEARCHING")).classes("btn")
        else:
            ui.label("CONTENT LOADED").style("opacity:.4;font-size:12px")

# ── PAGE ──────────────────────────────────────────────
@ui.page("/")
def index():
    apply_theme()

    # HEADER
    with ui.header().classes("header p-8"):
        with ui.row().classes("w-full justify-between items-center"):
            ui.label("NEXION").style("letter-spacing:6px")

            with ui.row().classes("gap-6"):
                for m in NAV:
                    ui.label(m).classes(
                        f"nav {'active' if state.menu_main == m else ''}"
                    ).on("click", lambda _, m=m: (
                        setattr(state, "menu_main", m),
                        setattr(state, "menu_sub", NAV[m][0] if NAV[m] else "GENERAL"),
                        content.refresh()
                    ))

            ui.label("☾ / ☀").classes("nav").on(
                "click",
                lambda: (
                    setattr(state, "dark", not state.dark),
                    apply_theme()
                )
            )

        # SUBMENU
        if NAV[state.menu_main]:
            with ui.row().classes("gap-6 justify-center mt-6"):
                for s in NAV[state.menu_main]:
                    ui.label(s).classes(
                        f"subnav {'active' if state.menu_sub == s else ''}"
                    ).on("click", lambda _, s=s: (
                        setattr(state, "menu_sub", s),
                        content.refresh()
                    ))

    content()

    # FOOTER
    with ui.footer().classes("footer"):
        ui.label("NEXION // LOGISTICS OS // 2026")

# ── RUN ───────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=False,
        show=False,
    )






































































































































































































































































































































































































































































































































