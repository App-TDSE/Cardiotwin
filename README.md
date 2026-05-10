# Cardiotwin Project

Este proyecto es una simulación de monitoreo cardíaco en tiempo real utilizando MQTT y Machine Learning.

## Estructura
- **data/**: Contiene el dataset `framingham.csv`.
- **services/emulator/**: Simula un sensor publicando datos al broker MQTT.
- **services/engine/**: Entrena un modelo (XGBoost) y procesa los datos en tiempo real para predecir riesgo cardíaco, incluyendo explicabilidad SHAP.
- **services/dashboard/**: Backend FastAPI que sirve el frontend HTML estático principal.
- **services/dashboard-st/**: Visualización interactiva en tiempo real (Semáforo de Riesgo y gráficos SHAP) construida con Streamlit.
- **mosquitto/**: Configuración del broker MQTT.

## Cómo ejecutar en Local
1. Asegúrate de tener Docker y Docker Compose instalados.
2. Ejecuta el comando en la raíz del proyecto:
   ```bash
   docker-compose up --build -d
   ```
3. Accede al Dashboard Integrado (Frontend HTML con Streamlit incrustado) en: `http://localhost:8501`

## Integración con Relojes Inteligentes (Smartwatches)

Para conectar tu reloj inteligente y que el dashboard se actualice en tiempo real, tu dispositivo (o aplicación puente) debe publicar las mediciones vía MQTT al broker Mosquitto interno.

**Detalles de conexión:**
- **Tópico MQTT**: `cardiotwin/telemetry/raw`
- **Formato del Payload (JSON)**:
  ```json
  {
    "patient_id": "id_del_reloj_01",
    "sysBP": 120,
    "diaBP": 80,
    "heartRate": 72,
    "glucose": 95,
    "timestamp": "2026-05-10T10:00:00Z"
  }
  ```

Al recibir el paquete JSON en ese tópico, el sistema automáticamente ejecutará el modelo de ML y actualizará la interfaz en la pantalla de forma instantánea.

## Estrategia de Despliegue a Producción (Deploy)

Al estar orquestado con `docker-compose`, llevar el ecosistema a producción es muy directo:

1. **Infraestructura Cloud (VM)**: La solución más sencilla es desplegar una Máquina Virtual (por ejemplo, EC2 en AWS o VM en Azure), clonar el repositorio y ejecutar `docker-compose up -d`.
2. **Reverse Proxy (Nginx/Traefik)**: Es fundamental exponer únicamente el puerto `8501` usando un proxy inverso y configurar certificados SSL/TLS. Esto protegerá la interfaz (HTTPS) y permitirá conexiones seguras (MQTTS) para los smartwatches remotos.
3. **Persistencia de Base de Datos**: Actualmente, `cardiotwin.db` utiliza SQLite montado en un volumen compartido. Para escalar a múltiples usuarios simultáneos, el `engine` puede ser configurado fácilmente para apuntar a un servicio como PostgreSQL alojado en la nube.

## Validación y Pruebas (End-to-End)

El flujo completo del sistema está validado mediante pruebas E2E en tiempo real:
1. **Ingesta**: Se inyecta un JSON con signos vitales en el tópico MQTT (`cardiotwin/telemetry/raw`).
2. **Inferencia de IA**: El `engine` captura el mensaje y ejecuta el modelo predictivo (XGBoost) para calcular el riesgo cardiovascular y la explicabilidad SHAP.
3. **Persistencia**: Los resultados son almacenados instantáneamente en `cardiotwin.db` (SQLite).
4. **Visualización Reactiva**: El Dashboard híbrido detecta los cambios en el volumen de Docker compartido y renderiza los nuevos datos, el semáforo y los gráficos SHAP en las pantallas sin necesidad de refrescar la página manualmente.

## Integrantes
- **Estudiante A**: Emulator Service
- **Estudiante B**: Engine Service
- **Estudiante C**: Dashboard Service