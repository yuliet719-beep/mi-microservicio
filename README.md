# mi-microservicio

Entrega de la actividad 3: microservicio FastAPI con integración continua, entrega continua y despliegue declarativo en Kubernetes usando GitHub Actions, Jenkins, Docker, Helm y Argo CD.

## Objetivo de la entrega

Demostrar un flujo DevOps funcional y trazable que cubra:

1. Integración continua automática con validaciones clave.
2. Stages de despliegue claramente definidos en Jenkins.
3. Uso justificado de herramientas actuales de CI/CD.
4. Documentación técnica suficiente para revisar la solución.
5. Repositorio organizado con código, pipelines y manifiestos de despliegue.

## Evidencia frente a la rúbrica

| Criterio | Cómo se cumple en este repositorio |
| --- | --- |
| Automatiza el flujo de integración continua | `.github/workflows/ci.yml` ejecuta `lint`, `test` y validación de build Docker automáticamente en cada `push` y `pull_request` a `main`. |
| Define correctamente los stages del despliegue | `Jenkinsfile` incluye `Checkout`, `Install dependencies`, `Static analysis`, `Unit tests`, `Build Docker image`, `Validate Helm chart`, `Publish Docker image` y `Update GitOps manifest`. |
| Utiliza herramientas actuales y relevantes | GitHub Actions valida código; Jenkins orquesta CD; Docker empaqueta; Helm define despliegue; Argo CD sincroniza el estado deseado; Kubernetes ejecuta el servicio. |
| Documentación técnica | Este README explica arquitectura, stages, credenciales, ejecución local y relación entre artefactos. |
| Repositorio organizado, funcional y accesible | El proyecto separa aplicación, pruebas, pipelines, Helm y Argo CD en carpetas claras y consistentes. |

## Estructura del repositorio

- `app/`: aplicación FastAPI y `Dockerfile`.
- `tests/`: pruebas automáticas con `pytest`.
- `requirements-dev.txt`: dependencias de validación.
- `.github/workflows/ci.yml`: pipeline de integración continua.
- `.github/workflows/deploy.yml`: publicación manual de respaldo hacia Docker Hub.
- `Jenkinsfile`: pipeline principal de CI/CD para la entrega.
- `helm/`: chart de Helm para Kubernetes.
- `argocd/`: manifiesto de Argo CD para sincronización GitOps.
- `monitoring/`: configuracion de Prometheus, alertas y dashboard provisionado de Grafana.
- `docker-compose.monitoring.yml`: stack local para la aplicacion, Prometheus y Grafana.
- `docs/`: informes de las actividades y el informe de seguridad.

## Flujo CI en GitHub Actions

El workflow `ci.yml` se ejecuta automáticamente en cada cambio hacia `main` y en cada `pull_request` contra `main`.

Stages implementados:

1. `lint`: instala dependencias y ejecuta `flake8` sobre aplicación y pruebas.
2. `test`: instala dependencias y ejecuta `pytest`.
3. `docker-build-validation`: construye la imagen para confirmar que el artefacto desplegable también es válido.

Con esto, el flujo de integración no se limita a correr pruebas: también verifica estilo y empaquetado.

## Flujo CD en Jenkins

El `Jenkinsfile` concentra el pipeline solicitado en la rúbrica. Los stages están separados para que cada fallo se identifique rápido y con trazabilidad:

1. `Checkout`: descarga el código y calcula una etiqueta inmutable basada en `BUILD_NUMBER` y el commit corto.
2. `Install dependencies`: crea un entorno virtual e instala dependencias de app y validación.
3. `Static analysis`: ejecuta `flake8`.
4. `Unit tests`: ejecuta `pytest`.
5. `Build Docker image`: construye la imagen `yulietrojas/mi-microservicio`.
6. `Validate Helm chart`: valida el chart con Helm antes de publicar artefactos.
7. `Publish Docker image`: publica etiquetas versionada y `latest` en Docker Hub.
8. `Update GitOps manifest`: actualiza `helm/values-dev.yaml` con la nueva etiqueta y hace commit al repositorio para que Argo CD sincronice el cambio.

La actualización GitOps agrega `[skip jenkins]` al commit automático para evitar un ciclo infinito de builds cuando Jenkins vuelve a detectar su propio commit.

## Herramientas y justificación técnica

