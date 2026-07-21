import abc
import bisect
from typing import Callable, List, Tuple

from .topic_writer import PublicMessage
from .._grpc.grpcwrapper.ydb_topic_public_types import PublicDescribeTopicResult

_MASK32 = 0xFFFFFFFF
_MASK64 = 0xFFFFFFFFFFFFFFFF

# Metadata key the server uses to validate bound-based partition selection.
PARTITION_KEY_METADATA_KEY = "__partition_key"

PartitionInfo = PublicDescribeTopicResult.PartitionInfo


def murmur2_32(data: bytes, seed: int = 0) -> int:
    """MurmurHash2, 32-bit, little-endian. Matches the Kafka BuiltInPartitioner
    and the YDB Go SDK ``xhash.Murmur2Hash32``."""
    m = 0x5BD1E995
    r = 24
    n = len(data)
    h = (seed ^ n) & _MASK32

    body = n - (n % 4)
    for i in range(0, body, 4):
        k = int.from_bytes(data[i : i + 4], "little")
        k = (k * m) & _MASK32
        k ^= k >> r
        k = (k * m) & _MASK32
        h = (h * m) & _MASK32
        h ^= k

    rem = n % 4
    if rem:
        tail = data[body:]
        if rem >= 3:
            h ^= tail[2] << 16
        if rem >= 2:
            h ^= tail[1] << 8
        h ^= tail[0]
        h = (h * m) & _MASK32

    h ^= h >> 13
    h = (h * m) & _MASK32
    h ^= h >> 15
    return h & _MASK32


def murmur64a(data: bytes, seed: int = 0) -> int:
    """MurmurHash64A, 64-bit, little-endian. Matches the YDB Go SDK
    ``xhash.Murmur2Hash64A`` and the C++ default partitioning key hasher."""
    m = 0xC6A4A7935BD1E995
    r = 47
    n = len(data)
    h = (seed ^ ((n * m) & _MASK64)) & _MASK64

    body = n - (n % 8)
    for i in range(0, body, 8):
        k = int.from_bytes(data[i : i + 8], "little")
        k = (k * m) & _MASK64
        k ^= k >> r
        k = (k * m) & _MASK64
        h ^= k
        h = (h * m) & _MASK64

    rem = n % 8
    if rem:
        tail = data[body:]
        for j in range(rem - 1, -1, -1):
            h ^= tail[j] << (8 * j)
        h = (h * m) & _MASK64

    h ^= h >> r
    h = (h * m) & _MASK64
    h ^= h >> r
    return h & _MASK64


def default_bound_key_hasher(key: str) -> bytes:
    """Hash a routing key the way the YDB server expects for bound-based
    partition selection: MurmurHash64A(seed=0) as 8 big-endian bytes."""
    return murmur64a(key.encode("utf-8"), 0).to_bytes(8, "big")


class PublicPartitionChooser(abc.ABC):
    """Maps a message to a target partition id and tracks the live partition set."""

    @abc.abstractmethod
    def choose_partition(self, message: PublicMessage) -> int: ...

    @abc.abstractmethod
    def add_partitions(self, partitions: List[PartitionInfo]) -> None: ...

    @abc.abstractmethod
    def remove_partition(self, partition_id: int) -> None: ...


class PublicPartitionByKeyKafka(PublicPartitionChooser):
    """Kafka-compatible routing: ``murmur2_32(key) % partitions_count``.

    Ignores server key ranges, so it fits topics with a fixed partition count.
    """

    def __init__(self):
        self._partitions: List[int] = []

    def add_partitions(self, partitions: List[PartitionInfo]) -> None:
        for p in partitions:
            kr = p.key_range
            if kr is not None and (kr.from_bound or kr.to_bound):
                raise ValueError("PublicPartitionByKeyKafka does not support partition key ranges")
            self._partitions.append(p.partition_id)
        self._partitions.sort()

    def remove_partition(self, partition_id: int) -> None:
        self._partitions = [p for p in self._partitions if p != partition_id]

    def choose_partition(self, message: PublicMessage) -> int:
        if not self._partitions:
            raise ValueError("no partitions configured for partition chooser")
        # Apache Kafka's DefaultPartitioner applies toPositive() (mask the sign bit) to the
        # murmur2 hash before the modulo; match it so the same key lands on the same partition.
        h = murmur2_32((message.key or "").encode("utf-8"), 0) & 0x7FFFFFFF
        return self._partitions[h % len(self._partitions)]


class PublicPartitionByKeyBound(PublicPartitionChooser):
    """Server-accurate routing: hashes the key and selects the partition whose
    ``[from_bound, to_bound)`` key range owns it. Mirrors YDB auto-partitioning,
    so the same key lands where the server expects it.
    """

    def __init__(self, key_hasher: Callable[[str], bytes] = default_bound_key_hasher):
        self._key_hasher = key_hasher
        # (from_bound, partition_id) sorted by from_bound; b"" is the leftmost bound.
        self._partitions: List[Tuple[bytes, int]] = []

    def add_partitions(self, partitions: List[PartitionInfo]) -> None:
        for i, p in enumerate(partitions):
            from_bound = p.key_range.from_bound if p.key_range is not None else b""
            if i > 0 and not from_bound:
                raise ValueError("non-first partition without a from_bound key range")
            self._partitions.append((from_bound, p.partition_id))
        self._partitions.sort(key=lambda x: x[0])

    def remove_partition(self, partition_id: int) -> None:
        self._partitions = [p for p in self._partitions if p[1] != partition_id]

    def choose_partition(self, message: PublicMessage) -> int:
        if not self._partitions:
            raise ValueError("no partitions configured for partition chooser")
        hashed = self._key_hasher(message.key or "")

        if message.metadata_items is None:
            message.metadata_items = {}
        message.metadata_items[PARTITION_KEY_METADATA_KEY] = hashed

        # First partition whose from_bound is strictly greater than the hashed key;
        # the owning partition is the previous one.
        bounds = [b for b, _ in self._partitions]
        idx = bisect.bisect_right(bounds, hashed)
        if idx == 0:
            raise RuntimeError("inconsistent partition bounds: lower-bound search returned 0")
        return self._partitions[idx - 1][1]
