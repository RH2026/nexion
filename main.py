import os
from nicegui import ui

class State:
    dark = True
    menu = "TRACKING"

state = State()

ui.add_head_html("""
<style>
body { transition: background .3s, color .3s; }
.center {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: fade .4s ease;
}
@keyframes fade {
    from { opacity:0; transform: translateY(12px); }
    to { opacity:1; transform: translateY(0); }
}
.search {
    border: 2px solid #FFCC00;
    padding: 18px;
    width: 360px;
    letter-spacing: 4px;
}
</style>
""", shared=True)

def apply_theme():
    bg = "#0A0A0B" if state.dark else "#FFFFFF"
    text = "#FFFFFF" if state.dark else "#000000"
    ui.query("body").style(f"background:{bg};color:{text}")

@ui.refreshable
def content():
    with ui.column().classes("center"):
        ui.label("VERSION NUEVA CONFIRMADA").style(
            "font-size:12px;letter-spacing:8px;opacity:.4"
        )
        ui.label(state.menu).style(
            "font-size:56px;font-weight:200;letter-spacing:20px"
        )
        ui.input(placeholder="REFERENCE").classes("search text-center")

@ui.page("/")
def index():
    apply_theme()

    with ui.header().classes("p-6 flex justify-between"):
        ui.label("NEXION")
        ui.button("☾ / ☀", on_click=lambda: (
            setattr(state, "dark", not state.dark),
            apply_theme()
        ))

    content()

    with ui.footer().classes("p-4 text-center opacity-40"):
        ui.label("NEXION // LOGISTICS OS")

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=False,
        show=False,
    )




































































































































































































































































































































































































































































































































