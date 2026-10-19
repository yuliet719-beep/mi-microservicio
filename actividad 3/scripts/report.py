"""Ten-page executive report, generated exclusively from measured artifacts."""
from pathlib import Path
import csv
import json
import math
import os
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing, Rect, String, Line
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidencias'
R = json.loads((E / 'results.json').read_text(encoding='utf-8'))
V = json.loads((E / 'verification.json').read_text())
A = json.loads((E / 'aiops-state.json').read_text())
S = json.loads((E / 'security-scan.json').read_text())
vulns = sorted({v['id'] for d in S['dependencies'] for v in d['vulns']})
rows = list(csv.DictReader((E / 'requests.csv').open(encoding='utf-8')))
for name, filename in [('Arial', 'arial.ttf'), ('Arial-Bold', 'arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts') / filename)))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold')
navy, teal = colors.HexColor('#15334B'), colors.HexColor('#007C83')
body = ParagraphStyle('body', fontName='Arial', fontSize=10.5, leading=15, spaceAfter=10, textColor=navy)
h1 = ParagraphStyle('h1', parent=body, fontName='Arial-Bold', fontSize=21, leading=26, spaceAfter=18)
h2 = ParagraphStyle('h2', parent=body, fontName='Arial-Bold', fontSize=12, leading=17, textColor=teal, spaceBefore=8)
small = ParagraphStyle('small', parent=body, fontSize=8, leading=11, spaceAfter=6)
story = []


def p(text, style=body):
    story.append(Paragraph(text, style))


def title(number, text):
    if number > 1:
        story.append(PageBreak())
    p(f'ACTIVIDAD 3.3 / {number:02d}', small)
    p(text, h1)


def table(headers, data, widths):
    cells = [[Paragraph(escape(str(x)), small) for x in row] for row in [headers] + data]
    t = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#DCEEF0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 7), ('LINEBELOW', (0,0), (-1,0), 1, teal),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F2F5F8')])]))
    story.append(t); story.append(Spacer(1, 10))


def image(path, maxh=235):
    if path.exists():
        from PIL import Image as PI
        w,h = PI.open(path).size
        scale = min(468/w, maxh/h)
        story.append(Image(str(path), width=w*scale, height=h*scale))
        story.append(Spacer(1,10))


# Generate a scientific plot from actual client requests.
fig, axes = plt.subplots(2, 1, figsize=(9, 4), sharex=True, constrained_layout=True)
start = float(rows[0]['epoch'])
palette = {'baseline':'#197E82','noise':'#967149','noise_recovery':'#A7B9C7','latency':'#DB7D26',
           'latency_recovery':'#A7B9C7','errors':'#BB3C54','recovery':'#218A60'}
for phase in R['phases']:
    rr = [r for r in rows if r['phase'] == phase]
    xs = [float(r['epoch'])-start for r in rr]
    axes[0].scatter(xs, [float(r['duration_s'])*1000 for r in rr], s=6, label=phase, c=palette[phase], alpha=.7)
    axes[1].scatter(xs, [int(r['status']) for r in rr], s=6, c=palette[phase], alpha=.7)
axes[0].axhline(200, color='black', linestyle='--', linewidth=.8)
axes[0].set_ylabel('Latencia (ms)'); axes[1].set_ylabel('HTTP status'); axes[1].set_xlabel('Segundos desde el inicio')
axes[0].legend(ncol=4, fontsize=7, loc='upper left')
fig.savefig(E / 'experimental-results.png', dpi=170); plt.close(fig)

