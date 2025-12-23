"""
OpenTelemetry configuration and setup for Application Insights.
Exports telemetry data to Azure Application Insights.
"""

import os
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from azure.monitor.opentelemetry.exporter import (
    AzureMonitorTraceExporter,
    AzureMonitorMetricExporter,
)


def setup_telemetry(service_name: str = "foundry-genai-demo") -> tuple[trace.Tracer, metrics.Meter]:
    """
    Initialize OpenTelemetry with Azure Application Insights exporters.
    
    Args:
        service_name: Name of the service for telemetry identification
        
    Returns:
        Tuple of (tracer, meter) for creating spans and metrics
        
    Environment Variables:
        APPLICATIONINSIGHTS_CONNECTION_STRING: Azure Application Insights connection string
    """
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not connection_string:
        print("Warning: APPLICATIONINSIGHTS_CONNECTION_STRING not set. Telemetry will not be exported.")
        # Set up basic providers without exporters for local development
        resource = Resource.create({SERVICE_NAME: service_name})
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)
        
        meter_provider = MeterProvider(resource=resource)
        metrics.set_meter_provider(meter_provider)
    else:
        # Configure resource with service name
        resource = Resource.create({SERVICE_NAME: service_name})
        
        # Set up tracing with Azure Monitor
        trace_exporter = AzureMonitorTraceExporter(connection_string=connection_string)
        trace_provider = TracerProvider(resource=resource)
        trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(trace_provider)
        
        # Set up metrics with Azure Monitor
        metric_exporter = AzureMonitorMetricExporter(connection_string=connection_string)
        metric_reader = PeriodicExportingMetricReader(metric_exporter)
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
    
    # Get tracer and meter for instrumentation
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)
    
    return tracer, meter


def add_event_metadata(span: trace.Span, event_name: str, **metadata):
    """
    Add a custom event to a span with metadata only (no sensitive data).
    
    Args:
        span: Active span to add event to
        event_name: Name of the event
        **metadata: Key-value pairs of metadata (should not include raw prompts/responses)
    """
    # Filter out any potentially sensitive fields
    safe_metadata = {
        k: v for k, v in metadata.items() 
        if k not in ['prompt', 'response', 'raw_text', 'content', 'message']
    }
    span.add_event(event_name, attributes=safe_metadata)


def set_span_metadata(span: trace.Span, **attributes):
    """
    Set metadata attributes on a span (metadata only, no sensitive data).
    
    Args:
        span: Span to set attributes on
        **attributes: Key-value pairs of metadata
    """
    # Filter out sensitive fields
    safe_attributes = {
        k: v for k, v in attributes.items()
        if k not in ['prompt', 'response', 'raw_text', 'content', 'message']
    }
    span.set_attributes(safe_attributes)
