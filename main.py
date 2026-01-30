import os
from nicegui import ui, app

# ── STATIC ─────────────────────────────────────────────
app.add_static_files('/static', 'static')

# ── SESSION STATE ─────────────────────────────────────
class SessionState:
    def __init__(self):
        self.message = "VERSION 1 – CHIC FREIGHT UI"
        self.dark_mode = True

state = SessionState()

# ── STYLES ────────────────────────────────────────────
def apply_styles():
    bg = "#0A0A0B"
    text = "#FFFFFF"

    ui.query('body').style(
        f'background:{bg}; color:{text}; transition:all .3s ease;'
    )

    ui.add_head_html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;600&display=swap');

    * {{
        font-family: 'Inter', sans-serif;
        -webkit-font-smoothing: antialiased;
    }}

    .version-badge {{
        border: 1px solid #5B2EFF;
        color: #5B2EFF;
        padding: 6px 14px;
        font-size: 9px;
        letter-spacing: 3px;
        text-transform: uppercase;
    }}

    .version-text {{
        font-size: 48px;
        font-weight: 600;
        letter-spacing: 4px;
        margin-top: 60px;
    }}

    .test-btn {{
        margin-top: 50px;
        padding: 18px 40px;
        border: 1px solid white;
        background: transparent;
        color: white;
        font-size: 11px;
        letter-spacing: 6px;
        cursor: pointer;
    }}
    .test-btn:hover {{
        background: white;
        color: black;
    }}
    </style>
    """)

# ── PAGE ──────────────────────────────────────────────
@ui.page('/')
def index():
    apply_styles()

    with ui.column().classes('w-full h-screen items-center justify-center'):
        ui.label('NEXION UI').classes('version-badge')
        ui.label().bind_text(state, 'message').classes('version-text')

        ui.button(
            'CHANGE MESSAGE',
            on_click=lambda: setattr(state, 'message', 'STATE UPDATED')
        ).classes('test-btn')

# ── RUN ───────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 8080)),
        show=False,
        reload=False
    )

































































































































































































































































































































































































































































































































