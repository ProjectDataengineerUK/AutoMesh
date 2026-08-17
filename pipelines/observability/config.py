"""Observability environment configuration."""

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ObservabilityConfig:
    service_name: str
    otlp_endpoint: str | None
    environment: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "ObservabilityConfig":
        values = os.environ if environ is None else environ
        service_name = values.get("OTEL_SERVICE_NAME", "automesh")
        if not service_name.strip():
            raise ValueError("OTEL_SERVICE_NAME cannot be blank")
        endpoint = values.get("OTEL_EXPORTER_OTLP_ENDPOINT") or None
        if endpoint is not None and not endpoint.startswith(("http://", "https://")):
            raise ValueError("OTLP endpoint must use http or https")
        return cls(service_name=service_name, otlp_endpoint=endpoint, environment=values.get("AUTOMESH_ENV", "local"))
