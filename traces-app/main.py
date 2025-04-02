import time
import random
import logging
import http.client

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('opentelemetry')
logger.setLevel(logging.INFO)

app = FastAPI()

resource = Resource(attributes={
    "service.name": "test-api-service"
})

provider = TracerProvider(resource=resource)

otel_endpoint_url = "http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4317"
if otel_endpoint_url:
    otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint_url)
    processor = BatchSpanProcessor(otlp_exporter)
else:
    processor = BatchSpanProcessor(ConsoleSpanExporter())

provider.add_span_processor(processor)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

FastAPIInstrumentor.instrument_app(app)

FAST_API_HOST = "test-app.playground.svc.cluster.local"
SLOW_API_HOST = "test-app.playground.svc.cluster.local"
FAST_API_PORT = 3000
SLOW_API_PORT = 3000

@app.get("/fast")
async def fast_endpoint():
    with tracer.start_as_current_span("fast_operation"):
        print("Fast request started")
        conn = http.client.HTTPConnection(FAST_API_HOST, FAST_API_PORT)
        conn.request("GET", "/fast")
        print("API call to test service started")
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        conn.close()
        print("API call to test service ended")
        print("Fast request completed")
        return {"message": "Fast response"}

@app.get("/slow")
async def slow_endpoint():
    with tracer.start_as_current_span("slow_operation"):
        print("Slow request started")
        conn = http.client.HTTPConnection(SLOW_API_HOST, SLOW_API_PORT)
        conn.request("GET", "/slow")
        print("API call to test service started")
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        conn.close()
        print("API call to test service ended")
        time.sleep(random.uniform(1, 3))
        print("Slow request completed")
        return {"message": "Slow response"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
