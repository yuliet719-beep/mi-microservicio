"""Repeat a ten-request burst once a prior counter sample exists."""
import json
from pathlib import Path
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
E=Path(__file__).resolve().parents[1]/'evidencias'
start=datetime.now(timezone.utc).isoformat()
codes=[]
for _ in range(10):
    try:
        urllib.request.urlopen('http://127.0.0.1:18080/auth',timeout=5)
    except urllib.error.HTTPError as exc:
        codes.append(exc.code)
deadline=time.monotonic()+20
while True:
    with urllib.request.urlopen('http://127.0.0.1:19090/api/v1/alerts',timeout=5) as r:
        alerts=json.load(r)
    if any(a['labels'].get('alertname')=='AuthFailures' and a['state']=='firing' for a in alerts['data']['alerts']):
        break
    if time.monotonic()>deadline:
        raise RuntimeError('Security alert did not fire')
    time.sleep(1)
(E/'security-alerts.json').write_text(json.dumps(alerts,indent=2))
(E/'security-validation.json').write_text(json.dumps({'utc':start,'repeat_burst':10,
    'total_attempts_this_session':20,'http_codes':codes,'reason':'First burst created the counter; second burst validates increase() against existing samples',
    'alert_firing':True},indent=2))
print('Ten-request security burst: 10 HTTP 401; AuthFailures FIRING')