title(1, 'Sistema de observabilidad\nend-to-end')
p('Laboratorio integrador con AIOps, observabilidad de red y resiliencia', h2)
p('Maestría en Arquitectura de Software<br/>Observabilidad en Ambientes Productivos<br/>Universidad de La Sabana<br/>18 de octubre de 2026')
p('<b>Resumen ejecutivo.</b> Se construyó y ejecutó un sandbox aislado con tres microservicios FastAPI, una base PostgreSQL, instrumentación OpenTelemetry de métricas, logs y trazas, proxies Envoy y detección automática correlacionada. Se conservaron los registros crudos para auditar cada resultado.')
table(['Resultado medido', 'Valor'], [
    ['Alerta por 200 ms en service-b', f"{R['mttd_s']['latency']:.2f} s"],
    ['Alerta por errores en data-service', f"{R['mttd_s']['errors']:.2f} s"],
    ['Comprobaciones de evidencias', f'{sum(V.values())}/{len(V)} satisfactorias'],
    ['Entorno efectivamente ejecutado', 'Docker local; cloud.provider=local'],
    ['Despliegue en AWS y GCP', 'Pendiente; no se dispone de cuenta AWS']
], [300,168])
p('<b>Conclusión de alcance.</b> La entrega demuestra el núcleo local y los dos experimentos, pero no acredita el 100% de los requisitos. Cloud SQL, RDS, service mesh gestionado, AIOps nativo, VPC Flow Logs y SCC/Security Hub requieren despliegue y evidencia cloud. La infraestructura adjunta fue validada, no aplicada. No se solicita asignar una nota automática.')
p('La modalidad del enunciado es grupal de tres integrantes. No se recibieron los nombres del equipo; deben incorporarse en la sustentación. El repositorio y los artefactos permiten reproducir el trabajo sin atribuir intervenciones personales no verificadas.', small)

title(2, 'Arquitectura y límites del sistema')
p('La petición externa entra por service-a, continúa por Envoy hacia service-b y luego por un segundo Envoy hacia data-service. Este último consulta una tabla real de PostgreSQL. El contexto W3C viaja por HTTP; la aplicación propaga el trace_id en la respuesta para facilitar la investigación.')
d = Drawing(468,155)
for x,y,label,w in [(5,100,'service-a',100),(165,100,'service-b',100),(330,100,'data-service',130),
                    (330,30,'PostgreSQL',130),(165,30,'OTel Collector',130),(5,30,'Grafana / LGTM',140)]:
    d.add(Rect(x,y,w,36,rx=5,fillColor=colors.HexColor('#DCEEF0'),strokeColor=teal))
    d.add(String(x+w/2,y+14,label,textAnchor='middle',fontName='Arial',fontSize=10))
for x1,y1,x2,y2 in [(105,118,165,118),(265,118,330,118),(395,100,395,66),(165,48,145,48)]:
    d.add(Line(x1,y1,x2,y2,strokeColor=navy))
d.add(String(120,132,'Envoy',fontName='Arial',fontSize=8));d.add(String(280,132,'Envoy',fontName='Arial',fontSize=8))
story.append(d)
table(['Capa', 'Implementación y contrato'], [
    ['Aplicación', 'Tres contenedores del mismo código, rol por SERVICE_NAME; /work y /health.'],
    ['Datos', 'PostgreSQL 16; tabla inventory con PK y restricción quantity >= 0.'],
    ['Telemetría', 'SDK OTel -> OTLP HTTP -> Collector -> Prometheus, Tempo y Loki.'],
    ['Red', 'Dos proxies Envoy con métricas L7 y access logs; red Docker dedicada.'],
    ['Operación', 'Detector continuo, reglas Prometheus, Grafana y controles de fallos con TTL.']
], [90,378])
p('<b>Aislamiento.</b> Todos los puertos publicados se limitan a 127.0.0.1. La base no tiene puerto público. Los servicios de aplicación usan usuario sin privilegios, filesystem de solo lectura, capacidades retiradas y límites de CPU/memoria. Las credenciales aleatorias se generan en .env ignorado por Git.')
p('<b>Frontera cloud.</b> El diseño de destino mantiene la cadena y sustituye PostgreSQL local por Cloud SQL o RDS privado. No se representa un segundo proveedor mediante una simple etiqueta local. Envoy local no demuestra mTLS, un control plane ni una malla gestionada.', small)

