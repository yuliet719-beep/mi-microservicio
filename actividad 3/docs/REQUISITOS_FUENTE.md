# Enunciado leído en Moodle

Fuente autenticada: https://unisabanae-learning.unisabana.edu.co/mod/assign/view.php?id=306421
Consulta: 18/10/2026, América/Bogotá. Actividad 3.3, laboratorio integrador U3.
Entrega grupal de tres integrantes. Duración estimada: 20 horas. Cierre: 18/10/2026 23:59.

## Módulos solicitados

A. Tercer microservicio data-service con GCP Cloud SQL y AWS RDS; OTel SDK de
tres pilares y spans DB con convenciones semánticas; Cloud Service Mesh/AWS App Mesh L7.

B. Cloud Monitoring Anomaly Detection o AWS DevOps Guru; correlación
error_rate > baseline + 2 sigma AND latency_p99 > SLO_threshold, con trace_id;
demostrar reducción de ruido frente a umbrales estáticos.

C. VPC Flow Logs de GCP y AWS y alertas de tráfico anómalo; SCC o Security Hub;
dashboard de autenticaciones fallidas, tráfico N-S/E-W y CVEs activos.

D. Dos experimentos en sandbox: service-b con 200 ms y data-service con error rate
10%; detección <2 min; analizar SLO, error budget y accionabilidad.

E. Ocho dominios del Observability Foundation Blueprint en escala 1-5 y roadmap
para el siguiente nivel en tres meses.

## Entregables

Repositorio GitHub con IaC, instrumentación, configuraciones y scripts; video de
demostración en vivo; PDF ejecutivo de 10 páginas con arquitectura, evidencias y madurez.
Recomendación: repositorio público con tag final v1.0; nunca caos en recursos compartidos.

## Nivel excelente de la rúbrica

| Criterio | Puntos máximos | Evidencia requerida |
|---|---:|---|
| Arquitectura | 1.25 | Tres servicios OTel, malla y correlación en ambas clouds |
| AIOps | 1.00 | Detección automática, correlación y evidencia cuantitativa |
| Red y seguridad | 1.00 | Funcional en ambas clouds con dashboards y alertas |
| Caos | 1.00 | Dos experimentos, MTTD <=2 min y análisis SLO/budget |
| Madurez y presentación | 0.75 | Autoevaluación completa, roadmap accionable y demo en vivo |

Esta transcripción de trabajo conserva los requisitos; no modifica la rúbrica oficial.
Los despliegues cloud y sus evidencias siguen pendientes para acreditar todos los
requisitos del nivel excelente. La cuenta AWS ya está disponible; todavía no se
han aplicado los recursos de este laboratorio.
