from ydb._grpc.grpcwrapper.ydb_topic import OffsetsRange


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
