"""Tests for the OpenTelemetry setup in spacelaunchnow.telemetry."""

import importlib
import os
from unittest import mock

from django.test import TestCase, override_settings

from spacelaunchnow import telemetry

OTEL_ENV_NAMES = ("OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_SERVICE_NAME", "OTEL_TRACES_SAMPLER_RATIO")


class TelemetryOffTests(TestCase):
    def setUp(self):
        telemetry._initialized = False
        self.addCleanup(setattr, telemetry, "_initialized", False)

    @override_settings(OTEL_EXPORTER_OTLP_ENDPOINT="")
    def test_empty_endpoint_returns_false_and_sets_no_provider(self):
        with mock.patch("opentelemetry.trace.set_tracer_provider") as set_provider:
            self.assertFalse(telemetry.init_telemetry())
        set_provider.assert_not_called()
        self.assertFalse(telemetry._initialized)

    def test_default_settings_have_tracing_off(self):
        from django.conf import settings

        with mock.patch.dict(os.environ):
            for name in OTEL_ENV_NAMES:
                os.environ.pop(name, None)
            self.assertEqual(self._reloaded_values(), ("", "spacelaunchnow-server", 0.05))
        self.assertEqual(settings.OTEL_EXPORTER_OTLP_ENDPOINT, "")
        self.assertFalse(telemetry.init_telemetry())

    def test_settings_read_the_environment(self):
        env = {
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://tempo.example:4317",
            "OTEL_SERVICE_NAME": "sln-test",
            "OTEL_TRACES_SAMPLER_RATIO": "0.5",
        }
        with mock.patch.dict(os.environ, env):
            self.assertEqual(self._reloaded_values(), ("http://tempo.example:4317", "sln-test", 0.5))

    def _reloaded_values(self):
        """Reload the settings module, read the OTEL values, then reload it back."""
        import spacelaunchnow.settings as settings_module

        try:
            module = importlib.reload(settings_module)
            return (
                module.OTEL_EXPORTER_OTLP_ENDPOINT,
                module.OTEL_SERVICE_NAME,
                module.OTEL_TRACES_SAMPLER_RATIO,
            )
        finally:
            self.addCleanup(importlib.reload, settings_module)


@override_settings(
    OTEL_EXPORTER_OTLP_ENDPOINT="http://tempo.example:4317",
    OTEL_SERVICE_NAME="sln-test",
    OTEL_TRACES_SAMPLER_RATIO=0.25,
    SLN_ENVIRONMENT="testing",
)
class TelemetryOnTests(TestCase):
    def setUp(self):
        telemetry._initialized = False
        self.addCleanup(setattr, telemetry, "_initialized", False)

        # Nothing here may reach the network or change global OpenTelemetry state.
        patches = {
            "exporter": mock.patch("opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter"),
            "processor": mock.patch("opentelemetry.sdk.trace.export.BatchSpanProcessor"),
            "set_provider": mock.patch("opentelemetry.trace.set_tracer_provider"),
            "django": mock.patch("opentelemetry.instrumentation.django.DjangoInstrumentor.instrument"),
            "psycopg": mock.patch("opentelemetry.instrumentation.psycopg.PsycopgInstrumentor.instrument"),
        }
        self.mocks = {}
        for name, patcher in patches.items():
            self.mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)

    def test_init_builds_provider_and_instruments(self):
        self.assertTrue(telemetry.init_telemetry())

        self.mocks["exporter"].assert_called_once_with(endpoint="http://tempo.example:4317", insecure=True)
        self.mocks["django"].assert_called_once()
        self.mocks["psycopg"].assert_called_once()

        provider = self.mocks["set_provider"].call_args.args[0]
        attrs = provider.resource.attributes
        self.assertEqual(attrs["service.name"], "sln-test")
        self.assertEqual(attrs["deployment.environment"], "testing")
        description = provider.sampler.get_description()
        self.assertIn("ParentBased", description)
        self.assertIn("TraceIdRatioBased{0.25}", description)

    def test_init_twice_sets_up_once(self):
        self.assertTrue(telemetry.init_telemetry())
        self.assertFalse(telemetry.init_telemetry())

        self.mocks["set_provider"].assert_called_once()
        self.mocks["django"].assert_called_once()
        self.mocks["psycopg"].assert_called_once()

    def test_failure_logs_a_warning_and_does_not_raise(self):
        self.mocks["django"].side_effect = RuntimeError("boom")

        with self.assertLogs("spacelaunchnow.telemetry", level="WARNING"):
            self.assertFalse(telemetry.init_telemetry())
        self.assertFalse(telemetry._initialized)
