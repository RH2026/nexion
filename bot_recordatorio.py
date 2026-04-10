import pandas as pd
import requests
import io

# Configuración (Usa tus datos que ya tenemos)
TOKEN = "8788568940:AAGGCFpRREU6SI1ngaIj8mbidLitT55aXcc"
CHAT_ID = "7273779444"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/main/tareas.csv"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def procesar_y_enviar():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Filtramos
        pendientes = df[(df["PROGRESO"] < 100) & (df["TAREA"].str.strip() != "")]
        
        if pendientes.empty:
            # CAMBIAMOS ESTO PARA PROBAR:
            enviar_telegram("⚠️ *Prueba de conexión:* El bot funciona, pero no encontré tareas pendientes en tu archivo CSV.")
            return

        reporte = "📋 *RESUMEN DIARIO DE PENDIENTES*\n"
        reporte += "_______________________________\n\n"
        
        for _, row in pendientes.iterrows():
            emoji = "🚨" if str(row['IMPORTANCIA']).strip() == "Urgente" else "📌"
            reporte += f"{emoji} *{row['TAREA']}*\n"
            reporte += f"   ┗ Avance: {row['PROGRESO']}% | {row['ULTIMO ACCION']}\n\n"
        
        enviar_telegram(reporte)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    procesar_y_enviar()
