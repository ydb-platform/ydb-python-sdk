# -*- coding: utf-8 -*-
import pytest

from ydb import tracing
from ydb.tracing import Tracer, TraceLevel, _TracingCtx, with_trace


class _FakeSpan:
    def __init__(self):
        self.tags = {}
        self._baggage = {}

    def set_tag(self, key, value):
        self.tags[key] = value

    def set_baggage_item(self, key, value):
        self._baggage[key] = value

    def get_baggage_item(self, key):
        return self._baggage.get(key)


class _FakeScope:
    def __init__(self, span):
        self.span = span
        self.closed = False

    def close(self):
        self.closed = True


class _FakeScopeManager:
    def __init__(self):
        self.active = None


class _FakeOpenTracer:
    """Minimal opentracing.Tracer stand-in for the interface tracing.py uses."""

    def __init__(self):
        self.scope_manager = _FakeScopeManager()
        self.started = []

    def start_active_span(self, name):
        scope = _FakeScope(_FakeSpan())
        self.scope_manager.active = scope
        self.started.append(name)
        return scope


def test_disabled_tracer_is_noop():
    tracer = Tracer(None)
    assert tracer.enabled is False

    ctx = tracer.trace("span")
    assert isinstance(ctx, _TracingCtx)
    with ctx as entered:
        assert entered is ctx
        assert entered.enabled is False
        entered.trace({"k": "v"})  # no active span, must not raise


def test_default_tracer_builder_composition():
    ft = _FakeOpenTracer()
    tracer = Tracer.default(ft)
    assert tracer.enabled is True
    assert tracer._pre_tags == {"started": True}
    assert tracer._post_tags_ok == {"ok": True}
    assert tracer._post_tags_err == {"ok": False}
    assert tracer._verbose_level == TraceLevel.INFO

    ret = tracer.with_pre_tags({"a": 1}).with_post_tags({"b": 2}, {"c": 3}).with_verbose_level(TraceLevel.DEBUG)
    assert ret is tracer
    assert tracer._pre_tags == {"a": 1}
    assert tracer._verbose_level == TraceLevel.DEBUG


def test_enabled_span_ok_path():
    ft = _FakeOpenTracer()
    tracer = Tracer.default(ft)

    with tracer.trace("myspan") as ctx:
        assert ctx.enabled is True
        assert ft.started == ["myspan"]
        scope = ft.scope_manager.active
        assert scope.span.get_baggage_item("ctx") is ctx
        assert scope.span.tags.get("started") is True  # pre-tags applied on enter
        ctx.trace({"custom": 1})
        assert scope.span.tags["custom"] == 1

    assert scope.span.tags.get("ok") is True  # post-ok tags applied on exit
    assert scope.closed is True


def test_enabled_span_error_path_runs_callback():
    ft = _FakeOpenTracer()
    tracer = Tracer.default(ft).with_verbose_level(TraceLevel.NONE)  # let ERROR-level traces through

    with pytest.raises(RuntimeError):
        with tracer.trace("s"):
            scope = ft.scope_manager.active
            raise RuntimeError("boom")

    assert scope.span.tags.get("ok") is False  # post-err tags applied
    assert scope.span.tags.get("error.type") == "RuntimeError"  # from _default_on_error_callback
    assert scope.closed is True


def test_trace_respects_verbose_level():
    ft = _FakeOpenTracer()
    tracer = Tracer(ft).with_verbose_level(TraceLevel.INFO)

    with tracer.trace("s") as ctx:
        scope = ft.scope_manager.active
        ctx.trace({"skipped": 1}, trace_level=TraceLevel.ERROR)  # ERROR > INFO threshold -> skipped
        assert "skipped" not in scope.span.tags
        ctx.trace({"kept": 1}, trace_level=TraceLevel.INFO)
        assert scope.span.tags["kept"] == 1


def test_trace_without_active_scope_is_noop():
    ft = _FakeOpenTracer()
    ctx = Tracer.default(ft).trace("s")  # created but not entered -> no scope
    ctx.trace({"k": 1})  # enabled but scope is None -> early return, no raise


def test_module_trace_disabled_returns_none():
    assert tracing.trace(Tracer(None), {"k": 1}) is None


def test_module_trace_no_active_scope_returns_false():
    ft = _FakeOpenTracer()
    assert tracing.trace(Tracer.default(ft), {"k": 1}) is False


def test_module_trace_active_scope_without_ctx_returns_false():
    ft = _FakeOpenTracer()
    ft.scope_manager.active = _FakeScope(_FakeSpan())  # no "ctx" baggage
    assert tracing.trace(Tracer.default(ft), {"k": 1}) is False


def test_module_trace_with_ctx_applies_tags():
    ft = _FakeOpenTracer()
    tracer = Tracer.default(ft)
    with tracer.trace("s"):
        assert tracing.trace(tracer, {"applied": 1}) is None
        assert ft.scope_manager.active.span.tags["applied"] == 1


def test_with_trace_decorator_default_and_custom_name():
    ft = _FakeOpenTracer()

    class Service:
        def __init__(self):
            self.tracer = Tracer.default(ft)

        @with_trace()
        def do(self, value):
            return value * 2

        @with_trace("custom.span")
        def do_named(self):
            return "ok"

    service = Service()
    assert service.do(3) == 6
    assert ft.started[-1] == "Service.do"
    assert service.do_named() == "ok"
    assert ft.started[-1] == "custom.span"
