import requests

def probar_conexion_directa():
    # Tus datos confirmados
    token = "8788568940:AAGGCFpRREU6SI1ngaIj8mbidLitT55aXcc"
    chat_id = "7273779444"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Mensaje de prueba ultra simple
    payload = {
        "chat_id": chat_id,
        "text": "🚀 ¡Rigo! Si lees esto, la conexión de Nexion ya funciona. El problema estaba en el filtro de la tabla."
    }
    
    print("Intentando enviar mensaje...")
    try:
        response = requests.post(url, data=payload)
        print(f"Respuesta de Telegram: {response.json()}")
    except Exception as e:
        print(f"Error fatal: {e}")

if __name__ == "__main__":
    probar_conexion_directa()
