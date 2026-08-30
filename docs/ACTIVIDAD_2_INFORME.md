# Actividad 2 - Estudio de caso: postmortem y transicion de DevOps a MLOps

**Autores:** Manuel Fernando Santofimio Tovar y Beycy Yuliet Rojas Acero

## Resumen del incidente simulado

Durante la configuracion del flujo de entrega se simulo un incidente de liberacion: Jenkins construia la imagen correctamente, pero el despliegue no quedaba disponible. El analisis encontro dos factores: una diferencia entre la etiqueta/repositorio publicados y los valores consumidos por Helm, y la necesidad de validar el chart antes de publicar. El riesgo era liberar una imagen que no pudiera ser encontrada por Kubernetes o dejar el servicio sin endpoints utiles. El caso confirma que la automatizacion debe contener mecanismos de retroalimentacion y recuperacion, no solo pasos de entrega (Humble & Farley, 2010).

## Linea de tiempo y respuesta

1. **Deteccion:** la validacion posterior al despliegue mostro que el servicio no tenia la disponibilidad esperada.
2. **Contencion:** se detuvo la promocion automatica y se revisaron los manifests y el pipeline antes de publicar una imagen adicional.
3. **Diagnostico:** se verificaron etiquetas, selectores, probes y valores Helm. Tambien se agrego `helm lint` antes de la publicacion.
4. **Recuperacion:** se alinearon los valores de imagen que actualiza Jenkins con el chart de Helm y se uso una etiqueta inmutable compuesta por numero de build y commit corto.
5. **Prevencion:** se mantuvieron readiness/liveness probes, recursos, `securityContext`, alertas de disponibilidad y una actualizacion GitOps trazable.

## Que salio bien

El servicio tenia endpoint `/health`, pruebas automatizadas y validacion estandar con flake8. Esto redujo el espacio de diagnostico. El modelo GitOps tambien resulto util: el estado deseado quedo registrado en Git, por lo que el cambio fue auditable y reversible. La separacion de responsabilidades fue adecuada: Jenkins publica y actualiza configuracion; Argo CD sincroniza Kubernetes; Prometheus observa el comportamiento. Esta observabilidad permite que desarrollo y operaciones compartan señales y decisiones, en lugar de transferir problemas entre equipos (Google, n.d.).

## Que salio mal

La primera definicion no garantizaba de manera suficiente que el repositorio y tag de la imagen publicada fueran exactamente los consumidos por el chart. Adicionalmente, la ejecucion local de herramientas en contenedor requiere considerar rutas visibles para el daemon Docker. Estas condiciones no son errores de negocio, pero si fallas de integracion que un pipeline debe detectar temprano.

## Aprendizajes y mejoras

La leccion principal es que una liberacion es una cadena de contratos: codigo, imagen, tag, manifest y estado del cluster deben referirse al mismo artefacto. Como mejoras se definieron etiquetas inmutables, `helm lint`, actualizacion atomica de los valores GitOps, escaneo Snyk, analisis SonarCloud y alertas de disponibilidad/memoria. Como siguiente paso se recomienda agregar pruebas de despliegue en un namespace efimero y una politica que bloquee la promocion si el Quality Gate o Snyk reportan problemas graves. La mejora continua de la plataforma debe reducir friccion y hacer visibles los cuellos de botella para el equipo (Spotify Engineering, 2020).

## DevOps y MLOps

DevOps automatiza la entrega de software convencional: compilar, probar, empaquetar, desplegar y observar una aplicacion. MLOps conserva esas practicas, pero agrega el ciclo de vida de datos y modelos. En DevOps, el artefacto principal suele ser una imagen o binario; en MLOps se deben versionar tambien dataset, caracteristicas, experimento, modelo, metricas de validacion y reglas de aprobacion (Osipov, 2022).

Un pipeline MLOps agregaria etapas de validacion de datos, entrenamiento reproducible, comparacion contra una linea base y registro del modelo. Tras desplegar, ademas de CPU, memoria y errores HTTP, se monitorean drift de datos, drift de concepto, sesgo y degradacion de precision. Herramientas como DVC permiten versionar datos, MLflow registra experimentos y modelos, y Kubeflow orquesta entrenamientos sobre Kubernetes (Osipov, 2022).

```text
DevOps: codigo -> build -> pruebas -> imagen -> despliegue -> metricas operativas
MLOps: codigo + datos -> validacion -> entrenamiento -> evaluacion -> registro del modelo
       -> despliegue -> metricas operativas + drift + calidad + sesgo
```

Para este caso, FastAPI, Docker, Jenkins, Helm, Argo CD, Prometheus y Grafana se conservarian. Se añadirian DVC para datos, MLflow para experimento/registro y Kubeflow para entrenamiento. La promocion solo ocurriria cuando las pruebas de software y los umbrales de calidad del modelo sean aprobados.

## Conclusion

El incidente evidencia que automatizar sin observabilidad solo acelera los errores. El flujo implementado mejora la confiabilidad porque desplaza validaciones hacia la izquierda, usa Git como fuente de verdad y mide la aplicacion despues del despliegue. La evolucion a MLOps extiende este criterio: no basta con que el servicio este sano; el modelo y los datos deben seguir siendo correctos y responsables en produccion.

## Referencias

Google. (s. f.). *How SRE relates to other disciplines*. https://sre.google/workbook/how-sre-relates/

Humble, J., & Farley, D. (2010). *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. Addison-Wesley Professional.

Osipov, C. (2022). *MLOps engineering at scale*. Manning Publications.

Spotify Engineering. (2020, 25 de agosto). *How we improved developer productivity for our DevOps teams*. https://engineering.atspotify.com/2020/08/how-we-improved-developer-productivity-for-our-devops-teams/