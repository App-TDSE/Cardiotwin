FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY emulator.py .

# Usuario no root por buenas prácticas
RUN useradd -m -u 1000 cardio && chown -R cardio:cardio /app
USER cardio

CMD ["python", "-u", "emulator.py"]
