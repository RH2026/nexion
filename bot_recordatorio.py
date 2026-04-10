import pandas as pd
import requests
import io
import time

TOKEN = "8788568940:AAGGCFpRREU6SI1ngaIj8mbidLitT55aXcc"
CHAT_ID = "7273779444"
CSV_URL = "https://raw.githubusercontent.com/RH2026/nexion/main/tareas.csv"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # QUITAMOS EL PARSE_MODE para que no de errores por caracteres especiales
    payload = {"chat_id": CHAT_ID, "text": mensaje} 
    try:
        r = requests.post(url, data=payload, timeout=10)
        # Si quieres ver en consola si falló algo:
        if r.status_code != 200:
            print(f"Error de Telegram: {r.text}")
    except:
        pass

def procesar():
    try:
        r = requests.get(f"{CSV_URL}?t={int(time.time())}")
        df = pd.read_csv(io.StringIO(r.text))
        
        # Limpiar columnas
        df.columns = [c.strip().upper() for c in df.columns]
        
        df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors='coerce').fillna(0)
        pendientes = df[df["PROGRESO"] < 100].copy()

        if pendientes.empty:
            enviar_telegram("Nexion: Sin pendientes hoy.")
            return

        msj = "--- RESUMEN PENDIENTES NEXION ---\n\n"
        
        for _, row in pendientes.iterrows():
            tarea = str(row.get('TAREA', 'Sin nombre')).strip()
            if not tarea or tarea == "nan": continue
            
            # AGREGAMOS LA PERRA COLUMNA
            accion = str(row.get('ULTIMO ACCION', 'SIN DATO')).strip()
            avance = int(row['PROGRESO'])

            msj += f"📌 TAREA: {tarea}\n"
            msj += f"   AVANCE: {avance}%\n"
            msj += f"   ULTIMA INFORMACION: {accion}\n\n"
            msj += "----------------------------\n"
        
        enviar_telegram(msj)
        
    except Exception as e:
        enviar_telegram(f"Error en el script: {str(e)}")

if __name__ == "__main__":
    procesar()
