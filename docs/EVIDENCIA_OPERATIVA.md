# Evidencia operativa - Actividad 1

Fecha de verificacion: 30 de agosto de 2026.

## Monitoreo local verificado

El comando ejecutado fue:

```bash
docker compose -f docker-compose.monitoring.yml up --build -d
```

Resultados observados:

| Componente | Direccion | Resultado |
| --- | --- | --- |
| Microservicio FastAPI | `http://localhost:8001/health` | Respuesta HTTP 200: `{"status":"ok"}`. |
| Prometheus | `http://localhost:9090/api/v1/targets` | Target `http://microservice:8000/metrics` con estado `up`. |
| Grafana | `http://localhost:3000/api/health` | Estado de base de datos `ok`. |
| Dashboard | Grafana / carpeta `DevOps` | Dashboard provisionado: `Mi Microservicio - Operacion`. |

Se generaron solicitudes a `/health` y `/hello` para alimentar las series HTTP. El dashboard contiene estado del objetivo, memoria residente, CPU del proceso y solicitudes HTTP por handler, metodo y estado. Las alertas se encuentran en `monitoring/prometheus/alerts.yml`.

Capturas propias almacenadas en el repositorio:

1. `evidencia-prometheus-target.png`: Prometheus muestra `mi-microservicio (1/1 up)` y el endpoint `/metrics` en estado `UP`.
2. `evidencia-grafana-dashboard.png`: dashboard Grafana con estado `1`, memoria, CPU y solicitudes HTTP reales.
3. `evidencia-sonarcloud-quality-gate.png`: SonarQube Cloud muestra Quality Gate `Passed`, 0 nuevos issues y 0 Security Hotspots.
4. `evidencia-github-actions-snyk-sonarcloud.png`: CI Pipeline exitoso, con los cinco jobs y un artefacto Snyk publicado.
5. `evidencia-jenkins-build-7.png`: captura autenticada de Jenkins Pipeline Overview para el build #7; muestra en verde `Checkout`, dependencias, analisis estatico, pruebas, build Docker, validacion Helm, publicacion Docker, actualizacion GitOps y post acciones.

## Evidencia CI/CD y GitOps

1. GitHub Actions ejecuta lint, pruebas, build Docker, SonarCloud y Snyk desde `.github/workflows/ci.yml`.
2. La ejecucion `33335315017` del 30 de agosto de 2026 termino en `success`: https://github.com/yuliet719-beep/mi-microservicio/actions/runs/33335315017
3. Los cinco jobs finalizaron correctamente: `lint`, `test`, `docker-build-validation`, `snyk` y `sonarcloud`. El job Snyk publica el artefacto `snyk-report` con el JSON de resultados para su descarga autenticada en GitHub Actions.
4. El build Jenkins #7 registrado durante la practica termino en `SUCCESS` tras ejecutar checkout, dependencias, flake8, pytest, build Docker, Helm lint, publicacion Docker y actualizacion GitOps. La salida confirmada registra las tres pruebas como `PASSED`, `1 chart(s) linted, 0 chart(s) failed` y `Finished: SUCCESS`.
5. `argocd/application.yaml` usa el chart Helm, la rama `main`, `values-dev.yaml`, `prune` y `selfHeal`.

## Estado de verificacion GitOps

En la comprobacion del 30 de agosto de 2026, Argo CD detecto y sincronizo la revision `4fbe8de`, pero el estado de salud quedo `Progressing`. El evento del pod identifica la causa: la imagen remota `yulietrojas/mi-microservicio:latest` que esta publicada actualmente se ejecuta como `root`, mientras el chart exige `runAsNonRoot: true`. El Dockerfile del repositorio fue corregido y validado localmente con imagen distroless y usuario `nonroot:nonroot`; para completar la evidencia de Argo CD en estado `Healthy` se debe publicar esa imagen corregida usando credenciales con permiso de escritura sobre el namespace `yulietrojas`, y ejecutar de nuevo el build Jenkins.

## Capturas para anexar

1. Jenkins, pantalla Pipeline Overview del build exitoso.
2. Grafana, dashboard `Mi Microservicio - Operacion` mostrando series y estado `up`.
3. Prometheus, pantalla Targets con estado `UP` y Alerts con las reglas cargadas.
4. GitHub Actions, ejecucion `33335315017`, con `sonarcloud`, `snyk` y el artefacto `snyk-report` exitosos.