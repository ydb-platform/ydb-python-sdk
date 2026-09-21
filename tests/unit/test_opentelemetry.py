# -*- coding: utf-8 -*-
import sys

import pytest

from ydb import opentelemetry as otel


def test_enable_tracing_dispatches_to_plugin(monkeypatch):
    calls = []
    monkeypatch.setattr("ydb.opentelemetry.plugin._enable_tracing", lambda tracer: calls.append(tracer))
    otel.enable_tracing("my-tracer")
    assert calls == ["my-tracer"]


def test_disable_tracing_dispatches_to_plugin(monkeypatch):
    calls = []
    monkeypatch.setattr("ydb.opentelemetry.plugin._disable_tracing", lambda: calls.append(True))
    otel.disable_tracing()
    assert calls == [True]


def test_enable_tracing_raises_when_plugin_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "ydb.opentelemetry.plugin", None)
    with pytest.raises(ImportError, match="OpenTelemetry packages are required"):
        otel.enable_tracing()


def test_disable_tracing_silent_when_plugin_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "ydb.opentelemetry.plugin", None)
    assert otel.disable_tracing() is None
