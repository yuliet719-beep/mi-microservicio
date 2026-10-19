# Actividad 3.2 - Laboratorio Plan de Game Day

Entrega solicitada en la carpeta `Actividad 3.2 - Laboratorio Plan de Game Day`. Informe principal: **Plan_Game_Day.pdf** (5 páginas). Servicio objetivo: el FastAPI del laboratorio anterior, sin modificar `app/app.py`.

## Reproducción

Desde la raíz del repositorio, con Docker Desktop activo y Python 3.11+:

```powershell
docker compose -p actividad2-gameday -f "Actividad 3.2 - Laboratorio Plan de Game Day/compose.yaml" up --build -d
python "Actividad 3.2 - Laboratorio Plan de Game Day/ejecutar.py"
docker compose -p actividad2-gameday -f "Actividad 3.2 - Laboratorio Plan de Game Day/compose.yaml" down
```

Puertos locales: aplicación 18082, Prometheus 19092. El ensayo puede abortar antes de 60 segundos: diez fallos consecutivos activan la salida de la fase y el bloque `finally` elimina la disciplina de red. Existe un watchdog dentro del contenedor a los 60 s. El rollback manual es:

```powershell
docker compose -p actividad2-gameday -f "Actividad 3.2 - Laboratorio Plan de Game Day/compose.yaml" exec -T target tc qdisc del dev eth0 root
```

`ejecutar.py` genera evidencia real y sobrescribe los archivos principales de `evidencias`; guardar una copia antes de repetir. La imagen sandbox añade `iproute2` y `NET_ADMIN` exclusivamente para el namespace de red del contenedor. No representa la imagen distroless de producción. Se usa el código y dependencias originales, una réplica, 1 CPU y 256 MiB. No hay base de datos ni dependencia HTTP externa en el servicio original.

## Evidencias y alcance

- `plan_previo.json`: hipótesis, umbrales y parada definidos antes de ejecutar.
- `evidencias/resultados.json`: resumen calculado y commit base.
- `evidencias/solicitudes.csv`: cada solicitud, estado, duración y un identificador de span cliente.
- `evidencias/eventos.json`: comandos reales, UTC, salida y código de retorno; incluye instalación y retirada de `netem`.
- `evidencias/metrics_*.txt`: métricas originales de FastAPI en referencia y recuperación.
- `evidencias/prometheus_*.json`: estado de recolección por fase.
- `evidencias/servidor.log`: registros del proceso Uvicorn.
- `evidencias/prometheus_captura.jpg`: captura real del objetivo de Prometheus.
- `evidencias/resultados.png`: gráfico generado a partir del CSV, no captura de una herramienta.
- `evidencias/criterios_fuente.txt`: transcripción de la guía y de los criterios de calificación leídos en Moodle, sin información del usuario ni del estado de entrega.
- `evidencias/preensayo_abortado/`: diagnóstico inicial conservado; su CSV solo contiene la referencia porque el primer cliente no persistía las muestras al abortar. La ejecución final corrige esa limitación.

Los identificadores en CSV son spans del cliente de prueba, no trazas distribuidas OpenTelemetry. El servicio original no propaga ni registra esos IDs; no se afirma correlación servidor/cliente inexistente. E2 y E3 se diseñan en el informe, no se presentan como ejecutados. No se despliega Gremlin, Litmus ni Chaos Monkey: se explica su equivalencia conceptual.

## Correspondencia con la rúbrica (20 criterios, 5 puntos posibles)

Auditoría del 18/10/2026: se contrastaron tanto la **Guía de evaluación** como los **Criterios de calificación** de la actividad `id=306420`. Contienen los mismos 20 criterios, de 0,25 puntos cada uno. La tabla es una autoevaluación sustentada, no una calificación oficial.

