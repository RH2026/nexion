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
        
        # Estandarizamos columnas a mayúsculas
        df.columns = [c.strip().upper() for c in df.columns]
        
        if 'PROGRESO' not in df.columns:
            enviar_telegram("❌ No encontré la columna PROGRESO")
            return

        df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors='coerce').fillna(0)
        pendientes = df[df["PROGRESO"] < 100].copy()

        if pendientes.empty:
            enviar_telegram("✅ Nexion: Sin pendientes hoy.")
            return

        msj = "RESUMEN PENDIENTES NEXION\n" + "-"*20 + "\n\n"
        
        for _, row in pendientes.iterrows():
            tarea = str(row.get('TAREA', 'Sin nombre')).strip()
            if not tarea or tarea == "nan": continue
            
            # Sacamos la columna tal cual está en tu imagen
            accion = str(row.get('ULTIMO ACCION', 'Sin dato')).strip()
            avance = int(row['PROGRESO'])

            # Construimos el texto plano para evitar que Telegram lo rechace
            msj += f"📌 {tarea}\n"
            msj += f"   Avance: {avance}%\n"
            msj += f"   Última Acción: {accion}\n\n"
        
        enviar_telegram(msj)
        
    except Exception as e:
        enviar_telegram(f"❌ Error: {str(e)}")
