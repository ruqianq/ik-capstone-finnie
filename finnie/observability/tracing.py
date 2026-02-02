"""Observability module with OpenTelemetry and Phoenix integration."""

import logging
import uuid
from typing import Optional, Any, Dict
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from finnie.config import config

# Set up logging
logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)


class ObservabilityManager:
    """Manages OpenTelemetry tracing and Phoenix integration."""
    
    def __init__(self):
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize OpenTelemetry tracing."""
        if self._initialized:
            return
        
        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": config.app_name,
                "service.version": config.app_version,
            })
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            
            # Configure OTLP exporter to Phoenix
            if config.observability.enable_tracing:
                otlp_exporter = OTLPSpanExporter(
                    endpoint=config.observability.otel_endpoint,
                    insecure=True,
                )
                span_processor = BatchSpanProcessor(otlp_exporter)
                self.tracer_provider.add_span_processor(span_processor)
            
            # Set as global tracer provider
            trace.set_tracer_provider(self.tracer_provider)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            self._initialized = True
            logger.info("Observability initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize observability: {e}")
            # Create a no-op tracer as fallback
            self.tracer = trace.get_tracer(__name__)
    
    def get_tracer(self) -> trace.Tracer:
        """Get the tracer instance."""
        if not self._initialized:
            self.initialize()
        return self.tracer
    
    @contextmanager
    def trace_operation(self, operation_name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing an operation."""
        tracer = self.get_tracer()
        with tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            
            # Generate trace ID for this operation
            trace_id = format(span.get_span_context().trace_id, '032x')
            span.set_attribute("trace_id", trace_id)
            
            try:
                yield span, trace_id
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                raise


# Global observability manager
observability = ObservabilityManager()


def get_trace_id() -> str:
    """Generate a new trace ID."""
    return str(uuid.uuid4())


def log_with_trace(message: str, trace_id: Optional[str] = None, level: str = "info"):
    """Log a message with trace ID."""
    log_message = f"[TraceID: {trace_id}] {message}" if trace_id else message
    getattr(logger, level)(log_message)
