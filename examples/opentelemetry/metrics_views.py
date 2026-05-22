"""OpenTelemetry metric views for the YDB Python SDK examples."""

from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View

DURATION_BUCKETS_SECONDS = (
    0.0005,
    0.001,
    0.0025,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
)

ATTEMPT_BUCKETS = (1, 2, 3, 5, 10)


def ydb_metrics_views():
    return [
        View(
            instrument_name="db.client.operation.duration",
            aggregation=ExplicitBucketHistogramAggregation(boundaries=DURATION_BUCKETS_SECONDS),
        ),
        View(
            instrument_name="ydb.query.session.create_time",
            aggregation=ExplicitBucketHistogramAggregation(boundaries=DURATION_BUCKETS_SECONDS),
        ),
        View(
            instrument_name="ydb.client.retry.duration",
            aggregation=ExplicitBucketHistogramAggregation(boundaries=DURATION_BUCKETS_SECONDS),
        ),
        View(
            instrument_name="ydb.client.retry.attempts",
            aggregation=ExplicitBucketHistogramAggregation(boundaries=ATTEMPT_BUCKETS),
        ),
    ]