title(3, 'Tres pilares y correlación verificable')
p('La instrumentación automática de FastAPI y HTTPX produce spans de servidor y cliente; psycopg2 instrumenta el acceso real a la base. El span SELECT inventory agrega convenciones actuales de base de datos sin registrar contraseñas ni valores de negocio. Los atributos db.system.name, db.namespace y db.operation.name permiten filtrar consultas.')
table(['Pilar', 'Prueba conservada', 'Uso operacional'], [
    ['Trazas', 'trace-success.json y trace-failed.json', 'Camino A/B/data; error y consulta SQL.'],
    ['Métricas', 'metrics.json, targets.json', 'Solicitudes, códigos HTTP, duración por servicio.'],
    ['Logs', 'logs.json y logs del Collector', 'Eventos estructurados con service y trace_id.'],
    ['Red L7', 'network-metrics.json y mesh-*.log', 'Ruta, upstream, código, tiempo y traceparent.']
], [70,180,218])
p('<b>Cadena de evidencia.</b> verify.py comprueba que una misma traza exitosa contenga los tres servicios y PostgreSQL, que Loki haya persistido logs correlacionables y que existan métricas de los tres servicios. No basta con mostrar el SDK instalado o un panel vacío.')
p('<b>Precisión del p99.</b> El histograma usa límites explícitos de 5, 10, 25, 50, 100, 150, 200, 250, 300, 500, 1000, 2000 y 5000 ms. Esto evita que buckets genéricos produzcan una interpolación inútil para un SLO de 200 ms. El p99 del cliente se obtiene de las solicitudes CSV; el de Prometheus sigue siendo una aproximación por buckets.')
p('<b>DataOps.</b> data-quality.txt registra cantidad de filas y filas inválidas sobre la base real. El esquema se crea de manera reproducible con init.sql y no se modifica durante caos. No existe todavía monitorización de frescura, linaje ni calidad histórica; se incluye en el roadmap.')
p('Retención local: traces 24 h; datos del ensayo quedan exportados en Git. La retención cloud, el control de cardinalidad y el muestreo de producción necesitan decisiones adicionales. Se evitan trace_id como etiquetas Prometheus para no multiplicar series.', small)

title(4, 'AIOps: baseline, correlación y ruido')
b=A['baseline']; n=R['noise_comparison']
p(f"El detector aprende {b['windows']} ventanas iniciales de {b['samples_per_window']} probes cada una. Congela la media ({b['mean']:.4f}) y la desviación poblacional ({b['sigma']:.4f}) de la tasa de errores; el umbral resultante es {b['threshold']:.4f}. La espera de arranque separa la disponibilidad inicial del baseline operacional.")
p('<b>Regla exigida.</b> error_rate &gt; media_baseline + 2 × sigma <b>Y</b> p99 &gt; 0.2 segundos. La alerta enriquecida incluye data-service, tasa, p99, umbral, trace_id fallido, acción sugerida y runbook. Prometheus evalúa aiops_correlated_anomaly cada 2 s y requiere 2 s de permanencia.')
table(['Control de ruido medido', 'Resultado'], [
    ['Ventanas independientes evaluadas', n['windows']], ['Ventanas con alerta estática (algún 5xx)', n['static']],
    ['Ventanas con ambas señales', n['correlated']], ['Reducción de ventanas alertadas', f"{(n['reduction'] or 0)*100:.1f}%"]
], [330,138])
image(E/'03-alerta-correlacionada.jpg',180)
p('La comparación aplica a la carga de errores rápidos de este ensayo; no es una estimación general de falsos positivos. No se dispone de un conjunto etiquetado para medir precisión/recall. Una regla AND suprime errores sin latencia y también puede ocultar incidentes reales de ese tipo; se recomienda mantener una alerta separada por disponibilidad.', small)
p('Esta es detección estadística local, no un modelo predictivo ni una implementación de DevOps Guru/Cloud Monitoring Anomaly Detection. La configuración nativa y su evidencia siguen pendientes.', small)

