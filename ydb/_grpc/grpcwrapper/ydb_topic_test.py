import datetime

from google.protobuf.json_format import MessageToDict

# Same version dispatch the module under test uses: the CI matrix runs protobuf v3..v6.
from ydb._grpc.common.protos import ydb_topic_pb2

from ydb._grpc.grpcwrapper.ydb_topic import OffsetsRange
from .ydb_topic import AlterTopicRequest, DescribeTopicResult
from .ydb_topic_public_types import (
    AlterTopicRequestParams,
    PublicAlterConsumer,
    PublicAlterAutoPartitioningSettings,
    PublicAutoPartitioningStrategy,
    PublicConsumer,
    PublicCodec,
)


def test_offsets_range_intersected():
    # not intersected
    for test in [(0, 1, 1, 2), (1, 2, 3, 5)]:
        assert not OffsetsRange(test[0], test[1]).is_intersected_with(OffsetsRange(test[2], test[3]))
        assert not OffsetsRange(test[2], test[3]).is_intersected_with(OffsetsRange(test[0], test[1]))

    # intersected
    for test in [
        (1, 2, 1, 2),
        (1, 10, 1, 2),
        (1, 10, 2, 3),
        (1, 10, 5, 15),
        (10, 20, 5, 15),
    ]:
        assert OffsetsRange(test[0], test[1]).is_intersected_with(OffsetsRange(test[2], test[3]))
        assert OffsetsRange(test[2], test[3]).is_intersected_with(OffsetsRange(test[0], test[1]))


def test_alter_topic_request_from_public_to_proto():
    # Specify all fields with all possible input ways
    params = {
        "path": "topic_name",
        "add_consumers": [
            "new_consumer_1",
            PublicConsumer("new_consumer_2"),
        ],
        "alter_consumers": [
            "old_consumer_1",
            PublicAlterConsumer("old_consumer_2"),
        ],
        "drop_consumers": ["redundant_consumer"],
        "set_retention_period": datetime.timedelta(weeks=4),
        "set_retention_storage_mb": 4,
        "set_supported_codecs": [1, PublicCodec(2)],
        "set_partition_write_burst_bytes": 8,
        "set_partition_write_speed_bytes_per_second": 15,
        "alter_attributes": {"key": "value"},
        "set_metering_mode": 1,
        "set_min_active_partitions": 2,
        "set_max_active_partitions": 8,
        "set_partition_count_limit": 10,
        "alter_auto_partitioning_settings": PublicAlterAutoPartitioningSettings(
            set_strategy=PublicAutoPartitioningStrategy.DISABLED,
        ),
    }

    params_public = AlterTopicRequestParams(**params)
    request = AlterTopicRequest.from_public(params_public)
    request_proto = request.to_proto()

    msg_dict = MessageToDict(request_proto, preserving_proto_field_name=True)

    expected_dict = {
        "path": "topic_name",
        "alter_partitioning_settings": {
            "set_min_active_partitions": "2",
            "set_max_active_partitions": "8",
            "set_partition_count_limit": "10",
            "alter_auto_partitioning_settings": {
                "set_strategy": "AUTO_PARTITIONING_STRATEGY_DISABLED",
                "set_partition_write_speed": {},
            },
        },
        "set_retention_period": "2419200s",
        "set_retention_storage_mb": "4",
        "set_supported_codecs": {"codecs": [1, 2]},
        "set_partition_write_speed_bytes_per_second": "15",
        "set_partition_write_burst_bytes": "8",
        "alter_attributes": {"key": "value"},
        "add_consumers": [
            {"name": "new_consumer_1", "supported_codecs": {}},
            {"name": "new_consumer_2", "supported_codecs": {}},
        ],
        "drop_consumers": ["redundant_consumer"],
        "alter_consumers": [
            {"name": "old_consumer_1"},
            {"name": "old_consumer_2"},
        ],
        "set_metering_mode": "METERING_MODE_RESERVED_CAPACITY",
    }

    assert msg_dict == expected_dict


def test_partition_key_range_round_trip():
    """A bounded partition must survive proto -> internal -> public unchanged.

    The multi-partition writer routes by these bounds, and an empty bound is meaningful (it
    marks an open end of the key space), so it has to stay distinguishable from an absent one.
    """
    msg = ydb_topic_pb2.DescribeTopicResult.PartitionInfo(
        partition_id=7,
        active=True,
        child_partition_ids=[8, 9],
        parent_partition_ids=[3],
        key_range=ydb_topic_pb2.PartitionKeyRange(from_bound=b"\x10", to_bound=b"\x80"),
    )

    internal = DescribeTopicResult.PartitionInfo.from_proto(msg)
    assert internal.key_range.from_bound == b"\x10"
    assert internal.key_range.to_bound == b"\x80"

    public = internal.to_public()
    assert public.partition_id == 7
    assert public.child_partition_ids == [8, 9]
    assert public.parent_partition_ids == [3]
    assert public.key_range.from_bound == b"\x10"
    assert public.key_range.to_bound == b"\x80"


def test_partition_without_key_range_stays_none():
    """Topics that are not auto-partitioned report no range at all.

    That is not the same as an open range: it is what tells the writer to route by hash
    instead of by bounds, so it must not be turned into empty bounds along the way.
    """
    msg = ydb_topic_pb2.DescribeTopicResult.PartitionInfo(partition_id=0, active=True)

    internal = DescribeTopicResult.PartitionInfo.from_proto(msg)
    assert internal.key_range is None
    assert internal.to_public().key_range is None

    assert DescribeTopicResult.PartitionKeyRange.from_proto(None) is None
