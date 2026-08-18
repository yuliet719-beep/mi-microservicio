# mi-microservicio

Microservicio FastAPI desplegado en Kubernetes vía Helm y ArgoCD, con dos pipelines complementarios de CI/CD: **CI con GitHub Actions** y **CD con Jenkins**.

## Estructura del repositorio

- `app/` — Código fuente de la aplicación (FastAPI) y Dockerfile
- `tests/` — Pruebas automatizadas (pytest)
- `conftest.py` — Configuración de path para que pytest importe app.py
- `requirements-dev.txt` — Dependencias de desarrollo/pruebas (pytest, httpx, flake8)
- `.github/workflows/ci.yml` — Pipeline CI (integración continua)
- `.github/workflows/deploy.yml` — Pipeline de build & push de imagen a DockerHub
- `Jenkinsfile` — Pipeline CD (entrega continua) con Jenkins
- `helm/` — Chart de Helm para despliegue en Kubernetes
- `argocd/` — Manifiesto de la Application de ArgoCD

## Pipeline CI — GitHub Actions (ci.yml)

Se ejecuta automáticamente en cada push o pull request sobre main. Etapas:

1. Checkout del código del repositorio.
2. Configuración de Python 3.11.
3. Instalación de dependencias de producción (app/requirements.txt) y de pruebas (requirements-dev.txt).
4. Ejecución de pruebas con pytest sobre los endpoints /health y /hello.
5. Análisis estático del código con flake8.

Este pipeline garantiza que ningún cambio se integre a main sin pasar validación funcional y de estilo básicas.

## Pipeline CD — Jenkins (Jenkinsfile)

Define el flujo de entrega continua hacia DockerHub. Etapas:

1. Clonar repositorio: obtiene la última versión de main desde GitHub.
2. Construir imagen Docker: usa el Dockerfile en app/ para generar la imagen yulietrojas/mi-microservicio, etiquetada con el número de build y latest.
3. Publicar imagen en DockerHub: autentica con credenciales gestionadas por Jenkins (dockerhub-credentials) y publica ambas etiquetas.

Las credenciales de DockerHub deben configurarse en Jenkins como un credential de tipo Username with password con el ID dockerhub-credentials, para que la variable DOCKERHUB_CREDENTIALS se resuelva correctamente en el pipeline.

## Cómo correr las pruebas localmente

pip install -r app/requirements.txt -r requirements-dev.txt
pytest tests/ -v

## Relación con el resto de la arquitectura DevOps

Este repositorio se integra con el resto del ecosistema DevOps del proyecto: una vez que la imagen se publica (vía GitHub Actions o Jenkins), ArgoCD detecta el cambio en el chart de Helm y sincroniza el despliegue en el clúster de Kubernetes de forma declarativa, cerrando el ciclo de entrega continua.
