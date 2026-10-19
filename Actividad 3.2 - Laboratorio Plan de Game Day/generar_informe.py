"""Genera cinco paginas APA 7 a partir de las evidencias originales."""
from pathlib import Path
import csv
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pymupdf
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image

ROOT=Path(__file__).resolve().parent
E=ROOT/'evidencias'
R=json.loads((E/'resultados.json').read_text(encoding='utf-8'))
rows=list(csv.DictReader((E/'solicitudes.csv').open(encoding='utf-8')))
fontdir=Path(os.environ.get('APA_FONT_DIR','C:/Windows/Fonts'))
for name, file in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf'),('Arial-Italic','ariali.ttf'),('Arial-BoldItalic','arialbi.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial-Italic',boldItalic='Arial-BoldItalic')
fig,ax=plt.subplots(figsize=(9,2.05))
for phase,label,marker,tone in [('baseline','Referencia','o','#008577'),('fault','Fallo','x','#d85c32'),('recovery','Recuperación','+','#315fba')]:
    d=[r for r in rows if r['phase']==phase]
    ax.scatter([float(r['elapsed_s']) for r in d],[float(r['duration_ms']) for r in d],s=12,label=label,marker=marker,color=tone)
ax.axhline(200,color='black',linestyle='--',linewidth=.7,label='Umbral: 200 ms')
ax.set(xlabel='Tiempo desde el inicio (s)',ylabel='Latencia cliente (ms)')
ax.tick_params(labelsize=9)
ax.legend(fontsize=9,ncol=4,loc='upper right')
ax.grid(alpha=.15)
fig.tight_layout(pad=.6)
fig.savefig(E/'resultados.png',dpi=220)
plt.close(fig)

W=468
base=dict(fontName='Arial',fontSize=11,leading=22,textColor=colors.black,spaceAfter=0,spaceBefore=0)
body=ParagraphStyle('Body',**base,firstLineIndent=36)
plain=ParagraphStyle('Plain',**base)
center=ParagraphStyle('Center',**base,alignment=TA_CENTER)
head=ParagraphStyle('Head',**{**base,'fontName':'Arial-Bold'},alignment=TA_CENTER,keepWithNext=True)
subhead=ParagraphStyle('Subhead',**{**base,'fontName':'Arial-Bold'},keepWithNext=True)
cell=ParagraphStyle('Cell',**{**base,'leading':12.5})
ref=ParagraphStyle('Reference',**base,leftIndent=36,firstLineIndent=-36)
story=[]
def p(t): story.append(Paragraph(t,body))
def text(t): story.append(Paragraph(t,plain))
def h(t): story.append(Paragraph(t,head))
def h2(t): story.append(Paragraph(t,subhead))
def label(n,t,kind='Tabla'):
    text(f'<b>{kind} {n}</b>')
    text(f'<i>{t}</i>')
