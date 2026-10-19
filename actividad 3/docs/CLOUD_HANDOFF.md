# Despliegue cloud: pendiente de cuentas y ejecución

Estado: no aplicado. La ejecución demostrada es Docker local. No existen evidencias de GCP/AWS.
Los directorios `iac/gcp` e `iac/aws` preparan VPC, VM y PostgreSQL gestionado privado,
Flow Logs, acceso administrativo limitado y controles básicos. No constituyen por sí
solos la solución de observabilidad cloud completa. Revisar costos y permisos en una
cuenta sandbox antes de aplicar. No habilitar Security Hub en una cuenta ya gestionada
sin importar primero el recurso existente. `db_password` y el estado de Terraform son sensibles.

## Secuencia de cierre de brechas

1. Autenticar los CLI oficiales con perfiles de sandbox. Configurar facturación y presupuesto.
2. Ejecutar `terraform init`, `terraform validate` y `terraform plan` por proveedor.
   Pasar `TF_VAR_project_id` y `TF_VAR_db_password` por entorno; usar backend remoto cifrado.
3. Revisar y aplicar el plan. Se crean recursos con costo. La base tiene protección de borrado.
4. Acceder a la VM AWS mediante SSM Session Manager y a GCP con IAP/OS Login. No abrir
   los puertos de Grafana, PostgreSQL ni controles de caos a Internet.
5. Instalar Docker y Compose desde el proveedor oficial. Clonar este repositorio en un
   commit auditado y ejecutar `scripts/init_env.py`. Transferir únicamente secretos de sandbox
   por Secret Manager/SSM, nunca mediante Git, capturas ni archivos de evidencias.
6. Crear `compose.cloud.yaml` fuera de Git que sobrescriba `data-service.environment.DATABASE_URL`
   con la conexión de RDS o Cloud SQL y `CLOUD_PROVIDER` con `aws` o `gcp`. Usar TLS validado:
   `sslmode=verify-full&sslrootcert=/ruta/ca.pem`, montar la CA oficial en el contenedor y
   definir `DB_HOST` como el endpoint real. Cargar `config/init.sql` en la base gestionada.
   El PostgreSQL local puede detenerse tras ajustar `depends_on` para el despliegue cloud.
7. Ejecutar Compose con el override y repetir `scripts/experiment.py` en la VM. Descargar
   evidencias por un canal autorizado a `evidencias/aws/` y `evidencias/gcp/`, sin mezclarlas
   con los resultados locales. Comprobar `cloud.provider`, endpoint de DB y spans SQL.
8. Configurar el Collector con exportadores autenticados para Google Cloud Monitoring/Logging/Trace
   o ADOT/CloudWatch/X-Ray. Los exportadores de este laboratorio apuntan al stack local.
   Añadir detección nativa gestionada: DevOps Guru para RDS con la etiqueta
   `devops-guru-actividad3=sandbox`, si la cuenta es elegible, o detector de anomalías
   compatible de Cloud Monitoring. El detector Python no equivale al producto gestionado.
9. Instalar Cloud Service Mesh en GCP; para AWS acordar con la docente Istio/Envoy o ECS
   Service Connect. AWS App Mesh finalizó soporte el 30 de septiembre de 2026.
   El enrutamiento Envoy local demuestra L7 básico; no afirma mTLS ni un control plane.
10. Activar SCC a nivel de proyecto/organización según permisos disponibles y el estándar
    pertinente en Security Hub. Capturar hallazgos, métricas N-S/E-W y rechazos reales en VPC
    Flow Logs; conectar alertas y dashboard a esas fuentes. El log Envoy no es un VPC Flow Log.
11. Grabar demostración en ambas clouds, revisar los cinco criterios de la rúbrica y reemplazar
    el estado pendiente solo cuando exista evidencia verificable.
12. Cerrar el sandbox: exportar evidencias, retirar fallos y revisar el plan de destrucción.
    Desactivar protección de DB únicamente tras respaldar los datos y autorizar su eliminación.

## Fuentes oficiales

- https://docs.aws.amazon.com/app-mesh/latest/userguide/
- https://docs.aws.amazon.com/devops-guru/latest/userguide/welcome.html
- https://cloud.google.com/service-mesh/docs
- https://cloud.google.com/vpc/docs/flow-logs
- https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
- https://cloud.google.com/security-command-center/docs/concepts-security-command-center-overview

Las instrucciones cloud son una ruta de trabajo pendiente, no evidencia de implementación.
