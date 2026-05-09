# Cardiotwin Project

Este proyecto es una simulación de monitoreo cardíaco en tiempo real utilizando MQTT y Machine Learning.

## Estructura
- **data/**: Contiene el dataset `framingham.csv`.
- **services/emulator/**: Simula un sensor publicando datos al broker MQTT.
- **services/engine/**: Entrena un modelo y procesa los datos en tiempo real para predecir riesgo cardíaco.
- **services/dashboard/**: Visualización en tiempo real con Streamlit.
- **mosquitto/**: Configuración del broker MQTT.

## Cómo ejecutar
1. Asegúrate de tener Docker y Docker Compose instalados.
2. Ejecuta el comando:
   ```bash
   docker-compose up --build
   ```
3. Accede al dashboard en: `http://localhost:8501`

## Integrantes
- **Estudiante A**: Emulator Service
- **Estudiante B**: Engine Service
- **Estudiante C**: Dashboard Service