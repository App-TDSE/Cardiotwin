FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY watchdog.py .

# Crear directorio para la base de datos
RUN mkdir -p /data

CMD ["python", "watchdog.py"]