| N.º | Criterio | Cobertura verificable |
|---|---|---|
| 1 | Servicio objetivo del laboratorio anterior identificado | Sí: PDF p. 1, `app/app.py`, repositorio y commit base `7d4e7f1913f2`. |
| 2 | Arquitectura, componentes y dependencias | Sí: PDF p. 1, capas de entrega/ejecución/observabilidad, dependencias y diferencias del sandbox. |
| 3 | Tres hipótesis en el formato exigido | Sí: H1, H2 y H3 en PDF p. 2 comienzan «En estado estable, cuando ... esperamos ...». |
| 4 | Comportamiento observable y medible | Sí: disponibilidad ≥99%, p95 <200 ms y recuperación acotada; PDF pp. 2-3. |
| 5 | Estado estable, fallo y resultado esperado | Sí: referencia común p. 1 y condiciones/resultados de cada hipótesis p. 2. |
| 6 | Tres experimentos alineados con las hipótesis | Sí: E1/H1, E2/H2 y E3/H3, tabla p. 2. Se distingue diseñado de ejecutado. |
| 7 | Tipo de fallo de cada experimento | Sí: latencia, agotamiento de CPU y error por caída de proceso, p. 2. |
| 8 | Radio de impacto de cada experimento | Sí: una réplica `target`; E1 solo su interfaz `eth0`; E2 cuota CPU; E3 solo ese servicio, p. 2. |
| 9 | Duración controlada y justificada | Sí: E1/E2 máximo 60 s, E3 20 s, referencia/recuperación de 30 s, p. 2. |
| 10 | Rollback automático para los tres | Sí: E1 watchdog + finally probado; E2 timeout y supervisor; E3 watchdog host y finally; PDF p. 2 y runbooks inferiores. |
| 11 | Métricas para validar cada hipótesis | Sí: matriz SLI y señales específicas de E1/E2/E3 en PDF p. 3. |
| 12 | SLI de impacto de cada experimento | Sí: disponibilidad, p95, error, throughput y recuperación; fórmulas y umbrales en PDF p. 3. |
| 13 | Logs, métricas y trazas definidos | Sí: CSV con spans cliente, Uvicorn, eventos de inyección, Prometheus y diseño de propagación de trazas; PDF p. 3. Se declara que no existen trazas distribuidas servidor en el servicio original. |
| 14 | Al menos un experimento ejecutado en local/sandbox | Sí: E1 real con `tc netem`, PDF p. 4; 336 peticiones, 36 durante fallo, 21 timeouts. |
| 15 | Procedimiento y herramientas documentados | Sí: PDF p. 4, instrucciones superiores, `ejecutar.py`, `compose.yaml` y comandos reales en `eventos.json`. |
| 16 | Evidencias de resultados | Sí: captura Prometheus, CSV, JSON, métricas, log servidor y gráfico calculado; carpeta `evidencias`. |
| 17 | Comparación esperado vs. obtenido | Sí: PDF p. 4, tabla por fase y rechazo explícito de H1: 41,67% de disponibilidad y p95 2038,1 ms durante fallo. |
| 18 | Debilidad sistémica identificada | Sí: PDF p. 5, única réplica, sensibilidad al camino de red y puntos ciegos del monitoreo interno. |
| 19 | Remediación viable | Sí: PDF p. 5, prioridades, responsables operativos y condiciones medibles para cerrar cada mejora. |
| 20 | Organización, redacción y extensión 4-5 páginas | Sí: PDF renderizado y revisado, exactamente 5 páginas; portada con los autores confirmados. |

La comprobación independiente recalculó recuentos, éxitos, disponibilidad y p95 desde `solicitudes.csv`; verificó `netem` aplicado, retirada con `noqueue`, referencia/recuperación al 100% y extensión de cinco páginas. Los registros originales mantienen las rutas históricas usadas durante el ensayo, aunque posteriormente se renombró la carpeta.

### Runbooks de recuperación para E2 y E3 (diseño)

Los siguientes mecanismos concretan los experimentos diseñados. No constituyen evidencia de ejecución de E2/E3; la rúbrica exige ejecutar al menos uno y E1 ya está ejecutado.

**E2:** preparar `stress-ng` desde el repositorio Debian en la imagen sandbox. El supervisor `timeout` de GNU coreutils debe existir antes de autorizar la inyección. Dentro de `target`, ejecutar `timeout --signal=TERM --kill-after=5s 60s stress-ng --cpu 2 --timeout 60s --metrics-brief`. El timeout propio detiene los trabajadores a los 60 s; el supervisor externo envía TERM y, si no termina, KILL cinco segundos después al grupo del ensayo. No se reinicia ni se mata Uvicorn. Verificar fin de los trabajadores y recuperación del SLI. La duración del fallo prevista es 60 s y el límite de contención de procesos es 65 s.

**E3:** el watchdog debe vivir en el host, pues el contenedor objetivo estará detenido. Este esquema Python usa la biblioteca estándar y el mismo `CMD` de `ejecutar.py`; se ejecuta desde una sesión dedicada después del preflight y con recolección paralela de solicitudes:

```python
# CMD = ['docker', 'compose', '-p', 'actividad2-gameday', '-f', ruta_compose]
import subprocess
import sys
import time

# Crear primero un proceso independiente que restablezca SOLO target.
watchdog_code = (
    'import subprocess,sys,time; time.sleep(20); '
    'subprocess.run(sys.argv[1:], check=True)'
)
watchdog = subprocess.Popen(
    [sys.executable, '-c', watchdog_code, *CMD, 'start', 'target'],
    stdin=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
)
try:
    # SIGKILL evita los segundos de gracia y hace inequívoco el inicio del fallo.
    subprocess.run([*CMD, 'kill', '-s', 'SIGKILL', 'target'], check=True)
    time.sleep(20)
finally:
    subprocess.run([*CMD, 'start', 'target'], check=True)
    watchdog.wait(timeout=30)
```

El proceso independiente sobrevive a una salida ordinaria del cliente; `finally` da una segunda vía de restauración. Ambos `start` son idempotentes. El límite de 20 s se cuenta desde el armado del watchdog; registrar el instante real de `kill` para medir la exposición efectiva. Una caída total del host/Docker queda fuera del alcance de este mecanismo. Verificar después `/health`, `/hello` y `up`; si no se recuperan dentro de 30 s, detener el programa de experimentos y diagnosticar.

Autores confirmados: **Manuel Fernando Santofimio Tovar y Beycy Yuliet Rojas**. La consigna indica trabajo grupal de tres integrantes; se incluyen los dos nombres proporcionados, sin inventar un tercero. El informe define los tres roles operativos del Game Day. La calificación corresponde al docente.

## Fuentes

- Consigna y rúbrica: https://unisabanae-learning.unisabana.edu.co/mod/assign/view.php?id=306420
- Principios: https://principlesofchaos.org/
- Manual de netem: https://man7.org/linux/man-pages/man8/tc-netem.8.html
- Histogramas: https://prometheus.io/docs/practices/histograms/
