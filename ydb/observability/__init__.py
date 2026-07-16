"""Vendor-neutral observability entrypoints for the YDB SDK.

Users pick a tracing backend and register it here:

.. code-block:: python

    from ydb.observability import enable_tracing
    from ydb.opentelemetry import OtelTracingProvider

    enable_tracing(OtelTracingProvider())  # or any custom TracingProvider

The SDK itself never imports ``opentelemetry`` — until a provider is enabled,
every span is a :class:`~ydb.observability.tracing.NoopSpan`.
"""

from typing import Optional

from ydb.observability.tracing import (
    NoopSpan,
    NoopTracingProvider,
    Span,
    SpanName,
    TracingProvider,
    _registry,
)


def enable_tracing(provider: TracingProvider) -> None:
    """Install *provider* as the active tracing backend.

    Calling this a second time replaces the previous provider — the old one
    stops receiving spans immediately. To turn tracing off again call
    :func:`disable_tracing`.
    """
    _registry.set_provider(provider)


def disable_tracing() -> None:
    """Reset the tracing backend to Noop.

    After this, :func:`enable_tracing` can be called again with any provider.
    """
    _registry.set_provider(None)


def get_active_provider() -> Optional[TracingProvider]:
    """Return the currently installed provider, or ``None`` if tracing is disabled."""
    return _registry.get_provider() if _registry.is_active() else None


__all__ = [
    "NoopSpan",
    "NoopTracingProvider",
    "Span",
    "SpanName",
    "TracingProvider",
    "disable_tracing",
    "enable_tracing",
    "get_active_provider",
]
