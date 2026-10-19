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
- `evidencias/preensayo_abortado/`: diagnóstico inicial conservado; su CSV solo contiene la referencia porque el primer cliente no persistía las muestras al abortar. La ejecución final corrige esa limitación.

Los identificadores en CSV son spans del cliente de prueba, no trazas distribuidas OpenTelemetry. El servicio original no propaga ni registra esos IDs; no se afirma correlación servidor/cliente inexistente. E2 y E3 se diseñan en el informe, no se presentan como ejecutados. No se despliega Gremlin, Litmus ni Chaos Monkey: se explica su equivalencia conceptual.

## Correspondencia con la rúbrica (20 criterios, 5 puntos posibles)

| Criterios | Ubicación en el PDF |
|---|---|
| 1-2 Servicio objetivo, arquitectura, componentes y dependencias | Página 1 |
| 3-5 Tres hipótesis con estado estable, fallo y resultado medible | Página 2 |
| 6-10 Tres experimentos alineados, tipo, radio, duración y rollback | Página 2 |
| 11-13 Métricas, SLI, logs y trazas | Página 3 |
| 14-16 Ejecución local, herramientas y evidencias reales | Página 4 y evidencias |
| 17-19 Esperado vs. real, debilidad y remediación | Páginas 4-5 |
| 20 Organización y extensión 4-5 páginas | PDF de 5 páginas |

Autores confirmados: **Manuel Fernando Santofimio Tovar y Beycy Yuliet Rojas**. La consigna indica trabajo grupal de tres integrantes; se incluyen los dos nombres proporcionados, sin inventar un tercero. El informe define los tres roles operativos del Game Day. La calificación corresponde al docente.

## Fuentes

- Consigna y rúbrica: https://unisabanae-learning.unisabana.edu.co/mod/assign/view.php?id=306420
- Principios: https://principlesofchaos.org/
- Manual de netem: https://man7.org/linux/man-pages/man8/tc-netem.8.html
- Histogramas: https://prometheus.io/docs/practices/histograms/
