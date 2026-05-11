FROM python:3.11-slim

WORKDIR /app

# libgomp1 es requerido por XGBoost y LightGBM
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY engine.py train.py ./

# Si el modelo ya está entrenado y commiteado, se copia.
# Si no, se entrena al inicio del contenedor (ver entrypoint).
# COPY model.pkl* ./

RUN useradd -m -u 1000 cardio && \
    mkdir -p /data && chown -R cardio:cardio /app /data
USER cardio

# Si no existe model.pkl entrena antes de arrancar el engine
CMD ["sh", "-c", "if [ ! -f /data/model.pkl ]; then python train.py; fi; exec python -u engine.py"]
