import pandas as pd
import requests
import io

# Tus credenciales que ya funcionan
TOKEN = "8788568940:AAGGCFpRREU6SI1ngaIj8mbidLitT55aXcc"
CHAT_ID = "7273779444"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/main/tareas.csv"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload)
        print(f"Resultado envío: {r.status_code}")
    except Exception as e:
        print(f"Error enviando: {e}")

def procesar_y_enviar():
    try:
        # Descargamos el CSV con un truco para que no use caché y lea lo más nuevo
        import time
        response = requests.get(f"{CSV_URL}?t={int(time.time())}")
        df = pd.read_csv(io.StringIO(response.text))
        
        # Limpiamos nombres de columnas (quita espacios y pone todo en mayúsculas)
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Aseguramos que PROGRESO sea número
        df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors='coerce').fillna(0)
        
        # Filtramos lo que sea menor a 100
        pendientes = df[df["PROGRESO"] < 100].copy()
        
        if pendientes.empty:
            enviar_telegram("✅ *Nexion:* Revisé la tabla y no encontré pendientes menores al 100%. ¡Todo al día!")
            return

        reporte = "📋 *RESUMEN DIARIO NEXION*\n"
        reporte += "_______________________________\n\n"
        
        for _, row in pendientes.iterrows():
            # Sacamos los datos con cuidado
            tarea = str(row.get('TAREA', 'Sin descripción')).strip()
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
