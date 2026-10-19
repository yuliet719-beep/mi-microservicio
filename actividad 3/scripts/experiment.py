"""Real sandbox traffic, automatic alert readback, rollback and evidence capture."""
import argparse
import concurrent.futures
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import math
import subprocess
import time
import urllib.request
import urllib.parse
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidencias'
E.mkdir(exist_ok=True)
env = dict(line.split('=', 1) for line in (ROOT / '.env').read_text().splitlines() if '=' in line)
events, samples = [], []


def get(url):
    with urllib.request.urlopen(url, timeout=8) as r:
        return json.load(r)


def save(name, data):
    (E / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def event(name, **data):
    row = {'event': name, 'epoch': time.time(), 'utc': datetime.now(timezone.utc).isoformat(), **data}
    events.append(row)
    save('events.json', events)
    print(json.dumps(row), flush=True)
    return row['epoch']


def control(port, **config):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/control',
            data=json.dumps({'ttl_s': 90, **config}).encode(), method='POST',
            headers={'Content-Type': 'application/json', 'x-control-token': env['CONTROL_TOKEN']})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)


def request(phase):
    start = time.time()
    try:
        r = urllib.request.urlopen('http://127.0.0.1:18080/work', timeout=6)
    except urllib.error.HTTPError as exc:
        r = exc
    except Exception as exc:
        return {'epoch': start, 'phase': phase, 'status': 0, 'duration_s': time.time() - start,
                'trace_id': '', 'error': type(exc).__name__}
    with r:
        try:
            payload = json.load(r)
        except (ValueError, OSError):
            payload = {'error': 'non-JSON or unreadable response'}
        return {'epoch': start, 'phase': phase, 'status': r.status,
                'duration_s': time.time() - start, 'trace_id': r.headers.get('x-trace-id', ''),
                'error': payload.get('error', '')}


def phase(name, seconds, alert_name=None, started=None):
    end = time.monotonic() + seconds
    detected = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        while time.monotonic() < end:
            samples.extend(pool.map(request, [name] * 4))
            if alert_name and detected is None:
                alerts = get('http://127.0.0.1:19090/api/v1/alerts')['data']['alerts']
                for a in alerts:
                    if a['labels'].get('alertname') == alert_name and a['state'] == 'firing':
                        detected = time.time()
                        event('alert_firing', phase=name, alert=alert_name, mttd_s=detected - started)
                        save(name + '-prometheus-alert.json', a)
            time.sleep(0.12)
    save(name + '-aiops.json', get('http://127.0.0.1:18083/state'))
    return None if detected is None else detected - started


