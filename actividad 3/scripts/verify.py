"""Assert evidence postconditions, including cross-service trace and real DB span."""
import json
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidencias'
checks = {}


def check(name, passed):
    checks[name] = bool(passed)


results = json.loads((E / 'results.json').read_text(encoding='utf-8'))
check('two_automatic_alerts_under_120s', all(v is not None and v < 120 for v in results['mttd_s'].values()))
check('recovery_no_errors', results['phases']['recovery']['error_rate'] == 0)
check('noise_reduction_measured', (results['noise_comparison']['reduction'] or 0) > 0)
trace = json.loads((E / 'trace-success.json').read_text())
raw = json.dumps(trace)
check('trace_three_services', all(f'"{s}"' in raw for s in ('service-a', 'service-b', 'data-service')))
check('trace_real_sql', 'SELECT' in raw and 'postgresql' in raw and 'db.operation.name' in raw)
logs = json.loads((E / 'logs.json').read_text())
check('logs_persisted_loki', len(logs['data']['result']) > 0)
check('logs_trace_correlation', 'trace_id' in json.dumps(logs))
metrics = json.loads((E / 'metrics.json').read_text())
check('metrics_three_services', all(s in json.dumps(metrics) for s in ('service-a', 'service-b', 'data-service')))
network = json.loads((E / 'network-metrics.json').read_text())
check('envoy_l7_metrics', len(network['data']['result']) > 0)
security = json.loads((E / 'security-alerts.json').read_text())
check('authentication_alert_firing', any(a['labels'].get('alertname') == 'AuthFailures' and a['state'] == 'firing'
                                        for a in security['data']['alerts']))
try:
    urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:18082/control', data=b'{}',
                           headers={'Content-Type': 'application/json'}), timeout=5)
    check('chaos_requires_operator_token', False)
except urllib.error.HTTPError as exc:
    check('chaos_requires_operator_token', exc.code == 403)
(E / 'verification.json').write_text(json.dumps(checks, indent=2))
print(json.dumps(checks, indent=2))
if not all(checks.values()):
    raise SystemExit('Evidence check failed; do not claim completion')
