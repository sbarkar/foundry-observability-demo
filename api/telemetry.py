"""
OpenTelemetry instrumentation configuration for Application Insights.
"""
import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

logger = logging.getLogger(__name__)

# Sensitive field names that should never be logged
SENSITIVE_FIELDS = ['content', 'message', 'query', 'text']


def initialize_telemetry():
    """
    Initialize OpenTelemetry instrumentation with Azure Monitor.
    Should be called once at application startup.
    """
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not connection_string or "00000000-0000-0000-0000-000000000000" in connection_string:
        logger.warning("Application Insights not configured, telemetry will not be sent")
        # Set up basic tracer provider for local development
        trace.set_tracer_provider(TracerProvider())
        return
    
    try:
        # Try to import and configure Azure Monitor with OpenTelemetry
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor(connection_string=connection_string)
        logger.info("OpenTelemetry initialized with Application Insights")
    except ImportError:
        logger.warning("Azure Monitor OpenTelemetry package not available, using basic tracer")
        trace.set_tracer_provider(TracerProvider())
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        # Fallback to basic tracer
        trace.set_tracer_provider(TracerProvider())


def get_tracer(name: str):
    """Get a tracer instance for creating spans."""
    return trace.get_tracer(name)


def add_span_attributes(span, attributes: dict):
    """Add custom attributes to the current span."""
    if span and span.is_recording():
        for key, value in attributes.items():
            # Only log metadata, never user content
            if value and not any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
                span.set_attribute(key, value)
