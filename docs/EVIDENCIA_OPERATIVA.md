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

## Evidencia CI/CD y GitOps

1. GitHub Actions ejecuta lint, pruebas, build Docker, SonarCloud y Snyk desde `.github/workflows/ci.yml`.
2. La ejecucion `33334905943` del 30 de agosto de 2026 termino en `success`: https://github.com/yuliet719-beep/mi-microservicio/actions/runs/33334905943
3. Los cinco jobs finalizaron correctamente: `lint`, `test`, `docker-build-validation`, `snyk` y `sonarcloud`.
4. El build Jenkins #7 registrado durante la practica termino en `SUCCESS` tras ejecutar checkout, dependencias, flake8, pytest, build Docker, Helm lint, publicacion Docker y actualizacion GitOps.
5. `argocd/application.yaml` usa el chart Helm, la rama `main`, `values-dev.yaml`, `prune` y `selfHeal`.

## Capturas para anexar

1. Jenkins, pantalla Pipeline Overview del build exitoso.
2. Grafana, dashboard `Mi Microservicio - Operacion` mostrando series y estado `up`.
3. Prometheus, pantalla Targets con estado `UP` y Alerts con las reglas cargadas.
4. GitHub Actions, ejecucion `33334905943`, con los jobs `sonarcloud` y `snyk` exitosos.