title(5, 'Observabilidad de red y seguridad')
p('Envoy aporta visibilidad Este-Oeste de las dos dependencias HTTP: código, duración, destino upstream y contexto traceparent. Prometheus recoge las métricas de ambos proxies. Las solicitudes de entrada a service-a permiten observar el frente Norte-Sur local; la red de proveedor no está instrumentada en este ensayo.')
table(['Golden Signal / control', 'Estado y evidencia'], [
    ['Autenticación fallida', 'Ráfaga validada de 10 respuestas 401; 20 intentos totales. AuthFailures y security-validation.json.'],
    ['Tráfico E-W', 'Métricas Envoy y access logs; alerta por tasa >100 req/s durante 10 s.'],
    ['Tráfico N-S', 'Solicitudes y métricas del servicio de entrada; sin VPC Flow Logs cloud.'],
    ['Vulnerabilidades conocidas', f'{len(vulns)} IDs únicos en Starlette; security-scan.json. No es un escaneo de imagen.'],
    ['Control de caos', 'Token de operador y validación de rango; prueba de acceso sin token rechazada.'],
    ['Seguridad cloud', 'Terraform declara Security Hub básico; SCC requiere configuración posterior.']
], [140,328])
p('<b>Análisis de riesgo.</b> Los hallazgos en dependencias no se ocultan ni se convierten en un cero por ausencia de integración. Deben actualizarse FastAPI/Starlette con versiones compatibles de OTel y volver a ejecutar todo el ensayo. El dashboard muestra una instantánea del escaneo, no un feed continuo de CVEs.')
p('<b>Brecha explícita.</b> VPC Flow Logs GCP/AWS, SCC/Security Hub operativo, reglas sobre flujos cloud y hallazgos centralizados no fueron ejecutados. Las reglas L7 no reemplazan esos requisitos. La IaC valida estructura de proveedor, no permisos, capacidad disponible ni ejecución de recursos.')
p('Actualización tecnológica: AWS documenta el fin de soporte de App Mesh el 30 de septiembre de 2026. Se propone acordar con la docente Istio/Envoy o ECS Service Connect como sustituto, conservando las métricas L7. La sustitución no se presume aprobada.', small)

title(6, 'Experimento 1: latencia en service-b')
q=R['phases']['latency']
p('<b>Hipótesis.</b> Al añadir 200 ms a service-b, el p99 supera el SLO y ServiceBLatency entra en firing en menos de dos minutos, conservando visibilidad de toda la cadena. Los errores no son necesarios para esta alerta de latencia.')
table(['Medición', 'Valor'], [['Latencia inyectada', '200 ms por petición al servicio B'],
    ['MTTD observado', f"{R['mttd_s']['latency']:.3f} s"], ['Solicitudes medidas', q['requests']],
    ['p99 extremo a extremo', f"{q['p99_s']*1000:.2f} ms"], ['Tasa de errores', f"{q['error_rate']*100:.2f}%"],
    ['SLI compuesto de la fase', f"{q['sli']*100:.2f}%"]], [300,168])
image(E/'experimental-results.png',235)
p('El cliente guarda cada petición y consulta el estado real de la alerta; la medición incorpora exportación, scrape, evaluación y observación. El registro events.json contiene inicio, firing y rollback. El TTL de 90 s y el bloque finally limitan la duración del fallo si el operador pierde el control.', small)
p('Resultado: la degradación se detectó dentro del objetivo de 120 s. Los resultados se limitan a una ejecución en este sandbox; la capacidad, el jitter y la configuración cloud pueden cambiar el tiempo de detección.', small)

title(7, 'Experimento 2: errores en data-service')
q=R['phases']['errors']
p('<b>Hipótesis.</b> Una probabilidad Bernoulli de fallo del 10% en data-service, con 250 ms en las peticiones fallidas, activa simultáneamente la tasa de error anómala y p99 fuera de SLO. Esto permite probar exactamente la regla de correlación solicitada.')
table(['Medición', 'Valor'], [['Probabilidad configurada', '10%; semilla 7341 por proceso'],
    ['MTTD observado', f"{R['mttd_s']['errors']:.3f} s"], ['Solicitudes / errores medidos', f"{q['requests']} / {q['errors']}"],
    ['Tasa de error observada', f"{q['error_rate']*100:.2f}%"], ['p99 extremo a extremo', f"{q['p99_s']*1000:.2f} ms"],
    ['Recuperación: errores', R['phases']['recovery']['errors']]], [300,168])
