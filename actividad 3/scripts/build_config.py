"""Generate deterministic Envoy routes and Grafana dashboards."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
for short, target in [('b', 'service-b'), ('data', 'data-service')]:
    config = f'''admin:
  address:
    socket_address: {{address: 0.0.0.0, port_value: 9901}}
static_resources:
  listeners:
    - name: east_west
      address:
        socket_address: {{address: 0.0.0.0, port_value: 8080}}
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: east_west
                access_log:
                  - name: envoy.access_loggers.stdout
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.access_loggers.stream.v3.StdoutAccessLog
                      log_format:
                        json_format:
                          time: "%START_TIME%"
                          method: "%REQ(:METHOD)%"
                          path: "%REQ(:PATH)%"
                          code: "%RESPONSE_CODE%"
                          duration_ms: "%DURATION%"
                          traceparent: "%REQ(TRACEPARENT)%"
                          upstream: "%UPSTREAM_HOST%"
                route_config:
                  name: local_route
                  virtual_hosts:
                    - name: service
                      domains: ["*"]
                      routes:
                        - match: {{prefix: /}}
                          route: {{cluster: upstream, timeout: 4s}}
                http_filters:
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
  clusters:
    - name: upstream
      type: STRICT_DNS
      connect_timeout: 1s
      load_assignment:
        cluster_name: upstream
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address: {{address: {target}, port_value: 8000}}
'''
    (ROOT / 'config' / f'envoy-{short}.yaml').write_text(config)
g = ROOT / 'config/grafana'
(g / 'datasources').mkdir(parents=True, exist_ok=True)
(g / 'dashboards').mkdir(parents=True, exist_ok=True)
(g / 'datasources/datasources.yaml').write_text('''apiVersion: 1
datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
  - name: Tempo
    uid: tempo
    type: tempo
    url: http://tempo:3200
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
        filterByTraceID: true
  - name: Loki
    uid: loki
    type: loki
    url: http://loki:3100
    jsonData:
      derivedFields:
        - name: TraceID
          matcherRegex: '"trace_id": "(\\w+)"'
          datasourceUid: tempo
          url: '$${__value.raw}'
'''.replace('$${', '${'))
(g / 'dashboards/provider.yaml').write_text('''apiVersion: 1
providers:
  - name: integrador
    options:
      path: /etc/grafana/provisioning/dashboards
''')
queries = [
    ('Solicitudes / s', 'sum by (service) (rate(lab_requests_total[30s]))', 'reqps'),
    ('Errores HTTP 5xx', 'sum by (service) (rate(lab_requests_total{status=~"5.."}[30s]))', 'reqps'),
    ('Latencia p99 por servicio', 'histogram_quantile(0.99, sum by (le, service) (rate(lab_duration_seconds_bucket[30s])))', 's'),
    ('AIOps: error rate vs baseline + 2 sigma', 'aiops_error_rate or aiops_baseline_threshold', 'percentunit'),
    ('Golden Signals: autenticacion fallida', 'sum(rate(lab_auth_failures_total[30s]))', 'reqps'),
    ('Golden Signals: trafico E-W Envoy', 'sum(rate(envoy_http_downstream_rq_total[30s]))', 'reqps'),
    ('Alerta correlacionada', 'aiops_correlated_anomaly', 'short'),
    ('Ventanas estaticas vs correlacionadas', 'aiops_static_windows_total or aiops_correlated_windows_total', 'short'),
]
panels = []
for i, (title, expr, unit) in enumerate(queries):
    panels.append({'id': i + 1, 'title': title, 'type': 'timeseries',
                   'datasource': {'type': 'prometheus', 'uid': 'prometheus'},
                   'gridPos': {'x': (i % 2) * 12, 'y': (i // 2) * 7, 'w': 12, 'h': 7},
                   'targets': [{'expr': q, 'refId': chr(65+j), 'legendFormat': '{{service}} {{__name__}}'}
                               for j, q in enumerate(expr.split(' or '))],
                   'fieldConfig': {'defaults': {'unit': unit}, 'overrides': []}})
scan = ROOT / 'evidencias/security-scan.json'
finding_text = 'Sin escaneo disponible; vulnerabilidades no equivalen a cero.'
if scan.exists():
    audit = json.loads(scan.read_text(encoding='utf-8'))
    ids = sorted({v['id'] for d in audit['dependencies'] for v in d['vulns']})
    finding_text = f'**{len(ids)} identificadores unicos de vulnerabilidad** en dependencias Python. Instantanea de pip-audit; no es escaneo de imagen ni Security Hub/SCC. Ver `evidencias/security-scan.json`. Prioridad: actualizar FastAPI/Starlette y repetir las pruebas.'
panels.append({'id': 9, 'title': 'Seguridad: vulnerabilidades conocidas (instantanea)', 'type': 'text',
               'gridPos': {'x': 0, 'y': 28, 'w': 24, 'h': 3},
               'options': {'mode': 'markdown', 'content': finding_text}})
dashboard = {'uid': 'actividad3-integrador', 'title': 'Actividad 3 - Observabilidad end-to-end',
             'schemaVersion': 39, 'version': 1, 'refresh': '5s',
             'time': {'from': 'now-15m', 'to': 'now'}, 'panels': panels}
(g / 'dashboards/integrador.json').write_text(json.dumps(dashboard, indent=2))
print('Envoy and Grafana configuration generated')
