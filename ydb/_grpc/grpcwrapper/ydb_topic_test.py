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

    assert msg_dict["path"] == params["path"]
    assert len(msg_dict["add_consumers"]) == len(params["add_consumers"])
    assert len(msg_dict["alter_consumers"]) == len(params["alter_consumers"])
    assert len(msg_dict["drop_consumers"]) == len(params["drop_consumers"])
    assert msg_dict["alter_attributes"] == params["alter_attributes"]

    assert (
        int(msg_dict["alter_partitioning_settings"]["set_min_active_partitions"]) == params["set_min_active_partitions"]
    )
    assert (
        int(msg_dict["alter_partitioning_settings"]["set_partition_count_limit"]) == params["set_partition_count_limit"]
    )

    assert int(msg_dict["set_partition_write_burst_bytes"]) == params["set_partition_write_burst_bytes"]
    assert (
        int(msg_dict["set_partition_write_speed_bytes_per_second"])
        == params["set_partition_write_speed_bytes_per_second"]
    )
    assert msg_dict["set_retention_period"] == str(int(params["set_retention_period"].total_seconds())) + "s"
    assert int(msg_dict["set_retention_storage_mb"]) == params["set_retention_storage_mb"]

    assert msg_dict["set_metering_mode"] == "METERING_MODE_RESERVED_CAPACITY"

    assert msg_dict["set_supported_codecs"]["codecs"] == params["set_supported_codecs"]
