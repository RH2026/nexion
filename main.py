import os
import asyncio
from nicegui import ui, app

# ── STATIC ─────────────────────────────────────────────
app.add_static_files('/static', 'static')

# ── SESSION STATE ─────────────────────────────────────
class SessionState:
    def __init__(self):
        self.dark_mode = True
        self.menu_main = "TRACKING"
        self.menu_sub = "GENERAL"

state = SessionState()

# ── STYLES ────────────────────────────────────────────
def apply_styles():
    bg = "#0A0A0B" if state.dark_mode else "#FFFFFF"
    text = "#FFFFFF" if state.dark_mode else "#000000"
    border = "#1A1A1D" if state.dark_mode else "#EEEEEE"

    ui.query('body').style(
        f'background:{bg}; color:{text}; transition:all .4s ease;'
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
        --accent: #5B2EFF;   /* FedEx precision */
        --alert: #FFCC00;    /* DHL clarity */
    }}

    /* ── NAV TEXT ───────────────── */
    .nav-text {{
        font-size: 11px;
        letter-spacing: 3px;
        text-transform: uppercase;
        font-weight: 300;
        cursor: pointer;
        opacity: .7;
        transition: opacity .2s;
    }}
    .nav-text:hover {{ opacity: 1; }}

    /* ── INPUT ─────────────────── */
    .zara-input {{
        border-bottom: 1px solid var(--text) !important;
        font-size: 12px;
        letter-spacing: 6px;
        text-transform: uppercase;
    }}

    /* ── CHIC BUTTON ───────────── */
    .chic-btn {{
        position: relative;
        width: 100%;
        padding: 18px 40px;
        background: transparent;
        border: 1px solid var(--text);
        color: var(--text);
        font-size: 10px;
        letter-spacing: 8px;
        text-transform: uppercase;
        font-weight: 300;
        cursor: pointer;
        overflow: hidden;
        transition: color .25s ease;
    }}

    .chic-btn::after {{
        content: "";
        position: absolute;
        left: 0;
        bottom: 0;
        width: 0%;
        height: 1px;
        background: var(--accent);
        transition: width .35s ease;
    }}

    .chic-btn:hover {{
        color: var(--accent);
    }}

    .chic-btn:hover::after {{
        width: 100%;
    }}

    .chic-btn:active {{
        color: var(--alert);
    }}

    /* ── FOOTER ───────────────── */
    .footer {{
        font-size: 9px;
        letter-spacing: 4px;
        opacity: .4;
    }}
    </style>
    """)

# ── NAV MAP ───────────────────────────────────────────
nav_map = {
    "TRACKING": [],
    "SEGUIMIENTO": ["TRK", "GANTT"],
    "REPORTES": ["APQ", "OPS", "OTD"],
    "FORMATOS": ["SALIDA DE PT"]
}

def navigate(main, sub=None):
    state.menu_main = main
    state.menu_sub = sub if sub else (nav_map[main][0] if nav_map[main] else "GENERAL")
    content.refresh()

# ── MAIN CONTENT ──────────────────────────────────────
@ui.refreshable
def content():
    with ui.column().classes('w-full items-center px-8 mt-40'):
        ui.label(state.menu_main).style(
            'letter-spacing:15px;font-size:10px;opacity:.4;'
        )
        ui.label(state.menu_sub).style(
            'letter-spacing:25px;font-size:60px;font-weight:100;margin-bottom:80px;'
        )

        if state.menu_main == "TRACKING":
            with ui.column().classes('w-full max-w-lg items-center gap-16'):
                ui.input(
                    placeholder='REFERENCE NUMBER'
                ).classes(
                    'w-full zara-input text-center'
                ).props('borderless')

                ui.button(
                    'E X E C U T E',
                    on_click=lambda: ui.notify('QUERY DISPATCHED')
                ).classes('chic-btn')

# ── PAGE ──────────────────────────────────────────────
@ui.page('/')
async def index():
    apply_styles()

    # HEADER
    with ui.header().classes(
        'bg-transparent p-10 items-center justify-between'
    ).style('backdrop-filter: blur(10px)'):

        logo = f"/static/n{'1' if state.dark_mode else '2'}.png"
        ui.image(logo).style('width:100px;opacity:.8;')

        with ui.row().classes('gap-8 items-center'):
            for main_item, subs in nav_map.items():
                if subs:
                    with ui.label(main_item).classes('nav-text'):
                        with ui.menu():
                            for s in subs:
                                ui.menu_item(
                                    s,
                                    on_click=lambda x, m=main_item, s=s: navigate(m, s)
                                )
                else:
                    ui.label(main_item).classes('nav-text').on(
                        'click', lambda x, m=main_item: navigate(m)
                    )

            ui.label(
                '☾' if state.dark_mode else '☀'
            ).classes('nav-text opacity-40').on(
                'click',
                lambda: [
                    setattr(state, 'dark_mode', not state.dark_mode),
                    ui.run_javascript('location.reload()')
                ]
            )

    content()

    ui.label(
        'NEXION // LOGISTICS OS // © 2026'
    ).classes(
        'footer fixed-bottom w-full text-center p-4'
    )

# ── RUN ───────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 8080)),
        title="NEXION | Core",
        reload=False,
        show=False
    )

































































































































































































































































































































































































































































































