def table(data,widths):
    t=Table([[Paragraph(str(v),cell) for v in row] for row in data],colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEABOVE',(0,0),(-1,0),.8,colors.black),('LINEBELOW',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,-1),(-1,-1),.8,colors.black),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    story.append(t)
def page(): story.append(PageBreak())

story.append(Spacer(1,66))
h('Plan de Game Day para evaluar la resiliencia de mi-microservicio')
story.append(Spacer(1,22))
for line in ['Manuel Fernando Santofimio Tovar y Beycy Yuliet Rojas','Maestría en Arquitectura de Software, Universidad de La Sabana']:
    story.append(Paragraph(line,center))
page()
h('Plan de Game Day para evaluar la resiliencia de mi-microservicio')
p('Se diseña un ensayo controlado para refutar hipótesis del estado estable y convertir debilidades en mejoras verificables (Principles of Chaos Engineering, 2019). La actividad exige tres diseños y una ejecución real (Universidad de La Sabana, 2026).')
h2('Arquitectura y estado estable')
p(f'El objetivo es FastAPI en app/app.py del laboratorio anterior (yuliet719-beep, s. f.; commit {R["source_commit"][:12]}). Expone /hello, /health y /metrics; depende de Python, Uvicorn e instrumentación Prometheus. No utiliza base de datos ni HTTP externo. GitHub Actions, Jenkins, Docker, Helm, Argo CD y Kubernetes integran la entrega; no se perturban.')
p('El cliente accede a target:8000 por 127.0.0.1:18082; Prometheus consulta /metrics cada 2 s. Se conserva el código, pero la imagen distroless se sustituye por python:3.11-slim con iproute2: una réplica, 1 CPU, 256 MiB y NET_ADMIN solo en su red. El estado estable exige 5 solicitudes/s, disponibilidad ≥99% y p95 &lt;200 ms, timeout de 2 s, sin reintentos y referencia de 30 s.')
p('El director controla inicio/parada; el operador inyecta/revierte; el observador registra SLI. Antes del fallo se verifica salud, UP y referencia válida; se aborta ante diez fallos consecutivos. La Tabla 1 presenta hipótesis previas cuya refutación es válida.')
label(1,'Hipótesis medibles de conservación del estado estable')
table([['<b>ID</b>','<b>Hipótesis</b>'],['H1','En estado estable, cuando se añaden 300 ms de latencia de salida a target hasta 60 s, esperamos disponibilidad ≥99%, p95 &lt;200 ms y retorno a ese umbral en 30 s tras el rollback.'],['H2','En estado estable, cuando un proceso consume la cuota de una CPU durante 60 s, esperamos disponibilidad ≥99%, p95 &lt;200 ms y recuperación a ambos umbrales en 30 s.'],['H3','En estado estable, cuando se pierde la única réplica durante 20 s, esperamos disponibilidad ≥99% durante el fallo y retorno de respuestas 2xx en ≤30 s desde su restauración.']],[36,W-36])
page()
h('Diseño experimental y observabilidad')
p('Cada fallo se limita a target, sin red del host ni producción. La Tabla 2 alinea los diseños con H1-H3. E1 usa netem, que altera paquetes fuera del handler (Ludovici &amp; Pfeifer, 2011). Los 60 s permiten hasta 300 solicitudes y 30 scrapes; los 20 s de E3 acotan la caída. Se miden 30 s antes y después.')
label(2,'Fallos, alcance y recuperación automática')
table([['<b>Diseño y fallo</b>','<b>Radio y duración</b>','<b>Inyección y rollback</b>'],['E1/H1: latencia.<br/>Ejecutado.','Solo eth0 de target, incluidos /hello y scrape. Máximo 60 s.','tc qdisc replace dev eth0 root netem delay 300ms. Watchdog interno elimina qdisc a 60 s; finally lo retira al abortar. Se verifica noqueue.'],['E2/H2: agotamiento CPU.<br/>Diseñado.','Solo cuota de target; Prometheus queda fuera. Carga de 60 s.','stress-ng --cpu 2 --timeout 60s, con supervisor timeout externo TERM a 60 s y KILL a 65 s si persiste. Solo termina trabajadores del ensayo.'],['E3/H3: caída de proceso.<br/>Diseñado.','Única réplica target, hasta 20 s; no es partición de red.','Armar watchdog host independiente que inicie target a 20 s; aplicar compose kill -s SIGKILL target. Finally inicia de nuevo. Verificar salud y UP.']],[99,132,237])
p('Gremlin modelaría CPU/latencia; Litmus, sondas y selección sandbox; Chaos Monkey, pérdida de instancia. Son equivalencias conceptuales. README.md concreta los runbooks. Se ejecuta un fallo a la vez; se detiene ante degradación residual.')
h2('SLI, registros y trazas')
p('Para H1-H3: disponibilidad = 2xx/total; error = 1 - disponibilidad; throughput = éxitos/segundos; p95 por rango más cercano, incluidos timeouts. El CSV registra UTC, fase, estado, duración y trace_id cliente. H1 contrasta red/handler; H2 observa CPU y memoria con docker stats; H3, conexión, up y reinicio. Los histogramas permiten estimar percentiles (Prometheus Authors, s. f.).')
p('Uvicorn aporta accesos; eventos.json, inyección/retirada; /metrics y up, proceso/scrape. Los IDs son spans cliente sin traza distribuida servidor; se propone OpenTelemetry y logs correlacionados. La recuperación se valida en 30 s, sin estimar MTTR exacto ni SLO mensual.')
page()
h('Resultados y acciones de mejora')
p('Se ejecutó E1 el 18 de octubre de 2026, 22:05-22:06 (Colombia). Se inició compose.yaml y ejecutar.py: referencia, watchdog, netem, parada y recuperación. Las 336 solicitudes y los comandos están en evidencias. La Tabla 3 contrasta H1 (≥99% y p95 &lt;200 ms) con los resultados.')
label(3,'Resultados medidos antes, durante y después de E1')
data=[['<b>Fase</b>','<b>Total/2xx</b>','<b>Disponibilidad</b>','<b>p95 (ms)</b>']]
for key,name in [('baseline','Referencia'),('fault','Fallo'),('recovery','Recuperación')]:
    v=R[key]
    data.append([name,f'{v["requests"]}/{v["successes"]}',f'{v["availability"]*100:.2f}%',f'{v["p95_ms"]:.1f}'])
table(data,[118,96,145,109])
p(f'H1 se refutó: 21 timeouts y parada a {R["fault"]["actual_seconds"]:.2f} s, con {R["fault"]["throughput_rps"]:.2f} éxitos/s. Finally retiró netem y tc mostró noqueue. El preensayo abortado se conserva aparte; E2/E3 siguen como diseños. La Figura 1 muestra la degradación y recuperación.')
label(1,'Latencia de las solicitudes del ensayo E1',kind='Figura')
story.append(Image(str(E/'resultados.png'),width=W,height=W*2.05/9))
text('<i>Nota.</i> Elaboración propia desde solicitudes.csv; los timeouts incluyen la espera.')
h2('Debilidad sistémica y remediación')
p('La única réplica es vulnerable a la red: /health no garantiza experiencia de usuario. TCP y Docker pueden amplificar el retardo; no se atribuye todo a 300 ms. Las alertas previas a 1 y 5 min no aseguran detectar este fallo breve.')
p('Prioridad 1: el observador añadirá sondeo externo con detección ≤10 s; el operador probará dos réplicas con éxito ≥99% en E3. Prioridad 2: ajustar timeouts y capacidad con E2 y correlacionar trazas. El director repetirá el plan para cerrar mejoras SRE con SLI.')
page()
h('Referencias')
for entry in [
    'Ludovici, F., &amp; Pfeifer, H. P. (2011, 25 de noviembre). <i>tc-netem(8): Linux manual page</i>. man7.org. https://man7.org/linux/man-pages/man8/tc-netem.8.html',
    'Principles of Chaos Engineering. (2019, marzo). <i>Principles of chaos engineering</i>. https://principlesofchaos.org/',
    'Prometheus Authors. (s. f.). <i>Histograms and summaries</i>. Prometheus. https://prometheus.io/docs/practices/histograms/',
    'Universidad de La Sabana. (2026). <i>Actividad 3.2. Laboratorio Plan de Game Day U3</i> [Consigna y criterios de evaluación]. VirtualSabana. https://unisabanae-learning.unisabana.edu.co/mod/assign/view.php?id=306420',
    'yuliet719-beep. (s. f.). <i>mi-microservicio</i> [Código fuente, versión '+R['source_commit'][:12]+']. GitHub. https://github.com/yuliet719-beep/mi-microservicio/tree/'+R['source_commit'],
]: story.append(Paragraph(entry,ref))

h('Anexos')
text('<b>Anexo A. Repositorio y evidencias reproducibles</b>')
text('Repositorio: <link href="https://github.com/yuliet719-beep/mi-microservicio">https://github.com/yuliet719-beep/mi-microservicio</link>')
text('Carpeta de entrega: <link href="https://github.com/yuliet719-beep/mi-microservicio/tree/main/Actividad%203.2%20-%20Laboratorio%20Plan%20de%20Game%20Day">Actividad 3.2 - Laboratorio Plan de Game Day</link>. Contiene el informe, los datos originales, la captura de Prometheus y los archivos para repetir el ensayo.')
text('Archivo complementario: Evidencias_Game_Day.zip. Incluye evidencias, plan previo, código de ejecución, configuración del sandbox y README con la auditoría de los 20 criterios.')

def header(canvas,doc):
    canvas.setFillColor(colors.black)
    canvas.setFont('Arial',11)
    canvas.drawRightString(letter[0]-72,letter[1]-36,str(doc.page))
    if doc.page == 1:
        for index,line in enumerate(['EFMAS-OBAP20265: Observabilidad en Ambientes Productivos','Actividad 3.2. Laboratorio Plan de Game Day','Carol Daniela Suarez Mendez','18 de octubre de 2026']):
            canvas.drawCentredString(letter[0]/2,138-index*22,line)
pdf=ROOT/'Plan_Game_Day.pdf'
SimpleDocTemplate(str(pdf),pagesize=letter,leftMargin=72,rightMargin=72,topMargin=72,bottomMargin=72,title='Plan de Game Day para evaluar la resiliencia de mi-microservicio',author='Manuel Fernando Santofimio Tovar; Beycy Yuliet Rojas').build(story,onFirstPage=header,onLaterPages=header)
doc=pymupdf.open(pdf)
print('Paginas generadas:',len(doc))
preview=ROOT/'revision'
preview.mkdir(exist_ok=True)
for i,pg in enumerate(doc): pg.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(preview/f'pagina_{i+1}.png')
assert len(doc)==5,f'Se requieren cinco paginas; se generaron {len(doc)}'
print('Informe APA validado: 5 paginas')
