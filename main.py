import os
from nicegui import ui

# ── STATE ─────────────────────────────────────────────
class State:
    def __init__(self):
        self.dark = True
        self.menu = "TRACKING"

state = State()

# ── GLOBAL STYLES (SHARED ✔️) ─────────────────────────
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

/* HEADER & FOOTER */
.bar {
    position: fixed;
    width: 100%;
    left: 0;
    z-index: 10;
}

/* NAV */
.nav {
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    opacity: .6;
    cursor: pointer;
}
.nav:hover { opacity: 1; }

/* CENTER */
.center {
    min-height: 100vh;
    padding-top: 140px;
    padding-bottom: 120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: fade .4s ease;
}

@keyframes fade {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}

/* DHL INPUT */
.search {
    border: 2px solid var(--accent);
    padding: 18px;
    width: 360px;
    font-size: 14px;
    letter-spacing: 4px;
    text-transform: uppercase;
    background: transparent;
}

/* BUTTON */
.btn {
    margin-top: 30px;
    padding: 16px 40px;
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

/* FOOTER */
.footer {
    bottom: 0;
    padding: 16px;
    font-size: 9px;
    letter-spacing: 4px;
    opacity: .4;
    text-align: center;
}
</style>
""", shared=True)

# ── THEME ─────────────────────────────────────────────
def apply_theme():
    bg = "#0A0A0B" if state.dark else "#FFFFFF"
    text = "#FFFFFF" if state.dark else "#000000"
    accent = "#FFCC00"  # DHL

    ui.query("body").style(
        f"""
        background:{bg};
        color:{text};
        --bg:{bg};
        --accent:{accent};
        """
    )

# ── CONTENT ───────────────────────────────────────────
@ui.refreshable
def content():
    apply_theme()

    with ui.column().classes("center"):
        ui.label(state.menu).style(
            "font-size:10px;letter-spacing:14px;opacity:.4"
        )
        ui.label("GENERAL").style(
            "font-size:56px;font-weight:200;letter-spacing:20px;margin:40px 0"
        )

        ui.input(placeholder="REFERENCE NUMBER").classes("search text-center")
        ui.button("EXECUTE", on_click=lambda: ui.notify("SEARCHING")).classes("btn")

# ── PAGE ──────────────────────────────────────────────
@ui.page("/")
def index():
    apply_theme()

    # HEADER
    with ui.header().classes("bar p-10 flex justify-between"):
        ui.label("NEXION").style("letter-spacing:6px")
        ui.label("☾" if state.dark else "☀").classes("nav").on(
            "click",
            lambda: [setattr(state, "dark", not state.dark), content.refresh()]
        )

    content()

    # FOOTER
    with ui.footer().classes("bar footer"):
        ui.label("NEXION // LOGISTICS OS")

# ── RUN ───────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        show=False,
        reload=False,
    )




































































































































































































































































































































































































































































































































