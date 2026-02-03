from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from openinference.instrumentation.langchain import LangChainInstrumentor
import os

def setup_observability():
    """Configures OpenTelemetry and auto-instrumentation."""
    resource = Resource(attributes={
        "service.name": "finnie-agent"
    })

    trace_provider = TracerProvider(resource=resource)
    
    # Phoenix runs on port 4317 for OTLP gRPC by default
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    
    trace_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(trace_provider)
    
    # Auto-instrument LangChain
    LangChainInstrumentor().instrument(tracer_provider=trace_provider)
    
    return trace.get_tracer(__name__)
