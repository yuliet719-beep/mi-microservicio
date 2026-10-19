"""Ejecuta E1 real con tc netem; solo usa biblioteca estandar de Python."""
import concurrent.futures as futures
import csv
import datetime as dt
import json
import math
from pathlib import Path
import subprocess
import threading
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidencias'
OUT.mkdir(exist_ok=True)
PLAN = json.loads((ROOT / 'plan_previo.json').read_text())
CMD = ['docker', 'compose', '-p', 'actividad2-gameday', '-f', str(ROOT / 'compose.yaml')]
rows = []
events = []
stop = threading.Event()
started = time.monotonic()

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def command(args, check=True):
    p = subprocess.run(args, capture_output=True, text=True)
    events.append({'utc': utc(), 'command': args, 'code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    (OUT / 'eventos.json').write_text(json.dumps(events, indent=2), encoding='utf-8')
    if check and p.returncode:
        raise RuntimeError(p.stderr)
    return p.stdout

def get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read().decode()

def sample(phase):
    t = time.perf_counter()
    trace = uuid.uuid4().hex
    status, error = 0, ''
    try:
        req = urllib.request.Request('http://127.0.0.1:18082/hello', headers={'X-Request-ID': trace})
        with urllib.request.urlopen(req, timeout=PLAN['timeout_seconds']) as r:
            status = r.status
            r.read()
    except Exception as exc:
        error = str(exc)
    return {'utc': utc(), 'elapsed_s': round(time.monotonic()-started, 3), 'phase': phase,
            'trace_id': trace, 'status': status, 'duration_ms': round((time.perf_counter()-t)*1000, 3), 'error': error}

def stats(data, seconds):
    latency = sorted(r['duration_ms'] for r in data)
    good = sum(200 <= r['status'] < 300 for r in data)
    return {'requests': len(data), 'successes': good, 'availability': good/len(data),
            'p95_ms': latency[math.ceil(.95*len(latency))-1],
            'under_200ms_ratio': sum(200 <= r['status'] < 300 and r['duration_ms'] < 200 for r in data)/len(data),
            'throughput_rps': good/seconds}

def phase(name, seconds):
    print('Fase:', name, flush=True)
    batch = []
    start = time.monotonic()
    with futures.ThreadPoolExecutor(max_workers=12) as pool:
        for i in range(seconds*PLAN['rate_rps']):
            time.sleep(max(0, start+i/PLAN['rate_rps']-time.monotonic()))
            batch.append(pool.submit(sample, name))
            completed = [f.result() for f in batch if f.done()]
            if len(completed) >= 10 and all(r['status'] == 0 or r['status'] >= 500 for r in completed[-10:]):
                stop.set()
                print('ABORT: diez fallos consecutivos; se activa rollback', flush=True)
                break
        data = [f.result() for f in batch]
    rows.extend(data)
    if name != 'fault':
        (OUT / f'metrics_{name}.txt').write_text(get('http://127.0.0.1:18082/metrics'))
    (OUT / f'prometheus_{name}.json').write_text(get('http://127.0.0.1:19092/api/v1/query?query=up'))
    with (OUT / 'solicitudes.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = stats(data, time.monotonic()-start)
    result['actual_seconds'] = round(time.monotonic()-start, 3)
    result['aborted'] = stop.is_set() and name == 'fault'
    return result

summary = {'started_utc': utc(), 'source_commit': command(['git', '-C', str(ROOT.parent), 'rev-parse', 'HEAD']).strip(), 'plan': PLAN}
try:
    command(CMD + ['exec', '-T', 'target', 'tc', 'qdisc', 'show', 'dev', 'eth0'])
    summary['baseline'] = phase('baseline', PLAN['baseline_seconds'])
    if summary['baseline']['availability'] < .99 or summary['baseline']['p95_ms'] >= 200:
        raise RuntimeError('ABORT: baseline fuera del estado estable')
    # Watchdog en el namespace objetivo: sobrevive a la salida del cliente.
    command(CMD + ['exec', '-d', 'target', 'sh', '-c', 'sleep 60; tc qdisc del dev eth0 root; date -u > /tmp/rollback.txt'])
    command(CMD + ['exec', '-T', 'target', 'tc', 'qdisc', 'replace', 'dev', 'eth0', 'root', 'netem', 'delay', '300ms'])
    command(CMD + ['exec', '-T', 'target', 'tc', '-s', 'qdisc', 'show', 'dev', 'eth0'])
    summary['fault'] = phase('fault', PLAN['fault_seconds'])
finally:
    command(CMD + ['exec', '-T', 'target', 'tc', 'qdisc', 'del', 'dev', 'eth0', 'root'], check=False)
    command(CMD + ['exec', '-T', 'target', 'tc', '-s', 'qdisc', 'show', 'dev', 'eth0'], check=False)
    (OUT / 'eventos.json').write_text(json.dumps(events, indent=2), encoding='utf-8')
summary['recovery'] = phase('recovery', PLAN['recovery_seconds'])
summary['finished_utc'] = utc()
summary['hypothesis_accepted'] = summary['fault']['availability'] >= .99 and summary['fault']['p95_ms'] < 200 and summary['recovery']['p95_ms'] < 200
(OUT / 'resultados.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
(OUT / 'servidor.log').write_text(command(CMD + ['logs', '--no-color', '--timestamps', 'target']), encoding='utf-8')
command(CMD + ['exec', '-T', 'target', 'cat', '/tmp/rollback.txt'], check=False)
print(json.dumps(summary, indent=2), flush=True)
