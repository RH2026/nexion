import streamlit as st

# Función para inyectar el código de impresión
def imprimir_formato(datos):
    # Definimos el estilo "Elite" con CSS
    html_layout = f"""
    <html>
    <head>
        <style>
            @media print {{
                .no-print {{ display: none; }}
                body {{ font-family: 'Arial', sans-serif; padding: 20px; }}
            }}
            .header {{ border-bottom: 3px solid #FFDD00; padding-bottom: 10px; margin-bottom: 20px; }}
            .footer {{ margin-top: 50px; border-top: 1px solid #ccc; text-align: center; font-size: 12px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .total {{ background-color: #FFDD00; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin:0;">JYPESA</h1>
            <p style="margin:0; color: #666;">REPORTE DE COSTOS DE MUESTRAS</p>
        </div>
        
        <p><strong>Destinatario:</strong> {datos['destinatario']}</p>
        <p><strong>Fecha:</strong> {datos['fecha']}</p>
        
        <table>
            <thead>
                <tr>
                    <th>Producto</th>
                    <th>Costo Unitario</th>
                    <th>Cantidad</th>
                    <th>Subtotal</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td>{p}</td><td>${c:,.2f}</td><td>{q}</td><td>${(c*q):,.2f}</td></tr>" for p, c, q in datos['items']])}
                <tr>
                    <td colspan="3" style="text-align:right">Flete Manual:</td>
                    <td>${datos['flete']:,.2f}</td>
                </tr>
                <tr class="total">
                    <td colspan="3" style="text-align:right">TOTAL GENERAL:</td>
                    <td>${datos['total']:,.2f}</td>
                </tr>
            </tbody>
        </table>

        <div class="footer">
            <p><strong>JYPESA</strong></p>
            <p>Automatización de Procesos</p>
        </div>

        <script>
            window.print();
        </script>
    </body>
    </html>
    """
    return html_layout

# --- Lógica de la App ---
st.title("📦 Sistema de Muestras NEXION")

# (Aquí irían tus inputs que ya tienes...)
# Supongamos que ya tienes estas variables listas:
datos_reporte = {
    "destinatario": "Tania Vega",
    "fecha": "04/02/2026",
    "flete": 150.00,
    "items": [("Elements", 29.34, 1), ("Biogena", 48.95, 2)],
    "total": 277.24
}

if st.button("🖨️ Abrir Formato de Impresión"):
    reporte_html = imprimir_formato(datos_reporte)
    # Abrimos una ventana nueva con el contenido
    st.components.v1.html(reporte_html, height=800, scrolling=True)





























































