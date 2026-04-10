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
    except:
        pass

def procesar():
    try:
        r = requests.get(f"{CSV_URL}?t={int(time.time())}")
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = [c.strip().upper() for c in df.columns]

        # --- LÍNEA DE PRUEBA: Borra esto después ---
        print("Columnas detectadas:", df.columns.tolist())
        # -------------------------------------------

        df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors='coerce').fillna(0)
        pendientes = df[df["PROGRESO"] < 100].copy()

        if pendientes.empty:
            print("No hay pendientes en el DataFrame")
            enviar_telegram("✅ *Nexion:* Sin pendientes hoy.")
            return

        msj = "*RESUMEN PENDIENTES NEXION*\n" + "_"*20 + "\n\n"
        
        for _, row in pendientes.iterrows():
            tarea = str(row.get('TAREA', 'Sin nombre')).strip()
            if not tarea or tarea == "nan": continue
            
            # Buscamos la columna (con o sin tilde)
            ultima = row.get('ULTIMO ACCION') or row.get('ULTIMO ACCION') or row.get('ULTIMA ACCION') or "Sin dato"
            
            prio = str(row.get('IMPORTANCIA', 'MEDIA')).upper()
            emoji = "📌" if "URGENTE" in prio else "📌"
            
            msj += f"{emoji} *{tarea}*\n    ┗ Avance: {int(row['PROGRESO'])}%\n"
            msj += f"    ┗ Última acción: {ultima}\n\n"
        
        print("Enviando mensaje a Telegram...")
        enviar_telegram(msj)

    except Exception as e:
        print(f"Error detectado: {e}")
        enviar_telegram(f"❌ Error: {str(e)}")
