# 1. Usamos Python (la base)
FROM python:3.11-slim

# 2. Creamos una carpeta para tu app dentro del servidor
WORKDIR /app

# 3. Copiamos tu lista de librerías (pandas, nicegui, openpyxl, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos todo tu código a la carpeta del servidor
COPY . .

# 5. El comando mágico para que Railway abra el puerto correcto
# Reemplaza 'main.py' por el nombre de tu archivo principal
CMD ["python", "main.py"]