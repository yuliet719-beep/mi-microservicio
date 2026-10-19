"""Continuous detector: learns a frozen baseline, evaluates independent windows."""
import asyncio
import json
import os
import statistics
import time
from collections import deque
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(title='AIOps detector')
state = {'baseline_ready': False, 'baseline': {}, 'windows': [], 'alerts': [], 'running': True}
anomaly = Gauge('aiops_correlated_anomaly', 'Correlated anomaly in latest window')
static = Counter('aiops_static_windows', 'Windows with any failed request')
correlated = Counter('aiops_correlated_windows', 'Windows satisfying both conditions')
p99g = Gauge('aiops_p99_seconds', 'Observed probe p99')
errg = Gauge('aiops_error_rate', 'Observed probe error fraction')
baselineg = Gauge('aiops_baseline_threshold', 'Frozen baseline mean plus two sigma')


def evaluate(error_rate, p99, mean, sigma, slo=0.2):
    return error_rate > mean + 2 * sigma and p99 > slo


async def loop():
    baseline = []
    async with httpx.AsyncClient(timeout=4) as client:
        # Exclude startup connection failures from the learned operational baseline.
        while True:
            try:
                ready = await client.get('http://data-service:8000/health')
                if ready.status_code == 200:
                    break
            except httpx.RequestError:
                pass
            await asyncio.sleep(1)
        await asyncio.sleep(3)
        while True:
            samples = []
            for _ in range(30):
                started = time.monotonic()
                try:
                    r = await client.get(os.getenv('PROBE_URL', 'http://mesh-data:8080/work'))
                    samples.append((time.monotonic() - started, r.status_code >= 500,
                                    r.headers.get('x-trace-id', ''), time.time()))
                except httpx.RequestError:
                    samples.append((time.monotonic() - started, True, '', time.time()))
                await asyncio.sleep(0.05)
            er = sum(x[1] for x in samples) / len(samples)
            p99 = sorted(x[0] for x in samples)[-1]  # nearest rank for n=30
            if not state['baseline_ready']:
                baseline.append(er)
                if len(baseline) >= 12:
                    mean, sigma = statistics.mean(baseline), statistics.pstdev(baseline)
                    state['baseline'] = {'mean': mean, 'sigma': sigma, 'windows': len(baseline),
                                         'threshold': mean + 2 * sigma, 'samples_per_window': 30}
                    state['baseline_ready'] = True
                    baselineg.set(mean + 2 * sigma)
                continue
            b = state['baseline']
            hit = evaluate(er, p99, b['mean'], b['sigma'])
            failed = next((x for x in samples if x[1] and x[2]), None)
            window = {'timestamp': datetime.now(timezone.utc).isoformat(), 'epoch': time.time(),
                      'error_rate': er, 'p99_s': p99, 'threshold': b['threshold'],
                      'static_alert': er > 0, 'correlated_alert': hit,
                      'trace_id': failed[2] if failed else '', 'samples': len(samples)}
            state['windows'].append(window)
            state['windows'] = state['windows'][-2000:]
            anomaly.set(int(hit)); p99g.set(p99); errg.set(er)
            if er > 0:
                static.inc()
            if hit:
                correlated.inc()
                alert = {**window, 'service': 'data-service', 'severity': 'critical',
                         'runbook': 'docs/RUNBOOK.md', 'action': 'rollback fault, inspect DB span',
                         'id': f'data-{int(time.time())}'}
                state['alerts'].append(alert)
                print(json.dumps(alert), flush=True)


@app.on_event('startup')
async def startup():
    app.state.task = asyncio.create_task(loop())


@app.get('/state')
def status():
    return state


@app.get('/alerts')
def alerts():
    return state['alerts']


@app.get('/metrics')
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