def main():
    event('preflight')
    # Wait for actual service startup and frozen baseline; no inferred readiness.
    deadline = time.monotonic() + 180
    while True:
        try:
            ready = all(get(f'http://127.0.0.1:{p}/health')['status'] == 'ok' for p in (18080, 18081, 18082))
            state = get('http://127.0.0.1:18083/state')
            if ready and state['baseline_ready']:
                break
        except Exception:
            pass
        if time.monotonic() > deadline:
            raise RuntimeError('Readiness/baseline timed out')
        time.sleep(2)
    save('baseline.json', state['baseline'])
    event('baseline_ready')
    # Wait for actual readiness before priming the authentication counter.
    try:
        urllib.request.urlopen('http://127.0.0.1:18080/auth', timeout=5)
    except urllib.error.HTTPError as exc:
        assert exc.code == 401
    phase('baseline', 20)
    baseline_alerts = get('http://127.0.0.1:19090/api/v1/alerts')['data']['alerts']
    assert not any(a['state'] == 'firing' and a['labels'].get('alertname') in
                   ('ServiceBLatency', 'CorrelatedDataServiceAnomaly') for a in baseline_alerts), 'Pre-existing alert invalidates MTTD'
    mttds = {}
    try:
        # Identical error-rate stimulus without slow requests: measured noise comparison.
        start_noise = event('noise_start', error_rate=0.1, error_delay_ms=0)
        control(18082, error_rate=0.1, error_delay_ms=0)
        phase('noise', 25)
        control(18082, error_rate=0)
        event('noise_end')
        phase('noise_recovery', 10)
        start = event('latency_start', service='service-b', latency_ms=200)
        control(18081, latency_ms=200)
        mttds['latency'] = phase('latency', 40, 'ServiceBLatency', start)
        control(18081, latency_ms=0)
        event('latency_rollback')
        phase('latency_recovery', 25)
        start = event('errors_start', service='data-service', error_rate=0.1, error_delay_ms=250)
        control(18082, error_rate=0.1)
        mttds['errors'] = phase('errors', 45, 'CorrelatedDataServiceAnomaly', start)
        control(18082, error_rate=0)
        event('errors_rollback')
        phase('recovery', 30)
        for _ in range(10):
            try:
                urllib.request.urlopen('http://127.0.0.1:18080/auth', timeout=5)
            except urllib.error.HTTPError as exc:
                assert exc.code == 401
        event('auth_probe', failed_attempts=10)
        time.sleep(8)
        save('security-alerts.json', get('http://127.0.0.1:19090/api/v1/alerts'))
    finally:
        control(18081, latency_ms=0)
        control(18082, error_rate=0)
        event('rollback_finally')
        if samples:
            with (E / 'requests.csv').open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=samples[0].keys()); writer.writeheader(); writer.writerows(samples)
    state = get('http://127.0.0.1:18083/state')
    save('aiops-state.json', state)
    summary = {}
    for phase_name in dict.fromkeys(r['phase'] for r in samples):
        rows = [r for r in samples if r['phase'] == phase_name]
        ds = sorted(r['duration_s'] for r in rows)
        errors = sum(r['status'] >= 500 or r['status'] == 0 for r in rows)
        # Each request must be successful AND <=200ms for the composite SLI.
        bad = sum(r['status'] >= 500 or r['status'] == 0 or r['duration_s'] > 0.2 for r in rows)
        summary[phase_name] = {'requests': len(rows), 'errors': errors, 'error_rate': errors / len(rows),
            'p99_s': ds[math.ceil(len(ds)*0.99)-1], 'good': len(rows)-bad, 'bad': bad,
            'sli': 1-bad/len(rows), 'budget_allowed_requests_99pct': len(rows)*0.01,
            'budget_consumed_multiple': bad/(len(rows)*0.01)}
    noise_windows = [w for w in state['windows'] if start_noise + 5 <= w['epoch'] < next(
        x['epoch'] for x in events if x['event'] == 'noise_end')]
    static_n = sum(w['static_alert'] for w in noise_windows)
    corr_n = sum(w['correlated_alert'] for w in noise_windows)
    save('results.json', {'scope': 'local Docker sandbox; no GCP/AWS deployment',
        'mttd_s': mttds, 'phases': summary, 'noise_comparison': {'windows': len(noise_windows),
        'static': static_n, 'correlated': corr_n, 'reduction': (static_n-corr_n)/static_n if static_n else None},
        'slo': {'target': 0.99, 'latency_threshold_s': 0.2, 'window': 'each experimental phase; not a monthly SLO'}})
    save('targets.json', get('http://127.0.0.1:19090/api/v1/targets'))
    for name, query in [('metrics.json', 'lab_requests_total'), ('network-metrics.json', 'envoy_http_downstream_rq_total')]:
        save(name, get('http://127.0.0.1:19090/api/v1/query?' + urllib.parse.urlencode({'query': query})))
    # A single trace must span all three services AND a real PostgreSQL query.
    tid = next(r['trace_id'] for r in reversed(samples) if r['status'] == 200 and r['trace_id'])
    save('trace-success.json', get('http://127.0.0.1:13200/api/traces/' + tid))
    failed_id = next((a['trace_id'] for a in reversed(state['alerts']) if a['trace_id']), None)
    if failed_id:
        save('trace-failed.json', get('http://127.0.0.1:13200/api/traces/' + failed_id))
    save('logs.json', get('http://127.0.0.1:13100/loki/api/v1/query_range?' + urllib.parse.urlencode(
        {'query': '{service_name=~"service-a|service-b|data-service"}', 'limit': 300})))
    for svc in ('mesh-b', 'mesh-data', 'collector'):
        p = subprocess.run(['docker', 'compose', 'logs', '--no-color', '--tail', '300', svc], cwd=ROOT,
                            capture_output=True, text=True, encoding='utf-8')
        (E / f'{svc}.log').write_text(p.stdout + p.stderr, encoding='utf-8')
    event('finished', mttd_s=mttds)
    assert all(v is not None and v < 120 for v in mttds.values()), 'MTTD failed; inspect genuine evidence'
    assert summary['recovery']['error_rate'] == 0, 'Recovery failed'


if __name__ == '__main__':
    main()
