"""Phoenix observability integration for FinnIE."""
import os
import structlog
from typing import Optional
from phoenix.otel import register


logger = structlog.get_logger(__name__)


class PhoenixObservability:
    """Phoenix observability integration."""
    
    def __init__(self, endpoint: Optional[str] = None, enable_tracing: bool = True):
        """Initialize Phoenix observability.
        
        Args:
            endpoint: Phoenix collector endpoint
            enable_tracing: Whether to enable tracing
        """
        self.endpoint = endpoint or os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
        self.enable_tracing = enable_tracing
        self._initialized = False
        
    def setup(self) -> None:
        """Set up Phoenix tracing and observability."""
        if not self.enable_tracing or self._initialized:
            return
            
        try:
            # Register Phoenix OTEL tracer
            tracer_provider = register(
                project_name="finnie",
                endpoint=self.endpoint,
            )
            
            self._initialized = True
            logger.info("Phoenix observability initialized", endpoint=self.endpoint)
        except Exception as e:
            logger.error("Failed to initialize Phoenix observability", error=str(e))
            # Don't fail the application if observability setup fails
            
    def is_initialized(self) -> bool:
        """Check if observability is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
