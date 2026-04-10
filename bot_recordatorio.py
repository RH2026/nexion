import pandas as pd
import requests
import io
import time

TOKEN = "8788568940:AAGGCFpRREU6SI1ngaIj8mbidLitT55aXcc"
CHAT_ID = "7273779444"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/main/tareas.csv"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")

def procesar_y_enviar():
    try:
        # Descargamos el CSV fresco
        url_fresca = f"{CSV_URL}?t={int(time.time())}"
        response = requests.get(url_fresca)
        
        if response.status_code != 200:
            enviar_telegram(f"❌ Error: No pude acceder al archivo CSV (Código: {response.status_code})")
            return

        df = pd.read_csv(io.StringIO(response.text))
        
        # Limpiamos columnas
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Convertimos PROGRESO a número
        if 'PROGRESO' in df.columns:
            df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors='coerce').fillna(0)
            pendientes = df[df["PROGRESO"] < 100].copy()
        else:
            enviar_telegram("❌ Error: No encontré la columna 'PROGRESO' en tu tabla.")
            return

        if pendientes.empty:
            enviar_telegram("✅ *Nexion:* Revisé la tabla y no hay pendientes menores al 100%.")
            return

        reporte = "📋 *RESUMEN DIARIO NEXION*\n"
        reporte += "_______________________________\n\n"
        
        for _, row in pendientes.iterrows():
            tarea = str(row.get('TAREA', 'Sin nombre')).strip()
            # Saltamos si la tarea está vacía
            if not tarea or tarea == "nan":
                continue
                
            prio = str(row.get('IMPORTANCIA', 'MEDIA')).strip().upper()
            accion = str(row.get('ULTIMO ACCION', 'Sin novedad')).strip()
            avance = int(row['PROGRESO'])
            
            emoji = "🚨" if prio == "URGENTE" else "📌"
            
            reporte += f"{emoji} *{tarea}*\n"
            reporte += f"   ┗ Estatus: {accion}\n"
            reporte += f"   ┗ Avance: {avance}%\n\n"
        
        enviar_telegram(reporte)
        
    except Exception as e:
        enviar_telegram(f"❌ *Error en el script:* {str(e)}")

if __name__ == "__main__":
    procesar_y_enviar()
        
    except Exception as e:
        enviar_telegram(f"❌ *Error al leer la tabla:* {str(e)}")

if __name__ == "__main__":
    procesar_y_enviar()
