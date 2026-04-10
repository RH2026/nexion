import pandas as pd
import requests
import io

TOKEN = "8788568940:AAGGCFpRREU6SI1ngaIj8mbidLitT55aXcc"
CHAT_ID = "7273779444"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/main/tareas.csv"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def procesar_y_enviar():
    try:
        # Cargamos la tabla de Nexion
        response = requests.get(CSV_URL)
        df = pd.read_csv(io.StringIO(response.text))
        
        # Limpiamos los nombres de las columnas (por si tienen espacios locos)
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Filtramos: Tareas con progreso menor a 100 y que no estén vacías
        pendientes = df[(df["PROGRESO"].astype(float) < 100) & (df["TAREA"].str.strip() != "")]
        
        if pendientes.empty:
            enviar_telegram("✅ *Nexion:* ¡Todo al corriente! No encontré pendientes para hoy.")
            return

        reporte = "📋 *TUS PENDIENTES DE HOY EN NEXION*\n"
        reporte += "_______________________________\n\n"
        
        for _, row in pendientes.iterrows():
            emoji = "🚨" if str(row['IMPORTANCIA']).strip().upper() == "URGENTE" else "📌"
            tarea = str(row['TAREA']).strip()
            avance = int(row['PROGRESO'])
            accion = str(row['ULTIMO ACCION']).strip() if 'ULTIMO ACCION' in row else "Sin novedad"
            
            reporte += f"{emoji} *{tarea}*\n"
            reporte += f"   ┗ Avance: {avance}% | {accion}\n\n"
        
        enviar_telegram(reporte)
        
    except Exception as e:
        enviar_telegram(f"❌ *Error al leer la tabla:* {str(e)}")

if __name__ == "__main__":
    procesar_y_enviar()
