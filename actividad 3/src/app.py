"""Three independently deployed services; all three OTel signals use OTLP."""
import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel, Field
import httpx
import psycopg2
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.view import View, ExplicitBucketHistogramAggregation
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.trace import Status, StatusCode, SpanKind

SERVICE = os.getenv('SERVICE_NAME', 'service-a')
RESOURCE = Resource.create({'service.name': SERVICE, 'deployment.environment.name': 'sandbox',
                            'cloud.provider': os.getenv('CLOUD_PROVIDER', 'local')})
provider = TracerProvider(resource=RESOURCE)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer('integrador')
metrics.set_meter_provider(MeterProvider(resource=RESOURCE, views=[View(
    instrument_name='lab_duration', aggregation=ExplicitBucketHistogramAggregation(
        boundaries=[0.005, 0.01, 0.025, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5, 1, 2, 5]))], metric_readers=[
    PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=2000)]))
meter = metrics.get_meter('integrador')
requests_total = meter.create_counter('lab_requests')
duration = meter.create_histogram('lab_duration', unit='s')
auth_failures = meter.create_counter('lab_auth_failures')
log_provider = LoggerProvider(resource=RESOURCE)
log_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
logger = logging.getLogger('integrador')
logger.setLevel(logging.INFO)
logger.addHandler(LoggingHandler(logger_provider=log_provider))
logger.addHandler(logging.StreamHandler())
HTTPXClientInstrumentor().instrument()
Psycopg2Instrumentor().instrument()
app = FastAPI(title=SERVICE)
FastAPIInstrumentor.instrument_app(app, excluded_urls='health,control')


@app.on_event('startup')
async def open_client():
    app.state.client = httpx.AsyncClient(timeout=3)


@app.on_event('shutdown')
async def close_client():
    await app.state.client.aclose()

fault = {'latency_ms': 0, 'error_rate': 0.0, 'error_delay_ms': 250, 'expires': 0.0}
rng = random.Random(7341)


class Fault(BaseModel):
    latency_ms: int = Field(0, ge=0, le=2000)
    error_rate: float = Field(0, ge=0, le=0.5)
    ttl_s: int = Field(60, ge=1, le=120)
    error_delay_ms: int = Field(250, ge=0, le=1000)


def trace_id():
    return format(trace.get_current_span().get_span_context().trace_id, '032x')


@app.middleware('http')
async def telemetry(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    if request.url.path in ('/work', '/auth'):
        attrs = {'service': SERVICE, 'status': str(response.status_code)}
        requests_total.add(1, attrs)
        duration.record(time.perf_counter() - started, {'service': SERVICE})
    return response


@app.get('/health')
def health():
    return {'status': 'ok', 'service': SERVICE, 'environment': 'sandbox'}


@app.post('/control')
def control(config: Fault, request: Request):
    token = os.environ.get('CONTROL_TOKEN')
    if not token or request.headers.get('x-control-token') != token:
        raise HTTPException(403, 'Control restricted to sandbox operator')
    fault.update(latency_ms=config.latency_ms, error_rate=config.error_rate, error_delay_ms=config.error_delay_ms,
                 expires=time.monotonic() + config.ttl_s)
    return {'service': SERVICE, 'ttl_s': config.ttl_s, 'config': config.model_dump()}


@app.get('/auth')
def auth(request: Request):
    if request.headers.get('authorization') != 'Bearer sandbox-demo':
        auth_failures.add(1, {'service': SERVICE})
        logger.warning(json.dumps({'event': 'auth_failed', 'service': SERVICE, 'trace_id': trace_id()}))
        raise HTTPException(401, 'Invalid sandbox credential')
    return {'authenticated': True}


@app.get('/work')
async def work(response: Response):
    response.status_code = 200
    tid = trace_id()
    response.headers['x-trace-id'] = tid
    active = time.monotonic() < fault['expires']
    if active and fault['latency_ms']:
        await asyncio.sleep(fault['latency_ms'] / 1000)
    # Errors also have latency: the AND correlation rule must observe both signals.
    if active and rng.random() < fault['error_rate']:
        await asyncio.sleep(fault['error_delay_ms'] / 1000)
        trace.get_current_span().set_status(Status(StatusCode.ERROR, 'sandbox injected fault'))
        logger.error(json.dumps({'event': 'injected_error', 'service': SERVICE, 'trace_id': tid}))
        response.status_code = 503
        return {'error': 'injected fault', 'trace_id': tid, 'service': SERVICE}
    if SERVICE == 'data-service':
        try:
            with tracer.start_as_current_span('SELECT inventory', kind=SpanKind.CLIENT,
                    attributes={'db.system.name': 'postgresql', 'db.namespace': 'observability',
                                'db.operation.name': 'SELECT', 'db.query.summary': 'SELECT inventory',
                                'server.address': os.getenv('DB_HOST', 'database'), 'server.port': 5432}):
                with psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=3) as conn:
                    with conn.cursor() as cur:
                        cur.execute('SELECT id, name, quantity FROM inventory ORDER BY id LIMIT 5')
                        rows = cur.fetchall()
            result = {'items': rows}
        except psycopg2.Error:
            response.status_code = 503
            result = {'error': 'database unavailable'}
            trace.get_current_span().set_status(Status(StatusCode.ERROR))
    else:
        target = os.environ['DOWNSTREAM_URL']
        try:
            downstream = await app.state.client.get(target + '/work')
            response.status_code = downstream.status_code
            try:
                result = {'downstream': downstream.json()}
            except ValueError:
                result = {'error': 'non-JSON upstream response', 'upstream_status': downstream.status_code}
                logger.error(json.dumps({'event': 'upstream_protocol_error', 'service': SERVICE,
                                         'trace_id': tid, 'status': downstream.status_code}))
        except httpx.RequestError:
            response.status_code = 502
            result = {'error': 'downstream unavailable'}
    logger.info(json.dumps({'event': 'request_completed', 'time': datetime.now(timezone.utc).isoformat(),
                            'service': SERVICE, 'trace_id': tid, 'status': response.status_code}))
    return {'service': SERVICE, 'trace_id': tid, **result}
