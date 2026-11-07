"""Verify that every YDB Python SDK metric reached Prometheus."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class MetricCheck:
    description: str
    prometheus_name: str
    promql: str = ""
    requires_error_probe: bool = False


LOOKBACK = "10m"


def _prometheus_label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _selector(**labels: str) -> str:
    return "{%s}" % ",".join('%s="%s"' % (name, _prometheus_label_value(value)) for name, value in labels.items())


def _present(prometheus_name: str, selector: str) -> str:
    return "count(count_over_time(%s%s[%s])) > 0" % (prometheus_name, selector, LOOKBACK)


def _positive(prometheus_name: str, selector: str) -> str:
    return "max(max_over_time(%s%s[%s])) > 0" % (prometheus_name, selector, LOOKBACK)


def _metric_checks(service_instance_id: str) -> Tuple[MetricCheck, ...]:
    run = _selector(service_instance_id=service_instance_id)
    error_probe = _selector(
        service_instance_id=service_instance_id,
        reader_name="load-tank-topic-error-probe",
        retry_decision="stop",
        status_code="SCHEME_ERROR",
    )
    return (
        MetricCheck(
            "client operation duration",
            "ydb_client_operation_duration_seconds_count",
            _positive("ydb_client_operation_duration_seconds_count", run),
        ),
        MetricCheck(
            "failed client operations",
            "ydb_client_operation_failed_total",
            _positive("ydb_client_operation_failed_total", run),
        ),
        MetricCheck("query session count", "ydb_query_session_count", _present("ydb_query_session_count", run)),
        MetricCheck(
            "closed query sessions",
            "ydb_query_session_closed_total",
            _positive("ydb_query_session_closed_total", run),
        ),
        MetricCheck(
            "query session create time",
            "ydb_query_session_create_time_seconds_count",
            _positive("ydb_query_session_create_time_seconds_count", run),
        ),
        MetricCheck(
            "pending query session requests",
            "ydb_query_session_pending_requests",
            _positive("ydb_query_session_pending_requests", run),
        ),
        MetricCheck(
            "query session acquire timeouts",
            "ydb_query_session_timeouts_total",
            _positive("ydb_query_session_timeouts_total", run),
        ),
        MetricCheck("query session maximum", "ydb_query_session_max", _positive("ydb_query_session_max", run)),
        MetricCheck("query session minimum", "ydb_query_session_min", _present("ydb_query_session_min", run)),
        MetricCheck(
            "retry attempts above one",
            "ydb_client_retry_attempts_count",
            "max(max_over_time(ydb_client_retry_attempts_sum%s[%s]) "
            "- max_over_time(ydb_client_retry_attempts_count%s[%s])) > 0" % (run, LOOKBACK, run, LOOKBACK),
        ),
        MetricCheck(
            "retry duration",
            "ydb_client_retry_duration_seconds_count",
            _positive("ydb_client_retry_duration_seconds_count", run),
        ),
        MetricCheck(
            "topic messages received",
            "ydb_topic_reader_received_messages_total",
            _positive("ydb_topic_reader_received_messages_total", run),
        ),
        MetricCheck(
            "topic bytes received",
            "ydb_topic_reader_received_bytes_total",
            _positive("ydb_topic_reader_received_bytes_total", run),
        ),
        MetricCheck(
            "topic messages delivered",
            "ydb_topic_reader_delivered_messages_total",
            _positive("ydb_topic_reader_delivered_messages_total", run),
        ),
        MetricCheck(
            "topic message decompression duration",
            "ydb_topic_reader_compression_duration_seconds_count",
            _positive("ydb_topic_reader_compression_duration_seconds_count", run),
        ),
        MetricCheck(
            "topic message processing duration",
            "ydb_topic_reader_message_processing_duration_seconds_count",
            _positive("ydb_topic_reader_message_processing_duration_seconds_count", run),
        ),
        MetricCheck(
            "topic commit ranges queued",
            "ydb_topic_reader_commit_queued_total",
            _positive("ydb_topic_reader_commit_queued_total", run),
        ),
        MetricCheck(
            "topic commit ranges acknowledged",
            "ydb_topic_reader_commit_acknowledged_total",
            _positive("ydb_topic_reader_commit_acknowledged_total", run),
        ),
        MetricCheck(
            "topic commit offset lag",
            "ydb_topic_reader_commit_offset_lag_max",
            _present("ydb_topic_reader_commit_offset_lag_max", run),
        ),
        MetricCheck(
            "topic reader session errors",
            "ydb_topic_reader_session_errors_total",
            _positive("ydb_topic_reader_session_errors_total", error_probe),
            requires_error_probe=True,
        ),
        MetricCheck(
            "topic reader credit balance",
            "ydb_topic_reader_credit_balance_bytes",
            _positive("ydb_topic_reader_credit_balance_bytes", run),
        ),
        MetricCheck(
            "topic reader local buffer",
            "ydb_topic_reader_local_buffer_messages",
            _positive("ydb_topic_reader_local_buffer_messages", run),
        ),
        MetricCheck(
            "oldest buffered topic message age",
            "ydb_topic_reader_local_buffer_message_age_max_seconds",
            _positive("ydb_topic_reader_local_buffer_message_age_max_seconds", run),
        ),
        MetricCheck(
            "topic partition sessions",
            "ydb_topic_reader_partition_session_count",
            _positive("ydb_topic_reader_partition_session_count", run),
        ),
    )


def _prometheus_query_has_result(prometheus_url: str, promql: str, timeout: float = 5) -> bool:
    query = urllib.parse.urlencode({"query": promql})
    url = "%s/api/v1/query?%s" % (prometheus_url.rstrip("/"), query)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = json.load(response)
    return payload.get("status") == "success" and bool(payload.get("data", {}).get("result"))


def _prometheus_has_series(prometheus_url: str, prometheus_name: str) -> bool:
    return _prometheus_query_has_result(prometheus_url, "count(%s)" % prometheus_name)


def wait_for_metrics(
    prometheus_url: str,
    checks: Iterable[MetricCheck],
    timeout: float,
    poll_interval: float,
) -> Dict[str, MetricCheck]:
    missing = {check.prometheus_name: check for check in checks}
    deadline = time.monotonic() + timeout

    while missing and time.monotonic() < deadline:
        for prometheus_name in tuple(missing):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                check = missing[prometheus_name]
                if _prometheus_query_has_result(
                    prometheus_url,
                    check.promql or "count(%s)" % prometheus_name,
                    timeout=min(5, remaining),
                ):
                    check = missing.pop(prometheus_name)
                    print("[ok] %s: %s" % (check.description, check.prometheus_name))
            except (OSError, ValueError, json.JSONDecodeError):
                pass

        if missing:
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(poll_interval, remaining))

    return missing


def _read_run_id_file(path: str, timeout: float, poll_interval: float) -> str:
    deadline = time.monotonic() + timeout
    while True:
        try:
            run_id = Path(path).read_text(encoding="utf-8").strip()
            if run_id:
                return run_id
        except OSError:
            pass

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("Run id was not published to %s" % path)
        time.sleep(min(poll_interval, remaining))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prometheus-url",
        default=os.environ.get("PROMETHEUS_URL", "http://localhost:9090"),
    )
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--poll-interval", type=float, default=2)
    parser.add_argument(
        "--service-instance-id",
        default=os.environ.get("METRICS_SERVICE_INSTANCE_ID", ""),
        help="service.instance.id of the load generator run to verify",
    )
    parser.add_argument(
        "--run-id-file",
        default=os.environ.get("METRICS_RUN_ID_FILE", ""),
        help="file from which to read the current load generator run id",
    )
    parser.add_argument(
        "--require-error-probe",
        action="store_true",
        default=os.environ.get("REQUIRE_TOPIC_ERROR_PROBE", "").lower() in {"1", "true", "yes"},
        help="also require ydb.topic.reader.session.errors",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    started_at = time.monotonic()
    if not args.service_instance_id and not args.run_id_file:
        print("Specify --service-instance-id or --run-id-file to select the load generator run.")
        return 2

    try:
        service_instance_id = args.service_instance_id or _read_run_id_file(
            args.run_id_file,
            args.timeout,
            args.poll_interval,
        )
    except RuntimeError as error:
        print("Cannot select the load generator run: %s" % error)
        return 2

    checks = tuple(
        check
        for check in _metric_checks(service_instance_id)
        if args.require_error_probe or not check.requires_error_probe
    )
    remaining_timeout = max(0, args.timeout - (time.monotonic() - started_at))
    print("Checking metrics for service.instance.id=%s" % service_instance_id)
    missing = wait_for_metrics(
        args.prometheus_url,
        checks,
        timeout=remaining_timeout,
        poll_interval=args.poll_interval,
    )
    if not missing:
        print("All %s expected SDK metrics are present in Prometheus." % len(checks))
        return 0

    print("Missing SDK metrics after %ss:" % args.timeout)
    for check in missing.values():
        print("[missing] %s: %s" % (check.description, check.prometheus_name))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