alert = next((x for x in A['alerts'] if x['trace_id']), {})
p('Ejemplo de alerta enriquecida conservada:', h2)
p(f"Servicio: data-service<br/>trace_id: {alert.get('trace_id','sin trace')}<br/>error_rate: {alert.get('error_rate',0):.4f}<br/>p99: {alert.get('p99_s',0):.4f} s<br/>Acción: revertir fallo y revisar span de dependencia/consulta SQL.")
p('La tasa observada puede diferir del 10% por el tamaño de muestra y porque el detector genera probes adicionales. El CSV documenta el tráfico cliente; las ventanas AIOps documentan sus probes. Son poblaciones relacionadas, pero no deben mezclarse para recalcular porcentajes.')
p('<b>Recuperación verificada.</b> Se retira el fallo y se ejecutan 30 s de tráfico de extremo a extremo. verify.py comprueba ausencia de errores en esa fase y preserva una traza exitosa con PostgreSQL. La alerta de latencia de service-b puede activarse también durante errores lentos aguas abajo; esa propagación es esperada y no implica una nueva inyección en B.')
p('Accionabilidad: el servicio responsable, trace_id y runbook reducen la búsqueda manual. No hay notificación externa ni automatización de remediación cloud; firing es el estado del motor de alertas, no una confirmación de recepción por un humano.', small)

title(8, 'SLO, error budget e interpretación')
p('Se define un SLO experimental del 99%: una solicitud buena responde sin 5xx/errores de conexión y tarda como máximo 200 ms. SLI = buenas/N. Presupuesto = 1% de N. Consumo de presupuesto = malas/(0.01 × N). Se reporta por fase, sin extrapolar a un mes de operación.')
table(['Fase', 'N', 'SLI', 'p99 ms', 'Consumo budget'], [
    [name, q['requests'], f"{q['sli']*100:.1f}%", f"{q['p99_s']*1000:.1f}", f"{q['budget_consumed_multiple']:.1f}x"]
    for name,q in R['phases'].items()], [120,55,75,90,128])
p('¿Se degradó el SLO? Se responde comparando cada SLI medido con el 99% objetivo. La latencia deliberada puede consumir el presupuesto aunque las respuestas sean exitosas. El ensayo de errores consume presupuesto por disponibilidad y por tiempo; una misma solicitud mala se contabiliza una sola vez.')
p('¿Se consumió el error budget? El múltiplo de la tabla muestra la relación con el presupuesto de esa fase. Un valor mayor que 1 significa agotamiento. En una ventana corta el presupuesto puede ser fraccionario; por eso se utiliza una razón y no se redondea el número permitido de fallos a un entero.')
p('¿La alerta fue accionable? Sí en el alcance local: el motor detectó la condición, conservó trace_id y permitió revertir el estímulo. La prueba no demuestra disponibilidad mensual, MTTR de un equipo real, resiliencia multirregión ni tolerancia a pérdida de la base gestionada.')
p('Limitaciones: una repetición por fallo, baseline breve, p99 de ventanas pequeñas, carga local y detector de probes. El objetivo <120 s se verifica para cada observación; no se afirma una media estadística de MTTD. Para producción se requieren repeticiones, intervalos de confianza y presupuesto de 28/30 días.', small)

title(9, 'Madurez en ocho dominios')
p('Autoevaluación operacional de ocho dominios alineados con los temas del enunciado. La actividad no adjunta una taxonomía detallada del Blueprint; esta correspondencia se declara explícitamente. Escala: 1 inicial, 2 repetible local, 3 gestionado con SLO, 4 cuantificado en producción y 5 optimización continua. La puntuación no es calificación docente.')
domains = [
    ['Métricas y SRE',2,'SLI y presupuesto calculados; sin ventana productiva.'],
    ['Logging',2,'OTLP/Loki correlacionado; falta gobierno y retención cloud.'],
    ['Tracing y OTel',2,'Tres servicios y DB; falta prueba multicloud y sampling.'],
    ['AIOps',2,'Baseline y AND medidos; falta proveedor nativo y evaluación etiquetada.'],
    ['Network Observability',2,'Envoy L7; sin flujos VPC ni mTLS gestionado.'],
    ['Security Observability',2,'401, alerta y escaneo; hallazgos pendientes, sin SCC/Hub activo.'],
    ['DataOps',2,'Esquema y calidad básica; sin frescura ni linaje continuo.'],
    ['Resiliencia y operación',2,'Dos fallos y rollback reproducibles; sin ejercicio grupal cloud.']]
