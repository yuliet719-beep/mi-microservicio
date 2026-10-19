# Runbook de incidentes y Game Day

## Alcance y condiciones de entrada

Únicamente el proyecto Docker `actividad3-observabilidad`, red `actividad3-sandbox`.
No ejecutar contra otros contenedores, recursos compartidos ni producción.
Mantener 3 servicios sanos, base inicializada, 12 ventanas de baseline y tres pilares
exportando. Antes de cada ensayo: confirmar `/health`, objetivos Prometheus UP,
una traza completa con consulta SQL y baseline no contaminado por errores de arranque.

## Hipótesis y observación

| Ensayo | Estímulo | Señal esperada | Detección |
|---|---|---|---|
| 1 | 200 ms adicionales en service-b | p99 > 200 ms, sin errores por diseño | ServiceBLatency firing <120 s |
| 2 | Probabilidad de error 10% en data-service; petición fallida espera 250 ms | 5xx y p99 >200 ms | CorrelatedDataServiceAnomaly firing <120 s |
| Control de ruido | Probabilidad de error 10%, sin espera adicional | alarmas estáticas sin degradación de p99 | menos ventanas correlacionadas |

El segundo ensayo incluye espera en las peticiones fallidas para satisfacer la regla
AND exigida. Una tasa de error del 10% por sí sola puede dejar p99 sano; no debe
afirmarse que una regla AND detecta cualquier incremento de errores.
El 10% es una probabilidad Bernoulli reproducible, no una cuota exacta por muestra.

## Procedimiento automático

Ejecutar `python scripts/experiment.py`; genera tráfico concurrente contra service-a,
consulta las alertas reales de Prometheus y guarda el instante de la primera alerta
en estado firing. MTTD = primera observación firing - aceptación del fallo (el registro
se toma inmediatamente antes del POST, por lo que incluye su costo de control).
Incluye espera de exportación, scraping y regla. Es una cota observacional con polling,
no el timestamp interno preciso del detector. Se miden dos tiempos individuales;
con una repetición no se puede estimar una media poblacional de MTTD.

## Respuesta

1. Leer `http://127.0.0.1:18083/alerts`; identificar servicio, tasa, baseline, p99 y trace_id.
2. Buscar el trace_id en Tempo/Grafana, revisar el error del data-service y el span DB.
3. Si el ensayo está dentro de ventana, confirmar hipótesis. Si el impacto excede el
   límite, revertir de inmediato: POST `/control` con `latency_ms:0,error_rate:0`
   y cabecera `x-control-token` desde el entorno local ignorado.
4. Confirmar recuperación con tráfico completo A -> B -> data -> PostgreSQL y alertas resueltas.
5. Guardar CSV, eventos, JSON de alertas y capturas; nunca token ni DSN con contraseña.

## Límites y rollback

TTL máximo admitido: 120 s; el ensayo usa 90 s y revierte explícitamente al finalizar.
Latencia máxima validada por esquema: 2000 ms; error rate máximo 50%. Estos son
límites técnicos, no autorización para utilizarlos todos. El plan usa 200 ms y 10%.
El `finally` revierte los dos fallos si se interrumpe el cliente. Si el cliente muere
sin ejecutar finally, el TTL en el servicio desactiva el fallo. Reiniciar el servicio
también borra el estado de inyección que reside en memoria.
Abortar si hay fallos fuera del servicio objetivo, caída de la base, pérdida de la
telemetría o si un fallo supera 90 s. No inferir recuperación solo de `/health`.

## SLI y error budget

Solicitud buena = respuesta <500, distinta de error de conexión, y duración <=200 ms.
SLI = buenas/N; objetivo del ensayo = 99%. Presupuesto = 0.01*N solicitudes.
Consumo = malas/(0.01*N), expresado como múltiplo del presupuesto de la fase.
No extrapolar el consumo de un ensayo breve al presupuesto mensual sin conocer
el tráfico y la ventana de producción. Los resultados de cada fase están en results.json.

## Responsabilidades para sustentación grupal

Asignar antes de presentar tres roles: operador del sandbox, observador de telemetría
y responsable de abortar/documentar. Los nombres no fueron suministrados; no se
atribuyen participaciones inventadas. El video local no sustituye una sustentación
en vivo con el equipo ni la demostración cloud pendiente.
