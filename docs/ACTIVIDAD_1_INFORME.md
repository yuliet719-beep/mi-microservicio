# Actividad 1 - Laboratorio tecnico: CI/CD, seguridad y monitoreo

**Autores:** Manuel Fernando Santofimio Tovar y Beycy Yuliet Rojas Acero  
**Repositorio:** https://github.com/yuliet719-beep/mi-microservicio

## Objetivo

Implementar un flujo CI/CD para un microservicio FastAPI que integre validacion de calidad, pruebas, seguridad, empaquetado Docker, despliegue declarativo y observabilidad. La solucion evita que el pipeline escriba directamente sobre Kubernetes: Jenkins actualiza el estado deseado en Git y Argo CD realiza la sincronizacion.

## Arquitectura y flujo

1. Un `push` o `pull_request` sobre `main` inicia GitHub Actions.
2. Los jobs `lint`, `test` y `docker-build-validation` validan estilo, comportamiento y construccion del artefacto.
3. Los jobs `sonarcloud` y `snyk` analizan calidad y dependencias con resultados visibles en la ejecucion de Actions.
4. Jenkins ejecuta checkout, dependencias, analisis estatico, pruebas, build Docker, `helm lint`, publicacion en Docker Hub y actualizacion GitOps.
5. El commit automatico en `helm/values-dev.yaml` incluye `[skip jenkins]` para impedir bucles de ejecucion.
6. Argo CD observa el repositorio, renderiza el chart Helm y sincroniza el estado en Kubernetes con `prune` y `selfHeal`.
7. Prometheus consulta `/metrics`; Grafana visualiza la disponibilidad, CPU, memoria y tasa de solicitudes.

## Evidencias tecnicas

| Requisito | Implementacion | Evidencia verificable |
| --- | --- | --- |
| CI/CD automatizado | `.github/workflows/ci.yml` y `Jenkinsfile` | Jobs independientes de GitHub Actions y ocho stages en Jenkins. |
| Calidad | `flake8` y `pytest` | El pipeline ejecuta `flake8 app tests` y `pytest tests -v`; las tres pruebas cubren `/health`, `/hello` y 404. |
| Artefacto | Dockerfile Python 3.11 y Docker Hub | Jenkins etiqueta la imagen con `BUILD_NUMBER-commit` y `latest`. |
| Seguridad | SonarCloud y Snyk | Jobs `sonarcloud` y `snyk`; configuracion en `sonar-project.properties` e informe en `docs/INFORME_SEGURIDAD.md`. |
| GitOps | Helm y Argo CD | `argocd/application.yaml` apunta al chart `helm` y usa `values-dev.yaml`. |
| Monitoreo | Prometheus y Grafana | `docker-compose.monitoring.yml` arranca ambos servicios y provisiona el dashboard. |

La ejecucion Jenkins #7 documentada durante la practica termino en `SUCCESS`: ejecuto las etapas de checkout, dependencias, analisis estatico, pruebas unitarias, build Docker, validacion Helm, publicacion de imagen y actualizacion GitOps. Adicionalmente, la ejecucion GitHub Actions `33335315017` del 30 de agosto de 2026 finalizo exitosamente con los jobs `lint`, `test`, `docker-build-validation`, `snyk` y `sonarcloud`, y publico el artefacto descargable `snyk-report`. La evidencia operativa y las capturas propias estan consolidadas en `docs/EVIDENCIA_OPERATIVA.md`.

## Seguridad y recomendaciones

SonarCloud analiza las fuentes Python y Snyk analiza las dependencias declaradas. Los secretos `SONAR_TOKEN` y `SNYK_TOKEN` se gestionan desde GitHub Actions, mientras que Jenkins usa credenciales de Docker Hub y GitHub administradas por el servidor. Las recomendaciones son: revisar el Quality Gate antes de promover una version, resolver vulnerabilidades de severidad alta, utilizar tokens de alcance minimo y rotar toda contrasena que haya sido compartida fuera de un gestor de secretos.

## Monitoreo y alertas

`prometheus-fastapi-instrumentator` expone `/metrics`. Prometheus recolecta cada 15 segundos y Grafana carga automaticamente el dashboard **Mi Microservicio - Operacion**. Este muestra estado del objetivo (`up`), memoria residente, uso de CPU y solicitudes HTTP por handler, metodo y codigo de respuesta. Se definieron dos alertas: indisponibilidad de la aplicacion durante un minuto y memoria residente superior a 100 MiB durante cinco minutos.

## Ejecucion de la evidencia

```bash
docker compose -f docker-compose.monitoring.yml up --build -d
```

Abrir Grafana en `http://localhost:3000` y Prometheus en `http://localhost:9090`. Producir trafico con solicitudes a `http://localhost:8001/health` y `http://localhost:8001/hello`, y capturar el dashboard. La definicion de alertas se puede verificar en Prometheus, menu **Alerts**.

## Reflexion

Separar CI, CD, GitOps y observabilidad disminuye el riesgo operacional. GitHub Actions detecta defectos cerca del cambio; Jenkins construye un artefacto trazable; Helm convierte configuracion en manifiestos repetibles; Argo CD evita credenciales de Kubernetes dentro del pipeline; y Prometheus/Grafana convierten el comportamiento en produccion en una señal observable. El principal aprendizaje es que automatizar el despliegue no es suficiente: un flujo maduro requiere controles de seguridad, trazabilidad de imagen y monitoreo posterior a la liberacion.