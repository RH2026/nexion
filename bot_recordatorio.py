import pandas as pd
import requests
import io
import time
from datetime import datetime

TOKEN = "8788568940:AAGGCFpRREU6SI1ngaIj8mbidLitT55aXcc"
CHAT_ID = "7273779444"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/main/tareas.csv"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # CAMBIAMOS A HTML PARA QUE NO MARQUE ERROR CON SÍMBOLOS RÁROS
    payload = {
        "chat_id": CHAT_ID, 
        "text": mensaje, 
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def procesar():
    try:
        r = requests.get(f"{CSV_URL}?t={int(time.time())}")
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = [c.strip().upper() for c in df.columns]
        
        if 'FECHA' in df.columns:
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')

        df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors='coerce').fillna(0)
        pendientes = df[df["PROGRESO"] < 100].copy()

        if pendientes.empty:
            enviar_telegram("<b>Nexion Smart Logistics:</b> Sin pendientes hoy.")
            return

        msj = "<b>--- PENDIENTES NEXION SMART LOGISTICS ---</b>\n\n"
        hoy = datetime.now()

        for _, row in pendientes.iterrows():
            tarea = str(row.get('TAREA', 'Sin nombre')).strip()
            if not tarea or tarea == "nan":
                continue
            
            # Calculo de dias
            fecha_val = row.get('FECHA')
            dias = f"{(hoy - fecha_val).days} días" if pd.notnull(fecha_val) else "S/F"
            
            # Datos adicionales
            accion = str(row.get('ULTIMO ACCION', 'S/D')).strip()
            avance = int(row['PROGRESO'])

            # FORMATO LIMPIO: Solo el pin al inicio
            msj += f"📌 <b>{tarea}</b>\n"
            msj += f"   <b>Dias sin resolver:</b> {dias} | <b>Avance:</b> {avance}%\n"
            msj += f"   <i>Comentarios: {accion}</i>\n"
            msj += "----------------------------\n"

        enviar_telegram(msj)

    except Exception as e:
        enviar_telegram(f"Error: {str(e)}")

if __name__ == "__main__":
    procesar()