table(['Dominio', 'Nivel', 'Justificación y brecha'], domains, [120,40,308])
p('<b>Lectura de la madurez.</b> El promedio es 2.0/5 en esta escala. Tener código y herramientas no equivale a capacidad productiva gestionada. Ningún dominio recibe un nivel superior por infraestructura aún no aplicada. La prioridad es cerrar las dependencias cloud y de seguridad antes de sofisticar el detector.')
p('La evidencia es auditable: verification.json, resultados, logs, trazas y tablas conservan el estado observado. Los artefactos crudos permiten refutar o reproducir las conclusiones; las capturas complementan esa evidencia, pero no sustituyen los datos.', small)

title(10, 'Roadmap, reproducción y referencias')
table(['Plazo / responsable', 'Entrega medible para alcanzar nivel 3'], [
    ['Mes 1 / plataforma', 'Cuentas sandbox y presupuesto; aplicar IaC; Cloud SQL/RDS privados; OTel en ambas clouds; evidencias verificadas.'],
    ['Mes 2 / observabilidad y seguridad', 'Resolver hallazgos; malla compatible acordada; Flow Logs, SCC/Hub y alertas nativas; dataset etiquetado de incidentes.'],
    ['Mes 3 / SRE y datos', 'SLO 30 días y burn rate; 5 repeticiones por caos; medir precisión/recall, MTTD y MTTR; frescura/linaje; sustentación grupal.']
], [120,348])
p('<b>Reproducción.</b> En la carpeta actividad 3: generar .env con scripts/init_env.py; iniciar docker compose up -d --build; esperar baseline; ejecutar scripts/experiment.py y scripts/verify.py. Consultar README.md y docs/RUNBOOK.md. Los secretos no forman parte de Git. CLOUD_HANDOFF.md describe las brechas de despliegue. Video_Demostracion_Local.mp4 registra una captura real de navegador, sin audio, y no una sustentación multicloud.', small)
p('<b>Referencias técnicas oficiales y fuente de evaluación</b>', h2)
refs = [
    ('Universidad de La Sabana. Actividad 3.3 y rúbrica (consulta autenticada, 18/10/2026).', 'https://unisabanae-learning.unisabana.edu.co/mod/assign/view.php?id=306421'),
    ('OpenTelemetry. Collector configuration.', 'https://opentelemetry.io/docs/collector/configuration/'),
    ('OpenTelemetry. Semantic conventions for SQL.', 'https://opentelemetry.io/docs/specs/semconv/db/sql/'),
    ('Grafana. Ingesting logs using OTLP.', 'https://grafana.com/docs/loki/latest/send-data/otel/'),
    ('AWS. App Mesh: aviso de fin de soporte.', 'https://docs.aws.amazon.com/app-mesh/latest/userguide/'),
    ('AWS. Amazon DevOps Guru.', 'https://docs.aws.amazon.com/devops-guru/latest/userguide/welcome.html'),
    ('Google Cloud. VPC Flow Logs.', 'https://cloud.google.com/vpc/docs/flow-logs'),
    ('Google Cloud. Security Command Center.', 'https://cloud.google.com/security-command-center/docs/concepts-security-command-center-overview')]
for label,url in refs:
    p(f'{escape(label)}<br/><link href="{url}" color="#007C83">{escape(url)}</link>', small)


def footer(canvas, doc):
    canvas.setStrokeColor(teal); canvas.line(54,43,558,43)
    canvas.setFont('Arial',8); canvas.setFillColor(navy)
    canvas.drawString(54,30,'Actividad 3.3 | Evidencias de sandbox local | 18/10/2026')
    canvas.drawRightString(558,30,f'{doc.page} / 10')


dest=ROOT/'Reporte_Ejecutivo_Actividad_3.pdf'
SimpleDocTemplate(str(dest), pagesize=letter, rightMargin=72, leftMargin=72,
                  topMargin=48,bottomMargin=58, title='Actividad 3.3 - Observabilidad end-to-end',
                  author='Entrega académica - equipo por identificar').build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(dest)
assert len(doc)==10, f'Expected ten pages; got {len(doc)}'
tmp=ROOT/'tmp/pdf-preview';tmp.mkdir(parents=True,exist_ok=True)
for i,page in enumerate(doc):
    page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(tmp/f'page-{i+1:02d}.png')
print(f'Report generated and rendered: {len(doc)} pages')