| Herramienta | Uso en el proyecto | Justificación |
| --- | --- | --- |
| GitHub Actions | Integración continua | Se integra directamente con el repositorio y valida cada cambio sin intervención manual. |
| Jenkins | Entrega continua | Permite modelar stages explícitos, credenciales y promoción de artefactos de forma clara para la actividad. |
| Docker | Empaquetado | Garantiza que el mismo artefacto validado sea el que se despliega. |
| Docker Hub | Registro | Centraliza imágenes versionadas y accesibles para Kubernetes. |
| Helm | Plantillas de despliegue | Parametriza repositorio, tag, réplicas y probes del despliegue. |
| Argo CD | GitOps | Toma el estado deseado desde Git y lo sincroniza automáticamente con Kubernetes. |
| Kubernetes | Ejecución | Hospeda el microservicio y usa probes para verificar salud. |
| SonarCloud | Calidad y seguridad | Analiza el código Python y publica el Quality Gate en el job `sonarcloud`. |
| Snyk | Seguridad de dependencias | Identifica vulnerabilidades en las dependencias Python durante el job `snyk`. |
| Prometheus | Recolección de métricas | Consulta `/metrics` de FastAPI cada 15 segundos y evalúa alertas. |
| Grafana | Visualización | Carga un dashboard con estado, memoria, CPU y solicitudes HTTP. |

## Despliegue declarativo

- `argocd/application.yaml` apunta al chart real en `helm/`.
- `helm/values-dev.yaml` define la imagen del ambiente de desarrollo y es el archivo que Jenkins actualiza en cada liberación.
- `helm/values-prod.yaml` queda preparado para una futura Application de Argo CD en producción (2 réplicas, tag `stable`, `pullPolicy: IfNotPresent`). No se despliega automáticamente en este entregable: solo se declara `argocd/application.yaml` apuntando a `values-dev.yaml`.
- `helm/templates/deployment.yaml` incluye `readinessProbe` y `livenessProbe` sobre `/health`, además de `resources` (requests/limits) y un `securityContext` básico (`runAsNonRoot`, sin escalamiento de privilegios).

## Credenciales necesarias en Jenkins

Configurar estos credentials de tipo `Username with password`:

1. `dockerhub-credentials`: usuario y contraseña o token de Docker Hub.
2. `github-credentials`: usuario y token personal con permisos de push al repositorio.

## Seguridad

El workflow de GitHub Actions incluye los jobs `sonarcloud` y `snyk`. Para ejecutarlos en GitHub se deben configurar los secretos `SONAR_TOKEN` y `SNYK_TOKEN`. El análisis de Snyk se mantiene como evidencia visible aunque encuentre vulnerabilidades, con el fin de que el reporte llegue al job y pueda revisarse. El alcance, la evidencia reproducible y las recomendaciones se encuentran en `docs/Actividad_1_Laboratorio_Tecnico.docx`.

## Monitoreo con Prometheus y Grafana

La aplicacion expone metricas en `GET /metrics`. Para iniciar el stack local:

```bash
docker compose -f docker-compose.monitoring.yml up --build -d
```

Servicios disponibles:

1. Microservicio: `http://localhost:8000/health`, `http://localhost:8000/metrics`.
	El stack reserva el puerto interno `8000` y lo expone en el host como `8001` para no interferir con otros servicios locales: `http://localhost:8001/health`.
2. Prometheus: `http://localhost:9090`, objetivo `mi-microservicio`.
3. Grafana: `http://localhost:3000` con usuario `admin` y contraseña `admin` para uso local.

El dashboard `Mi Microservicio - Operacion` se provisiona automaticamente. Presenta disponibilidad (`up`), memoria residente, uso de CPU y solicitudes HTTP. Las alertas `MicroserviceUnavailable` y `HighProcessMemory` se definen en `monitoring/prometheus/alerts.yml`.

Para detener los servicios:

```bash
docker compose -f docker-compose.monitoring.yml down
```

## Ejecución local

Instalar dependencias:

```bash
pip install -r app/requirements.txt -r requirements-dev.txt
```

Ejecutar pruebas:

```bash
pytest tests -v
```

Ejecutar análisis estático:

```bash
flake8 app tests --max-line-length=100 --extend-ignore=E203,W503
```

Construir la imagen:

```bash
docker build -t yulietrojas/mi-microservicio:local app
```

## Resultado esperado de la actividad

Con esta estructura, la entrega muestra un flujo completo:

1. El cambio entra por Git.
2. GitHub Actions valida calidad, pruebas y build.
3. Jenkins publica una imagen versionada.
4. Jenkins actualiza el manifiesto GitOps.
5. Argo CD detecta el nuevo tag y sincroniza Kubernetes.

La solución cubre los requisitos de automatización, stages de despliegue, herramientas justificadas, documentación técnica y organización del repositorio.
