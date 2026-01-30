import os
from nicegui import ui, app

# ── STATIC ─────────────────────────────────────────────
app.add_static_files('/static', 'static')

# ── STATE ─────────────────────────────────────────────
class State:
    def __init__(self):
        self.dark = True
        self.menu_main = "TRACKING"
        self.menu_sub = "GENERAL"

state = State()

# ── STYLES ────────────────────────────────────────────
def apply_styles():
    bg = "#0A0A0B" if state.dark else "#FFFFFF"
    text = "#FFFFFF" if state.dark else "#000000"
    border = "#1A1A1D" if state.dark else "#E5E5E5"
    accent = "#FFCC00"  # DHL

    ui.query("body").style(
        f"background:{bg}; color:{text}; transition:background .3s ease,color .3s ease;"
    )

    ui.add_head_html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400&display=swap');

    * {{
        font-family: 'Inter', sans-serif;
        -webkit-font-smoothing: antialiased;
    }}

    :root {{
        --bg: {bg};
        --text: {text};
        --border: {border};
        --accent: {accent};
    }}

    /* HEADER / FOOTER */
    .static-bar {{
        position: fixed;
        width: 100%;
        left: 0;
        z-index: 10;
        background: var(--bg);
    }}

    /* NAV */
    .nav-item {{
        font-size: 11px;
        letter-spacing: 3px;
        text-transform: uppercase;
        opacity: .6;
        cursor: pointer;
    }}
    .nav-item:hover {{ opacity: 1; }}

    /* CENTER CONTENT */
    .center {{
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        animation: fadeUp .6s ease;
    }}

    @keyframes fadeUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* DHL SEARCH */
    .dhl-input {{
        border: 2px solid var(--accent);
        padding: 18px;
        font-size: 14px;
        letter-spacing: 4px;
        text-transform: uppercase;
        width: 360px;
        background: transparent;
        color: var(--text);
    }}

    .dhl-input::placeholder {{
        color: var(--text);
        opacity: .4;
    }}

    /* BUTTON */
    .execute-btn {{
        margin-top: 30px;
        padding: 16px 40px;
        border: 1px solid var(--text);
        background: transparent;
        color: var(--text);
        font-size: 10px;
        letter-spacing: 6px;
        text-transform: uppercase;
        cursor: pointer;
    }}
    .execute-btn:hover {{
        background: var(--text);
        color: var(--bg);
    }}

    /* FOOTER */
    .footer {{
        bottom: 0;
        padding: 16px;
        font-size: 9px;
        letter-spacing: 4px;
        opacity: .4;
        text-align: center;
    }}
    </style>
    """)

# ── NAV MAP ───────────────────────────────────────────
nav = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT"],
}

def navigate(main, sub=None):
    state.menu_main = main
    state.menu_sub = sub or "GENERAL"
    content.refresh()

# ── CONTENT ───────────────────────────────────────────
@ui.refreshable
def content():
    with ui.column().classes("center"):
        ui.label(state.menu_main).style(
            "font-size:10px;letter-spacing:14px;opacity:.4"
        )
        ui.label(state.menu_sub).style(
            "font-size:56px;font-weight:200;letter-spacing:20px;margin:50px 0"
        )

        if state.menu_main == "TRACKING":
            ui.input(
                placeholder="REFERENCE NUMBER"
            ).classes("dhl-input text-center")
            ui.button(
                "EXECUTE",
                on_click=lambda: ui.notify("SEARCHING")
            ).classes("execute-btn")
        else:
            ui.label("CONTENT LOADED").style("opacity:.3")

# ── PAGE ──────────────────────────────────────────────
@ui.page("/")
def index():
    apply_styles()

    # HEADER
    with ui.header().classes("static-bar p-10 flex justify-between items-center"):
        ui.label("NEXION").style("font-size:18px;letter-spacing:6px")
        with ui.row().classes("gap-8"):
            for m in nav:
                ui.label(m).classes("nav-item").on(
                    "click", lambda x, m=m: navigate(m)
                )
            ui.label("☾" if state.dark else "☀").classes("nav-item").on(
                "click", lambda: [
                    setattr(state, "dark", not state.dark),
                    content.refresh(),
                ]
            )

    # BODY
    content()

    # FOOTER
    with ui.footer().classes("static-bar footer"):
        ui.label("NEXION // LOGISTICS OS // © 2026")

# ── RUN ───────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        show=False,
        reload=False,
        title="NEXION",
    )


































































































































































































































































































































































































































































































































