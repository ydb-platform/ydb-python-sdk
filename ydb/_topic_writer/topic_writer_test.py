from typing import List

import pytest

from .topic_writer import _split_messages_by_size


@pytest.mark.parametrize(
    "messages,split_size,expected",
    [
        (
            [1, 2, 3],
            0,
            [[1], [2], [3]],
        ),
        (
            [1, 2, 3],
            1,
            [[1], [2], [3]],
        ),
        (
            [1, 2, 3],
            3,
            [[1, 2], [3]],
        ),
        (
            [1, 2, 3],
            100,
            [[1, 2, 3]],
        ),
        (
            [100, 2, 3],
            100,
            [[100], [2, 3]],
        ),
        (
            [],
            100,
            [],
        ),
        (
            [],
            100,
            [],
        ),
    ],
)
def test_split_messages_by_size(messages: List[int], split_size: int, expected: List[List[int]]):
    res = _split_messages_by_size(messages, split_size, lambda x: x)  # noqa
    assert res == expected
