# Informe de seguridad

## Alcance

El pipeline de GitHub Actions ejecuta SonarCloud sobre el codigo Python y Snyk sobre `app/requirements.txt`. Ambos jobs se encuentran en `.github/workflows/ci.yml` y requieren los secretos `SONAR_TOKEN` y `SNYK_TOKEN` configurados en GitHub.

## Evidencia reproducible

1. El job `sonarcloud` usa `SonarSource/sonarqube-scan-action@v4` y la configuracion `sonar-project.properties` del repositorio.
2. El job `snyk` instala el CLI oficial y ejecuta `snyk test --file=app/requirements.txt --package-manager=pip --severity-threshold=high`.
3. El endpoint `/metrics` se expone mediante `prometheus-fastapi-instrumentator`, por lo que se monitorean tiempos y conteos HTTP de la aplicacion.

## Recomendaciones

1. Mantener `SONAR_TOKEN` y `SNYK_TOKEN` solamente como secretos de GitHub; no incluirlos en archivos ni evidencias.
2. Crear un token de Docker Hub con alcance minimo de lectura/escritura para Jenkins y revocar contrasenas expuestas durante pruebas.
3. Corregir vulnerabilidades de severidad alta que reporte Snyk antes de promover una imagen.
4. Revisar el Quality Gate de SonarCloud para deuda tecnica, bugs y problemas de mantenibilidad.
5. Mantener la imagen base `python:3.11-slim` actualizada y ejecutar periodicamente el escaneo de dependencias.