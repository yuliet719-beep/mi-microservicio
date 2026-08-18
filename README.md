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

## Despliegue declarativo

- `argocd/application.yaml` apunta al chart real en `helm/`.
- `helm/values-dev.yaml` define la imagen del ambiente de desarrollo y es el archivo que Jenkins actualiza en cada liberación.
- `helm/templates/deployment.yaml` incluye `readinessProbe` y `livenessProbe` sobre `/health`, lo que mejora la operabilidad del despliegue.

## Credenciales necesarias en Jenkins

Configurar estos credentials de tipo `Username with password`:

1. `dockerhub-credentials`: usuario y contraseña o token de Docker Hub.
2. `github-credentials`: usuario y token personal con permisos de push al repositorio.

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
