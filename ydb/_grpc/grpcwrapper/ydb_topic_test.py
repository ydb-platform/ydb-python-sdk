import datetime

from google.protobuf.json_format import MessageToDict

from ydb._grpc.grpcwrapper.ydb_topic import OffsetsRange
from .ydb_topic import AlterTopicRequest
from .ydb_topic_public_types import (
    AlterTopicRequestParams,
    PublicAlterConsumer,
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
        "set_partition_count_limit": 4,
    }

    params_public = AlterTopicRequestParams(**params)
    request = AlterTopicRequest.from_public(params_public)
    request_proto = request.to_proto()

    msg_dict = MessageToDict(request_proto, preserving_proto_field_name=True)

    expected_dict = {
        "path": "topic_name",
        "alter_partitioning_settings": {"set_min_active_partitions": "2", "set_partition_count_limit": "4"},
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
