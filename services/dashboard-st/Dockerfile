FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
RUN mkdir -p /app/static

RUN useradd -m -u 1000 cardio && chown -R cardio:cardio /app
# USER cardio

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8501/streamlit/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port", "8501", \
     "--server.address", "0.0.0.0", \
     "--server.baseUrlPath", "streamlit", \
     "--server.headless", "true", \
     "--browser.gatherUsageStats", "false"]
