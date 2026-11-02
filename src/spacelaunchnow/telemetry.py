"""OpenTelemetry trace setup for the Django server.

``init_telemetry`` is called once per gunicorn worker from ``wsgi.py``. With no
``OTEL_EXPORTER_OTLP_ENDPOINT`` it does nothing: it imports no OpenTelemetry
module and opens no connection. Any failure logs a warning and never stops
startup.
"""

import logging

logger = logging.getLogger(__name__)

_initialized = False


def _read_settings():
    """Return (endpoint, service_name, ratio, environment) from Django settings."""
    from django.conf import settings

    return (
        getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "") or "",
        getattr(settings, "OTEL_SERVICE_NAME", "spacelaunchnow-server"),
        getattr(settings, "OTEL_TRACES_SAMPLER_RATIO", 0.05),
        getattr(settings, "SLN_ENVIRONMENT", "development"),
    )


def init_telemetry():
    """Set up tracing. Return True if it started, False if it is off or failed."""
    global _initialized
    if _initialized:
        return False

    try:
        endpoint, service_name, ratio, environment = _read_settings()
        if not endpoint:
            return False

        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

        resource = Resource.create(
            {
                "service.name": service_name,
                "deployment.environment": environment,
            }
        )
        provider = TracerProvider(
            resource=resource,
            sampler=ParentBased(TraceIdRatioBased(ratio)),
        )
        # The collector is in-cluster (tempo...:4317), so no TLS.
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        DjangoInstrumentor().instrument()
        PsycopgInstrumentor().instrument()
    except Exception:
        logger.warning("OpenTelemetry setup failed; tracing is off", exc_info=True)
        return False

    _initialized = True
    logger.info("OpenTelemetry tracing on: service=%s ratio=%s", service_name, ratio)
    return True
