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
    payload = {"chat_id": CHAT_ID, "text": mensaje} 
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def procesar():
    try:
        # Descarga del CSV
        r = requests.get(f"{CSV_URL}?t={int(time.time())}")
        df = pd.read_csv(io.StringIO(r.text))
        
        # Limpiamos nombres de columnas
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Convertimos la columna FECHA
        if 'FECHA' in df.columns:
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')

        df["PROGRESO"] = pd.to_numeric(df["PROGRESO"], errors='coerce').fillna(0)
        pendientes = df[df["PROGRESO"] < 100].copy()

        if pendientes.empty:
            enviar_telegram("Nexion: Sin pendientes hoy.")
            return

        msj = "--- REPORTE DE PENDIENTES NEXION ---\n\n"
        hoy = datetime.now()

        for _, row in pendientes.iterrows():
            tarea = str(row.get('TAREA', 'Sin nombre')).strip()
            if not tarea or tarea == "nan": 
                continue
            
            # Cálculo de días
            fecha_valor = row.get('FECHA')
            if pd.notnull(fecha_valor):
                diff = hoy - fecha_valor
                dias_transcurridos = f"{diff.days} dias"
            else:
                dias_transcurridos = "Sin fecha"

            # Sacamos la columna ULTIMO ACCION
            accion = str(row.get('ULTIMO ACCION', 'SIN DATO')).strip()
            avance = int(row['PROGRESO'])

            # Construcción del mensaje (Líneas limpias sin caracteres raros)
            msj += f"📌 TAREA: {tarea}\n"
            msj += f"   ⏳ ANTIGÜEDAD: {dias_transcurridos}\n"
            msj += f"   📊 AVANCE: {avance}%\n"
            msj += f"   📝 ULTIMA ACCION: {accion}\n"
            msj += "----------------------------\n"
        
        enviar_telegram(msj)
        
    except Exception as e:
        error_msj = f"Error en script: {str(e)}"
        print(error_msj)
        enviar_telegram(error_msj)

if __name__ == "__main__":
    procesar()
        
    except Exception as e:
        enviar_telegram(f"Error en el script: {str(e)}")

if __name__ == "__main__":
    procesar()
